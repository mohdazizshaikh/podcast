"""Private append-only historical observations, not live ETA."""
import datetime
import math
import re
import uuid
from . import projects, source

FOLDER="production-timings"
ACTIONS=("kokoro","espeak","neural_pilot","neural_batch")


def validate(d):
    if not isinstance(d,dict) or set(d)!={"schema","scope","action","unit","seconds","utc"} or d["schema"]!=1:
        raise ValueError("Invalid timing record")
    if not re.fullmatch(r"[a-f0-9]{64}",d["scope"]) or d["action"] not in ACTIONS or not re.fullmatch(r"[0-9]{4}(?:-[0-9]{2})?",d["unit"]):
        raise ValueError("Invalid timing scope or unit")
    if type(d["seconds"]) not in (int,float) or not math.isfinite(d["seconds"]) or not 0<=d["seconds"]<=86400:
        raise ValueError("Invalid elapsed time")
    return d


def record(root,pid,*,scope,action,unit,seconds):
    folder=projects.project(root,pid)
    data=validate({"schema":1,"scope":scope,"action":action,"unit":unit,"seconds":round(seconds,3),
                   "utc":datetime.datetime.now(datetime.timezone.utc).isoformat()})
    with projects.exclusive(folder):
        dest=folder/FOLDER;projects._plain(dest,missing=True);dest.mkdir(exist_ok=True);projects._plain(dest)
        source.atomic_json(dest/(uuid.uuid4().hex+".json"),{"observation":data,"sha256":source.json_digest(data)},new=True)


def inspect(root,pid):
    folder=projects.project(root,pid);dest=folder/FOLDER;projects._plain(dest,missing=True)
    records=[]
    if dest.exists():
        for p in sorted(dest.iterdir()):
            projects._plain(p,directory=False)
            if not re.fullmatch(r"[a-f0-9]{32}\.json",p.name) or len(records)>=10000:raise ValueError("Invalid timing inventory")
            row=source.read_json(p,16000)
            if set(row)!={"observation","sha256"} or source.json_digest(row["observation"])!=row["sha256"]:raise ValueError("Timing hash differs")
            records.append(validate(row["observation"]))
    groups={}
    for row in records:groups.setdefault((row["scope"],row["action"]),[]).append(row["seconds"])
    lock=folder/projects.LOCK
    return {"project_id":pid,"operation_lock_present":lock.exists() or lock.is_symlink(),
            "completed_observations":len(records),"groups":[{"scope":k[0],"action":k[1],"count":len(v),
            "mean_seconds":round(sum(v)/len(v),3),"min_seconds":min(v),"max_seconds":max(v)} for k,v in groups.items()],
            "recent_observations":sorted(records,key=lambda d:d["utc"])[-20:],"live_eta_available":False,"historical_only":True}
