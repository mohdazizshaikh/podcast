import json
import shutil
from pathlib import Path
import pytest
from podcast_gpt import cli, kokoro_languages as langs, v4_tts as tts, v4_audio as audio
from podcast_gpt import projects, research, research_discovery as discovery, fact_review as fact, script_review, source
from test_v4_master_tts import ready
from test_research import req,URLS,TEXTS,fetch


def test_language_catalog_and_mismatch():
    assert cli.parse(["doctor"]).operation=="doctor"
    assert langs.language("Brazilian Portuguese")=="pt-br"
    assert langs.preset({"engine":"kokoro","language":"Spanish","preset":"ef_dora"},"es")=="ef_dora"
    with pytest.raises(ValueError):langs.language("English")
    with pytest.raises(ValueError):langs.preset({"engine":"kokoro","language":"French","preset":"ef_dora"},"fr-fr")


@pytest.mark.skipif(not shutil.which("ffmpeg"),reason="FFmpeg required")
def test_spanish_generation_receipts(tmp_path,monkeypatch):
    root,pid=ready(tmp_path,monkeypatch,"kokoro",language="Spanish",presets=("ef_dora","em_alex"))
    model=tmp_path/"model.onnx";model.write_bytes(b"x"*1000000)
    voices=tmp_path/"voices.bin";voices.write_bytes(b"x"*1000)
    class Fake:
        def create(self,phonemes,*,voice,speed,is_phonemes):
            return [0.1 if voice=="ef_dora" else 0.2]*24000,24000
    opts={"model":model,"voices":voices,"run_local":True,"acknowledgment":tts.ACK,"engine_factory":lambda *a:(Fake(),lambda text:(text,None))}
    assert tts.generate(root,pid,**opts)["new_generated_turns"]==["0001"]
    assert tts.generate(root,pid,**opts)["generated_turns"]==2
    _,dest,binding,turns,_,_=audio._context(root,pid)
    items=audio._read_parts(dest,binding,turns)
    assert items["0001"]["origin"]=="local_kokoro_multilingual"
    assert items["0001"]["generation"]["language"]=="es"
    assert audio.finalize(root,pid)["timeline_finalized"]


def test_discovery_explicit_and_read_only(tmp_path):
    root=tmp_path/"private";pid=projects.create(root,req())["project_id"]
    calls=[]
    def mock(q,limit):
        calls.append(q)
        return {"pages":[{"key":"Plant","title":"Plant"},{"key":"File:bad","title":"Ignore"},{"key":"Plant","title":"duplicate"},{"key":"A/B","title":"A/B"}]}
    with pytest.raises(ValueError,match="Explicit"):discovery.discover(root,pid,fetcher=mock)
    assert not calls
    result=discovery.discover(root,pid,allow_web_search=True,fetcher=mock)
    assert [r["url"] for r in result["candidates"]]==["https://en.wikipedia.org/wiki/Plant","https://en.wikipedia.org/wiki/A%2FB"]
    assert not result["source_capture_performed"]
    assert not (projects.project(root,pid)/research.FILENAME).exists()


def test_fact_review_binding_and_correction(tmp_path,monkeypatch):
    root=tmp_path/"private";pid=projects.create(root,req())["project_id"]
    research.capture(root,pid,URLS,allow_web_fetch=True,fetcher=fetch)
    current={"version_sha256":"a"*64,"turns":[{"id":"0001","speaker":"Solo","text":"Trees absorb carbon dioxide.","citations":[{"source_id":"S01","quote":TEXTS[0]}]},
             {"id":"0002","speaker":"Solo","text":"Let's discuss plants.","citations":[]}]}
    monkeypatch.setattr(script_review,"current_script",lambda *a,**k:current)
    path=Path(fact.create(root,pid)["template_path"])
    with pytest.raises(ValueError,match="Complete"):fact.record(root,pid,acknowledgment=fact.ACK)
    data=source.read_json(path)
    data["turns"]["0001"].update(decision="NEEDS_CORRECTION",note="Check the relevant source context again.")
    data["turns"]["0002"].update(decision="NO_FACTUAL_CLAIM",note="Only a conversational transition.")
    path.write_text(json.dumps(data),encoding="utf-8")
    result=fact.record(root,pid,acknowledgment=fact.ACK)
    assert result["review_status"]=="NEEDS_CORRECTION" and result["correction_turn_ids"]==["0001"]
    with pytest.raises(ValueError,match="Immutable"):fact.record(root,pid,acknowledgment=fact.ACK)
    current["version_sha256"]="b"*64
    assert fact.inspect(root,pid)["review_status"]=="UNREVIEWED"
