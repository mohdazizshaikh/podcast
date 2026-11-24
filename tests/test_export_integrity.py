"""Regression tests: export locking and independent stream-duration checks."""
import json
import subprocess
import sys
from types import SimpleNamespace

import pytest

from podcast_gpt import media, neural


def test_export_lock_refuses_both_entrypoints_and_second_process(private_studio):
    root = private_studio
    lock = root / "source" / media.EXPORT_LOCK
    with media.export_lock(root):
        marker = lock.read_text(encoding="ascii")
        for export in (media.render_static, neural.compose_neural):
            with pytest.raises(ValueError, match="export lock"):
                export(root, allow_short=True)
        script = ("import sys; from pathlib import Path; "
                  "from podcast_gpt.media import render_static; "
                  "render_static(Path(sys.argv[1]), allow_short=True)")
        child = subprocess.run([sys.executable, "-c", script, str(root)],
                               capture_output=True, text=True, timeout=30)
        assert child.returncode != 0
        assert "export lock" in child.stderr
        assert lock.read_text(encoding="ascii") == marker
    assert not lock.exists()


def test_export_lock_preserves_foreign_marker_and_releases_on_exception(private_studio):
    lock = private_studio / "source" / media.EXPORT_LOCK
    with pytest.raises(RuntimeError):
        with media.export_lock(private_studio):
            raise RuntimeError("synthetic encoder error")
    assert not lock.exists()
    with media.export_lock(private_studio):
        lock.write_text("foreign", encoding="ascii")
    assert lock.read_text(encoding="ascii") == "foreign"


def probe_data():
    return {"format": {"duration": "600"}, "streams": [
        {"codec_type": "video", "codec_name": "h264", "width": 1280, "height": 720,
         "duration": "600", "disposition": {"attached_pic": 0}},
        {"codec_type": "audio", "codec_name": "aac", "sample_rate": "48000", "duration": "600"}
    ]}


@pytest.mark.parametrize("bad", [None, "N/A", "nan", "inf", "0", "-1"])
@pytest.mark.parametrize("stream_index", [0, 1])
def test_stream_duration_must_be_explicit_positive_finite(monkeypatch, tmp_path, bad, stream_index):
    path = tmp_path / "synthetic.mp4"
    path.write_bytes(b"x" * 512)
    data = probe_data()
    if bad is None:
        del data["streams"][stream_index]["duration"]
    else:
        data["streams"][stream_index]["duration"] = bad
    monkeypatch.setattr(media, "cmd", lambda *a, **k: SimpleNamespace(stdout=json.dumps(data)))
    with pytest.raises(ValueError, match="duration"):
        media.streams(path)


@pytest.mark.parametrize("stream_index", [0, 1])
def test_final_export_rejects_missing_tail_even_with_full_container(monkeypatch, tmp_path, stream_index):
    path = tmp_path / "synthetic.mp4"
    path.write_bytes(b"x" * 512)
    data = probe_data()
    data["streams"][stream_index]["duration"] = "595"
    def fake_cmd(args, **kwargs):
        assert args[0] == "ffprobe", "reject before decoding"
        return SimpleNamespace(stdout=json.dumps(data))
    monkeypatch.setattr(media, "cmd", fake_cmd)
    with pytest.raises(ValueError, match="coverage"):
        media.full_decode(path, seconds=600, require_720=True)


def test_attached_artwork_not_video(monkeypatch, tmp_path):
    path = tmp_path / "synthetic.mp4"
    path.write_bytes(b"x" * 512)
    data = probe_data()
    data["streams"][0]["disposition"]["attached_pic"] = 1
    monkeypatch.setattr(media, "cmd", lambda *a, **k: SimpleNamespace(stdout=json.dumps(data)))
    with pytest.raises(ValueError, match="artwork"):
        media.streams(path)


def test_valid_final_streams_still_decode_both_tracks(monkeypatch, tmp_path):
    path = tmp_path / "synthetic.mp4"
    path.write_bytes(b"x" * 512)
    calls = []
    def fake_cmd(args, **kwargs):
        calls.append(args)
        return SimpleNamespace(stdout=json.dumps(probe_data()))
    monkeypatch.setattr(media, "cmd", fake_cmd)
    assert media.full_decode(path, seconds=600, require_720=True)["duration"] == 600
    assert len(calls) == 3
    assert "0:v:0" in calls[1]
    assert "0:a:0" in calls[2]
