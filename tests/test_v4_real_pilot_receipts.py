"""Real encoded clip receipt scans and pilot review recording; synthetic only."""
import shutil
from pathlib import Path
import pytest
from podcast_gpt import v4_neural as n, v4_export as export, source

pytestmark=pytest.mark.skipif(not (shutil.which('ffmpeg') and shutil.which('ffprobe')),reason='FFmpeg and ffprobe required')

@pytest.fixture(scope='module')
def encoded(tmp_path_factory):
    path=tmp_path_factory.mktemp('pilot-video')/'face.mp4'
    n.media.cmd(['ffmpeg','-nostdin','-v','error','-f','lavfi','-i','testsrc2=s=256x256:r=25','-f','lavfi','-i','sine=frequency=440:sample_rate=16000','-t','1','-c:v','libx264','-threads','1','-pix_fmt','yuv420p','-c:a','aac',str(path)],timeout=60)
    return path,n._decode(path,{'start_frame':0,'end_frame':16000})

@pytest.fixture
def setup(tmp_path,monkeypatch,encoded):
    dest=tmp_path/'audio';dest.mkdir();(dest/n.FOLDER).mkdir()
    rows=[{'id':'0001-01','turn_id':'0001','speaker':'A','start_frame':0,'end_frame':16000,'pcm_sha256':'a'*64}]
    targets=[rows[0]['id']];seal={'video_format':'square','schema':1}
    binding={'preview_inputs':seal,'chunk_plan_sha256':source.json_digest(rows),'pilot_ids':targets}
    clip=dest/n.FOLDER/targets[0]/'face.mp4';clip.parent.mkdir();shutil.copyfile(encoded[0],clip)
    receipt={'schema':1,'binding':binding,'chunk':rows[0],'model_sha256':'b'*64,'mp4_sha256':source.digest(clip),'streams':encoded[1],'test_fixture_only':True,'human_lipsync_approved':False}
    path=clip.parent/'receipt.json';source.atomic_json(path,receipt,new=True)
    timeline={'sample_rate':16000,'total_frames':16000,'rows':[{'turn_id':'0001','speaker':'A','start_frame':0,'speech_end_frame':16000,'pause_frames':0,'end_frame':16000}]}
    monkeypatch.setattr(n.projects,'project',lambda *a:tmp_path)
    monkeypatch.setattr(n,'_context',lambda *a:(tmp_path,dest,binding,rows,targets))
    monkeypatch.setattr(export.v4_preview,'_context',lambda *a:(tmp_path,dest,timeline,[{'text':'Synthetic'}],{},seal))
    return dest,binding,rows,targets,clip,path

@pytest.mark.parametrize('damage',['schema-bool','schema-float','binding-bool','chunk-bool','chunk-float','stream-float','stream-bool','model-hash','fixture-int','approved-int','video-hash','extra-field','missing-field','video-bytes','extra-file','missing-file'])
def test_scan_rejects(setup,damage):
    dest,binding,rows,targets,clip,path=setup
    saved=source.read_json(path)
    if damage=='schema-bool':saved['schema']=True
    elif damage=='schema-float':saved['schema']=1.0
    elif damage=='binding-bool':saved['binding']['preview_inputs']['schema']=True
    elif damage=='chunk-bool':saved['chunk']['start_frame']=False
    elif damage=='chunk-float':saved['chunk']['end_frame']=16000.0
    elif damage=='stream-float':saved['streams']['width']=256.0
    elif damage=='stream-bool':saved['streams']['duration']=True
    elif damage=='model-hash':saved['model_sha256']='B'*64
    elif damage=='fixture-int':saved['test_fixture_only']=1
    elif damage=='approved-int':saved['human_lipsync_approved']=0
    elif damage=='video-hash':saved['mp4_sha256']='c'*64
    elif damage=='extra-field':saved['extra']=0
    elif damage=='missing-field':del saved['streams']
    elif damage=='video-bytes':clip.write_bytes(b'changed')
    elif damage=='extra-file':(clip.parent/'extra').write_text('extra')
    else:clip.unlink()
    source.atomic_json(path,saved)
    with pytest.raises(ValueError):n._scan(dest,binding,rows)

@pytest.mark.parametrize('damage',['schema-bool','schema-float','binding-bool','unreviewed','missing-criterion','ack','stale-clip','pass','fail'])
def test_record_gate(setup,damage):
    dest,binding,rows,targets,clip,path=setup
    assert n.inspect(None,'p')['pilot_review_status']=='UNREVIEWED'
    template=Path(n.template(None,'p')['template_path']);value=source.read_json(template)
    for row in value['observations'].values():
        for key in row:row[key]='PASS'
    ack=n.REVIEW_ACK
    if damage=='schema-bool':value['schema']=True
    elif damage=='schema-float':value['schema']=1.0
    elif damage=='binding-bool':value['binding']['source']['preview_inputs']['schema']=True
    elif damage=='unreviewed':value['observations'][targets[0]]['lip_sync']='UNREVIEWED'
    elif damage=='missing-criterion':del value['observations'][targets[0]]['lip_sync']
    elif damage=='ack':ack='wrong'
    elif damage=='stale-clip':
        saved=source.read_json(path);saved['model_sha256']='c'*64;source.atomic_json(path,saved)
    elif damage=='fail':value['observations'][targets[0]]['lip_sync']='FAIL'
    source.atomic_json(template,value)
    review=dest/n.FOLDER/n.REVIEW
    if damage not in ('pass','fail'):
        with pytest.raises(ValueError):n.record(None,'p',acknowledgment=ack)
        assert not review.exists()
    else:
        state=n.record(None,'p',acknowledgment=ack)
        assert state['batch_unlocked'] is (damage=='pass')
        assert state['test_fixture_only'] and not state['publication_approved']
        assert n.inspect(None,'p')==state
        before=source.digest(review)
        with pytest.raises(ValueError,match='overwritten'):n.record(None,'p',acknowledgment=n.REVIEW_ACK)
        assert source.digest(review)==before
        if damage=='pass':
            with pytest.raises(ValueError,match='fixture'):export._context(None,'p')
            assert export._context(None,'p',allow_fixture=True)[-1]['test_fixture_only']
            saved=source.read_json(review);saved['binding']['source']['preview_inputs']['schema']=True;source.atomic_json(review,saved)
            with pytest.raises(ValueError,match='pilot review'):n.inspect(None,'p')
        else:
            with pytest.raises(ValueError,match='pilots'):export._context(None,'p',allow_fixture=True)
    assert not (dest.parent/n.projects.LOCK).exists()

@pytest.mark.parametrize('change',['model','fixture'])
def test_mixed_clip_sets(setup,change):
    dest,binding,rows,targets,clip,path=setup
    row={**rows[0],'id':'0002-01','turn_id':'0002'};rows.append(row)
    new=clip.parent.parent/row['id'];new.mkdir();shutil.copyfile(clip,new/'face.mp4')
    saved=source.read_json(path);saved['chunk']=row
    if change=='model':saved['model_sha256']='c'*64
    else:saved['test_fixture_only']=False
    source.atomic_json(new/'receipt.json',saved,new=True)
    with pytest.raises(ValueError,match='Mixed model'):n._scan(dest,binding,rows)


def test_scan_cache(setup,monkeypatch):
    dest,binding,rows,targets,clip,path=setup
    cache={};done=n._scan(dest,binding,rows,cache=cache)
    assert len(done)==1 and len(cache)==1
    def forbidden(*a):pytest.fail('Repeated decode despite verified cache')
    monkeypatch.setattr(n,'_decode',forbidden)
    assert n._scan(dest,binding,rows,cache=cache)==done
    clip.write_bytes(b'tampered')
    with pytest.raises(ValueError,match='hash'):n._scan(dest,binding,rows,cache=cache)
