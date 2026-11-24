"""Verbatim structured custom script import using existing timed-unit constraints."""
import json
from . import projects, source, episode_plan, script_generation as sg

PROVIDER="manual_source"
ACK="I_AUTHORIZE_VERBATIM_IMPORT_OF_THIS_STRUCTURED_SCRIPT"


def parse(req,evidence):
    if req["input_kind"]!="custom_script" or req["research_mode"]!="knowledge" or evidence is None:
        raise ValueError("Structured import requires a captured custom_script source and knowledge mode")
    try:data=json.loads(evidence["text"])
    except (ValueError,TypeError) as exc:raise ValueError("Custom source must contain timed script JSON") from exc
    if not isinstance(data,dict) or set(data)!={"title","minutes"} or not isinstance(data["minutes"],list) or len(data["minutes"])!=req["duration_minutes"]:
        raise ValueError("Supply title and one minutes entry per requested minute")
    outline=episode_plan.validate_plan({"title":data["title"],"sections":[{"heading":"Imported script",
        "minutes":req["duration_minutes"],"summary":"User-supplied verbatim timed dialogue","presenters":req["presenters"]}]},req)
    plan=sg.units(outline);previous=[];values=[]
    for unit,value in zip(plan,data["minutes"]):
        checked=sg.validate_dialogue(value,unit,previous)
        if checked!=value:raise ValueError("Use exact trimmed dialogue text; import never rewrites text")
        values.append(checked);previous.extend(checked["turns"])
    return outline,plan,values


def import_saved(root,pid,*,acknowledgment):
    if acknowledgment!=ACK:raise ValueError("Explicit verbatim import acknowledgment required")
    folder=projects.project(root,pid)
    with projects.exclusive(folder):
        req=projects.load(root,pid);evidence=projects.read_evidence(folder,req)
        outline,plan,values=parse(req,evidence)
        target=folder/projects.PLAN
        state=projects._inspect_planning(root,pid)
        if state["stage"]=="outline_saved":
            if state["provider"]!=PROVIDER or state["outline"]!=outline:raise ValueError("Existing non-manual outline cannot be overwritten")
        else:
            for name in (sg.PARTS,sg.FINAL):
                if (folder/name).exists() or (folder/name).is_symlink():raise ValueError("Existing script artifacts require manual inspection")
            source.atomic_json(target,{"schema":2,"request_sha256":source.json_digest(req),
                "evidence_sha256":source.json_digest(evidence),"outline_sha256":source.json_digest(outline),
                "outline":outline,"provider":PROVIDER},new=True)
        _,_,_,_,binding=sg._context(root,pid)
        parts,turns=sg._read_parts(folder,binding,plan)
        before=len(parts)
        dest=folder/sg.PARTS
        dest.mkdir(exist_ok=True);projects._plain(dest)
        for unit,value in zip(plan[before:],values[before:]):
            receipt={"schema":1,"binding":binding,"unit":unit,"dialogue":value,
                     "dialogue_sha256":source.json_digest(value),"provider":PROVIDER}
            source.atomic_json(dest/(unit["id"]+".json"),receipt,new=True)
            parts.append(receipt);turns.extend(value["turns"])
        saved=sg._check_final(folder,binding,plan,parts,turns)
        if saved is None:
            saved=sg._assembled(binding,plan,parts,turns)
            source.atomic_json(folder/sg.FINAL,saved,new=True)
        return {"project_id":pid,**sg._status(folder,binding,plan,parts,turns),
                "new_units":len(parts)-before,"script_sha256":source.json_digest(saved),
                "verbatim_import":True,"ai_calls":0}
