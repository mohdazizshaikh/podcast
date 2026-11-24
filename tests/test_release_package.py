"""Release packaging uses tracked committed source only, never private files."""
import hashlib
import subprocess
import zipfile
from pathlib import Path

import pytest

from scripts import build_release as release


def test_release_is_deterministic_and_ignores_unapproved_files(tmp_path):
    repo=tmp_path/"repo"
    repo.mkdir()
    def git(*args):
        subprocess.run(["git","-C",str(repo),*args],check=True,capture_output=True)
    git("init")
    git("config","user.email","synthetic@example.invalid")
    git("config","user.name","Synthetic release test")
    for name in release.REQUIRED:
        p=repo/name
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text("committed app fixture",encoding="utf-8")
    for name in ("voices/001.wav","models/private.onnx",".migration/old.patch","docs/secret.bin"):
        p=repo/name
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(b"TEST ONLY NOT REAL PRIVATE DATA")
    git("add",".")
    git("commit","-m","synthetic packaging fixture")
    # Build from Git objects rather than an uncontrolled live directory.
    (repo/"README.md").write_text("uncommitted content",encoding="utf-8")
    (repo/"podcast_gpt"/"untracked.py").write_text("untracked",encoding="utf-8")
    a=tmp_path/"a.zip"; b=tmp_path/"b.zip"
    result=release.build(repo,a)
    release.build(repo,b)
    assert a.read_bytes()==b.read_bytes()
    assert result["archive_sha256"]==hashlib.sha256(a.read_bytes()).hexdigest()
    assert a.with_suffix(".zip.sha256").is_file()
    with zipfile.ZipFile(a) as z:
        assert set(z.namelist())==release.REQUIRED|{release.MANIFEST}
        assert z.read("README.md")==b"committed app fixture"
    assert release.verify(a)["publication_approved"] is False
    with pytest.raises(FileExistsError):
        release.build(repo,a)


def test_release_rejects_unsafe_member_and_duplicate(tmp_path):
    bad=tmp_path/"bad.zip"
    with zipfile.ZipFile(bad,"w") as z:
        release._write(z,release.MANIFEST,b"{}")
        release._write(z,"../outside.py",b"no")
    with pytest.raises(ValueError,match="Unapproved"):
        release.verify(bad)
    dup=tmp_path/"dup.zip"
    with zipfile.ZipFile(dup,"w") as z:
        release._write(z,release.MANIFEST,b"{}")
        with pytest.warns(UserWarning):
            release._write(z,release.MANIFEST,b"{}")
    with pytest.raises(ValueError,match="Duplicate"):
        release.verify(dup)
