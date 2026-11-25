import shutil,subprocess
import pytest
from podcast_gpt import studio_transition as t


def plan(n,same=False):
    return [{'kind':'speech','speaker':'A','turn_id':'1','frames':10},
            {'kind':'pause','speaker':'A','turn_id':'1','frames':n},
            {'kind':'speech','speaker':'A' if same else 'B','turn_id':'2','frames':9}]

@pytest.mark.parametrize('mode',t.MATCH_MODES)
@pytest.mark.parametrize('n',[1,2,3,4,6,7,12,13,25,251])
@pytest.mark.parametrize('same',[False,True])
def test_schedule(mode,n,same):
    rows=plan(n,same);before=[dict(r) for r in rows]
    assert t.schedule(rows,mode)==t.schedule(rows,mode.removeprefix('match-'))
    assert rows==before

@pytest.mark.parametrize('prev',[1,2,10,125,251])
@pytest.mark.parametrize('n',[3,6,12,25])
def test_graph(prev,n):
    length=min(n,12);g=t.endpoint_graph(prev,n,n-length,length)
    assert f'trim=start_frame={prev-1}:end_frame={prev}' in g
    assert 'trim=start_frame=0:end_frame=1' in g
    assert g.count('loop=loop=-1:size=1:start=0')==2
    assert g.endswith(t.filter_graph(n,n-length,length).split('[a][b]')[1])

@pytest.mark.parametrize('prev',[0,-1,252,True,None,'1',1.5])
def test_invalid_previous(prev):
    with pytest.raises(ValueError):t.endpoint_graph(prev,6,0,6)

@pytest.mark.parametrize('args',[(2,0,2),(6,1,6),(6,-1,7),(13,0,13),(True,0,3),(6,0,True),(6,0,6.0),(100000001,99999995,6)])
def test_invalid_geometry(args):
    with pytest.raises(ValueError):t.endpoint_graph(10,*args)

@pytest.mark.skipif(not shutil.which('ffmpeg'),reason='FFmpeg required')
@pytest.mark.parametrize('prev',[1,3,10])
@pytest.mark.parametrize('pause',[3,6,13])
def test_render(tmp_path,prev,pause):
    # Distinct luma per input frame makes incorrect frame selection observable.
    w,h=32,24;size=w*h*3//2
    def frame(y):return bytes([y])*(w*h)+bytes([128])*(w*h//2)
    a=tmp_path/'a.yuv';b=tmp_path/'b.yuv'
    a.write_bytes(b''.join(frame(32+i*3) for i in range(prev)))
    b.write_bytes(frame(190)+frame(220)+frame(235))
    n=min(pause,6);start=pause-n
    inp=lambda p:['-f','rawvideo','-pixel_format','yuv420p','-video_size',f'{w}x{h}','-framerate','25','-i',str(p)]
    cmd=['ffmpeg','-nostdin','-v','error',*inp(a),*inp(b),'-filter_complex_threads','1','-filter_complex',t.endpoint_graph(prev,pause,start,n),'-map','[out]','-frames:v',str(pause),'-threads','1','-pix_fmt','yuv420p','-f','rawvideo','-']
    r=subprocess.run(cmd,capture_output=True,check=True,timeout=20)
    assert len(r.stdout)==pause*size
    vals=[r.stdout[i*size] for i in range(pause)]
    assert vals[:start+1]==[32+(prev-1)*3]*(start+1)
    assert vals[-1]==190 and vals==sorted(vals)
    assert vals[-2]<190

@pytest.mark.parametrize('mode',t.MATCH_MODES)
def test_render_order(tmp_path,monkeypatch,mode):
    from podcast_gpt import studio_neural as sn
    from PIL import Image
    dest=tmp_path/'audio';temp=tmp_path/'render';temp.mkdir()
    rows=plan(13)
    for row,cid in zip(rows,('0001','0001','0002')):row['id']=cid
    done={}
    for cid in ('0001','0002'):
        p=dest/sn.neural.FOLDER/cid/'face.mp4';p.parent.mkdir(parents=True);p.write_bytes(cid.encode())
        done[cid]={'mp4_sha256':sn.source.digest(p)}
    monkeypatch.setattr(sn,'_portraits',lambda *a:({1:b'',2:b''},{'A':1,'B':2}))
    monkeypatch.setattr(sn.studio,'card',lambda *a,**kw:Image.new('RGB',(720,720)))
    monkeypatch.setattr(sn.studio,'active_rect',lambda *a:(20,70,160,120))
    counts={};order=[]
    def command(args,**kw):
        from pathlib import Path
        path=Path(args[-1]);order.append(path.name)
        if path.name=='segment00001.mp4':
            for i in (0,2):
                prior=temp/f'segment{i:05}.mp4'
                assert str(prior) in args and prior.is_file()
            assert 'trim=start_frame=9:end_frame=10' in args[args.index('-filter_complex')+1]
        counts[str(path)]=int(args[args.index('-frames:v')+1]);path.touch()
    monkeypatch.setattr(sn.media,'cmd',command)
    monkeypatch.setattr(sn.export,'_video_frames',lambda path:counts[str(path)])
    listing=sn._segments(None,dest,None,done,{'video_format':'square'},{'layout':'spotlight','transition':mode},None,rows,temp)
    assert order==['segment00000.mp4','segment00002.mp4','segment00001.mp4']
    assert list(counts.values())==[10,9,13]
    assert listing.read_text().splitlines()[1:]==[f'file segment{i:05}.mp4' for i in range(3)]
