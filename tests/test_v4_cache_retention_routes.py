import pytest
from podcast_gpt import cli,web,dashboard_authoring as da,cache_retention as r

def test_cli():
    pid='a'*32;key='b'*64;sha='c'*64
    args=cli.parse(['project-studio-cache-prune-plan','--project-id',pid,'--max-mib','2048','--protect',key])
    assert (args.max_mib,args.keep_newest,args.protect)==(2048,1,[key])
    args=cli.parse(['project-studio-cache-prune','--project-id',pid,'--max-mib','2048','--keep-newest','2','--protect',key,'--plan-sha256',sha,'--acknowledgment',r.ACK])
    assert (args.keep_newest,args.plan_sha256,args.acknowledgment)==(2,sha,r.ACK)
    assert 'v4CachePrunePlan' in web.html_page('test')

def test_dashboard_routes(tmp_path,monkeypatch):
    pid='a'*32;key='b'*64;sha='c'*64
    data=dict(project_id=pid,max_mib=2048,keep_newest=2,protected=[key])
    monkeypatch.setattr(r,'inspect',lambda root,p,m,k,pro:{'project_id':p,'policy':r.policy(m,k,pro)})
    assert da.run(tmp_path,'studio-cache-prune-plan',data)['policy']==r.policy(2048,2,[key])
    calls=[]
    def prune(root,p,m,k,pro,s,*,acknowledgment):
        calls.append((p,m,k,pro,s,acknowledgment));return {'removed':[]}
    monkeypatch.setattr(r,'prune',prune)
    request={**data,'plan_sha256':sha,'stopped_processes_and_delete':True}
    with pytest.raises(ValueError):da.run(tmp_path,'studio-cache-prune',request)
    with pytest.raises(ValueError):da.run(tmp_path,'studio-cache-prune',{**request,'stopped_processes_and_delete':1},acknowledgment=da.ACK)
    assert not calls
    assert da.run(tmp_path,'studio-cache-prune',request,acknowledgment=da.ACK)=={'removed':[]}
    assert calls==[(pid,2048,2,[key],sha,r.ACK)]

@pytest.mark.parametrize('operation',['inspect','prune'])
def test_project_lock(tmp_path,monkeypatch,operation):
    from podcast_gpt import projects
    monkeypatch.setattr(projects,'project',lambda *a:tmp_path)
    with projects.exclusive(tmp_path):
        with pytest.raises(ValueError):
            if operation=='inspect':r.inspect(None,'p',0)
            else:r.prune(None,'p',0,1,[],'a'*64,acknowledgment=r.ACK)
