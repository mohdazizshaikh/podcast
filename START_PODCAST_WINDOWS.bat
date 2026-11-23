@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Podcast GPT - ORIGINAL 3-PRESENTER HINDI STUDIO v3
set "PYPATH=py -3.11"
py -3.11 -c "import sys" >nul 2>nul
if errorlevel 1 set "PYPATH=python"
if not exist ".venv\Scripts\python.exe" (
  echo [SETUP] Creating local Python app virtual environment...
  %PYPATH% -m venv .venv
  if errorlevel 1 goto :failed
)
echo [SETUP] Installing only Python application packages; no AI model weights downloaded.
".venv\Scripts\python.exe" -m pip install -e .
if errorlevel 1 goto :failed
where ffmpeg.exe >nul 2>nul
if errorlevel 1 (
 echo [BLOCKED] FFmpeg required. Install FFmpeg and put ffmpeg and ffprobe on PATH.
 echo Example: winget install Gyan.FFmpeg
 goto :failed
)
where ffprobe.exe >nul 2>nul
if errorlevel 1 goto :failed
set "BASE=%PODCAST_WORKSPACE%"
if not defined BASE set "BASE=%USERPROFILE%\PodcastGPTStudio"
echo [LOCAL ONLY] Opening browser at http://127.0.0.1:7860
start "" "http://127.0.0.1:7860"
".venv\Scripts\python.exe" -m podcast_gpt --workspace "%BASE%" web --port 7860
if errorlevel 1 goto :failed
exit /b 0
:failed
echo [BLOCKED] Setup or local server failed. Originals were not intentionally modified.
pause
exit /b 1