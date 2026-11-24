"""Explicit local import of user-edited version-bound observations."""
import tempfile
from pathlib import Path
from . import projects,script_review,v4_audio_review,v4_neural,v4_final_review
from . import studio_neural,v4_mixed_video,fact_review

KINDS=("script-edit","script","audio","pilot","final","studio","mix","mixed","mixed-studio","fact")
LIMIT=8_000_000
ACK="I_AUTHORIZE_THIS_EXACT_REVIEW_OR_REVISION_IMPORT"
MIX_KINDS={"mix":"mix","mixed":"video","mixed-studio":"studio"}
ATTEST={"script":script_review.ACK,"audio":v4_audio_review.ACK,"pilot":v4_neural.REVIEW_ACK,
        "final":v4_final_review.ACK,"studio":studio_neural.ACK,"mix":v4_mixed_video.MIX_ACK,
        "mixed":v4_mixed_video.VIDEO_ACK,"mixed-studio":v4_mixed_video.STUDIO_ACK,"fact":fact_review.ACK}
RECORD={"script":script_review.record,"audio":v4_audio_review.record,
        "pilot":v4_neural.record,"final":v4_final_review.record,"fact":fact_review.record}


def template(root,pid,kind):
    if kind not in KINDS:raise ValueError("Unknown review kind")
    if kind in ("script-edit","script"):return script_review.template(root,pid,review=kind=="script")
    if kind=="studio":return studio_neural.qa(root,pid,"template")
    if kind in MIX_KINDS:return v4_mixed_video.qa(root,pid,MIX_KINDS[kind],"template")
    if kind=="fact":return fact_review.create(root,pid)
    return {"audio":v4_audio_review.template,"pilot":v4_neural.template,"final":v4_final_review.template}[kind](root,pid)


def upload(root,pid,kind,raw,*,acknowledgment,attestation=None):
    if acknowledgment!=ACK:raise ValueError("Explicit review import consent required")
    if kind not in KINDS or not 1<=len(raw)<=LIMIT:raise ValueError("Unknown review kind or invalid file size")
    if kind!="script-edit" and attestation!=ATTEST[kind]:raise ValueError("Explicit selected full review attestation required")
    if kind=="script-edit" and attestation is not None:raise ValueError("Script edit does not record an approval")
    projects.project(root,pid)
    with tempfile.TemporaryDirectory(prefix="dashboard-review-",dir=projects.base(root)) as tmp:
        path=Path(tmp)/"review.json"
        with path.open("xb") as handle:handle.write(raw)
        if kind=="script-edit":return script_review.revise(root,pid,input_file=path)
        if kind in RECORD:return RECORD[kind](root,pid,acknowledgment=ATTEST[kind],input_file=path)
        if kind=="studio":return studio_neural.qa(root,pid,"record",acknowledgment=ATTEST[kind],input_file=path)
        return v4_mixed_video.qa(root,pid,MIX_KINDS[kind],"record",acknowledgment=ATTEST[kind],input_file=path)
