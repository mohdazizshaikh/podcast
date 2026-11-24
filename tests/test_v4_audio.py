import struct
import wave
import pytest
from PIL import Image
from podcast_gpt import v4_audio as audio, characters, projects, script_review, cli, source


def profile(name):
    return {"name":name,"personality":"Curious","speaking_style":"Friendly","appearance":"Fictional presenter",
            "voice_preferences":{"engine":"imported","language":"Hindi","preset":"","style_notes":""}}


def ready(tmp_path,monkeypatch):
    root=tmp_path/"private"
    req={"topic":"Science","language":"Hindi","duration_minutes":1,"presenters":["A","B"],
         "video_format":"square","workflow":"manual","input_kind":"topic","research_mode":"knowledge"}
    pid=projects.create(root,req)["project_id"]
    ids={}
    for name,color in (("A","red"),("B","blue")):
        p=tmp_path/(name+".png");Image.new("RGB",(200,200),color).save(p)
        ids[name]=characters.create(root,profile(name),portrait=p,acknowledgment=characters.ACK)["character_id"]
    characters.assign(root,pid,ids)
    current={"version_sha256":"a"*64,"turns":[{"id":"0001","speaker":"A","text":"First synthetic speech fixture."},
                                           {"id":"0002","speaker":"B","text":"Second synthetic speech fixture."}]}
    def review(root,pid,*,require_pass):
        assert require_pass
        return current
    monkeypatch.setattr(script_review,"current_script",review)
    return root,pid,current


def wav(path,frames,amplitude=100,rate=16000):
    with wave.open(str(path),"wb") as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate)
        w.writeframes(struct.pack("<h",amplitude)*frames)
    return path


def test_exact_timeline_resume_and_version_isolation(tmp_path,monkeypatch):
    root,pid,current=ready(tmp_path,monkeypatch)
    assert audio.inspect(root,pid)["missing_turn_ids"]==["0001","0002"]
    assert audio.voice_status(root,pid)["voices"][0]["status"]=="authorized_wav_import_supported"
    a=wav(tmp_path/"a.wav",30*16000,100)
    b=wav(tmp_path/"b.wav",29*16000,200)
    with pytest.raises(ValueError,match="acknowledgment"):audio.import_turn(root,pid,"0001",a,acknowledgment="YES")
    assert audio.import_turn(root,pid,"0001",a,acknowledgment=audio.ACK)["imported_turns"]==1
    with pytest.raises(ValueError,match="all script"):audio.finalize(root,pid)
    with pytest.raises(ValueError,match="already imported"):audio.import_turn(root,pid,"0001",a,acknowledgment=audio.ACK)
    with pytest.raises(ValueError,match="Duplicate"):audio.import_turn(root,pid,"0002",a,acknowledgment=audio.ACK)
    audio.import_turn(root,pid,"0002",b,acknowledgment=audio.ACK)
    result=audio.finalize(root,pid)
    assert result["measured_audio_seconds"]==59.25 and result["within_target_10_percent"]
    assert not result["human_audio_quality_approved"]
    timeline=audio.show(root,pid)["timeline"]
    assert timeline["rows"][1]["start_frame"]==30*16000+4000
    assert timeline["total_frames"]==59*16000+4000
    assert audio.finalize(root,pid)["timeline_sha256"]==source.json_digest(timeline)
    dest=audio._context(root,pid)[1]
    old=(dest/audio.TIMELINE).read_bytes()
    current["version_sha256"]="b"*64
    assert audio.inspect(root,pid)["imported_turns"]==0
    assert (dest/audio.TIMELINE).read_bytes()==old


def test_bad_pcm_and_tampering(tmp_path,monkeypatch):
    root,pid,_=ready(tmp_path,monkeypatch)
    bad=wav(tmp_path/"bad.wav",16000,rate=8000)
    with pytest.raises(ValueError,match="16kHz"):audio.import_turn(root,pid,"0001",bad,acknowledgment=audio.ACK)
    silent=wav(tmp_path/"silent.wav",16000,amplitude=0)
    with pytest.raises(ValueError,match="Silent"):audio.import_turn(root,pid,"0001",silent,acknowledgment=audio.ACK)
    valid=wav(tmp_path/"valid.wav",16000)
    audio.import_turn(root,pid,"0001",valid,acknowledgment=audio.ACK)
    dest=audio._context(root,pid)[1]/"0001"/"speech.wav"
    wav(dest,16000,amplitude=250)
    with pytest.raises(ValueError,match="hash"):audio.inspect(root,pid)


def test_cli_voice_status_and_read_only(tmp_path,monkeypatch):
    root,pid,_=ready(tmp_path,monkeypatch)
    result=cli.execute(cli.parse(["--workspace",str(root),"project-voice-status","--project-id",pid]))
    assert result["network_requests"]==0
    assert not (projects.project(root,pid)/audio.FOLDER).exists()
