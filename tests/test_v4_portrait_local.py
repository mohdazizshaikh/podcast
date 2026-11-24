import json
from PIL import Image
import pytest
from podcast_gpt import portrait_local as p,characters,projects,cli,source
from test_v4_master_tts import ready


def model(tmp_path):
    root=tmp_path/"model";root.mkdir()
    (root/"model_index.json").write_text(json.dumps({"_class_name":"StableDiffusionPipeline",
        "safety_checker":["stable_diffusion","StableDiffusionSafetyChecker"]}),encoding="utf-8")
    for name in ("unet","vae","text_encoder","safety_checker","scheduler","tokenizer","feature_extractor"):
        (root/name).mkdir()
        if name in ("unet","vae","text_encoder","safety_checker"):(root/name/"model.safetensors").write_bytes(b"fixture")
    return root


def test_candidate_does_not_mutate_cast(tmp_path,monkeypatch):
    root,pid=ready(tmp_path,monkeypatch);cast=characters.read_cast(root,pid)
    cid=cast["cast"][0]["character_id"];old=characters.read(root,cid);m=model(tmp_path)
    monkeypatch.setattr(p.hardware,"memory_bytes",lambda:(16*p.GIB,12*p.GIB))
    monkeypatch.setattr(p.shutil,"disk_usage",lambda x:type("D",(),{"free":10*p.GIB})())
    calls=[]
    def render(*args):calls.append(args);return Image.new("RGB",(512,512),"green")
    with pytest.raises(ValueError,match="consent"):p.generate(root,cid,model=m,renderer=render)
    result=p.generate(root,cid,model=m,acknowledgment=p.ACK,renderer=render)
    assert result["receipt"]["test_fixture_only"] and not result["receipt"]["human_portrait_approved"]
    assert len(calls)==1 and characters.read(root,cid)==old and characters.read_cast(root,pid)==cast
    assert result["receipt"]["portrait_sha256"]==source.digest(result["path"])


@pytest.mark.parametrize("seed,steps",[(True,20),(-1,20),(2**32,20),(42,9),(42,31),(42,True)])
def test_invalid_options(seed,steps):
    with pytest.raises(ValueError,match="Seed"):p.generate(None,None,model=None,seed=seed,steps=steps,acknowledgment=p.ACK)


@pytest.mark.parametrize("name",["weights.bin","model.ckpt","module.py","data.pkl"])
def test_reject_untrusted_formats(tmp_path,name):
    m=model(tmp_path);(m/name).write_bytes(b"bad")
    with pytest.raises(ValueError,match="safetensors"):p._model(m)


def test_missing_safety_checker(tmp_path):
    m=model(tmp_path)
    (m/"model_index.json").write_text(json.dumps({"_class_name":"StableDiffusionPipeline","safety_checker":[None,None]}),encoding="utf-8")
    with pytest.raises(ValueError,match="safety checker"):p._model(m)
    assert cli.parse(["character-portrait-preflight","--character-id","a"*32,"--model",str(m)]).operation=="character-portrait-preflight"
