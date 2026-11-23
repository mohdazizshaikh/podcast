# Podcast GPT — Reconstructed Hindi Three-Presenter Studio (v3.2)

> **Rebuilt from this ChatGPT Project's available requirements/milestone history, NOT cloned from or verified against the suspended repository.** New canonical repository: **https://github.com/mohdazizshaikh/podcast**. No access to the suspended account is required. The original v2.97 Git history and exact source-byte parity **cannot be claimed** from chat summaries alone. See [`docs/RECONSTRUCTION_LEDGER.md`](docs/RECONSTRUCTION_LEDGER.md).

### One click on Windows without a dedicated GPU

1. Install **Python 3.11** (recommended) and **FFmpeg + ffprobe** on PATH (free). One official installation route for FFmpeg is `winget install Gyan.FFmpeg`. Install Git if cloning.
2. `git clone https://github.com/mohdazizshaikh/podcast.git` then open the `podcast` directory.
3. Double-click **`START_PODCAST_WINDOWS.bat`**. The launcher creates `.venv`, installs this app's free Python packages, opens `http://127.0.0.1:7860`, and uses a private default workspace: `%USERPROFILE%\PodcastGPTStudio` (unless `PODCAST_WORKSPACE` is set). Internet is needed on the first `pip install`; **AI models are NOT silently downloaded**.
4. Initialize the reconstructed 45-turn Hindi script, inspect/edit `project.json`, and provide **three authorized human portrait PNGs** (`portraits/aarav.png`, `meera.png`, `kabir.png`, each >=200px). Provide original, authorized `voices/001.wav` ... `045.wav`: 16,000 Hz, single-channel, signed 16-bit PCM, WAV. Both original and imported voices are accepted; real audio is never preloaded in Git.
5. **New optional fully LOCAL Hindi Kokoro ONNX three-voice path:** Download/install licensed Kokoro model and voice pack yourself (no automatic weight downloads), install `kokoro-onnx`, `misaki`, and eSpeak-ng, then run `GENERATE_KOKORO_HINDI_CPU.bat` for up to 1–5 NEW original voice WAVs per explicit invocation. It maps Aarav to `hm_omega`, Meera to `hf_alpha`, Kabir to `hm_psi`; they are distinct voice PRESETS, not a guarantee of distinct personalities or natural quality. All original WAVs convert to 16kHz mono PCM and remain private. See [Kokoro offline Hindi](docs/KOKORO_OFFLINE.md).
6. If you choose optional **online Edge Hindi TTS**, use the `tts-one --allow-network-tts` CLI. It sends the selected script text to an external voice service; it is **NOT** fully offline. Included voice presets use two available Hindi identifiers with a slightly adjusted speaking rate for Kabir; **three genuinely distinct neural voices are NOT guaranteed**. To meet that requirement, import three separately authorized real/locally generated voice recordings from your preferred offline engine.
7. After all 45 WAVs and 3 portraits exist, click **Bind original sources**. The program independently checks the ~10-minute duration (540–660 seconds), PNG validity, exact voice PCM and source hashes. Then **Export 1–10-second exact PCM chunks** and **Render original 720p static video + real AAC + SRT** (CPU only). This is a REAL media video but **NOT moving lips**.
8. For optional **real facial animation** install and obtain model weights for external SadTalker yourself, subject to its third-party licenses. Choose `PILOT` for one source-bound real speaking-face segment each from Aarav, Meera, Kabir. The CPU launcher asks explicit image-rights `YES`. A single finite call can run for a long time and uses up to 6 GiB free disk preflight. It is **not** a guaranteed free/fast fully offline 10-minute face renderer.
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

All media, portraits, scripts, WAVs, SadTalker model assets, runtime outputs and review notes should live outside this PUBLIC Git repo; `.gitignore` blocks common media/model/secrets but **always manually inspect `git status` before pushing**. The dashboard binds to loopback only, has per-instance CSRF protection and does not serve your media over HTTP. No YouTube/publishing tokens or automatic posting are part of the current software.

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