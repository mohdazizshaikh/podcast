"""Windows launcher dependency stamp. No model downloads or private data access."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import sys
from pathlib import Path

from . import __version__


def dependency_fingerprint() -> dict:
    from PIL import Image, ImageFont
    # Verify the APIs needed by the application, not just package presence.
    Image.new("RGB", (1, 1))
    ImageFont.load_default(size=12)
    installed = importlib.metadata.version("podcast-gpt-reconstructed")
    if installed != __version__:
        raise ValueError("Installed application version differs from source")
    project = Path(__file__).resolve().parents[1] / "pyproject.toml"
    return {"schema": 1, "app_version": installed,
            "python": list(sys.version_info[:3]),
            "pillow": importlib.metadata.version("Pillow"),
            "project_sha256": hashlib.sha256(project.read_bytes()).hexdigest()}


def stamp_path() -> Path:
    return Path(sys.prefix) / ".podcast-app-dependencies.json"


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv not in (["check"], ["record"]):
        return 2
    try:
        if sys.prefix == sys.base_prefix:
            raise ValueError("Use the application virtual environment")
        expected = dependency_fingerprint()
        stamp = stamp_path()
        if argv == ["check"]:
            return 0 if json.loads(stamp.read_text(encoding="utf-8")) == expected else 1
        # A failed/interrupted write is only a cache miss next time.
        stamp.write_text(json.dumps(expected, sort_keys=True), encoding="utf-8")
        return 0
    except (OSError, ValueError, TypeError, ImportError, AttributeError) as err:
        print("Application dependency check: " + str(err), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
