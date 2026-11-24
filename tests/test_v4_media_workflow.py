import json
from pathlib import Path
import pytest
from podcast_gpt import projects, v4_orchestrator as auto, v4_progress as progress, source
from podcast_gpt import visual_media_review as visual, v4_audio_review as review, v4_readiness
from test_v4_preview import fixture


def test_visual_review_and_bound_import(tmp_path,monkeypatch):
    root,pid=fixture(tmp_path,monkeypatch)
    result=visual.create(root,pid,kind="audio")
    assert Path(result["html_path"]).exists() and not result["approval_recorded"]
    assert review.inspect(root,pid)["review_status"]=="UNREVIEWED"
    _,_,timeline,sha=review._context(root,pid)
    value={"schema":1,"master_sha256":sha,"turns":{r["turn_id"]:"PASS" for r in timeline["rows"]},
           "criteria":{k:"PASS" for k in review.CRITERIA}}
    path=tmp_path/"download.json";path.write_text(json.dumps(value),encoding="utf-8")
    with pytest.raises(ValueError,match="acknowledgment"):review.record(root,pid,input_file=path,acknowledgment="YES")
    assert review.record(root,pid,input_file=path,acknowledgment=review.ACK)["human_audio_self_attested_pass"]
    assert "</script><img" not in visual.build({"turns":{"x":"UNREVIEWED"}},["</script><img"],["turns"],"test.json")


def test_history_and_tamper(tmp_path,monkeypatch):
    root,pid=fixture(tmp_path,monkeypatch)
    assert progress.inspect(root,pid)["completed_observations"]==0
    for t in (2,4):progress.record(root,pid,scope="a"*64,action="kokoro",unit="0001",seconds=t)
    result=progress.inspect(root,pid)
    assert result["groups"][0]["mean_seconds"]==3 and not result["live_eta_available"]
    p=next((projects.project(root,pid)/progress.FOLDER).iterdir())
    d=source.read_json(p);d["observation"]["seconds"]=99;p.write_text(json.dumps(d),encoding="utf-8")
    with pytest.raises(ValueError,match="hash"):progress.inspect(root,pid)


def test_runner_media_consent(tmp_path,monkeypatch):
    root,pid=fixture(tmp_path,monkeypatch)
    before={"stage":"audio_required","next_action":"audio"};after={"stage":"listening_review_required","next_action":"review"}
    monkeypatch.setattr(v4_readiness,"inspect",lambda *a:before)
    assert auto.run(root,pid,execute=True,acknowledgment=auto.ACK)["events"]==[]
    with pytest.raises(ValueError,match="acknowledgment"):auto.run(root,pid,execute=True,acknowledgment=auto.ACK,kokoro_ack="YES")
    states=iter([before,after]);monkeypatch.setattr(v4_readiness,"inspect",lambda *a:next(states))
    monkeypatch.setattr(auto.audio,"_context",lambda *a:(None,None,{"binding":"fixture"},[{"id":"0001","speaker":"A"}],{},{"presenters":[{"speaker":"A","voice_preferences":{"engine":"kokoro"}}]}))
    monkeypatch.setattr(auto.audio,"_read_parts",lambda *a:{})
    monkeypatch.setattr(auto.model_config,"read",lambda *a:{"model":tmp_path/"model","voices":tmp_path/"voices"})
    def fake(*a,**kw):
        assert kw["run_local"] and kw["acknowledgment"]==auto.v4_tts.ACK and kw["max_new"]==1
        return {"new_generated_turns":["0001"]}
    monkeypatch.setattr(auto.v4_tts,"generate",fake)
    result=auto.run(root,pid,execute=True,acknowledgment=auto.ACK,kokoro_ack=auto.v4_tts.ACK,max_steps=1)
    assert result["readiness"]==after and progress.inspect(root,pid)["completed_observations"]==1
