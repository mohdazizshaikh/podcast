# V4 development and acceptance tracker

Last update: 2026-11-25. Status means implementation or automated verification only, not genuine AI output. This tracker supersedes stale planning-only descriptions in earlier incremental notes. Preserve stable-v3.7 at c68a0393e5f62abcbac70074e85cb1b4f5d22e76.

| Milestone | Implementation | Verification |
|---|---|---|
| V3 stable snapshot + Windows ZIP | Done | 6/6 CI run 45384845406 |
| V4 setup inventory | Done | 6/6 run 45392228899 |
| Free provider fallback and outline planner | Done | 6/6 run 45445343089 (mock AI only) |
| Private project manager and Windows DPAPI | Done | 6/6 run 45447184831 (Windows synthetic DPAPI test) |
| Bounded PDF/DOCX/TXT/MD/custom script and HTTPS input | Done | 6/6 run 45448095544 (fixture-only HTTPS) |
| Persistent model path configuration / guided installs | Partial | 6/6 CI 45462475819 and 45463360856; third-party models manual |
| Full dialogue drafting and resumable checkpoints | Done | 6/6 CI run 45449334764 (synthetic 60-minute/10-presenter coverage) |
| Versioned manual script editing and human script review | Done | 6/6 CI run 45452467622 |
| Version-bound authorized PCM imports and measured audio timeline | Done | 6/6 CI run 45455331211 (synthetic WAVs) |
| Exact PCM master audio composition and audit | Done | 6/6 CI run 45456602766 (synthetic PCM) |
| Version-bound human listening review | Done | 6/6 CI run 45457590951 (synthetic fixtures) |
| Audio-only peak normalization, background bed, intro/outro mix | Done | Corrective CI 45479131328 6/6 passed; synthetic PCM |
| Optional deterministic speech-driven bed ducking and LUFS/true-peak diagnostics | Implemented | 6/6 CI 45491404566; actual listening pending |
| Measured bounded static loudness-target gain and per-turn PCM diagnostics | Implemented | 6/6 CI 45492395979; no dynamic limiter/denoising |
| Provider refusal stop, malformed local inventory rejection and no-consent key isolation | Implemented | 6/6 CI 45491404566; mocks |
| Guided model setup plan using saved local configuration | Implemented | 6/6 CI 45491404566; no installs or model load |
| Mixed audio listening review, intro/outro video, shifted SRT and fresh video QA | Done | 6/6 CI 45479131328; synthetic fixture |
| Safe incomplete-output archive (ten types) | Implemented | 6/6 CI 45484813520; synthetic tests, not all failure modes |
| Explicit multi-source public HTTPS capture and exact-excerpt citations | Done | 6/6 CI run 45451883118 (offline fixtures) |
| Explicit Wikipedia candidate discovery and source-bound optional human factual review | Implemented | 6/6 CI 45481266847 (offline fixtures) |
| 17 allowlisted Wikipedia editions and exact citation-coverage report | Implemented | 6/6 CI 45498392552; fixture network and review data |
| Exact cross-source excerpt reuse and unused-source review signals | Implemented | Batch 34 CI pending; no independence claim |
| Broad web search, automated semantic claim verification and corroboration | Not implemented | Pending |
| Reusable character profiles, authorized PNG library and cast binding | Done | 6/6 CI run 45453165135 (synthetic PNGs) |
| Opt-in cast-bound personality-aware dialogue prompts | Done | 6/6 CI 45462475819 (mock provider) |
| Local profile-based portrait preparation brief | Implemented | 6/6 CI 45482554584; no image synthesis |
| Authorized portrait attachment as immutable profile revision | Implemented | 6/6 CI 45483234208; no image inference |
| Explicit selected reviewed prior-episode continuity snapshot for local drafting | Implemented | 6/6 CI 45492395979; no automatic memory capture or real quality verification |
| Explicit local CPU Stable Diffusion portrait candidate generation | Implemented | 6/6 CI 45498392552; fake renderer only, real model setup/quality pending |
| Browser portrait worker, preflight, candidate audit and explicit attachment | Implemented | 6/6 CI 45500231172; real browser/CPU model pending |
| Bounded portrait candidate library, provenance validation and CLI attachment | Implemented | 6/6 CI 45500231172; incomplete attempts isolated, no automatic deletion |
| Automatic longitudinal memory | Not implemented in V4 | Pending |
| V4 local Hindi Kokoro adapter with preset/model provenance | Done | 6/6 CI run 45456602766 (fake model fixture) |
| V4 local CPU SadTalker pilot, source-bound clips and reviewed batch | Done | 6/6 CI 45458379123 (synthetic model runner) |
| Local eSpeak multilingual fallback and installed language inventory | Done | 6/6 CI 45462475819 (fake executable) |
| Kokoro Spanish/French/Italian/Brazilian Portuguese expansion | Implemented | 6/6 CI 45481266847 (mock inference) |
| English US/UK Kokoro frontend and dependency group | Implemented | 6/6 CI 45482554584; actual voices unverified |
| Mandarin Kokoro v1.0 frontend and optional dependency group | Implemented | 6/6 CI 45494573255; mocked frontend only |
| Japanese neural frontend with local resource gate | Implemented | 6/6 CI 45500231172; actual dictionary/model execution unverified |
| Explicit online Edge V4 adapter, browser generation, offline plan, online voice inventory and checkpoint stop | Implemented | Batches 37–38 CI pending; actual service/voice quality/browser acceptance pending |
| Selected-format neural candidate composition, measured SRT and structural audit | Done | 6/6 CI 45458841874 (short synthetic fixture exports) |
| Full candidate-specific human video QA | Done | 6/6 CI run 45461563645 |
| Safe stopped neural scratch archive | Done | 6/6 CI run 45461563645; other failure modes manual |
| Read-only staged V4 readiness and dashboard action | Done | 6/6 CI run 45461563645 |
| Selected landscape/vertical/square static preview and measured SRT | Done | 6/6 CI run 45457590951 (short synthetic previews) |
| Authorized studio background and static focus/grid preview | Implemented | 6/6 CI 45482554584 |
| Separate neural focus/grid studio, per-turn switching and fresh QA | Implemented | 6/6 CI 45483234208; static listeners; synthetic only |
| Optional active-speaker digital push-in and local hash-verified portrait preview | Implemented | New CI pending; real browser/visual acceptance pending |
| Read-only decoded video audio/source comparison | Implemented | New CI pending; heuristic PCM comparison, no automatic approval |
| Decoded audio dropout/DC/uncompared-frame diagnostics | Implemented | Batch 34 CI pending; heuristic only |
| Spotlight layout and four additional active-speaker camera modes | Implemented | 65 isolated local cases passed; full integration and visual acceptance pending |
| Full-length real neural video, cross-clip camera continuity and animated listeners | Not implemented in V4 | Pending |
| Offline visual script editing and review JSON import | Done | 6/6 CI 45463360856; actual browser interaction pending |
| Bounded foreground orchestration and per-action elapsed timing | Done | 6/6 CI 45463360856 |
| Configured TTS/neural foreground orchestration | Done | 6/6 CI 45464174884 (mock inference) |
| Persistent media action timing history | Done | 6/6 CI 45464174884; historical only |
| Offline audio/pilot/final visual QA and JSON import | Done | 6/6 CI 45464174884; browser interaction pending |
| Selected-project dashboard overview and hash-checked local browser playback | Implemented | 6/6 CI 45484187245; browser interaction pending |
| Browser project creation and explicit local non-inference production actions | Done | 6/6 CI 45484813520; browser interaction pending |
| Browser character profiles, cast assignment, source imports and local model configuration | Implemented | 6/6 CI 45487275746; browser interaction pending |
| Explicit browser local Ollama/Kokoro/eSpeak/SadTalker bounded inference | Implemented | Corrective CI 45488657835 6/6; mock inference |
| Browser Wikipedia discovery and research pack capture/status | Implemented | Corrective CI 45488657835 6/6; offline mocks |
| Live elapsed task status and verified action checkpoints | Implemented | Corrective CI 45488657835 6/6; no internal model percentage |
| Browser source-bound review and revision JSON import (ten kinds) | Implemented | Corrective CI 45488657835 6/6; human declaration mandatory |
| Task-ID scoped cooperative stop at action checkpoint | Implemented | Corrective CI 45488657835 6/6; no force kill |
| Structured verbatim timed custom script import | Implemented | Corrective CI 45488657835 6/6; knowledge mode and existing size/timing limits |
| Mixed neural studio export, shifted SRT, separate QA and recovery | Done | 6/6 CI 45484813520; synthetic only |
| Historical neural-stage ETA with matched completed timings | Implemented | 6/6 CI 45484187245; no live subprocess progress |
| Browser authorized turn WAV, studio settings, continuity snapshot and one-action free-policy cloud drafting | Implemented | 6/6 CI 45494573255; real browser/cloud acceptance pending |
| Expanded 159-case compatibility/regression coverage | Authored | 6/6 CI 45494573255 |
| Optional deterministic speech compression and exact mix audit | Implemented | 6/6 combined CI 45495891248; 135 test cases authored; no dynamic true-peak limiter/denoising |
| Static project voice preflight, device acceptance checklist and browser per-turn diagnostics | Implemented | 6/6 combined CI 45495891248; no physical certification |
| Graphical bounded audio mix composition | Implemented | 6/6 combined CI 45495891248; 19 additional test cases; actual browser interaction pending |
| Optional deterministic DC correction and soft low-level gate | Implemented | 6/6 CI 45498392552; not intelligent denoising; actual listening pending |
| Optional whole-mix dynamic sample-peak limiter | Implemented | 58 isolated synthetic cases passed; repository integration CI pending; not true-peak limiting |
| Combined sample limiter and measured static loudness gain | Implemented | Batch 36 CI pending; ceiling takes precedence, not dynamic true-peak limiting |
| Full dashboard, automatic/manual orchestration, ETA | Partial | Overview/playback, authoring, explicit bounded local inference, research and live task status; review import and cooperative stop; explicit free-policy cloud drafting (keys CLI-only); live model ETA pending |
| Real Windows model run and acceptance | Not verified | Local user hardware required |
| V4 production release | Not released | Pending actual acceptance |

## Next priority
Verify batches 33–39 CI. Next actual model setup/pilot, Japanese dictionary/model execution, real portrait inference, dynamic limiting/denoising, broader research, actual browser and physical Windows acceptance. Broad research corroboration remains pending. Live ETA and integrated dashboard remain pending. Physical Windows pilot and full episode acceptance remain mandatory; no production claim. Do not prematurely replace the V3 verified pipeline.

## Updating the tracker
For every development increment, update this file, V4_REQUIREMENTS.md, V4_ROADMAP.md, REMAINING.md and relevant setup docs. Cite actual CI run IDs after completion. Record new limitations and actual user-device tests separately. No paid fallback; cloud consent is per invocation; credentials/private media outside Git. No access to suspended repository.

Batch 34 extends existing read-only research coverage with exact cross-source excerpt reuse, single-host turn and unused-source review signals; decoded AAC diagnostics now flag missing variable audio, DC offset changes and uncorrelatable mismatch, report unique flagged windows and uncompared frames. 68 new synthetic regression cases authored (not independent features). Batch 33 CI could not be confirmed through the available commit-status endpoints; Batch 34 CI pending. Actual model/browser/device acceptance and semantic corroboration remain open. See V4_BATCH34.md.

Batch 35 implements optional deterministic whole-mix dynamic sample-peak limiting, including intro/bed/outro, immutable exact PCM audit, CLI/browser setting and legacy defaults. 63 new regression cases authored; 58 standalone limiter cases passed in an isolated local Python harness, five repository integration cases and full CI unverified. Sample peaks are not intersample true peaks; dynamic true-peak limiting, combined LUFS normalization, real listening and physical Windows/model acceptance remain pending. See V4_BATCH35.md.

Batch 36 permits an optional dynamic sample limiter followed by bounded static loudness gain. The gain is capped by the selected sample ceiling, the candidate must pass the measured true-peak ceiling, and the immutable receipt binds the limiter and normalization settings. Legacy no-limiter receipts retain their format. 62 new unit regression cases authored, plus a revised project/dashboard integration case; full Python test execution and real device/listening acceptance remain unverified. This is not dynamic intersample true-peak limiting or guaranteed LUFS attainment. See V4_BATCH36.md.

Batch 37 implements explicit online Edge V4 speech adapter with static locale/preset validation, 1–5 bounded approved turns, private temporary MP3/PCM conversion, immutable source-bound receipts, resume, duplicate rejection and CLI/readiness/preflight integration. 81 new regression cases authored (71 pure locale/receipt cases and 10 adapter/CLI cases); tests not yet independently run. No automatic network fallback, service/voice inventory guarantee, browser Edge action or real voice/device acceptance. See V4_BATCH37.md.

Batch 38 adds read-only Edge pending-turn planning, separate bounded consented online voice inventory with filtering and deduplication, optional dependency setup, browser generation/inventory/preview, turn-bound progress and cooperative stop, and local-only continuity protection. 63 new test cases authored; full repository CI and real browser/service/device acceptance unverified. See V4_BATCH38.md.

Batch 39 adds a spotlight studio layout for 1–10 presenters in landscape, vertical and square, plus four opt-in active-speaker camera modes (pull-out, smooth push-in, pan left/right) alongside existing fixed and push-in. Settings, CLI and dashboard support; static preview uses layout only, neural composition inherits bounded camera filters. 71 authored tests, 65 isolated local tests passed including six real FFmpeg filter/frame-count renders; six full-project integration tests and repository CI pending. Listeners remain static, camera resets at clip boundaries, and real browser/model/Windows acceptance remains open. See V4_BATCH39.md.
