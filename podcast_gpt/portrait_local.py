"""Explicit CPU-only local Stable Diffusion portrait candidates.

Trusted local installations only. No automatic model downloads or cast mutation.
"""
import importlib.metadata
import math
import re
import os
import shutil
import time
import uuid
from pathlib import Path
from . import characters,projects,source,portrait_brief,hardware

ACK="I_TRUST_THIS_LOCAL_IMAGE_MODEL_AND_HAVE_USAGE_RIGHTS_AND_AUTHORIZE_CPU_INFERENCE"
FOLDER="portrait-candidates"
GIB=1024**3
SUFFIXES={".json",".txt",".safetensors",".model",".md",".gitattributes"}
PACKAGES=("torch","diffusers","transformers","safetensors","accelerate")


def _model(path):
    path=Path(path).expanduser().absolute()
    for parent in reversed((path,*path.parents)):projects._plain(parent)
    source.workspace_path(path)
    index=path/"model_index.json";projects._plain(index,directory=False)
    data=source.read_json(index,64000)
    if not isinstance(data,dict) or data.get("_class_name")!="StableDiffusionPipeline":
        raise ValueError("Use a trusted local StableDiffusionPipeline model directory")
    if data.get("safety_checker")!=["stable_diffusion","StableDiffusionSafetyChecker"]:
        raise ValueError("An enabled local Stable Diffusion safety checker is required")
    for name in ("unet","vae","text_encoder","safety_checker","scheduler","tokenizer","feature_extractor"):
        projects._plain(path/name)
    files={};total=0;entries=0
    for current,dirs,names in os.walk(path,followlinks=False):
        for name in dirs:
            entries+=1
            if entries>2048:raise ValueError("Model directory entry limit exceeded")
            projects._plain(Path(current)/name)
        for name in names:
            entries+=1
            if entries>2048:raise ValueError("Model directory entry limit exceeded")
            item=Path(current)/name;projects._plain(item,directory=False)
            if item.suffix.lower() not in SUFFIXES:raise ValueError("Only trusted local safetensors/config/tokenizer files are supported")
            total+=item.stat().st_size
            if total>16*GIB:raise ValueError("Local model exceeds 16 GiB inventory limit")
            files[item.relative_to(path).as_posix()]=source.digest(item)
    for component in ("unet","vae","text_encoder","safety_checker"):
        if not any(k.startswith(component+"/") and k.endswith(".safetensors") for k in files):
            raise ValueError("Missing safetensors weights: "+component)
    return path,{"model_sha256":source.json_digest(files),"file_count":len(files),"total_bytes":total}


def inspect(root,cid,model):
    profile=characters.read(root,cid)
    _,inventory=_model(model)
    packages={}
    for name in PACKAGES:
        try:packages[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:packages[name]=None
    _,available=hardware.memory_bytes()
    base=projects.base(root)
    return {"character_id":cid,"profile_sha256":profile["profile_sha256"],"model":inventory,
            "packages":packages,"packages_present":all(packages.values()),
            "available_ram_bytes":available,"conservative_ram_gate":available is not None and available>=8*GIB,
            "scratch_disk_gate":shutil.disk_usage(base).free>=2*GIB,
            "model_load_verified":False,"actual_image_quality_verified":False,"downloads":0}


def _render(model,brief,seed,steps):
    # The CLI is a dedicated foreground invocation. Offline flags are set before
    # imports, not an OS-level network sandbox. Use trusted packages offline.
    os.environ["HF_HUB_OFFLINE"]="1";os.environ["TRANSFORMERS_OFFLINE"]="1"
    os.environ["CUDA_VISIBLE_DEVICES"]=""
    try:
        import torch
        from diffusers import StableDiffusionPipeline
    except ImportError as exc:raise ValueError("Install trusted CPU torch and local Diffusers dependencies independently") from exc
    torch.set_num_threads(hardware.select_threads())
    pipeline=StableDiffusionPipeline.from_pretrained(str(model),local_files_only=True,use_safetensors=True,torch_dtype=torch.float32)
    pipeline=pipeline.to("cpu")
    if pipeline.safety_checker is None:raise ValueError("Local safety checker not loaded")
    pipeline.enable_attention_slicing()
    result=pipeline(brief["prompt"],negative_prompt=brief["negative_prompt"],height=512,width=512,
                    num_inference_steps=steps,guidance_scale=7.0,generator=torch.Generator(device="cpu").manual_seed(seed))
    if result.nsfw_content_detected!=[False] or len(result.images)!=1:raise ValueError("Portrait candidate blocked or safety result unavailable")
    return result.images[0]


def generate(root,cid,*,model,seed=42,steps=20,acknowledgment=None,renderer=None):
    if acknowledgment!=ACK:raise ValueError("Explicit local model trust, rights and inference consent required")
    if type(seed) is not int or not 0<=seed<=2**32-1 or type(steps) is not int or not 10<=steps<=30:
        raise ValueError("Seed must be 0–4294967295 and steps 10–30")
    report=inspect(root,cid,model)
    if not report["conservative_ram_gate"] or not report["scratch_disk_gate"]:raise ValueError("Portrait CPU pilot requires at least 8 GiB available RAM and 2 GiB scratch")
    if renderer is None and not report["packages_present"]:raise ValueError("Missing trusted local image runtime packages")
    model,inventory=_model(model)
    base=projects.base(root);dest=base/FOLDER
    with projects.exclusive(base):
        brief=portrait_brief.create(root,cid)
        if brief["profile_sha256"]!=report["profile_sha256"] or inventory!=report["model"]:raise ValueError("Profile or model changed before inference")
        projects._plain(dest,missing=True);dest.mkdir(exist_ok=True)
        attempt=dest/uuid.uuid4().hex;attempt.mkdir()
        start=time.monotonic()
        image=(renderer or _render)(model,brief,seed,steps)
        if image.size!=(512,512):raise ValueError("Unexpected portrait dimensions")
        path=attempt/"portrait.png"
        with path.open("xb") as handle:
            image.convert("RGB").save(handle,format="PNG");handle.flush();os.fsync(handle.fileno())
        info=characters._portrait_info(characters._read_file(path,characters.MAX_PORTRAIT))
        if _model(model)[1]!=inventory or portrait_brief.create(root,cid)!=brief:raise ValueError("Model or character changed during inference")
        receipt={"schema":1,"character_id":cid,"profile_sha256":brief["profile_sha256"],"brief_sha256":source.json_digest(brief),
                 "model":inventory,"portrait_sha256":info["sha256"],"seed":seed,"steps":steps,"dimensions":[512,512],
                 "elapsed_seconds":round(time.monotonic()-start,3),"test_fixture_only":renderer is not None,
                 "human_portrait_approved":False,"cast_changed":False,"publication_approved":False}
        source.atomic_json(attempt/"receipt.json",receipt,new=True)
        return {"candidate_id":attempt.name,"path":str(path),"receipt":receipt,"next_action":"Inspect the portrait yourself; use authorized portrait attach separately if suitable. No cast was modified."}


def audit_candidate(root,candidate_id):
    if not isinstance(candidate_id,str) or not projects.ID_RE.fullmatch(candidate_id):raise ValueError("Invalid portrait candidate ID")
    parent=projects.base(root)/FOLDER;projects._plain(parent)
    folder=parent/candidate_id;projects._plain(folder)
    if {p.name for p in folder.iterdir()}!={"receipt.json","portrait.png"}:raise ValueError("Incomplete or unexpected portrait candidate files")
    receipt=folder/"receipt.json";projects._plain(receipt,directory=False)
    value=source.read_json(receipt,32000)
    keys={"schema","character_id","profile_sha256","brief_sha256","model","portrait_sha256","seed","steps","dimensions","elapsed_seconds","test_fixture_only","human_portrait_approved","cast_changed","publication_approved"}
    if not isinstance(value,dict) or set(value)!=keys or value["schema"]!=1 or type(value["test_fixture_only"]) is not bool or any(value[k] is not False for k in ("human_portrait_approved","cast_changed","publication_approved")):
        raise ValueError("Invalid portrait candidate receipt")
    validate_provenance(value)
    brief=portrait_brief.create(root,value["character_id"])
    if brief["profile_sha256"]!=value["profile_sha256"] or source.json_digest(brief)!=value["brief_sha256"]:
        raise ValueError("Portrait character binding differs")
    path=folder/"portrait.png"
    info=characters._portrait_info(characters._read_file(path,characters.MAX_PORTRAIT))
    if info["sha256"]!=value["portrait_sha256"] or [info["width"],info["height"]]!=value["dimensions"] or value["dimensions"]!=[512,512]:
        raise ValueError("Portrait candidate integrity differs")
    return {"candidate_id":candidate_id,"path":str(path),"receipt":value,"candidate_integrity_checked":True}


def attach_candidate(root,candidate_id,*,acknowledgment):
    if acknowledgment!=characters.ACK:raise ValueError("Explicit portrait rights acknowledgment required")
    saved=audit_candidate(root,candidate_id)
    if saved["receipt"]["test_fixture_only"]:raise ValueError("Synthetic portrait candidate cannot use production attachment")
    return portrait_brief.attach(root,saved["receipt"]["character_id"],portrait=Path(saved["path"]),acknowledgment=acknowledgment)


def validate_provenance(value):
    def sha(v):return isinstance(v,str) and re.fullmatch("[0-9a-f]{64}",v) is not None
    if not all(sha(value[k]) for k in ("profile_sha256","brief_sha256","portrait_sha256")):
        raise ValueError("Invalid portrait provenance digest")
    if type(value["seed"]) is not int or not 0<=value["seed"]<2**32 or type(value["steps"]) is not int or not 10<=value["steps"]<=30:
        raise ValueError("Invalid portrait provenance options")
    elapsed=value["elapsed_seconds"]
    if type(elapsed) not in (int,float) or not 0<=elapsed<=10**9 or not math.isfinite(elapsed):
        raise ValueError("Invalid portrait provenance elapsed time")
    model=value["model"]
    if not isinstance(model,dict) or set(model)!={"model_sha256","file_count","total_bytes"} or not sha(model["model_sha256"]):
        raise ValueError("Invalid portrait model provenance")
    if type(model["file_count"]) is not int or not 5<=model["file_count"]<=2048 or type(model["total_bytes"]) is not int or not 1<=model["total_bytes"]<=16*GIB:
        raise ValueError("Invalid portrait model inventory")
    return value


def list_candidates(root,*,limit=50):
    if type(limit) is not int or not 1<=limit<=200:raise ValueError("List 1–200 portrait attempts")
    parent=projects.base(root)/FOLDER
    projects._plain(parent,missing=True)
    rows=[];truncated=False
    if parent.exists():
        # Bound the scan as well as the response; no recursive scratch traversal.
        from itertools import islice
        entries=list(islice(parent.iterdir(),1001))
        truncated=len(entries)>1000
        ids=sorted(p.name for p in entries[:1000] if projects.ID_RE.fullmatch(p.name))
        truncated=truncated or len(ids)>limit
        for cid in ids[:limit]:
            try:
                item=audit_candidate(root,cid)
                receipt=item["receipt"]
                rows.append({"candidate_id":cid,"character_id":receipt["character_id"],
                             "status":"fixture_only" if receipt["test_fixture_only"] else "candidate_integrity_checked",
                             "path":item["path"],"human_portrait_approved":False})
            except (ValueError,OSError,KeyError,TypeError,AttributeError):
                rows.append({"candidate_id":cid,"status":"incomplete_or_invalid"})
    return {"attempts":rows,"truncated":truncated,"automatic_attachment_performed":False}
