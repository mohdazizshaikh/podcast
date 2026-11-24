"""Explicit bounded browser invocation of already configured local engines."""
from . import projects, v4_orchestrator as auto, v4_tts, v4_espeak, v4_neural

ENGINES=("ollama","kokoro","espeak","sadtalker")
ACK="I_AUTHORIZE_SELECTED_LOCAL_ENGINE_AND_TRUST_ITS_MODELS_AND_HAVE_USAGE_RIGHTS"


def run(root,pid,*,engine,max_steps,acknowledgment,progress=None,should_stop=None):
    if acknowledgment!=ACK:raise ValueError("Explicit local model trust, execution and usage rights required")
    if engine not in ENGINES or type(max_steps) is not int or not 1<=max_steps<=5:
        raise ValueError("Choose one local engine and 1–5 bounded actions")
    projects.project(root,pid)
    options={
        "ollama":{"allow_local_ai":True,"allowed_stages":("outline_required","script_required")},
        "kokoro":{"kokoro_ack":v4_tts.ACK,"allowed_stages":("audio_required",)},
        "espeak":{"espeak_ack":v4_espeak.ACK,"allowed_stages":("audio_required",)},
        "sadtalker":{"neural_ack":v4_neural.ACK,"allowed_stages":("pilot_required","neural_batch_required")},
    }[engine]
    result=auto.run(root,pid,execute=True,acknowledgment=auto.ACK,max_steps=max_steps,progress=progress,should_stop=should_stop,**options)
    return {**result,"selected_engine":engine,"cloud_calls_authorized":False,"automatic_downloads_authorized":False}
