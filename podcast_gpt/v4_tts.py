"""Explicit local Hindi Kokoro adapter for reviewed V4 casts."""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from . import characters, kokoro, media, projects, v4_audio as audio

ACK="I_HAVE_RIGHTS_TO_USE_LOCAL_MODEL_AND_VOICES"
HINDI={"hindi","hi","hi-in","हिन्दी","हिंदी"}


def _preset(voice):
    if voice["engine"]!="kokoro" or voice["language"].casefold() not in HINDI or voice["preset"] not in kokoro.VOICE_CHOICES:
        raise ValueError("Local V4 Kokoro currently requires Hindi and a supported explicit Hindi preset")
    return voice["preset"]


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
        if req["language"].casefold() not in HINDI:raise ValueError("V4 local Kokoro currently supports Hindi scripts only")
        items=audio._read_parts(dest,binding,turns)
        if audio._check_timeline(dest,binding,turns,items,req) is not None:
            raise ValueError("Timeline already finalized")
        prefs={r["speaker"]:r["voice_preferences"] for r in cast["presenters"]}
        missing=[t for t in turns if t["id"] not in items and prefs[t["speaker"]]["engine"]=="kokoro"]
        chosen=missing[:max_new]
        if not chosen:return {**audio._summary(pid,dest,binding,turns,items,req),"new_generated_turns":[]}
        presets={t["speaker"]:_preset(prefs[t["speaker"]]) for t in chosen}
        # Distinct preset IDs for the Kokoro cast, not proof of distinct voices.
        all_presets=[_preset(v) for v in prefs.values() if v["engine"]=="kokoro"]
        if len(set(all_presets))!=len(all_presets):raise ValueError("Assign distinct Hindi Kokoro presets to each local TTS speaker")
        model,voices,hashes=_assets(model,voices)
        for item in items.values():
            if item["origin"]=="local_kokoro_hindi":
                gen=item["generation"]
                if gen!={"voice_preset":_preset(prefs[item["speaker"]]),"model_sha256":hashes["kokoro_model_sha256"],
                         "voices_sha256":hashes["kokoro_voices_pack_sha256"]}:
                    raise ValueError("Existing generated audio uses different local model or voice pack")
        if shutil.disk_usage(folder).free<100*1024**2:raise ValueError("At least 100 MiB private scratch disk space required")
        engine,g2p=(engine_factory or kokoro._engine)(model,voices)
        completed=[]
        for turn in chosen:
            if audio._context(root,pid)[2]!=binding:raise ValueError("Approved script or cast changed")
            preset=presets[turn["speaker"]]
            phonemes=g2p(turn["text"])[0]
            if not isinstance(phonemes,str) or not phonemes.strip():raise ValueError("Local Hindi phonemizer returned no phonemes")
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
            gen={"voice_preset":preset,"model_sha256":hashes["kokoro_model_sha256"],"voices_sha256":hashes["kokoro_voices_pack_sha256"]}
            audio._save_turn(dest,binding,turn,data,info,generation=gen)
            items=audio._read_parts(dest,binding,turns)
            completed.append(turn["id"])
        return {**audio._summary(pid,dest,binding,turns,items,req),"new_generated_turns":completed,
                "model_inference_calls":len(completed),"automatic_model_downloads":0}
