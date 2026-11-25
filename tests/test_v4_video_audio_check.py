import math
import shutil
import struct
import wave
import pytest
from podcast_gpt import video_audio_check as check,cli,web,media


@pytest.mark.parametrize("scale",[.5,1,1.5,-1])
def test_correlation_and_residual(scale):
    a=[-1000,0,1000]*1000;b=[int(x*scale) for x in a]
    result=check.compare_window(a,b)
    assert result["correlation"]==(1 if scale>0 else -1)
    assert result["relative_residual"]==abs(1-scale)


@pytest.mark.parametrize("a,b",[([],[]),([1],[]),([1],[1,2])])
def test_invalid_window(a,b):
    with pytest.raises(ValueError):check.compare_window(a,b)


def wav(path,samples):
    with wave.open(str(path),"wb") as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000)
        w.writeframes(b"".join(struct.pack("<h",v) for v in samples))


def test_window_flags_and_coverage(tmp_path):
    a=tmp_path/"a.wav";b=tmp_path/"b.wav";x=[-1000,1000]*8000
    wav(a,x+[0]*16000);wav(b,[-v for v in x]+[1000]*16000+[0]*160)
    result=check.compare_wavs(a,b)
    assert result["informative_windows"]==1 and result["low_similarity_windows"]==1
    assert result["unexpected_quiet_audio_windows"]==1 and result["duration_difference_seconds"]==.01
    assert result["mean_correlation"]==-1 and len(result["flagged_window_examples"])==2


@pytest.mark.skipif(not shutil.which("ffmpeg"),reason="FFmpeg required")
def test_real_aac_roundtrip(tmp_path):
    a=tmp_path/"a.wav";b=tmp_path/"b.wav";encoded=tmp_path/"encoded.m4a"
    wav(a,[round(8000*math.sin(2*math.pi*440*i/16000)) for i in range(32000)])
    media.cmd(["ffmpeg","-nostdin","-v","error","-i",str(a),"-c:a","aac","-ar","48000",str(encoded)],timeout=60)
    media.cmd(["ffmpeg","-nostdin","-v","error","-i",str(encoded),"-ar","16000","-ac","1","-c:a","pcm_s16le",str(b)],timeout=60)
    result=check.compare_wavs(a,b)
    assert result["informative_windows"]==2 and result["mean_correlation"]>.9
    assert abs(result["duration_difference_seconds"])<.1


def test_controls_and_wrong_kind():
    with pytest.raises(ValueError):check.inspect(None,None,"master")
    assert cli.parse(["project-video-audio-check","--project-id","a"*32,"--kind","neural"]).kind=="neural"
    assert "v4VideoAudioCheck" in web.html_page("test")
