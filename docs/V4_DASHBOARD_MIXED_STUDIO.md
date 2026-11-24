# V4 local project creation, bounded dashboard controls and mixed neural studio

The localhost dashboard now creates a private project request using topic, language, 1–60 minutes, 1–10 comma-separated distinct presenters, format, workflow, input and research mode. The existing request validator is authoritative. No automatic source capture, AI call, key storage or model download. Explicit local production controls allow one eligible non-inference runner step, offline script/audio/pilot/final review form creation, static preview/studio rendering and neural/mixed studio composition from existing audited clips. Select the action and tick consent each time. Source imports, provider/model inference and review receipt recording remain CLI-only. No arbitrary commands or paths accepted. Existing project locks, local task mutex, loopback host and CSRF checks apply. Browser action creates files locally; use reported paths. Closing the application can interrupt a task; inspect recovery before retry. Actual browser interaction still requires device testing.

## Mixed neural studio

Configure and compose the neural studio, create the optional post-audio mix, and record its own listening PASS. Then:

```cmd
.venv\Scripts\python.exe -m podcast_gpt project-mixed-studio-compose --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-mixed-studio-audit --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-mixed-studio-review-template --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-mixed-studio-review-record --project-id PROJECT_ID --acknowledgment I_WATCHED_THE_ENTIRE_CURRENT_MIXED_NEURAL_STUDIO
.venv\Scripts\python.exe -m podcast_gpt project-mixed-studio-review-status --project-id PROJECT_ID
```

The separate mixed-neural-studio directory contains episode-mixed.mp4, episode-mixed.srt and immutable receipt. Reuses audited neural studio body, static intro/outro cards, normalized/mixed audio and exact intro sample subtitle offsets. Original speech-only and mixed single-speaker exports remain separate and unchanged. The distinct review receipt requires every turn and global observation; no approval transfers, no publication. Production rejects fixture-only source clips. The new media kind is available in the dashboard hash-checked local player. Incomplete mixed-neural-studio without receipt is eligible for the existing explicit stopped-process archive; dependencies protect original studio and mix. This is not continuous camera motion, animated listeners or realistic model acceptance. CI exercises synthetic media, request validation and action gates, not browser end-to-end interaction or actual inference.
