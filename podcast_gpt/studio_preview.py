"""Optional authorized studio background and static cast layout preview.

Independent from existing static/neural candidates. No face segmentation,
animated camera, lip movement, or automatic quality approval.
"""
from __future__ import annotations
import io
import math
import shutil
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
from . import projects, characters, source, media, studio_camera, studio_layout, studio_listeners, v4_preview as preview, v4_master as master

CONFIG="studio-settings"
FOLDER="studio-preview"
ACK="I_HAVE_RIGHTS_TO_USE_THIS_STUDIO_BACKGROUND"
LAYOUTS=("focus","grid","spotlight")
VIDEO="studio.mp4"
SRT="studio.srt"


def _read(folder):
    path=folder/CONFIG;projects._plain(path)
    projects._plain(path/"settings.json",directory=False)
    data=source.read_json(path/"settings.json",32000)
    fields={"schema","layout","background","request_sha256"}
    if not isinstance(data,dict) or not fields<=set(data) or not set(data)<=fields|{"camera","listener_motion"} or data["schema"]!=1 or data["layout"] not in LAYOUTS:
        raise ValueError("Invalid studio settings")
    if "camera" in data and studio_camera.validate(data["camera"])=="fixed":raise ValueError("Fixed camera uses legacy studio settings")
    if "listener_motion" in data:
        if studio_listeners.validate(data["listener_motion"])=="static" or data["layout"]=="focus":raise ValueError("Invalid visible listener motion settings")
    expected={"settings.json"}
    raw=None
    if data["background"] is not None:
        expected.add("background.png")
        raw=characters._read_file(path/"background.png",characters.MAX_PORTRAIT)
        if characters._portrait_info(raw)!=data["background"]:raise ValueError("Studio background changed")
    if {p.name for p in path.iterdir()}!=expected:raise ValueError("Unexpected studio files")
    return data,raw


def configure(root,pid,*,layout,background=None,camera="fixed",listener_motion="static",acknowledgment=None):
    studio_camera.validate(camera)
    studio_listeners.validate(listener_motion)
    if listener_motion!="static" and layout=="focus":raise ValueError("Listener motion requires grid or spotlight layout")
    if layout not in LAYOUTS:raise ValueError("Choose focus, grid or spotlight studio layout")
    if background is not None and acknowledgment!=ACK:raise ValueError("Explicit background usage rights acknowledgment required")
    raw=characters._read_file(background,characters.MAX_PORTRAIT) if background is not None else None
    info=characters._portrait_info(raw) if raw is not None else None
    folder=projects.project(root,pid)
    with projects.exclusive(folder):
        req=projects.load(root,pid);path=folder/CONFIG
        if path.exists() or path.is_symlink():raise ValueError("Studio settings already exist; no overwrite")
        path.mkdir()
        if raw is not None:
            with (path/"background.png").open("xb") as h:h.write(raw)
        settings={"schema":1,"layout":layout,"background":info,"request_sha256":source.json_digest(req)}
        if camera!="fixed":settings["camera"]=camera
        if listener_motion!="static":settings["listener_motion"]=listener_motion
        source.atomic_json(path/"settings.json",settings,new=True)
        return inspect_settings(root,pid)


def inspect_settings(root,pid):
    folder=projects.project(root,pid);data,_=_read(folder)
    if data["request_sha256"]!=source.json_digest(projects.load(root,pid)):raise ValueError("Studio request changed")
    return {"project_id":pid,"settings":data,"settings_sha256":source.json_digest(data),"static_only":True}


def _context(root,pid):
    folder,dest,timeline,turns,cast,seal=preview._context(root,pid)
    settings,raw=_read(folder)
    if settings["request_sha256"]!=seal["binding"]["request_sha256"]:raise ValueError("Studio request binding changed")
    bound={**seal,"studio_settings_sha256":source.json_digest(settings)}
    return folder,dest,timeline,turns,cast,bound,settings,raw


def geometry(indices,active,size,layout):
    if layout=="spotlight":return studio_layout.spotlight(indices,active,size)
    if layout not in LAYOUTS:raise ValueError("Invalid studio layout")
    w,h=size
    chosen=list(indices) if layout=="grid" else [active]
    n=len(chosen)
    if not 1<=n<=10 or active not in chosen:raise ValueError("Invalid studio cast geometry")
    cols=(min(4,math.ceil(math.sqrt(n))) if w>=h else min(2,n)) if layout=="grid" else 1
    rows=math.ceil(n/cols);margin=20;top=70;bottom=h-52
    cellw=(w-margin*(cols+1))//cols
    cellh=(bottom-top-margin*(rows-1))//rows
    return {index:(margin+(i%cols)*(cellw+margin),top+(i//cols)*(cellh+margin),cellw,cellh)
            for i,index in enumerate(chosen)}


def active_rect(indices,active,size,layout):
    x,y,w,h=geometry(indices,active,size,layout)[active]
    # All video bounds are even for 4:2:0 encoding and inside the card.
    return ((x+9)//2*2,(y+7)//2*2,(w-16)//2*2,(h-36)//2*2)


def card(portraits,active,size,layout,background=None,*,neural=False,pause=False,listener_motion=False):
    w,h=size
    if background is not None:
        with Image.open(io.BytesIO(background)) as im:
            canvas=ImageOps.fit(im.convert("RGB"),size,method=Image.Resampling.LANCZOS)
        canvas=Image.blend(canvas,Image.new("RGB",size,(13,19,30)),.45)
    else:canvas=Image.new("RGB",size,(19,29,45))
    draw=ImageDraw.Draw(canvas)
    draw.text((w//2,22),"PODCAST STUDIO",anchor="mt",font=ImageFont.load_default(size=25),fill="white")
    for index,(x,y,cellw,cellh) in geometry(portraits,active,size,layout).items():
        selected=index==active
        draw.rounded_rectangle((x,y,x+cellw,y+cellh),radius=10,fill=(12,18,30),
            outline=(102,220,180) if selected else (120,135,155),width=5 if selected else 2)
        if not (neural and selected and not pause):
            with Image.open(io.BytesIO(portraits[index])) as im:
                pic=ImageOps.contain(im.convert("RGB"),(cellw-16,cellh-36),method=Image.Resampling.LANCZOS)
                canvas.paste(pic,(x+(cellw-pic.width)//2,y+6+(cellh-36-pic.height)//2))
        draw.text((x+cellw//2,y+cellh-8),f"Presenter {index:02}"+((" - pause" if pause else " - speaking") if selected else ""),
            anchor="mb",font=ImageFont.load_default(size=14 if cellw<300 else 20),fill="white")
    draw.text((w//2,h-12),(("NEURAL STUDIO - SIMULATED LISTENER MOTION" if listener_motion else "NEURAL STUDIO - STATIC LISTENERS") if neural else "STATIC STUDIO PREVIEW - NOT LIP SYNC"),anchor="mb",
              font=ImageFont.load_default(size=18),fill=(255,196,130))
    return canvas


def _listing(root,cast,timeline,seal,settings,background,temp):
    portraits={};speakers={}
    for i,row in enumerate(cast["cast"],1):
        record=characters.read(root,row["character_id"])
        if source.json_digest(record)!=row["record_sha256"]:raise ValueError("Studio cast changed")
        raw=characters._read_file(characters._profile_folder(root,row["character_id"])/characters.PORTRAIT,characters.MAX_PORTRAIT)
        if characters._portrait_info(raw)!=record["portrait"]:raise ValueError("Studio portrait changed")
        portraits[i]=raw;speakers[row["speaker"]]=i
    for i in portraits:
        card(portraits,i,preview.SIZES[seal["video_format"]],settings["layout"],background).save(temp/f"card{i:02}.png","PNG")
    lines=["ffconcat version 1.0"]
    for row in timeline["rows"]:
        lines.extend([f"file card{speakers[row['speaker']]:02}.png",f"duration {(row['end_frame']-row['start_frame'])/timeline['sample_rate']:.8f}"])
    lines.append(f"file card{speakers[timeline['rows'][-1]['speaker']]:02}.png")
    path=temp/"cards.ffconcat";path.write_text("\n".join(lines)+"\n",encoding="ascii")
    return path


def _receipt(out,timeline,seal,streams):
    return {"schema":1,"binding":seal,"video_sha256":source.digest(out/VIDEO),"srt_sha256":source.digest(out/SRT),
            "measured_streams":streams,"turn_count":len(timeline["rows"]),"static_only":True,
            "neural_lipsync_verified":False,"publication_approved":False}


def _audit(dest,timeline,turns,seal):
    out=dest/FOLDER;projects._plain(out)
    if {p.name for p in out.iterdir()}!={VIDEO,SRT,"receipt.json"}:raise ValueError("Incomplete studio preview")
    for name in (VIDEO,SRT,"receipt.json"):projects._plain(out/name,directory=False)
    if characters._read_file(out/SRT,2_000_000)!=preview.subtitles(timeline,turns):raise ValueError("Studio subtitles differ")
    saved=source.read_json(out/"receipt.json",32000)
    if saved.get("video_sha256")!=source.digest(out/VIDEO):raise ValueError("Studio video hash differs")
    expected=_receipt(out,timeline,seal,preview._decode(out/VIDEO,timeline,seal))
    if saved!=expected:raise ValueError("Studio receipt differs")
    return expected


def render(root,pid):
    folder=projects.project(root,pid)
    with projects.exclusive(folder):
        ctx=_context(root,pid);_,dest,timeline,turns,cast,seal,settings,background=ctx
        out=dest/FOLDER
        if out.exists() or out.is_symlink():return {"project_id":pid,"studio":_audit(dest,timeline,turns,seal)}
        seconds=timeline["measured_audio_seconds"]
        if shutil.disk_usage(folder).free<max(100*1024**2,int(seconds*500000)):raise ValueError("Insufficient private disk space")
        with tempfile.TemporaryDirectory(prefix="v4-studio-",dir=folder) as tmp:
            temp=Path(tmp);listing=_listing(root,cast,timeline,seal,settings,background,temp)
            staged=temp/VIDEO
            media.cmd(["ffmpeg","-nostdin","-hide_banner","-v","error","-f","concat","-safe","1","-i",str(listing),
                       "-i",str(dest/master.FOLDER/master.WAV),"-map","0:v:0","-map","1:a:0",
                       "-vf","fps=25,tpad=stop_mode=clone:stop_duration=1,format=yuv420p",
                       "-c:v","libx264","-threads","2","-preset","veryfast","-crf","25",
                       "-c:a","aac","-ar","48000","-b:a","128k","-movflags","+faststart","-t",f"{seconds:.8f}",str(staged)],
                       timeout=max(300,int(seconds*12)))
            streams=preview._decode(staged,timeline,seal)
            if _context(root,pid)!=ctx:raise ValueError("Studio inputs changed")
            out.mkdir()
            with staged.open("rb") as inp,(out/VIDEO).open("xb") as h:shutil.copyfileobj(inp,h)
            with (out/SRT).open("xb") as h:h.write(preview.subtitles(timeline,turns))
            source.atomic_json(out/"receipt.json",_receipt(out,timeline,seal,streams),new=True)
        return {"project_id":pid,"studio":_audit(dest,timeline,turns,seal)}


def inspect(root,pid):
    _,dest,timeline,turns,cast,seal,settings,background=_context(root,pid)
    return {"project_id":pid,"studio":_audit(dest,timeline,turns,seal)}
