import pytest
from podcast_gpt import cli,web,dashboard_authoring as da,render_history as h

def test_routes(tmp_path,monkeypatch):
    pid='a'*32
    assert cli.parse(['project-render-performance','--project-id',pid]).operation=='project-render-performance'
    assert 'v4RenderPerformance' in web.html_page('test')
    monkeypatch.setattr(h,'inspect',lambda root,pid:{'project_id':pid,'records':[]})
    assert da.run(tmp_path,'render-performance',{'project_id':pid})=={'project_id':pid,'records':[]}

def test_inspect_lock(tmp_path,monkeypatch):
    from podcast_gpt import projects
    monkeypatch.setattr(projects,'project',lambda *a:tmp_path)
    assert h.inspect(None,'p')['records']==[]
    with projects.exclusive(tmp_path):
        with pytest.raises(ValueError):h.inspect(None,'p')
