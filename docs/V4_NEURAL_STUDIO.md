# V4 independent neural studio and portrait attachment

Configure the existing immutable studio settings (focus or grid, optional authorized PNG background). With the current approved script/cast/master/listening review, complete neural clips and per-presenter pilot PASS, compose a separate neural studio candidate. It does not require the separate speech-only neural export to exist and does not overwrite it.

```cmd
.venv\Scripts\python.exe -m podcast_gpt project-neural-studio-compose --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-neural-studio-audit --project-id PROJECT_ID
```

The active presenter clip is fitted into an even-pixel rectangular card, retaining face aspect ratio. Grid displays static portraits for other speakers; focus shows only the current speaker. Silence shows a static portrait. This is turn-driven hard-cut switching, not continuous camera motion, face segmentation or realistic reaction animation. The background sits behind the cards, not behind a cut-out person. Uses exact cumulative frame plan, original audited master (model audio discarded), selected aspect ratio and measured SRT sidecar. Studio settings, clip receipts and original inputs bind output hashes. Full decode and actual frame count are structural checks, not proof of facial quality. Fixture-only media is rejected by production CLI. Mixed music/intro/outro studio export and advanced camera transitions remain pending.

Output is private neural-studio/studio-neural.mp4, studio-neural.srt and receipt.json. Review every turn and global criteria; prior export approvals do not transfer.

```cmd
.venv\Scripts\python.exe -m podcast_gpt project-neural-studio-review-template --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-neural-studio-review-record --project-id PROJECT_ID --acknowledgment I_WATCHED_AND_REVIEWED_THE_ENTIRE_CURRENT_NEURAL_STUDIO
.venv\Scripts\python.exe -m podcast_gpt project-neural-studio-review-status --project-id PROJECT_ID
```

No automatic PASS or publication. Failed review remains immutable. Incomplete studio-preview and neural-studio directories without completion receipts are eligible for stopped-process archive using project-incomplete-status/archive --kind studio-preview or neural-studio, with existing acknowledgment. Settings recovery still manual; dependent artifacts block unsafe archives.

## Attach generated or obtained portraits

```cmd
.venv\Scripts\python.exe -m podcast_gpt character-portrait-attach --character-id CHARACTER_ID --portrait "D:\Private\portrait.png" --acknowledgment I_HAVE_RIGHTS_TO_USE_THIS_PORTRAIT
```

Creates a new immutable character version using the original profile and authorized new PNG, preserving old records and casts. Select the new ID when assigning a new project's cast. Does not generate images or automatically reassign existing projects. Actual local image inference, genuine model rendering and Windows acceptance remain pending. Tests exercise synthetic media, geometry, archive and review behavior.

Verified neural studio candidate playback manifest is available through V4_PRODUCTION_OVERVIEW.md. Browser interaction and genuine model acceptance remain pending.

Independent mixed neural studio candidate, separate QA and recovery now available (V4_DASHBOARD_MIXED_STUDIO.md).

Batch 39 adds a spotlight studio layout for 1–10 presenters in landscape, vertical and square, plus four opt-in active-speaker camera modes (pull-out, smooth push-in, pan left/right) alongside existing fixed and push-in. Settings, CLI and dashboard support; static preview uses layout only, neural composition inherits bounded camera filters. 71 authored tests, 65 isolated local tests passed including six real FFmpeg filter/frame-count renders; six full-project integration tests and repository CI pending. Listeners remain static, camera resets at clip boundaries, and real browser/model/Windows acceptance remains open. See V4_BATCH39.md.
