"""Private standalone visual editor/review, no server or remote resources."""
import base64
import hashlib
import html
import json
from . import projects, script_review as review, source

JS=r"""
"use strict";
const model=JSON.parse(document.getElementById("payload").textContent);
const root=document.getElementById("rows");
const result=model.template;
function el(tag,text,parent){const node=document.createElement(tag);if(text!==null)node.textContent=text;parent.append(node);return node}
function choice(parent,label,callback){el("label",label,parent);const s=el("select",null,parent);for(const value of ["UNREVIEWED","PASS","FAIL"]){const o=el("option",value,s);o.value=value}s.addEventListener("change",()=>callback(s.value));return s}
for(const [i,t] of model.turns.entries()){
 const section=el("section",null,root);el("h2",t.id+" — "+t.speaker,section);
 if(model.mode==="edit"){
  el("label","Speaker",section);const who=el("input",null,section);who.value=t.speaker;who.maxLength=80;who.addEventListener("input",()=>result.turns[i].speaker=who.value);
  el("label","Dialogue",section);const speech=el("textarea",null,section);speech.value=t.text;speech.maxLength=600;speech.rows=4;speech.addEventListener("input",()=>result.turns[i].text=speech.value);
  el("label","Estimated seconds (2–30; unit total must remain 60)",section);const seconds=el("input",null,section);seconds.type="number";seconds.min=2;seconds.max=30;seconds.value=t.estimated_seconds;seconds.addEventListener("input",()=>result.turns[i].estimated_seconds=Number(seconds.value));
 }else{
  el("p",t.text,section);el("p","Estimated seconds: "+t.estimated_seconds,section);choice(section,"Turn decision",v=>result.observations.turn_decisions[t.id]=v);
 }
 if(t.citations)for(const c of t.citations)el("p","Source "+c.source_id+": "+c.quote,section);
}
if(model.mode==="review"){
 const section=el("section",null,root);el("h2","Global review criteria",section);
 for(const key of Object.keys(result.observations.criteria))choice(section,key.replaceAll("_"," "),v=>result.observations.criteria[key]=v);
}
document.getElementById("save").addEventListener("click",()=>{
 if(model.mode==="review"&&[...Object.values(result.observations.turn_decisions),...Object.values(result.observations.criteria)].includes("UNREVIEWED")){
  document.getElementById("status").textContent="Complete every decision before exporting.";return;
 }
 const url=URL.createObjectURL(new Blob([JSON.stringify(result,null,2)],{type:"application/json"}));
 const a=document.createElement("a");a.href=url;a.download=model.filename;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
 document.getElementById("status").textContent="JSON export requested. Use the explicit CLI import command to validate and save. No server changes have been made.";
});
"""


def build(current,*,mode):
    if mode not in ("edit","review"):raise ValueError("Choose edit or review")
    if mode=="review" and current["review_status"]!="UNREVIEWED":raise ValueError("Current version already has immutable review")
    if mode=="edit" and current["version"]>=review.MAX_REVISIONS:raise ValueError("Revision limit reached")
    base={"schema":1,"version":current["version"],"version_sha256":current["version_sha256"]}
    if mode=="edit":base["turns"]=current["turns"]
    else:base["observations"]={"turn_decisions":{t["id"]:"UNREVIEWED" for t in current["turns"]},
                              "criteria":{k:"UNREVIEWED" for k in review.CRITERIA}}
    filename=mode+"-r"+f"{current['version']:03}"+".json"
    payload=json.dumps({"mode":mode,"template":base,"turns":current["turns"],"filename":filename},ensure_ascii=True).replace("<",r"\u003c").replace(">",r"\u003e").replace("&",r"\u0026")
    # Escape script terminators and use a CSP hash for our fixed inline JS.
    digest=base64.b64encode(hashlib.sha256(JS.encode("utf-8")).digest()).decode("ascii")
    policy="default-src 'none'; script-src 'sha256-"+digest+"'; style-src 'unsafe-inline'; connect-src 'none'; form-action 'none'; base-uri 'none'; object-src 'none'"
    return ("<!doctype html><html lang='en'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<meta http-equiv='Content-Security-Policy' content=\""+html.escape(policy,quote=True)+"\">"
            "<title>Private Podcast Script</title><style>body{font:16px system-ui;max-width:850px;margin:24px auto;padding:16px;background:#fafafa;color:#20242b}section{background:white;border:1px solid #ddd;padding:16px;margin:12px 0;border-radius:8px}label{display:block;margin-top:12px}textarea,input,select{box-sizing:border-box;width:100%;font:inherit;padding:8px}h2{font-size:18px}button{font:inherit;padding:12px}p{white-space:pre-wrap;overflow-wrap:anywhere}</style>"
            "<h1>Private script "+mode+"</h1><p>Offline document. Export JSON and validate it using the CLI. No automatic approval or upload. Source citations and turn IDs remain fixed.</p>"
            "<main id='rows'></main><button id='save'>Export JSON</button><p id='status' role='status'></p>"
            "<script id='payload' type='application/json'>"+payload+"</script><script>"+JS+"</script></html>")


def create(root,pid,*,mode):
    folder=projects.project(root,pid)
    with projects.exclusive(folder):
        current=review.current_script(root,pid)
        name="visual-"+mode+"-"+current["version_sha256"]+".html"
        if mode not in ("edit","review"):raise ValueError("Choose edit or review")
        path=folder/name
        content=build(current,mode=mode).encode("utf-8")
        if len(content)>5_000_000:raise ValueError("Visual script exceeds bounded size")
        with path.open("xb") as handle:handle.write(content)
        return {"project_id":pid,"html_path":str(path),"mode":mode,"version_sha256":current["version_sha256"],
                "upload_required":False,"human_approval_recorded":False}
