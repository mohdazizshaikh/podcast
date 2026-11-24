"""Read-only objective audio measurements on an audited private master or mix."""
import math
import json
import re
import wave
from . import projects,source,media,v4_master,v4_post_audio
from .v4_post_audio import _samples


def _number(value):
    try:n=float(value)
    except (TypeError,ValueError):raise ValueError("Invalid FFmpeg loudness measurement") from None
    return round(n,2) if math.isfinite(n) else None


def parse_loudness(stderr):
    # loudnorm emits one small JSON object at the end of its diagnostic log.
    for match in reversed(list(re.finditer(r"\{[^{}]{1,4096}\}",stderr))):
        try:data=json.loads(match.group())
        except ValueError:continue
        if not isinstance(data,dict) or not {"input_i","input_tp","input_lra","input_thresh"}<=set(data):continue
        return {"integrated_lufs":_number(data["input_i"]),"true_peak_dbtp":_number(data["input_tp"]),
                "loudness_range_lu":_number(data["input_lra"]),"gating_threshold_lufs":_number(data["input_thresh"])}
    raise ValueError("FFmpeg loudness measurements unavailable")


def pcm_stats(path):
    count=peak=squares=clipped=zero=total=0
    with wave.open(str(path),"rb") as w:
        if (w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getcomptype())!=(1,2,16000,"NONE"):
            raise ValueError("Expected audited mono PCM16 16 kHz")
        expected=w.getnframes()
        while True:
            block=w.readframes(16000)
            if not block:break
            samples=_samples(block)
            count+=len(samples);peak=max(peak,max(map(abs,samples),default=0))
            squares+=sum(v*v for v in samples);total+=sum(samples)
            clipped+=sum(v in (-32768,32767) for v in samples)
            zero+=samples.count(0)
        if count!=expected or not count:raise ValueError("Invalid PCM coverage")
    return {"frames":count,"sample_peak_pcm":peak,"sample_peak_dbfs":round(20*math.log10(peak/32768),2) if peak else None,
            "rms_dbfs":round(10*math.log10(squares/count/32768**2),2) if squares else None,
            "full_scale_sample_count":clipped,"zero_sample_fraction":round(zero/count,6),
            "dc_offset_pcm":round(total/count,2)}


def measure(path,frames):
    result=media.cmd(["ffmpeg","-nostdin","-hide_banner","-v","info","-i",str(path),"-map","0:a:0",
                      "-af","loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json","-f","null","-"],
                     timeout=max(120,int(frames/16000*8)))
    return parse_loudness(result.stderr)


def inspect(root,pid,*,kind="master",per_turn=False):
    if kind not in ("master","mix"):raise ValueError("Choose master or mix")
    if per_turn and kind!="master":raise ValueError("Per-turn diagnostics require master")
    folder=projects.project(root,pid)
    # Lock during audit and measurement, no persistent result or new media.
    with projects.exclusive(folder):
        _,dest,binding,timeline,receipt=v4_post_audio._ctx(root,pid)
        if kind=="master":path=dest/v4_master.FOLDER/v4_master.WAV
        else:
            receipt=v4_post_audio._audit(dest,binding,timeline,receipt)
            path=dest/v4_post_audio.FOLDER/v4_post_audio.WAV
        sha=receipt["wav_sha256"]
        projects._plain(path,directory=False)
        stats=pcm_stats(path)
        loudness=measure(path,stats["frames"])
        turns=[]
        if per_turn:
            for row in timeline["rows"]:
                unit=dest/row["turn_id"]/"speech.wav"
                projects._plain(unit,directory=False)
                if source.digest(unit)!=row["wav_sha256"]:raise ValueError("Speech changed during diagnostics")
                values=pcm_stats(unit)
                if source.digest(unit)!=row["wav_sha256"]:raise ValueError("Speech changed during diagnostics")
                flags=[]
                if values["full_scale_sample_count"]:flags.append("full_scale_samples")
                if values["rms_dbfs"] is None or values["rms_dbfs"]<-45:flags.append("low_rms")
                if abs(values["dc_offset_pcm"])>512:flags.append("dc_offset")
                turns.append({"turn_id":row["turn_id"],"speaker":row["speaker"],"pcm":values,"diagnostic_flags":flags})
        if source.digest(path)!=sha:raise ValueError("Audio changed during measurement")
        integrated=loudness["integrated_lufs"];peak=loudness["true_peak_dbtp"]
        gain=None if integrated is None or peak is None else round(min(-16-integrated,-1.5-peak),2)
        return {"project_id":pid,"kind":kind,"wav_sha256":sha,"pcm":stats,"loudness":loudness,
                "reference_target_lufs":-16,"reference_true_peak_ceiling_dbtp":-1.5,
                "suggested_static_gain_db":gain,"audio_modified":False,"target_normalization_performed":False,
                "human_quality_verified":False,"publication_approved":False,
                "per_turn_requested":bool(per_turn),"turn_diagnostics":turns,"flags_are_heuristic":True}
