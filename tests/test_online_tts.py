"""OFFLINE simulated Edge-TTS provider; NEVER sends a network request.

Tests only the optional explicit online path's no-overwrite, SHA and
private-volume behavior using locally synthesized placeholder MP3.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from podcast_gpt import cli,source

pytestmark=pytest.mark.skipif(
    not shutil.which("ffmpeg"),reason="Real FFmpeg required for offline mock audio")


@pytest.fixture
def fake_edge(tmp_path,monkeypatch):
    calls=[]
    def install(root:Path,*,change_project=False):
        class FakeCommunicate:
            def __init__(self,text,voice,rate):
                calls.append((text,voice,rate))
            async def save(self,filename):
                path=Path(filename)
                assert path.parent.parent==(root/"scratch")
                subprocess.run([
                    "ffmpeg","-y","-hide_banner","-v","error",
                    "-f","lavfi","-i","sine=frequency=440:duration=2",
                    "-c:a","libmp3lame","-q:a","7",str(path)
                ],check=True,timeout=45)
                if change_project:
                    project_path=root/"project.json"
                    project=json.loads(project_path.read_text(encoding="utf-8"))
                    project["turns"][0]["text"]+=" परीक्षण"
                    project_path.write_text(json.dumps(project,ensure_ascii=False),
                                            encoding="utf-8")
        monkeypatch.setitem(sys.modules,"edge_tts",
                            SimpleNamespace(Communicate=FakeCommunicate))
    return install,calls


def test_explicit_online_tts_private_wav_and_source_receipt_no_overwrite(
        private_studio,fake_edge):
    root=private_studio
    (root/"voices"/"001.wav").unlink()
    install,calls=fake_edge
    install(root)
    a=cli.parse(["--workspace",str(root),"tts-one","--turn","1",
                 "--allow-network-tts"])
    result=cli.execute(a)
    assert result["saved_original_hindi_wav"]=="001"
    assert result["network_tts_used"] is True
    assert result["human_voice_quality_approved"] is False
    assert len(calls)==1 and calls[0][1]=="hi-IN-MadhurNeural"
    voice=root/"voices"/"001.wav"
    source.wav_info(voice)
    receipt=source.read_json(root/"voices"/"001.edge-tts-source.json")
    assert receipt["wav_sha256"]==source.digest(voice)
    assert receipt["project_sha256"]==source.json_digest(source.load_project(root))
    assert receipt["network_tts_used"] is True
    assert receipt["full_ten_minute_neural_video_completed"] is False
    with pytest.raises(ValueError,match="never overwrite"):
        cli.execute(a)
    assert len(calls)==1
    assert not list((root/"scratch").glob("hindi-online-tts-*"))


def test_online_tts_refuses_source_already_sha_bound_before_provider(
        signed_studio,fake_edge):
    root=signed_studio
    (root/"voices"/"001.wav").unlink()
    install,calls=fake_edge
    install(root)
    a=cli.parse(["--workspace",str(root),"tts-one","--turn","1",
                 "--allow-network-tts"])
    with pytest.raises(ValueError,match="SHA-bound"):
        cli.execute(a)
    assert not calls
    assert not (root/"voices"/"001.edge-tts-source.json").exists()
    assert not (root/"voices"/"001.wav").exists()


def test_online_tts_changed_project_during_async_network_is_refused(
        private_studio,fake_edge):
    root=private_studio
    (root/"voices"/"001.wav").unlink()
    install,calls=fake_edge
    install(root,change_project=True)
    a=cli.parse(["--workspace",str(root),"tts-one","--turn","1",
                 "--allow-network-tts"])
    with pytest.raises(ValueError,match="changed during online TTS"):
        cli.execute(a)
    assert len(calls)==1
    assert not (root/"voices"/"001.wav").exists()
    assert not (root/"voices"/"001.edge-tts-source.json").exists()


def test_online_tts_without_consent_does_not_contact_provider(
        private_studio,fake_edge):
    root=private_studio
    (root/"voices"/"001.wav").unlink()
    install,calls=fake_edge
    install(root)
    a=cli.parse(["--workspace",str(root),"tts-one","--turn","1"])
    with pytest.raises(ValueError,match="explicit"):
        cli.execute(a)
    assert not calls
    assert not (root/"voices"/"001.wav").exists()
