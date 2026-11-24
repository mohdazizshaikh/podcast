# V4 development and acceptance tracker

Last update: 2026-11-24. Status means implementation or automated verification only, not genuine AI output. This tracker supersedes stale planning-only descriptions in earlier incremental notes. Preserve stable-v3.7 at c68a0393e5f62abcbac70074e85cb1b4f5d22e76.

| Milestone | Implementation | Verification |
|---|---|---|
| V3 stable snapshot + Windows ZIP | Done | 6/6 CI run 45384845406 |
| V4 setup inventory | Done | 6/6 run 45392228899 |
| Free provider fallback and outline planner | Done | 6/6 run 45445343089 (mock AI only) |
| Private project manager and Windows DPAPI | Done | Run 45447184831: 5 core jobs passed; packaging in progress at check |
| Bounded PDF/DOCX/TXT/MD/custom script and HTTPS input | Implemented | New CI pending; fixture tests added |
| Persistent model path configuration / guided installs | Partial | Inventory only |
| Full dialogue generation, checkpoints and script QA | Not implemented | Pending |
| Verified live multi-source research and citations | Not implemented | Pending |
| AI portrait creation and character memory | Not implemented in V4 | Pending |
| Multilingual TTS and 1–10 character general source schema | Not implemented in V4 | Pending |
| 1–60 minute landscape/vertical/square video rendering | Planning metadata only | Pending |
| Full dashboard, automatic/manual orchestration, ETA | Partial | Listing/diagnostics only |
| Real Windows model run and acceptance | Not verified | Local user hardware required |
| V4 production release | Not released | Pending actual acceptance |

## Next priority
Chunked script generation against a source-bound outline, validated speaker IDs and dialogue, immutable per-section checkpoints, bounded calls, recovery, and actual duration estimation separate from measured audio. Then add citations/research and generalized media capabilities. Do not prematurely replace the V3 verified pipeline.

## Updating the tracker
For every development increment, update this file, V4_REQUIREMENTS.md, V4_ROADMAP.md, REMAINING.md and relevant setup docs. Cite actual CI run IDs after completion. Record new limitations and actual user-device tests separately. No paid fallback; cloud consent is per invocation; credentials/private media outside Git. No access to suspended repository.
