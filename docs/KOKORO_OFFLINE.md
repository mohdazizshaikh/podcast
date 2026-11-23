# Offline original Hindi CPU voice: local Kokoro ONNX (optional)

This is a **new reconstructed v3.1 integration**. It neither recovers the old v2 Kokoro scripts nor downloads pretrained weights without consent. It creates original voice WAVs ONLY; it does not animate faces, guarantee natural Hindi pronunciation or publish anything.

## What you install, manually

1. Use Windows Python 3.11 or 3.12 on a capable CPU. Install FFmpeg + FFprobe and **eSpeak-ng** (needed for Misaki Hindi phonemization) on your Windows system. `espeak-ng` installation and compatible DLL discovery vary by Windows environment; confirm with the upstream docs.
2. From the new `podcast` repository: `.venv\Scripts\python.exe -m pip install -e ".[kokoro]"`. Python dependency installation requires internet, but inference is local after installation.
3. Separately download compatible `kokoro-v1.0.onnx` model weights and `voices-v1.0.bin` voice pack from the upstream Kokoro ONNX project's official releases, verifying licensing and file origin yourself. **Never upload model weights, prompts, portraits or generated WAVs to PUBLIC Git.**
4. Double-click `START_PODCAST_WINDOWS.bat`, create the original 45-turn `project.json`, edit original Hindi text, and set your private workspace. Then run `GENERATE_KOKORO_HINDI_CPU.bat` and enter local model and voice file paths. It asks `YES` consent; at most 1–5 NEW original private WAVs are rendered in one explicit invocation. Re-run for the next set; it skips existing WAVs and never overwrites them.
5. Model voices per original presenter: `aarav=hm_omega` (male), `meera=hf_alpha` (female), `kabir=hm_psi` (different male). These are **three separate Hindi presets** in compatible Kokoro voice packs. Presets are not proof of genuinely distinct, natural or identity-safe speech; preview on your hardware.
6. Once all 45 WAVs are present and their combined original PCM duration is **540–660 seconds**, provide 3 separately authorized portraits, then run BIND → CHUNKS → STATIC, followed by actual separately consented SadTalker PILOT and human reviews.

CLI example (source project must already exist; model files downloaded by you):

```powershell
python -m podcast_gpt --workspace "$HOME\PodcastGPTStudio" tts-kokoro --model "D:\LocalModels\kokoro-v1.0.onnx" --voices "D:\LocalModels\voices-v1.0.bin" --next --max-new 3 --run-local
```

No command automatically contacts a cloud TTS server or downloads pretrained models. By contrast, the optional explicit `tts-one --allow-network-tts` Edge path **does** send text to an external TTS service.

## Source and API references

- [thewh1teagle/kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx) — upstream Python ONNX implementation (MIT package; model license separately documented).
- [Kokoro ONNX multilingual examples](https://github.com/thewh1teagle/kokoro-onnx/tree/main/examples) — Misaki `EspeakG2P`, local `Kokoro(...).create(..., is_phonemes=True)`.
- [Kokoro Hindi voice support](https://github.com/OpenTTSGroup/kokoro-open-tts/blob/main/README.md) — example `hf_alpha`, `hf_beta`, `hm_omega`, `hm_psi` voice identifiers.

All automated Kokoro tests use synthetic fake engine output with user-injected test functions only; **no actual ONNX weights or natural Hindi voice quality** are verified by CI.