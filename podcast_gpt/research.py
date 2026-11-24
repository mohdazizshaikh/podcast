"""Explicit, bounded public-source research and exact excerpt citation checks.

A matched quotation proves it occurs in the captured text, not that a
claim is true, that the source is authoritative, or that it is current.
"""
from __future__ import annotations

from . import ingestion, projects, source

FILENAME="research-evidence.json"
MAX_SOURCES=4
MAX_TOTAL_TEXT=12000


def validate_pack(pack):
    if not isinstance(pack,dict) or set(pack)!={"schema","sources"} or pack["schema"]!=1:
        raise ValueError("Invalid research pack")
    rows=pack["sources"]
    if not isinstance(rows,list) or not 2<=len(rows)<=MAX_SOURCES:
        raise ValueError("Research requires 2–4 explicit public sources")
    locators=set();hashes=set();total=0
    for i,row in enumerate(rows,1):
        if not isinstance(row,dict) or set(row)!={"id","evidence"} or row["id"]!=f"S{i:02}":
            raise ValueError("Invalid research source ID")
        evidence=ingestion.validate(row["evidence"],"url")
        # Recheck URL syntax without any DNS or network in read-only validation.
        from urllib.parse import urlsplit
        u=urlsplit(evidence["locator"])
        if u.scheme!="https" or not u.hostname or u.username is not None or u.password is not None or u.query or u.fragment or u.port not in (None,443):
            raise ValueError("Invalid saved public source URL")
        if evidence["locator"] in locators or evidence["text_sha256"] in hashes:
            raise ValueError("Duplicate research source URL or extracted text")
        locators.add(evidence["locator"]);hashes.add(evidence["text_sha256"]);total+=len(evidence["text"])
    if total>MAX_TOTAL_TEXT:raise ValueError("Combined research exceeds 12000 characters; select shorter sources")
    return pack


def read_pack(folder,req):
    p=folder/FILENAME
    if not p.exists() and not p.is_symlink():return None
    projects._plain(p,directory=False)
    if req["research_mode"]!="web":raise ValueError("Unexpected research pack for knowledge-only request")
    wrapper=source.read_json(p,150000)
    if set(wrapper)!={"request_sha256","pack_sha256","pack"} or wrapper["request_sha256"]!=source.json_digest(req):
        raise ValueError("Research request binding differs")
    pack=validate_pack(wrapper["pack"])
    if source.json_digest(pack)!=wrapper["pack_sha256"]:raise ValueError("Research evidence hash differs")
    return pack


def capture(root,pid,urls,*,allow_web_fetch=False,fetcher=None):
    if allow_web_fetch is not True:raise ValueError("Explicit --allow-web-fetch required")
    if not isinstance(urls,list) or not 2<=len(urls)<=MAX_SOURCES or any(not isinstance(u,str) for u in urls) or len(set(urls))!=len(urls):
        raise ValueError("Select 2–4 distinct public HTTPS source URLs")
    folder=projects.project(root,pid)
    with projects.exclusive(folder):
        req=projects.load(root,pid)
        if req["research_mode"]!="web":raise ValueError("Project must use web research mode")
        for name in (FILENAME,projects.PLAN):
            p=folder/name
            if p.exists() or p.is_symlink():raise ValueError("Existing research/outline cannot be overwritten")
        rows=[]
        for i,url in enumerate(urls,1):
            evidence=ingestion.extract("url",url=url,allow_web_fetch=True,fetcher=fetcher)
            rows.append({"id":f"S{i:02}","evidence":evidence})
        pack=validate_pack({"schema":1,"sources":rows})
        if projects.load(root,pid)!=req:raise ValueError("Project changed during research")
        source.atomic_json(folder/FILENAME,{"request_sha256":source.json_digest(req),
                           "pack_sha256":source.json_digest(pack),"pack":pack},new=True)
        return {"project_id":pid,**summary(pack)}


def summary(pack):
    pack=validate_pack(pack)
    return {"source_count":len(pack["sources"]),"sources":[{"id":r["id"],"url":r["evidence"]["locator"],
            "captured_utc":r["evidence"]["captured_utc"],"text_sha256":r["evidence"]["text_sha256"]}
            for r in pack["sources"]],"retrieved_source_snapshots":True,"independent_fact_check_verified":False,
            "automatic_search_performed":False,"publication_approved":False}


def inspect(root,pid):
    req=projects.load(root,pid)
    pack=read_pack(projects.project(root,pid),req)
    if pack is None:raise ValueError("No saved research pack")
    return {"project_id":pid,**summary(pack)}


def prompt_sources(pack):
    return [{"id":r["id"],"text":r["evidence"]["text"]} for r in validate_pack(pack)["sources"]]


def validate_citations(citations,pack):
    if not isinstance(citations,list) or len(citations)>3:
        raise ValueError("Each turn permits 0–3 excerpt citations")
    texts={r["id"]:r["evidence"]["text"] for r in pack["sources"]}
    seen=set();out=[]
    for c in citations:
        if not isinstance(c,dict) or set(c)!={"source_id","quote"}:
            raise ValueError("Invalid citation fields")
        sid,quote=c["source_id"],c["quote"]
        if not isinstance(sid,str) or sid not in texts or not isinstance(quote,str) or not 12<=len(quote)<=200 or quote!=quote.strip():
            raise ValueError("Invalid source ID or citation excerpt")
        if quote not in texts[sid] or (sid,quote) in seen:
            raise ValueError("Citation excerpt does not occur verbatim in saved source or is duplicated")
        seen.add((sid,quote));out.append({"source_id":sid,"quote":quote})
    return out
