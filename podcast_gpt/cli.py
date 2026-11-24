"""Command line entry point for source-bound, privacy-first three-presenter studio."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

from . import __version__


def parse(argv=None):
    p=argparse.ArgumentParser(description="Podcast GPT — reconstructed private Hindi CPU studio")
    p.add_argument("--workspace",type=Path,default=Path(os.environ.get("PODCAST_WORKSPACE",str(Path.home()/"PodcastGPTStudio"))))
    subs=p.add_subparsers(dest="operation",required=True)
    for name in ("doctor","init","build-source","verify-source","prepare-chunks","verify-chunks",
                 "render-static","audit-static","progress","budget","readiness","review-pilot","inspect-pilot",
                 "compose-neural","audit-neural","review-full","recovery","check-pilot-gate",
                 "template-full-review","inspect-full-review","web"):
        cmd=subs.add_parser(name)
        if name=="web":
            cmd.add_argument("--port",type=int,default=7860)
            cmd.add_argument("--open-browser",action="store_true",
                             help="Open default browser only after successful local server bind")
    create=subs.add_parser("project-create",help="Create separate private V4 planning project")
    create.add_argument("--request",type=Path,required=True)
    subs.add_parser("project-list",help="List private V4 planning projects")
    show=subs.add_parser("project-show")
    show.add_argument("--project-id",required=True)
    ingest=subs.add_parser("project-import-source",help="Import one bounded private document or explicit public HTTPS source")
    ingest.add_argument("--project-id",required=True)
    item=ingest.add_mutually_exclusive_group(required=True)
    item.add_argument("--file",type=Path)
    item.add_argument("--url")
    ingest.add_argument("--allow-web-fetch",action="store_true")
    capture=subs.add_parser("project-research-capture",help="Capture 2–4 user-selected public HTTPS sources")
    capture.add_argument("--project-id",required=True)
    capture.add_argument("--url",action="append",required=True)
    capture.add_argument("--allow-web-fetch",action="store_true")
    research_status=subs.add_parser("project-research-status")
    research_status.add_argument("--project-id",required=True)
    outline=subs.add_parser("project-plan")
    outline.add_argument("--project-id",required=True)
    outline.add_argument("--allow-cloud-text",action="store_true")
    outline.add_argument("--confirm-gemini-free-project",action="store_true")
    outline.add_argument("--offline-only",action="store_true")
    outline.add_argument("--ollama-model")
    script=subs.add_parser("project-script-generate",help="Generate 1–5 new source-bound planned minutes")
    script.add_argument("--project-id",required=True)
    script.add_argument("--max-new",type=int,default=1)
    script.add_argument("--allow-cloud-text",action="store_true")
    script.add_argument("--confirm-gemini-free-project",action="store_true")
    script.add_argument("--offline-only",action="store_true")
    script.add_argument("--ollama-model")
    for name in ("project-script-status","project-script-finalize","project-script-show"):
        s=subs.add_parser(name)
        s.add_argument("--project-id",required=True)
    for name in ("project-script-edit-template","project-script-revise","project-script-review-template",
                 "project-script-review-record","project-script-review-status","project-script-current"):
        r=subs.add_parser(name)
        r.add_argument("--project-id",required=True)
        if name=="project-script-review-record":r.add_argument("--acknowledgment",required=True)
    char=subs.add_parser("character-create",help="Save a reusable local character profile and optional authorized PNG")
    char.add_argument("--profile",type=Path,required=True)
    char.add_argument("--portrait",type=Path)
    char.add_argument("--acknowledgment")
    char.add_argument("--parent-id")
    subs.add_parser("character-list")
    char_show=subs.add_parser("character-show")
    char_show.add_argument("--character-id",required=True)
    cast=subs.add_parser("project-cast-assign")
    cast.add_argument("--project-id",required=True)
    cast.add_argument("--mapping",type=Path,required=True)
    for name in ("project-cast-status","project-media-preflight"):
        c=subs.add_parser(name)
        c.add_argument("--project-id",required=True)
    audio=subs.add_parser("project-audio-import",help="Import authorized PCM WAV bound to a reviewed script turn")
    audio.add_argument("--project-id",required=True)
    audio.add_argument("--turn-id",required=True)
    audio.add_argument("--file",type=Path,required=True)
    audio.add_argument("--acknowledgment",required=True)
    for name in ("project-voice-status","project-audio-status","project-audio-finalize","project-audio-show"):
        v=subs.add_parser(name)
        v.add_argument("--project-id",required=True)
    for name in ("key-store","key-remove","key-status"):
        k=subs.add_parser(name)
        k.add_argument("--project-id")
        if name!="key-status":k.add_argument("--provider",choices=("openrouter","gemini"),required=True)
    subs.add_parser("ai-provider-status",help="Local key presence and strict free provider policy; no calls")
    planner=subs.add_parser("plan-episode",help="V4 topic-based episode outline, not media generation")
    planner.add_argument("--request",type=Path,required=True)
    planner.add_argument("--allow-cloud-text",action="store_true")
    planner.add_argument("--confirm-gemini-free-project",action="store_true")
    planner.add_argument("--offline-only",action="store_true")
    planner.add_argument("--ollama-model")
    planner.add_argument("--prompt-keys",action="store_true",help="Optional session-only override; never store keys")
    setup=subs.add_parser("setup-wizard",help="Unified V4 hardware and local model setup inventory")
    setup.add_argument("--interactive",action="store_true")
    setup.add_argument("--kokoro-model",type=Path)
    setup.add_argument("--kokoro-voices",type=Path)
    setup.add_argument("--sadtalker-root",type=Path)
    setup.add_argument("--sadtalker-python",type=Path)
    setup.add_argument("--probe-interpreter",action="store_true",help="Explicitly allow selected trusted Python version probe")
    full_review=subs.add_parser("record-full-review",help="Record all 45 manually reviewed turn observations")
    full_review.add_argument("--acknowledgment",required=True)
    recover=subs.add_parser("archive-failed-attempt",help="Preserve one stopped model attempt in a private archive")
    recover.add_argument("--chunk-id",required=True)
    recover.add_argument("--acknowledgment",required=True)
    preflight=subs.add_parser("check-sadtalker",help="READ ONLY local SadTalker CPU installation check; NO inference")
    preflight.add_argument("--sadtalker-root",type=Path,required=True)
    preflight.add_argument("--sadtalker-python",type=Path,required=True)
    kokoro_check=subs.add_parser("check-kokoro",help="Read-only local Kokoro assets and dependency inventory")
    kokoro_check.add_argument("--model",type=Path,required=True)
    kokoro_check.add_argument("--voices",type=Path,required=True)
    cpu=subs.add_parser("run-cpu",help="Genuine local SadTalker CPU; requires explicit rights")
    cpu.add_argument("--mode",choices=("pilot","batch","session"),required=True)
    cpu.add_argument("--max-new",type=int,default=3)
    cpu.add_argument("--wall-seconds",type=int,default=7200)
    cpu.add_argument("--per-chunk-timeout",type=int,default=1800)
    cpu.add_argument("--sadtalker-root",type=Path,required=True)
    cpu.add_argument("--sadtalker-python",type=Path,required=True)
    cpu.add_argument("--rights-confirmed",action="store_true")
    cpu.add_argument("--cpu-threads",type=int,help="Native CPU thread pool hint; default leaves one CPU free when possible, capped at four")
    review=subs.add_parser("record-pilot")
    for name in ("aarav","meera","kabir"):
        review.add_argument("--"+name,choices=("PASS","FAIL"),required=True)
    review.add_argument("--acknowledgment",required=True)
    offline=subs.add_parser("tts-kokoro",help="Optional genuine OFFLINE 3-distinct-preset Hindi Kokoro ONNX CPU WAV")
    offline.add_argument("--model",type=Path,required=True,help="existing local Kokoro v1.0 .onnx")
    offline.add_argument("--voices",type=Path,required=True,help="existing local voices-v1.0.bin")
    offline.add_argument("--turn",type=int)
    offline.add_argument("--next",action="store_true",help="generate earliest missing original WAVs")
    offline.add_argument("--max-new",type=int,default=1,help="at most 5 explicit new WAVs per run")
    offline.add_argument("--run-local",action="store_true",help="explicit model inference consent; no downloads")
    voice=subs.add_parser("tts-one",help="OPTIONAL explicit online Edge Hindi TTS for one turn")
    voice.add_argument("--turn",type=int,required=True)
    voice.add_argument("--allow-network-tts",action="store_true")
    voice.add_argument("--voice",choices=("hi-IN-MadhurNeural","hi-IN-SwaraNeural"))
    return p.parse_args(argv)


def doctor(root:Path) -> dict:
    from .media import tools_ready
    import importlib.util
    media=tools_ready()
    parent=root.resolve()
    while not parent.exists() and parent!=parent.parent:
        parent=parent.parent
    free_gib=round(shutil.disk_usage(parent).free/(1024**3),2)
    from .hardware import report
    return {"hardware":report(),"version":__version__,"workspace":str(root.resolve()),
            "workspace_disk_free_gib":free_gib,"source_minimum_free_gib_for_render":3,
            "neural_minimum_free_gib_for_render":6,
            "ffmpeg":bool(media["ffmpeg"]),"ffprobe":bool(media["ffprobe"]),
            "pillow":bool(importlib.util.find_spec("PIL")),
            "edge_tts_optional":bool(importlib.util.find_spec("edge_tts")),
            "sadtalker_cpu_model_included":False,"portrait_rights_automatically_verified":False,
            "original_10_min_neural_video_verified":False}


async def _tts_one(root:Path, turn:int, allow:bool, voice:str|None)->dict:
    """Optional ONLINE Edge voice. No network until explicit consent and preflight."""
    if allow is not True:raise ValueError("Online TTS requires explicit --allow-network-tts")
    if type(turn) is not int or not 1<=turn<=45:
        raise ValueError("Original Hindi turn must be 1..45")
    from .source import (load_project, SOURCE_FILE, wav_info, digest,
                         json_digest, atomic_json, workspace_path,
                         original_voice_lock)
    root=workspace_path(root)
    with original_voice_lock(root):
        project=load_project(root)
        line=project["turns"][turn-1]
        if voice is None:
            voice="hi-IN-SwaraNeural" if line["speaker"]=="meera" else "hi-IN-MadhurNeural"
        if voice not in ("hi-IN-SwaraNeural","hi-IN-MadhurNeural"):
            raise ValueError("Explicit unsupported online Hindi voice preset")
        bound=root/"source"/SOURCE_FILE
        if bound.exists() or bound.is_symlink():
            raise ValueError("Original private source already SHA-bound; online TTS cannot alter it")
        folder=root/"voices"
        if folder.is_symlink() or not folder.is_dir():
            raise ValueError("Original private voices folder missing/unsafe")
        wav=folder/(line["id"]+".wav")
        receipt=folder/(line["id"]+".edge-tts-source.json")
        if any(p.exists() or p.is_symlink() for p in (wav,receipt)):
            raise ValueError("Original Hindi WAV/online-TTS receipt exists; never overwrite")
        scratch_root=root/"scratch"
        if scratch_root.is_symlink() or not scratch_root.is_dir():
            raise ValueError("Private voice scratch directory missing/unsafe")
        if shutil.disk_usage(scratch_root).free<100*1024**2:
            raise ValueError("At least 100 MiB free on the private original voice scratch drive required")
        try:
            import edge_tts
        except ImportError as err:
            raise ValueError("Optional online edge-tts not installed; install pip install -e '.[tts]'") from err
        import tempfile
        from .media import cmd
        rate="-10%" if line["speaker"]=="kabir" else "+0%"
        with tempfile.TemporaryDirectory(prefix="hindi-online-tts-",dir=scratch_root) as tempdir:
            tmp=Path(tempdir)
            mp3=tmp/"original-online.mp3"
            await edge_tts.Communicate(line["text"],voice,rate=rate).save(str(mp3))
            converted=tmp/"original-16k.wav"
            cmd(["ffmpeg","-y","-hide_banner","-v","error","-i",str(mp3),
                 "-ar","16000","-ac","1","-c:a","pcm_s16le",str(converted)],timeout=120)
            wav_info(converted)
            # A real network call may take seconds. Recheck both immutable project
            # and source-manifest state before committing any source WAV.
            if load_project(root)!=project or bound.exists() or bound.is_symlink():
                raise ValueError("Original Hindi project/source SHA changed during online TTS")
            if receipt.exists() or receipt.is_symlink():
                raise ValueError("Online TTS receipt exists; no repeated or ambiguous source")
            with wav.open("xb") as dest, converted.open("rb") as inp:
                shutil.copyfileobj(inp,dest)
            atomic_json(receipt,{
                "schema":3,"status":"explicit_online_edge_hindi_original_voice_not_neural_face",
                "turn_id":line["id"],"speaker":line["speaker"],"voice_preset":voice,
                "speech_rate":rate,"project_sha256":json_digest(project),
                "wav_sha256":digest(wav),"network_tts_used":True,
                "all_three_distinct_natural_voices_guaranteed":False,
                "human_voice_quality_approved":False,
                "full_ten_minute_neural_video_completed":False
            },new=True)
        return {"saved_original_hindi_wav":line["id"],"network_tts_used":True,
                "source_wav_sha256":digest(wav),
                "all_three_distinct_natural_voice_identities_guaranteed":False,
                "human_voice_quality_approved":False,
                "full_ten_minute_neural_video_completed":False}


def execute(a)->dict:
    root=a.workspace.expanduser().resolve()
    action=a.operation
    if action=="doctor":return doctor(root)
    if action in ("project-create","project-list","project-show","project-plan","project-import-source","key-store","key-remove","key-status"):
        from . import projects,episode_plan,credentials
        # Use unresolved user path so project manager can reject reparse points.
        private=a.workspace.expanduser().absolute()
        if action=="project-create":return projects.create(private,episode_plan.load_request(a.request))
        if action=="project-list":return projects.list_projects(private)
        if action=="project-show":return projects.inspect(private,a.project_id)
        if action=="project-import-source":return projects.import_source(private,a.project_id,path=a.file,url=a.url,allow_web_fetch=a.allow_web_fetch)
        if action=="key-status":return credentials.status(private,pid=a.project_id)
        if action=="key-store":return credentials.store(private,a.provider,credentials.prompt_key(a.provider),pid=a.project_id)
        if action=="key-remove":return credentials.remove(private,a.provider,pid=a.project_id)
        keys=credentials.resolve(private,pid=a.project_id) if a.allow_cloud_text and not a.offline_only else None
        return projects.generate_outline(private,a.project_id,credentials=keys,
            allow_cloud_text=a.allow_cloud_text,confirm_gemini_free_project=a.confirm_gemini_free_project,
            offline_only=a.offline_only,local_model=a.ollama_model)
    if action in ("project-research-capture","project-research-status"):
        from . import research
        private=a.workspace.expanduser().absolute()
        if action=="project-research-status":return research.inspect(private,a.project_id)
        return research.capture(private,a.project_id,a.url,allow_web_fetch=a.allow_web_fetch)
    if action in ("project-script-generate","project-script-status","project-script-finalize","project-script-show"):
        from . import script_generation,credentials
        private=a.workspace.expanduser().absolute()
        if action=="project-script-status":return script_generation.inspect(private,a.project_id)
        if action=="project-script-finalize":return script_generation.finalize(private,a.project_id)
        if action=="project-script-show":return script_generation.show(private,a.project_id)
        keys=credentials.resolve(private,pid=a.project_id) if a.allow_cloud_text and not a.offline_only else None
        return script_generation.generate(private,a.project_id,max_new=a.max_new,credentials=keys,
            allow_cloud_text=a.allow_cloud_text,confirm_gemini_free_project=a.confirm_gemini_free_project,
            offline_only=a.offline_only,local_model=a.ollama_model)
    if action in ("project-script-edit-template","project-script-revise","project-script-review-template",
                  "project-script-review-record","project-script-review-status","project-script-current"):
        from . import script_review
        private=a.workspace.expanduser().absolute()
        if action=="project-script-edit-template":return script_review.template(private,a.project_id)
        if action=="project-script-revise":return script_review.revise(private,a.project_id)
        if action=="project-script-review-template":return script_review.template(private,a.project_id,review=True)
        if action=="project-script-review-record":return script_review.record(private,a.project_id,acknowledgment=a.acknowledgment)
        if action=="project-script-review-status":return script_review.inspect(private,a.project_id)
        return script_review.current_script(private,a.project_id)
    if action in ("character-create","character-list","character-show","project-cast-assign","project-cast-status","project-media-preflight"):
        from . import characters
        private=a.workspace.expanduser().absolute()
        if action=="character-create":return characters.create_from_file(private,a.profile,portrait=a.portrait,acknowledgment=a.acknowledgment,parent_id=a.parent_id)
        if action=="character-list":return characters.list_characters(private)
        if action=="character-show":return characters.read(private,a.character_id)
        if action=="project-cast-assign":return characters.assign_from_file(private,a.project_id,a.mapping)
        if action=="project-cast-status":return characters.status(private,a.project_id)
        return characters.prepare_media_binding(private,a.project_id)
    if action in ("project-voice-status","project-audio-import","project-audio-status","project-audio-finalize","project-audio-show"):
        from . import v4_audio
        private=a.workspace.expanduser().absolute()
        if action=="project-voice-status":return v4_audio.voice_status(private,a.project_id)
        if action=="project-audio-import":return v4_audio.import_turn(private,a.project_id,a.turn_id,a.file,acknowledgment=a.acknowledgment)
        if action=="project-audio-status":return v4_audio.inspect(private,a.project_id)
        if action=="project-audio-finalize":return v4_audio.finalize(private,a.project_id)
        return v4_audio.show(private,a.project_id)
    if action=="ai-provider-status":
        from .ai_providers import inventory
        return inventory()
    if action=="plan-episode":
        from . import ai_providers,episode_plan
        credentials=ai_providers.Credentials.environment()
        if a.prompt_keys:
            if not a.allow_cloud_text or a.offline_only:
                raise ValueError("Session cloud keys require explicit cloud text consent")
            import getpass
            try:
                router=getpass.getpass("OpenRouter free API key (Enter to retain environment default): ")
                gemini=getpass.getpass("Gemini free API key (Enter to retain environment default): ") if a.confirm_gemini_free_project else ""
            except (EOFError,KeyboardInterrupt):
                raise ValueError("AI key input cancelled")
            credentials=ai_providers.Credentials(router or credentials.openrouter,gemini or credentials.gemini)
        return episode_plan.plan(episode_plan.load_request(a.request),credentials=credentials,
            allow_cloud_text=a.allow_cloud_text,confirm_gemini_free_project=a.confirm_gemini_free_project,
            offline_only=a.offline_only,local_model=a.ollama_model)
    if action=="setup-wizard":
        from . import setup_wizard
        if a.interactive:
            if any((a.kokoro_model,a.kokoro_voices,a.sadtalker_root,a.sadtalker_python,a.probe_interpreter)):
                raise ValueError("Use interactive wizard OR explicit model path options")
            try:return setup_wizard.interactive(root)
            except (EOFError,KeyboardInterrupt):
                raise ValueError("Setup wizard cancelled; no model inference or downloads")
        return setup_wizard.inspect(root,kokoro_model=a.kokoro_model,kokoro_voices=a.kokoro_voices,
                  sadtalker_root=a.sadtalker_root,sadtalker_python=a.sadtalker_python,
                  probe_interpreter=a.probe_interpreter)
    from . import source,media,neural,review
    if action=="init":return {"original_project":source.init(root)}
    if action=="build-source":return source.build_source(root)
    if action=="verify-source":return source.verify_source(root)
    if action=="prepare-chunks":return source.prepare_chunks(root)
    if action=="verify-chunks":
        result=source.verify_chunks(root)
        return {"signed_original_chunks":result["count"],"verified_exact_pcm":True,
                "full_neural_video_completed":False}
    if action=="render-static":return media.render_static(root)
    if action=="audit-static":return media.audit_static(root)
    if action=="progress":return neural.progress(root)
    if action=="readiness":
        from .readiness import inspect
        return inspect(root)
    if action=="recovery":
        from .recovery import inspect
        return inspect(root)
    if action=="archive-failed-attempt":
        from .recovery import archive
        return archive(root,a.chunk_id,acknowledgment=a.acknowledgment)
    if action=="budget":
        from .budget import estimate_cpu_budget
        return estimate_cpu_budget(root)
    if action=="check-sadtalker":
        from .model_preflight import inspect_sadtalker_installation
        return inspect_sadtalker_installation(a.sadtalker_root,a.sadtalker_python)
    if action=="check-kokoro":
        from .kokoro_preflight import inspect
        return inspect(a.model,a.voices)
    if action=="run-cpu":return neural.run_cpu(root,mode=a.mode,
            rights_confirmed=a.rights_confirmed,max_new=a.max_new,
            wall_seconds=a.wall_seconds,per_chunk_timeout=a.per_chunk_timeout,
            sadtalker_root=a.sadtalker_root,sadtalker_python=a.sadtalker_python,cpu_threads=a.cpu_threads)
    if action=="review-pilot":return review.review_pilot(root)
    if action=="record-pilot":return review.record_pilot(root,
           {name:getattr(a,name) for name in source.SPEAKERS},a.acknowledgment)
    if action=="inspect-pilot":return review.inspect_pilot(root)
    if action=="check-pilot-gate":return review.check_batch_pilot(root)
    if action=="compose-neural":return neural.compose_neural(root)
    if action=="audit-neural":return neural.audit_neural(root)
    if action=="review-full":return review.review_full(root)
    if action in ("template-full-review","record-full-review","inspect-full-review"):
        from . import final_review
        if action=="template-full-review":return final_review.template(root)
        if action=="record-full-review":return final_review.record(root,acknowledgment=a.acknowledgment)
        return final_review.inspect(root)
    if action=="tts-kokoro":
        from .kokoro import generate
        return generate(root,model=a.model,voices=a.voices,turn=a.turn,
                        next_missing=a.next,max_new=a.max_new,run_local=a.run_local)
    if action=="tts-one":
        import asyncio
        return asyncio.run(_tts_one(root,a.turn,a.allow_network_tts,a.voice))
    if action=="web":
        from .web import serve
        serve(root,a.port,open_browser=a.open_browser)
        return {"dashboard_stopped":True}
    raise ValueError("Unknown action")


def _print_json(result,stream=None)->None:
    """Preserve Unicode JSON on UTF-8 terminals and legacy redirected CMD.

    Fall back to JSON Unicode escapes before writing any bytes if the selected
    stream cannot encode the original Hindi. The decoded JSON is identical.
    """
    stream=sys.stdout if stream is None else stream
    payload=json.dumps(result,ensure_ascii=False,indent=2,default=str)
    encoding=getattr(stream,"encoding",None)
    if encoding:
        try:payload.encode(encoding,errors="strict")
        except UnicodeEncodeError:
            payload=json.dumps(result,ensure_ascii=True,indent=2,default=str)
    print(payload,file=stream)


def _print_error(err)->None:
    message="BLOCKED: "+str(err)
    encoding=getattr(sys.stderr,"encoding",None)
    if encoding:
        message=message.encode(encoding,errors="backslashreplace").decode(encoding)
    print(message,file=sys.stderr)


def main(argv=None)->int:
    try:
        args=parse(argv)
        result=execute(args)
        _print_json(result)
        return 0
    except (ValueError,RuntimeError,OSError,TimeoutError,KeyError,TypeError,ImportError,
            json.JSONDecodeError) as err:
        # Avoid leaking user-supplied Hindi dialogue, portraits or private secrets.
        _print_error(err)
        return 1

if __name__=="__main__":
    raise SystemExit(main())