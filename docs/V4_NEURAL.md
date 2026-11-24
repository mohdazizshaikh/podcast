# V4 generalized CPU SadTalker pilot and resumable clips

Requires the current reviewed script, complete authorized cast, measured audio timeline, audited master and explicit human listening PASS. Static preview itself is optional. Install trusted local SadTalker and its pretrained assets using SADTALKER_CPU_SETUP.md; the app does not install or authenticate third-party code, verify licenses, or guarantee the model can load. The local interpreter preflight executes only a version probe before inference. Run only trusted code/assets; the external process is not a network or process sandbox.

The source-bound chunk plan divides each exact turn PCM into equal sample ranges no longer than 10 seconds. Cuts may occur mid-word. First eligible >=1-second chunk per speaking presenter becomes the pilot. Every presenter must have an eligible pilot. Each clip receipt binds exact chunk PCM, portrait, current master/review, request/cast and selected local model fingerprint. The fingerprint includes inference.py, interpreter, config and checkpoint bytes, not the complete dependency tree. A full structural decode verifies clip coverage, not actual facial motion.

```cmd
.venv\Scripts\python.exe -m podcast_gpt project-neural-status --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-neural-run --project-id PROJECT_ID --model "D:\Models\SadTalker" --python "D:\Models\SadTalker\.venv38\Scripts\python.exe" --mode pilot --max-new 1 --run-local --acknowledgment I_HAVE_RIGHTS_AND_TRUST_THIS_LOCAL_SADTALKER_INSTALLATION
.venv\Scripts\python.exe -m podcast_gpt project-neural-pilot-template --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-neural-pilot-record --project-id PROJECT_ID --acknowledgment I_WATCHED_EVERY_CURRENT_PILOT_CLIP
```

Repeat pilot until every presenter has a saved clip; watch every clip and fill every template observation (lip sync, identity, visual quality, audio alignment) PASS or FAIL. An immutable PASS on all pilot clips unlocks batch mode. Use the same run command with --mode batch, 1–3 new chunks per invocation. Explicit model consent is per invocation. Max 120–7200 seconds per chunk timeout, default 1800; preflight, hashing, decode and cleanup add overhead. No background run. At least 6 GiB workspace free; CPU thread hints are not speed or RAM guarantees. Model scratch failures are preserved and block retries at the same chunk until manually inspected; dedicated recovery remains pending. Do not delete or replace completed receipts.

The current clips are raw model output, not composed into an episode or selected video aspect ratio. Short chunks may not be supported by actual SadTalker; genuine Windows pilot must confirm. Tests only use synthetic FFmpeg clips, marked fixture-only; production runs cannot mix those with real invocation receipts. Human pilot PASS is self-attestation, not publication approval. Final neural composition with original master audio, pauses, selected aspect ratio, synchronized subtitles and full episode QA remains pending.

Complete reviewed clips now feed selected-format candidate composition and audit (V4_EXPORT.md). Production CLI rejects fixture-only exports. Full human video QA and dedicated failure recovery remain pending.

Stopped current-binding missing-chunk scratch can now be archived explicitly through V4_ACCEPTANCE.md. Partial committed clips and orphan locks still need manual inspection.
