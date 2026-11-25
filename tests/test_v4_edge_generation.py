import shutil
import pytest
from podcast_gpt import v4_edge as edge,v4_audio as audio,media,cli
from test_v4_master_tts import ready,wav

@pytest.mark.parametrize("allow,ack",[(False,edge.ACK),(True,"YES"),(1,edge.ACK),(True,None)])
def test_consent_before_project_access(allow,ack):
    with pytest.raises(ValueError,match="acknowledgment"):
        edge.generate(None,None,allow_network_tts=allow,acknowledgment=ack)

@pytest.mark.parametrize("count",[0,6,True,1.5])
def test_count_before_project_access(count):
    with pytest.raises(ValueError,match="1–5"):
        edge.generate(None,None,allow_network_tts=True,acknowledgment=edge.ACK,max_new=count)

@pytest.mark.skipif(not shutil.which("ffmpeg"),reason="FFmpeg required")
def test_resume_and_origin(tmp_path,monkeypatch):
    root,pid=ready(tmp_path,monkeypatch,"edge",presets=("hi-IN-MadhurNeural","hi-IN-SwaraNeural"))
    calls=[]
    def fake(text,preset,path):
        calls.append(preset)
        original=wav(tmp_path/(preset+".wav"),1000 if len(calls)==1 else 2000)
        media.cmd(["ffmpeg","-nostdin","-v","error","-i",str(original),"-c:a","libmp3lame",str(path)],timeout=30)
    opts={"allow_network_tts":True,"acknowledgment":edge.ACK,"synthesizer":fake}
    assert edge.generate(root,pid,**opts)["new_generated_turns"]==["0001"]
    assert edge.generate(root,pid,**opts)["new_generated_turns"]==["0002"]
    assert edge.generate(root,pid,**opts)["new_generated_turns"]==[]
    assert calls==["hi-IN-MadhurNeural","hi-IN-SwaraNeural"]
    assert audio.inspect(root,pid)["generated_turns"]==2
    assert audio.finalize(root,pid)["timeline_finalized"]

def test_cli_default_offline():
    args=cli.parse(["project-tts-edge","--project-id","a"*32,"--acknowledgment",edge.ACK])
    assert not args.allow_network_tts and args.max_new==1
