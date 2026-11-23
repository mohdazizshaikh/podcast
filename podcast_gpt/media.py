"""Real CPU FFmpeg/Pillow H.264 + ORIGINAL 16k PCM AAC/SRT rendering and checks.

No synthetic model inference. Decoder/provenance audits do not mean Hindi
phonemes or face motion have passed human quality review.
"""
from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from .source import SPEAKERS, RATE, digest, json_digest, load_project, verify_source, verify_chunks, atomic_json, read_json, workspace_path

FPS=24
WIDTH, HEIGHT=1280,720


def tools_ready() -> dict:
    return {name: shutil.which(name) for name in ("ffmpeg","ffprobe")}


def cmd(args: list[str], *, timeout: int = 3600) -> subprocess.CompletedProcess:
    process = subprocess.run([str(x) for x in args], capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=timeout, check=False)
    if process.returncode:
        raise RuntimeError("Media encoder/decoder error (inspect FFmpeg installation and local source; exit " + str(process.returncode) + ")")
    return process


def streams(path: Path) -> dict:
    if path.is_symlink() or not path.is_file() or path.stat().st_size < 256:
        raise ValueError("Missing/symlinked/incomplete video")
    data=json.loads(cmd(["ffprobe","-v","error","-show_streams","-show_format",
                         "-of","json",str(path)], timeout=90).stdout)
    video=[x for x in data.get("streams",[]) if x.get("codec_type")=="video"]
    audio=[x for x in data.get("streams",[]) if x.get("codec_type")=="audio"]
    if len(video)!=1 or len(audio)!=1:
        raise ValueError("Video must have EXACTLY one real video and one audio stream")
    length=float(data.get("format",{}).get("duration",0))
    if not math.isfinite(length) or length<=0:
        raise ValueError("Video has invalid measured duration")
    return {"duration":length,"width":int(video[0]["width"]),"height":int(video[0]["height"]),
            "video_codec":video[0]["codec_name"],"audio_codec":audio[0]["codec_name"],
            "audio_rate":int(audio[0].get("sample_rate",0)),
            "video_duration":float(video[0].get("duration",length)),
            "audio_duration":float(audio[0].get("duration",length))}


def full_decode(mp4: Path, *, seconds: float, require_720: bool=False) -> dict:
    d=streams(mp4)
    if d["width"] < 200 or d["height"] < 200 or d["video_codec"] not in ("h264", "mpeg4", "vp9", "av1"):
        raise ValueError("Video codec/dimensions unsupported")
    if require_720 and (d["width"], d["height"])!=(WIDTH,HEIGHT):
        raise ValueError("Final exported video is not 1280x720")
    if abs(d["duration"]-seconds)>max(0.45,seconds*.025):
        raise ValueError("Video does not match signed original PCM duration")
    if abs(d["audio_duration"]-seconds)>max(0.5,seconds*.028):
        raise ValueError("Original Hindi AAC timeline coverage is incomplete")
    cmd(["ffmpeg","-hide_banner","-v","error","-xerror","-i",str(mp4),
         "-map","0:v:0","-f","null","-"],timeout=max(100,math.ceil(seconds*5)))
    cmd(["ffmpeg","-hide_banner","-v","error","-xerror","-i",str(mp4),
         "-map","0:a:0","-f","null","-"],timeout=max(100,math.ceil(seconds*5)))
    return d


def srt_stamp(seconds: float) -> str:
    ticks=round(seconds*1000)
    h, ticks=divmod(ticks,3600000);m,ticks=divmod(ticks,60000);s,ms=divmod(ticks,1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def timeline(root: Path, source: dict) -> list[dict]:
    project=load_project(root)
    clock=0.0;rows=[]
    for turn in project["turns"]:
        duration=source["voices"][turn["id"]]["frames"]/RATE
        rows.append({"id":turn["id"],"speaker":turn["speaker"],"text":turn["text"],
                     "start":clock,"end":clock+duration,"duration":duration,
                     "pause":float(turn["pause_after"])})
        clock+=duration+turn["pause_after"]
    if abs(clock-source["original_seconds"])>.0001:
        raise ValueError("Original signed timeline is inconsistent")
    return rows


def subtitle(rows: list[dict]) -> str:
    return "\n".join(f"{i}\n{srt_stamp(x['start'])} --> {srt_stamp(x['end'])}\n{x['text']}\n"
                     for i,x in enumerate(rows,1))


def original_audio(root: Path, rows: list[dict], target: Path) -> None:
    """Exact original spoken samples + silence, no secondary model audio."""
    with wave.open(str(target),"wb") as final:
        final.setnchannels(1);final.setsampwidth(2);final.setframerate(RATE)
        for row in rows:
            with wave.open(str(root/"voices"/(row["id"]+".wav")),"rb") as voice:
                if (voice.getnchannels(),voice.getsampwidth(),voice.getframerate())!=(1,2,RATE):
                    raise ValueError("Source voice WAV structure changed")
                final.writeframes(voice.readframes(voice.getnframes()))
            final.writeframes(b"\0\0" * round(row["pause"]*RATE))


def portrait_card(root: Path, speaker: str, dest: Path) -> None:
    portrait=root/"portraits"/(speaker+".png")
    with Image.open(portrait) as face:
        face=ImageOps.exif_transpose(face).convert("RGB")
        # Explicit static layout; no false representation of AI lip-sync.
        background=Image.new("RGB",(WIDTH,HEIGHT),(12,20,34))
        crop=ImageOps.fit(face,(440,540),method=Image.Resampling.LANCZOS)
        background.paste(crop,(95,90))
        draw=ImageDraw.Draw(background)
        draw.rounded_rectangle((580,135,1160,605),radius=26,fill=(23,37,59),outline=(73,100,139),width=3)
        draw.text((628,208),speaker.upper(),fill=(235,244,255),font=ImageFont.load_default(size=34))
        draw.text((628,285),"HINDI PODCAST",fill=(157,196,236),font=ImageFont.load_default(size=26))
        draw.text((628,354),"ORIGINAL HUMAN/AUTHORIZED VOICE",fill=(205,219,240),font=ImageFont.load_default(size=18))
        draw.text((628,398),"STATIC IMAGE - NOT LIP SYNC",fill=(255,192,159),font=ImageFont.load_default(size=17))
        background.save(dest,"PNG")


def _images_concat(root: Path, rows: list[dict], tmp: Path) -> Path:
    cards={}
    for sp in SPEAKERS:
        img=tmp/(sp+".png");portrait_card(root,sp,img);cards[sp]=img
    manifest=tmp/"images.ffconcat"
    lines=["ffconcat version 1.0"]
    for row in rows:
        # FFmpeg concat demuxer does NOT interpolate still images; CFR encoding
        # -vsync vfr then fps=24 duplicates individual source cards.
        path=cards[row["speaker"]].as_posix().replace("'","'\\''")
        lines.extend(["file '"+path+"'",f"duration {row['duration']+row['pause']:.6f}"])
    # Needed so demuxer honors duration on final still image.
    last=cards[rows[-1]["speaker"]].as_posix().replace("'","'\\''")
    lines.append("file '"+last+"'")
    manifest.write_text("\n".join(lines)+"\n",encoding="utf-8")
    return manifest


def render_static(root: Path, *, allow_short: bool=False) -> dict:
    root=workspace_path(root)
    src=verify_source(root,allow_short=allow_short)
    target=root/"exports"/"original_hindi_static.mp4"
    report_path=root/"exports"/"original_hindi_static.json"
    captions=root/"exports"/"original_hindi.srt"
    if any(p.exists() or p.is_symlink() for p in (target,report_path,captions)):
        raise ValueError("Existing private static video/report/SRT; no silent overwrite")
    rows=timeline(root,src)
    with tempfile.TemporaryDirectory(prefix="podcast-static-") as temp:
        temp=Path(temp)
        audio=temp/"original.wav";original_audio(root,rows,audio)
        listing=_images_concat(root,rows,temp)
        staging=temp/"video.mp4"
        cmd(["ffmpeg","-y","-hide_banner","-v","error","-f","concat","-safe","0",
             "-i",str(listing),"-i",str(audio),"-filter:v",f"fps={FPS},format=yuv420p",
             "-c:v","libx264","-preset","veryfast","-crf","25","-r",str(FPS),
             "-c:a","aac","-b:a","160k","-ar","48000","-movflags","+faststart",
             "-t",f"{src['original_seconds']:.6f}","-shortest",str(staging)],
            timeout=max(300,round(src['original_seconds']*10)))
        measured=full_decode(staging,seconds=src["original_seconds"],require_720=True)
        # Verify original inputs didn't change during the slow encode.
        verify_source(root,allow_short=allow_short)
        target.parent.mkdir(exist_ok=True)
        with captions.open("x",encoding="utf-8") as f:f.write(subtitle(rows))
        shutil.copyfile(staging,target)
        result={"schema":3,"status":"original_static_video_structurally_verified_not_lipsync",
                "source_binding":json_digest(src),"source_seconds":src["original_seconds"],
                "video_sha256":digest(target),"srt_sha256":digest(captions),
                "measured_streams":measured,"turns":45,"neural_lipsync_verified":False,
                "human_lipsync_approved":False,"full_ten_minute_neural_video_completed":False,
                "synthetic_short_test_only":allow_short}
        atomic_json(report_path,result,new=True)
    return result


def audit_static(root: Path, *, allow_short: bool=False) -> dict:
    root=workspace_path(root);src=verify_source(root,allow_short=allow_short)
    report=read_json(root/"exports"/"original_hindi_static.json")
    target=root/"exports"/"original_hindi_static.mp4"
    captions=root/"exports"/"original_hindi.srt"
    if captions.is_symlink() or digest(target)!=report.get("video_sha256") or digest(captions)!=report.get("srt_sha256"):
        raise ValueError("Static video/SRT SHA changed")
    if (report.get("source_binding")!=json_digest(src) or report.get("source_seconds")!=src["original_seconds"]
            or report.get("status")!="original_static_video_structurally_verified_not_lipsync"
            or report.get("human_lipsync_approved") is not False):
        raise ValueError("Static media report invalid or source changed")
    if captions.read_text(encoding="utf-8")!=subtitle(timeline(root,src)):
        raise ValueError("Subtitle timeline differs from original exact PCM")
    measured=full_decode(target,seconds=src["original_seconds"],require_720=True)
    return {"original_hindi_static_structurally_verified":True,"media":measured,
            "neural_lipsync_verified":False,"human_lipsync_approved":False,
            "publication_approved":False}