# Podcast GPT v3.4.0 — External CPU model integration reliability

Canonical new account/repo: https://github.com/mohdazizshaikh/podcast

Reconstructed from project chat specifications. The suspended GitHub account
was not accessed. The original repository's exact source/history cannot be
proven identical to this reconstruction.

## Changes

1. **Real subprocess boundary is now in CI.** The test launches a separate
   local Python executable with SadTalker's official CPU, original audio,
   source image, result directory, still and preprocessing flags. A **test-only**
   fake executable generates a short static video in the official
   timestamp-named result-MP4 location. The wrapper must discover, independently
   FFmpeg-decode, hash-bind and checkpoint one preview per Hindi presenter.
   A second PILOT invocation must reuse all three saved clips (zero new model
   calls), and missing output must never be accepted. This does not use
   pretrained SadTalker, actual moving lips or original user content.
2. **Private external-process diagnostics.** Instead of capturing potentially
   large model stdout/stderr in memory then discarding them, the real subprocess
   writes to `PRIVATE_WORKSPACE/scratch/model-<chunk>/model-stdout.log`
   and `model-stderr.log`. On failure/nonzero exit/timeout, the private scratch
   folder is preserved for user troubleshooting; no completed MP4 sidecar
   is emitted. On success, scratch and its transient logs are removed.
3. **Safer CPU voice intermediates.** Kokoro original PCM normalization is
   staged on the private workspace scratch volume, not Windows C: TEMP, with
   an explicit 100 MiB free-space and symlink guard.
4. **Read-only Python version preflight isolation.** Check the selected
   user's SadTalker interpreter with `python -I -S -c ...` before real model
   execution. This bypasses the usual site/user import initialization,
   but cannot prove the executable itself or its model weights are safe.

## Windows setup

```powershell
git clone https://github.com/mohdazizshaikh/podcast.git
cd podcast
.\START_PODCAST_WINDOWS.bat
```

After importing or explicitly generating **45 actual** source WAVs,
providing three authorized portrait PNGs, verifying source duration
540–660s and making exact PCM chunks, use
`CONTINUE_FULL_HINDI_NEURAL.bat` and its `MODEL`, `PILOT`, `REVIEW`,
`BATCH`, `SESSION` stages. All real CPU inference remains explicitly
consented, bounded and local.

## Remaining work (user's real hardware / rights required)

Install genuine licensed third-party SadTalker weights and a compatible
Python/FFmpeg environment; run real 3-person face previews; inspect Hindi
mouth sync/voice quality; complete genuine 10-minute render; independently
audit video/audio; perform 45-turn human review. The passing GitHub tests
only prove source and synthetic FFmpeg/media plumbing, not real natural
AI talking-face performance or permission to publish.

Upstream official SadTalker CLI/output reference:
https://github.com/OpenTalker/SadTalker/blob/main/inference.py
