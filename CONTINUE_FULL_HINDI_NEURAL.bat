@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Podcast GPT - ONE guided original Hindi step v3.1
set "BASE=%~1"
if not defined BASE set "BASE=%PODCAST_WORKSPACE%"
if not defined BASE set "BASE=%USERPROFILE%\PodcastGPTStudio"
rem cmd.exe /c can preserve surrounding literal quotes in first BAT arg.
rem Strip double quote characters before passing one safe quoted workspace arg.
set "BASE=%BASE:"=%"
if not exist ".venv\Scripts\python.exe" (
 echo [BLOCKED] Run START_PODCAST_WINDOWS.bat first.
 exit /b 1
)
echo.
echo ================================================================
echo ORIGINAL HINDI 45 TURNS - ONE SAFE STEP EACH INVOCATION
 echo ================================================================
echo INIT      - NEW private original 45-turn script
 echo KOKORO    - optional OFFLINE original Hindi 3-voice local CPU synthesis
 echo BIND      - verify originals and write immutable SHA manifest
 echo CHUNKS    - export exact 1-10sec PCM source segments
 echo STATIC    - create true 720p original Hindi static AAC + SRT
 echo AUDIT     - independently decode/check static MP4
 echo PILOT     - real face one-per-presenter, separate YES consent
 echo BATCH     - max 5 real CPU clips, separate YES consent
 echo SESSION   - bounded real CPU clips, separate YES consent
 echo PROGRESS  - read-only independently decode saved MP4 previews
 echo RECOVERY  - read-only interrupted model attempt inventory
 echo BUDGET    - READ ONLY estimated CPU hours from measured saved previews
 echo READINESS - READ ONLY stage-by-stage original 45-turn workspace audit
 echo MODEL     - READ ONLY installed SadTalker CPU environment check
 echo REVIEW    - local private 3-face sample HTML (real clips required)
 echo RECORD    - manual three face PASS/FAIL observation record
 echo INSPECT   - verify manual observation against current media
 echo COMPOSE   - full face candidate from ALL real model clips
 echo AUDITFULL - independently decode full face MP4/AAC/SRT
 echo REVIEWFULL- private 45-turn human review navigator
 echo TEMPLATEFULL - create private 45-turn manual PASS/FAIL template
 echo INSPECTFULL - read-only final human observation record audit
 echo NO        - exit without action
 echo.
set "STEP="
set /p "STEP=Select exactly ONE action: "
setlocal EnableDelayedExpansion
if /I "!STEP!"=="INIT" (endlocal & goto :init)
if /I "!STEP!"=="KOKORO" (endlocal & goto :kokoro)
if /I "!STEP!"=="BIND" (endlocal & goto :bind)
if /I "!STEP!"=="CHUNKS" (endlocal & goto :chunks)
if /I "!STEP!"=="STATIC" (endlocal & goto :static)
if /I "!STEP!"=="AUDIT" (endlocal & goto :audit)
if /I "!STEP!"=="PILOT" (endlocal & goto :cpu_pilot)
if /I "!STEP!"=="BATCH" (endlocal & goto :cpu_batch)
if /I "!STEP!"=="SESSION" (endlocal & goto :cpu_session)
if /I "!STEP!"=="PROGRESS" (endlocal & goto :progress)
if /I "!STEP!"=="RECOVERY" (endlocal & goto :recovery)
if /I "!STEP!"=="BUDGET" (endlocal & goto :budget)
if /I "!STEP!"=="READINESS" (endlocal & goto :readiness)
if /I "!STEP!"=="MODEL" (endlocal & goto :model)
if /I "!STEP!"=="REVIEW" (endlocal & goto :review)
if /I "!STEP!"=="RECORD" (endlocal & goto :record)
if /I "!STEP!"=="INSPECT" (endlocal & goto :inspect)
if /I "!STEP!"=="COMPOSE" (endlocal & goto :compose)
if /I "!STEP!"=="AUDITFULL" (endlocal & goto :auditfull)
if /I "!STEP!"=="REVIEWFULL" (endlocal & goto :reviewfull)
if /I "!STEP!"=="TEMPLATEFULL" (endlocal & goto :templatefull)
if /I "!STEP!"=="INSPECTFULL" (endlocal & goto :inspectfull)
endlocal
exit /b 2
:init
".venv\Scripts\python.exe" -m podcast_gpt --workspace "%BASE%" init
exit /b %ERRORLEVEL%
:kokoro
call "%~dp0GENERATE_KOKORO_HINDI_CPU.bat" "%BASE%"
exit /b %ERRORLEVEL%
:bind
".venv\Scripts\python.exe" -m podcast_gpt --workspace "%BASE%" build-source
exit /b %ERRORLEVEL%
:chunks
".venv\Scripts\python.exe" -m podcast_gpt --workspace "%BASE%" prepare-chunks
exit /b %ERRORLEVEL%
:static
".venv\Scripts\python.exe" -m podcast_gpt --workspace "%BASE%" render-static
exit /b %ERRORLEVEL%
:audit
".venv\Scripts\python.exe" -m podcast_gpt --workspace "%BASE%" audit-static
exit /b %ERRORLEVEL%
:cpu_pilot
call "%~dp0RUN_NEURAL_CPU.bat" "%BASE%" "PILOT"
exit /b %ERRORLEVEL%
:cpu_batch
call "%~dp0RUN_NEURAL_CPU.bat" "%BASE%" "BATCH"
exit /b %ERRORLEVEL%
:cpu_session
call "%~dp0RUN_NEURAL_CPU.bat" "%BASE%" "SESSION"
exit /b %ERRORLEVEL%
:progress
".venv\Scripts\python.exe" -m podcast_gpt --workspace "%BASE%" progress
exit /b %ERRORLEVEL%
:recovery
".venv\Scripts\python.exe" -m podcast_gpt --workspace "%BASE%" recovery
exit /b %ERRORLEVEL%
:budget
".venv\Scripts\python.exe" -m podcast_gpt --workspace "%BASE%" budget
exit /b %ERRORLEVEL%
:readiness
".venv\Scripts\python.exe" -m podcast_gpt --workspace "%BASE%" readiness
exit /b %ERRORLEVEL%
:model
call "%~dp0CHECK_SADTALKER_CPU.bat" "%BASE%"
exit /b %ERRORLEVEL%
:review
".venv\Scripts\python.exe" -m podcast_gpt --workspace "%BASE%" review-pilot
exit /b %ERRORLEVEL%
:record
call "%~dp0REVIEW_THREE_PRESENTER_PILOT.bat" "%BASE%"
exit /b %ERRORLEVEL%
:inspect
".venv\Scripts\python.exe" -m podcast_gpt --workspace "%BASE%" inspect-pilot
exit /b %ERRORLEVEL%
:compose
".venv\Scripts\python.exe" -m podcast_gpt --workspace "%BASE%" compose-neural
exit /b %ERRORLEVEL%
:auditfull
".venv\Scripts\python.exe" -m podcast_gpt --workspace "%BASE%" audit-neural
exit /b %ERRORLEVEL%
:reviewfull
".venv\Scripts\python.exe" -m podcast_gpt --workspace "%BASE%" review-full
exit /b %ERRORLEVEL%
:templatefull
".venv\Scripts\python.exe" -m podcast_gpt --workspace "%BASE%" template-full-review
exit /b %ERRORLEVEL%
:inspectfull
".venv\Scripts\python.exe" -m podcast_gpt --workspace "%BASE%" inspect-full-review
exit /b %ERRORLEVEL%
