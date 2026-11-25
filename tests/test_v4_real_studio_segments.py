"""Real synthetic FFmpeg segment composition; no model or approval claims."""
import io
import json
import shutil
from pathlib import Path

import pytest
from PIL import Image, ImageDraw
from podcast_gpt import studio_neural as sn, studio_cache, render_history
from podcast_gpt.render_progress import RenderProgress, RenderStopped

pytestmark=pytest.mark.skipif(not (shutil.which('ffmpeg') and shutil.which('ffprobe')),reason='FFmpeg and ffprobe required')


@pytest.mark.parametrize('fmt,layout,count,listeners,camera,transition',[
    ('landscape','focus',1,'static','fixed','cut'),
    ('landscape','grid',3,'drift','continuous-drift','quick'),
    ('vertical','spotlight',3,'breathe','continuous-breathe','match-gentle'),
    ('square','spotlight',10,'drift','continuous-drift','match-quick'),
    ('vertical','grid',10,'breathe','push-in','gentle'),
    ('landscape','spotlight',10,'breathe','continuous-breathe','match-gentle'),
])
def test_real_segments_and_resume(tmp_path,monkeypatch,fmt,layout,count,listeners,camera,transition):
    portraits={}
    for i in range(1,count+1):
        im=Image.new('RGB',(144,160),(20*i,80,150));draw=ImageDraw.Draw(im)
        draw.rectangle((25,35,100,120),fill=(200,160,20*i))
        draw.line((0,0,143,159),fill='white',width=4)
        b=io.BytesIO();im.save(b,format='PNG');portraits[i]=b.getvalue()
    speakers={f'S{i}':i for i in portraits}
    monkeypatch.setattr(sn,'_portraits',lambda *args:(portraits,speakers))
    second='S'+str(count)
    plan=[{'kind':'speech','id':'0001','turn_id':'0001','speaker':'S1','frames':12},
          {'kind':'pause','id':'0001','turn_id':'0001','speaker':'S1','frames':13},
          {'kind':'speech','id':'0002','turn_id':'0002','speaker':second,'frames':9}]
    dest=tmp_path/'audio';done={}
    for cid in ('0001','0002'):
        clip=dest/sn.neural.FOLDER/cid/'face.mp4';clip.parent.mkdir(parents=True)
        sn.media.cmd(['ffmpeg','-nostdin','-v','error','-f','lavfi','-i','testsrc2=s=144x160:r=25',
                      '-frames:v','12','-c:v','libx264','-threads','1','-pix_fmt','yuv420p',str(clip)],timeout=30)
        done[cid]={'mp4_sha256':sn.source.digest(clip)}
    binding={'video_format':fmt};settings={'layout':layout,'listener_motion':listeners,'camera':camera,'transition':transition}
    cache=studio_cache.SegmentCache(tmp_path,{'binding':binding,'settings':settings},plan,'synthetic-test')
    first=tmp_path/'first';first.mkdir();second_dir=tmp_path/'second';second_dir.mkdir()
    events=[]
    tracker=RenderProgress(plan,events.append,lambda:bool(events and events[-1]['verified_frames']>=12))
    tracker.begin()
    with pytest.raises(RenderStopped):
        sn._segments(None,dest,None,done,binding,settings,None,plan,first,tracker=tracker,cache=cache)
    assert len(list(cache.path.glob('segment*')))==1
    saved=first/'segment00000.mp4';assert sn.export._video_frames(saved)==12
    saved_hash=sn.source.digest(saved);shutil.rmtree(first)
    timing=render_history.Timing('neural-studio',fmt,True)
    tracker=RenderProgress(plan);tracker.begin()
    listing=sn._segments(None,dest,None,done,binding,settings,None,plan,second_dir,tracker=tracker,cache=cache,timing=timing)
    stats=timing.finish(34)
    assert (stats['restored_frames'],stats['rendered_frames'])==(12,22)
    assert (stats['restored_units'],stats['rendered_units'])==(1,2)
    assert sn.source.digest(second_dir/'segment00000.mp4')==saved_hash
    assert tracker.count==34 and len(list(cache.path.glob('segment*')))==3
    assert listing.read_text().splitlines()[1:]==[f'file segment{i:05}.mp4' for i in range(3)]
    if transition.startswith('match-'):
        receipt=json.loads((cache.path/'segment000001'/'receipt.json').read_text())
        assert receipt['dependencies']==[sn.source.digest(second_dir/f'segment{i:05}.mp4') for i in (0,2)]
    output=tmp_path/'combined.mp4'
    sn.media.cmd(['ffmpeg','-nostdin','-v','error','-f','concat','-safe','1','-i',str(listing),'-c','copy',str(output)],timeout=60)
    assert sn.export._video_frames(output)==34
    stream=json.loads(sn.media.cmd(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,codec_name,pix_fmt','-of','json',str(output)],timeout=30).stdout)['streams'][0]
    assert (stream['width'],stream['height'])==sn.preview.SIZES[fmt]
    assert stream['codec_name']=='h264' and stream['pix_fmt']=='yuv420p'
