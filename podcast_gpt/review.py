"""Private local-only, self-attested manual Hindi face/lip review.

PASS/FAIL is user's own observation and never becomes automated human or
publication rights verification. Review notes never transmitted over HTTP.
"""
from __future__ import annotations

import html
import json
import os
from pathlib import Path
from urllib.parse import quote

from .source import SPEAKERS, atomic_json, digest, json_digest, load_project, read_json, verify_source, workspace_path
from .neural import verified_previews

ACK="I_REVIEWED_ALL_THREE_ORIGINAL_HINDI_FACES"


def _pilot_binding(root:Path,*,allow_short:bool=False) -> dict:
    manifest,done=verified_previews(root,allow_short=allow_short)
    return _binding_from_verified(manifest,done)


def _binding_from_verified(manifest:dict,done:dict) -> dict:
    # Internal helper: the caller MUST have just independently verified all
    # source and preview hashes/decodes. No CLI accepts a supplied binding.
    entries={}
    for speaker in SPEAKERS:
        rows=[row for row in manifest["chunks"] if row["speaker"]==speaker and row["id"] in done]
        if not rows:raise ValueError("Real independently decoded preview missing for presenter "+speaker)
        row=rows[0]
        entries[speaker]={"id":row["id"],"sha256":done[row["id"]],
                          "duration":row["duration"],"portrait_sha256":row["portrait_sha256"]}
    return {"schema":3,"original_source_binding":manifest["source_binding"],
            "chunks_binding":json_digest(manifest),"presenters":entries}


def review_pilot(root:Path,*,allow_short:bool=False) -> dict:
    root=workspace_path(root)
    binding=_pilot_binding(root,allow_short=allow_short)
    digest_binding=json_digest(binding)
    dest=root/"review"/("three-presenter-"+digest_binding[:12]+".html")
    if dest.exists() or dest.is_symlink():raise ValueError("This exact signed review HTML exists; never overwrite")
    cells=[]
    for speaker,entry in binding["presenters"].items():
        cid=entry["id"]
        source=f"../previews/{cid}.mp4"
        cells.append(f'<section><h2>{html.escape(speaker.title())} — {html.escape(cid)}</h2>'
                     f'<video src="{quote(source,safe="/.-")}" controls preload="metadata" playsinline></video>'
                     f'<p>Original 16k Hindi PCM: {entry["duration"]:.2f} seconds.</p>'
                     '<p>Check lips, identity, frozen/jitter artifacts and creator rights manually.</p></section>')
    page='''<!doctype html><html lang="hi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; media-src 'self' file:; style-src 'unsafe-inline'; connect-src 'none'; form-action 'none'">
<title>PRIVATE real Hindi face review — NOT approved</title><style>
body{background:#0d182a;color:#f2f6fc;font:16px system-ui;max-width:950px;margin:30px auto;padding:18px}
video{max-width:100%;width:480px;max-height:430px;background:black}
section{padding:20px;border-bottom:1px solid #52627d}p{line-height:1.5}
</style></head><body><h1>Three genuine Hindi face samples — human inspection needed</h1>
<p>Original media SHA and decoded audio/video verified at page creation. 
<b>This does not certify Hindi mouth timing, identity rights, source authenticity, quality, 
full video completion, or publication.</b> No uploads, network calls, cookie storage or automatic decisions.</p>
<p>Signed original sample binding: '''+html.escape(digest_binding[:12])+'''</p>'''+''.join(cells)+'''<p>After inspecting all THREE videos locally, use the explicit record-pilot
command with PASS/FAIL per presenter. Passing is your private personal opinion only.</p></body></html>'''
    dest.parent.mkdir(exist_ok=True)
    with dest.open("x",encoding="utf-8") as f:f.write(page)
    return {"local_file":str(dest),"verified_samples":len(cells),
            "human_lipsync_approved":False,"publication_approved":False}


def record_pilot(root:Path,decisions:dict,acknowledgment:str,*,allow_short:bool=False) -> dict:
    if acknowledgment!=ACK or set(decisions)!=set(SPEAKERS) or any(v not in ("PASS","FAIL") for v in decisions.values()):
        raise ValueError("Explicit three-presenter human PASS/FAIL and exact acknowledgment required")
    root=workspace_path(root);binding=_pilot_binding(root,allow_short=allow_short)
    dest=root/"review"/"three-presenter-human-observations.json"
    if dest.exists() or dest.is_symlink():raise ValueError("Existing review record cannot be overwritten")
    result={"schema":3,"status":"private_self_attested_three_presenter_human_observation_not_publication_approval",
            "source_bound_face_samples":binding,"decisions":dict(decisions),
            "every_presenter_manual_pass":all(x=="PASS" for x in decisions.values()),
            "creator_portrait_rights_independently_verified":False,
            "full_ten_minute_neural_video_completed":False,"publication_approved":False}
    atomic_json(dest,result,new=True)
    return {"private_record_written":True,"every_presenter_manual_pass":result["every_presenter_manual_pass"],
            "publication_approved":False}


def inspect_pilot(root:Path,*,allow_short:bool=False) -> dict:
    root=workspace_path(root)
    actual=_pilot_binding(root,allow_short=allow_short)
    return _inspect_binding(root,actual)


def _inspect_binding(root:Path,actual:dict) -> dict:
    folder=root/"review"
    record=folder/"three-presenter-human-observations.json"
    if folder.is_symlink() or record.is_symlink() or not record.is_file():
        raise ValueError("Three-presenter manual pilot review record missing or unsafe; use REVIEW and RECORD")
    previous=read_json(record)
    if (previous.get("status")!="private_self_attested_three_presenter_human_observation_not_publication_approval"
            or previous.get("source_bound_face_samples")!=actual
            or set(previous.get("decisions",{}))!=set(SPEAKERS)
            or any(x not in ("PASS","FAIL") for x in previous["decisions"].values())
            or previous.get("every_presenter_manual_pass") != all(x=="PASS" for x in previous["decisions"].values())
            or previous.get("publication_approved") is not False):
        raise ValueError("Manual observation is stale, tampered or does not match present face MP4 SHA")
    return {"status":"private_manual_observation_matches_original_face_previews",
            "decisions":previous["decisions"],
            "every_presenter_manual_pass":previous["every_presenter_manual_pass"],
            "publication_approved":False,"full_ten_minute_neural_video_completed":False}


def _require_batch_pilot(root:Path,manifest:dict,done:dict) -> dict:
    """Internal gate using only a just-verified manifest and preview set."""
    state=_inspect_binding(root,_binding_from_verified(manifest,done))
    if state["every_presenter_manual_pass"] is not True:
        raise ValueError("Three-presenter pilot manual FAIL; do not start BATCH or SESSION")
    return state


def check_batch_pilot(root:Path,*,allow_short:bool=False) -> dict:
    root=workspace_path(root)
    manifest,done=verified_previews(root,allow_short=allow_short)
    state=_require_batch_pilot(root,manifest,done)
    return {**state,"batch_pilot_gate_passed":True,"new_model_inference_calls":0}


def review_full(root:Path,*,allow_short:bool=False) -> dict:
    from .neural import audit_neural
    from .media import timeline
    root=workspace_path(root)
    audit_neural(root,allow_short=allow_short)
    source=verify_source(root,allow_short=allow_short)
    rows=timeline(root,source)
    video=root/"exports"/"original_hindi_full_neural.mp4"
    dest=root/"review"/"all-45-original-hindi-turns.html"
    if dest.exists() or dest.is_symlink():raise ValueError("Old full human review page must not be overwritten")
    file_uri=html.escape(video.resolve().as_uri(),quote=True)
    buttons=[]
    for row in rows:
        seek=f"{row['start']:.6f}"
        buttons.append(f'<tr><td><button type="button" data-seek="{seek}">Play {html.escape(row["id"])}</button></td>'
                       f'<td>{html.escape(row["speaker"])}</td><td lang="hi">{html.escape(row["text"])}</td>'
                       '<td><input type="checkbox" aria-label="manual observation, not approval"></td></tr>')
    page='''<!doctype html><html lang="hi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; media-src 'self' file:; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'none'">
<title>45 Hindi turns — unverified manual QA</title><style>body{font:16px system-ui;max-width:1000px;margin:auto;padding:20px;background:#111b2c;color:white}
video{max-width:100%;width:700px}td{border-bottom:1px solid #667;padding:10px}button{padding:8px}</style>
<h1>Original 45 Hindi dialogue turns — manual QA, NOT approved</h1>
<p>Structural AAC/MP4/SRT audit passed when this local page was created. Check every turn, lip movements, captions, transitions, identity and rights yourself.
Nothing here certifies or publishes a video; checkboxes reset and do not store data.</p>
<video id="v" src="'''+file_uri+'''" controls preload="metadata"></video><table>'''+''.join(buttons)+'''</table>
<script>const v=document.getElementById('v');document.querySelectorAll('button[data-seek]').forEach(b=>b.addEventListener('click',()=>{
const n=Number(b.dataset.seek);if(Number.isFinite(n)&&n>=0){v.currentTime=n;v.play().catch(()=>{});}}));</script>'''
    dest.parent.mkdir(exist_ok=True)
    with dest.open("x",encoding="utf-8") as f:f.write(page)
    return {"private_review_file":str(dest),"original_hindi_turns":45,
            "human_lipsync_verified":False,"publication_approved":False}