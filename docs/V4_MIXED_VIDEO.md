# V4 optional mixed video candidate

The original speech-only neural candidate and exact PCM master remain immutable. Optional post-audio WAV needs its own complete listening review before mixed video composition. Edit the private JSON template, set every turn and criterion PASS or FAIL, then record explicit acknowledgment. FAIL is immutable; new project or approved script version required for a corrected candidate.

```cmd
.venv\Scripts\python.exe -m podcast_gpt project-mix-review-template --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-mix-review-record --project-id PROJECT_ID --acknowledgment I_LISTENED_TO_THE_ENTIRE_CURRENT_MIX
.venv\Scripts\python.exe -m podcast_gpt project-mix-review-status --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-mixed-video-compose --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-mixed-video-audit --project-id PROJECT_ID
```

Requires original structurally audited neural candidate, reviewed pilot, and the current mix listening PASS. The optional intro/outro scenes are simple local static title cards in the selected aspect ratio. The existing speech video is reencoded, its audio discarded, and the verified mix is the only muxed audio. Cumulative 25 fps frame rounding may move a scene boundary by up to one frame; subtitle offsets are based on exact intro samples, not rounded video frames. No studio animation, burned-in subtitles or simultaneous three-format export.

New private mixed-export/episode-mixed.mp4, episode-mixed.srt and receipt.json bind base export, mix, listening review, frame plan and hashes. Full decode and count check structure, not perceptual quality. Production CLI rejects synthetic fixture exports. Separate full video review is mandatory for a human-approved mixed candidate:

```cmd
.venv\Scripts\python.exe -m podcast_gpt project-mixed-review-template --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-mixed-review-record --project-id PROJECT_ID --acknowledgment I_WATCHED_THE_ENTIRE_CURRENT_MIXED_EPISODE
.venv\Scripts\python.exe -m podcast_gpt project-mixed-review-status --project-id PROJECT_ID
```

Review every turn and global criteria; prior approvals do not transfer. No automatic publication or real device acceptance claim. Incomplete mixed-export without receipt can be archived using project-incomplete-status/archive --kind mixed-export under the existing stopped-process rules. No completed artifact replacement.

Corrective CI 45479131328 passed all six jobs (synthetic media, not real model acceptance).
