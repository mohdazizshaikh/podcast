@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
echo.
echo PODCAST GPT - RESTORE FULL ORIGINAL LOCAL CLONE TO NEW REPO
echo Destination: https://github.com/mohdazizshaikh/podcast.git
echo Source: your EXISTING LOCAL original full Git clone ONLY.
echo No connection to any suspended account. No source changes.
echo.
set "SOURCE=%~1"
if not defined SOURCE set /p "SOURCE=Full existing local podcast-gpt clone folder: "
set "SOURCE=%SOURCE:"=%"
if not exist "%SOURCE%\.git" goto :blocked
if not exist "..\.git" goto :blocked
where py >nul 2>&1
if errorlevel 1 goto :blocked
py -3 "%~dp0migrate_from_local.py" --source "%SOURCE%"
if errorlevel 1 goto :blocked
echo.
echo DRY-RUN finished. Verify inventory/count and confirm no secrets.
echo IMPORTANT: Destination GitHub repo is PUBLIC, and ALL Git history
echo will become visible. Review old commits for leaked API keys or
echo confidential media before consenting to publish.
choice /C YN /M "Publish full local project into new GitHub repo?"
if errorlevel 2 exit /b 0
set "BACKUP=%USERPROFILE%\Podcast-Git-Migration-Backups"
py -3 "%~dp0migrate_from_local.py" --source "%SOURCE%" --publish --backup-dir "%BACKUP%" --v298-patch "%~dp0v298-offline.patch"
if errorlevel 1 goto :blocked
echo.
echo SUCCESS: new repo MAIN has original committed source AND local changes.
echo Backup bundle saved to %BACKUP%
exit /b 0
:blocked
echo.
echo BLOCKED: original source absent, risky media/credentials, or Git error.
echo No success claimed. Run again after correcting inventory and access.
exit /b 1