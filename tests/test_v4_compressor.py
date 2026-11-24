import pytest
from podcast_gpt import speech_compressor as c,v4_post_audio as mix,v4_master as master,cli
from test_v4_preview import fixture
from test_v4_master_tts import wav


@pytest.mark.parametrize("ratio",range(2,7))
@pytest.mark.parametrize("threshold",[2000,6000,12000,16000,20000])
@pytest.mark.parametrize("sample",[-24000,-1000,0,1000,24000])
def test_compression_sign_and_bounds(ratio,threshold,sample):
    cfg=c.settings(ratio,threshold)
    value,env=c.step(sample,0,cfg)
    assert abs(value)<=abs(sample) and env==abs(sample)
    if abs(sample)<=threshold:assert value==sample
    else:assert abs(value)==threshold+(abs(sample)-threshold)//ratio
    if sample:assert value*sample>=0


@pytest.mark.parametrize("ratio,threshold",[(0,12000),(7,12000),(True,12000),(2,1999),(2,20001),(1,2000),(2,False),(2,12000.0)])
def test_invalid_settings(ratio,threshold):
    with pytest.raises(ValueError):c.settings(ratio,threshold)


def test_release_and_legacy():
    cfg=c.settings(4,8000);_,env=c.step(24000,0,cfg)
    for _ in range(1600):
        _,new=c.step(0,env,cfg);assert new<=env;env=new
    assert env<12000
    assert mix._settings(22000,3000)=={"speech_peak":22000,"bed_peak":3000,"mix_algorithm":"integer_peak_v1"}


def test_compressed_mix_audit(tmp_path,monkeypatch):
    root,pid=fixture(tmp_path,monkeypatch)
    original=master.inspect(root,pid)
    bed=wav(tmp_path/"bed.wav",500)
    result=mix.compose(root,pid,bed=bed,duck_percent=70,compress_ratio=4,compress_threshold=8000,acknowledgment=mix.ACK)
    assert result==mix.inspect(root,pid)
    assert result["mix"]["settings"]["compressor"]==c.settings(4,8000)
    assert result["mix"]["total_frames"]==36000 and master.inspect(root,pid)==original
    with pytest.raises(ValueError,match="overwrite"):mix.compose(root,pid,acknowledgment=mix.ACK)
    assert cli.parse(["doctor"]).operation=="doctor"
