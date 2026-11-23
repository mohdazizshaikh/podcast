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
    "नमस्कार दोस्तों, हमारे हिंदी पॉडकास्ट में आपका स्वागत है। आज हम नई तकनीक के असली उपयोग पर बात करेंगे।",
    "सबसे पहले यह समझते हैं कि तकनीक का लक्ष्य लोगों की रोज़मर्रा की समस्याओं को सरल बनाना है।",
    "मैं आज कुछ व्यावहारिक उदाहरण दूँगा, जिनसे हम अच्छे और गलत इस्तेमाल के बीच फर्क समझ सकें।",
    "जब कोई नया एआई उपकरण इस्तेमाल करें, तो उसकी सीमाएँ और जानकारी की विश्वसनीयता जरूर जाँचें।",
    "आवाज़ और चेहरे जैसे व्यक्तिगत डेटा का उपयोग केवल उचित अनुमति के साथ करना चाहिए।",
    "तकनीक सीखने के लिए छोटे प्रयोग करें, परिणाम देखें और फिर धीरे-धीरे काम आगे बढ़ाएँ।",
    "सिर्फ आकर्षक वीडियो नहीं, साफ आवाज़, सही जानकारी और दर्शकों का भरोसा भी महत्वपूर्ण है।",
    "अगर कोई परिणाम गलत लगे, तो प्रक्रिया रोककर स्रोत और सेटिंग की दोबारा समीक्षा करें।",
    "आज की बातचीत से हमारा उद्देश्य जिम्मेदार रचनात्मकता को बढ़ावा देना है।",
    "धन्यवाद, अगले हिस्से में हम इस विचार को और गहराई से समझेंगे।",
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
                      "text": f"भाग {i}: {DIALOGUE[(i-1) % len(DIALOGUE)]}",
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