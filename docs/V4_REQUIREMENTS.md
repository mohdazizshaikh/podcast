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

## Increment 3 — bounded source ingestion
Implemented one immutable source attachment per V4 project, PDF text (optional parser), DOCX/TXT/Markdown, custom script reference text and explicit public HTTPS page retrieval. Source hashes bind the outline. Live research, large/multiple sources, OCR and timed script import remain pending. See V4_INGESTION.md and V4_TRACKER.md.

## Increment 4 — resumable AI dialogue drafting
Implemented 1–60 one-minute planning units from a verified outline, strict speaker and text validation, bounded 1–5 unit invocations, immutable source-bound checkpoints, resume and final script assembly. Planned seconds are not actual measured voice timing. Human approval, manual revisions, exact custom-script import and generalized media remain pending. See V4_SCRIPT_GENERATION.md and V4_TRACKER.md.

## Increment 5 — bounded research evidence and citations
Implemented explicit 2–4 public HTTPS source snapshots, immutable research pack, source-bound outline and script, and exact excerpt/source-ID validation. Automatic search discovery, semantic truth checking and independent human review remain pending. See V4_RESEARCH.md.

## Increment 6 — versioned manual script editing and human approval
Implemented editable JSON templates, immutable revision chain, current-version inspection, per-turn PASS/FAIL and global script review criteria, self-attestation receipt, stale approval invalidation and reusable PASS gate. Browser editing, arbitrary restructuring, actual duration and media integration remain pending. See V4_SCRIPT_REVIEW.md.

## Increment 7 — reusable character library and voice identity preferences
Implemented immutable reusable profile versions, explicit authorized PNG import, hash verification, 1–10 presenter cast binding, private profile inspection, and read-only current-approved-script/portrait handoff. Actual image generation, persistent conversational memory, personality-aware script prompting and real multilingual voice compatibility remain pending. See V4_CHARACTERS.md.

## Increment 8 — authorized audio import and measured timeline
Implemented current approved script/cast-bound PCM WAV import, immutable per-turn receipts, version isolation, missing-turn progress and exact integer sample timeline with fixed gaps and duration tolerance indicator. Voice inventory is metadata only; actual generalized TTS, audio composition, quality review and video rendering remain pending. See V4_AUDIO.md.

## Increment 9 — local Hindi TTS and master audio
Implemented explicit local Kokoro Hindi adapter, up to four distinct supported Hindi presets with mixed authorized WAV imports, resumable generated receipts and exact PCM master composition/audit. Other languages, Edge, real voice acceptance, audio QA/mixing and video remain pending. See V4_TTS_MASTER.md.

## Increment 10 — listening review and static video preview
Implemented immutable master-specific per-turn and global listening self-attestation, explicit PASS gate, selected 16:9/9:16/1:1 static portrait preview and measured UTF-8 SRT sidecar, structural video audit. Not neural lip-sync, full video acceptance, or independent human quality verification. See V4_PREVIEW.md.
