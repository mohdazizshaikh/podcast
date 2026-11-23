# Windows setup — original Hindi podcast (no dedicated GPU)

1. Install Python 3.11 and FFmpeg/FFprobe. Confirm `py -3.11 --version`, `ffmpeg -version`, `ffprobe -version` in a new CMD window. Optionally use `winget install Gyan.FFmpeg` for FFmpeg; installation source/availability may vary.
2. Clone **only new repo**: `git clone https://github.com/mohdazizshaikh/podcast.git` then `cd podcast`.
3. Double-click `START_PODCAST_WINDOWS.bat`. The local dashboard at `http://127.0.0.1:7860` will use `%USERPROFILE%\PodcastGPTStudio`. It installs application Python dependencies on first use (internet required) but NEVER downloads pretrained SadTalker weights.
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
