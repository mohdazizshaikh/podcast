"""Read-only exact citation coverage, not semantic or factual verification."""
from urllib.parse import urlsplit
from . import projects,research,script_review,source


def inspect(root,pid):
    folder=projects.project(root,pid)
    req=projects.load(root,pid)
    pack=research.read_pack(folder,req)
    if pack is None:raise ValueError("Capture research sources before coverage inspection")
    current=script_review.current_script(root,pid)
    urls={r["id"]:r["evidence"]["locator"] for r in pack["sources"]}
    hosts={sid:urlsplit(url).hostname for sid,url in urls.items()}
    counts={sid:0 for sid in urls}
    rows=[]
    for turn in current["turns"]:
        citations=research.validate_citations(turn["citations"],pack)
        ids=sorted({c["source_id"] for c in citations})
        for sid in ids:counts[sid]+=1
        unique_hosts=sorted({hosts[sid] for sid in ids})
        rows.append({"turn_id":turn["id"],"speaker":turn["speaker"],"citation_count":len(citations),
                     "source_ids":ids,"distinct_host_count":len(unique_hosts),
                     "review_priority":"uncited" if not ids else "single_host" if len(unique_hosts)==1 else "multiple_hosts"})
    cited=sum(bool(row["source_ids"]) for row in rows)
    return {"project_id":pid,"script_version_sha256":current["version_sha256"],
            "research_sha256":source.json_digest(pack),"turn_count":len(rows),"cited_turn_count":cited,
            "uncited_turn_ids":[r["turn_id"] for r in rows if not r["source_ids"]],
            "multiple_host_turn_ids":[r["turn_id"] for r in rows if r["distinct_host_count"]>1],
            "source_usage":[{"source_id":sid,"url":urls[sid],"host":hosts[sid],"cited_turn_count":counts[sid]} for sid in urls],
            "turns":rows,"exact_excerpt_checks_passed":True,"independent_corroboration_verified":False,
            "semantic_claim_verification_performed":False,"publication_approved":False}
