@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Podcast GPT - Consented real SadTalker local CPU previews
if not exist ".venv\Scripts\python.exe" goto :failed
set "BASE=%~1"
if not defined BASE set "BASE=%PODCAST_WORKSPACE%"
if not defined BASE set "BASE=%USERPROFILE%\PodcastGPTStudio"
set "BASE=%BASE:"=%"
if not exist "%BASE%\source\chunks-manifest.json" goto :failed
echo.
echo [VERIFY] Genuine original source exact PCM and existing saved MP4s.
".venv\Scripts\python.exe" -m podcast_gpt --workspace "%BASE%" verify-chunks
if errorlevel 1 goto :failed
".venv\Scripts\python.exe" -m podcast_gpt --workspace "%BASE%" progress
if errorlevel 1 goto :failed
set "MODE=%~2"
if not defined MODE set /p "MODE=Enter PILOT (3 presenters), BATCH (<=5) or SESSION (<=20): "
setlocal EnableDelayedExpansion
if /I "!MODE!"=="PILOT" (endlocal & set "MODE=pilot" & goto :mode_ok)
if /I "!MODE!"=="BATCH" (endlocal & set "MODE=batch" & goto :mode_ok)
if /I "!MODE!"=="SESSION" (endlocal & set "MODE=session" & goto :mode_ok)
endlocal
goto :cancel
:mode_ok
set "COUNT=3"
if /I "%MODE%"=="batch" set "COUNT=1"
if /I "%MODE%"=="session" set "COUNT=3"
if /I not "%MODE%"=="pilot" set /p "COUNT=Number of NEW samples for this ONE call [default 1 batch/3 session]: "
if not defined COUNT goto :failed
set "STROOT="
set /p "STROOT=Existing legitimate SadTalker root containing inference.py: "
set "STROOT=%STROOT:"=%"
if not exist "%STROOT%\inference.py" goto :failed
set "STPY=%STROOT%\.venv38\Scripts\python.exe"
if not exist "%STPY%" goto :failed
echo.
echo [READ ONLY] Checking local SadTalker CLI, pretrained checkpoint files
echo and Python interpreter before asking to run any AI model.
".venv\Scripts\python.exe" -m podcast_gpt --workspace "%BASE%" check-sadtalker --sadtalker-root "%STROOT%" --sadtalker-python "%STPY%"
if errorlevel 1 goto :failed
echo.
echo [EXPLICIT CONSENT] This invokes ACTUAL locally installed CPU pretrained
 echo models on original face PNGs and original Hindi voice. You affirm you
 echo own the portraits or have written permission for ALL THREE presenters.
echo CPU/RAM heavy. No GPU required but very slow on some computers.
echo Existing clips are reverified; models are NOT downloaded or faked.
set "YESNO="
set /p "YESNO=Type EXACTLY YES to authorize this session: "
if not "%YESNO%"=="YES" goto :cancel
".venv\Scripts\python.exe" -m podcast_gpt --workspace "%BASE%" run-cpu --mode "%MODE%" --max-new "%COUNT%" --wall-seconds 7200 --per-chunk-timeout 1800 --sadtalker-root "%STROOT%" --sadtalker-python "%STPY%" --rights-confirmed
if errorlevel 1 goto :failed
echo [PASS] Saved real model previews; manual Hindi lip-sync inspection still required.
exit /b 0
:cancel
echo [CANCELLED] No real neural model invoked.
exit /b 2
:failed
echo [BLOCKED] Missing source, virtual environment, model, or unsafe params.
exit /b 1