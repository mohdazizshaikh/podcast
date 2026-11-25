import shutil,subprocess
import pytest
from podcast_gpt import mixed_chunks as c,studio_cache as cache


def plan(i,s,o):
    return dict(intro_frames=i,speech_frames=s,outro_frames=o,total_video_frames=i+s+o)

@pytest.mark.parametrize('i',[0,1,1501])
@pytest.mark.parametrize('s',[1,1499,1500,1501,3001])
@pytest.mark.parametrize('o',[0,1,3000])
def test_partition(i,s,o):
    p=plan(i,s,o);before=p.copy();rows=c.chunks(p)
    assert p==before
    assert sum(r['frames'] for r in rows)==i+s+o
    for kind,n in [('intro',i),('speech',s),('outro',o)]:
        selected=[r for r in rows if r['kind']==kind]
        assert [r['start'] for r in selected]==list(range(0,n,c.MAX_FRAMES))
        assert sum(r['frames'] for r in selected)==n
        assert all(1<=r['frames']<=c.MAX_FRAMES for r in selected)
    assert [r['kind'] for r in rows]==sorted([r['kind'] for r in rows],key=['intro','speech','outro'].index)

@pytest.mark.parametrize('limit',[0,-1,True,1.5,'1',None,1501])
def test_bad_limit(limit):
    with pytest.raises(ValueError):c.chunks(plan(0,1,0),limit)

@pytest.mark.parametrize('start,frames',[(-1,1),(True,1),(1.5,1),(0,0),(0,1501),(0,True),(0,1.5),(100000000,1)])
def test_bad_range(start,frames):
    with pytest.raises(ValueError):c.filter_graph(start,frames)

@pytest.mark.parametrize('studio',[False,True])
@pytest.mark.parametrize('change',['seal','renderer','plan'])
def test_namespace(tmp_path,studio,change):
    seal={'studio':studio,'mix':'a'};rows=c.chunks(plan(1,1501,0))
    a=cache.SegmentCache(tmp_path,{'kind':'mixed-resume-v1','seal':seal},rows,'v1')
    source=tmp_path/'v';source.write_bytes(b'video');a.save(0,[],source)
    b=cache.SegmentCache(tmp_path,{'kind':'mixed-resume-v1','seal':{**seal,'mix':'b'} if change=='seal' else seal},c.chunks(plan(1,1502,0)) if change=='plan' else rows,'v2' if change=='renderer' else 'v1')
    assert a.key!=b.key and not b.restore(0,[],tmp_path/'restored',lambda _:1)

@pytest.mark.skipif(not shutil.which('ffmpeg'),reason='FFmpeg required')
@pytest.mark.parametrize('length,limit',[(9,1),(13,4),(21,7),(23,10),(31,15),(32,31)])
def test_exact_frames(length,limit):
    base=['ffmpeg','-nostdin','-v','error','-f','lavfi','-i','testsrc2=s=64x48:r=25']
    def render(graph,count):
        r=subprocess.run(base+['-vf',graph,'-frames:v',str(count),'-threads','1','-pix_fmt','yuv420p','-f','rawvideo','-'],capture_output=True,check=True,timeout=20)
        assert len(r.stdout)==count*64*48*3//2
        return r.stdout
    full=render('fps=25,setsar=1,tpad=stop_mode=clone:stop_duration=1,format=yuv420p',length)
    assert full==b''.join(render(c.filter_graph(row['start'],row['frames']),row['frames']) for row in c.chunks(plan(0,length,0),limit))

@pytest.mark.parametrize('studio',[False,True])
@pytest.mark.parametrize('stop_after',[1,2,3])
def test_resume_compose(tmp_path,monkeypatch,studio,stop_after):
    from contextlib import nullcontext
    from pathlib import Path
    from types import SimpleNamespace
    from podcast_gpt import v4_mixed_video as mv
    from podcast_gpt.render_progress import RenderStopped
    folder=tmp_path/'project';folder.mkdir();dest=folder/'audio';dest.mkdir()
    raw=dict(plan(4,1501,5),speech_offset_samples=2560)
    seal={'video_format':'square'}
    if studio:seal['variant']='neural-studio'
    ctx=(folder,dest,{},[],{'total_frames':1510*640},raw,seal)
    monkeypatch.setattr(mv.projects,'project',lambda *a:folder)
    monkeypatch.setattr(mv.projects,'exclusive',lambda *a:nullcontext())
    monkeypatch.setattr(mv,'_context',lambda *a,**kw:ctx)
    monkeypatch.setattr(mv,'_renderer_identity',lambda:'test')
    monkeypatch.setattr(mv.shutil,'disk_usage',lambda *a:SimpleNamespace(free=10**12))
    monkeypatch.setattr(mv,'_card',lambda p,*a:p.write_bytes(b'card'))
    monkeypatch.setattr(mv,'_decode',lambda *a:{'decoded_video_frames':1510})
    monkeypatch.setattr(mv,'_receipt',lambda *a:{'verified':True})
    monkeypatch.setattr(mv,'_audit',lambda *a:{'verified':True})
    monkeypatch.setattr(mv,'shifted_subtitles',lambda *a:b'subtitles')
    calls=[]
    def cmd(args,**kw):
        p=Path(args[-1]);calls.append(p.name)
        p.write_text(args[args.index('-frames:v')+1] if '-frames:v' in args else 'mux',encoding='ascii')
    monkeypatch.setattr(mv.media,'cmd',cmd)
    monkeypatch.setattr(mv.export,'_video_frames',lambda p:int(p.read_text(encoding='ascii')))
    out=dest/(mv.STUDIO_FOLDER if studio else mv.FOLDER)
    with pytest.raises(RenderStopped):
        mv.compose(None,'p',studio=studio,resume=True,should_stop=lambda:len(calls)>=stop_after)
    assert not out.exists() and len(calls)==stop_after
    assert not list(folder.glob('v4-mixed-*'))
    assert mv.compose(None,'p',studio=studio,resume=True)=={'project_id':'p','export':{'verified':True}}
    assert calls==[f'segment{i:06}.mp4' for i in range(4)]+[mv.VIDEO]
    assert (out/mv.SRT).read_bytes()==b'subtitles'

@pytest.mark.parametrize('studio',[False,True])
def test_dashboard_resume(tmp_path,monkeypatch,studio):
    from podcast_gpt import dashboard_actions as da,cli,web
    action='project-mixed-'+('studio' if studio else 'video')+'-resume'
    monkeypatch.setattr(da.projects,'project',lambda *a:tmp_path)
    def compose(root,pid,**kw):
        assert kw=={'studio':studio,'progress':None,'should_stop':None,'resume':True}
        return {'ok':True}
    monkeypatch.setattr(da.v4_mixed_video,'compose',compose)
    assert da.run(tmp_path,'p',action,acknowledgment=da.ACK)=={'ok':True}
    assert cli.parse([action,'--project-id','p']).operation==action
    assert action in web.html_page('test')
