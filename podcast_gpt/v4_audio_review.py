"""Explicit human listening observations for an exact verified master."""
from __future__ import annotations

from . import projects, source, v4_master as master

REVIEW="audio-review.json"
ACK="I_LISTENED_TO_THIS_ENTIRE_MASTER_AND_ALL_TURNS"
CRITERIA=("text_and_pronunciation","voice_identity_and_consistency","clarity_and_levels","timing_and_pauses","audio_usage_rights")


def _context(root,pid):
    folder,dest,binding,timeline=master._context(root,pid)
    receipt=master._audit(dest,binding,timeline)
    return folder,dest,timeline,source.json_digest(receipt)


def _validate(data,timeline,sha):
    if (not isinstance(data,dict) or set(data)!={"schema","master_sha256","turns","criteria"}
            or data["schema"]!=1 or data["master_sha256"]!=sha):
        raise ValueError("Audio review template is stale or malformed")
    turns=data["turns"];criteria=data["criteria"]
    if not isinstance(turns,dict) or set(turns)!={r["turn_id"] for r in timeline["rows"]}:
        raise ValueError("Review every measured audio turn")
    if not isinstance(criteria,dict) or set(criteria)!=set(CRITERIA):
        raise ValueError("Review every audio quality criterion")
    if any(v not in ("PASS","FAIL") for v in [*turns.values(),*criteria.values()]):
        raise ValueError("Set every audio observation to PASS or FAIL, not UNREVIEWED")
    return data


def _read(dest,timeline,sha):
    path=dest/REVIEW
    if not path.exists() and not path.is_symlink():return None
    projects._plain(path,directory=False)
    saved=source.read_json(path,300_000)
    if set(saved)!={"observations","observations_sha256","acknowledgment"} or saved["acknowledgment"]!=ACK:
        raise ValueError("Invalid audio review receipt")
    data=_validate(saved["observations"],timeline,sha)
    if saved["observations_sha256"]!=source.json_digest(data):raise ValueError("Audio review hash differs")
    return saved


def _status(pid,sha,saved):
    bad_turns=[];bad_criteria=[]
    if saved is not None:
        obs=saved["observations"]
        bad_turns=sorted(k for k,v in obs["turns"].items() if v=="FAIL")
        bad_criteria=sorted(k for k,v in obs["criteria"].items() if v=="FAIL")
    passed=saved is not None and not bad_turns and not bad_criteria
    return {"project_id":pid,"master_receipt_sha256":sha,
            "review_status":"PASS" if passed else "FAIL" if saved is not None else "UNREVIEWED",
            "failed_turn_ids":bad_turns,"failed_criteria":bad_criteria,
            "human_audio_self_attested_pass":passed,"independent_voice_quality_verified":False,
            "publication_approved":False}


def inspect(root,pid):
    _,dest,timeline,sha=_context(root,pid)
    return _status(pid,sha,_read(dest,timeline,sha))


def template(root,pid):
    folder=projects.project(root,pid)
    with projects.exclusive(folder):
        _,dest,timeline,sha=_context(root,pid)
        if _read(dest,timeline,sha) is not None:raise ValueError("Immutable audio review already recorded")
        path=folder/("audio-review-"+sha+".json")
        if path.exists() or path.is_symlink():raise ValueError("Audio review template already exists")
        data={"schema":1,"master_sha256":sha,
              "turns":{r["turn_id"]:"UNREVIEWED" for r in timeline["rows"]},
              "criteria":{k:"UNREVIEWED" for k in CRITERIA}}
        source.atomic_json(path,data,new=True)
        return {"project_id":pid,"template_path":str(path),"master_wav_path":str(dest/master.FOLDER/master.WAV),
                "review_status":"UNREVIEWED"}


def record(root,pid,*,acknowledgment):
    if acknowledgment!=ACK:raise ValueError("Explicit complete listening acknowledgment required")
    folder=projects.project(root,pid)
    with projects.exclusive(folder):
        _,dest,timeline,sha=_context(root,pid)
        if _read(dest,timeline,sha) is not None:raise ValueError("Existing audio review cannot be overwritten")
        path=folder/("audio-review-"+sha+".json")
        projects._plain(path,directory=False)
        value=_validate(source.read_json(path,300_000),timeline,sha)
        saved={"observations":value,"observations_sha256":source.json_digest(value),"acknowledgment":ACK}
        source.atomic_json(dest/REVIEW,saved,new=True)
        return _status(pid,sha,saved)


def require_pass(root,pid):
    _,dest,timeline,sha=_context(root,pid)
    saved=_read(dest,timeline,sha)
    if not _status(pid,sha,saved)["human_audio_self_attested_pass"]:
        raise ValueError("Current master requires explicit complete human listening PASS")
    return source.json_digest(saved)
