import json
from pathlib import Path

import pytest
from podcast_gpt import source,neural,review


def test_initial_progress_no_fake_model(chunk_studio):
    state=neural.progress(chunk_studio,allow_short=True)
    assert state["verified"]==0
    assert state["remaining"]==45
    assert not state["all_speech_neural_clips_structurally_present"]
    assert not state["three_presenter_samples_ready"]
    assert not (chunk_studio/"source"/neural.LOCK).exists()


def test_explicit_consent_and_invalid_limits_block_before_model(chunk_studio):
    with pytest.raises(ValueError,match="rights"):
        neural.run_cpu(chunk_studio,mode="pilot",max_new=3,rights_confirmed=False,allow_short=True)
    with pytest.raises(ValueError):
        neural.run_cpu(chunk_studio,mode="pilot",max_new=5,rights_confirmed=True,allow_short=True)
    with pytest.raises(ValueError):
        neural.run_cpu(chunk_studio,mode="batch",max_new=6,rights_confirmed=True,allow_short=True)
    assert not (chunk_studio/"previews"/"001-001.mp4").exists()


def test_pilot_targets_three_distinct_original_speakers(chunk_studio):
    plan=source.verify_chunks(chunk_studio,allow_short=True)
    assert neural.pilot_targets(plan,{})==["001-001","002-001","003-001"]
    assert neural.pilot_targets(plan,{"001-001":"fakehash"})==["002-001","003-001"]


def test_orphan_json_video_symlink_and_unknown_outputs_refused(chunk_studio):
    saved=chunk_studio/"previews"/"001-001.json"
    saved.write_text('{}',encoding="utf-8")
    with pytest.raises(ValueError,match="Orphan"):
        neural.progress(chunk_studio,allow_short=True)
    saved.unlink()
    (chunk_studio/"previews"/"work-abandoned").mkdir()
    with pytest.raises(ValueError,match="Unexpected"):
        neural.progress(chunk_studio,allow_short=True)


def test_no_full_compose_without_all_genuine_samples(chunk_studio):
    with pytest.raises(ValueError,match="All genuine"):
        neural.compose_neural(chunk_studio,allow_short=True)


def test_no_human_review_without_genuine_verified_previews(chunk_studio):
    with pytest.raises(ValueError,match="preview missing"):
        review.review_pilot(chunk_studio,allow_short=True)


def test_no_manual_record_with_unsupported_acknowledgment(chunk_studio):
    with pytest.raises(ValueError,match="Explicit"):
        review.record_pilot(chunk_studio,{"aarav":"PASS","meera":"PASS","kabir":"PASS"},"NO",allow_short=True)


def test_saved_cpu_lock_refuses_inference(chunk_studio):
    lock=chunk_studio/"source"/neural.LOCK
    lock.write_text("ABANDONED",encoding="utf-8")
    with pytest.raises(ValueError,match="lock"):
        neural.run_cpu(chunk_studio,mode="pilot",max_new=3,rights_confirmed=True,allow_short=True)
    assert lock.read_text()=="ABANDONED"


def test_full_human_navigator_requires_verified_real_candidate(chunk_studio):
    with pytest.raises((ValueError,FileNotFoundError)):
        review.review_full(chunk_studio,allow_short=True)