"""Read-only local Japanese dictionary checks before importing the frontend."""
import importlib.metadata as metadata
import os
from pathlib import Path
from . import projects

REQUIRED=("sys.dic","unk.dic","matrix.bin","char.bin","dicrc")
PACKAGES=("misaki","fugashi","jaconv","mojimoji","unidic","pyopenjtalk")


def dictionary(path):
    if not path:return False
    try:
        p=Path(path)
        if not p.is_absolute() or str(p).startswith(("\\\\","//")):return False
        for parent in reversed((p,*p.parents)):projects._plain(parent)
        for name in REQUIRED:
            file=p/name;projects._plain(file,directory=False)
            if not file.stat().st_size:return False
        return True
    except (ValueError,OSError,TypeError):return False


def inspect():
    packages={}
    for name in PACKAGES:
        try:packages[name]=metadata.version(name)
        except metadata.PackageNotFoundError:packages[name]=None
    try:unidic=metadata.distribution("unidic").locate_file("unidic/dicdir")
    except metadata.PackageNotFoundError:unidic=None
    jtalk=os.environ.get("OPEN_JTALK_DICT_DIR")
    return {"packages":packages,"unidic_dictionary_files_present":dictionary(unidic),
            "open_jtalk_dictionary_files_present":dictionary(jtalk),
            "explicit_open_jtalk_path_set":bool(jtalk),"frontend_executed":False,
            "actual_pronunciation_verified":False,"downloads":0}


def require():
    report=inspect()
    if not all(report["packages"].values()) or not report["unidic_dictionary_files_present"] or not report["open_jtalk_dictionary_files_present"]:
        raise ValueError("Japanese requires installed Misaki ja dependencies, full local UniDic and explicit OPEN_JTALK_DICT_DIR; prepare resources separately")
    return report
