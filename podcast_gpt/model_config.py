"""Private persistent selections of existing trusted local model paths.

Saving or reading selections never runs an interpreter or installs anything.
Actual inference retains its separate explicit consent and preflight.
"""
from pathlib import Path
from . import projects, source, kokoro

FILES={"kokoro":"kokoro-paths.json","sadtalker":"sadtalker-paths.json","espeak":"espeak-paths.json"}
KEYS={"kokoro":("model","voices"),"sadtalker":("model","python"),"espeak":("executable",)}


def _path(value,*,directory=False):
    p=Path(value).expanduser().absolute()
    for parent in reversed(p.parents):projects._plain(parent)
    projects._plain(p,directory=directory)
    return p


def _validate(engine,paths):
    if engine not in KEYS or set(paths)!=set(KEYS[engine]):raise ValueError("Select complete model path configuration")
    values={key:str(_path(value,directory=engine=="sadtalker" and key=="model")) for key,value in paths.items()}
    if engine=="kokoro":kokoro._check_assets(Path(values["model"]),Path(values["voices"]))
    elif engine=="sadtalker":
        model=Path(values["model"])
        projects._plain(model/"inference.py",directory=False)
        projects._plain(model/"src");projects._plain(model/"src"/"config");projects._plain(model/"checkpoints")
    return values


def save(root,engine,paths,*,replace=False):
    values=_validate(engine,paths)
    folder=projects.base(root,create=True)
    with projects.exclusive(folder):
        path=folder/FILES[engine]
        projects._plain(path,directory=False,missing=True)
        if path.exists() and not replace:raise ValueError("Model configuration exists; explicit --replace required")
        source.atomic_json(path,{"schema":1,"engine":engine,"paths":values,"paths_sha256":source.json_digest(values)},new=not replace)
    return {"engine":engine,"configured":True,"model_load_verified":False,"downloads":0}


def read(root,engine):
    if engine not in FILES:raise ValueError("Unknown local engine")
    folder=projects.base(root);path=folder/FILES[engine]
    projects._plain(path,directory=False)
    saved=source.read_json(path,32000)
    if set(saved)!={"schema","engine","paths","paths_sha256"} or saved["schema"]!=1 or saved["engine"]!=engine:
        raise ValueError("Invalid model configuration")
    paths=saved["paths"]
    if not isinstance(paths,dict) or source.json_digest(paths)!=saved["paths_sha256"] or _validate(engine,paths)!=paths:
        raise ValueError("Model configuration path binding differs")
    return {k:Path(v) for k,v in paths.items()}


def resolve(root,engine,paths,*,use_config=False):
    if use_config:
        if any(v is not None for v in paths.values()):raise ValueError("Choose saved configuration or explicit paths, not both")
        return read(root,engine)
    if any(v is None for v in paths.values()):raise ValueError("Select explicit model paths or --use-config")
    return paths


def status(root):
    folder=projects.base(root)
    engines={}
    for engine,name in FILES.items():
        path=folder/name
        if not path.exists() and not path.is_symlink():engines[engine]="not_configured";continue
        try:read(root,engine);engines[engine]="paths_checked"
        except (OSError,ValueError,TypeError,KeyError):engines[engine]="blocked"
    return {"engines":engines,"model_load_verified":False,"interpreter_executions":0,"downloads":0}
