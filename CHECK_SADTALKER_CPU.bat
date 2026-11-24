@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Podcast GPT - READ ONLY model installation preflight
if not exist ".venv\Scripts\python.exe" (
 echo [BLOCKED] First install app via START_PODCAST_WINDOWS.bat
 exit /b 1
)
set "BASE=%~1"
if not defined BASE set "BASE=%PODCAST_WORKSPACE%"
if not defined BASE set "BASE=%USERPROFILE%\PodcastGPTStudio"
set "BASE=%BASE:"=%"
echo.
echo [READ ONLY] No real SadTalker model load, inference, downloads, portraits,
echo saved voice files or rendered videos are touched by this check.
set "STROOT="
set /p "STROOT=Full path to your installed SadTalker root (inference.py): "
set "STROOT=%STROOT:"=%"
if not exist "%STROOT%\inference.py" goto :failed
set "STPY=%STROOT%\.venv38\Scripts\python.exe"
if exist "%STPY%" goto :python_ok
set "STPY="
set /p "STPY=Full path to existing SadTalker Python executable: "
set "STPY=%STPY:"=%"
:python_ok
".venv\Scripts\python.exe" -m podcast_gpt --workspace "%BASE%" check-sadtalker --sadtalker-root "%STROOT%" --sadtalker-python "%STPY%"
if errorlevel 1 goto :failed
echo [PASS] STRUCTURAL ONLY. This is NOT a trained-model runtime, lipsync
echo quality, creator-rights or ten-minute completion certificate.
exit /b 0
:failed
echo [BLOCKED] Read-only model installation preflight incomplete.
exit /b 1
