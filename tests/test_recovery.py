"""No genuine model or user media: preserve synthetic failed scratch."""
import pytest
from podcast_gpt import neural, recovery, readiness, source


def test_archive_preserves_failed_logs_and_source(chunk_studio):
    root=chunk_studio
    attempt=root/"scratch"/"model-001-001"
    attempt.mkdir()
    (attempt/"model-stderr.log").write_text("test failure",encoding="utf-8")
    (attempt/"incomplete.mp4").write_bytes(b"not real video")
    signed=source.digest(root/"source"/source.CHUNK_FILE)
    state=recovery.inspect(root,allow_short=True)
    assert state["attempts"]==[{"chunk_id":"001-001","eligible_for_explicit_archive":True}]
    assert state["files_changed"]==0
    state=readiness.inspect(root,allow_short=True)
    assert "interrupted_model_attempts" in state["blocked_stages"]
    with pytest.raises(ValueError,match="acknowledgment"):
        recovery.archive(root,"001-001",acknowledgment="NO",allow_short=True)
    assert attempt.exists()
    result=recovery.archive(root,"001-001",acknowledgment=recovery.ACK,allow_short=True)
    from pathlib import Path
    dest=Path(result["private_archive"])
    assert (dest/"model-stderr.log").read_text()=="test failure"
    assert (dest/"incomplete.mp4").read_bytes()==b"not real video"
    assert not attempt.exists()
    assert source.digest(root/"source"/source.CHUNK_FILE)==signed
    assert neural.progress(root,allow_short=True)["verified"]==0
    assert recovery.inspect(root,allow_short=True)["attempts"]==[]
    assert not (root/"source"/neural.LOCK).exists()


def test_recovery_refuses_active_cpu_lock(chunk_studio):
    with neural.cpu_session_lock(chunk_studio):
        lock=chunk_studio/"source"/neural.LOCK
        old=lock.read_bytes()
        assert neural.LOCK in recovery.inspect(chunk_studio,allow_short=True)["active_or_orphan_locks"]
        with pytest.raises(ValueError,match="lock"):
            recovery.archive(chunk_studio,"001-001",acknowledgment=recovery.ACK,allow_short=True)
        assert lock.read_bytes()==old


def test_recovery_refuses_orphan_preview_and_unknown_chunk(chunk_studio):
    root=chunk_studio
    with pytest.raises(ValueError,match="signed source"):
        recovery.archive(root,"999-999",acknowledgment=recovery.ACK,allow_short=True)
    attempt=root/"scratch"/"model-001-001"
    attempt.mkdir()
    (root/"previews"/"001-001.mp4").write_bytes(b"partial")
    with pytest.raises(ValueError,match="Orphan"):
        recovery.archive(root,"001-001",acknowledgment=recovery.ACK,allow_short=True)
    assert attempt.exists()
    assert (root/"previews"/"001-001.mp4").exists()


def test_recovery_refuses_unsafe_link(chunk_studio,tmp_path):
    target=tmp_path/"outside"
    target.mkdir()
    link=chunk_studio/"scratch"/"model-001-001"
    try:
        link.symlink_to(target,target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation unavailable")
    with pytest.raises(ValueError,match="unsafe"):
        recovery.archive(chunk_studio,"001-001",acknowledgment=recovery.ACK,allow_short=True)
    assert link.is_symlink() and target.is_dir()
