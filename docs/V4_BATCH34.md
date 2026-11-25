# Batch 34 — research evidence and decoded audio integrity diagnostics

## Research
Existing `project-research-coverage --project-id ID` and dashboard research coverage report now expose per-citation exact excerpt matches in other captured sources, source IDs, quote lengths, uncited/single-host turns and unused captured sources. Matching passages may indicate syndication or quotation; they do not prove independent corroboration or semantic support. No network call, source mutation, new dependency or automatic approval.

## Audio
Existing `project-video-audio-check --project-id ID --kind neural` (or supported candidate kind) and dashboard report now include reference/decoded AC RMS and DC mean per flagged window. For windows of at least 0.1s, extra heuristic flags cover missing variable audio (reference AC RMS >=100, decoded <10), DC mean differences >=300 PCM units, and uncorrelatable nonquiet reference mismatch with residual >0.35. Counts are per flag and unique window; examples capped at 20. Reports include short-window count and exact uncompared reference/decoded frame counts. No alignment correction, automatic quality pass, audio mutation or new model inference.

## Validation and limitations
68 authored synthetic tests: 30 exact text matching, 1 ordering/empty test, 36 audio fault matrix cases, 1 multi-window/truncation/coverage test. Full CI not independently verified in this turn. The previous Batch 33 commit-status endpoints returned no checks; no pass or fail inferred. Real Windows browser, full episode, local model, human listening, semantic review, dynamic limiting and broader web research remain pending. Stable V3 untouched.
