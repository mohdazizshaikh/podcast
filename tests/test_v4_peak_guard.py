import math
import random
import struct
import subprocess
import wave
import shutil
import pytest
from podcast_gpt import peak_guard as g

@pytest.mark.parametrize('length',[0,1,2,3,4,5,7,8,50,1000])
@pytest.mark.parametrize('pattern',['positive','negative','alternating','random'])
def test_bound(length,pattern):
    rng=random.Random(42)
    xs=[32767 if pattern=='positive' else -32768 if pattern=='negative' else (-32768 if i%2 else 32767) if pattern=='alternating' else rng.randint(-32768,32767) for i in range(length)]
    ys=list(g.samples(xs))
    assert len(ys)==length
    assert ys==list(g.samples(xs))
    assert all(abs(y)<=min(abs(x),g.CAP) and y*x>=0 for x,y in zip(xs,ys))
    padded=[0,0,0]+ys+[0,0,0]
    for i in range(len(padded)-3):
        for weights in [(-9,111,29,-3),(-8,72,72,-8),(-3,29,111,-9)]:
            assert abs(sum(x*w for x,w in zip(padded[i:i+4],weights)))<=g.CAP*160

@pytest.mark.parametrize('value',[None,0,1,'true',[],{}])
def test_invalid_setting(value):
    with pytest.raises(ValueError):g.settings(value)

@pytest.mark.parametrize('value',[None,True,float('nan'),float('inf'),-151,-1.49,0])
def test_invalid_measure(value):
    with pytest.raises(ValueError):g.check(value)

@pytest.mark.parametrize('value',[-150,-20,-1.5])
def test_measure_pass(value):assert g.check(value)['measured_true_peak_dbtp']==value

def encode(xs):return b''.join(struct.pack('<h',x) for x in xs)
def decode(raw):return [x[0] for x in struct.iter_unpack('<h',raw)]

def test_chunk_invariance():
    raw=encode([32767,1000,-32768,2000]*10000)
    cfg=g.settings(True)
    single=b''.join(g.blocks([raw],cfg,decode,encode))
    split=b''.join(g.blocks([raw[:2],raw[2:6],raw[6:300],raw[300:]],cfg,decode,encode))
    assert single==split and len(single)==len(raw)
    assert b''.join(g.blocks([raw],g.settings(False),decode,encode))==raw

def test_lookahead_release():
    xs=[1000]*10+[32767]+[1000]*900
    ys=list(g.samples(xs))
    assert ys[6]==1000 and ys[7]<1000 and ys[10]<=g.CAP
    assert ys[-1]==1000

@pytest.mark.skipif(not shutil.which('ffmpeg'),reason='FFmpeg required')
@pytest.mark.parametrize('frequency',[100,1000,3500,4000,6000,7500])
def test_ffmpeg_measured_guard(tmp_path,frequency):
    import json,re
    x=[round(32767*math.sin(2*math.pi*frequency*i/16000+.6)) for i in range(16000)]
    path=tmp_path/'guard.wav'
    with wave.open(str(path),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000);w.writeframes(encode(g.samples(x)))
    result=subprocess.run(['ffmpeg','-nostdin','-hide_banner','-v','info','-i',str(path),'-af','loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json','-f','null','-'],capture_output=True,text=True,check=True,timeout=30)
    report=json.loads(re.findall(r'\{[^{}]+\}',result.stderr)[-1]);peak=float(report['input_tp'])
    if frequency<=3500:assert peak<=g.CEILING
    if peak>g.CEILING:
        with pytest.raises(ValueError,match='above'):g.check(peak)
    else:assert g.check(peak)['measured_true_peak_dbtp']==peak

def measurement(peak):
    return {"integrated_lufs":-20.0,"true_peak_dbtp":peak,"loudness_range_lu":2.0,"gating_threshold_lufs":-30.0}

@pytest.mark.parametrize("limiter,target",[(0,None),(16000,None),(28000,-16)])
def test_guard_mix_and_audit(tmp_path,monkeypatch,limiter,target):
    from podcast_gpt import v4_post_audio as mix,audio_diagnostics as diag,dashboard_mix as dm
    from test_v4_preview import fixture
    from test_v4_dashboard_mix import data
    root,pid=fixture(tmp_path,monkeypatch)
    monkeypatch.setattr(diag,"measure",lambda *args:measurement(-4.0))
    req={**data(pid),"remove_dc":False,"gate_threshold":0,"limiter_ceiling":limiter,
         "highpass_hz":0,"hum_hz":0,"lowpass_hz":0,"true_peak_guard":True,"target_lufs":target}
    result=dm.run(root,req,acknowledgment=dm.ACK)
    assert result==mix.inspect(root,pid)
    assert result["mix"]["settings"]["peak_guard"]==g.settings(True)
    assert result["mix"]["settings"]["peak_guard_check"]==g.check(-4.0)
    assert diag.pcm_stats(result["path"])["sample_peak_pcm"]<=min(limiter or g.CAP,g.CAP)
    if target is not None:assert result["mix"]["settings"]["normalization"]["sample_peak_ceiling_pcm"]==g.CAP

@pytest.mark.parametrize("peak",[None,-1.49])
def test_guard_rejects_before_commit(tmp_path,monkeypatch,peak):
    from podcast_gpt import v4_post_audio as mix,audio_diagnostics as diag
    from test_v4_preview import fixture
    root,pid=fixture(tmp_path,monkeypatch)
    monkeypatch.setattr(diag,"measure",lambda *args:measurement(peak))
    dest=mix._ctx(root,pid)[1]
    with pytest.raises(ValueError,match="Measured true peak"):mix.compose(root,pid,true_peak_guard=True,acknowledgment=mix.ACK)
    assert not (dest/mix.FOLDER).exists()

def test_guard_audit_remeasures(tmp_path,monkeypatch):
    from podcast_gpt import v4_post_audio as mix,audio_diagnostics as diag
    from test_v4_preview import fixture
    root,pid=fixture(tmp_path,monkeypatch)
    monkeypatch.setattr(diag,"measure",lambda *args:measurement(-4.0))
    mix.compose(root,pid,true_peak_guard=True,acknowledgment=mix.ACK)
    monkeypatch.setattr(diag,"measure",lambda *args:measurement(-3.0))
    with pytest.raises(ValueError,match="check differs"):mix.inspect(root,pid)

def test_cli_and_browser():
    from podcast_gpt import cli,web
    base=["project-mix-compose","--project-id","a"*32,"--acknowledgment","test"]
    assert not cli.parse(base).true_peak_guard
    assert cli.parse(base+["--true-peak-guard"]).true_peak_guard
    assert "v4MixTruePeak" in web.html_page("test")
