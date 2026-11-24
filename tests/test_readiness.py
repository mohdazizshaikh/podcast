"""Read-only private device readiness, synthetic original media only."""
from __future__ import annotations

from podcast_gpt import cli,readiness,source


def test_missing_workspace_does_not_create_or_approve(tmp_path):
    workspace=tmp_path/"DO_NOT_CREATE_private_studio"
    result=readiness.inspect(workspace)
    assert result["checks"]["workspace"]["status"]=="missing"
    assert not workspace.exists()
    assert result["new_model_inference_calls"]==0
    assert result["new_tts_service_calls"]==0
    assert result["new_video_render_calls"]==0
    assert result["publication_approved"] is False
    assert result["human_lipsync_accuracy_automatically_approved"] is False
    assert "INIT" in result["next_safe_action"]


def test_private_test_only_source_identifies_exact_next_steps(private_studio):
    root=private_studio
    result=readiness.inspect(root,allow_short=True)
    assert result["checks"]["script"]["status"]=="verified"
    assert result["checks"]["portrait_files"]["status"]=="present_unbound"
    assert result["checks"]["original_voice_files"]["valid_wavs"]==45
    assert result["checks"]["source_sha"]["status"]=="missing"
    assert "BIND" in result["next_safe_action"]
    assert result["all_source_and_media_structurally_verified"] is False


def test_sha_signed_original_without_chunks_next_action(signed_studio):
    result=readiness.inspect(signed_studio,allow_short=True)
    assert result["checks"]["source_sha"]["status"]=="verified"
    assert result["checks"]["exact_pcm_chunks"]["status"]=="missing"
    assert "CHUNKS" in result["next_safe_action"]


def test_complete_synthetic_45_pcm_chunks_no_face_render_next_static(chunk_studio):
    root=chunk_studio
    before={str(p):p.stat().st_mtime_ns for p in root.rglob("*") if p.is_file()}
    result=readiness.inspect(root,allow_short=True)
    after={str(p):p.stat().st_mtime_ns for p in root.rglob("*") if p.is_file()}
    assert before==after, "READINESS must never mutate original private evidence"
    assert result["checks"]["source_sha"]["status"]=="verified"
    assert result["checks"]["exact_pcm_chunks"]["status"]=="verified"
    assert result["checks"]["face_preview_mp4"]["status"]=="missing"
    assert result["checks"]["static_video"]["status"]=="missing"
    assert "STATIC" in result["next_safe_action"]
    assert result["publication_approved"] is False


def test_default_real_ten_minute_gate_refuses_short_synthetic_voices(private_studio):
    report=readiness.inspect(private_studio)
    voices=report["checks"]["original_voice_files"]
    assert voices["status"]=="blocked"
    assert voices["production_duration_gate_met"] is False
    assert "540–660" in voices["problems"]["timeline"]
    assert "STOP" in report["next_safe_action"]
    assert report["all_source_and_media_structurally_verified"] is False


def test_tampered_source_manifest_is_marked_blocked_not_completed(signed_studio):
    root=signed_studio
    p=root/"voices"/"001.wav"
    p.write_bytes(p.read_bytes()+b"tamper")
    result=readiness.inspect(root,allow_short=True)
    assert result["checks"]["source_sha"]["status"]=="blocked"
    assert "source_sha" in result["blocked_stages"]
    assert "STOP" in result["next_safe_action"]


def test_cli_readiness_does_not_start_models_or_create_workspace(tmp_path):
    workspace=tmp_path/"no-created-workspace"
    args=cli.parse(["--workspace",str(workspace),"readiness"])
    assert args.operation=="readiness"
    result=cli.execute(args)
    assert result["new_model_inference_calls"]==0
    assert not workspace.exists()



def test_readiness_refuses_a_half_written_or_crashed_voice_session(private_studio):
    root=private_studio
    with source.original_voice_lock(root):
        report=readiness.inspect(root,allow_short=True)
        assert report["checks"]["original_voice_source_session"]["status"]=="blocked"
        assert "original_voice_source_session" in report["blocked_stages"]
        assert report["all_source_and_media_structurally_verified"] is False
        assert "STOP" in report["next_safe_action"]
        assert report["new_model_inference_calls"]==0
        assert report["downloads"]==0
    report=readiness.inspect(root,allow_short=True)
    assert report["checks"]["original_voice_source_session"]["status"]=="clear"
    assert report["checks"]["original_voice_files"]["status"]=="technically_valid_unbound"



def test_readiness_stops_during_export_or_cpu_session(private_studio):
    from podcast_gpt import media, neural
    with media.export_lock(private_studio):
        report = readiness.inspect(private_studio, allow_short=True)
        assert report["blocked_stages"] == ["media_export_session"]
        assert not report["all_source_and_media_structurally_verified"]
    lock = private_studio / "source" / neural.LOCK
    lock.write_text("active or interrupted", encoding="ascii")
    report = readiness.inspect(private_studio, allow_short=True)
    assert report["blocked_stages"] == ["cpu_neural_session"]
    assert lock.exists()
