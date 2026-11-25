import pytest
from podcast_gpt.render_progress import RenderProgress,RenderStopped,mixed_scenes


def plan(i,s,o):
    return dict(intro_frames=i,speech_frames=s,outro_frames=o,total_video_frames=i+s+o)


@pytest.mark.parametrize('i',[0,1,25,100])
@pytest.mark.parametrize('s',[1,25,15000])
@pytest.mark.parametrize('o',[0,1,50])
def test_scene_matrix(i,s,o):
    raw=plan(i,s,o);before=raw.copy();rows=mixed_scenes(raw)
    assert rows==tuple((k,n) for k,n in zip(('intro','speech','outro'),(i,s,o)) if n)
    assert raw==before
    tick=[0.0];events=[]
    p=RenderProgress([{'frames':n} for _,n in rows],events.append,clock=lambda:tick[0],label='mixed',estimate_segments=False)
    p.begin()
    for j,(_,n) in enumerate(rows):
        tick[0]+=1;p.segment(j)
        assert events[-1]['verified_frames']==sum(v for _,v in rows[:j+1])
    p.muxed();p.committing();p.finished()
    assert all(e['action'].startswith('mixed-') and e['segment_eta_seconds'] is None for e in events)
    assert events[-1]['verified_frames']==i+s+o
    assert events[-1]['completed_actions']==events[-1]['action_limit']==len(rows)+3
    assert all(e['stop_allowed'] for e in events[:-2])
    assert not any(e['stop_allowed'] for e in events[-2:])

@pytest.mark.parametrize('key',['intro_frames','speech_frames','outro_frames','total_video_frames'])
@pytest.mark.parametrize('value',[-1,True,1.5,'1',None])
def test_invalid_scene(key,value):
    raw=plan(1,2,3);raw[key]=value
    with pytest.raises(ValueError):mixed_scenes(raw)

@pytest.mark.parametrize('raw',[plan(1,0,1),dict(plan(1,2,3),total_video_frames=7)])
def test_inconsistent_scene(raw):
    with pytest.raises(ValueError):mixed_scenes(raw)

@pytest.mark.parametrize('label,estimate',[('unknown',True),('',True),(None,True),('mixed',0),('studio','yes')])
def test_invalid_progress_mode(label,estimate):
    with pytest.raises(ValueError):RenderProgress([{'frames':1}],label=label,estimate_segments=estimate)

@pytest.mark.parametrize('where',['begin','first','last','mux','commit'])
def test_mixed_stop(where):
    seen=[];flag=[False]
    p=RenderProgress([{'frames':1},{'frames':20}],seen.append,lambda:flag[0],label='mixed',estimate_segments=False)
    def run(name,func,*args):
        flag[0]=name==where;func(*args)
    with pytest.raises(RenderStopped):
        run('begin',p.begin);run('first',p.segment,0);run('last',p.segment,1);run('mux',p.muxed);run('commit',p.committing)
    assert seen[-1]['action'].startswith('mixed-')


def test_no_stop_after_commit():
    flag=[False];seen=[]
    p=RenderProgress([{'frames':5}],seen.append,lambda:flag[0],label='mixed',estimate_segments=False)
    p.begin();p.segment(0);p.muxed();p.committing();flag[0]=True;p.finished()
    assert seen[-1]['action']=='mixed-audit-complete' and seen[-1]['stop_allowed'] is False


@pytest.mark.parametrize('studio',[False,True])
@pytest.mark.parametrize('stop_at',[None,'mixed-render-segments','mixed-mux-verified','mixed-commit'])
def test_compose_checkpoints(tmp_path,monkeypatch,studio,stop_at):
    from contextlib import nullcontext
    from pathlib import Path
    from types import SimpleNamespace
    from podcast_gpt import v4_mixed_video as mv
    folder=tmp_path/'project';folder.mkdir();dest=folder/'audio';dest.mkdir()
    raw=dict(plan(4,10,5),speech_offset_samples=2560)
    ctx=(folder,dest,{},[],{'total_frames':19*640},raw,{'video_format':'square'})
    monkeypatch.setattr(mv.projects,'project',lambda *a:folder)
    monkeypatch.setattr(mv.projects,'exclusive',lambda *a:nullcontext())
    monkeypatch.setattr(mv,'_context',lambda *a,**kw:ctx)
    monkeypatch.setattr(mv.shutil,'disk_usage',lambda *a:SimpleNamespace(free=10**12))
    monkeypatch.setattr(mv,'_card',lambda p,*a:p.write_bytes(b'card'))
    monkeypatch.setattr(mv,'_decode',lambda *a:{'decoded_video_frames':19})
    monkeypatch.setattr(mv,'_receipt',lambda *a:{'verified':True})
    monkeypatch.setattr(mv,'_audit',lambda *a:{'verified':True})
    monkeypatch.setattr(mv,'shifted_subtitles',lambda *a:b'subtitles')
    counts={};calls=[]
    def cmd(args,**kw):
        p=Path(args[-1]);p.write_bytes(b'video');calls.append(p.name)
        if '-frames:v' in args:counts[str(p)]=int(args[args.index('-frames:v')+1])
    monkeypatch.setattr(mv.media,'cmd',cmd)
    monkeypatch.setattr(mv.export,'_video_frames',lambda p:counts[str(p)])
    seen=[];flag=[False]
    def report(event):
        seen.append(event)
        if event['action']==stop_at and (stop_at!='mixed-render-segments' or event['verified_frames']>0):flag[0]=True
    out=dest/(mv.STUDIO_FOLDER if studio else mv.FOLDER)
    if stop_at:
        with pytest.raises(RenderStopped):mv.compose(None,'p',studio=studio,progress=report,should_stop=lambda:flag[0])
        assert not out.exists()
        assert calls==(['intro.mp4'] if stop_at=='mixed-render-segments' else ['intro.mp4','speech.mp4','outro.mp4',mv.VIDEO])
    else:
        assert mv.compose(None,'p',studio=studio,progress=report,should_stop=lambda:flag[0])=={'project_id':'p','export':{'verified':True}}
        assert (out/mv.VIDEO).read_bytes()==b'video' and (out/mv.SRT).read_bytes()==b'subtitles'
        assert seen[-1]['action']=='mixed-audit-complete'
        assert [e['verified_frames'] for e in seen[:4]]==[0,4,14,19]
    assert not list(folder.glob('v4-mixed-*'))


def test_dashboard_forwarding(tmp_path,monkeypatch):
    from podcast_gpt import dashboard_actions as da
    monkeypatch.setattr(da.projects,'project',lambda *a:tmp_path)
    events=[];report=events.append;stop=lambda:False
    def compose(root,pid,*,studio,progress,should_stop):
        assert studio is True and progress==report and should_stop==stop
        progress({'action':'mixed-test'});return {'ok':True}
    monkeypatch.setattr(da.v4_mixed_video,'compose',compose)
    assert da.run(tmp_path,'p','project-mixed-studio-compose',acknowledgment=da.ACK,progress=report,should_stop=stop)=={'ok':True}
    assert events==[{'action':'mixed-test'}]
