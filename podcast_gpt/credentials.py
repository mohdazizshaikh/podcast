"""Windows current-user DPAPI credential storage, CLI only.

No plaintext file fallback, credentials in arguments, browser access or
persistent cloud consent. On other OSes use environment/session keys.
"""
from __future__ import annotations

import base64
import ctypes
import sys
import warnings
from pathlib import Path

from . import ai_providers, projects, source

FILENAME=".provider-credentials.json"
PROVIDERS=("openrouter","gemini")


def _dpapi(payload:bytes,*,decrypt:bool):
    if sys.platform!="win32":raise ValueError("Persistent encrypted keys require Windows DPAPI; use environment keys instead")
    from ctypes import wintypes
    class Blob(ctypes.Structure):
        _fields_=[("cbData",wintypes.DWORD),("pbData",ctypes.POINTER(ctypes.c_ubyte))]
    buf=(ctypes.c_ubyte*len(payload)).from_buffer_copy(payload)
    inp=Blob(len(payload),ctypes.cast(buf,ctypes.POINTER(ctypes.c_ubyte)))
    out=Blob()
    crypt=ctypes.WinDLL("crypt32",use_last_error=True)
    kernel=ctypes.WinDLL("kernel32",use_last_error=True)
    fn=crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
    fn.argtypes=[ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(Blob)]
    fn.restype=wintypes.BOOL
    kernel.LocalFree.argtypes=[ctypes.c_void_p]
    kernel.LocalFree.restype=ctypes.c_void_p
    try:
        # No machine-wide flag: encrypted blob belongs to current Windows user.
        if not fn(ctypes.byref(inp),None,None,None,None,1,ctypes.byref(out)):
            raise ValueError("Windows credential encryption/decryption failed")
        return ctypes.string_at(out.pbData,out.cbData)
    finally:
        ctypes.memset(buf,0,len(payload))
        if out.pbData:
            ctypes.memset(out.pbData,0,out.cbData)
            kernel.LocalFree(out.pbData)


def _folder(root,pid,*,create=False):
    return projects.project(root,pid) if pid is not None else projects.base(root,create=create)


def _read(folder):
    p=folder/FILENAME
    if not p.exists() and not p.is_symlink():return {}
    projects._plain(p,directory=False)
    value=source.read_json(p,16_000)
    if set(value)!={"schema","encrypted"} or value["schema"]!=1 or not isinstance(value["encrypted"],dict):
        raise ValueError("Invalid encrypted credential store")
    if not set(value["encrypted"]).issubset(PROVIDERS) or any(not isinstance(v,str) for v in value["encrypted"].values()):
        raise ValueError("Invalid encrypted credential entries")
    return value["encrypted"]


def store(root,provider,key,*,pid=None):
    if provider not in PROVIDERS or not ai_providers._key(key):raise ValueError("Invalid provider or key format")
    if sys.platform!="win32":raise ValueError("Windows DPAPI required for persistent keys")
    folder=_folder(root,pid,create=True)
    with projects.exclusive(folder):
        data=_read(folder)
        data[provider]=base64.b64encode(_dpapi(key.encode("ascii"),decrypt=False)).decode("ascii")
        source.atomic_json(folder/FILENAME,{"schema":1,"encrypted":data})
    return {"provider":provider,"project_id":pid,"encrypted_key_saved":True}


def remove(root,provider,*,pid=None):
    if provider not in PROVIDERS:raise ValueError("Unknown provider")
    folder=_folder(root,pid)
    if not folder.exists():return {"removed":False}
    with projects.exclusive(folder):
        data=_read(folder)
        existed=provider in data
        if existed:
            del data[provider]
            source.atomic_json(folder/FILENAME,{"schema":1,"encrypted":data})
    return {"provider":provider,"project_id":pid,"removed":existed}


def status(root,*,pid=None):
    global_keys=_read(_folder(root,None))
    local_keys=_read(_folder(root,pid)) if pid else {}
    env=ai_providers.Credentials.environment()
    return {"default_encrypted":sorted(global_keys),"project_encrypted":sorted(local_keys),
            "environment":{p:bool(getattr(env,p)) for p in PROVIDERS},
            "windows_dpapi_available":sys.platform=="win32",
            "cloud_consent_persisted":False}


def resolve(root,*,pid=None):
    env=ai_providers.Credentials.environment()
    data=_read(_folder(root,None))
    if pid:data.update(_read(_folder(root,pid)))
    result={}
    for provider in PROVIDERS:
        if provider not in data:result[provider]=getattr(env,provider);continue
        try:key=_dpapi(base64.b64decode(data[provider],validate=True),decrypt=True).decode("ascii")
        except (ValueError,UnicodeError):raise ValueError("Unable to decrypt saved provider key; remove or replace it") from None
        if not ai_providers._key(key):raise ValueError("Invalid decrypted provider key")
        result[provider]=key
    return ai_providers.Credentials(**result)


def prompt_key(provider):
    import getpass
    if sys.platform!="win32":raise ValueError("Windows DPAPI required; use environment keys on this OS")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error",getpass.GetPassWarning)
            return getpass.getpass("Enter "+provider+" API key (hidden): ")
    except (getpass.GetPassWarning,EOFError,KeyboardInterrupt):
        raise ValueError("Secure hidden key input unavailable or cancelled") from None
