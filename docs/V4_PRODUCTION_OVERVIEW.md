# V4 production overview, local playback and historical ETA

In the private localhost dashboard, enter a project ID and select Production overview / historical estimate. This read-only action shows validated current readiness, next command, timing history, saved model configuration and an approximate neural-stage estimate when enough evidence exists. It does not run models or automatically approve artifacts.

```cmd
.venv\Scripts\python.exe -m podcast_gpt project-production-overview --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-media-check --project-id PROJECT_ID --kind master
```

Estimate applies only to the eligible current neural pilot or batch stage, with at least three distinct matching completed chunks from the same source and saved-path scope, excluding synthetic media. It extrapolates median wall-clock seconds per source second to remaining source seconds; observed min/max rates form a rough range, not a confidence interval. Different clip lengths, initialization overhead, changed model files or hardware, other workloads and interrupted processes can invalidate it. This is not live progress, a countdown, or a whole-project ETA; human review and other stages are not included. No estimate while the project lock is present. Timings are only collected from orchestrated media runs.

## Verified local playback

Choose master, preview, neural, mix, mixed, studio-preview or neural-studio. Audit selected media uses the current existing structural audit and returns the exact local path, SHA-256 and size; no arbitrary filesystem paths are accepted from the browser. Select the displayed local file in the browser picker. The browser hashes it locally and plays a matching file via a blob URL with native media controls. No media bytes are uploaded and no HTTP media routes are added. Browser SHA-256 requires a supported secure localhost context; file selection and playback are capped at 128 MiB to limit memory. Larger files must be opened in a separate local player using the displayed path. Browser codec support and actual UI interaction are not yet independently tested. A hash match is not human review or publication approval. Existing CSRF/loopback restrictions and source-bound approval gates remain unchanged.

Full dashboard authoring/inference controls, live subprocess percentage, embedded subtitles, mixed neural studio and physical Windows model acceptance remain pending. Tests exercise local manifest validation, lock protection, estimate scope and dashboard markup, not actual browser playback.

Dashboard now also permits validated private project creation and explicit local non-inference production actions. Mixed neural studio playback is available. See V4_DASHBOARD_MIXED_STUDIO.md; actual browser verification pending.
