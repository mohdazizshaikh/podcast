"""Native Windows CMD dispatch tests; harmless staged executables, no AI models."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def windows_stage(tmp_path_factory):
    if os.name!="nt":pytest.skip("Only native Windows cmd.exe can verify BAT branching")
    stage=tmp_path_factory.mktemp("v31 Windows Hindi guided audio studio & spaces")
    shutil.copy2(ROOT/"CONTINUE_FULL_HINDI_NEURAL.bat",stage/"CONTINUE_FULL_HINDI_NEURAL.bat")
    subprocess.run([sys.executable,"-m","venv",str(stage/".venv")],check=True,timeout=120)
    stub=stage/"podcast_gpt";stub.mkdir()
    (stub/"__main__.py").write_text('''import json,os,sys
with open(os.environ["PODCAST_V31_NATIVE_TRACE"],"a",encoding="utf-8") as f:
    f.write("PY:"+json.dumps(sys.argv[1:])+"\\n")
print("TEST ONLY harmless Python command")
''',encoding="utf-8")
    (stage/"RUN_NEURAL_CPU.bat").write_text('''@echo off
>> "%PODCAST_V31_NATIVE_TRACE%" echo NEURAL-STUB:%~2
exit /b 0
''',encoding="ascii")
    (stage/"GENERATE_KOKORO_HINDI_CPU.bat").write_text('''@echo off
>> "%PODCAST_V31_NATIVE_TRACE%" echo KOKORO-STUB
exit /b 0
''',encoding="ascii")
    return stage


def _run(windows_stage,tmp_path,answer:str):
    trace=tmp_path/"native.log"
    base=tmp_path/"private source folder & हिंदी ! important"
    # Workspace paths with Hindi, & and ! are supplied via the supported
    # PODCAST_WORKSPACE environment input, avoiding extra cmd.exe parsing.
    # This is also how users can configure an alternate permanent workspace.
    env={**os.environ,"PODCAST_V31_NATIVE_TRACE":str(trace),
         "PODCAST_WORKSPACE":str(base),"PYTHONIOENCODING":"utf-8"}
    # Launch BAT directly from cwd without a nested CALL or cmd /s,
    # both of which can expand punctuation and quotes a second time.
    cmd='CONTINUE_FULL_HINDI_NEURAL.bat'
    result=subprocess.run(["cmd.exe","/d","/c",cmd],cwd=windows_stage,
                          env=env,input=answer,text=True,encoding="utf-8",errors="replace",
                          capture_output=True,check=False,timeout=60)
    lines=trace.read_text(encoding="utf-8").splitlines() if trace.exists() else []
    return result,lines,base


@pytest.mark.skipif(os.name!="nt",reason="Windows CMD only")
@pytest.mark.parametrize("mode,expected",[
    ("INIT","init"),("BIND","build-source"),("CHUNKS","prepare-chunks"),
    ("STATIC","render-static"),("AUDIT","audit-static"),
    ("PROGRESS","progress"),("REVIEW","review-pilot"),
    ("INSPECT","inspect-pilot"),("COMPOSE","compose-neural"),
    ("AUDITFULL","audit-neural"),("REVIEWFULL","review-full"),
])
def test_one_original_hindi_stage_only(windows_stage,tmp_path,mode,expected):
    result,lines,base=_run(windows_stage,tmp_path,mode+"\n")
    assert result.returncode==0,result.stdout+result.stderr
    assert len(lines)==1,lines
    assert lines[0].startswith("PY:")
    args=json.loads(lines[0][3:])
    assert "--workspace" in args
    assert str(base) in args
    assert args[-1]==expected


@pytest.mark.skipif(os.name!="nt",reason="Windows CMD only")
@pytest.mark.parametrize("mode,expected",[("PILOT","NEURAL-STUB:PILOT"),("BATCH","NEURAL-STUB:BATCH"),
                                        ("SESSION","NEURAL-STUB:SESSION"),("KOKORO","KOKORO-STUB")])
def test_one_real_model_stage_is_only_local_stub_no_inference(windows_stage,tmp_path,mode,expected):
    result,lines,_=_run(windows_stage,tmp_path,mode+"\n")
    assert result.returncode==0,result.stdout+result.stderr
    assert lines==[expected]


@pytest.mark.skipif(os.name!="nt",reason="Windows CMD only")
@pytest.mark.parametrize("mode",["NO\n","garbage\n","PILOT five\n",'evil" & echo INJECTED > malicious.txt\n'])
def test_malformed_or_cancelled_user_choice_does_not_dispatch(windows_stage,tmp_path,mode):
    result,lines,_=_run(windows_stage,tmp_path,mode)
    assert result.returncode==2,result.stdout+result.stderr
    assert lines==[]
    assert not (windows_stage/"malicious.txt").exists()

@pytest.mark.skipif(os.name!="nt",reason="Windows CMD only")
def test_plain_ascii_commandline_workspace_is_forwarded(windows_stage,tmp_path):
    trace=tmp_path/"plain_trace.jsonl"
    base=tmp_path/"private workspace with spaces"
    env={**os.environ, "PODCAST_V31_NATIVE_TRACE":str(trace),
         "PYTHONIOENCODING":"utf-8"}
    env.pop("PODCAST_WORKSPACE",None)
    # Pass the command as ONE raw CreateProcessW string. A Python argv
    # list with embedded quoted CMD commands introduces backslash-escaping
    # that CMD treats as literal characters, not quote escaping.
    native_command=f'cmd.exe /d /c CONTINUE_FULL_HINDI_NEURAL.bat "{base}"'
    result=subprocess.run(native_command,
                          cwd=windows_stage,env=env,input="INIT\n",text=True,
                          encoding="utf-8",errors="replace",capture_output=True,
                          check=False,timeout=60)
    assert result.returncode==0,result.stdout+result.stderr
    call=json.loads(trace.read_text(encoding="utf-8").splitlines()[0][3:])
    assert call==["--workspace",str(base),"init"]
