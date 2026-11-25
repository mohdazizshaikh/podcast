"""Exact mixed scene partitioning; normalized frame indices, never timestamp guesses."""
from .render_progress import mixed_scenes

MAX_FRAMES=1500


def chunks(plan,limit=MAX_FRAMES):
    if type(limit) is not int or not 1<=limit<=MAX_FRAMES:
        raise ValueError('Invalid mixed cache chunk limit')
    result=[]
    for kind,count in mixed_scenes(plan):
        if count>100_000_000:raise ValueError('Mixed scene too long')
        for start in range(0,count,limit):
            result.append({'kind':kind,'start':start,'frames':min(limit,count-start)})
    return result


def filter_graph(start,frames):
    if type(start) is not int or type(frames) is not int or start<0 or not 1<=frames<=MAX_FRAMES or start+frames>100_000_000:
        raise ValueError('Invalid mixed cache chunk range')
    return ('fps=25,setsar=1,tpad=stop_mode=clone:stop_duration=1,format=yuv420p,'
            f'trim=start_frame={start}:end_frame={start+frames},setpts=PTS-STARTPTS,fps=25')
