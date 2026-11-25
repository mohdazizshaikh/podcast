"""Synthetic neural studio compose orchestration with real media, no model."""
import io
import shutil
import wave
import pytest
from PIL import Image, ImageDraw
from podcast_gpt import studio_neural as sn, studio_cache, render_history
from podcast_gpt.render_progress import RenderStopped

pytestmark=pytest.mark.skipif(not (shutil.which('ffmpeg') and shutil.which('ffprobe')),reason='FFmpeg and ffprobe required')

@pytest.mark.parametrize('fmt,layout,transition,scenario',[
    ('square','spotlight','match-gentle','resume'),
    ('vertical','grid','quick','resume'),
    ('landscape','grid','cut','stop-mux'),
    ('square','spotlight','match-quick','stop-commit'),
    ('square','grid','gentle','changed'),
    ('landscape','spotlight','match-gentle','ordinary'),
])
def test_neural_compose(tmp_path,monkeypatch,fmt,layout,transition,scenario):
    folder=tmp_path/'project';folder.mkdir();dest=folder/'audio';dest.mkdir()
    portraits={}
    for i in (1,2):
        im=Image.new('RGB',(144,160),(60*i,80,150))
        ImageDraw.Draw(im).rectangle((25,35,100,120),fill=(200,160,20*i))
        buf=io.BytesIO();im.save(buf,format='PNG');portraits[i]=buf.getvalue()
    monkeypatch.setattr(sn,'_portraits',lambda *a:(portraits,{'A':1,'B':2}))
    timeline={'sample_rate':16000,'total_frames':21760,'measured_audio_seconds':1.36,'rows':[
        {'turn_id':'0001','speaker':'A','start_frame':0,'speech_end_frame':7680,'pause_frames':8320,'end_frame':16000},
        {'turn_id':'0002','speaker':'B','start_frame':16000,'speech_end_frame':21760,'pause_frames':0,'end_frame':21760}]}
    rows=[{'id':'0001','turn_id':'0001','speaker':'A','start_frame':0,'end_frame':7680},
          {'id':'0002','turn_id':'0002','speaker':'B','start_frame':0,'end_frame':5760}]
    turns=[{'text':'Synthetic speaker one'},{'text':'Synthetic speaker two'}]
    plan=sn.export.frame_plan(timeline,rows)
    assert [row['frames'] for row in plan]==[12,13,9]
    done={};inputs={}
    for cid in ('0001','0002'):
        clip=dest/sn.neural.FOLDER/cid/'face.mp4';clip.parent.mkdir(parents=True)
        sn.media.cmd(['ffmpeg','-nostdin','-v','error','-f','lavfi','-i','testsrc2=s=144x160:r=25','-frames:v','12','-c:v','libx264','-threads','1','-pix_fmt','yuv420p',str(clip)],timeout=30)
        done[cid]={'mp4_sha256':sn.source.digest(clip)};inputs[clip]=sn.source.digest(clip)
    wav=dest/sn.master.FOLDER/sn.master.WAV;wav.parent.mkdir()
    with wave.open(str(wav),'wb') as out:
        out.setnchannels(1);out.setsampwidth(2);out.setframerate(16000)
        out.writeframes(b'\x00\x02\x00\xfe'*(timeline['total_frames']//2))
    inputs[wav]=sn.source.digest(wav)
    binding={'video_format':fmt,'test_fixture_only':True,'listener_motion':'breathe','studio_settings_sha256':'a'*64}
    if transition!='cut':binding['transition']=transition
    settings={'layout':layout,'listener_motion':'breathe','camera':'continuous-breathe','transition':transition}
    calls=[]
    def context(root,pid,*,allow_fixture):
        assert allow_fixture is True
        calls.append(1);current={**binding}
        if scenario=='changed' and len(calls)>1:current['studio_settings_sha256']='b'*64
        return folder,dest,timeline,turns,None,rows,done,current,settings,None
    monkeypatch.setattr(sn.projects,'project',lambda *a:folder)
    monkeypatch.setattr(sn,'_context',context)
    output=dest/sn.FOLDER;events=[];stop=[False]
    def report(event):
        events.append(event)
        assert (folder/sn.projects.LOCK).is_file()
        if scenario=='resume' and event.get('verified_frames')==12:stop[0]=True
        if scenario=='stop-mux' and event['action']=='studio-mux-verified':stop[0]=True
        if scenario=='stop-commit' and event['action']=='studio-commit':stop[0]=True
    options={'allow_fixture':True,'resume':scenario=='resume','progress':report,'should_stop':lambda:stop[0]}
    if scenario in ('resume','stop-mux','stop-commit'):
        with pytest.raises(RenderStopped):sn.compose(None,'p',**options)
        assert not output.exists() and not (folder/sn.projects.LOCK).exists()
        assert not list(folder.glob('v4-neural-studio-*'))
        assert not (folder/render_history.FILENAME).exists()
        if scenario!='resume':return
        entries=list((folder/studio_cache.FOLDER).glob('*/segment*'))
        assert len(entries)==1
        saved=sn.source.digest(entries[0]/'video.mp4')
        restored=[];restore=studio_cache.SegmentCache.restore
        def observe(self,index,deps,target,verify):
            result=restore(self,index,deps,target,verify)
            if result:restored.append(sn.source.digest(target))
            return result
        monkeypatch.setattr(studio_cache.SegmentCache,'restore',observe)
        events=[];options.update(progress=events.append,should_stop=lambda:False)
    if scenario=='changed':
        with pytest.raises(ValueError,match='Neural studio inputs changed'):sn.compose(None,'p',**options)
        assert not output.exists() and not (folder/sn.projects.LOCK).exists()
        assert not list(folder.glob('v4-neural-studio-*'))
        return
    result=sn.compose(None,'p',**options)
    if scenario=='resume':assert restored==[saved]
    assert result==sn.inspect(None,'p',allow_fixture=True)
    receipt=result['studio']
    assert receipt['test_fixture_only'] and not receipt['publication_approved'] and not receipt['human_lipsync_approved']
    assert receipt['streams']['decoded_video_frames']==34
    assert abs(receipt['streams']['video_duration']-1.36)<.001
    assert not receipt['inactive_presenters_static'] and receipt['pause_handoff_count']==1
    text=(output/sn.SRT).read_text()
    assert '00:00:00,000 --> 00:00:00,480' in text and '00:00:01,000 --> 00:00:01,360' in text
    assert all(sn.source.digest(p)==sha for p,sha in inputs.items())
    assert not (folder/render_history.FILENAME).exists()
    assert not list(folder.glob('v4-neural-studio-*')) and not (folder/sn.projects.LOCK).exists()
    hashes={p.name:sn.source.digest(p) for p in output.iterdir()};repeat=[]
    assert sn.compose(None,'p',allow_fixture=True,resume=options['resume'],progress=repeat.append)==result
    assert [e['action'] for e in repeat]==['studio-existing-audit','studio-audit-complete']
    assert hashes=={p.name:sn.source.digest(p) for p in output.iterdir()}
    (output/sn.SRT).write_text('changed',encoding='utf-8')
    with pytest.raises(ValueError,match='Neural studio subtitles differ'):sn.inspect(None,'p',allow_fixture=True)
