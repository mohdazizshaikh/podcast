"""Explicit local Kokoro language adapter for reviewed V4 casts."""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from . import characters, kokoro, kokoro_languages as languages, media, projects, v4_audio as audio

ACK="I_HAVE_RIGHTS_TO_USE_LOCAL_MODEL_AND_VOICES"
HINDI={"hindi","hi","hi-in","हिन्दी","हिंदी"}


def _preset(voice,code="hi"):
    return languages.preset(voice,code)


def _assets(model,voices):
    model=Path(model).expanduser().absolute();voices=Path(voices).expanduser().absolute()
    for p in (model,voices):
        for parent in reversed(p.parents):projects._plain(parent)
        projects._plain(p,directory=False)
    return model,voices,kokoro._check_assets(model,voices)


def generate(root,pid,*,model,voices,run_local=False,acknowledgment=None,max_new=1,engine_factory=None):
    if run_local is not True or acknowledgment!=ACK:raise ValueError("Explicit local inference and model rights acknowledgment required")
    if type(max_new) is not int or not 1<=max_new<=5:raise ValueError("Generate 1–5 new turns per invocation")
    folder=projects.project(root,pid)
    with projects.exclusive(folder):
        _,dest,binding,turns,req,cast=audio._context(root,pid)
        code=languages.language(req["language"])
        origin="local_kokoro_hindi" if code=="hi" else "local_kokoro_multilingual"
        items=audio._read_parts(dest,binding,turns)
        if audio._check_timeline(dest,binding,turns,items,req) is not None:
            raise ValueError("Timeline already finalized")
        prefs={r["speaker"]:r["voice_preferences"] for r in cast["presenters"]}
        missing=[t for t in turns if t["id"] not in items and prefs[t["speaker"]]["engine"]=="kokoro"]
        chosen=missing[:max_new]
        if not chosen:return {**audio._summary(pid,dest,binding,turns,items,req),"new_generated_turns":[]}
        presets={t["speaker"]:_preset(prefs[t["speaker"]],code) for t in chosen}
        # Distinct preset IDs for the Kokoro cast, not proof of distinct voices.
        all_presets=[_preset(v,code) for v in prefs.values() if v["engine"]=="kokoro"]
        if len(set(all_presets))!=len(all_presets):raise ValueError("Assign distinct Kokoro presets to each local TTS speaker")
        model,voices,hashes=_assets(model,voices)
        def provenance(preset):
            result={"voice_preset":preset,"model_sha256":hashes["kokoro_model_sha256"],"voices_sha256":hashes["kokoro_voices_pack_sha256"]}
            if code!="hi":result["language"]=code
            return result
        for item in items.values():
            if item["origin"] in ("local_kokoro_hindi","local_kokoro_multilingual"):
                if item["origin"]!=origin or item["generation"]!=provenance(_preset(prefs[item["speaker"]],code)):
                    raise ValueError("Existing generated audio uses different local model, language or voice pack")
        if shutil.disk_usage(folder).free<100*1024**2:raise ValueError("At least 100 MiB private scratch disk space required")
        engine,g2p=engine_factory(model,voices) if engine_factory else languages.engine(model,voices,code)
        if engine_factory is None:
            for preset in all_presets:
                try:engine.get_voice_style(preset)
                except (KeyError,ValueError,AttributeError) as exc:raise ValueError("Selected voice is unavailable in installed Kokoro pack") from exc
        completed=[]
        for turn in chosen:
            if audio._context(root,pid)[2]!=binding:raise ValueError("Approved script or cast changed")
            preset=presets[turn["speaker"]]
            phonemes=g2p(turn["text"])[0]
            if not isinstance(phonemes,str) or not phonemes.strip():raise ValueError("Local phonemizer returned no phonemes")
            if len(phonemes)>510:raise ValueError("Phoneme sequence exceeds 510 characters; revise or split the dialogue before rendering")
            samples,rate=engine.create(phonemes,voice=preset,speed=1.0,is_phonemes=True)
            with tempfile.TemporaryDirectory(prefix="v4-kokoro-",dir=folder) as temp:
                raw=Path(temp)/"raw.wav";fixed=Path(temp)/"speech.wav"
                kokoro._write_float_wav(raw,samples,int(rate))
                media.cmd(["ffmpeg","-nostdin","-hide_banner","-v","error","-i",str(raw),
                           "-ar","16000","-ac","1","-c:a","pcm_s16le",str(fixed)],timeout=120)
                data=characters._read_file(fixed,audio.MAX_WAV)
                info=audio._pcm(data)
            if audio._context(root,pid)[2]!=binding or _assets(model,voices)[2]!=hashes:
                raise ValueError("Approved script, cast or local model assets changed")
            if audio._read_parts(dest,binding,turns)!=items:raise ValueError("Existing audio changed during inference")
            if any(v["pcm_sha256"]==info["pcm_sha256"] for v in items.values()):raise ValueError("Duplicate generated PCM")
            if sum(v["frames"] for v in items.values())+info["frames"]>audio.MAX_TOTAL:raise ValueError("Audio duration limit exceeded")
            audio._save_turn(dest,binding,turn,data,info,generation=provenance(preset),origin=origin)
            items=audio._read_parts(dest,binding,turns)
            completed.append(turn["id"])
        return {**audio._summary(pid,dest,binding,turns,items,req),"new_generated_turns":completed,
                "model_inference_calls":len(completed),"automatic_model_downloads":0}
