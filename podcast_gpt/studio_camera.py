"""Optional active-speaker push-in with unchanged frame count."""
MODES=("fixed","push-in")


def validate(mode):
    if not isinstance(mode,str) or mode not in MODES:raise ValueError("Choose fixed or push-in camera")
    return mode


def filter_suffix(mode,width,height,frames):
    validate(mode)
    if any(type(n) is not int for n in (width,height,frames)) or min(width,height)<2 or width%2 or height%2 or not 1<=frames<=251:
        raise ValueError("Invalid camera frame geometry")
    if mode=="fixed" or frames==1:return ""
    return (f",zoompan=z='1+0.03*min(on/{frames-1},1)':"
            "x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':"
            f"d=1:s={width}x{height}:fps=25")
