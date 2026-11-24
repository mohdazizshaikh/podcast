import pytest
from PIL import Image
from pathlib import Path
from podcast_gpt import portrait_local as p,projects,characters,source,cli
from test_v4_master_tts import ready
from test_v4_portrait_local import model


def valid():
    return {"profile_sha256":"a"*64,"brief_sha256":"b"*64,"portrait_sha256":"c"*64,
            "seed":42,"steps":20,"elapsed_seconds":1.0,
            "model":{"model_sha256":"d"*64,"file_count":5,"total_bytes":100}}


@pytest.mark.parametrize("patch",[
    {"profile_sha256":"bad"},{"brief_sha256":None},{"portrait_sha256":"z"*64},
    {"seed":True},{"seed":2**32},{"steps":9},{"steps":31},{"elapsed_seconds":-1},
    {"elapsed_seconds":float("nan")},{"elapsed_seconds":float("inf")},{"model":[]},
    {"model":{"model_sha256":"a"*64,"file_count":0,"total_bytes":1}},
    {"model":{"model_sha256":"a"*64,"file_count":5,"total_bytes":17*p.GIB}}])
def test_invalid_provenance(patch):
    with pytest.raises(ValueError):p.validate_provenance({**valid(),**patch})


@pytest.mark.parametrize("limit",[0,201,True,None,"50"])
def test_invalid_list_limit(limit):
    with pytest.raises(ValueError,match="1–200"):p.list_candidates(None,limit=limit)


def test_list_isolates_incomplete_attempts(tmp_path,monkeypatch):
    root,pid=ready(tmp_path,monkeypatch);cid=characters.read_cast(root,pid)["cast"][0]["character_id"]
    assert p.list_candidates(root)["attempts"]==[]
    m=model(tmp_path)
    monkeypatch.setattr(p.hardware,"memory_bytes",lambda:(16*p.GIB,12*p.GIB))
    monkeypatch.setattr(p.shutil,"disk_usage",lambda x:type("D",(),{"free":10*p.GIB})())
    result=p.generate(root,cid,model=m,acknowledgment=p.ACK,renderer=lambda *a:Image.new("RGB",(512,512),"blue"))
    parent=projects.base(root)/p.FOLDER
    (parent/("0"*32)).mkdir()
    rows=p.list_candidates(root)["attempts"]
    assert {row["status"] for row in rows}=={"fixture_only","incomplete_or_invalid"}
    assert p.list_candidates(root,limit=1)["truncated"]
    assert p.validate_provenance(valid())==valid()
    assert cli.parse(["character-portrait-candidates"]).operation=="character-portrait-candidates"
