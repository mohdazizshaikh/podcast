"""Explicit READ-ONLY private Windows Hindi studio stage/acceptance inspection.

Unlike checking whether files exist, any "verified" stage uses the original
source SHA/PCM or independent FFmpeg decoder from the production pipeline.
No local source/media/receipt is created, deleted or changed by this module.
A complete structural candidate NEVER implies approved natural lip-sync,
human likeness permission, or publication readiness.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image

from . import source


def inspect(root: Path, *, allow_short: bool=False) -> dict:
    root=source.workspace_path(root)
    result={
        "status":"private_hindi_podcast_read_only_acceptance_inspection",
        "workspace":str(root),
        "schema":1,
        "checks":{},
        "new_model_inference_calls":0,
        "new_tts_service_calls":0,
        "downloads":0,
        "new_video_render_calls":0,
        "human_lipsync_accuracy_automatically_approved":False,
        "creator_portrait_rights_independently_verified":False,
        "publication_approved":False,
        "synthetic_short_test_only":bool(allow_short),
    }
    stages=result["checks"]
    def mark(key,status,**details):
        stages[key]={"status":status,**details}
    def gate(key,work):
        try:
            evidence=work()
            mark(key,"verified",**evidence)
            return True
        except Exception as err:
            mark(key,"blocked",reason=str(err))
            return False
    if not root.is_dir():
        mark("workspace","missing")
        result["next_safe_action"]="INIT — initialize a new private workspace outside the public Git repository"
        result["all_source_and_media_structurally_verified"]=False
        return result
    mark("workspace","exists_private_path_not_rights_certified")
    originals_lock=root/"source"/source.ORIGINALS_LOCK
    if originals_lock.exists() or originals_lock.is_symlink():
        # A different Windows/CLI process may be generating original WAVs or
        # binding its SHA source RIGHT NOW. Never report a half-written source
        # as complete, and never remove someone else's exclusive lock.
        mark("original_voice_source_session","blocked",
             reason="Private original WAV/TTS/BIND session active or interrupted; inspect lock manually",
             lock_path=str(originals_lock))
        result["blocked_stages"]=["original_voice_source_session"]
        result["next_safe_action"]="STOP — original voice/BIND process active or crashed; inspect private exclusive lock before retrying"
        result["all_source_and_media_structurally_verified"]=False
        return result
    mark("original_voice_source_session","clear")
    from .media import EXPORT_LOCK
    from .neural import LOCK as CPU_LOCK
    for key, name in (("media_export_session", EXPORT_LOCK), ("cpu_neural_session", CPU_LOCK)):
        lock = root / "source" / name
        if lock.exists() or lock.is_symlink():
            mark(key, "blocked", reason="Private media session active or interrupted; inspect lock manually", lock_path=str(lock))
            result["blocked_stages"] = [key]
            result["next_safe_action"] = "STOP — media session active or interrupted; inspect the private lock before retrying"
            result["all_source_and_media_structurally_verified"] = False
            return result
        mark(key, "clear")
    project_path=root/"project.json"
    if not project_path.exists() and not project_path.is_symlink():
        mark("script","missing")
        project=None
    else:
        try:
            project=source.load_project(root)
            mark("script","verified",turns=len(project["turns"]),
                 per_presenter={name:sum(x["speaker"]==name for x in project["turns"])
                                for name in source.SPEAKERS})
        except Exception as err:
            mark("script","blocked",reason=str(err))
            project=None

    portraits=[]
    errors={}
    for name in source.SPEAKERS:
        path=root/"portraits"/(name+".png")
        if not path.exists() or path.is_symlink():
            if path.is_symlink():errors[name]="Unsafe portrait symlink"
            continue
        try:
            if not path.is_file() or path.stat().st_size>25_000_000:
                raise ValueError("Oversized/invalid portrait")
            with Image.open(path) as img:
                img.verify()
            with Image.open(path) as img:
                if img.format!="PNG" or min(img.size)<200:
                    raise ValueError("Portrait not valid PNG >=200px")
            portraits.append(name)
        except Exception as err:
            errors[name]=str(err)
    mark("portrait_files",("blocked" if errors else "present_unbound"
                           if len(portraits)==3 else "partial"),
         valid_presenters=portraits,missing_presenters=[
             name for name in source.SPEAKERS if name not in portraits],
         problems=errors,ownership_self_attestation_not_rights_proof=True)

    voices=[]
    voice_errors={}
    unique=set()
    total=0.0
    for n in range(1,46):
        id_=f"{n:03}"
        path=root/"voices"/(id_+".wav")
        if not path.exists() and not path.is_symlink():
            continue
        try:
            frames,duration=source.wav_info(path)
            voices.append(id_)
            unique.add(source.digest(path))
            total+=duration
        except Exception as err:
            voice_errors[id_]=str(err)
    if project:
        total+=sum(float(x["pause_after"]) for x in project["turns"])
    duration_ok=(len(voices)==45 and project is not None
                 and (allow_short or source.TOTAL_MIN<=total<=source.TOTAL_MAX))
    duplicate=len(voices)==45 and len(unique)!=45
    if duplicate:voice_errors["duplicate"]="Original 45 WAVs must have distinct SHA256"
    if len(voices)==45 and not duration_ok:
        voice_errors["timeline"]=f"Source duration {total:.2f}s must be 540–660 seconds"
    mark("original_voice_files",("blocked" if voice_errors else
                                "technically_valid_unbound" if len(voices)==45
                                else "partial"),
         valid_wavs=len(voices),missing_wavs=[f"{n:03}" for n in range(1,46)
                                             if f"{n:03}" not in voices],
         measured_seconds=round(total,3),production_duration_gate_met=duration_ok,
         problems=voice_errors,human_hindi_voice_quality_verified=False)

    signed=root/"source"/source.SOURCE_FILE
    src_ok=False
    if signed.is_symlink():
        mark("source_sha","blocked",reason="Unsafe signed-source manifest symlink")
    elif not signed.exists():
        mark("source_sha","missing")
    else:
        src_ok=gate("source_sha",lambda:{
            "original_seconds":source.verify_source(
                root,allow_short=allow_short)["original_seconds"],
            "exact_45_wav_portrait_and_script_shas_verified":True
        })

    chunks_ok=False
    chunk_path=root/"source"/source.CHUNK_FILE
    if chunk_path.is_symlink():
        mark("exact_pcm_chunks","blocked",reason="Unsafe chunk manifest symlink")
    elif not chunk_path.exists():
        mark("exact_pcm_chunks","missing")
    elif src_ok:
        chunks_ok=gate("exact_pcm_chunks",lambda:{
            "signed_chunk_count":source.verify_chunks(
                root,allow_short=allow_short)["count"],
            "original_pcm_bytes_verified":True
        })
    else:
        mark("exact_pcm_chunks","blocked",reason="Cannot validate chunks against unverified original source")

    static_base=root/"exports"
    static_paths=[static_base/"original_hindi_static.mp4",
                  static_base/"original_hindi_static.json",
                  static_base/"original_hindi.srt"]
    static_ok=False
    if any(p.exists() or p.is_symlink() for p in static_paths):
        if src_ok:
            from . import media
            static_ok=gate("static_video",lambda:{
                "decoded_720p_aac_srt_not_neural_lipsync":
                media.audit_static(root,allow_short=allow_short)[
                    "original_hindi_static_structurally_verified"]
            })
        else:
            mark("static_video","blocked",reason="Cannot audit against unverified original source")
    else:
        mark("static_video","missing")

    preview_state={}
    if chunks_ok:
        from . import neural
        try:
            preview_state=neural.progress(root,allow_short=allow_short)
            count=preview_state["verified"]
            total_chunks=preview_state["total"]
            mark("face_preview_mp4",("all_decoded" if count==total_chunks else
                                      "partial" if count else "missing"),
                 independently_sha_decoded=count,required=total_chunks,
                 per_presenter=preview_state["by_speaker"],
                 real_natural_lipsync_human_verified=False)
        except Exception as err:
            mark("face_preview_mp4","blocked",reason=str(err))
    else:
        mark("face_preview_mp4","not_yet_verifiable")

    record=root/"review"/"three-presenter-human-observations.json"
    if record.is_symlink():
        mark("pilot_human_observation","blocked",reason="Manual review record symlink")
    elif record.exists():
        if preview_state.get("three_presenter_samples_ready"):
            from . import review
            gate("pilot_human_observation",lambda:{
                "self_attested_passes_not_publication_approval":
                review.inspect_pilot(root,allow_short=allow_short)[
                    "every_presenter_manual_pass"]
            })
        else:
            mark("pilot_human_observation","blocked",reason="Cannot validate record without 3 decoded speaker faces")
    else:
        mark("pilot_human_observation","missing")
    candidate=[static_base/"original_hindi_full_neural.mp4",
               static_base/"original_hindi_full_neural.json",
               static_base/"original_hindi_full_neural.srt"]
    full_ok=False
    if any(p.exists() or p.is_symlink() for p in candidate):
        if preview_state.get("all_speech_neural_clips_structurally_present"):
            from . import neural
            full_ok=gate("full_neural_candidate",lambda:{
                "all_45_turns_real_video_aac_srt_decoded_not_human_certified":
                neural.audit_neural(root,allow_short=allow_short)[
                    "complete_45_turn_video_structurally_audited"]
            })
        else:
            mark("full_neural_candidate","blocked",reason="Cannot validate candidate without all 45 turns' decoded face clips")
    else:
        mark("full_neural_candidate","missing")

    blocked=[k for k,v in stages.items() if v["status"]=="blocked"]
    if blocked:
        result["next_safe_action"]="STOP — manually inspect blocked stages; never overwrite, forge approval or bypass signed originals"
        result["blocked_stages"]=blocked
    elif project is None:
        result["next_safe_action"]="INIT — initialize original 45-turn Hindi private project"
    elif len(portraits)!=3:
        result["next_safe_action"]="Import three authorized original PNG portraits (AI likeness rights self-attested, not automatic)"
    elif len(voices)!=45:
        result["next_safe_action"]="Import/generate remaining original 16kHz Hindi WAVs; verify voice quality and duration"
    elif not src_ok:
        result["next_safe_action"]="BIND — verify 540–660s source and write original SHA manifest"
    elif not chunks_ok:
        result["next_safe_action"]="CHUNKS — export signed original 1–10s PCM segments"
    elif not static_ok:
        result["next_safe_action"]="STATIC then AUDIT — create/verify 720p non-lipsync fallback"
    elif not preview_state.get("three_presenter_samples_ready"):
        result["next_safe_action"]="MODEL preflight, then consented PILOT: first genuine Aarav/Meera/Kabir samples"
    elif stages["pilot_human_observation"].get("status")!="verified":
        result["next_safe_action"]="REVIEW/RECORD — manually inspect all 3 genuine face samples and record private PASS/FAIL"
    elif not stages["pilot_human_observation"].get(
            "self_attested_passes_not_publication_approval"):
        result["next_safe_action"]="STOP — pilot manual FAIL: improve real model/face quality, do not start costly full render"
    elif not preview_state.get("all_speech_neural_clips_structurally_present"):
        result["next_safe_action"]="BUDGET then separately consented BATCH/SESSION for remaining authentic face clips"
    elif not full_ok:
        result["next_safe_action"]="COMPOSE then AUDITFULL — combine all verified previews with original Hindi audio"
    else:
        result["next_safe_action"]="REVIEWFULL — watch/listen to all 45 turns; personally verify lips/voice/rights BEFORE any publishing"

    result["all_source_and_media_structurally_verified"]=bool(
        src_ok and chunks_ok and static_ok and full_ok)
    return result
