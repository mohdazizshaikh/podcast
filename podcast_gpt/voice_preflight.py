"""Static voice compatibility report; no model loading or engine execution."""
from . import projects,characters,model_config,kokoro_languages as langs,v4_espeak as espeak


def inspect(root,pid):
    req=projects.load(root,pid);cast=characters.status(root,pid);configs=model_config.status(root)["engines"]
    rows=[];used={}
    for item in cast.get("presenters",[]):
        voice=item["voice_preferences"];engine=voice["engine"];issues=[];candidate=None
        if engine=="kokoro":
            try:candidate=langs.preset(voice,langs.language(req["language"]))
            except (ValueError,KeyError,TypeError,AttributeError):issues.append("kokoro_language_or_preset_mismatch")
        elif engine=="espeak":
            try:candidate=espeak.compatible(voice,req["language"],{voice["preset"].split("+")[0]})
            except (ValueError,KeyError,TypeError,AttributeError):issues.append("espeak_language_or_preset_mismatch")
        elif engine=="undecided":issues.append("select_voice_or_import")
        elif engine=="edge":issues.append("v4_edge_adapter_pending_use_authorized_import")
        if engine in ("kokoro","espeak") and configs.get(engine)!="paths_checked":issues.append("saved_paths_not_checked")
        row={"speaker":item["speaker"],"engine":engine,"candidate_preset":candidate,"issues":issues,
             "runtime_voice_inventory_verified":False,"human_voice_quality_verified":False}
        rows.append(row)
        if candidate is not None:used.setdefault((engine,candidate),[]).append(row)
    for group in used.values():
        if len(group)>1:
            for row in group:row["issues"].append("duplicate_preset")
    return {"project_id":pid,"language":req["language"],"cast_assigned":cast["cast_assigned"],
            "voices":rows,"saved_model_status":configs,
            "static_preflight_clear":bool(rows) and all(not row["issues"] for row in rows),
            "authorized_import_available":True,"runtime_voice_compatibility_verified":False,
            "model_inference_calls":0,"network_requests":0,"publication_approved":False}
