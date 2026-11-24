"""Conservative recovery of abandoned model scratch only.

Never adopts failed outputs, removes locks, edits signed source, or changes
verified previews. Explicit consent and a separately acquired CPU lock are
required for moving one abandoned attempt to a unique private archive.
"""
from __future__ import annotations

import os
import stat
import uuid
from pathlib import Path

from . import neural, source
from .media import EXPORT_LOCK

ACK = "ARCHIVE_STOPPED_ATTEMPT"


def _plain_directory(path: Path) -> bool:
    # Refuse symlinks and Windows reparse points (including junctions).
    if not path.is_dir() or path.is_symlink():
        return False
    attrs = getattr(path.lstat(), "st_file_attributes", 0)
    return not bool(attrs & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


def _present(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def _assert_tree_safe(folder: Path) -> None:
    for directory, dirs, files in os.walk(folder, followlinks=False):
        for name in dirs + files:
            path = Path(directory) / name
            info = path.lstat()
            if (path.is_symlink() or
                getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
                or not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode))):
                raise ValueError("Unsafe link or special file in failed scratch; inspect manually")


def inspect(root: Path, *, allow_short: bool = False) -> dict:
    root = source.workspace_path(root)
    locks = [name for name in (source.ORIGINALS_LOCK, neural.LOCK, EXPORT_LOCK)
             if _present(root / "source" / name)]
    result = {"status": "read_only_interrupted_model_attempt_inventory",
              "active_or_orphan_locks": locks, "attempts": [],
              "new_model_inference_calls": 0, "files_changed": 0,
              "publication_approved": False}
    if locks:
        result["next_action"] = "STOP: verify active processes or orphan locks manually; no lock is removed"
        return result
    manifest, verified = neural.verified_previews(root, allow_short=allow_short)
    scratch = root / "scratch"
    if not _plain_directory(scratch):
        raise ValueError("Unsafe or missing private scratch directory")
    known = {row["id"] for row in manifest["chunks"]}
    for path in sorted(scratch.glob("model-*")):
        cid = path.name[len("model-"):]
        safe = cid in known and _plain_directory(path) and cid not in verified
        if safe:
            try:
                _assert_tree_safe(path)
            except ValueError:
                safe = False
        result["attempts"].append({"chunk_id": cid,
                                   "eligible_for_explicit_archive": safe})
    result["next_action"] = "Inspect private logs and stop all child model processes before any explicit archive"
    return result


def archive(root: Path, chunk_id: str, *, acknowledgment: str,
            allow_short: bool = False) -> dict:
    if acknowledgment != ACK:
        raise ValueError("Explicit ARCHIVE_STOPPED_ATTEMPT acknowledgment required")
    if not isinstance(chunk_id, str) or not source.CHUNK_RE.fullmatch(chunk_id):
        raise ValueError("Invalid signed chunk ID")
    root = source.workspace_path(root)
    with neural.cpu_session_lock(root):
        for name in (source.ORIGINALS_LOCK, EXPORT_LOCK):
            if _present(root / "source" / name):
                raise ValueError("Another original or export lock exists; inspect manually")
        manifest, verified = neural.verified_previews(root, allow_short=allow_short)
        if chunk_id not in {row["id"] for row in manifest["chunks"]}:
            raise ValueError("Chunk is not in the signed source")
        if chunk_id in verified:
            raise ValueError("Verified preview cannot be archived by failed attempt recovery")
        scratch = root / "scratch"
        attempt = scratch / ("model-" + chunk_id)
        if not _plain_directory(scratch) or not _plain_directory(attempt):
            raise ValueError("Missing or unsafe failed attempt directory")
        _assert_tree_safe(attempt)
        archive_dir = scratch / "failed-attempts"
        if not _present(archive_dir):
            archive_dir.mkdir()
        if not _plain_directory(archive_dir):
            raise ValueError("Unsafe private archive directory")
        # Unique directory and same-volume rename preserve the entire attempt,
        # including stdout/stderr and any untrusted incomplete model output.
        destination_parent = archive_dir / uuid.uuid4().hex
        destination_parent.mkdir()
        destination = destination_parent / attempt.name
        attempt.rename(destination)
        return {"status": "failed_attempt_archived_not_adopted",
                "chunk_id": chunk_id, "private_archive": str(destination),
                "verified_preview_count_preserved": len(verified),
                "new_model_inference_calls": 0, "publication_approved": False,
                "next_action": "After fixing the model error, explicitly consent to a new PILOT/BATCH/SESSION"}
