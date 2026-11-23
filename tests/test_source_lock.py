"""V3.7 cross-process exclusive original Hindi voice/source-binding tests.

No user portraits, neural inference, online TTS or model downloads.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from podcast_gpt import cli, kokoro, source


def test_source_binding_fails_while_another_private_voice_session_is_active(private_studio):
    root=private_studio
    lock=root/"source"/source.ORIGINALS_LOCK
    assert not lock.exists()
    with source.original_voice_lock(root):
        assert lock.exists()
        with pytest.raises(ValueError,match="lock"):
            source.build_source(root,allow_short=True)
        assert not (root/"source"/source.SOURCE_FILE).exists()
    assert not lock.exists(), "Owned lock must be removed on normal exit"
    created=source.build_source(root,allow_short=True)
    assert created["original_turn_count"]==45
    assert not lock.exists(), "Successful BIND must release exclusive originals lock"


def test_separate_python_process_cannot_bind_while_voice_lock_exists(private_studio):
    root=private_studio
    lock=root/"source"/source.ORIGINALS_LOCK
    command=[sys.executable,"-m","podcast_gpt","--workspace",str(root),"build-source"]
    with source.original_voice_lock(root):
        done=subprocess.run(command,capture_output=True,text=True,
                            encoding="utf-8",errors="replace",timeout=30)
        assert done.returncode!=0
        assert "lock" in done.stderr.lower()
        assert not (root/"source"/source.SOURCE_FILE).exists()
        assert lock.exists()
    assert not lock.exists()


def test_offline_kokoro_cannot_start_while_binding_or_another_tts_holds_lock(private_studio):
    root=private_studio
    with source.original_voice_lock(root):
        with pytest.raises(ValueError,match="lock"):
            kokoro.generate(root,model=root/"not-installed.onnx",
                            voices=root/"not-installed.bin",turn=1,max_new=1,
                            run_local=True)
    assert not (root/"voices"/"001.kokoro-source.json").exists()


def test_online_edge_tts_does_not_contact_provider_while_originals_locked(private_studio,monkeypatch):
    root=private_studio
    contacted=[]
    # The lock refusal must occur BEFORE import/call to an external service.
    class BadProvider:
        def __init__(self,*args,**kwargs):
            contacted.append(True)
            raise AssertionError("TTS provider must NOT be contacted")
    monkeypatch.setitem(sys.modules,"edge_tts",type("Fake",(),{"Communicate":BadProvider}))
    command=cli.parse(["--workspace",str(root),"tts-one","--turn","1",
                       "--allow-network-tts"])
    with source.original_voice_lock(root):
        with pytest.raises(ValueError,match="lock"):
            cli.execute(command)
    assert contacted==[]


def test_lock_is_preserved_if_another_actor_substitutes_it(private_studio):
    root=private_studio
    lock=root/"source"/source.ORIGINALS_LOCK
    with source.original_voice_lock(root):
        lock.write_text("UNRELATED_SESSION",encoding="ascii")
    assert lock.read_text(encoding="ascii")=="UNRELATED_SESSION"
    with pytest.raises(ValueError,match="lock"):
        source.build_source(root,allow_short=True)
    # Test-only manual cleanup: production deliberately never auto-deletes an
    # unknown/abandoned lock file; user must inspect the interrupted session.
    lock.unlink()


def test_originals_lock_releases_after_inventory_validation_error(private_studio):
    root=private_studio
    (root/"voices"/"001.wav").unlink()
    with pytest.raises(ValueError):
        source.build_source(root,allow_short=True)
    assert not (root/"source"/source.ORIGINALS_LOCK).exists()
    assert not (root/"source"/source.SOURCE_FILE).exists()


def test_old_source_manifest_prevents_kokoro_without_writing_receipts(signed_studio):
    root=signed_studio
    with pytest.raises(ValueError,match="SHA-bound"):
        kokoro.generate(root,model=root/"not-installed.onnx",
                        voices=root/"not-installed.bin",turn=1,max_new=1,
                        run_local=True)
    assert not (root/"source"/source.ORIGINALS_LOCK).exists()
