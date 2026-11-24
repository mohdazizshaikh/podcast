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
| Audio-only peak normalization, background bed, intro/outro mix | Implemented | CI 45478604299 failed CLI parser regression; fix included; retest pending |
| Mixed audio listening review, intro/outro video, shifted SRT and fresh video QA | Implemented | New CI pending; synthetic fixture only |
| Safe incomplete-output archive (seven types) | Implemented | CI 45478604299 failed CLI parser regression; corrected parser and added mixed export; retest pending |
| Explicit multi-source public HTTPS capture and exact-excerpt citations | Done | 6/6 CI run 45451883118 (offline fixtures) |
| Automatic research discovery, semantic claim verification and human fact-checking | Not implemented | Pending |
| Reusable character profiles, authorized PNG library and cast binding | Done | 6/6 CI run 45453165135 (synthetic PNGs) |
| Opt-in cast-bound personality-aware dialogue prompts | Done | 6/6 CI 45462475819 (mock provider) |
| AI portrait creation and longitudinal memory | Not implemented in V4 | Pending |
| V4 local Hindi Kokoro adapter with preset/model provenance | Done | 6/6 CI run 45456602766 (fake model fixture) |
| V4 local CPU SadTalker pilot, source-bound clips and reviewed batch | Done | 6/6 CI 45458379123 (synthetic model runner) |
| Local eSpeak multilingual fallback and installed language inventory | Done | 6/6 CI 45462475819 (fake executable) |
| Wider neural multilingual TTS and Edge adapter | Not implemented in V4 | Pending |
| Selected-format neural candidate composition, measured SRT and structural audit | Done | 6/6 CI 45458841874 (short synthetic fixture exports) |
| Full candidate-specific human video QA | Done | 6/6 CI run 45461563645 |
| Safe stopped neural scratch archive | Done | 6/6 CI run 45461563645; other failure modes manual |
| Read-only staged V4 readiness and dashboard action | Done | 6/6 CI run 45461563645 |
| Selected landscape/vertical/square static preview and measured SRT | Done | 6/6 CI run 45457590951 (short synthetic previews) |
| Full-length real neural video and dynamic camera layouts | Not implemented in V4 | Pending |
| Offline visual script editing and review JSON import | Done | 6/6 CI 45463360856; actual browser interaction pending |
| Bounded foreground orchestration and per-action elapsed timing | Done | 6/6 CI 45463360856 |
| Configured TTS/neural foreground orchestration | Done | 6/6 CI 45464174884 (mock inference) |
| Persistent media action timing history | Done | 6/6 CI 45464174884; historical only |
| Offline audio/pilot/final visual QA and JSON import | Done | 6/6 CI 45464174884; browser interaction pending |
| Full dashboard, automatic/manual orchestration, ETA | Partial | Offline script/media QA and configured CLI runner; no live ETA |
| Real Windows model run and acceptance | Not verified | Local user hardware required |
| V4 production release | Not released | Pending actual acceptance |

## Next priority
P0 verify CLI regression fix and audio/mixed-video/recovery CI. Next wider natural neural TTS, actual model setup/pilot, research/portrait workflows and dashboard. Live ETA and integrated dashboard remain pending. Physical Windows pilot and full episode acceptance remain mandatory; no production claim. Do not prematurely replace the V3 verified pipeline.

## Updating the tracker
For every development increment, update this file, V4_REQUIREMENTS.md, V4_ROADMAP.md, REMAINING.md and relevant setup docs. Cite actual CI run IDs after completion. Record new limitations and actual user-device tests separately. No paid fallback; cloud consent is per invocation; credentials/private media outside Git. No access to suspended repository.
