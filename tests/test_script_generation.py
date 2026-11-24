"""Synthetic dialogue fixtures only; no actual provider requests or audio."""
import json
import pytest
from podcast_gpt import ai_providers as ai, projects, source, script_generation as sg, cli


def setup(root,minutes=3,people=None):
    people=people or ["Aarav","Meera","Kabir"]
    req={"topic":"Science","language":"Hindi","duration_minutes":minutes,"presenters":people,
         "video_format":"vertical","workflow":"automatic","input_kind":"topic","research_mode":"knowledge"}
    pid=projects.create(root,req)["project_id"]
    outline={"title":"Science","sections":[{"heading":"Discussion","minutes":minutes,"summary":"Explore ideas","presenters":people}]}
    source.atomic_json(projects.project(root,pid)/projects.PLAN,{"schema":2,"request_sha256":source.json_digest(req),
        "evidence_sha256":None,"outline_sha256":source.json_digest(outline),"outline":outline,"provider":"ollama"},new=True)
    return pid


def fake_value(unit):
    people=unit["presenters"]
    names=people if len(people)>=2 else people*2
    seconds=[60//len(names)]*len(names)
    seconds[-1]+=60-sum(seconds)
    return {"turns":[{"speaker":name,"text":f"Original synthetic dialogue unit {unit['id']} turn {i} about science.",
                       "estimated_seconds":sec} for i,(name,sec) in enumerate(zip(names,seconds))]}


def fixture_provider(prompt,validator,**kwargs):
    unit=json.loads(prompt.split("Context JSON:\n",1)[1])["unit"]
    return {"provider":"ollama","result":validator(fake_value(unit))}


def test_resume_and_finalization(tmp_path,monkeypatch):
    root=tmp_path/"private";pid=setup(root)
    monkeypatch.setattr(ai,"generate_json",fixture_provider)
    assert sg.inspect(root,pid)["completed_units"]==0
    assert not (projects.project(root,pid)/sg.PARTS).exists()
    assert sg.generate(root,pid,max_new=1)["completed_units"]==1
    assert projects.inspect(root,pid)["stage"]=="script_in_progress"
    with pytest.raises(ValueError,match="every script unit"):sg.finalize(root,pid)
    first=(projects.project(root,pid)/sg.PARTS/"001.json").read_bytes()
    result=sg.generate(root,pid,max_new=5)
    assert result["new_units"]==2 and result["stage"]=="script_ready_to_finalize"
    assert first==(projects.project(root,pid)/sg.PARTS/"001.json").read_bytes()
    assert sg.finalize(root,pid)["stage"]=="script_saved"
    final=sg.show(root,pid)["script"]
    assert len(final["turns"])==9 and final["planned_seconds"]==180
    assert final["measured_audio_seconds"] is None and not final["human_review_approved"]
    assert sg.generate(root,pid)["new_units"]==0
    assert sg.finalize(root,pid)["script_sha256"]==source.json_digest(final)
    assert projects.list_projects(root)["projects"][0]["stage"]=="script_saved"


def test_failure_preserves_prefix_and_resume(tmp_path,monkeypatch):
    root=tmp_path/"private";pid=setup(root)
    calls=[]
    def fail(prompt,validator,**kwargs):
        calls.append(prompt)
        if len(calls)==2:raise ai.ProviderError("synthetic quota error")
        return fixture_provider(prompt,validator,**kwargs)
    monkeypatch.setattr(ai,"generate_json",fail)
    with pytest.raises(ai.ProviderError):sg.generate(root,pid,max_new=3)
    assert sg.inspect(root,pid)["completed_units"]==1
    assert not (projects.project(root,pid)/projects.LOCK).exists()
    monkeypatch.setattr(ai,"generate_json",fixture_provider)
    assert sg.generate(root,pid,max_new=3)["new_units"]==2


def test_tamper_and_gap_block_before_provider(tmp_path,monkeypatch):
    root=tmp_path/"private";pid=setup(root)
    monkeypatch.setattr(ai,"generate_json",fixture_provider)
    sg.generate(root,pid,max_new=2)
    folder=projects.project(root,pid)/sg.PARTS
    first=folder/"001.json";original=first.read_bytes()
    data=json.loads(original);data["dialogue"]["turns"][0]["text"]="Changed but long enough dialogue to stay valid."
    first.write_text(json.dumps(data),encoding="utf-8")
    with pytest.raises(ValueError,match="hash"):sg.inspect(root,pid)
    first.unlink()
    with pytest.raises(ValueError,match="prefix"):sg.generate(root,pid)


def test_60_minute_10_presenter_bounds_and_dialogue_validation(tmp_path,monkeypatch):
    root=tmp_path/"private";pid=setup(root,60,["P"+str(i) for i in range(10)])
    _,req,evidence,outline,binding=sg._context(root,pid)
    plan=sg.units(outline)
    assert len(plan)==60 and plan[-1]["id"]=="060"
    value=fake_value(plan[0])
    assert sg.validate_dialogue(value,plan[0])==value
    bad=json.loads(json.dumps(value));bad["turns"][0]["speaker"]="Unknown"
    with pytest.raises(ValueError,match="presenter"):sg.validate_dialogue(bad,plan[0])
    bad=json.loads(json.dumps(value));bad["turns"][0]["estimated_seconds"]+=1
    with pytest.raises(ValueError,match="sum"):sg.validate_dialogue(bad,plan[0])
    with pytest.raises(ValueError,match="Repeated"):sg.validate_dialogue(value,plan[0],value["turns"])
    with pytest.raises(ValueError,match="1–5"):sg.generate(root,pid,max_new=60)
    monkeypatch.setattr(ai,"generate_json",fixture_provider)
    for _ in range(12):sg.generate(root,pid,max_new=5)
    assert sg.finalize(root,pid)["draft_turns"]==600
    assert sg.show(root,pid)["script"]["planned_seconds"]==3600


def test_cli_script_status(tmp_path):
    root=tmp_path/"private";pid=setup(root,1,["Solo"])
    args=cli.parse(["--workspace",str(root),"project-script-status","--project-id",pid])
    assert cli.execute(args)["remaining_units"]==1
