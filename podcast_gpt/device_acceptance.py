"""Read-only staged acceptance checklist; never certifies physical hardware."""
from . import projects,v4_readiness,voice_preflight,setup_wizard,v4_audio,v4_final_review


def inspect(root,pid):
    state=v4_readiness.inspect(root,pid);req=projects.load(root,pid)
    setup=setup_wizard.inspect(root);voices=voice_preflight.inspect(root,pid)
    stage=state["stage"];timing=None;review=None
    if stage in ("master_required","listening_review_required","pilot_required","pilot_review_required",
                 "neural_batch_required","export_required","final_review_required","human_review_passed"):
        timing=v4_audio.inspect(root,pid)
    if stage=="human_review_passed":review=v4_final_review.inspect(root,pid)
    return {"project_id":pid,"request_minutes":req["duration_minutes"],"request_presenters":len(req["presenters"]),
            "readiness":state,"hardware_inventory":setup["hardware"],"workspace":setup["workspace"],
            "application_prerequisites_present":setup["application_prerequisites_present"],
            "voice_preflight":voices,"measured_audio_seconds":timing["measured_audio_seconds"] if timing else None,
            "within_target_10_percent":timing["within_target_10_percent"] if timing else None,
            "candidate_human_review_passed":bool(review and review["human_video_self_attested_pass"]),
            "device_checks_remaining":["Verify installed models and real inference on target Windows PC",
                "Listen to the entire episode for pronunciation and voice identities",
                "Watch complete video for lip sync, subtitles and transitions",
                "Verify intended duration, media rights, startup/restart/recovery"],
            "physical_device_acceptance_verified":False,"production_release_approved":False,"publication_approved":False}
