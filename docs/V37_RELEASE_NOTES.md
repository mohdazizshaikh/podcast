# Podcast GPT v3.7.0 — cross-process original-source protection

New canonical repository: https://github.com/mohdazizshaikh/podcast

Reconstructed from accessible Podcast Project requirements; no source pull
from the suspended account or claimed byte-identical old Git history.

## The problem this release addresses

Before v3.7 the source manifest (`BIND`) and separate offline/online voice
generators could run concurrently in different Windows/Python processes.
Also the localhost dashboard's upload mutex only covered HTTP threads,
not a second external CLI process editing the same original WAV files.
Real 10-minute Hindi scripts can take a long time to synthesize on a CPU;
this time-of-check race risked attaching the wrong original WAV to signed
source evidence or confusing users about an incomplete import.

## Implemented safeguards

1. `build-source`, `tts-kokoro`, optional networked `tts-one` and the
   localhost dashboard's PNG/WAV import all acquire the SAME
   `source/originals-voice-and-binding-exclusive.lock` file under the private
   studio before changing any original. Acquisition is atomic (`open('x')`)
   with an owner-specific marker and fsync, and blocks if the lock exists.
   It only releases a lock carrying its own marker, never an unrelated one.
2. Source binding cannot succeed during a slow voice generation. Kokoro
   rechecks source text and manifest presence before adopting WAVs; Edge
   TTS rechecks its project, media and manifest after the network await.
   Neither will overwrite existing SHA-bound original audio.
3. Browser upload still works before project INIT, but safely creates only
   the private source-lock directory if missing. Once BIND succeeds, all
   late PNG/WAV imports are refused, even via a separate browser/CLI.
4. Read-only `READINESS` reports an active/interrupted originals lock as
   `original_voice_source_session: blocked`, preventing false readiness
   when source files may be partially written.
5. New private workspace initialization is forbidden inside any Git
   worktree/repository, including linked Git worktree `.git` files, to
   prevent accidental publication of original portraits, Hindi voices,
   local model outputs and private troubleshooting logs.

## Verification scope

GitHub Actions includes a second independent Python process trying to
`build-source` while an exclusive lock is held, offline Kokoro/online Edge
provider refusal before model/network calls, real localhost HTTP upload
under a competing lock, post-binding upload refusal, read-only readiness
lock detection, and symlink/worktree privacy cases. CI also runs the
existing synthetic 45-turn FFmpeg video source/encoder/decode tests.

**Important:** No CI job has loaded genuine SadTalker pretrained weights
or produced/quality-reviewed 10 minutes of natural Hindi face/lip video.
Real user-authorized portraits and 45 original 540–660s Hindi WAVs,
model CPU/RAM testing, actual mouth movement, three human pilot PASS/FAIL
and final 45-turn human review remain device/user-dependent.

## Run on Windows

```powershell
cd podcast
git pull origin main
.\START_PODCAST_WINDOWS.bat
```

In the private dashboard or `CONTINUE_FULL_HINDI_NEURAL.bat`, use
`READINESS` to identify the exact next safe stage. Keep real media outside
the Git repo. Never delete a source lock while any authoring process is active.
