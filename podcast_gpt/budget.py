"""Read-only original Hindi CPU face budget from *verified saved real* sample timings.

Never invokes SadTalker, TTS, downloads, encoders or copies media.
This is a planning illustration, NOT a runtime commitment or quality claim.
"""
from __future__ import annotations

import math
import statistics
from pathlib import Path

from .source import SPEAKERS, read_json, workspace_path
from .neural import verified_previews


def estimate_from_measured(rows: list[dict], verified_ids: set[str],
                           elapsed_seconds: dict[str, float]) -> dict:
    """Pure computation; caller MUST independently verify source and MP4s."""
    if (not isinstance(rows, list) or not rows
            or not isinstance(verified_ids, set)
            or not isinstance(elapsed_seconds, dict)):
        raise ValueError("Complete signed neural inventory required for CPU estimate")
    known = set()
    remaining = []
    rates: dict[str, list[float]] = {speaker: [] for speaker in SPEAKERS}
    for row in rows:
        if (not isinstance(row, dict) or row.get("speaker") not in rates
                or not isinstance(row.get("id"), str)
                or row["id"] in known
                or isinstance(row.get("duration"), bool)
                or not isinstance(row.get("duration"), (float, int))
                or not math.isfinite(row["duration"])
                or not 1 <= row["duration"] <= 10):
            raise ValueError("Invalid source-bound original Hindi PCM inventory")
        known.add(row["id"])
        if row["id"] not in verified_ids:
            remaining.append(row)
    if not verified_ids.issubset(known) or not set(elapsed_seconds).issubset(verified_ids):
        raise ValueError("Unverified or foreign CPU model timing was supplied")
    for row in rows:
        cid = row["id"]
        if cid in elapsed_seconds:
            elapsed = elapsed_seconds[cid]
            if (type(elapsed) not in (float, int) or not math.isfinite(elapsed)
                    or not 0 < elapsed <= 172800):
                raise ValueError("Invalid/forged local model timing")
            rates[row["speaker"]].append(elapsed / row["duration"])
    sample_count = sum(map(len, rates.values()))
    out = {
        "status": "source_verified_local_cpu_pace_planning_only",
        "schema": 1,
        "original_pcm_chunks_total": len(rows),
        "independently_decoded_saved_neural_previews": len(verified_ids),
        "remaining_original_pcm_chunks": len(remaining),
        "measured_saved_model_cpu_samples": sample_count,
        "measured_speakers": [name for name in SPEAKERS if rates[name]],
        "new_model_inference_calls": 0,
        "new_media_encoding_calls": 0,
        "real_ten_minute_neural_video_verified": False,
        "human_lipsync_approved": False,
        "estimate_is_a_guarantee": False,
    }
    if not sample_count:
        return {**out, "estimate_available": False,
                "next_action": ("Render and independently decode at least one genuine "
                                "authorized SadTalker CPU preview first; estimates "
                                "cannot be inferred from fake/untimed clips."),
                "estimated_remaining_cpu_seconds": None,
                "illustrative_range_hours": None,
                "fallback_unmeasured_speakers": list(SPEAKERS)}
    global_rate = statistics.median(rate for group in rates.values() for rate in group)
    fallback = sorted({row["speaker"] for row in remaining if not rates[row["speaker"]]})
    seconds = sum(row["duration"] * (
        statistics.median(rates[row["speaker"]]) if rates[row["speaker"]]
        else global_rate) for row in remaining)
    hours = seconds / 3600
    return {**out, "estimate_available": True,
            "estimated_remaining_cpu_seconds": round(seconds, 1),
            "estimated_remaining_cpu_hours": round(hours, 2),
            "illustrative_range_hours": [round(hours * .5, 2), round(hours * 3.0, 2)],
            "fallback_unmeasured_speakers": fallback,
            "model_cpu_seconds_per_speech_second_median": round(global_rate, 3),
            "important_limitation": ("Local samples may not represent all voices, "
                                     "lengths, system load, model startup and FFmpeg "
                                     "composition. The requested wall budget is "
                                     "NOT a hard total runtime cutoff. This does not "
                                     "verify lip sync or a finished episode.")}


def estimate_cpu_budget(root: Path, *, allow_short: bool = False) -> dict:
    """Full independent source SHA/PCM + saved genuine MP4 decoder gate first."""
    root = workspace_path(root)
    manifest, confirmed = verified_previews(root, allow_short=allow_short)
    elapsed: dict[str, float] = {}
    for row in manifest["chunks"]:
        cid = row["id"]
        if cid not in confirmed:
            continue
        sidecar = read_json(root/"previews"/(cid+".json"), 100_000)
        # Explicitly labelled test-only static fake face clips are never
        # accepted as model timing evidence, even if a test wrote a number.
        if sidecar.get("TEST_ONLY_FAKE_MODEL_NOT_GENUINE_SADTALKER") is True:
            continue
        sec = sidecar.get("actual_cpu_model_seconds")
        if sec is None:
            continue
        if (type(sec) not in (int, float) or not math.isfinite(sec)
                or not 0 < sec <= 172800):
            raise ValueError("Saved source-bound model elapsed time invalid")
        elapsed[cid] = float(sec)
    return estimate_from_measured(manifest["chunks"], set(confirmed), elapsed)
