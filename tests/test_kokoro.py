"""Synthetic injection only: not real Kokoro ONNX, eSpeak Hindi, or human voice QA."""
from __future__ import annotations

import json
import shutil
from array import array
from pathlib import Path

import pytest

from podcast_gpt import kokoro,source

@pytest.fixture
def offline_assets(tmp_path):
    model=tmp_path/"fake-test-only-model.onnx"
    voices=tmp_path/"fake-test-only-voices.bin"
    model.write_bytes(b"FAKE-ONLY-NO-KOKORO"*62000)
    voices.write_bytes(b"FAKE-ONLY-NO-VOICE"*100)
    return model,voices


def fake_factory(model,voices):
    class FakeLocalModel:
        def create(self,phonemes,*,voice,speed,is_phonemes):
            assert is_phonemes and speed==1.0
            assert voice in kokoro.VOICE_CHOICES
            assert isinstance(phonemes,str) and len(phonemes.split()) >= 15
            assert not phonemes.startswith("भाग "), "Do not speak a mechanical turn label"
            value={"hm_omega":.09,"hf_alpha":.17,"hm_psi":.28}[voice]
            return array('f',[value])*(24_000+len(phonemes)),24000
    return FakeLocalModel(),lambda text:(text,None)


@pytest.mark.skipif(not shutil.which("ffmpeg"),reason="FFmpeg for exact original 16k PCM conversion")
def test_three_distinct_original_hindi_voice_presets_offline_no_overwrite(private_studio,offline_assets,monkeypatch):
    root=private_studio
    original_temp=kokoro.tempfile.TemporaryDirectory
    scratch_locations=[]
    def recording_temp(*args,**kwargs):
        scratch_locations.append(kwargs.get("dir"))
        return original_temp(*args,**kwargs)
    monkeypatch.setattr(kokoro.tempfile,"TemporaryDirectory",recording_temp)
    for i in range(1,4):(root/"voices"/f"{i:03}.wav").unlink()
    original_other=(root/"voices"/"009.wav").read_bytes()
    result=kokoro.generate(root,model=offline_assets[0],voices=offline_assets[1],
                           run_local=True,next_missing=True,max_new=3,
                           engine_factory=fake_factory)
    assert result["model_inference_calls"]==3
    assert scratch_locations==[root/"scratch"]*3
    assert result["new_original_hindi_wav_turns"]==["001","002","003"]
    assert result["distinct_voice_presets_chosen"] is True
    assert result["three_natural_voice_identities_human_verified"] is False
    assert result["network_service_used"] is False
    assert result["full_ten_minute_neural_video_completed"] is False
    assert (root/"voices"/"009.wav").read_bytes()==original_other
    for id_,voice in [("001","hm_omega"),("002","hf_alpha"),("003","hm_psi")]:
        wav=root/"voices"/(id_+".wav")
        frame_count,_=source.wav_info(wav)
        assert frame_count>source.RATE
        report=json.loads((root/"voices"/(id_+".kokoro-source.json")).read_text(encoding="utf-8"))
        assert report["voice_preset"]==voice
        assert report["wav_sha256"]==source.digest(wav)
        assert report["human_voice_quality_approved"] is False
    assert len({source.digest(root/"voices"/(id_+".wav")) for id_ in ("001","002","003")})==3
    assert result["remaining_missing_voice_wavs"]==0
    assert kokoro.generate(root,model=offline_assets[0],voices=offline_assets[1],
                          run_local=True,next_missing=True,max_new=3,
                          engine_factory=fake_factory)["model_inference_calls"]==0
    # Synthetic short private originals cannot claim a 10-minute production episode.
    with pytest.raises(ValueError,match="10 minutes"):
        source.build_source(root)
    assert source.build_source(root,allow_short=True)["original_turn_count"]==45


def test_no_explicit_consent_blocks_all_local_model_runs(private_studio,offline_assets):
    with pytest.raises(ValueError,match="run-local"):
        kokoro.generate(private_studio,model=offline_assets[0],voices=offline_assets[1],
                        run_local=False,next_missing=True,engine_factory=fake_factory)


@pytest.mark.parametrize("turn,next_missing,max_new",[(None,False,1),(1,True,1),(46,False,1),(1,False,5)])
def test_invalid_kokoro_target_or_budget_is_refused(private_studio,offline_assets,turn,next_missing,max_new):
    with pytest.raises(ValueError):
        kokoro.generate(private_studio,model=offline_assets[0],voices=offline_assets[1],
                        run_local=True,turn=turn,next_missing=next_missing,max_new=max_new,
                        engine_factory=fake_factory)


def test_no_real_model_files_no_generated_voice(private_studio,tmp_path):
    (private_studio/"voices"/"001.wav").unlink()
    with pytest.raises(ValueError,match="locally installed"):
        kokoro.generate(private_studio,model=tmp_path/"missing.onnx",voices=tmp_path/"missing.bin",
                        run_local=True,turn=1,engine_factory=fake_factory)
    assert not (private_studio/"voices"/"001.wav").exists()


@pytest.mark.skipif(not shutil.which("ffmpeg"),reason="FFmpeg for TTS conversion")
def test_voice_after_source_SHA_bind_is_refused(private_studio,offline_assets):
    source.build_source(private_studio,allow_short=True)
    with pytest.raises(ValueError,match="SHA-bound"):
        kokoro.generate(private_studio,model=offline_assets[0],voices=offline_assets[1],
                        run_local=True,next_missing=True,engine_factory=fake_factory)


def test_cli_registers_explicit_offline_voice_command(private_studio,offline_assets):
    from podcast_gpt.cli import parse
    args=parse(["--workspace",str(private_studio),"tts-kokoro", "--model",str(offline_assets[0]),
                "--voices",str(offline_assets[1]),"--next","--max-new","3"])
    assert args.operation=="tts-kokoro"
    assert args.run_local is False
    assert args.next is True