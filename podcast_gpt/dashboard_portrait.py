"""Run one explicitly consented portrait in a separate trusted Python process."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from . import projects,portrait_local,source

ACK=portrait_local.ACK


def generate(root,cid,model,seed,steps,*,acknowledgment,runner=None):
    if acknowledgment!=ACK:raise ValueError("Explicit local portrait inference consent required")
    if type(seed) is not int or not 0<=seed<2**32 or type(steps) is not int or not 10<=steps<=30:raise ValueError("Invalid portrait seed or steps")
    characters=portrait_local.characters
    characters.read(root,cid)
    model=Path(model)
    if not model.is_absolute():raise ValueError("Use absolute model directory")
    base=projects.base(root)
    with tempfile.TemporaryDirectory(prefix="portrait-worker-",dir=base) as tmp:
        result=Path(tmp)/"result.json"
        env={k:v for k,v in os.environ.items() if k.upper() not in ("OPENROUTER_API_KEY","GEMINI_API_KEY","GOOGLE_API_KEY","HF_TOKEN","HUGGING_FACE_HUB_TOKEN")}
        env.update(HF_HUB_OFFLINE="1",TRANSFORMERS_OFFLINE="1",CUDA_VISIBLE_DEVICES="")
        try:
            done=(runner or subprocess.run)([sys.executable,"-m","podcast_gpt.portrait_worker",str(root),cid,str(model),str(seed),str(steps),str(result)],
                env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=7200,check=False)
        except subprocess.TimeoutExpired:raise ValueError("Portrait worker timed out; inspect private scratch and locks") from None
        if done.returncode:raise ValueError("Portrait worker failed; inspect local model prerequisites and private attempts")
        projects._plain(result,directory=False)
        value=source.read_json(result,32000)
        verified=portrait_local.audit_candidate(root,value["candidate_id"])
        if verified["receipt"]["character_id"]!=cid or verified["receipt"]["test_fixture_only"] or verified["receipt"]["seed"]!=seed or verified["receipt"]["steps"]!=steps:
            raise ValueError("Portrait worker result differs")
        return verified
