"""Bounded foreground production stages; all existing human gates remain mandatory."""
import time
from . import projects, v4_readiness as readiness, script_generation as scripts
from . import v4_audio as audio, v4_master as master, v4_export as export

ACK="I_AUTHORIZE_BOUNDED_LOCAL_PRODUCTION_STEPS"


def run(root,pid,*,execute=False,acknowledgment=None,max_steps=3,allow_local_ai=False):
    if type(max_steps) is not int or not 1<=max_steps<=5:raise ValueError("Select 1–5 foreground stages")
    if execute and acknowledgment!=ACK:raise ValueError("Explicit foreground production acknowledgment required")
    events=[]
    state=readiness.inspect(root,pid)
    if not execute:return {"project_id":pid,"status":"plan_only","readiness":state,"events":events,"publication_approved":False}
    for _ in range(max_steps):
        stage=state["stage"];action=state["next_action"]
        if stage=="outline_required" and allow_local_ai:
            fn=lambda:projects.generate_outline(root,pid,offline_only=True)
        elif stage=="script_required":
            progress=state["checks"]["script_units"]
            if progress["completed"]==progress["total"]:fn=lambda:scripts.finalize(root,pid)
            elif allow_local_ai:fn=lambda:scripts.generate(root,pid,max_new=1,offline_only=True)
            else:break
        elif stage=="timeline_required":fn=lambda:audio.finalize(root,pid)
        elif stage=="master_required":fn=lambda:master.compose(root,pid)
        elif stage=="export_required":fn=lambda:export.compose(root,pid)
        else:break
        started=time.monotonic()
        fn()
        elapsed=round(time.monotonic()-started,3)
        after=readiness.inspect(root,pid)
        events.append({"stage":stage,"action":action,"elapsed_seconds":elapsed,"next_stage":after["stage"]})
        if after==state:raise ValueError("No verified production progress; stopped")
        state=after
    return {"project_id":pid,"status":"bounded_steps_completed" if events else "stopped_at_gate",
            "readiness":state,"events":events,"elapsed_action_seconds":round(sum(e["elapsed_seconds"] for e in events),3),
            "live_eta_available":False,"cloud_calls_authorized":False,"human_review_automated":False,"publication_approved":False}
