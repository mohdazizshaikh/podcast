import math
import struct
import wave
import shutil
import pytest
from podcast_gpt import audio_diagnostics as diag,v4_post_audio as mix,v4_master as master,v4_audio as audio,loudness_gain as gain
from podcast_gpt import projects,characters,continuity,script_generation as sg,script_review,source,cli
from test_v4_master_tts import ready
from test_v4_preview import fixture


def measurement(i,peak):
    return {"integrated_lufs":i,"true_peak_dbtp":peak,"loudness_range_lu":0.0,"gating_threshold_lufs":i-10}


def test_gain_bound_and_ceiling():
    before=measurement(-30,-4)
    ppm=gain.gain_ppm(-16,before,30000)
    assert 0<ppm<=1000000
    with pytest.raises(ValueError,match="ceiling"):gain.record(-16,before,30000,"a"*64,measurement(-16,-1))
    with pytest.raises(ValueError):gain.gain_ppm(-2,before,30000)


def test_normalization_exact_recipe_and_per_turn(tmp_path,monkeypatch):
    root,pid=fixture(tmp_path,monkeypatch)
    original=master.inspect(root,pid)
    results=iter([measurement(-20,-1.5),measurement(-19,-2.5),measurement(-19,-2.5)])
    monkeypatch.setattr(diag,"measure",lambda *a:next(results))
    result=mix.compose(root,pid,target_lufs=-16,acknowledgment=mix.ACK)
    norm=result["mix"]["settings"]["normalization"]
    assert norm["gain_ppm"]<=1000000 and not norm["measured_target_within_0_5_lu"]
    assert mix.inspect(root,pid)==result and master.inspect(root,pid)==original
    checks=diag.inspect(root,pid,per_turn=True)
    assert len(checks["turn_diagnostics"])==2
    assert sum(x["pcm"]["frames"] for x in checks["turn_diagnostics"])==32000
    dest=audio._context(root,pid)[1]/mix.FOLDER
    with (dest/mix.WAV).open("r+b") as handle:handle.seek(44);handle.write(b"\0\0")
    with pytest.raises(ValueError,match="PCM differs"):mix.inspect(root,pid)


@pytest.mark.skipif(not shutil.which("ffmpeg"),reason="FFmpeg required")
def test_real_sine_normalized(tmp_path,monkeypatch):
    root,pid=ready(tmp_path,monkeypatch)
    for tid,hz in (("0001",440),("0002",660)):
        path=tmp_path/(tid+".wav")
        with wave.open(str(path),"wb") as w:
            w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000)
            w.writeframes(b"".join(struct.pack("<h",round(1000*math.sin(2*math.pi*hz*i/16000))) for i in range(16000)))
        audio.import_turn(root,pid,tid,path,acknowledgment=audio.ACK)
    audio.finalize(root,pid);master.compose(root,pid)
    result=mix.compose(root,pid,speech_peak=8000,target_lufs=-20,acknowledgment=mix.ACK)
    norm=result["mix"]["settings"]["normalization"]
    assert norm["candidate_measurement"]["true_peak_dbtp"]<=-1.5
    assert result["mix"]["total_frames"]==36000
    assert mix.inspect(root,pid)==result


def test_continuity_frozen_matching_cast(tmp_path,monkeypatch):
    root,prior=ready(tmp_path,monkeypatch)
    req=projects.load(root,prior);pid=projects.create(root,{**req,"topic":"Next episode"})["project_id"]
    cast=characters.read_cast(root,prior)
    characters.assign(root,pid,{r["speaker"]:r["character_id"] for r in cast["cast"]})
    with pytest.raises(ValueError,match="acknowledgment"):continuity.enable(root,pid,prior,["0001"],acknowledgment="YES")
    saved=continuity.enable(root,pid,prior,["0001"],acknowledgment=continuity.ACK)
    snapshot=saved["snapshot"]
    assert len(snapshot["excerpts"])==1 and snapshot["excerpts"][0]["speaker"]=="A"
    assert snapshot["excerpts"][0]["text"]=="पहला संवाद"
    assert continuity.inspect(root,pid)==saved
    with pytest.raises(ValueError,match="overwrite"):continuity.enable(root,pid,prior,["0002"],acknowledgment=continuity.ACK)
    outline={"title":"Next","sections":[{"heading":"Topic","minutes":1,"summary":"Science","presenters":req["presenters"]}]}
    folder=projects.project(root,pid)
    source.atomic_json(folder/projects.PLAN,{"schema":1,"request_sha256":source.json_digest(projects.load(root,pid)),
         "outline_sha256":source.json_digest(outline),"outline":outline,"provider":"ollama"},new=True)
    binding=sg._context(root,pid)[4]
    assert binding["continuity_sha256"]==source.json_digest(snapshot)
    with pytest.raises(ValueError,match="offline-only"):sg.generate(root,pid,allow_cloud_text=True)
    prompt=sg._prompt(req,None,outline,sg.units(outline)[0],[],previous_episode=snapshot)
    assert "untrusted_prior_episode_dialogue" in prompt and "पहला संवाद" in prompt
    assert snapshot["prior_project_id"] not in prompt
    assert cli.parse(["doctor"]).operation=="doctor"
