import hashlib,json,math,re,shutil,struct,subprocess,wave
import pytest
from podcast_gpt import peak_correction as p

@pytest.mark.parametrize('measured',[-1.49,-1,0,1,2,5,8,9])
@pytest.mark.parametrize('sample',[-32768,-22000,-1,0,1,22000,32767])
def test_gain_and_pcm(measured,sample):
    gain=p.next_gain(p.SCALE,measured)
    raw=struct.pack('<h',sample)
    value=struct.unpack('<h',p.apply(raw,gain))[0]
    assert p.MIN_GAIN<=gain<p.SCALE and abs(value)<=abs(sample) and value*sample>=0
    assert p.apply(raw,p.SCALE)==raw

@pytest.mark.parametrize('value',[None,True,float('nan'),float('inf'),-151,101,-1.5])
def test_bad_step(value):
    with pytest.raises(ValueError):p.next_gain(p.SCALE,value)

@pytest.mark.parametrize('peak',[10,20,100])
def test_budget(peak):
    with pytest.raises(ValueError,match='bounded'):p.next_gain(p.SCALE,peak)

def write(path,raw):
    with wave.open(str(path),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000);w.writeframes(raw)
    return hashlib.sha256(raw).hexdigest()

def read(path):
    with wave.open(str(path),'rb') as w:return w.readframes(w.getnframes())

@pytest.mark.parametrize('peaks',[[-3],[-1.5],[0,-2],[1,0,-2],[0,0,0,-2]])
def test_run(tmp_path,peaks):
    raw=struct.pack('<hhhh',-22000,1000,0,22000)*100
    base=tmp_path/'base.wav';sha=write(base,raw);it=iter(peaks)
    path,digest,record=p.run(base,tmp_path,len(raw)//2,sha,lambda *a:{'true_peak_dbtp':next(it)})
    assert p.validate(record)==record and len(record['attempts'])==len(peaks)
    assert read(path)==p.apply(raw,record['gain_ppm']) and hashlib.sha256(read(path)).hexdigest()==digest
    assert read(base)==raw

@pytest.mark.parametrize('peaks',[[None],[0,0,0,0],[100]])
def test_reject(tmp_path,peaks):
    raw=struct.pack('<h',22000)*100;base=tmp_path/'base.wav';sha=write(base,raw);it=iter(peaks)
    with pytest.raises(ValueError):p.run(base,tmp_path,100,sha,lambda *a:{'true_peak_dbtp':next(it)})

@pytest.mark.skipif(not shutil.which('ffmpeg'),reason='FFmpeg required')
@pytest.mark.parametrize('freq',[1000,4000,6000,7500])
def test_actual_ffmpeg(tmp_path,freq):
    raw=b''.join(struct.pack('<h',round(30000*math.sin(2*math.pi*freq*i/16000+.6))) for i in range(16000))
    base=tmp_path/'base.wav';sha=write(base,raw)
    def measure(path,frames):
        r=subprocess.run(['ffmpeg','-nostdin','-hide_banner','-v','info','-i',str(path),'-af','loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json','-f','null','-'],capture_output=True,text=True,check=True,timeout=30)
        return {'true_peak_dbtp':float(json.loads(re.findall(r'\{[^{}]+\}',r.stderr)[-1])['input_tp'])}
    out,digest,rec=p.run(base,tmp_path,16000,sha,measure)
    assert measure(out,16000)['true_peak_dbtp']<=p.CEILING
    assert len(read(out))==len(raw) and read(base)==raw

def test_tamper():
    sha='a'*64;gain=p.next_gain(p.SCALE,0);rec=p.receipt([{'gain_ppm':p.SCALE,'measured_true_peak_dbtp':0},{'gain_ppm':gain,'measured_true_peak_dbtp':-2}],sha)
    with pytest.raises(ValueError):p.validate({**rec,'gain_ppm':gain+1})

@pytest.mark.parametrize("initial",[-4.0,0.0])
def test_dashboard_and_audit(tmp_path,monkeypatch,initial):
    from podcast_gpt import v4_post_audio as mix,dashboard_mix as dm,audio_diagnostics as diag
    from test_v4_preview import fixture
    from test_v4_dashboard_mix import data
    root,pid=fixture(tmp_path,monkeypatch)
    monkeypatch.setattr(diag,"measure",lambda path,frames:{"true_peak_dbtp":-4.0 if "peak-correction-" in str(path) or path.parent.name==mix.FOLDER else initial})
    result=dm.run(root,{**data(pid),"remove_dc":False,"gate_threshold":0,"limiter_ceiling":0,"highpass_hz":0,"hum_hz":0,"lowpass_hz":0,"true_peak_guard":True,"auto_peak_correction":True},acknowledgment=dm.ACK)
    assert mix.inspect(root,pid)==result
    assert len(result["mix"]["settings"]["peak_correction"]["attempts"])==(1 if initial<=p.CEILING else 2)
    assert result["mix"]["total_frames"]==36000

def test_mode_constraints():
    from podcast_gpt import v4_post_audio as mix
    with pytest.raises(ValueError,match="requires"):mix.compose(None,None,auto_peak_correction=True,acknowledgment=mix.ACK)
    with pytest.raises(ValueError,match="requires"):mix.compose(None,None,auto_peak_correction=True,target_lufs=-16,acknowledgment=mix.ACK)

def test_reject_before_save(tmp_path,monkeypatch):
    from podcast_gpt import v4_post_audio as mix,audio_diagnostics as diag
    from test_v4_preview import fixture
    root,pid=fixture(tmp_path,monkeypatch)
    monkeypatch.setattr(diag,"measure",lambda *args:{"true_peak_dbtp":100})
    dest=mix._ctx(root,pid)[1]
    with pytest.raises(ValueError,match="bounded"):mix.compose(root,pid,true_peak_guard=True,auto_peak_correction=True,acknowledgment=mix.ACK)
    assert not (dest/mix.FOLDER).exists()

def test_cli_markup():
    from podcast_gpt import cli,web
    args=cli.parse(["project-mix-compose","--project-id","a"*32,"--true-peak-guard","--auto-peak-correction"])
    assert args.auto_peak_correction and args.true_peak_guard
    assert "v4MixPeakCorrect" in web.html_page("test")
