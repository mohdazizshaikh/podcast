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


def test_cumulative_original_hindi_frames_never_drift_across_ninety_segments():
    durations=[1.023,0.4]*44+[1.023]
    plan=neural.quantize_segment_frames(durations)
    assert len(plan)==89
    assert all(x>=1 for x in plan)
    assert sum(plan)==round(sum(durations)*neural.FPS)
    # Independently rounding speech and each pause separately can cause
    # a cumulative large, audible video/audio offset on 45 turns.
    naive=sum(round(duration*neural.FPS) for duration in durations)
    assert abs(naive-sum(plan))>=10
    for i in range(len(plan)):
        assert abs(sum(plan[:i+1])-round(sum(durations[:i+1])*neural.FPS))<=1


@pytest.mark.parametrize("bad", [
    [], [0], [-.1], [float("nan")], [float("inf")],
    [1,0], [False], [".4"], [0.001],
])
def test_cumulative_frame_plan_refuses_invalid_or_subframe_source(bad):
    with pytest.raises(ValueError):
        neural.quantize_segment_frames(bad)


def test_real_face_preview_rejects_video_shorter_than_signed_pcm(monkeypatch,tmp_path):
    # Synthetic decoder fixture: even if format and AAC extend to 9s,
    # a single short visual stream may not be called verified face motion.
    file=tmp_path/"model.mp4"
    file.write_bytes(b"synthetic only")
    observed=[]
    def fake_decode(path,*,seconds,require_720=False):
        observed.append(seconds)
        return {"duration":9,"audio_duration":9,"video_duration":0.25}
    monkeypatch.setattr(neural,"full_decode",fake_decode)
    with pytest.raises(ValueError,match="facial video stream"):
        neural._verify_model_clip(file,9.0)
    assert observed==[9.0]


def test_normal_real_face_preview_duration_rounding_is_accepted(monkeypatch,tmp_path):
    file=tmp_path/"source-bound.mp4"
    file.write_bytes(b"synthetic only")
    monkeypatch.setattr(neural,"full_decode",
                        lambda file,*,seconds:{"duration":seconds,
                             "audio_duration":seconds,"video_duration":seconds-.04})
    checked=neural._verify_model_clip(file,5.0)
    assert checked["video_duration"]==4.96


def test_original_speaker_frame_plan_no_monotone_overrun():
    # Real ten-minute-length episode with 90 exact speech parts, 44 pauses.
    durations=[6.0,6.0,.4]*44+[6.0,6.0]
    frames=neural.quantize_segment_frames(durations)
    assert len(frames)==134
    assert sum(frames)==round(sum(durations)*24)
    assert max(abs(sum(frames[:i+1]) /24 - sum(durations[:i+1]))
               for i in range(len(frames)))<=.5/24 + 1e-8
