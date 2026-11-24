"""Private versioned manual dialogue editing and explicit human self-attestation.

Never overwrites generated draft or review receipts. Approval is for the
specific text version only; it is not independent fact/rights/audio QA.
"""
from __future__ import annotations

import re
from pathlib import Path

from . import projects, research, script_generation as sg, source

FOLDER="script-revisions"
MAX_REVISIONS=20
ACK="I_REVIEWED_THIS_ENTIRE_SCRIPT_VERSION"
CRITERIA=("accuracy_and_source_context","language_and_dialogue","estimated_timing_and_continuity","content_rights")
DECISIONS=("PASS","FAIL")


def _context(root,pid):
    folder,req,evidence,outline,binding=sg._context(root,pid)
    pack=research.read_pack(folder,req)
    plan=sg.units(outline)
    parts,turns=sg._read_parts(folder,binding,plan,pack)
    draft=sg._check_final(folder,binding,plan,parts,turns)
    if draft is None:raise ValueError("Finalize generated script before manual editing or review")
    sizes=[len(p["dialogue"]["turns"]) for p in parts]
    return folder,draft,plan,sizes,pack


def _validate_turns(rows,draft,plan,sizes,pack):
    if not isinstance(rows,list) or len(rows)!=len(draft["turns"]):
        raise ValueError("Keep the original number of turns; create a new project to restructure")
    checked=[];previous=[];offset=0
    for unit,count in zip(plan,sizes):
        chunk=rows[offset:offset+count]
        expected=draft["turns"][offset:offset+count]
        values=[]
        for row,old in zip(chunk,expected):
            if not isinstance(row,dict) or row.get("id")!=old["id"]:
                raise ValueError("Turn IDs and ordering must remain unchanged")
            values.append({k:v for k,v in row.items() if k!="id"})
        val=sg.validate_dialogue({"turns":values},unit,previous,research_pack=pack)["turns"]
        previous.extend(val)
        checked.extend({"id":old["id"],**turn} for old,turn in zip(expected,val))
        offset+=count
    return checked


def _review_values(data,turns):
    if not isinstance(data,dict) or set(data)!={"turn_decisions","criteria"}:
        raise ValueError("Review requires turn decisions and global criteria")
    decisions=data["turn_decisions"];criteria=data["criteria"]
    if not isinstance(decisions,dict) or set(decisions)!={t["id"] for t in turns}:
        raise ValueError("Review must contain every current turn ID")
    if not isinstance(criteria,dict) or set(criteria)!=set(CRITERIA):
        raise ValueError("Review must contain all global criteria")
    if any(v not in DECISIONS for v in [*decisions.values(),*criteria.values()]):
        raise ValueError("Complete all review decisions with PASS or FAIL; no UNREVIEWED values")
    return {"turn_decisions":decisions,"criteria":criteria}


def _version_name(number):
    return f"r{number:03}"


def _scan(folder,draft,plan,sizes,pack):
    base=source.json_digest(draft)
    versions=[{"number":0,"version_sha256":base,"turns":draft["turns"]}]
    dest=folder/FOLDER
    names=set()
    if dest.exists() or dest.is_symlink():
        projects._plain(dest)
        for item in dest.iterdir():
            projects._plain(item,directory=False)
            if not re.fullmatch(r"r[0-9]{3}(?:-review)?\.json",item.name):
                raise ValueError("Unexpected or interrupted revision artifact; inspect manually")
            names.add(item.name)
    revision_names={n for n in names if not n.endswith("-review.json")}
    if len(revision_names)>MAX_REVISIONS:raise ValueError("Revision limit exceeded")
    for i in range(1,len(revision_names)+1):
        name=_version_name(i)+".json"
        if name not in names:raise ValueError("Script revision chain has a gap")
        saved=source.read_json(dest/name,sg.MAX_FINAL_BYTES)
        expected={"schema":1,"number":i,"draft_sha256":base,"parent_sha256":versions[-1]["version_sha256"]}
        if set(saved)!=set(expected)|{"turns","turns_sha256"} or any(saved.get(k)!=v for k,v in expected.items()):
            raise ValueError("Revision chain binding differs")
        turns=_validate_turns(saved["turns"],draft,plan,sizes,pack)
        if turns!=saved["turns"] or saved["turns_sha256"]!=source.json_digest(turns):
            raise ValueError("Revision dialogue hash differs")
        versions.append({"number":i,"version_sha256":source.json_digest(saved),"turns":turns})
    reviews={}
    for name in names-revision_names:
        i=int(name[1:4])
        if i>=len(versions):raise ValueError("Review has no matching script version")
        saved=source.read_json(dest/name,200_000)
        expected={"schema":1,"version":i,"version_sha256":versions[i]["version_sha256"],"acknowledgment":ACK}
        if set(saved)!=set(expected)|{"observations","observations_sha256"} or any(saved.get(k)!=v for k,v in expected.items()):
            raise ValueError("Review is stale or version binding differs")
        observations=_review_values(saved["observations"],versions[i]["turns"])
        if saved["observations_sha256"]!=source.json_digest(observations):
            raise ValueError("Review observations hash differs")
        reviews[i]=observations
    return versions,reviews


def _state(root,pid):
    folder,draft,plan,sizes,pack=_context(root,pid)
    versions,reviews=_scan(folder,draft,plan,sizes,pack)
    return folder,draft,plan,sizes,pack,versions,reviews


def _status(pid,versions,reviews):
    current=versions[-1]
    observations=reviews.get(current["number"])
    failed=[];criteria=[]
    if observations is not None:
        failed=sorted(k for k,v in observations["turn_decisions"].items() if v=="FAIL")
        criteria=sorted(k for k,v in observations["criteria"].items() if v=="FAIL")
    approved=observations is not None and not failed and not criteria
    return {"project_id":pid,"version":current["number"],"version_sha256":current["version_sha256"],
            "turn_count":len(current["turns"]),"saved_revisions":len(versions)-1,
            "review_status":"PASS" if approved else "FAIL" if observations is not None else "UNREVIEWED",
            "failed_turns":failed,"failed_criteria":criteria,
            "human_script_self_attested_pass":approved,"independent_fact_check_verified":False,
            "measured_audio_seconds":None,"publication_approved":False}


def inspect(root,pid):
    *_,versions,reviews=_state(root,pid)
    return _status(pid,versions,reviews)


def current_script(root,pid,*,require_pass=False):
    *_,versions,reviews=_state(root,pid)
    status=_status(pid,versions,reviews)
    if require_pass and not status["human_script_self_attested_pass"]:
        raise ValueError("Current script version requires an explicit complete human PASS review")
    return {**status,"turns":versions[-1]["turns"]}


def template(root,pid,*,review=False):
    folder=projects.project(root,pid)
    with projects.exclusive(folder):
        *_,versions,reviews=_state(root,pid)
        current=versions[-1]
        name=("review-" if review else "edit-")+_version_name(current["number"])+".json"
        path=folder/name
        if path.exists() or path.is_symlink():raise ValueError("Editable template exists; do not overwrite it")
        if review:
            if current["number"] in reviews:raise ValueError("Current version already has immutable review")
            value={"schema":1,"version":current["number"],"version_sha256":current["version_sha256"],
                   "observations":{"turn_decisions":{t["id"]:"UNREVIEWED" for t in current["turns"]},
                                   "criteria":{k:"UNREVIEWED" for k in CRITERIA}}}
        else:
            if current["number"]>=MAX_REVISIONS:raise ValueError("Revision limit reached; create another project")
            value={"schema":1,"version":current["number"],"version_sha256":current["version_sha256"],
                   "turns":current["turns"]}
        source.atomic_json(path,value,new=True)
        return {**_status(pid,versions,reviews),"template_path":str(path)}


def _template_input(folder,current,*,review=False,input_file=None):
    if input_file is None:
        path=folder/(("review-" if review else "edit-")+_version_name(current["number"])+".json")
        projects._plain(path,directory=False)
        data=source.read_json(path,sg.MAX_FINAL_BYTES)
    else:
        import json
        from . import characters
        path=Path(input_file).expanduser().absolute()
        source.workspace_path(path.parent)
        data=json.loads(characters._read_file(path,sg.MAX_FINAL_BYTES).decode("utf-8-sig"))
        if not isinstance(data,dict):raise ValueError("Editable template must be a JSON object")
    field="observations" if review else "turns"
    if (set(data)!={"schema","version","version_sha256",field} or data.get("schema")!=1
            or data.get("version")!=current["number"] or data.get("version_sha256")!=current["version_sha256"]):
        raise ValueError("Editable template is stale or malformed")
    return data[field]


def revise(root,pid,*,input_file=None):
    folder=projects.project(root,pid)
    with projects.exclusive(folder):
        folder,draft,plan,sizes,pack,versions,reviews=_state(root,pid)
        current=versions[-1]
        number=current["number"]+1
        if number>MAX_REVISIONS:raise ValueError("Revision limit reached")
        turns=_validate_turns(_template_input(folder,current,input_file=input_file),draft,plan,sizes,pack)
        if turns==current["turns"]:raise ValueError("No script changes; edit the template before saving")
        saved={"schema":1,"number":number,"draft_sha256":source.json_digest(draft),
               "parent_sha256":current["version_sha256"],"turns":turns,"turns_sha256":source.json_digest(turns)}
        dest=folder/FOLDER
        dest.mkdir(exist_ok=True);projects._plain(dest)
        source.atomic_json(dest/(_version_name(number)+".json"),saved,new=True)
        return inspect(root,pid)


def record(root,pid,*,acknowledgment,input_file=None):
    if acknowledgment!=ACK:raise ValueError("Explicit full script review acknowledgment required")
    folder=projects.project(root,pid)
    with projects.exclusive(folder):
        *_,versions,reviews=_state(root,pid)
        current=versions[-1];i=current["number"]
        if i in reviews:raise ValueError("Existing review cannot be overwritten; revise script to obtain a new review")
        observations=_review_values(_template_input(folder,current,review=True,input_file=input_file),current["turns"])
        saved={"schema":1,"version":i,"version_sha256":current["version_sha256"],"acknowledgment":ACK,
               "observations":observations,"observations_sha256":source.json_digest(observations)}
        dest=folder/FOLDER
        dest.mkdir(exist_ok=True);projects._plain(dest)
        source.atomic_json(dest/(_version_name(i)+"-review.json"),saved,new=True)
        return inspect(root,pid)
