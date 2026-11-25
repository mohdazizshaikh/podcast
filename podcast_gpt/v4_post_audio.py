"""Deterministic offline audio-only post-production candidate.

Never replace the exact speech master, modify neural bindings or inherit
listening approval. All added audio must be user-authorized.
"""
from __future__ import annotations
import array
import hashlib
import io
import os
import shutil
import sys
import tempfile
import wave
from pathlib import Path
from . import characters, projects, source, v4_audio as audio, v4_master as master

FOLDER="post-audio"
WAV="episode-mix.wav"
ACK="I_HAVE_RIGHTS_TO_ALL_ADDED_AUDIO_AND_AUTHORIZE_LOCAL_MIX"
ROLES=("intro","bed","outro")
LIMITS={"intro":30,"bed":120,"outro":30}
PEAK=24000
BLOCK=16000


def _samples(raw):
    result=array.array("h");result.frombytes(raw)
    if sys.byteorder!="little":result.byteswap()
    return result


def _bytes(samples):
    a=array.array("h",samples)
    if sys.byteorder!="little":a.byteswap()
    return a.tobytes()


def _asset(path,role):
    raw=characters._read_file(path,audio.MAX_WAV)
    info=audio._pcm(raw)
    if info["frames"]>LIMITS[role]*audio.RATE:raise ValueError("Added audio exceeds role duration limit")
    with wave.open(io.BytesIO(raw),"rb") as w:pcm=w.readframes(info["frames"])
    return raw,info,_samples(pcm)


def _speech_blocks(dest,timeline,cleanup,filters=None,adaptive=None,spectral=None):
    from .speech_cleanup import centered
    from .speech_filter import apply
    from .adaptive_noise import apply as reduce_noise
    from .spectral_noise import apply as reduce_spectrum
    for block in master._chunks(dest,timeline):
        samples=_samples(block)
        if cleanup and cleanup["remove_dc"]:samples=centered(samples)
        yield reduce_noise(reduce_spectrum(apply(samples,filters),spectral),adaptive)


def _master_peak(dest,timeline,cleanup=None,filters=None,adaptive=None,spectral=None):
    peak=0
    for samples in _speech_blocks(dest,timeline,cleanup,filters,adaptive,spectral):
        peak=max(peak,max(map(abs,samples),default=0))
    if not peak:raise ValueError("Master has no nonzero PCM")
    return peak


def _scale(value,num,den):
    # Deterministic integer gain rounded toward zero.
    return (abs(value)*num//den)*(1 if value>=0 else -1)


def _unlimited_mix_blocks(dest,timeline,assets,settings):
    cleanup=settings.get("cleanup")
    filters=settings.get("speech_filter")
    adaptive=settings.get("adaptive_noise")
    spectral=settings.get("spectral_noise")
    peak=_master_peak(dest,timeline,cleanup,filters,adaptive,spectral)
    speech_target=settings["speech_peak"]
    bed_target=settings["bed_peak"]
    bed=assets.get("bed")
    bed_samples=bed[2] if bed else None
    bed_peak=max(map(abs,bed_samples)) if bed_samples else 1
    for role in ("intro",):
        if role in assets:
            samples=assets[role][2];p=max(map(abs,samples))
            yield _bytes(_scale(s,PEAK,p) for s in samples)
    cursor=0;total=timeline["total_frames"]
    duck=settings.get("duck_percent",0);level=10000;hold=0
    # Fixed 10 ms attack, 150 ms hold, 250 ms release at 16 kHz.
    floor=10000-duck*100
    from .speech_compressor import step
    compressor=settings.get('compressor');envelope=0
    from .speech_cleanup import step as gate_step
    gate=cleanup['gate_threshold_pcm'] if cleanup else 0
    gate_env=0;gate_level=10000
    for samples in _speech_blocks(dest,timeline,cleanup,filters,adaptive,spectral):
        mixed=array.array("h")
        for s in samples:
            voice=_scale(s,speech_target,peak)
            if gate:voice,gate_env,gate_level=gate_step(voice,gate_env,gate_level,gate)
            if compressor is not None:voice,envelope=step(voice,envelope,compressor)
            music=0
            if bed_samples and duck:
                if abs(voice)>=512:hold=2400
                if hold:
                    level=max(floor,level-63);hold-=1
                else:level=min(10000,level+3)
            if bed_samples:
                # 0.5-second overall fade, plus loop-edge fades to reduce clicks.
                j=cursor%len(bed_samples)
                edge=min(800,len(bed_samples)//2)
                fade=min(8000,cursor,total-1-cursor)
                loopfade=min(edge,j,len(bed_samples)-1-j)
                music=_scale(bed_samples[j],bed_target,bed_peak)
                music=_scale(music,fade,8000)
                if edge:music=_scale(music,loopfade,edge)
                if duck:music=_scale(music,level,10000)
            value=voice+music
            if not -32768<=value<=32767:raise ValueError("Unexpected mix clipping")
            mixed.append(value);cursor+=1
        yield _bytes(mixed)
    if cursor!=total:raise ValueError("Unexpected speech sample coverage")
    if "outro" in assets:
        samples=assets["outro"][2];p=max(map(abs,samples))
        yield _bytes(_scale(s,PEAK,p) for s in samples)


def _mix_blocks(dest,timeline,assets,settings):
    from . import peak_limiter,peak_guard
    limited=peak_limiter.blocks(_unlimited_mix_blocks(dest,timeline,assets,settings),
                                settings.get("limiter"),_samples,_bytes)
    yield from peak_guard.blocks(limited,settings.get("peak_guard"),_samples,_bytes)


def _gain_ceiling(settings):
    from . import peak_guard
    cap=settings.get("limiter",{}).get("ceiling_pcm")
    if "peak_guard" in settings:cap=min(cap,peak_guard.CAP) if cap is not None else peak_guard.CAP
    return cap


def _guard_check(path,frames):
    from . import peak_guard,audio_diagnostics
    return peak_guard.check(audio_diagnostics.measure(path,frames)["true_peak_dbtp"])


def _settings(speech_peak,bed_peak,duck_percent=0,compress_ratio=1,compress_threshold=12000,remove_dc=False,gate_threshold=0,limiter_ceiling=0,highpass_hz=0,hum_hz=0,lowpass_hz=0,true_peak_guard=False,auto_peak_correction=False,adaptive_noise="off",spectral_noise="off"):
    if type(speech_peak) is not int or not 8000<=speech_peak<=24000 or type(bed_peak) is not int or not 0<=bed_peak<=6000:
        raise ValueError("Speech peak must be 8000–24000 and bed peak 0–6000 PCM units")
    if type(duck_percent) is not int or not 0<=duck_percent<=90:raise ValueError("Duck percent must be 0–90")
    result={"speech_peak":speech_peak,"bed_peak":bed_peak,"mix_algorithm":"integer_peak_v1"}
    if duck_percent:result.update(mix_algorithm="integer_peak_duck_v2",duck_percent=duck_percent)
    from .speech_compressor import settings as compressor_settings
    comp=compressor_settings(compress_ratio,compress_threshold)
    if comp is not None:result["compressor"]=comp
    from .speech_cleanup import settings as cleanup_settings
    cleanup=cleanup_settings(remove_dc,gate_threshold)
    if cleanup is not None:result["cleanup"]=cleanup
    from .peak_limiter import settings as limiter_settings
    limiter=limiter_settings(limiter_ceiling)
    if limiter is not None:result["limiter"]=limiter
    from .speech_filter import settings as filter_settings
    filters=filter_settings(highpass_hz,hum_hz,lowpass_hz)
    if filters is not None:result["speech_filter"]=filters
    from .peak_guard import settings as guard_settings
    guard=guard_settings(true_peak_guard)
    if guard is not None:result["peak_guard"]=guard
    if type(auto_peak_correction) is not bool or (auto_peak_correction and not true_peak_guard):
        raise ValueError("Automatic peak correction requires explicit peak guard")
    from .adaptive_noise import settings as noise_settings
    adaptive=noise_settings(adaptive_noise)
    if adaptive is not None:result["adaptive_noise"]=adaptive
    from .spectral_noise import settings as spectrum_settings
    spectral=spectrum_settings(spectral_noise)
    if spectral is not None:result["spectral_noise"]=spectral
    return result


def _ctx(root,pid):
    folder,dest,binding,timeline=master._context(root,pid)
    receipt=master._audit(dest,binding,timeline)
    return folder,dest,binding,timeline,receipt


def _record(binding,timeline,receipt,settings,assets,pcm_hash,wav_hash):
    before=assets["intro"][1]["frames"] if "intro" in assets else 0
    after=assets["outro"][1]["frames"] if "outro" in assets else 0
    return {"schema":1,"binding":binding,"master_receipt_sha256":source.json_digest(receipt),
            "settings":settings,"assets":{k:v[1] for k,v in assets.items()},
            "rights_self_attested":True,"sample_rate":audio.RATE,"intro_frames":before,
            "speech_offset_frames":before,"speech_and_pauses_frames":timeline["total_frames"],
            "outro_frames":after,"total_frames":before+timeline["total_frames"]+after,
            "pcm_sha256":pcm_hash,"wav_sha256":wav_hash,
            "status":"audio_only_mix_candidate","human_mix_quality_approved":False,"publication_approved":False}


def _audit(dest,binding,timeline,receipt):
    out=dest/FOLDER;projects._plain(out)
    for name in ("receipt.json",WAV):projects._plain(out/name,directory=False)
    saved=source.read_json(out/"receipt.json",32000)
    settings=saved["settings"]
    from . import loudness_gain as gain,combined_gain
    normalization=settings.get("normalization")
    combined=isinstance(normalization,dict) and normalization.get("algorithm")==combined_gain.ALGORITHM
    comp=settings.get("compressor",{})
    if not isinstance(comp,dict):raise ValueError("Invalid compressor settings")
    cleanup=settings.get("cleanup",{})
    if not isinstance(cleanup,dict):raise ValueError("Invalid cleanup settings")
    limiter=settings.get("limiter",{})
    if not isinstance(limiter,dict):raise ValueError("Invalid limiter settings")
    filters=settings.get("speech_filter",{})
    if not isinstance(filters,dict):raise ValueError("Invalid speech filter settings")
    adaptive=settings.get("adaptive_noise",{})
    if not isinstance(adaptive,dict):raise ValueError("Invalid adaptive noise settings")
    spectral=settings.get("spectral_noise",{})
    if not isinstance(spectral,dict):raise ValueError("Invalid spectral noise settings")
    base_settings=_settings(settings["speech_peak"],settings["bed_peak"],settings.get("duck_percent",0),comp.get("ratio",1),comp.get("threshold_pcm",12000),cleanup.get("remove_dc",False),cleanup.get("gate_threshold_pcm",0),limiter.get("ceiling_pcm",0),filters.get("highpass_hz",0),filters.get("hum_hz",0),filters.get("lowpass_hz",0),"peak_guard" in settings,"peak_correction" in settings or combined,adaptive.get("mode","off"),spectral.get("mode","off"))
    if "peak_guard" in settings:
        from . import peak_guard
        check=settings.get("peak_guard_check")
        if not isinstance(check,dict):raise ValueError("Missing measured peak guard check")
        base_settings["peak_guard_check"]=peak_guard.check(check.get("measured_true_peak_dbtp"))
    ceiling=_gain_ceiling(base_settings)
    correction=settings.get("peak_correction")
    if "peak_correction" in settings:
        from . import peak_correction
        correction=peak_correction.validate(correction)
        if correction["attempts"][-1]["measured_true_peak_dbtp"]!=base_settings["peak_guard_check"]["measured_true_peak_dbtp"]:
            raise ValueError("Peak correction final measurement differs")
        base_settings["peak_correction"]=correction
    if correction is not None and normalization is not None:raise ValueError("Separate peak correction receipt cannot accompany normalization")
    if normalization is not None:
        base_settings["normalization"]=gain.validate(normalization)
        if normalization.get("sample_peak_ceiling_pcm")!=ceiling:
            raise ValueError("Normalization sample ceiling differs from limiter recipe")
        if combined and normalization["candidate_measurement"]["true_peak_dbtp"]!=base_settings["peak_guard_check"]["measured_true_peak_dbtp"]:
            raise ValueError("Combined gain final measurement differs")
    if base_settings!=settings:raise ValueError("Invalid mix settings")
    roles=saved["assets"]
    if not isinstance(roles,dict) or not set(roles)<=set(ROLES):raise ValueError("Invalid mix asset inventory")
    if {p.name for p in out.iterdir()}!={"receipt.json",WAV,*[r+".wav" for r in roles]}:raise ValueError("Incomplete or unexpected mix files")
    assets={r:_asset(out/(r+".wav"),r) for r in ROLES if r in roles}
    total=timeline["total_frames"]+sum(assets[r][1]["frames"] for r in ("intro","outro") if r in assets)
    path=out/WAV
    if path.stat().st_size>total*2+65536:raise ValueError("Oversized mix WAV")
    digest=hashlib.sha256();baseline_digest=hashlib.sha256();baseline_peak=0;count=0
    try:
        with wave.open(str(path),"rb") as w:
            if (w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getcomptype(),w.getnframes())!=(1,2,audio.RATE,"NONE",total):
                raise ValueError("Mix WAV format or duration differs")
            for block in _mix_blocks(dest,timeline,assets,settings):
                if normalization is not None:
                    baseline_digest.update(block)
                    baseline_peak=max(baseline_peak,max(map(abs,_samples(block)),default=0))
                    block=gain.apply(block,normalization["gain_ppm"],ceiling)
                if correction is not None:
                    baseline_digest.update(block)
                    block=peak_correction.apply(block,correction["gain_ppm"])
                if w.readframes(len(block)//2)!=block:raise ValueError("Mix PCM differs from verified recipe")
                digest.update(block);count+=len(block)//2
            if count!=total or w.readframes(1):raise ValueError("Mix recipe sample coverage differs")
    except (wave.Error,EOFError):raise ValueError("Invalid mix WAV") from None
    if normalization is not None and (baseline_digest.hexdigest()!=normalization["baseline_pcm_sha256"] or baseline_peak!=normalization["baseline_pcm_peak"]):
        raise ValueError("Normalization baseline differs from verified mix recipe")
    if correction is not None and baseline_digest.hexdigest()!=correction["baseline_pcm_sha256"]:
        raise ValueError("Peak correction baseline differs from verified mix recipe")
    expected=_record(binding,timeline,receipt,settings,assets,digest.hexdigest(),source.digest(path))
    if saved!=expected:raise ValueError("Mix receipt differs")
    if "peak_guard" in settings:
        if combined:
            from . import audio_diagnostics,peak_guard
            measured=audio_diagnostics.measure(path,total)
            if measured!=normalization["candidate_measurement"] or peak_guard.check(measured["true_peak_dbtp"])!=settings["peak_guard_check"]:
                raise ValueError("Combined gain final measurement differs; revalidate locally")
        elif _guard_check(path,total)!=settings["peak_guard_check"]:raise ValueError("Measured peak guard check differs; revalidate locally")
        if source.digest(path)!=expected["wav_sha256"]:raise ValueError("Mix changed during peak measurement")
    return expected


def _write_wav(path,blocks):
    digest=hashlib.sha256()
    with path.open("xb") as handle:
        with wave.open(handle,"wb") as w:
            w.setnchannels(1);w.setsampwidth(2);w.setframerate(audio.RATE)
            for block in blocks:
                w.writeframesraw(block);digest.update(block)
        handle.flush();os.fsync(handle.fileno())
    return digest.hexdigest()


def _stage_normalized(dest,timeline,assets,settings,target_lufs,temp,*,auto_peak_correction=False):
    from . import audio_diagnostics as diag,loudness_gain as gain
    baseline=temp/"baseline.wav";candidate=temp/WAV
    baseline_sha=_write_wav(baseline,_mix_blocks(dest,timeline,assets,settings))
    stats=diag.pcm_stats(baseline);before=diag.measure(baseline,stats["frames"])
    ceiling=_gain_ceiling(settings)
    if auto_peak_correction:
        from . import combined_gain
        candidate,pcm_sha,record=combined_gain.run(baseline,temp,stats["frames"],baseline_sha,target_lufs,before,stats["sample_peak_pcm"],ceiling,diag.measure)
        settings["normalization"]=record
        return candidate,pcm_sha
    ppm=gain.gain_ppm(target_lufs,before,stats["sample_peak_pcm"],ceiling)
    def blocks():
        h=hashlib.sha256()
        with wave.open(str(baseline),"rb") as w:
            while True:
                block=w.readframes(BLOCK)
                if not block:break
                h.update(block);yield gain.apply(block,ppm,ceiling)
        if h.hexdigest()!=baseline_sha:raise ValueError("Staged baseline changed")
    pcm_sha=_write_wav(candidate,blocks())
    after=diag.pcm_stats(candidate)
    if after["frames"]!=stats["frames"] or after["full_scale_sample_count"]:
        raise ValueError("Normalized sample coverage or clipping differs")
    if after["sample_peak_pcm"]>gain.sample_ceiling(ceiling):raise ValueError("Normalized sample peak exceeds ceiling")
    measured=diag.measure(candidate,after["frames"])
    settings["normalization"]=gain.record(target_lufs,before,stats["sample_peak_pcm"],baseline_sha,measured,ceiling)
    return candidate,pcm_sha


def compose(root,pid,*,intro=None,bed=None,outro=None,speech_peak=22000,bed_peak=3000,duck_percent=0,target_lufs=None,compress_ratio=1,compress_threshold=12000,remove_dc=False,gate_threshold=0,limiter_ceiling=0,highpass_hz=0,hum_hz=0,lowpass_hz=0,true_peak_guard=False,auto_peak_correction=False,adaptive_noise="off",spectral_noise="off",acknowledgment=None):
    if acknowledgment!=ACK:raise ValueError("Explicit audio usage rights and mix acknowledgment required")
    settings=_settings(speech_peak,bed_peak,duck_percent,compress_ratio,compress_threshold,remove_dc,gate_threshold,limiter_ceiling,highpass_hz,hum_hz,lowpass_hz,true_peak_guard,auto_peak_correction,adaptive_noise,spectral_noise)
    if target_lufs is not None:
        from .loudness_gain import target
        target(target_lufs)
    folder=projects.project(root,pid)
    with projects.exclusive(folder):
        _,dest,binding,timeline,receipt=_ctx(root,pid)
        out=dest/FOLDER
        if out.exists() or out.is_symlink():raise ValueError("Mix already exists; audit existing candidate, no overwrite")
        assets={k:_asset(v,k) for k,v in (("intro",intro),("bed",bed),("outro",outro)) if v is not None}
        if duck_percent and "bed" not in assets:raise ValueError("Ducking requires a background bed")
        total=timeline["total_frames"]+sum(assets[r][1]["frames"] for r in ("intro","outro") if r in assets)
        if shutil.disk_usage(folder).free<total*(12 if auto_peak_correction and target_lufs is not None else 10 if auto_peak_correction else 6 if target_lufs is not None else 2)+sum(len(v[0]) for v in assets.values())+1024**2:
            raise ValueError("Insufficient private disk space")
        with tempfile.TemporaryDirectory(prefix="v4-mix-",dir=folder) as tmp:
            if target_lufs is not None:
                if auto_peak_correction:staged,pcm_sha=_stage_normalized(dest,timeline,assets,settings,target_lufs,Path(tmp),auto_peak_correction=True)
                else:staged,pcm_sha=_stage_normalized(dest,timeline,assets,settings,target_lufs,Path(tmp))
            else:
                staged=Path(tmp)/WAV
                pcm_sha=_write_wav(staged,_mix_blocks(dest,timeline,assets,settings))
            if auto_peak_correction and target_lufs is None:
                from . import peak_correction,audio_diagnostics
                staged,pcm_sha,settings["peak_correction"]=peak_correction.run(staged,Path(tmp),total,pcm_sha,audio_diagnostics.measure)
            if "peak_guard" in settings:
                if auto_peak_correction and target_lufs is not None:
                    from . import audio_diagnostics,peak_guard,loudness_gain
                    measured=loudness_gain._measurement(audio_diagnostics.measure(staged,total))
                    if measured!=settings["normalization"]["candidate_measurement"]:
                        raise ValueError("Combined gain final measurement differs before save; revalidate locally")
                    settings["peak_guard_check"]=peak_guard.check(measured["true_peak_dbtp"])
                else:
                    settings["peak_guard_check"]=_guard_check(staged,total)
                if auto_peak_correction:
                    final_peak=(settings["normalization"]["candidate_measurement"]["true_peak_dbtp"] if target_lufs is not None else settings["peak_correction"]["attempts"][-1]["measured_true_peak_dbtp"])
                    if final_peak!=settings["peak_guard_check"]["measured_true_peak_dbtp"]:raise ValueError("Peak correction final measurement differs")
                # Check staged bytes and full frame coverage before creating immutable output.
                h=hashlib.sha256();count=0
                with wave.open(str(staged),"rb") as candidate:
                    if (candidate.getnchannels(),candidate.getsampwidth(),candidate.getframerate(),candidate.getcomptype(),candidate.getnframes())!=(1,2,audio.RATE,"NONE",total):
                        raise ValueError("Guarded candidate format or duration differs")
                    while True:
                        block=candidate.readframes(BLOCK)
                        if not block:break
                        count+=len(block)//2;h.update(block)
                if count!=total or h.hexdigest()!=pcm_sha:raise ValueError("Guarded staged PCM changed")
            if _ctx(root,pid)[2:]!=(binding,timeline,receipt):raise ValueError("Original master changed")
            out.mkdir()
            for role,(raw,info,samples) in assets.items():
                with (out/(role+".wav")).open("xb") as handle:handle.write(raw)
            with staged.open("rb") as inp,(out/WAV).open("xb") as handle:
                shutil.copyfileobj(inp,handle);handle.flush();os.fsync(handle.fileno())
            record=_record(binding,timeline,receipt,settings,assets,pcm_sha,source.digest(out/WAV))
            source.atomic_json(out/"receipt.json",record,new=True)
        return {"project_id":pid,"mix":_audit(dest,binding,timeline,receipt),"path":str(out/WAV)}


def inspect(root,pid):
    _,dest,binding,timeline,receipt=_ctx(root,pid)
    return {"project_id":pid,"mix":_audit(dest,binding,timeline,receipt),"path":str(dest/FOLDER/WAV)}
