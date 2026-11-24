"""V4 milestone 1: unified, local, read-only setup and model inventory.

No downloaded weights, package installation, persisted model paths, inference,
or workspace creation. An explicit local interpreter probe is opt-in only.
"""
from __future__ import annotations

import importlib.metadata
import shutil
import sys
from pathlib import Path

from . import hardware, source, kokoro_preflight, model_preflight

GIB=1024**3
APP_PACKAGES=("Pillow","kokoro-onnx","misaki","onnxruntime","espeakng-loader")
GUIDES={"app":"docs/SETUP_WINDOWS.md","voice":"docs/KOKORO_OFFLINE.md",
        "face":"docs/SADTALKER_CPU_SETUP.md"}


def _package_versions():
    out={}
    for name in APP_PACKAGES:
        try:out[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:out[name]=None
    return out


def _model_paths(path):
    return Path(path).expanduser().absolute() if path is not None else None


def inspect(root:Path,*,kokoro_model:Path|None=None,kokoro_voices:Path|None=None,
            sadtalker_root:Path|None=None,sadtalker_python:Path|None=None,
            probe_interpreter:bool=False)->dict:
    hw=hardware.report()
    packages=_package_versions()
    tools={name:bool(shutil.which(name)) for name in ("ffmpeg","ffprobe","git","espeak-ng")}
    app_ok=sys.version_info>=(3,10) and bool(packages["Pillow"]) and tools["ffmpeg"] and tools["ffprobe"]
    workspace={"status":"blocked","free_gib":None}
    try:
        private=source.workspace_path(root)
        parent=private
        while not parent.exists() and parent!=parent.parent:parent=parent.parent
        if not parent.is_dir():raise ValueError("Workspace parent is not a directory")
        free=shutil.disk_usage(parent).free
        workspace={"status":"existing" if private.is_dir() else "not_created",
                   "free_gib":round(free/GIB,2),"source_disk_gate":free>=3*GIB,
                   "neural_disk_gate":free>=6*GIB}
    except (OSError,ValueError) as exc:workspace["reason"]=str(exc)
    model,voices=map(_model_paths,(kokoro_model,kokoro_voices))
    voice={"status":"not_configured","guide":GUIDES["voice"]}
    if model is not None or voices is not None:
        if model is None or voices is None:voice["status"]="incomplete_selection"
        else:
            try:
                result=kokoro_preflight.inspect(model,voices)
                voice.update(status="inventory_checked" if result["required_python_packages_present"] and result["ffmpeg_tools_present"] else "dependencies_missing",inventory=result)
            except (ValueError,OSError,RuntimeError,ImportError) as exc:voice.update(status="blocked",reason=str(exc))
    face_root,face_python=map(_model_paths,(sadtalker_root,sadtalker_python))
    face={"status":"not_configured","guide":GUIDES["face"]}
    if face_root is not None:
        if face_python is None:
            candidate=face_root/".venv38"/("Scripts/python.exe" if sys.platform=="win32" else "bin/python")
            if candidate.is_file():face_python=candidate
        if not face_root.is_dir() or face_python is None or not face_python.is_file():
            face["status"]="incomplete_selection"
        elif probe_interpreter is not True:
            face["status"]="interpreter_probe_consent_required"
        else:
            try:
                result=model_preflight.inspect_sadtalker_installation(face_root,face_python)
                face.update(status="inventory_checked",inventory=result)
            except (ValueError,OSError,RuntimeError,ImportError) as exc:face.update(status="blocked",reason=str(exc))
    elif face_python is not None:face["status"]="incomplete_selection"
    steps=[]
    if not app_ok:steps.append("Install missing Python/Pillow/FFmpeg prerequisites; see "+GUIDES["app"])
    if workspace["status"]=="blocked" or not workspace.get("neural_disk_gate"):
        steps.append("Choose a private workspace outside Git with at least 6 GiB free for CPU previews")
    if hw["low_available_ram_warning"]:steps.append("Low available RAM: close other applications before a model pilot")
    if voice["status"]!="inventory_checked":steps.append("Configure Kokoro or import 45 authorized WAVs; see "+GUIDES["voice"])
    if face["status"]!="inventory_checked":steps.append("Configure trusted local SadTalker and explicitly probe its interpreter; see "+GUIDES["face"])
    steps.append("After actual model setup, prepare source and run a separately consented pilot; no quality guarantee")
    return {"status":"v4_setup_inventory_only","python_version":".".join(map(str,sys.version_info[:3])),
            "hardware":hw,"packages":packages,"tools":tools,"application_prerequisites_present":app_ok,
            "workspace":workspace,"voice_engine":voice,"face_engine":face,"next_steps":steps,
            "model_load_verified":False,"hardware_model_compatibility_verified":False,
            "new_model_inference_calls":0,"downloads":0,"publication_approved":False}


def interactive(root:Path)->dict:
    """Paths read by Python, not interpolated into shell commands."""
    from .cli import _print_json
    print("Podcast GPT V4 — guided local setup inventory (no model installs or downloads)")
    _print_json(inspect(root))
    def ask(label):
        value=input(label+" (Enter to skip): ").strip().strip('"')
        return Path(value) if value else None
    model=ask("Existing Kokoro ONNX file")
    voices=ask("Existing Kokoro voices BIN file") if model else None
    face=ask("Existing trusted SadTalker directory")
    python=ask("Existing SadTalker Python executable (default .venv38)") if face else None
    consent=False
    if face:
        print("The interpreter probe executes the selected local Python with isolated standard-library flags.")
        print("Only continue for a trusted interpreter. No inference.py or model will be loaded.")
        consent=input("Type PROBE to authorize the interpreter version check: ").strip()=="PROBE"
    return inspect(root,kokoro_model=model,kokoro_voices=voices,sadtalker_root=face,
                   sadtalker_python=python,probe_interpreter=consent)
