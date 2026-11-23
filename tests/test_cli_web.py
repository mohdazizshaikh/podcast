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
