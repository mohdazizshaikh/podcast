"""CPU static active-speaker preview, never neural lip-sync."""
from __future__ import annotations

import io
import shutil
import tempfile

from PIL import Image, ImageOps, ImageDraw, ImageFont
from . import characters, media, projects, script_review, source
from . import v4_audio_review as review, v4_master as master

FOLDER="static-preview"
VIDEO="preview.mp4"
SRT="preview.srt"
RECEIPT="receipt.json"
SIZES={"landscape":(1280,720),"vertical":(720,1280),"square":(720,720)}


def _context(root,pid):
    folder,dest,binding,timeline=master._context(root,pid)
    receipt=master._audit(dest,binding,timeline)
    approved=review.require_pass(root,pid)
    current=script_review.current_script(root,pid,require_pass=True)
    req=projects.load(root,pid)
    cast=characters.read_cast(root,pid)
    if current["version_sha256"]!=binding["script_version_sha256"] or cast["cast_sha256"]!=binding["cast_sha256"]:
        raise ValueError("Preview inputs changed")
    turns=current["turns"]
    if [(t["id"],t["speaker"]) for t in turns]!=[(r["turn_id"],r["speaker"]) for r in timeline["rows"]]:
        raise ValueError("Timeline does not match current script")
    seal={"binding":binding,"master_receipt_sha256":source.json_digest(receipt),
          "audio_review_sha256":approved,"timeline_sha256":source.json_digest(timeline),
          "video_format":req["video_format"]}
    return folder,dest,timeline,turns,cast,seal


def subtitles(timeline,turns):
    lines=[]
    for i,(row,turn) in enumerate(zip(timeline["rows"],turns),1):
        start=media.srt_stamp(row["start_frame"]/timeline["sample_rate"])
        end=media.srt_stamp(row["speech_end_frame"]/timeline["sample_rate"])
        lines.extend([str(i),start+" --> "+end,turn["text"],""])
    return ("\n".join(lines)+"\n").encode("utf-8")


def _card(raw,index,size,path):
    w,h=size
    canvas=Image.new("RGB",size,(17,24,39))
    with Image.open(io.BytesIO(raw)) as im:
        crop=ImageOps.contain(im.convert("RGB"),(int(w*.84),int(h*.77)),method=Image.Resampling.LANCZOS)
        canvas.paste(crop,((w-crop.width)//2,(int(h*.80)-crop.height)//2))
    draw=ImageDraw.Draw(canvas)
    font=ImageFont.load_default(size=25)
    draw.text((w//2,int(h*.86)),f"PRESENTER {index:02}",anchor="mm",font=font,fill=(240,245,250))
    draw.text((w//2,int(h*.93)),"STATIC PREVIEW - NOT LIP SYNC",anchor="mm",
              font=ImageFont.load_default(size=18),fill=(255,190,120))
    canvas.save(path,"PNG")


def _listing(root,cast,timeline,seal,temp):
    cards={}
    for i,row in enumerate(cast["cast"],1):
        data=characters.read(root,row["character_id"])
        if source.json_digest(data)!=row["record_sha256"]:raise ValueError("Cast profile changed")
        raw=characters._read_file(characters._profile_folder(root,row["character_id"])/characters.PORTRAIT,characters.MAX_PORTRAIT)
        if characters._portrait_info(raw)!=data["portrait"]:raise ValueError("Portrait changed")
        filename=f"card{i:02}.png"
        _card(raw,i,SIZES[seal["video_format"]],temp/filename)
        cards[row["speaker"]]=filename
    lines=["ffconcat version 1.0"]
    for row in timeline["rows"]:
        lines.extend(["file "+cards[row["speaker"]],
                      f"duration {(row['end_frame']-row['start_frame'])/timeline['sample_rate']:.8f}"])
    lines.append("file "+cards[timeline["rows"][-1]["speaker"]])
    path=temp/"cards.ffconcat"
    path.write_text("\n".join(lines)+"\n",encoding="ascii")
    return path


def _decode(path,timeline,seal):
    seconds=timeline["measured_audio_seconds"]
    streams=media.full_decode(path,seconds=seconds)
    if (streams["width"],streams["height"])!=SIZES[seal["video_format"]] or (streams["video_codec"],streams["audio_codec"],streams["audio_rate"])!=("h264","aac",48000):
        raise ValueError("Preview codec or selected aspect ratio differs")
    if any(abs(streams[k]-seconds)>.5 for k in ("duration","video_duration","audio_duration")):
        raise ValueError("Preview stream coverage differs from measured audio")
    return streams


def _record(path,timeline,seal,streams):
    return {"schema":1,"binding":seal,"video_sha256":source.digest(path/VIDEO),
            "srt_sha256":source.digest(path/SRT),"measured_streams":streams,
            "turn_count":len(timeline["rows"]),"status":"static_portrait_preview_not_neural_lipsync",
            "neural_lipsync_verified":False,"publication_approved":False}


def _audit(dest,timeline,turns,seal):
    path=dest/FOLDER
    projects._plain(path)
    if {p.name for p in path.iterdir()}!={VIDEO,SRT,RECEIPT}:
        raise ValueError("Incomplete preview; inspect locally")
    for name in (VIDEO,SRT,RECEIPT):projects._plain(path/name,directory=False)
    if characters._read_file(path/SRT,2_000_000)!=subtitles(timeline,turns):
        raise ValueError("Subtitle content or timing differs")
    saved=source.read_json(path/RECEIPT,32_000)
    if saved.get("video_sha256")!=source.digest(path/VIDEO):raise ValueError("Preview video hash differs")
    expected=_record(path,timeline,seal,_decode(path/VIDEO,timeline,seal))
    if saved!=expected:raise ValueError("Preview receipt differs")
    return expected


def render(root,pid):
    folder=projects.project(root,pid)
    with projects.exclusive(folder):
        _,dest,timeline,turns,cast,seal=_context(root,pid)
        path=dest/FOLDER
        if path.exists() or path.is_symlink():return {"project_id":pid,"preview":_audit(dest,timeline,turns,seal)}
        if shutil.disk_usage(folder).free<max(100*1024**2,int(timeline["measured_audio_seconds"]*500000)):
            raise ValueError("Insufficient private disk space for static preview")
        with tempfile.TemporaryDirectory(prefix="v4-preview-",dir=folder) as tmp:
            from pathlib import Path
            temp=Path(tmp)
            listing=_listing(root,cast,timeline,seal,temp)
            seconds=timeline["measured_audio_seconds"]
            staging=temp/VIDEO
            media.cmd(["ffmpeg","-nostdin","-hide_banner","-v","error","-f","concat","-safe","1","-i",str(listing),
                       "-i",str(dest/master.FOLDER/master.WAV),"-map","0:v:0","-map","1:a:0",
                       "-vf","fps=25,tpad=stop_mode=clone:stop_duration=1,format=yuv420p",
                       "-c:v","libx264","-threads","2","-preset","veryfast","-crf","25",
                       "-c:a","aac","-ar","48000","-b:a","128k","-movflags","+faststart",
                       "-t",f"{seconds:.8f}",str(staging)],timeout=max(300,int(seconds*12)))
            streams=_decode(staging,timeline,seal)
            if _context(root,pid)[2:]!=(timeline,turns,cast,seal):raise ValueError("Preview source changed during rendering")
            path.mkdir()
            with staging.open("rb") as inp,(path/VIDEO).open("xb") as out:shutil.copyfileobj(inp,out)
            with (path/SRT).open("xb") as out:out.write(subtitles(timeline,turns))
            source.atomic_json(path/RECEIPT,_record(path,timeline,seal,streams),new=True)
        return {"project_id":pid,"preview":_audit(dest,timeline,turns,seal)}


def inspect(root,pid):
    _,dest,timeline,turns,cast,seal=_context(root,pid)
    return {"project_id":pid,"preview":_audit(dest,timeline,turns,seal)}
