@echo off
setlocal EnableExtensions DisableDelayedExpansion
title Podcast GPT - Apply additive v2.98 offline quality patch
echo.
echo Podcast GPT v2.98 OFFLINE quality review patch (no AI or downloads)
echo This does not push to GitHub, install models, or change private media.
echo The patch adds NEW code files only. Existing files are not overwritten.
echo.
set "REPO=%~1"
if not defined REPO if exist "%~dp0.git\" set "REPO=%~dp0"
if not defined REPO set /p "REPO=Enter your existing local podcast-gpt clone directory: "
set "REPO=%REPO:"=%"
if not defined REPO goto :fail
if not exist "%REPO%\.git" goto :fail
where git.exe >nul 2>nul
if errorlevel 1 goto :fail
if not exist "%~dp0v298-offline.patch" goto :fail
cd /d "%REPO%"
if errorlevel 1 goto :fail
echo [CHECK] Verify this exact new-files patch applies without collisions...
git apply --check "%~dp0v298-offline.patch"
if errorlevel 1 goto :fail
echo [APPLY] Add new pilot reviewer source, tests and instructions...
git apply "%~dp0v298-offline.patch"
if errorlevel 1 goto :fail
echo.
echo [PASS] Offline v2.98 ADDITIVE patch applied to your local clone.
echo No GitHub push or model rendering was attempted.
echo Next: inspect docs\V298_RELEASE_NOTES.md and run the three-face review
echo AFTER a verified Aarav / Meera / Kabir original Hindi pilot exists.
exit /b 0

:fail
echo.
echo [BLOCKED] Existing local Git clone, installed Git or clean patch check
echo was unavailable. No models and no source media were intentionally changed.
exit /b 1