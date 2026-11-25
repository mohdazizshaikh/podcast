"""Deterministic spotlight layout: one large active card, static listener rail."""
import math


def spotlight(indices,active,size):
    indices=list(indices)
    if not 1<=len(indices)<=10 or len(set(indices))!=len(indices) or active not in indices:
        raise ValueError("Invalid spotlight cast")
    if size not in ((1280,720),(720,1280),(720,720)):
        raise ValueError("Unsupported spotlight canvas")
    w,h=size; margin=20;top=70;bottom=h-52
    usable_w=w-2*margin;usable_h=bottom-top
    others=[index for index in indices if index!=active]
    if not others:return {active:(margin,top,usable_w,usable_h)}
    n=len(others)
    if w>h:
        active_w=usable_w*3//5
        out={active:(margin,top,active_w,usable_h)}
        x0=margin+active_w+margin;y0=top
        rail_w=usable_w-active_w-margin;rail_h=usable_h
        cols=min(2,n) if n>3 else 1
    else:
        active_h=usable_h*11//20
        out={active:(margin,top,usable_w,active_h)}
        x0=margin;y0=top+active_h+margin
        rail_w=usable_w;rail_h=usable_h-active_h-margin
        cols=min(3,n)
    rows=math.ceil(n/cols)
    cw=(rail_w-margin*(cols-1))//cols
    ch=(rail_h-margin*(rows-1))//rows
    if min(cw,ch)<=36:raise ValueError("Spotlight listener cards too small")
    for i,index in enumerate(others):
        out[index]=(x0+(i%cols)*(cw+margin),y0+(i//cols)*(ch+margin),cw,ch)
    return out
