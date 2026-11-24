"""Unified setup is inspection only, never real AI acceptance."""
from pathlib import Path
import pytest
from podcast_gpt import setup_wizard as wizard, cli, web


def test_unconfigured_wizard_is_read_only(tmp_path):
    root=tmp_path/"not created"
    result=wizard.inspect(root)
    assert result["workspace"]["status"]=="not_created"
    assert result["voice_engine"]["status"]=="not_configured"
    assert result["face_engine"]["status"]=="not_configured"
    assert result["downloads"]==result["new_model_inference_calls"]==0
    assert not result["model_load_verified"]
    assert not root.exists()


def test_model_probe_requires_consent(tmp_path,monkeypatch):
    model=tmp_path/"model"
    model.mkdir()
    exe=model/"python.exe"
    exe.write_bytes(b"synthetic fixture, do not execute")
    calls=[]
    def probe(*args):
        calls.append(args)
        return {"model_can_actually_load_verified":False}
    monkeypatch.setattr(wizard.model_preflight,"inspect_sadtalker_installation",probe)
    root=tmp_path/"private"
    args={"sadtalker_root":model,"sadtalker_python":exe}
    assert wizard.inspect(root,**args)["face_engine"]["status"]=="interpreter_probe_consent_required"
    assert calls==[]
    assert wizard.inspect(root,**args,probe_interpreter=True)["face_engine"]["status"]=="inventory_checked"
    assert calls==[(model,exe)]
    assert not root.exists()


def test_voice_and_face_missing_paths_have_independent_status(tmp_path,monkeypatch):
    def bad(*args):raise ValueError("test invalid voice asset")
    monkeypatch.setattr(wizard.kokoro_preflight,"inspect",bad)
    root=tmp_path/"private"
    result=wizard.inspect(root,kokoro_model=tmp_path/"m.onnx",kokoro_voices=tmp_path/"v.bin",sadtalker_root=tmp_path/"missing")
    assert result["voice_engine"]["status"]=="blocked"
    assert result["face_engine"]["status"]=="incomplete_selection"
    assert not root.exists()


def test_cli_and_dashboard_expose_only_read_only_setup(tmp_path):
    root=tmp_path/"private"
    args=cli.parse(["--workspace",str(root),"setup-wizard"])
    assert cli.execute(args)["downloads"]==0
    assert 'data-action="setup-wizard"' in web.html_page("test")
    assert not root.exists()
