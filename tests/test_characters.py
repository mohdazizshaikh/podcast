import json
from pathlib import Path
import pytest
from PIL import Image
from podcast_gpt import characters as ch, projects, source, cli, script_review


def profile(name):
    return {"name":name,"personality":"Curious, analytical","speaking_style":"Conversational",
            "appearance":"Fictional adult presenter in a studio","voice_preferences":{"engine":"undecided","language":"Hindi","preset":"","style_notes":"Warm"}}


def req():
    return {"topic":"Science","language":"Hindi","duration_minutes":1,"presenters":["A","B"],
            "video_format":"vertical","workflow":"manual","input_kind":"topic","research_mode":"knowledge"}


def png(path,color):
    Image.new("RGB",(200,200),color).save(path)
    return path


def test_reusable_cast_and_portrait_integrity(tmp_path):
    root=tmp_path/"private"
    assert ch.list_characters(root)=={"characters":[],"blocked":[]}
    a=png(tmp_path/"a.png","red");b=png(tmp_path/"b.png","blue")
    with pytest.raises(ValueError,match="acknowledgment"):ch.create(root,profile("A"),portrait=a)
    ca=ch.create(root,profile("A"),portrait=a,acknowledgment=ch.ACK)["character_id"]
    cb=ch.create(root,profile("B"),portrait=b,acknowledgment=ch.ACK)["character_id"]
    assert len(ch.list_characters(root)["characters"])==2
    pid=projects.create(root,req())["project_id"]
    assert not ch.status(root,pid)["cast_assigned"]
    with pytest.raises(ValueError,match="exactly"):ch.assign(root,pid,{"A":ca})
    with pytest.raises(ValueError,match="distinct"):ch.assign(root,pid,{"A":ca,"B":ca})
    result=ch.assign(root,pid,{"A":ca,"B":cb})
    assert result["all_portraits_present"] and not result["character_media_ready"]
    assert projects.inspect(root,pid)["cast"]["cast_sha256"]==result["cast_sha256"]
    with pytest.raises(ValueError,match="already assigned"):ch.assign(root,pid,{"A":cb,"B":ca})
    revised=ch.create(root,profile("A revised"),parent_id=ca)["character_id"]
    assert ch.read(root,revised)["parent_id"]==ca
    assert ch.status(root,pid)["presenters"][0]["character_id"]==ca
    pid2=projects.create(root,req())["project_id"]
    assert ch.assign(root,pid2,{"A":ca,"B":cb})["cast_sha256"]==result["cast_sha256"]
    portrait=ch._profile_folder(root,ca)/ch.PORTRAIT
    png(portrait,"green")
    with pytest.raises(ValueError,match="hash"):ch.status(root,pid)
    assert ca in ch.list_characters(root)["blocked"]


def test_media_gate_requires_review_and_distinct_images(tmp_path,monkeypatch):
    root=tmp_path/"private"
    p=png(tmp_path/"p.png","red");q=png(tmp_path/"q.png","blue")
    a=ch.create(root,profile("A"),portrait=p,acknowledgment=ch.ACK)["character_id"]
    b=ch.create(root,profile("B"),portrait=q,acknowledgment=ch.ACK)["character_id"]
    pid=projects.create(root,req())["project_id"]
    ch.assign(root,pid,{"A":a,"B":b})
    with pytest.raises(ValueError):ch.prepare_media_binding(root,pid)
    def reviewed(root,pid,*,require_pass):
        assert require_pass is True
        return {"version_sha256":"a"*64,"turns":[{"id":"0001"}]}
    monkeypatch.setattr(script_review,"current_script",reviewed)
    result=ch.prepare_media_binding(root,pid)
    assert result["script_version_sha256"]=="a"*64 and not result["actual_media_generated"]
    duplicate=ch.create(root,profile("B clone"),portrait=p,acknowledgment=ch.ACK)["character_id"]
    pid2=projects.create(root,req())["project_id"];ch.assign(root,pid2,{"A":a,"B":duplicate})
    with pytest.raises(ValueError,match="distinct portrait"):ch.prepare_media_binding(root,pid2)


def test_cli_and_invalid_portrait(tmp_path):
    root=tmp_path/"private"
    path=tmp_path/"profile.json";path.write_text(json.dumps(profile("A")),encoding="utf-8")
    result=cli.execute(cli.parse(["--workspace",str(root),"character-create","--profile",str(path)]))
    assert result["portrait"] is None
    bad=tmp_path/"bad.png";bad.write_bytes(b"not PNG")
    with pytest.raises(ValueError,match="PNG"):ch.create(root,profile("B"),portrait=bad,acknowledgment=ch.ACK)
    small=tmp_path/"small.png";Image.new("RGB",(10,10)).save(small)
    with pytest.raises(ValueError,match="dimensions"):ch.create(root,profile("C"),portrait=small,acknowledgment=ch.ACK)
