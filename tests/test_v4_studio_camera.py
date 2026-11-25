import pytest
from podcast_gpt import studio_camera as cam,studio_preview as studio,projects,cli,web
from test_v4_preview import fixture


@pytest.mark.parametrize("size",[(1280,720),(720,1280),(720,720)])
@pytest.mark.parametrize("layout",studio.LAYOUTS)
@pytest.mark.parametrize("count",[1,3,10])
@pytest.mark.parametrize("mode",cam.MODES)
def test_camera_geometry(size,layout,count,mode):
    for active in range(1,count+1):
        _,_,w,h=studio.active_rect(range(1,count+1),active,size,layout)
        text=cam.filter_suffix(mode,w,h,250)
        assert (not text) if mode=="fixed" else f"d=1:s={w}x{h}:fps=25" in text
        one=cam.filter_suffix(mode,w,h,1)
        assert bool(one)==(mode in cam.CONTINUOUS)


@pytest.mark.parametrize("mode",[None,True,1,[],{},"","zoom","pan"])
def test_invalid_mode(mode):
    with pytest.raises(ValueError):cam.validate(mode)


@pytest.mark.parametrize("geometry",[(0,20,10),(21,20,10),(20,21,10),(20,20,0),(20,20,252),(20,20,True)])
def test_invalid_geometry(geometry):
    with pytest.raises(ValueError):cam.filter_suffix("push-in",*geometry)


@pytest.mark.parametrize("mode",cam.MODES)
def test_immutable_camera_setting(tmp_path,monkeypatch,mode):
    root,pid=fixture(tmp_path,monkeypatch)
    saved=studio.configure(root,pid,layout="grid",camera=mode)
    assert saved["settings"].get("camera","fixed")==mode
    assert ("camera" in saved["settings"])==(mode!="fixed")
    assert studio.inspect_settings(root,pid)==saved
    with pytest.raises(ValueError,match="overwrite"):studio.configure(root,pid,layout="grid",camera=mode)
    assert cli.parse(["project-studio-configure","--project-id",pid,"--layout","grid","--camera",mode]).camera==mode


def test_local_preview_controls():
    html=web.html_page("test")
    assert "img-src blob:" in html and "v4PortraitViewFile" in html
    assert "seq!==mediaSequence" in html and "portraitSequence!==seq" in html
