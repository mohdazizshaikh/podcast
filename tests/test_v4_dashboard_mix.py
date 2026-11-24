import base64
import pytest
from podcast_gpt import dashboard_mix as dm,v4_post_audio as mix,projects,web
from test_v4_preview import fixture
from test_v4_master_tts import wav


def data(pid):
    return {"project_id":pid,"assets":{},"speech_peak":22000,"bed_peak":3000,"duck_percent":0,
            "target_lufs":None,"compress_ratio":4,"compress_threshold":8000,"rights":True}


def test_mix_upload_and_audit(tmp_path,monkeypatch):
    root,pid=fixture(tmp_path,monkeypatch);req=data(pid)
    req["assets"]["bed"]=base64.b64encode(wav(tmp_path/"bed.wav",500).read_bytes()).decode("ascii")
    result=dm.run(root,{**req,"duck_percent":70},acknowledgment=dm.ACK)
    assert result==mix.inspect(root,pid)
    assert result["mix"]["total_frames"]==36000
    assert result["mix"]["settings"]["compressor"]["ratio"]==4
    with pytest.raises(ValueError,match="overwrite"):dm.run(root,req,acknowledgment=dm.ACK)
    assert not list(projects.base(root).glob("dashboard-mix-*"))


@pytest.mark.parametrize("change",[
    {"rights":False},{"rights":1},{"assets":{"../../x":"abc"}},
    {"assets":{"bed":"%%"}},{"assets":{"bed":1}},{"assets":[]},
    {"duck_percent":70},{"compress_ratio":0},{"target_lufs":-5},
    {"speech_peak":True},{"bed_peak":6001},{"extra":True}])
def test_invalid_mix_requests(tmp_path,monkeypatch,change):
    root,pid=fixture(tmp_path,monkeypatch)
    with pytest.raises(ValueError):dm.run(root,{**data(pid),**change},acknowledgment=dm.ACK)


@pytest.mark.parametrize("raw",[b"",b"[]",b"null",b"\xff",b"x"*8500001])
def test_invalid_body(raw):
    with pytest.raises(ValueError):dm.parse(raw)


def test_consent_and_markup():
    with pytest.raises(ValueError,match="consent"):dm.run(None,{},acknowledgment="YES")
    assert "v4MixCompose" in web.html_page("test")
