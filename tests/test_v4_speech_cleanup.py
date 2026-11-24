import math
import struct
import wave
import pytest
from podcast_gpt import speech_cleanup as c,v4_post_audio as mix,v4_master as master,v4_audio as audio,cli,web
from test_v4_master_tts import ready


@pytest.mark.parametrize("samples,expected",[
    ([101,99],[1,-1]),([-101,-99],[-1,1]),([0,0],[0,0]),
    ([-32768,32767],[-32768,32767]),([1,2,3],[-1,0,1])])
def test_dc_correction(samples,expected):
    assert list(c.centered(samples))==expected


@pytest.mark.parametrize("dc,threshold",[(1,0),("yes",0),(False,-1),(True,1001),(True,True),(False,1.5)])
def test_invalid_settings(dc,threshold):
    with pytest.raises(ValueError):c.settings(dc,threshold)


def test_gate_and_legacy():
    assert c.settings(False,0) is None
    with pytest.raises(ValueError,match="erase"):c.centered([100,100])
    env=0;level=10000
    for _ in range(3000):
        output,env,level=c.step(100,env,level,500)
    assert output==20 and level==2000
    for _ in range(200):
        output,env,level=c.step(-1000,env,level,500)
    assert output==-1000 and level==10000
    assert mix._settings(22000,3000)=={"speech_peak":22000,"bed_peak":3000,"mix_algorithm":"integer_peak_v1"}


def test_cleanup_mix_exact_audit(tmp_path,monkeypatch):
    root,pid=ready(tmp_path,monkeypatch)
    for tid,hz in (("0001",440),("0002",660)):
        path=tmp_path/(tid+".wav")
        with wave.open(str(path),"wb") as w:
            w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000)
            w.writeframes(b"".join(struct.pack("<h",2000+round(1000*math.sin(2*math.pi*hz*i/16000))) for i in range(16000)))
        audio.import_turn(root,pid,tid,path,acknowledgment=audio.ACK)
    audio.finalize(root,pid);master.compose(root,pid)
    before=master.inspect(root,pid)
    result=mix.compose(root,pid,remove_dc=True,gate_threshold=500,compress_ratio=3,acknowledgment=mix.ACK)
    assert result==mix.inspect(root,pid) and master.inspect(root,pid)==before
    assert result["mix"]["settings"]["cleanup"]==c.settings(True,500)
    assert result["mix"]["total_frames"]==36000
    assert "v4MixDc" in web.html_page("test")
    assert cli.parse(["doctor"]).operation=="doctor"
