# V4 authorized audio import and measured timeline

This increment implements language-independent authorized PCM speech import, not generalized TTS. It requires a current script self-attested PASS, a complete cast, and authorized distinct PNG portraits (the existing media preflight). Voice preference inventory reports imported/undecided/Kokoro/Edge configuration, but does not claim real voice or language compatibility. V3 Hindi TTS remains separate. No network, inference or paid requests.

Use one exact mono 16-bit 16 kHz PCM WAV per current script turn ID. If needed, convert an authorized recording with local FFmpeg before import. Minimum 0.25 seconds, maximum 120 seconds per turn, total speech bounded to 66 minutes. All-zero PCM and duplicate PCM rejected; these checks do not prove genuine speech, naturalness or different speaker identities.

```cmd
.venv\Scripts\python.exe -m podcast_gpt project-voice-status --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-audio-import --project-id PROJECT_ID --turn-id 0001 --file "D:\Voices\0001.wav" --acknowledgment I_HAVE_RIGHTS_AND_AUDIO_MATCHES_THIS_SCRIPT_TURN
.venv\Scripts\python.exe -m podcast_gpt project-audio-status --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-audio-finalize --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-audio-show --project-id PROJECT_ID
```

Repeat import for each missing turn. The acknowledgment is a human declaration, not independently checked transcript or usage rights. Audio is saved under a script-version/cast/request hash directory. Previous version recordings stay intact, but are not automatically reused by a new approved revision. Each turn has an immutable WAV and receipt binding exact PCM and script turn. Partial/interrupted directories block further work until manually inspected. No automatic deletion or overwriting.

Finalize only when every turn is verified. The timeline uses integer 16 kHz sample offsets, with a fixed 250 ms gap between turns (none after final turn). It records measured speech and pause duration, plus a +/-10% target-duration indicator. A duration outside target is reported, not automatically stretched, clipped or certified. The final timeline is revalidated against actual WAV bytes. This is a measured timeline only, not a composed master WAV or video. Manual audio review, configurable pauses, normalization/mixing, generalized Kokoro/Edge adapters, language compatibility tests and generalized video rendering remain pending. Keep private inputs outside Git.

Local Hindi Kokoro generation and exact master WAV composition are now available through V4_TTS_MASTER.md. The older import-only description applies to the previous increment; actual language/voice compatibility and human listening review remain unverified.
