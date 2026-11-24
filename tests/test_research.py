"""Offline research fixtures: no real web or AI requests."""
import json
import pytest
from podcast_gpt import research, projects, source, episode_plan, script_generation as sg, ai_providers as ai

URLS=["https://example.org/a","https://example.net/b"]
TEXTS=["Trees absorb carbon dioxide during photosynthesis.","Plants release oxygen as a product of photosynthesis."]

def fetch(url):
    return TEXTS[URLS.index(url)].encode(),"text/plain","utf-8"

def req():
    return {"topic":"Plants","language":"English","duration_minutes":1,"presenters":["Solo"],
            "video_format":"square","workflow":"manual","input_kind":"topic","research_mode":"web"}

def test_research_full_flow(tmp_path,monkeypatch):
    root=tmp_path/"private";pid=projects.create(root,req())["project_id"]
    with pytest.raises(ValueError,match="before planning"):projects.generate_outline(root,pid)
    with pytest.raises(ValueError,match="Explicit"):research.capture(root,pid,URLS,fetcher=fetch)
    result=research.capture(root,pid,URLS,allow_web_fetch=True,fetcher=fetch)
    assert result["source_count"]==2 and not result["independent_fact_check_verified"]
    assert projects.inspect(root,pid)["stage"]=="research_captured"
    with pytest.raises(ValueError,match="overwritten"):research.capture(root,pid,URLS,allow_web_fetch=True,fetcher=fetch)
    def plan(data,*,research_pack,**options):
        assert research_pack["sources"][0]["id"]=="S01"
        return {"provider":"ollama","result":{"title":"Plants","sections":[{"heading":"Science","minutes":1,"summary":"Discuss plants","presenters":["Solo"]}]}}
    monkeypatch.setattr(episode_plan,"plan",plan)
    projects.generate_outline(root,pid)
    def generate(prompt,validator,**kwargs):
        assert "S01" in prompt and TEXTS[0] in prompt
        return {"provider":"ollama","result":validator({"turns":[
            {"speaker":"Solo","text":"Trees absorb carbon dioxide when they photosynthesize.","estimated_seconds":30,"citations":[{"source_id":"S01","quote":TEXTS[0]}]},
            {"speaker":"Solo","text":"Plants also release oxygen during this process.","estimated_seconds":30,"citations":[{"source_id":"S02","quote":TEXTS[1]}]}]})}
    monkeypatch.setattr(ai,"generate_json",generate)
    assert sg.generate(root,pid)["completed_units"]==1
    sg.finalize(root,pid)
    script=sg.show(root,pid)["script"]
    assert script["turns"][0]["citations"][0]["source_id"]=="S01"
    assert "research_sha256" in script["binding"]
    assert not script["publication_approved"]
    p=projects.project(root,pid)/research.FILENAME
    saved=source.read_json(p);saved["pack"]["sources"][0]["evidence"]["text"]="changed"
    p.write_text(json.dumps(saved),encoding="utf-8")
    with pytest.raises(ValueError,match="hash"):sg.inspect(root,pid)


def test_reject_fabricated_citations_and_duplicate_sources(tmp_path):
    root=tmp_path/"private";pid=projects.create(root,req())["project_id"]
    with pytest.raises(ValueError,match="Duplicate"):
        research.capture(root,pid,URLS,allow_web_fetch=True,fetcher=lambda u:(b"Same source content","text/plain","utf-8"))
    assert not (projects.project(root,pid)/research.FILENAME).exists()
    research.capture(root,pid,URLS,allow_web_fetch=True,fetcher=fetch)
    pack=research.read_pack(projects.project(root,pid),req())
    assert research.validate_citations([{"source_id":"S01","quote":TEXTS[0]}],pack)
    for cite in ({"source_id":"S99","quote":TEXTS[0]},{"source_id":"S02","quote":TEXTS[0]},{"source_id":"S01","quote":"Fabricated exact quotation"}):
        with pytest.raises(ValueError):research.validate_citations([cite],pack)
    unit={"presenters":["Solo"],"minute_in_section":1,"planned_seconds":60}
    value={"turns":[{"speaker":"Solo","text":"This is a long synthetic dialogue sentence.","estimated_seconds":30,"citations":[]},
                    {"speaker":"Solo","text":"Another distinct synthetic dialogue sentence.","estimated_seconds":30,"citations":[]}]}
    with pytest.raises(ValueError,match="at least one"):sg.validate_dialogue(value,unit,research_pack=pack)
