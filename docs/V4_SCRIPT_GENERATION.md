# V4 resumable script drafting

Create a V4 project, import required reference source if applicable, and save its validated outline first. Script drafting divides the outline into deterministic one-minute planning units (1–60 units), independent of section length. Each unit is generated separately; only validated JSON is saved. Every unit requires 2–20 turns with recognized speaker names and estimated seconds totaling 60, bounded nonempty text, and no exact normalized repeated dialogue anywhere in the script. The first minute of each section covers every speaker specified in that section. This is a design choice for coverage, not a guarantee of natural conversation. Language is a requested prompt label, not independently classified.

```cmd
.venv\Scripts\python.exe -m podcast_gpt project-script-status --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-script-generate --project-id PROJECT_ID --offline-only --max-new 1
.venv\Scripts\python.exe -m podcast_gpt project-script-generate --project-id PROJECT_ID --allow-cloud-text --confirm-gemini-free-project --max-new 5
.venv\Scripts\python.exe -m podcast_gpt project-script-finalize --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-script-show --project-id PROJECT_ID
```

Cloud flags are optional and explicit per invocation. Only confirm Gemini after ensuring billing is disabled. Cloud prompts include project data, imported source text if present, and the previous two turns for continuity. No automatic research or paid fallback. Default local model context and multilingual output may be insufficient for long reference text; do not claim guaranteed generation. Select a smaller excerpt or use a permitted cloud provider when appropriate. One to five units per invocation; each uses the existing bounded provider fallback. Failure leaves a validated prefix and stops; rerun to resume. There is no hidden retry loop.

Each private script-parts/NNN.json binds request, source evidence and outline hashes, unit metadata, validated dialogue and provider. The project lock serializes writes. A changed receipt, unexpected file, gap or stale binding blocks work. Successful finalization writes script.json with stable turn IDs, part hashes and complete dialogue. Finalization and status are read-only with respect to existing verified files. To revise a script, create a new project rather than overwrite verified evidence. Inspect interrupted locks or scratch files manually; no automated deletion.

The script is an unreviewed AI draft. Planned seconds are model estimates, not a measured timeline; actual voice durations, naturalness, pronunciation, factual accuracy and rights need separate validation. A custom script is currently reference material for adaptation, not a verbatim timed import. V3 fixed 45-turn rendering is intentionally not fed V4 drafts. Multi-source research, citations, manual editing/revision, generalized voice/media and actual user-device tests are still pending.

Web research mode now accepts a validated 2–4 source research pack and requires exact excerpt citations in each generated unit. See V4_RESEARCH.md. Citation correctness is structural only; fact checking remains human work.

Manual revision and human review of a finalized draft are now available without overwriting generated parts. See V4_SCRIPT_REVIEW.md. The old script-show command still returns the original draft; project-script-current returns the latest revision.
