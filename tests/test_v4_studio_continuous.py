import shutil,subprocess
import pytest
from podcast_gpt import studio_camera as cam

@pytest.mark.parametrize('mode',cam.CONTINUOUS)
@pytest.mark.parametrize('start',[0,1,199,200,201,9999])
@pytest.mark.parametrize('frames',[1,2,125,251])
def test_phase(mode,start,frames):
    suffix=cam.filter_suffix(mode,160,120,frames,start_frame=start)
    assert f'(on+{start%cam.PERIOD})/{cam.PERIOD}' in suffix
    assert 'd=1:s=160x120:fps=25' in suffix
    assert suffix==cam.filter_suffix(mode,160,120,frames,start_frame=start%cam.PERIOD)

@pytest.mark.parametrize('mode',[m for m in cam.MODES if m not in cam.CONTINUOUS])
@pytest.mark.parametrize('frames',[1,2,251])
def test_legacy_offset(mode,frames):
    assert cam.filter_suffix(mode,160,120,frames)==cam.filter_suffix(mode,160,120,frames,start_frame=451)

@pytest.mark.parametrize('offset',[-1,True,1.2,None,'1',cam.MAX_START+1])
def test_invalid_offset(offset):
    with pytest.raises(ValueError):cam.filter_suffix('continuous-drift',160,120,2,start_frame=offset)

@pytest.mark.parametrize('frames',[[1],[2,5,10],[251,6,2,200],[],[1]*100])
def test_offsets(frames):
    assert list(cam.offsets([{'frames':n} for n in frames]))==[sum(frames[:i]) for i in range(len(frames))]

@pytest.mark.parametrize('frames',[[0],[-1],[True],[1.5],[cam.MAX_START,1]])
def test_bad_plan(frames):
    with pytest.raises(ValueError):list(cam.offsets([{'frames':n} for n in frames]))

def render(mode,frames,start):
    # Repeated static source isolates camera trajectory from subject movement.
    suffix=cam.filter_suffix(mode,160,120,frames,start_frame=start)
    r=subprocess.run(['ffmpeg','-nostdin','-v','error','-f','lavfi','-i','testsrc2=size=160x120:rate=25','-vf','trim=end_frame=1,loop=loop=-1:size=1:start=0,setpts=N/(25*TB)'+suffix+',format=yuv420p','-frames:v',str(frames),'-threads','1','-f','rawvideo','-pix_fmt','yuv420p','-'],capture_output=True,timeout=30,check=True)
    assert len(r.stdout)==frames*160*120*3//2
    return r.stdout

@pytest.mark.skipif(not shutil.which('ffmpeg'),reason='FFmpeg required')
@pytest.mark.parametrize('mode',cam.CONTINUOUS)
@pytest.mark.parametrize('start,split',[(0,1),(25,20),(190,10),(199,1)])
def test_split_render(mode,start,split):
    frames=split+12
    single=render(mode,frames,start)
    assert single==render(mode,split,start)+render(mode,12,start+split)

@pytest.mark.skipif(not shutil.which('ffmpeg'),reason='FFmpeg required')
@pytest.mark.parametrize('mode',cam.CONTINUOUS)
def test_motion(mode):
    size=160*120*3//2
    raw=render(mode,101,0)
    assert raw[:size]!=raw[-size:]

@pytest.mark.parametrize('mode',cam.CONTINUOUS)
def test_settings_and_markup(tmp_path,monkeypatch,mode):
    from podcast_gpt import studio_preview as studio,cli,web
    from test_v4_preview import fixture
    root,pid=fixture(tmp_path,monkeypatch)
    result=studio.configure(root,pid,layout='spotlight',camera=mode)
    assert studio.inspect_settings(root,pid)==result
    assert result['settings']['camera']==mode
    assert cli.parse(['project-studio-configure','--project-id',pid,'--layout','spotlight','--camera',mode]).camera==mode
    assert f'value="{mode}"' in web.html_page('test')

@pytest.mark.parametrize('mode',cam.CONTINUOUS)
def test_segment_offsets_include_pause(tmp_path,monkeypatch,mode):
    from podcast_gpt import studio_neural as sn
    from PIL import Image
    dest=tmp_path/'audio';temp=tmp_path/'render';temp.mkdir()
    plan=[{'kind':'speech','speaker':'A','id':'0001','frames':10},
          {'kind':'pause','speaker':'A','id':'0001','frames':5},
          {'kind':'speech','speaker':'B','id':'0002','frames':1}]
    done={}
    for cid in ('0001','0002'):
        path=dest/sn.neural.FOLDER/cid/'face.mp4';path.parent.mkdir(parents=True);path.write_bytes(cid.encode())
        done[cid]={'mp4_sha256':sn.source.digest(path)}
    monkeypatch.setattr(sn,'_portraits',lambda *a:({1:b'',2:b''},{'A':1,'B':2}))
    monkeypatch.setattr(sn.studio,'card',lambda *a,**kw:Image.new('RGB',(720,720)))
    monkeypatch.setattr(sn.studio,'active_rect',lambda *a:(20,70,160,120))
    seen=[];original=cam.filter_suffix
    def capture(mode,w,h,n,*,start_frame=0):
        seen.append((n,start_frame))
        return original(mode,w,h,n,start_frame=start_frame)
    monkeypatch.setattr(cam,'filter_suffix',capture)
    counts={}
    def command(args,**kw):counts[args[-1]]=int(args[args.index('-frames:v')+1])
    monkeypatch.setattr(sn.media,'cmd',command)
    monkeypatch.setattr(sn.export,'_video_frames',lambda path:counts[str(path)])
    listing=sn._segments(None,dest,None,done,{'video_format':'square'},{'layout':'spotlight','camera':mode},None,plan,temp)
    assert seen==[(10,0),(1,15)]
    assert listing.read_text().count('file segment')==3
