@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Podcast GPT - Local genuine Hindi Kokoro ONNX CPU WAV (NO downloads)
if not exist ".venv\Scripts\python.exe" goto :failed
set "BASE=%~1"
if not defined BASE set "BASE=%PODCAST_WORKSPACE%"
if not defined BASE set "BASE=%USERPROFILE%\PodcastGPTStudio"
if not exist "%BASE%\project.json" goto :failed
if exist "%BASE%\source\source-manifest.json" (
 echo [BLOCKED] Signed original WAVs already bound. Never replace them!
 exit /b 1
)
echo.
echo [KOKORO] Optional REAL local Hindi ONNX CPU voice generation.
echo Uses distinct Hindi presets: Aarav hm_omega, Meera hf_alpha, Kabir hm_psi.
echo Requires model and compatible voice pack installed by YOU, plus eSpeak-ng.
echo Only ORIGINAL new WAVs; no face video, internet TTS or publishing.
echo.
echo Install Python optional packages once when online if needed:
echo   .venv\Scripts\python.exe -m pip install -e ".[kokoro]"
set "MODEL="
set /p "MODEL=Local existing kokoro-v1.0.onnx FULL path: "
set "MODEL=%MODEL:"=%"
if not exist "%MODEL%" goto :failed
set "VOICES="
set /p "VOICES=Local existing voices-v1.0.bin FULL path: "
set "VOICES=%VOICES:"=%"
if not exist "%VOICES%" goto :failed
set "COUNT=3"
set /p "COUNT=Maximum NEW Hindi WAVs this invocation, 1-5 [default 3]: "
if not defined COUNT set "COUNT=3"
setlocal EnableDelayedExpansion
if "!COUNT!"=="1" (endlocal & set "COUNT=1" & goto :countok)
if "!COUNT!"=="2" (endlocal & set "COUNT=2" & goto :countok)
if "!COUNT!"=="3" (endlocal & set "COUNT=3" & goto :countok)
if "!COUNT!"=="4" (endlocal & set "COUNT=4" & goto :countok)
if "!COUNT!"=="5" (endlocal & set "COUNT=5" & goto :countok)
endlocal
goto :failed
:countok
echo.
echo [CONSENT] Run actual Kokoro ONNX model locally on up to %COUNT% new turns.
echo No model weight downloads, cloud calls, overwrites or auto-inference.
set "YESNO="
set /p "YESNO=Type YES to run this ONE bounded CPU voice generation: "
setlocal EnableDelayedExpansion
if not "!YESNO!"=="YES" (endlocal & goto :cancel)
endlocal
".venv\Scripts\python.exe" -m podcast_gpt --workspace "%BASE%" tts-kokoro --model "%MODEL%" --voices "%VOICES%" --next --max-new "%COUNT%" --run-local
if errorlevel 1 goto :failed
echo [PASS] Generated original private Hindi PCM WAVs, not approved lip-sync.
exit /b 0
:cancel
echo [CANCELLED] No local Kokoro model called.
exit /b 2
:failed
echo [BLOCKED] Source folder, local ONNX, voices, G2P, consent or output validation failed.
exit /b 1