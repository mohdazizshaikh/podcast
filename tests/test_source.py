import json
import wave
from pathlib import Path
from PIL import Image

import pytest
from podcast_gpt import source


def test_original_45_turn_personas_and_no_overwrite(private_studio):
    p=source.load_project(private_studio)
    assert len(p["turns"])==45
    assert set(t["speaker"] for t in p["turns"])==set(source.SPEAKERS)
    with pytest.raises(ValueError):source.init(private_studio)


def test_real_full_10_min_duration_gate_blocks_synthetic_quick_test(private_studio):
    with pytest.raises(ValueError,match="10 minutes"):
        source.build_source(private_studio)
    assert not (private_studio/"source"/source.SOURCE_FILE).exists()
    d=source.build_source(private_studio,allow_short=True)
    assert d["original_turn_count"]==45 and d["synthetic_short_test_only"]


def test_change_original_source_wav_refused_after_sha_bind(signed_studio):
    p=signed_studio/"voices"/"003.wav"
    p.write_bytes(p.read_bytes()+b"changed")
    with pytest.raises(ValueError):source.verify_source(signed_studio,allow_short=True)


def test_short_duplicate_wav_rejected(private_studio):
    p=private_studio/"voices"/"002.wav"
    p.write_bytes((private_studio/"voices"/"001.wav").read_bytes())
    with pytest.raises(ValueError,match="distinct"):
        source.build_source(private_studio,allow_short=True)


def test_exact_original_pcm_repartition_45_turns(chunk_studio):
    m=source.verify_chunks(chunk_studio,allow_short=True)
    assert m["count"]==45
    assert len(set(x["chunk_sha256"] for x in m["chunks"]))==45
    assert sum(x["frames"] for x in m["chunks"])==sum(x["frames"] for x in source.verify_source(chunk_studio,allow_short=True)["voices"].values())
    with pytest.raises(ValueError):source.prepare_chunks(chunk_studio,allow_short=True)


def test_pcm_frame_bounds_exact_no_overlap():
    for f in (16000,160001,320000,640000,1599999):
        out=source.frame_bounds(f)
        assert out[0][0]==0 and out[-1][1]==f
        assert all(b-a>=16000 and b-a<=160000 for a,b in out)
        assert all(out[i][1]==out[i+1][0] for i in range(len(out)-1))


def test_chunk_tampering_and_symlink_refused(chunk_studio):
    wav=chunk_studio/"chunks"/"002-001.wav"
    wav.write_bytes(wav.read_bytes()+b"tamper")
    with pytest.raises(ValueError):source.verify_chunks(chunk_studio,allow_short=True)


def test_unauthorized_bad_portrait_and_project_edit(signed_studio):
    portrait=signed_studio/"portraits"/"kabir.png"
    portrait.write_bytes(portrait.read_bytes()+b"edit")
    with pytest.raises(ValueError):source.verify_source(signed_studio,allow_short=True)


def test_invalid_script_wrong_count_or_voice(signed_studio):
    project=signed_studio/"project.json"
    d=json.loads(project.read_text(encoding="utf-8"));d["turns"][9]["speaker"]="unknown"
    project.write_text(json.dumps(d,ensure_ascii=False),encoding="utf-8")
    with pytest.raises(ValueError):source.verify_source(signed_studio,allow_short=True)


def test_false_completion_flags_are_explicit(chunk_studio):
    m=source.verify_chunks(chunk_studio,allow_short=True)
    assert m["human_lipsync_approved"] is False
    assert m["full_ten_minute_neural_video_completed"] is False


def test_real_ten_minute_pcm_timeline_source_binding_and_90_exact_chunks(tmp_path):
    """540–660s production gate on REAL 16k PCM file bytes, NO AI inference.

    Audio content is deliberately synthetic; this proves source duration and
    frame identity, NOT a natural Hindi voice, model or lip-sync video.
    """
    root=tmp_path/"real length FAKE synthetic no model"
    source.init(root)
    for idx, name in enumerate(source.SPEAKERS):
        Image.new("RGB",(240+idx*5,250),(90+idx*20,100,110)).save(
            root/"portraits"/(name+".png"))
    frames=source.RATE*12  # 45 * 12s speech + 44 * .4s pause = 557.6 seconds
    for turn in range(1,46):
        path=root/"voices"/f"{turn:03}.wav"
        # Every source voice receives distinct deterministic PCM bytes.
        with wave.open(str(path),"wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(source.RATE)
            wav.writeframes(bytes((turn, 0))*frames)
    bound=source.build_source(root)
    assert 540<=bound["original_seconds"]<=660
    assert bound["synthetic_short_test_only"] is False
    assert bound["original_turn_count"]==45
    chunks=source.prepare_chunks(root)
    assert chunks["count"]==90
    verified=source.verify_chunks(root)
    assert verified["count"]==90
    assert all(1<=row["duration"]<=10 for row in verified["chunks"])
    assert sum(x["frames"] for x in verified["chunks"])==45*frames
    assert source.verify_source(root)==bound
    assert verified["human_lipsync_approved"] is False
    assert verified["full_ten_minute_neural_video_completed"] is False


def test_default_45_hindi_conversation_is_unique_substantive_and_no_spoken_part_prefix(private_studio):
    script=source.load_project(private_studio)["turns"]
    dialogues=[turn["text"] for turn in script]
    assert len(dialogues)==45
    assert len(set(dialogues))==45
    assert 1400<=sum(len(text.split()) for text in dialogues)<=1700
    assert not any(text.startswith("भाग ") for text in dialogues)
    assert [sum(turn["speaker"]==name for turn in script) for name in source.SPEAKERS]==[15,15,15]
    # Script length is NOT a duration guarantee: the production gate
    # still uses actual recorded/locally generated 16k PCM frame counts.
