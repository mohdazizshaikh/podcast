"""Broad inexpensive compatibility/regression matrix; not real model inference."""
import pytest
from podcast_gpt import kokoro_languages as langs,studio_preview as studio,v4_preview as preview
from podcast_gpt import loudness_gain as gain,dashboard_authoring as author
from podcast_gpt import dependency_setup,cli

# 39 positive and 39 negative cases. One exact preset per case.
VOICES=[(code,voice) for code,presets in langs.PRESETS.items() for voice in sorted(presets)]


@pytest.mark.parametrize("code,voice",VOICES)
def test_each_voice_compatible(code,voice):
    assert langs.preset({"engine":"kokoro","language":code,"preset":voice},code)==voice


@pytest.mark.parametrize("code,voice",VOICES)
def test_each_voice_rejects_cross_language(code,voice):
    wrong="es" if code!="es" else "hi"
    with pytest.raises(ValueError):
        langs.preset({"engine":"kokoro","language":wrong,"preset":voice},wrong)


# 60 layout/size/cast combinations, all active speakers and cell bounds checked.
@pytest.mark.parametrize("size",list(preview.SIZES.values()))
@pytest.mark.parametrize("count",range(1,11))
@pytest.mark.parametrize("layout",studio.LAYOUTS)
def test_every_studio_geometry(size,count,layout):
    for active in range(1,count+1):
        cells=studio.geometry(range(1,count+1),active,size,layout)
        assert len(cells)==(count if layout=="grid" else 1)
        for x,y,w,h in cells.values():
            assert min(w,h)>0 and x>=0 and y>=0 and x+w<=size[0] and y+h<=size[1]
        x,y,w,h=studio.active_rect(range(1,count+1),active,size,layout)
        assert all(v%2==0 for v in (x,y,w,h)) and min(w,h)>0 and x+w<=size[0] and y+h<=size[1]


@pytest.mark.parametrize("value",[-25,-13,True,False,None,"-16",float("nan"),-16.0])
def test_invalid_loudness_target(value):
    with pytest.raises(ValueError):gain.target(value)


@pytest.mark.parametrize("value",[b"[]",b"null",b"true",b"1",b'"x"',b"",b"\xff",b"x"*32769])
def test_invalid_authoring_body(value):
    with pytest.raises(ValueError):author.parse(value)


def test_mandarin_group():
    assert "misaki[zh]>=0.9,<1" in dependency_setup.GROUPS["kokoro-mandarin"]
    assert cli.parse(["dependency-plan","--group","kokoro-mandarin"]).operation=="dependency-plan"
