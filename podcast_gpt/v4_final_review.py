"""Explicit full-episode self-attestation, bound to the audited candidate."""
from . import projects, source, v4_export as export

RECORD="final-video-review.json"
ACK="I_WATCHED_AND_REVIEWED_THE_ENTIRE_CURRENT_EPISODE"
CRITERIA=("lip_sync","face_identity","speech_and_audio","subtitles","transitions")
GLOBAL=("complete_episode_watched","content_and_media_rights","overall_quality")


def _context(root,pid):
    folder,dest,timeline,turns,cast,rows,done,bound=export._context(root,pid)
    receipt=export._audit(dest,timeline,turns,bound,export.frame_plan(timeline,rows))
    if receipt["test_fixture_only"]:raise ValueError("Synthetic candidate cannot receive production review")
    return folder,dest,receipt,turns


def _validate(value,receipt,turns):
    if not isinstance(value,dict) or set(value)!={"schema","candidate_sha256","turns","criteria"} or value["schema"]!=1 or value["candidate_sha256"]!=source.json_digest(receipt):
        raise ValueError("Final review template is stale or invalid")
    obs=value["turns"];criteria=value["criteria"]
    if not isinstance(obs,dict) or set(obs)!={t["id"] for t in turns}:
        raise ValueError("Review every current script turn")
    if not isinstance(criteria,dict) or set(criteria)!=set(GLOBAL):
        raise ValueError("Review all global criteria")
    for row in [criteria,*obs.values()]:
        if not isinstance(row,dict) or (row is not criteria and set(row)!=set(CRITERIA)) or any(v not in ("PASS","FAIL") for v in row.values()):
            raise ValueError("Set every observation to PASS or FAIL, not UNREVIEWED")
    return value


def _read(dest,receipt,turns):
    path=dest/RECORD
    if not path.exists() and not path.is_symlink():return None
    projects._plain(path,directory=False)
    saved=source.read_json(path,2_000_000)
    if set(saved)!={"observations","observations_sha256","acknowledgment"} or saved["acknowledgment"]!=ACK:
        raise ValueError("Invalid final review receipt")
    value=_validate(saved["observations"],receipt,turns)
    if source.json_digest(value)!=saved["observations_sha256"]:raise ValueError("Final review hash differs")
    return saved


def _summary(pid,receipt,saved):
    bad=[];criteria=[]
    if saved:
        value=saved["observations"]
        bad=sorted(k for k,row in value["turns"].items() if "FAIL" in row.values())
        criteria=sorted(k for k,v in value["criteria"].items() if v=="FAIL")
    passed=saved is not None and not bad and not criteria
    return {"project_id":pid,"candidate_sha256":source.json_digest(receipt),
            "review_status":"PASS" if passed else "FAIL" if saved else "UNREVIEWED",
            "failed_turn_ids":bad,"failed_criteria":criteria,"human_video_self_attested_pass":passed,
            "independent_lipsync_quality_verified":False,"publication_approved":False}


def inspect(root,pid):
    _,dest,receipt,turns=_context(root,pid)
    return _summary(pid,receipt,_read(dest,receipt,turns))


def template(root,pid):
    folder=projects.project(root,pid)
    with projects.exclusive(folder):
        _,dest,receipt,turns=_context(root,pid)
        if _read(dest,receipt,turns):raise ValueError("Final review already recorded")
        sha=source.json_digest(receipt)
        path=folder/("final-review-"+sha+".json")
        value={"schema":1,"candidate_sha256":sha,"turns":{t["id"]:{k:"UNREVIEWED" for k in CRITERIA} for t in turns},
               "criteria":{k:"UNREVIEWED" for k in GLOBAL}}
        source.atomic_json(path,value,new=True)
        return {"project_id":pid,"template_path":str(path),"video_path":str(dest/export.FOLDER/export.VIDEO),
                "subtitle_path":str(dest/export.FOLDER/export.SRT),"review_status":"UNREVIEWED"}


def record(root,pid,*,acknowledgment):
    if acknowledgment!=ACK:raise ValueError("Explicit full-episode viewing acknowledgment required")
    folder=projects.project(root,pid)
    with projects.exclusive(folder):
        _,dest,receipt,turns=_context(root,pid)
        if _read(dest,receipt,turns):raise ValueError("Final review cannot be overwritten")
        path=folder/("final-review-"+source.json_digest(receipt)+".json")
        projects._plain(path,directory=False)
        value=_validate(source.read_json(path,2_000_000),receipt,turns)
        saved={"observations":value,"observations_sha256":source.json_digest(value),"acknowledgment":ACK}
        source.atomic_json(dest/RECORD,saved,new=True)
        return _summary(pid,receipt,saved)
