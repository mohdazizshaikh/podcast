"""Read-only current project overview, local playback manifests and rough ETA.

No HTTP media routes, arbitrary client paths, inference, or automatic approval.
"""
from statistics import median
from . import projects, source, model_config, v4_progress, v4_readiness, v4_audio
from . import v4_neural, v4_master, v4_preview, v4_export, v4_post_audio, v4_mixed_video
from . import studio_preview, studio_neural

MEDIA={
    "master":(v4_master,"master",v4_master.WAV,"wav_sha256"),
    "preview":(v4_preview,"preview",v4_preview.VIDEO,"video_sha256"),
    "neural":(v4_export,"export",v4_export.VIDEO,"video_sha256"),
    "mix":(v4_post_audio,"mix",v4_post_audio.WAV,"wav_sha256"),
    "mixed":(v4_mixed_video,"export",v4_mixed_video.VIDEO,"video_sha256"),
    "studio-preview":(studio_preview,"studio",studio_preview.VIDEO,"video_sha256"),
    "neural-studio":(studio_neural,"studio",studio_neural.VIDEO,"video_sha256"),
    "mixed-neural-studio":(v4_mixed_video,"export",v4_mixed_video.VIDEO,"video_sha256"),
}
BROWSER_LIMIT=128*1024*1024


def _locked(folder):
    p=folder/projects.LOCK
    return p.exists() or p.is_symlink()


def media_check(root,pid,kind):
    if kind not in MEDIA:raise ValueError("Unknown supported media kind")
    folder=projects.project(root,pid)
    if _locked(folder):raise ValueError("Project operation lock present; inspect after it stops")
    module,key,filename,hash_key=MEDIA[kind]
    _,dest,_,_,_,_=v4_audio._context(root,pid)
    is_mixed_studio=kind=="mixed-neural-studio"
    receipt=(module.inspect(root,pid,studio=True) if is_mixed_studio else module.inspect(root,pid))[key]
    path=dest/(v4_mixed_video.STUDIO_FOLDER if is_mixed_studio else module.FOLDER)/filename
    projects._plain(path,directory=False)
    size=path.stat().st_size
    sha=source.digest(path)
    if sha!=receipt[hash_key] or _locked(folder):raise ValueError("Media or operation state changed during check")
    return {"project_id":pid,"kind":kind,"local_path":str(path),"filename":filename,
            "bytes":size,"sha256":sha,"mime":"audio/wav" if filename.endswith(".wav") else "video/mp4",
            "browser_check_supported":size<=BROWSER_LIMIT,"browser_limit_bytes":BROWSER_LIMIT,
            "structural_audit_passed":True,"human_quality_independently_verified":False,
            "publication_approved":False,"http_media_served":False}


def estimate_from_records(rows,done,targets,records,scope,mode):
    """Rate per source second, same version/path scope, distinct completed units.

    Range is observed extrema projected onto remaining durations, not a
    confidence interval; initialization overhead and CPU changes can dominate.
    """
    if mode not in ("pilot","batch"):raise ValueError("Unknown neural timing mode")
    planned={r["id"]:(r["end_frame"]-r["start_frame"])/16000 for r in rows}
    eligible=set(targets) if mode=="pilot" else set(planned)-set(targets)
    remaining=sorted(eligible-set(done))
    result={"mode":mode,"remaining_chunks":len(remaining),"remaining_source_seconds":round(sum(planned[k] for k in remaining),3),
            "estimate_available":False,"live_eta_available":False,"historical_only":True,
            "includes_future_human_review_time":False}
    if not remaining:return {**result,"reason":"No remaining chunks in this stage"}
    observations={}
    for row in sorted(records,key=lambda r:r["utc"]):
        unit=row["unit"]
        if row["scope"]==scope and row["action"]=="neural_"+mode and unit in eligible and unit in done and row["seconds"]>0 and planned[unit]>0:
            observations[unit]=row["seconds"]/planned[unit]
    rates=list(observations.values())
    result["matching_completed_observations"]=len(rates)
    if len(rates)<3:return {**result,"reason":"At least three distinct matching completed chunks required"}
    seconds=result["remaining_source_seconds"]
    return {**result,"estimate_available":True,"estimated_seconds":round(median(rates)*seconds),
            "observed_rate_range_seconds":[round(min(rates)*seconds),round(max(rates)*seconds)],
            "reason":"Historical extrapolation; model path scope is not proof of unchanged hardware or model contents"}


def estimate(root,pid,state=None):
    folder=projects.project(root,pid)
    if _locked(folder):return {"estimate_available":False,"live_eta_available":False,"reason":"Project operation lock present"}
    state=v4_readiness.inspect(root,pid) if state is None else state
    stage=state["stage"]
    if stage not in ("pilot_required","neural_batch_required"):
        return {"estimate_available":False,"live_eta_available":False,"reason":"No eligible neural rendering stage; respect current prerequisite"}
    _,dest,binding,rows,targets=v4_neural._context(root,pid)
    done=v4_neural._scan(dest,binding,rows)
    if any(r["test_fixture_only"] for r in done.values()):
        return {"estimate_available":False,"live_eta_available":False,"reason":"Synthetic clips are not production timing evidence"}
    try:paths=model_config.read(root,"sadtalker")
    except (OSError,ValueError):return {"estimate_available":False,"live_eta_available":False,"reason":"Valid saved SadTalker paths required"}
    scope=source.json_digest({"binding":binding,"paths":{k:str(v) for k,v in paths.items()}})
    records=v4_progress.records(root,pid)
    result=estimate_from_records(rows,done,targets,records,scope,"pilot" if stage=="pilot_required" else "batch")
    if _locked(folder):return {"estimate_available":False,"live_eta_available":False,"reason":"Project operation state changed"}
    return result


def inspect(root,pid):
    state=v4_readiness.inspect(root,pid)
    return {"project_id":pid,"readiness":state,"timing":v4_progress.inspect(root,pid),
            "neural_estimate":estimate(root,pid,state),"model_configuration":model_config.status(root),
            "supported_media_kinds":list(MEDIA),"read_only":True,"publication_approved":False}
