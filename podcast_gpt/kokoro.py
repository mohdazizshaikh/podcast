"""Optional OFFLINE original Hindi Kokoro-ONNX CPU voice generator.

Does NOT fetch weights or phonemizer packages, NEVER overwrites original
WAVs or source manifests, and generates at most 5 turns per explicit run.
The four Hindi voice IDs are model-dependent; install compatible upstream
Kokoro ONNX v1.0 voice pack + eSpeak-ng/Misaki before using production CLI.
"""
from __future__ import annotations

import math
import os
import struct
import tempfile
import wave
from pathlib import Path

from .media import cmd
from .source import SPEAKERS, atomic_json, digest, json_digest, load_project, wav_info, workspace_path

VOICE_MAP={"aarav":"hm_omega", "meera":"hf_alpha", "kabir":"hm_psi"}
VOICE_CHOICES=frozenset(("hm_omega","hf_alpha","hm_psi","hf_beta"))
MODEL_INFO="kokoro_onnx_hindi_voice_private_original_no_automatic_quality_approval"


def _check_assets(model:Path,voices:Path)->dict:
    model=Path(model).expanduser()
    voices=Path(voices).expanduser()
    for p,minimum in ((model,1_000_000),(voices,1_000)):
        if p.is_symlink() or not p.is_file() or p.stat().st_size<minimum:
            raise ValueError("Missing or invalid locally installed Kokoro ONNX model/voices; no auto-download")
    return {"kokoro_model_sha256":digest(model),"kokoro_voices_pack_sha256":digest(voices)}


def _engine(model:Path,voices:Path):
    try:
        from kokoro_onnx import Kokoro
        from misaki.espeak import EspeakG2P
    except ImportError as err:
        raise ValueError("Install optional kokoro-onnx and misaki + local eSpeak-ng before CPU Hindi voice generation") from err
    instance=Kokoro(str(model),str(voices))
    g2p=EspeakG2P(language="hi")
    return instance,g2p


def _write_float_wav(path:Path,samples,sample_rate:int)->None:
    if (type(sample_rate) is not int or not 8000<=sample_rate<=96000):
        raise ValueError("Kokoro sample rate invalid")
    # This is a private transient 24k-ish PCM WAV, converted to exact 16k
    # original voice by FFmpeg before it can enter source SHA provenance.
    with wave.open(str(path),"wb") as out:
        out.setnchannels(1);out.setsampwidth(2);out.setframerate(sample_rate)
        count=0
        block=bytearray()
        for sample in samples:
            value=float(sample)
            if not math.isfinite(value):raise ValueError("Local Kokoro produced invalid audio sample")
            value=max(-1.0,min(1.0,value))
            block.extend(struct.pack("<h",round(value*32767)))
            count+=1
            if len(block)>=131072:
                out.writeframes(block);block.clear()
            if count>sample_rate*360:
                raise ValueError("Single Hindi turn too long for signed original PCM")
        if block:out.writeframes(block)
        if count<sample_rate:
            raise ValueError("Original Hindi Kokoro voice turn must be at least 1 second")


def generate(root:Path,*,model:Path,voices:Path,run_local:bool,
             turn:int|None=None,next_missing:bool=False,max_new:int=1,
             engine_factory=None) -> dict:
    """Explicit 1–5 original Hindi voice turns, one serial CPU inference each.

    Test-only engine_factory injection is never available from CLI or web.
    The public API only generates new authorized original private WAVs.
    """
    if run_local is not True:raise ValueError("Explicit --run-local required for offline model inference")
    if (next_missing is (turn is not None)):
        raise ValueError("Choose exactly one: --turn 1..45 or --next")
    if type(max_new) is not int or not 1<=max_new<=5:
        raise ValueError("Local Kokoro CPU generation cap is 1–5 NEW turns per invocation")
    if turn is not None and (type(turn) is not int or not 1<=turn<=45 or max_new!=1):
        raise ValueError("One original Hindi turn must be 1..45, max-new 1")
    root=workspace_path(root)
    project=load_project(root)
    # NEVER silently generate new voices against already bound original SHA.
    if (root/"source"/"source-manifest.json").exists():
        raise ValueError("Original private source is already SHA-bound; do not replace its 45 WAVs")
    hashes=_check_assets(model,voices)
    missing=[]
    for row in project["turns"]:
        target=root/"voices"/(row["id"]+".wav")
        if target.is_symlink():raise ValueError("Symlinked original voice WAV refused")
        if target.exists():
            wav_info(target)  # Existing originals may be separately supplied.
        else:missing.append(row)
    if turn is not None:
        chosen=[project["turns"][turn-1]]
        if chosen[0] not in missing:raise ValueError("Original WAV already exists; no model repeat/overwrite")
    else:
        chosen=missing[:max_new]
    if not chosen:
        return {"model_inference_calls":0,"new_original_hindi_wav_turns":[],
                "remaining_missing_voice_wavs":0,"fully_neural_lipsync_verified":False}
    if len({VOICE_MAP[x["speaker"]] for x in chosen})>3:
        raise ValueError("Unexpected voice preset mapping")
    # Load model once per bounded invocation, no hidden network call.
    factory=engine_factory or _engine
    engine,g2p=factory(Path(model),Path(voices))
    completed=[]
    for line in chosen:
        speaker=line["speaker"]
        voice=VOICE_MAP[speaker]
        if voice not in VOICE_CHOICES:raise ValueError("Selected unsupported Hindi voice")
        dest=root/"voices"/(line["id"]+".wav")
        receipt=root/"voices"/(line["id"]+".kokoro-source.json")
        if dest.exists() or dest.is_symlink() or receipt.exists() or receipt.is_symlink():
            raise ValueError("Private Hindi original voice/checkpoint exists; no overwrite")
        # eSpeak G2P converts Hindi Devanagari to model phonemes; Kokoro
        # runs only on local bytes of explicitly supplied model/voice pack.
        phonemes=g2p(line["text"])[0]
        if not isinstance(phonemes,str) or not phonemes.strip():
            raise ValueError("Hindi G2P produced no model phonemes")
        samples,rate=engine.create(phonemes,voice=voice,speed=1.0,is_phonemes=True)
        with tempfile.TemporaryDirectory(prefix="private-kokoro-") as temp:
            scratch=Path(temp)
            raw=scratch/"generated.wav"
            fixed=scratch/"original-16k.wav"
            _write_float_wav(raw,samples,int(rate))
            cmd(["ffmpeg","-y","-hide_banner","-v","error","-i",str(raw),
                 "-ar","16000","-ac","1","-c:a","pcm_s16le",str(fixed)],timeout=120)
            wav_info(fixed)
            # Recheck project source after slow local inference; never
            # adopt model audio if a user edited a different dialogue mid-run.
            if load_project(root)!=project:
                raise ValueError("Original Hindi script changed during local TTS CPU inference")
            import shutil
            with dest.open("xb") as out, fixed.open("rb") as incoming:
                shutil.copyfileobj(incoming,out)
        data={"schema":3,"status":MODEL_INFO,"turn_id":line["id"],"speaker":speaker,
              "voice_preset":voice,"model_sha256":hashes["kokoro_model_sha256"],
              "voice_pack_sha256":hashes["kokoro_voices_pack_sha256"],
              "project_sha256":json_digest(project),"wav_sha256":digest(dest),
              "offline_model_downloads":0,"human_voice_quality_approved":False,
              "full_ten_minute_neural_video_completed":False}
        atomic_json(receipt,data,new=True)
        completed.append(line["id"])
    remaining=sum(not (root/"voices"/(x["id"]+".wav")).is_file() for x in project["turns"])
    return {"status":"original_hindi_kokoro_on_device_voice_turns_no_face_video",
            "new_original_hindi_wav_turns":completed,"model_inference_calls":len(completed),
            "remaining_missing_voice_wavs":remaining,"speaker_voices":VOICE_MAP,
            "distinct_voice_presets_chosen":len(set(VOICE_MAP.values()))==3,
            "three_natural_voice_identities_human_verified":False,
            "full_ten_minute_neural_video_completed":False,"network_service_used":False}