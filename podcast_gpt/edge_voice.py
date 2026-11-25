"""Static Edge locale/preset validation; no network or provider inventory."""
import re

ALIASES={
    "english":"en","hindi":"hi","हिंदी":"hi","हिन्दी":"hi","marathi":"mr",
    "tamil":"ta","telugu":"te","bengali":"bn","gujarati":"gu","urdu":"ur",
    "spanish":"es","french":"fr","german":"de","italian":"it","portuguese":"pt",
    "arabic":"ar","russian":"ru","japanese":"ja","chinese":"zh","mandarin":"zh",
    "korean":"ko","dutch":"nl","polish":"pl","turkish":"tr","indonesian":"id",
    "vietnamese":"vi","thai":"th","malayalam":"ml","kannada":"kn","punjabi":"pa",
    "nepali":"ne","swedish":"sv","danish":"da","finnish":"fi","greek":"el",
    "hebrew":"he","ukrainian":"uk","czech":"cs","romanian":"ro",
}
TAG=re.compile(r"[a-z]{2,3}(?:-[a-z0-9]{2,8}){0,3}",re.ASCII)
VOICE=re.compile(r"([a-z]{2,3}(?:-[A-Z][a-z]{3})?-[A-Z]{2})-([A-Za-z][A-Za-z0-9]{0,79}Neural)",re.ASCII)


def language(value):
    if not isinstance(value,str):raise ValueError("Invalid Edge language")
    value=value.strip().casefold()
    value=ALIASES.get(value,value)
    if not TAG.fullmatch(value):raise ValueError("Use a language name or BCP-47 language tag")
    return value


def locale(preset):
    match=VOICE.fullmatch(preset) if isinstance(preset,str) else None
    if not match:raise ValueError("Select an explicit Edge neural voice short name")
    return match.group(1).lower()


def compatible(voice,requested):
    if not isinstance(voice,dict) or voice.get("engine")!="edge":raise ValueError("Select Edge voice engine")
    preset=voice.get("preset")
    tag=locale(preset)
    for value in (voice.get("language"),requested):
        code=language(value)
        if tag!=code and not tag.startswith(code+"-"):
            raise ValueError("Edge voice locale does not match script/profile language")
    return preset


def validate_receipt(data):
    if not isinstance(data,dict) or set(data)!={"voice_preset","language","provider","network_consent"}:
        raise ValueError("Invalid Edge generation receipt")
    tag=locale(data["voice_preset"])
    code=language(data["language"])
    if data["language"]!=code or (tag!=code and not tag.startswith(code+"-")):
        raise ValueError("Edge receipt language differs")
    if data["provider"]!="edge_tts_online" or data["network_consent"] is not True:
        raise ValueError("Invalid Edge network provenance")
    return data
