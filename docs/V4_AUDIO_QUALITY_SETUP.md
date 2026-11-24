# V4 audio quality diagnostics, ducking and guided model setup

## Optional music ducking

Existing peak-normalized mix behavior is unchanged by default (integer_peak_v1). For a new mix, specify an authorized background WAV and --duck-percent 1–90 to attenuate its level while speech is detected. The integer recipe uses a normalized speech sample threshold of 512 PCM units, bounded attack, 150 ms hold and gradual release. The versioned recipe is reconstructed exactly by existing PCM audit. Intro/outro and speech sample count remain unchanged. No replacement of an existing mix/master or inherited listening approval. Example:

```cmd
.venv\Scripts\python.exe -m podcast_gpt project-mix-compose --project-id PROJECT_ID --bed "D:\Private\music.wav" --duck-percent 75 --acknowledgment I_HAVE_RIGHTS_TO_ALL_ADDED_AUDIO_AND_AUTHORIZE_LOCAL_MIX
```

This is simple amplitude-driven ducking, not voice activity detection or perceptual optimization. Quiet speech or noise may produce imperfect results; listen to the entire mix before approving.

## Objective audio report

```cmd
.venv\Scripts\python.exe -m podcast_gpt project-audio-diagnostics --project-id PROJECT_ID --kind master
.venv\Scripts\python.exe -m podcast_gpt project-audio-diagnostics --project-id PROJECT_ID --kind mix
```

Also available in dashboard by choosing master/mix and Measure selected master/mix loudness. Audits the existing source and candidate under project lock, streams PCM peak, RMS, full-scale sample count and zero-sample fraction, and uses FFmpeg loudnorm analysis for integrated LUFS, true peak dBTP, loudness range and gating threshold. Nonfinite measurements are reported as null. Reference -16 LUFS and -1.5 dBTP are chosen starting targets, not universal publication standards. A suggested static gain is limited by measured true peak headroom. No gain applied; actual LUFS-target normalization/limiting and noise reduction remain pending. Measurements do not certify natural speech quality.

## Guided model setup

```cmd
.venv\Scripts\python.exe -m podcast_gpt model-setup-plan
```

Dashboard and CLI combine current application/hardware/storage inventory, saved local path checks, optional dependency group versions, approved local Ollama tags and engine-specific next steps. Existing setup guides are linked by repository-relative paths. No model installation, downloads, execution, or model quality guarantee. Use trusted local installations; actual device preflight, real pilot and full episode review remain mandatory.

## Provider behavior

A structured explicit refusal/filter from OpenRouter or Gemini is terminal; do not try another provider to evade it. Malformed local model inventory fails closed. Cloud environment keys are not read by generate_json without explicit cloud consent. Ordinary invalid JSON or unavailable provider still uses existing bounded eligible free-provider fallback. No paid fallback. These tests use mocked provider responses, not actual provider availability or account billing verification.

Optional measured static gain toward a target and per-turn PCM diagnostics now implemented in V4_NORMALIZATION_CONTINUITY.md. Target may remain unmet; no dynamic limiter or denoising. Existing recipes preserved.
