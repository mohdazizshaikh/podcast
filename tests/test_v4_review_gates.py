"""Receipt and export gate regressions; source/media context boundaries are fixtures."""
import pytest
from podcast_gpt import source, v4_neural as neural, v4_export as export, v4_mixed_video as mixed, studio_neural as studio


def pilot_fixture(tmp_path,monkeypatch,fixture=True):
    dest=tmp_path/'audio';dest.mkdir();(dest/neural.FOLDER).mkdir()
    timeline={'sample_rate':16000,'total_frames':16000,'rows':[{'turn_id':'0001','speaker':'A','start_frame':0,'speech_end_frame':16000,'pause_frames':0,'end_frame':16000}]}
    rows=[{'id':'0001-01','turn_id':'0001','speaker':'A','start_frame':0,'end_frame':16000}]
    targets=['0001-01'];seal={'video_format':'square'};binding={'preview_inputs':seal}
    done={targets[0]:{'test_fixture_only':fixture,'mp4_sha256':'a'*64}}
    obs={targets[0]:{k:'PASS' for k in neural.CRITERIA}}
    receipt={'schema':1,'binding':neural._pilot_binding(binding,targets,done),'observations':obs,'observations_sha256':source.json_digest(obs),'acknowledgment':neural.REVIEW_ACK}
    monkeypatch.setattr(neural,'_context',lambda *a:(tmp_path,dest,binding,rows,targets))
    monkeypatch.setattr(neural,'_scan',lambda *a:done)
    monkeypatch.setattr(export.v4_preview,'_context',lambda *a:(tmp_path,dest,timeline,[{'text':'test'}],{},seal))
    return dest,timeline,rows,targets,binding,done,receipt


@pytest.mark.parametrize('targets',[[],['a','a'],[''],[None],[1],{},'a'])
def test_invalid_pilot_targets(targets):
    with pytest.raises(ValueError,match='pilot target'):neural._pilot_binding({},targets,{})
    with pytest.raises(ValueError,match='pilot target'):neural._validate_observations({},targets)


@pytest.mark.parametrize('saved',[None,{}, {'observations':{}},{'observations':{'a':{}}},{'observations':{'a':None}},{'observations':{'a':{'lip_sync':'PASS'}}},{'observations':[]}])
def test_no_vacuous_pass(saved):
    assert neural._passed(saved) is False


@pytest.mark.parametrize('schema',[True,False,1.0,'1',0,None])
def test_pilot_schema(tmp_path,monkeypatch,schema):
    dest,_,_,_,_,_,receipt=pilot_fixture(tmp_path,monkeypatch)
    receipt['schema']=schema
    source.atomic_json(dest/neural.FOLDER/neural.REVIEW,receipt,new=True)
    with pytest.raises(ValueError,match='pilot review'):export._context(None,'p',allow_fixture=True)


@pytest.mark.parametrize('override',[1,0,'yes','false',None,[],{}])
def test_fixture_override_type(override):
    with pytest.raises(ValueError,match='boolean'):export._context(None,'p',allow_fixture=override)


@pytest.mark.parametrize('fixture',[True,False])
@pytest.mark.parametrize('allow',[True,False])
def test_fixture_export(tmp_path,monkeypatch,fixture,allow):
    dest,_,_,_,_,_,receipt=pilot_fixture(tmp_path,monkeypatch,fixture)
    source.atomic_json(dest/neural.FOLDER/neural.REVIEW,receipt,new=True)
    if fixture and not allow:
        with pytest.raises(ValueError,match='fixture'):export._context(None,'p',allow_fixture=allow)
    else:
        assert export._context(None,'p',allow_fixture=allow)[-1]['test_fixture_only'] is fixture


@pytest.mark.parametrize('damage',['missing','fail','unreviewed','binding','hash','ack','clip','incomplete'])
def test_pilot_gate(tmp_path,monkeypatch,damage):
    dest,_,_,_,_,done,receipt=pilot_fixture(tmp_path,monkeypatch)
    if damage in ('fail','unreviewed'):
        receipt['observations']['0001-01']['lip_sync']='FAIL' if damage=='fail' else 'UNREVIEWED'
        receipt['observations_sha256']=source.json_digest(receipt['observations'])
    elif damage=='binding':receipt['binding']={}
    elif damage=='hash':receipt['observations_sha256']='f'*64
    elif damage=='ack':receipt['acknowledgment']='yes'
    elif damage=='clip':done['0001-01']['mp4_sha256']='b'*64
    elif damage=='incomplete':done.clear()
    if damage!='missing':source.atomic_json(dest/neural.FOLDER/neural.REVIEW,receipt,new=True)
    with pytest.raises(ValueError):export._context(None,'p',allow_fixture=True)


def observations(record,timeline,kind):
    v=mixed._review_value(record,timeline,kind)
    for k in v['criteria']:v['criteria'][k]='PASS'
    for k in v['turns']:
        if kind=='mix':v['turns'][k]='PASS'
        else:v['turns'][k]={c:'PASS' for c in mixed.VIDEO_CRITERIA}
    return v


@pytest.mark.parametrize('kind',['mix','video','studio'])
@pytest.mark.parametrize('schema',[True,False,1.0,'1',0,None])
def test_mixed_schema(kind,schema):
    timeline={'rows':[{'turn_id':'a'}]};record={'sha':'a'}
    v=observations(record,timeline,kind);v['schema']=schema
    with pytest.raises(ValueError,match='binding'):mixed._validate(v,record,timeline,kind)


@pytest.mark.parametrize('kind',['mix','video','studio'])
@pytest.mark.parametrize('ids',[[],['a','a'],[''],[None],[1]])
def test_mixed_review_turns(kind,ids):
    with pytest.raises(ValueError,match='turn set'):mixed._review_value({}, {'rows':[{'turn_id':i} for i in ids]},kind)


@pytest.mark.parametrize('kind',['mix','video','studio'])
def test_review_roundtrip(tmp_path,kind):
    timeline={'rows':[{'turn_id':'a'},{'turn_id':'b'}]};record={'sha':'a'}
    v=observations(record,timeline,kind);ack={'mix':mixed.MIX_ACK,'video':mixed.VIDEO_ACK,'studio':mixed.STUDIO_ACK}[kind]
    path=mixed._review_file(tmp_path,kind)
    assert mixed._read_review(tmp_path,record,timeline,kind)==(None,False)
    data={'observations':v,'sha256':source.json_digest(v),'acknowledgment':ack}
    source.atomic_json(path,data,new=True)
    assert mixed._read_review(tmp_path,record,timeline,kind)==(data,True)
    with pytest.raises(ValueError,match='binding'):mixed._read_review(tmp_path,{'sha':'b'},timeline,kind)
    v['criteria'][next(iter(v['criteria']))]='FAIL';data['sha256']=source.json_digest(v)
    source.atomic_json(path,data)
    assert mixed._read_review(tmp_path,record,timeline,kind)==(data,False)


@pytest.mark.parametrize('is_studio',[False,True])
@pytest.mark.parametrize('state',['missing','fail','pass','stale','fixture-denied','base-mismatch'])
def test_mixed_context(tmp_path,monkeypatch,is_studio,state):
    dest,timeline,rows,_,_,_,pilot=pilot_fixture(tmp_path,monkeypatch)
    source.atomic_json(dest/neural.FOLDER/neural.REVIEW,pilot,new=True)
    record={'intro_frames':0,'outro_frames':0,'speech_offset_frames':0,'speech_and_pauses_frames':16000,'total_frames':16000}
    monkeypatch.setattr(mixed,'_mix_context',lambda *a:(tmp_path,dest,timeline,record))
    v=observations(record,timeline,'mix')
    if state=='fail':v['turns']['0001']='FAIL'
    if state=='stale':v['candidate_sha256']='f'*64
    if state!='missing':source.atomic_json(dest/mixed.MIX_REVIEW,{'observations':v,'sha256':source.json_digest(v),'acknowledgment':mixed.MIX_ACK},new=True)
    def base_context(root,pid,*,allow_fixture):
        f,d,t,turns,cast,rs,done,bound=export._context(root,pid,allow_fixture=allow_fixture)
        if state=='base-mismatch':d=tmp_path/'other'
        return f,d,t,turns,cast,rs,done,bound
    if is_studio:
        def studio_context(*a,**kw):
            f,d,t,turns,cast,rs,done,bound=base_context(*a,**kw)
            return f,d,t,turns,cast,rs,done,{'video_format':'square','test_fixture_only':bound['test_fixture_only']},{},None
        monkeypatch.setattr(studio,'_context',studio_context)
        monkeypatch.setattr(studio,'_audit',lambda *a:{'test_fixture_only':True})
    else:
        original=export._context
        def other_context(*a,**kw):
            f,d,t,turns,cast,rs,done,bound=original(*a,**kw)
            return f,tmp_path/'other' if state=='base-mismatch' else d,t,turns,cast,rs,done,bound
        monkeypatch.setattr(export,'_context',other_context)
        monkeypatch.setattr(export,'_audit',lambda *a:{'test_fixture_only':True})
    if state=='pass':
        ctx=mixed._context(None,'p',studio=is_studio,allow_fixture=True)
        assert ctx[-1]['test_fixture_only'] and ctx[-1]['mix_review_sha256']==source.json_digest(source.read_json(dest/mixed.MIX_REVIEW))
        assert ctx[-1].get('variant')==('neural-studio' if is_studio else None)
    else:
        with pytest.raises(ValueError):mixed._context(None,'p',studio=is_studio,allow_fixture=state!='fixture-denied')
