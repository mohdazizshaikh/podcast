import json
import sys
from pathlib import Path
from types import SimpleNamespace
import pytest
from podcast_gpt import visual_script as visual, script_review as review, source, projects, cli
from podcast_gpt import dependency_setup as deps, v4_orchestrator as auto, v4_readiness
from test_script_review import ready


def test_visual_editor_and_bound_import(tmp_path,monkeypatch):
    root=tmp_path/"private";pid=ready(root,monkeypatch)
    current=review.current_script(root,pid)
    content=visual.build({**current,"turns":[{**current["turns"][0],"text":"</script><img src=x onerror=alert(1)>"}]},mode="edit")
    assert "</script><img" not in content and "Content-Security-Policy" in content
    path=Path(visual.create(root,pid,mode="edit")["html_path"])
    assert "Export JSON" in path.read_text(encoding="utf-8")
    with pytest.raises(FileExistsError):visual.create(root,pid,mode="edit")
    value={"schema":1,"version":current["version"],"version_sha256":current["version_sha256"],"turns":current["turns"]}
    value["turns"][0]["text"]="A revised synthetic discussion about science and its applications."
    edit=tmp_path/"edit.json";edit.write_text(json.dumps(value),encoding="utf-8")
    assert review.revise(root,pid,input_file=edit)["version"]==1
    with pytest.raises(ValueError,match="stale"):review.revise(root,pid,input_file=edit)
    cur=review.current_script(root,pid)
    assert Path(visual.create(root,pid,mode="review")["html_path"]).exists()
    obs={"schema":1,"version":cur["version"],"version_sha256":cur["version_sha256"],
         "observations":{"turn_decisions":{t["id"]:"PASS" for t in cur["turns"]},"criteria":{k:"PASS" for k in review.CRITERIA}}}
    path=tmp_path/"review.json";path.write_text(json.dumps(obs),encoding="utf-8")
    assert review.record(root,pid,input_file=path,acknowledgment=review.ACK)["human_script_self_attested_pass"]


def test_dependency_install_consent_and_argv(monkeypatch):
    calls=[]
    def runner(args,**kw):
        calls.append((args,kw));return SimpleNamespace(returncode=0)
    with pytest.raises(ValueError,match="acknowledgment"):deps.install("documents",acknowledgment="YES",runner=runner)
    assert not calls
    monkeypatch.setattr(sys,"prefix","fake-venv")
    result=deps.install("documents",acknowledgment=deps.ACK,runner=runner)
    assert result["pip_check_passed"] and len(calls)==2
    assert calls[0][0][-1]=="pypdf>=5,<8" and calls[1][0][-1]=="check"
    assert calls[0][1]["env"]["PIP_CONFIG_FILE"]
    with pytest.raises(ValueError):deps.plan("arbitrary-package")


def test_orchestration_bounded_and_stops_at_review(tmp_path,monkeypatch):
    root=tmp_path/"private";pid=ready(root,monkeypatch)
    assert auto.run(root,pid)["status"]=="plan_only"
    with pytest.raises(ValueError,match="acknowledgment"):auto.run(root,pid,execute=True)
    assert auto.run(root,pid,execute=True,acknowledgment=auto.ACK)["readiness"]["stage"]=="script_review_required"
    states=iter([{"stage":"timeline_required","next_action":"project-audio-finalize"},
                 {"stage":"master_required","next_action":"project-master-compose"},
                 {"stage":"listening_review_required","next_action":"review"}])
    monkeypatch.setattr(v4_readiness,"inspect",lambda *a:next(states))
    calls=[]
    monkeypatch.setattr(auto.audio,"finalize",lambda *a:calls.append("timeline"))
    monkeypatch.setattr(auto.master,"compose",lambda *a:calls.append("master"))
    result=auto.run(root,pid,execute=True,acknowledgment=auto.ACK,max_steps=2)
    assert calls==["timeline","master"] and len(result["events"])==2
    assert result["readiness"]["stage"]=="listening_review_required"
    assert not result["human_review_automated"]
