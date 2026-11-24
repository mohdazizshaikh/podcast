import pytest
from podcast_gpt import dashboard_inference as d, dashboard_authoring as author, projects, v4_orchestrator as auto
from podcast_gpt import v4_readiness, ai_providers, web
from test_v4_dashboard_actions import request


def test_selected_engine_consent_and_scope(tmp_path,monkeypatch):
    root=tmp_path/"private";pid=projects.create(root,request())["project_id"]
    data={"project_id":pid,"engine":"ollama","max_steps":1,"model_consent":True}
    with pytest.raises(ValueError,match="consent"):author.run(root,"local-inference",data)
    with pytest.raises(ValueError,match="consent"):author.run(root,"local-inference",{**data,"model_consent":False},acknowledgment=author.ACK)
    with pytest.raises(ValueError):author.run(root,"local-inference",{**data,"engine":"gemini"},acknowledgment=author.ACK)
    with pytest.raises(ValueError):author.run(root,"local-inference",{**data,"max_steps":True},acknowledgment=author.ACK)
    calls=[]
    monkeypatch.setattr(auto,"run",lambda *a,**kw:(calls.append(kw) or {"events":[]}))
    result=author.run(root,"local-inference",data,acknowledgment=author.ACK)
    assert not result["cloud_calls_authorized"]
    assert calls[0]["allow_local_ai"] and calls[0]["allowed_stages"]==("outline_required","script_required")
    assert "neural_ack" not in calls[0]
    assert "v4InferenceRun" in web.html_page("test")


def test_progress_and_gate(tmp_path,monkeypatch):
    root=tmp_path/"private";pid=projects.create(root,request())["project_id"]
    states=iter([{"stage":"outline_required","next_action":"project-plan"},
                 {"stage":"script_required","next_action":"project-script-generate","checks":{"script_units":{"completed":0,"total":1}}},
                 {"stage":"script_review_required","next_action":"review"}])
    monkeypatch.setattr(v4_readiness,"inspect",lambda *a:next(states))
    calls=[];events=[]
    monkeypatch.setattr(projects,"generate_outline",lambda *a,**kw:calls.append(kw))
    monkeypatch.setattr(auto.scripts,"generate",lambda *a,**kw:calls.append(kw))
    result=d.run(root,pid,engine="ollama",max_steps=5,acknowledgment=d.ACK,progress=events.append)
    assert calls==[{"offline_only":True},{"max_new":1,"offline_only":True}]
    assert [e["completed_actions"] for e in events]==[0,1,1,2]
    assert [e["checkpoint_verified"] for e in events]==[False,True,False,True]
    assert result["readiness"]["stage"]=="script_review_required"
    assert len(result["events"])==2


def test_research_browser_consent(tmp_path,monkeypatch):
    root=tmp_path/"private";pid=projects.create(root,{**request(),"research_mode":"web"})["project_id"]
    calls=[]
    monkeypatch.setattr(author.research,"capture",lambda *a,**kw:(calls.append((a,kw)) or {"source_count":2}))
    data={"project_id":pid,"urls":["https://example.org/a","https://example.org/b"],"allow_web_fetch":True}
    with pytest.raises(ValueError,match="consent"):author.run(root,"research-capture",data)
    assert author.run(root,"research-capture",data,acknowledgment=author.ACK)["source_count"]==2
    assert calls[0][1]=={"allow_web_fetch":True}
    with pytest.raises(ValueError):author.run(root,"research-capture",{**data,"urls":[1]},acknowledgment=author.ACK)


def test_offline_does_not_load_environment_keys(monkeypatch):
    def fail(*a):raise AssertionError("Offline should not read cloud environment keys")
    monkeypatch.setattr(ai_providers.Credentials,"environment",fail)
    def request(*a,**kw):raise ai_providers.ProviderError("offline_test")
    with pytest.raises(ai_providers.ProviderError):ai_providers.generate_json("test",lambda x:x,offline_only=True,request=request)
