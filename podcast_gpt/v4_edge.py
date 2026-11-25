"""Explicit bounded online speech generation; never an offline fallback."""
from __future__ import annotations
import asyncio
import shutil
import tempfile
from pathlib import Path
from . import characters,media,projects,v4_audio as audio,edge_voice

ACK="I_AUTHORIZE_SENDING_APPROVED_DIALOGUE_TO_EDGE_AND_HAVE_USAGE_RIGHTS"
MAX_MP3=8_000_000


async def _stream(text,preset,path):
    try:
        import edge_tts
    except ImportError:
        raise ValueError("Install the optional tts dependency in the app virtual environment") from None
    size=0
    with path.open("xb") as handle:
        async for chunk in edge_tts.Communicate(text,preset).stream():
            if chunk.get("type")=="audio":
                raw=chunk.get("data")
                if not isinstance(raw,bytes) or size+len(raw)>MAX_MP3:
                    raise ValueError("Edge audio exceeds bounded response size")
                handle.write(raw);size+=len(raw)
    if not size:raise ValueError("Edge service returned no audio")


def _synthesize(text,preset,path):
    try:
        asyncio.run(asyncio.wait_for(_stream(text,preset,path),timeout=120))
    except Exception:
        # Avoid surfacing provider errors containing private dialogue or URL data.
        raise ValueError("Online Edge synthesis failed; check optional package, service availability and network locally") from None


def generate(root,pid,*,allow_network_tts=False,acknowledgment=None,max_new=1,synthesizer=None):
    if allow_network_tts is not True or acknowledgment!=ACK:
        raise ValueError("Explicit online speech and usage rights acknowledgment required")
    if type(max_new) is not int or not 1<=max_new<=5:
        raise ValueError("Generate 1–5 new Edge turns per invocation")
    folder=projects.project(root,pid)
    with projects.exclusive(folder):
        _,dest,binding,turns,req,cast=audio._context(root,pid)
        items=audio._read_parts(dest,binding,turns)
        if audio._check_timeline(dest,binding,turns,items,req) is not None:
            raise ValueError("Timeline already finalized")
        prefs={p["speaker"]:p["voice_preferences"] for p in cast["presenters"] if p["voice_preferences"]["engine"]=="edge"}
        chosen=[t for t in turns if t["id"] not in items and t["speaker"] in prefs][:max_new]
        if not chosen:return {**audio._summary(pid,dest,binding,turns,items,req),"new_generated_turns":[],"network_requests_authorized":0}
        presets={speaker:edge_voice.compatible(v,req["language"]) for speaker,v in prefs.items()}
        if len(set(presets.values()))!=len(presets):raise ValueError("Select distinct Edge presets per speaker")
        def provenance(speaker):
            return {"voice_preset":presets[speaker],"language":edge_voice.language(req["language"]),
                    "provider":"edge_tts_online","network_consent":True}
        for item in items.values():
            if item["origin"]=="online_edge" and (item["speaker"] not in presets or item["generation"]!=provenance(item["speaker"])):
                raise ValueError("Existing Edge audio uses different voice or locale")
        if shutil.disk_usage(folder).free<100*1024**2:raise ValueError("At least 100 MiB private scratch disk required")
        completed=[]
        for turn in chosen:
            if audio._context(root,pid)[2]!=binding:raise ValueError("Script or cast changed")
            if audio._read_parts(dest,binding,turns)!=items:raise ValueError("Existing audio changed")
            with tempfile.TemporaryDirectory(prefix="v4-edge-",dir=folder) as tmp:
                raw=Path(tmp)/"raw.mp3";fixed=Path(tmp)/"speech.wav"
                (synthesizer or _synthesize)(turn["text"],presets[turn["speaker"]],raw)
                projects._plain(raw,directory=False)
                if not 1<=raw.stat().st_size<=MAX_MP3:raise ValueError("Invalid bounded Edge audio")
                media.cmd(["ffmpeg","-nostdin","-hide_banner","-v","error","-f","mp3","-i",str(raw),
                           "-t","121","-ar","16000","-ac","1","-c:a","pcm_s16le",str(fixed)],timeout=120)
                data=characters._read_file(fixed,audio.MAX_WAV);info=audio._pcm(data)
            if audio._context(root,pid)[2]!=binding or audio._read_parts(dest,binding,turns)!=items:
                raise ValueError("Script, cast or existing audio changed during online speech")
            if any(v["pcm_sha256"]==info["pcm_sha256"] for v in items.values()):raise ValueError("Duplicate generated PCM")
            if sum(v["frames"] for v in items.values())+info["frames"]>audio.MAX_TOTAL:raise ValueError("Audio duration limit exceeded")
            audio._save_turn(dest,binding,turn,data,info,generation=provenance(turn["speaker"]),origin="online_edge")
            items=audio._read_parts(dest,binding,turns);completed.append(turn["id"])
        return {**audio._summary(pid,dest,binding,turns,items,req),"new_generated_turns":completed,
                "network_requests_authorized":len(chosen),"voice_quality_verified":False,"automatic_downloads":0}
