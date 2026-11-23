"""Real FFmpeg short synthetic tests: NOT genuine pretrained lip-sync or 10m proof."""
import json
import shutil
from pathlib import Path

import pytest

from podcast_gpt import media,neural,review,source

pytestmark=pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"),reason="FFmpeg/FFprobe needed")


def test_real_ffmpeg_45_hindi_static_aac_srt_and_decoder(signed_studio,monkeypatch):
    # Assert large intermediate encodes stay on the PRIVATE workspace drive.
    original_temp=media.tempfile.TemporaryDirectory
    temp_roots=[]
    def trace_temp(*args,**kwargs):
        temp_roots.append(kwargs.get("dir"))
        return original_temp(*args,**kwargs)
    monkeypatch.setattr(media.tempfile,"TemporaryDirectory",trace_temp)
    done=media.render_static(signed_studio,allow_short=True)
    assert temp_roots==[signed_studio/"scratch"]
    assert done["turns"]==45
    assert done["neural_lipsync_verified"] is False
    assert done["human_lipsync_approved"] is False
    assert done["measured_streams"]["video_codec"]=="h264"
    checked=media.audit_static(signed_studio,allow_short=True)
    assert checked["original_hindi_static_structurally_verified"] is True
    assert checked["media"]["width"]==1280
    assert checked["media"]["audio_codec"]=="aac"
    assert not checked["publication_approved"]
    with pytest.raises(ValueError,match="Existing"):
        media.render_static(signed_studio,allow_short=True)


def _unit_only_fake_model(root,row,scratch,timeout):
    """Only in tests, synthesizes decodable SOURCE-BOUND short STATIC face video."""
    output=scratch/"FAKE_UNIT_TEST_STATIC_FACE.mp4"
    img=root/"portraits"/(row["speaker"]+".png")
    wav=root/"chunks"/(row["id"]+".wav")
    media.cmd(["ffmpeg","-y","-hide_banner","-v","error","-loop","1","-framerate","24",
               "-i",str(img),"-i",str(wav),"-c:v","libx264","-preset","ultrafast",
               "-pix_fmt","yuv420p","-c:a","aac","-ar","48000",
               "-t",str(row["duration"]),"-shortest",str(output)],timeout=60)
    return output


def test_three_real_decoded_but_synthetic_preview_qc_rights_and_record(chunk_studio):
    done=neural.run_cpu(chunk_studio,mode="pilot",max_new=3,wall_seconds=300,
                        per_chunk_timeout=120,rights_confirmed=True,
                        allow_short=True,model_runner=_unit_only_fake_model)
    assert done["session_new_real_neural_calls"]==3
    assert done["three_presenter_samples_ready"]
    assert done["by_speaker"]=={"aarav":1,"meera":1,"kabir":1}
    assert done["full_ten_minute_neural_video_completed"] is False
    reviewer=review.review_pilot(chunk_studio,allow_short=True)
    assert reviewer["verified_samples"]==3
    with pytest.raises(ValueError,match="exists"):
        review.review_pilot(chunk_studio,allow_short=True)
    outcome=review.record_pilot(chunk_studio,{sp:"PASS" for sp in source.SPEAKERS},
                                review.ACK,allow_short=True)
    assert outcome["every_presenter_manual_pass"] is True
    assert review.inspect_pilot(chunk_studio,allow_short=True)["publication_approved"] is False
    # A different clip digest invalidates the private manual review.
    clip=chunk_studio/"previews"/"002-001.mp4"
    clip.write_bytes(clip.read_bytes()+b"CHANGED")
    with pytest.raises(ValueError):
        review.inspect_pilot(chunk_studio,allow_short=True)


def test_real_video_decoder_rejects_audio_only_file(chunk_studio,tmp_path):
    wav=chunk_studio/"chunks"/"001-001.wav"
    fake=tmp_path/"fake_audio.mp4"
    media.cmd(["ffmpeg","-y","-v","error","-i",str(wav),"-c:a","aac",str(fake)])
    with pytest.raises(ValueError,match="EXACTLY"):
        media.full_decode(fake,seconds=1)