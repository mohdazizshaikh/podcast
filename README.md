# Podcast GPT — Reconstructed Hindi Three-Presenter Studio (v3.7)

> **Rebuilt from this ChatGPT Project's available requirements/milestone history, NOT cloned from or verified against the suspended repository.** New canonical repository: **https://github.com/mohdazizshaikh/podcast**. No access to the suspended account is required. The original v2.97 Git history and exact source-byte parity **cannot be claimed** from chat summaries alone. See [`docs/RECONSTRUCTION_LEDGER.md`](docs/RECONSTRUCTION_LEDGER.md).

### One click on Windows without a dedicated GPU

1. Install **Python 3.11** (recommended) and **FFmpeg + ffprobe** on PATH (free). One official installation route for FFmpeg is `winget install Gyan.FFmpeg`. Install Git if cloning.
2. `git clone https://github.com/mohdazizshaikh/podcast.git` then open the `podcast` directory.
3. Double-click **`START_PODCAST_WINDOWS.bat`**. The launcher creates `.venv`, installs this app's free Python packages, opens `http://127.0.0.1:7860`, and uses a private default workspace: `%USERPROFILE%\PodcastGPTStudio` (unless `PODCAST_WORKSPACE` is set). Internet is needed on the first `pip install` or dependency refresh; routine starts reuse the installed dependencies. The browser opens only after the local server successfully binds. **AI models are NOT silently downloaded**.
4. Initialize the rebuilt **45 unique, original conversational Hindi turns** (15 per presenter; no repeated template filler), inspect/edit `project.json`, and provide **three authorized human portrait PNGs** (`portraits/aarav.png`, `meera.png`, `kabir.png`, each >=200px). Provide original, authorized `voices/001.wav` ... `045.wav`: 16,000 Hz, single-channel, signed 16-bit PCM, WAV. Both original and imported voices are accepted; real audio is never preloaded in Git.
5. **New optional fully LOCAL Hindi Kokoro ONNX three-voice path:** Download/install licensed Kokoro model and voice pack yourself (no automatic weight downloads), install `kokoro-onnx`, `misaki`, and eSpeak-ng, then run `GENERATE_KOKORO_HINDI_CPU.bat` for up to 1–5 NEW original voice WAVs per explicit invocation. It maps Aarav to `hm_omega`, Meera to `hf_alpha`, Kabir to `hm_psi`; they are distinct voice PRESETS, not a guarantee of distinct personalities or natural quality. All original WAVs convert to 16kHz mono PCM and remain private. See [Kokoro offline Hindi](docs/KOKORO_OFFLINE.md).
6. If you choose optional **online Edge Hindi TTS**, use the `tts-one --allow-network-tts` CLI. It sends the selected script text to an external voice service; it is **NOT** fully offline. Included voice presets use two available Hindi identifiers with a slightly adjusted speaking rate for Kabir; **three genuinely distinct neural voices are NOT guaranteed**. To meet that requirement, import three separately authorized real/locally generated voice recordings from your preferred offline engine.
7. After all 45 WAVs and 3 portraits exist, click **Bind original sources**. The program independently checks the ~10-minute duration (540–660 seconds), PNG validity, exact voice PCM and source hashes. Then **Export 1–10-second exact PCM chunks** and **Render original 720p static video + real AAC + SRT** (CPU only). This is a REAL media video but **NOT moving lips**.
8. For optional **real facial animation** install and obtain model weights for external SadTalker yourself, subject to its third-party licenses. First choose guided `MODEL` (or `CHECK_SADTALKER_CPU.bat`) for a READ-ONLY installed-model preflight: real Python executable, original SadTalker argument flags, source config and nonempty checkpoint assets; it does **not** load pretrained weights, check their legitimacy or run inference. Choose `PILOT` for one source-bound real speaking-face segment each from Aarav, Meera, Kabir. The CPU launcher asks explicit image-rights `YES`. A single finite call can run for a long time and uses up to 6 GiB free disk preflight. It is **not** a guaranteed free/fast fully offline 10-minute face renderer.
9. Run **private three-presenter manual review**, mark every face `PASS`/`FAIL` in the CLI using exact acknowledgment. Continue model `BATCH` (at most 5 new clips) or `SESSION` (at most 20 in an invocation) with new explicit consent, as desired. Each MP4 is independently decoder-audited, SHA-bound to original portrait/voice and saved for resume.
10. Once **all** original speech chunks have genuine saved/verified real face video and the pilot quality observation passes, explicitly **Compose candidate full 45-turn real neural video**. It renders video segments at consistent 24 FPS and joins them to the **original Hindi WAV timeline** (not re-synthesized model audio), then audits AAC/video and creates an SRT. The full 45-turn human review navigator remains required before any real-world publishing.

**Critical truthfulness:** Automated checks validate file provenance, PCM identity, video/audio structure and duration. They **do not** independently establish correct Hindi phonemes, natural-looking lips, likeness rights, user satisfaction, or publishing permission. The CPU inference model/weights are external; no genuine 10-minute neural episode has been run on your actual machine by this reconstruction.

## Guided command on Windows

Use the one-step textual guide (same concept as historical V2.90+):

```bat
CONTINUE_FULL_HINDI_NEURAL.bat
```

Or launch the real model CPU consent workflow directly:

```bat
RUN_NEURAL_CPU.bat "C:\Users\YOU\PodcastGPTStudio"
```

To manually record observations after 3 genuine verified face samples:

```bat
REVIEW_THREE_PRESENTER_PILOT.bat "C:\Users\YOU\PodcastGPTStudio"
```

Both 720p static and neural composition now stage large intermediates in the **private workspace `scratch/` directory** (not Windows system `C:\\TEMP`), and independently check free space on both actual scratch and export drives before encoding. Scratch must be a real private directory, not a symlink. This prevents a D:-drive studio from unexpectedly exhausting the C: system partition.

All media, portraits, scripts, WAVs, SadTalker model assets, runtime outputs and review notes should live outside this PUBLIC Git repo; `.gitignore` blocks common media/model/secrets but **always manually inspect `git status` before pushing**. The dashboard binds to loopback only, has per-instance CSRF protection, requires a separate self-attested portrait-rights acknowledgment for portrait upload, serializes uploads with source-binding jobs, and does not serve your media over HTTP. This does not independently certify permission or likeness rights. No YouTube/publishing tokens or automatic posting are part of the current software.

## CLI: independent source and media checks

```powershell
# From the repository root, after pip install -e .
python -m podcast_gpt --workspace "$HOME\PodcastGPTStudio" doctor
python -m podcast_gpt --workspace "$HOME\PodcastGPTStudio" init
# Edit project.json, add three authorized PNGs and 45 exact WAVs.
python -m podcast_gpt --workspace "$HOME\PodcastGPTStudio" build-source
python -m podcast_gpt --workspace "$HOME\PodcastGPTStudio" prepare-chunks
python -m podcast_gpt --workspace "$HOME\PodcastGPTStudio" render-static
python -m podcast_gpt --workspace "$HOME\PodcastGPTStudio" audit-static
python -m podcast_gpt --workspace "$HOME\PodcastGPTStudio" progress
python -m podcast_gpt --workspace "$HOME\PodcastGPTStudio" budget  # Read-only local measured CPU hours; never starts a model
```

For real SadTalker CPU model calls (owner/written-permission for ALL THREE images required):

```powershell
python -m podcast_gpt --workspace "$HOME\PodcastGPTStudio" run-cpu --mode pilot --max-new 3 --wall-seconds 7200 --per-chunk-timeout 1800 --sadtalker-root "C:\SadTalker" --sadtalker-python "C:\SadTalker\.venv38\Scripts\python.exe" --rights-confirmed
python -m podcast_gpt --workspace "$HOME\PodcastGPTStudio" review-pilot
python -m podcast_gpt --workspace "$HOME\PodcastGPTStudio" record-pilot --aarav PASS --meera PASS --kabir PASS --acknowledgment I_REVIEWED_ALL_THREE_ORIGINAL_HINDI_FACES
python -m podcast_gpt --workspace "$HOME\PodcastGPTStudio" inspect-pilot
python -m podcast_gpt --workspace "$HOME\PodcastGPTStudio" run-cpu --mode session --max-new 3 --wall-seconds 7200 --per-chunk-timeout 1800 --sadtalker-root "C:\SadTalker" --sadtalker-python "C:\SadTalker\.venv38\Scripts\python.exe" --rights-confirmed
python -m podcast_gpt --workspace "$HOME\PodcastGPTStudio" compose-neural
python -m podcast_gpt --workspace "$HOME\PodcastGPTStudio" audit-neural
python -m podcast_gpt --workspace "$HOME\PodcastGPTStudio" review-full
```

The `allow_short=True` Python-internal test parameter is never exposed as a production CLI flag and does not demonstrate a ten-minute podcast. No command should claim full-neural completion until the independent post-composition decoder/provenance gate succeeds.

## Feature status (new rebuilt code)

| Area | Implemented (source code) | Requires real user input/hardware validation |
|---|---|---|
| 45 original Hindi turns, 3 personas | Editable source project, timing/provenance | Voice duration must measure 540–660s |
| Natural Hindi TTS | Optional genuine local Kokoro ONNX 3 distinct Hindi voice presets; Edge online fallback; imported WAV | Real model files, G2P, license and actual voice quality/episode duration must be verified on user hardware |
| Images, rights, privacy | 3 genuine local PNGs, strict no-replace, explicit inference consent | Creator rights verified externally by the user, never automated |
| Exact original speech PCM | 16kHz mono WAV validation, SHA, 1–10s precise chunks | Voices supplied or synthesized |
| Static 3-presenter full MP4 | Pillow studio + FFmpeg H264/AAC and full SRT, independent decoder | GPU-free video can take time on weak CPUs |
| Real face previews | External SadTalker `--cpu`, finite PILOT/BATCH/SESSION, SHA/decoder/resume | SadTalker weights/Python 3.8 environment installed separately |
| Human quality checks | Local-only 3-face reviewer + fail/pass records; 45-turn seek navigator | Actual full Hindi phoneme and face quality must be judged by a human |
| Full neural composition | Source-bound face-videos + ORIGINAL PCM mix and AAC/SRT; independent audit | All real saved preview clips, actual CPU render and human QA |
| Windows/Browser | One-click setup + loopback dashboard with local uploads and job state; guided BAT | Python/FFmpeg installations and adequate RAM/storage |
| CI/source preservation | Automated synthetic unit tests, private media ignore rules | Tests cannot prove output of external SadTalker weights / complete real 10m run |

## Files and output directory

The public repository contains Python source (`podcast_gpt/`), Windows launchers (`*.bat`), tests, CI and docs. It intentionally **does not include** human photos, WAVs, generated MP4s, pretrained model weights, .env secrets or a private example dataset.

The local private workspace uses:

```text
PodcastGPTStudio/
  project.json                   # 45 editable original Hindi turns and voice presets
  portraits/{aarav,meera,kabir}.png  # ORIGINAL rights-confirmed images
  voices/001.wav ... 045.wav     # ORIGINAL exact 16k mono PCM recordings
  source/source-manifest.json   # SHA binding of all 45 WAVs+3 portraits+script
  source/chunks-manifest.json   # precise speech chunk source+sha mapping
  chunks/001-001.wav ...        # exact original frames, no resynthesis
  previews/001-001.mp4/.json    # real verified CPU model + SHA provenance pairs
  exports/original_hindi_static.mp4/.json
  exports/original_hindi.srt
  exports/original_hindi_full_neural.mp4/.json
  exports/original_hindi_full_neural.srt
  review/                        # offline HTML + self-attested original face notes
  scratch/                       # manual inspection of interrupted work
```

**Migration note:** `.migration/` contains the earlier migration bootstrap and the original v2.98 additive patch, preserved unchanged so it isn't lost. Its patch was written against the old v2.97 layout and **must NOT be applied blindly to this rebuilt v3 code**. The importer can import a separate local legacy clone, but that would require a planned conflict review; it is not a prerequisite for using reconstructed v3.

### v3.7 — Cross-process original audio, portrait and source-binding protection

**The private `BIND` action, offline Kokoro voice generator, explicitly
consented online Edge TTS, and dashboard WAV/portrait imports now share
a real **cross-process exclusive file lock** in the private workspace:
`source/originals-voice-and-binding-exclusive.lock`. This prevents a
separate Windows terminal or browser import from changing originals during
a slow voice generation/source SHA-binding operation. Any existing unknown
or interrupted lock blocks the next write; the app never silently deletes
a different process's lock. `READINESS` reports active/stale locks as
BLOCKED, rather than treating partially written audio as valid.

Workspaces are deliberately **refused inside any Git working tree** (including
linked worktrees using a `.git` file), to reduce the risk that private
portrait images, Hindi WAVs, model results or troubleshooting logs could
accidentally be published with a broad Git add/push command. Keep the
default `%USERPROFILE%\\PodcastGPTStudio` or another directory **outside**
the public project clone. Dashboard imports remain allowed *before* INIT,
but do not bind or generate a project automatically; they lazily create
only the private lock folder as needed.

After interruption, investigate whether any Python/Kokoro/Edge/model
process is still running and whether a WAV/receipt was partially written.
Do **not** force-remove the lock while a process is active, and do not
overwrite existing original media. See [v3.7 release notes](docs/V37_RELEASE_NOTES.md).

### v3.6 — READINESS: verified, read-only local remaining-work planner

Choose **`READINESS`** in `CONTINUE_FULL_HINDI_NEURAL.bat`, click
**READINESS** on the private localhost dashboard, or run:

```powershell
python -m podcast_gpt --workspace "$HOME\PodcastGPTStudio" readiness
```

This runs **no TTS/AI inference, downloads or video encoding** and does not
alter the workspace. It verifies actual script/portrait/WAV source structure,
checks the 540–660s production audio gate, re-hashes the signed original
source and exact PCM chunks, and—where present—independently decodes static
and complete candidate MP4s, verifies original facial preview SHAs and
checks private presenter PASS/FAIL records. It explicitly marks any missing,
partial or tampered stage and suggests **one next safe action**. On a fully
rendered episode the final action still requires human 45-turn review;
readiness NEVER certifies natural Hindi lip sync, likeness rights or
publication approval. Deep decode can take several minutes on CPU and
the diagnostic stays on the owner's device.

See [v3.6 release notes](docs/V36_RELEASE_NOTES.md).

### v3.5 — Online Edge Hindi TTS source integrity (optional, explicit network)

Choosing `tts-one --allow-network-tts` is an **opt-in online** action: the
selected Hindi script text is sent to the external Edge TTS service. Without
the explicit flag the provider is not contacted. This route now checks
that the original 45-turn source has **not** already been SHA-bound, refuses
any existing WAV or same-turn receipt, converts its returned speech using
the private workspace `scratch/` drive (not Windows C: TEMP), and re-verifies
the unchanged script/source state after network synthesis before opening
the destination with exclusive `xb` creation. The original audio SHA,
provider voice preset, request speech rate and project SHA are saved in a
private `.edge-tts-source.json` receipt; there is no automatic human voice
quality approval. Simulated-provider FFmpeg tests verify this without
actually connecting to Microsoft or generating neural voices.

Use optional **offline Kokoro** instead if you do not wish to send your
script text to the network; natural quality and 10-minute duration on your
CPU remain unverified. See [v3.5 release notes](docs/V35_RELEASE_NOTES.md).

### v3.4 — External SadTalker subprocess + private failure troubleshooting

CI now launches a **separate Python subprocess** with the same CPU CLI
arguments and timestamp-named MP4 layout documented in upstream SadTalker.
The external program is deliberately a **fake test runner** that makes
short static FFmpeg video; this validates actual subprocess/MP4 discovery,
three-speaker pilot checkpointing, reuse-on-resume and incomplete-output
refusal on Windows and Ubuntu. It does NOT download, run or certify the
real SadTalker neural model or natural Hindi lip motion.

When an authorized real model subprocess fails, its complete stdout/stderr
are preserved in the **private workspace** at `scratch/model-<chunk>/model-stdout.log`
and `model-stderr.log` for local troubleshooting. The app no longer buffers
unbounded subprocess output in RAM. Successful chunks remove their own
temporary logs with scratch cleanup. Do **not** upload private logs, portraits
or original recordings to the public repository.

Local Kokoro-to-16k original WAV conversion also uses the private workspace
`scratch/` directory (with 100 MiB minimum free) rather than the Windows
system temporary drive. SadTalker Python's read-only version preflight uses
`-I -S` to avoid normal site/user initialization; this does not authenticate
the third-party Python interpreter. [v3.4 release notes](docs/V34_RELEASE_NOTES.md).

### v3.3.1 — Private dashboard import safety

Portrait uploads in the localhost dashboard require an explicit self-attested
owner/written-permission checkbox, verified again server-side, before storing
a PNG. This is not independent rights or identity verification. Media uploads
take the same exclusive lock as source binding and rendering tasks, so no
background action can start while a WAV or portrait is only partially saved.
The original WAV filename validator accepts exactly `001.wav`–`045.wav`, not
`000.wav`. Originals remain no-overwrite, local-only and protected by CSRF.
Loopback HTTP regression tests cover failed rights acknowledgment, forbidden
filename, existing-file refusal and upload/action concurrency.

### v3.3 — Read-only model preflight and source-bound video sync

Choose **`MODEL`** in `CONTINUE_FULL_HINDI_NEURAL.bat` or run
`CHECK_SADTALKER_CPU.bat` before an expensive genuine SadTalker CPU `PILOT`.
This verifies the existing local script's expected CLI flags, source config,
nonempty checkpoint files, and selected Python interpreter version without
loading third-party weights or performing any AI inference. It does NOT prove
that the model can load, that portrait usage is authorized, or that lips are natural.

**Audio/video correction:** 24fps final-video frames are allocated by
rounding the cumulative original Hindi PCM and pause timeline rather than
independently rounding every short face/pause segment. The app also rejects
face MP4s with insufficient actual video stream duration, even when AAC or
container duration appears long enough. See [v3.3 release notes](docs/V33_RELEASE_NOTES.md).

### Read-only real CPU pace budget (`BUDGET` stage)

Once at least one genuine source/FFmpeg-verified SadTalker CPU sample exists,
choose `BUDGET` in the Windows guide or run `python -m podcast_gpt
--workspace "<PRIVATE_STUDIO>" budget`. It rechecks signed original PCM,
authorized portrait SHAs, and ALL saved MP4s; then uses saved local
`actual_cpu_model_seconds` to illustrate remaining model CPU hours.
It does **not** start a model, encode video, download anything or claim that
its broad 0.5x–3x range is a reliable clock-time promise. Unmeasured speakers
borrow the global median and are explicitly identified; with zero genuine
measured clips it returns **no estimate**, never an invented figure.
This reflects previous v2.92 planning intent and is a newly reconstructed implementation.

## Quality, trust and limitations

- **Not the same Git history or exact source as the old repo.** Previous version labels in conversation history describe design decisions, not recoverable file contents. The new repo is a clean-room functional implementation with its own storage format; it does not claim backward-compatible access to historical private workspaces.
- **No free pretrained models included.** SadTalker weights may have storage, license, RAM and CPU requirements. Always review all third-party licenses and model sources yourself.
- **CPU-only is not instant.** At 720p, 45+ dialogue segments, a 10-minute composition and dozens of real model calls can take a long time on a Windows laptop without GPU. The requested 7,200s wall budget governs launching additional model calls, not a strict total system shutdown.
- **Offline vs online:** source import, static rendering and optional locally installed SadTalker are local; Edge TTS and installing pip dependencies need a network connection.
- **No AI identity verification:** correctness and permissions are the owner's responsibility; saved HUMAN `PASS` is a private opinion only. Do not deceive people into thinking an AI-generated likeness is a real person's uncensored speech.
- **App routes never automatically publish.** It has no YouTube upload, automated social posting, paid API, scraping, or remote upload service. Those are **not rebuilt from the available project history**.

## Tests and independently reproducible smoke

```powershell
python -m pip install -e ".[test]"
python -m pytest -q tests
```

GitHub Actions exercises synthetic source WAV/portrait integrity and Windows/Linux combinations. Local FFmpeg synthetic smoke is separate from the external real model test. See [reconstruction ledger](docs/RECONSTRUCTION_LEDGER.md), [Windows setup](docs/SETUP_WINDOWS.md), [architecture](docs/ARCHITECTURE.md) and [remaining acceptance](docs/REMAINING.md).
### Guided local model setup and pilot gate

For the separate SadTalker legacy CPU environment, see [guided Windows CPU installation](docs/SADTALKER_CPU_SETUP.md). BATCH and SESSION require a current all-three manual PASS record bound to verified pilot clips before any further inference. The app does not download or authenticate third-party weights, certify quality, or publish.

### Windows source-only ZIP candidate

After all required CI jobs pass, the Windows packaging job builds and verifies a source-only ZIP, smoke-tests clean app setup and uploads the candidate and SHA256 to the successful Actions run. See [release candidate instructions](docs/RELEASE_CANDIDATE.md). Real model weights, private media and migration archives are excluded; this is not real model acceptance.

### V4 Smart setup (development milestone 1)

Stable V3 remains on [stable-v3.7](https://github.com/mohdazizshaikh/podcast/tree/stable-v3.7). Run SMART_SETUP_WINDOWS.bat after installing the application with START_PODCAST_WINDOWS.bat --setup-only, or use python -m podcast_gpt setup-wizard. The dashboard offers a read-only hardware/package inventory. Local model selection and explicit trusted interpreter probing are CLI only. No model installs or downloads occur. See [V4 roadmap](docs/V4_ROADMAP.md).

### V4 free AI planning

The first generalized planning increment supports topic-based outlines for 1–10 presenters and 1–60 target minutes. See [confirmed requirements](docs/V4_REQUIREMENTS.md) and [free AI provider setup](docs/AI_PROVIDERS.md). Cloud text is opt-in, Gemini requires a confirmed unbilled Free Tier project, and Ollama is limited to known installed under-3B models. No general V4 media rendering or research claim yet.

V4 private project storage and Windows encrypted default/project API keys: see [V4 project guide](docs/V4_PROJECTS.md). CLI creates and plans projects; dashboard lists them. Existing V3 media pipeline remains separate.

V4 bounded URL/PDF/DOCX/text/custom-script source ingestion: [guide](docs/V4_INGESTION.md). See [current project tracking](docs/V4_TRACKER.md) for code, CI and real-world acceptance status.

V4 full dialogue drafting (1–60 planned minutes, 1–10 speakers), resumable checkpoints and final script JSON: [script generation guide](docs/V4_SCRIPT_GENERATION.md). See [master tracker](docs/V4_TRACKER.md) for latest verified status. No V4 media rendering or actual duration certification yet.

V4 source-grounded research: explicit 2–4 public HTTPS pages and source-bound exact excerpt citations. [Research guide](docs/V4_RESEARCH.md); no automatic discovery or independent fact-checking yet.
