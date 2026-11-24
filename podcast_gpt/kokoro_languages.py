"""Explicit Kokoro v1.0 candidate presets using Misaki EspeakG2P.

Not an installed voice inventory or proof of natural pronunciation.
English/CJK frontends deliberately not enabled by this adapter.
"""
from . import kokoro

PRESETS={"hi":kokoro.VOICE_CHOICES,"es":frozenset(("ef_dora","em_alex","em_santa")),
         "fr-fr":frozenset(("ff_siwis",)),"it":frozenset(("if_sara","im_nicola")),
         "pt-br":frozenset(("pf_dora","pm_alex","pm_santa"))}
ALIASES={"hi":"hi","hindi":"hi","hi-in":"hi","हिन्दी":"hi","हिंदी":"hi",
         "spanish":"es","es":"es","es-es":"es",
         "french":"fr-fr","fr":"fr-fr","fr-fr":"fr-fr",
         "italian":"it","it":"it","it-it":"it",
         "brazilian portuguese":"pt-br","portuguese (brazil)":"pt-br","pt-br":"pt-br"}


def language(value):
    code=ALIASES.get(value.casefold().strip())
    if code is None:raise ValueError("Local Kokoro requires Hindi, Spanish, French, Italian or explicit Brazilian Portuguese")
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
        from misaki.espeak import EspeakG2P
    except ImportError as exc:raise ValueError("Install trusted local Kokoro ONNX, Misaki and eSpeak dependencies") from exc
    return Kokoro(str(model),str(voices)),EspeakG2P(language=code)
