"""Bounded static gain toward an explicit loudness target.

Not a dynamic limiter. Store the measured baseline and measured candidate,
then audit the exact integer PCM recipe independently of FFmpeg version.
"""
import math
import hashlib

CEILING=-1.5
MARGIN=0.25
MAX_PCM=30000
SCALE=1_000_000


def target(value):
    if type(value) is not int or not -24<=value<=-14:
        raise ValueError("Target loudness must be a whole number from -24 to -14 LUFS")
    return value


def _measurement(value):
    keys={"integrated_lufs","true_peak_dbtp","loudness_range_lu","gating_threshold_lufs"}
    if not isinstance(value,dict) or set(value)!=keys:raise ValueError("Invalid loudness measurement")
    if any(type(v) not in (int,float) or not math.isfinite(v) or not -150<=v<=100 for v in value.values()):
        raise ValueError("Finite loudness measurements required; inspect audio before normalization")
    return value


def gain_ppm(goal,baseline,peak):
    target(goal);_measurement(baseline)
    if type(peak) is not int or not 1<=peak<=32768:raise ValueError("Invalid baseline PCM peak")
    db=min(goal-baseline["integrated_lufs"],CEILING-MARGIN-baseline["true_peak_dbtp"],12)
    factor=min(10**(db/20),MAX_PCM/peak)
    value=math.floor(SCALE*factor)
    if not 1<=value<=4*SCALE:raise ValueError("Gain outside bounded processing range")
    return value


def record(goal,baseline,peak,baseline_sha,after):
    gain=gain_ppm(goal,baseline,peak);_measurement(after)
    if after["true_peak_dbtp"]>CEILING:raise ValueError("Measured candidate exceeds true-peak ceiling; no normalized mix saved")
    if not isinstance(baseline_sha,str) or len(baseline_sha)!=64 or any(c not in "0123456789abcdef" for c in baseline_sha):
        raise ValueError("Invalid baseline PCM digest")
    return {"algorithm":"bounded_static_gain_v1","target_lufs":goal,"true_peak_ceiling_dbtp":CEILING,
            "baseline_measurement":baseline,"baseline_pcm_peak":peak,"baseline_pcm_sha256":baseline_sha,
            "gain_ppm":gain,"candidate_measurement":after,
            "measured_target_within_0_5_lu":abs(after["integrated_lufs"]-goal)<=.5,
            "dynamic_limiter_used":False}


def validate(value):
    if not isinstance(value,dict):raise ValueError("Invalid normalization recipe")
    try:expected=record(value["target_lufs"],value["baseline_measurement"],value["baseline_pcm_peak"],
                        value["baseline_pcm_sha256"],value["candidate_measurement"])
    except (KeyError,TypeError,OverflowError):raise ValueError("Invalid normalization recipe") from None
    if expected!=value:raise ValueError("Normalization settings differ")
    return value


def apply(block,gain):
    from .v4_post_audio import _samples,_bytes,_scale
    values=[_scale(s,gain,SCALE) for s in _samples(block)]
    if max(map(abs,values),default=0)>MAX_PCM:raise ValueError("Normalized PCM exceeds sample ceiling")
    return _bytes(values)
