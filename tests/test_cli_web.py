import json
import os
from pathlib import Path

import pytest
from podcast_gpt import cli,web


def test_cli_doctor_and_valid_help(tmp_path):
    p=cli.parse(["--workspace",str(tmp_path),"doctor"])
    assert p.operation=="doctor"
    assert cli.execute(p)["sadtalker_cpu_model_included"] is False


def test_cli_consent_requires_explicit_flag(tmp_path):
    a=cli.parse(["--workspace",str(tmp_path),"tts-one","--turn","3"])
    with pytest.raises(ValueError,match="explicit"):
        cli.execute(a)


def test_local_dashboard_has_no_model_start_or_publish_controls():
    page=web.html_page("f"*64)
    assert "http://127.0.0.1" not in page
    assert "data-action=\"init\"" in page
    assert "data-action=\"readiness\"" in page
    assert "X-CSRF-Token" in page
    assert "connect-src 'self'" in page
    assert "run-cpu" not in page
    assert "upload('/remote" not in page
    assert "https://" not in page

def test_portrait_ui_requires_explicit_local_owner_declaration():
    page=web.html_page("1"*64)
    assert 'id="portraitRights"' in page
    assert "X-Portrait-Rights-Confirmed" in page
    assert "source authentic" not in page.lower()



def test_web_browser_launch_requires_explicit_flag(tmp_path,monkeypatch):
    calls=[]
    monkeypatch.setattr(web,"serve",lambda root,port,*,open_browser: calls.append((port,open_browser)))
    for flags in ([],["--open-browser"]):
        args=cli.parse(["--workspace",str(tmp_path),"web","--port","7861"]+flags)
        assert cli.execute(args)["dashboard_stopped"]
    assert calls==[(7861,False),(7861,True)]


def test_browser_only_opens_after_successful_local_bind(tmp_path,monkeypatch):
    import webbrowser
    events=[]
    class FakeServer:
        def __init__(self,address,handler):
            assert address==("127.0.0.1",7861)
            events.append("bind")
        def serve_forever(self): events.append("serve")
        def server_close(self): events.append("close")
    monkeypatch.setattr(web,"ThreadingHTTPServer",FakeServer)
    monkeypatch.setattr(webbrowser,"open",lambda url: events.append(url) or True)
    web.serve(tmp_path/"private",7861,open_browser=True)
    assert events==["bind","http://127.0.0.1:7861","serve","close"]
    events.clear()
    def occupied(*args):
        raise OSError("Port occupied")
    monkeypatch.setattr(web,"ThreadingHTTPServer",occupied)
    with pytest.raises(OSError,match="occupied"):
        web.serve(tmp_path/"private",7861,open_browser=True)
    assert events==[]


def test_browser_failure_keeps_manual_dashboard_available(tmp_path,monkeypatch):
    import webbrowser
    events=[]
    class FakeServer:
        def __init__(self,*args): pass
        def serve_forever(self): events.append("serve")
        def server_close(self): events.append("close")
    def unavailable(url):
        raise webbrowser.Error("No browser")
    monkeypatch.setattr(web,"ThreadingHTTPServer",FakeServer)
    monkeypatch.setattr(webbrowser,"open",unavailable)
    web.serve(tmp_path/"private",7861,open_browser=True)
    assert events==["serve","close"]
