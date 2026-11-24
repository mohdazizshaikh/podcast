"""Synthetic color/PCM fixtures only. Never genuine model evidence."""
import json
import shutil
from pathlib import Path
import pytest
from podcast_gpt import v4_neural as neural, media, source
from test_v4_preview import fixture,approve


def test_pilot_gate_and_plan(tmp_path,monkeypatch):
    root,pid=fixture(tmp_path,monkeypatch)
    approve(root,pid)
    state=neural.inspect(root,pid)
    assert state["chunk_count"]==2 and len(state["pilot_ids"])==2
    assert not state["batch_unlocked"]
    with pytest.raises(ValueError,match="Generate every"):neural.template(root,pid)
    with pytest.raises(ValueError,match="consent"):neural.generate(root,pid,model=tmp_path,python=tmp_path)
    with pytest.raises(ValueError,match="PASS"):neural.generate(root,pid,model=tmp_path,python=tmp_path,mode="batch",
          run_local=True,acknowledgment=neural.ACK)


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"),reason="FFmpeg required")
def test_synthetic_neural_resume_and_review(tmp_path,monkeypatch):
    root,pid=fixture(tmp_path,monkeypatch);approve(root,pid)
    monkeypatch.setattr(neural,"_installation",lambda m,p:(m,p))
    monkeypatch.setattr(neural,"_model_hash",lambda *a:"a"*64)
    # No physical model needed for fixture tests, bypass only disk probe.
    monkeypatch.setattr(neural.shutil,"disk_usage",lambda p:type('Disk',(),{'free':20*1024**3})())
    def runner(model,python,scratch,timeout,threads):
        video=scratch/"fixture.mp4"
        media.cmd(["ffmpeg","-nostdin","-hide_banner","-v","error","-f","lavfi","-i","color=c=blue:s=256x256:r=25",
                   "-i",str(scratch/"speech.wav"),"-t","1","-c:v","libx264","-pix_fmt","yuv420p","-c:a","aac",str(video)],timeout=60)
        return video
    opts={"model":tmp_path,"python":tmp_path,"run_local":True,"acknowledgment":neural.ACK,"model_runner":runner}
    assert len(neural.generate(root,pid,**opts)["new_chunk_ids"])==1
    assert neural.generate(root,pid,**opts)["completed_chunks"]==2
    path=Path(neural.template(root,pid)["template_path"])
    with pytest.raises(ValueError,match="UNREVIEWED"):neural.record(root,pid,acknowledgment=neural.REVIEW_ACK)
    data=source.read_json(path)
    for row in data["observations"].values():
        for k in row:row[k]="PASS"
    path.write_text(json.dumps(data),encoding="utf-8")
    state=neural.record(root,pid,acknowledgment=neural.REVIEW_ACK)
    assert state["batch_unlocked"] and state["test_fixture_only"] and not state["full_neural_video_generated"]
    assert neural.generate(root,pid,mode="batch",**opts)["new_chunk_ids"]==[]
    with pytest.raises(ValueError,match="overwritten"):neural.record(root,pid,acknowledgment=neural.REVIEW_ACK)
