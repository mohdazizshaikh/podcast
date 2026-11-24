"""Bounded text-only free-provider fallback. No credentials persisted.

Gemini billing tier cannot be proven from an API key. It is disabled unless
the owner expressly confirms an unbilled Free Tier project for this run.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Callable

from . import hardware

OPENROUTER="https://openrouter.ai/api/v1/chat/completions"
GEMINI_MODEL="gemini-3.5-flash-lite"
GEMINI="https://generativelanguage.googleapis.com/v1beta/models/"+GEMINI_MODEL+":generateContent"
OLLAMA="http://127.0.0.1:11434"
LOCAL_MODELS=("qwen3.5:2b-q4_K_M","qwen3:1.7b","qwen2.5:1.5b","qwen3:0.6b")
MAX_RESPONSE=1_000_000
MAX_PROMPT=48_000


class ProviderError(RuntimeError):
    pass


class ProviderRefusal(ProviderError):
    """Explicit refusal or safety block must not trigger provider fallback."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        return None


def _request(url,body=None,headers=None,timeout=90):
    # Fixed endpoints only; no redirects or environment proxies, especially
    # when calling the local model. Never log raw HTTP errors or response bodies.
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),_NoRedirect())
    req=urllib.request.Request(url,data=None if body is None else json.dumps(body,ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type":"application/json",**(headers or {})},
                               method="GET" if body is None else "POST")
    try:
        with opener.open(req,timeout=timeout) as response:
            raw=response.read(MAX_RESPONSE+1)
        if len(raw)>MAX_RESPONSE:raise ProviderError("response_too_large")
        result=json.loads(raw.decode("utf-8"))
        if not isinstance(result,dict):raise ProviderError("invalid_response")
        return result
    except urllib.error.HTTPError as exc:
        raise ProviderError("http_"+str(exc.code)) from None
    except (OSError,ValueError,UnicodeError):
        raise ProviderError("connection_or_invalid_json") from None


def _key(value):
    if not isinstance(value,str) or not re.fullmatch(r"[!-~]{8,512}",value):
        return None
    return value


@dataclass(frozen=True)
class Credentials:
    # repr deliberately excludes API keys, no secret file or command argument.
    openrouter: str|None=field(default=None,repr=False)
    gemini: str|None=field(default=None,repr=False)

    @classmethod
    def environment(cls):
        return cls(_key(os.environ.get("OPENROUTER_API_KEY")), _key(os.environ.get("GEMINI_API_KEY")))


def _text_or_error(response,provider):
    try:
        if response.get("error"):raise ProviderError("provider_error")
        if provider=="openrouter":
            item=response["choices"][0]
            if item.get("finish_reason") in ("content_filter","safety") or item.get("message",{}).get("refusal"):
                raise ProviderRefusal("provider_refused_or_filtered")
            if item.get("finish_reason")!="stop":raise ProviderError("incomplete_output")
            text=item["message"]["content"]
        elif provider=="gemini":
            feedback=response.get("promptFeedback")
            if isinstance(feedback,dict) and feedback.get("blockReason") not in (None,"","BLOCK_REASON_UNSPECIFIED"):
                raise ProviderRefusal("provider_refused_or_filtered")
            item=response["candidates"][0]
            if item.get("finishReason") in ("SAFETY","RECITATION","BLOCKLIST","PROHIBITED_CONTENT","SPII","IMAGE_SAFETY","MODEL_ARMOR"):
                raise ProviderRefusal("provider_refused_or_filtered")
            if item.get("finishReason")!="STOP":raise ProviderError("incomplete_output")
            text="".join(p["text"] for p in item["content"]["parts"] if not p.get("thought",False) and isinstance(p.get("text"),str))
        else:
            if response.get("done") is not True or response.get("done_reason")!="stop":
                raise ProviderError("incomplete_output")
            text=response["message"]["content"]
        if not isinstance(text,str) or not text.strip():raise ProviderError("empty_output")
        return text
    except (KeyError,IndexError,TypeError,AttributeError):
        raise ProviderError("invalid_response") from None


def _local_model(request,preferred):
    listing=request(OLLAMA+"/api/tags",timeout=5)
    models=listing.get("models") if isinstance(listing,dict) else None
    if not isinstance(models,list):raise ProviderError("invalid_local_model_inventory")
    names={row.get("name") for row in models if isinstance(row,dict) and isinstance(row.get("name"),str)}
    candidates=(preferred,) if preferred else LOCAL_MODELS
    # On low available RAM, start with the smallest permitted installed model.
    if not preferred and hardware.report()["low_available_ram_warning"]:
        candidates=tuple(reversed(candidates))
    for name in candidates:
        if name not in names:continue
        try:
            info=request(OLLAMA+"/api/show",{"model":name},timeout=10)
            if info.get("remote_host") or info.get("remote_model"):continue
            metadata=info.get("model_info",{})
            count=metadata.get("general.parameter_count") if isinstance(metadata,dict) else None
            if type(count) is int and 0<count<3_000_000_000:
                return name,count
        except ProviderError:
            continue
    raise ProviderError("no_verified_installed_under_3b_model")


def inventory(credentials=None):
    c=credentials or Credentials.environment()
    return {"provider_order":["openrouter","gemini","ollama"],
            "openrouter_key_present":bool(_key(c.openrouter)),
            "gemini_key_present":bool(_key(c.gemini)),
            "openrouter_model":"openrouter/free","gemini_model":GEMINI_MODEL,
            "ollama_candidates":list(LOCAL_MODELS),
            "cloud_text_consent_required":True,"gemini_free_project_confirmation_required":True,
            "billing_tier_independently_verified":False,"network_requests":0}


def generate_json(prompt:str,validator:Callable,*,credentials=None,allow_cloud_text=False,
                  confirm_gemini_free_project=False,offline_only=False,local_model=None,request=None):
    """One bounded attempt per eligible provider; invalid output falls back too.

    No tools, image uploads, paid model IDs, dynamic URLs, cloud Ollama models,
    automatic model pulls, or automatic paid retries. Caller supplies validator.
    """
    if not isinstance(prompt,str) or not prompt.strip() or len(prompt)>MAX_PROMPT:
        raise ValueError("Invalid or oversized AI text request")
    if local_model is not None and local_model not in LOCAL_MODELS:
        raise ValueError("Local model must be an approved explicit under-3B tag")
    if offline_only and allow_cloud_text:
        raise ValueError("Offline-only mode conflicts with cloud text consent")
    c=(credentials or Credentials.environment()) if allow_cloud_text is True and not offline_only else Credentials()
    request=request or _request
    attempts=[]
    cloud=allow_cloud_text is True and not offline_only
    for provider in ("openrouter","gemini","ollama"):
        model=None
        try:
            if provider=="openrouter":
                if not cloud or not _key(c.openrouter):
                    attempts.append({"provider":provider,"status":"skipped_no_consent_or_key"});continue
                model="openrouter/free"
                response=request(OPENROUTER,{"model":model,"messages":[{"role":"user","content":prompt}],
                    "max_tokens":3000,"response_format":{"type":"json_object"},"stream":False},
                    {"Authorization":"Bearer "+c.openrouter},timeout=90)
            elif provider=="gemini":
                if not cloud or not _key(c.gemini) or confirm_gemini_free_project is not True:
                    attempts.append({"provider":provider,"status":"skipped_no_free_project_confirmation_or_key"});continue
                model=GEMINI_MODEL
                response=request(GEMINI,{"contents":[{"parts":[{"text":prompt}]}],
                    "generationConfig":{"maxOutputTokens":3000,"responseMimeType":"application/json"}},
                    {"x-goog-api-key":c.gemini},timeout=90)
            else:
                model,count=_local_model(request,local_model)
                response=request(OLLAMA+"/api/chat",{"model":model,"messages":[{"role":"user","content":prompt}],
                    "stream":False,"format":"json","think":False,"keep_alive":0,
                    "options":{"num_ctx":4096,"num_predict":3000,"num_thread":hardware.select_threads(),"num_gpu":0}},timeout=180)
            text=_text_or_error(response,provider)
            try:
                value=validator(json.loads(text))
            except (ValueError,TypeError,KeyError,AttributeError):
                raise ProviderError("invalid_structured_output") from None
            attempts.append({"provider":provider,"model":model,"status":"validated"})
            return {"provider":provider,"requested_model":model,"attempts":attempts,
                    "result":value,"paid_fallback_enabled":False,
                    "billing_tier_independently_verified":False}
        except ProviderRefusal:
            raise ProviderRefusal("Provider explicitly refused or filtered the request; no fallback attempted") from None
        except ProviderError as exc:
            # Internal transport only emits sanitized status strings.
            attempts.append({"provider":provider,"model":model,"status":str(exc)})
    raise ProviderError("No eligible AI provider returned valid JSON; "+json.dumps(attempts,ensure_ascii=True))
