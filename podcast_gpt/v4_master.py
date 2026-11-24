"""Compose and audit exact PCM master from verified V4 measured timeline."""
from __future__ import annotations

import hashlib
import io
import os
import shutil
import wave

from . import characters, projects, source, v4_audio as audio

FOLDER="master"
WAV="episode.wav"
RECEIPT="receipt.json"


def _context(root,pid):
    folder,dest,binding,turns,req,_=audio._context(root,pid)
    items=audio._read_parts(dest,binding,turns)
    timeline=audio._check_timeline(dest,binding,turns,items,req)
    if timeline is None:raise ValueError("Finalize verified measured audio timeline first")
    return folder,dest,binding,timeline


def _chunks(dest,timeline):
    for row in timeline["rows"]:
        raw=characters._read_file(dest/row["turn_id"]/"speech.wav",audio.MAX_WAV)
        info=audio._pcm(raw)
        if info["wav_sha256"]!=row["wav_sha256"] or info["pcm_sha256"]!=row["pcm_sha256"] or info["frames"]!=row["speech_end_frame"]-row["start_frame"]:
            raise ValueError("Speech audio changed during master composition")
        with wave.open(io.BytesIO(raw),"rb") as w:yield w.readframes(info["frames"])
        if row["pause_frames"]:yield bytes(row["pause_frames"]*2)


def _audit(dest,binding,timeline):
    folder=dest/FOLDER;projects._plain(folder)
    if {p.name for p in folder.iterdir()}!={WAV,RECEIPT}:raise ValueError("Incomplete master audio; inspect locally")
    path=folder/WAV;projects._plain(path,directory=False)
    receipt=folder/RECEIPT;projects._plain(receipt,directory=False)
    if path.stat().st_size>timeline["total_frames"]*2+65536:raise ValueError("Oversized master WAV")
    digest=hashlib.sha256()
    try:
        with wave.open(str(path),"rb") as w:
            if (w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getcomptype(),w.getnframes())!=(1,2,audio.RATE,"NONE",timeline["total_frames"]):
                raise ValueError("Master WAV format or duration differs")
            for chunk in _chunks(dest,timeline):
                if w.readframes(len(chunk)//2)!=chunk:raise ValueError("Master PCM differs from original speech or pause samples")
                digest.update(chunk)
    except (wave.Error,EOFError):raise ValueError("Invalid master WAV") from None
    expected={"schema":1,"binding":binding,"timeline_sha256":source.json_digest(timeline),
              "wav_sha256":source.digest(path),"pcm_sha256":digest.hexdigest(),"frames":timeline["total_frames"],
              "sample_rate":audio.RATE,"human_audio_quality_approved":False,"publication_approved":False}
    if source.read_json(receipt,16000)!=expected:raise ValueError("Master audio receipt differs")
    return expected


def compose(root,pid):
    folder=projects.project(root,pid)
    with projects.exclusive(folder):
        _,dest,binding,timeline=_context(root,pid)
        out=dest/FOLDER
        if out.exists() or out.is_symlink():return {"project_id":pid,"master":_audit(dest,binding,timeline)}
        if shutil.disk_usage(folder).free<timeline["total_frames"]*2+1024**2:raise ValueError("Insufficient private disk space for master")
        out.mkdir()
        path=out/WAV
        digest=hashlib.sha256()
        with path.open("xb") as handle:
            with wave.open(handle,"wb") as w:
                w.setnchannels(1);w.setsampwidth(2);w.setframerate(audio.RATE)
                for chunk in _chunks(dest,timeline):
                    w.writeframesraw(chunk);digest.update(chunk)
            handle.flush();os.fsync(handle.fileno())
        if _context(root,pid)[2:]!=(binding,timeline):raise ValueError("Source changed during master composition")
        record={"schema":1,"binding":binding,"timeline_sha256":source.json_digest(timeline),
                "wav_sha256":source.digest(path),"pcm_sha256":digest.hexdigest(),"frames":timeline["total_frames"],
                "sample_rate":audio.RATE,"human_audio_quality_approved":False,"publication_approved":False}
        source.atomic_json(out/RECEIPT,record,new=True)
        return {"project_id":pid,"master":_audit(dest,binding,timeline)}


def inspect(root,pid):
    _,dest,binding,timeline=_context(root,pid)
    return {"project_id":pid,"master":_audit(dest,binding,timeline)}
