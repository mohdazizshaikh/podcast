# V4 optional dependencies, visual script editing and bounded production steps

## Optional application dependencies

Use the existing app virtual environment. Inspect the allowlisted package groups (documents or kokoro), then separately authorize installation. No arbitrary package names, global installs, automatic weight downloads or automatic installation on app launch. Python packages and their dependencies are third-party software; review their licenses and trust before installing. This invokes pip against PyPI, may install or change dependencies, and can fail or leave a partially changed environment. It does not prove model loading or actual compatibility. Use the existing Windows setup guide for FFmpeg, eSpeak, SadTalker and model assets.

```cmd
.venv\Scripts\python.exe -m podcast_gpt dependency-plan --group documents
.venv\Scripts\python.exe -m podcast_gpt dependency-install --group documents --acknowledgment I_AUTHORIZE_INSTALLING_FREE_OPTIONAL_PYTHON_PACKAGES
```

## Visual script editor

After finalizing a draft, create an offline HTML editor or review page in the private workspace. Open the returned HTML path in your local browser. Edit dialogue, speaker and estimated seconds (original turn IDs and unit boundaries remain fixed); research quotations are displayed but not edited by this interface. Export JSON using the page button, then import the actual downloaded file path with the existing version-bound validator. No HTTP upload or remote resources. Keep these files private; browser downloads may be stored outside the workspace.

```cmd
.venv\Scripts\python.exe -m podcast_gpt project-script-visual --project-id PROJECT_ID --mode edit
.venv\Scripts\python.exe -m podcast_gpt project-script-revise --project-id PROJECT_ID --file "D:\Private\edit-r000.json"
.venv\Scripts\python.exe -m podcast_gpt project-script-visual --project-id PROJECT_ID --mode review
.venv\Scripts\python.exe -m podcast_gpt project-script-review-record --project-id PROJECT_ID --file "D:\Private\review-r001.json" --acknowledgment I_REVIEWED_THIS_ENTIRE_SCRIPT_VERSION
```

Review page requires individual PASS/FAIL and all global criteria; export is not approval. No old version may be applied to a new version. The HTML files cannot be overwritten; reopen existing file for the same version. Existing JSON template workflow still works.

## Bounded foreground orchestration

```cmd
.venv\Scripts\python.exe -m podcast_gpt project-auto-step --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-auto-step --project-id PROJECT_ID --execute --acknowledgment I_AUTHORIZE_BOUNDED_LOCAL_PRODUCTION_STEPS --max-steps 3
```

Default is plan-only. Explicit execution runs at most 1–5 eligible steps in the foreground, each using existing validations/locks: script finalization, audio timeline, master composition, neural export. Add --allow-local-ai to permit offline-only outline and one-minute dialogue generation; no cloud calls or automatic pulls. Human review, missing input/cast/audio, neural pilot/batch and recovery gates stop the runner. No automatic approvals, imports, TTS, neural inference, publishing or background jobs. Existing completed artifacts remain immutable. Each successful action is timed using monotonic time; no estimated remaining time is claimed. Failed operations stop with their existing error, verified checkpoints remain available for rerun. The next CLI status is authoritative; no persistent timing history or live progress streaming yet. Full one-click production and genuine Windows acceptance remain pending.
