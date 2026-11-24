"""Version-bound V4 PCM audio imports and exact sample timeline.

Local TTS can supply separately attributed audio receipts. No external
network requests, voice cloning or automatic voice/rights quality approval.
"""
from __future__ import annotations

import hashlib
import io
import os
import shutil
import wave
from pathlib import Path

from . import characters, projects, script_review, source

RATE=16000
PAUSE_FRAMES=RATE//4
FOLDER="audio-versions"
TIMELINE="timeline.json"
ACK="I_HAVE_RIGHTS_AND_AUDIO_MATCHES_THIS_SCRIPT_TURN"
MAX_WAV=RATE*2*120+65536
MAX_TOTAL=RATE*60*66


def _context(root,pid):
    folder=projects.project(root,pid)
    media=characters.prepare_media_binding(root,pid)
    current=script_review.current_script(root,pid,require_pass=True)
    if current["version_sha256"]!=media["script_version_sha256"]:
        raise ValueError("Current script changed during media preflight")
    req=projects.load(root,pid)
    binding={"script_version_sha256":current["version_sha256"],"cast_sha256":media["cast_sha256"],
             "request_sha256":source.json_digest(req)}
    base=folder/FOLDER
    projects._plain(base,missing=True)
    dest=base/source.json_digest(binding)
    projects._plain(dest,missing=True)
    return folder,dest,binding,current["turns"],req,media


def _pcm(raw):
    if len(raw)>MAX_WAV:raise ValueError("WAV exceeds bounded import size")
    try:
        with wave.open(io.BytesIO(raw),"rb") as w:
            if (w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getcomptype())!=(1,2,RATE,"NONE"):
                raise ValueError("Use exact PCM mono 16-bit 16kHz WAV")
            n=w.getnframes()
            if not RATE//4<=n<=120*RATE:raise ValueError("WAV turn must be 0.25–120 seconds")
            pcm=w.readframes(n)
            if len(pcm)!=n*2:raise ValueError("Truncated WAV PCM")
            if not any(pcm):raise ValueError("Silent all-zero PCM is not a speech recording")
    except (wave.Error,EOFError) as exc:raise ValueError("Invalid WAV container") from None
    return {"wav_sha256":hashlib.sha256(raw).hexdigest(),"pcm_sha256":hashlib.sha256(pcm).hexdigest(),"frames":n}


def _turn_binding(turn):
    return source.json_digest(turn)


def _read_parts(dest,binding,turns):
    if not dest.exists():return {}
    projects._plain(dest)
    by_id={t["id"]:t for t in turns}
    items={}
    for child in dest.iterdir():
        if child.name==TIMELINE:
            projects._plain(child,directory=False);continue
        if child.name in ("master","static-preview","neural-clips","neural-export","post-audio","mixed-export","studio-preview"):
            projects._plain(child);continue
        if child.name in ("audio-review.json","final-video-review.json","mix-listening-review.json","mixed-video-review.json"):
            projects._plain(child,directory=False);continue
        projects._plain(child)
        if child.name not in by_id:raise ValueError("Unknown or interrupted audio turn directory")
        if {p.name for p in child.iterdir()}!={"speech.wav","receipt.json"}:
            raise ValueError("Incomplete audio turn; inspect locally before retrying")
        receipt=child/"receipt.json";projects._plain(receipt,directory=False)
        saved=source.read_json(receipt,16_000)
        info=_pcm(characters._read_file(child/"speech.wav",MAX_WAV))
        expected={"schema":1,"binding":binding,"turn_id":child.name,
                  "turn_sha256":_turn_binding(by_id[child.name]),"speaker":by_id[child.name]["speaker"],
                  "origin":"authorized_import","rights_and_text_match_self_attested":True,**info}
        if saved.get("origin")=="local_kokoro_hindi":
            from .kokoro import VOICE_CHOICES
            extra=saved.get("generation")
            if (not isinstance(extra,dict) or set(extra)!={"voice_preset","model_sha256","voices_sha256"}
                    or extra["voice_preset"] not in VOICE_CHOICES
                    or any(not isinstance(extra[k],str) or len(extra[k])!=64 or any(c not in "0123456789abcdef" for c in extra[k])
                           for k in ("model_sha256","voices_sha256"))):
                raise ValueError("Invalid local speech provenance")
            expected.pop("rights_and_text_match_self_attested")
            expected.update(origin="local_kokoro_hindi",generation=extra,model_usage_rights_self_attested=True)
        if saved.get("origin")=="local_kokoro_multilingual":
            from .kokoro_languages import PRESETS
            extra=saved.get("generation")
            if (not isinstance(extra,dict) or set(extra)!={"voice_preset","model_sha256","voices_sha256","language"}
                    or not isinstance(extra["language"],str) or extra["language"] not in PRESETS or extra["language"]=="hi"
                    or not isinstance(extra["voice_preset"],str) or extra["voice_preset"] not in PRESETS[extra["language"]]
                    or any(not isinstance(extra[k],str) or len(extra[k])!=64 or any(c not in "0123456789abcdef" for c in extra[k]) for k in ("model_sha256","voices_sha256"))):
                raise ValueError("Invalid multilingual Kokoro provenance")
            expected.pop("rights_and_text_match_self_attested")
            expected.update(origin="local_kokoro_multilingual",generation=extra,model_usage_rights_self_attested=True)
        if saved.get("origin")=="local_espeak":
            from .v4_espeak import PRESET
            extra=saved.get("generation")
            if (not isinstance(extra,dict) or set(extra)!={"voice_preset","executable_sha256","inventory_sha256"}
                    or not isinstance(extra["voice_preset"],str) or not PRESET.fullmatch(extra["voice_preset"])
                    or any(not isinstance(extra[k],str) or len(extra[k])!=64 or any(c not in "0123456789abcdef" for c in extra[k]) for k in ("executable_sha256","inventory_sha256"))):
                raise ValueError("Invalid eSpeak speech provenance")
            expected.pop("rights_and_text_match_self_attested")
            expected.update(origin="local_espeak",generation=extra,model_usage_rights_self_attested=True)
        if saved!=expected:raise ValueError("Audio receipt, PCM hash or turn binding differs")
        items[child.name]=saved
    if len({v["pcm_sha256"] for v in items.values()})!=len(items):
        raise ValueError("Duplicate speech PCM across different turns")
    if sum(v["frames"] for v in items.values())>MAX_TOTAL:raise ValueError("Audio exceeds maximum total duration")
    return items


def _timeline(binding,turns,items,req):
    if len(items)!=len(turns):raise ValueError("Import all script turn WAVs before finalizing")
    rows=[];cursor=0
    for i,t in enumerate(turns):
        item=items[t["id"]]
        end=cursor+item["frames"]
        pause=PAUSE_FRAMES if i<len(turns)-1 else 0
        rows.append({"turn_id":t["id"],"speaker":t["speaker"],"start_frame":cursor,"speech_end_frame":end,
                     "end_frame":end+pause,"pause_frames":pause,"wav_sha256":item["wav_sha256"],
                     "pcm_sha256":item["pcm_sha256"]})
        cursor=end+pause
    target=req["duration_minutes"]*60*RATE
    return {"schema":1,"binding":binding,"sample_rate":RATE,"rows":rows,"total_frames":cursor,
            "measured_audio_seconds":cursor/RATE,"planned_seconds":target/RATE,
            "within_target_10_percent":target*9<=cursor*10<=target*11,
            "human_audio_quality_approved":False,"publication_approved":False}


def _check_timeline(dest,binding,turns,items,req):
    path=dest/TIMELINE
    if not path.exists() and not path.is_symlink():return None
    projects._plain(path,directory=False)
    data=source.read_json(path,2_000_000)
    if data!=_timeline(binding,turns,items,req):raise ValueError("Measured timeline differs from verified audio")
    return data


def _summary(pid,dest,binding,turns,items,req):
    saved=_check_timeline(dest,binding,turns,items,req)
    missing=[t["id"] for t in turns if t["id"] not in items]
    return {"project_id":pid,"binding":binding,"total_turns":len(turns),"imported_turns":len(items),
            "missing_turn_ids":missing,"measured_imported_speech_seconds":sum(v["frames"] for v in items.values() if v["origin"]=="authorized_import")/RATE,
            "completed_audio_turns":len(items),"generated_turns":sum(v["origin"] in ("local_kokoro_hindi","local_kokoro_multilingual","local_espeak") for v in items.values()),
            "measured_total_speech_seconds":sum(v["frames"] for v in items.values())/RATE,
            "timeline_finalized":saved is not None,"measured_audio_seconds":saved["measured_audio_seconds"] if saved else None,
            "within_target_10_percent":saved["within_target_10_percent"] if saved else None,
            "human_audio_quality_approved":False,"actual_video_generated":False,"publication_approved":False}


def inspect(root,pid):
    _,dest,binding,turns,req,_=_context(root,pid)
    return _summary(pid,dest,binding,turns,_read_parts(dest,binding,turns),req)


def voice_status(root,pid):
    cast=characters.status(root,pid)
    from .kokoro_languages import ALIASES,PRESETS
    rows=[]
    for item in cast.get("presenters",[]):
        voice=item["voice_preferences"];engine=voice["engine"]
        code=ALIASES.get(voice["language"].casefold().strip())
        rows.append({"speaker":item["speaker"],"preferences":voice,
                     "status":"authorized_wav_import_supported" if engine=="imported" else
                              "select_import_or_future_tts" if engine=="undecided" else
                              "local_hindi_kokoro_candidate" if engine=="kokoro" and code=="hi" and voice["preset"] in PRESETS[code] else
                              "local_multilingual_kokoro_candidate" if engine=="kokoro" and code in PRESETS and voice["preset"] in PRESETS[code] else
                              "local_espeak_inventory_required" if engine=="espeak" else
                              "generalized_tts_adapter_pending",
                     "actual_language_voice_compatibility_verified":False})
    return {"project_id":pid,"cast_assigned":cast["cast_assigned"],"voices":rows,
            "import_pcm_supported_for_any_language":True,"network_requests":0,"model_inference_calls":0}


def _save_turn(dest,binding,turn,raw,info,*,generation=None,origin="local_kokoro_hindi"):
    dest.mkdir(parents=True,exist_ok=True);projects._plain(dest)
    out=dest/turn["id"];out.mkdir()
    with (out/"speech.wav").open("xb") as handle:
        handle.write(raw);handle.flush();os.fsync(handle.fileno())
    receipt={"schema":1,"binding":binding,"turn_id":turn["id"],"turn_sha256":_turn_binding(turn),
             "speaker":turn["speaker"],**info}
    if generation is None:receipt.update(origin="authorized_import",rights_and_text_match_self_attested=True)
    else:receipt.update(origin=origin,generation=generation,model_usage_rights_self_attested=True)
    source.atomic_json(out/"receipt.json",receipt,new=True)


def import_turn(root,pid,turn_id,path,*,acknowledgment):
    if acknowledgment!=ACK:raise ValueError("Explicit audio rights and script-turn match acknowledgment required")
    folder=projects.project(root,pid)
    with projects.exclusive(folder):
        _,dest,binding,turns,req,_=_context(root,pid)
        by_id={t["id"]:t for t in turns}
        if turn_id not in by_id:raise ValueError("Unknown script turn ID")
        items=_read_parts(dest,binding,turns)
        if _check_timeline(dest,binding,turns,items,req) is not None:raise ValueError("Timeline already finalized")
        if turn_id in items:raise ValueError("Audio turn already imported; no overwrite")
        raw=characters._read_file(path,MAX_WAV);info=_pcm(raw)
        if any(v["pcm_sha256"]==info["pcm_sha256"] for v in items.values()):raise ValueError("Duplicate speech PCM")
        if sum(v["frames"] for v in items.values())+info["frames"]>MAX_TOTAL:
            raise ValueError("Audio exceeds maximum total duration")
        if shutil.disk_usage(folder).free<len(raw)+1024**2:raise ValueError("Insufficient private workspace disk space")
        if _context(root,pid)[2]!=binding:raise ValueError("Script or cast changed during import")
        _save_turn(dest,binding,by_id[turn_id],raw,info)
        return _summary(pid,dest,binding,turns,_read_parts(dest,binding,turns),req)


def finalize(root,pid):
    folder=projects.project(root,pid)
    with projects.exclusive(folder):
        _,dest,binding,turns,req,_=_context(root,pid)
        items=_read_parts(dest,binding,turns)
        saved=_check_timeline(dest,binding,turns,items,req)
        if saved is None:
            saved=_timeline(binding,turns,items,req)
            source.atomic_json(dest/TIMELINE,saved,new=True)
        return {**_summary(pid,dest,binding,turns,items,req),"timeline_sha256":source.json_digest(saved)}


def show(root,pid):
    _,dest,binding,turns,req,_=_context(root,pid)
    items=_read_parts(dest,binding,turns)
    saved=_check_timeline(dest,binding,turns,items,req)
    if saved is None:raise ValueError("Finalize the measured audio timeline first")
    return {"project_id":pid,"timeline":saved}
