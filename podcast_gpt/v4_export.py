"""Compose current reviewed neural clips against the original measured master.

No model audio is used. Structural media audit is not independent lip-sync,
identity, speech fidelity, rights, or publication approval.
"""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from . import characters, media, projects, source, v4_master, v4_neural as neural, v4_preview

FOLDER="neural-export"
VIDEO="episode.mp4"
SRT="episode.srt"
RECEIPT="receipt.json"
FPS=25
RATE=16000


def _context(root,pid,*,allow_fixture=False):
    if type(allow_fixture) is not bool:raise ValueError("Fixture export override must be boolean")
    folder,dest,binding,rows,targets=neural._context(root,pid)
    done=neural._scan(dest,binding,rows)
    if len(done)!=len(rows):raise ValueError("Complete every verified neural chunk before export")
    pilot=neural._review(dest,binding,targets,done)
    if not neural._passed(pilot):raise ValueError("All presenter pilots require explicit PASS before export")
    fixture=any(r["test_fixture_only"] for r in done.values())
    if fixture and not allow_fixture:raise ValueError("Synthetic fixture clips cannot be exported as production media")
    _,current_dest,timeline,turns,cast,seal=v4_preview._context(root,pid)
    if current_dest!=dest or seal!=binding["preview_inputs"]:raise ValueError("Current export inputs changed")
    bound={"neural_binding":binding,"pilot_review_sha256":source.json_digest(pilot),
           "clip_receipts_sha256":source.json_digest(done),"test_fixture_only":fixture}
    return folder,dest,timeline,turns,cast,rows,done,bound


def frame_plan(timeline,rows):
    """Integer sample positions -> cumulative nearest frame boundaries."""
    groups={r["turn_id"]:[] for r in timeline["rows"]}
    for row in rows:groups[row["turn_id"]].append(row)
    segments=[];samples=0;frames=0
    def add(kind,identifier,turn_id,speaker,count):
        nonlocal samples,frames
        if type(count) is not int or count<=0:raise ValueError("Invalid export sample range")
        samples+=count
        end=(samples*FPS+RATE//2)//RATE
        n=end-frames
        if n<1:raise ValueError("Sub-frame segment cannot be exported")
        segments.append({"kind":kind,"id":identifier,"turn_id":turn_id,"speaker":speaker,"frames":n})
        frames=end
    if timeline["sample_rate"]!=RATE:raise ValueError("Unexpected timeline sample rate")
    for turn in timeline["rows"]:
        if samples!=turn["start_frame"]:raise ValueError("Timeline has a gap")
        offset=0
        for row in groups[turn["turn_id"]]:
            if row["start_frame"]!=offset or row["speaker"]!=turn["speaker"]:raise ValueError("Chunk plan is not contiguous")
            add("speech",row["id"],turn["turn_id"],turn["speaker"],row["end_frame"]-offset)
            offset=row["end_frame"]
        if samples!=turn["speech_end_frame"]:raise ValueError("Incomplete speech segment coverage")
        if turn["pause_frames"]:
            add("pause",turn["turn_id"],turn["turn_id"],turn["speaker"],turn["pause_frames"])
        if samples!=turn["end_frame"]:raise ValueError("Pause coverage differs")
    if samples!=timeline["total_frames"] or not segments:raise ValueError("Incomplete final frame plan")
    return segments


def _video_frames(path):
    probe=json.loads(media.cmd(["ffprobe","-v","error","-select_streams","v:0",
        "-count_frames","-show_entries","stream=nb_read_frames","-of","json",str(path)],timeout=300).stdout)
    streams=probe.get("streams",[])
    if len(streams)!=1:raise ValueError("Expected one counted video stream")
    try:n=int(streams[0]["nb_read_frames"])
    except (KeyError,ValueError,TypeError):raise ValueError("Unable to count actual video frames") from None
    return n


def _decode(path,timeline,bound,plan):
    seal=bound["neural_binding"]["preview_inputs"]
    measured=v4_preview._decode(path,timeline,seal)
    n=_video_frames(path)
    if n!=sum(r["frames"] for r in plan):raise ValueError("Final frame count differs from measured timeline")
    return {**measured,"decoded_video_frames":n}


def _receipt(path,timeline,bound,plan,streams):
    return {"schema":1,"binding":bound,"frame_plan_sha256":source.json_digest(plan),
            "video_sha256":source.digest(path/VIDEO),"srt_sha256":source.digest(path/SRT),
            "measured_streams":streams,"turn_count":len(timeline["rows"]),
            "status":"synthetic_fixture_export_not_real_model" if bound["test_fixture_only"] else "neural_episode_candidate_pending_full_human_review",
            "test_fixture_only":bound["test_fixture_only"],"human_lipsync_approved":False,"publication_approved":False}


def _audit(dest,timeline,turns,bound,plan):
    path=dest/FOLDER;projects._plain(path)
    if {p.name for p in path.iterdir()}!={VIDEO,SRT,RECEIPT}:raise ValueError("Incomplete neural export; inspect privately")
    for name in (VIDEO,SRT,RECEIPT):projects._plain(path/name,directory=False)
    if characters._read_file(path/SRT,2_000_000)!=v4_preview.subtitles(timeline,turns):
        raise ValueError("Neural export subtitle content differs")
    saved=source.read_json(path/RECEIPT,64000)
    if saved.get("video_sha256")!=source.digest(path/VIDEO):raise ValueError("Neural export video hash differs")
    measured=_decode(path/VIDEO,timeline,bound,plan)
    expected=_receipt(path,timeline,bound,plan,measured)
    if saved!=expected:raise ValueError("Neural export receipt differs")
    return expected


def _segments(root,dest,cast,rows,done,bound,plan,temp):
    w,h=v4_preview.SIZES[bound["neural_binding"]["preview_inputs"]["video_format"]]
    members={r["speaker"]:r for r in cast["cast"]}
    lookup={r["id"]:r for r in rows}
    cards={}
    paths=[]
    for i,seg in enumerate(plan):
        path=temp/f"segment{i:05}.mp4"
        if seg["kind"]=="speech":
            cid=seg["id"];row=lookup[cid]
            original=dest/neural.FOLDER/cid/"face.mp4"
            projects._plain(original,directory=False)
            if source.digest(original)!=done[cid]["mp4_sha256"]:raise ValueError("Neural clip changed before composition")
            inputs=["-i",str(original)]
        else:
            speaker=seg["speaker"]
            if speaker not in cards:
                member=members[speaker];record=characters.read(root,member["character_id"])
                if source.json_digest(record)!=member["record_sha256"]:raise ValueError("Cast changed")
                raw=characters._read_file(characters._profile_folder(root,member["character_id"])/characters.PORTRAIT,characters.MAX_PORTRAIT)
                if neural._sha(raw)!=record["portrait"]["sha256"]:raise ValueError("Portrait changed")
                card=temp/f"pause{len(cards):02}.png"
                v4_preview._card(raw,len(cards)+1,(w,h),card)
                cards[speaker]=card
            inputs=["-loop","1","-framerate",str(FPS),"-i",str(cards[speaker])]
        # Fit, do not crop facial geometry. Pad short model tail by at most
        # one second; initial clip audit already restricts duration error.
        vf=f"scale={w}:{h}:force_original_aspect_ratio=decrease:force_divisible_by=2,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={FPS},tpad=stop_mode=clone:stop_duration=1,format=yuv420p"
        media.cmd(["ffmpeg","-nostdin","-hide_banner","-v","error",*inputs,
                   "-map","0:v:0","-an","-vf",vf,"-frames:v",str(seg["frames"]),
                   "-c:v","libx264","-threads","2","-preset","veryfast","-crf","23",str(path)],timeout=max(120,seg["frames"]*2))
        if _video_frames(path)!=seg["frames"]:raise ValueError("Normalized segment frame coverage differs")
        paths.append(path.name)
    listing=temp/"segments.ffconcat"
    listing.write_text("ffconcat version 1.0\n"+"".join("file "+name+"\n" for name in paths),encoding="ascii")
    return listing


def compose(root,pid,*,allow_fixture=False):
    folder=projects.project(root,pid)
    with projects.exclusive(folder):
        context=_context(root,pid,allow_fixture=allow_fixture)
        _,dest,timeline,turns,cast,rows,done,bound=context
        plan=frame_plan(timeline,rows)
        path=dest/FOLDER
        if path.exists() or path.is_symlink():return {"project_id":pid,"export":_audit(dest,timeline,turns,bound,plan)}
        seconds=timeline["measured_audio_seconds"]
        if shutil.disk_usage(folder).free<max(100*1024**2,int(seconds*2_000_000)):
            raise ValueError("Insufficient private disk space for neural composition")
        with tempfile.TemporaryDirectory(prefix="v4-neural-export-",dir=folder) as scratch:
            temp=Path(scratch)
            listing=_segments(root,dest,cast,rows,done,bound,plan,temp)
            staged=temp/VIDEO
            # Segments contain pixels only; the single audited master supplies audio.
            media.cmd(["ffmpeg","-nostdin","-hide_banner","-v","error","-f","concat","-safe","1","-i",str(listing),
                       "-i",str(dest/v4_master.FOLDER/v4_master.WAV),"-map","0:v:0","-map","1:a:0",
                       "-c:v","copy","-c:a","aac","-ar","48000","-b:a","160k","-movflags","+faststart",str(staged)],
                      timeout=max(300,int(seconds*8)))
            measured=_decode(staged,timeline,bound,plan)
            if _context(root,pid,allow_fixture=allow_fixture)!=context:raise ValueError("Neural export inputs changed during composition")
            path.mkdir()
            with staged.open("rb") as inp,(path/VIDEO).open("xb") as out:shutil.copyfileobj(inp,out)
            with (path/SRT).open("xb") as out:out.write(v4_preview.subtitles(timeline,turns))
            source.atomic_json(path/RECEIPT,_receipt(path,timeline,bound,plan,measured),new=True)
        return {"project_id":pid,"export":_audit(dest,timeline,turns,bound,plan)}


def inspect(root,pid,*,allow_fixture=False):
    _,dest,timeline,turns,cast,rows,done,bound=_context(root,pid,allow_fixture=allow_fixture)
    return {"project_id":pid,"export":_audit(dest,timeline,turns,bound,frame_plan(timeline,rows))}
