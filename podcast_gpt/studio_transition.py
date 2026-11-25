"""Pause-only speaker handoffs with no timeline overlap or dropped frames."""
MODES=('cut','quick','gentle')
LIMITS={'quick':6,'gentle':12}


def validate(mode):
    if not isinstance(mode,str) or mode not in MODES:
        raise ValueError('Choose cut, quick or gentle studio transition')
    return mode


def schedule(plan,mode):
    validate(mode)
    if mode=='cut':return {}
    result={}
    for i in range(1,len(plan)-1):
        prev,row,nxt=plan[i-1:i+2]
        if row['kind']!='pause':continue
        frames=row['frames']
        if type(frames) is not int or frames<1:raise ValueError('Invalid transition pause frame count')
        if frames<3 or prev['kind']!='speech' or nxt['kind']!='speech':continue
        if prev['speaker']!=row['speaker'] or prev['turn_id']!=row['turn_id'] or nxt['speaker']==row['speaker']:continue
        length=min(frames,LIMITS[mode])
        result[i]={'from':row['speaker'],'to':nxt['speaker'],'start':frames-length,'frames':length}
    return result


def filter_graph(total,start,frames):
    if any(type(v) is not int for v in (total,start,frames)) or not 3<=frames<=12 or start<0 or start+frames!=total or total>100_000_000:
        raise ValueError('Invalid pause transition frame geometry')
    # Blend N starts at one. Hold outgoing until the transition tail.
    p=f'clip((N-1-{start})/{frames-1},0,1)'
    return ("[0:v]fps=25,setsar=1,format=yuv420p[a];"
            "[1:v]fps=25,setsar=1,format=yuv420p[b];"
            f"[a][b]blend=all_expr='A*(1-{p})+B*{p}':shortest=1,format=yuv420p[out]")
