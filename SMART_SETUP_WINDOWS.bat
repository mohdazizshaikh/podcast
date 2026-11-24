@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Podcast GPT V4 - Smart local setup
set "BASE=%PODCAST_WORKSPACE%"
if not defined BASE set "BASE=%USERPROFILE%\PodcastGPTStudio"
if not exist ".venv\Scripts\python.exe" (
 echo First run START_PODCAST_WINDOWS.bat --setup-only to install application dependencies.
 echo No model downloads will be started.
 pause
 exit /b 1
)
".venv\Scripts\python.exe" -m podcast_gpt setup-wizard --interactive
set "RESULT=%ERRORLEVEL%"
pause
exit /b %RESULT%
