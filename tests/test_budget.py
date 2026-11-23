"""Offline v3.2 original-source-bound CPU budget planner; NO real AI inference."""
from __future__ import annotations
import json
from pathlib import Path

import pytest
from podcast_gpt.budget import estimate_from_measured, estimate_cpu_budget
from podcast_gpt import budget, cli


def _rows():
    return [
        {"id":"001-001","speaker":"aarav","duration":5.0},
        {"id":"002-001","speaker":"meera","duration":5.0},
        {"id":"003-001","speaker":"kabir","duration":6.0},
        {"id":"004-001","speaker":"aarav","duration":5.0},
    ]


def test_no_real_measured_sample_means_no_estimate_or_inference():
    result=estimate_from_measured(_rows(),set(),{})
    assert result["estimate_available"] is False
    assert result["estimated_remaining_cpu_seconds"] is None
    assert result["measured_saved_model_cpu_samples"]==0
    assert result["new_model_inference_calls"]==0
    assert result["new_media_encoding_calls"]==0
    assert result["human_lipsync_approved"] is False


def test_verified_speaker_sample_median_fallback_is_explicit():
    result=estimate_from_measured(_rows(),{"001-001"},{"001-001":50.0})
    assert result["estimate_available"] is True
    assert result["original_pcm_chunks_total"]==4
    assert result["remaining_original_pcm_chunks"]==3
    assert result["estimated_remaining_cpu_seconds"]==160.0
    assert result["measured_speakers"]==["aarav"]
    assert result["fallback_unmeasured_speakers"]==["kabir","meera"]
    assert result["new_model_inference_calls"]==0
    assert result["estimate_is_a_guarantee"] is False
    assert result["real_ten_minute_neural_video_verified"] is False


def test_per_speaker_real_sample_is_used_when_available():
    r=estimate_from_measured(_rows(),{"001-001","002-001"},
                             {"001-001":50.0,"002-001":20.0})
    # Aarav 10 sec compute per spoken second, Meera 4; Kabir fallback 7.
    # Remaining: Kabir 6*7 + Aarav 5*10 = 92 seconds.
    assert r["estimated_remaining_cpu_seconds"]==92.0
    assert r["fallback_unmeasured_speakers"]==["kabir"]


@pytest.mark.parametrize("elapsed",[-1,0,float("nan"),float("inf"),
                                     True,"300",172801])
def test_bad_measured_model_elapsed_refused(elapsed):
    with pytest.raises(ValueError):
        estimate_from_measured(_rows(),{"001-001"},{"001-001":elapsed})


@pytest.mark.parametrize("invalid",[
    {"id":"../../x","speaker":"aarav","duration":0.2},
    {"id":"001-001","speaker":"evil","duration":5.0},
    {"id":"001-001","speaker":"aarav","duration":float("nan")},
])
def test_untrusted_edited_speech_inventory_refused(invalid):
    with pytest.raises(ValueError):
        estimate_from_measured([invalid],set(),{})


def test_foreign_timing_or_unverified_clip_refused():
    with pytest.raises(ValueError):
        estimate_from_measured(_rows(),set(),{"001-001":100.0})
    with pytest.raises(ValueError):
        estimate_from_measured(_rows(),{"999-001"},{})


def test_production_budget_wrapper_skips_explicit_fake_model_marker(tmp_path,monkeypatch):
    # Synthetic test-only replacement for an independent FFmpeg gate.
    root=tmp_path/"private"
    (root/"previews").mkdir(parents=True)
    source={"chunks":[_rows()[0]]}
    monkeypatch.setattr(budget,"verified_previews",
                        lambda real_root,allow_short=False:(source,{"001-001":"dummySHA"}))
    sidecar=root/"previews"/"001-001.json"
    sidecar.write_text(json.dumps({"TEST_ONLY_FAKE_MODEL_NOT_GENUINE_SADTALKER":True,
                                    "actual_cpu_model_seconds":900}),encoding="utf-8")
    report=estimate_cpu_budget(root)
    assert report["estimate_available"] is False
    assert report["new_model_inference_calls"]==0
    # The same test-only sidecar without the fake flag becomes a synthetic
    # estimate; production read path always first validates real MP4.
    sidecar.write_text(json.dumps({"actual_cpu_model_seconds":900}),encoding="utf-8")
    report=estimate_cpu_budget(root)
    assert report["estimate_available"] is True
    assert report["measured_saved_model_cpu_samples"]==1


def test_budget_cli_routes_read_only_without_cpu_dispatch(tmp_path,monkeypatch):
    calls=[]
    monkeypatch.setattr(budget,"estimate_cpu_budget",lambda root:(calls.append(root) or
                      {"new_model_inference_calls":0,"estimate_available":False}))
    parsed=cli.parse(["--workspace",str(tmp_path),"budget"])
    value=cli.execute(parsed)
    assert calls==[tmp_path.resolve()]
    assert value["new_model_inference_calls"]==0
