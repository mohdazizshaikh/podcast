"""Conservative archive of current incomplete outputs without completion receipt."""
import uuid
from . import projects, source, v4_audio as audio, v4_master as master
from . import v4_preview as preview, v4_neural as neural, v4_export as export
from . import v4_recovery as recovery, v4_post_audio as mix, v4_mixed_video as mixed
from . import studio_preview as studio, studio_neural as sn

ACK="I_STOPPED_ALL_PRODUCTION_PROCESSES_AND_AUTHORIZE_INCOMPLETE_OUTPUT_ARCHIVE"
KINDS=("audio-turn","master","static-preview","neural-clip","neural-export","post-audio","mixed-export","studio-preview","neural-studio")
ARCHIVE="incomplete-output-archive"


def _exists(path):
    return path.exists() or path.is_symlink()


def _refuse_dependencies(dest,names):
    if any(_exists(dest/n) for n in names):raise ValueError("Dependent artifacts exist; manual inspection required")


def _locate(root,pid,kind,unit):
    if kind not in KINDS:raise ValueError("Unknown recoverable output type")
    folder,dest,binding,turns,req,cast=audio._context(root,pid)
    if kind=="audio-turn":
        if unit not in {t["id"] for t in turns}:raise ValueError("Select current script turn ID")
        _refuse_dependencies(dest,(audio.TIMELINE,master.FOLDER,preview.FOLDER,studio.FOLDER,sn.FOLDER,sn.REVIEW,neural.FOLDER,export.FOLDER,mix.FOLDER,"audio-review.json","final-video-review.json"))
        path=dest/unit;allowed={"speech.wav"}
    elif kind=="master":
        if unit is not None:raise ValueError("Unit ID not required")
        master._context(root,pid)
        _refuse_dependencies(dest,(preview.FOLDER,studio.FOLDER,sn.FOLDER,sn.REVIEW,neural.FOLDER,export.FOLDER,mix.FOLDER,"audio-review.json","final-video-review.json"))
        path=dest/master.FOLDER;allowed={master.WAV}
    elif kind=="post-audio":
        if unit is not None:raise ValueError("Unit ID not required")
        mix._ctx(root,pid)
        _refuse_dependencies(dest,(mixed.FOLDER,mixed.MIX_REVIEW,mixed.VIDEO_REVIEW))
        path=dest/mix.FOLDER;allowed={mix.WAV,"intro.wav","bed.wav","outro.wav"}
    elif kind=="static-preview":
        if unit is not None:raise ValueError("Unit ID not required")
        preview._context(root,pid)
        path=dest/preview.FOLDER;allowed={preview.VIDEO,preview.SRT}
    elif kind=="studio-preview":
        if unit is not None:raise ValueError("Unit ID not required")
        studio._context(root,pid)
        path=dest/studio.FOLDER;allowed={studio.VIDEO,studio.SRT}
    elif kind=="neural-studio":
        if unit is not None:raise ValueError("Unit ID not required")
        sn._context(root,pid)
        _refuse_dependencies(dest,(sn.REVIEW,))
        path=dest/sn.FOLDER;allowed={sn.VIDEO,sn.SRT}
    elif kind=="neural-export":
        if unit is not None:raise ValueError("Unit ID not required")
        export._context(root,pid)
        _refuse_dependencies(dest,("final-video-review.json",mixed.FOLDER,mixed.VIDEO_REVIEW))
        path=dest/export.FOLDER;allowed={export.VIDEO,export.SRT}
    elif kind=="mixed-export":
        if unit is not None:raise ValueError("Unit ID not required")
        mixed._context(root,pid)
        _refuse_dependencies(dest,(mixed.VIDEO_REVIEW,))
        path=dest/mixed.FOLDER;allowed={mixed.VIDEO,mixed.SRT}
    else:
        _,_,nb,rows,targets=neural._context(root,pid)
        if unit not in {r["id"] for r in rows}:raise ValueError("Select current neural chunk ID")
        _refuse_dependencies(dest,(export.FOLDER,"final-video-review.json",sn.FOLDER,sn.REVIEW))
        if unit in targets and _exists(dest/neural.FOLDER/neural.REVIEW):
            raise ValueError("Reviewed pilot cannot be archived")
        projects._plain(dest/neural.FOLDER)
        path=dest/neural.FOLDER/unit;allowed={"face.mp4"}
    projects._plain(dest)
    projects._plain(path)
    names={p.name for p in path.iterdir()}
    if "receipt.json" in names:raise ValueError("Completion receipt exists; never archive automatically")
    if not names<=allowed:raise ValueError("Unexpected files; manual inspection required")
    for child in path.iterdir():projects._plain(child,directory=False)
    return folder,path,binding


def inspect(root,pid,kind,unit=None):
    folder=projects.project(root,pid)
    if _exists(folder/projects.LOCK):return {"project_id":pid,"eligible":False,"lock_present":True}
    _,path,binding=_locate(root,pid,kind,unit)
    return {"project_id":pid,"eligible":True,"kind":kind,"unit":unit,"relative_path":str(path.relative_to(folder)),
            "binding_sha256":source.json_digest(binding),"manual_process_check_required":True}


def archive(root,pid,kind,unit=None,*,acknowledgment):
    if acknowledgment!=ACK:raise ValueError("Explicit stopped-process archive acknowledgment required")
    folder=projects.project(root,pid)
    with projects.exclusive(folder):
        _,path,binding=_locate(root,pid,kind,unit)
        recovery._plain_tree(path)
        base=folder/ARCHIVE;projects._plain(base,missing=True);base.mkdir(exist_ok=True);projects._plain(base)
        target=base/uuid.uuid4().hex;target.mkdir()
        relative=str(path.relative_to(folder))
        path.rename(target/"attempt")
        source.atomic_json(target/"archive.json",{"schema":1,"kind":kind,"unit":unit,"relative_path":relative,
            "binding_sha256":source.json_digest(binding),"acknowledgment":ACK},new=True)
        return {"project_id":pid,"archived":True,"archive_path":str(target),"deleted_files":0,"retry_requires_explicit_run":True}
