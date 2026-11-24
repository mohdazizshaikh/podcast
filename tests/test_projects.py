import json
import sys
import pytest
from podcast_gpt import projects,credentials,episode_plan,source,cli,web


def req(topic="Test"):
    return {"topic":topic,"language":"Hindi","duration_minutes":1,"presenters":["Solo"],
            "video_format":"square","workflow":"manual","input_kind":"topic","research_mode":"knowledge"}


def test_projects_are_separate_and_read_only_list(tmp_path,monkeypatch):
    root=tmp_path/"private"
    assert projects.list_projects(root)=={"projects":[],"blocked":[]}
    assert not root.exists()
    a=projects.create(root,req("One"))["project_id"]
    b=projects.create(root,req("Two"))["project_id"]
    assert a!=b and projects.load(root,a)["topic"]=="One"
    def plan(data,**options):
        return {"provider":"ollama","result":{"title":"One","sections":[{"heading":"Start","minutes":1,"summary":"Intro","presenters":["Solo"]}]}}
    monkeypatch.setattr(episode_plan,"plan",plan)
    result=projects.generate_outline(root,a)
    assert result["stage"]=="outline_saved" and not result["publication_approved"]
    assert projects.inspect(root,b)["stage"]=="request_saved"
    assert len(projects.list_projects(root)["projects"])==2
    with pytest.raises(ValueError,match="exists"):projects.generate_outline(root,a)
    p=projects.project(root,a)/projects.PLAN
    data=source.read_json(p);data["outline"]["title"]="Changed"
    p.write_text(json.dumps(data),encoding="utf-8")
    with pytest.raises(ValueError,match="hash"):projects.inspect(root,a)
    assert projects.list_projects(root)["blocked"]==[a]
    assert not (root/"project.json").exists()


def test_path_and_lock_guard(tmp_path):
    root=tmp_path/"private"
    pid=projects.create(root,req())["project_id"]
    with pytest.raises(ValueError):projects.project(root,"../outside")
    with projects.exclusive(projects.project(root,pid)):
        with pytest.raises(ValueError,match="active"):projects.generate_outline(root,pid)
    repo=tmp_path/"repo";repo.mkdir();(repo/".git").mkdir()
    with pytest.raises(ValueError,match="OUTSIDE"):projects.create(repo/"private",req())


def test_encrypted_store_precedence_and_remove(tmp_path,monkeypatch):
    root=tmp_path/"private"
    pid=projects.create(root,req())["project_id"]
    # Fixture only, never a production cryptography replacement.
    monkeypatch.setattr(credentials.sys,"platform","win32")
    monkeypatch.setattr(credentials,"_dpapi",lambda b,**kw:bytes(x^0xA5 for x in b))
    monkeypatch.setenv("OPENROUTER_API_KEY","env-test-key")
    monkeypatch.delenv("GEMINI_API_KEY",raising=False)
    credentials.store(root,"openrouter","default-test-key")
    credentials.store(root,"openrouter","project-test-key",pid=pid)
    credentials.store(root,"gemini","gemini-test-key")
    assert credentials.resolve(root,pid=pid).openrouter=="project-test-key"
    assert credentials.resolve(root,pid=pid).gemini=="gemini-test-key"
    result=credentials.status(root,pid=pid)
    assert result["project_encrypted"]==["openrouter"]
    for p in root.rglob(credentials.FILENAME):
        assert b"test-key" not in p.read_bytes()
    assert "test-key" not in json.dumps(result)
    credentials.remove(root,"openrouter",pid=pid)
    assert credentials.resolve(root,pid=pid).openrouter=="default-test-key"
    credentials.remove(root,"openrouter")
    assert credentials.resolve(root,pid=pid).openrouter=="env-test-key"


@pytest.mark.skipif(sys.platform!="win32",reason="Actual Windows DPAPI test")
def test_actual_windows_dpapi_round_trip(tmp_path):
    root=tmp_path/"private"
    credentials.store(root,"openrouter","synthetic-dpapi-key")
    assert credentials.resolve(root).openrouter=="synthetic-dpapi-key"
    assert b"synthetic-dpapi-key" not in (projects.base(root)/credentials.FILENAME).read_bytes()
    assert credentials.remove(root,"openrouter")["removed"]


def test_cli_project_list_and_dashboard(tmp_path):
    assert cli.execute(cli.parse(["--workspace",str(tmp_path/"none"),"project-list"]))["projects"]==[]
    assert 'data-action="project-list"' in web.html_page("token")
