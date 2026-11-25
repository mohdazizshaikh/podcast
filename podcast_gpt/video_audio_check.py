"""Read-only decoded AAC versus audited master/mix sample comparison.

Lossy codec, resampling and encoder delay prevent bit-exact equivalence.
No automatic approval, lag compensation or semantic speech verification.
"""
import math
import shutil
import tempfile
import wave
from pathlib import Path
from . import projects,source,production_overview as overview,media
from .v4_post_audio import _samples

KINDS=("preview","neural","mixed","studio-preview","neural-studio","mixed-neural-studio")
RATE=16000
WINDOW=RATE


def compare_window(a,b):
    if len(a)!=len(b) or not a:raise ValueError("Equal nonempty PCM windows required")
    n=len(a);sa=sum(a);sb=sum(b)
    aa=sum(x*x for x in a);bb=sum(y*y for y in b)
    cross=sum(x*y for x,y in zip(a,b))
    va=n*aa-sa*sa;vb=n*bb-sb*sb
    corr=(n*cross-sa*sb)/math.sqrt(va*vb) if va>0 and vb>0 else None
    error=max(0,aa+bb-2*cross)
    rms=math.sqrt(error/n)
    return {"correlation":round(max(-1,min(1,corr)),6) if corr is not None else None,
            "reference_rms_pcm":round(math.sqrt(aa/n),2),
            "reference_ac_rms_pcm":round(math.sqrt(va)/n,2),
            "decoded_ac_rms_pcm":round(math.sqrt(vb)/n,2),
            "reference_dc_pcm":round(sa/n,2),"decoded_dc_pcm":round(sb/n,2),
            "decoded_rms_pcm":round(math.sqrt(bb/n),2),"residual_rms_pcm":round(rms,2),
            "relative_residual":round(math.sqrt(error/aa),6) if aa else None}


def extra_window_flags(m,count):
    """Heuristic dropouts/DC faults; never a pass/fail quality certificate."""
    if count<1600:
        return []
    flags=[]
    if m["reference_ac_rms_pcm"]>=100 and m["decoded_ac_rms_pcm"]<10:
        flags.append("missing_variable_audio")
    if abs(m["decoded_dc_pcm"]-m["reference_dc_pcm"])>=300:
        flags.append("dc_offset_difference")
    if m["correlation"] is None and m["reference_rms_pcm"]>=100 and m["relative_residual"]>.35:
        flags.append("uncorrelatable_audio_mismatch")
    return flags


def compare_wavs(reference,decoded):
    rows=[];checked=0;informative=0;low=0;correlations=[];residuals=[];quiet_mismatch=0;extra_counts={};flagged=0;windows=0;short_windows=0
    with wave.open(str(reference),"rb") as a,wave.open(str(decoded),"rb") as b:
        for w in (a,b):
            if (w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getcomptype())!=(1,2,RATE,"NONE"):
                raise ValueError("Expected mono PCM16 16 kHz")
        af,bf=a.getnframes(),b.getnframes()
        if not 1<=af<=RATE*4020 or not 1<=bf<=RATE*4021:raise ValueError("Audio sample coverage out of bounds")
        overlap=min(af,bf)
        while checked<overlap:
            count=min(WINDOW,overlap-checked)
            x=_samples(a.readframes(count));y=_samples(b.readframes(count))
            if len(x)!=count or len(y)!=count:raise ValueError("Truncated decoded PCM")
            m=compare_window(x,y)
            flags=[];windows+=1
            if count<1600:short_windows+=1
            # Near-constant and quiet windows cannot establish similarity.
            if count>=1600 and m["reference_rms_pcm"]>=100 and m["correlation"] is not None:
                informative+=1;correlations.append(m["correlation"]);residuals.append(m["relative_residual"])
                if m["correlation"]<.90 or m["relative_residual"]>.35:low+=1;flags.append("low_similarity")
            elif m["reference_rms_pcm"]<100 and m["decoded_rms_pcm"]>=300:
                quiet_mismatch+=1;flags.append("unexpected_audio_in_quiet_window")
            for flag in extra_window_flags(m,count):
                extra_counts[flag]=extra_counts.get(flag,0)+1
                flags.append(flag)
            if flags:flagged+=1
            if flags and len(rows)<20:rows.append({"start_seconds":checked/RATE,"sample_count":count,**m,"flags":flags})
            checked+=count
    return {"reference_frames":af,"decoded_frames":bf,"overlap_frames":checked,
            "duration_difference_seconds":round((bf-af)/RATE,6),"informative_windows":informative,
            "low_similarity_windows":low,"unexpected_quiet_audio_windows":quiet_mismatch,
            "mean_correlation":round(sum(correlations)/len(correlations),6) if correlations else None,
            "mean_relative_residual":round(sum(residuals)/len(residuals),6) if residuals else None,
            "flagged_window_examples":rows,"flagged_examples_truncated":flagged>len(rows),
            "flagged_window_count":flagged,"window_count":windows,"short_window_count":short_windows,
            "additional_flag_counts":extra_counts,
            "uncompared_reference_frames":af-overlap,"uncompared_decoded_frames":bf-overlap,
            "lag_compensation_performed":False,"thresholds_are_heuristic":True}


def inspect(root,pid,kind):
    if kind not in KINDS:raise ValueError("Choose a supported video candidate")
    folder=projects.project(root,pid)
    ref=overview.media_check(root,pid,"mix" if kind in ("mixed","mixed-neural-studio") else "master")
    video=overview.media_check(root,pid,kind)
    with projects.exclusive(folder):
        reference=Path(ref["local_path"]);candidate=Path(video["local_path"])
        for p,item in ((reference,ref),(candidate,video)):
            projects._plain(p,directory=False)
            if source.digest(p)!=item["sha256"]:raise ValueError("Audited input changed")
        if shutil.disk_usage(folder).free<reference.stat().st_size+32*1024**2:raise ValueError("Insufficient private scratch disk space")
        with tempfile.TemporaryDirectory(prefix="audio-compare-",dir=folder) as tmp:
            decoded=Path(tmp)/"decoded.wav"
            # Bound decoded output to maximum supported speech + intro/outro.
            media.cmd(["ffmpeg","-nostdin","-hide_banner","-v","error","-i",str(candidate),
                       "-map","0:a:0","-vn","-t","4021","-ac","1","-ar","16000","-c:a","pcm_s16le",str(decoded)],timeout=3600)
            report=compare_wavs(reference,decoded)
        if source.digest(reference)!=ref["sha256"] or source.digest(candidate)!=video["sha256"]:raise ValueError("Audited input changed during comparison")
        return {"project_id":pid,"kind":kind,"reference_kind":ref["kind"],"reference_sha256":ref["sha256"],
                "video_sha256":video["sha256"],"comparison":report,"audio_modified":False,
                "bit_exact_audio_verified":False,"human_quality_verified":False,"publication_approved":False}
