import json
import shutil
import subprocess
from pathlib import Path
import pytest
from podcast_gpt import studio_cache as c


def cache(root,frames=(3,6,10),binding=None,renderer='v1'):
    return c.SegmentCache(root,{'input':'a'} if binding is None else binding,[{'frames':n} for n in frames],renderer)

@pytest.mark.parametrize('frames',[(1,),(3,6,10),(251,1,6)])
@pytest.mark.parametrize('deps',[[],['a'*64,'b'*64]])
@pytest.mark.parametrize('payload',[b'video',b'\x00'*64,b'\xff'*1024])
def test_roundtrip(tmp_path,frames,deps,payload):
    first=cache(tmp_path,frames);p=tmp_path/'original.mp4';p.write_bytes(payload)
    for i,n in enumerate(frames):
        target=tmp_path/f'restored{i}.mp4'
        assert not first.restore(i,deps,target,lambda _:n)
        first.save(i,deps,p)
        reopened=cache(tmp_path,frames)
        assert reopened.restore(i,deps,target,lambda _:n)
        assert target.read_bytes()==payload
        with pytest.raises(ValueError,match='already exists'):reopened.save(i,deps,p)

@pytest.mark.parametrize('changed',['binding','plan','renderer'])
@pytest.mark.parametrize('index',[0,1,2])
def test_namespace(tmp_path,changed,index):
    first=cache(tmp_path);p=tmp_path/'v';p.write_bytes(b'v');first.save(index,[],p)
    other=cache(tmp_path,frames=(3,6,11) if changed=='plan' else (3,6,10),binding={'input':'b'} if changed=='binding' else None,renderer='v2' if changed=='renderer' else 'v1')
    assert first.key!=other.key and not other.restore(index,[],tmp_path/'out',lambda _:3)

@pytest.mark.parametrize('field,value',[('schema',True),('schema',2),('key','a'*64),('index',True),('index',2),('frames',True),('frames',9),('dependencies',['a'*64,'b'*64]),('sha256','a'*64),('bytes',True),('bytes',1),('extra',0)])
def test_receipt(tmp_path,field,value):
    obj=cache(tmp_path);v=tmp_path/'v';v.write_bytes(b'video');obj.save(0,[],v)
    p=obj.path/'segment000000'/'receipt.json';saved=json.loads(p.read_text());saved[field]=value;p.write_text(json.dumps(saved))
    with pytest.raises(ValueError,match='receipt differs'):obj.restore(0,[],tmp_path/'out',lambda _:3)

@pytest.mark.parametrize('index',[-1,True,3,1.5,'1',None])
def test_index(tmp_path,index):
    obj=cache(tmp_path)
    with pytest.raises(ValueError):obj.restore(index,[],tmp_path/'out',lambda _:3)

@pytest.mark.parametrize('deps',[None,{},'a'*64,['a'*64],['a'*64,'B'*64],['a'*64,'b'*64,'c'*64],[1,2]])
def test_dependencies(tmp_path,deps):
    obj=cache(tmp_path)
    with pytest.raises(ValueError):obj.restore(0,deps,tmp_path/'out',lambda _:3)

@pytest.mark.parametrize('frames',[(),(0,),(-1,),(True,),(1.5,),('1',),(100000001,)])
def test_plan(tmp_path,frames):
    with pytest.raises(ValueError):cache(tmp_path,frames)

@pytest.mark.parametrize('damage',['video','receipt_missing','extra','wrong_frame','dependency_change','empty'])
def test_damage(tmp_path,damage):
    obj=cache(tmp_path);v=tmp_path/'v';v.write_bytes(b'video');deps=['a'*64,'b'*64];obj.save(0,deps,v)
    entry=obj.path/'segment000000';expected=3
    if damage=='video':(entry/'video.mp4').write_bytes(b'other')
    elif damage=='receipt_missing':(entry/'receipt.json').unlink()
    elif damage=='extra':(entry/'extra').touch()
    elif damage=='wrong_frame':expected=2
    elif damage=='dependency_change':deps=['a'*64,'c'*64]
    else:(entry/'video.mp4').write_bytes(b'')
    with pytest.raises(ValueError):obj.restore(0,deps,tmp_path/'out',lambda _:expected)

@pytest.mark.parametrize('which',['root','namespace','entry','video','receipt'])
def test_symlinks(tmp_path,which):
    obj=cache(tmp_path);v=tmp_path/'v';v.write_bytes(b'video');obj.save(0,[],v)
    entry=obj.path/'segment000000'
    p={'root':obj.path.parent,'namespace':obj.path,'entry':entry,'video':entry/'video.mp4','receipt':entry/'receipt.json'}[which]
    dest=tmp_path/'moved';p.rename(dest)
    try:p.symlink_to(dest,target_is_directory=dest.is_dir())
    except OSError:pytest.skip('Symlink creation unavailable')
    with pytest.raises(ValueError):obj.restore(0,[],tmp_path/'out',lambda _:3)

@pytest.mark.parametrize('n',[1,3,12])
@pytest.mark.skipif(not (shutil.which('ffmpeg') and shutil.which('ffprobe')),reason='FFmpeg required')
def test_real_video(tmp_path,n):
    v=tmp_path/'v.mp4'
    subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=s=64x48:r=25','-frames:v',str(n),'-c:v','libx264','-threads','1',str(v)],check=True,timeout=20)
    def count(p):
        r=subprocess.run(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames','-of','csv=p=0',str(p)],capture_output=True,text=True,check=True,timeout=20)
        return int(r.stdout.strip())
    obj=cache(tmp_path,(n,));obj.save(0,[],v)
    out=tmp_path/'restored.mp4';assert obj.restore(0,[],out,count)
    assert count(out)==n and out.read_bytes()==v.read_bytes()

@pytest.mark.parametrize('mode',['cut','match-gentle'])
@pytest.mark.parametrize('stop_after',[1,2,3])
def test_resume_segments(tmp_path,monkeypatch,mode,stop_after):
    from PIL import Image
    from podcast_gpt import studio_neural as sn
    from podcast_gpt.render_progress import RenderProgress,RenderStopped
    dest=tmp_path/'audio'
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
    calls=[]
    def cmd(args,**kw):
        p=Path(args[-1]);calls.append(p.name)
        p.write_text(args[args.index('-frames:v')+1],encoding='ascii')
    monkeypatch.setattr(sn.media,'cmd',cmd)
    monkeypatch.setattr(sn.export,'_video_frames',lambda p:int(p.read_text(encoding='ascii')))
    binding={'video_format':'square'};settings={'layout':'spotlight','transition':mode}
    sc=c.SegmentCache(tmp_path,binding,plan,'test')
    first=tmp_path/'first';first.mkdir()
    tracker=RenderProgress(plan,should_stop=lambda:len(calls)>=stop_after)
    tracker.begin()
    with pytest.raises(RenderStopped):
        sn._segments(None,dest,None,done,binding,settings,None,plan,first,tracker=tracker,cache=sc)
    assert len(calls)==stop_after
    shutil.rmtree(first)
    second=tmp_path/'second';second.mkdir()
    tracker=RenderProgress(plan,estimate_segments=False);tracker.begin()
    listing=sn._segments(None,dest,None,done,binding,settings,None,plan,second,tracker=tracker,cache=c.SegmentCache(tmp_path,binding,plan,'test'))
    assert len(calls)==3 and tracker.count==32
    assert listing.read_text().splitlines()[1:]==[f'file segment{i:05}.mp4' for i in range(3)]

def test_dashboard_resume(tmp_path,monkeypatch):
    from podcast_gpt import dashboard_actions as da,cli,web
    monkeypatch.setattr(da.projects,'project',lambda *a:tmp_path)
    def compose(root,pid,**kwargs):
        assert kwargs=={'progress':None,'should_stop':None,'resume':True}
        return {'ok':True}
    monkeypatch.setattr(da.studio_neural,'compose',compose)
    assert da.run(tmp_path,'p','project-neural-studio-resume',acknowledgment=da.ACK)=={'ok':True}
    assert cli.parse(['project-neural-studio-resume','--project-id','p']).operation=='project-neural-studio-resume'
    assert 'project-neural-studio-resume' in web.html_page('test')
