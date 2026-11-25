import os
import pytest
from podcast_gpt import cache_retention as r, studio_cache as c, studio_cache_admin as a


def populate(folder, n):
    keys=[]
    for i in range(n):
        obj=c.SegmentCache(folder,{'variant':i},[{'frames':3}],'renderer')
        v=folder/'input.mp4';v.write_bytes(b'v'*128)
        obj.save(0,[],v)
        for p in (obj.path/'segment000000').iterdir():
            os.utime(p,ns=(1000000000*(i+1),1000000000*(i+1)))
        keys.append(obj.key)
    return keys

@pytest.mark.parametrize('n',[1,2,3,5])
@pytest.mark.parametrize('keep',[0,1,2,5])
@pytest.mark.parametrize('protect',[False,True])
def test_plan_apply(tmp_path,n,keep,protect):
    keys=populate(tmp_path,n)
    protected=keys[:1] if protect else []
    before=a.inventory(tmp_path)
    p=r.plan(tmp_path,0,keep,protected)
    retained=set(keys[max(0,n-keep):])|set(protected)
    assert p['protected_namespaces']==sorted(retained)
    assert [x['namespace'] for x in p['delete']]==[k for k in keys if k not in retained]
    assert a.inventory(tmp_path)==before
    result=r.apply(tmp_path,0,keep,protected,p['plan_sha256'],acknowledgment=r.ACK)
    after=a.inventory(tmp_path)
    assert {x['namespace'] for x in after['namespaces']}==retained
    assert result['deleted_logical_bytes']==before['logical_bytes']-after['logical_bytes']
    assert result['remaining_logical_bytes']==after['logical_bytes']
    assert result['budget_met']==(not retained)
    assert (tmp_path/'input.mp4').read_bytes()==b'v'*128

@pytest.mark.parametrize('budget',[1,2,100])
@pytest.mark.parametrize('keep',[0,1,128])
def test_under_budget(tmp_path,budget,keep):
    populate(tmp_path,3)
    p=r.plan(tmp_path,budget,keep)
    assert p['delete']==[] and p['budget_met']
    assert r.apply(tmp_path,budget,keep,[],p['plan_sha256'],acknowledgment=r.ACK)['removed']==[]

@pytest.mark.parametrize('budget',[-1,True,1.5,'1',None,1048577])
def test_bad_budget(budget):
    with pytest.raises(ValueError):r.policy(budget,1,[])

@pytest.mark.parametrize('keep',[-1,True,1.5,'1',None,129])
def test_bad_keep(keep):
    with pytest.raises(ValueError):r.policy(1,keep,[])

@pytest.mark.parametrize('protected',[{},'a'*64,[True],['../x'],['a'*64]*2,['a'*64]*129])
def test_bad_protected(protected):
    with pytest.raises(ValueError):r.policy(1,1,protected)

@pytest.mark.parametrize('change',['add','modify','policy','digest','ack','unknown'])
def test_stale(tmp_path,change):
    keys=populate(tmp_path,3);p=r.plan(tmp_path,0,1,[])
    keep=1;digest=p['plan_sha256'];ack=r.ACK;protected=[]
    if change=='add':c.SegmentCache(tmp_path,'other',[{'frames':3}],'renderer')
    elif change=='modify':(tmp_path/c.FOLDER/keys[0]/'segment000000'/'video.mp4').write_bytes(b'changed')
    elif change=='policy':keep=0
    elif change=='digest':digest='f'*64
    elif change=='ack':ack='yes'
    else:protected=['f'*64]
    with pytest.raises(ValueError):r.apply(tmp_path,0,keep,protected,digest,acknowledgment=ack)
    assert all((tmp_path/c.FOLDER/k).is_dir() for k in keys)


def test_partial_budget(tmp_path):
    keys=populate(tmp_path,3)
    for i,k in enumerate(keys):
        video=tmp_path/c.FOLDER/k/'segment000000'/'video.mp4'
        video.write_bytes(b'x'*600000)
        os.utime(video,ns=(1000000000*(i+1),1000000000*(i+1)))
    p=r.plan(tmp_path,1,0)
    assert [x['namespace'] for x in p['delete']]==keys[:2]
    assert 600000<=p['remaining_logical_bytes']<r.MIB


def test_empty(tmp_path):
    p=r.plan(tmp_path,0)
    assert p['budget_met'] and p['delete']==[]
    assert not (tmp_path/c.FOLDER).exists()


def test_equal_timestamps(tmp_path):
    keys=populate(tmp_path,3)
    for p in (tmp_path/c.FOLDER).glob('*/*/*'):os.utime(p,ns=(1000000000,1000000000))
    assert r.plan(tmp_path,0,1)['protected_namespaces']==[max(keys)]
