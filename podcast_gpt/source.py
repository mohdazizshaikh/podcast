"""Original 45 Hindi turns, immutable voice/portrait SHA binding, exact PCM partition.

The PRIVATE workspace is outside the Git repository. Never create fake audio,
portrait samples, or mark a neural video complete from a JSON file alone.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import struct
import wave
from pathlib import Path
from typing import Any

from PIL import Image

SPEAKERS = ("aarav", "meera", "kabir")
RATE = 16000
SPEECH_LIMIT = 10.0
MIN_DURATION = 1.0
TOTAL_MIN, TOTAL_MAX = 540.0, 660.0
SOURCE_FILE = "source-manifest.json"
CHUNK_FILE = "chunks-manifest.json"
CHUNK_RE = re.compile(r"^\d{3}-\d{3}$")

DIALOGUE = (
    "नमस्कार दोस्तों, मैं आरव हूँ और हमारे हिंदी पॉडकास्ट में आपका स्वागत है। आज हम एआई की मदद से उपयोगी वीडियो बनाने की यात्रा पर चलेंगे।",
    "मैं मीरा हूँ। मेरे लिए पहला सवाल है कि दर्शक इस एपिसोड से क्या सीखकर जाएँगे। इसलिए हर तकनीकी हिस्से को रोजमर्रा के किसी उदाहरण से जोड़ेंगे, ताकि सामान्य विंडोज कंप्यूटर रखने वाला नया क्रिएटर भी हमारी बात आसानी से समझ सके।",
    "और मैं कबीर हूँ। मैं बताऊँगा कि मशीन कौन से काम कर सकती है और कहाँ इंसानी जाँच जरूरी है। हम अनुमान को तथ्य नहीं कहेंगे और किसी सॉफ्टवेयर की क्षमता बढ़ा चढ़ाकर नहीं बताएँगे।",
    "शुरुआत विषय चुनने से होती है। किसी एक वायरल खबर पर दस मिनट भर देने की कोशिश न करें। ऐसा सवाल उठाएँ जिसके कई पहलू हों, जैसे एआई वीडियो का उपयोग, दर्शकों का भरोसा, खर्च, गोपनीयता और काम को बार बार सुधारने का तरीका।",
    "मैं विषय चुनते वक्त अपने दर्शकों की तीन जरूरतें लिखती हूँ। उन्हें आसान शुरुआत चाहिए, वास्तविक उदाहरण चाहिए और गलतियों से बचने का तरीका चाहिए।",
    "रिसर्च में एक मॉडल का जवाब अकेला पर्याप्त नहीं है। मूल दस्तावेज, तारीख, प्रकाशक और दूसरे स्वतंत्र स्रोत भी देखिए। यदि कोई दावा बदलती तकनीक पर आधारित हो, तो रिकॉर्डिंग से ठीक पहले उसकी स्थिति फिर जाँच लेना समझदारी है।",
    "अब स्क्रिप्ट का ढाँचा बनाते हैं। शुरुआत में समस्या, बीच में अलग उदाहरण और अंत में स्पष्ट निष्कर्ष रखें।",
    "एक प्राकृतिक बातचीत में मैं बीच में दर्शकों की ओर से सवाल पूछूँगी। मान लीजिए छोटे व्यवसाय को प्रचार वीडियो बनाना है, लेकिन महंगे उपकरण नहीं हैं। तब हम उसे एक छोटा परीक्षण करने की सलाह देंगे, न कि तुरंत पूरी परियोजना बनाने की।",
    "हर संवाद की अलग पहचान संख्या रखना बहुत उपयोगी होता है। यदि तीसरे वक्ता की कोई आवाज गलत बनी, तो पूरी रिकॉर्डिंग दोबारा बनाने की जरूरत नहीं पड़ेगी।",
    "अब तीन आवाजों की बात करते हैं। अलग वॉइस प्रीसेट चुनना अच्छा कदम है, लेकिन प्रीसेट अलग होने से आवाजें प्राकृतिक या पूरी तरह अलग व्यक्तित्व वाली हों, इसकी गारंटी नहीं मिलती। इसलिए छोटा नमूना सुनना जरूरी है।",
    "हिंदी में उच्चारण जाँचते समय मैं नाम, अंग्रेजी तकनीकी शब्द और लंबे वाक्य सुनती हूँ। कभी आवाज बहुत तेज लगती है, कभी भाव बिल्कुल सपाट।",
    "कुछ आवाज इंजन कंप्यूटर पर ही चलते हैं, जबकि कुछ इंटरनेट सेवा को टेक्स्ट भेजते हैं। इंस्टॉलेशन, लाइसेंस, गोपनीयता और प्रोसेसिंग समय जाँचकर ही विकल्प चुनें। मुफ्त डाउनलोड का मतलब हर तरह के व्यावसायिक उपयोग की अनुमति नहीं होता।",
    "चेहरे के मामले में एक नियम सबसे ऊपर है। जिस व्यक्ति की तस्वीर या पहचान इस्तेमाल कर रहे हैं, उसकी स्पष्ट अनुमति और उचित अधिकार जरूरी हैं।",
    "मैं चाहूँगी कि तीनों पात्र एक ही स्टूडियो में बैठे हुए लगें। समान कैमरा ऊँचाई, संतुलित रोशनी और सरल पृष्ठभूमि से अनुभव बेहतर होता है। बहुत सारे ग्राफिक्स के बजाय साफ चेहरे और पढ़ने योग्य नाम पट्टियाँ अधिक उपयोगी हैं।",
    "एक स्थिर तस्वीर से सही होंठ, पलक और सिर की चाल बनाना कठिन काम है। इसलिए साफ सामने वाला चेहरा चुनना मदद करता है, लेकिन अच्छी तस्वीर भी सही एनीमेशन की गारंटी नहीं देती।",
    "रिकॉर्ड की गई आवाजों को एक तय तकनीकी प्रारूप में रखना चाहिए। हमारे उदाहरण में सोलह हजार हर्ट्ज, एक चैनल और सोलह बिट पीसीएम है। इससे असली ऑडियो की अवधि मापने और बिना दोबारा आवाज बनाए सटीक हिस्से निकालने में मदद मिलती है।",
    "ऑडियो सुनते समय केवल शब्दों की जाँच न करें। अचानक कटी सांस, तेज पृष्ठभूमि शोर और अलग अलग वक्ताओं के बीच आवाज की ऊँचाई भी देखें।",
    "हर मूल आवाज और तस्वीर का डिजिटल हैश रिकॉर्ड करना एक अच्छी सुरक्षा जाँच है। यदि मूल फ़ाइल के बाइट बदल जाएँ, तो उससे बनी पुरानी वीडियो उसी स्रोत का प्रमाण नहीं रहेगी। ऐसे बदलाव के बाद आगे की प्रक्रिया रोककर दोबारा सत्यापन करना चाहिए।",
    "अब छोटे होंठ परीक्षण की बात आती है। पूरे दस मिनट के चेहरे बनाने से पहले हर प्रस्तुतकर्ता का एक छोटा नमूना तैयार करें।",
    "मैं नमूने को ध्यान से देखकर पूछूँगी कि आवाज शुरू होने से पहले होंठ हिल तो नहीं रहे। कहीं आँखें जड़ हैं, गर्दन अजीब मुड़ रही है या मुस्कान गायब हो रही है। हर छोटी खराबी को स्पष्ट रूप से नोट करना चाहिए।",
    "एक वीडियो सही तरह से खुल जाए तो इसका मतलब सिर्फ इतना है कि फ़ाइल तकनीकी रूप से पढ़ी जा सकती है। इससे सही हिंदी होंठ तालमेल सिद्ध नहीं होता।",
    "कमजोर कंप्यूटर पर बिना अलग ग्राफिक्स कार्ड के मॉडल चल सकता है, लेकिन वास्तविक समय बहुत लग सकता है। इसलिए सीमित बैच, सुरक्षित सेव और छोटे प्रयोग काम आते हैं। कई घंटों का काम शुरू करने से पहले तीनों चेहरों की गुणवत्ता देखना बेहतर है।",
    "यदि एक क्लिप बनने में कई मिनट लगे, तो उसका समय नोट कीजिए। फिर बाकी काम का एक अनुमान बनाया जा सकता है।",
    "अच्छी तकनीकी प्रक्रिया हर सफल हिस्से के बाद सुरक्षित चेकपॉइंट रखती है। अगली बार वही क्लिप फिर चलाने से पहले उसकी फ़ाइल और स्रोत जाँच लिए जाएँ। यदि बीच में कंप्यूटर बंद हो जाए, तो पहले से सही परिणाम बेवजह दोबारा न बनें।",
    "उपशीर्षक हमारे पॉडकास्ट का महत्वपूर्ण हिस्सा हैं। हिंदी शब्द सही लिखे हों, सही समय पर दिखाई दें और मोबाइल की छोटी स्क्रीन पर पढ़े जा सकें।",
    "हिंदी फ़ॉन्ट के चुनाव में मात्राएँ और संयुक्त अक्षर खास चुनौती होते हैं। मैं चाहूँगी कि शीर्षक सुंदर होने के साथ पढ़ने में भी आसान हों। कैप्शन को कंप्यूटर और फोन दोनों पर देखकर ही तय करना चाहिए कि उनका आकार सही है।",
    "ऑडियो और उपशीर्षक एक ही मूल समय रेखा से बनने चाहिए। यदि एनीमेशन मॉडल अपना अलग ऑडियो दे, तो उसे मूल हिंदी आवाज पर नहीं थोपना चाहिए।",
    "तीन वक्ताओं के बीच बदलाव सहज होना चाहिए। बोलने के बाद थोड़ा विराम दर्शकों को समझने का समय देता है। हर दृश्य पर चमकीला ट्रांजिशन लगाने के बजाय कैमरे और आवाज में निरंतरता बनाए रखें, ताकि ध्यान बातचीत पर ही रहे।",
    "मैं कई बार संपादन में जरूरत से ज्यादा चीजें जोड़ देती थी। फिर समझ आया कि साफ नाम पट्टी, हल्का बैकग्राउंड और समय पर कट ज्यादा अच्छे लगते हैं।",
    "सभी हिस्सों को जोड़ने से पहले उनका फ्रेम आकार और दर एक जैसी रखनी चाहिए। यदि किसी क्लिप का ऑडियो छोटा है या फ्रेम बीच में टूटता है, तो अंतिम वीडियो खराब हो सकता है। हर स्रोत क्लिप को स्वतंत्र रूप से जाँचना जरूरी है।",
    "अब निजी डेटा की बात करें। असली तस्वीरें, आवाजें और अधूरे मॉडल परिणाम निजी कार्यक्षेत्र में रहने चाहिए।",
    "ऑनलाइन और ऑफलाइन विकल्प का फर्क साफ समझना भी जरूरी है। कुछ टूल आवाज बनाते समय टेक्स्ट इंटरनेट पर भेजते हैं, जबकि स्थानीय मॉडल उसी कंप्यूटर में काम करते हैं। इंस्टॉलेशन के लिए इंटरनेट लगना और हर बार डेटा भेजना अलग बातें हैं।",
    "हर परिणाम के साथ स्रोत पहचान, मॉडल चरण और समय दर्ज किया जा सकता है। इससे बाद में समझना आसान होगा कि कौन सा वीडियो किस मूल आवाज से बना था।",
    "वीडियो निर्यात करते समय पहले सात सौ बीस पी का साफ परिणाम देखें। कमजोर कंप्यूटर पर बहुत ऊँचा रिजोल्यूशन चुनने से प्रक्रिया बहुत धीमी हो सकती है। दर्शक सबसे पहले साफ आवाज, समझ में आने वाली कहानी और स्थिर चेहरे पर ध्यान देते हैं।",
    "मैं निर्यात के बाद पूरा वीडियो एक बार लगातार देखूँगी। बीच में कोई संवाद गायब तो नहीं, आवाज अचानक तेज तो नहीं हुई और कैप्शन गलत समय पर तो नहीं आए।",
    "फ़ाइल बन जाने पर उसके नाम से सफलता मान लेना ठीक नहीं है। अवधि, वीडियो स्ट्रीम, ऑडियो कोडेक और उपशीर्षक को स्वतंत्र रूप से पढ़कर जाँचें। अधूरी फ़ाइल मौजूद होने का मतलब वास्तविक दस मिनट का पूरा पॉडकास्ट बनना नहीं है।",
    "तकनीकी विषयों में गलत जानकारी बहुत तेजी से फैल सकती है। इसलिए आत्मविश्वास से दिया गया एआई जवाब भी जाँचने योग्य है।",
    "दूसरों की आवाज, संगीत या तस्वीर बिना अनुमति इस्तेमाल नहीं करनी चाहिए। मुफ्त डाउनलोड हमेशा मुफ्त उपयोग अधिकार नहीं देता। मौलिक सामग्री और सही श्रेय दर्शकों का भरोसा बढ़ाते हैं, साथ ही अनावश्यक कानूनी समस्याओं से भी बचाते हैं।",
    "एआई से बना चेहरा या आवाज हो तो दर्शकों को उचित जानकारी देना अच्छा अभ्यास है। खासकर जब पात्र असली लोगों जैसे दिखें, तो स्पष्ट अनुमति और पारदर्शिता जरूरी है।",
    "अच्छे पॉडकास्ट की पहचान सिर्फ आकर्षक वीडियो नहीं है। साफ आवाज और पढ़ने योग्य उपशीर्षक उन लोगों के लिए भी मददगार हैं जो वीडियो नहीं देख सकते। सामग्री को सुलभ बनाना कोई अतिरिक्त सजावट नहीं, बल्कि दर्शकों का सम्मान है।",
    "पहला संस्करण तैयार होने पर मैं छोटे समूह से प्रतिक्रिया माँगूँगी। किस हिस्से में कहानी धीमी लगी, कहाँ आवाज अजीब थी और कौन सा उदाहरण समझ नहीं आया।",
    "प्रतिक्रिया को तीन वर्गों में बाँट सकते हैं। कहानी और तथ्य, आवाज और चित्र, तथा तकनीकी स्थिरता। इससे हमें पता चलता है कि समस्या स्क्रिप्ट में है, मॉडल में है या संपादन में। हर सुधार को छोटे परीक्षण से फिर जाँचना चाहिए।",
    "प्रकाशन की जल्दी में समीक्षा न छोड़ें। हर संवाद का अर्थ, चेहरे की स्वाभाविकता, उचित अधिकार और अंतिम वीडियो की स्थिति देखें। अगर कोई हिस्सा संदिग्ध हो, तो पहले उसे ठीक करें।",
    "आज हमने विचार से लेकर शोध, स्क्रिप्ट, तीन आवाजें, चित्रों की अनुमति, मूल ऑडियो, होंठ परीक्षण और अंतिम जाँच तक पूरी यात्रा देखी। मुझे उम्मीद है कि अब यह प्रक्रिया थोड़ा कम रहस्यमय और ज्यादा व्यावहारिक लगेगी।",
    "और मैं कबीर, आखिरी बात जोड़ूँगा। एआई हमें नए रचनात्मक अवसर देता है, लेकिन सच, अनुमति और इंसानी जिम्मेदारी की जगह नहीं ले सकता।",
)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def json_digest(data: Any) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def atomic_json(path: Path, data: dict, *, new: bool = False) -> None:
    if path.is_symlink() or (new and path.exists()):
        raise ValueError("Source-bound artifact already exists or unsafe symlink")
    path.parent.mkdir(parents=True, exist_ok=True)
    scratch = path.with_name(path.name + "." + os.urandom(8).hex() + ".tmp")
    try:
        with scratch.open("x", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        if new and path.exists():
            raise ValueError("Never overwrite source-bound new artifact")
        scratch.replace(path)
    finally:
        scratch.unlink(missing_ok=True)


def read_json(path: Path, max_size: int = 1_000_000) -> dict:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > max_size:
        raise ValueError("Missing, symlinked or oversized private manifest")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Private manifest must be an object")
    return data


def workspace_path(root: str | Path) -> Path:
    raw = Path(root).expanduser()
    if raw.is_symlink():
        raise ValueError("Workspace cannot be a symlink")
    return raw.resolve()


def init(root: Path) -> dict:
    root = workspace_path(root)
    if (root / "project.json").exists() or (root / "project.json").is_symlink():
        raise ValueError("Private project exists already; no overwriting")
    root.mkdir(parents=True, exist_ok=True)
    for folder in ("portraits", "voices", "source", "chunks", "previews", "exports", "review", "scratch"):
        (root / folder).mkdir(exist_ok=True)
    turns = []
    for i in range(1, 46):
        speaker = SPEAKERS[(i-1) % len(SPEAKERS)]
        turns.append({"id": f"{i:03}", "speaker": speaker,
                      "text": DIALOGUE[i-1],
                      "pause_after": 0.4 if i < 45 else 0.0})
    project = {"schema": 3, "title": "Original Hindi Three-Presenter Podcast",
               "speakers": list(SPEAKERS), "language": "hi-IN", "turns": turns,
               "voice_presets": {"aarav": "hi-IN-MadhurNeural", "meera": "hi-IN-SwaraNeural",
                                 "kabir": "hi-IN-MadhurNeural (-10% rate, not distinct identity)"}}
    atomic_json(root / "project.json", project, new=True)
    return project


def load_project(root: Path) -> dict:
    project = read_json(Path(root) / "project.json")
    turns = project.get("turns")
    if (project.get("schema") != 3 or project.get("speakers") != list(SPEAKERS)
            or not isinstance(turns, list) or len(turns) != 45):
        raise ValueError("Exactly 45 original Hindi turns and three speakers required")
    seen = set()
    for i, turn in enumerate(turns, start=1):
        if (not isinstance(turn, dict) or turn.get("id") != f"{i:03}"
                or turn.get("speaker") not in SPEAKERS
                or not isinstance(turn.get("text"), str) or not turn["text"].strip()
                or not isinstance(turn.get("pause_after"), (float, int))
                or isinstance(turn["pause_after"], bool)
                or not 0 <= turn["pause_after"] <= 5):
            raise ValueError("Original Hindi speaker/turn/text/pause invalid")
        seen.add(turn["speaker"])
    if seen != set(SPEAKERS):
        raise ValueError("All three presenters must speak in the episode")
    return project


def wav_info(path: Path) -> tuple[int, float]:
    if path.is_symlink() or not path.is_file():
        raise ValueError("Original WAV missing or symlinked")
    with wave.open(str(path), "rb") as w:
        if (w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getcomptype()) != (1, 2, RATE, "NONE"):
            raise ValueError("Original WAV must be exact PCM mono 16-bit 16kHz")
        frames = w.getnframes()
        if frames < RATE or frames > RATE * 360:
            raise ValueError("Original Hindi voice turn must be 1–360 seconds")
        if len(w.readframes(frames)) != frames * 2:
            raise ValueError("Original WAV has truncated PCM bytes")
        return frames, frames / RATE


def source_inventory(root: Path, *, allow_short: bool = False) -> dict:
    root = workspace_path(root)
    p = load_project(root)
    portraits = {}
    for name in SPEAKERS:
        image = root / "portraits" / f"{name}.png"
        if image.is_symlink() or not image.is_file() or image.stat().st_size > 25_000_000:
            raise ValueError("Creator-authorized PNG required for " + name)
        with Image.open(image) as im:
            im.verify()
        with Image.open(image) as im:
            if im.format != "PNG" or min(im.size) < 200:
                raise ValueError("Real authorized portrait PNG must be >=200px")
        portraits[name] = digest(image)
    voices = {}
    seconds = 0.0
    for turn in p["turns"]:
        wav = root / "voices" / f"{turn['id']}.wav"
        frames, duration = wav_info(wav)
        voices[turn["id"]] = {"sha256": digest(wav), "frames": frames,
                                "duration": duration, "speaker": turn["speaker"]}
        seconds += duration + float(turn["pause_after"])
    if not allow_short and not TOTAL_MIN <= seconds <= TOTAL_MAX:
        raise ValueError(f"Original 45-turn Hindi timeline must be ~10 minutes; measured {seconds:.2f}s")
    if len({v["sha256"] for v in voices.values()}) != 45:
        raise ValueError("All 45 original voice WAVs must be distinct")
    return {"schema": 3, "status": "verified_original_speech_source_not_neural_video",
            "project_sha256": json_digest(p), "portrait_sha256": portraits,
            "voices": voices, "original_seconds": round(seconds, 6),
            "original_turn_count": 45, "human_lipsync_approved": False,
            "full_ten_minute_neural_video_completed": False,
            "synthetic_short_test_only": bool(allow_short)}


def build_source(root: Path, *, allow_short: bool = False) -> dict:
    root = workspace_path(root)
    dest = root / "source" / SOURCE_FILE
    if dest.exists() or dest.is_symlink():
        raise ValueError("Bound source manifest exists; use verify-source, no silent replacement")
    manifest = source_inventory(root, allow_short=allow_short)
    atomic_json(dest, manifest, new=True)
    return manifest


def verify_source(root: Path, *, allow_short: bool = False) -> dict:
    root = workspace_path(root)
    previous = read_json(root / "source" / SOURCE_FILE)
    fresh = source_inventory(root, allow_short=allow_short)
    if fresh != previous:
        raise ValueError("Original voice/portrait/project SHA or metadata changed")
    return fresh


def frame_bounds(frames: int) -> list[tuple[int, int]]:
    if type(frames) is not int or frames < RATE:
        raise ValueError("Invalid original PCM frame count")
    count = (frames + RATE * 10 - 1) // (RATE * 10)
    base, extra = divmod(frames, count)
    if base < RATE:
        raise ValueError("Cannot split source into playable >=1s chunks")
    boundaries = []
    offset = 0
    for i in range(count):
        n = base + (i < extra)
        boundaries.append((offset, offset + n))
        offset += n
    assert offset == frames
    return boundaries


def chunk_plan(source: dict) -> dict:
    chunks = []
    for id_, voice in source["voices"].items():
        for i, (start, end) in enumerate(frame_bounds(voice["frames"]), start=1):
            chunks.append({"id": f"{id_}-{i:03}", "line_id": id_,
                           "speaker": voice["speaker"], "part": i,
                           "start_frame": start, "end_frame": end,
                           "frames": end - start, "duration": (end-start) / RATE,
                           "source_wav_sha256": voice["sha256"],
                           "portrait_sha256": source["portrait_sha256"][voice["speaker"]]})
    return {"schema": 3, "status": "original_pcm_chunks_not_neural_video",
            "source_binding": json_digest(source), "count": len(chunks),
            "chunks": chunks, "human_lipsync_approved": False,
            "full_ten_minute_neural_video_completed": False}


def prepare_chunks(root: Path, *, allow_short: bool = False) -> dict:
    root = workspace_path(root)
    src = verify_source(root, allow_short=allow_short)
    if (root / "source" / CHUNK_FILE).exists():
        raise ValueError("Existing chunk export cannot be overwritten")
    plan = chunk_plan(src)
    for row in plan["chunks"]:
        out = root / "chunks" / (row["id"] + ".wav")
        if out.exists() or out.is_symlink():
            raise ValueError("Chunk output already exists; inspect, do not overwrite")
    root.joinpath("chunks").mkdir(exist_ok=True)
    for row in plan["chunks"]:
        wav = root / "voices" / (row["line_id"] + ".wav")
        out = root / "chunks" / (row["id"] + ".wav")
        with wave.open(str(wav), "rb") as f:
            f.setpos(row["start_frame"])
            payload = f.readframes(row["frames"])
        with out.open("xb") as raw:
            with wave.open(raw, "wb") as f:
                f.setnchannels(1);f.setsampwidth(2);f.setframerate(RATE)
                f.writeframes(payload)
        row["chunk_sha256"] = digest(out)
    atomic_json(root / "source" / CHUNK_FILE, plan, new=True)
    return plan


def verify_chunks(root: Path, *, allow_short: bool = False) -> dict:
    root = workspace_path(root)
    src = verify_source(root, allow_short=allow_short)
    recorded = read_json(root / "source" / CHUNK_FILE, 2_000_000)
    expected = chunk_plan(src)
    if {k: v for k, v in recorded.items() if k != "chunks"} != {k: v for k, v in expected.items() if k != "chunks"}:
        raise ValueError("Original PCM chunk source binding differs")
    if not isinstance(recorded.get("chunks"), list) or len(recorded["chunks"]) != expected["count"]:
        raise ValueError("Missing signed original speech chunks")
    for row, spec in zip(recorded["chunks"], expected["chunks"]):
        if ({k: v for k, v in row.items() if k != "chunk_sha256"} != spec
                or set(row) != set(spec) | {"chunk_sha256"}):
            raise ValueError("Original chunk metadata was modified")
        path = root / "chunks" / (spec["id"] + ".wav")
        if path.is_symlink() or not path.is_file() or digest(path) != row["chunk_sha256"]:
            raise ValueError("Chunk SHA or file missing")
        frames, _ = wav_info(path)
        if frames != spec["frames"]:
            raise ValueError("Original PCM chunk frame count differs")
        with wave.open(str(root / "voices" / (row["line_id"] + ".wav")), "rb") as source:
            source.setpos(row["start_frame"])
            payload = source.readframes(row["frames"])
        with wave.open(str(path), "rb") as piece:
            if piece.readframes(row["frames"]) != payload:
                raise ValueError("Saved PCM chunk bytes not identical to original source")
    return recorded