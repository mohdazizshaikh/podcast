"""Bounded measured static peak correction of an already guarded PCM mix."""
import array
import hashlib
import math
import sys
import wave
from pathlib import Path

SCALE=1_000_000
STEP=944060  # approximately -0.5 dB, rounded conservatively
MIN_GAIN=251180  # approximately -12 dB maximum attenuation
MAX_RETRIES=3
CEILING=-1.5


def peak(value):
    if type(value) not in (int,float) or not math.isfinite(value) or not -150<=value<=100:
        raise ValueError("Finite measured true peak required")
    return value


def next_gain(current,measured):
    peak(measured)
    if type(current) is not int or not MIN_GAIN<=current<=SCALE or measured<=CEILING:
        raise ValueError("Invalid peak correction step")
    steps=math.ceil((measured-CEILING+0.25)*2)
    gain=current
    for _ in range(min(steps,25)):
        gain=gain*STEP//SCALE
    if gain<MIN_GAIN or gain>=current:raise ValueError("Peak correction exceeds bounded attenuation")
    return gain


def receipt(attempts,baseline_sha):
    if not isinstance(baseline_sha,str) or len(baseline_sha)!=64 or any(c not in '0123456789abcdef' for c in baseline_sha):
        raise ValueError("Invalid peak correction baseline digest")
    if not isinstance(attempts,list) or not 1<=len(attempts)<=MAX_RETRIES+1:
        raise ValueError("Invalid peak correction attempt count")
    expected=SCALE
    for i,row in enumerate(attempts):
        if not isinstance(row,dict) or set(row)!={'gain_ppm','measured_true_peak_dbtp'} or type(row['gain_ppm']) is not int or row['gain_ppm']!=expected:
            raise ValueError("Invalid peak correction attempt")
        measured=peak(row['measured_true_peak_dbtp'])
        if i<len(attempts)-1:expected=next_gain(expected,measured)
        elif measured>CEILING:raise ValueError("Peak correction did not reach measured ceiling")
    return {'algorithm':'bounded_measured_attenuation_v1','baseline_pcm_sha256':baseline_sha,
            'attempts':attempts,'gain_ppm':expected,'ceiling_dbtp':CEILING}


def validate(value):
    if not isinstance(value,dict):raise ValueError("Invalid peak correction recipe")
    if receipt(value.get('attempts'),value.get('baseline_pcm_sha256'))!=value:raise ValueError("Peak correction recipe differs")
    return value


def apply(raw,gain):
    if type(gain) is not int or not MIN_GAIN<=gain<=SCALE:raise ValueError("Invalid peak correction gain")
    if gain==SCALE:return raw
    a=array.array('h');a.frombytes(raw)
    if sys.byteorder!='little':a.byteswap()
    a=array.array('h',((abs(x)*gain//SCALE)*(1 if x>=0 else -1) for x in a))
    if sys.byteorder!='little':a.byteswap()
    return a.tobytes()


def _copy(baseline,dest,frames,expected,gain):
    before=hashlib.sha256();after=hashlib.sha256();count=0
    with wave.open(str(baseline),'rb') as inp,dest.open('xb') as handle:
        if (inp.getnchannels(),inp.getsampwidth(),inp.getframerate(),inp.getcomptype(),inp.getnframes())!=(1,2,16000,'NONE',frames):
            raise ValueError("Invalid peak correction baseline WAV")
        with wave.open(handle,'wb') as out:
            out.setnchannels(1);out.setsampwidth(2);out.setframerate(16000)
            while True:
                raw=inp.readframes(16000)
                if not raw:break
                before.update(raw);count+=len(raw)//2
                fixed=apply(raw,gain);after.update(fixed);out.writeframesraw(fixed)
    if count!=frames or before.hexdigest()!=expected:raise ValueError("Peak correction baseline changed")
    return after.hexdigest()


def run(baseline,temp,frames,baseline_sha,measure):
    """Measure and retry from the same source, never repeatedly quantize output."""
    current=Path(baseline);digest=baseline_sha;gain=SCALE;attempts=[]
    for i in range(MAX_RETRIES+1):
        measured=peak(measure(current,frames)['true_peak_dbtp'])
        attempts.append({'gain_ppm':gain,'measured_true_peak_dbtp':measured})
        if measured<=CEILING:return current,digest,receipt(attempts,baseline_sha)
        if i==MAX_RETRIES:break
        gain=next_gain(gain,measured)
        current=Path(temp)/f'peak-correction-{i+1}.wav'
        digest=_copy(baseline,current,frames,baseline_sha,gain)
    raise ValueError("Peak correction did not reach measured ceiling")
