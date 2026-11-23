# Architecture and threat model

`project.json` → optional explicit local Kokoro ONNX Hindi G2P + three distinct preset voice generation (no model download), or externally imported/online-consented original PCM → 45 validated original PCM WAVs + three PNGs → immutable source SHA manifest → exact-frame PCM chunks (1–10s) → FFmpeg/Pillow real 720p original static video + SRT.

Optional real neural stage: local explicit-rights/consent CPU SadTalker → one signed MP4+JSON per chunk → independent MP4 full decode/SHA → atomic checkpoint → local human pilot observations → full 45-turn candidate composer from original source WAVs and saved neural VIDEO ONLY → independent AAC/video/SRT audit → local 45-turn human review.

Dashboard is `127.0.0.1` only and rejects external origins and CSRF. It never serves `.png`, `.wav`, `.mp4`, `.json` workspace assets over HTTP. It never runs a model or posts media. HTML review is loaded locally by the owner.

Risks: external model licenses/weights, human likeness rights, private file security on user's PC, long CPU inference, manual lip-sync quality, non-cryptographic self-attested rights, old source-schema incompatibility. Source hashes detect accidental/modification changes but do not legally establish rights. A computer with no GPU may not produce satisfying results in practical time.
V3.3: The optional real CPU model stage first runs a read-only installed-model preflight before acquiring a session lock. Each face MP4's video stream must cover original PCM time, not merely its AAC audio. The compositor assigns frames using cumulative 24fps rounding across all 45 original dialogue turns and pauses to bound aggregate video drift. The saved original audio always supplies the final AAC stream. All structural checks remain separate from human visual/rights approval.
