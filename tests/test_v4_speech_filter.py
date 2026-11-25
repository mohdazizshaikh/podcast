import math
import pytest
from podcast_gpt import speech_filter as f

@pytest.mark.parametrize('high',[0,60,80,100,120])
@pytest.mark.parametrize('hum',[0,50,60])
@pytest.mark.parametrize('low',[0,4500,6000])
def test_matrix(high,hum,low):
    cfg=f.settings(high,hum,low)
    samples=[-32768,32767,0,1000,-2000]*100
    result=f.apply(samples,cfg)
    assert len(result)==len(samples) and result==f.apply(samples,cfg)
    assert max(map(abs,result))<131072
    assert not any(f.apply([0]*500,cfg))
    if cfg is None:assert result is samples

@pytest.mark.parametrize('values',[(True,0,0),(61,0,0),(0,True,0),(0,55,0),(0,0,True),(0,0,7000),(None,0,0),(60.0,0,0),(0,'50',0),(0,0,[])])
def test_invalid(values):
    with pytest.raises(ValueError):f.settings(*values)

def tone(hz):return [round(10000*math.sin(2*math.pi*hz*i/16000)) for i in range(64000)]
def rms(x):return math.sqrt(sum(v*v for v in x)/len(x))

@pytest.mark.parametrize('high',[60,80,100,120])
def test_rumble(high):
    x=tone(10);y=f.apply(x,f.settings(high,0,0))
    assert rms(y[32000:])<.05*rms(x[32000:])

@pytest.mark.parametrize('hum',[50,60])
def test_hum(hum):
    x=tone(hum);y=f.apply(x,f.settings(0,hum,0))
    assert rms(y[32000:])<.05*rms(x[32000:])

@pytest.mark.parametrize('low',[4500,6000])
def test_hiss_band(low):
    x=tone(7500);y=f.apply(x,f.settings(0,0,low))
    assert rms(y[32000:])<.1*rms(x[32000:])

@pytest.mark.parametrize('hum',[0,50,60])
def test_midband(hum):
    x=tone(1000);y=f.apply(x,f.settings(100,hum,4500))
    assert .95<rms(y[32000:])/rms(x[32000:])<1.05

@pytest.mark.parametrize('freqs',[(80,0,0),(0,50,0),(0,0,4500),(100,60,6000)])
def test_dashboard_mix_audit(tmp_path,monkeypatch,freqs):
    import wave
    from podcast_gpt import v4_post_audio as mix,dashboard_mix as dm
    from test_v4_preview import fixture
    from test_v4_dashboard_mix import data
    root,pid=fixture(tmp_path,monkeypatch)
    req={**data(pid),"remove_dc":False,"gate_threshold":0,"limiter_ceiling":0,
         **dict(zip(("highpass_hz","hum_hz","lowpass_hz"),freqs))}
    result=dm.run(root,req,acknowledgment=dm.ACK)
    assert mix.inspect(root,pid)==result
    assert result["mix"]["settings"]["speech_filter"]==f.settings(*freqs)
    with wave.open(result["path"],"rb") as w:assert w.getnframes()==36000
    assert not result["mix"]["human_mix_quality_approved"]

def test_cli_and_markup():
    from podcast_gpt import cli,web
    args=cli.parse(["project-mix-compose","--project-id","a"*32,"--acknowledgment","test",
                    "--highpass-hz","80","--hum-hz","50","--lowpass-hz","6000"])
    assert (args.highpass_hz,args.hum_hz,args.lowpass_hz)==(80,50,6000)
    assert all(x in web.html_page("test") for x in ("v4MixHighpass","v4MixHum","v4MixLowpass"))
