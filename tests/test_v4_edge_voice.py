import pytest
from podcast_gpt import edge_voice as voice

@pytest.mark.parametrize("name,tag,preset",[
    ("Hindi","hi","hi-IN-MadhurNeural"),("English","en","en-US-GuyNeural"),
    ("Marathi","mr","mr-IN-ManoharNeural"),("Tamil","ta","ta-IN-ValluvarNeural"),
    ("Telugu","te","te-IN-MohanNeural"),("Bengali","bn","bn-IN-BashkarNeural"),
    ("Gujarati","gu","gu-IN-NiranjanNeural"),("Urdu","ur","ur-PK-AsadNeural"),
    ("Spanish","es","es-ES-AlvaroNeural"),("French","fr","fr-FR-HenriNeural"),
    ("German","de","de-DE-ConradNeural"),("Italian","it","it-IT-DiegoNeural"),
    ("Portuguese","pt","pt-BR-AntonioNeural"),("Arabic","ar","ar-SA-HamedNeural"),
    ("Russian","ru","ru-RU-DmitryNeural"),("Japanese","ja","ja-JP-KeitaNeural"),
    ("Mandarin","zh","zh-CN-YunxiNeural"),("Korean","ko","ko-KR-InJoonNeural"),
])
@pytest.mark.parametrize("mode",["name","tag","wrong"])
def test_language_matrix(name,tag,preset,mode):
    requested={"name":name,"tag":tag,"wrong":"xx"}[mode]
    profile={"engine":"edge","language":name,"preset":preset}
    if mode=="wrong":
        with pytest.raises(ValueError):voice.compatible(profile,requested)
    else:assert voice.compatible(profile,requested)==preset

@pytest.mark.parametrize("preset",[None,True,"", "en-US-Guy","en-us-GuyNeural","https://example.org/Neural",
                                  "en-US-GuyNeural\n","en-US-../Neural","en-US-123Neural","en-US-GuyNeural;"])
def test_malformed_presets(preset):
    with pytest.raises(ValueError):voice.locale(preset)

@pytest.mark.parametrize("patch",[{"provider":"other"},{"network_consent":False},{"network_consent":1},
                                   {"language":"en"},{"language":"Hindi"},{"voice_preset":"bad"},{"extra":True}])
def test_receipt_validation(patch):
    valid={"provider":"edge_tts_online","network_consent":True,"language":"hi","voice_preset":"hi-IN-MadhurNeural"}
    assert voice.validate_receipt(valid)==valid
    with pytest.raises(ValueError):voice.validate_receipt({**valid,**patch})
