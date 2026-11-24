# V4 configured media runner, timing history and graphical QA

The bounded foreground runner now supports one eligible Kokoro/eSpeak turn or SadTalker clip per action, only with the respective acknowledgment and saved model paths. It still stops at missing inputs and human review gates. If both TTS engines are eligible and authorized, Kokoro is selected first. No automatic engine substitution, cloud calls, weights downloads or automatic approval. External executables are not sandboxed.

```cmd
.venv\Scripts\python.exe -m podcast_gpt project-auto-step --project-id PROJECT_ID --execute --acknowledgment I_AUTHORIZE_BOUNDED_LOCAL_PRODUCTION_STEPS --kokoro-ack I_HAVE_RIGHTS_TO_USE_LOCAL_MODEL_AND_VOICES --max-steps 3
.venv\Scripts\python.exe -m podcast_gpt project-auto-step --project-id PROJECT_ID --execute --acknowledgment I_AUTHORIZE_BOUNDED_LOCAL_PRODUCTION_STEPS --espeak-ack I_TRUST_THIS_LOCAL_ESPEAK_EXECUTABLE_AND_HAVE_USAGE_RIGHTS --max-steps 3
.venv\Scripts\python.exe -m podcast_gpt project-auto-step --project-id PROJECT_ID --execute --acknowledgment I_AUTHORIZE_BOUNDED_LOCAL_PRODUCTION_STEPS --neural-ack I_HAVE_RIGHTS_AND_TRUST_THIS_LOCAL_SADTALKER_INSTALLATION --max-steps 1
.venv\Scripts\python.exe -m podcast_gpt project-production-progress --project-id PROJECT_ID
```

Successful orchestrated media actions record wall-clock elapsed seconds, unit ID and source/config-path scope hash, with historical count/min/max/mean. A project lock is not proof of a running process. No live subprocess percentage or ETA, no hardware/model comparability guarantee. Direct CLI inference isn't timed by this feature. If timing record fails, existing media checkpoints are retained.

```cmd
.venv\Scripts\python.exe -m podcast_gpt project-media-review-visual --project-id PROJECT_ID --kind audio
.venv\Scripts\python.exe -m podcast_gpt project-audio-review-record --project-id PROJECT_ID --file "D:\Private\review.json" --acknowledgment I_LISTENED_TO_THIS_ENTIRE_MASTER_AND_ALL_TURNS
.venv\Scripts\python.exe -m podcast_gpt project-media-review-visual --project-id PROJECT_ID --kind pilot
.venv\Scripts\python.exe -m podcast_gpt project-neural-pilot-record --project-id PROJECT_ID --file "D:\Private\pilot.json" --acknowledgment I_WATCHED_EVERY_CURRENT_PILOT_CLIP
.venv\Scripts\python.exe -m podcast_gpt project-media-review-visual --project-id PROJECT_ID --kind final
.venv\Scripts\python.exe -m podcast_gpt project-final-review-record --project-id PROJECT_ID --file "D:\Private\final.json" --acknowledgment I_WATCHED_AND_REVIEWED_THE_ENTIRE_CURRENT_EPISODE
```

Open private HTML locally and listed files in a separate local media player. Complete observations and export JSON, then use actual downloaded path. No remote resources or default PASS, and existing source-bound review validators remain mandatory. Pilot and final production forms reject synthetic clips. Real browser interaction, integrated playback, genuine model inference and actual Windows acceptance remain pending.

A read-only dashboard overview and historical neural-stage extrapolation are now available (V4_PRODUCTION_OVERVIEW.md). No live ETA or automatic approval.
