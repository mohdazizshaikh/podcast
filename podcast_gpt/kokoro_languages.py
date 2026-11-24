"""Explicit Kokoro v1.0 candidate presets using Misaki EspeakG2P.

Not an installed voice inventory or proof of natural pronunciation.
English uses non-transformer Misaki G2P; CJK is not enabled.
"""
from . import kokoro

PRESETS={"hi":kokoro.VOICE_CHOICES,"es":frozenset(("ef_dora","em_alex","em_santa")),
         "fr-fr":frozenset(("ff_siwis",)),"it":frozenset(("if_sara","im_nicola")),
         "pt-br":frozenset(("pf_dora","pm_alex","pm_santa")),
         "en-us":frozenset(("af_heart","af_bella","af_sarah","af_nicole","af_sky","am_adam","am_michael","am_fenrir","am_onyx","am_puck")),
         "en-gb":frozenset(("bf_alice","bf_emma","bf_isabella","bf_lily","bm_daniel","bm_fable","bm_george","bm_lewis"))}
ALIASES={"hi":"hi","hindi":"hi","hi-in":"hi","हिन्दी":"hi","हिंदी":"hi",
         "spanish":"es","es":"es","es-es":"es",
         "french":"fr-fr","fr":"fr-fr","fr-fr":"fr-fr",
         "italian":"it","it":"it","it-it":"it",
         "brazilian portuguese":"pt-br","portuguese (brazil)":"pt-br","pt-br":"pt-br",
         "english":"en-us","en":"en-us","en-us":"en-us","american english":"en-us",
         "british english":"en-gb","en-gb":"en-gb"}


def language(value):
    code=ALIASES.get(value.casefold().strip())
    if code is None:raise ValueError("Local Kokoro requires a supported explicit language or English variant")
    return code


def preset(voice,code):
    if voice["engine"]!="kokoro" or language(voice["language"])!=code or voice["preset"] not in PRESETS[code]:
        raise ValueError("Select an explicit Kokoro preset matching the script language")
    return voice["preset"]


def catalog():
    return {"languages":[{"code":code,"candidate_presets":sorted(voices)} for code,voices in PRESETS.items()],
            "installed_voice_inventory_verified":False,"actual_voice_quality_verified":False,"downloads":0}


def engine(model,voices,code):
    if code=="hi":return kokoro._engine(model,voices)
    try:
        from kokoro_onnx import Kokoro
        if code in ("en-us","en-gb"):
            from misaki import en,espeak
            british=code=="en-gb"
            g2p=en.G2P(trf=False,british=british,fallback=espeak.EspeakFallback(british=british))
        else:
            from misaki.espeak import EspeakG2P
            g2p=EspeakG2P(language=code)
    except ImportError as exc:raise ValueError("Install trusted local Kokoro ONNX, Misaki and matching eSpeak dependencies") from exc
    return Kokoro(str(model),str(voices)),g2p
