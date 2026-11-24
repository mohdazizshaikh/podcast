# V4 audio post-production and incomplete output recovery

## Audio-only post-production candidate

The original exact PCM master stays immutable. This separate optional local candidate performs global peak normalization, a controlled looping background audio bed with overall/loop-edge fades, and optional intro/outro concatenation. Inputs must be authorized 16 kHz mono signed 16-bit PCM WAV. Intro/outro each at most 30 seconds, bed at most 120 seconds. No stock music is downloaded. Speech target defaults to 22000 PCM units, bed to 3000; bounded targets keep summed peaks below clipping. This is peak normalization, not LUFS normalization, compression, noise reduction or sidechain ducking. Intro/outro are peak-scaled; no crossfade. The implementation uses deterministic integer samples and verifies every output sample against the recipe.

```cmd
.venv\Scripts\python.exe -m podcast_gpt project-mix-compose --project-id PROJECT_ID --intro "D:\Audio\intro.wav" --bed "D:\Audio\music.wav" --outro "D:\Audio\outro.wav" --acknowledgment I_HAVE_RIGHTS_TO_ALL_ADDED_AUDIO_AND_AUTHORIZE_LOCAL_MIX
.venv\Scripts\python.exe -m podcast_gpt project-mix-audit --project-id PROJECT_ID
```

All three added audio inputs are optional. The private post-audio/episode-mix.wav and receipt bind the original verified master, exact added asset hashes, gain settings, duration and speech offset. The current video exporter still uses the original unmodified master; mixed video mux, intro/outro visuals and shifted subtitle export remain pending. Do not substitute the mix for the original master. This is an audio-only candidate requiring fresh human listening; previous approvals do not transfer. No automated publication.

## Incomplete artifact recovery

Only current-version directories with no completion receipt and a strict known filename set are eligible. Select audio-turn, master, static-preview, neural-clip, neural-export or post-audio. For an audio turn or neural chunk supply --unit with the exact ID. Dependent artifacts and reviewed pilot clips block unsafe archive. Any receipt (even invalid) blocks recovery. Some prerequisite corruption requires manual inspection. Existing stopped neural scratch recovery remains separate.

```cmd
.venv\Scripts\python.exe -m podcast_gpt project-incomplete-status --project-id PROJECT_ID --kind audio-turn --unit 0001
.venv\Scripts\python.exe -m podcast_gpt project-incomplete-archive --project-id PROJECT_ID --kind audio-turn --unit 0001 --acknowledgment I_STOPPED_ALL_PRODUCTION_PROCESSES_AND_AUTHORIZE_INCOMPLETE_OUTPUT_ARCHIVE
```

Stop every external producer first; lock absence is not evidence that all processes have stopped. An exclusive project lock protects archive, symlinks/reparse points and unexpected files are refused. Move original directory intact to unique private archive, never delete or overwrite. A separate explicit command retries the operation. If archive metadata write fails after rename, bytes remain in the archive. Stale locks, arbitrary scratch, corrupted completed artifacts and recovery involving reviewed downstream media remain manual. Synthetic tests verify sample processing and limited recovery cases, not perceptual audio quality or actual Windows model acceptance.

Separate mix listening review, mixed video export and shifted subtitles are now implemented in V4_MIXED_VIDEO.md; older audio-only limitation applies to earlier increment. Recovery now includes mixed-export. CI 45478604299 failed a CLI parser shadowing regression; fix/retest pending in subsequent increment.
