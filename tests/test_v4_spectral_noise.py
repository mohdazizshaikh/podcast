import math,random
import pytest
from podcast_gpt import spectral_noise as s

@pytest.mark.parametrize('mode',['off','light','medium','strong'])
@pytest.mark.parametrize('length',[0,1,127,128,3199,3200,4001,8192])
@pytest.mark.parametrize('pattern',['zero','uniform'])
def test_bypass(mode,length,pattern):
    x=[0 if pattern=='zero' else 300]*length
    assert s.apply(x,s.settings(mode)) is x

@pytest.mark.parametrize('mode',[None,True,0,[],{},'','auto','LIGHT'])
def test_invalid(mode):
    with pytest.raises(ValueError):s.settings(mode)

@pytest.mark.parametrize('mode',['light','medium','strong'])
@pytest.mark.parametrize('freq',[500,1000,2000])
def test_mixed_tones(mode,freq):
    # Stationary 3000 Hz noise persists under a stronger midband tone.
    noise=lambda i:round(300*math.sin(2*math.pi*3000*i/16000))
    clean=lambda i:round(4000*math.sin(2*math.pi*freq*i/16000))
    x=[noise(i)+(clean(i) if i>=3200 else 0) for i in range(9600)]
    y=s.apply(x,s.settings(mode))
    assert len(y)==len(x) and y==s.apply(x,s.settings(mode))
    def amplitude(a,hz):
        return abs(sum(v*math.sin(2*math.pi*hz*(i+4096)/16000) for i,v in enumerate(a[4096:8192])))*2/4096
    assert amplitude(y,3000)<amplitude(x,3000)*.85
    assert .90<amplitude(y,freq)/amplitude(x,freq)<1.05

@pytest.mark.parametrize('mode',['light','medium','strong'])
def test_seeded_noise(mode):
    rng=random.Random(77)
    noise=[rng.randint(-250,250) for _ in range(9600)]
    x=[v+(round(4000*math.sin(2*math.pi*1000*i/16000)) if i>=3200 else 0) for i,v in enumerate(noise)]
    y=s.apply(x,s.settings(mode));assert len(y)==len(x)
    assert sum(v*v for v in y[128:3000])<sum(v*v for v in x[128:3000])
    assert max(map(abs,y))<5000

@pytest.mark.parametrize('freq',[125,500,1000,3000,6000])
def test_fft_roundtrip(freq):
    x=[round(10000*math.sin(2*math.pi*freq*i/16000)) for i in range(s.N)]
    r,v=s._fft(x);back,_=s._fft(r,v,True)
    assert max(abs(a-round(b/s.N)) for a,b in zip(x,back))<=3

@pytest.mark.parametrize('mode',['off','light','medium','strong'])
def test_dashboard_audit(tmp_path,monkeypatch,mode):
    from podcast_gpt import v4_post_audio as mix,dashboard_mix as dm
    from test_v4_preview import fixture
    from test_v4_dashboard_mix import data
    root,pid=fixture(tmp_path,monkeypatch)
    req={**data(pid),"remove_dc":False,"gate_threshold":0,"limiter_ceiling":0,
         "highpass_hz":0,"hum_hz":0,"lowpass_hz":0,"true_peak_guard":False,
         "auto_peak_correction":False,"adaptive_noise":"medium","spectral_noise":mode}
    result=dm.run(root,req,acknowledgment=dm.ACK)
    assert mix.inspect(root,pid)==result
    assert result["mix"]["settings"].get("spectral_noise")==s.settings(mode)
    assert result["mix"]["total_frames"]==36000
    assert not result["mix"]["human_mix_quality_approved"]

def test_receipt_tamper(tmp_path,monkeypatch):
    import json
    from podcast_gpt import v4_post_audio as mix,source
    from test_v4_preview import fixture
    root,pid=fixture(tmp_path,monkeypatch)
    mix.compose(root,pid,spectral_noise="medium",acknowledgment=mix.ACK)
    path=mix._ctx(root,pid)[1]/mix.FOLDER/"receipt.json"
    record=source.read_json(path,32000)
    record["settings"]["spectral_noise"]["minimum_gain_q15"]=1
    path.write_text(json.dumps(record),encoding="utf-8")
    with pytest.raises(ValueError,match="Invalid mix settings"):mix.inspect(root,pid)

def test_cli_and_markup():
    from podcast_gpt import cli,web
    args=cli.parse(["project-mix-compose","--project-id","a"*32,"--acknowledgment","test","--spectral-noise","strong"])
    assert args.spectral_noise=="strong"
    assert "v4MixSpectralNoise" in web.html_page("test")
