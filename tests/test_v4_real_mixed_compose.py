"""Real mixed compose orchestration with synthetic source context, no model."""
import shutil
import wave
import pytest
from podcast_gpt import v4_mixed_video as mv, studio_neural, studio_cache, mixed_chunks, render_history
from podcast_gpt.render_progress import RenderStopped

pytestmark=pytest.mark.skipif(not (shutil.which('ffmpeg') and shutil.which('ffprobe')),reason='FFmpeg and ffprobe required')

@pytest.mark.parametrize('studio,fmt,scenario',[
    (False,'square','resume'),(True,'vertical','resume'),
    (False,'landscape','stop-mux'),(True,'square','stop-commit'),
    (False,'square','changed'),(True,'landscape','ordinary'),
])
def test_mixed_compose(tmp_path,monkeypatch,studio,fmt,scenario):
    folder=tmp_path/'project';folder.mkdir();dest=folder/'audio';dest.mkdir()
    module=studio_neural if studio else mv.export
    base=dest/module.FOLDER/module.VIDEO;base.parent.mkdir()
    w,h=mv.preview.SIZES[fmt]
    mv.media.cmd(['ffmpeg','-nostdin','-v','error','-f','lavfi','-i',f'testsrc2=s={w}x{h}:r=25','-frames:v','16','-c:v','libx264','-threads','2','-pix_fmt','yuv420p',str(base)],timeout=60)
    intro,speech,outro=2560,10240,3200
    timeline={'sample_rate':16000,'total_frames':speech,'rows':[{'start_frame':0,'speech_end_frame':speech}]}
    turns=[{'text':'Synthetic compose regression'}]
    record={'intro_frames':intro,'outro_frames':outro,'speech_offset_frames':intro,'speech_and_pauses_frames':speech,'total_frames':intro+speech+outro}
    wav=dest/mv.mix.FOLDER/mv.mix.WAV;wav.parent.mkdir()
    with wave.open(str(wav),'wb') as out:
        out.setnchannels(1);out.setsampwidth(2);out.setframerate(16000)
        out.writeframes(b'\x00\x02\x00\xfe'*(record['total_frames']//2))
    plan=mv.scene_plan(timeline,record)
    seal={'video_format':fmt,'test_fixture_only':True,'mix_sha256':mv.source.digest(wav)}
    if studio:seal['variant']='neural-studio'
    calls=[]
    def context(root,pid,*,allow_fixture,studio):
        assert allow_fixture is True
        calls.append(1)
        current={**seal}
        if scenario=='changed' and len(calls)>1:current['mix_sha256']='f'*64
        return folder,dest,timeline,turns,record,plan,current
    monkeypatch.setattr(mv.projects,'project',lambda *a:folder)
    monkeypatch.setattr(mv,'_context',context)
    original_chunks=mixed_chunks.chunks
    monkeypatch.setattr(mixed_chunks,'chunks',lambda p:original_chunks(p,7))
    out=dest/(mv.STUDIO_FOLDER if studio else mv.FOLDER)
    base_sha=mv.source.digest(base);wav_sha=mv.source.digest(wav)
    events=[];stop=[False]
    def report(event):
        events.append(event)
        assert (folder/mv.projects.LOCK).is_file()
        if scenario=='resume' and event.get('verified_frames')==4:stop[0]=True
        if scenario=='stop-mux' and event['action']=='mixed-mux-verified':stop[0]=True
        if scenario=='stop-commit' and event['action']=='mixed-commit':stop[0]=True
    options={'allow_fixture':True,'studio':studio,'resume':scenario=='resume','progress':report,'should_stop':lambda:stop[0]}
    if scenario in ('resume','stop-mux','stop-commit'):
        with pytest.raises(RenderStopped):mv.compose(None,'p',**options)
        assert not out.exists() and not (folder/mv.projects.LOCK).exists()
        assert not list(folder.glob('v4-mixed-*'))
        assert not (folder/render_history.FILENAME).exists()
        if scenario!='resume':return
        entries=list((folder/studio_cache.FOLDER).glob('*/segment*'))
        assert len(entries)==1
        saved=mv.source.digest(entries[0]/'video.mp4')
        restored=[];restore=studio_cache.SegmentCache.restore
        def observe(self,index,deps,target,verify):
            result=restore(self,index,deps,target,verify)
            if result:restored.append(mv.source.digest(target))
            return result
        monkeypatch.setattr(studio_cache.SegmentCache,'restore',observe)
        events=[];options.update(progress=events.append,should_stop=lambda:False)
    if scenario=='changed':
        with pytest.raises(ValueError,match='Mixed inputs changed'):mv.compose(None,'p',**options)
        assert not out.exists() and not (folder/mv.projects.LOCK).exists()
        assert not list(folder.glob('v4-mixed-*'))
        return
    result=mv.compose(None,'p',**options)
    if scenario=='resume':assert restored==[saved]
    assert result==mv.inspect(None,'p',allow_fixture=True,studio=studio)
    receipt=result['export']
    assert receipt['test_fixture_only'] and not receipt['publication_approved']
    assert receipt['streams']['decoded_video_frames']==25
    assert abs(receipt['streams']['video_duration']-1)<.001
    assert '00:00:00,160 --> 00:00:00,800' in (out/mv.SRT).read_text()
    assert mv.source.digest(base)==base_sha and mv.source.digest(wav)==wav_sha
    assert not (folder/render_history.FILENAME).exists()
    assert not list(folder.glob('v4-mixed-*')) and not (folder/mv.projects.LOCK).exists()
    hashes={p.name:mv.source.digest(p) for p in out.iterdir()}
    repeat=[]
    assert mv.compose(None,'p',allow_fixture=True,studio=studio,resume=options['resume'],progress=repeat.append)==result
    assert [e['action'] for e in repeat]==['mixed-existing-audit','mixed-audit-complete']
    assert hashes=={p.name:mv.source.digest(p) for p in out.iterdir()}
