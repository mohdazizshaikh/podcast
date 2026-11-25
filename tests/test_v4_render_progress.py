import itertools
import pytest
from podcast_gpt.render_progress import RenderProgress,RenderStopped

@pytest.mark.parametrize('frames',[(1,2,3),(25,1,251),(9,9,9),(251,6,250)])
@pytest.mark.parametrize('order',list(itertools.permutations(range(3))))
@pytest.mark.parametrize('step',[0.1,1.0])
def test_progress(frames,order,step):
    seen=[];tick=[0.0]
    p=RenderProgress([{'frames':n} for n in frames],seen.append,clock=lambda:tick[0])
    p.begin()
    total=0
    for i in order:
        tick[0]+=step;total+=frames[i];p.segment(i)
        assert seen[-1]['verified_frames']==total
    p.muxed();p.committing();p.finished()
    assert [r['completed_actions'] for r in seen]==list(range(7))
    assert all(r['action_limit']==6 and r['total_frames']==sum(frames) for r in seen)
    assert seen[-2]['stop_allowed'] is False and seen[-1]['stop_allowed'] is False
    assert seen[2]['segment_eta_seconds'] is not None if step==1.0 else seen[2]['segment_eta_seconds'] is None
    assert all(r['segment_eta_seconds'] is None for r in seen[3:])

@pytest.mark.parametrize('frames',[[],[0],[-1],[True],[1.5],['1']])
def test_bad_plan(frames):
    with pytest.raises(ValueError):RenderProgress([{'frames':n} for n in frames])

@pytest.mark.parametrize('index',[-1,3,True,1.5,'1',None])
def test_bad_index(index):
    p=RenderProgress([{'frames':1}]*3)
    with pytest.raises(ValueError):p.segment(index)

@pytest.mark.parametrize('where',['begin','segment','muxed','committing'])
def test_stop(where):
    flag=[False];seen=[]
    p=RenderProgress([{'frames':4}],seen.append,lambda:flag[0])
    def step(name,*args):
        flag[0]=name==where
        getattr(p,name)(*args)
    with pytest.raises(RenderStopped):
        step('begin');step('segment',0);step('muxed');step('committing')
    assert seen[-1]['action'] in ('studio-render-segments','studio-mux-verified','studio-commit')

def test_final_audit_not_cancelled():
    flag=[False];p=RenderProgress([{'frames':1}],should_stop=lambda:flag[0])
    p.begin();p.segment(0);p.muxed();p.committing();flag[0]=True;p.finished()
    assert p.stage==3

@pytest.mark.parametrize('operation',['muxed','committing','finished'])
def test_invalid_stage(operation):
    p=RenderProgress([{'frames':1}])
    with pytest.raises(ValueError):getattr(p,operation)()

def test_duplicate():
    p=RenderProgress([{'frames':1}]);p.segment(0)
    with pytest.raises(ValueError):p.segment(0)

@pytest.mark.parametrize('mode',['cut','match-gentle'])
@pytest.mark.parametrize('stop',[False,True])
def test_compositor_checkpoint(tmp_path,monkeypatch,mode,stop):
    from PIL import Image
    from podcast_gpt import studio_neural as sn
    dest=tmp_path/'audio';temp=tmp_path/'render';temp.mkdir()
    plan=[{'kind':'speech','speaker':'A','turn_id':'1','id':'0001','frames':10},
          {'kind':'pause','speaker':'A','turn_id':'1','id':'0001','frames':13},
          {'kind':'speech','speaker':'B','turn_id':'2','id':'0002','frames':9}]
    done={}
    for cid in ('0001','0002'):
        path=dest/sn.neural.FOLDER/cid/'face.mp4';path.parent.mkdir(parents=True);path.write_bytes(cid.encode())
        done[cid]={'mp4_sha256':sn.source.digest(path)}
    monkeypatch.setattr(sn,'_portraits',lambda *a:({1:b'',2:b''},{'A':1,'B':2}))
    monkeypatch.setattr(sn.studio,'card',lambda *a,**kw:Image.new('RGB',(720,720)))
    monkeypatch.setattr(sn.studio,'active_rect',lambda *a:(20,70,160,120))
    counts={};seen=[]
    def command(args,**kw):
        counts[args[-1]]=int(args[args.index('-frames:v')+1])
    monkeypatch.setattr(sn.media,'cmd',command)
    monkeypatch.setattr(sn.export,'_video_frames',lambda path:counts[str(path)])
    p=RenderProgress(plan,seen.append,lambda:stop and len(counts)>=1)
    p.begin()
    def render():return sn._segments(None,dest,None,done,{'video_format':'square'},{'layout':'spotlight','transition':mode},None,plan,temp,tracker=p)
    if stop:
        with pytest.raises(RenderStopped):render()
        assert len(counts)==1 and seen[-1]['verified_frames']==10
        assert not (temp/'segments.ffconcat').exists()
    else:
        assert render().is_file()
        assert seen[-1]['verified_frames']==32
        assert [r['verified_frames'] for r in seen]==([0,10,23,32] if mode=='cut' else [0,10,19,32])

def test_dashboard_progress_forwarding(tmp_path,monkeypatch):
    from podcast_gpt import dashboard_actions as da
    monkeypatch.setattr(da.projects,'project',lambda *a:tmp_path)
    seen=[];report=seen.append;stop=lambda:False
    def compose(root,pid,*,progress,should_stop):
        assert progress==report and should_stop==stop
        progress({'action':'test'});return {'ok':True}
    monkeypatch.setattr(da.studio_neural,'compose',compose)
    assert da.run(tmp_path,'p','project-neural-studio-compose',acknowledgment=da.ACK,progress=report,should_stop=stop)=={'ok':True}
    assert seen==[{'action':'test'}]
