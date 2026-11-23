"""EXTERNAL PROCESS integration smoke with a FAKE SadTalker Python program.

Only FFmpeg test media. This DOES NOT run or authenticate pretrained
SadTalker, a real face, actual lip sync, or approved publication.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

from podcast_gpt import neural, source

pytestmark=pytest.mark.skipif(
    not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
    reason="Real FFmpeg and ffprobe are required for external bridge smoke")


def _fake_sadtalker(root: Path, *, output_variant: str="official") -> Path:
    install=root/"Local fake SadTalker CLI & Hindi test"
    (install/"src"/"config").mkdir(parents=True)
    (install/"checkpoints").mkdir()
    (install/"checkpoints"/"FAKE-TEST-WEIGHTS.safetensors").write_bytes(
        b"NOT A REAL TRAINED MODEL" * 50_000)
    inference=install/"inference.py"
    inference.write_text(
        """
import argparse
import subprocess
import wave
from pathlib import Path
parser=argparse.ArgumentParser()
parser.add_argument('--cpu',action='store_true')
parser.add_argument('--source_image',required=True)
parser.add_argument('--driven_audio',required=True)
parser.add_argument('--result_dir',required=True)
parser.add_argument('--still',action='store_true')
parser.add_argument('--preprocess',required=True)
args=parser.parse_args()
if not args.cpu or not args.still or args.preprocess!='full':
    raise SystemExit(17)
result_dir=Path(args.result_dir)
with wave.open(args.driven_audio,'rb') as w:
    duration=w.getnframes()/w.getframerate()
# This matches official SadTalker's timestamp-named MP4 placed directly
# inside --result_dir; it does NOT animate mouth pixels.
output=result_dir/'2026_11_24_00.00.00.mp4'
subprocess.run(
    ['ffmpeg','-y','-v','error','-loop','1','-framerate','24','-i',args.source_image,
     '-i',args.driven_audio,'-c:v','libx264','-preset','ultrafast',
     '-pix_fmt','yuv420p','-c:a','aac','-t',str(duration),
     '-shortest',str(output)],
    timeout=90,check=True)
""" if output_variant=="official" else """
import argparse
from pathlib import Path
parser=argparse.ArgumentParser()
parser.add_argument('--cpu',action='store_true')
parser.add_argument('--source_image',required=True)
parser.add_argument('--driven_audio',required=True)
parser.add_argument('--result_dir',required=True)
parser.add_argument('--still',action='store_true')
parser.add_argument('--preprocess',required=True)
args=parser.parse_args()
# Exit 0 without a real video file, like failed third-party output code.
Path(args.result_dir,'NO-MP4-MODEL-PRODUCED.txt').write_text('No model MP4 produced')
""",
        encoding="utf-8")
    return install


def test_real_external_process_cli_three_presenter_pilot_and_resume(chunk_studio,tmp_path):
    fake=_fake_sadtalker(tmp_path)
    done=neural.run_cpu(chunk_studio,mode="pilot",rights_confirmed=True,
                        max_new=3,wall_seconds=600,per_chunk_timeout=120,
                        sadtalker_root=fake,sadtalker_python=Path(sys.executable),
                        allow_short=True)
    assert done["new_chunk_ids"]==["001-001","002-001","003-001"]
    assert done["session_new_real_neural_calls"]==3
    assert done["three_presenter_samples_ready"] is True
    assert done["full_ten_minute_neural_video_completed"] is False
    assert not (chunk_studio/"source"/neural.LOCK).exists()
    assert not list((chunk_studio/"scratch").glob("model-*"))
    for cid in done["new_chunk_ids"]:
        mp4=chunk_studio/"previews"/(cid+".mp4")
        receipt=source.read_json(chunk_studio/"previews"/(cid+".json"))
        assert mp4.is_file()
        assert receipt["mp4_sha256"]==source.digest(mp4)
        assert receipt["actual_cpu_model_seconds"]>=0
        assert receipt["human_lipsync_approved"] is False
        assert receipt["full_ten_minute_neural_video_completed"] is False
    # Resumed pilot never silently regenerates verified existing samples.
    resume=neural.run_cpu(chunk_studio,mode="pilot",rights_confirmed=True,
                          max_new=3,wall_seconds=600,per_chunk_timeout=120,
                          sadtalker_root=fake,sadtalker_python=Path(sys.executable),
                          allow_short=True)
    assert resume["session_new_real_neural_calls"]==0
    assert resume["verified"]==3


def test_external_process_exit_zero_without_mp4_is_refused_and_no_checkpoint(chunk_studio,tmp_path):
    fake=_fake_sadtalker(tmp_path,output_variant="no-video")
    with pytest.raises(ValueError,match="ONE fresh pretrained face MP4"):
        neural.run_cpu(chunk_studio,mode="pilot",rights_confirmed=True,
                       max_new=3,wall_seconds=300,per_chunk_timeout=120,
                       sadtalker_root=fake,sadtalker_python=Path(sys.executable),
                       allow_short=True)
    assert not (chunk_studio/"previews"/"001-001.mp4").exists()
    assert not (chunk_studio/"previews"/"001-001.json").exists()
    assert not (chunk_studio/"source"/neural.LOCK).exists()
    # Failed model scratch intentionally remains for manual inspection.
    assert (chunk_studio/"scratch"/"model-001-001").is_dir()
