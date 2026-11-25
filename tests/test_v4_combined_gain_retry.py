import hashlib,json,math,re,shutil,struct,subprocess,wave
import pytest
from podcast_gpt import combined_gain as c,loudness_gain as g,peak_correction as p

def measurement(lufs=-20,peak=-4):
    return {'integrated_lufs':lufs,'true_peak_dbtp':peak,'loudness_range_lu':2.0,'gating_threshold_lufs':-30.0}

@pytest.mark.parametrize('goal',[-24,-20,-16,-14])
@pytest.mark.parametrize('peak',[8000,16000,22000])
@pytest.mark.parametrize('ceiling',[8000,16000,22000])
@pytest.mark.parametrize('measured',[-1.49,0])
def test_gain_matrix(goal,peak,ceiling,measured):
    before=measurement();initial=g.gain_ppm(goal,before,peak,ceiling)
    rel=p.next_gain(p.SCALE,measured);final=c.absolute(initial,rel)
    rows=[{'relative_gain_ppm':g.SCALE,'gain_ppm':initial,'measurement':measurement(peak=measured)}, {'relative_gain_ppm':rel,'gain_ppm':final,'measurement':measurement(peak=-3)}]
    rec=c.record(goal,before,peak,'a'*64,ceiling,rows)
    assert c.validate(rec)==rec and 0<final<initial
    raw=struct.pack('<hhh',-peak,0,peak)
    vals=struct.unpack('<hhh',c.apply(raw,final,ceiling))
    assert vals[0]==-vals[2] and vals[1]==0 and vals[2]<=ceiling

@pytest.mark.parametrize('initial,relative',[(True,1000000),(0,1000000),(4000001,1000000),(1,251180),(1000000,True),(1000000,251179),(1000000,1000001)])
def test_invalid_absolute(initial,relative):
    with pytest.raises(ValueError):c.absolute(initial,relative)

def write(path,raw):
    with wave.open(str(path),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000);w.writeframes(raw)
    return hashlib.sha256(raw).hexdigest()

def read(path):
    with wave.open(str(path),'rb') as w:return w.readframes(w.getnframes())

@pytest.mark.parametrize('peaks',[[-4],[-1.5],[0,-3],[1,0,-3],[0,0,0,-3]])
def test_retry(tmp_path,peaks):
    raw=struct.pack('<hhhh',-16000,1000,0,16000)*100
    base=tmp_path/'base.wav';sha=write(base,raw);it=iter(peaks)
    out,digest,rec=c.run(base,tmp_path,len(raw)//2,sha,-16,measurement(),16000,22000,lambda *a:measurement(peak=next(it)))
    assert c.validate(rec)==rec and len(rec['attempts'])==len(peaks)
    assert read(out)==c.apply(raw,rec['gain_ppm'],22000) and hashlib.sha256(read(out)).hexdigest()==digest
    assert read(base)==raw

@pytest.mark.parametrize('peaks',[[None],[0,0,0,0],[100]])
def test_reject(tmp_path,peaks):
    raw=struct.pack('<h',16000)*100;base=tmp_path/'base.wav';sha=write(base,raw);it=iter(peaks)
    with pytest.raises(ValueError):c.run(base,tmp_path,100,sha,-16,measurement(),16000,22000,lambda *a:measurement(peak=next(it)))

@pytest.mark.skipif(not shutil.which('ffmpeg'),reason='FFmpeg required')
@pytest.mark.parametrize('freq',[1000,4000,6000,7500])
def test_ffmpeg(tmp_path,freq):
    raw=b''.join(struct.pack('<h',round(22000*math.sin(2*math.pi*freq*i/16000+.6))) for i in range(48000))
    base=tmp_path/'base.wav';sha=write(base,raw)
    def measure(path,frames):
        r=subprocess.run(['ffmpeg','-nostdin','-hide_banner','-v','info','-i',str(path),'-af','loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json','-f','null','-'],capture_output=True,text=True,check=True,timeout=30)
        x=json.loads(re.findall(r'\{[^{}]+\}',r.stderr)[-1])
        return dict(zip(('integrated_lufs','true_peak_dbtp','loudness_range_lu','gating_threshold_lufs'),[float(x[k]) for k in ('input_i','input_tp','input_lra','input_thresh')]))
    out,digest,rec=c.run(base,tmp_path,48000,sha,-16,measure(base,48000),22000,22000,measure)
    assert measure(out,48000)['true_peak_dbtp']<=g.CEILING and c.validate(rec)==rec
    assert len(read(out))==len(raw) and read(base)==raw

def test_tamper():
    initial=g.gain_ppm(-16,measurement(),16000,22000)
    rec=c.record(-16,measurement(),16000,'a'*64,22000,[{'relative_gain_ppm':g.SCALE,'gain_ppm':initial,'measurement':measurement()}])
    with pytest.raises(ValueError):c.validate({**rec,'gain_ppm':initial+1})

@pytest.mark.parametrize("limiter,initial",[(0,-4),(8000,0),(28000,0)])
def test_dashboard_and_audit(tmp_path,monkeypatch,limiter,initial):
    from podcast_gpt import v4_post_audio as mix,dashboard_mix as dm,audio_diagnostics as diag
    from test_v4_preview import fixture
    from test_v4_dashboard_mix import data
    root,pid=fixture(tmp_path,monkeypatch)
    monkeypatch.setattr(diag,"measure",lambda path,frames:measurement(peak=initial if path.name=="combined-gain-0.wav" else -4))
    result=dm.run(root,{**data(pid),"remove_dc":False,"gate_threshold":0,"limiter_ceiling":limiter,"highpass_hz":0,"hum_hz":0,"lowpass_hz":0,"true_peak_guard":True,"auto_peak_correction":True,"target_lufs":-16},acknowledgment=dm.ACK)
    assert mix.inspect(root,pid)==result
    norm=result["mix"]["settings"]["normalization"]
    assert norm["algorithm"]==c.ALGORITHM and len(norm["attempts"])==(1 if initial<=g.CEILING else 2)
    assert norm["sample_peak_ceiling_pcm"]==min(limiter or 22000,22000)
    assert "peak_correction" not in result["mix"]["settings"]
    assert g.validate(norm)==norm
    assert result["mix"]["total_frames"]==36000

def test_cli_and_browser():
    from podcast_gpt import cli,web
    args=cli.parse(["project-mix-compose","--project-id","a"*32,"--target-lufs","-16","--true-peak-guard","--auto-peak-correction"])
    assert args.target_lufs==-16 and args.true_peak_guard and args.auto_peak_correction
    assert "optional LUFS target, peak safety takes priority" in web.html_page("test")
