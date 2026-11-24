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
