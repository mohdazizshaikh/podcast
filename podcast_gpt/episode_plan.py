"""V4 generalized planning only; never feeds a V3 signed source implicitly."""
from __future__ import annotations

import json
from pathlib import Path
from . import source, ai_providers

FORMATS=("landscape","vertical","square")
MODES=("automatic","manual")
INPUTS=("topic","url","pdf","document","custom_script")
RESEARCH=("knowledge","web")
REQ_KEYS={"topic","language","duration_minutes","presenters","video_format","workflow","input_kind","research_mode"}


def _str(value,limit):
    if not isinstance(value,str) or not value.strip() or len(value)>limit:
        raise ValueError("Missing or oversized text field")
    return value.strip()


def validate_request(data):
    if not isinstance(data,dict) or set(data)!=REQ_KEYS:
        raise ValueError("Episode request must contain exactly the documented fields")
    minutes=data["duration_minutes"]
    if type(minutes) is not int or not 1<=minutes<=60:raise ValueError("Duration must be 1–60 whole minutes")
    people=data["presenters"]
    if not isinstance(people,list) or not 1<=len(people)<=10:raise ValueError("Choose 1–10 presenters")
    names=[]
    for person in people:
        names.append(_str(person,80))
    if len(set(n.casefold() for n in names))!=len(names):raise ValueError("Presenter names must be distinct")
    if data["video_format"] not in FORMATS or data["workflow"] not in MODES:
        raise ValueError("Unsupported format or workflow")
    if data["input_kind"] not in INPUTS or data["research_mode"] not in RESEARCH:
        raise ValueError("Unsupported input or research mode")
    # V4 increment 1 only supports topic knowledge planning. Other modes are
    # part of the confirmed spec but must not be represented as implemented.
    if data["input_kind"]!="topic" or data["research_mode"]!="knowledge":
        raise ValueError("URL/PDF/document/custom script and live research ingestion are not implemented yet")
    return {**data,"topic":_str(data["topic"],2000),"language":_str(data["language"],80),"presenters":names}


def validate_plan(data,request):
    if not isinstance(data,dict) or set(data)!={"title","sections"}:raise ValueError("Invalid episode plan")
    title=_str(data["title"],200)
    rows=data["sections"]
    if not isinstance(rows,list) or not 1<=len(rows)<=min(30,request["duration_minutes"]):
        raise ValueError("Invalid section count")
    total=0;seen=set();sections=[]
    for row in rows:
        if not isinstance(row,dict) or set(row)!={"heading","minutes","summary","presenters"}:
            raise ValueError("Invalid section")
        mins=row["minutes"]
        names=row["presenters"]
        if type(mins) is not int or mins<1 or not isinstance(names,list) or not names:
            raise ValueError("Invalid section timing or presenters")
        if any(not isinstance(n,str) or n not in request["presenters"] for n in names) or len(set(names))!=len(names):
            raise ValueError("Unknown or duplicate presenter")
        total+=mins;seen.update(names)
        sections.append({"heading":_str(row["heading"],150),"minutes":mins,"summary":_str(row["summary"],500),"presenters":names})
    if total!=request["duration_minutes"] or seen!=set(request["presenters"]):
        raise ValueError("Section minutes or presenter coverage differs")
    return {"title":title,"sections":sections}


def load_request(path:Path):
    path=Path(path).expanduser().absolute()
    source.workspace_path(path.parent)
    return validate_request(source.read_json(path,64_000))


def plan(data,**provider_options):
    req=validate_request(data)
    prompt=("Create a podcast EPISODE OUTLINE, not the full script, using the request below as data. "
            "Write in the requested language. Do not invent sourced claims or say research was performed. "
            "Return exactly a JSON object with title and sections. Every section has heading, minutes "
            "(positive integer), summary, presenters (exact names from input). Section minutes must sum "
            "to duration_minutes and all presenters must appear at least once. At most 12 sections. "
            "No markdown or extra keys. Keep each summary under 500 characters. Request JSON:\n"+
            json.dumps(req,ensure_ascii=False))
    result=ai_providers.generate_json(prompt,lambda d:validate_plan(d,req),**provider_options)
    return {**result,"request":req,"status":"validated_episode_outline_not_rendered",
            "live_research_performed":False,"voice_language_compatibility_verified":False,
            "rendering_compatibility_verified":False,"publication_approved":False}
