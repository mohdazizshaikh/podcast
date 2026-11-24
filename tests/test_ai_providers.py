import json
import pytest
from podcast_gpt import ai_providers as ai, episode_plan as ep, cli


def response(value):
    return {"choices":[{"finish_reason":"stop","message":{"content":json.dumps(value)}}]}


def request_data():
    return {"topic":"Local science","language":"Hindi","duration_minutes":60,
            "presenters":["P"+str(i) for i in range(10)],"video_format":"vertical",
            "workflow":"automatic","input_kind":"topic","research_mode":"knowledge"}


def valid_plan(req):
    return {"title":"Episode","sections":[{"heading":"Topic","minutes":req["duration_minutes"],
            "summary":"Discussion","presenters":req["presenters"]}]}


def test_openrouter_free_only_and_generalized_plan():
    req=request_data();calls=[]
    def call(url,body=None,headers=None,timeout=90):
        calls.append((url,body,headers))
        return response(valid_plan(req))
    result=ep.plan(req,credentials=ai.Credentials("test-router-key","test-gemini-key"),
                   allow_cloud_text=True,request=call)
    assert result["provider"]=="openrouter"
    assert calls[0][0]==ai.OPENROUTER and calls[0][1]["model"]=="openrouter/free"
    assert "tools" not in calls[0][1] and len(calls)==1
    assert not result["paid_fallback_enabled"] and not result["rendering_compatibility_verified"]
    assert "test-router-key" not in json.dumps(result)


def test_invalid_router_output_falls_back_to_explicit_gemini():
    req=request_data();calls=[]
    def call(url,body=None,headers=None,timeout=90):
        calls.append(url)
        if url==ai.OPENROUTER:return response({"bad":True})
        assert url==ai.GEMINI
        assert "tools" not in body and headers=={"x-goog-api-key":"test-gemini-key"}
        return {"candidates":[{"finishReason":"STOP","content":{"parts":[{"text":json.dumps(valid_plan(req))}]}}]}
    result=ep.plan(req,credentials=ai.Credentials("test-router-key","test-gemini-key"),
                    allow_cloud_text=True,confirm_gemini_free_project=True,request=call)
    assert result["provider"]=="gemini" and calls==[ai.OPENROUTER,ai.GEMINI]
    assert result["attempts"][0]["status"]=="invalid_structured_output"


def test_no_cloud_consent_local_only_and_under_3b_metadata():
    req=request_data();calls=[]
    def call(url,body=None,headers=None,timeout=90):
        calls.append(url)
        assert url.startswith(ai.OLLAMA+"/")
        if url.endswith("/tags"):return {"models":[{"name":"qwen3:1.7b"}]}
        if url.endswith("/show"):return {"model_info":{"general.parameter_count":1_700_000_000}}
        assert body["model"]=="qwen3:1.7b" and body["options"]["num_gpu"]==0
        return {"done":True,"done_reason":"stop","message":{"content":json.dumps(valid_plan(req))}}
    result=ep.plan(req,credentials=ai.Credentials("test-router-key","test-gemini-key"),request=call)
    assert result["provider"]=="ollama" and len(calls)==3
    assert all(x.startswith(ai.OLLAMA) for x in calls)


def test_gemini_skipped_without_confirmation_and_retagged_large_model_rejected():
    calls=[]
    def call(url,body=None,headers=None,timeout=90):
        calls.append(url)
        if url.endswith("/tags"):return {"models":[{"name":"qwen3:1.7b"}]}
        if url.endswith("/show"):return {"model_info":{"general.parameter_count":3_000_000_000}}
        raise AssertionError("Must not invoke a model")
    with pytest.raises(ai.ProviderError,match="no_verified_installed_under_3b_model"):
        ep.plan(request_data(),credentials=ai.Credentials(None,"test-gemini-key"),
                allow_cloud_text=True,request=call)
    assert calls==[ai.OLLAMA+"/api/tags",ai.OLLAMA+"/api/show"]


def test_strict_request_plan_validation_and_key_redaction(monkeypatch):
    req=request_data();req["duration_minutes"]=1;req["presenters"]=["Solo"]
    assert ep.validate_plan(valid_plan(req),ep.validate_request(req))
    bad=valid_plan(req);bad["sections"][0]["minutes"]=2
    with pytest.raises(ValueError):ep.validate_plan(bad,req)
    with pytest.raises(ValueError,match="not implemented"):ep.validate_request({**req,"input_kind":"pdf"})
    with pytest.raises(ValueError):ep.validate_request({**req,"presenters":["Solo","solo"]})
    with pytest.raises(ValueError,match="under-3B"):ep.plan(req,local_model="qwen3:4b")
    monkeypatch.setenv("OPENROUTER_API_KEY","test-secret-key")
    status=cli.execute(cli.parse(["ai-provider-status"]))
    assert status["openrouter_key_present"] and status["network_requests"]==0
    assert "test-secret-key" not in json.dumps(status)
    assert "test-secret-key" not in repr(ai.Credentials.environment())
