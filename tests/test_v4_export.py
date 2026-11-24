"""Short synthetic media only; never genuine lip-sync evidence."""
import json
import shutil
from pathlib import Path

import pytest
from podcast_gpt import v4_neural as neural, v4_export as export, media, source
from test_v4_preview import fixture,approve


def test_cumulative_rounding():
    timeline={"sample_rate":16000,"total_frames":36000,"rows":[
        {"turn_id":"0001","speaker":"A","start_frame":0,"speech_end_frame":16000,"end_frame":20000,"pause_frames":4000},
        {"turn_id":"0002","speaker":"B","start_frame":20000,"speech_end_frame":36000,"end_frame":36000,"pause_frames":0}]}
    rows=[{"id":"0001-01","turn_id":"0001","speaker":"A","start_frame":0,"end_frame":16000},
          {"id":"0002-01","turn_id":"0002","speaker":"B","start_frame":0,"end_frame":16000}]
    plan=export.frame_plan(timeline,rows)
    assert [r["frames"] for r in plan]==[25,6,25]
    assert sum(r["frames"] for r in plan)==56
    rows[1]["start_frame"]=1
    with pytest.raises(ValueError,match="contiguous"):export.frame_plan(timeline,rows)


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"),reason="FFmpeg required")
@pytest.mark.parametrize("fmt",["landscape","vertical","square"])
def test_export_fixture_gate_and_audit(tmp_path,monkeypatch,fmt):
    root,pid=fixture(tmp_path,monkeypatch,fmt);approve(root,pid)
    with pytest.raises(ValueError,match="Complete every"):export.compose(root,pid)
    monkeypatch.setattr(neural,"_installation",lambda m,p:(m,p))
    monkeypatch.setattr(neural,"_model_hash",lambda *a:"b"*64)
    monkeypatch.setattr(neural.shutil,"disk_usage",lambda p:type("Disk",(),{"free":20*1024**3})())
    def runner(model,python,scratch,timeout,threads):
        path=scratch/"fixture.mp4"
        # Different audio in model output deliberately; final uses master.
        media.cmd(["ffmpeg","-nostdin","-hide_banner","-v","error","-f","lavfi","-i","color=c=blue:s=256x256:r=25",
                   "-f","lavfi","-i","anullsrc=r=16000:cl=mono","-t","1","-c:v","libx264","-pix_fmt","yuv420p","-c:a","aac",str(path)],timeout=60)
        return path
    neural.generate(root,pid,model=tmp_path,python=tmp_path,run_local=True,acknowledgment=neural.ACK,
                    max_new=2,model_runner=runner)
    with pytest.raises(ValueError,match="pilots"):export.compose(root,pid,allow_fixture=True)
    template=Path(neural.template(root,pid)["template_path"])
    data=source.read_json(template)
    for row in data["observations"].values():
        for k in row:row[k]="PASS"
    template.write_text(json.dumps(data),encoding="utf-8")
    neural.record(root,pid,acknowledgment=neural.REVIEW_ACK)
    with pytest.raises(ValueError,match="fixture"):export.compose(root,pid)
    result=export.compose(root,pid,allow_fixture=True)
    assert result["export"]["test_fixture_only"] and not result["export"]["human_lipsync_approved"]
    assert result["export"]["measured_streams"]["decoded_video_frames"]==56
    assert export.inspect(root,pid,allow_fixture=True)==result
    assert export.compose(root,pid,allow_fixture=True)==result
    path=neural._context(root,pid)[1]/export.FOLDER/export.SRT
    assert "पहला संवाद" in path.read_text(encoding="utf-8")
    path.write_text("tampered",encoding="utf-8")
    with pytest.raises(ValueError,match="subtitle"):export.inspect(root,pid,allow_fixture=True)
