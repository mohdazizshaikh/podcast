# Batch 37 — explicit online Edge speech adapter

Edge is optional, online and never an automatic fallback. Install the already declared optional package in the app virtual environment with `python -m pip install -e ".[tts]"`. Select engine `edge`, a language name or tag and a provider neural voice short name in each character profile, e.g. `hi-IN-MadhurNeural`. Distinct preset IDs are required, not proof of distinct or natural voice quality.

```cmd
.venv\Scripts\python.exe -m podcast_gpt project-tts-edge --project-id ID --allow-network-tts --acknowledgment I_AUTHORIZE_SENDING_APPROVED_DIALOGUE_TO_EDGE_AND_HAVE_USAGE_RIGHTS --max-new 1
```

Each explicitly authorized invocation sends only selected current approved dialogue turns and their voice preset to the external service (1–5 new turns). Consent is per invocation, not saved as permission for future requests. The receipt records past consent, locale/preset and provider, not proof of speaker identity or service terms. The optional package/provider may fail or change; no paid fallback or guaranteed free availability. Static preflight checks syntax/locale only and reports that separate online consent and availability are required. The local-only browser/orchestrator engine list remains unchanged.

Bounded 120-second async stream, 8 MB MP3 limit, private temporary workspace, bounded FFmpeg PCM conversion (16 kHz mono PCM16), existing 0.25–120 second turn and total-duration limits, no overwrite, exact source binding and duplicate rejection. Existing speech remains intact after a failure. Completed turns resume on next explicit invocation. No automatic network voice inventory or publication.

81 authored test cases: 54 locale matrix, 10 malformed presets, 7 receipt validation, 4 consent, 4 count, 1 fake-provider FFmpeg resume and 1 CLI default. Actual tests and CI not independently confirmed yet. Real service, model/browser/device acceptance and full episode remain pending.

Batch 38 adds read-only Edge pending-turn planning, separate bounded consented online voice inventory with filtering and deduplication, optional dependency setup, browser generation/inventory/preview, turn-bound progress and cooperative stop, and local-only continuity protection. 63 new test cases authored; full repository CI and real browser/service/device acceptance unverified. See V4_BATCH38.md.
