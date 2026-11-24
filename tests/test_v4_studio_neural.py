import json
from pathlib import Path
import pytest
from PIL import Image
from podcast_gpt import characters,portrait_brief,studio_preview as studio,studio_neural as sn,projects,source
from podcast_gpt import v4_partial_recovery as recovery,v4_audio as audio,cli
from test_v4_preview import fixture,approve


def test_geometry():
    for size in ((1280,720),(720,1280),(720,720)):
        for n in (1,3,10):
            for layout in studio.LAYOUTS:
                rect=studio.active_rect(range(1,n+1),n,size,layout)
                x,y,w,h=rect
                assert all(v%2==0 for v in rect) and min(w,h)>0 and x+w<=size[0] and y+h<=size[1]
    assert cli.parse(["doctor"]).operation=="doctor"


def test_attach_immutable_profile(tmp_path,monkeypatch):
    root,pid=fixture(tmp_path,monkeypatch)
    cast=characters.read_cast(root,pid);cid=cast["cast"][0]["character_id"]
    old=characters.read(root,cid)
    new=tmp_path/"new.png";Image.new("RGB",(256,256),"yellow").save(new)
    with pytest.raises(ValueError,match="acknowledgment"):portrait_brief.attach(root,cid,portrait=new,acknowledgment="YES")
    result=portrait_brief.attach(root,cid,portrait=new,acknowledgment=characters.ACK)
    assert result["parent_id"]==cid and result["profile"]==old["profile"]
    assert characters.read(root,cid)==old and characters.read_cast(root,pid)==cast
    assert result["character_id"]!=cid


def test_static_studio_recovery(tmp_path,monkeypatch):
    root,pid=fixture(tmp_path,monkeypatch);approve(root,pid)
    studio.configure(root,pid,layout="focus")
    dest=audio._context(root,pid)[1];out=dest/studio.FOLDER;out.mkdir()
    (out/studio.VIDEO).write_bytes(b"interrupted")
    assert recovery.inspect(root,pid,"studio-preview")["eligible"]
    result=recovery.archive(root,pid,"studio-preview",acknowledgment=recovery.ACK)
    assert not out.exists()
    assert (Path(result["archive_path"])/"attempt"/studio.VIDEO).read_bytes()==b"interrupted"


def test_studio_review_is_separate(tmp_path,monkeypatch):
    root,pid=fixture(tmp_path,monkeypatch)
    folder=projects.project(root,pid);dest=audio._context(root,pid)[1]
    receipt={"video_sha256":"a"*64};turns=[{"id":"0001"}]
    monkeypatch.setattr(sn,"_qa_context",lambda *a:(folder,dest,receipt,turns))
    p=Path(sn.qa(root,pid,"template")["template_path"])
    with pytest.raises(ValueError,match="UNREVIEWED"):sn.qa(root,pid,"record",acknowledgment=sn.ACK)
    data=source.read_json(p)
    for row in [data["criteria"],*data["turns"].values()]:
        for k in row:row[k]="PASS"
    p.write_text(json.dumps(data),encoding="utf-8")
    assert sn.qa(root,pid,"record",acknowledgment=sn.ACK)["human_video_self_attested_pass"]
    assert not (dest/"final-video-review.json").exists()
    receipt["video_sha256"]="b"*64
    with pytest.raises(ValueError,match="stale"):sn.qa(root,pid,"status")
