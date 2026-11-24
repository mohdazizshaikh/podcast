import json
from types import SimpleNamespace
import pytest
from podcast_gpt import model_config as config, characters, projects, persona, script_generation as sg, ai_providers as ai, source
from podcast_gpt import v4_espeak as es, v4_audio as audio, media
from test_script_generation import setup,fixture_provider
from test_characters import profile
from test_v4_master_tts import ready,wav


def test_config_no_execution_and_explicit_replace(tmp_path):
    root=tmp_path/"private";exe=tmp_path/"espeak.exe";exe.write_bytes(b"fixture only")
    assert config.status(root)["engines"]["espeak"]=="not_configured"
    config.save(root,"espeak",{"executable":exe})
    assert config.read(root,"espeak")=={"executable":exe}
    with pytest.raises(ValueError,match="replace"):config.save(root,"espeak",{"executable":exe})
    with pytest.raises(ValueError,match="not both"):config.resolve(root,"espeak",{"executable":exe},use_config=True)
    assert config.resolve(root,"espeak",{"executable":None},use_config=True)["executable"]==exe
    exe.unlink()
    assert config.status(root)["engines"]["espeak"]=="blocked"


def test_persona_opt_in_and_binding(tmp_path,monkeypatch):
    root=tmp_path/"private";pid=setup(root,2,["A","B"])
    ids={n:characters.create(root,profile(n))["character_id"] for n in ("A","B")}
    characters.assign(root,pid,ids)
    persona.enable(root,pid)
    def fake(prompt,validator,**kw):
        ctx=json.loads(prompt.split("Context JSON:\n",1)[1])
        assert ctx["untrusted_character_profiles"][0]["personality"]=="Curious, analytical"
        assert "appearance" not in ctx["untrusted_character_profiles"][0]
        return fixture_provider(prompt,validator,**kw)
    monkeypatch.setattr(ai,"generate_json",fake)
    sg.generate(root,pid)
    with pytest.raises(ValueError,match="before generating"):persona.enable(root,pid)
    sg.generate(root,pid)
    sg.finalize(root,pid)
    assert "persona_sha256" in sg.show(root,pid)["script"]["binding"]
    assert projects.inspect(root,pid)["stage"]=="script_saved"


def test_espeak_inventory_and_language_guard(tmp_path,monkeypatch):
    exe=tmp_path/"espeak.exe";exe.write_bytes(b"fixture")
    monkeypatch.setattr(media,"cmd",lambda *a,**k:SimpleNamespace(stdout="Pty Language Age/Gender VoiceName File\n 5 en-us M English en\n 5 hi M Hindi hi\n"))
    with pytest.raises(ValueError,match="acknowledgment"):es.inventory(exe,acknowledgment="YES")
    assert es.inventory(exe,acknowledgment=es.ACK)["languages"]==["en-us","hi"]
    assert es.compatible({"engine":"espeak","language":"English","preset":"en-us+f1"},"English",["en-us"])=="en-us+f1"
    with pytest.raises(ValueError,match="language"):es.compatible({"engine":"espeak","language":"English","preset":"en-us"},"Hindi",["en-us"])
    with pytest.raises(ValueError,match="installed"):es.compatible({"engine":"espeak","language":"Hindi","preset":"hi"},"Hindi",["en-us"])


def test_espeak_generation_fixture(tmp_path,monkeypatch):
    # Use the existing private approved-cast fixture, with explicit eSpeak presets.
    # The fixture's preset IDs are Kokoro-specific, so modify the fixture handoff
    # in memory only; production casts remain immutable.
    root,pid=ready(tmp_path,monkeypatch,engine="espeak")
    original=audio._context
    def ctx(*args):
        folder,dest,binding,turns,req,cast=original(*args)
        for i,row in enumerate(cast["presenters"]):row["voice_preferences"]["preset"]="hi+"+("m1" if i==0 else "f1")
        return folder,dest,binding,turns,req,cast
    monkeypatch.setattr(audio,"_context",ctx)
    exe=tmp_path/"espeak.exe";exe.write_bytes(b"fixture")
    calls=[]
    def cmd(args,**kw):
        if "--voices" in args:return SimpleNamespace(stdout=" 5 hi M Hindi hi\n")
        if str(args[0])==str(exe):
            calls.append(args[args.index("-v")+1]);wav(__import__("pathlib").Path(args[-1]),100 if len(calls)==1 else 200)
        else:
            import shutil
            shutil.copyfile(args[args.index("-i")+1],args[-1])
        return SimpleNamespace(stdout="")
    monkeypatch.setattr(media,"cmd",cmd)
    opts={"executable":exe,"run_local":True,"acknowledgment":es.ACK}
    assert es.generate(root,pid,**opts)["new_generated_turns"]==["0001"]
    assert es.generate(root,pid,**opts)["generated_turns"]==2
    assert calls==["hi+m1","hi+f1"]
    assert audio.finalize(root,pid)["timeline_finalized"]
