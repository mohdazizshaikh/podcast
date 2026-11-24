"""Read-only guided next steps from private saved paths and local inventory."""
from . import model_config,dependency_setup,setup_wizard,ai_providers


def inspect(root):
    configured=model_config.status(root)
    inventory=setup_wizard.inspect(root)
    packages={group:dependency_setup.plan(group) for group in dependency_setup.GROUPS}
    steps=[]
    if not inventory["application_prerequisites_present"]:steps.append({"engine":"app","action":"Install missing application prerequisites","guide":"docs/SETUP_WINDOWS.md"})
    if not inventory["workspace"].get("neural_disk_gate"):steps.append({"engine":"app","action":"Choose private workspace with at least 6 GiB free; actual project may need more","guide":"docs/SETUP_WINDOWS.md"})
    for engine,guide in (("kokoro","docs/KOKORO_OFFLINE.md"),("sadtalker","docs/SADTALKER_CPU_SETUP.md"),("espeak","docs/V4_MODEL_VOICES_PERSONA.md")):
        state=configured["engines"][engine]
        if state!="paths_checked":action="Obtain trusted local assets manually and save validated model paths"
        else:action="Run separately consented local preflight or small production pilot; inspect and review actual output"
        steps.append({"engine":engine,"path_status":state,"action":action,"guide":guide})
    steps.append({"engine":"ollama","action":"Manually install a trusted local Ollama service and one approved under-3B tag; no automatic pull",
                  "candidate_tags":list(ai_providers.LOCAL_MODELS),"guide":"docs/V4_WORKFLOW.md"})
    return {"inventory":inventory,"saved_model_status":configured,"optional_dependency_groups":packages,"next_steps":steps,
            "downloads":0,"interpreter_executions":0,"model_load_verified":False,"actual_device_acceptance_verified":False}
