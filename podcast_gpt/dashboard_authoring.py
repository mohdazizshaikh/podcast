"""Explicit local browser authoring; no arbitrary source paths or inference."""
import json
import re
import tempfile
from pathlib import Path
from . import projects, characters, portrait_brief, ingestion, model_config, research, research_discovery, dashboard_inference, dashboard_review, manual_script, continuity, studio_preview, v4_audio, dashboard_cloud, voice_preflight, device_acceptance, audio_diagnostics, research_coverage, portrait_local, dashboard_portrait, japanese_resources, video_audio_check

JSON_LIMIT=32768
READ_ONLY=("character-list","character-show","cast-status","cast-choices","model-status","research-status","continuity-status","studio-status","voice-preflight","device-acceptance","turn-diagnostics","research-coverage","portrait-brief","portrait-preflight","portrait-candidate","japanese-resources","portrait-candidates","video-audio-check")
ACTIONS=("character-list","character-show","character-create","cast-assign","cast-status","cast-choices",
         "source-url","model-configure","model-status","research-status","research-discover","research-capture","local-inference","review-template","manual-script","continuity-enable","continuity-status","studio-configure","studio-status","cloud-draft","voice-preflight","device-acceptance","turn-diagnostics","research-coverage","portrait-brief","portrait-preflight","portrait-candidate","portrait-generate","portrait-candidate-attach","japanese-resources","portrait-candidates","video-audio-check")
UPLOADS={"portrait":characters.MAX_PORTRAIT,"source":ingestion.MAX_FILE,"audio-turn":v4_audio.MAX_WAV,"studio-background":characters.MAX_PORTRAIT}
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


def run(root,action,data,*,acknowledgment=None,progress=None,should_stop=None):
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
    if action=="video-audio-check":
        _keys(data,("project_id","kind"))
        return video_audio_check.inspect(root,data["project_id"],data["kind"])
    if action=="japanese-resources":
        _keys(data,())
        return japanese_resources.inspect()
    if action=="portrait-preflight":
        _keys(data,("character_id","model"))
        return portrait_local.inspect(root,data["character_id"],_local_path(data["model"]))
    if action=="portrait-candidates":
        _keys(data,())
        return portrait_local.list_candidates(root)
    if action=="portrait-candidate":
        _keys(data,("candidate_id",))
        return portrait_local.audit_candidate(root,data["candidate_id"])
    if action=="portrait-brief":
        _keys(data,("character_id",))
        return portrait_brief.create(root,data["character_id"])
    if action=="research-coverage":
        _keys(data,("project_id",))
        return research_coverage.inspect(root,data["project_id"])
    if action=="research-status":
        _keys(data,("project_id",))
        return research.inspect(root,data["project_id"])
    if action in ("continuity-status","studio-status"):
        _keys(data,("project_id",))
        return continuity.inspect(root,data["project_id"]) if action=="continuity-status" else studio_preview.inspect_settings(root,data["project_id"])
    if action in ("voice-preflight","device-acceptance","turn-diagnostics"):
        _keys(data,("project_id",))
        pid=data["project_id"]
        if action=="voice-preflight":return voice_preflight.inspect(root,pid)
        if action=="device-acceptance":return device_acceptance.inspect(root,pid)
        return audio_diagnostics.inspect(root,pid,kind="master",per_turn=True)
    if acknowledgment!=ACK:raise ValueError("Explicit local authoring consent required")
    if action=="portrait-generate":
        _keys(data,("character_id","model","seed","steps","model_consent"))
        if data["model_consent"] is not True:raise ValueError("Explicit portrait model consent required")
        return dashboard_portrait.generate(root,data["character_id"],_local_path(data["model"]),data["seed"],data["steps"],acknowledgment=portrait_local.ACK)
    if action=="portrait-candidate-attach":
        _keys(data,("candidate_id","rights"))
        if data["rights"] is not True:raise ValueError("Explicit reviewed portrait rights required")
        return portrait_local.attach_candidate(root,data["candidate_id"],acknowledgment=characters.ACK)
    if action=="continuity-enable":
        _keys(data,("project_id","prior_project_id","turn_ids","local_only_consent"))
        if data["local_only_consent"] is not True:raise ValueError("Explicit local-only continuity consent required")
        return continuity.enable(root,data["project_id"],data["prior_project_id"],data["turn_ids"],acknowledgment=continuity.ACK)
    if action=="studio-configure":
        if isinstance(data,dict) and set(data)=={"project_id","layout"}:data={**data,"camera":"fixed"}
        _keys(data,("project_id","layout","camera"))
        return studio_preview.configure(root,data["project_id"],layout=data["layout"],camera=data["camera"])
    if action=="cloud-draft":
        _keys(data,("project_id","cloud_consent","confirm_gemini_free_project"))
        if data["cloud_consent"] is not True:raise ValueError("Explicit cloud text consent required")
        return dashboard_cloud.run(root,data["project_id"],acknowledgment=dashboard_cloud.ACK,confirm_gemini_free_project=data["confirm_gemini_free_project"])
    if action=="local-inference":
        _keys(data,("project_id","engine","max_steps","model_consent"))
        if data["model_consent"] is not True:raise ValueError("Explicit model execution consent required")
        return dashboard_inference.run(root,data["project_id"],engine=data["engine"],max_steps=data["max_steps"],
            acknowledgment=dashboard_inference.ACK,progress=progress,should_stop=should_stop)
    if action=="review-template":
        _keys(data,("project_id","kind"))
        return dashboard_review.template(root,data["project_id"],data["kind"])
    if action=="manual-script":
        _keys(data,("project_id",))
        return manual_script.import_saved(root,data["project_id"],acknowledgment=manual_script.ACK)
    if action=="research-discover":
        if isinstance(data,dict) and set(data)=={"project_id","query","allow_web_search"}:data={**data,"edition":"en"}
        _keys(data,("project_id","query","allow_web_search","edition"))
        return research_discovery.discover(root,data["project_id"],query=data["query"],edition=data["edition"],allow_web_search=data["allow_web_search"])
    if action=="research-capture":
        _keys(data,("project_id","urls","allow_web_fetch"))
        urls=data["urls"]
        if not isinstance(urls,list) or any(not isinstance(u,str) or not 1<=len(u)<=2048 for u in urls):raise ValueError("Invalid research URLs")
        return research.capture(root,data["project_id"],urls,allow_web_fetch=data["allow_web_fetch"])
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


def upload(root,kind,identifier,name,raw,*,acknowledgment=None,rights=False,unit=None,layout=None,camera="fixed"):
    if kind not in UPLOADS or not 1<=len(raw)<=UPLOADS[kind]:raise ValueError("Invalid local upload kind or size")
    if acknowledgment!=ACK:raise ValueError("Explicit local authoring consent required")
    if not isinstance(name,str) or not 1<=len(name)<=160 or not re.fullmatch(r"[\w .()-]+",name) or name in (".",".."):
        raise ValueError("Use a simple source filename")
    suffix=Path(name).suffix.lower()
    if kind=="audio-turn":
        if rights is not True or suffix!=".wav" or not isinstance(unit,str) or not re.fullmatch(r"\d{4}",unit):raise ValueError("Authorized matching WAV and valid turn ID required")
        projects.project(root,identifier);v4_audio._pcm(raw)
    elif kind=="studio-background":
        if rights is not True or suffix!=".png" or layout not in studio_preview.LAYOUTS:raise ValueError("Authorized PNG and studio layout required")
        projects.project(root,identifier);characters._portrait_info(raw)
    elif kind=="portrait":
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
        path=Path(tmp)/("input"+suffix)
        with path.open("xb") as handle:handle.write(raw)
        if kind=="portrait":return portrait_brief.attach(root,identifier,portrait=path,acknowledgment=characters.ACK)
        if kind=="audio-turn":return v4_audio.import_turn(root,identifier,unit,path,acknowledgment=v4_audio.ACK)
        if kind=="studio-background":return studio_preview.configure(root,identifier,layout=layout,background=path,camera=camera,acknowledgment=studio_preview.ACK)
        # Preserve the existing evidence locator naming convention.
        source_path=Path(tmp)/("source"+suffix);path.rename(source_path)
        return projects.import_source(root,identifier,path=source_path)
