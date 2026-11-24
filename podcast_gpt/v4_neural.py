"""V4 source-bound local SadTalker clips and per-speaker pilot gate.

Only explicit foreground CPU runs. Structural media verification does not
establish genuine face animation, identity, lip-sync or human quality.
"""
from __future__ import annotations

import hashlib
import io
import os
import shutil
import subprocess
import time
import wave
from pathlib import Path

from . import characters, hardware, media, model_preflight, projects, source, v4_preview

FOLDER="neural-clips"
REVIEW="pilot-review.json"
ACK="I_HAVE_RIGHTS_AND_TRUST_THIS_LOCAL_SADTALKER_INSTALLATION"
REVIEW_ACK="I_WATCHED_EVERY_CURRENT_PILOT_CLIP"
CRITERIA=("lip_sync","face_identity","visual_quality","audio_alignment")
RATE=16000
MAX_FRAMES=10*RATE
MAX_CLIP_BYTES=100_000_000


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _pcm(dest,row):
    raw=characters._read_file(dest/row["turn_id"]/"speech.wav",RATE*2*120+65536)
    if _sha(raw)!=row["wav_sha256"]:raise ValueError("Speech WAV changed")
    with wave.open(io.BytesIO(raw),"rb") as w:pcm=w.readframes(w.getnframes())
    if _sha(pcm)!=row["pcm_sha256"] or len(pcm)!=2*(row["speech_end_frame"]-row["start_frame"]):
        raise ValueError("Speech PCM changed")
    return pcm


def _context(root,pid):
    folder,dest,timeline,turns,cast,seal=v4_preview._context(root,pid)
    identities={}
    for member in cast["cast"]:
        record=characters.read(root,member["character_id"])
        if source.json_digest(record)!=member["record_sha256"]:raise ValueError("Cast changed")
        identities[member["speaker"]]=(member["character_id"],record["portrait"]["sha256"])
    rows=[]
    for turn in timeline["rows"]:
        pcm=_pcm(dest,turn)
        frames=len(pcm)//2
        count=(frames+MAX_FRAMES-1)//MAX_FRAMES
        cid,portrait=identities[turn["speaker"]]
        for i in range(count):
            start=i*frames//count;end=(i+1)*frames//count
            rows.append({"id":f"{turn['turn_id']}-{i+1:02}","turn_id":turn["turn_id"],"speaker":turn["speaker"],
                         "character_id":cid,"portrait_sha256":portrait,"start_frame":start,"end_frame":end,
                         "pcm_sha256":_sha(pcm[2*start:2*end])})
    targets=[];seen=set()
    for row in rows:
        if row["speaker"] not in seen and row["end_frame"]-row["start_frame"]>=RATE:
            targets.append(row["id"]);seen.add(row["speaker"])
    if seen!=set(identities):raise ValueError("Every presenter needs a pilot speech chunk of at least one second")
    binding={"preview_inputs":seal,"chunk_plan_sha256":source.json_digest(rows),"pilot_ids":targets}
    return folder,dest,binding,rows,targets


def _decode(path,row):
    projects._plain(path,directory=False)
    if path.stat().st_size>MAX_CLIP_BYTES:raise ValueError("Oversized model clip")
    seconds=(row["end_frame"]-row["start_frame"])/RATE
    streams=media.full_decode(path,seconds=seconds)
    if any(abs(streams[k]-seconds)>.5 for k in ("duration","video_duration","audio_duration")):
        raise ValueError("Model clip does not cover original PCM")
    return streams


def _valid_hash(s):
    return isinstance(s,str) and len(s)==64 and all(c in "0123456789abcdef" for c in s)


def _scan(dest,binding,rows,*,cache=None):
    path=dest/FOLDER;projects._plain(path,missing=True)
    if not path.exists():return {}
    expected={r["id"]:r for r in rows};done={}
    for child in sorted(path.iterdir()):
        if child.name==REVIEW:
            projects._plain(child,directory=False);continue
        projects._plain(child)
        if child.name not in expected or {p.name for p in child.iterdir()}!={"face.mp4","receipt.json"}:
            raise ValueError("Unexpected or interrupted neural clip; inspect privately")
        for p in child.iterdir():projects._plain(p,directory=False)
        saved=source.read_json(child/"receipt.json",64000)
        row=expected[child.name];clip=child/"face.mp4"
        if (set(saved)!={"schema","binding","chunk","model_sha256","mp4_sha256","streams","test_fixture_only","human_lipsync_approved"}
                or saved["schema"]!=1 or saved["binding"]!=binding or saved["chunk"]!=row
                or not _valid_hash(saved["model_sha256"]) or type(saved["test_fixture_only"]) is not bool
                or saved["human_lipsync_approved"] is not False or saved["mp4_sha256"]!=source.digest(clip)):
            raise ValueError("Neural clip provenance or video hash differs")
        key=(saved["mp4_sha256"],row["pcm_sha256"])
        if cache is not None and key in cache:streams=cache[key]
        else:
            streams=_decode(clip,row)
            if source.digest(clip)!=saved["mp4_sha256"]:raise ValueError("Neural video changed during decode")
            if cache is not None:cache[key]=streams
        if streams!=saved["streams"]:raise ValueError("Neural stream receipt differs")
        done[child.name]=saved
    if len({r["model_sha256"] for r in done.values()})>1 or len({r["test_fixture_only"] for r in done.values()})>1:
        raise ValueError("Mixed model installations or fixture/production clips refused")
    return done


def _pilot_binding(binding,targets,done):
    if not all(k in done for k in targets):raise ValueError("Generate every presenter pilot first")
    return {"source":binding,"pilot_clip_sha256":{k:source.json_digest(done[k]) for k in targets}}


def _validate_observations(obs,targets):
    if not isinstance(obs,dict) or set(obs)!=set(targets):raise ValueError("Review every pilot clip")
    for values in obs.values():
        if not isinstance(values,dict) or set(values)!=set(CRITERIA) or any(v not in ("PASS","FAIL") for v in values.values()):
            raise ValueError("Set all pilot observations to PASS or FAIL, not UNREVIEWED")
    return obs


def _review(dest,binding,targets,done):
    path=dest/FOLDER/REVIEW
    if not path.exists() and not path.is_symlink():return None
    projects._plain(path,directory=False)
    saved=source.read_json(path,300000)
    if (set(saved)!={"schema","binding","observations","acknowledgment","observations_sha256"}
            or saved["schema"]!=1 or saved["binding"]!=_pilot_binding(binding,targets,done)
            or saved["acknowledgment"]!=REVIEW_ACK):
        raise ValueError("Stale or invalid pilot review")
    obs=_validate_observations(saved["observations"],targets)
    if saved["observations_sha256"]!=source.json_digest(obs):raise ValueError("Pilot observations hash differs")
    return saved


def _passed(saved):
    return saved is not None and all(v=="PASS" for row in saved["observations"].values() for v in row.values())


def _status(pid,dest,binding,rows,targets,done):
    saved=_review(dest,binding,targets,done)
    passed=_passed(saved)
    return {"project_id":pid,"chunk_count":len(rows),"completed_chunks":len(done),
            "pilot_ids":targets,"missing_pilot_ids":[k for k in targets if k not in done],
            "pilot_review_status":"PASS" if passed else "FAIL" if saved else "UNREVIEWED",
            "batch_unlocked":passed,"remaining_chunks":len(rows)-len(done),
            "test_fixture_only":any(r["test_fixture_only"] for r in done.values()),
            "independent_lipsync_quality_verified":False,"full_neural_video_generated":False,"publication_approved":False}


def inspect(root,pid):
    _,dest,binding,rows,targets=_context(root,pid)
    return _status(pid,dest,binding,rows,targets,_scan(dest,binding,rows))


def template(root,pid):
    folder=projects.project(root,pid)
    with projects.exclusive(folder):
        _,dest,binding,rows,targets=_context(root,pid)
        done=_scan(dest,binding,rows)
        if _review(dest,binding,targets,done) is not None:raise ValueError("Pilot review already recorded")
        bound=_pilot_binding(binding,targets,done)
        path=folder/("neural-pilot-"+source.json_digest(bound)+".json")
        source.atomic_json(path,{"schema":1,"binding":bound,
            "observations":{k:{c:"UNREVIEWED" for c in CRITERIA} for k in targets}},new=True)
        return {"project_id":pid,"template_path":str(path),
                "pilot_clips":[str(dest/FOLDER/k/"face.mp4") for k in targets]}


def record(root,pid,*,acknowledgment,input_file=None):
    if acknowledgment!=REVIEW_ACK:raise ValueError("Explicit pilot viewing acknowledgment required")
    folder=projects.project(root,pid)
    with projects.exclusive(folder):
        _,dest,binding,rows,targets=_context(root,pid)
        done=_scan(dest,binding,rows)
        if _review(dest,binding,targets,done) is not None:raise ValueError("Pilot review cannot be overwritten")
        bound=_pilot_binding(binding,targets,done)
        path=folder/("neural-pilot-"+source.json_digest(bound)+".json")
        if input_file is None:
            projects._plain(path,directory=False)
            data=source.read_json(path,300000)
        else:
            from .visual_media_review import read_input
            data=read_input(input_file,300000)
        value=data
        if set(value)!={"schema","binding","observations"} or value["schema"]!=1 or value["binding"]!=bound:
            raise ValueError("Pilot review template is stale")
        obs=_validate_observations(value["observations"],targets)
        source.atomic_json(dest/FOLDER/REVIEW,{**value,"observations_sha256":source.json_digest(obs),
                           "acknowledgment":REVIEW_ACK},new=True)
        return _status(pid,dest,binding,rows,targets,done)


def _installation(model,python):
    model=Path(model).expanduser().absolute();python=Path(python).expanduser().absolute()
    for path in (model,python):
        for parent in reversed(path.parents):projects._plain(parent)
    projects._plain(model);projects._plain(python,directory=False)
    model_preflight.inspect_sadtalker_installation(model,python)
    return model,python


def _model_hash(model,python):
    # Fingerprint selected inference entrypoint, config and checkpoint bytes;
    # this is not authentication of third-party Python or its dependencies.
    records={"inference.py":source.digest(model/"inference.py"),"interpreter":source.digest(python)}
    for base in (model/"src"/"config",model/"checkpoints"):
        projects._plain(base)
        for p in sorted(base.rglob("*")):
            projects._plain(p,directory=p.is_dir())
            if p.is_file():records[p.relative_to(model).as_posix()]=source.digest(p)
            if len(records)>1000:raise ValueError("Model inventory too large")
    return source.json_digest(records)


def _run_model(model,python,scratch,timeout,threads):
    output=scratch/"output";output.mkdir()
    args=[str(python),str(model/"inference.py"),"--driven_audio",str(scratch/"speech.wav"),
          "--source_image",str(scratch/"portrait.png"),"--result_dir",str(output),"--still","--preprocess","full","--cpu"]
    env=os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"]="";env["OMP_DYNAMIC"]="FALSE"
    for name in ("OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS","NUMEXPR_NUM_THREADS"):env[name]=str(threads)
    with (scratch/"stdout.log").open("xb") as out,(scratch/"stderr.log").open("xb") as err:
        try:result=subprocess.run(args,cwd=str(model),env=env,stdout=out,stderr=err,timeout=timeout,check=False)
        except subprocess.TimeoutExpired:raise RuntimeError("Local CPU model timed out; private scratch retained") from None
    if result.returncode:raise RuntimeError("Local CPU model failed; private scratch logs retained")
    candidates=list(output.rglob("*.mp4"))
    if len(candidates)!=1:raise ValueError("Expected one local model MP4")
    return candidates[0]


def generate(root,pid,*,model,python,mode="pilot",max_new=1,timeout=1800,acknowledgment=None,run_local=False,cpu_threads=None,model_runner=None):
    if run_local is not True or acknowledgment!=ACK:raise ValueError("Explicit local model consent and rights acknowledgment required")
    if mode not in ("pilot","batch") or type(max_new) is not int or not 1<=max_new<=3 or type(timeout) is not int or not 120<=timeout<=7200:
        raise ValueError("Choose pilot or batch, 1–3 chunks and 120–7200 seconds per chunk")
    threads=hardware.select_threads(cpu_threads)
    folder=projects.project(root,pid)
    with projects.exclusive(folder):
        _,dest,binding,rows,targets=_context(root,pid)
        cache={};done=_scan(dest,binding,rows,cache=cache)
        saved=_review(dest,binding,targets,done)
        if mode=="batch" and not _passed(saved):raise ValueError("All presenter pilots need explicit PASS before batch")
        chosen=[r for r in rows if r["id"] not in done and (mode=="batch" or r["id"] in targets)][:max_new]
        if not chosen:return {**_status(pid,dest,binding,rows,targets,done),"new_chunk_ids":[]}
        if any(r["test_fixture_only"]!=(model_runner is not None) for r in done.values()):raise ValueError("Fixture and production clips cannot mix")
        if shutil.disk_usage(folder).free<6*1024**3:raise ValueError("At least 6 GiB free for private CPU inference")
        model,python=_installation(model,python)
        fingerprint=_model_hash(model,python)
        if any(r["model_sha256"]!=fingerprint for r in done.values()):raise ValueError("Local model fingerprint differs from saved clips")
        out=dest/FOLDER;out.mkdir(exist_ok=True);projects._plain(out)
        scratch_base=folder/"neural-scratch";scratch_base.mkdir(exist_ok=True);projects._plain(scratch_base)
        completed=[]
        for row in chosen:
            if _context(root,pid)[2]!=binding or _scan(dest,binding,rows,cache=cache)!=done:
                raise ValueError("Neural source or checkpoints changed")
            if mode=="batch" and not _passed(_review(dest,binding,targets,done)):raise ValueError("Pilot gate changed")
            scratch=scratch_base/(source.json_digest(binding)+"-"+row["id"])
            scratch.mkdir()
            current=next(t for t in v4_preview._context(root,pid)[2]["rows"] if t["turn_id"]==row["turn_id"])
            pcm=_pcm(dest,current)[row["start_frame"]*2:row["end_frame"]*2]
            if _sha(pcm)!=row["pcm_sha256"]:raise ValueError("Chunk PCM changed")
            with wave.open(str(scratch/"speech.wav"),"wb") as w:
                w.setnchannels(1);w.setsampwidth(2);w.setframerate(RATE);w.writeframes(pcm)
            raw=characters._read_file(characters._profile_folder(root,row["character_id"])/characters.PORTRAIT,characters.MAX_PORTRAIT)
            if _sha(raw)!=row["portrait_sha256"]:raise ValueError("Portrait changed")
            with (scratch/"portrait.png").open("xb") as f:f.write(raw)
            video=Path((model_runner or _run_model)(model,python,scratch,timeout,threads))
            if not video.resolve().is_relative_to(scratch.resolve()):raise ValueError("Model output outside private scratch")
            for parent in video.parents:
                projects._plain(parent)
                if parent==scratch:break
            streams=_decode(video,row);sha=source.digest(video)
            if _context(root,pid)[2]!=binding or _model_hash(model,python)!=fingerprint or _scan(dest,binding,rows,cache=cache)!=done:
                raise ValueError("Source, model or prior clips changed during inference")
            target=out/row["id"];target.mkdir()
            with video.open("rb") as inp,(target/"face.mp4").open("xb") as f:shutil.copyfileobj(inp,f)
            if source.digest(target/"face.mp4")!=sha:raise ValueError("Copied model clip differs")
            receipt={"schema":1,"binding":binding,"chunk":row,"model_sha256":fingerprint,"mp4_sha256":sha,
                     "streams":streams,"test_fixture_only":model_runner is not None,"human_lipsync_approved":False}
            source.atomic_json(target/"receipt.json",receipt,new=True)
            confirmed=_scan(dest,binding,rows,cache=cache)
            if confirmed!={**done,row["id"]:receipt}:raise ValueError("Unexpected neural checkpoint changes")
            done=confirmed;completed.append(row["id"])
            # Preserve scratch on failure; remove only this completed invocation's own files.
            shutil.rmtree(scratch)
        confirmed=_scan(dest,binding,rows)
        if confirmed!=done:raise ValueError("Final neural clip audit differs")
        return {**_status(pid,dest,binding,rows,targets,done),"new_chunk_ids":completed}
