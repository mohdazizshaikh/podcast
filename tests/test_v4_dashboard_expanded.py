import io
import sys
from types import SimpleNamespace
import pytest
from PIL import Image
from podcast_gpt import dashboard_authoring as a,dashboard_cloud as cloud,credentials,projects,characters,continuity
from podcast_gpt import studio_preview as studio,v4_audio as audio,kokoro_languages as langs,v4_readiness,web
from test_v4_master_tts import ready,wav
from test_v4_dashboard_actions import request


def test_cloud_consent_and_only_one_action(tmp_path,monkeypatch):
    root=tmp_path/"private";pid=projects.create(root,request())["project_id"]
    data={"project_id":pid,"cloud_consent":True,"confirm_gemini_free_project":False}
    calls=[]
    monkeypatch.setattr(credentials,"resolve",lambda *args,**kw:(calls.append(kw) or "opaque"))
    monkeypatch.setattr(projects,"generate_outline",lambda *args,**kw:{"provider":"openrouter"})
    with pytest.raises(ValueError,match="consent"):a.run(root,"cloud-draft",data)
    with pytest.raises(ValueError,match="consent"):a.run(root,"cloud-draft",{**data,"cloud_consent":False},acknowledgment=a.ACK)
    assert not calls
    result=a.run(root,"cloud-draft",data,acknowledgment=a.ACK)
    assert calls==[{"pid":pid,"providers":("openrouter",)}]
    assert not result["paid_fallback_enabled"] and not result["cloud_consent_persisted"]
    monkeypatch.setattr(continuity,"read",lambda *args:{"snapshot":"present"})
    with pytest.raises(ValueError,match="local drafting"):a.run(root,"cloud-draft",data,acknowledgment=a.ACK)
    assert len(calls)==1


def test_new_uploads_and_continuity(tmp_path,monkeypatch):
    root,pid=ready(tmp_path,monkeypatch)
    opts={"acknowledgment":a.ACK}
    raw=wav(tmp_path/"turn.wav",123).read_bytes()
    with pytest.raises(ValueError):a.upload(root,"audio-turn",pid,"turn.wav",raw,unit="0001",**opts)
    a.upload(root,"audio-turn",pid,"turn.wav",raw,unit="0001",rights=True,**opts)
    assert audio.inspect(root,pid)["completed_audio_turns"]==1
    buf=io.BytesIO();Image.new("RGB",(256,256),"navy").save(buf,"PNG")
    with pytest.raises(ValueError):a.upload(root,"studio-background",pid,"bg.png",buf.getvalue(),layout="grid",**opts)
    result=a.upload(root,"studio-background",pid,"bg.png",buf.getvalue(),layout="grid",rights=True,**opts)
    assert result["settings"]["layout"]=="grid"
    assert a.run(root,"studio-status",{"project_id":pid})==result
    new=projects.create(root,{**projects.load(root,pid),"topic":"Next"})["project_id"]
    characters.assign(root,new,{r["speaker"]:r["character_id"] for r in characters.read_cast(root,pid)["cast"]})
    data={"project_id":new,"prior_project_id":pid,"turn_ids":["0001"],"local_only_consent":True}
    assert a.run(root,"continuity-enable",data,**opts)["enabled"]
    assert a.run(root,"continuity-status",{"project_id":new})["enabled"]
    assert not list(projects.base(root).glob("dashboard-input-*"))


def test_mandarin_frontend_contract(monkeypatch):
    calls=[]
    monkeypatch.setitem(sys.modules,"kokoro_onnx",SimpleNamespace(Kokoro=lambda *a:"engine"))
    monkeypatch.setitem(sys.modules,"misaki",SimpleNamespace(zh=SimpleNamespace(ZHG2P=lambda **kw:(calls.append(kw) or "g2p"))))
    assert langs.engine("model","voices","zh")==("engine","g2p")
    assert calls==[{"version":None}]
    assert langs.language("Mandarin Chinese")=="zh"
    assert "v4TurnImport" in web.html_page("test") and "v4CloudDraft" in web.html_page("test")


def test_session_key_hidden_input_failure(monkeypatch):
    import getpass,warnings
    def warn(*args):warnings.warn("not hidden",getpass.GetPassWarning)
    monkeypatch.setattr(getpass,"getpass",warn)
    with pytest.raises(ValueError,match="hidden"):credentials.prompt_key("openrouter")
