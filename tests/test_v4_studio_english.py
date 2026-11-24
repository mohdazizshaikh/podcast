import io
import shutil
import sys
from types import SimpleNamespace
import pytest
from PIL import Image
from podcast_gpt import kokoro_languages as langs, dependency_setup as deps, studio_preview as studio
from podcast_gpt import portrait_brief, characters, v4_audio as audio, v4_preview as preview, cli
from test_v4_preview import fixture,approve


def test_english_frontend_and_catalog(monkeypatch):
    assert langs.language("English")=="en-us"
    assert langs.preset({"engine":"kokoro","language":"British English","preset":"bm_george"},"en-gb")=="bm_george"
    with pytest.raises(ValueError):langs.preset({"engine":"kokoro","language":"British English","preset":"af_heart"},"en-gb")
    calls=[]
    def g2p(**kwargs):calls.append(kwargs);return "g2p"
    monkeypatch.setitem(sys.modules,"kokoro_onnx",SimpleNamespace(Kokoro=lambda *a:"engine"))
    monkeypatch.setitem(sys.modules,"misaki",SimpleNamespace(en=SimpleNamespace(G2P=g2p),espeak=SimpleNamespace(EspeakFallback=lambda **kw:kw)))
    assert langs.engine("model","voices","en-gb")==("engine","g2p")
    assert calls==[{"trf":False,"british":True,"fallback":{"british":True}}]
    assert "misaki[en]>=0.9,<1" in deps.GROUPS["kokoro-english"]
    assert cli.parse(["doctor"]).operation=="doctor"


def test_studio_grid_all_sizes():
    data=io.BytesIO();Image.new("RGB",(200,200),"red").save(data,"PNG")
    portraits={i:data.getvalue() for i in range(1,11)}
    for size in preview.SIZES.values():
        for layout in studio.LAYOUTS:
            assert studio.card(portraits,10,size,layout).size==size


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"),reason="FFmpeg required")
def test_studio_preview_and_original_preservation(tmp_path,monkeypatch):
    root,pid=fixture(tmp_path,monkeypatch);approve(root,pid)
    cast=characters.read_cast(root,pid)
    brief=portrait_brief.create(root,cast["cast"][0]["character_id"])
    assert not brief["image_generated"] and "Fictional" in brief["prompt"]
    bg=tmp_path/"background.png";Image.new("RGB",(400,400),"navy").save(bg)
    with pytest.raises(ValueError,match="acknowledgment"):studio.configure(root,pid,layout="grid",background=bg)
    settings=studio.configure(root,pid,layout="grid",background=bg,acknowledgment=studio.ACK)
    assert settings["static_only"]
    with pytest.raises(ValueError,match="overwrite"):studio.configure(root,pid,layout="focus")
    base=preview.render(root,pid)
    result=studio.render(root,pid)
    assert result==studio.inspect(root,pid)
    assert not result["studio"]["neural_lipsync_verified"]
    assert preview.inspect(root,pid)==base
    path=audio._context(root,pid)[1]/studio.FOLDER/studio.SRT
    path.write_text("changed",encoding="utf-8")
    with pytest.raises(ValueError,match="subtitles"):studio.inspect(root,pid)
