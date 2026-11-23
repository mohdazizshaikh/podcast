"""Actual private loopback HTTP acceptance; no network provider / AI models."""
from __future__ import annotations

import io
import json
import re
import socket
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import wave
from pathlib import Path

from PIL import Image
from podcast_gpt import web


def _port():
    with socket.socket() as s:
        s.bind(("127.0.0.1",0))
        return s.getsockname()[1]


def _request(port,path,*,body=None,token=None,origin=None,rights=False):
    hdr={}
    if token is not None:hdr["X-CSRF-Token"]=token
    if origin is not None:hdr["Origin"]=origin
    if rights:hdr["X-Portrait-Rights-Confirmed"]="YES"
    request=urllib.request.Request(f"http://127.0.0.1:{port}"+path,data=body,
                                    headers=hdr,method="POST" if body is not None else "GET")
    try:
        with urllib.request.urlopen(request,timeout=15) as resp:
            return resp.status,resp.read()
    except urllib.error.HTTPError as err:
        return err.code,err.read()


def test_local_dashboard_real_loopback_csrf_private_upload_and_no_serve_media(tmp_path):
    port=_port();root=tmp_path/"User Private Hindi Sources Outside Repo"
    thread=threading.Thread(target=web.serve,args=(root,port),daemon=True)
    thread.start()
    body=None
    for _ in range(70):
        try:
            code,body=_request(port,"/")
            break
        except (OSError,ConnectionError):
            time.sleep(.08)
    assert code==200
    html=body.decode("utf8")
    token=re.search(r'const token="([0-9a-f]{64})"',html).group(1)
    assert "private" in html.lower()
    assert "run-cpu" not in html
    assert "setTimeout" in html  # Actual UI updates during long local renders.
    code,_=_request(port,"/api/action?cmd=init",body=b"")
    assert code==403  # Not authorized without same-page CSRF token.
    code,_=_request(port,"/api/action?cmd=init",body=b"",token=token,origin="https://attacker.example")
    assert code==403
    code,receipt=_request(port,"/api/action?cmd=init",body=b"",token=token)
    assert code==202,receipt
    for _ in range(90):
        code,response=_request(port,"/api/status")
        result=json.loads(response)
        if result["phase"]!="running":break
        time.sleep(.07)
    assert result["phase"]=="complete",result
    assert (root/"project.json").is_file()
    # Read-only device stage inspector is accessible without model/voice calls.
    code,_=_request(port,"/api/action?cmd=readiness",body=b"",token=token)
    assert code==202
    for _ in range(90):
        code,response=_request(port,"/api/status")
        report=json.loads(response)
        if report["phase"]!="running":break
        time.sleep(.07)
    assert report["phase"]=="complete",report
    assert report["result"]["new_model_inference_calls"]==0
    assert report["result"]["new_tts_service_calls"]==0
    assert report["result"]["publication_approved"] is False
    assert report["result"]["checks"]["script"]["status"]=="verified"
    assert "portraits" in report["result"]["next_safe_action"]
    image=io.BytesIO();Image.new("RGB",(230,230),(73,121,188)).save(image,format="PNG")
    png=image.getvalue()
    code,_=_request(port,"/api/upload?kind=portrait&name=aarav.png",body=png,token=token)
    assert code==403  # Rights not declared; portrait not imported.
    assert not (root/"portraits"/"aarav.png").exists()
    code,_=_request(port,"/api/upload?kind=portrait&name=aarav.png",body=png,
                    token=token,rights=True)
    assert code==201
    before=(root/"portraits"/"aarav.png").read_bytes()
    code,_=_request(port,"/api/upload?kind=portrait&name=aarav.png",body=png,
                    token=token,rights=True)
    assert code==409
    assert (root/"portraits"/"aarav.png").read_bytes()==before
    code,_=_request(port,"/portraits/aarav.png")
    assert code==404
    code,_=_request(port,"/api/upload?kind=portrait&name=..%2Fsecret.png",body=png,token=token,rights=True)
    assert code==400
    with io.BytesIO() as raw:
        with wave.open(raw,"wb") as wav:
            wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(16000)
            wav.writeframes(b"\0\0"*16000)
        original_wav=raw.getvalue()
    code,_=_request(port,"/api/upload?kind=voice&name=000.wav",body=original_wav,token=token)
    assert code==400  # The numbered original source turns are strictly 001..045.
    assert not (root/"voices"/"000.wav").exists()
    code,_=_request(port,"/api/upload?kind=voice&name=001.wav",body=original_wav,token=token)
    assert code==201
    assert (root/"voices"/"001.wav").read_bytes()==original_wav


def test_original_voice_upload_blocks_concurrent_source_actions(tmp_path,monkeypatch):
    """Native threaded localhost HTTP: uploads hold the SAME exclusive task lock."""
    port=_port()
    root=tmp_path/"Private race-free studio"
    threading.Thread(target=web.serve,args=(root,port),daemon=True).start()
    page=None
    for _ in range(70):
        try:
            status,page=_request(port,"/")
            if status==200:break
        except (OSError,ConnectionError):
            time.sleep(.08)
    assert page is not None
    token=re.search(r'const token="([0-9a-f]{64})"',page.decode("utf-8")).group(1)
    blob=io.BytesIO()
    with wave.open(blob,"wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\0\0"*16000)
    entered=threading.Event()
    resume=threading.Event()
    original=web.wav_info
    def slow_independent_pcm_validation(path):
        entered.set()
        if not resume.wait(10):
            raise RuntimeError("test-only upload validation timeout")
        return original(path)
    monkeypatch.setattr(web,"wav_info",slow_independent_pcm_validation)
    result=[]
    upload=threading.Thread(
        target=lambda:result.append(_request(
            port,"/api/upload?kind=voice&name=003.wav",body=blob.getvalue(),
            token=token)),daemon=True)
    upload.start()
    try:
        assert entered.wait(10), "Local upload should reach real WAV validation"
        code,_=_request(port,"/api/action?cmd=doctor",body=b"",token=token)
        assert code==409, "No source/action may start mid-upload"
    finally:
        resume.set()
        upload.join(timeout=10)
    assert not upload.is_alive()
    assert [x[0] for x in result]==[201]
    assert (root/"voices"/"003.wav").is_file()
    code,_=_request(port,"/api/action?cmd=doctor",body=b"",token=token)
    assert code==202, "Exclusive lock must release after original upload"
