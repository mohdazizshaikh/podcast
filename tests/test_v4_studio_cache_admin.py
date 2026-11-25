import os
from pathlib import Path
import pytest
from podcast_gpt import studio_cache as c, studio_cache_admin as a


def populate(folder, n=2, binding='a'):
    obj=c.SegmentCache(folder, binding, [{'frames':3}]*max(1,n),'renderer')
    src=folder/'source.mp4';src.write_bytes(b'video')
    for i in range(n):obj.save(i,[],src)
    return obj

@pytest.mark.parametrize('n',[0,1,2,5])
@pytest.mark.parametrize('other',[False,True])
@pytest.mark.parametrize('damage',['none','missing_receipt','missing_video'])
def test_inventory_delete(tmp_path,n,other,damage):
    obj=populate(tmp_path,n)
    if other:second=populate(tmp_path,1,'b')
    if n and damage!='none':
        (obj.path/'segment000000'/('receipt.json' if damage=='missing_receipt' else 'video.mp4')).unlink()
    (tmp_path/'final.mp4').write_bytes(b'final')
    before=a.inventory(tmp_path)
    row=next(r for r in before['namespaces'] if r['namespace']==obj.key)
    assert row['entries']==n
    assert row['complete_pairs']==n-int(n>0 and damage!='none')
    assert row['logical_bytes']==sum(p.stat().st_size for p in obj.path.glob('*/*'))
    assert a.inventory(tmp_path)==before
    result=a.delete_namespace(tmp_path,obj.key,row['snapshot_sha256'],acknowledgment=a.ACK)
    assert result['deleted_entries']==n and not obj.path.exists()
    assert (tmp_path/'source.mp4').read_bytes()==b'video' and (tmp_path/'final.mp4').read_bytes()==b'final'
    assert a.inventory(tmp_path)['namespace_count']==int(other)
    if other:assert second.path.exists()

@pytest.mark.parametrize('change',['video','receipt','new_entry','removed_entry','new_file'])
def test_stale_snapshot(tmp_path,change):
    obj=populate(tmp_path,2);row=a.inventory(tmp_path)['namespaces'][0]
    entry=obj.path/'segment000000'
    if change=='video':(entry/'video.mp4').write_bytes(b'changed')
    elif change=='receipt':(entry/'receipt.json').write_text('{}')
    elif change=='new_entry':(obj.path/'segment000002').mkdir()
    elif change=='removed_entry':(obj.path/'segment000001'/'video.mp4').unlink()
    else:(entry/'extra').touch()
    with pytest.raises(ValueError):a.delete_namespace(tmp_path,obj.key,row['snapshot_sha256'],acknowledgment=a.ACK)
    assert entry.exists()

@pytest.mark.parametrize('key',[None,'','../outside','A'*64,'a'*63,'a'*65,123])
@pytest.mark.parametrize('field',['key','snapshot'])
def test_bad_input(tmp_path,key,field):
    obj=populate(tmp_path);row=a.inventory(tmp_path)['namespaces'][0]
    with pytest.raises(ValueError):a.delete_namespace(tmp_path,key if field=='key' else obj.key,key if field=='snapshot' else row['snapshot_sha256'],acknowledgment=a.ACK)
    assert obj.path.exists()

@pytest.mark.parametrize('ack',[None,True,'','delete'])
def test_ack(tmp_path,ack):
    obj=populate(tmp_path);row=a.inventory(tmp_path)['namespaces'][0]
    with pytest.raises(ValueError):a.delete_namespace(tmp_path,obj.key,row['snapshot_sha256'],acknowledgment=ack)
    assert obj.path.exists()

@pytest.mark.parametrize('where',['base','namespace','entry','video','receipt'])
def test_symlink(tmp_path,where):
    obj=populate(tmp_path);row=a.inventory(tmp_path)['namespaces'][0]
    entry=obj.path/'segment000000'
    p={'base':obj.path.parent,'namespace':obj.path,'entry':entry,'video':entry/'video.mp4','receipt':entry/'receipt.json'}[where]
    dest=tmp_path/'outside';p.rename(dest)
    try:p.symlink_to(dest,target_is_directory=dest.is_dir())
    except OSError:pytest.skip('Symlink unavailable')
    with pytest.raises(ValueError):a.inventory(tmp_path)
    with pytest.raises(ValueError):a.delete_namespace(tmp_path,obj.key,row['snapshot_sha256'],acknowledgment=a.ACK)
    assert dest.exists()

@pytest.mark.parametrize('name',['unknown','segment00000','segment0000000','segmentabcdef'])
def test_unexpected_entries(tmp_path,name):
    obj=populate(tmp_path);(obj.path/name).mkdir()
    with pytest.raises(ValueError):a.inventory(tmp_path)

@pytest.mark.parametrize('limit',[0,1,2])
def test_bound(tmp_path,monkeypatch,limit):
    populate(tmp_path,3)
    monkeypatch.setattr(a,'MAX_ENTRIES',limit)
    with pytest.raises(ValueError):a.inventory(tmp_path)


def test_namespace_limit(tmp_path,monkeypatch):
    populate(tmp_path,1);populate(tmp_path,1,'b')
    monkeypatch.setattr(a,'MAX_NAMESPACES',1)
    with pytest.raises(ValueError):a.inventory(tmp_path)


def test_missing(tmp_path):
    assert a.inventory(tmp_path)==dict(namespaces=[],namespace_count=0,entries=0,logical_bytes=0,content_verified=False,automatic_pruning=False)
    assert not (tmp_path/c.FOLDER).exists()

def test_cli_and_dashboard(tmp_path,monkeypatch):
    from podcast_gpt import cli,web,dashboard_authoring as da
    pid='a'*32;key='b'*64;snapshot='c'*64
    assert cli.parse(['project-studio-cache-inventory','--project-id',pid]).operation=='project-studio-cache-inventory'
    args=cli.parse(['project-studio-cache-delete','--project-id',pid,'--namespace',key,'--snapshot-sha256',snapshot,'--acknowledgment',a.ACK])
    assert args.namespace==key and args.snapshot_sha256==snapshot
    monkeypatch.setattr(a,'inspect',lambda root,pid:{'project_id':pid})
    assert da.run(tmp_path,'studio-cache-inventory',{'project_id':pid})=={'project_id':pid}
    seen=[]
    def remove(root,pid,k,s,*,acknowledgment):
        seen.append((pid,k,s,acknowledgment));return {'deleted':True}
    monkeypatch.setattr(a,'remove',remove)
    data=dict(project_id=pid,namespace=key,snapshot_sha256=snapshot,stopped_processes_and_delete=True)
    with pytest.raises(ValueError):da.run(tmp_path,'studio-cache-delete',data)
    with pytest.raises(ValueError):da.run(tmp_path,'studio-cache-delete',{**data,'stopped_processes_and_delete':1},acknowledgment=da.ACK)
    assert not seen
    assert da.run(tmp_path,'studio-cache-delete',data,acknowledgment=da.ACK)=={'deleted':True}
    assert seen==[(pid,key,snapshot,a.ACK)]
    assert 'v4CacheDeleteConsent' in web.html_page('test')

@pytest.mark.parametrize('operation',['inspect','remove'])
def test_project_lock(tmp_path,monkeypatch,operation):
    from podcast_gpt import projects
    obj=populate(tmp_path);row=a.inventory(tmp_path)['namespaces'][0]
    monkeypatch.setattr(projects,'project',lambda *args:tmp_path)
    with projects.exclusive(tmp_path):
        with pytest.raises(ValueError):
            if operation=='inspect':a.inspect(None,'p')
            else:a.remove(None,'p',obj.key,row['snapshot_sha256'],acknowledgment=a.ACK)
    assert obj.path.exists()
