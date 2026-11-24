"""Legacy Windows redirected stdout must not fail after writing private project."""
import io
import json
import os
import subprocess
import sys

from podcast_gpt import cli


def test_json_stream_round_trip_in_legacy_and_utf8():
    data={"dialogue":"नमस्ते, आप कैसे हैं?","path":"D:/हिंदी/मेरी फ़ाइल"}
    for encoding in ("cp1252","ascii","utf-8"):
        buffer=io.BytesIO()
        stream=io.TextIOWrapper(buffer,encoding=encoding,errors="strict")
        cli._print_json(data,stream)
        stream.flush()
        raw=buffer.getvalue()
        assert json.loads(raw.decode(encoding))==data
        if encoding=="utf-8":
            assert "नमस्ते".encode("utf-8") in raw
        else:
            assert b"\\u" in raw


def test_redirected_legacy_cli_init_and_readiness(tmp_path):
    root=tmp_path/"Hindi private studio"
    env={**os.environ,"PYTHONIOENCODING":"cp1252:strict"}
    for op in ("init","readiness"):
        proc=subprocess.run([sys.executable,"-m","podcast_gpt","--workspace",str(root),op],
                            env=env,capture_output=True,timeout=60)
        assert proc.returncode==0,proc.stderr
        assert isinstance(json.loads(proc.stdout.decode("cp1252")),dict)
    assert (root/"project.json").is_file()


def test_legacy_cli_error_has_no_secondary_encoding_failure(monkeypatch):
    buffer=io.BytesIO()
    stream=io.TextIOWrapper(buffer,encoding="cp1252",errors="strict")
    monkeypatch.setattr(cli.sys,"stderr",stream)
    cli._print_error(ValueError("हिंदी"))
    stream.flush()
    assert b"BLOCKED:" in buffer.getvalue()
    assert b"\\u" in buffer.getvalue()
