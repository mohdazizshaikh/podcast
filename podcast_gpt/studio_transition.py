"""Pause-only speaker handoffs with no timeline overlap or dropped frames."""
MODES=('cut','quick','gentle','match-quick','match-gentle')
MATCH_MODES=('match-quick','match-gentle')
LIMITS={'quick':6,'gentle':12,'match-quick':6,'match-gentle':12}


def validate(mode):
    if not isinstance(mode,str) or mode not in MODES:
        raise ValueError('Choose cut, quick, gentle, match-quick or match-gentle studio transition')
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


def _blend(total,start,frames):
    if any(type(v) is not int for v in (total,start,frames)) or not 3<=frames<=12 or start<0 or start+frames!=total or total>100_000_000:
        raise ValueError('Invalid pause transition frame geometry')
    # Blend N starts at one. Hold outgoing until the transition tail.
    p=f'clip((N-1-{start})/{frames-1},0,1)'
    return f"[a][b]blend=all_expr='A*(1-{p})+B*{p}':shortest=1,format=yuv420p[out]"


def filter_graph(total,start,frames):
    return ("[0:v]fps=25,setsar=1,format=yuv420p[a];"
            "[1:v]fps=25,setsar=1,format=yuv420p[b];"+_blend(total,start,frames))


def endpoint_graph(previous_frames,total,start,frames):
    """Use decoded last/first frames of neighboring rendered speech segments."""
    if type(previous_frames) is not int or not 1<=previous_frames<=251:
        raise ValueError('Invalid previous speech frame count')
    tail=previous_frames-1
    # Rendered segments already have exact 25 fps frame counts. No resampling
    # before selection; loop a single frame and explicitly reset timestamps.
    hold='loop=loop=-1:size=1:start=0,setpts=N/(25*TB),setsar=1,format=yuv420p'
    return (f'[0:v]trim=start_frame={tail}:end_frame={previous_frames},setpts=PTS-STARTPTS,{hold}[a];'
            f'[1:v]trim=start_frame=0:end_frame=1,setpts=PTS-STARTPTS,{hold}[b];'+_blend(total,start,frames))
