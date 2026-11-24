import array
import shutil
import pytest
from podcast_gpt import audio_diagnostics as diag,v4_post_audio as mix,v4_master,ai_providers as ai,model_setup_plan,cli,web
from test_v4_preview import fixture
from test_v4_master_tts import wav


def test_ducking_legacy_and_audit(tmp_path,monkeypatch):
    root,pid=fixture(tmp_path,monkeypatch)
    before=v4_master.inspect(root,pid)
    bed=wav(tmp_path/"bed.wav",500)
    assert mix._settings(22000,3000)=={"speech_peak":22000,"bed_peak":3000,"mix_algorithm":"integer_peak_v1"}
    result=mix.compose(root,pid,bed=bed,duck_percent=75,acknowledgment=mix.ACK)
    assert result["mix"]["settings"]["duck_percent"]==75
    assert mix.inspect(root,pid)==result
    assert v4_master.inspect(root,pid)==before
    assert not result["mix"]["human_mix_quality_approved"]
    with pytest.raises(ValueError):mix._settings(22000,3000,91)


def test_ducking_reduces_bed_during_active_speech(monkeypatch):
    samples=[1000]*16000+[0]*16000
    monkeypatch.setattr(v4_master,"_chunks",lambda *a:iter([mix._bytes(samples)]))
    assets={"bed":(b"",{},array.array("h",[1000]*32000))}
    timeline={"total_frames":32000}
    plain=mix._samples(b"".join(mix._mix_blocks(None,timeline,assets,mix._settings(22000,3000))))
    duck=mix._samples(b"".join(mix._mix_blocks(None,timeline,assets,mix._settings(22000,3000,75))))
    assert duck[10000]<plain[10000] and duck[28000]==plain[28000]
    assert max(map(abs,duck))<=30000


def test_loudness_parse():
    result=diag.parse_loudness('info\n{"input_i":"-21.5","input_tp":"-3.0","input_lra":"0.0","input_thresh":"-31.5"}')
    assert result["integrated_lufs"]==-21.5 and result["true_peak_dbtp"]==-3
    assert diag.parse_loudness('{"input_i":"-inf","input_tp":"-inf","input_lra":"0","input_thresh":"-70"}')["integrated_lufs"] is None
    with pytest.raises(ValueError):diag.parse_loudness("not a measurement")


@pytest.mark.skipif(not shutil.which("ffmpeg"),reason="FFmpeg required")
def test_real_ffmpeg_measurement(tmp_path,monkeypatch):
    root,pid=fixture(tmp_path,monkeypatch)
    before=v4_master.inspect(root,pid)
    result=diag.inspect(root,pid)
    assert result["wav_sha256"]==before["master"]["wav_sha256"]
    assert result["pcm"]["frames"]==36000 and not result["audio_modified"]
    assert "integrated_lufs" in result["loudness"] and v4_master.inspect(root,pid)==before


@pytest.mark.parametrize("provider,response",[
    ("router",{"choices":[{"finish_reason":"content_filter","message":{}}]}),
    ("router",{"choices":[{"finish_reason":"stop","message":{"refusal":"refused"}}]}),
    ("gemini",{"promptFeedback":{"blockReason":"SAFETY"}}),
    ("gemini",{"candidates":[{"finishReason":"SAFETY"}]})])
def test_refusal_no_fallback(provider,response):
    calls=[]
    def request(url,*a,**kw):calls.append(url);return response
    creds=ai.Credentials("router-key" if provider=="router" else None,"gemini-key")
    with pytest.raises(ai.ProviderRefusal,match="no fallback"):
        ai.generate_json("topic",lambda x:x,credentials=creds,allow_cloud_text=True,confirm_gemini_free_project=True,request=request)
    assert calls==[ai.OPENROUTER if provider=="router" else ai.GEMINI]


def test_malformed_local_inventory_and_setup(tmp_path):
    with pytest.raises(ai.ProviderError,match="invalid_local_model_inventory"):
        ai.generate_json("topic",lambda x:x,offline_only=True,request=lambda *a,**kw:{"models":None})
    report=model_setup_plan.inspect(tmp_path/"private")
    assert report["downloads"]==0 and not report["model_load_verified"]
    assert all(v=="not_configured" for v in report["saved_model_status"]["engines"].values())
    assert "kokoro-english" in report["optional_dependency_groups"]
    assert cli.parse(["doctor"]).operation=="doctor"
    assert "v4AudioDiagnostics" in web.html_page("test")
