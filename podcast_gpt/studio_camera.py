"""Bounded active-speaker camera motion with unchanged frame count."""
MODES=("fixed","push-in","pull-out","smooth-push","pan-left","pan-right","continuous-drift","continuous-breathe")
CONTINUOUS=("continuous-drift","continuous-breathe")
PERIOD=200
MAX_START=100_000_000


def validate(mode):
    if not isinstance(mode,str) or mode not in MODES:raise ValueError("Choose a supported studio camera mode")
    return mode


def filter_suffix(mode,width,height,frames,*,start_frame=0):
    validate(mode)
    if any(type(n) is not int for n in (width,height,frames,start_frame)) or min(width,height)<2 or width%2 or height%2 or not 1<=frames<=251 or not 0<=start_frame<=MAX_START:
        raise ValueError("Invalid camera frame geometry or offset")
    if mode=="fixed" or (frames==1 and mode not in CONTINUOUS):return ""
    x="iw/2-iw/zoom/2";y="ih/2-ih/zoom/2"
    if mode in CONTINUOUS:
        phase=f"(1-cos(2*PI*(on+{start_frame%PERIOD})/{PERIOD}))/2"
        if mode=="continuous-drift":
            z="1.04";x=f"(iw-iw/zoom)*({phase})"
        else:z=f"1+0.03*({phase})"
    else:
        p=f"min(on/{frames-1},1)"
        if mode=="push-in":z=f"1+0.03*{p}"
        elif mode=="pull-out":z=f"1+0.03*(1-{p})"
        elif mode=="smooth-push":z=f"1+0.03*{p}*{p}*(3-2*{p})"
        else:
            z="1.04"
            x=f"(iw-iw/zoom)*{'(1-'+p+')' if mode=='pan-left' else p}"
    return f",zoompan=z='{z}':x='{x}':y='{y}':d=1:s={width}x{height}:fps=25"


def offsets(plan):
    """Absolute episode frame starts, including every pause."""
    cursor=0
    for segment in plan:
        frames=segment['frames']
        if type(frames) is not int or frames<1 or cursor+frames>MAX_START:
            raise ValueError("Invalid camera timeline coverage")
        yield cursor
        cursor+=frames
