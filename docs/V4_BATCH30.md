# Batch 30 — optional speech compression

New project-mix-compose flags: --compress-ratio 1–6 (1 disables), --compress-threshold 2000–20000 PCM (default 12000). Immediate peak capture with approximately 100 ms integer release. Applies only to normalized speech before bed summing. Optional ducking and static LUFS-target gain remain compatible. Old default recipes and receipts unchanged; exact PCM audit reconstructs compression. No original master modification, makeup gain, lookahead, dynamic true-peak limiter, denoising or automatic approval.

Example:
```cmd
.venv\Scripts\python.exe -m podcast_gpt project-mix-compose --project-id PROJECT_ID --compress-ratio 4 --compress-threshold 8000 --acknowledgment I_HAVE_RIGHTS_TO_ALL_ADDED_AUDIO_AND_AUTHORIZE_LOCAL_MIX
```
135 test cases authored (125 signed compression parameter combinations, 8 invalid settings, release/legacy and synthetic mix audit). New CI pending; not 135 separate features. Actual listening, real model/device acceptance pending. Batch 29 CI five core jobs passed; packaging running at check.

## Static voice and device preflight
CLI `project-voice-preflight --project-id PROJECT_ID` and `project-device-acceptance --project-id PROJECT_ID`, plus browser buttons. Reports static preset/language mismatch, duplicates, saved path status, unsupported engines, current readiness, measured audio duration when available and remaining physical-device checks. eSpeak static check is not an installed inventory. Browser per-turn PCM diagnostics also exposed. No engine execution, automatic physical acceptance or production approval. Three more regression tests authored; CI pending.

## Graphical mix authoring
Dashboard Audio post-production sends one bounded JSON request (8.5 MB maximum) with base64-encoded local WAVs, optional intro/outro up to 30 seconds each and background up to 120 seconds. Exact PCM16 mono 16 kHz validation and rights/general authoring consent required. Controls expose speech/music peak, ducking, static LUFS target and compression. Private temporary staging uses fixed filenames, cleans up on normal failure/success; abrupt shutdown may leave scratch. No external upload, arbitrary input paths or overwrite. Nineteen additional test cases authored (one synthetic mix audit, twelve invalid requests, five invalid bodies, one consent/markup case). Total batch 30: 157 authored test cases (135 + 3 + 19), not separate product features. Actual browser interaction remains pending.

Batch 29 and 30 CI completed successfully (45494573255, 45495891248 latest combined: 6/6 each). Batch 31 adds explicitly consented local CPU portrait candidate generation with safetensors inventory and immutable candidate receipt; new CI pending. Real model setup, physical acceptance and portrait quality remain unverified. See docs/V4_BATCH31.md (repository-relative).

Batch 35 implements optional deterministic whole-mix dynamic sample-peak limiting, including intro/bed/outro, immutable exact PCM audit, CLI/browser setting and legacy defaults. 63 new regression cases authored; 58 standalone limiter cases passed in an isolated local Python harness, five repository integration cases and full CI unverified. Sample peaks are not intersample true peaks; dynamic true-peak limiting, combined LUFS normalization, real listening and physical Windows/model acceptance remain pending. See V4_BATCH35.md.
