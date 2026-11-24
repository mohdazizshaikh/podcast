import io
import json
import zipfile
import pytest
from PIL import Image
from podcast_gpt import dashboard_authoring as d, projects, characters, ingestion, web, cli, model_config


def profile():
    return {"name":"A","personality":"Curious","speaking_style":"Clear","appearance":"Fictional adult",
            "voice_preferences":{"engine":"imported","language":"Hindi","preset":"","style_notes":""}}


def request(kind="topic"):
    return {"topic":"Science","language":"Hindi","duration_minutes":1,"presenters":["A"],
            "video_format":"square","workflow":"manual","input_kind":kind,"research_mode":"knowledge"}


def test_author_character_and_cast(tmp_path):
    root=tmp_path/"private";pid=projects.create(root,request())["project_id"]
    data={"profile":profile(),"parent_id":None}
    with pytest.raises(ValueError,match="consent"):d.run(root,"character-create",data)
    old=d.run(root,"character-create",data,acknowledgment=d.ACK)
    buf=io.BytesIO();Image.new("RGB",(256,256),"blue").save(buf,"PNG")
    opts={"acknowledgment":d.ACK}
    with pytest.raises(ValueError,match="rights"):d.upload(root,"portrait",old["character_id"],"portrait.png",buf.getvalue(),**opts)
    new=d.upload(root,"portrait",old["character_id"],"portrait.png",buf.getvalue(),rights=True,**opts)
    assert new["parent_id"]==old["character_id"] and characters.read(root,old["character_id"])["portrait"] is None
    choices=d.run(root,"cast-choices",{"project_id":pid})
    assert len(choices["characters"])==2
    assigned=d.run(root,"cast-assign",{"project_id":pid,"mapping":{"A":new["character_id"]}},**opts)
    assert assigned["all_portraits_present"]
    with pytest.raises(ValueError,match="already assigned"):d.run(root,"cast-assign",{"project_id":pid,"mapping":{"A":old["character_id"]}},**opts)


def test_source_upload_and_model_paths(tmp_path,monkeypatch):
    root=tmp_path/"private";pid=projects.create(root,request("document"))["project_id"]
    opts={"acknowledgment":d.ACK}
    with pytest.raises(ValueError):d.upload(root,"source",pid,"../bad.txt",b"text",**opts)
    with pytest.raises(ValueError,match="extension"):d.upload(root,"source",pid,"test.pdf",b"text",**opts)
    result=d.upload(root,"source",pid,"text.txt",b"Example trusted document",**opts)
    assert result["stage"]=="source_imported"
    with pytest.raises(ValueError,match="overwritten"):d.upload(root,"source",pid,"text.txt",b"other",**opts)
    exe=tmp_path/"espeak.exe";exe.write_bytes(b"not executed")
    data={"engine":"espeak","paths":{"executable":str(exe)},"replace":False}
    assert d.run(root,"model-configure",data,**opts)["configured"]
    assert model_config.read(root,"espeak")["executable"]==exe
    with pytest.raises(ValueError,match="replace"):d.run(root,"model-configure",data,**opts)
    for path in ("relative.exe",r"\\server\share\file.exe"):
        with pytest.raises(ValueError,match="absolute local"):d.run(root,"model-configure",{**data,"paths":{"executable":path}},**opts)
    with pytest.raises(ValueError,match="consent"):d.run(root,"source-url",{"project_id":pid,"url":"https://example.org","allow_web_fetch":False},**opts)
    assert not list(projects.base(root).glob("dashboard-input-*"))


def test_docx_unsafe_encoding_and_dashboard():
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w") as z:z.writestr("word/document.xml",'<!DOCTYPE x [<!ENTITY a "bad">]><x>&a;</x>'.encode("utf-16"))
    with pytest.raises(ValueError,match="UTF-8"):ingestion._docx(b.getvalue())
    assert "v4PortraitAttach" in web.html_page("test") and "v4ModelSave" in web.html_page("test")
    assert cli.parse(["doctor"]).operation=="doctor"
    with pytest.raises(ValueError):d.parse(b"[]")
