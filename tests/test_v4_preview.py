import json
import shutil
from pathlib import Path
import pytest
from podcast_gpt import v4_audio as audio, v4_master as master, v4_audio_review as review, v4_preview as preview, source
from test_v4_master_tts import ready,wav


def fixture(tmp_path,monkeypatch,fmt="square"):
    root,pid=ready(tmp_path,monkeypatch,video_format=fmt)
    for tid,amp in (("0001",100),("0002",200)):
        audio.import_turn(root,pid,tid,wav(tmp_path/(tid+".wav"),amp),acknowledgment=audio.ACK)
    audio.finalize(root,pid);master.compose(root,pid)
    return root,pid


def approve(root,pid,fail=False):
    path=Path(review.template(root,pid)["template_path"])
    data=source.read_json(path)
    data["turns"]={k:"FAIL" if fail and k=="0001" else "PASS" for k in data["turns"]}
    data["criteria"]={k:"PASS" for k in data["criteria"]}
    path.write_text(json.dumps(data),encoding="utf-8")
    return review.record(root,pid,acknowledgment=review.ACK)


def test_review_gates_and_immutable_failure(tmp_path,monkeypatch):
    root,pid=fixture(tmp_path,monkeypatch)
    assert review.inspect(root,pid)["review_status"]=="UNREVIEWED"
    with pytest.raises(ValueError,match="listening PASS"):preview.render(root,pid)
    path=Path(review.template(root,pid)["template_path"])
    with pytest.raises(ValueError,match="UNREVIEWED"):review.record(root,pid,acknowledgment=review.ACK)
    data=source.read_json(path)
    data["turns"]={k:"FAIL" for k in data["turns"]}
    data["criteria"]={k:"PASS" for k in data["criteria"]}
    path.write_text(json.dumps(data),encoding="utf-8")
    assert review.record(root,pid,acknowledgment=review.ACK)["review_status"]=="FAIL"
    with pytest.raises(ValueError,match="overwritten"):review.record(root,pid,acknowledgment=review.ACK)
    with pytest.raises(ValueError,match="listening PASS"):preview.render(root,pid)


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"),reason="FFmpeg required")
@pytest.mark.parametrize("fmt",["landscape","vertical","square"])
def test_static_preview_three_formats(tmp_path,monkeypatch,fmt):
    root,pid=fixture(tmp_path,monkeypatch,fmt)
    assert approve(root,pid)["human_audio_self_attested_pass"]
    result=preview.render(root,pid)
    streams=result["preview"]["measured_streams"]
    assert (streams["width"],streams["height"])==preview.SIZES[fmt]
    assert not result["preview"]["neural_lipsync_verified"]
    assert preview.inspect(root,pid)==result
    path=audio._context(root,pid)[1]/preview.FOLDER/preview.SRT
    text=path.read_text(encoding="utf-8")
    assert "00:00:00,000 --> 00:00:01,000" in text
    assert "00:00:01,250 --> 00:00:02,250" in text
    assert "पहला संवाद" in text
    path.write_text("changed",encoding="utf-8")
    with pytest.raises(ValueError,match="Subtitle"):preview.inspect(root,pid)
