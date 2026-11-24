# V4 measured target gain, per-turn diagnostics and selected episode continuity

## Target gain for a new mix
```cmd
.venv\Scripts\python.exe -m podcast_gpt project-mix-compose --project-id PROJECT_ID --target-lufs -16 --acknowledgment I_HAVE_RIGHTS_TO_ALL_ADDED_AUDIO_AND_AUTHORIZE_LOCAL_MIX
```

Optional integer target -24 to -14 LUFS. Existing peak mix and optional ducking are performed first into private scratch. FFmpeg loudnorm analysis measures baseline integrated loudness and true peak; static gain is bounded by target, -1.5 dBTP ceiling with 0.25 dB analysis margin, +12 dB amplification and PCM peak 30000. Candidate is remeasured before final files are created; true peak over ceiling or nonfinite measurements block saving. Receipt stores baseline PCM hash/peak, measurements, gain and whether measured target is within 0.5 LU. Exact sample count and deterministic integer PCM audit remain authoritative; stored FFmpeg measurements are creation-time observations, not rerun during every audit. Use diagnostics for current measurements. Static gain may not reach target, particularly with high crest factor or gated quiet material. No dynamic limiter, compression, denoising or broadcast certification. Existing mixes keep original recipes and approvals; no overwrite. New mixed video uses unchanged sample timing and requires fresh listening approval. Interrupted scratch may require manual inspection.

## Per-turn objective diagnostics
```cmd
.venv\Scripts\python.exe -m podcast_gpt project-audio-diagnostics --project-id PROJECT_ID --kind master --per-turn
```
Master audit and report include per-turn PCM peak, RMS, full-scale samples, zero fraction and mean DC offset. Flags for low RMS, DC offset and full-scale samples are simple heuristics, not pronunciation, noise or clipping certification. No audio modification.

## Selected prior-episode continuity
Assign current and prior project casts. Before generating any script units, select 1–8 turn IDs from the prior project's current human-PASS script. Every selected speaker must match the exact immutable character ID and record hash in the current cast. New speaker labels may differ. Explicitly authorize a frozen snapshot:
```cmd
.venv\Scripts\python.exe -m podcast_gpt project-continuity-enable --project-id NEW_ID --prior-project-id OLD_ID --turn-id 0001 --turn-id 0003 --acknowledgment I_AUTHORIZE_SELECTED_REVIEWED_DIALOGUE_FOR_LOCAL_DRAFTING
.venv\Scripts\python.exe -m podcast_gpt project-continuity-status --project-id NEW_ID
```
Selected excerpts are private, immutable, bound to both reviewed version and current request/cast. The snapshot does not follow later prior-script revisions. Only matching speaker text is sent to local Ollama during AI script generation; continuity-enabled drafts require explicit offline-only mode (dashboard local Ollama also works). No provider cloud sharing, automatic memory mining, automatic episode summary, personal facts, or fact verification. Prior dialogue is untrusted style/continuity context, not evidence. Existing script review and media approval gates remain mandatory. Verbatim custom-script projects are excluded. CLI selection only; no browser continuity authoring yet. Real model continuity quality and Windows/device acceptance pending.

CI 45492395979 passed 6/6. Browser continuity selection now available (V4_BATCH29.md).
