import json
from pathlib import Path
import pytest
from podcast_gpt import projects, source, v4_final_review as final, v4_recovery as recovery, v4_readiness as ready, v4_neural as neural, web
from test_v4_preview import fixture,approve


def test_full_review_version_binding(tmp_path,monkeypatch):
    folder=tmp_path/"private";folder.mkdir();dest=folder/"audio";dest.mkdir()
    receipt={"test_fixture_only":False,"video_sha256":"a"*64}
    turns=[{"id":"0001"},{"id":"0002"}]
    monkeypatch.setattr(projects,"project",lambda *a:folder)
    monkeypatch.setattr(final,"_context",lambda *a:(folder,dest,receipt,turns))
    assert final.inspect(folder,"x")["review_status"]=="UNREVIEWED"
    p=Path(final.template(folder,"x")["template_path"])
    with pytest.raises(ValueError,match="UNREVIEWED"):final.record(folder,"x",acknowledgment=final.ACK)
    data=source.read_json(p)
    for row in [data["criteria"],*data["turns"].values()]:
        for k in row:row[k]="PASS"
    p.write_text(json.dumps(data),encoding="utf-8")
    with pytest.raises(ValueError,match="acknowledgment"):final.record(folder,"x",acknowledgment="YES")
    result=final.record(folder,"x",acknowledgment=final.ACK)
    assert result["human_video_self_attested_pass"] and not result["publication_approved"]
    with pytest.raises(ValueError,match="overwritten"):final.record(folder,"x",acknowledgment=final.ACK)
    receipt["video_sha256"]="b"*64
    with pytest.raises(ValueError,match="stale"):final.inspect(folder,"x")


def test_archive_stopped_attempt_and_preserve_lock(tmp_path,monkeypatch):
    root,pid=fixture(tmp_path,monkeypatch);approve(root,pid)
    folder,dest,binding,rows,targets=neural._context(root,pid)
    cid=targets[0];scratch=folder/recovery.SCRATCH/(source.json_digest(binding)+"-"+cid)
    scratch.mkdir(parents=True);(scratch/"stderr.log").write_bytes(b"synthetic failure")
    assert recovery.inspect(root,pid)["archive_eligible_ids"]==[cid]
    with projects.exclusive(folder):
        assert recovery.inspect(root,pid)["lock_present"]
        with pytest.raises(ValueError,match="active"):recovery.archive(root,pid,cid,acknowledgment=recovery.ACK)
    with pytest.raises(ValueError,match="acknowledgment"):recovery.archive(root,pid,cid,acknowledgment="YES")
    saved=recovery.archive(root,pid,cid,acknowledgment=recovery.ACK)
    assert not scratch.exists()
    assert (Path(saved["archive_path"])/"attempt"/"stderr.log").read_bytes()==b"synthetic failure"
    assert recovery.inspect(root,pid)["archive_eligible_ids"]==[]
    with pytest.raises(ValueError,match="eligible"):recovery.archive(root,pid,cid,acknowledgment=recovery.ACK)


def test_readiness_initial_and_web_markup(tmp_path):
    root=tmp_path/"private"
    req={"topic":"Science","language":"Hindi","duration_minutes":1,"presenters":["A"],
         "video_format":"square","workflow":"manual","input_kind":"topic","research_mode":"knowledge"}
    pid=projects.create(root,req)["project_id"]
    folder=projects.project(root,pid)
    before={p.name for p in folder.iterdir()}
    result=ready.inspect(root,pid)
    assert result["stage"]=="outline_required" and result["next_action"]=="project-plan"
    assert {p.name for p in folder.iterdir()}==before
    assert "v4Readiness" in web.html_page("test")
    with projects.exclusive(folder):assert ready.inspect(root,pid)["stage"]=="operation_locked"
