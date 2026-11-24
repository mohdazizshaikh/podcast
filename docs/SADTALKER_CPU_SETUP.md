# Guided SadTalker CPU installation (Windows, separate legacy environment)

This is a local, manually authorized third-party setup. The Podcast launcher installs only its own app; it never auto-downloads or runs untrusted model weights. The recipe below is based on upstream installation documentation and the official PyTorch historical CPU wheel instructions, not a tested fresh Windows installation.

## 1. Keep environments separate

- Install Git, FFmpeg/FFprobe, and the current Podcast app as in SETUP_WINDOWS.md.
- The upstream SadTalker legacy recipe uses Python 3.8. Python 3.8 is end-of-life; isolate this environment, do not use it for general browsing or public web serving, and review its dependency risks.
- Use a separate local model directory outside the public podcast repository and outside the private episode folder. Download only from verified upstream sources. Review model and dependency licenses; do not put weights into Git.
- The commands below use CMD, and assume the Python 3.8 x64 launcher is installed.

## 2. Manually install the separate model environment

After reviewing the upstream repository and license, use a directory such as D:\LocalModels (create it first). Each download below is initiated by you, not by the Podcast app.

```cmd
cd /d D:\LocalModels
git clone https://github.com/OpenTalker/SadTalker.git
cd SadTalker
git rev-parse HEAD
py -3.8 -m venv .venv38
.venv38\Scripts\python.exe -m pip install torch==1.12.1+cpu torchvision==0.13.1+cpu torchaudio==0.12.1 --extra-index-url https://download.pytorch.org/whl/cpu
.venv38\Scripts\python.exe -m pip install -r requirements.txt
.venv38\Scripts\python.exe -m pip check
```

This is a historical compatible-version starting point, not a guarantee that today's package resolver or all upstream dependencies will install. If pip check fails, do not blindly upgrade torch or torchvision or disable security checks. Save the exact commit/version and local error. Refer to upstream install instructions and the official compatibility matrix. This environment is not the Podcast app's .venv.

## 3. Install and inspect checkpoints

Follow the [official SadTalker README](https://github.com/OpenTalker/SadTalker) checkpoint instructions for the chosen source revision. Obtain the actual model and mapping assets required by that revision, including any separately required auxiliary weights. Verify file origins and available checksums before using them. Do not treat one arbitrary checkpoint file as a complete model. Only load trusted weights: legacy PyTorch checkpoint deserialization may execute code.

The Podcast MODEL check verifies local file layout, required CLI spellings, checkpoint inventory, interpreter version, and hardware observations. It does not authenticate weight contents, import torch or prove inference works.

## 4. Validate before spending hours on CPU

- Return to the Podcast repository; run CHECK_SADTALKER_CPU.bat and enter the selected SadTalker folder. It finds .venv38 or prompts for a custom Python executable.
- Build authorized source and exact PCM chunks in a separate private studio. Run PILOT with explicit rights consent (one sample per presenter).
- Inspect lips, identity, voice, facial stability, and playback via REVIEW. Record all three honest PASS/FAIL observations using RECORD. BATCH and SESSION now reject absent, failed or stale manual pilot records, before any new model inference.
- A failed pilot is not permission to overwrite original source, previews or review records. Preserve evidence and use a fresh private workspace if model/portrait/source changes require a new production attempt.
- Use BUDGET and READINESS; then perform bounded BATCH/SESSION only after the gate passes. No guaranteed speed or ten-minute model output is claimed by this setup recipe.

## Upstream references

- https://github.com/OpenTalker/SadTalker
- https://github.com/OpenTalker/SadTalker/blob/main/docs/install.md
- https://docs.pytorch.org/get-started/previous-versions/
- https://docs.pytorch.org/audio/stable/installation.html
