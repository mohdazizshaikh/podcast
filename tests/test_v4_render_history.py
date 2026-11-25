import json
import pytest
from podcast_gpt import render_history as h


def record(variant='neural-studio',fmt='square',resume=False):
    t=[0];timer=h.Timing(variant,fmt,resume,clock=lambda:t[0],wall=lambda:123000000)
    for frames,ms,restored in [(10,40,False),(25,80,resume),(7,20,False)]:
        timer.begin_unit();t[0]+=ms*1000000;timer.unit(frames,restored=restored)
    t[0]+=50000000
    return timer.finish(42)

@pytest.mark.parametrize('variant',h.VARIANTS)
@pytest.mark.parametrize('fmt',h.FORMATS)
@pytest.mark.parametrize('resume',[False,True])
def test_roundtrip(tmp_path,variant,fmt,resume):
    row=record(variant,fmt,resume)
    assert row['rendered_frames']==(17 if resume else 42)
    assert row['restored_ms']==(80 if resume else 0)
    assert row['elapsed_ms']==190
    h.append(tmp_path,row);h.append(tmp_path,row)
    assert h.read(tmp_path)==[row,row]
    group=h.summarize(h.read(tmp_path))[0]
    assert group['runs']==2 and group['rendered_frames']==row['rendered_frames']*2

@pytest.mark.parametrize('field,value', [('variant','bad'),('format','portrait'),('resume',1),('rendered_units',True),('rendered_frames',-1),('elapsed_ms',0),('recorded_unix_ms',None),('restored_ms',1),('restored_frames',1),('rendered_units',43),('extra',1)])
def test_invalid(field,value):
    row=record();row[field]=value
    with pytest.raises(ValueError):h.validate(row)

@pytest.mark.parametrize('bad',[[],{}, {'schema':True,'records':[]},{'schema':1,'records':[{}]}, {'schema':1,'records':[],'extra':1},{'schema':1,'records':[record()]*31}])
def test_corrupt(tmp_path,bad):
    path=tmp_path/h.FILENAME;path.write_text(json.dumps(bad));before=path.read_bytes()
    with pytest.raises(ValueError):h.append(tmp_path,record())
    assert path.read_bytes()==before

@pytest.mark.parametrize('where',['no_start','double_start','wrong_frames','pending','double_finish','invalid_count'])
def test_state(where):
    timer=h.Timing('neural-studio','square',False,clock=lambda:0)
    with pytest.raises(ValueError):
        if where=='no_start':timer.unit(1)
        elif where=='double_start':timer.begin_unit();timer.begin_unit()
        elif where=='pending':timer.begin_unit();timer.finish(0)
        elif where=='invalid_count':timer.begin_unit();timer.unit(True)
        else:
            timer.begin_unit();timer.unit(1)
            if where=='wrong_frames':timer.finish(2)
            else:timer.finish(1);timer.finish(1)


def test_limit(tmp_path):
    for i in range(35):h.append(tmp_path,{**record(),'recorded_unix_ms':i})
    assert [r['recorded_unix_ms'] for r in h.read(tmp_path)]==list(range(5,35))
    assert not list(tmp_path.glob('render-history-*'))


def test_grouping():
    rows=[record(v,f,r) for v in h.VARIANTS for f in h.FORMATS for r in (False,True)]
    assert len(h.summarize(rows))==18
    assert sum(x['runs'] for x in h.summarize(rows+rows))==36


def test_empty(tmp_path):
    assert h.read(tmp_path)==[] and h.summarize([])==[]
    assert not (tmp_path/h.FILENAME).exists()


def test_symlink(tmp_path):
    dest=tmp_path/'original';dest.write_text('private')
    try:(tmp_path/h.FILENAME).symlink_to(dest)
    except OSError:pytest.skip('Symlink unavailable')
    with pytest.raises(ValueError):h.append(tmp_path,record())
    assert dest.read_text()=='private'


def test_auxiliary_failure(tmp_path,caplog):
    path=tmp_path/h.FILENAME;path.write_text('broken')
    timer=h.Timing('mixed-video','square',False,clock=lambda:0);timer.begin_unit();timer.unit(1)
    assert not h.save_completed(tmp_path,timer,1)
    assert path.read_text()=='broken' and 'audited video unchanged' in caplog.text
