# V4 saved model paths, offline language fallback and character-aware dialogue

These three optional features are separate from actual model acceptance. Save existing trusted paths in the private workspace, not Git. Saving checks path types and basic structure, never installs packages, downloads weights or launches the selected interpreter. For existing selections use explicit --replace. Hashes protect configuration consistency, not third-party code authenticity.

```cmd
.venv\Scripts\python.exe -m podcast_gpt model-configure --engine kokoro --model "D:\Models\kokoro.onnx" --voices "D:\Models\voices.bin"
.venv\Scripts\python.exe -m podcast_gpt model-configure --engine sadtalker --model "D:\Models\SadTalker" --python "D:\Models\SadTalker\.venv38\Scripts\python.exe"
.venv\Scripts\python.exe -m podcast_gpt model-configure --engine espeak --executable "C:\Program Files\eSpeak NG\espeak-ng.exe"
.venv\Scripts\python.exe -m podcast_gpt model-config-status
```

Use --use-config instead of explicit paths on project-tts-kokoro, project-neural-run, espeak-inventory and project-tts-espeak. All existing inference consent, preflight, source binding and model/voice rights requirements still apply. No silent automatic model choice. Install trusted software manually using the existing setup guides; one-click third-party dependency installation remains pending.

## Lightweight multilingual fallback

Install a trusted local eSpeak NG executable and voice data yourself. eSpeak is non-neural and typically robotic; not a replacement for realistic voices. Inventory explicitly invokes the selected executable to enumerate installed language codes. No paid service or model downloads by the app; external executable is not sandboxed.

```cmd
.venv\Scripts\python.exe -m podcast_gpt espeak-inventory --use-config --acknowledgment I_TRUST_THIS_LOCAL_ESPEAK_EXECUTABLE_AND_HAVE_USAGE_RIGHTS
.venv\Scripts\python.exe -m podcast_gpt project-tts-espeak --project-id PROJECT_ID --use-config --run-local --acknowledgment I_TRUST_THIS_LOCAL_ESPEAK_EXECUTABLE_AND_HAVE_USAGE_RIGHTS --max-new 1
```

Use engine espeak in a character profile, a matching language name/code, and an exact installed language code as preset (optionally +m1 through +m7 or +f1 through +f5). For example hi+m1 and hi+f1, if hi is installed. Distinct preset labels are required for participating characters, not proof of distinct voice identity. Named language aliases cover common languages, other installed codes can be selected directly. Actual installed variant support, pronunciation and voice quality still need listening tests. Generate 1–5 missing eligible turns, mixed with imports and Kokoro where appropriate; exact PCM and executable/language inventory hashes are saved. The inventory hash does not authenticate all external voice data. No Edge adapter or wider neural voice engine in this increment.

## Character-aware script drafting

Create and assign the cast before generating any script units, then opt in:

```cmd
.venv\Scripts\python.exe -m podcast_gpt project-persona-enable --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-script-generate --project-id PROJECT_ID --offline-only --max-new 1
```

Only personality and speaking style for the current section speakers are added as untrusted prompt data. Snapshot and cast hashes bind checkpoints and final scripts. Portraits, appearance and voice preferences are excluded from this prompt. Explicit cloud text consent applies to these descriptors too. Existing scripts remain unchanged; opt in before any script parts directory exists. Character style is not independently validated, and long-term cross-episode conversational memory remains pending.

Optional app-venv dependency installation for documents/Kokoro is available with explicit consent; see V4_WORKFLOW.md. Model asset and external tool setup is still manual.

Local model path configuration can also be saved through the dashboard (V4_DASHBOARD_AUTHORING.md); inference remains separately consented CLI-only.

Optional prior-episode continuity snapshot is separate from persona context and bound to current script units (V4_NORMALIZATION_CONTINUITY.md); offline-only drafting.

Batch 37 implements explicit online Edge V4 speech adapter with static locale/preset validation, 1–5 bounded approved turns, private temporary MP3/PCM conversion, immutable source-bound receipts, resume, duplicate rejection and CLI/readiness/preflight integration. 81 new regression cases authored (71 pure locale/receipt cases and 10 adapter/CLI cases); tests not yet independently run. No automatic network fallback, service/voice inventory guarantee, browser Edge action or real voice/device acceptance. See V4_BATCH37.md.

Batch 38 adds read-only Edge pending-turn planning, separate bounded consented online voice inventory with filtering and deduplication, optional dependency setup, browser generation/inventory/preview, turn-bound progress and cooperative stop, and local-only continuity protection. 63 new test cases authored; full repository CI and real browser/service/device acceptance unverified. See V4_BATCH38.md.
