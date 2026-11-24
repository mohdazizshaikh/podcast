"""Explicit installed eSpeak NG CPU speech fallback; not neural/natural TTS."""
from __future__ import annotations
import re
import shutil
import tempfile
from pathlib import Path
from . import characters, media, projects, source, v4_audio as audio

ACK="I_TRUST_THIS_LOCAL_ESPEAK_EXECUTABLE_AND_HAVE_USAGE_RIGHTS"
LANGUAGES={"english":"en","hindi":"hi","हिंदी":"hi","हिन्दी":"hi","marathi":"mr","tamil":"ta","telugu":"te",
           "bengali":"bn","gujarati":"gu","urdu":"ur","spanish":"es","french":"fr","german":"de",
           "italian":"it","portuguese":"pt","arabic":"ar","russian":"ru","japanese":"ja","chinese":"cmn","mandarin":"cmn"}
TAG=re.compile(r"[a-z]{2,3}(?:-[a-z0-9]{2,8}){0,3}")
PRESET=re.compile(r"[a-z]{2,3}(?:-[a-z0-9]{2,8}){0,3}(?:\+(?:m[1-7]|f[1-5]))?")


def language(value):
    value=value.casefold().strip()
    value=LANGUAGES.get(value,value)
    if not TAG.fullmatch(value):raise ValueError("Use an installed eSpeak language code or supported language name")
    return value


def compatible(voice,requested,installed):
    preset=voice["preset"]
    if voice["engine"]!="espeak" or not PRESET.fullmatch(preset):raise ValueError("Select explicit eSpeak language preset, optionally +m1 to +m7 or +f1 to +f5")
    base=preset.split("+")[0]
    for value in (language(voice["language"]),language(requested)):
        if not (base==value or ("-" not in value and base.startswith(value+"-"))):
            raise ValueError("eSpeak preset language does not match requested script/profile language")
    if base not in installed:raise ValueError("eSpeak preset language is not installed")
    return preset


def _executable(path):
    p=Path(path).expanduser().absolute()
    for parent in reversed(p.parents):projects._plain(parent)
    projects._plain(p,directory=False)
    return p


def inventory(executable,*,acknowledgment):
    if acknowledgment!=ACK:raise ValueError("Explicit trusted executable acknowledgment required")
    p=_executable(executable)
    before=source.digest(p)
    out=media.cmd([str(p),"--voices"],timeout=30).stdout
    if len(out)>500000:raise ValueError("Unexpected eSpeak voice inventory size")
    tags=set()
    for line in out.splitlines():
        cols=line.split()
        if len(cols)>=4 and cols[0].isdigit() and TAG.fullmatch(cols[1]):tags.add(cols[1])
    if not tags:raise ValueError("No installed eSpeak language inventory detected")
    if source.digest(p)!=before:raise ValueError("eSpeak executable changed during inventory")
    return {"languages":sorted(tags),"executable_sha256":before,"inventory_sha256":source.json_digest(sorted(tags)),
            "actual_voice_quality_verified":False,"downloads":0}


def generate(root,pid,*,executable,run_local=False,acknowledgment=None,max_new=1):
    if run_local is not True or acknowledgment!=ACK:raise ValueError("Explicit local speech consent and rights acknowledgment required")
    if type(max_new) is not int or not 1<=max_new<=5:raise ValueError("Generate 1–5 new turns per invocation")
    folder=projects.project(root,pid)
    with projects.exclusive(folder):
        _,dest,binding,turns,req,cast=audio._context(root,pid)
        items=audio._read_parts(dest,binding,turns)
        if audio._check_timeline(dest,binding,turns,items,req) is not None:raise ValueError("Timeline already finalized")
        prefs={p["speaker"]:p["voice_preferences"] for p in cast["presenters"] if p["voice_preferences"]["engine"]=="espeak"}
        chosen=[t for t in turns if t["id"] not in items and t["speaker"] in prefs][:max_new]
        if not chosen:return {**audio._summary(pid,dest,binding,turns,items,req),"new_generated_turns":[]}
        exe=_executable(executable);inv=inventory(exe,acknowledgment=ACK)
        presets={speaker:compatible(v,req["language"],inv["languages"]) for speaker,v in prefs.items()}
        if len(set(presets.values()))!=len(presets):raise ValueError("Select distinct eSpeak presets per speaker")
        def provenance(speaker):
            return {"voice_preset":presets[speaker],"executable_sha256":inv["executable_sha256"],"inventory_sha256":inv["inventory_sha256"]}
        for item in items.values():
            if item["origin"]=="local_espeak" and item["generation"]!=provenance(item["speaker"]):
                raise ValueError("Existing eSpeak audio uses different executable or voice inventory")
        if shutil.disk_usage(folder).free<100*1024**2:raise ValueError("At least 100 MiB private scratch disk required")
        completed=[]
        for turn in chosen:
            if audio._context(root,pid)[2]!=binding:raise ValueError("Script or cast changed")
            with tempfile.TemporaryDirectory(prefix="v4-espeak-",dir=folder) as tmp:
                temp=Path(tmp);text=temp/"speech.txt";raw=temp/"raw.wav";fixed=temp/"speech.wav"
                text.write_text(turn["text"],encoding="utf-8")
                media.cmd([str(exe),"-b","1","-v",presets[turn["speaker"]],"-f",str(text),"-w",str(raw)],timeout=120)
                projects._plain(raw,directory=False)
                media.cmd(["ffmpeg","-nostdin","-hide_banner","-v","error","-i",str(raw),"-ar","16000","-ac","1","-c:a","pcm_s16le",str(fixed)],timeout=120)
                data=characters._read_file(fixed,audio.MAX_WAV);info=audio._pcm(data)
            if source.digest(exe)!=inv["executable_sha256"] or audio._context(root,pid)[2]!=binding or audio._read_parts(dest,binding,turns)!=items:
                raise ValueError("Local executable, script or existing audio changed")
            if any(v["pcm_sha256"]==info["pcm_sha256"] for v in items.values()):raise ValueError("Duplicate generated PCM")
            if sum(v["frames"] for v in items.values())+info["frames"]>audio.MAX_TOTAL:raise ValueError("Audio duration limit exceeded")
            audio._save_turn(dest,binding,turn,data,info,generation=provenance(turn["speaker"]),origin="local_espeak")
            items=audio._read_parts(dest,binding,turns);completed.append(turn["id"])
        return {**audio._summary(pid,dest,binding,turns,items,req),"new_generated_turns":completed,
                "voice_quality_verified":False,"automatic_downloads":0}
