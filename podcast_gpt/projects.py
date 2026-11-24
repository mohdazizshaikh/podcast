"""Independent V4 planning projects; never mutate fixed V3 source artifacts."""
from __future__ import annotations

import os
import re
import stat
import uuid
from contextlib import contextmanager
from pathlib import Path

from . import episode_plan, source

ID_RE=re.compile(r"[0-9a-f]{32}")
FOLDER="v4-projects"
REQUEST="request.json"
PLAN="outline.json"
EVIDENCE="input-evidence.json"
LOCK=".project-exclusive.lock"


def _plain(path:Path,*,directory=True,missing=False):
    try:s=path.lstat()
    except FileNotFoundError:
        if missing:return
        raise ValueError("Missing V4 project path") from None
    if stat.S_ISLNK(s.st_mode) or getattr(s,"st_file_attributes",0)&0x400:
        raise ValueError("V4 project symlink/reparse point refused")
    if not (stat.S_ISDIR(s.st_mode) if directory else stat.S_ISREG(s.st_mode)):
        raise ValueError("Unexpected V4 project path type")


def base(root:Path,*,create=False):
    raw=Path(root).expanduser().absolute()
    # Check every existing component, not merely the resolved final path.
    for p in reversed((raw,*raw.parents)):
        if p.exists() or p.is_symlink():_plain(p)
    root=source.workspace_path(raw)
    folder=root/FOLDER
    _plain(folder,missing=True)
    if create:
        folder.mkdir(parents=True,exist_ok=True)
        _plain(folder)
    return folder


def project(root:Path,pid:str):
    if not isinstance(pid,str) or not ID_RE.fullmatch(pid):
        raise ValueError("Invalid V4 project ID")
    folder=base(root)
    _plain(folder)
    path=folder/pid
    _plain(path)
    source.workspace_path(path)
    return path


@contextmanager
def exclusive(folder:Path):
    _plain(folder)
    lock=folder/LOCK
    marker=uuid.uuid4().hex
    try:
        with lock.open("x",encoding="ascii") as f:
            f.write(marker);f.flush();os.fsync(f.fileno())
    except FileExistsError:
        raise ValueError("V4 operation active or interrupted; inspect lock manually") from None
    try:yield
    finally:
        try:
            _plain(lock,directory=False)
            if lock.read_text(encoding="ascii")==marker:lock.unlink()
        except (OSError,ValueError,UnicodeError):pass


def create(root:Path,data:dict):
    req=episode_plan.validate_request(data)
    folder=base(root,create=True)
    pid=uuid.uuid4().hex
    dest=folder/pid
    dest.mkdir()
    with exclusive(dest):
        source.atomic_json(dest/REQUEST,req,new=True)
    return {"project_id":pid,"request":req,"stage":"request_saved","publication_approved":False}


def load(root:Path,pid:str):
    folder=project(root,pid)
    _plain(folder/REQUEST,directory=False)
    return episode_plan.validate_request(source.read_json(folder/REQUEST,64_000))


def read_evidence(folder,req):
    from . import ingestion
    p=folder/EVIDENCE
    if not p.exists() and not p.is_symlink():return None
    _plain(p,directory=False)
    if req["input_kind"]=="topic":raise ValueError("Unexpected source evidence for topic")
    wrapper=source.read_json(p,100_000)
    if wrapper.get("request_sha256")!=source.json_digest(req):
        raise ValueError("Source evidence request binding differs")
    value=ingestion.validate(wrapper.get("evidence"),req["input_kind"])
    if wrapper.get("evidence_sha256")!=source.json_digest(value):
        raise ValueError("Source evidence hash differs")
    return value


def import_source(root,pid,**options):
    from . import ingestion
    folder=project(root,pid)
    with exclusive(folder):
        req=load(root,pid)
        for name in (PLAN,EVIDENCE):
            p=folder/name
            if p.exists() or p.is_symlink():raise ValueError("Existing source/outline cannot be overwritten")
        evidence=ingestion.extract(req["input_kind"],**options)
        if load(root,pid)!=req:raise ValueError("Project request changed during source import")
        source.atomic_json(folder/EVIDENCE,{"request_sha256":source.json_digest(req),
            "evidence_sha256":source.json_digest(evidence),"evidence":evidence},new=True)
        return {"project_id":pid,"stage":"source_imported","input_kind":evidence["kind"],
                "text_characters":len(evidence["text"]),"raw_sha256":evidence["raw_sha256"],
                "text_sha256":evidence["text_sha256"],"live_research_performed":False}


def inspect(root:Path,pid:str):
    folder=project(root,pid)
    req=load(root,pid)
    result={"project_id":pid,"request":req,"stage":"request_saved","publication_approved":False}
    evidence=read_evidence(folder,req)
    binding=source.json_digest(evidence) if evidence is not None else None
    if evidence is not None:
        result.update(stage="source_imported",source={"kind":evidence["kind"],"locator":evidence["locator"],"text_sha256":evidence["text_sha256"],"text_characters":len(evidence["text"])})
    p=folder/PLAN
    if p.exists() or p.is_symlink():
        _plain(p,directory=False)
        saved=source.read_json(p,200_000)
        legacy=saved.get("schema")==1 and req["input_kind"]=="topic" and binding is None
        if (not legacy and (saved.get("schema")!=2 or saved.get("evidence_sha256")!=binding)
                or saved.get("request_sha256")!=source.json_digest(req)
                or (req["input_kind"]!="topic" and evidence is None)):
            raise ValueError("Saved outline does not match the project request")
        value=episode_plan.validate_plan(saved.get("outline"),req)
        if saved.get("outline_sha256")!=source.json_digest(value):
            raise ValueError("Saved outline hash differs")
        if saved.get("provider") not in ("openrouter","gemini","ollama"):
            raise ValueError("Unknown saved provider")
        result.update(stage="outline_saved",outline=value,provider=saved["provider"])
    return result


def list_projects(root:Path):
    folder=base(root)
    if not folder.exists():return {"projects":[],"blocked":[]}
    _plain(folder)
    rows=[];blocked=[]
    for child in sorted(folder.iterdir()):
        if not ID_RE.fullmatch(child.name):continue
        try:
            state=inspect(root,child.name)
            req=state["request"]
            rows.append({"project_id":child.name,"topic":req["topic"],"language":req["language"],
                         "duration_minutes":req["duration_minutes"],"stage":state["stage"]})
        except (OSError,ValueError,TypeError,KeyError):
            blocked.append(child.name)
    return {"projects":rows,"blocked":blocked}


def generate_outline(root:Path,pid:str,**options):
    folder=project(root,pid)
    with exclusive(folder):
        req=load(root,pid)
        dest=folder/PLAN
        if dest.exists() or dest.is_symlink():raise ValueError("Saved outline exists; create a new project for another version")
        evidence=read_evidence(folder,req)
        if req["input_kind"]!="topic" and evidence is None:
            raise ValueError("Import source evidence before planning")
        if evidence is not None:
            result=episode_plan.plan(req,evidence=evidence,**options)
        else:
            result=episode_plan.plan(req,**options)
        if load(root,pid)!=req or read_evidence(folder,req)!=evidence:
            raise ValueError("Project request or source evidence changed while planning")
        value=episode_plan.validate_plan(result["result"],req)
        provider=result["provider"]
        if provider not in ("openrouter","gemini","ollama"):raise ValueError("Unknown provider")
        source.atomic_json(dest,{"schema":2,"request_sha256":source.json_digest(req),
            "evidence_sha256":source.json_digest(evidence) if evidence is not None else None,
            "outline_sha256":source.json_digest(value),"outline":value,"provider":provider},new=True)
        return {"project_id":pid,"stage":"outline_saved","outline":value,"provider":provider,
                "publication_approved":False,"rendering_compatibility_verified":False}
