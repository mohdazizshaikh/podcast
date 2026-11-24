# V4 local Hindi TTS and exact master audio

Requires approved current script, assigned authorized distinct portraits, and explicit Kokoro Hindi preset for each participating local speaker (hm_omega, hf_alpha, hm_psi, hf_beta). Distinct presets are required, so at most four Kokoro Hindi voices in this adapter; other characters can use authorized imported PCM recordings. Hindi only; wider language and Edge adapters remain pending. Install trusted optional Kokoro ONNX, Misaki/eSpeak and compatible local assets following KOKORO_OFFLINE.md. No automatic downloads or external requests by this adapter. Third-party packages and model assets need independent trust/license review.

```cmd
.venv\Scripts\python.exe -m podcast_gpt project-tts-kokoro --project-id PROJECT_ID --model "D:\Models\kokoro.onnx" --voices "D:\Models\voices.bin" --run-local --acknowledgment I_HAVE_RIGHTS_TO_USE_LOCAL_MODEL_AND_VOICES --max-new 1
.venv\Scripts\python.exe -m podcast_gpt project-audio-status --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-audio-finalize --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-master-compose --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-master-audit --project-id PROJECT_ID
```

Generate 1–5 missing eligible turns per invocation. Imported turns are retained. Local generation records model and voices file hashes, voice preset and exact PCM; resume refuses different model assets. Local FFmpeg converts to 16 kHz mono PCM. Generation is synchronous; inference time depends on CPU. Incomplete output directories block rather than silently overwrite. Actual voice quality and model compatibility must be checked on physical Windows; tests inject fake model samples.

Once every turn is available, finalize the measured timeline and compose master/episode.wav in the current private audio version. The master contains original speech samples and exact 250 ms silence gaps; audit compares every PCM byte with the source, verifies frame count and hashes. No audio normalization, clipping, stretching, noise removal, background music or audio quality claim. Target duration remains informational. Human listening review, wider TTS languages, Edge, audio mixing and video rendering remain pending.

After master composition, complete the human listening workflow and selected static video preview using V4_PREVIEW.md. No lip-sync or production acceptance claim.

Optional saved local paths and eSpeak non-neural multilingual fallback are now available. See V4_MODEL_VOICES_PERSONA.md. Wider natural neural TTS still pending.

An optional separate audio-only normalized/music/intro/outro candidate is now available (V4_POST_AUDIO_RECOVERY.md). It never replaces the original exact master or inherits approval.

V4 Kokoro adapter now also accepts explicit Spanish, French, Italian and Brazilian Portuguese candidate presets. See V4_LANGUAGE_RESEARCH.md for limits and setup. Existing Hindi receipts preserved.
