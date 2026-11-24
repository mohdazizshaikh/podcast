"""Dependency cache checks never contact a package or model service."""
from podcast_gpt import bootstrap


def test_dependency_stamp_records_and_invalidates(tmp_path,monkeypatch):
    stamp=tmp_path/"dependency.json"
    monkeypatch.setattr(bootstrap.sys,"prefix",str(tmp_path))
    monkeypatch.setattr(bootstrap,"stamp_path",lambda:stamp)
    fingerprint={"schema":1,"project_sha256":"first"}
    monkeypatch.setattr(bootstrap,"dependency_fingerprint",lambda:dict(fingerprint))
    assert bootstrap.main(["check"])==1
    assert not stamp.exists()
    assert bootstrap.main(["record"])==0
    before=stamp.read_bytes()
    assert bootstrap.main(["check"])==0
    assert stamp.read_bytes()==before
    fingerprint["project_sha256"]="changed"
    assert bootstrap.main(["check"])==1
    assert bootstrap.main(["record"])==0
    assert bootstrap.main(["check"])==0
    stamp.write_text("corrupt",encoding="utf-8")
    assert bootstrap.main(["check"])==1


def test_dependency_stamp_refuses_system_python(monkeypatch):
    monkeypatch.setattr(bootstrap.sys,"prefix",bootstrap.sys.base_prefix)
    assert bootstrap.main(["record"])==1
