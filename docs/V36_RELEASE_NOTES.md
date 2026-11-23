# Podcast GPT v3.6.0 — private READINESS stage verification

New canonical GitHub repo: https://github.com/mohdazizshaikh/podcast

This is an independently reconstructed implementation from Project history,
not a byte-identical extraction of the suspended account's source tree.

## Read-only one-click stage navigator

Run `CONTINUE_FULL_HINDI_NEURAL.bat`, choose `READINESS`, or click
READINESS on the localhost private dashboard. Alternatively:

```powershell
python -m podcast_gpt --workspace "$HOME\PodcastGPTStudio" readiness
```

The JSON report is private and returns concrete statuses, remaining counts,
explicit blockers, and one next safe stage. Its checks include:

- Valid original 45-turn Hindi script and 15 turns per presenter;
- Three actual valid portrait PNGs (technical only, no likeness-rights claim);
- Up to 45 exact 16kHz mono PCM WAVs, SHA distinctness and production 540–660s gate;
- Independently rehashed original source manifest and exact PCM chunks;
- Independent FFmpeg/ffprobe 720p/AAC/SRT static media audit if present;
- Independently decoded, source-bound saved facial MP4 preview counts by speaker;
- Current private three-presenter PASS/FAIL receipt bound to live MP4 SHAs;
- Source-bound full-neural candidate MP4/AAC/SRT audit if present.

Any missing stage is marked missing/partial. SHA mismatch, corrupt media,
unsafe symlink, stale pilot observations or incomplete outputs are BLOCKED.
Conservative next actions never bypass signed-source or human quality gates.

## Privacy / resource limits

READINESS does **not** write or overwrite source, media, model/checkpoint or
report files. It makes **zero** model/TTS calls, downloads or encodes. It
does rehash/decode genuine saved media, so a full 10-minute workspace may
take several minutes on a normal Windows CPU. Its local JSON output
can contain private file paths/error strings; don't publish it accidentally.

No automated report establishes portrait ownership, natural Hindi voice,
lip/identity quality or publication authorization. The final decision
still requires a user review of all original 45 dialogue turns.

## Remaining validation

Real pretrained third-party SadTalker CPU model installation, authorized
portrait assets, original 540–660s Hindi WAVs, genuine three-speaker lip
previews, total render duration/cost and human review must be tested on
the owner's actual Windows computer. GitHub Actions uses synthetic data
and a clearly fake external model process, not natural AI video.
