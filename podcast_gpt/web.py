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
from .source import SPEAKERS,init,build_source,prepare_chunks,wav_info,read_json,workspace_path
from .media import render_static,audit_static
from .neural import progress

STYLE="""body{font:16px system-ui;background:#121b2b;color:#f4f7ff;margin:auto;max-width:1100px;padding:28px}
header{padding:18px;border-bottom:1px solid #53627c}.panel{padding:18px;margin:18px 0;border:1px solid #4c5a70;border-radius:12px}
button{padding:12px 18px;border-radius:7px;border:0;margin:4px;cursor:pointer;font-weight:600}
small{color:#c5d1e6}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#233149;padding:16px}input{margin:8px}label{display:inline-block;padding:6px}
"""


def html_page(token:str)->str:
    # Static trusted markup, token is exclusively server-generated hex.
    return '''<!doctype html><html lang="hi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none';style-src 'unsafe-inline';script-src 'unsafe-inline';connect-src 'self';form-action 'none';base-uri 'none'">
<title>Podcast GPT — Private Hindi Studio</title><style>'''+STYLE+'''</style></head><body>
<header><h1>Podcast GPT — Private Hindi Studio</h1>
<p>Three human-authorized presenters, original 45 Hindi turns, true WAV sample provenance and CPU-only rendering.</p>
<small>Localhost-only. Your portraits, voices and rendered media stay on your computer and are never served over HTTP. Online TTS and real SadTalker require separate explicit CLI consent.</small></header>
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
<p><small>Static is NOT lip-sync. Real SadTalker CPU models and one-per-presenter PILOT use the separate explicit-consent Windows launcher.</small></p></section>
<section class="panel"><h2>Local task log</h2><pre id="status" aria-live="polite">Ready. Nothing running.</pre></section>
<script>
'use strict';const token='''+json.dumps(token)+''';const out=document.getElementById('status');
async function send(endpoint,data,portraitRights=false){let opt={method:'POST',headers:{'X-CSRF-Token':token}};
if(portraitRights)opt.headers['X-Portrait-Rights-Confirmed']='YES';
if(data instanceof File){opt.body=data;opt.headers['Content-Type']='application/octet-stream'}
let r=await fetch(endpoint,opt);let j=await r.json();if(!r.ok)throw new Error(j.error||('HTTP '+r.status));return j}
async function refresh(){
 let r=await fetch('/api/status',{cache:'no-store'});let status=await r.json();
 out.textContent=JSON.stringify(status,null,2);
 if(status.phase==='running')setTimeout(()=>refresh().catch(e=>out.textContent='BLOCKED: '+e.message),1100);
}
async function action(name){try{
 out.textContent='Starting '+name+'...';
 let receipt=await send('/api/action?cmd='+encodeURIComponent(name));
 out.textContent=JSON.stringify(receipt,null,2);
 await refresh();
}catch(e){out.textContent='BLOCKED: '+e.message}}
document.querySelectorAll('[data-action]').forEach(b=>b.addEventListener('click',()=>action(b.dataset.action)));
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


def serve(root:Path,port:int=7860):
    if type(port)!=int or not 1024<=port<=65535:raise ValueError("Private loopback port 1024..65535")
    root=workspace_path(root);root.mkdir(parents=True,exist_ok=True)
    token=secrets.token_hex(32)
    status={"phase":"idle","command":None,"result":None}
    lock=threading.Lock()
    actions={"init":lambda:init(root),"doctor":lambda:doctor(root),
             "build-source":lambda:build_source(root),
             "prepare-chunks":lambda:prepare_chunks(root),
             "render-static":lambda:render_static(root),
             "audit-static":lambda:audit_static(root),
             "progress":lambda:progress(root)}

    class Handler(BaseHTTPRequestHandler):
        def _send(self,code:int,payload:bytes,kind="application/json"):
            self.send_response(code);self.send_header("Content-Type",kind+"; charset=utf-8")
            self.send_header("Cache-Control","no-store");self.send_header("X-Content-Type-Options","nosniff")
            self.send_header("Referrer-Policy","no-referrer")
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
            if self.path=="/api/status":return self._json(200,dict(status))
            return self._json(404,{"error":"No HTTP media or private filesystem routes"})
        def do_POST(self):
            if not self._allowed() or not secrets.compare_digest(self.headers.get("X-CSRF-Token",""),token):
                return self._json(403,{"error":"Blocked external/cross-origin/CSRF request"})
            size_str=self.headers.get("Content-Length","")
            if not size_str.isdecimal():return self._json(411,{"error":"Content-Length required"})
            size=int(size_str);url=urlsplit(self.path);query=parse_qs(url.query)
            if url.path=="/api/action":
                if size!=0:return self._json(400,{"error":"Action body must be empty"})
                command=query.get("cmd",[""])[0]
                if command not in actions:return self._json(400,{"error":"Unrecognized local action"})
                if not lock.acquire(blocking=False):return self._json(409,{"error":"Another explicit local task is running"})
                status.update(phase="running",command=command,result=None)
                def run():
                    try:
                        result=actions[command]()
                        status.update(phase="complete",result=result)
                    except Exception as e:
                        status.update(phase="blocked",result={"error":str(e)})
                    finally:lock.release()
                threading.Thread(target=run,daemon=True).start()
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
                    folder=root/("portraits" if kind=="portrait" else "voices")
                    if folder.is_symlink():
                        return self._json(400,{"error":"Unsafe private media directory symlink"})
                    folder.mkdir(parents=True,exist_ok=True)
                    if folder.is_symlink():
                        return self._json(400,{"error":"Unsafe private media directory symlink"})
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
                        return self._json(201,{"original_local_file_imported":name,
                                               "portrait_rights_independently_verified":False})
                    except FileExistsError:
                        return self._json(409,{"error":"Original exists; refused overwrite"})
                    except Exception:
                        if created:target.unlink(missing_ok=True)
                        return self._json(400,{"error":"Invalid, incomplete or unsupported private media"})
                finally:
                    lock.release()
            return self._json(404,{"error":"Unknown private API"})
        def log_message(self,format,*args):pass  # no local portrait or private URL traces

    http=ThreadingHTTPServer(("127.0.0.1",port),Handler)
    print(f"Private local studio: http://127.0.0.1:{port} ; private workspace outside repo")
    try:http.serve_forever()
    finally:http.server_close()