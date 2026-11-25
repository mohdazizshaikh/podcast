"""Local-only dashboard: explicit one-click source actions + private file imports.

No media/portrait HTTP GET endpoints, automatic publishing, or model downloads.
V4 local inference requires explicit selected-engine consent; cloud AI remains CLI-only. Stateful CSRF token per local server instance.
"""
from __future__ import annotations

import json
import os
import re
import secrets
import threading
import time
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
from . import production_overview, dashboard_actions, dashboard_authoring, dashboard_review, projects

STYLE="""body{font:16px system-ui;background:#121b2b;color:#f4f7ff;margin:auto;max-width:1100px;padding:28px}
header{padding:18px;border-bottom:1px solid #53627c}.panel{padding:18px;margin:18px 0;border:1px solid #4c5a70;border-radius:12px}
button{padding:12px 18px;border-radius:7px;border:0;margin:4px;cursor:pointer;font-weight:600}
small{color:#c5d1e6}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#233149;padding:16px}input{margin:8px}label{display:inline-block;padding:6px}
"""


def html_page(token:str)->str:
    # Static trusted markup, token is exclusively server-generated hex.
    return '''<!doctype html><html lang="hi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none';style-src 'unsafe-inline';script-src 'unsafe-inline';connect-src 'self';media-src blob:;img-src blob:;form-action 'none';base-uri 'none'">
<title>Podcast GPT — Private Hindi Studio</title><style>'''+STYLE+'''</style></head><body>
<header><h1>Podcast GPT — Private Hindi Studio</h1>
<p>Three human-authorized presenters, original 45 Hindi turns, true WAV sample provenance and CPU-only rendering.</p>
<small>Localhost-only. Your portraits, voices and rendered media stay on your computer and are never served over HTTP. V4 local inference requires separate explicit model consent; original V3 neural inference and cloud AI remain CLI-only.</small></header>
<section class="panel"><h2>0. V4 Smart setup — hardware and model readiness</h2>
<button data-action="setup-wizard">Inspect hardware, storage and installed app packages</button>
<button data-action="model-setup-plan">Show guided local model setup plan</button>
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
<h3>Character library and cast</h3>
<button id="v4CharList">List characters</button>
<label>Character ID / optional parent <input id="v4CharId" maxlength="32"></label><button id="v4CharShow">Load profile</button><button id="v4PortraitBrief">Show local portrait prompt</button>
<label>Trusted local Stable Diffusion directory <input id="v4PortraitModel" maxlength="2048"></label>
<label>Seed <input id="v4PortraitSeed" type="number" min="0" max="4294967295" value="42"></label>
<label>Steps <input id="v4PortraitSteps" type="number" min="10" max="30" value="20"></label>
<button id="v4PortraitPreflight">Check local portrait model</button>
<label><input id="v4PortraitConsent" type="checkbox"> I trust this local model and authorize CPU generation and have usage rights</label>
<button id="v4PortraitGenerate">Generate one portrait candidate</button>
<button id="v4PortraitCandidates">List local portrait attempts</button>
<label>Candidate ID <input id="v4PortraitCandidate" maxlength="32"></label><button id="v4PortraitAudit">Audit candidate and show local file path</button>
<label>Choose audited PNG locally <input id="v4PortraitViewFile" type="file" accept=".png" disabled></label>
<p id="v4PortraitViewInfo">Audit a candidate first.</p><img id="v4PortraitView" alt="Hash-verified local portrait candidate" style="display:none;max-width:256px;width:100%">
<label><input id="v4CandidateRights" type="checkbox"> I inspected this exact local PNG and have usage rights</label><button id="v4CandidateAttach">Attach candidate as new character version</button>
<button id="v4JapaneseResources">Check Japanese local dictionary resources</button>
<label>Name <input id="v4CharName" maxlength="80"></label>
<label>Personality <input id="v4CharPersonality" maxlength="600"></label>
<label>Speaking style <input id="v4CharStyle" maxlength="600"></label>
<label>Appearance <input id="v4CharAppearance" maxlength="1000"></label>
<label>Voice engine <select id="v4CharEngine"><option>undecided</option><option>imported</option><option>kokoro</option><option>espeak</option><option>edge</option></select></label>
<label>Voice language <input id="v4CharLanguage" value="Hindi" maxlength="80"></label>
<label>Voice preset <input id="v4CharPreset" maxlength="100"></label>
<label>Voice notes <input id="v4CharNotes" maxlength="400"></label>
<button id="v4CharCreate">Create new character version</button>
<label>Authorized portrait PNG <input id="v4Portrait" type="file" accept=".png"></label>
<label><input id="v4PortraitRights" type="checkbox"> I have rights to this portrait</label>
<button id="v4PortraitAttach">Attach portrait as new version</button>
<button id="v4CastLoad">Load selected project cast and choices</button><div id="v4CastRows"></div>
<button id="v4CastAssign">Assign immutable cast</button>
<h3>Project source input</h3>
<label>Local PDF, DOCX, TXT or MD <input id="v4SourceFile" type="file" accept=".pdf,.docx,.txt,.md"></label>
<button id="v4SourceImport">Import selected local source</button>
<label>Public HTTPS URL <input id="v4SourceUrl" maxlength="2048"></label>
<label><input id="v4WebConsent" type="checkbox"> Retrieve this public URL over the internet</label>
<button id="v4SourceWeb">Capture URL source</button>
<h3>Local model path configuration</h3>
<button id="v4ModelStatus">Check saved configurations</button>
<label>Engine <select id="v4ModelEngine"><option>kokoro</option><option>sadtalker</option><option>espeak</option></select></label>
<label>Model file / directory <input id="v4ModelPath" maxlength="2048"></label>
<label>Voices file <input id="v4VoicesPath" maxlength="2048"></label>
<label>Python executable <input id="v4PythonPath" maxlength="2048"></label>
<label>eSpeak executable <input id="v4ExePath" maxlength="2048"></label>
<label><input id="v4ModelReplace" type="checkbox"> Explicitly replace previous configuration</label>
<button id="v4ModelSave">Save selected paths (no execution)</button>
<p><label><input id="v4AuthorConsent" type="checkbox"> I authorize the selected local authoring or import action</label></p>
<small>Selected files go only to this localhost application. Use trusted sources and model paths. No AI inference or dependency install in these authoring controls.</small>
<h3>Research pack</h3>
<label>Optional public search query <input id="v4ResearchQuery" maxlength="200"></label>
<label>Wikipedia edition <select id="v4ResearchEdition"><option>en</option><option>hi</option><option>mr</option><option>bn</option><option>gu</option><option>ta</option><option>te</option><option>ur</option><option>es</option><option>fr</option><option>it</option><option>pt</option><option>de</option><option>ja</option><option>zh</option><option>ar</option><option>ru</option></select></label>
<label>2–4 distinct public HTTPS source URLs (one per line) <textarea id="v4ResearchUrls" rows="4" maxlength="8200"></textarea></label>
<label><input id="v4ResearchConsent" type="checkbox"> I authorize the selected public internet search or source retrieval</label>
<button id="v4ResearchDiscover">Discover Wikipedia candidates</button><button id="v4ResearchCapture">Capture selected research sources</button><button id="v4ResearchStatus">Inspect saved research pack</button><button id="v4ResearchCoverage">Inspect exact citation coverage</button>
<button id="v4ManualScript">Import captured structured script verbatim (knowledge mode)</button>
<h3>Import script edits and record reviewed observations</h3>
<label>Review type <select id="v4ReviewKind"><option value="script-edit">Script revision (no approval)</option><option value="script">Script review</option><option value="audio">Master audio review</option><option value="pilot">Pilot review</option><option value="final">Final video review</option><option value="studio">Neural studio review</option><option value="mix">Mix listening review</option><option value="mixed">Mixed video review</option><option value="mixed-studio">Mixed studio review</option><option value="fact">Factual review</option></select></label>
<button id="v4ReviewTemplate">Create private JSON template</button>
<label>Completed JSON file <input id="v4ReviewFile" type="file" accept=".json"></label>
<label>Exact full-review declaration (shown below, not needed for script revision) <input id="v4ReviewAck" maxlength="100"></label>
<p id="v4ReviewDeclaration"></p>
<button id="v4ReviewImport">Import selected completed JSON</button>
<small>Review all current media and criteria yourself before recording. No automatic PASS; existing review receipts cannot be overwritten.</small>
<h3>Voice and device preflight</h3>
<button id="v4VoicePreflight">Check voice selections and saved paths</button>
<button id="v4DeviceAcceptance">Inspect device acceptance checklist</button>
<button id="v4TurnDiagnostics">Measure individual master dialogue levels</button>
<h3>Audio post-production</h3>
<label>Optional intro WAV (max 30 s) <input id="v4MixIntro" type="file" accept=".wav"></label>
<label>Optional background WAV (max 120 s) <input id="v4MixBed" type="file" accept=".wav"></label>
<label>Optional outro WAV (max 30 s) <input id="v4MixOutro" type="file" accept=".wav"></label>
<label>Speech peak PCM <input id="v4MixSpeech" type="number" min="8000" max="24000" value="22000"></label>
<label>Music peak PCM <input id="v4MixMusic" type="number" min="0" max="6000" value="3000"></label>
<label>Ducking percent <input id="v4MixDuck" type="number" min="0" max="90" value="0"></label>
<label>Optional LUFS target (blank disables) <input id="v4MixTarget" type="number" min="-24" max="-14"></label>
<label>Speech compression ratio (1 disables) <input id="v4MixRatio" type="number" min="1" max="6" value="1"></label>
<label>Compression threshold PCM <input id="v4MixThreshold" type="number" min="2000" max="20000" value="12000"></label>
<label><input id="v4MixDc" type="checkbox"> Optional dialogue DC-offset correction</label>
<label>Soft gate threshold PCM (0 disables) <input id="v4MixGate" type="number" min="0" max="1000" value="0"></label>
<label>Sample peak limiter ceiling PCM (0 disables; otherwise 8000–28000; takes priority over LUFS target) <input id="v4MixLimiter" type="number" min="0" max="28000" value="0"></label>
<label><input id="v4MixRights" type="checkbox"> I authorize this mix and have rights to all added audio</label>
<button id="v4MixCompose">Compose separate audio mix</button>
<small>Local files only, mono PCM16 16 kHz. Existing mix cannot be replaced. Listen to the whole candidate before approval.</small>
<h3>Voice import and studio settings</h3>
<label>Approved script turn ID <input id="v4TurnId" maxlength="4"></label>
<label>Matching local mono PCM16 16 kHz WAV <input id="v4TurnWav" type="file" accept=".wav"></label>
<label><input id="v4TurnRights" type="checkbox"> I have rights and this recording matches the exact approved dialogue</label>
<button id="v4TurnImport">Import one dialogue recording</button>
<label>Studio layout <select id="v4StudioLayout"><option>focus</option><option>grid</option></select></label>
<label>Neural speaker camera <select id="v4StudioCamera"><option value="fixed">Fixed</option><option value="push-in">Subtle push-in</option></select></label>
<label>Optional local studio background PNG <input id="v4StudioBg" type="file" accept=".png"></label>
<label><input id="v4StudioRights" type="checkbox"> I have rights to use the selected background</label>
<button id="v4StudioSave">Save immutable studio settings</button><button id="v4StudioStatus">Inspect studio settings</button>
<h3>Selected prior-episode continuity</h3>
<label>Prior reviewed project ID <input id="v4PriorId" maxlength="32"></label>
<label>Prior turn IDs (1–8, comma separated) <input id="v4PriorTurns" maxlength="48"></label>
<label><input id="v4ContinuityConsent" type="checkbox"> I authorize selected reviewed excerpts for local-only drafting</label>
<button id="v4ContinuitySave">Freeze continuity snapshot</button><button id="v4ContinuityStatus">Inspect continuity</button>
<h3>Explicit free-policy cloud text drafting</h3>
<p>One outline or one script unit. Current topic, source evidence, research and relevant persona context may be sent to OpenRouter and, only with separate confirmation, Gemini. Local Ollama fallback may execute. No paid fallback; provider billing status cannot be independently verified. Set keys through the CLI.</p>
<label><input id="v4CloudConsent" type="checkbox"> I authorize this text transfer and eligible local fallback now</label>
<label><input id="v4GeminiConsent" type="checkbox"> I confirm my Gemini project is unbilled Free Tier and authorize Gemini fallback</label>
<button id="v4CloudDraft">Run one consented drafting action</button>
<h3>Optional online Edge speech</h3>
<p>Preview approved pending turns without network access. Online generation sends selected dialogue and voice presets to Edge. No automatic fallback or guaranteed availability.</p>
<label>Maximum new turns <input id="v4EdgeCount" type="number" min="1" max="5" value="1"></label>
<button id="v4EdgePlan">Preview pending Edge turns (offline)</button>
<label>Optional voice language filter <input id="v4EdgeLanguage" maxlength="80"></label>
<label><input id="v4EdgeInventoryConsent" type="checkbox"> I authorize an online voice inventory request (no dialogue)</label>
<button id="v4EdgeInventory">Discover online voices</button>
<label><input id="v4EdgeConsent" type="checkbox"> I have usage rights and authorize sending selected approved dialogue and voice presets to Edge now</label>
<button id="v4EdgeGenerate">Generate bounded online speech</button>
<h3>Explicit local AI production</h3>
<label>Engine <select id="v4InferenceEngine"><option value="ollama">Ollama — local script</option><option value="kokoro">Kokoro — voice</option><option value="espeak">eSpeak — voice</option><option value="sadtalker">SadTalker — neural clips</option></select></label>
<label>Maximum actions <input id="v4InferenceSteps" type="number" min="1" max="5" value="1"></label>
<label><input id="v4InferenceConsent" type="checkbox"> I trust the selected local installation, have usage rights and authorize execution now</label>
<button id="v4InferenceRun">Run bounded local inference</button>
<p><small>No cloud AI or automatic model downloads authorized. Local third-party programs are not sandboxed. Human review and missing-input gates stop processing. Do not close the app while a task is running.</small></p>
<h3>Explicit local production actions</h3>
<label><input type="checkbox" id="v4ProcessConsent"> I authorize the selected local processing action. No AI inference or approval is authorized here.</label>
<select id="v4Process"><option value="project-safe-step">One eligible non-inference production step</option><option value="project-script-visual-edit">Create offline script editor</option><option value="project-script-visual-review">Create script review page</option><option value="project-audio-visual-review">Create audio review page</option><option value="project-pilot-visual-review">Create pilot review page</option><option value="project-final-visual-review">Create final review page</option><option value="project-static-render">Render static preview</option><option value="project-studio-render">Render static studio</option><option value="project-neural-studio-compose">Compose neural studio from saved clips</option><option value="project-mixed-studio-compose">Compose mixed neural studio</option></select>
<button id="v4Run">Run selected local action</button>
<h3>Verified local playback</h3>
<label>Media type <select id="v4MediaKind"><option value="master">Master WAV</option><option value="preview">Static preview</option><option value="neural">Neural video</option><option value="mix">Audio mix</option><option value="mixed">Mixed video</option><option value="studio-preview">Static studio</option><option value="neural-studio">Neural studio</option><option value="mixed-neural-studio">Mixed neural studio</option></select></label>
<button id="v4MediaCheck">Audit selected media</button>
<button id="v4AudioDiagnostics">Measure selected master/mix loudness (read-only)</button>
<button id="v4VideoAudioCheck">Compare selected video audio to verified source (read-only)</button>
<p id="v4MediaInfo">Audit first, then select the matching local file (128 MiB maximum for browser hash check).</p>
<input type="file" id="v4LocalMedia" accept=".wav,.mp4" disabled><video id="v4Player" controls preload="none" style="max-width:100%;display:none"></video>
<p><small>File bytes stay in this browser tab; no upload or HTTP media endpoint. Large files: use the displayed local path in your own player.</small></p>
<small>Cloud drafting requires separate per-action consent; API keys remain CLI-only. Review imports require explicit full-review declarations.</small></section>
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
<section class="panel"><h2>Local task log</h2><p id="v4TaskProgress" aria-live="polite">Idle</p><button id="v4RefreshTask">Refresh task status</button><button id="v4StopTask" disabled>Stop after current verified action</button><pre id="status" aria-live="polite">Ready. Nothing running.</pre></section>
<script>
'use strict';const token='''+json.dumps(token)+''';const out=document.getElementById('status');
async function send(endpoint,data,portraitRights=false){let opt={method:'POST',headers:{'X-CSRF-Token':token}};
if(portraitRights)opt.headers['X-Portrait-Rights-Confirmed']='YES';
if(data instanceof File){opt.body=data;opt.headers['Content-Type']='application/octet-stream'}
else if(data!==undefined&&data!==null){opt.body=JSON.stringify(data);opt.headers['Content-Type']='application/json'}
let r=await fetch(endpoint,opt);let j=await r.json();if(!r.ok)throw new Error(j.error||('HTTP '+r.status));return j}
let manifest=null,blobUrl=null,castPid=null,mediaSequence=0;
let portraitManifest=null,portraitUrl=null,portraitSequence=0;
function clearPortrait(){portraitSequence++;portraitManifest=null;const img=document.getElementById("v4PortraitView");img.removeAttribute("src");img.style.display="none";if(portraitUrl){URL.revokeObjectURL(portraitUrl);portraitUrl=null}const file=document.getElementById("v4PortraitViewFile");file.value="";file.disabled=true;document.getElementById("v4CandidateRights").checked=false;document.getElementById("v4PortraitViewInfo").textContent="Audit a candidate first."}
function clearMedia(){mediaSequence++;manifest=null;let p=document.getElementById('v4Player');p.pause();p.removeAttribute('src');p.load();p.style.display='none';if(blobUrl){URL.revokeObjectURL(blobUrl);blobUrl=null}let i=document.getElementById('v4LocalMedia');i.value='';i.disabled=true}
function showResult(status){
 if(status.phase!=='complete'||!status.result)return;
 let data=status.result;
 if(status.command==='author-portrait-generate'&&data.candidate_id&&document.getElementById('v4PortraitCandidate').value!==data.candidate_id){clearPortrait();document.getElementById('v4PortraitCandidate').value=data.candidate_id;}
 if((status.command==='author-portrait-candidate'||status.command==='author-portrait-generate')&&data.candidate_integrity_checked&&data.candidate_id===document.getElementById('v4PortraitCandidate').value.trim()){
  if(!portraitManifest||portraitManifest.candidate_id!==data.candidate_id||portraitManifest.sha256!==data.receipt.portrait_sha256){clearPortrait();portraitManifest={candidate_id:data.candidate_id,sha256:data.receipt.portrait_sha256};document.getElementById('v4PortraitViewFile').disabled=false;document.getElementById('v4PortraitViewInfo').textContent='Select exact local PNG: '+data.path;}
 }
 if(status.command==='author-character-create'||status.command==='author-portrait'||status.command==='author-portrait-candidate-attach'){if(data.character_id)document.getElementById('v4CharId').value=data.character_id}
 if(status.command==='author-character-show'&&data.profile){let p=data.profile,v=p.voice_preferences;for(const [id,value] of Object.entries({v4CharName:p.name,v4CharPersonality:p.personality,v4CharStyle:p.speaking_style,v4CharAppearance:p.appearance,v4CharEngine:v.engine,v4CharLanguage:v.language,v4CharPreset:v.preset,v4CharNotes:v.style_notes}))document.getElementById(id).value=value}
 if(status.command==='author-cast-choices'&&data.project_id===document.getElementById('v4ProjectId').value.trim()){
  castPid=data.project_id;const area=document.getElementById('v4CastRows');area.replaceChildren();
  for(const speaker of data.presenters){const label=document.createElement('label');label.textContent=speaker+' ';const select=document.createElement('select');select.dataset.speaker=speaker;const empty=document.createElement('option');empty.value='';empty.textContent='Choose character';select.append(empty);for(const c of data.characters){const o=document.createElement('option');o.value=c.character_id;o.textContent=c.name+' — '+c.character_id+(c.portrait_present?'':' (no portrait)');select.append(o)}label.append(select);area.append(label)}
 }
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
let pollTimer=null,currentTask=null;
async function refresh(){
 if(pollTimer!==null){clearTimeout(pollTimer);pollTimer=null}
 let r=await fetch('/api/status',{cache:'no-store'});let status=await r.json();
 out.textContent=JSON.stringify(status,null,2);showResult(status);
 currentTask=status.task_id;document.getElementById("v4StopTask").disabled=!(status.phase==="running"&&["author-local-inference","author-edge-generate"].includes(status.command)&&!status.stop_requested);
 const progress=status.progress;document.getElementById('v4TaskProgress').textContent=status.phase+' | '+(status.command||'No task')+' | elapsed '+(status.elapsed_seconds??0)+' s'+(status.stop_requested?' | stop requested at next checkpoint':'')+(progress?' | '+progress.action+' | verified actions '+progress.completed_actions+'/'+progress.action_limit:'');
 if(status.phase==='running')pollTimer=setTimeout(()=>refresh().catch(e=>out.textContent='BLOCKED: '+e.message),1100);
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
const field=id=>document.getElementById(id);
const val=id=>field(id).value;
function authorConsent(){if(!field('v4AuthorConsent').checked)throw new Error('Explicit local authoring consent required');field('v4AuthorConsent').checked=false}
async function author(action,data,write=false){
 if(write)authorConsent();
 out.textContent=JSON.stringify(await send('/api/author?cmd='+encodeURIComponent(action)+(write?'&consent=YES':''),data),null,2);await refresh();
}
function onAuthor(id,fn){field(id).addEventListener('click',async()=>{try{await fn()}catch(e){out.textContent='BLOCKED: '+e.message}})}
onAuthor('v4CharList',()=>author('character-list',{}));
onAuthor('v4CharShow',()=>author('character-show',{character_id:val('v4CharId').trim()}));
onAuthor('v4PortraitBrief',()=>author('portrait-brief',{character_id:val('v4CharId').trim()}));
onAuthor('v4PortraitPreflight',()=>author('portrait-preflight',{character_id:val('v4CharId').trim(),model:val('v4PortraitModel')}));
onAuthor('v4PortraitGenerate',()=>{if(!field('v4PortraitConsent').checked)throw new Error('Confirm model trust and usage rights');field('v4PortraitConsent').checked=false;return author('portrait-generate',{character_id:val('v4CharId').trim(),model:val('v4PortraitModel'),seed:Number(val('v4PortraitSeed')),steps:Number(val('v4PortraitSteps')),model_consent:true},true)});
onAuthor('v4PortraitCandidates',()=>author('portrait-candidates',{}));
onAuthor('v4PortraitAudit',()=>{clearPortrait();return author('portrait-candidate',{candidate_id:val('v4PortraitCandidate').trim()})});
field('v4PortraitCandidate').addEventListener('input',clearPortrait);
field('v4PortraitViewFile').addEventListener('change',async()=>{
 const selected=portraitManifest,seq=++portraitSequence,img=field('v4PortraitView'),info=field('v4PortraitViewInfo'),file=field('v4PortraitViewFile').files[0];
 img.removeAttribute('src');img.style.display='none';if(portraitUrl){URL.revokeObjectURL(portraitUrl);portraitUrl=null}field('v4CandidateRights').checked=false;
 try{if(!selected||!file||file.size>12*1024*1024||!globalThis.crypto?.subtle)throw new Error('Select matching bounded local PNG with browser SHA-256 support');
 const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',await file.arrayBuffer())),b=>b.toString(16).padStart(2,'0')).join('');
 if(portraitSequence!==seq||portraitManifest!==selected)return;if(hash!==selected.sha256)throw new Error('PNG differs from audited candidate');
 portraitUrl=URL.createObjectURL(new Blob([file],{type:'image/png'}));img.src=portraitUrl;img.style.display='block';info.textContent='Local PNG hash matches candidate. Inspect the image before attachment.';
 }catch(e){if(portraitSequence===seq&&portraitManifest===selected)info.textContent='BLOCKED: '+e.message}
});
onAuthor('v4CandidateAttach',()=>{if(!field('v4CandidateRights').checked)throw new Error('Inspect exact candidate and confirm rights');field('v4CandidateRights').checked=false;return author('portrait-candidate-attach',{candidate_id:val('v4PortraitCandidate').trim(),rights:true},true)});
onAuthor('v4JapaneseResources',()=>author('japanese-resources',{}));
onAuthor('v4CharCreate',()=>author('character-create',{parent_id:val('v4CharId').trim()||null,profile:{name:val('v4CharName'),personality:val('v4CharPersonality'),speaking_style:val('v4CharStyle'),appearance:val('v4CharAppearance'),voice_preferences:{engine:val('v4CharEngine'),language:val('v4CharLanguage'),preset:val('v4CharPreset'),style_notes:val('v4CharNotes')}}},true));
onAuthor('v4CastLoad',()=>author('cast-choices',{project_id:currentPid()}));
onAuthor('v4CastAssign',()=>{if(castPid!==currentPid())throw new Error('Load cast choices for selected project');const mapping=Object.fromEntries(Array.from(field('v4CastRows').querySelectorAll('select'),s=>[s.dataset.speaker,s.value]));return author('cast-assign',{project_id:currentPid(),mapping},true)});
async function authorFile(kind,id,file,rights=false,extra=''){if(!file)throw new Error('Select a local file first');authorConsent();out.textContent=JSON.stringify(await send('/api/author-file?kind='+encodeURIComponent(kind)+'&id='+encodeURIComponent(id)+'&name='+encodeURIComponent(file.name)+'&consent=YES'+extra,file,rights),null,2);await refresh()}
onAuthor('v4PortraitAttach',()=>{if(!field('v4PortraitRights').checked)throw new Error('Confirm portrait rights');field('v4PortraitRights').checked=false;return authorFile('portrait',val('v4CharId').trim(),field('v4Portrait').files[0],true)});
onAuthor('v4SourceImport',()=>authorFile('source',currentPid(),field('v4SourceFile').files[0]));
onAuthor('v4VoicePreflight',()=>author('voice-preflight',{project_id:currentPid()}));
onAuthor('v4DeviceAcceptance',()=>author('device-acceptance',{project_id:currentPid()}));
onAuthor('v4TurnDiagnostics',()=>author('turn-diagnostics',{project_id:currentPid()}));
onAuthor('v4VideoAudioCheck',()=>author('video-audio-check',{project_id:currentPid(),kind:val('v4MediaKind')}));
async function encodeWav(file,limit){
 if(!file||file.size<44||file.size>limit||!file.name.toLowerCase().endsWith('.wav'))throw new Error('Select a bounded WAV file');
 const bytes=new Uint8Array(await file.arrayBuffer());let parts=[];
 for(let i=0;i<bytes.length;i+=16384)parts.push(String.fromCharCode(...bytes.subarray(i,i+16384)));
 return btoa(parts.join(''));
}
onAuthor('v4MixCompose',async()=>{
 if(!field('v4MixRights').checked)throw new Error('Confirm audio rights and mix processing');
 const pid=currentPid(),files={intro:field('v4MixIntro').files[0],bed:field('v4MixBed').files[0],outro:field('v4MixOutro').files[0]};
 const data={project_id:pid,assets:{},speech_peak:Number(val('v4MixSpeech')),bed_peak:Number(val('v4MixMusic')),duck_percent:Number(val('v4MixDuck')),target_lufs:val('v4MixTarget')===''?null:Number(val('v4MixTarget')),compress_ratio:Number(val('v4MixRatio')),compress_threshold:Number(val('v4MixThreshold')),remove_dc:field('v4MixDc').checked,gate_threshold:Number(val('v4MixGate')),limiter_ceiling:Number(val('v4MixLimiter')),rights:true};
 authorConsent();field('v4MixRights').checked=false;
 for(const role of Object.keys(files))if(files[role])data.assets[role]=await encodeWav(files[role],(role==='bed'?120:30)*32000+65536);
 if(pid!==currentPid())throw new Error('Project selection changed; reconfirm mix');
 out.textContent=JSON.stringify(await send('/api/mix-compose?consent=YES',data),null,2);await refresh();
});
onAuthor('v4TurnImport',()=>{if(!field('v4TurnRights').checked)throw new Error('Confirm matching dialogue and rights');field('v4TurnRights').checked=false;return authorFile('audio-turn',currentPid(),field('v4TurnWav').files[0],true,'&unit='+encodeURIComponent(val('v4TurnId').trim()))});
onAuthor('v4StudioSave',()=>{const file=field('v4StudioBg').files[0],layout=val('v4StudioLayout'),camera=val('v4StudioCamera');if(!file)return author('studio-configure',{project_id:currentPid(),layout,camera},true);if(!field('v4StudioRights').checked)throw new Error('Confirm background rights');field('v4StudioRights').checked=false;return authorFile('studio-background',currentPid(),file,true,'&layout='+encodeURIComponent(layout)+'&camera='+encodeURIComponent(camera))});
onAuthor('v4StudioStatus',()=>author('studio-status',{project_id:currentPid()}));
onAuthor('v4ContinuitySave',()=>{if(!field('v4ContinuityConsent').checked)throw new Error('Explicit local continuity consent required');field('v4ContinuityConsent').checked=false;return author('continuity-enable',{project_id:currentPid(),prior_project_id:val('v4PriorId').trim(),turn_ids:val('v4PriorTurns').split(',').map(s=>s.trim()),local_only_consent:true},true)});
onAuthor('v4ContinuityStatus',()=>author('continuity-status',{project_id:currentPid()}));
onAuthor('v4EdgePlan',()=>author('edge-plan',{project_id:currentPid(),max_new:Number(val('v4EdgeCount'))}));
onAuthor('v4EdgeInventory',()=>{if(!field('v4EdgeInventoryConsent').checked)throw new Error('Explicit inventory network consent required');field('v4EdgeInventoryConsent').checked=false;return author('edge-inventory',{language:val('v4EdgeLanguage').trim()||null,network_consent:true},true)});
onAuthor('v4EdgeGenerate',()=>{if(!field('v4EdgeConsent').checked)throw new Error('Explicit dialogue transfer consent and rights required');field('v4EdgeConsent').checked=false;return author('edge-generate',{project_id:currentPid(),max_new:Number(val('v4EdgeCount')),network_consent:true},true)});
onAuthor('v4CloudDraft',()=>{if(!field('v4CloudConsent').checked)throw new Error('Explicit cloud text consent required');const gemini=field('v4GeminiConsent').checked;field('v4CloudConsent').checked=false;field('v4GeminiConsent').checked=false;return author('cloud-draft',{project_id:currentPid(),cloud_consent:true,confirm_gemini_free_project:gemini},true)});
onAuthor('v4SourceWeb',()=>{if(!field('v4WebConsent').checked)throw new Error('Explicit internet retrieval consent required');field('v4WebConsent').checked=false;return author('source-url',{project_id:currentPid(),url:val('v4SourceUrl').trim(),allow_web_fetch:true},true)});
function researchConsent(){if(!field('v4ResearchConsent').checked)throw new Error('Explicit public internet consent required');field('v4ResearchConsent').checked=false}
onAuthor('v4ResearchDiscover',()=>{researchConsent();return author('research-discover',{project_id:currentPid(),query:val('v4ResearchQuery').trim()||null,edition:val('v4ResearchEdition'),allow_web_search:true},true)});
onAuthor('v4ResearchCapture',()=>{researchConsent();return author('research-capture',{project_id:currentPid(),urls:val('v4ResearchUrls').split(/\\r?\\n/).map(s=>s.trim()).filter(Boolean),allow_web_fetch:true},true)});
onAuthor('v4ResearchStatus',()=>author('research-status',{project_id:currentPid()}));
onAuthor('v4ResearchCoverage',()=>author('research-coverage',{project_id:currentPid()}));
onAuthor('v4InferenceRun',()=>{if(!field('v4InferenceConsent').checked)throw new Error('Explicit local model trust and usage rights required');field('v4InferenceConsent').checked=false;return author('local-inference',{project_id:currentPid(),engine:val('v4InferenceEngine'),max_steps:Number(val('v4InferenceSteps')),model_consent:true},true)});
onAuthor('v4RefreshTask',()=>refresh());
onAuthor('v4StopTask',async()=>{if(!currentTask)throw new Error('Refresh current task first');await send('/api/stop?task_id='+encodeURIComponent(currentTask));await refresh()});
onAuthor('v4ManualScript',()=>author('manual-script',{project_id:currentPid()},true));
const reviewAcks='''+json.dumps(dashboard_review.ATTEST)+''';
function reviewDeclaration(){field('v4ReviewAck').value='';field('v4ReviewDeclaration').textContent=reviewAcks[val('v4ReviewKind')]||'Script edit only — no approval declaration'}
field('v4ReviewKind').addEventListener('change',reviewDeclaration);reviewDeclaration();
onAuthor('v4ReviewTemplate',()=>author('review-template',{project_id:currentPid(),kind:val('v4ReviewKind')},true));
onAuthor('v4ReviewImport',async()=>{
 const kind=val('v4ReviewKind'),file=field('v4ReviewFile').files[0],ack=val('v4ReviewAck');
 if(!file||!file.name.toLowerCase().endsWith('.json'))throw new Error('Select completed JSON');
 if(ack!==(reviewAcks[kind]||''))throw new Error('Enter the exact full review declaration');
 authorConsent();field('v4ReviewAck').value='';
 out.textContent=JSON.stringify(await send('/api/review-import?project_id='+encodeURIComponent(currentPid())+'&kind='+encodeURIComponent(kind)+'&consent=YES&attestation='+encodeURIComponent(ack),file),null,2);await refresh();
});
onAuthor('v4ModelStatus',()=>author('model-status',{}));
onAuthor('v4ModelSave',()=>{const engine=val('v4ModelEngine'),paths=engine==='kokoro'?{model:val('v4ModelPath'),voices:val('v4VoicesPath')}:engine==='sadtalker'?{model:val('v4ModelPath'),python:val('v4PythonPath')}:{executable:val('v4ExePath')};const replace=field('v4ModelReplace').checked;field('v4ModelReplace').checked=false;return author('model-configure',{engine,paths,replace},true)});
field('v4ProjectId').addEventListener('input',()=>{castPid=null;field('v4CastRows').replaceChildren()});
document.getElementById('v4Overview').addEventListener('click',()=>{try{action('project-production-overview',currentPid())}catch(e){out.textContent=e.message}});
document.getElementById('v4AudioDiagnostics').addEventListener('click',()=>{try{const kind=val('v4MediaKind');if(!['master','mix'].includes(kind))throw new Error('Choose master or mix');action('project-audio-diagnostics',currentPid(),kind)}catch(e){out.textContent=e.message}});
document.getElementById('v4MediaCheck').addEventListener('click',()=>{try{clearMedia();document.getElementById('v4MediaInfo').textContent='Auditing current candidate...';action('project-media-check',currentPid(),document.getElementById('v4MediaKind').value)}catch(e){out.textContent=e.message}});
for(const id of ['v4ProjectId','v4MediaKind'])document.getElementById(id).addEventListener('input',()=>{clearMedia();document.getElementById('v4MediaInfo').textContent='Audit the current selection first.';document.getElementById('v4Summary').replaceChildren()});
document.getElementById('v4LocalMedia').addEventListener('change',async()=>{
 const seq=++mediaSequence,selected=manifest,info=document.getElementById('v4MediaInfo'),player=document.getElementById('v4Player');
 const file=document.getElementById('v4LocalMedia').files[0];
 player.pause();player.removeAttribute('src');player.load();player.style.display='none';if(blobUrl){URL.revokeObjectURL(blobUrl);blobUrl=null}
 try{
  if(!selected||!file||!selected.browser_check_supported||file.size!==selected.bytes||file.size>134217728)throw new Error('Select the matching verified file within the browser size limit');
  if(!globalThis.crypto?.subtle)throw new Error('Browser SHA-256 unavailable; use a local player');
  const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',await file.arrayBuffer())),b=>b.toString(16).padStart(2,'0')).join('');
  if(manifest!==selected||seq!==mediaSequence)return;
  if(hash!==selected.sha256)throw new Error('Selected file differs from audited SHA-256');
  blobUrl=URL.createObjectURL(file);player.src=blobUrl;player.style.display='block';info.textContent='Local file hash matches audited candidate. Use playback controls; no review saved.';
 }catch(e){if(manifest===selected&&seq===mediaSequence)info.textContent='BLOCKED: '+e.message}
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
    from . import model_setup_plan,audio_diagnostics,dashboard_mix
    root=workspace_path(root);root.mkdir(parents=True,exist_ok=True)
    token=secrets.token_hex(32)
    status={"phase":"idle","command":None,"result":None,"progress":None,"elapsed_seconds":0}
    started=None
    active_stop=None
    lock=threading.Lock()
    state_lock=threading.Lock()
    actions={"init":lambda:init(root),"doctor":lambda:doctor(root),
             "setup-wizard":lambda:inspect_setup(root),
             "model-setup-plan":lambda:model_setup_plan.inspect(root),
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
                    if status["phase"]=="running" and started is not None:snapshot["elapsed_seconds"]=round(time.monotonic()-started,1)
                return self._json(200,snapshot)
            return self._json(404,{"error":"No HTTP media or private filesystem routes"})
        def do_POST(self):
            nonlocal started,active_stop
            if not self._allowed() or not secrets.compare_digest(self.headers.get("X-CSRF-Token",""),token):
                return self._json(403,{"error":"Blocked external/cross-origin/CSRF request"})
            size_str=self.headers.get("Content-Length","")
            if not size_str.isdecimal():return self._json(411,{"error":"Content-Length required"})
            size=int(size_str);url=urlsplit(self.path);query=parse_qs(url.query)
            if url.path=="/api/stop":
                if size!=0:return self._json(400,{"error":"Stop body must be empty"})
                with state_lock:
                    if status["phase"]!="running" or status["command"] not in ("author-local-inference","author-edge-generate") or query.get("task_id",[""])[0]!=status.get("task_id") or active_stop is None:
                        accepted=False
                    else:
                        active_stop.set();status["stop_requested"]=True;accepted=True
                return self._json(202 if accepted else 409,{"stop_requested":accepted,"note":"Current action is not forcibly interrupted"})
            stop_event=threading.Event()
            if url.path in ("/api/action","/api/project-create","/api/author","/api/author-file","/api/review-import","/api/mix-compose"):
                if url.path=="/api/mix-compose":
                    if not 1<=size<=dashboard_mix.LIMIT or self.headers.get("Content-Type")!="application/json":return self._json(400,{"error":"Invalid bounded mix request"})
                    if query.get("consent",[""])[0]!="YES":return self._json(403,{"error":"Explicit mix consent required"})
                    try:
                        self.connection.settimeout(20);raw=self.rfile.read(size)
                        if len(raw)!=size:raise ValueError("Incomplete mix request")
                        data=dashboard_mix.parse(raw)
                    except (ValueError,OSError) as err:return self._json(400,{"error":str(err)})
                    command="mix-compose";selected=lambda:dashboard_mix.run(root,data,acknowledgment=dashboard_mix.ACK)
                elif url.path=="/api/review-import":
                    pid=query.get("project_id",[""])[0];kind=query.get("kind",[""])[0]
                    if not ID_RE.fullmatch(pid) or kind not in dashboard_review.KINDS or not 1<=size<=dashboard_review.LIMIT or self.headers.get("Content-Type")!="application/octet-stream":return self._json(400,{"error":"Invalid review upload"})
                    if query.get("consent",[""])[0]!="YES":return self._json(403,{"error":"Explicit review import consent required"})
                    ack=query.get("attestation",[None])[0]
                    if kind!="script-edit" and ack!=dashboard_review.ATTEST[kind]:return self._json(403,{"error":"Exact selected review declaration required"})
                    try:
                        self.connection.settimeout(20);raw=self.rfile.read(size)
                        if len(raw)!=size:raise ValueError("Incomplete review upload")
                    except (ValueError,OSError) as err:return self._json(400,{"error":str(err)})
                    command="review-import";selected=lambda:dashboard_review.upload(root,pid,kind,raw,acknowledgment=dashboard_review.ACK,attestation=ack)
                elif url.path in ("/api/author","/api/author-file"):
                    is_file=url.path=="/api/author-file"
                    kind=query.get("kind",[""])[0]
                    action=query.get("cmd",[""])[0]
                    limit=dashboard_authoring.UPLOADS.get(kind,0) if is_file else dashboard_authoring.JSON_LIMIT
                    mime="application/octet-stream" if is_file else "application/json"
                    if not 1<=size<=limit or self.headers.get("Content-Type")!=mime:
                        return self._json(400,{"error":"Invalid bounded authoring request"})
                    if not is_file and action not in dashboard_authoring.ACTIONS:
                        return self._json(400,{"error":"Unknown authoring action"})
                    consent=dashboard_authoring.ACK if query.get("consent",[""])[0]=="YES" else None
                    if (is_file or action not in dashboard_authoring.READ_ONLY) and consent is None:
                        return self._json(403,{"error":"Explicit authoring consent required"})
                    try:
                        self.connection.settimeout(20)
                        raw=self.rfile.read(size)
                        if len(raw)!=size:raise ValueError("Incomplete authoring request")
                        if is_file:
                            identifier=query.get("id",[""])[0];name=query.get("name",[""])[0]
                            if not ID_RE.fullmatch(identifier):raise ValueError("Invalid target ID")
                            rights=self.headers.get("X-Portrait-Rights-Confirmed")=="YES"
                            command="author-"+kind
                            unit=query.get("unit",[None])[0];layout=query.get("layout",[None])[0];camera=query.get("camera",["fixed"])[0]
                            selected=lambda:dashboard_authoring.upload(root,kind,identifier,name,raw,acknowledgment=consent,rights=rights,unit=unit,layout=layout,camera=camera)
                        else:
                            data=dashboard_authoring.parse(raw)
                            command="author-"+action
                            def report(value):
                                with state_lock:status["progress"]=dict(value)
                            selected=lambda:dashboard_authoring.run(root,action,data,acknowledgment=consent,progress=report,should_stop=stop_event.is_set)
                    except (ValueError,OSError) as err:return self._json(400,{"error":str(err)})
                elif url.path=="/api/project-create":
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
                if url.path in ("/api/project-create","/api/author","/api/author-file","/api/review-import","/api/mix-compose"):pass
                elif command in dashboard_actions.ACTIONS:
                    pid=query.get("project_id",[""])[0]
                    if not ID_RE.fullmatch(pid):return self._json(400,{"error":"Invalid V4 project ID"})
                    if query.get("consent",[""])[0]!="YES":return self._json(403,{"error":"Explicit local processing consent required"})
                    selected=lambda:dashboard_actions.run(root,pid,command,acknowledgment=dashboard_actions.ACK)
                elif command in ("project-readiness","project-production-overview","project-media-check","project-audio-diagnostics"):
                    pid=query.get("project_id",[""])[0]
                    if not ID_RE.fullmatch(pid):return self._json(400,{"error":"Invalid V4 project ID"})
                    if command=="project-readiness":selected=lambda:inspect_v4_readiness(root,pid)
                    elif command=="project-production-overview":selected=lambda:production_overview.inspect(root,pid)
                    elif command=="project-audio-diagnostics":
                        kind=query.get("kind",[""])[0]
                        if kind not in ("master","mix"):return self._json(400,{"error":"Choose master or mix"})
                        selected=lambda:audio_diagnostics.inspect(root,pid,kind=kind)
                    else:
                        kind=query.get("kind",[""])[0]
                        if kind not in production_overview.MEDIA:return self._json(400,{"error":"Unknown media kind"})
                        selected=lambda:production_overview.media_check(root,pid,kind)
                elif command in actions:selected=actions[command]
                else:return self._json(400,{"error":"Unrecognized local action"})
                with state_lock:
                    accepted=lock.acquire(blocking=False)
                    if accepted:
                        started=time.monotonic()
                        active_stop=stop_event
                        status.update(phase="running",command=command,result=None,progress=None,elapsed_seconds=0,task_id=secrets.token_hex(16),stop_requested=False)
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
                            status.update(phase=phase,result=result,elapsed_seconds=round(time.monotonic()-started,1))
                try:
                    threading.Thread(target=run,daemon=True).start()
                except RuntimeError as err:
                    with state_lock:
                        lock.release()
                        status.update(phase="blocked",result={"error":str(err)})
                    return self._json(503,{"error":"Unable to start local task"})
                return self._json(202,{"task_started":command,"next":"Refresh /api/status for actual task status; only explicitly selected action authorized"})
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