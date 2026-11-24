import io
import shutil
import struct
import wave
import pytest
from podcast_gpt import v4_audio as audio, v4_master as master, v4_tts as tts, characters, projects, script_review
from PIL import Image


def ready(tmp_path,monkeypatch,engine="imported"):
    root=tmp_path/"private"
    req={"topic":"Science","language":"Hindi","duration_minutes":1,"presenters":["A","B"],
         "video_format":"square","workflow":"manual","input_kind":"topic","research_mode":"knowledge"}
    pid=projects.create(root,req)["project_id"];ids={}
    for name,color,preset in (("A","red","hm_omega"),("B","blue","hf_alpha")):
        p=tmp_path/(name+".png");Image.new("RGB",(200,200),color).save(p)
        profile={"name":name,"personality":"Curious","speaking_style":"Friendly","appearance":"Fictional",
                 "voice_preferences":{"engine":engine,"language":"Hindi","preset":preset,"style_notes":""}}
        ids[name]=characters.create(root,profile,portrait=p,acknowledgment=characters.ACK)["character_id"]
    characters.assign(root,pid,ids)
    current={"version_sha256":"a"*64,"turns":[{"id":"0001","speaker":"A","text":"पहला संवाद"},
                                           {"id":"0002","speaker":"B","text":"दूसरा संवाद"}]}
    monkeypatch.setattr(script_review,"current_script",lambda *a,**k:current)
    return root,pid


def wav(path,amp):
    with wave.open(str(path),"wb") as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000)
        w.writeframes(struct.pack("<h",amp)*16000)
    return path


def test_master_exact_pcm_and_tamper(tmp_path,monkeypatch):
    root,pid=ready(tmp_path,monkeypatch)
    with pytest.raises(ValueError,match="Finalize"):master.compose(root,pid)
    for tid,amp in (("0001",100),("0002",200)):
        audio.import_turn(root,pid,tid,wav(tmp_path/(tid+".wav"),amp),acknowledgment=audio.ACK)
    audio.finalize(root,pid)
    result=master.compose(root,pid)
    assert result["master"]["frames"]==36000
    assert master.compose(root,pid)==result==master.inspect(root,pid)
    path=audio._context(root,pid)[1]/master.FOLDER/master.WAV
    with wave.open(str(path),"rb") as w:
        assert w.readframes(36000)==struct.pack("<h",100)*16000+bytes(8000)+struct.pack("<h",200)*16000
    with path.open("r+b") as f:f.seek(44);f.write(b"\x01\x00")
    with pytest.raises(ValueError,match="PCM differs"):master.inspect(root,pid)


@pytest.mark.skipif(not shutil.which("ffmpeg"),reason="FFmpeg required")
def test_local_tts_fixture_resume_and_provenance(tmp_path,monkeypatch):
    root,pid=ready(tmp_path,monkeypatch,"kokoro")
    model=tmp_path/"model.onnx";model.write_bytes(b"x"*1000000)
    voices=tmp_path/"voices.bin";voices.write_bytes(b"x"*1000)
    calls=[]
    class Fake:
        def create(self,phonemes,*,voice,speed,is_phonemes):
            calls.append(voice)
            return [0.1 if voice=="hm_omega" else 0.2]*24000,24000
    factory=lambda *a:(Fake(),lambda text:(text,None))
    opts={"model":model,"voices":voices,"run_local":True,"acknowledgment":tts.ACK,"engine_factory":factory}
    with pytest.raises(ValueError,match="acknowledgment"):tts.generate(root,pid,model=model,voices=voices)
    assert tts.generate(root,pid,**opts)["new_generated_turns"]==["0001"]
    assert tts.generate(root,pid,**opts)["new_generated_turns"]==["0002"]
    assert calls==["hm_omega","hf_alpha"]
    result=audio.inspect(root,pid)
    assert result["generated_turns"]==2 and result["measured_imported_speech_seconds"]==0
    audio.finalize(root,pid)
    assert master.compose(root,pid)["master"]["frames"]==36000
