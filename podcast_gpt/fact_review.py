"""Optional source-bound human factual review, not automatic truth certification."""
from . import projects, research, script_review, source

ACK="I_CHECKED_EACH_TURN_AND_ITS_CITED_SOURCE_CONTEXT"
DECISIONS=("SUPPORTED","NO_FACTUAL_CLAIM","NEEDS_CORRECTION")


def _context(root,pid):
    folder=projects.project(root,pid);req=projects.load(root,pid)
    pack=research.read_pack(folder,req)
    if pack is None:raise ValueError("Capture research sources before factual review")
    current=script_review.current_script(root,pid)
    bind={"script_version_sha256":current["version_sha256"],"research_sha256":source.json_digest(pack)}
    urls={r["id"]:r["evidence"]["locator"] for r in pack["sources"]}
    rows={}
    for t in current["turns"]:
        citations=research.validate_citations(t["citations"],pack)
        rows[t["id"]]={"speaker":t["speaker"],"text":t["text"],
            "citations":[{**c,"url":urls[c["source_id"]]} for c in citations],"decision":"UNREVIEWED","note":""}
    return folder,{"schema":1,"binding":bind,"turns":rows}


def _paths(folder,template):
    name="fact-review-"+source.json_digest(template["binding"])
    return folder/(name+"-template.json"),folder/(name+"-receipt.json")


def _validate(value,template):
    if not isinstance(value,dict) or set(value)!=set(template) or value["schema"]!=1 or value["binding"]!=template["binding"]:
        raise ValueError("Stale factual review binding")
    rows=value["turns"]
    if not isinstance(rows,dict) or set(rows)!=set(template["turns"]):raise ValueError("Review every turn")
    for tid,row in rows.items():
        expected=template["turns"][tid]
        if not isinstance(row,dict) or set(row)!=set(expected) or any(row[k]!=expected[k] for k in ("speaker","text","citations")):
            raise ValueError("Factual review turn or citation content changed")
        decision=row["decision"];note=row["note"]
        if decision not in DECISIONS or not isinstance(note,str) or not 10<=len(note.strip())<=1000:
            raise ValueError("Complete all decisions with a substantive 10–1000 character note")
        if decision=="SUPPORTED" and not row["citations"]:raise ValueError("SUPPORTED requires at least one saved source quotation")
    return value


def _read(path,template):
    if not path.exists() and not path.is_symlink():return None
    projects._plain(path,directory=False);record=source.read_json(path,8_000_000)
    if set(record)!={"observations","sha256","acknowledgment"} or record["acknowledgment"]!=ACK or record["sha256"]!=source.json_digest(record["observations"]):
        raise ValueError("Factual review receipt differs")
    return _validate(record["observations"],template)


def _summary(pid,template,record):
    failed=[k for k,r in record["turns"].items() if r["decision"]=="NEEDS_CORRECTION"] if record else []
    return {"project_id":pid,"binding":template["binding"],"review_status":"UNREVIEWED" if record is None else "NEEDS_CORRECTION" if failed else "PASS",
            "correction_turn_ids":failed,"human_factual_self_attestation":record is not None and not failed,
            "independent_fact_check_verified":False,"publication_approved":False,"mandatory_media_gate":False}


def inspect(root,pid):
    folder,template=_context(root,pid);_,receipt=_paths(folder,template)
    return _summary(pid,template,_read(receipt,template))


def create(root,pid):
    folder=projects.project(root,pid)
    with projects.exclusive(folder):
        _,template=_context(root,pid);path,receipt=_paths(folder,template)
        if _read(receipt,template) is not None:raise ValueError("Factual review already recorded")
        source.atomic_json(path,template,new=True)
        return {"project_id":pid,"template_path":str(path),"research_snapshot_path":str(folder/research.FILENAME),
                "review_status":"UNREVIEWED"}


def record(root,pid,*,acknowledgment):
    if acknowledgment!=ACK:raise ValueError("Explicit factual review acknowledgment required")
    folder=projects.project(root,pid)
    with projects.exclusive(folder):
        _,template=_context(root,pid);path,receipt=_paths(folder,template)
        if _read(receipt,template) is not None:raise ValueError("Immutable factual review already recorded")
        projects._plain(path,directory=False)
        value=_validate(source.read_json(path,8_000_000),template)
        source.atomic_json(receipt,{"observations":value,"sha256":source.json_digest(value),"acknowledgment":ACK},new=True)
        return _summary(pid,template,value)
