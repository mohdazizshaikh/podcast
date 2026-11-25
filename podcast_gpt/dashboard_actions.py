"""Narrow local dashboard action allowlist; no model execution or approval."""
import json
from . import projects, episode_plan, v4_orchestrator, visual_script, visual_media_review
from . import v4_preview, studio_preview, studio_neural, v4_mixed_video

CREATE_LIMIT=32768
ACK="I_AUTHORIZE_LOCAL_DASHBOARD_PROCESSING"
ACTIONS=("project-safe-step","project-script-visual-edit","project-script-visual-review",
         "project-audio-visual-review","project-pilot-visual-review","project-final-visual-review",
         "project-static-render","project-studio-render","project-neural-studio-compose","project-neural-studio-resume","project-mixed-studio-compose","project-mixed-studio-resume","project-mixed-video-resume")


def parse_request(raw):
    if not 1<=len(raw)<=CREATE_LIMIT:raise ValueError("Invalid project request size")
    try:value=json.loads(raw.decode("utf-8"))
    except (ValueError,UnicodeError) as exc:raise ValueError("Invalid project request JSON") from exc
    return episode_plan.validate_request(value)


def run(root,pid,action,*,acknowledgment,progress=None,should_stop=None):
    if acknowledgment!=ACK:raise ValueError("Explicit local dashboard processing acknowledgment required")
    if action not in ACTIONS:raise ValueError("Unknown dashboard production action")
    folder=projects.project(root,pid)
    lock=folder/projects.LOCK
    if lock.exists() or lock.is_symlink():raise ValueError("Project operation lock present")
    if action=="project-safe-step":
        return v4_orchestrator.run(root,pid,execute=True,acknowledgment=v4_orchestrator.ACK,max_steps=1)
    if action.startswith("project-script-visual-"):
        return visual_script.create(root,pid,mode=action.rsplit("-",1)[1])
    if action in ("project-audio-visual-review","project-pilot-visual-review","project-final-visual-review"):
        return visual_media_review.create(root,pid,kind=action.split("-")[1])
    if action=="project-static-render":return v4_preview.render(root,pid)
    if action=="project-studio-render":return studio_preview.render(root,pid)
    if action=="project-neural-studio-resume":
        return studio_neural.compose(root,pid,progress=progress,should_stop=should_stop,resume=True)
    if action=="project-neural-studio-compose":
        if progress is None and should_stop is None:return studio_neural.compose(root,pid)
        return studio_neural.compose(root,pid,progress=progress,should_stop=should_stop)
    if action in ("project-mixed-studio-resume","project-mixed-video-resume"):
        return v4_mixed_video.compose(root,pid,studio=action=="project-mixed-studio-resume",progress=progress,should_stop=should_stop,resume=True)
    if progress is None and should_stop is None:return v4_mixed_video.compose(root,pid,studio=True)
    return v4_mixed_video.compose(root,pid,studio=True,progress=progress,should_stop=should_stop)
