# Confirmed V4 personal-use specification

User-approved scope: personal only; all engine-supported languages; 1–10 characters; AI-generated or uploaded authorized portraits; topic/URL/PDF/documents/custom script; 1–60 minutes; automatic and advanced manual; landscape/vertical/square; knowledge and verified web research; personal default and per-project keys; hardware RAM unknown; strictly free, no paid fallback.

## Increment 1 — free text AI and outline planner
- OpenRouter `openrouter/free` primary, Gemini `gemini-3.5-flash-lite` backup, Ollama loopback local models strictly under 3 billion parameters.
- Cloud text is opt-in per run. Gemini requires an explicit confirmation of a genuinely unbilled Free Tier project. The API key alone cannot establish billing status; do not enable billing. No search grounding, paid tools, paid model routing or automatic model downloads.
- Default keys come from the current process environment. Optional session-only hidden prompts override them for a selected project invocation. Persistent encrypted per-project credentials are not implemented yet. Never commit or log API keys.
- Local model selection permits explicit known tags only, verifies installed model metadata parameter count, rejects reported remote models, uses CPU and bounded context/output. No promise of quality or throughput.
- Episode outline supports topic-only knowledge mode, all requested languages as text labels, 1–10 presenters, whole-minute target 1–60, all three format selections and both workflow selections as planning metadata. Strict JSON validation rejects incomplete timing or missing presenter coverage. No live research or full script/media generation in this increment.

## Subsequent milestones (not implemented by this increment)
1. Full project manager and persistent private configuration; generalize signed source schema beyond V3 fixed Hindi 45 turns/3 speakers.
2. Input importers for URL/PDF/documents/custom script, explicit network/data disclosure, source attribution and safe parsing.
3. Live research through separately verified free sources, no paid grounding.
4. Chunked script generation, validation/repair/checkpoints, language-specific voice capability matrix.
5. Authorized portrait upload and separately evaluated free/local image generation.
6. Generalized multilingual TTS, active-speaker rendering, layout presets, 1–60 minute timeline and manual/automatic workflow.
7. Actual Windows pilot, then longer real episodes and final QA. No V4 production claim before acceptance.

The fixed V3 pipeline and stable-v3.7 branch remain supported. AI text engines are not themselves proof of image, voice or lip-sync availability in every language.

## Increment 2 — private projects and keys
Implemented isolated immutable topic request/outline storage, project inventory, CLI planning, dashboard listing, Windows current-user DPAPI default and per-project encrypted keys, with environment fallback. Persistent cloud consent is forbidden. Generalized script/media and non-topic input ingestion are still pending. See V4_PROJECTS.md.
