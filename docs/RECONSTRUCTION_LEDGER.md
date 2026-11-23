# Reconstruction ledger — source provenance

## Known facts supported by available Podcast Project conversation context

- Original goal: three realistic AI presenters (Aarav, Meera, Kabir), 45 Hindi dialogue turns in a ~10-minute episode, natural Hindi voices and moving lips, on Windows WITHOUT dedicated GPU, free components where licensing permits.
- The previous historical development used Kokoro original Hindi WAVs, original signed AAC/SRT/static video, FFmpeg, SadTalker CPU real pretrained one-segment face previews, checkpoints and signed sources. Stages `PILOT`, `BATCH`, `SESSION`, `BUDGET`, `SAMPLES`, `REVIEW`, full neural candidate and human review were discussed/implemented historically.
- The original GitHub account is suspended and **must never be accessed**. The new canonical GitHub account/repository is `mohdazizshaikh/podcast`.
- The previous offline v2.98 patch is retained verbatim in `.migration/v298-offline.patch`, but it targets a different source architecture; do not apply it blindly to new code.

## Reconstructed v3.0 source (new, not copied)

- `podcast_gpt/source.py`: clean original 45-turn script template; 16kHz signed PCM, source image + WAV SHA, exact chunk partition, immutable originals.
- `podcast_gpt/media.py`: actual Pillow + FFmpeg 720p ORIGINAL STATIC MP4/AAC/SRT, FFprobe and real decoder checks.
- `podcast_gpt/neural.py`: opt-in local SadTalker CPU, per-model timeout, bounded one-per-speaker PILOT/BATCH/SESSION, fresh real MP4/JSON SHA and independent FFmpeg decoding, exclusive lock and resume, full candidate composition from genuine clips + original exact speech.
- `podcast_gpt/review.py`: local offline review for three presenters, private pass/fail record and 45-turn full-review navigator. Never approves publishing automatically.
- `podcast_gpt/cli.py` and `podcast_gpt/web.py`: CLI + loopback-only browser dashboard, upload originals to private workspace, CSRF, no media HTTP serving, no model auto-run.
- Windows BATs, packaging, synthetic/FFmpeg tests, Linux/Windows CI.

## Not recoverable from chat summaries / not represented as recovered original code

1. Byte-identical historical source files and exact Git history of former project.
2. Any user's original privately authorized presenter portraits, Kokoro voice WAVs, original actual rendered episode or signed output checkpoints.
3. Exact old Kokoro source files and weight snapshots. Reconstructed v3.1 newly includes optional genuine LOCAL Kokoro ONNX Hindi voice generation with three distinct source voice PRESETS; model weights must be installed by the user. Offline voice quality remains unverified on real hardware.
4. Real SadTalker model weights, their third-party licenses, full 10-minute CPU timing and Hindi phoneme accuracy on the user's Windows computer.
5. Historical v2.97 manifest compatibility (different schema); old v2.98 patch is archived, not silently transplanted.
6. Claims of complete historic parity or natural lip-sync quality approval.

## Rebuilding rather than falsely marking migration complete

This repository is a **new independent implementation based on observed requirements**, retaining previous migration backup tools for optional future legacy import. Complete architectural **functional parity** requires real authorized source inputs and Windows testing; old Git history preservation requires the user's original local Git clone. Do not claim it is a byte-perfect migration.