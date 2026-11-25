import shutil,subprocess
import pytest
from podcast_gpt import studio_transition as t


def plan(n,previous='A',following='B'):
    return [{'kind':'speech','speaker':previous,'turn_id':'1','frames':10},
            {'kind':'pause','speaker':previous,'turn_id':'1','frames':n},
            {'kind':'speech','speaker':following,'turn_id':'2','frames':9}]

@pytest.mark.parametrize('mode',t.MODES)
@pytest.mark.parametrize('n',[1,2,3,4,5,6,7,11,12,13,251])
@pytest.mark.parametrize('same',[False,True])
def test_schedule(mode,n,same):
    rows=plan(n,following='A' if same else 'B')
    before=[dict(r) for r in rows]
    out=t.schedule(rows,mode)
    assert rows==before
    if mode=='cut' or same or n<3:assert out=={}
    else:
        length=min(n,t.LIMITS[mode]);assert out=={1:{'from':'A','to':'B','start':n-length,'frames':length}}

@pytest.mark.parametrize('mode',[None,True,1,[],{},'', 'fade','QUICK'])
def test_invalid_mode(mode):
    with pytest.raises(ValueError):t.validate(mode)

@pytest.mark.parametrize('args',[(2,0,2),(6,1,6),(6,-1,7),(13,0,13),(True,0,3),(6,0,True),(6,0,6.0),(100000001,99999995,6)])
def test_invalid_geometry(args):
    with pytest.raises(ValueError):t.filter_graph(*args)

@pytest.mark.parametrize('change',['no_previous','no_next','previous_mismatch','turn_mismatch','next_pause','speech_only'])
def test_skip(change):
    rows=plan(8)
    if change=='no_previous':rows=rows[1:]
    elif change=='no_next':rows=rows[:-1]
    elif change=='previous_mismatch':rows[0]['speaker']='C'
    elif change=='turn_mismatch':rows[0]['turn_id']='3'
    elif change=='next_pause':rows[2]['kind']='pause'
    else:rows[1]['kind']='speech'
    assert t.schedule(rows,'quick')=={}

@pytest.mark.skipif(not shutil.which('ffmpeg'),reason='FFmpeg required')
@pytest.mark.parametrize('mode',['quick','gentle'])
@pytest.mark.parametrize('n',[3,6,13,25])
def test_ffmpeg(mode,n):
    spec=t.schedule(plan(n),mode)[1];vf=t.filter_graph(n,spec['start'],spec['frames'])
    r=subprocess.run(['ffmpeg','-nostdin','-v','error','-f','lavfi','-i','color=black:s=64x48:r=25','-f','lavfi','-i','color=white:s=64x48:r=25','-filter_complex_threads','1','-filter_complex',vf,'-map','[out]','-frames:v',str(n),'-threads','1','-pix_fmt','yuv420p','-f','rawvideo','-'],capture_output=True,check=True,timeout=20)
    size=64*48*3//2;assert len(r.stdout)==n*size
    values=[r.stdout[i*size] for i in range(n)]
    assert values[:spec['start']+1]==[16]*(spec['start']+1)
    assert values[-1]==235 and values==sorted(values)
    assert 16<values[-2]<235

@pytest.mark.parametrize('mode',t.MODES)
def test_settings(tmp_path,monkeypatch,mode):
    from podcast_gpt import studio_preview as studio,cli,web
    from test_v4_preview import fixture
    root,pid=fixture(tmp_path,monkeypatch)
    saved=studio.configure(root,pid,layout='spotlight',transition=mode)
    assert studio.inspect_settings(root,pid)==saved
    assert saved['settings'].get('transition','cut')==mode
    assert ('transition' in saved['settings'])==(mode!='cut')
    assert cli.parse(['project-studio-configure','--project-id',pid,'--layout','spotlight','--transition',mode]).transition==mode
    assert 'v4StudioTransition' in web.html_page('test')

@pytest.mark.parametrize('mode',['quick','gentle'])
def test_compositor(tmp_path,monkeypatch,mode):
    from podcast_gpt import studio_neural as sn
    from PIL import Image
    dest=tmp_path/'audio';temp=tmp_path/'render';temp.mkdir()
    rows=plan(13);rows[0]['id']='0001';rows[1]['id']='0001';rows[2]['id']='0002'
    done={}
    for cid in ('0001','0002'):
        path=dest/sn.neural.FOLDER/cid/'face.mp4';path.parent.mkdir(parents=True);path.write_bytes(cid.encode())
        done[cid]={'mp4_sha256':sn.source.digest(path)}
    monkeypatch.setattr(sn,'_portraits',lambda *a:({1:b'',2:b''},{'A':1,'B':2}))
    monkeypatch.setattr(sn.studio,'card',lambda *a,**kw:Image.new('RGB',(720,720)))
    monkeypatch.setattr(sn.studio,'active_rect',lambda *a:(20,70,160,120))
    seen=[];counts={}
    def command(args,**kw):
        seen.append(args);counts[args[-1]]=int(args[args.index('-frames:v')+1])
    monkeypatch.setattr(sn.media,'cmd',command)
    monkeypatch.setattr(sn.export,'_video_frames',lambda path:counts[str(path)])
    listing=sn._segments(None,dest,None,done,{'video_format':'square'},{'layout':'spotlight','transition':mode},None,rows,temp)
    assert list(counts.values())==[10,13,9]
    assert 'blend=all_expr' in seen[1][seen[1].index('-filter_complex')+1]
    assert str(temp/'card-01-1.png') in seen[1] and str(temp/'card-02-1.png') in seen[1]
    assert all('blend=all_expr' not in x for j in (0,2) for x in seen[j])
    assert listing.read_text().count('file segment')==3
