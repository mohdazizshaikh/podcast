"""Explicit local browser authoring; no arbitrary source paths or inference."""
import json
import re
import tempfile
from pathlib import Path
from . import projects, characters, portrait_brief, ingestion, model_config

JSON_LIMIT=32768
READ_ONLY=("character-list","character-show","cast-status","cast-choices","model-status")
ACTIONS=("character-list","character-show","character-create","cast-assign","cast-status","cast-choices",
         "source-url","model-configure","model-status")
UPLOADS={"portrait":characters.MAX_PORTRAIT,"source":ingestion.MAX_FILE}
ACK="I_AUTHORIZE_THIS_LOCAL_AUTHORING_ACTION"


def parse(raw):
    if not 1<=len(raw)<=JSON_LIMIT:raise ValueError("Invalid authoring request size")
    try:value=json.loads(raw.decode("utf-8"))
    except (ValueError,UnicodeError):raise ValueError("Invalid authoring JSON") from None
    if not isinstance(value,dict):raise ValueError("Expected JSON object")
    return value


def _keys(data,keys):
    if not isinstance(data,dict) or set(data)!=set(keys):raise ValueError("Unexpected authoring fields")


def _local_path(value):
    if not isinstance(value,str) or not 1<=len(value)<=2048 or any(ord(c)<32 for c in value):
        raise ValueError("Invalid local model path")
    # Reject explicit UNC/device paths and relative paths. Mapped volumes
    # may still be remote; this is not a network filesystem detector.
    if value.startswith(("\\\\","//")) or not Path(value).is_absolute():
        raise ValueError("Use absolute local model paths, not UNC/device paths")
    return Path(value)


def run(root,action,data,*,acknowledgment=None):
    if action not in ACTIONS:raise ValueError("Unknown authoring action")
    if action in ("character-list","model-status"):
        _keys(data,())
        return characters.list_characters(root) if action=="character-list" else model_config.status(root)
    if action=="character-show":
        _keys(data,("character_id",))
        return characters.read(root,data["character_id"])
    if action in ("cast-status","cast-choices"):
        _keys(data,("project_id",))
        pid=data["project_id"]
        result={"project_id":pid,"presenters":projects.load(root,pid)["presenters"],"cast":characters.status(root,pid)}
        if action=="cast-choices":result.update(characters.list_characters(root))
        return result
    if acknowledgment!=ACK:raise ValueError("Explicit local authoring consent required")
    if action=="character-create":
        _keys(data,("profile","parent_id"))
        return characters.create(root,data["profile"],parent_id=data["parent_id"])
    if action=="cast-assign":
        _keys(data,("project_id","mapping"))
        return characters.assign(root,data["project_id"],data["mapping"])
    if action=="source-url":
        _keys(data,("project_id","url","allow_web_fetch"))
        if data["allow_web_fetch"] is not True or not isinstance(data["url"],str) or not 1<=len(data["url"])<=2048:
            raise ValueError("Explicit public HTTPS retrieval consent and URL required")
        return projects.import_source(root,data["project_id"],url=data["url"],allow_web_fetch=True)
    _keys(data,("engine","paths","replace"))
    engine=data["engine"]
    if not isinstance(engine,str) or engine not in model_config.KEYS or type(data["replace"]) is not bool:
        raise ValueError("Invalid model selection or replacement flag")
    _keys(data["paths"],model_config.KEYS[engine])
    return model_config.save(root,engine,{k:_local_path(v) for k,v in data["paths"].items()},replace=data["replace"])


def upload(root,kind,identifier,name,raw,*,acknowledgment=None,rights=False):
    if kind not in UPLOADS or not 1<=len(raw)<=UPLOADS[kind]:raise ValueError("Invalid local upload kind or size")
    if acknowledgment!=ACK:raise ValueError("Explicit local authoring consent required")
    if not isinstance(name,str) or not 1<=len(name)<=160 or not re.fullmatch(r"[\w .()-]+",name) or name in (".",".."):
        raise ValueError("Use a simple source filename")
    suffix=Path(name).suffix.lower()
    if kind=="portrait":
        if rights is not True or suffix!=".png":raise ValueError("Authorized PNG and portrait rights required")
        characters.read(root,identifier)
        characters._portrait_info(raw)
    else:
        req=projects.load(root,identifier)
        allowed={"pdf":(".pdf",),"document":(".docx",".txt",".md"),"custom_script":(".txt",".md")}
        if suffix not in allowed.get(req["input_kind"],()):raise ValueError("File extension must match project input kind")
    # Never use a client-provided path or filename for disk writes.
    base=projects.base(root,create=True)
    with tempfile.TemporaryDirectory(prefix="dashboard-input-",dir=base) as tmp:
        path=Path(tmp)/("portrait.png" if kind=="portrait" else "source"+suffix)
        with path.open("xb") as handle:handle.write(raw)
        if kind=="portrait":return portrait_brief.attach(root,identifier,portrait=path,acknowledgment=characters.ACK)
        return projects.import_source(root,identifier,path=path)
