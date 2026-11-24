"""Explicit private 45-turn observations, not automatic quality certification."""
from __future__ import annotations

from pathlib import Path
from . import neural, source

ACK = "I_REVIEWED_ALL_45_ORIGINAL_HINDI_TURNS"
RECORD = "full-45-turn-human-observations.json"
TEMPLATE = "full-45-turn-review-template.json"
STATUS = "private_self_attested_45_turn_review_not_publication_approval"
TURN_IDS = tuple(f"{i:03}" for i in range(1,46))
CRITERIA = ("lip_sync","voice","identity","captions","transitions")


def _folder(root: Path) -> Path:
    folder = root / "review"
    if not folder.is_dir() or folder.is_symlink():
        raise ValueError("Missing or unsafe private review folder")
    return folder


def _binding(root: Path, allow_short: bool) -> dict:
    audit = neural.audit_neural(root, allow_short=allow_short)
    return audit["candidate_binding"]


def template(root: Path, *, allow_short: bool = False) -> dict:
    root = source.workspace_path(root)
    folder = _folder(root)
    binding = _binding(root, allow_short)
    target = folder / TEMPLATE
    source.atomic_json(target, {"schema":1,"candidate_binding":binding,
        "decisions":{tid:{key:"UNREVIEWED" for key in CRITERIA} for tid in TURN_IDS},
        "rights_self_attested":"UNREVIEWED"}, new=True)
    return {"private_template":str(target),"turns":45,"criteria":list(CRITERIA),
            "publication_approved":False}


def _validate(data: dict, binding: dict) -> tuple[dict, str]:
    if type(data.get("schema")) is not int or data["schema"]!=1 or data.get("candidate_binding")!=binding:
        raise ValueError("Full review template/record is stale or mismatched to audited export hashes")
    decisions = data.get("decisions")
    if not isinstance(decisions,dict) or set(decisions)!=set(TURN_IDS):
        raise ValueError("Exactly 45 original turn decisions required")
    for row in decisions.values():
        if not isinstance(row,dict) or set(row)!=set(CRITERIA) or any(v not in ("PASS","FAIL") for v in row.values()):
            raise ValueError("Every turn requires explicit PASS/FAIL for all five criteria")
    rights = data.get("rights_self_attested")
    if rights not in ("PASS","FAIL"):
        raise ValueError("Explicit self-attested rights PASS/FAIL required")
    return decisions, rights


def _summary(decisions: dict, rights: str) -> dict:
    failed = [tid for tid in TURN_IDS if any(v=="FAIL" for v in decisions[tid].values())]
    return {"manual_turns_reviewed":45,"failed_turn_ids":failed,
            "rights_self_attested":rights,
            "all_manual_observations_pass":not failed and rights=="PASS",
            "human_quality_independently_verified":False,
            "publication_approved":False}


def record(root: Path, *, acknowledgment: str, allow_short: bool = False) -> dict:
    if acknowledgment != ACK:
        raise ValueError("Explicit full 45-turn review acknowledgment required")
    root = source.workspace_path(root)
    folder = _folder(root)
    dest = folder / RECORD
    if dest.exists() or dest.is_symlink():
        raise ValueError("Existing full review record cannot be overwritten")
    binding = _binding(root, allow_short)
    data = source.read_json(folder / TEMPLATE)
    decisions, rights = _validate(data,binding)
    summary = _summary(decisions,rights)
    source.atomic_json(dest,{"schema":1,"status":STATUS,"candidate_binding":binding,
                            "decisions":decisions,**summary},new=True)
    return {"private_record_written":True,**summary}


def inspect(root: Path, *, allow_short: bool = False) -> dict:
    root = source.workspace_path(root)
    folder = _folder(root)
    binding = _binding(root,allow_short)
    data = source.read_json(folder / RECORD)
    decisions, rights = _validate(data,binding)
    summary = _summary(decisions,rights)
    if data.get("status")!=STATUS or any(data.get(k)!=v for k,v in summary.items()) or data.get("publication_approved") is not False or data.get("human_quality_independently_verified") is not False:
        raise ValueError("Full review record summary/status differs from private observations")
    return {"status":"full_manual_observation_record_matches_current_export",**summary}
