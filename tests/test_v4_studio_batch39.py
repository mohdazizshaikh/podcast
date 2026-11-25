import itertools
import subprocess
import shutil
import pytest
from podcast_gpt import studio_camera as cam, studio_layout as lay

@pytest.mark.parametrize('size',[(1280,720),(720,1280),(720,720)])
@pytest.mark.parametrize('count',range(1,11))
def test_spotlight_geometry(size,count):
    for active in range(1,count+1):
        rects=lay.spotlight(range(1,count+1),active,size)
        assert set(rects)==set(range(1,count+1))
        x,y,w,h=rects[active]
        for i,(a,b,c,d) in rects.items():
            assert a>=20 and b>=70 and c>36 and d>36
            assert a+c<=size[0]-20 and b+d<=size[1]-52
            if i!=active:assert w*h>c*d
        for r,s in itertools.combinations(rects.values(),2):
            x,y,w,h=r;a,b,c,d=s
            assert x+w<=a or a+c<=x or y+h<=b or b+d<=y

@pytest.mark.parametrize('mode',cam.MODES)
@pytest.mark.parametrize('frames',[1,2,125,251])
def test_camera_suffix(mode,frames):
    suffix=cam.filter_suffix(mode,320,240,frames)
    if mode=='fixed' or (frames==1 and mode not in cam.CONTINUOUS):assert suffix==''
    else:assert 'd=1:s=320x240:fps=25' in suffix

@pytest.mark.skipif(not shutil.which("ffmpeg"),reason="FFmpeg required")
@pytest.mark.parametrize('mode',cam.MODES)
def test_camera_ffmpeg(mode):
    suffix=cam.filter_suffix(mode,160,120,12)
    result=subprocess.run(['ffmpeg','-nostdin','-v','error','-f','lavfi','-i','testsrc2=size=160x120:rate=25',
        '-vf','fps=25'+suffix+',format=yuv420p','-frames:v','12','-threads','1','-f','rawvideo','-pix_fmt','yuv420p','-'],
        capture_output=True,timeout=30,check=True)
    assert len(result.stdout)==12*160*120*3//2

@pytest.mark.parametrize('indices,active,size',[([],1,(720,720)),([1,1],1,(720,720)),([1],2,(720,720)),(range(11),1,(720,720)),([1],1,(640,480))])
def test_invalid_layout(indices,active,size):
    with pytest.raises(ValueError):lay.spotlight(indices,active,size)

@pytest.mark.parametrize("mode",cam.MODES)
def test_studio_integration(tmp_path,monkeypatch,mode):
    from podcast_gpt import studio_preview as studio,cli,web
    from test_v4_preview import fixture
    root,pid=fixture(tmp_path,monkeypatch)
    saved=studio.configure(root,pid,layout="spotlight",camera=mode)
    assert saved["settings"]["layout"]=="spotlight"
    assert studio.inspect_settings(root,pid)==saved
    assert studio.geometry(range(1,4),2,(720,720),"spotlight")==lay.spotlight(range(1,4),2,(720,720))
    assert cli.parse(["project-studio-configure","--project-id",pid,"--layout","spotlight","--camera",mode]).camera==mode
    assert mode in web.html_page("test") and "spotlight" in web.html_page("test")
