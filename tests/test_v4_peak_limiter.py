import struct
import wave
import pytest
from podcast_gpt import peak_limiter as limiter, v4_post_audio as mix, cli, web
from test_v4_preview import fixture
from test_v4_dashboard_mix import data
from podcast_gpt import dashboard_mix as dm


@pytest.mark.parametrize('ceiling',[8000,10000,16000,22000,24000,28000])
@pytest.mark.parametrize('sample',[-32768,-30000,-8000,0,8000,30000,32767])
def test_bound_and_polarity(ceiling,sample):
    value,gain=limiter.step(sample,limiter.SCALE,limiter.settings(ceiling))
    assert abs(value)<=ceiling and abs(value)<=abs(sample)
    assert value*sample>=0 and 0<gain<=limiter.SCALE
    if abs(sample)<=ceiling:assert value==sample


@pytest.mark.parametrize('invalid',[True,False,None,-1,1,7999,28001,32768,8000.0,'8000',[],{}])
def test_invalid(invalid):
    with pytest.raises(ValueError):limiter.settings(invalid)


@pytest.mark.parametrize('ceiling',[8000,16000,28000])
def test_release(ceiling):
    cfg=limiter.settings(ceiling)
    _,gain=limiter.step(32767,limiter.SCALE,cfg)
    before=gain
    value,gain=limiter.step(1000,gain,cfg)
    assert before<gain<=limiter.SCALE and value<=1000
    for _ in range(limiter.RELEASE_FRAMES):_,gain=limiter.step(1000,gain,cfg)
    assert gain==limiter.SCALE


def encode(values):
    return b''.join(struct.pack('<h',x) for x in values)


def decode(raw):
    return [x[0] for x in struct.iter_unpack('<h',raw)]


def test_chunk_invariance_and_bypass():
    values=[32767,1000,-32768,2000]*500
    raw=encode(values)
    cfg=limiter.settings(16000)
    single=b''.join(limiter.blocks([raw],cfg,decode,encode))
    split=b''.join(limiter.blocks([raw[:6],raw[6:500],raw[500:]],cfg,decode,encode))
    assert single==split and len(single)==len(raw)
    assert b''.join(limiter.blocks([raw],limiter.settings(0),decode,encode))==raw


@pytest.mark.parametrize("ceiling",[8000,16000,28000])
def test_mix_audit(tmp_path,monkeypatch,ceiling):
    root,pid=fixture(tmp_path,monkeypatch)
    result=dm.run(root,{**data(pid),"remove_dc":False,"gate_threshold":0,"limiter_ceiling":ceiling},acknowledgment=dm.ACK)
    assert mix.inspect(root,pid)==result
    assert result["mix"]["settings"]["limiter"]==limiter.settings(ceiling)
    with wave.open(result["path"],"rb") as w:
        assert max(map(abs,mix._samples(w.readframes(w.getnframes()))))<=ceiling
    assert not result["mix"]["human_mix_quality_approved"]


def test_incompatible_static_gain():
    with pytest.raises(ValueError,match="cannot be combined"):
        mix.compose(None,None,limiter_ceiling=16000,target_lufs=-16,acknowledgment=mix.ACK)


def test_cli_and_browser_controls():
    args=cli.parse(["project-mix-compose","--project-id","a"*32,"--limiter-ceiling","16000"])
    assert args.limiter_ceiling==16000
    assert "v4MixLimiter" in web.html_page("test")
