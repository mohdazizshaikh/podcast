import json
from pathlib import Path
import pytest
from podcast_gpt import dashboard_review as review, manual_script as manual, projects, script_generation as sg
from podcast_gpt import script_review, v4_orchestrator as auto, dashboard_inference as inference, v4_readiness, web, source
from test_v4_dashboard_actions import request


def test_manual_script_and_browser_review(tmp_path,monkeypatch):
    root=tmp_path/"private";pid=projects.create(root,{**request(),"input_kind":"custom_script"})["project_id"]
    value={"title":"Manual episode","minutes":[{"turns":[
        {"speaker":"A","text":"This is the exact supplied opening dialogue for our episode.","estimated_seconds":30},
        {"speaker":"A","text":"This is the exact supplied conclusion without any rewriting.","estimated_seconds":30}]}]}
    path=tmp_path/"script.txt";path.write_text(json.dumps(value),encoding="utf-8")
    projects.import_source(root,pid,path=path)
    with pytest.raises(ValueError,match="acknowledgment"):manual.import_saved(root,pid,acknowledgment="YES")
    result=manual.import_saved(root,pid,acknowledgment=manual.ACK)
    assert result["new_units"]==1 and result["ai_calls"]==0
    assert manual.import_saved(root,pid,acknowledgment=manual.ACK)["new_units"]==0
    current=script_review.current_script(root,pid)
    assert [{k:v for k,v in t.items() if k!="id"} for t in current["turns"]]==value["minutes"][0]["turns"]
    assert current["review_status"]=="UNREVIEWED"
    template=review.template(root,pid,"script")
    data=source.read_json(Path(template["template_path"]))
    for row in data["observations"].values():
        for k in row:row[k]="PASS"
    raw=json.dumps(data).encode()
    with pytest.raises(ValueError,match="attestation"):review.upload(root,pid,"script",raw,acknowledgment=review.ACK)
    result=review.upload(root,pid,"script",raw,acknowledgment=review.ACK,attestation=script_review.ACK)
    assert result["human_script_self_attested_pass"] and not result["publication_approved"]
    with pytest.raises(ValueError,match="overwritten"):review.upload(root,pid,"script",raw,acknowledgment=review.ACK,attestation=script_review.ACK)
    with pytest.raises(ValueError,match="manual import"):sg.generate(root,pid)
    part=projects.project(root,pid)/sg.PARTS/"001.json";saved=source.read_json(part)
    saved["dialogue"]["turns"][0]["text"]="Changed dialogue that still fits within the validated text limits."
    saved["dialogue_sha256"]=source.json_digest(saved["dialogue"]);part.write_text(json.dumps(saved),encoding="utf-8")
    with pytest.raises(ValueError,match="captured source"):sg.show(root,pid)


def test_cooperative_stop_after_checkpoint(tmp_path,monkeypatch):
    root=tmp_path/"private";pid=projects.create(root,request())["project_id"]
    states=iter([{"stage":"outline_required","next_action":"project-plan"},
        {"stage":"script_required","next_action":"project-script-generate","checks":{"script_units":{"completed":0,"total":1}}}])
    monkeypatch.setattr(v4_readiness,"inspect",lambda *a:next(states))
    calls=[];stop=[False]
    monkeypatch.setattr(projects,"generate_outline",lambda *a,**kw:calls.append("outline"))
    def report(event):
        if event["checkpoint_verified"]:stop[0]=True
    result=inference.run(root,pid,engine="ollama",max_steps=5,acknowledgment=inference.ACK,progress=report,should_stop=lambda:stop[0])
    assert calls==["outline"] and result["status"]=="stopped_at_checkpoint" and len(result["events"])==1
    assert "v4StopTask" in web.html_page("test") and "v4ReviewImport" in web.html_page("test")


def test_bad_manual_input_does_not_create_outline(tmp_path):
    root=tmp_path/"private";pid=projects.create(root,{**request(),"input_kind":"custom_script"})["project_id"]
    path=tmp_path/"script.txt";path.write_text('{"title":"bad","minutes":[]}',encoding="utf-8")
    projects.import_source(root,pid,path=path)
    with pytest.raises(ValueError):manual.import_saved(root,pid,acknowledgment=manual.ACK)
    assert not (projects.project(root,pid)/projects.PLAN).exists()
