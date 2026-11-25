"""Independent source-bound neural studio candidate.

Only the current speaker uses an animated model clip. Optional listener
portrait framing simulates movement, not facial reactions or lip sync.
"""
import shutil
import tempfile
from pathlib import Path
from . import projects, source, characters, media, studio_camera, studio_listeners, studio_transition, studio_preview as studio
from . import v4_export as export, v4_neural as neural, v4_preview as preview, v4_master as master
from . import v4_final_review as review
from .render_progress import RenderProgress,RenderStopped

FOLDER="neural-studio"
VIDEO="studio-neural.mp4"
SRT="studio-neural.srt"
REVIEW="studio-neural-review.json"
ACK="I_WATCHED_AND_REVIEWED_THE_ENTIRE_CURRENT_NEURAL_STUDIO"


def _context(root,pid,*,allow_fixture=False):
    folder,dest,timeline,turns,cast,rows,done,bound=export._context(root,pid,allow_fixture=allow_fixture)
    settings,background=studio._read(folder)
    seal=bound["neural_binding"]["preview_inputs"]
    if settings["request_sha256"]!=seal["binding"]["request_sha256"]:raise ValueError("Studio request changed")
    binding={"neural_export_inputs":bound,"studio_settings_sha256":source.json_digest(settings),
             "video_format":seal["video_format"],"test_fixture_only":bound["test_fixture_only"]}
    if settings.get("listener_motion","static")!="static" and len(cast["cast"])>1:
        binding["listener_motion"]=settings["listener_motion"]
    if settings.get("transition","cut")!="cut":binding["transition"]=settings["transition"]
    return folder,dest,timeline,turns,cast,rows,done,binding,settings,background


def _portraits(root,cast):
    portraits={};speakers={}
    for index,row in enumerate(cast["cast"],1):
        record=characters.read(root,row["character_id"])
        if source.json_digest(record)!=row["record_sha256"]:raise ValueError("Studio cast changed")
        raw=characters._read_file(characters._profile_folder(root,row["character_id"])/characters.PORTRAIT,characters.MAX_PORTRAIT)
        if characters._portrait_info(raw)!=record["portrait"]:raise ValueError("Studio portrait changed")
        portraits[index]=raw;speakers[row["speaker"]]=index
    return portraits,speakers


def _segments(root,dest,cast,done,binding,settings,background,plan,temp,*,tracker=None):
    size=preview.SIZES[binding["video_format"]]
    portraits,speakers=_portraits(root,cast);cards={}
    names=[f"segment{i:05}.mp4" for i in range(len(plan))]
    starts=list(studio_camera.offsets(plan))
    transition_mode=settings.get("transition","cut")
    transitions=studio_transition.schedule(plan,transition_mode)
    deferred=set(transitions) if transition_mode in studio_transition.MATCH_MODES else set()
    # Render both neighboring speech segments before their endpoint-matched pause.
    order=[i for i in range(len(plan)) if i not in deferred]+sorted(deferred)
    def get_card(active,pause):
        key=(active,pause)
        if key not in cards:
            card=temp/f"card-{active:02}-{int(pause)}.png"
            studio.card(portraits,active,size,settings["layout"],background,neural=True,pause=pause,listener_motion=settings.get("listener_motion","static")!="static" and len(portraits)>1).save(card,"PNG")
            cards[key]=card
        return cards[key]
    for i in order:
        if tracker is not None:tracker.checkpoint()
        seg=plan[i]
        active=speakers[seg["speaker"]];pause=seg["kind"]=="pause"
        if i in deferred:
            spec=transitions[i]
            inputs=["-i",str(temp/names[i-1]),"-i",str(temp/names[i+1])]
            vf=studio_transition.endpoint_graph(plan[i-1]["frames"],seg["frames"],spec["start"],spec["frames"])
            filters=["-filter_complex_threads","1","-filter_complex",vf,"-map","[out]"]
        elif pause:
            inputs=["-loop","1","-framerate","25","-i",str(get_card(active,pause))]
            if i in transitions:
                spec=transitions[i]
                incoming=get_card(speakers[spec["to"]],True)
                inputs+=["-loop","1","-framerate","25","-i",str(incoming)]
                vf=studio_transition.filter_graph(seg["frames"],spec["start"],spec["frames"])
                filters=["-filter_complex_threads","1","-filter_complex",vf,"-map","[out]"]
            else:filters=["-map","0:v:0","-vf","fps=25,setsar=1,format=yuv420p"]
        else:
            inputs=["-loop","1","-framerate","25","-i",str(get_card(active,pause))]
            cid=seg["id"];clip=dest/neural.FOLDER/cid/"face.mp4"
            projects._plain(clip,directory=False)
            if source.digest(clip)!=done[cid]["mp4_sha256"]:raise ValueError("Studio clip changed")
            inputs+=["-i",str(clip)]
            x,y,w,h=studio.active_rect(portraits,active,size,settings["layout"])
            camera=studio_camera.filter_suffix(settings.get("camera","fixed"),w,h,seg["frames"],start_frame=starts[i])
            listener_mode=settings.get("listener_motion","static")
            rects=studio_listeners.regions(studio.geometry(portraits,active,size,settings["layout"]),active,size) if listener_mode!="static" else {}
            layers,base=studio_listeners.graph(rects,listener_mode,seg["frames"],starts[i])
            vf=(f"[1:v]fps=25,scale={w}:{h}:force_original_aspect_ratio=decrease:force_divisible_by=2,"
                f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1{camera},tpad=stop_mode=clone:stop_duration=1[face];"
                f"{base}[face]overlay={x}:{y}:shortest=1:repeatlast=0,format=yuv420p[out]")
            if layers:vf=";".join(layers+[vf])
            filters=["-filter_complex_threads","1","-filter_complex",vf,"-map","[out]"]
        path=temp/names[i]
        media.cmd(["ffmpeg","-nostdin","-hide_banner","-v","error",*inputs,*filters,"-an",
                   "-frames:v",str(seg["frames"]),"-c:v","libx264","-threads","2","-preset","veryfast","-crf","23",str(path)],
                  timeout=max(120,seg["frames"]*2))
        if export._video_frames(path)!=seg["frames"]:raise ValueError("Studio segment frame count differs")
        if tracker is not None:tracker.segment(i)
    listing=temp/"segments.ffconcat"
    listing.write_text("ffconcat version 1.0\n"+"".join("file "+n+"\n" for n in names),encoding="ascii")
    return listing


def _decode(path,timeline,binding,plan):
    streams=preview._decode(path,timeline,binding)
    count=export._video_frames(path)
    if count!=sum(r["frames"] for r in plan):raise ValueError("Neural studio frame count differs")
    return {**streams,"decoded_video_frames":count}


def _receipt(path,timeline,binding,plan,streams):
    result={"schema":1,"binding":binding,"frame_plan_sha256":source.json_digest(plan),
            "video_sha256":source.digest(path/VIDEO),"srt_sha256":source.digest(path/SRT),
            "streams":streams,"turn_count":len(timeline["rows"]),"test_fixture_only":binding["test_fixture_only"],
            "inactive_presenters_static":"listener_motion" not in binding,"human_lipsync_approved":False,"publication_approved":False}
    if "transition" in binding:
        result["pause_handoff_count"]=len(studio_transition.schedule(plan,binding["transition"]))
    return result


def _audit(dest,timeline,turns,binding,plan):
    out=dest/FOLDER;projects._plain(out)
    if {p.name for p in out.iterdir()}!={VIDEO,SRT,"receipt.json"}:raise ValueError("Incomplete neural studio")
    for name in (VIDEO,SRT,"receipt.json"):projects._plain(out/name,directory=False)
    if characters._read_file(out/SRT,2_000_000)!=preview.subtitles(timeline,turns):raise ValueError("Neural studio subtitles differ")
    saved=source.read_json(out/"receipt.json",64000)
    if saved.get("video_sha256")!=source.digest(out/VIDEO):raise ValueError("Neural studio video hash differs")
    expected=_receipt(out,timeline,binding,plan,_decode(out/VIDEO,timeline,binding,plan))
    if saved!=expected:raise ValueError("Neural studio receipt differs")
    return expected


def compose(root,pid,*,allow_fixture=False,progress=None,should_stop=None):
    folder=projects.project(root,pid)
    with projects.exclusive(folder):
        ctx=_context(root,pid,allow_fixture=allow_fixture)
        _,dest,timeline,turns,cast,rows,done,binding,settings,background=ctx
        plan=export.frame_plan(timeline,rows);out=dest/FOLDER
        if out.exists() or out.is_symlink():
            if progress is not None:progress({"action":"studio-existing-audit","completed_actions":0,"action_limit":1,"stop_allowed":False})
            if should_stop is not None and should_stop():raise RenderStopped("Studio audit stopped before existing candidate verification")
            result={"project_id":pid,"studio":_audit(dest,timeline,turns,binding,plan)}
            if progress is not None:progress({"action":"studio-audit-complete","completed_actions":1,"action_limit":1,"stop_allowed":False})
            return result
        tracker=RenderProgress(plan,progress,should_stop) if progress is not None or should_stop is not None else None
        seconds=timeline["measured_audio_seconds"]
        if shutil.disk_usage(folder).free<max(100*1024**2,int(seconds*2_000_000)):raise ValueError("Insufficient studio disk space")
        if tracker is not None:tracker.begin()
        with tempfile.TemporaryDirectory(prefix="v4-neural-studio-",dir=folder) as tmp:
            temp=Path(tmp)
            listing=_segments(root,dest,cast,done,binding,settings,background,plan,temp,**({"tracker":tracker} if tracker is not None else {}))
            if tracker is not None:tracker.checkpoint()
            staged=temp/VIDEO
            media.cmd(["ffmpeg","-nostdin","-hide_banner","-v","error","-f","concat","-safe","1","-i",str(listing),
                       "-i",str(dest/master.FOLDER/master.WAV),"-map","0:v:0","-map","1:a:0","-c:v","copy",
                       "-c:a","aac","-ar","48000","-b:a","160k","-movflags","+faststart",str(staged)],timeout=max(300,int(seconds*8)))
            streams=_decode(staged,timeline,binding,plan)
            if tracker is not None:tracker.muxed()
            if _context(root,pid,allow_fixture=allow_fixture)!=ctx:raise ValueError("Neural studio inputs changed")
            if tracker is not None:tracker.committing()
            out.mkdir()
            with staged.open("rb") as inp,(out/VIDEO).open("xb") as h:shutil.copyfileobj(inp,h)
            with (out/SRT).open("xb") as h:h.write(preview.subtitles(timeline,turns))
            source.atomic_json(out/"receipt.json",_receipt(out,timeline,binding,plan,streams),new=True)
        result={"project_id":pid,"studio":_audit(dest,timeline,turns,binding,plan)}
        if tracker is not None:tracker.finished()
        return result


def inspect(root,pid,*,allow_fixture=False):
    _,dest,timeline,turns,cast,rows,done,binding,settings,background=_context(root,pid,allow_fixture=allow_fixture)
    return {"project_id":pid,"studio":_audit(dest,timeline,turns,binding,export.frame_plan(timeline,rows))}


def _qa_context(root,pid):
    folder,dest,timeline,turns,cast,rows,done,binding,settings,background=_context(root,pid)
    receipt=_audit(dest,timeline,turns,binding,export.frame_plan(timeline,rows))
    return folder,dest,receipt,turns


def _read_review(dest,receipt,turns):
    path=dest/REVIEW
    if not path.exists() and not path.is_symlink():return None
    projects._plain(path,directory=False)
    saved=source.read_json(path,2_000_000)
    if set(saved)!={"observations","observations_sha256","acknowledgment"} or saved["acknowledgment"]!=ACK:
        raise ValueError("Invalid studio review receipt")
    value=review._validate(saved["observations"],receipt,turns)
    if source.json_digest(value)!=saved["observations_sha256"]:raise ValueError("Studio review hash differs")
    return saved


def qa(root,pid,operation,*,acknowledgment=None,input_file=None):
    if operation=="status":
        _,dest,receipt,turns=_qa_context(root,pid)
        return review._summary(pid,receipt,_read_review(dest,receipt,turns))
    if operation not in ("template","record"):raise ValueError("Unknown studio review operation")
    folder=projects.project(root,pid)
    with projects.exclusive(folder):
        _,dest,receipt,turns=_qa_context(root,pid)
        if _read_review(dest,receipt,turns) is not None:raise ValueError("Immutable studio review already recorded")
        sha=source.json_digest(receipt);path=folder/("studio-neural-review-"+sha+".json")
        if operation=="template":
            value={"schema":1,"candidate_sha256":sha,"turns":{t["id"]:{k:"UNREVIEWED" for k in review.CRITERIA} for t in turns},
                   "criteria":{k:"UNREVIEWED" for k in review.GLOBAL}}
            source.atomic_json(path,value,new=True)
            return {"project_id":pid,"template_path":str(path),"video_path":str(dest/FOLDER/VIDEO),"subtitle_path":str(dest/FOLDER/SRT)}
        if acknowledgment!=ACK:raise ValueError("Explicit full studio viewing acknowledgment required")
        if input_file is None:
            projects._plain(path,directory=False)
            data=source.read_json(path,2_000_000)
        else:
            from .visual_media_review import read_input
            data=read_input(input_file,2_000_000)
        value=review._validate(data,receipt,turns)
        saved={"observations":value,"observations_sha256":source.json_digest(value),"acknowledgment":ACK}
        source.atomic_json(dest/REVIEW,saved,new=True)
        return review._summary(pid,receipt,saved)
