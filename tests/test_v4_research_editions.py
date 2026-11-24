import pytest
from podcast_gpt import research_discovery as d,research_coverage as c,projects,research,script_review,cli,web
from test_research import req,URLS,TEXTS,fetch


@pytest.mark.parametrize("edition",d.EDITIONS)
def test_edition_routes(tmp_path,edition):
    root=tmp_path/"private";pid=projects.create(root,req())["project_id"]
    report=d.discover(root,pid,edition=edition,allow_web_search=True,fetcher=lambda *a:{"pages":[{"title":"Plant","key":"Plant"}]})
    assert report["edition"]==edition and report["candidates"][0]["url"]=="https://"+edition+".wikipedia.org/wiki/Plant"
    assert not report["source_capture_performed"]


@pytest.mark.parametrize("edition",["","EN","en.wikipedia.org","../en","https://example.org","en@evil.com",None,1,[],{}])
def test_edition_rejects_arbitrary_host(edition):
    with pytest.raises(ValueError,match="allowlisted"):d._host(edition)


def test_coverage_only_exact_excerpts(tmp_path,monkeypatch):
    root=tmp_path/"private";pid=projects.create(root,req())["project_id"]
    research.capture(root,pid,URLS,allow_web_fetch=True,fetcher=fetch)
    current={"version_sha256":"a"*64,"turns":[
        {"id":"0001","speaker":"Solo","text":"First","citations":[{"source_id":"S01","quote":TEXTS[0]}]},
        {"id":"0002","speaker":"Solo","text":"Second","citations":[]},
        {"id":"0003","speaker":"Solo","text":"Third","citations":[{"source_id":"S01","quote":TEXTS[0]},{"source_id":"S02","quote":TEXTS[1]}]}]}
    monkeypatch.setattr(script_review,"current_script",lambda *a,**k:current)
    result=c.inspect(root,pid)
    assert result["cited_turn_count"]==2 and result["uncited_turn_ids"]==["0002"]
    assert result["source_usage"][0]["cited_turn_count"]==2
    assert not result["independent_corroboration_verified"]
    current["turns"][0]["citations"][0]["quote"]="fabricated source quotation"
    with pytest.raises(ValueError):c.inspect(root,pid)
    assert cli.parse(["project-research-coverage","--project-id",pid]).operation=="project-research-coverage"
    assert "v4ResearchEdition" in web.html_page("test")
