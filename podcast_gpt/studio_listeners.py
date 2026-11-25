"""Simulated listener portrait framing; no facial synthesis or reaction inference."""
from . import studio_camera as camera

MODES=("static","drift","breathe")


def validate(mode):
    if not isinstance(mode,str) or mode not in MODES:
        raise ValueError("Choose static, drift or breathe listener motion")
    return mode


def regions(rectangles,active,size):
    """Even, interior portrait bounds from the current layout, never its labels."""
    width,height=size
    result={}
    for index,(x,y,w,h) in rectangles.items():
        if index==active:continue
        if type(index) is not int or not 1<=index<=10:raise ValueError("Invalid listener index")
        rect=((x+9)//2*2,(y+7)//2*2,(w-16)//2*2,(h-36)//2*2)
        a,b,c,d=rect
        if min(c,d)<2 or a<0 or b<0 or a+c>width or b+d>height:
            raise ValueError("Invalid listener portrait bounds")
        result[index]=rect
    return result


def graph(rects,mode,frames,start_frame):
    """Crop from the static card and overlay only listener portrait interiors."""
    validate(mode)
    if mode=="static" or not rects:return [],"[0:v]"
    if type(start_frame) is not int or not 0<=start_frame<=camera.MAX_START:
        raise ValueError("Invalid listener motion offset")
    if len(rects)>9:raise ValueError("Too many visible listeners")
    pairs=sorted(rects.items());labels="".join(f"[ls{i}]" for i,_ in pairs)
    filters=[f"[0:v]split={len(pairs)+1}[lb0]{labels}"]
    base="[lb0]"
    for j,(i,(x,y,w,h)) in enumerate(pairs,1):
        if type(i) is not int or not 1<=i<=10 or any(type(v) is not int or v%2 for v in (x,y,w,h)) or min(x,y)<0:
            raise ValueError("Invalid listener motion geometry")
        suffix=camera.filter_suffix("continuous-"+mode,w,h,frames,start_frame=(start_frame+37*i)%camera.PERIOD)
        filters.append(f"[ls{i}]crop={w}:{h}:{x}:{y},setsar=1{suffix}[lp{i}]")
        out=f"[lb{j}]"
        filters.append(f"{base}[lp{i}]overlay={x}:{y}:shortest=1:repeatlast=0{out}")
        base=out
    return filters,base
