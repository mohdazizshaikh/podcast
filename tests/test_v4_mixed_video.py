import json
from pathlib import Path
import pytest
from podcast_gpt import cli, source, v4_mixed_video as mixed, v4_post_audio as mix
from test_v4_preview import fixture
from test_v4_master_tts import wav


def test_parser_regression():
    assert cli.parse(["doctor"]).operation=="doctor"
    assert cli.parse(["project-incomplete-status","--project-id","x","--kind","mixed-export"]).operation=="project-incomplete-status"
    assert cli.parse(["project-mixed-video-compose","--project-id","x"]).operation=="project-mixed-video-compose"


def test_mix_review_requires_current_candidate(tmp_path,monkeypatch):
    root,pid=fixture(tmp_path,monkeypatch)
    mix.compose(root,pid,intro=wav(tmp_path/"intro.wav",500),acknowledgment=mix.ACK)
    assert mixed.qa(root,pid,"mix","status")["review_status"]=="UNREVIEWED"
    with pytest.raises(ValueError,match="listening PASS"):mixed.compose(root,pid)
    p=Path(mixed.qa(root,pid,"mix","template")["template_path"])
    with pytest.raises(ValueError,match="UNREVIEWED"):mixed.qa(root,pid,"mix","record",acknowledgment=mixed.MIX_ACK)
    value=source.read_json(p)
    for row in (value["turns"],value["criteria"]):
        for key in row:row[key]="PASS"
    p.write_text(json.dumps(value),encoding="utf-8")
    assert mixed.qa(root,pid,"mix","record",acknowledgment=mixed.MIX_ACK)["review_status"]=="PASS"
    with pytest.raises(ValueError,match="Immutable"):mixed.qa(root,pid,"mix","record",acknowledgment=mixed.MIX_ACK)


def test_frame_rounding_and_exact_subtitle_offset():
    timeline={"total_frames":36000,"sample_rate":16000,"rows":[{"start_frame":0,"speech_end_frame":16000}]}
    record={"intro_frames":16000,"speech_offset_frames":16000,"speech_and_pauses_frames":36000,"outro_frames":16000,"total_frames":68000}
    plan=mixed.scene_plan(timeline,record)
    assert plan["total_video_frames"]==106 and plan["intro_frames"]==25
    assert b"00:00:01,000 --> 00:00:02,000" in mixed.shifted_subtitles(timeline,[{"text":"test"}],16000)
