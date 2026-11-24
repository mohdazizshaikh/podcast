import pytest
from pathlib import Path
from podcast_gpt import production_overview as o,projects,web,cli,v4_progress,v4_master
from test_v4_preview import fixture


def test_eta_scope_and_distinct_observations():
    rows=[{"id":f"000{i}-01","start_frame":0,"end_frame":32000} for i in range(1,7)]
    done={r["id"]:{} for r in rows[:4]}
    records=[{"scope":"x","action":"neural_batch","unit":f"000{i}-01","seconds":s,"utc":str(i)} for i,s in [(2,10),(3,20),(4,30)]]
    assert not o.estimate_from_records(rows,done,["0001-01"],records[:2],"x","batch")["estimate_available"]
    assert not o.estimate_from_records(rows,done,["0001-01"],records,"other","batch")["estimate_available"]
    eta=o.estimate_from_records(rows,done,["0001-01"],records,"x","batch")
    assert eta["matching_completed_observations"]==3 and eta["remaining_chunks"]==2
    assert eta["estimated_seconds"]==40 and eta["observed_rate_range_seconds"]==[20,60]
    assert not eta["live_eta_available"]


def test_master_manifest_and_lock(tmp_path,monkeypatch):
    root,pid=fixture(tmp_path,monkeypatch)
    result=o.media_check(root,pid,"master")
    path=Path(result["local_path"])
    assert path.is_file() and result["bytes"]==path.stat().st_size
    assert result["sha256"]==v4_master.inspect(root,pid)["master"]["wav_sha256"]
    assert not result["http_media_served"] and not result["publication_approved"]
    with pytest.raises(ValueError,match="Unknown"):o.media_check(root,pid,"../../secret")
    with projects.exclusive(projects.project(root,pid)):
        with pytest.raises(ValueError,match="lock"):o.media_check(root,pid,"master")


def test_dashboard_and_initial_overview(tmp_path):
    root=tmp_path/"private"
    req={"topic":"Science","language":"Hindi","duration_minutes":1,"presenters":["A"],"video_format":"square",
         "workflow":"manual","input_kind":"topic","research_mode":"knowledge"}
    pid=projects.create(root,req)["project_id"]
    result=o.inspect(root,pid)
    assert result["readiness"]["stage"]=="outline_required" and not result["neural_estimate"]["estimate_available"]
    assert result["timing"]["completed_observations"]==0 and result["read_only"]
    html=web.html_page("test")
    assert "v4Player" in html and "crypto.subtle.digest" in html and "media-src blob:" in html
    assert cli.parse(["doctor"]).operation=="doctor"
    assert cli.parse(["project-media-check","--project-id",pid,"--kind","master"]).operation=="project-media-check"
