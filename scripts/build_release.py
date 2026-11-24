"""Build a deterministic *source-only* candidate from committed Git blobs.

No model, user data, working-tree changes or legacy migration helpers included.
No publication or genuine model quality certification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path

ROOT_FILES = frozenset((
    ".gitignore", "README.md", "pyproject.toml",
    "START_PODCAST_WINDOWS.bat", "CONTINUE_FULL_HINDI_NEURAL.bat",
    "CHECK_SADTALKER_CPU.bat", "RUN_NEURAL_CPU.bat",
    "GENERATE_KOKORO_HINDI_CPU.bat", "REVIEW_THREE_PRESENTER_PILOT.bat",
    "SMART_SETUP_WINDOWS.bat",
))
MANIFEST = "RELEASE_MANIFEST.json"
REQUIRED = ROOT_FILES | {"podcast_gpt/__init__.py","podcast_gpt/__main__.py",
                        "podcast_gpt/cli.py","podcast_gpt/bootstrap.py",
                        "docs/SETUP_WINDOWS.md","docs/REMAINING.md"}
MAX_MEMBER_BYTES = 2_000_000
MAX_ARCHIVE_BYTES = 20_000_000


def allowed(name: str) -> bool:
    return name in ROOT_FILES or bool(re.fullmatch(
        r"(?:podcast_gpt/[A-Za-z_][A-Za-z_0-9]*\.py|docs/[A-Za-z_0-9-]+\.md)", name))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(repo: Path, *args: str) -> bytes:
    return subprocess.run(["git","-C",str(repo),*args],check=True,
                          stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                          timeout=60).stdout


def inventory(repo: Path, commit: str) -> dict[str,bytes]:
    files = {}
    for item in git(repo,"ls-tree","-r","-z",commit).split(b"\0"):
        if not item: continue
        meta, raw_name = item.split(b"\t",1)
        mode, kind, oid = meta.decode("ascii").split()
        name = raw_name.decode("utf-8")
        if not allowed(name): continue
        if mode not in ("100644","100755") or kind!="blob":
            raise ValueError("Release member is not a regular committed file: "+name)
        size = int(git(repo,"cat-file","-s",oid))
        if size>MAX_MEMBER_BYTES:
            raise ValueError("Release member exceeds source-only size cap: "+name)
        files[name]=git(repo,"cat-file","blob",oid)
    if not REQUIRED.issubset(files):
        raise ValueError("Required app files missing: "+str(sorted(REQUIRED-set(files))))
    if sum(map(len,files.values()))>MAX_ARCHIVE_BYTES:
        raise ValueError("Source release exceeds size cap")
    return files


def _write(z: zipfile.ZipFile, name: str, payload: bytes) -> None:
    info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0))
    info.create_system=3
    info.external_attr=0o100644 << 16
    # Stored mode avoids compression-library variability across platforms.
    z.writestr(info,payload,compress_type=zipfile.ZIP_STORED)


def build(repo: Path, output: Path) -> dict:
    commit=git(repo,"rev-parse","--verify","HEAD^{commit}").decode("ascii").strip()
    files=inventory(repo,commit)
    manifest={"schema":1,"source_commit":commit,
              "kind":"source_only_candidate_no_models_or_private_media",
              "files":{name:sha(data) for name,data in sorted(files.items())},
              "genuine_model_execution_verified":False,
              "publication_approved":False}
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,"x") as z:
        for name,data in sorted(files.items()): _write(z,name,data)
        _write(z,MANIFEST,(json.dumps(manifest,sort_keys=True,indent=2)+"\n").encode("utf-8"))
    verify(output)
    checksum=sha(output.read_bytes())
    with output.with_suffix(output.suffix+".sha256").open("x",encoding="ascii",newline="\n") as f:
        f.write(checksum+"  "+output.name+"\n")
    return {"source_commit":commit,"files":len(files),"archive_sha256":checksum}


def verify(path: Path) -> dict:
    if path.stat().st_size>MAX_ARCHIVE_BYTES+1_000_000:
        raise ValueError("Source archive size limit exceeded")
    with zipfile.ZipFile(path) as z:
        names=z.namelist()
        if len(names)!=len(set(names)) or MANIFEST not in names:
            raise ValueError("Duplicate names or missing release manifest")
        if any(n!=MANIFEST and not allowed(n) for n in names):
            raise ValueError("Unapproved archive member")
        if any(i.file_size>MAX_MEMBER_BYTES or i.is_dir() or
               ((i.external_attr>>16)&0o170000)!=0o100000 for i in z.infolist()):
            raise ValueError("Invalid archive member type or size")
        if sum(i.file_size for i in z.infolist())>MAX_ARCHIVE_BYTES:
            raise ValueError("Uncompressed source archive size limit exceeded")
        data=json.loads(z.read(MANIFEST))
        if (data.get("schema")!=1 or data.get("kind")!="source_only_candidate_no_models_or_private_media"
                or not re.fullmatch(r"[0-9a-f]{40,64}",str(data.get("source_commit","")))
                or data.get("genuine_model_execution_verified") is not False
                or data.get("publication_approved") is not False):
            raise ValueError("Invalid release manifest")
        actual={name:sha(z.read(name)) for name in names if name!=MANIFEST}
        if not REQUIRED.issubset(actual) or actual!=data.get("files"):
            raise ValueError("Release file manifest differs from contents")
        return data


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo",type=Path,default=Path.cwd())
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument("--output",type=Path)
    group.add_argument("--verify",type=Path)
    a=p.parse_args()
    print(json.dumps(verify(a.verify) if a.verify else build(a.repo,a.output),indent=2))


if __name__=="__main__":
    main()
