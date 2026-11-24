# V4 batch 29 — expanded local authoring, Mandarin and free-policy drafting

Previous CI 45491404566 and 45492395979 both completed 6/6. This increment adds four browser workflows, Mandarin frontend, safer credential prompting, and broad regression coverage. No real model or billing acceptance claim.

## Dashboard
- Import one matching authorized PCM16 mono 16 kHz WAV by approved script turn ID; existing source and duplicate checks apply.
- Save immutable focus/grid studio settings with optional authorized PNG, inspect settings, no arbitrary path reads.
- Freeze 1–8 selected reviewed prior dialogue turns and inspect current continuity; explicit local-only consent, exact immutable cast matching. No automatic memory mining.
- One cloud text drafting action (outline or one script unit), explicit text transfer and local fallback consent; optional separate Gemini unbilled Free Tier confirmation. Existing OpenRouter free -> confirmed Gemini -> approved local Ollama policy. Keys remain CLI-managed; no browser key input; no paid model fallback. Billing tier cannot independently be verified. Continuity projects blocked from browser cloud drafting. Consent never persisted. Finalization and human approval remain separate.
- Selected file bytes go to localhost only. Existing CSRF, size limits, private staging, operation locks and immutable receipts apply. Real browser interaction pending.

## Mandarin
Optional dependency group kokoro-mandarin installs Misaki zh extras under existing explicit install policy. Kokoro v1.0 Mandarin ZHG2P(version=None) uses eight candidate presets, not verified installed assets. Upstream references: [Kokoro pipeline](https://github.com/hexgrad/kokoro/blob/main/kokoro/pipeline.py), [voice catalog](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md), [Misaki](https://github.com/hexgrad/misaki). Prepare trusted resources manually, use offline environment. Japanese remains disabled because dictionary/runtime setup requires separate verification. No automatic model/dictionary downloads authorized. V4 rejects phoneme sequences longer than 510 before inference rather than risk truncation; revise/split the approved script and review again. Mixed-language accuracy is unverified.

```cmd
.venv\Scripts\python.exe -m podcast_gpt dependency-plan --group kokoro-mandarin
.venv\Scripts\python.exe -m podcast_gpt dependency-install --group kokoro-mandarin --acknowledgment I_AUTHORIZE_INSTALLING_FREE_OPTIONAL_PYTHON_PACKAGES
```

Session hidden key prompting fails closed if secure terminal entry unavailable; persistent storage still Windows DPAPI only. Gemini encrypted key is not decrypted for project cloud calls without separate confirmation.

## Work item accounting
Six grouped feature areas: Mandarin frontend and presets, long phoneme rejection, credential isolation/hidden input, cloud drafting, audio/studio authoring, continuity controls. Regression matrix adds 155 cases: 39 compatible preset cases, 39 cross-language rejection cases, 60 geometry combinations, 8 invalid loudness targets, 8 invalid authoring requests, 1 dependency-group check. Four additional workflow tests cover cloud consent, uploads/continuity, Mandarin constructor and hidden-input failure. Total 159 new test cases authored, not 159 separate product features or completed real-world tests. CI pending. Actual user hardware, browser interaction, public cloud eligibility and model inference not verified. Full 100–200 feature-task completion is not claimed.

Batch 29 and 30 CI completed successfully (45494573255, 45495891248 latest combined: 6/6 each). Batch 31 adds explicitly consented local CPU portrait candidate generation with safetensors inventory and immutable candidate receipt; new CI pending. Real model setup, physical acceptance and portrait quality remain unverified. See docs/V4_BATCH31.md (repository-relative).
