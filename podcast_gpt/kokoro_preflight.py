"""Read-only local Kokoro inventory; no model loads, imports or downloads."""
from __future__ import annotations

import importlib.metadata
import shutil
from pathlib import Path

from .hardware import report
from .kokoro import _check_assets, VOICE_MAP


def inspect(model: Path, voices: Path) -> dict:
    hashes = _check_assets(model, voices)
    packages = {}
    for name in ("kokoro-onnx", "misaki", "onnxruntime", "espeakng-loader"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    tools = {name: bool(shutil.which(name)) for name in ("ffmpeg","ffprobe","espeak-ng")}
    return {"status": "local_kokoro_assets_inventory_not_model_verified",
            **hashes, "packages": packages, "path_tools": tools,
            "required_python_packages_present": all(packages[n] for n in ("kokoro-onnx","misaki","onnxruntime")),
            "ffmpeg_tools_present": tools["ffmpeg"] and tools["ffprobe"],
            "requested_hindi_presets": dict(VOICE_MAP),
            "hardware": report(),
            "model_load_verified": False, "voice_pack_compatibility_verified": False,
            "espeak_library_load_verified": False, "human_voice_quality_verified": False,
            "new_model_inference_calls": 0, "internet_downloads": 0,
            "note": "eSpeak executable on PATH is informational; a bundled DLL may work even if absent. Real runtime and voice pack compatibility require a separately consented test."}
