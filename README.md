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

V4 manual script editing, immutable revisions and per-version human approval: [review guide](docs/V4_SCRIPT_REVIEW.md). No generalized media production until subsequent implementation and acceptance.

V4 reusable local characters, authorized PNG portraits, voice identity preferences and cast assignment: [character guide](docs/V4_CHARACTERS.md). The media preflight binds current reviewed text and portrait hashes; actual image/voice generation and generalized rendering remain pending.

V4 authorized speech import, per-turn PCM receipts and measured audio timeline: [audio guide](docs/V4_AUDIO.md). Generalized TTS and video rendering remain pending.

V4 local Hindi Kokoro adapter and exact PCM master WAV composition/audit: [TTS and master audio guide](docs/V4_TTS_MASTER.md). Actual local model acceptance, broader TTS languages and video remain pending.

V4 human listening review, selected three-format static preview and measured SRT: [preview guide](docs/V4_PREVIEW.md). Static previews are explicitly not lip-sync; real generalized neural media remains pending.

V4 source-bound local SadTalker CPU pilot, resumable clips and human pilot batch gate: [neural guide](docs/V4_NEURAL.md). Full neural episode composition and physical Windows model acceptance remain pending.

V4 selected-format neural candidate composition and structural audit: [export guide](docs/V4_EXPORT.md). Requires complete reviewed source-bound facial clips, preserves original master as sole audio input, and emits synchronized SRT. Genuine model and full human QA remain pending.

V4 full episode review, stopped neural scratch archive and selected-project readiness: [acceptance and recovery guide](docs/V4_ACCEPTANCE.md). The local dashboard exposes a read-only readiness action; real Windows model acceptance remains pending.

V4 saved local model paths, optional eSpeak non-neural multilingual fallback and opt-in character-aware dialogue: [combined guide](docs/V4_MODEL_VOICES_PERSONA.md). No automatic installation or real model quality certification.

V4 optional dependency setup, offline visual script editor and bounded foreground production runner: [workflow guide](docs/V4_WORKFLOW.md). Actual model acceptance and complete one-click production remain pending.

V4 configured media orchestration, private timing history and visual media QA: [media workflow guide](docs/V4_MEDIA_WORKFLOW.md). No live ETA or automatic approval.

V4 optional audio-only normalization/music/intro/outro mix and safe incomplete-output recovery: [post-production guide](docs/V4_POST_AUDIO_RECOVERY.md). Original speech master remains unchanged; mixed-video export pending.

V4 optional mixed audio/video candidate with static intro/outro, shifted subtitles, fresh review gates and incomplete-output recovery: [mixed video guide](docs/V4_MIXED_VIDEO.md). Actual model acceptance pending.

V4 expanded local Kokoro language presets, opt-in Wikipedia candidate discovery and source-bound factual review: [language and research guide](docs/V4_LANGUAGE_RESEARCH.md). Actual voice and independent fact verification remain pending.

V4 English voice frontend, portrait preparation briefs and static background/focus/grid studio preview: [studio and English guide](docs/V4_STUDIO_ENGLISH.md). Real image generation and animated neural studio remain pending.

V4 separate neural studio composition, fresh full review, studio recovery and portrait attachment: [neural studio guide](docs/V4_NEURAL_STUDIO.md). Active speaker animated clip; other presenters static. Actual local model acceptance pending.

V4 dashboard overview, historical neural-stage estimate and verified local playback: [production overview guide](docs/V4_PRODUCTION_OVERVIEW.md). No media HTTP endpoint, live ETA or automatic publication.

V4 dashboard project creation, bounded local non-inference controls and mixed neural studio: [workflow guide](docs/V4_DASHBOARD_MIXED_STUDIO.md). Actual browser and model acceptance pending.

V4 browser character and cast management, private source imports and saved local model paths: [graphical authoring guide](docs/V4_DASHBOARD_AUTHORING.md). Real browser and model acceptance pending.

V4 explicit browser local inference, research pack management and measured task status: [dashboard inference guide](docs/V4_DASHBOARD_INFERENCE.md). Cloud AI and approval recording remain CLI-only; actual device acceptance pending.

V4 browser review/revision imports, cooperative checkpoint stop and structured verbatim script: [review and custom script guide](docs/V4_REVIEW_STOP_MANUAL.md). Actual browser/model acceptance pending.

V4 optional speech-driven music ducking, read-only LUFS/true-peak diagnostics, guided local model setup and provider refusal hardening: [audio quality and setup guide](docs/V4_AUDIO_QUALITY_SETUP.md). Actual model acceptance and target normalization pending.

V4 measured loudness-target static gain, per-turn audio diagnostics and explicit local cross-episode continuity: [normalization and continuity guide](docs/V4_NORMALIZATION_CONTINUITY.md). Real model/device acceptance and dynamic limiting remain pending.

V4 expanded dashboard WAV/studio/continuity authoring, explicitly consented free-policy cloud drafting, Mandarin frontend and broad test matrix: [batch 29 guide](docs/V4_BATCH29.md). Real browser/model acceptance pending.

V4 optional speech compression: [batch 30 guide](docs/V4_BATCH30.md). Actual model/device acceptance pending.

Batch 30 adds CLI/browser voice preflight and read-only device checklist, plus browser per-turn audio diagnostics. New CI pending. Real model inference, physical acceptance and browser interaction remain pending. See V4_BATCH30.md.

Batch 30 also implements graphical local mix composition with bounded WAV inputs, compression, ducking and optional static loudness target. Total 157 authored regression cases across the three commits; CI pending. Actual browser and Windows/model acceptance remain open. See V4_BATCH30.md.

Batch 29 and 30 CI completed successfully (45494573255, 45495891248 latest combined: 6/6 each). Batch 31 adds explicitly consented local CPU portrait candidate generation with safetensors inventory and immutable candidate receipt; new CI pending. Real model setup, physical acceptance and portrait quality remain unverified. See docs/V4_BATCH31.md (repository-relative).

Batch 31 adds 17 allowlisted Wikipedia discovery editions, exact citation coverage and browser portrait brief/coverage controls. New CI pending; broad web search, semantic verification and independent corroboration remain pending. See V4_BATCH31.md.

Batch 31 adds optional deterministic per-dialogue DC correction and low-level soft gate, CLI/browser settings and exact mix audit; new CI pending. AI/spectral denoising, dynamic true-peak limiting and real listening acceptance remain pending. See V4_BATCH31.md.

Batch 31 combined CI 45498392552 passed 6/6. Batch 32 adds guarded Japanese neural frontend/resource status, graphical isolated local portrait worker and candidate audit/attachment. Actual Japanese dictionary/model inference and real browser/device acceptance remain pending; new CI pending. See V4_BATCH32.md.

Batch 32 also adds bounded portrait attempt listing, candidate provenance validation and CLI candidate audit/attachment. 68 new regression cases authored across the two commits, not 68 independent features. New CI pending; real model and browser acceptance remain open. See V4_BATCH32.md.

Batch 32 combined CI 45500231172 passed 6/6. Batch 33 implements optional active-speaker digital push-in, local hash-verified portrait preview and stale asynchronous selection guards. 53 new regression cases authored, CI pending. Actual model/browser acceptance, advanced transitions and listener animation remain pending. See V4_BATCH33.md.

Batch 33 adds read-only decoded AAC/source audio comparison, timing and similarity diagnostics; CI pending. 63 new regression cases authored across two commits. Real browser/model acceptance and semantic audio review remain pending. See V4_BATCH33.md.

Batch 34 extends existing read-only research coverage with exact cross-source excerpt reuse, single-host turn and unused-source review signals; decoded AAC diagnostics now flag missing variable audio, DC offset changes and uncorrelatable mismatch, report unique flagged windows and uncompared frames. 68 new synthetic regression cases authored (not independent features). Batch 33 CI could not be confirmed through the available commit-status endpoints; Batch 34 CI pending. Actual model/browser/device acceptance and semantic corroboration remain open. See V4_BATCH34.md.

Batch 35 implements optional deterministic whole-mix dynamic sample-peak limiting, including intro/bed/outro, immutable exact PCM audit, CLI/browser setting and legacy defaults. 63 new regression cases authored; 58 standalone limiter cases passed in an isolated local Python harness, five repository integration cases and full CI unverified. Sample peaks are not intersample true peaks; dynamic true-peak limiting, combined LUFS normalization, real listening and physical Windows/model acceptance remain pending. See V4_BATCH35.md.

Batch 36 permits an optional dynamic sample limiter followed by bounded static loudness gain. The gain is capped by the selected sample ceiling, the candidate must pass the measured true-peak ceiling, and the immutable receipt binds the limiter and normalization settings. Legacy no-limiter receipts retain their format. 62 new unit regression cases authored, plus a revised project/dashboard integration case; full Python test execution and real device/listening acceptance remain unverified. This is not dynamic intersample true-peak limiting or guaranteed LUFS attainment. See V4_BATCH36.md.

Batch 37 implements explicit online Edge V4 speech adapter with static locale/preset validation, 1–5 bounded approved turns, private temporary MP3/PCM conversion, immutable source-bound receipts, resume, duplicate rejection and CLI/readiness/preflight integration. 81 new regression cases authored (71 pure locale/receipt cases and 10 adapter/CLI cases); tests not yet independently run. No automatic network fallback, service/voice inventory guarantee, browser Edge action or real voice/device acceptance. See V4_BATCH37.md.

Batch 38 adds read-only Edge pending-turn planning, separate bounded consented online voice inventory with filtering and deduplication, optional dependency setup, browser generation/inventory/preview, turn-bound progress and cooperative stop, and local-only continuity protection. 63 new test cases authored; full repository CI and real browser/service/device acceptance unverified. See V4_BATCH38.md.

Batch 39 adds a spotlight studio layout for 1–10 presenters in landscape, vertical and square, plus four opt-in active-speaker camera modes (pull-out, smooth push-in, pan left/right) alongside existing fixed and push-in. Settings, CLI and dashboard support; static preview uses layout only, neural composition inherits bounded camera filters. 71 authored tests, 65 isolated local tests passed including six real FFmpeg filter/frame-count renders; six full-project integration tests and repository CI pending. Listeners remain static, camera resets at clip boundaries, and real browser/model/Windows acceptance remains open. See V4_BATCH39.md.

Batch 40 adds optional deterministic dialogue-only fixed-point high-pass (60/80/100/120 Hz), narrow mains hum notch (50/60 Hz), and low-pass (4500/6000 Hz) filters before peak normalization; CLI/dashboard, exact recipe audit and disabled legacy defaults. 71 authored regression cases; 66 standalone cases passed locally (including synthetic frequency response); five integration cases and full repository CI unverified. These are targeted filters, not intelligent broadband denoising, and may affect voice tone. Human listening and physical model acceptance remain mandatory. See V4_BATCH40.md.

Batch 41 adds an optional conservative whole-mix dynamic PCM peak guard (three-sample lookahead/history, 22000 PCM cap, 50 ms release) with mandatory measured -1.5 dBTP check before committing and repeated check during audit. Supports sample limiter and bounded LUFS gain using the stricter sample ceiling; legacy defaults unchanged. 71 new tests authored, 64 standalone tests actually passed including six FFmpeg signal tests; initial three high-frequency cases exceeded ceiling, so explicit rejection is tested. Seven full-project cases and full CI unverified. This is not a standards-certified oversampled true-peak limiter, and may reject a candidate instead of automatically correcting it. See V4_BATCH41.md.

Batch 42 adds optional bounded measured static true-peak correction after the dynamic guard, up to three attenuation retries from the same PCM baseline, at most approximately 12 dB total attenuation, mandatory final measurement, exact PCM replay and baseline hash, and precommit frame/hash checks. CLI/dashboard, legacy defaults unchanged. Requires guard and no LUFS target (separate modes). 84 tests authored; 79 standalone tests executed successfully, including four actual FFmpeg tones. Five project integration cases and full CI pending. Not a standards-certified oversampled dynamic limiter. See V4_BATCH42.md.

Batch 43 adds combined bounded LUFS targeting and automatic measured peak correction with an explicit guard: a new normalization recipe computes each retry from the same unnormalized guarded PCM, with up to three attenuation retries, stricter sample cap, exact baseline/PCM replay, final full measurement audit and honest target attainment reporting. Legacy independent modes and receipts remain supported. 96 tests authored, 92 isolated cases passed (including four real FFmpeg tone tests using equivalent existing gain helpers); four repository integration cases and full CI unverified. Actual speech listening and physical Windows/model acceptance pending. See V4_BATCH43.md.

Batch 44 adds optional adaptive quiet-region dialogue attenuation (off/light/medium/strong), using per-turn 20 ms energy windows, conservative 20th-percentile quiet-floor estimation, contrast and floor bounds, 5 ms gain transitions, and exact integer PCM processing before speech peak normalization. CLI/dashboard, recipe replay and disabled legacy defaults. 97 cases authored; 91 isolated tests passed locally (0.83 s); six project/CLI/dashboard cases and full CI pending. This is adaptive level-based broadband attenuation, not spectral denoising, voice activity recognition or AI speech isolation; quiet speech may be reduced and subsequent normalization can amplify remaining noise. Real listening and physical model acceptance pending. See V4_BATCH44.md.

Batch 45 adds opt-in stationary-noise spectral subtraction with a fixed-point 128-point FFT, 64-sample overlap, frozen Q15 coefficients, per-turn quiet-profile estimation (at most 64 analysis frames), contrast-based bypass, bounded frequency-bin attenuation and normalized overlap-add reconstruction. CLI/dashboard, exact recipe replay, unchanged disabled defaults. 95 authored cases; actual isolated pytest run 89/89 passed in 2.09 s, six integrations pending. A 10-second synthetic input took 1.42 s for a single pass in this environment. Stationary noise suppression can also attenuate speech components; not AI speech isolation or validated real speech enhancement. Full CI, real listening and Windows performance remain pending. See V4_BATCH45.md.

Batch 46 adds two opt-in episode-clock active-speaker camera modes, continuous-drift and continuous-breathe, with an eight-second periodic phase and exact cumulative speech/pause offsets. Existing six modes retain their behavior. Static listeners and pause cards remain still; speaker/layout changes remain hard cuts, and mixed studio inherits motion from its audited base. 96 new authored cases, 92 standalone tests actually passed in 2.44 s, including 10 real FFmpeg tests (8 split/whole byte comparisons and 2 motion checks). Four integration cases and full CI remain unverified. See V4_BATCH46.md.

Batch 47 adds optional simulated listener portrait framing (static/drift/breathe) for grid and spotlight neural studios, with staggered global camera phase, interior-only crops and unchanged active speaker, static pauses, settings digest and honest receipt metadata. Static preview unchanged; mixed studio inherits the audited base. 90 new test cases authored, 85 passed locally, plus 92/92 Batch 46 camera tests rerun (177 total passed in 3.05 s); five new integration cases unexecuted, full CI unverified. Small portraits may show little visible motion due to pixel rounding. Not neural facial animation or reaction inference. See V4_BATCH47.md.

Batch 48 adds opt-in quick/gentle pause-only speaker handoff crossfades (up to 6/12 existing pause frames), skips same-speaker or under-three-frame pauses, preserves original timeline and speech segments, adds CLI/dashboard/background-upload controls and immutable transition binding plus scheduled handoff count. Mixed studio reuses audited base. 101 new authored cases: 96 isolated tests actually passed in 0.77 s, including 8 actual FFmpeg renders; five integration cases unexecuted, full CI and real Windows/model acceptance pending. Not a crossfade of moving neural speech clips; transitions blend still pause cards. See V4_BATCH48.md.

Batch 49 adds match-quick and match-gentle pause handoffs using the last decoded frame of the outgoing rendered speech segment and first decoded frame of the incoming segment. Defers matched pauses until both speech segments are rendered and checked, then concatenates in original chronological order. Holds/blends frozen endpoints (including existing labels), not moving facial clips; no audio/subtitle changes, no added frames, old modes unchanged. 86 dedicated cases authored; 84 standalone tests actually passed (0.79 s), including nine FFmpeg raw-video endpoint tests; two compositor integration cases unexecuted. Full CI, actual model/hardware visual review pending. See V4_BATCH49.md.

Batch 50 adds neural studio dashboard verified-segment/frame progress, provisional remaining-segment ETA and cooperative precommit cancellation; distinguishes mux verification, input revalidation/commit and final audit, including deferred endpoint rendering and existing candidate audit. Scratch output discarded on precommit stop; no force-killing FFmpeg or cancellation during immutable save. 74 new authored cases; 69 isolated tests passed and 84 Batch 49 standalone cases reran, 153 total in 0.80 s. Five new integration cases unexecuted; repository DNS blocked. Existing .github/workflows/tests.yml verified present (Windows/Linux matrix, FFmpeg and clean source ZIP); current CI result unavailable. See V4_BATCH50.md.

Batch 51 extends verified render progress and cooperative precommit stopping to mixed video/studio composition; validated nonempty intro/speech/outro scene counts, separate mixed stage labels, no unreliable scene ETA, preserved mix listening PASS and source-binding audits. 78 dedicated new cases authored; 69 standalone passed plus 69 previous progress tests rerun (138 passed in 0.13 s). Nine mocked full-repo integration cases authored but unexecuted. Full CI, real model, full episode and physical Windows acceptance remain unverified. See V4_BATCH51.md.

Batch 52 adds explicit neural studio compose/resume with a private, input/plan/renderer-bound verified segment cache, SHA-256 and decoded frame checks, atomic staging, dependency hashes for matched pause endpoints, safe path checks, and stop-compatible cache retention. Existing compose remains ephemeral; resumable ETA intentionally disabled. 80 dedicated tests authored; 73 standalone passed in 1.34 s including three actual FFmpeg/ffprobe cache restores. Seven integration cases unexecuted; full CI and Windows/model acceptance pending. Cache persists even after success; manual cleanup only, not approved output or authenticated storage. See V4_BATCH52.md.

Batch 53 adds explicit private studio-cache inventory and single-namespace cleanup with metadata snapshots, exact namespace selection, project locking and dual dashboard consent. Reports logical bytes, entry/pair counts and latest file mtime; does not verify content or classify obsolete caches. Rejects unsafe paths, unknown names, changed snapshots and unbounded trees; no automatic pruning. 64 new cases authored; 61 standalone actually passed in 0.45 s, three repository integration cases unexecuted. No user cache was deleted. See V4_BATCH53.md.

Batch 54 adds explicit mixed-video and mixed-studio resume, partitioning existing intro/speech/outro into at most 1,500-frame (60-second) chunks. Reuses the private verified cache and admin controls; namespace binds mix/base receipts and renderer. Uses normalized frame-index trim, not approximate seek; repeated prefix decoding may be slower, and chunks can still exceed the cache byte limit. Ordinary compose unchanged. 80 new cases authored; 72 standalone actually passed in 1.95 s including six real FFmpeg raw-frame comparisons, eight full-repo integration cases unexecuted. See V4_BATCH54.md.

Batch 55 repairs five audio CLI regression tests that omitted required acknowledgment and closes a combined gain precommit verification gap: repeat measurement must match all four recorded fields before immutable output is created, not merely true peak. Four additional integration regressions authored, unexecuted. Earlier 428 isolated Batches 49–54 cases reran successfully in 3.93 s (transition, render progress, cache and mixed chunk modules); full CI not verified. See V4_BATCH55.md.

Batch 56 adds explicit budget-based multi-namespace cache cleanup preview/apply with oldest-modification-time ordering, newest-N and named protections, exact plan digest and whole-inventory binding, and project locking/dual dashboard consent. Protected caches can prevent budget attainment; no background pruning or automatic deletion. 72 cases authored; 68 new local filesystem cases passed (0.44 s) after fixing keep-count > inventory boundary, four repository route/lock cases unexecuted. No user cache deleted. See V4_BATCH56.md.

Batch 57 adds private bounded performance history for newly completed audited non-fixture neural studio, mixed video and mixed studio renders, separating rendered/restored frame counts and measured unit processing durations, with grouped totals and read-only CLI/dashboard inspection. Last 30 records per project, no network or dialogue storage; history errors logged without invalidating audited media. 48 dedicated tests authored; 46 standalone passed in 0.17 s, two repository route/lock tests unexecuted. Actual model/render performance and full CI remain unverified. Renderer source changes invalidate prior resume cache namespace selection; old cache remains available for explicit cleanup. See V4_BATCH57.md.

Batch 58 fixes a reproduced encoded-MP4 matched-endpoint transition defect: on local FFmpeg 7.1.5 a 13-frame pause produced 13 packets but only 12 decoded frames (last marked discard, duration 0.48 s rather than 0.52 s). Explicit 25 fps normalization of frozen endpoint streams fixes this. Six new actual synthetic compositor/stop/resume/concat regressions cover all aspect ratios, three layouts, 1/3/10 presenters, listener framing, camera and transitions. Initial run 3/6 passed; all six passed after fix, plus 84 existing standalone endpoint cases (90 passed in 26.16 s). Local partial-source harness uses exact copied renderer functions and helper modules; synthetic portraits, no genuine neural generation or whole-project checkout. Full CI and Windows acceptance pending. Transition source hash changes cache renderer identity, so older namespaces are retained but bypassed. See V4_BATCH58.md.

Batch 59 fixes a reproduced mixed resume encoded-frame loss: six of six synthetic encoded media tests failed on the first seven-frame chunk (six decoded frames). Explicit fps=25 after trim and timestamp reset corrected all six. Actual test path encodes, caches/restores each chunk, muxes synthetic PCM into AAC, performs real mixed decode/receipt/subtitle audit and rejects subtitle tampering. All six passed in 17.02 s and 72 earlier standalone chunk cases passed in 1.98 s. Test harness uses copied production helper functions and encoder argument sequences, not the complete compose/context/approval orchestration. Mixed cache identity changes; older cache files are not deleted. Full CI and real Windows/model acceptance remain unverified. See V4_BATCH59.md.

Batch 60 adds six real synthetic mixed compose-entry regression cases with actual encoding, AAC mux, receipt audit, project-exclusive lock, two stop/resume variants, post-mux and precommit cancellation, changed context rejection and ordinary composition. Successful cases verify 25 decoded frames, exact one-second video duration, shifted SRT, cache hash reuse, fixture history exclusion and immutable existing-candidate re-audit. Final local partial-harness run 84 passed in 29.87 s (six new compose cases plus previous 78 mixed chunk cases); compose/inspect/renderer identity excerpts match committed source by length and deterministic checksum. Upstream project lookup and source/approval context mocked; seven-frame test chunks selected for short fixtures. No production renderer changes or cache invalidation this batch. Full CI, physical Windows and genuine model acceptance still pending. See V4_BATCH60.md.

Batch 61 adds six actual synthetic neural studio compose/inspect regressions using real frame_plan, compositor, FFmpeg H.264/AAC mux, project lock, cache restore, precommit cancellation, changed-context rejection, original PCM/clip hashes, final receipt, existing-candidate re-audit and subtitle tamper rejection. Successful cases verify 34 decoded frames/1.36 seconds, exact sample-derived SRT intervals, no fixture timing history or human/publication approval. Six new cases passed in 24.83 s; 84 prior endpoint cases passed in 0.66 s (90 total across two local runs). Partial-source harness with copied production functions, synthetic portraits/clips and mocked project lookup, portrait loader and upstream approval context. No renderer change or cache invalidation. Full CI, genuine models, Windows acceptance remain unverified. See V4_BATCH61.md.

Batch 62 hardens pilot and mixed review validation against boolean/float schema aliases, empty or duplicate review targets, vacuous PASS, and nonboolean fixture-export override. Exact review hash/consent/current-candidate gates remain. 87 new targeted cases passed in 0.17 s on a partial-source harness exercising actual pilot/mixed review readers, neural export and mixed context functions with lower-level clip scans, source context and media audits substituted. Additional strict schema checks in neural clip scan and pilot record entry point are not directly exercised. No complete approval-chain or full CI claim. Mixed renderer source hash changes its cache namespace; existing cache files retained. See V4_BATCH62.md.
