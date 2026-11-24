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
| Broad web search, automated semantic claim verification and corroboration | Not implemented | Pending |
| Reusable character profiles, authorized PNG library and cast binding | Done | 6/6 CI run 45453165135 (synthetic PNGs) |
| Opt-in cast-bound personality-aware dialogue prompts | Done | 6/6 CI 45462475819 (mock provider) |
| Local profile-based portrait preparation brief | Implemented | 6/6 CI 45482554584; no image synthesis |
| Authorized portrait attachment as immutable profile revision | Implemented | 6/6 CI 45483234208; no image inference |
| Explicit selected reviewed prior-episode continuity snapshot for local drafting | Implemented | 6/6 CI 45492395979; no automatic memory capture or real quality verification |
| AI portrait creation and automatic longitudinal memory | Not implemented in V4 | Pending |
| V4 local Hindi Kokoro adapter with preset/model provenance | Done | 6/6 CI run 45456602766 (fake model fixture) |
| V4 local CPU SadTalker pilot, source-bound clips and reviewed batch | Done | 6/6 CI 45458379123 (synthetic model runner) |
| Local eSpeak multilingual fallback and installed language inventory | Done | 6/6 CI 45462475819 (fake executable) |
| Kokoro Spanish/French/Italian/Brazilian Portuguese expansion | Implemented | 6/6 CI 45481266847 (mock inference) |
| English US/UK Kokoro frontend and dependency group | Implemented | 6/6 CI 45482554584; actual voices unverified |
| Mandarin Kokoro v1.0 frontend and optional dependency group | Implemented | CI 45494573255 five core jobs passed; packaging running at check; mocked frontend only |
| Japanese neural frontend and Edge adapter | Not implemented in V4 | Pending |
| Selected-format neural candidate composition, measured SRT and structural audit | Done | 6/6 CI 45458841874 (short synthetic fixture exports) |
| Full candidate-specific human video QA | Done | 6/6 CI run 45461563645 |
| Safe stopped neural scratch archive | Done | 6/6 CI run 45461563645; other failure modes manual |
| Read-only staged V4 readiness and dashboard action | Done | 6/6 CI run 45461563645 |
| Selected landscape/vertical/square static preview and measured SRT | Done | 6/6 CI run 45457590951 (short synthetic previews) |
| Authorized studio background and static focus/grid preview | Implemented | 6/6 CI 45482554584 |
| Separate neural focus/grid studio, per-turn switching and fresh QA | Implemented | 6/6 CI 45483234208; static listeners; synthetic only |
| Full-length real neural video and dynamic camera layouts | Not implemented in V4 | Pending |
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
| Browser authorized turn WAV, studio settings, continuity snapshot and one-action free-policy cloud drafting | Implemented | New CI pending; real browser/cloud acceptance pending |
| Expanded 159-case compatibility/regression coverage | Authored | CI 45494573255 five core jobs passed at check |
| Optional deterministic speech compression and exact mix audit | Implemented | New CI pending; 135 test cases authored; no dynamic true-peak limiter/denoising |
| Static project voice preflight, device acceptance checklist and browser per-turn diagnostics | Implemented | New CI pending; no physical certification |
| Graphical bounded audio mix composition | Implemented | New CI pending; 19 additional test cases; actual browser interaction pending |
| Full dashboard, automatic/manual orchestration, ETA | Partial | Overview/playback, authoring, explicit bounded local inference, research and live task status; review import and cooperative stop; explicit free-policy cloud drafting (keys CLI-only); live model ETA pending |
| Real Windows model run and acceptance | Not verified | Local user hardware required |
| V4 production release | Not released | Pending actual acceptance |

## Next priority
Verify batch 29 packaging and batch 30 CI. Next actual model setup/pilot, Japanese offline resource setup, local portrait inference, dynamic limiting/denoising, broader research, actual browser and physical Windows acceptance. Broad research corroboration remains pending. Live ETA and integrated dashboard remain pending. Physical Windows pilot and full episode acceptance remain mandatory; no production claim. Do not prematurely replace the V3 verified pipeline.

## Updating the tracker
For every development increment, update this file, V4_REQUIREMENTS.md, V4_ROADMAP.md, REMAINING.md and relevant setup docs. Cite actual CI run IDs after completion. Record new limitations and actual user-device tests separately. No paid fallback; cloud consent is per invocation; credentials/private media outside Git. No access to suspended repository.
