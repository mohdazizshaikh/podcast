"""Explicit free Wikipedia candidate discovery, not source capture or fact checking."""
from __future__ import annotations
import json
import time
import http.client
from urllib.parse import quote,urlencode
from . import ingestion,projects

EDITIONS=("en","hi","mr","bn","gu","ta","te","ur","es","fr","it","pt","de","ja","zh","ar","ru")
HOST="https://en.wikipedia.org"
MAX_BYTES=256000


def _host(edition):
    if not isinstance(edition,str) or edition not in EDITIONS:raise ValueError("Select an allowlisted Wikipedia edition")
    return "https://"+edition+".wikipedia.org"


def _fetch(query,limit,edition="en"):
    host,_,ip=ingestion._target(_host(edition))
    conn=ingestion._PinnedHTTPS(host,ip)
    path="/w/rest.php/v1/search/page?"+urlencode({"q":query,"limit":limit})
    try:
        conn.request("GET",path,headers={"Accept":"application/json","Accept-Encoding":"identity",
                     "User-Agent":"PodcastGPTPrivateStudio/4 (manual research discovery; https://github.com/mohdazizshaikh/podcast)"})
        response=conn.getresponse()
        if response.status!=200 or response.getheader("Content-Encoding","identity").lower()!="identity" or response.getheader("Content-Type","").split(";")[0].strip()!="application/json":
            raise ValueError("Wikipedia discovery unavailable; select source URLs manually")
        data=bytearray();started=time.monotonic()
        while True:
            block=response.read1(min(16384,MAX_BYTES+1-len(data)))
            if not block:break
            data.extend(block)
            if len(data)>MAX_BYTES or time.monotonic()-started>30:raise ValueError("Discovery response exceeds limits")
        return json.loads(data.decode("utf-8"))
    except (OSError,UnicodeError,json.JSONDecodeError,http.client.HTTPException) as exc:raise ValueError("Wikipedia discovery request failed; use manual source URLs") from exc
    finally:conn.close()


def discover(root,pid,*,query=None,limit=5,edition="en",allow_web_search=False,fetcher=None):
    if allow_web_search is not True:raise ValueError("Explicit --allow-web-search required; query is sent to Wikipedia")
    host=_host(edition)
    req=projects.load(root,pid)
    if req["research_mode"]!="web":raise ValueError("Choose web research mode")
    text=req["topic"] if query is None else query
    if not isinstance(text,str) or not 1<=len(text.strip())<=200 or any(ord(c)<32 for c in text):
        raise ValueError("Search query must be 1–200 printable characters")
    if type(limit) is not int or not 1<=limit<=10:raise ValueError("Select 1–10 candidate links")
    response=fetcher(text.strip(),limit) if fetcher is not None else _fetch(text.strip(),limit,edition)
    if not isinstance(response,dict) or not isinstance(response.get("pages"),list):raise ValueError("Invalid discovery response")
    candidates=[];seen=set()
    for row in response["pages"][:limit]:
        if not isinstance(row,dict):continue
        key=row.get("key");title=row.get("title")
        if not isinstance(key,str) or not isinstance(title,str) or not 1<=len(key)<=300 or not 1<=len(title)<=300 or any(ord(c)<32 for c in key+title) or ":" in key or key in (".","..") or key in seen:continue
        try:url=host+"/wiki/"+quote(key,safe="_-()")
        except UnicodeError:continue
        candidates.append({"title":title,"url":url});seen.add(key)
    return {"project_id":pid,"provider":"Wikipedia English search" if edition=="en" else "Wikipedia "+edition+" search","edition":edition,"candidates":candidates,
            "source_capture_performed":False,"independent_fact_check_verified":False,"paid_api_calls":0,
            "note":"Select and verify sources manually. Results are discovery leads from one encyclopedia, not independent evidence."}
