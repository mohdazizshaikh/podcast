@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Podcast GPT - ORIGINAL 3-PRESENTER HINDI STUDIO v3
rem Optional setup-only mode for clean deployment checks; no server/browser.
set "SETUP_ONLY=0"
if /I "%~1"=="--setup-only" set "SETUP_ONLY=1"
set "BASE=%PODCAST_WORKSPACE%"
if not defined BASE set "BASE=%USERPROFILE%\PodcastGPTStudio"
where ffmpeg.exe >nul 2>nul
if errorlevel 1 goto :missingffmpeg
where ffprobe.exe >nul 2>nul
if errorlevel 1 goto :missingffmpeg
if exist ".venv\Scripts\python.exe" goto :checkvenv
set "PYPATH=py -3.11"
%PYPATH% -c "import sys; assert sys.version_info >= (3,10)" >nul 2>nul
if not errorlevel 1 goto :createvenv
set "PYPATH=py -3.12"
%PYPATH% -c "import sys; assert sys.version_info >= (3,10)" >nul 2>nul
if not errorlevel 1 goto :createvenv
set "PYPATH=py -3"
%PYPATH% -c "import sys; assert sys.version_info >= (3,10)" >nul 2>nul
if not errorlevel 1 goto :createvenv
set "PYPATH=python"
%PYPATH% -c "import sys; assert sys.version_info >= (3,10)" >nul 2>nul
if errorlevel 1 goto :missingpython
:createvenv
echo [SETUP] Creating local Python app virtual environment...
%PYPATH% -m venv .venv
if errorlevel 1 goto :failed
:checkvenv
".venv\Scripts\python.exe" -c "import sys; assert sys.version_info >= (3,10)" >nul 2>nul
if errorlevel 1 goto :brokenvenv
rem Avoid network/package changes on normal starts. The helper checks the
rem installed editable package and records the exact pyproject.toml digest.
".venv\Scripts\python.exe" -m podcast_gpt.bootstrap check >nul 2>nul
if not errorlevel 1 goto :launch
echo [SETUP] Installing or refreshing application dependencies only (internet may be needed).
".venv\Scripts\python.exe" -m pip install -e .
if errorlevel 1 goto :failed
".venv\Scripts\python.exe" -m podcast_gpt.bootstrap record
if errorlevel 1 goto :failed
:launch
if "%SETUP_ONLY%"=="1" (
 echo [PASS] Application setup ready. No server or model started.
 exit /b 0
)
echo [LOCAL ONLY] Starting private dashboard; browser opens after successful local bind.
".venv\Scripts\python.exe" -m podcast_gpt --workspace "%BASE%" web --port 7860 --open-browser
if errorlevel 1 goto :failed
exit /b 0
:missingffmpeg
echo [BLOCKED] FFmpeg and FFprobe required on PATH.
echo Example: winget install Gyan.FFmpeg
echo Open a new CMD window after installation.
goto :failed
:missingpython
echo [BLOCKED] Python 3.10 or newer required. Python 3.11 recommended.
goto :failed
:brokenvenv
echo [BLOCKED] Existing .venv Python is missing dependencies or incompatible.
echo Rename only the application .venv folder and retry; do NOT rename or delete your private workspace.
goto :failed
:failed
echo [BLOCKED] Setup or local server failed. Originals were not intentionally modified.
if "%SETUP_ONLY%"=="0" pause
exit /b 1
