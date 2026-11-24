"""Read-only staged readiness. No inference, publication or automatic action."""
from . import projects, characters, v4_audio as audio, v4_master as master
from . import v4_audio_review as listening, v4_neural as neural, v4_export as export
from . import v4_final_review as final, v4_recovery as recovery


def inspect(root,pid):
    folder=projects.project(root,pid)
    result={"project_id":pid,"checks":{},"publication_approved":False,"physical_model_acceptance_verified":False}
    def stop(stage,action):
        return {**result,"stage":stage,"next_action":action}
    lock=folder/projects.LOCK
    if lock.exists() or lock.is_symlink():return stop("operation_locked","Inspect active or interrupted process manually; do not clear lock automatically")
    state=projects.inspect(root,pid);req=state["request"]
    result["checks"]["planning_stage"]=state["stage"]
    if req["input_kind"]!="topic" and "source" not in state:return stop("source_required","project-import-source")
    if req["research_mode"]=="web" and "research" not in state:return stop("research_required","project-research-capture")
    if "outline" not in state:return stop("outline_required","project-plan")
    progress=state["script_progress"]
    result["checks"]["script_units"]={"completed":progress["completed_units"],"total":progress["planned_units"]}
    if state["stage"]!="script_saved":
        return stop("script_required","project-script-finalize" if progress["remaining_units"]==0 else "project-script-generate")
    script=state["script_review"];result["checks"]["script_review"]=script["review_status"]
    if not script["human_script_self_attested_pass"]:
        return stop("script_review_required","project-script-review-template / record, or revise failed script")
    cast=state.get("cast",{})
    if not cast.get("all_portraits_present"):return stop("cast_required","character-create / project-cast-assign")
    info=audio.inspect(root,pid)
    result["checks"]["audio_turns"]={"completed":info["completed_audio_turns"],"total":info["total_turns"]}
    if info["missing_turn_ids"]:return stop("audio_required","project-audio-import / project-tts-kokoro / project-tts-espeak")
    if not info["timeline_finalized"]:return stop("timeline_required","project-audio-finalize")
    _,dest,_,_,_,_=audio._context(root,pid)
    if not (dest/master.FOLDER).exists() and not (dest/master.FOLDER).is_symlink():return stop("master_required","project-master-compose")
    master.inspect(root,pid)
    review=listening.inspect(root,pid);result["checks"]["listening_review"]=review["review_status"]
    if not review["human_audio_self_attested_pass"]:return stop("listening_review_required","project-audio-review-template / record")
    clips=neural.inspect(root,pid)
    result["checks"]["neural_chunks"]={"completed":clips["completed_chunks"],"total":clips["chunk_count"]}
    result["checks"]["pilot_review"]=clips["pilot_review_status"]
    if clips["test_fixture_only"]:return stop("fixture_only","Synthetic clips are not production evidence")
    rec=recovery.inspect(root,pid)
    if rec["archive_eligible_ids"]:
        result["checks"]["stopped_attempt_candidates"]=rec["archive_eligible_ids"]
        return stop("scratch_inspection_required","project-neural-recovery-status / project-neural-archive after stopping processes")
    if clips["missing_pilot_ids"]:return stop("pilot_required","project-neural-run --mode pilot")
    if not clips["batch_unlocked"]:return stop("pilot_review_required","project-neural-pilot-template / record")
    if clips["remaining_chunks"]:return stop("neural_batch_required","project-neural-run --mode batch")
    if not (dest/export.FOLDER).exists() and not (dest/export.FOLDER).is_symlink():return stop("export_required","project-neural-compose")
    export.inspect(root,pid)
    qa=final.inspect(root,pid);result["checks"]["final_review"]=qa["review_status"]
    if not qa["human_video_self_attested_pass"]:return stop("final_review_required","project-final-review-template / record")
    return stop("human_review_passed","Review real-device acceptance and publication rights separately; no automatic publication")
