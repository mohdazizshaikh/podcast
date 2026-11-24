import json
import pytest
from podcast_gpt import dashboard_actions as d, projects, cli, web
from podcast_gpt import v4_mixed_video as mixed


def request():
    return {"topic":"Science","language":"Hindi","duration_minutes":1,"presenters":["A"],
            "video_format":"square","workflow":"manual","input_kind":"topic","research_mode":"knowledge"}


def test_project_request_and_action_gates(tmp_path,monkeypatch):
    root=tmp_path/"private"
    value=d.parse_request(json.dumps(request()).encode())
    pid=projects.create(root,value)["project_id"]
    assert projects.load(root,pid)==value
    for raw in (b"{}",b"bad",b"x"*32769,json.dumps({**request(),"duration_minutes":61}).encode(),
                json.dumps({**request(),"api_key":"not allowed"}).encode()):
        with pytest.raises(ValueError):d.parse_request(raw)
    with pytest.raises(ValueError,match="acknowledgment"):d.run(root,pid,"project-safe-step",acknowledgment="YES")
    with pytest.raises(ValueError,match="Unknown"):d.run(root,pid,"project-tts-kokoro",acknowledgment=d.ACK)
    calls=[]
    def runner(*args,**kwargs):
        calls.append(kwargs);return {"ok":True}
    monkeypatch.setattr(d.v4_orchestrator,"run",runner)
    assert d.run(root,pid,"project-safe-step",acknowledgment=d.ACK)=={"ok":True}
    assert calls==[{"execute":True,"acknowledgment":d.v4_orchestrator.ACK,"max_steps":1}]
    with projects.exclusive(projects.project(root,pid)):
        with pytest.raises(ValueError,match="lock"):d.run(root,pid,"project-safe-step",acknowledgment=d.ACK)
    assert "v4Create" in web.html_page("test") and "v4ProcessConsent" in web.html_page("test")
    assert cli.parse(["doctor"]).operation=="doctor"
    assert cli.parse(["project-mixed-studio-compose","--project-id",pid]).operation=="project-mixed-studio-compose"


def test_separate_mixed_studio_review_binding(tmp_path):
    receipt={"video_sha256":"a"*64}
    timeline={"rows":[{"turn_id":"0001"}]}
    value=mixed._review_value(receipt,timeline,"studio")
    for row in [value["criteria"],value["turns"]["0001"]]:
        for k in row:row[k]="PASS"
    assert mixed._validate(value,receipt,timeline,"studio")
    with pytest.raises(ValueError,match="binding"):mixed._validate(value,receipt,timeline,"video")
    assert mixed._review_file(tmp_path,"studio")!=mixed._review_file(tmp_path,"video")
