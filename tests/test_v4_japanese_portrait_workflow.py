import json
from pathlib import Path
import pytest
from PIL import Image
from podcast_gpt import japanese_resources as j,kokoro_languages as langs,portrait_local as p,dashboard_portrait as worker
from podcast_gpt import dashboard_authoring as author,characters,source,cli,web
from test_v4_portrait_local import model
from test_v4_master_tts import ready


@pytest.mark.parametrize("alias",["Japanese","ja","ja-JP","日本語"," JAPANESE "])
def test_japanese_alias(alias):
    assert langs.language(alias)=="ja"


@pytest.mark.parametrize("missing",[None,*j.REQUIRED])
@pytest.mark.parametrize("empty",[False,True])
def test_dictionary_file_gate(tmp_path,missing,empty):
    dic=tmp_path/"dic";dic.mkdir()
    for name in j.REQUIRED:
        if name==missing:
            if empty:(dic/name).write_bytes(b"")
        else:(dic/name).write_bytes(b"fixture")
    assert j.dictionary(dic)==(missing is None)


@pytest.mark.parametrize("path",[None,"","relative",r"\\host\share","//host/share"])
def test_invalid_dictionary_path(path):
    assert not j.dictionary(path)


def test_resource_missing_blocks_frontend(monkeypatch):
    monkeypatch.setattr(j,"inspect",lambda:{"packages":{name:None for name in j.PACKAGES},"unidic_dictionary_files_present":False,"open_jtalk_dictionary_files_present":False})
    with pytest.raises(ValueError,match="prepare resources"):j.require()
    assert cli.parse(["japanese-resource-status"]).operation=="japanese-resource-status"
    assert cli.parse(["dependency-plan","--group","kokoro-japanese"]).operation=="dependency-plan"


@pytest.mark.parametrize("seed,steps",[(True,20),(-1,20),(2**32,20),(42,9),(42,31),(42,True)])
def test_worker_invalid_options(seed,steps):
    with pytest.raises(ValueError,match="seed"):worker.generate(None,None,None,seed,steps,acknowledgment=worker.ACK)


def test_candidate_audit_and_fixture_block(tmp_path,monkeypatch):
    root,pid=ready(tmp_path,monkeypatch);cid=characters.read_cast(root,pid)["cast"][0]["character_id"]
    m=model(tmp_path)
    monkeypatch.setattr(p.hardware,"memory_bytes",lambda:(16*p.GIB,12*p.GIB))
    monkeypatch.setattr(p.shutil,"disk_usage",lambda x:type("D",(),{"free":10*p.GIB})())
    result=p.generate(root,cid,model=m,acknowledgment=p.ACK,renderer=lambda *a:Image.new("RGB",(512,512),"blue"))
    candidate=result["candidate_id"]
    assert p.audit_candidate(root,candidate)["candidate_integrity_checked"]
    with pytest.raises(ValueError,match="Synthetic"):p.attach_candidate(root,candidate,acknowledgment=characters.ACK)
    Path(result["path"]).write_bytes(b"invalid")
    with pytest.raises(ValueError):p.audit_candidate(root,candidate)


@pytest.mark.parametrize("cid",["", "../x","a"*31,"A"*32,None,1,[],{}])
def test_invalid_candidate_id(cid):
    with pytest.raises(ValueError,match="candidate ID"):p.audit_candidate(None,cid)


def test_dashboard_controls_and_consent():
    with pytest.raises(ValueError,match="consent"):author.run(None,"portrait-generate",{})
    with pytest.raises(ValueError,match="consent"):worker.generate(None,None,None,42,20,acknowledgment=None)
    assert "v4PortraitGenerate" in web.html_page("test")
