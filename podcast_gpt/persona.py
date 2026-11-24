"""Opt-in, immutable cast personality context for new dialogue drafts."""
from . import characters, projects, source

FILE="script-persona.json"


def _profiles(root,pid):
    cast=characters.read_cast(root,pid)
    if cast is None:raise ValueError("Assign a cast before enabling character-aware dialogue")
    rows=[]
    for row in cast["cast"]:
        record=characters.read(root,row["character_id"])
        if source.json_digest(record)!=row["record_sha256"]:raise ValueError("Cast changed")
        profile=record["profile"]
        # Deliberately omit portraits, paths, appearance and voice configuration.
        rows.append({"speaker":row["speaker"],"personality":profile["personality"],"speaking_style":profile["speaking_style"]})
    return {"schema":1,"cast_sha256":cast["cast_sha256"],"profiles":rows}


def read(folder):
    path=folder/FILE
    if not path.exists() and not path.is_symlink():return None
    projects._plain(path,directory=False)
    saved=source.read_json(path,100000)
    if saved!=_profiles(folder.parent.parent,folder.name):raise ValueError("Script persona binding differs")
    return saved


def enable(root,pid):
    from . import script_generation as sg
    folder=projects.project(root,pid)
    with projects.exclusive(folder):
        if any((folder/name).exists() or (folder/name).is_symlink() for name in (sg.PARTS,sg.FINAL,FILE)):
            raise ValueError("Enable personality context before generating any script units; no overwrite")
        value=_profiles(root,pid)
        source.atomic_json(folder/FILE,value,new=True)
        return {"project_id":pid,"persona_enabled":True,"persona_sha256":source.json_digest(value),
                "speaker_count":len(value["profiles"]),"actual_personality_quality_verified":False}
