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
