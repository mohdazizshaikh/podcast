"""Explicit frozen prior-episode dialogue excerpts for local drafting.

No automatic cross-project scanning, cloud disclosure, personal facts,
or inherited approval. Selected immutable character IDs must match.
"""
import re
from . import projects,characters,source,script_review

FILE="episode-continuity.json"
ACK="I_AUTHORIZE_SELECTED_REVIEWED_DIALOGUE_FOR_LOCAL_DRAFTING"
MAX_TURNS=8


def _sha(value):
    return isinstance(value,str) and re.fullmatch("[0-9a-f]{64}",value) is not None


def _validate(root,pid,value):
    fields={"schema","request_sha256","cast_sha256","prior_project_id","prior_script_sha256","prior_cast_sha256","excerpts"}
    if not isinstance(value,dict) or set(value)!=fields or value["schema"]!=1:raise ValueError("Invalid continuity snapshot")
    req=projects.load(root,pid);cast=characters.read_cast(root,pid)
    if cast is None or req["input_kind"]=="custom_script" or value["request_sha256"]!=source.json_digest(req) or value["cast_sha256"]!=cast["cast_sha256"]:
        raise ValueError("Continuity current project/cast binding differs")
    if not isinstance(value["prior_project_id"],str) or not projects.ID_RE.fullmatch(value["prior_project_id"]) or value["prior_project_id"]==pid:
        raise ValueError("Invalid prior project ID")
    if not _sha(value["prior_script_sha256"]) or not _sha(value["prior_cast_sha256"]):raise ValueError("Invalid prior version binding")
    by_id={row["character_id"]:row for row in cast["cast"]}
    rows=value["excerpts"]
    if not isinstance(rows,list) or not 1<=len(rows)<=MAX_TURNS:raise ValueError("Select 1–8 prior dialogue turns")
    seen=set()
    for row in rows:
        if not isinstance(row,dict) or set(row)!={"character_id","record_sha256","speaker","prior_turn_id","text"}:raise ValueError("Invalid continuity excerpt")
        cid=row["character_id"]
        if not isinstance(cid,str) or cid not in by_id or row["speaker"]!=by_id[cid]["speaker"] or row["record_sha256"]!=by_id[cid]["record_sha256"]:
            raise ValueError("Continuity character version differs")
        tid=row["prior_turn_id"];text=row["text"]
        if not isinstance(tid,str) or not re.fullmatch(r"\d{4}",tid) or tid in seen or not isinstance(text,str) or not 1<=len(text)<=600 or any(ord(c)<32 or ord(c)==127 for c in text):
            raise ValueError("Invalid or duplicate prior dialogue")
        seen.add(tid)
    return value


def read(folder):
    path=folder/FILE
    if not path.exists() and not path.is_symlink():return None
    projects._plain(path,directory=False)
    data=source.read_json(path,64000)
    if set(data)!={"snapshot","sha256"} or source.json_digest(data["snapshot"])!=data["sha256"]:
        raise ValueError("Continuity snapshot hash differs")
    return _validate(folder.parent.parent,folder.name,data["snapshot"])


def enable(root,pid,prior_pid,turn_ids,*,acknowledgment):
    if acknowledgment!=ACK:raise ValueError("Explicit local continuity acknowledgment required")
    if pid==prior_pid:raise ValueError("Select another prior project")
    if not isinstance(turn_ids,list) or not 1<=len(turn_ids)<=MAX_TURNS or any(not isinstance(t,str) or not re.fullmatch(r"\d{4}",t) for t in turn_ids) or len(set(turn_ids))!=len(turn_ids):
        raise ValueError("Select 1–8 distinct prior turn IDs")
    from . import script_generation as sg
    folder=projects.project(root,pid);prior=projects.project(root,prior_pid)
    # Both nonblocking locks are held for a consistent snapshot.
    with projects.exclusive(folder),projects.exclusive(prior):
        for name in (FILE,sg.PARTS,sg.FINAL):
            if (folder/name).exists() or (folder/name).is_symlink():raise ValueError("Enable continuity before script drafting; no overwrite")
        req=projects.load(root,pid);cast=characters.read_cast(root,pid);old=characters.read_cast(root,prior_pid)
        if cast is None or old is None:raise ValueError("Assign both project casts first")
        if req["input_kind"]=="custom_script":raise ValueError("Continuity is for AI drafting, not verbatim custom scripts")
        current=script_review.current_script(root,prior_pid,require_pass=True)
        old_by_speaker={row["speaker"]:row for row in old["cast"]}
        new_by_id={row["character_id"]:row for row in cast["cast"]}
        excerpts=[]
        for turn in current["turns"]:
            if turn["id"] not in turn_ids:continue
            before=old_by_speaker[turn["speaker"]];after=new_by_id.get(before["character_id"])
            if after is None or after["record_sha256"]!=before["record_sha256"]:raise ValueError("Selected prior speaker has no matching immutable character version")
            excerpts.append({"character_id":after["character_id"],"record_sha256":after["record_sha256"],
                             "speaker":after["speaker"],"prior_turn_id":turn["id"],"text":turn["text"]})
        if len(excerpts)!=len(turn_ids):raise ValueError("Unknown prior dialogue turn")
        value=_validate(root,pid,{"schema":1,"request_sha256":source.json_digest(req),"cast_sha256":cast["cast_sha256"],
            "prior_project_id":prior_pid,"prior_script_sha256":current["version_sha256"],"prior_cast_sha256":old["cast_sha256"],"excerpts":excerpts})
        source.atomic_json(folder/FILE,{"snapshot":value,"sha256":source.json_digest(value)},new=True)
        return inspect(root,pid)


def inspect(root,pid):
    saved=read(projects.project(root,pid))
    return {"project_id":pid,"enabled":saved is not None,"snapshot":saved,
            "local_drafting_only":True,"frozen_prior_reviewed_version":True if saved else False,
            "automatic_memory_capture":False,"independent_fact_check_verified":False}
