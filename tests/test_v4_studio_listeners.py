import subprocess,shutil
import pytest
from podcast_gpt import studio_listeners as l

@pytest.mark.parametrize('mode',l.MODES)
@pytest.mark.parametrize('count',range(1,11))
@pytest.mark.parametrize('start',[0,199])
def test_graph(mode,count,start):
    rects={i:(i*20,20,20,40) for i in range(1,count)}
    parts,base=l.graph(rects,mode,12,start)
    if mode=='static' or not rects:assert parts==[] and base=='[0:v]'
    else:
        assert len(parts)==1+2*len(rects) and base==f'[lb{len(rects)}]'
        for i in rects:assert f'on+{(start+37*i)%200}' in ';'.join(parts)

@pytest.mark.parametrize('mode',[None,True,0,[],{},'', 'nod','DRIFT'])
def test_invalid(mode):
    with pytest.raises(ValueError):l.validate(mode)

@pytest.mark.parametrize('active',[1,2,3])
@pytest.mark.parametrize('size',[(1280,720),(720,1280),(720,720)])
def test_regions(active,size):
    cards={i:(20+150*(i-1),70,140,180) for i in range(1,4)}
    out=l.regions(cards,active,size)
    assert set(out)==set(cards)-{active}
    for i,(x,y,w,h) in out.items():
        a,b,c,d=cards[i];assert all(v%2==0 for v in (x,y,w,h))
        assert a<x and b<y and x+w<a+c and y+h<b+d-20

@pytest.mark.parametrize('rects',[{1:(0,0,21,40)},{1:(-2,0,20,40)},{1:(0,0,0,40)},{11:(0,0,20,40)}])
def test_bad_rect(rects):
    with pytest.raises(ValueError):l.graph(rects,'drift',12,0)

@pytest.mark.skipif(not shutil.which('ffmpeg'),reason='FFmpeg required')
@pytest.mark.parametrize('mode',['drift','breathe'])
@pytest.mark.parametrize('count',[1,2])
def test_render(mode,count):
    rects={i:(16+128*(i-1),16,128,96) for i in range(1,count+1)}
    parts,base=l.graph(rects,mode,101,0)
    vf=';'.join(parts+[base+'format=rgb24[out]'])
    r=subprocess.run(['ffmpeg','-nostdin','-v','error','-f','lavfi','-i','testsrc2=size=320x160:rate=25','-filter_complex_threads','1','-filter_complex','[0:v]trim=end_frame=1,loop=loop=-1:size=1:start=0,setpts=N/(25*TB)[still];'+vf.replace('[0:v]','[still]'),'-map','[out]','-frames:v','101','-threads','1','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True,check=True,timeout=30)
    size=320*160*3;assert len(r.stdout)==101*size
    first=r.stdout[:size];last=r.stdout[-size:]
    assert any(r.stdout[i:i+size]!=first for i in range(size,len(r.stdout),size))
    assert first[:16*320*3]==last[:16*320*3]

@pytest.mark.parametrize('mode',l.MODES)
def test_settings_and_markup(tmp_path,monkeypatch,mode):
    from podcast_gpt import studio_preview as studio,cli,web
    from test_v4_preview import fixture
    root,pid=fixture(tmp_path,monkeypatch)
    result=studio.configure(root,pid,layout='spotlight',listener_motion=mode)
    assert studio.inspect_settings(root,pid)==result
    assert result['settings'].get('listener_motion','static')==mode
    assert ('listener_motion' in result['settings'])==(mode!='static')
    assert cli.parse(['project-studio-configure','--project-id',pid,'--layout','spotlight','--listener-motion',mode]).listener_motion==mode
    assert 'v4StudioListeners' in web.html_page('test')

@pytest.mark.parametrize('mode',['drift','breathe'])
def test_focus_rejection(mode):
    from podcast_gpt import studio_preview as studio
    with pytest.raises(ValueError,match='requires grid or spotlight'):
        studio.configure(None,None,layout='focus',listener_motion=mode)
