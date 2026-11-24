# V4 full video review, recovery and readiness

The final review requires a structurally audited current non-fixture neural candidate. Watch the complete MP4 with its SRT and review every turn for lip sync, identity, speech/audio, subtitles and transitions, plus global complete viewing, rights and overall quality. Edit the returned private UTF-8 JSON template. No default PASS. The saved observation receipt binds the exact export hash and cannot be overwritten.

```cmd
.venv\Scripts\python.exe -m podcast_gpt project-final-review-template --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-final-review-record --project-id PROJECT_ID --acknowledgment I_WATCHED_AND_REVIEWED_THE_ENTIRE_CURRENT_EPISODE
.venv\Scripts\python.exe -m podcast_gpt project-final-review-status --project-id PROJECT_ID
```

All PASS is only human self-attestation for this candidate. It does not independently certify real model performance, rights or publication. A failed review is immutable; new approved revision/project and new media are required for a corrected candidate.

For an interrupted neural attempt, first stop all external model processes and verify no active project lock. The tool cannot detect every orphan process. Never remove a lock automatically. Only current-binding scratch for a missing chunk is eligible; completed clips, stale versions, partial committed clip directories, TTS/master/export failures and orphan locks are not archived by this increment.

```cmd
.venv\Scripts\python.exe -m podcast_gpt project-neural-recovery-status --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-neural-archive --project-id PROJECT_ID --chunk-id 0001-01 --acknowledgment I_STOPPED_ALL_MODEL_PROCESSES_AND_WANT_TO_ARCHIVE_THIS_ATTEMPT
```

Archive uses an exclusive project lock, rejects links/reparse points and moves the stopped attempt intact to a unique private directory. No deletion; retry is a separate explicit neural run. If archive metadata writing fails after rename, the attempt is still preserved in the archive folder; inspect manually.

```cmd
.venv\Scripts\python.exe -m podcast_gpt project-readiness --project-id PROJECT_ID
```

The read-only readiness checker walks existing validated state, shows script/audio/chunk counts and the next recommended command. Missing prerequisites return a stage; invalid or tampered evidence blocks with an error. It performs no model calls, edits, publication or automatic repair. In the existing local dashboard, list V4 projects, enter one project ID, then use the new readiness button. The loopback/CSRF guard remains; no new executable path or credential inputs over HTTP. Full visual editing, orchestration, live inference ETA, broader multilingual TTS, automated portraits/research and genuine Windows acceptance are still pending. Auditing large episodes can be slow.

Bounded foreground production orchestration is now available through V4_WORKFLOW.md. It stops at every human approval and missing media gate; no automatic publication.
