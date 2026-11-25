"""Conservative dynamic PCM guard; FFmpeg measurement is separately mandatory."""
import math
from collections import deque

CAP=22000
SCALE=1_000_000
RELEASE=800
RADIUS=3
CEILING=-1.5


def settings(enabled):
    if type(enabled) is not bool:raise ValueError("True-peak guard must be boolean")
    if not enabled:return None
    return {"algorithm":"local_peak_lookahead_v1","sample_cap_pcm":CAP,"radius_frames":RADIUS,
            "release_frames":RELEASE,"measured_ceiling_dbtp":CEILING}


def samples(values):
    # Three-sample lookahead and history, including zero padding at edges.
    window=deque([0]*RADIUS,maxlen=2*RADIUS+1)
    it=iter(values)
    for _ in range(RADIUS+1):
        try:window.append(next(it))
        except StopIteration:break
    count=len(window)-RADIUS
    if not count:return
    while len(window)<2*RADIUS+1:window.append(0)
    gain=SCALE
    while count:
        peak=max(map(abs,window))
        allowed=SCALE if peak<=CAP else CAP*SCALE//peak
        gain=min(allowed,gain+SCALE//RELEASE,SCALE)
        x=window[RADIUS]
        yield (abs(x)*gain//SCALE)*(1 if x>=0 else -1)
        try:window.append(next(it))
        except StopIteration:window.append(0);count-=1


def blocks(raw_blocks,config,decode,encode):
    if config is None:
        yield from raw_blocks
        return
    values=(s for block in raw_blocks for s in decode(block))
    chunk=[]
    for value in samples(values):
        chunk.append(value)
        if len(chunk)==16000:
            yield encode(chunk);chunk=[]
    if chunk:yield encode(chunk)


def check(measured):
    if type(measured) not in (int,float) or not math.isfinite(measured) or not -150<=measured<=CEILING:
        raise ValueError("Measured true peak unavailable or above -1.5 dBTP; no guarded candidate approved")
    return {"measured_true_peak_dbtp":measured,"ceiling_dbtp":CEILING}
