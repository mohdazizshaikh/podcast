"""Read-only local SadTalker preflight; NO model import, inference or weights."""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

import pytest
from podcast_gpt import cli, neural
from podcast_gpt.model_preflight import inspect_sadtalker_installation


@pytest.fixture
def fake_sadtalker_root(tmp_path):
    root=tmp_path/"only synthetic model structure"
    (root/"src"/"config").mkdir(parents=True)
    (root/"checkpoints").mkdir()
    (root/"inference.py").write_text(
        "from argparse import ArgumentParser\n" +
        "p=ArgumentParser()\n" +
        "\n".join(f"p.add_argument({flag!r})" for flag in
                  ("--cpu","--source_image","--driven_audio","--result_dir","--preprocess")) +
        "\n" + "# Synthetic ONLY; no actual SadTalker code or weights.\n"*8,
        encoding="utf-8")
    (root/"checkpoints"/"FAKE_TEST_ONLY.safetensors").write_bytes(
        b"FAKE-NO-MODEL-INFERENCE" * 50_000)
    return root


def test_user_selected_local_python_and_checkpoint_structural_check_only(fake_sadtalker_root):
    result=inspect_sadtalker_installation(fake_sadtalker_root,Path(sys.executable))
    assert result["checkpoint_files_detected"]==1
    assert result["inference_cli_flags_present"]==[
        "--cpu","--source_image","--driven_audio","--result_dir","--preprocess"]
    assert result["model_can_actually_load_verified"] is False
    assert result["model_license_or_portrait_rights_verified"] is False
    assert result["new_model_inference_calls"]==0
    assert result["internet_downloads"]==0


@pytest.mark.parametrize("missing",[
    "inference.py", "src/config", "checkpoints",
    "checkpoints/FAKE_TEST_ONLY.safetensors",
])
def test_incomplete_local_sadtalker_installation_fails_before_model(
        fake_sadtalker_root,missing):
    path=fake_sadtalker_root/missing
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
    with pytest.raises(ValueError):
        inspect_sadtalker_installation(fake_sadtalker_root,Path(sys.executable))


def test_unknown_inference_flags_refused_without_running_script(fake_sadtalker_root):
    script=fake_sadtalker_root/"inference.py"
    script.write_text(script.read_text(encoding="utf-8").replace("--cpu","--cuda"),
                      encoding="utf-8")
    with pytest.raises(ValueError,match="CLI options"):
        inspect_sadtalker_installation(fake_sadtalker_root,Path(sys.executable))


def test_fake_checkpoint_and_interpreter_rejected(fake_sadtalker_root,tmp_path):
    (fake_sadtalker_root/"checkpoints"/"FAKE_TEST_ONLY.safetensors").write_bytes(b"empty")
    with pytest.raises(ValueError,match="incomplete"):
        inspect_sadtalker_installation(fake_sadtalker_root,Path(sys.executable))
    (fake_sadtalker_root/"checkpoints"/"FAKE_TEST_ONLY.safetensors").write_bytes(
        b"FAKE" * 300_000)
    with pytest.raises(ValueError,match="interpreter"):
        inspect_sadtalker_installation(fake_sadtalker_root,tmp_path/"not-a-python.exe")


def test_python_version_only_check_refuses_broken_selected_binary(fake_sadtalker_root):
    class Bad:
        returncode=1
        stdout=""
    commands=[]
    def fake_runner(*args,**kwargs):
        commands.append(args[0])
        assert args[0][1]=="-c"
        assert "import torch" not in args[0][2]
        assert kwargs["timeout"]<=25
        return Bad()
    with pytest.raises(ValueError,match="interpreter failed"):
        inspect_sadtalker_installation(fake_sadtalker_root,Path(sys.executable),
                                       runner=fake_runner)
    assert len(commands)==1


def test_preflight_cli_needs_no_voice_files_or_portraits(fake_sadtalker_root,tmp_path):
    args=cli.parse(["--workspace",str(tmp_path/"never-initialized-private-workspace"),
                    "check-sadtalker","--sadtalker-root",str(fake_sadtalker_root),
                    "--sadtalker-python",sys.executable])
    report=cli.execute(args)
    assert report["new_model_inference_calls"]==0
    assert not (tmp_path/"never-initialized-private-workspace").exists()


def test_production_cpu_workflow_refuses_missing_model_before_lock(chunk_studio,tmp_path):
    with pytest.raises(ValueError):
        neural.run_cpu(chunk_studio,mode="pilot",max_new=3,rights_confirmed=True,
                       wall_seconds=300,per_chunk_timeout=120,allow_short=True,
                       sadtalker_root=tmp_path/"missing",
                       sadtalker_python=tmp_path/"missing"/"python.exe")
    assert not (chunk_studio/"source"/neural.LOCK).exists()
    assert not list((chunk_studio/"scratch").glob("model-*"))
