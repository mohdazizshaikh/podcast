"""Local-only dashboard: explicit one-click source actions + private file imports.

No media/portrait HTTP GET endpoints, network uploads, AI model inference,
automatic publishing, or model downloads. Real CPU model from separate
consent-screen BAT/CLI only. Stateful CSRF token per local server instance.
"""
from __future__ import annotations

import json
import os
import re
import secrets
import threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs,urlsplit

from .cli import doctor
from .source import (SPEAKERS, SOURCE_FILE, init, build_source, prepare_chunks,
                     wav_info, read_json, workspace_path, original_voice_lock)
from .media import render_static,audit_static
from .neural import progress
from .readiness import inspect as inspect_readiness
from .setup_wizard import inspect as inspect_setup
from .projects import list_projects,ID_RE
from .v4_readiness import inspect as inspect_v4_readiness
from . import production_overview, dashboard_actions, projects

STYLE="""body{font:16px system-ui;background:#121b2b;color:#f4f7ff;margin:auto;max-width:1100px;padding:28px}
header{padding:18px;border-bottom:1px solid #53627c}.panel{padding:18px;margin:18px 0;border:1px solid #4c5a70;border-radius:12px}
button{padding:12px 18px;border-radius:7px;border:0;margin:4px;cursor:pointer;font-weight:600}
small{color:#c5d1e6}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#233149;padding:16px}input{margin:8px}label{display:inline-block;padding:6px}
"""


def html_page(token:str)->str:
    # Static trusted markup, token is exclusively server-generated hex.
    return '''<!doctype html><html lang="hi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none';style-src 'unsafe-inline';script-src 'unsafe-inline';connect-src 'self';media-src blob:;form-action 'none';base-uri 'none'">
<title>Podcast GPT — Private Hindi Studio</title><style>'''+STYLE+'''</style></head><body>
<header><h1>Podcast GPT — Private Hindi Studio</h1>
<p>Three human-authorized presenters, original 45 Hindi turns, true WAV sample provenance and CPU-only rendering.</p>
<small>Localhost-only. Your portraits, voices and rendered media stay on your computer and are never served over HTTP. Online TTS and real SadTalker require separate explicit CLI consent.</small></header>
<section class="panel"><h2>0. V4 Smart setup — hardware and model readiness</h2>
<button data-action="setup-wizard">Inspect hardware, storage and installed app packages</button>
<p><small>For selecting existing local AI model files and explicitly probing a trusted model interpreter, run SMART_SETUP_WINDOWS.bat. No model downloads or external executable paths are accepted over HTTP.</small></p></section>
<section class="panel"><h2>V4 personal projects</h2>
<button data-action="project-list">List private V4 projects</button>
<h3>Create private project</h3>
<label>Topic <textarea id="v4Topic" maxlength="2000" rows="2"></textarea></label>
<label>Language <input id="v4Language" value="Hindi" maxlength="80"></label>
<label>Minutes <input id="v4Minutes" type="number" min="1" max="60" value="10"></label>
<label>Presenter names, comma separated <input id="v4Presenters" value="Aarav, Meera, Kabir" maxlength="810"></label>
<label>Format <select id="v4Format"><option>landscape</option><option>vertical</option><option>square</option></select></label>
<label>Workflow <select id="v4Workflow"><option>automatic</option><option>manual</option></select></label>
<label>Input <select id="v4Input"><option>topic</option><option>url</option><option>pdf</option><option>document</option><option>custom_script</option></select></label>
<label>Research <select id="v4Research"><option>knowledge</option><option>web</option></select></label>
<button id="v4Create">Create project (local configuration only)</button>
<label>Project ID <input id="v4ProjectId" maxlength="32" autocomplete="off"></label>
<button id="v4Readiness">Check selected V4 project readiness (read-only)</button>
<button id="v4Overview">Production overview / historical estimate</button>
<div id="v4Summary" aria-live="polite"></div>
<h3>Explicit local production actions</h3>
<label><input type="checkbox" id="v4ProcessConsent"> I authorize the selected local processing action. No AI inference or approval is authorized here.</label>
<select id="v4Process"><option value="project-safe-step">One eligible non-inference production step</option><option value="project-script-visual-edit">Create offline script editor</option><option value="project-script-visual-review">Create script review page</option><option value="project-audio-visual-review">Create audio review page</option><option value="project-pilot-visual-review">Create pilot review page</option><option value="project-final-visual-review">Create final review page</option><option value="project-static-render">Render static preview</option><option value="project-studio-render">Render static studio</option><option value="project-neural-studio-compose">Compose neural studio from saved clips</option><option value="project-mixed-studio-compose">Compose mixed neural studio</option></select>
<button id="v4Run">Run selected local action</button>
<h3>Verified local playback</h3>
<label>Media type <select id="v4MediaKind"><option value="master">Master WAV</option><option value="preview">Static preview</option><option value="neural">Neural video</option><option value="mix">Audio mix</option><option value="mixed">Mixed video</option><option value="studio-preview">Static studio</option><option value="neural-studio">Neural studio</option><option value="mixed-neural-studio">Mixed neural studio</option></select></label>
<button id="v4MediaCheck">Audit selected media</button>
<p id="v4MediaInfo">Audit first, then select the matching local file (128 MiB maximum for browser hash check).</p>
<input type="file" id="v4LocalMedia" accept=".wav,.mp4" disabled><video id="v4Player" controls preload="none" style="max-width:100%;display:none"></video>
<p><small>File bytes stay in this browser tab; no upload or HTTP media endpoint. Large files: use the displayed local path in your own player.</small></p>
<small>Source imports, model inference, cloud consent, API keys and recorded human approvals remain CLI-only.</small></section>
<section class="panel"><h2>1. Original 45-turn episode</h2>
<button data-action="init">Create NEW original 45-turn project</button>
<button data-action="doctor">Check tools</button>
<small>Once created, edit private project.json to your own Hindi dialogue.</small></section>
<section class="panel"><h2>2. Import authorized original media</h2>
<p>Portrait PNGs (>=200px):</p>
<label><input id="portraitRights" type="checkbox"> I own these portraits or have written permission to use them for AI talking-face creation. This is my own declaration, not automatic rights verification.</label>
<label>Aarav <input id="aarav" type="file" accept="image/png"></label>
<label>Meera <input id="meera" type="file" accept="image/png"></label>
<label>Kabir <input id="kabir" type="file" accept="image/png"></label>
<button id="faces">Import portraits (never overwrite)</button>
<p>Original WAVs: file names 001.wav through 045.wav, exact 16kHz mono signed 16-bit PCM. Select all 45.</p>
<input id="voices" type="file" accept="audio/wav,.wav" multiple>
<button id="speech">Import original WAVs (never overwrite)</button></section>
<section class="panel"><h2>3. Verify and create</h2>
<button data-action="build-source">Bind ALL original source SHA</button>
<button data-action="prepare-chunks">Export exact 1–10s original PCM</button>
<button data-action="render-static">Render REAL 720p static presenter MP4 / AAC / SRT</button>
<button data-action="audit-static">Independently audit original MP4</button>
<button data-action="progress">Check genuine saved neural previews</button>
<button data-action="readiness">READINESS — read-only all-stage SHA/video audit and next safe step</button>
<p><small>Static is NOT lip-sync. Real SadTalker CPU models and one-per-presenter PILOT use the separate explicit-consent Windows launcher.</small></p></section>
<section class="panel"><h2>Local task log</h2><pre id="status" aria-live="polite">Ready. Nothing running.</pre></section>
<script>
'use strict';const token='''+json.dumps(token)+''';const out=document.getElementById('status');
async function send(endpoint,data,portraitRights=false){let opt={method:'POST',headers:{'X-CSRF-Token':token}};
if(portraitRights)opt.headers['X-Portrait-Rights-Confirmed']='YES';
if(data instanceof File){opt.body=data;opt.headers['Content-Type']='application/octet-stream'}
else if(data!==undefined&&data!==null){opt.body=JSON.stringify(data);opt.headers['Content-Type']='application/json'}
let r=await fetch(endpoint,opt);let j=await r.json();if(!r.ok)throw new Error(j.error||('HTTP '+r.status));return j}
let manifest=null,blobUrl=null;
function clearMedia(){manifest=null;let p=document.getElementById('v4Player');p.pause();p.removeAttribute('src');p.load();p.style.display='none';if(blobUrl){URL.revokeObjectURL(blobUrl);blobUrl=null}let i=document.getElementById('v4LocalMedia');i.value='';i.disabled=true}
function showResult(status){
 if(status.phase!=='complete'||!status.result)return;
 let data=status.result;
 if(status.command==='project-create'&&data.project_id){document.getElementById('v4ProjectId').value=data.project_id;clearMedia();document.getElementById('v4Summary').replaceChildren()}
 if(status.command==='project-production-overview'){
  if(data.project_id!==document.getElementById('v4ProjectId').value.trim())return;
  let area=document.getElementById('v4Summary');area.replaceChildren();
  for(let line of ['Stage: '+data.readiness.stage,'Next: '+data.readiness.next_action,...Object.entries(data.readiness.checks).map(([k,v])=>k+': '+JSON.stringify(v)), 'Historical timing observations: '+data.timing.completed_observations, data.neural_estimate.estimate_available?'Approximate remaining stage seconds: '+data.neural_estimate.estimated_seconds+' (historical range '+data.neural_estimate.observed_rate_range_seconds.join('–')+')':'Estimate unavailable: '+data.neural_estimate.reason]){let p=document.createElement('p');p.textContent=line;area.append(p)}
 }
 if(status.command==='project-media-check'&&data.project_id===document.getElementById('v4ProjectId').value.trim()&&data.kind===document.getElementById('v4MediaKind').value){
  manifest=data;document.getElementById('v4MediaInfo').textContent='Verified local file: '+data.local_path+' | SHA-256: '+data.sha256+(data.browser_check_supported?' | Select this file locally.':' | Too large for browser hash check; use a local player.');
  document.getElementById('v4LocalMedia').disabled=!data.browser_check_supported;
 }
}
async function refresh(){
 let r=await fetch('/api/status',{cache:'no-store'});let status=await r.json();
 out.textContent=JSON.stringify(status,null,2);showResult(status);
 if(status.phase==='running')setTimeout(()=>refresh().catch(e=>out.textContent='BLOCKED: '+e.message),1100);
}
async function action(name,pid=null,kind=null,consent=false){try{
 out.textContent='Starting '+name+'...';
 let receipt=await send('/api/action?cmd='+encodeURIComponent(name)+(pid===null?'':'&project_id='+encodeURIComponent(pid))+(kind===null?'':'&kind='+encodeURIComponent(kind))+(consent?'&consent=YES':''));
 out.textContent=JSON.stringify(receipt,null,2);
 await refresh();
}catch(e){out.textContent='BLOCKED: '+e.message}}
document.querySelectorAll('[data-action]').forEach(b=>b.addEventListener('click',()=>action(b.dataset.action)));
document.getElementById('v4Readiness').addEventListener('click',()=>{let pid=document.getElementById('v4ProjectId').value.trim();if(!/^[0-9a-f]{32}$/.test(pid)){out.textContent='Enter a valid project ID from the project list';return}action('project-readiness',pid)});
function currentPid(){let pid=document.getElementById('v4ProjectId').value.trim();if(!/^[0-9a-f]{32}$/.test(pid))throw new Error('Enter a valid project ID');return pid}
document.getElementById('v4Create').addEventListener('click',async()=>{
 try{
  const get=id=>document.getElementById(id).value;
  const request={topic:get('v4Topic'),language:get('v4Language'),duration_minutes:Number(get('v4Minutes')),presenters:get('v4Presenters').split(',').map(s=>s.trim()),video_format:get('v4Format'),workflow:get('v4Workflow'),input_kind:get('v4Input'),research_mode:get('v4Research')};
  out.textContent=JSON.stringify(await send('/api/project-create',request),null,2);await refresh();
 }catch(e){out.textContent='BLOCKED: '+e.message}
});
document.getElementById('v4Run').addEventListener('click',()=>{
 try{
  if(!document.getElementById('v4ProcessConsent').checked)throw new Error('Explicit local processing consent required');
  document.getElementById('v4ProcessConsent').checked=false;
  action(document.getElementById('v4Process').value,currentPid(),null,true);
 }catch(e){out.textContent='BLOCKED: '+e.message}
});
document.getElementById('v4Overview').addEventListener('click',()=>{try{action('project-production-overview',currentPid())}catch(e){out.textContent=e.message}});
document.getElementById('v4MediaCheck').addEventListener('click',()=>{try{clearMedia();document.getElementById('v4MediaInfo').textContent='Auditing current candidate...';action('project-media-check',currentPid(),document.getElementById('v4MediaKind').value)}catch(e){out.textContent=e.message}});
for(const id of ['v4ProjectId','v4MediaKind'])document.getElementById(id).addEventListener('input',()=>{clearMedia();document.getElementById('v4MediaInfo').textContent='Audit the current selection first.';document.getElementById('v4Summary').replaceChildren()});
document.getElementById('v4LocalMedia').addEventListener('change',async()=>{
 const selected=manifest,info=document.getElementById('v4MediaInfo'),player=document.getElementById('v4Player');
 const file=document.getElementById('v4LocalMedia').files[0];
 player.pause();player.removeAttribute('src');player.load();player.style.display='none';if(blobUrl){URL.revokeObjectURL(blobUrl);blobUrl=null}
 try{
  if(!selected||!file||!selected.browser_check_supported||file.size!==selected.bytes||file.size>134217728)throw new Error('Select the matching verified file within the browser size limit');
  if(!globalThis.crypto?.subtle)throw new Error('Browser SHA-256 unavailable; use a local player');
  const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',await file.arrayBuffer())),b=>b.toString(16).padStart(2,'0')).join('');
  if(manifest!==selected)return;
  if(hash!==selected.sha256)throw new Error('Selected file differs from audited SHA-256');
  blobUrl=URL.createObjectURL(file);player.src=blobUrl;player.style.display='block';info.textContent='Local file hash matches audited candidate. Use playback controls; no review saved.';
 }catch(e){if(manifest===selected)info.textContent='BLOCKED: '+e.message}
});
async function upload(files,kind){
if(kind==='portrait'&&!document.getElementById('portraitRights').checked)
  throw new Error('Explicit portrait ownership/written permission required');
for(let file of files){out.textContent='Importing '+file.name;
let q=new URLSearchParams({kind,name:file.name});await send('/api/upload?'+q,file,kind==='portrait');}
out.textContent='Imported '+files.length+' local media file(s). No existing originals overwritten.'}
document.getElementById('faces').addEventListener('click',async()=>{try{let files=[];for(let x of ['aarav','meera','kabir']){
let f=document.getElementById(x).files[0];if(f){if(f.name.toLowerCase().split('.').pop()!=='png')throw new Error('PNG only');files.push(new File([f],x+'.png',{type:'image/png'}))}}
if(!files.length)throw new Error('Select one or more authorized portraits');await upload(files,'portrait')}catch(e){out.textContent='BLOCKED: '+e.message}});
document.getElementById('speech').addEventListener('click',async()=>{try{let files=[...document.getElementById('voices').files];
if(!files.length)throw new Error('Select WAVs');await upload(files,'voice')}catch(e){out.textContent='BLOCKED: '+e.message}});
</script></body></html>'''


def serve(root:Path,port:int=7860,*,open_browser:bool=False):
    if type(port)!=int or not 1024<=port<=65535:raise ValueError("Private loopback port 1024..65535")
    root=workspace_path(root);root.mkdir(parents=True,exist_ok=True)
    token=secrets.token_hex(32)
    status={"phase":"idle","command":None,"result":None}
    lock=threading.Lock()
    state_lock=threading.Lock()
    actions={"init":lambda:init(root),"doctor":lambda:doctor(root),
             "setup-wizard":lambda:inspect_setup(root),
             "project-list":lambda:list_projects(root),
             "build-source":lambda:build_source(root),
             "prepare-chunks":lambda:prepare_chunks(root),
             "render-static":lambda:render_static(root),
             "audit-static":lambda:audit_static(root),
             "progress":lambda:progress(root),
             "readiness":lambda:inspect_readiness(root)}

    class Handler(BaseHTTPRequestHandler):
        def _send(self,code:int,payload:bytes,kind="application/json"):
            self.send_response(code);self.send_header("Content-Type",kind+"; charset=utf-8")
            self.send_header("Cache-Control","no-store");self.send_header("X-Content-Type-Options","nosniff")
            self.send_header("Referrer-Policy","no-referrer")
            self.send_header("X-Frame-Options","DENY")
            self.send_header("Content-Security-Policy","default-src 'none'; frame-ancestors 'none'") if kind!="text/html" else None
            self.send_header("Content-Length",str(len(payload)));self.end_headers();self.wfile.write(payload)
        def _json(self,code,obj):self._send(code,json.dumps(obj,ensure_ascii=False,default=str).encode("utf-8"))
        def _allowed(self):
            host=self.headers.get("Host","")
            origin=self.headers.get("Origin","")
            return host in (f"127.0.0.1:{port}",f"localhost:{port}") and (not origin or origin in (f"http://127.0.0.1:{port}",f"http://localhost:{port}"))
        def do_GET(self):
            if not self._allowed():return self._json(403,{"error":"Private loopback host only"})
            if self.path=="/":return self._send(200,html_page(token).encode("utf-8"),"text/html")
            if self.path=="/api/status":
                with state_lock:
                    snapshot=dict(status)
                return self._json(200,snapshot)
            return self._json(404,{"error":"No HTTP media or private filesystem routes"})
        def do_POST(self):
            if not self._allowed() or not secrets.compare_digest(self.headers.get("X-CSRF-Token",""),token):
                return self._json(403,{"error":"Blocked external/cross-origin/CSRF request"})
            size_str=self.headers.get("Content-Length","")
            if not size_str.isdecimal():return self._json(411,{"error":"Content-Length required"})
            size=int(size_str);url=urlsplit(self.path);query=parse_qs(url.query)
            if url.path in ("/api/action","/api/project-create"):
                if url.path=="/api/project-create":
                    if not 1<=size<=dashboard_actions.CREATE_LIMIT or self.headers.get("Content-Type")!="application/json":return self._json(400,{"error":"Bounded JSON project request required"})
                    try:
                        raw=self.rfile.read(size)
                        if len(raw)!=size:raise ValueError("Incomplete project request")
                        request=dashboard_actions.parse_request(raw)
                    except ValueError as err:return self._json(400,{"error":str(err)})
                    command="project-create";selected=lambda:projects.create(root,request)
                else:
                    if size!=0:return self._json(400,{"error":"Action body must be empty"})
                    command=query.get("cmd",[""])[0]
                if url.path=="/api/project-create":pass
                elif command in dashboard_actions.ACTIONS:
                    pid=query.get("project_id",[""])[0]
                    if not ID_RE.fullmatch(pid):return self._json(400,{"error":"Invalid V4 project ID"})
                    if query.get("consent",[""])[0]!="YES":return self._json(403,{"error":"Explicit local processing consent required"})
                    selected=lambda:dashboard_actions.run(root,pid,command,acknowledgment=dashboard_actions.ACK)
                elif command in ("project-readiness","project-production-overview","project-media-check"):
                    pid=query.get("project_id",[""])[0]
                    if not ID_RE.fullmatch(pid):return self._json(400,{"error":"Invalid V4 project ID"})
                    if command=="project-readiness":selected=lambda:inspect_v4_readiness(root,pid)
                    elif command=="project-production-overview":selected=lambda:production_overview.inspect(root,pid)
                    else:
                        kind=query.get("kind",[""])[0]
                        if kind not in production_overview.MEDIA:return self._json(400,{"error":"Unknown media kind"})
                        selected=lambda:production_overview.media_check(root,pid,kind)
                elif command in actions:selected=actions[command]
                else:return self._json(400,{"error":"Unrecognized local action"})
                with state_lock:
                    accepted=lock.acquire(blocking=False)
                    if accepted:
                        status.update(phase="running",command=command,result=None)
                if not accepted:
                    return self._json(409,{"error":"Another explicit local task is running"})
                def run():
                    phase="blocked"
                    result={"error":"Local task interrupted"}
                    try:
                        result=selected()
                        phase="complete"
                    except Exception as e:
                        result={"error":str(e)}
                    finally:
                        # A visible terminal state must mean the action mutex
                        # is already released, without clobbering a new task.
                        with state_lock:
                            lock.release()
                            status.update(phase=phase,result=result)
                try:
                    threading.Thread(target=run,daemon=True).start()
                except RuntimeError as err:
                    with state_lock:
                        lock.release()
                        status.update(phase="blocked",result={"error":str(err)})
                    return self._json(503,{"error":"Unable to start local task"})
                return self._json(202,{"task_started":command,"next":"Refresh /api/status for result; no AI inference"})
            if url.path=="/api/upload":
                kind=query.get("kind",[""])[0];name=query.get("name",[""])[0]
                valid=(name in [s+".png" for s in SPEAKERS]) if kind=="portrait" else bool(re.fullmatch(r"0(?:0[1-9]|[1-3]\d|4[0-5])\.wav",name)) if kind=="voice" else False
                limit=25_000_000 if kind=="portrait" else 75_000_000
                if not valid or size>limit or size<44:
                    return self._json(400,{"error":"Invalid original media name/size"})
                if kind=="portrait" and self.headers.get("X-Portrait-Rights-Confirmed")!="YES":
                    return self._json(403,{"error":"Explicit self-attested portrait rights declaration required"})
                # ONE exclusive lock protects BOTH media upload and source-binding
                # jobs; the old lock.locked() check allowed a time-of-check race.
                if not lock.acquire(blocking=False):
                    return self._json(409,{"error":"Active private task/media import; retry later"})
                try:
                    code,payload=self._import_original(kind,name,size)
                finally:
                    lock.release()
                # Reply only after BOTH cross-process and server locks have
                # been released. A disconnected client cannot roll back an
                # already validated file merely because the socket write fails.
                return self._json(code,payload)
            return self._json(404,{"error":"Unknown private API"})
        def _import_original(self,kind,name,size):
            try:
                # Media may be imported before INIT (historical dashboard
                # workflow). Lazily create only the *private lock folder*;
                # do not create a project or bind originals automatically.
                source_lock_dir=root/"source"
                if source_lock_dir.is_symlink():
                    return (400,{"error":"Unsafe private source-lock directory"})
                source_lock_dir.mkdir(parents=True,exist_ok=True)
                if source_lock_dir.is_symlink():
                    return (400,{"error":"Unsafe private source-lock directory"})
                # Unlike the per-server threading.Lock, this EXCLUSIVE
                # filesystem lock also serializes separate Windows/Python
                # TTS and BIND processes running against the same studio.
                with original_voice_lock(root):
                    bound=root/"source"/SOURCE_FILE
                    if bound.exists() or bound.is_symlink():
                        return (409,{"error":"Original source SHA already bound; all media imports closed"})
                    folder=root/("portraits" if kind=="portrait" else "voices")
                    if folder.is_symlink():
                        return (400,{"error":"Unsafe private media directory symlink"})
                    folder.mkdir(parents=True,exist_ok=True)
                    if folder.is_symlink():
                        return (400,{"error":"Unsafe private media directory symlink"})
                    target=folder/name
                    created=False
                    try:
                        with target.open("xb") as file:
                            created=True
                            pending=size
                            while pending:
                                piece=self.rfile.read(min(pending,1024*1024))
                                if not piece:raise ValueError("Upload interrupted")
                                file.write(piece);pending-=len(piece)
                        if kind=="voice":wav_info(target)
                        else:
                            from PIL import Image
                            with Image.open(target) as im: im.verify()
                            with Image.open(target) as im:
                                if im.format!="PNG" or min(im.size)<200:
                                    raise ValueError("Portrait must be PNG >=200px")
                        return (201,{"original_local_file_imported":name,
                                               "portrait_rights_independently_verified":False})
                    except FileExistsError:
                        return (409,{"error":"Original exists; refused overwrite"})
                    except Exception:
                        if created:target.unlink(missing_ok=True)
                        return (400,{"error":"Invalid, incomplete or unsupported private media"})
            except ValueError as err:
                return (409,{"error":"Cross-process original source lock/blocker: "+str(err)})

        def log_message(self,format,*args):pass  # no local portrait or private URL traces

    http=ThreadingHTTPServer(("127.0.0.1",port),Handler)
    url=f"http://127.0.0.1:{port}"
    print(f"Private local studio: {url} ; private workspace outside repo",flush=True)
    try:
        if open_browser:
            # The socket is already successfully bound/listening. Do not open
            # a browser pointing at another process on an occupied port.
            import webbrowser
            try:
                if not webbrowser.open(url):
                    print("Open the private dashboard URL manually.",flush=True)
            except (OSError, webbrowser.Error):
                print("Browser unavailable; open the private dashboard URL manually.",flush=True)
        http.serve_forever()
    finally:http.server_close()