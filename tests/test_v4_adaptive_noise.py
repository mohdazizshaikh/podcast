import random
import math
import pytest
from podcast_gpt import adaptive_noise as n

@pytest.mark.parametrize('mode',['off','light','medium','strong'])
@pytest.mark.parametrize('quiet',[16,100,500,1500])
@pytest.mark.parametrize('tail',[0,1,79,319])
def test_matrix(mode,quiet,tail):
    rng=random.Random(13)
    x=[quiet*(-1 if rng.randrange(2) else 1) for _ in range(10*n.FRAME)]
    x += [quiet*5*(-1 if rng.randrange(2) else 1) for _ in range(20*n.FRAME+tail)]
    cfg=n.settings(mode);y=n.apply(x,cfg)
    assert len(y)==len(x) and y==n.apply(x,cfg)
    assert all(abs(b)<=abs(a) and a*b>=0 for a,b in zip(x,y))
    if mode=='off':assert y is x
    else:
        assert abs(y[100])==quiet*n.FLOORS[mode]//n.SCALE
        assert y[11*n.FRAME:]==x[11*n.FRAME:]

@pytest.mark.parametrize('mode',[None,True,0,[],{},'','auto','LIGHT'])
def test_invalid(mode):
    with pytest.raises(ValueError):n.settings(mode)

@pytest.mark.parametrize('mode',['light','medium','strong'])
@pytest.mark.parametrize('case',['silence','uniform','short','low','loud'])
def test_safe_bypass(mode,case):
    x=([0]*3200 if case=='silence' else [200]*3200 if case=='uniform' else [100]*3199 if case=='short' else [8]*3200+[200]*6400 if case=='low' else [2500]*3200+[12000]*6400)
    assert n.apply(x,n.settings(mode)) is x

@pytest.mark.parametrize('mode',['light','medium','strong'])
def test_noise_and_tone(mode):
    rng=random.Random(99)
    noise=[rng.randint(-400,400) for _ in range(16000)]
    signal=[round(3000*math.sin(2*math.pi*440*i/16000))+rng.randint(-400,400) for i in range(32000)]
    x=noise+signal+[0]*320
    y=n.apply(x,n.settings(mode))
    rms=lambda v:math.sqrt(sum(s*s for s in v)/len(v))
    assert rms(y[:16000])<=rms(noise)*n.FLOORS[mode]/n.SCALE
    assert y[16320:48000]==x[16320:48000]
    assert y[-320:]==[0]*320

def test_transition():
    x=[100]*3200+[500]*6400
    y=n.apply(x,n.settings('strong'))
    ramp=y[3200:3281]
    assert ramp[0]==175 and ramp[-1]==500 and ramp==sorted(ramp)

@pytest.mark.parametrize('mode',['off','light','medium','strong'])
def test_dashboard_audit(tmp_path,monkeypatch,mode):
    from podcast_gpt import v4_post_audio as mix,dashboard_mix as dm
    from test_v4_preview import fixture
    from test_v4_dashboard_mix import data
    root,pid=fixture(tmp_path,monkeypatch)
    req={**data(pid),"remove_dc":False,"gate_threshold":0,"limiter_ceiling":0,
         "highpass_hz":0,"hum_hz":0,"lowpass_hz":0,"true_peak_guard":False,
         "auto_peak_correction":False,"adaptive_noise":mode}
    result=dm.run(root,req,acknowledgment=dm.ACK)
    assert mix.inspect(root,pid)==result
    assert result["mix"]["settings"].get("adaptive_noise")==n.settings(mode)
    assert result["mix"]["total_frames"]==36000
    assert not result["mix"]["human_mix_quality_approved"]

def test_receipt_tamper(tmp_path,monkeypatch):
    import json
    from podcast_gpt import v4_post_audio as mix,source
    from test_v4_preview import fixture
    root,pid=fixture(tmp_path,monkeypatch)
    mix.compose(root,pid,adaptive_noise="medium",acknowledgment=mix.ACK)
    path=mix._ctx(root,pid)[1]/mix.FOLDER/"receipt.json"
    record=source.read_json(path,32000)
    record["settings"]["adaptive_noise"]["minimum_gain_bp"]=1
    path.write_text(json.dumps(record),encoding="utf-8")
    with pytest.raises(ValueError,match="Invalid mix settings"):mix.inspect(root,pid)

def test_cli_and_markup():
    from podcast_gpt import cli,web
    args=cli.parse(["project-mix-compose","--project-id","a"*32,"--acknowledgment","test","--adaptive-noise","strong"])
    assert args.adaptive_noise=="strong"
    assert "v4MixAdaptiveNoise" in web.html_page("test")
