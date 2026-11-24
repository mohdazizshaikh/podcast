"""Private reusable character identity and authorized portrait library.

Immutable profile versions; no identity recognition, image synthesis,
voice cloning, provider calls, or independent rights certification.
"""
from __future__ import annotations

import hashlib
import io
import os
import uuid
from pathlib import Path

from PIL import Image
from . import projects, source

LIBRARY="character-library"
PROFILE="profile.json"
PORTRAIT="portrait.png"
CAST="cast.json"
MAX_PORTRAIT=12_000_000
ACK="I_HAVE_RIGHTS_TO_USE_THIS_PORTRAIT"
FIELDS={"name","personality","speaking_style","appearance","voice_preferences"}
ENGINES=("undecided","imported","kokoro","edge")


def _text(value,limit,*,optional=False):
    if not isinstance(value,str) or len(value)>limit or any(ord(c)<32 or ord(c)==127 for c in value):
        raise ValueError("Invalid character text field")
    value=value.strip()
    if not optional and not value:raise ValueError("Required character field is empty")
    return value


def validate_profile(data):
    if not isinstance(data,dict) or set(data)!=FIELDS:
        raise ValueError("Invalid character profile fields")
    voice=data["voice_preferences"]
    if not isinstance(voice,dict) or set(voice)!={"engine","language","preset","style_notes"} or voice["engine"] not in ENGINES:
        raise ValueError("Invalid voice preference fields")
    return {"name":_text(data["name"],80),"personality":_text(data["personality"],600),
            "speaking_style":_text(data["speaking_style"],600),"appearance":_text(data["appearance"],1000),
            "voice_preferences":{"engine":voice["engine"],"language":_text(voice["language"],80),
              "preset":_text(voice["preset"],100,optional=True),"style_notes":_text(voice["style_notes"],400,optional=True)}}


def _library(root,*,create=False):
    folder=projects.base(root,create=create)/LIBRARY
    projects._plain(folder,missing=True)
    if create:
        folder.mkdir(exist_ok=True);projects._plain(folder)
        source.workspace_path(folder)
    return folder


def _profile_folder(root,cid):
    if not isinstance(cid,str) or not projects.ID_RE.fullmatch(cid):
        raise ValueError("Invalid character ID")
    folder=_library(root)
    projects._plain(folder)
    dest=folder/cid
    projects._plain(dest)
    source.workspace_path(dest)
    return dest


def _read_file(path,limit):
    path=Path(path).expanduser().absolute()
    for p in reversed(path.parents):projects._plain(p)
    projects._plain(path,directory=False)
    if path.stat().st_size>limit:raise ValueError("Character input exceeds size limit")
    with path.open("rb") as handle:raw=handle.read(limit+1)
    if len(raw)>limit:raise ValueError("Character input exceeds size limit")
    return raw


def _portrait_info(raw):
    if not raw or len(raw)>MAX_PORTRAIT:raise ValueError("Portrait must be at most 12 MB")
    try:
        with Image.open(io.BytesIO(raw),formats=["PNG"]) as image:
            if image.format!="PNG" or getattr(image,"n_frames",1)!=1:
                raise ValueError("Use a single-frame PNG portrait")
            w,h=image.size
            if not 200<=w<=4096 or not 200<=h<=4096 or w*h>12_000_000:
                raise ValueError("Portrait dimensions must be 200–4096 pixels and at most 12 megapixels")
            image.verify()
        with Image.open(io.BytesIO(raw),formats=["PNG"]) as image:image.load()
    except (OSError,SyntaxError,Image.DecompressionBombError) as exc:
        raise ValueError("Invalid or unsafe PNG portrait") from None
    return {"sha256":hashlib.sha256(raw).hexdigest(),"width":w,"height":h,"rights_self_attested":True}


def read(root,cid):
    folder=_profile_folder(root,cid)
    path=folder/PROFILE
    projects._plain(path,directory=False)
    data=source.read_json(path,32_000)
    if set(data)!={"schema","character_id","parent_id","profile","portrait","profile_sha256"} or data["schema"]!=1 or data["character_id"]!=cid:
        raise ValueError("Invalid character profile record")
    parent=data["parent_id"]
    if parent is not None and (not isinstance(parent,str) or not projects.ID_RE.fullmatch(parent) or parent==cid):
        raise ValueError("Invalid character parent ID")
    profile=validate_profile(data["profile"])
    if profile!=data["profile"] or data["profile_sha256"]!=source.json_digest(profile):
        raise ValueError("Character profile hash differs")
    portrait=folder/PORTRAIT
    if data["portrait"] is None:
        if portrait.exists() or portrait.is_symlink():raise ValueError("Unregistered portrait file")
    else:
        if _portrait_info(_read_file(portrait,MAX_PORTRAIT))!=data["portrait"]:
            raise ValueError("Character portrait hash or metadata differs")
    return data


def create(root,profile,*,portrait=None,acknowledgment=None,parent_id=None):
    profile=validate_profile(profile)
    if parent_id is not None:read(root,parent_id)
    if portrait is not None:
        if acknowledgment!=ACK:raise ValueError("Explicit portrait rights acknowledgment required")
        raw=_read_file(portrait,MAX_PORTRAIT);info=_portrait_info(raw)
    else:raw=None;info=None
    library=_library(root,create=True)
    cid=uuid.uuid4().hex
    with projects.exclusive(library):
        dest=library/cid;dest.mkdir()
        if raw is not None:
            with (dest/PORTRAIT).open("xb") as handle:
                handle.write(raw);handle.flush();os.fsync(handle.fileno())
        record={"schema":1,"character_id":cid,"parent_id":parent_id,"profile":profile,
                "portrait":info,"profile_sha256":source.json_digest(profile)}
        source.atomic_json(dest/PROFILE,record,new=True)
    return {"character_id":cid,"profile":profile,"portrait":info,"parent_id":parent_id,
            "voice_compatibility_verified":False,"face_identity_verified":False,"publication_approved":False}


def create_from_file(root,path,**options):
    path=Path(path).expanduser().absolute()
    source.workspace_path(path.parent)
    raw=_read_file(path,32_000)
    import json
    return create(root,json.loads(raw.decode("utf-8-sig")),**options)


def list_characters(root):
    library=_library(root)
    if not library.exists():return {"characters":[],"blocked":[]}
    rows=[];blocked=[]
    for child in sorted(library.iterdir()):
        if not projects.ID_RE.fullmatch(child.name):continue
        try:
            data=read(root,child.name)
            rows.append({"character_id":child.name,"name":data["profile"]["name"],"portrait_present":data["portrait"] is not None,
                         "voice_engine":data["profile"]["voice_preferences"]["engine"],"parent_id":data["parent_id"]})
        except (OSError,ValueError,TypeError,KeyError):blocked.append(child.name)
    return {"characters":rows,"blocked":blocked}


def _cast_rows(root,req,mapping):
    if not isinstance(mapping,dict) or set(mapping)!=set(req["presenters"]):
        raise ValueError("Assign exactly one character to every project presenter")
    ids=list(mapping.values())
    if any(not isinstance(cid,str) or not projects.ID_RE.fullmatch(cid) for cid in ids):
        raise ValueError("Invalid cast character ID")
    if len(set(ids))!=len(ids):raise ValueError("Use distinct character IDs for every presenter")
    rows=[]
    for speaker in req["presenters"]:
        data=read(root,mapping[speaker])
        rows.append({"speaker":speaker,"character_id":data["character_id"],
                     "record_sha256":source.json_digest(data)})
    return rows


def read_cast(root,pid):
    folder=projects.project(root,pid)
    path=folder/CAST
    if not path.exists() and not path.is_symlink():return None
    projects._plain(path,directory=False)
    req=projects.load(root,pid)
    data=source.read_json(path,64_000)
    if set(data)!={"schema","request_sha256","cast","cast_sha256"} or data["schema"]!=1 or data["request_sha256"]!=source.json_digest(req):
        raise ValueError("Cast request binding differs")
    rows=data["cast"]
    if not isinstance(rows,list) or any(not isinstance(r,dict) or set(r)!={"speaker","character_id","record_sha256"} for r in rows):
        raise ValueError("Invalid cast records")
    if rows!=_cast_rows(root,req,{r["speaker"]:r["character_id"] for r in rows}) or data["cast_sha256"]!=source.json_digest(rows):
        raise ValueError("Cast profile binding or hash differs")
    return data


def assign(root,pid,mapping):
    folder=projects.project(root,pid)
    with projects.exclusive(folder):
        dest=folder/CAST
        if dest.exists() or dest.is_symlink():raise ValueError("Cast already assigned; create another project to change its cast")
        req=projects.load(root,pid)
        rows=_cast_rows(root,req,mapping)
        data={"schema":1,"request_sha256":source.json_digest(req),"cast":rows,"cast_sha256":source.json_digest(rows)}
        source.atomic_json(dest,data,new=True)
    return status(root,pid)


def assign_from_file(root,pid,path):
    path=Path(path).expanduser().absolute()
    source.workspace_path(path.parent)
    import json
    return assign(root,pid,json.loads(_read_file(path,32_000).decode("utf-8-sig")))


def status(root,pid):
    cast=read_cast(root,pid)
    if cast is None:return {"project_id":pid,"cast_assigned":False,"character_media_ready":False}
    details=[]
    for row in cast["cast"]:
        profile=read(root,row["character_id"])
        details.append({**row,"name":profile["profile"]["name"],"portrait_present":profile["portrait"] is not None,
                        "voice_preferences":profile["profile"]["voice_preferences"]})
    return {"project_id":pid,"cast_assigned":True,"cast_sha256":cast["cast_sha256"],"presenters":details,
            "all_portraits_present":all(d["portrait_present"] for d in details),
            "voice_compatibility_verified":False,"character_media_ready":False,"publication_approved":False}


def prepare_media_binding(root,pid):
    """Read-only handoff for later generalized audio/media pipeline."""
    from . import script_review
    cast=read_cast(root,pid)
    if cast is None:raise ValueError("Assign a complete cast before media preparation")
    current=script_review.current_script(root,pid,require_pass=True)
    profile_rows=[]
    portrait_hashes=set()
    for row in cast["cast"]:
        data=read(root,row["character_id"])
        if data["portrait"] is None:raise ValueError("Every cast member needs an authorized PNG portrait")
        sha=data["portrait"]["sha256"]
        if sha in portrait_hashes:raise ValueError("Distinct presenters require distinct portrait files")
        portrait_hashes.add(sha)
        profile_rows.append({**row,"portrait_sha256":sha,"voice_preferences":data["profile"]["voice_preferences"]})
    if cast!=read_cast(root,pid) or current!=script_review.current_script(root,pid,require_pass=True):
        raise ValueError("Cast or approved script changed during media preparation")
    return {"project_id":pid,"script_version_sha256":current["version_sha256"],"cast_sha256":cast["cast_sha256"],
            "presenters":profile_rows,"turn_count":len(current["turns"]),"status":"verified_text_and_portrait_binding_only",
            "voice_compatibility_verified":False,"actual_media_generated":False,"publication_approved":False}
