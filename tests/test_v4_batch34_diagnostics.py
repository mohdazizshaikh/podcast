"""Batch 34 synthetic evidence and PCM regression matrix."""
import struct
import wave
import pytest
from podcast_gpt import research_coverage as research, video_audio_check as audio


@pytest.mark.parametrize("quote",["exact shared excerpt", "Hindi संवाद का उदाहरण", "UPPER Case text", "a  double  space quote", "punctuation: exact!", "123456789012"])
@pytest.mark.parametrize("variant,expected",[("same",True),("wrapped",True),("absent",False),("extra",True),("empty",False)])
def test_exact_excerpt_overlap(quote,variant,expected):
    other={"same":quote,"wrapped":"before "+quote+" after","absent":"unrelated",
           "extra":quote+quote,"empty":""}[variant]
    rows=research.excerpt_overlap([{"source_id":"S01","quote":quote}],
                                  {"S01":quote,"S02":other})
    assert rows==[{"source_id":"S01","quote_length":len(quote),
                   "other_matching_source_ids":["S02"] if expected else []}]


def test_overlap_order_and_no_self():
    quote="exact shared excerpt"
    rows=research.excerpt_overlap([{"source_id":"S02","quote":quote}],
                                   {"S03":quote,"S02":quote,"S01":quote})
    assert rows[0]["other_matching_source_ids"]==["S01","S03"]
    assert research.excerpt_overlap([],{"S01":quote})==[]


@pytest.mark.parametrize("amp",[100,500,1000,3000,8000,15000])
@pytest.mark.parametrize("mode",["identical","silence","constant","offset","inverse","short"])
def test_pcm_fault_matrix(amp,mode):
    n=100 if mode=="short" else 1600
    x=[-amp,amp]*(n//2)
    y={"identical":x,"silence":[0]*n,"constant":[500]*n,
       "offset":[v+500 for v in x],"inverse":[-v for v in x],"short":[0]*n}[mode]
    m=audio.compare_window(x,y)
    assert m["reference_ac_rms_pcm"]==amp
    flags=audio.extra_window_flags(m,n)
    if mode in ("silence","constant"):
        assert "missing_variable_audio" in flags
        assert "uncorrelatable_audio_mismatch" in flags
    else:
        assert "missing_variable_audio" not in flags
        assert "uncorrelatable_audio_mismatch" not in flags
    assert ("dc_offset_difference" in flags)==(mode in ("constant","offset"))
    if mode=="short":
        assert flags==[]


def wav(path,values):
    with wave.open(str(path),"wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(struct.pack("<"+"h"*len(values),*values))


def test_dropouts_are_counted_and_examples_truncated(tmp_path):
    a,b=tmp_path/"a.wav",tmp_path/"b.wav"
    wav(a,[-1000,1000]*8000*21+[0]*100)
    wav(b,[500]*16000*21+[0]*200)
    r=audio.compare_wavs(a,b)
    assert r["flagged_window_count"]==21
    assert len(r["flagged_window_examples"])==20 and r["flagged_examples_truncated"]
    assert r["additional_flag_counts"]["missing_variable_audio"]==21
    assert r["additional_flag_counts"]["dc_offset_difference"]==21
    assert r["uncompared_decoded_frames"]==100
    assert r["short_window_count"]==1 and r["window_count"]==22
