"""Synthetic audit boundary fixtures; never evidence of actual human QA."""
import json
import pytest
from podcast_gpt import final_review, neural, source


@pytest.fixture
def bound_review(private_studio,monkeypatch):
    binding={"source_sha256":"source","video_sha256":"video",
             "srt_sha256":"captions","chunks_sha256":"chunks","export_report_sha256":"report"}
    monkeypatch.setattr(neural,"audit_neural",lambda *a,**kw:{"candidate_binding":dict(binding)})
    final_review.template(private_studio,allow_short=True)
    return private_studio,binding


def fill(root):
    path=root/"review"/final_review.TEMPLATE
    data=source.read_json(path)
    for row in data["decisions"].values():
        for key in row:row[key]="PASS"
    data["rights_self_attested"]="PASS"
    path.write_text(json.dumps(data),encoding="utf-8")
    return path,data


def test_complete_receipt_no_overwrite_and_stale_export(bound_review):
    root,binding=bound_review
    with pytest.raises(ValueError,match="PASS/FAIL"):
        final_review.record(root,acknowledgment=final_review.ACK,allow_short=True)
    fill(root)
    with pytest.raises(ValueError,match="acknowledgment"):
        final_review.record(root,acknowledgment="NO",allow_short=True)
    result=final_review.record(root,acknowledgment=final_review.ACK,allow_short=True)
    assert result["all_manual_observations_pass"]
    assert result["publication_approved"] is False
    assert final_review.inspect(root,allow_short=True)["manual_turns_reviewed"]==45
    with pytest.raises(ValueError,match="overwrite"):
        final_review.record(root,acknowledgment=final_review.ACK,allow_short=True)
    binding["video_sha256"]="changed"
    with pytest.raises(ValueError,match="stale"):
        final_review.inspect(root,allow_short=True)


def test_failed_turn_and_missing_decision(bound_review):
    root,_=bound_review
    path,data=fill(root)
    missing=data["decisions"].pop("045")
    path.write_text(json.dumps(data),encoding="utf-8")
    with pytest.raises(ValueError,match="Exactly 45"):
        final_review.record(root,acknowledgment=final_review.ACK,allow_short=True)
    data["decisions"]["045"]=missing
    data["decisions"]["045"]["lip_sync"]="FAIL"
    path.write_text(json.dumps(data),encoding="utf-8")
    result=final_review.record(root,acknowledgment=final_review.ACK,allow_short=True)
    assert result["failed_turn_ids"]==["045"]
    assert not result["all_manual_observations_pass"]
    assert not final_review.inspect(root,allow_short=True)["all_manual_observations_pass"]
