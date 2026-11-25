"""One bounded local mix request; no arbitrary input paths."""
import base64
import binascii
import json
import tempfile
from pathlib import Path
from . import projects,v4_post_audio as mix,v4_audio as audio,loudness_gain

LIMIT=8_500_000
ACK="I_AUTHORIZE_LOCAL_MIX_AND_HAVE_RIGHTS_TO_ALL_ADDED_AUDIO"


def parse(raw):
    if not 1<=len(raw)<=LIMIT:raise ValueError("Invalid bounded mix request size")
    try:data=json.loads(raw.decode("utf-8"))
    except (ValueError,UnicodeError,RecursionError):raise ValueError("Invalid mix JSON") from None
    if not isinstance(data,dict):raise ValueError("Expected mix JSON object")
    return data


def run(root,data,*,acknowledgment):
    keys={"project_id","assets","speech_peak","bed_peak","duck_percent","target_lufs","compress_ratio","compress_threshold","rights"}
    if acknowledgment!=ACK:raise ValueError("Explicit local mix consent required")
    if isinstance(data,dict) and set(data)==keys:data={**data,"remove_dc":False,"gate_threshold":0}
    keys|={"remove_dc","gate_threshold"}
    if isinstance(data,dict) and set(data)==keys:data={**data,"limiter_ceiling":0}
    keys|={"limiter_ceiling"}
    if not isinstance(data,dict) or set(data)!=keys or data["rights"] is not True:
        raise ValueError("Exact mix settings and audio rights required")
    pid=data["project_id"];projects.project(root,pid)
    mix._settings(data["speech_peak"],data["bed_peak"],data["duck_percent"],data["compress_ratio"],data["compress_threshold"],data["remove_dc"],data["gate_threshold"],data["limiter_ceiling"])
    if data["target_lufs"] is not None:loudness_gain.target(data["target_lufs"])
    assets=data["assets"]
    if not isinstance(assets,dict) or not set(assets)<=set(mix.ROLES):raise ValueError("Unknown mix asset role")
    if data["duck_percent"] and "bed" not in assets:raise ValueError("Ducking requires a background bed")
    with tempfile.TemporaryDirectory(prefix="dashboard-mix-",dir=projects.base(root)) as tmp:
        paths={}
        for role,encoded in assets.items():
            if not isinstance(encoded,str) or not 1<=len(encoded)<=4*((audio.MAX_WAV+2)//3):
                raise ValueError("Invalid encoded audio size")
            try:raw=base64.b64decode(encoded,validate=True)
            except (ValueError,binascii.Error):raise ValueError("Invalid base64 audio") from None
            info=audio._pcm(raw)
            if info["frames"]>mix.LIMITS[role]*audio.RATE:raise ValueError("Added audio exceeds role duration limit")
            path=Path(tmp)/(role+".wav")
            with path.open("xb") as h:h.write(raw)
            paths[role]=path
        return mix.compose(root,pid,**paths,speech_peak=data["speech_peak"],bed_peak=data["bed_peak"],
            duck_percent=data["duck_percent"],target_lufs=data["target_lufs"],compress_ratio=data["compress_ratio"],
            compress_threshold=data["compress_threshold"],remove_dc=data["remove_dc"],gate_threshold=data["gate_threshold"],limiter_ceiling=data["limiter_ceiling"],acknowledgment=mix.ACK)
