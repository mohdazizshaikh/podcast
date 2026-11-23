@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
set "BASE=%~1"
if not defined BASE set "BASE=%PODCAST_WORKSPACE%"
if not defined BASE set "BASE=%USERPROFILE%\PodcastGPTStudio"
if not exist ".venv\Scripts\python.exe" exit /b 1
echo [READ ONLY] Rechecking all signed sources and genuinely saved face MP4s.
".venv\Scripts\python.exe" -m podcast_gpt --workspace "%BASE%" review-pilot
if errorlevel 1 exit /b 1
echo Open the generated PRIVATE .html in your review folder.
echo This is NOT an automatic quality check or publishing approval.
set "A="
set "M="
set "K="
set /p "A=After reviewing Aarav, enter PASS or FAIL: "
set /p "M=After reviewing Meera, enter PASS or FAIL: "
set /p "K=After reviewing Kabir, enter PASS or FAIL: "
echo You are recording your PRIVATE observations only; NOT automatic proof.
set "YES="
set /p "YES=Type I_REVIEWED_ALL_THREE_ORIGINAL_HINDI_FACES exactly: "
if not "%YES%"=="I_REVIEWED_ALL_THREE_ORIGINAL_HINDI_FACES" exit /b 2
".venv\Scripts\python.exe" -m podcast_gpt --workspace "%BASE%" record-pilot --aarav "%A%" --meera "%M%" --kabir "%K%" --acknowledgment "%YES%"
exit /b %ERRORLEVEL%