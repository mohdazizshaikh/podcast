"""Actual synthetic mixed-media encoding and auditing, without model inference."""
import math
import shutil
import struct
import wave
import pytest
from podcast_gpt import v4_mixed_video as mv, mixed_chunks, studio_cache

pytestmark=pytest.mark.skipif(not (shutil.which('ffmpeg') and shutil.which('ffprobe')),reason='FFmpeg and ffprobe required')

@pytest.mark.parametrize('fmt,studio,intro,speech,outro',[
    ('square',False,0,12800,0),
    ('landscape',True,6400,16000,6400),
    ('vertical',False,6719,16319,0),
    ('square',True,6720,16320,0),
    ('vertical',True,0,12800,6400),
    ('landscape',False,6400,12800,6400),
])
def test_encoded_mixed_chunks(tmp_path,fmt,studio,intro,speech,outro):
    timeline={'sample_rate':16000,'total_frames':speech,'rows':[{'start_frame':0,'speech_end_frame':speech}]}
    turns=[{'text':'Synthetic timing test'}]
    record={'intro_frames':intro,'outro_frames':outro,'speech_offset_frames':intro,'speech_and_pauses_frames':speech,'total_frames':intro+speech+outro}
    plan=mv.scene_plan(timeline,record)
    seal={'video_format':fmt,'test_fixture_only':True}
    if studio:seal['variant']='neural-studio'
    base=tmp_path/'base.mp4';w,h=mv.preview.SIZES[fmt]
    mv.media.cmd(['ffmpeg','-nostdin','-v','error','-f','lavfi','-i',f'testsrc2=s={w}x{h}:r=25','-frames:v',str(mv._frames(speech)),'-c:v','libx264','-threads','2','-pix_fmt','yuv420p',str(base)],timeout=60)
    wav=tmp_path/'mix.wav'
    raw=b''.join(struct.pack('<h',round(8000*math.sin(2*math.pi*440*i/16000))) for i in range(record['total_frames']))
    with wave.open(str(wav),'wb') as out:
        out.setnchannels(1);out.setsampwidth(2);out.setframerate(16000);out.writeframes(raw)
    base_sha=mv.source.digest(base);wav_sha=mv.source.digest(wav)
    units=mixed_chunks.chunks(plan,7)
    cache=studio_cache.SegmentCache(tmp_path,seal,units,'synthetic')
    names=[]
    for index,unit in enumerate(units):
        kind,count=unit['kind'],unit['frames']
        target=tmp_path/f'segment{index:06}.mp4'
        if kind=='speech':inputs=['-i',str(base)]
        else:
            card=tmp_path/(kind+'.png')
            if not card.exists():mv._card(card,(w,h),kind.upper())
            inputs=['-loop','1','-framerate','25','-i',str(card)]
        mv.media.cmd(['ffmpeg','-nostdin','-hide_banner','-v','error',*inputs,'-map','0:v:0','-an','-vf',mixed_chunks.filter_graph(unit['start'],count),'-frames:v',str(count),'-c:v','libx264','-threads','2','-preset','veryfast','-crf','23',str(target)],timeout=120)
        assert mv.export._video_frames(target)==count
        cache.save(index,[],target)
        sha=mv.source.digest(target);target.unlink()
        assert cache.restore(index,[],target,mv.export._video_frames)
        assert mv.source.digest(target)==sha
        names.append(target.name)
    listing=tmp_path/'scenes.ffconcat';listing.write_text('ffconcat version 1.0\n'+''.join('file '+n+'\n' for n in names),encoding='ascii')
    out=tmp_path/(mv.STUDIO_FOLDER if studio else mv.FOLDER);out.mkdir()
    mv.media.cmd(['ffmpeg','-nostdin','-hide_banner','-v','error','-f','concat','-safe','1','-i',str(listing),'-i',str(wav),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-ar','48000','-b:a','160k','-movflags','+faststart',str(out/mv.VIDEO)],timeout=120)
    streams=mv._decode(out/mv.VIDEO,record,plan,seal)
    assert streams['decoded_video_frames']==plan['total_video_frames']
    assert abs(streams['video_duration']-plan['total_video_frames']/25)<.001
    assert abs(streams['audio_duration']-record['total_frames']/16000)<.03
    (out/mv.SRT).write_bytes(mv.shifted_subtitles(timeline,turns,intro))
    receipt=mv._receipt(out,plan,seal,streams)
    mv.source.atomic_json(out/mv.RECEIPT,receipt,new=True)
    assert receipt==mv._audit(tmp_path,timeline,turns,record,plan,seal)
    assert receipt['test_fixture_only'] and not receipt['publication_approved']
    assert mv.media.srt_stamp(intro/16000) in (out/mv.SRT).read_text()
    assert mv.source.digest(base)==base_sha and mv.source.digest(wav)==wav_sha
    (out/mv.SRT).write_text('changed',encoding='utf-8')
    with pytest.raises(ValueError,match='Mixed subtitle'):mv._audit(tmp_path,timeline,turns,record,plan,seal)
