"""Private offline visual QA forms; media playback stays in a local player."""
import base64
import hashlib
import html
import json
from pathlib import Path
from . import projects, source, characters
from . import v4_audio_review as audio, v4_final_review as final, v4_neural as neural, v4_master, v4_export

JS=r"""
"use strict";
const m=JSON.parse(document.getElementById("payload").textContent);
function add(tag,text,parent){const n=document.createElement(tag);if(text!==null)n.textContent=text;parent.append(n);return n}
function controls(obj,parent){for(const key of Object.keys(obj)){
 if(typeof obj[key]==="object"){const s=add("section",null,parent);add("h2",key,s);controls(obj[key],s);continue}
 add("label",key.replaceAll("_"," "),parent);const select=add("select",null,parent);
 for(const v of ["UNREVIEWED","PASS","FAIL"]){const o=add("option",v,select);o.value=v}
 select.addEventListener("change",()=>obj[key]=select.value);
}}
for(const file of m.files)add("p",file,document.getElementById("files"));
for(const key of m.fields){const root=document.getElementById("rows");add("h2",key,root);controls(m.template[key],root)}
function incomplete(o){return Object.values(o).some(v=>typeof v==="object"?incomplete(v):v==="UNREVIEWED")}
document.getElementById("export").addEventListener("click",()=>{
 if(m.fields.some(k=>incomplete(m.template[k]))){document.getElementById("status").textContent="Complete every observation.";return}
 const u=URL.createObjectURL(new Blob([JSON.stringify(m.template,null,2)],{type:"application/json"}));
 const a=document.createElement("a");a.href=u;a.download=m.filename;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),1000);
 document.getElementById("status").textContent="Export requested. Record using the explicit CLI command; no approval saved.";
});
"""


def read_input(path,limit):
    path=Path(path).expanduser().absolute()
    source.workspace_path(path.parent)
    data=json.loads(characters._read_file(path,limit).decode("utf-8-sig"))
    if not isinstance(data,dict):raise ValueError("Review input must be a JSON object")
    return data


def build(value,files,fields,filename):
    payload=json.dumps({"template":value,"files":files,"fields":fields,"filename":filename},ensure_ascii=True).replace("<",r"\u003c").replace(">",r"\u003e").replace("&",r"\u0026")
    digest=base64.b64encode(hashlib.sha256(JS.encode()).digest()).decode("ascii")
    csp="default-src 'none'; script-src 'sha256-"+digest+"'; style-src 'unsafe-inline'; connect-src 'none'; base-uri 'none'; form-action 'none'"
    return ("<!doctype html><html lang='en'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<meta http-equiv='Content-Security-Policy' content=\""+html.escape(csp,quote=True)+"\"><title>Private media review</title>"
        "<style>body{font:16px system-ui;max-width:900px;margin:24px auto;padding:16px}section{border:1px solid #ccc;padding:12px;margin:12px 0}label{display:block;margin:8px 0}select,button{font:inherit;padding:8px}p{overflow-wrap:anywhere}</style>"
        "<h1>Private media quality review</h1><p>Open listed media in your local player. Review every observation. No automatic approval.</p>"
        "<div id='files'></div><main id='rows'></main><button id='export'>Export JSON</button><p id='status' role='status'></p>"
        "<script id='payload' type='application/json'>"+payload+"</script><script>"+JS+"</script></html>")


def create(root,pid,*,kind):
    folder=projects.project(root,pid)
    with projects.exclusive(folder):
        if kind=="audio":
            _,dest,timeline,sha=audio._context(root,pid)
            if audio._read(dest,timeline,sha) is not None:raise ValueError("Review already recorded")
            value={"schema":1,"master_sha256":sha,"turns":{r["turn_id"]:"UNREVIEWED" for r in timeline["rows"]},
                   "criteria":{k:"UNREVIEWED" for k in audio.CRITERIA}}
            files=[str(dest/v4_master.FOLDER/v4_master.WAV)];fields=["turns","criteria"]
        elif kind=="pilot":
            _,dest,binding,rows,targets=neural._context(root,pid);done=neural._scan(dest,binding,rows)
            if neural._review(dest,binding,targets,done) is not None:raise ValueError("Review already recorded")
            bound=neural._pilot_binding(binding,targets,done)
            if any(done[k]["test_fixture_only"] for k in targets):raise ValueError("Synthetic pilot cannot be reviewed as production")
            value={"schema":1,"binding":bound,"observations":{k:{c:"UNREVIEWED" for c in neural.CRITERIA} for k in targets}}
            files=[str(dest/neural.FOLDER/k/"face.mp4") for k in targets];fields=["observations"]
        elif kind=="final":
            _,dest,receipt,turns=final._context(root,pid)
            if final._read(dest,receipt,turns) is not None:raise ValueError("Review already recorded")
            value={"schema":1,"candidate_sha256":source.json_digest(receipt),
                   "turns":{t["id"]:{c:"UNREVIEWED" for c in final.CRITERIA} for t in turns},
                   "criteria":{c:"UNREVIEWED" for c in final.GLOBAL}}
            files=[str(dest/v4_export.FOLDER/v4_export.VIDEO),str(dest/v4_export.FOLDER/v4_export.SRT)];fields=["turns","criteria"]
        else:raise ValueError("Choose audio, pilot or final")
        name="visual-"+kind+"-"+source.json_digest(value);path=folder/(name+".html")
        content=build(value,files,fields,name+".json").encode("utf-8")
        if len(content)>5_000_000:raise ValueError("Media review form too large")
        with path.open("xb") as handle:handle.write(content)
        return {"project_id":pid,"html_path":str(path),"media_paths":files,"review_kind":kind,"approval_recorded":False}
