"""Optional genuine local SadTalker CPU preview, resumable provenance and full composition.

No fake model, forced success, automatic model download, or portrait approval.
"""
from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

from .media import FPS, WIDTH, HEIGHT, cmd, streams, full_decode, original_audio, timeline, srt_stamp, subtitle, portrait_card
from .source import SPEAKERS, CHUNK_RE, atomic_json, digest, json_digest, read_json, verify_chunks, verify_source, workspace_path

LOCK = "cpu-neural-exclusive.lock"
CHECKPOINT = "cpu-neural-checkpoint.json"
MODEL_STATUS = "genuine_sadtalker_cpu_preview_structurally_decoded_pending_human_review"
MAX_BATCH = 5
MAX_SESSION = 20


def _clip_paths(root: Path, cid: str) -> tuple[Path,Path]:
    if not CHUNK_RE.fullmatch(cid):
        raise ValueError("Untrusted original speech chunk ID")
    return root/"previews"/(cid+".mp4"),root/"previews"/(cid+".json")


def _verify_model_clip(mp4:Path, seconds:float) -> dict:
    measured=full_decode(mp4,seconds=seconds)
    # A clip with ten seconds of AAC but only a fraction of a second of
    # face frames is NOT a real ten-second speaking face. FFprobe's format
    # duration alone would incorrectly accept it.
    if abs(measured["video_duration"]-seconds)>max(.45,.025*seconds):
        raise ValueError("Real facial video stream does not cover original Hindi PCM chunk")
    return measured


def verified_previews(root:Path,*, allow_short:bool=False) -> tuple[dict,dict]:
    """Always independent SHA/decoder check of every existing MP4+sidecar."""
    root=workspace_path(root)
    source=verify_chunks(root,allow_short=allow_short)
    all_rows={x["id"]:x for x in source["chunks"]}
    folder=root/"previews"
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError("Private face previews directory invalid")
    permissible={cid+suffix for cid in all_rows for suffix in (".mp4",".json")}
    for item in folder.iterdir():
        if item.is_symlink() or not item.is_file() or item.name not in permissible:
            raise ValueError("Unexpected/incomplete real model preview; manual review required")
    confirmed={}
    for cid,row in all_rows.items():
        mp4,report=_clip_paths(root,cid)
        if not mp4.exists() and not report.exists():continue
        if not mp4.is_file() or not report.is_file():
            raise ValueError("Orphan face MP4/JSON checkpoint")
        saved=read_json(report,100_000)
        expected={"schema":3,"status":MODEL_STATUS,"chunk_id":cid,"speaker":row["speaker"],
                  "chunk_sha256":row["chunk_sha256"],"portrait_sha256":row["portrait_sha256"],
                  "source_binding":source["source_binding"],
                  "authorized_portraits_self_attested":True,
                  "human_lipsync_approved":False,"full_ten_minute_neural_video_completed":False}
        if any(saved.get(k)!=v for k,v in expected.items()) or saved.get("mp4_sha256")!=digest(mp4):
            raise ValueError("Real neural preview SHA/speaker/source rights marker differs")
        media=_verify_model_clip(mp4,row["duration"])
        if abs(media["duration"]-row["duration"])>max(.45,.025*row["duration"]):
            raise ValueError("Neural clip voice timeline changed")
        confirmed[cid]=saved["mp4_sha256"]
    checkpoint=root/"source"/CHECKPOINT
    if checkpoint.is_symlink():
        raise ValueError("Checkpoint symlink refused")
    if checkpoint.exists():
        previous=read_json(checkpoint)
        if (previous.get("schema")!=3 or previous.get("source_binding")!=source["source_binding"]
                or not isinstance(previous.get("verified_previews"),dict)
                or any(confirmed.get(k)!=v for k,v in previous["verified_previews"].items())):
            raise ValueError("Saved CPU checkpoint disagrees with independently decoded MP4")
    return source,confirmed


def progress(root:Path,*,allow_short:bool=False) -> dict:
    manifest,done=verified_previews(root,allow_short=allow_short)
    missing=[x["id"] for x in manifest["chunks"] if x["id"] not in done]
    count={sp:0 for sp in SPEAKERS}
    for x in manifest["chunks"]:
        if x["id"] in done: count[x["speaker"]]+=1
    return {"status":"independently_verified_real_neural_preview_progress",
            "total":len(manifest["chunks"]),"verified":len(done),"remaining":len(missing),
            "by_speaker":count,"next_missing":missing[:5],
            "three_presenter_samples_ready":all(count.values()),
            "all_speech_neural_clips_structurally_present":not missing,
            "full_ten_minute_neural_video_completed":False,"human_lipsync_approved":False}


def pilot_targets(source:dict,done:dict) -> list[str]:
    result=[]
    for speaker in SPEAKERS:
        ids=[x["id"] for x in source["chunks"] if x["speaker"]==speaker]
        if not ids:raise ValueError("All three original Hindi presenters must speak")
        if not any(x in done for x in ids): result.append(ids[0])
    return result


def _model_call(root:Path,row:dict,*,sadtalker_root:Path,sadtalker_python:Path,
                timeout:int,allow_short:bool=False,model_runner=None) -> dict:
    """Real SadTalker model runs only after separate explicit owner confirmation.

    Injecting a runner exists solely for offline synthetic tests; no CLI route
    accepts a custom runner.
    """
    cid=row["id"]
    clip,sidecar=_clip_paths(root,cid)
    if clip.exists() or sidecar.exists():raise ValueError("Existing neural chunk cannot be overwritten")
    if digest(root/"chunks"/(cid+".wav"))!=row["chunk_sha256"] or digest(root/"portraits"/(row["speaker"]+".png"))!=row["portrait_sha256"]:
        raise ValueError("Original signed chunk/portrait changed before real model")
    scratch=root/"scratch"/("model-"+cid)
    scratch.mkdir(exist_ok=False,parents=True)
    started=time.monotonic()
    if model_runner is None:
        # CLI always uses real external inference and does not download model weights.
        if (not sadtalker_python.is_file() or not (sadtalker_root/"inference.py").is_file()
                or not (sadtalker_root/"checkpoints").is_dir()):
            raise ValueError("Local SadTalker Python/weights/inference.py not installed")
        args=[str(sadtalker_python),str(sadtalker_root/"inference.py"),
              "--driven_audio",str(root/"chunks"/(cid+".wav")),
              "--source_image",str(root/"portraits"/(row["speaker"]+".png")),
              "--result_dir",str(scratch),"--still","--preprocess","full","--cpu"]
        env=os.environ.copy();env["CUDA_VISIBLE_DEVICES"]=""
        result=subprocess.run(args,cwd=str(sadtalker_root),env=env,
                              capture_output=True,text=True,errors="replace",timeout=timeout)
        if result.returncode:
            raise RuntimeError("SadTalker CPU model failed; inspect scratch and local Python/checkpoints")
        output=list(scratch.rglob("*.mp4"))
        if len(output)!=1:raise ValueError("Expected ONE fresh pretrained face MP4 output")
        model_video=output[0]
    else:
        model_video=Path(model_runner(root,row,scratch,timeout))
    if not model_video.resolve().is_relative_to(scratch.resolve()):
        raise ValueError("Untrusted external/out-of-scratch model output")
    _verify_model_clip(model_video,row["duration"])
    # Long-running CPU call may have raced with modification of original source.
    verify_chunks(root,allow_short=allow_short)
    if digest(root/"portraits"/(row["speaker"]+".png"))!=row["portrait_sha256"]:
        raise ValueError("Creator image changed during neural inference")
    clip.parent.mkdir(exist_ok=True)
    staging=clip.with_name(clip.name+".part")
    if staging.exists():raise ValueError("Interrupted copied face clip requires manual inspection")
    shutil.copyfile(model_video,staging)
    if digest(staging)!=digest(model_video):raise ValueError("Copied model video differs")
    _verify_model_clip(staging,row["duration"])
    staging.replace(clip)
    bound=verify_chunks(root,allow_short=allow_short)
    report={"schema":3,"status":MODEL_STATUS,"chunk_id":cid,"speaker":row["speaker"],
            "chunk_sha256":row["chunk_sha256"],"portrait_sha256":row["portrait_sha256"],
            "source_binding":bound["source_binding"],"mp4_sha256":digest(clip),
            "actual_cpu_model_seconds":round(time.monotonic()-started,2),
            "authorized_portraits_self_attested":True,"human_lipsync_approved":False,
            "full_ten_minute_neural_video_completed":False}
    atomic_json(sidecar,report,new=True)
    # Cleanup only successful own scratch; interrupted scratch stays inspectable.
    shutil.rmtree(scratch)
    return report


def run_cpu(root:Path,*,mode:str,rights_confirmed:bool,max_new:int=3,
            wall_seconds:int=7200,per_chunk_timeout:int=1800,
            sadtalker_root:Path|None=None,sadtalker_python:Path|None=None,
            allow_short:bool=False,model_runner=None,clock=None) -> dict:
    """One bounded, serial, foreground opt-in run, always recheck checkpoints."""
    if rights_confirmed is not True:raise ValueError("Explicit human image rights YES required")
    if mode not in ("pilot","batch","session"):raise ValueError("Unsupported CPU session mode")
    if type(max_new) is not int or not 1<=max_new<=(3 if mode=="pilot" else MAX_BATCH if mode=="batch" else MAX_SESSION):
        raise ValueError("CPU preview exceeds bounded mode maximum")
    if mode=="pilot" and max_new!=3:raise ValueError("Three-presenter PILOT must cap at exactly 3")
    if (type(wall_seconds) is not int or not 300<=wall_seconds<=14400
            or type(per_chunk_timeout) is not int or not 120<=per_chunk_timeout<=7200):
        raise ValueError("CPU time budget is outside safe finite bounds")
    root=workspace_path(root)
    source,done=verified_previews(root,allow_short=allow_short)
    if model_runner is None:
        # Production CLI always preflights user-installed pretrained model
        # assets BEFORE taking a lock or initiating an expensive model run.
        from .model_preflight import inspect_sadtalker_installation
        inspect_sadtalker_installation(Path(sadtalker_root or ""),
                                       Path(sadtalker_python or ""))
    # Measure the ACTUAL private workspace volume, not the application repo.
    # A real pretrained model can create large temporary frames before its MP4.
    if shutil.disk_usage(root/"previews").free < 6*1024**3:
        raise ValueError("At least 6 GiB free on the private CPU model output drive is required")
    if shutil.disk_usage(root/"voices").free < 3*1024**3:
        raise ValueError("At least 3 GiB free on the original Hindi source drive is required")
    lock=root/"source"/LOCK
    if lock.is_symlink() or lock.exists():raise ValueError("Another/orphan CPU session lock exists; manual inspection")
    clock=clock or time.monotonic
    before=len(done);completed=[];stopped=False
    lock_marker="LOCAL_CPU_SESSION="+uuid.uuid4().hex+"\n"
    with lock.open("x",encoding="ascii") as f:
        f.write(lock_marker);f.flush();os.fsync(f.fileno())
    try:
        begin=clock()
        for _ in range(max_new):
            source,done=verified_previews(root,allow_short=allow_short)
            target=pilot_targets(source,done) if mode=="pilot" else [x["id"] for x in source["chunks"] if x["id"] not in done]
            if not target:break
            elapsed=clock()-begin
            if elapsed <0:raise ValueError("System monotonic clock moved backwards")
            left=int(wall_seconds-elapsed)
            if left<120:stopped=True;break
            timeout=min(per_chunk_timeout,left)
            row=next(x for x in source["chunks"] if x["id"]==target[0])
            _model_call(root,row,sadtalker_root=Path(sadtalker_root or ""),
                        sadtalker_python=Path(sadtalker_python or ""),timeout=timeout,
                        allow_short=allow_short,model_runner=model_runner)
            # Independently re-audit before progressing; never trust JSON alone.
            _,confirmed=verified_previews(root,allow_short=allow_short)
            if len(confirmed)!=before+len(completed)+1:raise ValueError("Checkpoint advanced unexpectedly")
            completed.append(row["id"])
            atomic_json(root/"source"/CHECKPOINT,{"schema":3,"source_binding":source["source_binding"],
                         "verified_previews":confirmed})
        final=progress(root,allow_short=allow_short)
        return {**final,"session_new_real_neural_calls":len(completed),
                "new_chunk_ids":completed,"mode":mode,"stopped_for_budget":stopped,
                "requested_wall_seconds":wall_seconds,"wall_budget_excludes_cleanup_overhead":True,
                "background_autorun":False,"publication_approved":False}
    finally:
        # We created this exclusive local file; do not accidentally remove a
        # manually substituted foreign lock while model inference ran.
        if lock.exists() and not lock.is_symlink() and lock.read_text(encoding="ascii")==lock_marker:
            lock.unlink()


def quantize_segment_frames(durations:list[float],*,fps:int=FPS) -> list[int]:
    """Round the *cumulative* signed speech/pause timeline to 24fps.

    Independent per-clip rounding accumulates up to ~0.5 frame error on
    EACH of 100+ segments. Cumulative rounding keeps total error at
    most half one frame, and prevents end-of-episode visual drift.
    """
    if (not isinstance(durations,list) or not durations
            or type(fps) is not int or fps<1 or fps>120):
        raise ValueError("Invalid source-bound 24fps segment plan")
    t=0.0
    previous=0
    plan=[]
    for duration in durations:
        if (type(duration) not in (int,float)
                or not math.isfinite(duration) or duration<=0):
            raise ValueError("Invalid original spoken/pause segment duration")
        t+=duration
        next_count=round(t*fps)
        number=next_count-previous
        if number<1:raise ValueError("Sub-frame source segment is not playable")
        plan.append(number)
        previous=next_count
    assert sum(plan)==round(t*fps)
    return plan


def _concat_video(chunks:list[Path],tmp:Path, duration:float) -> Path:
    lst=tmp/"join.ffconcat"
    lines=["ffconcat version 1.0"]
    for p in chunks:
        s=p.as_posix().replace("'","'\\''")
        lines.append("file '"+s+"'")
    lst.write_text("\n".join(lines)+"\n",encoding="utf-8")
    result=tmp/"joined.mp4"
    cmd(["ffmpeg","-y","-hide_banner","-v","error","-f","concat","-safe","0","-i",str(lst),
         "-c:v","libx264","-threads","2","-preset","ultrafast","-crf","23","-vf",f"fps={FPS},format=yuv420p",
         "-an","-t",str(duration),str(result)],timeout=max(200,int(duration*12)))
    return result


def compose_neural(root:Path,*,allow_short:bool=False) -> dict:
    """No model audio in final: exact 45 original Hindi WAVs and pauses."""
    root=workspace_path(root);src=verify_source(root,allow_short=allow_short)
    chunks,done=verified_previews(root,allow_short=allow_short)
    if len(done)!=chunks["count"]:raise ValueError("All genuine original face previews must be decoded first")
    from .review import inspect_pilot
    review=inspect_pilot(root,allow_short=allow_short)
    if review.get("every_presenter_manual_pass") is not True:
        raise ValueError("Human 3-presenter pilot PASS observations required before costly final composition")
    target=root/"exports"/"original_hindi_full_neural.mp4"
    report=root/"exports"/"original_hindi_full_neural.json"
    captions=root/"exports"/"original_hindi_full_neural.srt"
    if any(p.exists() or p.is_symlink() for p in (target,report,captions)):
        raise ValueError("Existing full video/SRT/report cannot be silently overwritten")
    if shutil.disk_usage(root/"exports").free < 6*1024**3:
        raise ValueError("At least 6 GiB free for the final 720p candidate video output required")
    scratch=root/"scratch"
    if scratch.is_symlink() or not scratch.is_dir():
        raise ValueError("Private full neural scratch directory missing/symlinked")
    if shutil.disk_usage(scratch).free < 6*1024**3:
        raise ValueError("At least 6 GiB free on actual neural encoder scratch volume required")
    rows=timeline(root,src)
    groups={row["line_id"]:[] for row in chunks["chunks"]}
    for row in chunks["chunks"]:groups[row["line_id"]].append(row)
    ordered=[]
    for turn in rows:
        for part in groups[turn["id"]]:
            ordered.append(("speech",turn,part,float(part["duration"])))
        if turn["pause"]>0:
            ordered.append(("pause",turn,None,float(turn["pause"])))
    if not ordered:raise ValueError("No original Hindi speaking face timeline to compose")
    frame_plan=quantize_segment_frames([segment[3] for segment in ordered])
    if sum(frame_plan)!=round(src["original_seconds"]*FPS):
        raise ValueError("Original final frame timeline is not source bound")
    with tempfile.TemporaryDirectory(prefix="podcast-full-neural-",dir=scratch) as folder:
        tmp=Path(folder);segments=[]
        for (kind,turn,part,_),frame_count in zip(ordered,frame_plan):
            if kind=="speech":
                model_video=root/"previews"/(part["id"]+".mp4")
                segment=tmp/(part["id"]+".mp4")
                # Video pixels only. Pad any sub-frame end gap by cloning
                # the last face frame; exact cumulative frame count is
                # source-PCM-derived, never determined by model AAC.
                cmd(["ffmpeg","-y","-hide_banner","-v","error","-i",str(model_video),
                     "-an","-vf",f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
                     f"crop={WIDTH}:{HEIGHT},fps={FPS},"
                     "tpad=stop_mode=clone:stop_duration=1,format=yuv420p",
                     "-frames:v",str(frame_count),
                     "-c:v","libx264","-threads","2","-preset","ultrafast","-crf","23",
                     str(segment)],timeout=max(120,int(part["duration"]*20)))
                segments.append(segment)
            else:
                # Original source-bound still card during exact silence.
                card=tmp/(turn["speaker"]+"-still.png")
                if not card.exists():portrait_card(root,turn["speaker"],card)
                segment=tmp/(turn["id"]+"-pause.mp4")
                cmd(["ffmpeg","-y","-hide_banner","-v","error","-loop","1",
                     "-framerate",str(FPS),"-i",str(card),"-an",
                     "-frames:v",str(frame_count),"-c:v","libx264",
                     "-threads","2","-preset","ultrafast",
                     "-pix_fmt","yuv420p",str(segment)],timeout=120)
                segments.append(segment)
            if (os.environ.get("PODCAST_BUILD_PROGRESS")=="1"
                    and kind=="pause" and int(turn["id"])%10==0):
                print(f"[SOURCE-BOUND COMPOSER] Encoded {turn['id']}/045 original turns; real model inference calls 0",flush=True)
        if not segments:raise ValueError("No genuine verified neural face videos")
        joined=_concat_video(segments,tmp,src["original_seconds"])
        # No segment-by-segment 24fps rounding drift: 45-turn joined video
        # must span the PCM timeline, within at most one 24fps frame.
        probe=json.loads(cmd(["ffprobe","-v","error","-select_streams","v:0",
                              "-show_entries","stream=duration","-of","json",
                              str(joined)],timeout=90).stdout)
        if len(probe.get("streams",[]))!=1:
            raise ValueError("Joined original face video stream missing")
        joined_seconds=float(probe["streams"][0].get("duration",0))
        if (not math.isfinite(joined_seconds)
                or abs(joined_seconds-src["original_seconds"])>1/FPS+.005):
            raise ValueError("45-turn neural candidate video timing drifted from original Hindi PCM")
        audio=tmp/"original.wav";original_audio(root,rows,audio)
        staged=tmp/"full.mp4"
        cmd(["ffmpeg","-y","-hide_banner","-v","error","-i",str(joined),"-i",str(audio),
             "-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","160k",
             "-ar","48000","-t",f"{src['original_seconds']:.6f}","-movflags","+faststart",str(staged)],
            timeout=max(240,int(src["original_seconds"]*4)))
        measure=full_decode(staged,seconds=src["original_seconds"],require_720=True)
        verify_source(root,allow_short=allow_short)
        verified_chunks,again=verified_previews(root,allow_short=allow_short)
        if again!=done:raise ValueError("Neural speaking clips changed while composing")
        captions.write_text(subtitle(rows),encoding="utf-8")
        shutil.copyfile(staged,target)
        result={"schema":3,"status":"candidate_full_original_hindi_neural_video_independently_decoded",
                "source_binding":json_digest(src),"chunks_binding":json_digest(verified_chunks),
                "verified_preview_sha256":done,"video_sha256":digest(target),
                "srt_sha256":digest(captions),"seconds":src["original_seconds"],
                "turns":45,"media":measure,
                "human_lipsync_approved":False,"publication_approved":False,
                "full_ten_minute_neural_video_structurally_audited":not allow_short,
                "synthetic_short_test_only":allow_short}
        atomic_json(report,result,new=True)
    return result


def audit_neural(root:Path,*,allow_short:bool=False) -> dict:
    root=workspace_path(root)
    src=verify_source(root,allow_short=allow_short)
    chunks,done=verified_previews(root,allow_short=allow_short)
    report=read_json(root/"exports"/"original_hindi_full_neural.json",3_000_000)
    video=root/"exports"/"original_hindi_full_neural.mp4"
    captions=root/"exports"/"original_hindi_full_neural.srt"
    if (report.get("status")!="candidate_full_original_hindi_neural_video_independently_decoded"
            or report.get("source_binding")!=json_digest(src)
            or report.get("chunks_binding")!=json_digest(chunks)
            or report.get("verified_preview_sha256")!=done
            or report.get("video_sha256")!=digest(video)
            or report.get("srt_sha256")!=digest(captions)
            or report.get("seconds")!=src["original_seconds"]
            or captions.read_text(encoding="utf-8")!=subtitle(timeline(root,src))
            or report.get("publication_approved") is not False):
        raise ValueError("Candidate full video/SRT/provenance differs from current original Hindi source")
    return {"complete_45_turn_video_structurally_audited":True,
            "media":full_decode(video,seconds=src["original_seconds"],require_720=True),
            "original_ten_minute_duration_required":not allow_short,
            "human_hindi_lipsync_accuracy_verified":False,
            "publication_approved":False}