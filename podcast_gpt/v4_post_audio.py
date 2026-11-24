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


def _master_peak(dest,timeline):
    peak=0
    for block in master._chunks(dest,timeline):
        peak=max(peak,max(map(abs,_samples(block)),default=0))
    if not peak:raise ValueError("Master has no nonzero PCM")
    return peak


def _scale(value,num,den):
    # Deterministic integer gain rounded toward zero.
    return (abs(value)*num//den)*(1 if value>=0 else -1)


def _mix_blocks(dest,timeline,assets,settings):
    peak=_master_peak(dest,timeline)
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
    for chunk in master._chunks(dest,timeline):
        samples=_samples(chunk)
        mixed=array.array("h")
        for s in samples:
            voice=_scale(s,speech_target,peak)
            music=0
            if bed_samples:
                # 0.5-second overall fade, plus loop-edge fades to reduce clicks.
                j=cursor%len(bed_samples)
                edge=min(800,len(bed_samples)//2)
                fade=min(8000,cursor,total-1-cursor)
                loopfade=min(edge,j,len(bed_samples)-1-j)
                music=_scale(bed_samples[j],bed_target,bed_peak)
                music=_scale(music,fade,8000)
                if edge:music=_scale(music,loopfade,edge)
            value=voice+music
            if not -32768<=value<=32767:raise ValueError("Unexpected mix clipping")
            mixed.append(value);cursor+=1
        yield _bytes(mixed)
    if cursor!=total:raise ValueError("Unexpected speech sample coverage")
    if "outro" in assets:
        samples=assets["outro"][2];p=max(map(abs,samples))
        yield _bytes(_scale(s,PEAK,p) for s in samples)


def _settings(speech_peak,bed_peak):
    if type(speech_peak) is not int or not 8000<=speech_peak<=24000 or type(bed_peak) is not int or not 0<=bed_peak<=6000:
        raise ValueError("Speech peak must be 8000–24000 and bed peak 0–6000 PCM units")
    return {"speech_peak":speech_peak,"bed_peak":bed_peak,"mix_algorithm":"integer_peak_v1"}


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
    if _settings(settings["speech_peak"],settings["bed_peak"])!=settings:raise ValueError("Invalid mix settings")
    roles=saved["assets"]
    if not isinstance(roles,dict) or not set(roles)<=set(ROLES):raise ValueError("Invalid mix asset inventory")
    if {p.name for p in out.iterdir()}!={"receipt.json",WAV,*[r+".wav" for r in roles]}:raise ValueError("Incomplete or unexpected mix files")
    assets={r:_asset(out/(r+".wav"),r) for r in ROLES if r in roles}
    total=timeline["total_frames"]+sum(assets[r][1]["frames"] for r in ("intro","outro") if r in assets)
    path=out/WAV
    if path.stat().st_size>total*2+65536:raise ValueError("Oversized mix WAV")
    digest=hashlib.sha256()
    try:
        with wave.open(str(path),"rb") as w:
            if (w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getcomptype(),w.getnframes())!=(1,2,audio.RATE,"NONE",total):
                raise ValueError("Mix WAV format or duration differs")
            for block in _mix_blocks(dest,timeline,assets,settings):
                if w.readframes(len(block)//2)!=block:raise ValueError("Mix PCM differs from verified recipe")
                digest.update(block)
    except (wave.Error,EOFError):raise ValueError("Invalid mix WAV") from None
    expected=_record(binding,timeline,receipt,settings,assets,digest.hexdigest(),source.digest(path))
    if saved!=expected:raise ValueError("Mix receipt differs")
    return expected


def compose(root,pid,*,intro=None,bed=None,outro=None,speech_peak=22000,bed_peak=3000,acknowledgment=None):
    if acknowledgment!=ACK:raise ValueError("Explicit audio usage rights and mix acknowledgment required")
    settings=_settings(speech_peak,bed_peak)
    folder=projects.project(root,pid)
    with projects.exclusive(folder):
        _,dest,binding,timeline,receipt=_ctx(root,pid)
        out=dest/FOLDER
        if out.exists() or out.is_symlink():raise ValueError("Mix already exists; audit existing candidate, no overwrite")
        assets={k:_asset(v,k) for k,v in (("intro",intro),("bed",bed),("outro",outro)) if v is not None}
        total=timeline["total_frames"]+sum(assets[r][1]["frames"] for r in ("intro","outro") if r in assets)
        if shutil.disk_usage(folder).free<total*2+sum(len(v[0]) for v in assets.values())+1024**2:
            raise ValueError("Insufficient private disk space")
        out.mkdir()
        for role,(raw,info,samples) in assets.items():
            with (out/(role+".wav")).open("xb") as handle:handle.write(raw)
        digest=hashlib.sha256()
        with (out/WAV).open("xb") as handle:
            with wave.open(handle,"wb") as w:
                w.setnchannels(1);w.setsampwidth(2);w.setframerate(audio.RATE)
                for block in _mix_blocks(dest,timeline,assets,settings):
                    w.writeframesraw(block);digest.update(block)
            handle.flush();os.fsync(handle.fileno())
        if _ctx(root,pid)[2:]!=(binding,timeline,receipt):raise ValueError("Original master changed")
        record=_record(binding,timeline,receipt,settings,assets,digest.hexdigest(),source.digest(out/WAV))
        source.atomic_json(out/"receipt.json",record,new=True)
        return {"project_id":pid,"mix":_audit(dest,binding,timeline,receipt),"path":str(out/WAV)}


def inspect(root,pid):
    _,dest,binding,timeline,receipt=_ctx(root,pid)
    return {"project_id":pid,"mix":_audit(dest,binding,timeline,receipt),"path":str(dest/FOLDER/WAV)}
