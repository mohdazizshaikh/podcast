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

## Increment 11 — generalized CPU neural clips and pilot gate
Implemented exact sample chunk planning, explicit local SadTalker CPU invocation, clip receipts, resume, per-presenter pilot self-attestation and reviewed batch gate. No final neural episode composition or genuine model acceptance yet. See V4_NEURAL.md.

## Increment 12 — selected-format neural candidate export
Implemented cumulative PCM-derived 25 fps frame plan, normalized facial clip composition, static pause cards, master-only audio mux, measured UTF-8 SRT, full structural audit and fixture-only export rejection from production CLI. Full human video QA, actual Windows model acceptance, polished studio layouts and broader features remain pending. See V4_EXPORT.md.

## Increment 13 — combined acceptance, recovery and readiness
Implemented immutable full candidate per-turn/global human review, non-destructive stopped current neural scratch archive, and read-only staged project readiness with dashboard selection. No automatic publication, orphan-process detection, lock deletion, generalized failure recovery or measured ETA. See V4_ACCEPTANCE.md.

## Increment 14 — combined local configuration, language fallback and personality prompting
Implemented private saved Kokoro/SadTalker/eSpeak paths with explicit reuse/replacement, opt-in installed eSpeak language inventory and bounded local PCM synthesis, and immutable cast personality snapshots for new dialogue generation. Non-neural eSpeak is a fallback, not realistic multilingual speech. Actual installed model/voice tests, wider neural TTS, automated installations and longitudinal memory remain pending. See V4_MODEL_VOICES_PERSONA.md.

## Increment 15 — combined workflow controls
Implemented allowlisted optional app-venv dependency plan/install, private offline visual script editor and review JSON export/import, and explicitly bounded foreground orchestration with optional offline AI and measured action durations. Human gates remain mandatory. Third-party models, live ETA, media QA visual UI and real device acceptance remain pending. See V4_WORKFLOW.md.

## Increment 16 — configured media workflow and visual QA
Implemented explicit configured Kokoro/eSpeak/SadTalker bounded orchestration, private measured action history and offline audio/pilot/final QA forms with bound JSON import. No live ETA or embedded playback. See V4_MEDIA_WORKFLOW.md.

## Increment 17 — audio post-production and partial recovery
Implemented optional deterministic audio-only peak normalization, looping authorized bed and intro/outro WAV, exact sample audit and private archive of six incomplete-output types lacking receipts. Original master/approvals unchanged; mixed-video export and actual listening acceptance pending. See V4_POST_AUDIO_RECOVERY.md.

## Increment 18 — mixed video and fresh review gates
Fixed CLI parser shadowing regression (45478604299). Implemented separate mix listening review, selected-format mixed video with static intro/outro cards, exact shifted SRT and fresh complete mixed video QA, plus incomplete mixed export recovery. CI pending; actual acceptance unverified. See V4_MIXED_VIDEO.md.

## Increment 19 — combined voice and research expansion
Corrective CI 45479131328 passed 6/6. Implemented explicit local Kokoro Spanish/French/Italian/Brazilian Portuguese candidate presets, free opt-in Wikipedia discovery and current-script/research-bound human factual review. No automatic claim verification, broad search, mandatory new media gate, English/CJK neural frontend or real model acceptance. See V4_LANGUAGE_RESEARCH.md.

## Increment 20 — English frontend and static studio preparation
Implemented US/UK Kokoro non-transformer English phonemization and optional dependency group, local profile-derived portrait briefs, immutable authorized background and focus/grid static studio preview with measured subtitles and structural audit. No image generation or animated neural studio. CJK and physical model acceptance remain pending. See V4_STUDIO_ENGLISH.md.

## Increment 21 — neural studio, fresh review and portrait attachment
Implemented independent neural focus/grid candidate with active speaker motion and static listeners, exact frame plan/master/SRT, immutable full review, two new studio recovery types and authorized immutable portrait attachment. No genuine model acceptance, local portrait inference, mixed studio or continuous camera motion. See V4_NEURAL_STUDIO.md.

## Increment 22 — production overview, local playback and historical estimate
Implemented selected-project read-only dashboard overview, allowlisted structural media manifests, client-local hash-checked playback and same-scope neural stage timing extrapolation. No HTTP file serving, inference controls, live ETA or approval automation. See V4_PRODUCTION_OVERVIEW.md.

## Increment 23 — dashboard project creation and mixed studio
Implemented bounded JSON project creation, explicit non-inference dashboard actions, independent mixed neural studio export/QA, playback manifest and tenth incomplete-output archive type. Original candidates remain immutable; browser inference/approval, real model and full GUI acceptance pending. See V4_DASHBOARD_MIXED_STUDIO.md.

## Increment 24 — graphical local authoring
Implemented browser character profile/revision creation, authorized portrait attachment, immutable cast selection, bounded local source upload and explicit public URL capture, and local model path configuration. DOCX XML restricted to UTF-8. Browser inference, research pack capture and approval recording remain CLI-only. CI pending; see V4_DASHBOARD_AUTHORING.md.

## Increment 25 — graphical local inference, research and task status
Implemented explicitly consented selected-engine bounded local inference, research discovery/capture/status, offline cloud-key isolation and measured elapsed/checkpoint task reporting. No live internal model percentage, cloud AI, automatic downloads or approval recording. CI pending; see V4_DASHBOARD_INFERENCE.md.

## Increment 26 — review import, cooperative stop and structured custom script
Implemented ten-kind browser JSON review/revision import with exact declarations, task-ID scoped cooperative stop after current action, and structured verbatim knowledge-mode custom source import with manual provenance and existing timed-unit validation. CI pending; no automatic approval, force kill or unrestricted script input. See V4_REVIEW_STOP_MANUAL.md.

Corrective note: graphical authoring CI 45487275746 completed 6/6. Inference CI 45487824070 reported three failing tests in Ubuntu matrix: script progress variable shadowed callback, and offline credential isolation was applied to inventory rather than generate_json. Both code regressions corrected in subsequent commit; existing regression tests retained. Corrective CI pending. Actual model/browser acceptance remains unverified.

## Increment 27 — audio quality, provider reliability and setup plan
Corrective CI 45488657835 passed 6/6, superseding failed inference and initial review/stop/manual runs. Optional integer speech-driven music ducking, read-only LUFS/true-peak/PCM report, provider refusal stop and guided saved-model setup plan implemented. CI pending; no target loudness normalization, real model installation or physical acceptance. See V4_AUDIO_QUALITY_SETUP.md.

## Increment 28 — measured static gain and episode continuity
Implemented optional bounded loudness-target static gain with baseline and output measurement, exact sample audit and true-peak ceiling gate; per-turn PCM/DC diagnostics; explicit frozen reviewed prior dialogue with matching character versions for local-only drafting. CI pending; no dynamic limiter, automatic memory capture, actual model/device acceptance. See V4_NORMALIZATION_CONTINUITY.md.

## Increment 29 — expanded dashboard, Mandarin and validation matrix
Batch 27 and 28 CI each 6/6. Implemented Mandarin candidate presets and frontend, phoneme length rejection, secure session key input and optional Gemini credential isolation, explicit single-action cloud drafting, graphical authorized WAV/studio/continuity controls. 159 test cases authored, CI pending. See V4_BATCH29.md. No actual inference, billing or browser acceptance claim.

## Increment 30 — speech compression
Optional deterministic speech compressor integrated with exact mix audit, ducking and static target gain; 135 tests authored, CI pending. See V4_BATCH30.md. No dynamic true-peak limiting or denoising.

Batch 30 adds CLI/browser voice preflight and read-only device checklist, plus browser per-turn audio diagnostics. New CI pending. Real model inference, physical acceptance and browser interaction remain pending. See V4_BATCH30.md.

Batch 30 also implements graphical local mix composition with bounded WAV inputs, compression, ducking and optional static loudness target. Total 157 authored regression cases across the three commits; CI pending. Actual browser and Windows/model acceptance remain open. See V4_BATCH30.md.

Batch 29 and 30 CI completed successfully (45494573255, 45495891248 latest combined: 6/6 each). Batch 31 adds explicitly consented local CPU portrait candidate generation with safetensors inventory and immutable candidate receipt; new CI pending. Real model setup, physical acceptance and portrait quality remain unverified. See docs/V4_BATCH31.md (repository-relative).

Batch 31 adds 17 allowlisted Wikipedia discovery editions, exact citation coverage and browser portrait brief/coverage controls. New CI pending; broad web search, semantic verification and independent corroboration remain pending. See V4_BATCH31.md.

Batch 31 adds optional deterministic per-dialogue DC correction and low-level soft gate, CLI/browser settings and exact mix audit; new CI pending. AI/spectral denoising, dynamic true-peak limiting and real listening acceptance remain pending. See V4_BATCH31.md.

Batch 31 combined CI 45498392552 passed 6/6. Batch 32 adds guarded Japanese neural frontend/resource status, graphical isolated local portrait worker and candidate audit/attachment. Actual Japanese dictionary/model inference and real browser/device acceptance remain pending; new CI pending. See V4_BATCH32.md.

Batch 32 also adds bounded portrait attempt listing, candidate provenance validation and CLI candidate audit/attachment. 68 new regression cases authored across the two commits, not 68 independent features. New CI pending; real model and browser acceptance remain open. See V4_BATCH32.md.

Batch 32 combined CI 45500231172 passed 6/6. Batch 33 implements optional active-speaker digital push-in, local hash-verified portrait preview and stale asynchronous selection guards. 53 new regression cases authored, CI pending. Actual model/browser acceptance, advanced transitions and listener animation remain pending. See V4_BATCH33.md.

Batch 33 adds read-only decoded AAC/source audio comparison, timing and similarity diagnostics; CI pending. 63 new regression cases authored across two commits. Real browser/model acceptance and semantic audio review remain pending. See V4_BATCH33.md.

Batch 34 extends existing read-only research coverage with exact cross-source excerpt reuse, single-host turn and unused-source review signals; decoded AAC diagnostics now flag missing variable audio, DC offset changes and uncorrelatable mismatch, report unique flagged windows and uncompared frames. 68 new synthetic regression cases authored (not independent features). Batch 33 CI could not be confirmed through the available commit-status endpoints; Batch 34 CI pending. Actual model/browser/device acceptance and semantic corroboration remain open. See V4_BATCH34.md.

Batch 35 implements optional deterministic whole-mix dynamic sample-peak limiting, including intro/bed/outro, immutable exact PCM audit, CLI/browser setting and legacy defaults. 63 new regression cases authored; 58 standalone limiter cases passed in an isolated local Python harness, five repository integration cases and full CI unverified. Sample peaks are not intersample true peaks; dynamic true-peak limiting, combined LUFS normalization, real listening and physical Windows/model acceptance remain pending. See V4_BATCH35.md.

Batch 36 permits an optional dynamic sample limiter followed by bounded static loudness gain. The gain is capped by the selected sample ceiling, the candidate must pass the measured true-peak ceiling, and the immutable receipt binds the limiter and normalization settings. Legacy no-limiter receipts retain their format. 62 new unit regression cases authored, plus a revised project/dashboard integration case; full Python test execution and real device/listening acceptance remain unverified. This is not dynamic intersample true-peak limiting or guaranteed LUFS attainment. See V4_BATCH36.md.

Batch 37 implements explicit online Edge V4 speech adapter with static locale/preset validation, 1–5 bounded approved turns, private temporary MP3/PCM conversion, immutable source-bound receipts, resume, duplicate rejection and CLI/readiness/preflight integration. 81 new regression cases authored (71 pure locale/receipt cases and 10 adapter/CLI cases); tests not yet independently run. No automatic network fallback, service/voice inventory guarantee, browser Edge action or real voice/device acceptance. See V4_BATCH37.md.

Batch 38 adds read-only Edge pending-turn planning, separate bounded consented online voice inventory with filtering and deduplication, optional dependency setup, browser generation/inventory/preview, turn-bound progress and cooperative stop, and local-only continuity protection. 63 new test cases authored; full repository CI and real browser/service/device acceptance unverified. See V4_BATCH38.md.

Batch 39 adds a spotlight studio layout for 1–10 presenters in landscape, vertical and square, plus four opt-in active-speaker camera modes (pull-out, smooth push-in, pan left/right) alongside existing fixed and push-in. Settings, CLI and dashboard support; static preview uses layout only, neural composition inherits bounded camera filters. 71 authored tests, 65 isolated local tests passed including six real FFmpeg filter/frame-count renders; six full-project integration tests and repository CI pending. Listeners remain static, camera resets at clip boundaries, and real browser/model/Windows acceptance remains open. See V4_BATCH39.md.

Batch 40 adds optional deterministic dialogue-only fixed-point high-pass (60/80/100/120 Hz), narrow mains hum notch (50/60 Hz), and low-pass (4500/6000 Hz) filters before peak normalization; CLI/dashboard, exact recipe audit and disabled legacy defaults. 71 authored regression cases; 66 standalone cases passed locally (including synthetic frequency response); five integration cases and full repository CI unverified. These are targeted filters, not intelligent broadband denoising, and may affect voice tone. Human listening and physical model acceptance remain mandatory. See V4_BATCH40.md.

Batch 41 adds an optional conservative whole-mix dynamic PCM peak guard (three-sample lookahead/history, 22000 PCM cap, 50 ms release) with mandatory measured -1.5 dBTP check before committing and repeated check during audit. Supports sample limiter and bounded LUFS gain using the stricter sample ceiling; legacy defaults unchanged. 71 new tests authored, 64 standalone tests actually passed including six FFmpeg signal tests; initial three high-frequency cases exceeded ceiling, so explicit rejection is tested. Seven full-project cases and full CI unverified. This is not a standards-certified oversampled true-peak limiter, and may reject a candidate instead of automatically correcting it. See V4_BATCH41.md.

Batch 42 adds optional bounded measured static true-peak correction after the dynamic guard, up to three attenuation retries from the same PCM baseline, at most approximately 12 dB total attenuation, mandatory final measurement, exact PCM replay and baseline hash, and precommit frame/hash checks. CLI/dashboard, legacy defaults unchanged. Requires guard and no LUFS target (separate modes). 84 tests authored; 79 standalone tests executed successfully, including four actual FFmpeg tones. Five project integration cases and full CI pending. Not a standards-certified oversampled dynamic limiter. See V4_BATCH42.md.

Batch 43 adds combined bounded LUFS targeting and automatic measured peak correction with an explicit guard: a new normalization recipe computes each retry from the same unnormalized guarded PCM, with up to three attenuation retries, stricter sample cap, exact baseline/PCM replay, final full measurement audit and honest target attainment reporting. Legacy independent modes and receipts remain supported. 96 tests authored, 92 isolated cases passed (including four real FFmpeg tone tests using equivalent existing gain helpers); four repository integration cases and full CI unverified. Actual speech listening and physical Windows/model acceptance pending. See V4_BATCH43.md.

Batch 44 adds optional adaptive quiet-region dialogue attenuation (off/light/medium/strong), using per-turn 20 ms energy windows, conservative 20th-percentile quiet-floor estimation, contrast and floor bounds, 5 ms gain transitions, and exact integer PCM processing before speech peak normalization. CLI/dashboard, recipe replay and disabled legacy defaults. 97 cases authored; 91 isolated tests passed locally (0.83 s); six project/CLI/dashboard cases and full CI pending. This is adaptive level-based broadband attenuation, not spectral denoising, voice activity recognition or AI speech isolation; quiet speech may be reduced and subsequent normalization can amplify remaining noise. Real listening and physical model acceptance pending. See V4_BATCH44.md.

Batch 45 adds opt-in stationary-noise spectral subtraction with a fixed-point 128-point FFT, 64-sample overlap, frozen Q15 coefficients, per-turn quiet-profile estimation (at most 64 analysis frames), contrast-based bypass, bounded frequency-bin attenuation and normalized overlap-add reconstruction. CLI/dashboard, exact recipe replay, unchanged disabled defaults. 95 authored cases; actual isolated pytest run 89/89 passed in 2.09 s, six integrations pending. A 10-second synthetic input took 1.42 s for a single pass in this environment. Stationary noise suppression can also attenuate speech components; not AI speech isolation or validated real speech enhancement. Full CI, real listening and Windows performance remain pending. See V4_BATCH45.md.

Batch 46 adds two opt-in episode-clock active-speaker camera modes, continuous-drift and continuous-breathe, with an eight-second periodic phase and exact cumulative speech/pause offsets. Existing six modes retain their behavior. Static listeners and pause cards remain still; speaker/layout changes remain hard cuts, and mixed studio inherits motion from its audited base. 96 new authored cases, 92 standalone tests actually passed in 2.44 s, including 10 real FFmpeg tests (8 split/whole byte comparisons and 2 motion checks). Four integration cases and full CI remain unverified. See V4_BATCH46.md.

Batch 47 adds optional simulated listener portrait framing (static/drift/breathe) for grid and spotlight neural studios, with staggered global camera phase, interior-only crops and unchanged active speaker, static pauses, settings digest and honest receipt metadata. Static preview unchanged; mixed studio inherits the audited base. 90 new test cases authored, 85 passed locally, plus 92/92 Batch 46 camera tests rerun (177 total passed in 3.05 s); five new integration cases unexecuted, full CI unverified. Small portraits may show little visible motion due to pixel rounding. Not neural facial animation or reaction inference. See V4_BATCH47.md.

Batch 48 adds opt-in quick/gentle pause-only speaker handoff crossfades (up to 6/12 existing pause frames), skips same-speaker or under-three-frame pauses, preserves original timeline and speech segments, adds CLI/dashboard/background-upload controls and immutable transition binding plus scheduled handoff count. Mixed studio reuses audited base. 101 new authored cases: 96 isolated tests actually passed in 0.77 s, including 8 actual FFmpeg renders; five integration cases unexecuted, full CI and real Windows/model acceptance pending. Not a crossfade of moving neural speech clips; transitions blend still pause cards. See V4_BATCH48.md.

Batch 49 adds match-quick and match-gentle pause handoffs using the last decoded frame of the outgoing rendered speech segment and first decoded frame of the incoming segment. Defers matched pauses until both speech segments are rendered and checked, then concatenates in original chronological order. Holds/blends frozen endpoints (including existing labels), not moving facial clips; no audio/subtitle changes, no added frames, old modes unchanged. 86 dedicated cases authored; 84 standalone tests actually passed (0.79 s), including nine FFmpeg raw-video endpoint tests; two compositor integration cases unexecuted. Full CI, actual model/hardware visual review pending. See V4_BATCH49.md.

Batch 50 adds neural studio dashboard verified-segment/frame progress, provisional remaining-segment ETA and cooperative precommit cancellation; distinguishes mux verification, input revalidation/commit and final audit, including deferred endpoint rendering and existing candidate audit. Scratch output discarded on precommit stop; no force-killing FFmpeg or cancellation during immutable save. 74 new authored cases; 69 isolated tests passed and 84 Batch 49 standalone cases reran, 153 total in 0.80 s. Five new integration cases unexecuted; repository DNS blocked. Existing .github/workflows/tests.yml verified present (Windows/Linux matrix, FFmpeg and clean source ZIP); current CI result unavailable. See V4_BATCH50.md.

Batch 51 extends verified render progress and cooperative precommit stopping to mixed video/studio composition; validated nonempty intro/speech/outro scene counts, separate mixed stage labels, no unreliable scene ETA, preserved mix listening PASS and source-binding audits. 78 dedicated new cases authored; 69 standalone passed plus 69 previous progress tests rerun (138 passed in 0.13 s). Nine mocked full-repo integration cases authored but unexecuted. Full CI, real model, full episode and physical Windows acceptance remain unverified. See V4_BATCH51.md.

Batch 52 adds explicit neural studio compose/resume with a private, input/plan/renderer-bound verified segment cache, SHA-256 and decoded frame checks, atomic staging, dependency hashes for matched pause endpoints, safe path checks, and stop-compatible cache retention. Existing compose remains ephemeral; resumable ETA intentionally disabled. 80 dedicated tests authored; 73 standalone passed in 1.34 s including three actual FFmpeg/ffprobe cache restores. Seven integration cases unexecuted; full CI and Windows/model acceptance pending. Cache persists even after success; manual cleanup only, not approved output or authenticated storage. See V4_BATCH52.md.

Batch 53 adds explicit private studio-cache inventory and single-namespace cleanup with metadata snapshots, exact namespace selection, project locking and dual dashboard consent. Reports logical bytes, entry/pair counts and latest file mtime; does not verify content or classify obsolete caches. Rejects unsafe paths, unknown names, changed snapshots and unbounded trees; no automatic pruning. 64 new cases authored; 61 standalone actually passed in 0.45 s, three repository integration cases unexecuted. No user cache was deleted. See V4_BATCH53.md.

Batch 54 adds explicit mixed-video and mixed-studio resume, partitioning existing intro/speech/outro into at most 1,500-frame (60-second) chunks. Reuses the private verified cache and admin controls; namespace binds mix/base receipts and renderer. Uses normalized frame-index trim, not approximate seek; repeated prefix decoding may be slower, and chunks can still exceed the cache byte limit. Ordinary compose unchanged. 80 new cases authored; 72 standalone actually passed in 1.95 s including six real FFmpeg raw-frame comparisons, eight full-repo integration cases unexecuted. See V4_BATCH54.md.
