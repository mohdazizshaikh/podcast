# Batch 30 — optional speech compression

New project-mix-compose flags: --compress-ratio 1–6 (1 disables), --compress-threshold 2000–20000 PCM (default 12000). Immediate peak capture with approximately 100 ms integer release. Applies only to normalized speech before bed summing. Optional ducking and static LUFS-target gain remain compatible. Old default recipes and receipts unchanged; exact PCM audit reconstructs compression. No original master modification, makeup gain, lookahead, dynamic true-peak limiter, denoising or automatic approval.

Example:
```cmd
.venv\Scripts\python.exe -m podcast_gpt project-mix-compose --project-id PROJECT_ID --compress-ratio 4 --compress-threshold 8000 --acknowledgment I_HAVE_RIGHTS_TO_ALL_ADDED_AUDIO_AND_AUTHORIZE_LOCAL_MIX
```
135 test cases authored (125 signed compression parameter combinations, 8 invalid settings, release/legacy and synthetic mix audit). New CI pending; not 135 separate features. Actual listening, real model/device acceptance pending. Batch 29 CI five core jobs passed; packaging running at check.
