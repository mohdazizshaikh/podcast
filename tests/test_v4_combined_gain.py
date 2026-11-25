"""Pure gain/receipt matrix; no network, model or FFmpeg needed."""
import pytest
from podcast_gpt import loudness_gain as gain

def measurement(lufs=-30.0,peak=-12.0):
    return {"integrated_lufs":lufs,"true_peak_dbtp":peak,"loudness_range_lu":2.0,"gating_threshold_lufs":-40.0}

@pytest.mark.parametrize("goal",[-24,-20,-16,-14])
@pytest.mark.parametrize("ceiling",[None,8000,16000,28000])
@pytest.mark.parametrize("peak",[1000,16000,32768])
def test_gain_bound_and_recipe(goal,ceiling,peak):
    before=measurement()
    ppm=gain.gain_ppm(goal,before,peak,ceiling)
    cap=gain.sample_ceiling(ceiling)
    assert 0<ppm<=4*gain.SCALE
    assert peak*ppm//gain.SCALE<=cap
    record=gain.record(goal,before,peak,"a"*64,measurement(-20,-6),ceiling)
    assert gain.validate(record)==record
    assert record["dynamic_limiter_used"] is (ceiling is not None)
    if ceiling is None:assert "sample_peak_ceiling_pcm" not in record
    else:assert record["sample_peak_ceiling_pcm"]==ceiling
    assert record["gain_ppm"]==ppm

@pytest.mark.parametrize("ceiling",[0,True,False,7999,28001,16000.0,"16000",[],{}])
def test_invalid_ceiling(ceiling):
    with pytest.raises(ValueError):gain.gain_ppm(-16,measurement(),1000,ceiling)

@pytest.mark.parametrize("ceiling",[None,8000,16000,28000])
def test_true_peak_rejection(ceiling):
    with pytest.raises(ValueError,match="true-peak"):
        gain.record(-16,measurement(),1000,"a"*64,measurement(-16,-1),ceiling)

def test_receipt_tamper():
    record=gain.record(-16,measurement(),16000,"a"*64,measurement(-16,-6),16000)
    for patch in ({"gain_ppm":record["gain_ppm"]+1},{"dynamic_limiter_used":False},{"sample_peak_ceiling_pcm":None}):
        with pytest.raises(ValueError):gain.validate({**record,**patch})
