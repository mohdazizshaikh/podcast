"""Archive only a stopped, current, uncompleted neural scratch attempt."""
import os
import uuid
from . import projects, source, v4_neural as neural

ACK="I_STOPPED_ALL_MODEL_PROCESSES_AND_WANT_TO_ARCHIVE_THIS_ATTEMPT"
SCRATCH="neural-scratch"
ARCHIVE="neural-attempt-archive"


def _candidates(folder,binding,rows,done):
    base=folder/SCRATCH;projects._plain(base,missing=True)
    if not base.exists():return []
    prefix=source.json_digest(binding)+"-"
    candidates=[]
    for row in rows:
        if row["id"] in done:continue
        path=base/(prefix+row["id"])
        if path.exists() or path.is_symlink():
            projects._plain(path)
            candidates.append(row["id"])
    return candidates


def inspect(root,pid):
    folder=projects.project(root,pid)
    lock=folder/projects.LOCK
    if lock.exists() or lock.is_symlink():
        return {"project_id":pid,"lock_present":True,"archive_eligible_ids":[],"manual_process_check_required":True}
    _,dest,binding,rows,targets=neural._context(root,pid)
    done=neural._scan(dest,binding,rows)
    return {"project_id":pid,"lock_present":False,"archive_eligible_ids":_candidates(folder,binding,rows,done),
            "manual_process_check_required":True,"completed_clips_preserved":True}


def _plain_tree(path):
    projects._plain(path)
    def fail(error):raise error
    count=0
    for current,dirs,files in os.walk(path,followlinks=False,onerror=fail):
        from pathlib import Path
        p=Path(current);projects._plain(p)
        for name in dirs:projects._plain(p/name)
        for name in files:projects._plain(p/name,directory=False)
        count+=len(dirs)+len(files)
        if count>100000:raise ValueError("Unexpectedly large scratch inventory; inspect manually")


def archive(root,pid,chunk_id,*,acknowledgment):
    if acknowledgment!=ACK:raise ValueError("Explicit stopped-process archive acknowledgment required")
    folder=projects.project(root,pid)
    with projects.exclusive(folder):
        _,dest,binding,rows,targets=neural._context(root,pid)
        done=neural._scan(dest,binding,rows)
        if chunk_id not in _candidates(folder,binding,rows,done):
            raise ValueError("No eligible stopped current uncompleted neural scratch")
        attempt=folder/SCRATCH/(source.json_digest(binding)+"-"+chunk_id)
        _plain_tree(attempt)
        base=folder/ARCHIVE;projects._plain(base,missing=True);base.mkdir(exist_ok=True);projects._plain(base)
        target=base/uuid.uuid4().hex;target.mkdir()
        # Same-volume rename retains the original bytes; no recursive deletion.
        attempt.rename(target/"attempt")
        source.atomic_json(target/"archive.json",{"schema":1,"binding_sha256":source.json_digest(binding),
            "chunk_id":chunk_id,"acknowledgment":ACK,"completed_clip_preserved":True},new=True)
        return {"project_id":pid,"chunk_id":chunk_id,"archive_path":str(target),
                "archived":True,"retry_requires_explicit_run":True,"deleted_files":0}
