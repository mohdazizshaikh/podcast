"""Synthetic diagnostics only; no model execution or third-party downloads."""
import importlib.metadata
import pytest
from podcast_gpt import cli, hardware, kokoro_preflight


def test_cpu_thread_selection(monkeypatch):
    monkeypatch.setattr(hardware,"logical_cpus",lambda:8)
    assert hardware.select_threads()==4
    assert hardware.select_threads(2)==2
    for bad in (0,9,True,2.5):
        with pytest.raises(ValueError,match="CPU threads"):
            hardware.select_threads(bad)
    monkeypatch.setattr(hardware,"logical_cpus",lambda:1)
    assert hardware.select_threads()==1


def test_ram_diagnostics_never_certify_speed(monkeypatch):
    monkeypatch.setattr(hardware,"memory_bytes",lambda:(8*1024**3,2*1024**3))
    state=hardware.report()
    assert state["physical_ram_gib"]==8
    assert state["available_ram_gib"]==2
    assert state["low_available_ram_warning"]
    assert not state["actual_model_speed_measured"]
    monkeypatch.setattr(hardware,"memory_bytes",lambda:(None,None))
    assert hardware.report()["available_ram_gib"] is None


def test_read_only_kokoro_inventory(tmp_path,monkeypatch):
    model=tmp_path/"test.onnx"; model.write_bytes(b"x"*1_000_000)
    voices=tmp_path/"test.bin"; voices.write_bytes(b"y"*1000)
    def missing(name):
        raise importlib.metadata.PackageNotFoundError(name)
    monkeypatch.setattr(kokoro_preflight.importlib.metadata,"version",missing)
    workspace=tmp_path/"not-created"
    args=cli.parse(["--workspace",str(workspace),"check-kokoro","--model",str(model),"--voices",str(voices)])
    state=cli.execute(args)
    assert not workspace.exists()
    assert not state["required_python_packages_present"]
    assert state["new_model_inference_calls"]==0
    assert state["internet_downloads"]==0
    assert not state["model_load_verified"]
    assert len(state["kokoro_model_sha256"])==64
