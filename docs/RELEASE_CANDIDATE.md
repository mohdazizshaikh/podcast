# Source-only Windows release candidate

The canonical Git repository remains the complete development source. The Windows distribution is a smaller app-only candidate, deliberately excluding tests, historical migration materials, user media, trained models, checkpoints, virtual environments and private logs.

On a successful CI run, the final Windows job packages only committed allowlisted app code, launchers, and Markdown documentation into podcast-windows-source.zip. It verifies internal SHA256 hashes, extracts the ZIP outside the repository, builds a fresh application venv, installs the app, verifies its dependency stamp, initializes a synthetic private workspace and runs READINESS. Only then does it upload the ZIP and external SHA256 file as a GitHub Actions artifact. This is not a published production release or proof of real model inference. Artifacts expire after 30 days.

## Install from an artifact

1. Download the artifact from a successful Actions run. Extract the outer GitHub artifact to get the source ZIP and its .sha256 file.
2. Compare the checksum (PowerShell): 
```powershell
Get-FileHash .\podcast-windows-source.zip -Algorithm SHA256
Get-Content .\podcast-windows-source.zip.sha256
```
3. Extract the source ZIP to a new application directory; keep your private studio outside it, and never add generated media to Git.
4. Install Python 3.11, FFmpeg and FFprobe separately. Double-click START_PODCAST_WINDOWS.bat. Initial dependency installation may require internet. Models are not bundled. Follow SETUP_WINDOWS.md and SADTALKER_CPU_SETUP.md for local model and human acceptance steps.

Developers can reproduce the archive from a committed checkout using python scripts/build_release.py --output dist/podcast-windows-source.zip and inspect its contents with --verify. Builds use committed Git blobs, not the dirty working tree. The internal manifest and checksum detect file corruption; they do not independently authenticate the publisher. Use the trusted repository and Actions run to obtain the expected source commit and checksum.
