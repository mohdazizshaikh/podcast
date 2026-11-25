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
    manual=subs.add_parser("project-script-import-verbatim")
    manual.add_argument("--project-id",required=True)
    manual.add_argument("--acknowledgment",required=True)
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
        if name in ("project-script-revise","project-script-review-record"):r.add_argument("--file",type=Path)
    visual=subs.add_parser("project-script-visual")
    visual.add_argument("--project-id",required=True)
    visual.add_argument("--mode",choices=("edit","review"),required=True)
    for name in ("dependency-plan","dependency-install"):
        dep=subs.add_parser(name)
        dep.add_argument("--group",choices=("documents","kokoro","kokoro-english","kokoro-mandarin","kokoro-japanese","edge"),required=True)
        if name=="dependency-install":dep.add_argument("--acknowledgment",required=True)
    auto=subs.add_parser("project-auto-step")
    auto.add_argument("--project-id",required=True)
    auto.add_argument("--execute",action="store_true")
    auto.add_argument("--acknowledgment")
    auto.add_argument("--max-steps",type=int,default=3)
    auto.add_argument("--allow-local-ai",action="store_true")
    auto.add_argument("--kokoro-ack")
    auto.add_argument("--espeak-ack")
    auto.add_argument("--neural-ack")
    overview=subs.add_parser("project-production-overview")
    overview.add_argument("--project-id",required=True)
    checkmedia=subs.add_parser("project-media-check")
    checkmedia.add_argument("--project-id",required=True)
    checkmedia.add_argument("--kind",choices=("master","preview","neural","mix","mixed","studio-preview","neural-studio","mixed-neural-studio"),required=True)
    prog=subs.add_parser("project-production-progress")
    prog.add_argument("--project-id",required=True)
    qa=subs.add_parser("project-media-review-visual")
    qa.add_argument("--project-id",required=True)
    qa.add_argument("--kind",choices=("audio","pilot","final"),required=True)
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
    tts=subs.add_parser("project-tts-kokoro",help="Explicit local Kokoro generation for supported language presets")
    tts.add_argument("--project-id",required=True)
    tts.add_argument("--model",type=Path)
    tts.add_argument("--voices",type=Path)
    tts.add_argument("--use-config",action="store_true")
    tts.add_argument("--run-local",action="store_true")
    tts.add_argument("--acknowledgment",required=True)
    tts.add_argument("--max-new",type=int,default=1)
    for name in ("project-master-compose","project-master-audit"):
        m=subs.add_parser(name)
        m.add_argument("--project-id",required=True)
    for name in ("project-audio-review-template","project-audio-review-record","project-audio-review-status",
                 "project-preview-render","project-preview-audit"):
        r=subs.add_parser(name)
        r.add_argument("--project-id",required=True)
        if name=="project-audio-review-record":
            r.add_argument("--acknowledgment",required=True)
            r.add_argument("--file",type=Path)
    neural4=subs.add_parser("project-neural-run",help="Explicit local SadTalker CPU pilot or reviewed batch")
    neural4.add_argument("--project-id",required=True)
    neural4.add_argument("--model",type=Path)
    neural4.add_argument("--python",type=Path)
    neural4.add_argument("--use-config",action="store_true")
    neural4.add_argument("--mode",choices=("pilot","batch"),default="pilot")
    neural4.add_argument("--max-new",type=int,default=1)
    neural4.add_argument("--timeout",type=int,default=1800)
    neural4.add_argument("--cpu-threads",type=int)
    neural4.add_argument("--run-local",action="store_true")
    neural4.add_argument("--acknowledgment",required=True)
    for name in ("project-neural-status","project-neural-pilot-template","project-neural-pilot-record"):
        n=subs.add_parser(name)
        n.add_argument("--project-id",required=True)
        if name=="project-neural-pilot-record":
            n.add_argument("--acknowledgment",required=True)
            n.add_argument("--file",type=Path)
    for name in ("project-neural-compose","project-neural-audit"):
        e=subs.add_parser(name)
        e.add_argument("--project-id",required=True)
    for name in ("project-final-review-template","project-final-review-record","project-final-review-status",
                 "project-neural-recovery-status","project-neural-archive","project-readiness"):
        q=subs.add_parser(name)
        q.add_argument("--project-id",required=True)
        if name in ("project-final-review-record","project-neural-archive"):q.add_argument("--acknowledgment",required=True)
        if name=="project-neural-archive":q.add_argument("--chunk-id",required=True)
        if name=="project-final-review-record":q.add_argument("--file",type=Path)
    config=subs.add_parser("model-configure")
    config.add_argument("--engine",choices=("kokoro","sadtalker","espeak"),required=True)
    for key in ("model","voices","python","executable"):config.add_argument("--"+key,type=Path)
    config.add_argument("--replace",action="store_true")
    subs.add_parser("model-config-status")
    persona4=subs.add_parser("project-persona-enable")
    persona4.add_argument("--project-id",required=True)
    continuity4=subs.add_parser("project-continuity-enable")
    continuity4.add_argument("--project-id",required=True)
    continuity4.add_argument("--prior-project-id",required=True)
    continuity4.add_argument("--turn-id",action="append",required=True)
    continuity4.add_argument("--acknowledgment",required=True)
    contstatus=subs.add_parser("project-continuity-status")
    contstatus.add_argument("--project-id",required=True)
    for name in ("espeak-inventory","project-tts-espeak"):
        e=subs.add_parser(name)
        e.add_argument("--executable",type=Path)
        e.add_argument("--use-config",action="store_true")
        e.add_argument("--acknowledgment",required=True)
        if name=="project-tts-espeak":
            e.add_argument("--project-id",required=True)
            e.add_argument("--run-local",action="store_true")
            e.add_argument("--max-new",type=int,default=1)
    edge4=subs.add_parser("project-tts-edge",help="Explicit online Edge speech for reviewed V4 dialogue")
    edge4.add_argument("--project-id",required=True)
    edge4.add_argument("--allow-network-tts",action="store_true")
    edge4.add_argument("--acknowledgment",required=True)
    edge4.add_argument("--max-new",type=int,default=1)
    edgeplan=subs.add_parser("project-edge-plan")
    edgeplan.add_argument("--project-id",required=True)
    edgeplan.add_argument("--max-new",type=int,default=1)
    edgeinv=subs.add_parser("edge-voice-inventory")
    edgeinv.add_argument("--language")
    edgeinv.add_argument("--allow-network",action="store_true")
    edgeinv.add_argument("--acknowledgment",required=True)
    mix=subs.add_parser("project-mix-compose")
    mix.add_argument("--project-id",required=True)
    for role in ("intro","bed","outro"):mix.add_argument("--"+role,type=Path)
    mix.add_argument("--speech-peak",type=int,default=22000)
    mix.add_argument("--bed-peak",type=int,default=3000)
    mix.add_argument("--duck-percent",type=int,default=0)
    mix.add_argument("--target-lufs",type=int)
    mix.add_argument("--compress-ratio",type=int,default=1)
    mix.add_argument("--compress-threshold",type=int,default=12000)
    mix.add_argument("--remove-dc",action="store_true")
    mix.add_argument("--gate-threshold",type=int,default=0)
    mix.add_argument("--spectral-noise",choices=("off","light","medium","strong"),default="off",help="Conservative per-turn spectral noise subtraction")
    mix.add_argument("--adaptive-noise",choices=("off","light","medium","strong"),default="off",help="Conservative per-turn adaptive quiet-region attenuation")
    mix.add_argument("--highpass-hz",type=int,choices=(0,60,80,100,120),default=0)
    mix.add_argument("--hum-hz",type=int,choices=(0,50,60),default=0)
    mix.add_argument("--lowpass-hz",type=int,choices=(0,4500,6000),default=0)
    mix.add_argument("--auto-peak-correction",action="store_true",help="Bounded measured attenuation retries; requires --true-peak-guard; optional LUFS target")
    mix.add_argument("--true-peak-guard",action="store_true",help="Conservative whole-mix peak guard with mandatory -1.5 dBTP measurement")
    mix.add_argument("--limiter-ceiling",type=int,default=0,help="Sample peak ceiling in PCM units; 0 disables")
    diagnostic=subs.add_parser("project-audio-diagnostics")
    diagnostic.add_argument("--project-id",required=True)
    diagnostic.add_argument("--kind",choices=("master","mix"),default="master")
    diagnostic.add_argument("--per-turn",action="store_true")
    subs.add_parser("model-setup-plan")
    compare=subs.add_parser("project-video-audio-check")
    compare.add_argument("--project-id",required=True)
    compare.add_argument("--kind",choices=("preview","neural","mixed","studio-preview","neural-studio","mixed-neural-studio"),required=True)
    for name in ("project-voice-preflight","project-device-acceptance"):
        pre=subs.add_parser(name)
        pre.add_argument("--project-id",required=True)
    mix.add_argument("--acknowledgment",required=True)
    mixaudit=subs.add_parser("project-mix-audit")
    mixaudit.add_argument("--project-id",required=True)
    for name in ("project-incomplete-status","project-incomplete-archive"):
        recover4=subs.add_parser(name)
        recover4.add_argument("--project-id",required=True)
        recover4.add_argument("--kind",choices=("audio-turn","master","static-preview","neural-clip","neural-export","post-audio","mixed-export","studio-preview","neural-studio","mixed-neural-studio"),required=True)
        recover4.add_argument("--unit")
        if name=="project-incomplete-archive":recover4.add_argument("--acknowledgment",required=True)
    for name in ("project-mix-review-template","project-mix-review-record","project-mix-review-status",
                 "project-mixed-video-compose","project-mixed-video-audit","project-mixed-review-template",
                 "project-mixed-review-record","project-mixed-review-status"):
        mixed=subs.add_parser(name)
        mixed.add_argument("--project-id",required=True)
        if name in ("project-mix-review-record","project-mixed-review-record"):
            mixed.add_argument("--acknowledgment",required=True)
    discover=subs.add_parser("project-research-discover")
    discover.add_argument("--project-id",required=True)
    discover.add_argument("--query")
    discover.add_argument("--limit",type=int,default=5)
    discover.add_argument("--edition",default="en")
    coverage=subs.add_parser("project-research-coverage")
    coverage.add_argument("--project-id",required=True)
    discover.add_argument("--allow-web-search",action="store_true")
    subs.add_parser("kokoro-language-catalog")
    subs.add_parser("japanese-resource-status")
    for name in ("project-fact-review-template","project-fact-review-record","project-fact-review-status"):
        fact=subs.add_parser(name)
        fact.add_argument("--project-id",required=True)
        if name=="project-fact-review-record":fact.add_argument("--acknowledgment",required=True)
    portrait=subs.add_parser("character-portrait-brief")
    portrait.add_argument("--character-id",required=True)
    pl=subs.add_parser("character-portrait-candidates")
    pl.add_argument("--limit",type=int,default=50)
    for name in ("character-portrait-candidate-audit","character-portrait-candidate-attach"):
        pa=subs.add_parser(name)
        pa.add_argument("--candidate-id",required=True)
        if name=="character-portrait-candidate-attach":pa.add_argument("--acknowledgment",required=True)
    for name in ("character-portrait-preflight","character-portrait-generate"):
        pg=subs.add_parser(name)
        pg.add_argument("--character-id",required=True)
        pg.add_argument("--model",type=Path,required=True)
        if name=="character-portrait-generate":
            pg.add_argument("--seed",type=int,default=42)
            pg.add_argument("--steps",type=int,default=20)
            pg.add_argument("--acknowledgment",required=True)
    studio=subs.add_parser("project-studio-configure")
    studio.add_argument("--project-id",required=True)
    studio.add_argument("--layout",choices=("focus","grid","spotlight"),required=True)
    studio.add_argument("--camera",choices=("fixed","push-in","pull-out","smooth-push","pan-left","pan-right","continuous-drift","continuous-breathe"),default="fixed")
    studio.add_argument("--listener-motion",choices=("static","drift","breathe"),default="static",help="Simulated listener framing (grid/spotlight only)")
    studio.add_argument("--transition",choices=("cut","quick","gentle","match-quick","match-gentle"),default="cut",help="Pause-only speaker handoff: portraits or rendered endpoints")
    studio.add_argument("--background",type=Path)
    studio.add_argument("--acknowledgment")
    for name in ("project-studio-status","project-studio-render","project-studio-audit"):
        st=subs.add_parser(name)
        st.add_argument("--project-id",required=True)
    attach=subs.add_parser("character-portrait-attach")
    attach.add_argument("--character-id",required=True)
    attach.add_argument("--portrait",type=Path,required=True)
    attach.add_argument("--acknowledgment",required=True)
    cache_inventory=subs.add_parser("project-studio-cache-inventory")
    cache_inventory.add_argument("--project-id",required=True)
    cache_delete=subs.add_parser("project-studio-cache-delete")
    cache_delete.add_argument("--project-id",required=True)
    cache_delete.add_argument("--namespace",required=True)
    cache_delete.add_argument("--snapshot-sha256",required=True)
    cache_delete.add_argument("--acknowledgment",required=True)
    for name in ("project-neural-studio-compose","project-neural-studio-resume","project-neural-studio-audit","project-neural-studio-review-template",
                 "project-neural-studio-review-record","project-neural-studio-review-status"):
        ns=subs.add_parser(name)
        ns.add_argument("--project-id",required=True)
        if name=="project-neural-studio-review-record":ns.add_argument("--acknowledgment",required=True)
    for name in ("project-mixed-studio-compose","project-mixed-studio-audit","project-mixed-studio-review-template","project-mixed-studio-review-record","project-mixed-studio-review-status"):
        ms=subs.add_parser(name)
        ms.add_argument("--project-id",required=True)
        if name=="project-mixed-studio-review-record":ms.add_argument("--acknowledgment",required=True)
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
        keys=credentials.resolve(private,pid=a.project_id,providers=("openrouter","gemini") if a.confirm_gemini_free_project else ("openrouter",)) if a.allow_cloud_text and not a.offline_only else None
        return projects.generate_outline(private,a.project_id,credentials=keys,
            allow_cloud_text=a.allow_cloud_text,confirm_gemini_free_project=a.confirm_gemini_free_project,
            offline_only=a.offline_only,local_model=a.ollama_model)
    if action in ("project-research-capture","project-research-status"):
        from . import research
        private=a.workspace.expanduser().absolute()
        if action=="project-research-status":return research.inspect(private,a.project_id)
        return research.capture(private,a.project_id,a.url,allow_web_fetch=a.allow_web_fetch)
    if action=="project-script-import-verbatim":
        from . import manual_script
        return manual_script.import_saved(a.workspace.expanduser().absolute(),a.project_id,acknowledgment=a.acknowledgment)
    if action in ("project-script-generate","project-script-status","project-script-finalize","project-script-show"):
        from . import script_generation,credentials
        private=a.workspace.expanduser().absolute()
        if action=="project-script-status":return script_generation.inspect(private,a.project_id)
        if action=="project-script-finalize":return script_generation.finalize(private,a.project_id)
        if action=="project-script-show":return script_generation.show(private,a.project_id)
        keys=credentials.resolve(private,pid=a.project_id,providers=("openrouter","gemini") if a.confirm_gemini_free_project else ("openrouter",)) if a.allow_cloud_text and not a.offline_only else None
        return script_generation.generate(private,a.project_id,max_new=a.max_new,credentials=keys,
            allow_cloud_text=a.allow_cloud_text,confirm_gemini_free_project=a.confirm_gemini_free_project,
            offline_only=a.offline_only,local_model=a.ollama_model)
    if action in ("project-script-edit-template","project-script-revise","project-script-review-template",
                  "project-script-review-record","project-script-review-status","project-script-current"):
        from . import script_review
        private=a.workspace.expanduser().absolute()
        if action=="project-script-edit-template":return script_review.template(private,a.project_id)
        if action=="project-script-revise":return script_review.revise(private,a.project_id,input_file=a.file)
        if action=="project-script-review-template":return script_review.template(private,a.project_id,review=True)
        if action=="project-script-review-record":return script_review.record(private,a.project_id,acknowledgment=a.acknowledgment,input_file=a.file)
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
    if action=="project-edge-plan":
        from . import v4_edge
        return v4_edge.plan(a.workspace.expanduser().absolute(),a.project_id,max_new=a.max_new)
    if action=="edge-voice-inventory":
        from . import edge_inventory
        return edge_inventory.discover(requested=a.language,allow_network=a.allow_network,acknowledgment=a.acknowledgment)
    if action=="project-tts-edge":
        from . import v4_edge
        return v4_edge.generate(a.workspace.expanduser().absolute(),a.project_id,
            allow_network_tts=a.allow_network_tts,acknowledgment=a.acknowledgment,max_new=a.max_new)
    if action=="project-tts-kokoro":
        from . import v4_tts,model_config
        private=a.workspace.expanduser().absolute()
        paths=model_config.resolve(private,"kokoro",{"model":a.model,"voices":a.voices},use_config=a.use_config)
        return v4_tts.generate(private,a.project_id,**paths,
            run_local=a.run_local,acknowledgment=a.acknowledgment,max_new=a.max_new)
    if action in ("project-master-compose","project-master-audit"):
        from . import v4_master
        fn=v4_master.compose if action=="project-master-compose" else v4_master.inspect
        return fn(a.workspace.expanduser().absolute(),a.project_id)
    if action in ("project-audio-review-template","project-audio-review-record","project-audio-review-status",
                  "project-preview-render","project-preview-audit"):
        from . import v4_audio_review,v4_preview
        private=a.workspace.expanduser().absolute()
        if action=="project-audio-review-template":return v4_audio_review.template(private,a.project_id)
        if action=="project-audio-review-record":return v4_audio_review.record(private,a.project_id,acknowledgment=a.acknowledgment,input_file=a.file)
        if action=="project-audio-review-status":return v4_audio_review.inspect(private,a.project_id)
        if action=="project-preview-render":return v4_preview.render(private,a.project_id)
        return v4_preview.inspect(private,a.project_id)
    if action in ("project-neural-run","project-neural-status","project-neural-pilot-template","project-neural-pilot-record"):
        from . import v4_neural
        private=a.workspace.expanduser().absolute()
        if action=="project-neural-status":return v4_neural.inspect(private,a.project_id)
        if action=="project-neural-pilot-template":return v4_neural.template(private,a.project_id)
        if action=="project-neural-pilot-record":return v4_neural.record(private,a.project_id,acknowledgment=a.acknowledgment,input_file=a.file)
        from . import model_config
        paths=model_config.resolve(private,"sadtalker",{"model":a.model,"python":a.python},use_config=a.use_config)
        return v4_neural.generate(private,a.project_id,**paths,mode=a.mode,max_new=a.max_new,
            timeout=a.timeout,cpu_threads=a.cpu_threads,run_local=a.run_local,acknowledgment=a.acknowledgment)
    if action in ("project-neural-compose","project-neural-audit"):
        from . import v4_export
        fn=v4_export.compose if action=="project-neural-compose" else v4_export.inspect
        return fn(a.workspace.expanduser().absolute(),a.project_id)
    if action in ("project-final-review-template","project-final-review-record","project-final-review-status",
                  "project-neural-recovery-status","project-neural-archive","project-readiness"):
        from . import v4_final_review,v4_recovery,v4_readiness
        private=a.workspace.expanduser().absolute()
        if action=="project-final-review-template":return v4_final_review.template(private,a.project_id)
        if action=="project-final-review-record":return v4_final_review.record(private,a.project_id,acknowledgment=a.acknowledgment,input_file=a.file)
        if action=="project-final-review-status":return v4_final_review.inspect(private,a.project_id)
        if action=="project-neural-recovery-status":return v4_recovery.inspect(private,a.project_id)
        if action=="project-neural-archive":return v4_recovery.archive(private,a.project_id,a.chunk_id,acknowledgment=a.acknowledgment)
        return v4_readiness.inspect(private,a.project_id)
    if action in ("model-configure","model-config-status","project-persona-enable","espeak-inventory","project-tts-espeak"):
        from . import model_config,persona,v4_espeak
        private=a.workspace.expanduser().absolute()
        if action=="model-config-status":return model_config.status(private)
        if action=="model-configure":
            paths={k:getattr(a,k) for k in ("model","voices","python","executable") if getattr(a,k) is not None}
            return model_config.save(private,a.engine,paths,replace=a.replace)
        if action=="project-persona-enable":return persona.enable(private,a.project_id)
        paths=model_config.resolve(private,"espeak",{"executable":a.executable},use_config=a.use_config)
        if action=="espeak-inventory":return v4_espeak.inventory(**paths,acknowledgment=a.acknowledgment)
        return v4_espeak.generate(private,a.project_id,**paths,run_local=a.run_local,acknowledgment=a.acknowledgment,max_new=a.max_new)
    if action=="project-script-visual":
        from . import visual_script
        return visual_script.create(a.workspace.expanduser().absolute(),a.project_id,mode=a.mode)
    if action in ("dependency-plan","dependency-install"):
        from . import dependency_setup
        if action=="dependency-plan":return dependency_setup.plan(a.group)
        return dependency_setup.install(a.group,acknowledgment=a.acknowledgment)
    if action=="project-auto-step":
        from . import v4_orchestrator
        return v4_orchestrator.run(a.workspace.expanduser().absolute(),a.project_id,execute=a.execute,
            acknowledgment=a.acknowledgment,max_steps=a.max_steps,allow_local_ai=a.allow_local_ai,
            kokoro_ack=a.kokoro_ack,espeak_ack=a.espeak_ack,neural_ack=a.neural_ack)
    if action in ("project-production-overview","project-media-check"):
        from . import production_overview
        private=a.workspace.expanduser().absolute()
        if action=="project-production-overview":return production_overview.inspect(private,a.project_id)
        return production_overview.media_check(private,a.project_id,a.kind)
    if action=="project-production-progress":
        from . import v4_progress
        return v4_progress.inspect(a.workspace.expanduser().absolute(),a.project_id)
    if action=="project-media-review-visual":
        from . import visual_media_review
        return visual_media_review.create(a.workspace.expanduser().absolute(),a.project_id,kind=a.kind)
    if action in ("project-mix-compose","project-mix-audit"):
        from . import v4_post_audio
        private=a.workspace.expanduser().absolute()
        if action=="project-mix-audit":return v4_post_audio.inspect(private,a.project_id)
        return v4_post_audio.compose(private,a.project_id,intro=a.intro,bed=a.bed,outro=a.outro,
            speech_peak=a.speech_peak,bed_peak=a.bed_peak,duck_percent=a.duck_percent,target_lufs=a.target_lufs,compress_ratio=a.compress_ratio,compress_threshold=a.compress_threshold,remove_dc=a.remove_dc,gate_threshold=a.gate_threshold,limiter_ceiling=a.limiter_ceiling,highpass_hz=a.highpass_hz,hum_hz=a.hum_hz,lowpass_hz=a.lowpass_hz,true_peak_guard=a.true_peak_guard,auto_peak_correction=a.auto_peak_correction,adaptive_noise=a.adaptive_noise,spectral_noise=a.spectral_noise,acknowledgment=a.acknowledgment)
    if action in ("project-incomplete-status","project-incomplete-archive"):
        from . import v4_partial_recovery
        private=a.workspace.expanduser().absolute()
        if action=="project-incomplete-status":return v4_partial_recovery.inspect(private,a.project_id,a.kind,a.unit)
        return v4_partial_recovery.archive(private,a.project_id,a.kind,a.unit,acknowledgment=a.acknowledgment)
    if action in ("project-mix-review-template","project-mix-review-record","project-mix-review-status",
                  "project-mixed-video-compose","project-mixed-video-audit","project-mixed-review-template",
                  "project-mixed-review-record","project-mixed-review-status"):
        from . import v4_mixed_video as mixed
        private=a.workspace.expanduser().absolute()
        if action=="project-mixed-video-compose":return mixed.compose(private,a.project_id)
        if action=="project-mixed-video-audit":return mixed.inspect(private,a.project_id)
        return mixed.qa(private,a.project_id,"mix" if action.startswith("project-mix-review-") else "video",
                        action.rsplit("-",1)[1],acknowledgment=getattr(a,"acknowledgment",None))
    if action=="kokoro-language-catalog":
        from . import kokoro_languages
        return kokoro_languages.catalog()
    if action=="project-research-coverage":
        from . import research_coverage
        return research_coverage.inspect(a.workspace.expanduser().absolute(),a.project_id)
    if action=="project-research-discover":
        from . import research_discovery
        return research_discovery.discover(a.workspace.expanduser().absolute(),a.project_id,query=a.query,limit=a.limit,edition=a.edition,allow_web_search=a.allow_web_search)
    if action in ("project-fact-review-template","project-fact-review-record","project-fact-review-status"):
        from . import fact_review
        private=a.workspace.expanduser().absolute()
        if action=="project-fact-review-template":return fact_review.create(private,a.project_id)
        if action=="project-fact-review-record":return fact_review.record(private,a.project_id,acknowledgment=a.acknowledgment)
        return fact_review.inspect(private,a.project_id)
    if action in ("character-portrait-candidates","character-portrait-candidate-audit","character-portrait-candidate-attach"):
        from . import portrait_local
        private=a.workspace.expanduser().absolute()
        if action=="character-portrait-candidates":return portrait_local.list_candidates(private,limit=a.limit)
        if action=="character-portrait-candidate-audit":return portrait_local.audit_candidate(private,a.candidate_id)
        return portrait_local.attach_candidate(private,a.candidate_id,acknowledgment=a.acknowledgment)
    if action in ("character-portrait-preflight","character-portrait-generate"):
        from . import portrait_local
        private=a.workspace.expanduser().absolute()
        if action=="character-portrait-preflight":return portrait_local.inspect(private,a.character_id,a.model)
        return portrait_local.generate(private,a.character_id,model=a.model,seed=a.seed,steps=a.steps,acknowledgment=a.acknowledgment)
    if action=="japanese-resource-status":
        from . import japanese_resources
        return japanese_resources.inspect()
    if action=="character-portrait-brief":
        from . import portrait_brief
        return portrait_brief.create(a.workspace.expanduser().absolute(),a.character_id)
    if action in ("project-studio-configure","project-studio-status","project-studio-render","project-studio-audit"):
        from . import studio_preview
        private=a.workspace.expanduser().absolute()
        if action=="project-studio-configure":return studio_preview.configure(private,a.project_id,layout=a.layout,background=a.background,camera=a.camera,listener_motion=a.listener_motion,transition=a.transition,acknowledgment=a.acknowledgment)
        if action=="project-studio-status":return studio_preview.inspect_settings(private,a.project_id)
        if action=="project-studio-render":return studio_preview.render(private,a.project_id)
        return studio_preview.inspect(private,a.project_id)
    if action=="character-portrait-attach":
        from . import portrait_brief
        return portrait_brief.attach(a.workspace.expanduser().absolute(),a.character_id,portrait=a.portrait,acknowledgment=a.acknowledgment)
    if action in ("project-studio-cache-inventory","project-studio-cache-delete"):
        from . import studio_cache_admin
        private=a.workspace.expanduser().absolute()
        if action=="project-studio-cache-inventory":return studio_cache_admin.inspect(private,a.project_id)
        return studio_cache_admin.remove(private,a.project_id,a.namespace,a.snapshot_sha256,acknowledgment=a.acknowledgment)
    if action in ("project-neural-studio-compose","project-neural-studio-resume","project-neural-studio-audit","project-neural-studio-review-template",
                  "project-neural-studio-review-record","project-neural-studio-review-status"):
        from . import studio_neural
        private=a.workspace.expanduser().absolute()
        if action=="project-neural-studio-compose":return studio_neural.compose(private,a.project_id)
        if action=="project-neural-studio-resume":return studio_neural.compose(private,a.project_id,resume=True)
        if action=="project-neural-studio-audit":return studio_neural.inspect(private,a.project_id)
        return studio_neural.qa(private,a.project_id,action.rsplit("-",1)[1],acknowledgment=getattr(a,"acknowledgment",None))
    if action in ("project-mixed-studio-compose","project-mixed-studio-audit","project-mixed-studio-review-template","project-mixed-studio-review-record","project-mixed-studio-review-status"):
        from . import v4_mixed_video as mixed
        private=a.workspace.expanduser().absolute()
        if action=="project-mixed-studio-compose":return mixed.compose(private,a.project_id,studio=True)
        if action=="project-mixed-studio-audit":return mixed.inspect(private,a.project_id,studio=True)
        return mixed.qa(private,a.project_id,"studio",action.rsplit("-",1)[1],acknowledgment=getattr(a,"acknowledgment",None))
    if action=="ai-provider-status":
        from .ai_providers import inventory
        return inventory()
    if action=="plan-episode":
        from . import ai_providers,episode_plan
        credentials=ai_providers.Credentials.environment()
        if a.prompt_keys:
            if not a.allow_cloud_text or a.offline_only:
                raise ValueError("Session cloud keys require explicit cloud text consent")
            from .credentials import prompt_key
            router=prompt_key("openrouter")
            gemini=prompt_key("gemini") if a.confirm_gemini_free_project else ""
            credentials=ai_providers.Credentials(router or credentials.openrouter,gemini or credentials.gemini)
        return episode_plan.plan(episode_plan.load_request(a.request),credentials=credentials,
            allow_cloud_text=a.allow_cloud_text,confirm_gemini_free_project=a.confirm_gemini_free_project,
            offline_only=a.offline_only,local_model=a.ollama_model)
    if action in ("project-continuity-enable","project-continuity-status"):
        from . import continuity
        private=a.workspace.expanduser().absolute()
        if action=="project-continuity-status":return continuity.inspect(private,a.project_id)
        return continuity.enable(private,a.project_id,a.prior_project_id,a.turn_id,acknowledgment=a.acknowledgment)
    if action in ("project-voice-preflight","project-device-acceptance"):
        from . import voice_preflight,device_acceptance
        module=voice_preflight if action=="project-voice-preflight" else device_acceptance
        return module.inspect(a.workspace.expanduser().absolute(),a.project_id)
    if action=="project-video-audio-check":
        from . import video_audio_check
        return video_audio_check.inspect(a.workspace.expanduser().absolute(),a.project_id,a.kind)
    if action=="model-setup-plan":
        from . import model_setup_plan
        return model_setup_plan.inspect(a.workspace.expanduser().absolute())
    if action=="project-audio-diagnostics":
        from . import audio_diagnostics
        return audio_diagnostics.inspect(a.workspace.expanduser().absolute(),a.project_id,kind=a.kind,per_turn=a.per_turn)
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