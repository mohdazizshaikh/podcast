"""Bounded active-speaker camera motion with unchanged frame count."""
MODES=("fixed","push-in","pull-out","smooth-push","pan-left","pan-right")


def validate(mode):
    if not isinstance(mode,str) or mode not in MODES:raise ValueError("Choose a supported studio camera mode")
    return mode


def filter_suffix(mode,width,height,frames):
    validate(mode)
    if any(type(n) is not int for n in (width,height,frames)) or min(width,height)<2 or width%2 or height%2 or not 1<=frames<=251:
        raise ValueError("Invalid camera frame geometry")
    if mode=="fixed" or frames==1:return ""
    p=f"min(on/{frames-1},1)"
    x="iw/2-iw/zoom/2";y="ih/2-ih/zoom/2"
    if mode=="push-in":z=f"1+0.03*{p}"
    elif mode=="pull-out":z=f"1+0.03*(1-{p})"
    elif mode=="smooth-push":z=f"1+0.03*{p}*{p}*(3-2*{p})"
    else:
        z="1.04"
        x=f"(iw-iw/zoom)*{'(1-'+p+')' if mode=='pan-left' else p}"
    return f",zoompan=z='{z}':x='{x}':y='{y}':d=1:s={width}x{height}:fps=25"
