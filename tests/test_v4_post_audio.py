import wave
from pathlib import Path
import pytest
from podcast_gpt import v4_post_audio as mix, v4_partial_recovery as recovery, v4_audio as audio, v4_master as master, projects
from test_v4_preview import fixture
from test_v4_master_tts import ready,wav


def test_mix_preserves_master_and_duration(tmp_path,monkeypatch):
    root,pid=fixture(tmp_path,monkeypatch)
    _,dest,_,_,receipt=mix._ctx(root,pid)
    original=(dest/master.FOLDER/master.WAV).read_bytes()
    intro=wav(tmp_path/"intro.wav",500);bed=wav(tmp_path/"bed.wav",1000);outro=wav(tmp_path/"outro.wav",200)
    with pytest.raises(ValueError,match="acknowledgment"):mix.compose(root,pid,intro=intro)
    result=mix.compose(root,pid,intro=intro,bed=bed,outro=outro,acknowledgment=mix.ACK)
    record=result["mix"]
    assert record["intro_frames"]==16000 and record["speech_offset_frames"]==16000
    assert record["total_frames"]==68000 and not record["human_mix_quality_approved"]
    assert mix.inspect(root,pid)==result
    assert (dest/master.FOLDER/master.WAV).read_bytes()==original
    with wave.open(result["path"],"rb") as w:
        data=mix._samples(w.readframes(w.getnframes()))
        assert max(map(abs,data))<=28000 and len(data)==68000
    with pytest.raises(ValueError,match="no overwrite"):mix.compose(root,pid,acknowledgment=mix.ACK)
    with Path(result["path"]).open("r+b") as h:h.seek(44);h.write(b"\x01\x00")
    with pytest.raises(ValueError,match="PCM differs"):mix.inspect(root,pid)


def test_partial_audio_archive_and_retry(tmp_path,monkeypatch):
    root,pid=ready(tmp_path,monkeypatch)
    _,dest,_,_,_,_=audio._context(root,pid)
    incomplete=dest/"0001";incomplete.mkdir(parents=True)
    (incomplete/"speech.wav").write_bytes(b"interrupted")
    assert recovery.inspect(root,pid,"audio-turn","0001")["eligible"]
    with projects.exclusive(projects.project(root,pid)):
        assert recovery.inspect(root,pid,"audio-turn","0001")["lock_present"]
    with pytest.raises(ValueError,match="acknowledgment"):recovery.archive(root,pid,"audio-turn","0001",acknowledgment="YES")
    result=recovery.archive(root,pid,"audio-turn","0001",acknowledgment=recovery.ACK)
    assert not incomplete.exists()
    assert (Path(result["archive_path"])/"attempt"/"speech.wav").read_bytes()==b"interrupted"
    audio.import_turn(root,pid,"0001",wav(tmp_path/"voice.wav",100),acknowledgment=audio.ACK)
    with pytest.raises(ValueError,match="Completion receipt"):recovery.archive(root,pid,"audio-turn","0001",acknowledgment=recovery.ACK)


def test_partial_mix_archive(tmp_path,monkeypatch):
    root,pid=fixture(tmp_path,monkeypatch)
    _,dest,_,_,_=mix._ctx(root,pid)
    path=dest/mix.FOLDER;path.mkdir();(path/mix.WAV).write_bytes(b"partial")
    assert recovery.inspect(root,pid,"post-audio")["eligible"]
    recovery.archive(root,pid,"post-audio",acknowledgment=recovery.ACK)
    result=mix.compose(root,pid,acknowledgment=mix.ACK)
    assert result["mix"]["total_frames"]==36000
    with pytest.raises(ValueError,match="Completion receipt"):recovery.inspect(root,pid,"post-audio")
