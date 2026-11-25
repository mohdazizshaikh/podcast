"""Explicit network voice discovery, independent of project/dialogue data."""
import asyncio
from . import edge_voice

ACK="I_AUTHORIZE_ONLINE_EDGE_VOICE_INVENTORY_REQUEST"
MAX_ROWS=5000
MAX_RESULTS=1000


def normalize(rows,requested=None):
    code=edge_voice.language(requested) if requested is not None else None
    if not isinstance(rows,list) or not 1<=len(rows)<=MAX_ROWS:
        raise ValueError("Invalid bounded Edge voice inventory")
    voices={}
    for row in rows:
        if not isinstance(row,dict):raise ValueError("Invalid Edge inventory row")
        preset=row.get("ShortName")
        try:tag=edge_voice.locale(preset)
        except ValueError:continue  # unsupported preset shapes are not selectable
        raw_locale=row.get("Locale")
        if not isinstance(raw_locale,str) or raw_locale.casefold()!=tag:
            raise ValueError("Edge inventory locale differs from preset")
        if code is not None and tag!=code and not tag.startswith(code+"-"):continue
        gender=row.get("Gender")
        entry={"voice_preset":preset,"locale":tag,"gender":gender if gender in ("Male","Female") else None}
        if preset in voices and voices[preset]!=entry:raise ValueError("Conflicting Edge voice inventory")
        voices[preset]=entry
    entries=sorted(voices.values(),key=lambda r:r["voice_preset"])
    return {"language_filter":code,"voices":entries[:MAX_RESULTS],"matching_voice_count":len(entries),
            "truncated":len(entries)>MAX_RESULTS,"voice_quality_verified":False}


async def _fetch():
    import edge_tts
    return await edge_tts.list_voices()


def discover(*,requested=None,allow_network=False,acknowledgment=None,fetcher=None):
    if allow_network is not True or acknowledgment!=ACK:
        raise ValueError("Explicit online voice inventory consent required")
    if requested is not None:edge_voice.language(requested)
    try:rows=(fetcher or (lambda:asyncio.run(asyncio.wait_for(_fetch(),timeout=30))))()
    except Exception:raise ValueError("Edge voice inventory unavailable; check package and network locally") from None
    return {**normalize(rows,requested),"network_request_performed":fetcher is None,
            "dialogue_sent":False,"automatic_fallback":False,"consent_persisted":False}
