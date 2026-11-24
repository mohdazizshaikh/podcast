# Windows setup — original Hindi podcast (no dedicated GPU)

1. Install Python 3.11 and FFmpeg/FFprobe. Confirm `py -3.11 --version`, `ffmpeg -version`, `ffprobe -version` in a new CMD window. Optionally use `winget install Gyan.FFmpeg` for FFmpeg; installation source/availability may vary.
2. Clone **only new repo**: `git clone https://github.com/mohdazizshaikh/podcast.git` then `cd podcast`.
3. Double-click `START_PODCAST_WINDOWS.bat`. The local dashboard at `http://127.0.0.1:7860` will use `%USERPROFILE%\PodcastGPTStudio`. It checks FFmpeg/FFprobe and creates a Python 3.10+ environment (3.11 recommended). It installs application Python dependencies on first use or when the dependency fingerprint changes (internet may be required), but NEVER downloads pretrained SadTalker weights. Normal starts reuse the installed dependencies without calling pip. The browser opens only after the loopback server successfully binds; if the port is occupied, close the existing server or use `python -m podcast_gpt web --port 7861 --open-browser`.
4. Initialize project; edit private `project.json`. Supply 3 authorized human source portrait PNGs `portraits\aarav.png`, `meera.png`, `kabir.png` (>=200px) and 45 authorized genuine original WAVs `voices\001.wav` through `045.wav` (16kHz, 16-bit mono PCM). You may separately use `python -m podcast_gpt ... tts-one --turn 1 --allow-network-tts` after explicitly installing `pip install -e ".[tts]"`, which contacts Microsoft Edge's online service and offers only 2 Hindi voice IDs.
5. For fully LOCAL Hindi voice synthesis instead, install optional dependencies `.venv\Scripts\python.exe -m pip install -e ".[kokoro]"`, local eSpeak-ng, and a compatible local Kokoro ONNX v1.0 model/voice pack. Run `GENERATE_KOKORO_HINDI_CPU.bat` up to 5 new original WAVs per consented session. See `docs/KOKORO_OFFLINE.md`.
6. Verify source → export PCM chunks → render original static 720p MP4 AAC/SRT → independent decoder audit. The output is a REAL STATIC portrait video, **not yet moving lips**.
6. For moving faces, separately obtain/install allowed SadTalker CPU inference.py/model weights and Python3.8 environment, then run `RUN_NEURAL_CPU.bat`. Give explicit separate YES consent and start PILOT (one missing genuine sample per speaker, max3). Model may be slow on non-GPU hardware.
7. Open `REVIEW_THREE_PRESENTER_PILOT.bat`, inspect each actual original-speaking MP4 and record PASS/FAIL. Checks are private human observations, not certification. Continue BATCH/SESSION only after deciding output is acceptable.
8. After all chunks have signed decoder-audited real face MP4s, run `compose-neural`, `audit-neural`, `review-full`; manually review all 45 turns and identity/rights before ever publishing yourself.

Never put your private workspace inside the public clone. The old suspended GitHub account is not contacted.
### Privacy and original media imports (v3.3.1)

When importing a presenter PNG from the local browser, tick the explicit checkbox confirming you own the portrait or hold written permission. The private localhost HTTP server also requires this acknowledgment and refuses missing consent. The checkbox does not automatically verify your permission. File import and signed-source processing cannot overlap, and `000.wav` is not a valid 45-turn original voice name. Existing media can never be overwritten.

### Optional online Edge TTS safe source import (v3.5)

This is **NOT OFFLINE**; the selected Hindi dialogue is sent to an online Microsoft Edge voice service and may be subject to its terms. Only after consciously opting in, install `.venv\Scripts\python.exe -m pip install -e ".[tts]"`. For exactly one missing original turn, run `.venv\Scripts\python.exe -m podcast_gpt --workspace "%USERPROFILE%\PodcastGPTStudio" tts-one --turn 1 --allow-network-tts` in CMD. The source **must not already be SHA-bound**. Existing original WAVs/checkpoint receipts are never overwritten, each new original voice is hash-recorded, and temporary downloaded/converted data stays on the private workspace drive. This option uses two voice presets rather than independently proving three distinct natural voices. All original voice content/rights and final 540–660 second duration require human verification.

### Read-only one-click status — v3.6

In `CONTINUE_FULL_HINDI_NEURAL.bat`, choose **READINESS**. Or use the READINESS button on the private local dashboard. It independently checks 45 voice WAVs (including duration gate), three PNGs, SHA-bound manifest, PCM chunks, and any present static/face/final videos and human pilot observation record. It reports the **next safe step** and refuses to mark broken/tampered evidence complete. The report does not run neural models, contact TTS services, download weights, encode video, write local files, or automatically approve publication. With many full videos it may take time to decode every clip.

### v3.7 — concurrent Windows source-binding and voice generation safety

Keep `PODCAST_WORKSPACE` **outside** the public Git repo and any other Git worktree; the platform now refuses a private workspace under a `.git` ancestor. Browser original-media imports, offline Kokoro synthesis, opt-in online Edge TTS and `BIND` share the private `source\originals-voice-and-binding-exclusive.lock` even when started from different CMD/PowerShell processes. Uploads can still occur before `INIT` and never silently initialize a project. If an operation crashes mid-way, READINESS shows the stale lock and refuses further source writes. Inspect the relevant processes and private files carefully **before** manually resolving an abandoned lock; never remove an active lock or overwrite a saved original WAV.

### CPU model setup diagnostics and thread budget

DOCTOR and MODEL now report detected logical CPUs and physical/available RAM where supported. These are host observations, not model memory requirements or performance benchmarks. A low available RAM warning is advisory. `run-cpu --cpu-threads 2` requests two threads in common native thread pools; the default is at most four and leaves one logical CPU free when possible. The actual model may override these hints. Model scratch and output drives each need at least 6 GiB free. Both SadTalker launchers accept a custom existing Python executable when .venv38 is absent. Relative paths supplied via CLI are made absolute before subprocess execution. No third-party model install or license is automatically certified.

### Interrupted model rendering recovery

After a failed model run, inspect the private logs in scratch/model-CHUNK-ID. In the guided launcher select RECOVERY (read-only). If all model and child processes are stopped, the CPU lock is clear, and the attempt has no verified or orphan preview, explicitly archive exactly one attempt using:

```cmd
.venv\Scripts\python.exe -m podcast_gpt archive-failed-attempt --chunk-id 001-001 --acknowledgment ARCHIVE_STOPPED_ATTEMPT
```

This moves the entire attempt to a unique private scratch/failed-attempts folder without deleting logs or adopting output. If the private workspace is not the default, supply --workspace before the command. Stale CPU locks and orphan preview files still require manual inspection. After fixing the cause, separately consent to a new model session. READINESS now identifies interrupted scratch as blocked. No automatic model restart or deletion.

### Guided local CPU installation and enforced pilot gate

See [SADTALKER_CPU_SETUP.md](SADTALKER_CPU_SETUP.md) for the separate legacy Python environment, official CPU wheel recipe, checkpoint guidance, and limitations. Before BATCH or SESSION, the launcher and core CPU command require a current all-three manual PASS record bound to the independently verified original sample hashes. A missing/failed/stale record blocks new inference. No approval of publication or actual quality is inferred.

### Full 45-turn manual QA record

After AUDITFULL, choose REVIEWFULL to watch every turn, then TEMPLATEFULL to create the private review/full-45-turn-review-template.json. Edit only each turn's five UNREVIEWED fields (lip_sync, voice, identity, captions, transitions) and rights_self_attested to honest PASS or FAIL. Do not edit candidate hashes. Save locally. Run:

```cmd
.venv\Scripts\python.exe -m podcast_gpt record-full-review --acknowledgment I_REVIEWED_ALL_45_ORIGINAL_HINDI_TURNS
```

Use --workspace before the command for a non-default studio. INSPECTFULL and READINESS validate the saved record against current decoded video, source, SRT and export report hashes. A stale or failed review cannot be treated as passed. The immutable private record is self-attested only; it never automatically approves quality, rights or publication. Keep both files outside Git.

### Install from a verified source-only ZIP

See [RELEASE_CANDIDATE.md](RELEASE_CANDIDATE.md) for the CI-produced candidate, SHA256 check and installation workflow. Git clone remains the complete developer installation method.

### Setup without opening the dashboard

For installation diagnostics, run START_PODCAST_WINDOWS.bat --setup-only from CMD. This performs the same prerequisite and dependency checks and exits without launching a browser or server; it does not pause on errors. Normal double-click behavior is unchanged. Hindi JSON remains valid under legacy Windows redirected encodings, using Unicode escapes when necessary.
