"""Bounded loudness gain with measured attenuation retries from one PCM baseline."""
import array
import hashlib
import sys
import wave
from pathlib import Path
from . import loudness_gain as gain, peak_correction as correction

ALGORITHM="bounded_static_gain_retry_v2"


def absolute(initial,relative):
    if type(initial) is not int or not 1<=initial<=4*gain.SCALE or type(relative) is not int or not correction.MIN_GAIN<=relative<=gain.SCALE:
        raise ValueError("Invalid combined gain")
    result=initial*relative//gain.SCALE
    if not result:raise ValueError("Combined gain below supported range")
    return result


def record(goal,before,peak,sha,ceiling,attempts):
    if ceiling is None:raise ValueError("Combined gain requires a peak guard ceiling")
    initial=gain.gain_ppm(goal,before,peak,ceiling)
    if not isinstance(sha,str) or len(sha)!=64 or any(c not in "0123456789abcdef" for c in sha):raise ValueError("Invalid combined baseline digest")
    if not isinstance(attempts,list) or not 1<=len(attempts)<=correction.MAX_RETRIES+1:raise ValueError("Invalid combined attempt count")
    relative=gain.SCALE
    for i,row in enumerate(attempts):
        if not isinstance(row,dict) or set(row)!={"relative_gain_ppm","gain_ppm","measurement"}:raise ValueError("Invalid combined attempt")
        actual=absolute(initial,relative)
        if type(row["relative_gain_ppm"]) is not int or type(row["gain_ppm"]) is not int or row["relative_gain_ppm"]!=relative or row["gain_ppm"]!=actual:raise ValueError("Combined attempt gain differs")
        measured=gain._measurement(row["measurement"])
        if i<len(attempts)-1:
            relative=correction.next_gain(relative,measured["true_peak_dbtp"])
            if absolute(initial,relative)>=actual:raise ValueError("Combined gain did not decrease")
        elif measured["true_peak_dbtp"]>gain.CEILING:raise ValueError("Combined candidate exceeds measured true-peak ceiling")
    return {"algorithm":ALGORITHM,"target_lufs":goal,"true_peak_ceiling_dbtp":gain.CEILING,
            "baseline_measurement":before,"baseline_pcm_peak":peak,"baseline_pcm_sha256":sha,
            "initial_gain_ppm":initial,"gain_ppm":actual,"attempts":attempts,"candidate_measurement":measured,
            "measured_target_within_0_5_lu":abs(measured["integrated_lufs"]-goal)<=.5,
            "dynamic_limiter_used":True,"sample_peak_ceiling_pcm":ceiling}


def validate(value):
    if not isinstance(value,dict):raise ValueError("Invalid combined gain recipe")
    try:expected=record(value["target_lufs"],value["baseline_measurement"],value["baseline_pcm_peak"],value["baseline_pcm_sha256"],value["sample_peak_ceiling_pcm"],value["attempts"])
    except (KeyError,TypeError,OverflowError):raise ValueError("Invalid combined gain recipe") from None
    if expected!=value:raise ValueError("Combined gain recipe differs")
    return value


def apply(raw,ppm,ceiling):
    if type(ppm) is not int or not 1<=ppm<=4*gain.SCALE:raise ValueError("Invalid combined PCM gain")
    cap=gain.sample_ceiling(ceiling)
    a=array.array("h");a.frombytes(raw)
    if sys.byteorder!="little":a.byteswap()
    values=[abs(x)*ppm//gain.SCALE*(1 if x>=0 else -1) for x in a]
    if max(map(abs,values),default=0)>cap:raise ValueError("Combined PCM exceeds sample ceiling")
    a=array.array("h",values)
    if sys.byteorder!="little":a.byteswap()
    return a.tobytes()


def _copy(baseline,path,frames,sha,ppm,ceiling):
    before=hashlib.sha256();after=hashlib.sha256();count=0
    with wave.open(str(baseline),"rb") as inp,path.open("xb") as handle:
        if (inp.getnchannels(),inp.getsampwidth(),inp.getframerate(),inp.getcomptype(),inp.getnframes())!=(1,2,16000,"NONE",frames):raise ValueError("Invalid combined baseline WAV")
        with wave.open(handle,"wb") as out:
            out.setnchannels(1);out.setsampwidth(2);out.setframerate(16000)
            while True:
                raw=inp.readframes(16000)
                if not raw:break
                before.update(raw);count+=len(raw)//2
                fixed=apply(raw,ppm,ceiling);after.update(fixed);out.writeframesraw(fixed)
    if count!=frames or before.hexdigest()!=sha:raise ValueError("Combined baseline changed")
    return after.hexdigest()


def run(baseline,temp,frames,sha,goal,before,peak,ceiling,measure):
    if ceiling is None:raise ValueError("Combined gain requires a peak guard ceiling")
    initial=gain.gain_ppm(goal,before,peak,ceiling);relative=gain.SCALE;attempts=[]
    for i in range(correction.MAX_RETRIES+1):
        ppm=absolute(initial,relative)
        path=Path(temp)/f"combined-gain-{i}.wav"
        digest=_copy(baseline,path,frames,sha,ppm,ceiling)
        measured=gain._measurement(measure(path,frames))
        attempts.append({"relative_gain_ppm":relative,"gain_ppm":ppm,"measurement":measured})
        if measured["true_peak_dbtp"]<=gain.CEILING:return path,digest,record(goal,before,peak,sha,ceiling,attempts)
        if i==correction.MAX_RETRIES:break
        relative=correction.next_gain(relative,measured["true_peak_dbtp"])
        if absolute(initial,relative)>=ppm:raise ValueError("Combined gain did not decrease")
    raise ValueError("Combined gain did not reach measured ceiling")
