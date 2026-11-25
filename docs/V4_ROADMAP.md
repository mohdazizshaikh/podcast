# V4 Smart AI Podcast Studio — staged development

V3 baseline: stable-v3.7 branch at c68a0393e5f62abcbac70074e85cb1b4f5d22e76. Six CI jobs passed and a source-only Windows candidate was produced. The original suspended repository is not accessed. The package version remains 3.7.0 until an accepted V4 release.

1. Unified setup inventory (first increment): hardware/RAM/disk, app prerequisites, optional local Kokoro and SadTalker inventories, CLI and Windows interactive launcher. Only a trusted interpreter version probe may be explicitly authorized. No model downloads or installations from this tool.
2. Guided explicit dependency installation and model configuration persistence, with validated local paths and separate consent before third-party downloads. Actual installation tested on physical Windows.
3. Character/voice profiles and project management, preserving existing source integrity and rights workflow.
4. Real three-presenter short pilot, measuring CPU time and quality; tune rendering based on actual results.
5. Full 540–660-second original Hindi episode, independently decoded and manually reviewed across 45 turns.
6. V4 production candidate only after actual local acceptance. Additional studio layouts, camera transitions, subtitles, audio processing and export presets should be driven by the pilot.

Current limitations: no physical desktop access, no genuine pretrained model run, no actual pilot or ten-minute output verified. Synthetic CI is not real AI quality evidence. No automatic publishing or paid API dependency.

## Confirmed expanded scope

See [V4_REQUIREMENTS.md](V4_REQUIREMENTS.md) for the user's confirmed personal-use scope, and [AI_PROVIDERS.md](AI_PROVIDERS.md) for the initial free provider and episode outline implementation. This is independent of the fixed V3 source pipeline; no automatic conversion or premature rendering is allowed.

## Execution sequence after confirmed scope
1. Setup and free text provider foundation — CI verified.
2. Private project storage and DPAPI credentials — 6/6 CI passed (45447184831).
3. Bounded source ingestion — 6/6 CI passed (45448095544).
4. Chunked full dialogue drafting and resume — implemented, CI pending; see V4_SCRIPT_GENERATION.md. Next: multi-source research, citation verification and manual script review/revision.
5. Character/voice profiles, actual multilingual media compatibility, generalized signed source, layout rendering, orchestration.
6. Physical Windows acceptance and V4 release. Track evidence in [V4_TRACKER.md](V4_TRACKER.md).

Dialogue drafting CI passed 6/6 (45449334764). Explicit multi-source research and excerpt citation matching implemented (new CI pending); next priorities human script review/revision, automated search discovery and character profiles. See V4_RESEARCH.md.

Versioned manual script editing and current-version human review implemented (CI pending). Research CI 45451883118 had three core jobs passed at last observation; Windows and packaging still pending. Next priorities persistent character/voice profiles, automatic discovery, measured audio pipeline, and general media rendering. See V4_SCRIPT_REVIEW.md and V4_TRACKER.md.

Research CI passed 6/6 (45451883118). Script review CI 45452467622 had four core jobs passed at initial check. Reusable character library, cast assignment and media preflight implemented (new CI pending); next priorities measured audio and language/voice compatibility, personality-aware prompts, automated discovery and general media rendering. See V4_CHARACTERS.md.

Script review and character library CI passed 6/6 each (45452467622, 45453165135). Version-bound authorized PCM import and measured timeline implemented (CI pending). Next priorities actual generalized TTS, composed audio and QA, followed by video composition and neural rendering. See V4_AUDIO.md.

Audio import/timeline CI passed 6/6 (45455331211). Local Hindi Kokoro adapter and exact master WAV implemented (CI pending). Next: human audio QA, generalized three-format static video and subtitles, broader TTS and actual neural rendering. See V4_TTS_MASTER.md.

Local Hindi TTS/master CI passed 6/6 (45456602766). Human listening review and selected three-format static preview/SRT implemented (CI pending); next priority generalized CPU neural pilot and per-turn checkpoint pipeline. See V4_PREVIEW.md.

Static preview CI 45457590951 had four core jobs passed at initial check. Generalized SadTalker CPU pilot/checkpoints and reviewed batch implemented (CI pending). Next: final neural composition, source-bound full video QA, safe recovery, then broader voice/image/UI workflows. See V4_NEURAL.md.

Static preview/listening review CI passed 6/6 (45457590951). Neural pilot CI 45458379123 had both Ubuntu jobs pass at initial check. Selected-format neural composition and audit implemented (new CI pending); next full human QA and safe failure recovery, broader voice/image/UI workflows. See V4_EXPORT.md.

Neural pilot and candidate export CI completed 6/6 each (45458379123, 45458841874). Combined full QA, stopped scratch recovery and selected-project dashboard readiness implemented (CI pending). Next broader voice/language and character-aware prompting, persistent model setup, interactive visual controls and safe orchestration; real device acceptance remains mandatory.

Combined acceptance CI 45461563645 had four core jobs passed at initial check. Saved local model paths, eSpeak fallback and character-aware prompts implemented (new CI pending). Next visual editing/review, orchestration, safe installation workflow and wider neural TTS; actual hardware acceptance remains mandatory.

Acceptance CI passed 6/6 (45461563645); model-config/eSpeak/persona CI 45462475819 passed five core jobs, packaging pending at check. Combined workflow controls implemented (CI pending). Next wider natural voices, actual local pilot, graphical media QA, progress and model asset setup. See V4_WORKFLOW.md.

Model-config/eSpeak/persona CI passed 6/6 (45462475819). Workflow CI 45463360856 had three jobs passed at check. Combined media orchestration, timing and visual QA implemented, CI pending. Next wider natural TTS, recovery, audio processing and research/portrait workflows.

Workflow CI 45463360856 and media workflow CI 45464174884 passed 6/6 each. Audio-only mix and expanded incomplete-output recovery implemented (new CI pending). Next mixed-video integration, wider natural TTS, research/portrait and actual hardware acceptance.

Audio post-production CI 45478604299 failed four matrix jobs at CLI doctor due parser shadowing. Fixed parser, added regression test and mixed-video candidate/QA (new CI pending). Next wider neural voices, research/portrait and dashboard; physical Windows acceptance mandatory.

Corrective audio/mixed-video/recovery CI 45479131328 passed 6/6. Combined Kokoro language expansion, Wikipedia candidate discovery and optional factual review implemented (CI pending). Next English/CJK voices, local pilot, portrait/studio controls and dashboard; actual device acceptance mandatory.

Language/research CI 45481266847 had five core jobs passed, packaging pending at check. English/studio/portrait preparation implemented (new CI pending). Next actual Windows model tests, CJK frontend, neural studio composition, local portrait generation, integrated dashboard and ETA.

Language/research CI 45481266847 passed 6/6. English/static studio CI 45482554584 had three jobs passed at check. Neural studio composition, separate QA, expanded recovery and portrait attachment implemented (new CI pending). Next actual model pilot, CJK, local portrait inference, integrated dashboard and mixed studio.

English/static studio CI 45482554584 passed 6/6. Neural studio CI 45483234208 had four jobs passed at check. Combined dashboard overview, local playback and historical neural-stage estimate implemented (CI pending). Next real model acceptance, mixed studio, local portrait generation and CJK, full GUI and live progress.

Neural studio CI 45483234208 passed 6/6; dashboard overview CI 45484187245 had three jobs passed at check. Dashboard creation/processing controls and mixed neural studio implemented (new CI pending). Next real model setup/acceptance, CJK and portrait inference, full GUI and live progress.

Dashboard overview CI 45484187245 and mixed studio CI 45484813520 each passed 6/6. Graphical authoring implemented (new CI pending). Next actual model acceptance, CJK and portrait inference, browser production controls and live progress.

Authoring CI 45487275746 running at check. Browser local inference, research pack controls and live elapsed/checkpoint status implemented (new CI pending). Next real model acceptance, CJK, image inference and graphical approval recording.

Authoring CI 45487275746 five core jobs passed at check; inference CI 45487824070 running. Review/revision imports, checkpoint stop and structured manual script implemented (new CI pending). Next real model acceptance, CJK, image inference and free cloud consent controls.

Corrective note: graphical authoring CI 45487275746 completed 6/6. Inference CI 45487824070 reported three failing tests in Ubuntu matrix: script progress variable shadowed callback, and offline credential isolation was applied to inventory rather than generate_json. Both code regressions corrected in subsequent commit; existing regression tests retained. Corrective CI pending. Actual model/browser acceptance remains unverified.

Corrective CI 45488657835 6/6 passed. Audio ducking/diagnostics, provider hardening and model setup plan implemented (CI pending). Actual model setup and acceptance, loudness-target processing, CJK, local portrait inference and free cloud consent UI remain pending.

Prior CI 45491404566 had three core jobs passed at initial check. Bounded measured static gain, per-turn diagnostics and selected episode continuity implemented (new CI pending). Next actual model acceptance, CJK, image inference, cloud consent controls, dynamic limiting/denoising and remaining UI.

CI 45491404566 and 45492395979 passed 6/6 each. Batch 29 expanded authoring and consented drafting plus Mandarin and regression matrix implemented; new CI pending. Next Japanese resource preflight, real device acceptance, portrait inference and dynamic audio processing.

Batch 29 CI 45494573255 five core jobs passed at check. Batch 30 optional speech compressor implemented, new CI pending. Continue graphical mixing, preflight and actual device acceptance.

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
