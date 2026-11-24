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
| Versioned manual script editing and human script review | Implemented | 45452467622: 4 core jobs passed, remaining Windows/packaging pending at check |
| Measured audio timeline and actual rendering | Not implemented in V4 | Pending |
| Explicit multi-source public HTTPS capture and exact-excerpt citations | Done | 6/6 CI run 45451883118 (offline fixtures) |
| Automatic research discovery, semantic claim verification and human fact-checking | Not implemented | Pending |
| Reusable character profiles, authorized PNG library and cast binding | Implemented | New CI pending; synthetic PNG fixtures |
| AI portrait creation, personality-aware prompting and longitudinal memory | Not implemented in V4 | Pending |
| Multilingual TTS and 1–10 character general source schema | Not implemented in V4 | Pending |
| 1–60 minute landscape/vertical/square video rendering | Planning metadata only | Pending |
| Full dashboard, automatic/manual orchestration, ETA | Partial | Listing/diagnostics only |
| Real Windows model run and acceptance | Not verified | Local user hardware required |
| V4 production release | Not released | Pending actual acceptance |

## Next priority
Verify revision/review and character-library CI, then implement generalized measured audio timeline and voice engine compatibility, personality-aware prompting, automatic source discovery and claim verification, and generalized media rendering. Do not prematurely replace the V3 verified pipeline.

## Updating the tracker
For every development increment, update this file, V4_REQUIREMENTS.md, V4_ROADMAP.md, REMAINING.md and relevant setup docs. Cite actual CI run IDs after completion. Record new limitations and actual user-device tests separately. No paid fallback; cloud consent is per invocation; credentials/private media outside Git. No access to suspended repository.
