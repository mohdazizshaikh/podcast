"""Bounded foreground production stages; all existing human gates remain mandatory."""
import time
from . import projects, v4_readiness as readiness, script_generation as scripts
from . import v4_audio as audio, v4_master as master, v4_export as export
from . import model_config, v4_tts, v4_espeak, v4_neural, v4_progress, source

ACK="I_AUTHORIZE_BOUNDED_LOCAL_PRODUCTION_STEPS"


def run(root,pid,*,execute=False,acknowledgment=None,max_steps=3,allow_local_ai=False,
        kokoro_ack=None,espeak_ack=None,neural_ack=None,allowed_stages=None,progress=None,should_stop=None):
    if type(max_steps) is not int or not 1<=max_steps<=5:raise ValueError("Select 1–5 foreground stages")
    if execute and acknowledgment!=ACK:raise ValueError("Explicit foreground production acknowledgment required")
    for supplied,expected in ((kokoro_ack,v4_tts.ACK),(espeak_ack,v4_espeak.ACK),(neural_ack,v4_neural.ACK)):
        if supplied is not None and supplied!=expected:raise ValueError("Invalid explicit local model acknowledgment")
    events=[]
    state=readiness.inspect(root,pid)
    if not execute:return {"project_id":pid,"status":"plan_only","readiness":state,"events":events,"publication_approved":False}
    stopped=False
    for _ in range(max_steps):
        if should_stop is not None and should_stop():stopped=True;break
        stage=state["stage"];action=state["next_action"];timing=None
        if allowed_stages is not None and stage not in allowed_stages:break
        if stage=="outline_required" and allow_local_ai:
            fn=lambda:projects.generate_outline(root,pid,offline_only=True)
        elif stage=="script_required":
            script_progress=state["checks"]["script_units"]
            if script_progress["completed"]==script_progress["total"]:fn=lambda:scripts.finalize(root,pid)
            elif allow_local_ai:fn=lambda:scripts.generate(root,pid,max_new=1,offline_only=True)
            else:break
        elif stage=="audio_required" and (kokoro_ack or espeak_ack):
            _,dest,binding,turns,req,cast=audio._context(root,pid)
            items=audio._read_parts(dest,binding,turns)
            engines={r["speaker"]:r["voice_preferences"]["engine"] for r in cast["presenters"]}
            eligible={engines[t["speaker"]] for t in turns if t["id"] not in items}
            if "kokoro" in eligible and kokoro_ack:
                paths=model_config.read(root,"kokoro");action="project-tts-kokoro"
                fn=lambda:v4_tts.generate(root,pid,**paths,run_local=True,acknowledgment=kokoro_ack,max_new=1)
                timing=("kokoro",binding,"new_generated_turns")
            elif "espeak" in eligible and espeak_ack:
                paths=model_config.read(root,"espeak");action="project-tts-espeak"
                fn=lambda:v4_espeak.generate(root,pid,**paths,run_local=True,acknowledgment=espeak_ack,max_new=1)
                timing=("espeak",binding,"new_generated_turns")
            else:break
        elif stage in ("pilot_required","neural_batch_required") and neural_ack:
            paths=model_config.read(root,"sadtalker")
            _,_,binding,_,_=v4_neural._context(root,pid)
            mode="pilot" if stage=="pilot_required" else "batch"
            action="project-neural-run --mode "+mode
            fn=lambda:v4_neural.generate(root,pid,**paths,mode=mode,max_new=1,run_local=True,acknowledgment=neural_ack)
            timing=("neural_"+mode,binding,"new_chunk_ids")
        elif stage=="timeline_required":fn=lambda:audio.finalize(root,pid)
        elif stage=="master_required":fn=lambda:master.compose(root,pid)
        elif stage=="export_required":fn=lambda:export.compose(root,pid)
        else:break
        if progress is not None:progress({"stage":stage,"action":action,"completed_actions":len(events),"action_limit":max_steps,"checkpoint_verified":False})
        if should_stop is not None and should_stop():stopped=True;break
        started=time.monotonic()
        outcome=fn()
        elapsed=round(time.monotonic()-started,3)
        if timing is not None:
            engine,binding,key=timing
            ids=outcome.get(key,[])
            if len(ids)!=1:raise ValueError("No single verified media unit completed; stopped")
            v4_progress.record(root,pid,scope=source.json_digest({"binding":binding,"paths":{k:str(v) for k,v in paths.items()}}),action=engine,unit=ids[0],seconds=elapsed)
        after=readiness.inspect(root,pid)
        events.append({"stage":stage,"action":action,"elapsed_seconds":elapsed,"next_stage":after["stage"]})
        if after==state:raise ValueError("No verified production progress; stopped")
        state=after
        if progress is not None:progress({"stage":after["stage"],"action":action,"completed_actions":len(events),"action_limit":max_steps,"checkpoint_verified":True,"last_action_elapsed_seconds":elapsed})
    if should_stop is not None and should_stop():stopped=True
    return {"project_id":pid,"status":"stopped_at_checkpoint" if stopped else "bounded_steps_completed" if events else "stopped_at_gate",
            "readiness":state,"events":events,"elapsed_action_seconds":round(sum(e["elapsed_seconds"] for e in events),3),
            "live_eta_available":False,"cloud_calls_authorized":False,"human_review_automated":False,"publication_approved":False}
