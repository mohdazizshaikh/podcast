"""Separate mixed-audio candidate, exact subtitle offsets and fresh QA.

The original speech-only candidate and all prior approvals remain untouched.
"""
from __future__ import annotations
import shutil
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from . import projects, source, characters, media, v4_post_audio as mix
from . import v4_export as export, v4_preview as preview
from .render_progress import RenderProgress,RenderStopped,mixed_scenes

FOLDER="mixed-export"
VIDEO="episode-mixed.mp4"
SRT="episode-mixed.srt"
RECEIPT="receipt.json"
STUDIO_FOLDER="mixed-neural-studio"
STUDIO_REVIEW="mixed-neural-studio-review.json"
STUDIO_ACK="I_WATCHED_THE_ENTIRE_CURRENT_MIXED_NEURAL_STUDIO"
MIX_REVIEW="mix-listening-review.json"
VIDEO_REVIEW="mixed-video-review.json"
MIX_ACK="I_LISTENED_TO_THE_ENTIRE_CURRENT_MIX"
VIDEO_ACK="I_WATCHED_THE_ENTIRE_CURRENT_MIXED_EPISODE"
AUDIO_CRITERIA=("speech_clarity","music_balance","intro_outro","timing","audio_rights")
VIDEO_CRITERIA=("lip_sync","identity","audio","subtitles","transitions")
GLOBAL=("complete_episode","intro_outro","overall_quality","usage_rights")


def _mix_context(root,pid):
    folder,dest,binding,timeline,master=mix._ctx(root,pid)
    receipt=mix._audit(dest,binding,timeline,master)
    return folder,dest,timeline,receipt


def _review_value(receipt,timeline,kind):
    return {"schema":1,"kind":kind,"candidate_sha256":source.json_digest(receipt),
            "turns":{r["turn_id"]:("UNREVIEWED" if kind=="mix" else {k:"UNREVIEWED" for k in VIDEO_CRITERIA}) for r in timeline["rows"]},
            "criteria":{k:"UNREVIEWED" for k in (AUDIO_CRITERIA if kind=="mix" else GLOBAL)}}


def _validate(value,receipt,timeline,kind):
    expected=_review_value(receipt,timeline,kind)
    if not isinstance(value,dict) or set(value)!=set(expected) or any(value[k]!=expected[k] for k in ("schema","kind","candidate_sha256")):
        raise ValueError("Review candidate binding differs")
    if not isinstance(value["turns"],dict) or set(value["turns"])!=set(expected["turns"]):
        raise ValueError("Review all turns")
    if not isinstance(value["criteria"],dict) or set(value["criteria"])!=set(expected["criteria"]):
        raise ValueError("Review all criteria")
    decisions=list(value["criteria"].values())
    for row in value["turns"].values():
        if kind=="mix":decisions.append(row)
        else:
            if not isinstance(row,dict) or set(row)!=set(VIDEO_CRITERIA):raise ValueError("Review all video criteria per turn")
            decisions.extend(row.values())
    if any(v not in ("PASS","FAIL") for v in decisions):raise ValueError("Complete all PASS/FAIL decisions, not UNREVIEWED")
    return all(v=="PASS" for v in decisions)


def _review_file(dest,kind):
    return dest/{"mix":MIX_REVIEW,"video":VIDEO_REVIEW,"studio":STUDIO_REVIEW}[kind]


def _read_review(dest,receipt,timeline,kind):
    path=_review_file(dest,kind)
    if not path.exists() and not path.is_symlink():return None,False
    projects._plain(path,directory=False)
    data=source.read_json(path,2_000_000)
    ack={"mix":MIX_ACK,"video":VIDEO_ACK,"studio":STUDIO_ACK}[kind]
    if set(data)!={"observations","sha256","acknowledgment"} or data["acknowledgment"]!=ack or data["sha256"]!=source.json_digest(data["observations"]):
        raise ValueError("Review receipt differs")
    return data,_validate(data["observations"],receipt,timeline,kind)


def _frames(samples):
    return (samples*export.FPS+export.RATE//2)//export.RATE


def scene_plan(timeline,record):
    before=record["intro_frames"];after=record["outro_frames"];speech=timeline["total_frames"]
    if record["speech_offset_frames"]!=before or record["speech_and_pauses_frames"]!=speech or record["total_frames"]!=before+speech+after:
        raise ValueError("Mixed audio duration binding differs")
    # The existing neural video is kept at its exact decoded frame count.
    # Round intro start to nearest frame, adjust only outro (or final held
    # frame when no outro) for cumulative nearest-frame total.
    start=_frames(before);body=_frames(speech);total=_frames(before+speech+after)
    if before and start<1:raise ValueError("Intro shorter than one video frame")
    if not after:
        tail=total-start-body
        if tail not in (-1,0,1):raise ValueError("Unexpected frame rounding")
        body+=tail
    end=total-start-body
    if body<1 or end<0 or (after and end<1):raise ValueError("Invalid mixed scene duration")
    return {"intro_frames":start,"speech_frames":body,"outro_frames":end,"total_video_frames":total,
            "speech_offset_samples":before,"sample_rate":export.RATE,"fps":export.FPS}


def shifted_subtitles(timeline,turns,offset):
    rows=[{**r,"start_frame":r["start_frame"]+offset,"speech_end_frame":r["speech_end_frame"]+offset} for r in timeline["rows"]]
    return preview.subtitles({**timeline,"rows":rows},turns)


def _context(root,pid,*,allow_fixture=False,studio=False):
    folder,dest,timeline,record=_mix_context(root,pid)
    reviewed,passed=_read_review(dest,record,timeline,"mix")
    if not passed:raise ValueError("Current mix requires explicit listening PASS")
    if studio:
        from . import studio_neural as sn
        _,base_dest,base_timeline,turns,cast,rows,done,bound,settings,background=sn._context(root,pid,allow_fixture=allow_fixture)
        if base_dest!=dest or timeline!=base_timeline:raise ValueError("Mixed studio source mismatch")
        base=sn._audit(dest,timeline,turns,bound,export.frame_plan(timeline,rows))
        fmt=bound["video_format"]
    else:
        _,base_dest,base_timeline,turns,cast,rows,done,bound=export._context(root,pid,allow_fixture=allow_fixture)
        if base_dest!=dest or timeline!=base_timeline:raise ValueError("Mixed video source mismatch")
        base=export._audit(dest,timeline,turns,bound,export.frame_plan(timeline,rows))
        fmt=bound["neural_binding"]["preview_inputs"]["video_format"]
    plan=scene_plan(timeline,record)
    seal={"base_export_sha256":source.json_digest(base),"mix_sha256":source.json_digest(record),
          "mix_review_sha256":source.json_digest(reviewed),"video_format":fmt,
          "test_fixture_only":base["test_fixture_only"]}
    if studio:seal["variant"]="neural-studio"
    return folder,dest,timeline,turns,record,plan,seal


def _decode(path,record,plan,seal):
    streams=preview._decode(path,{"measured_audio_seconds":record["total_frames"]/export.RATE},seal)
    n=export._video_frames(path)
    if n!=plan["total_video_frames"]:raise ValueError("Mixed video frame count differs")
    return {**streams,"decoded_video_frames":n}


def _receipt(path,plan,seal,streams):
    return {"schema":1,"binding":seal,"scene_plan":plan,"streams":streams,
            "video_sha256":source.digest(path/VIDEO),"srt_sha256":source.digest(path/SRT),
            "test_fixture_only":seal["test_fixture_only"],"human_mixed_video_approved":False,"publication_approved":False}


def _audit(dest,timeline,turns,record,plan,seal):
    out=dest/(STUDIO_FOLDER if seal.get("variant")=="neural-studio" else FOLDER);projects._plain(out)
    if {p.name for p in out.iterdir()}!={VIDEO,SRT,RECEIPT}:raise ValueError("Incomplete mixed export")
    for name in (VIDEO,SRT,RECEIPT):projects._plain(out/name,directory=False)
    if characters._read_file(out/SRT,2_000_000)!=shifted_subtitles(timeline,turns,plan["speech_offset_samples"]):
        raise ValueError("Mixed subtitle timing or content differs")
    saved=source.read_json(out/RECEIPT,64000)
    if saved.get("video_sha256")!=source.digest(out/VIDEO):raise ValueError("Mixed video hash differs")
    expected=_receipt(out,plan,seal,_decode(out/VIDEO,record,plan,seal))
    if expected!=saved:raise ValueError("Mixed export receipt differs")
    return expected


def _card(path,size,label):
    w,h=size
    im=Image.new("RGB",size,(17,24,39));draw=ImageDraw.Draw(im)
    draw.text((w//2,h//2),"PODCAST GPT",font=ImageFont.load_default(size=42),anchor="mm",fill=(240,245,250))
    draw.text((w//2,h//2+65),label,font=ImageFont.load_default(size=26),anchor="mm",fill=(155,190,225))
    im.save(path,"PNG")


def compose(root,pid,*,allow_fixture=False,studio=False,progress=None,should_stop=None):
    folder=projects.project(root,pid)
    with projects.exclusive(folder):
        if should_stop is not None and should_stop():raise RenderStopped("Mixed render stopped before candidate preparation")
        ctx=_context(root,pid,allow_fixture=allow_fixture,studio=studio)
        _,dest,timeline,turns,record,plan,seal=ctx
        out=dest/(STUDIO_FOLDER if studio else FOLDER)
        if studio:
            from . import studio_neural as sn
            base_path=dest/sn.FOLDER/sn.VIDEO
        else:base_path=dest/export.FOLDER/export.VIDEO
        if out.exists() or out.is_symlink():
            if progress is not None:progress({"action":"mixed-existing-audit","completed_actions":0,"action_limit":1,"stop_allowed":False})
            if should_stop is not None and should_stop():raise RenderStopped("Mixed audit stopped before existing candidate verification")
            result={"project_id":pid,"export":_audit(dest,timeline,turns,record,plan,seal)}
            if progress is not None:progress({"action":"mixed-audit-complete","completed_actions":1,"action_limit":1,"stop_allowed":False})
            return result
        scenes=mixed_scenes(plan)
        tracker=RenderProgress([{"frames":n} for _,n in scenes],progress,should_stop,label="mixed",estimate_segments=False) if progress is not None or should_stop is not None else None
        seconds=record["total_frames"]/export.RATE
        if shutil.disk_usage(folder).free<max(100*1024**2,int(seconds*2_000_000)):raise ValueError("Insufficient private disk space")
        if tracker is not None:tracker.begin()
        with tempfile.TemporaryDirectory(prefix="v4-mixed-",dir=folder) as tmp:
            temp=Path(tmp);segments=[]
            for index,(kind,count) in enumerate(scenes):
                if tracker is not None:tracker.checkpoint()
                target=temp/(kind+".mp4")
                if kind=="speech":inputs=["-i",str(base_path)]
                else:
                    card=temp/(kind+".png");_card(card,preview.SIZES[seal["video_format"]],kind.upper())
                    inputs=["-loop","1","-framerate","25","-i",str(card)]
                media.cmd(["ffmpeg","-nostdin","-hide_banner","-v","error",*inputs,"-map","0:v:0","-an",
                    "-vf","fps=25,setsar=1,tpad=stop_mode=clone:stop_duration=1,format=yuv420p",
                    "-frames:v",str(count),"-c:v","libx264","-threads","2","-preset","veryfast","-crf","23",str(target)],
                    timeout=max(120,count*2))
                if export._video_frames(target)!=count:raise ValueError("Mixed scene frame coverage differs")
                segments.append(target.name)
                if tracker is not None:tracker.segment(index)
            if tracker is not None:tracker.checkpoint()
            listing=temp/"scenes.ffconcat";listing.write_text("ffconcat version 1.0\n"+"".join("file "+p+"\n" for p in segments),encoding="ascii")
            staged=temp/VIDEO
            media.cmd(["ffmpeg","-nostdin","-hide_banner","-v","error","-f","concat","-safe","1","-i",str(listing),
                       "-i",str(dest/mix.FOLDER/mix.WAV),"-map","0:v:0","-map","1:a:0","-c:v","copy",
                       "-c:a","aac","-ar","48000","-b:a","160k","-movflags","+faststart",str(staged)],timeout=max(300,int(seconds*8)))
            streams=_decode(staged,record,plan,seal)
            if tracker is not None:tracker.muxed()
            if _context(root,pid,allow_fixture=allow_fixture,studio=studio)!=ctx:raise ValueError("Mixed inputs changed during export")
            if tracker is not None:tracker.committing()
            out.mkdir()
            with staged.open("rb") as inp,(out/VIDEO).open("xb") as handle:shutil.copyfileobj(inp,handle)
            with (out/SRT).open("xb") as handle:handle.write(shifted_subtitles(timeline,turns,plan["speech_offset_samples"]))
            source.atomic_json(out/RECEIPT,_receipt(out,plan,seal,streams),new=True)
        result={"project_id":pid,"export":_audit(dest,timeline,turns,record,plan,seal)}
        if tracker is not None:tracker.finished()
        return result


def inspect(root,pid,*,allow_fixture=False,studio=False):
    _,dest,timeline,turns,record,plan,seal=_context(root,pid,allow_fixture=allow_fixture,studio=studio)
    return {"project_id":pid,"export":_audit(dest,timeline,turns,record,plan,seal)}


def _qa_context(root,pid,kind):
    if kind=="mix":
        folder,dest,timeline,receipt=_mix_context(root,pid)
        files=[str(dest/mix.FOLDER/mix.WAV)]
    elif kind in ("video","studio"):
        folder,dest,timeline,turns,record,plan,seal=_context(root,pid,studio=kind=="studio")
        receipt=_audit(dest,timeline,turns,record,plan,seal)
        out=dest/(STUDIO_FOLDER if kind=="studio" else FOLDER)
        files=[str(out/VIDEO),str(out/SRT)]
    else:raise ValueError("Unknown review kind")
    return folder,dest,timeline,receipt,files


def qa(root,pid,kind,operation,*,acknowledgment=None,input_file=None):
    folder=projects.project(root,pid)
    if operation=="status":
        _,dest,timeline,receipt,_=_qa_context(root,pid,kind)
        saved,passed=_read_review(dest,receipt,timeline,kind)
        return {"project_id":pid,"kind":kind,"review_status":"PASS" if passed else "FAIL" if saved else "UNREVIEWED","publication_approved":False}
    if operation not in ("template","record"):raise ValueError("Unknown review operation")
    with projects.exclusive(folder):
        _,dest,timeline,receipt,files=_qa_context(root,pid,kind)
        if _read_review(dest,receipt,timeline,kind)[0] is not None:raise ValueError("Immutable review already recorded")
        value=_review_value(receipt,timeline,kind)
        path=folder/("review-"+kind+"-"+value["candidate_sha256"]+".json")
        if operation=="template":
            source.atomic_json(path,value,new=True)
            return {"project_id":pid,"template_path":str(path),"media_paths":files,"review_status":"UNREVIEWED"}
        ack={"mix":MIX_ACK,"video":VIDEO_ACK,"studio":STUDIO_ACK}[kind]
        if acknowledgment!=ack:raise ValueError("Explicit full media review acknowledgment required")
        if input_file is None:
            projects._plain(path,directory=False)
            value=source.read_json(path,2_000_000)
        else:
            from .visual_media_review import read_input
            value=read_input(input_file,2_000_000)
        passed=_validate(value,receipt,timeline,kind)
        source.atomic_json(_review_file(dest,kind),{"observations":value,"sha256":source.json_digest(value),"acknowledgment":ack},new=True)
        return {"project_id":pid,"review_status":"PASS" if passed else "FAIL","publication_approved":False}
