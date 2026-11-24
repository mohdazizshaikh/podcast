import json
import pytest
from pathlib import Path
from podcast_gpt import projects, source, ai_providers as ai, script_generation as sg, script_review as sr, cli


def ready(root,monkeypatch):
    req={"topic":"Science","language":"English","duration_minutes":1,"presenters":["A","B"],
         "video_format":"square","workflow":"manual","input_kind":"topic","research_mode":"knowledge"}
    pid=projects.create(root,req)["project_id"]
    outline={"title":"Science","sections":[{"heading":"Science","minutes":1,"summary":"Discussion","presenters":["A","B"]}]}
    source.atomic_json(projects.project(root,pid)/projects.PLAN,{"schema":2,"request_sha256":source.json_digest(req),
        "evidence_sha256":None,"outline_sha256":source.json_digest(outline),"outline":outline,"provider":"ollama"},new=True)
    def fake(prompt,validator,**kwargs):
        return {"provider":"ollama","result":validator({"turns":[
            {"speaker":"A","text":"An original synthetic discussion about a scientific idea.","estimated_seconds":30},
            {"speaker":"B","text":"A different synthetic response about that scientific idea.","estimated_seconds":30}]})}
    monkeypatch.setattr(ai,"generate_json",fake)
    sg.generate(root,pid);sg.finalize(root,pid)
    return pid


def edit(path,change):
    value=source.read_json(path,sg.MAX_FINAL_BYTES)
    change(value)
    path.write_text(json.dumps(value,ensure_ascii=False),encoding="utf-8")


def complete_review(path,*,fail=False):
    def change(data):
        obs=data["observations"]
        obs["turn_decisions"]={k:"FAIL" if fail and k=="0001" else "PASS" for k in obs["turn_decisions"]}
        obs["criteria"]={k:"PASS" for k in obs["criteria"]}
    edit(path,change)


def test_review_and_new_revision_invalidate_approval(tmp_path,monkeypatch):
    root=tmp_path/"private";pid=ready(root,monkeypatch)
    folder=projects.project(root,pid)
    draft=(folder/sg.FINAL).read_bytes()
    assert sr.inspect(root,pid)["review_status"]=="UNREVIEWED"
    with pytest.raises(ValueError,match="PASS"):sr.current_script(root,pid,require_pass=True)
    path=Path(sr.template(root,pid,review=True)["template_path"])
    with pytest.raises(ValueError,match="acknowledgment"):sr.record(root,pid,acknowledgment="YES")
    with pytest.raises(ValueError,match="UNREVIEWED"):sr.record(root,pid,acknowledgment=sr.ACK)
    complete_review(path)
    assert sr.record(root,pid,acknowledgment=sr.ACK)["human_script_self_attested_pass"]
    assert sr.current_script(root,pid,require_pass=True)["version"]==0
    with pytest.raises(ValueError,match="overwritten"):sr.record(root,pid,acknowledgment=sr.ACK)
    previous=(folder/sr.FOLDER/"r000-review.json").read_bytes()
    path=Path(sr.template(root,pid)["template_path"])
    with pytest.raises(ValueError,match="No script changes"):sr.revise(root,pid)
    edit(path,lambda d:d["turns"][0].update(text="Revised original discussion for the human reviewed science script."))
    result=sr.revise(root,pid)
    assert result["version"]==1 and result["review_status"]=="UNREVIEWED"
    assert not result["human_script_self_attested_pass"]
    assert (folder/sg.FINAL).read_bytes()==draft
    assert (folder/sr.FOLDER/"r000-review.json").read_bytes()==previous
    assert projects.inspect(root,pid)["script_review"]["version"]==1
    path=Path(sr.template(root,pid,review=True)["template_path"])
    complete_review(path,fail=True)
    result=sr.record(root,pid,acknowledgment=sr.ACK)
    assert result["review_status"]=="FAIL" and result["failed_turns"]==["0001"]
    with pytest.raises(ValueError,match="PASS"):sr.current_script(root,pid,require_pass=True)


def test_revision_validation_and_tamper(tmp_path,monkeypatch):
    root=tmp_path/"private";pid=ready(root,monkeypatch)
    path=Path(sr.template(root,pid)["template_path"])
    edit(path,lambda d:d["turns"][0].update(id="0099"))
    with pytest.raises(ValueError,match="IDs"):sr.revise(root,pid)
    edit(path,lambda d:d["turns"][0].update(id="0001",speaker="Unknown"))
    with pytest.raises(ValueError,match="presenter"):sr.revise(root,pid)
    edit(path,lambda d:d["turns"][0].update(speaker="A",text="Revised original speech for the science podcast."))
    sr.revise(root,pid)
    receipt=projects.project(root,pid)/sr.FOLDER/"r001.json"
    edit(receipt,lambda d:d["turns"][0].update(text="Tampered but otherwise valid dialogue about scientific ideas."))
    with pytest.raises(ValueError,match="hash"):sr.inspect(root,pid)


def test_cli_current_and_read_only_status(tmp_path,monkeypatch):
    root=tmp_path/"private";pid=ready(root,monkeypatch)
    result=cli.execute(cli.parse(["--workspace",str(root),"project-script-current","--project-id",pid]))
    assert len(result["turns"])==2 and result["review_status"]=="UNREVIEWED"
    assert not (projects.project(root,pid)/sr.FOLDER).exists()
