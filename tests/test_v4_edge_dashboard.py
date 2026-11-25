import pytest
from podcast_gpt import edge_inventory as inv, v4_edge as edge, dashboard_authoring as author, cli, web, dependency_setup
from test_v4_master_tts import ready

def row(preset,locale,gender="Male"):
    return {"ShortName":preset,"Locale":locale,"Gender":gender}

ROWS=[row("hi-IN-MadhurNeural","hi-IN"),row("en-US-GuyNeural","en-US"),
      row("en-GB-RyanNeural","en-GB"),row("zh-CN-YunxiNeural","zh-CN"),
      row("ja-JP-KeitaNeural","ja-JP"),row("fr-FR-HenriNeural","fr-FR")]

@pytest.mark.parametrize("language,expected",[(None,6),("English",2),("en-US",1),("en-GB",1),("Hindi",1),
    ("hi-IN",1),("Mandarin",1),("zh-CN",1),("Japanese",1),("French",1),("de",0),("es",0)])
@pytest.mark.parametrize("order",["forward","reverse","duplicate"])
def test_inventory_filter(language,expected,order):
    rows=ROWS if order=="forward" else ROWS[::-1] if order=="reverse" else ROWS+ROWS
    r=inv.normalize(rows,language)
    assert r["matching_voice_count"]==expected and len(r["voices"])==expected
    assert r["voices"]==sorted(r["voices"],key=lambda x:x["voice_preset"])
    assert not r["truncated"]

@pytest.mark.parametrize("rows",[None,{},[],[None],[row("hi-IN-MadhurNeural","en-US")],
    [row("hi-IN-MadhurNeural","hi-IN"),row("hi-IN-MadhurNeural","hi-IN","Female")]])
def test_inventory_rejects_malformed(rows):
    with pytest.raises(ValueError):inv.normalize(rows)

@pytest.mark.parametrize("consent,ack",[(False,inv.ACK),(1,inv.ACK),(True,None),(True,"YES")])
def test_inventory_consent(consent,ack):
    with pytest.raises(ValueError,match="consent"):
        inv.discover(allow_network=consent,acknowledgment=ack,fetcher=lambda:pytest.fail("network called"))

def test_inventory_mock_and_no_dialogue():
    r=inv.discover(requested="en",allow_network=True,acknowledgment=inv.ACK,fetcher=lambda:ROWS)
    assert len(r["voices"])==2 and not r["network_request_performed"] and not r["dialogue_sent"]

def test_inventory_bounded_and_unsupported():
    rows=[row("en-US-V"+str(i)+"Neural","en-US") for i in range(1001)]
    r=inv.normalize(rows)
    assert len(r["voices"])==1000 and r["truncated"] and r["matching_voice_count"]==1001
    with pytest.raises(ValueError):inv.normalize(rows*5)
    assert inv.normalize([row("unsupported","en-US")])["voices"]==[]

@pytest.mark.parametrize("count",[0,6,True,1.5])
def test_plan_limit(count):
    with pytest.raises(ValueError,match="1–5"):edge.plan(None,None,max_new=count)

@pytest.mark.parametrize("action",["edge-generate","edge-inventory"])
@pytest.mark.parametrize("consent",[False,1,"yes",None])
def test_dashboard_consent(action,consent):
    data={"project_id":"x","max_new":1,"network_consent":consent} if action=="edge-generate" else {"language":None,"network_consent":consent}
    with pytest.raises(ValueError,match="consent"):author.run(None,action,data,acknowledgment=author.ACK)

def test_offline_plan_and_stop(tmp_path,monkeypatch):
    root,pid=ready(tmp_path,monkeypatch,"edge",presets=("hi-IN-MadhurNeural","hi-IN-SwaraNeural"))
    report=author.run(root,"edge-plan",{"project_id":pid,"max_new":1})
    assert report["selected_turns"][0]["turn_id"]=="0001" and report["remaining_edge_turns"]==2
    assert report["network_requests"]==0 and "text" not in report["selected_turns"][0]
    result=edge.generate(root,pid,allow_network_tts=True,acknowledgment=edge.ACK,max_new=2,
        should_stop=lambda:True,synthesizer=lambda *a:pytest.fail("network called"))
    assert result["stopped_at_checkpoint"] and result["new_generated_turns"]==[]

def test_dashboard_dispatch(monkeypatch):
    calls=[]
    monkeypatch.setattr(edge,"generate",lambda *a,**k:calls.append(k) or {})
    author.run(None,"edge-generate",{"project_id":"x","max_new":2,"network_consent":True},acknowledgment=author.ACK)
    assert calls[0]["allow_network_tts"] is True and calls[0]["acknowledgment"]==edge.ACK

def test_cli_and_markup():
    assert not cli.parse(["edge-voice-inventory","--acknowledgment",inv.ACK]).allow_network
    assert cli.parse(["project-edge-plan","--project-id","a"*32]).max_new==1
    assert cli.parse(["dependency-plan","--group","edge"]).group=="edge"
    assert dependency_setup.plan("edge")["packages"][0]["requirement"]=="edge-tts>=7,<9"
    page=web.html_page("test")
    assert all(x in page for x in ("v4EdgePlan","v4EdgeGenerate","v4EdgeInventory","author-edge-generate"))
