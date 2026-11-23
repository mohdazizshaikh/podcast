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
                 "render-static","audit-static","progress","budget","review-pilot","inspect-pilot",
                 "compose-neural","audit-neural","review-full","web"):
        cmd=subs.add_parser(name)
        if name=="web":cmd.add_argument("--port",type=int,default=7860)
    preflight=subs.add_parser("check-sadtalker",help="READ ONLY local SadTalker CPU installation check; NO inference")
    preflight.add_argument("--sadtalker-root",type=Path,required=True)
    preflight.add_argument("--sadtalker-python",type=Path,required=True)
    cpu=subs.add_parser("run-cpu",help="Genuine local SadTalker CPU; requires explicit rights")
    cpu.add_argument("--mode",choices=("pilot","batch","session"),required=True)
    cpu.add_argument("--max-new",type=int,default=3)
    cpu.add_argument("--wall-seconds",type=int,default=7200)
    cpu.add_argument("--per-chunk-timeout",type=int,default=1800)
    cpu.add_argument("--sadtalker-root",type=Path,required=True)
    cpu.add_argument("--sadtalker-python",type=Path,required=True)
    cpu.add_argument("--rights-confirmed",action="store_true")
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
    return {"version":__version__,"workspace":str(root.resolve()),
            "workspace_disk_free_gib":free_gib,"source_minimum_free_gib_for_render":3,
            "neural_minimum_free_gib_for_render":6,
            "ffmpeg":bool(media["ffmpeg"]),"ffprobe":bool(media["ffprobe"]),
            "pillow":bool(importlib.util.find_spec("PIL")),
            "edge_tts_optional":bool(importlib.util.find_spec("edge_tts")),
            "sadtalker_cpu_model_included":False,"portrait_rights_automatically_verified":False,
            "original_10_min_neural_video_verified":False}


async def _tts_one(root:Path, turn:int, allow:bool, voice:str|None)->dict:
    from .source import load_project,SPEAKERS
    if not allow:raise ValueError("Online TTS requires explicit --allow-network-tts")
    if not 1<=turn<=45:raise ValueError("Original Hindi turn must be 1..45")
    try:import edge_tts
    except ImportError as err:raise ValueError("Optional edge-tts not installed; install pip install -e '.[tts]'") from err
    project=load_project(root);line=project["turns"][turn-1]
    if voice is None:voice="hi-IN-SwaraNeural" if line["speaker"]=="meera" else "hi-IN-MadhurNeural"
    wav=root/"voices"/(line["id"]+".wav")
    if wav.exists() or wav.is_symlink():raise ValueError("Original Hindi WAV exists; no overwrites")
    import tempfile,subprocess
    from .media import cmd
    root.joinpath("voices").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="hindi-tts-") as folder:
        mp3=Path(folder)/"output.mp3"
        await edge_tts.Communicate(line["text"],voice,rate="-10%" if line["speaker"]=="kabir" else "+0%").save(str(mp3))
        temp=Path(folder)/"original.wav"
        cmd(["ffmpeg","-y","-hide_banner","-v","error","-i",str(mp3),"-ar","16000","-ac","1",
             "-c:a","pcm_s16le",str(temp)],timeout=120)
        from .source import wav_info
        wav_info(temp)
        import shutil
        shutil.copyfile(temp,wav)
    return {"saved_original_hindi_wav":line["id"],"network_tts_used":True,
            "all_three_distinct_natural_voice_identities_guaranteed":False}


def execute(a)->dict:
    root=a.workspace.expanduser().resolve()
    action=a.operation
    if action=="doctor":return doctor(root)
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
    if action=="budget":
        from .budget import estimate_cpu_budget
        return estimate_cpu_budget(root)
    if action=="check-sadtalker":
        from .model_preflight import inspect_sadtalker_installation
        return inspect_sadtalker_installation(a.sadtalker_root,a.sadtalker_python)
    if action=="run-cpu":return neural.run_cpu(root,mode=a.mode,
            rights_confirmed=a.rights_confirmed,max_new=a.max_new,
            wall_seconds=a.wall_seconds,per_chunk_timeout=a.per_chunk_timeout,
            sadtalker_root=a.sadtalker_root,sadtalker_python=a.sadtalker_python)
    if action=="review-pilot":return review.review_pilot(root)
    if action=="record-pilot":return review.record_pilot(root,
           {name:getattr(a,name) for name in source.SPEAKERS},a.acknowledgment)
    if action=="inspect-pilot":return review.inspect_pilot(root)
    if action=="compose-neural":return neural.compose_neural(root)
    if action=="audit-neural":return neural.audit_neural(root)
    if action=="review-full":return review.review_full(root)
    if action=="tts-kokoro":
        from .kokoro import generate
        return generate(root,model=a.model,voices=a.voices,turn=a.turn,
                        next_missing=a.next,max_new=a.max_new,run_local=a.run_local)
    if action=="tts-one":
        import asyncio
        return asyncio.run(_tts_one(root,a.turn,a.allow_network_tts,a.voice))
    if action=="web":
        from .web import serve
        serve(root,a.port)
        return {"dashboard_stopped":True}
    raise ValueError("Unknown action")


def main(argv=None)->int:
    try:
        args=parse(argv)
        result=execute(args)
        print(json.dumps(result,ensure_ascii=False,indent=2,default=str))
        return 0
    except (ValueError,RuntimeError,OSError,TimeoutError,KeyError,TypeError,ImportError,
            json.JSONDecodeError) as err:
        # Avoid leaking user-supplied Hindi dialogue, portraits or private secrets.
        print("BLOCKED: " + str(err),file=sys.stderr)
        return 1

if __name__=="__main__":
    raise SystemExit(main())