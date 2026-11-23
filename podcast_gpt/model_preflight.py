"""Read-only sanity check for user-installed SadTalker CPU environment.

This cannot certify model licenses, real model load, face quality or speed.
It never imports torch, executes inference.py, downloads weights or opens a
user portrait. The only launched process reads the selected interpreter's
Python version with the standard library.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

EXPECTED_FLAGS=("--cpu","--source_image","--driven_audio","--result_dir","--preprocess")
CHECKPOINT_SUFFIXES=(".safetensors",".pth",".pt",".tar",".mat",".ckpt")


def inspect_sadtalker_installation(model_root:Path,python_executable:Path,*,runner=None)->dict:
    root=Path(model_root).expanduser()
    interpreter=Path(python_executable).expanduser()
    if root.is_symlink() or not root.is_dir():
        raise ValueError("SadTalker model root missing or unsafe symlink")
    inference=root/"inference.py"
    config=root/"src"/"config"
    ckpt=root/"checkpoints"
    if inference.is_symlink() or not inference.is_file() or not 100<=inference.stat().st_size<=2_000_000:
        raise ValueError("Existing SadTalker inference.py missing/unsafe/incomplete")
    if config.is_symlink() or not config.is_dir():
        raise ValueError("SadTalker src/config directory missing")
    if ckpt.is_symlink() or not ckpt.is_dir():
        raise ValueError("Existing SadTalker checkpoints directory missing")
    if not interpreter.is_file():
        raise ValueError("Selected SadTalker CPU Python interpreter does not exist")
    # Only inspect the script's argparse option spelling; never import it.
    source=inference.read_text(encoding="utf-8",errors="replace")
    missing=[flag for flag in EXPECTED_FLAGS if flag not in source]
    if missing:
        raise ValueError("Installed SadTalker inference.py has incompatible/missing CLI options: "+
                         ", ".join(missing))
    weights=[]
    for path in ckpt.rglob("*"):
        if path.is_symlink():
            raise ValueError("Checkpoint symlink refused; local files must be inspected manually")
        if path.is_file() and path.name.lower().endswith(CHECKPOINT_SUFFIXES):
            weights.append(path)
        if len(weights)>500:
            raise ValueError("Unexpectedly large checkpoint inventory; inspect manually")
    if not weights:
        raise ValueError("No existing pretrained model checkpoint files detected (no downloads performed)")
    if sum(path.stat().st_size for path in weights)<1_000_000:
        raise ValueError("SadTalker checkpoint files appear incomplete or empty")
    probe=runner or subprocess.run
    code="import json,sys; print(json.dumps({'major':sys.version_info.major,'minor':sys.version_info.minor,'executable':sys.executable}))"
    try:
        completed=probe([str(interpreter),"-c",code],
                        cwd=str(root),capture_output=True,text=True,
                        encoding="utf-8",errors="replace",timeout=25,check=False)
    except (OSError,subprocess.TimeoutExpired) as err:
        raise ValueError("Selected local SadTalker interpreter failed read-only Python version check") from err
    if completed.returncode!=0:
        raise ValueError("Selected local SadTalker interpreter failed before model loading")
    try:
        version=json.loads(completed.stdout.strip())
    except (ValueError,TypeError,AttributeError) as err:
        raise ValueError("SadTalker interpreter did not return an interpretable Python version") from err
    major=version.get("major")
    minor=version.get("minor")
    if (type(major) is not int or type(minor) is not int
            or major!=3 or not 8<=minor<=13):
        raise ValueError("Selected SadTalker Python is not a supported Python 3 interpreter")
    return {
        "status":"read_only_sadtalker_cpu_installation_structure_checked_not_inference_verified",
        "python_version":f"{major}.{minor}",
        "checkpoint_files_detected":len(weights),
        "inference_cli_flags_present":list(EXPECTED_FLAGS),
        "checkpoint_file_contents_authenticated":False,
        "model_can_actually_load_verified":False,
        "model_license_or_portrait_rights_verified":False,
        "real_hindi_lipsync_quality_verified":False,
        "new_model_inference_calls":0,
        "internet_downloads":0,
        "next_action":"Only after reviewing licenses/rights and supplying real signed originals, use separate explicit YES consent for PILOT"
    }
