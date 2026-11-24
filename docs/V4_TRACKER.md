# V4 development and acceptance tracker

Last update: 2026-11-24. Status means implementation or automated verification only, not genuine AI output. This tracker supersedes stale planning-only descriptions in earlier incremental notes. Preserve stable-v3.7 at c68a0393e5f62abcbac70074e85cb1b4f5d22e76.

| Milestone | Implementation | Verification |
|---|---|---|
| V3 stable snapshot + Windows ZIP | Done | 6/6 CI run 45384845406 |
| V4 setup inventory | Done | 6/6 run 45392228899 |
| Free provider fallback and outline planner | Done | 6/6 run 45445343089 (mock AI only) |
| Private project manager and Windows DPAPI | Done | 6/6 run 45447184831 (Windows synthetic DPAPI test) |
| Bounded PDF/DOCX/TXT/MD/custom script and HTTPS input | Done | 6/6 run 45448095544 (fixture-only HTTPS) |
| Persistent model path configuration / guided installs | Partial | Inventory only |
| Full dialogue drafting and resumable checkpoints | Done | 6/6 CI run 45449334764 (synthetic 60-minute/10-presenter coverage) |
| Versioned manual script editing and human script review | Done | 6/6 CI run 45452467622 |
| Version-bound authorized PCM imports and measured audio timeline | Done | 6/6 CI run 45455331211 (synthetic WAVs) |
| Exact PCM master audio composition and audit | Done | 6/6 CI run 45456602766 (synthetic PCM) |
| Version-bound human listening review | Implemented | 45457590951: 4 core jobs passed at check; Windows/packaging pending |
| Audio normalization/mixing and generalized neural rendering | Not implemented in V4 | Pending |
| Explicit multi-source public HTTPS capture and exact-excerpt citations | Done | 6/6 CI run 45451883118 (offline fixtures) |
| Automatic research discovery, semantic claim verification and human fact-checking | Not implemented | Pending |
| Reusable character profiles, authorized PNG library and cast binding | Done | 6/6 CI run 45453165135 (synthetic PNGs) |
| AI portrait creation, personality-aware prompting and longitudinal memory | Not implemented in V4 | Pending |
| V4 local Hindi Kokoro adapter with preset/model provenance | Done | 6/6 CI run 45456602766 (fake model fixture) |
| V4 local CPU SadTalker pilot, source-bound clips and reviewed batch | Implemented | New CI pending; synthetic model runner |
| Other language TTS, Edge adapter and final neural composition | Not implemented in V4 | Pending |
| Selected landscape/vertical/square static preview and measured SRT | Implemented | 45457590951: 4 core jobs passed at check; Windows/packaging pending |
| Full-length real neural video and dynamic camera layouts | Not implemented in V4 | Pending |
| Full dashboard, automatic/manual orchestration, ETA | Partial | Listing/diagnostics only |
| Real Windows model run and acceptance | Not verified | Local user hardware required |
| V4 production release | Not released | Pending actual acceptance |

## Next priority
Verify preview and neural pilot/clip CI, then implement final neural composition against exact master audio with selected aspect ratio, synchronized SRT, full human QA and safe recovery. Broader TTS, personality-aware prompting, automated research, graphical controls, and physical Windows acceptance remain pending. Do not prematurely replace the V3 verified pipeline.

## Updating the tracker
For every development increment, update this file, V4_REQUIREMENTS.md, V4_ROADMAP.md, REMAINING.md and relevant setup docs. Cite actual CI run IDs after completion. Record new limitations and actual user-device tests separately. No paid fallback; cloud consent is per invocation; credentials/private media outside Git. No access to suspended repository.
