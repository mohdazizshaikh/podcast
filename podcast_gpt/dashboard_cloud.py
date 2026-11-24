"""One explicitly consented free-policy text drafting action, no key input in browser."""
from . import projects, credentials, continuity, v4_readiness, script_generation

ACK="I_AUTHORIZE_SENDING_CURRENT_PROJECT_TEXT_TO_ELIGIBLE_FREE_PROVIDERS_AND_LOCAL_FALLBACK"


def run(root,pid,*,acknowledgment,confirm_gemini_free_project=False):
    if acknowledgment!=ACK or type(confirm_gemini_free_project) is not bool:
        raise ValueError("Explicit cloud text consent and free-project selection required")
    folder=projects.project(root,pid)
    if continuity.read(folder) is not None:
        raise ValueError("Continuity-enabled projects are local drafting only")
    state=v4_readiness.inspect(root,pid)
    stage=state["stage"]
    if stage=="script_required":
        progress=state["checks"]["script_units"]
        if progress["completed"]==progress["total"]:
            raise ValueError("Finalize completed script with local non-inference controls")
    elif stage!="outline_required":
        raise ValueError("Cloud drafting is only available at eligible outline or script generation stages")
    options={"allow_cloud_text":True,"confirm_gemini_free_project":confirm_gemini_free_project,
             "credentials":credentials.resolve(root,pid=pid,providers=("openrouter","gemini") if confirm_gemini_free_project else ("openrouter",))}
    if stage=="outline_required":result=projects.generate_outline(root,pid,**options)
    else:result=script_generation.generate(root,pid,max_new=1,**options)
    return {**result,"cloud_consent_persisted":False,"paid_fallback_enabled":False,
            "billing_tier_independently_verified":False,"gemini_free_project_self_attested":confirm_gemini_free_project}
