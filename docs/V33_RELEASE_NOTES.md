# Podcast GPT v3.3.0 — safe model setup and cumulative Hindi video timing

Canonical source: https://github.com/mohdazizshaikh/podcast

Built from available project requirements, not copied from the suspended legacy account.

## What's new

- **Read-only SadTalker setup check**: `MODEL` in the guided Windows BAT,
  `CHECK_SADTALKER_CPU.bat`, or CLI `check-sadtalker` (both `--sadtalker-root`
  and `--sadtalker-python` required). It checks that `inference.py` contains
  the expected upstream CPU/face/audio/result options, `src/config` exists,
  checkpoint files are not empty and the selected Python can report its
  version using only the standard library. No model inference, torch import,
  downloads, generated video, portraits or WAVs are touched.
- **CPU consent safety**: `run-cpu` repeats the read-only installed-model check
  before starting real inference, checks pre-existing session locks first,
  then asks for explicit separate rights/CPU consent as before.
- **Real preview completeness**: Independently decoded saved MP4 video
  streams must cover signed PCM duration; an artificially long AAC stream
  does not make a short, broken facial video a verified real model preview.
- **24fps cumulative timing**: Original audio speech+pause durations allocate
  exact per-segment frame counts from the cumulative clock. Prevents dozens
  of short independent rounding errors accumulating into visible/video
  timeline drift over 45 turns. FFmpeg verifies the joined video time before
  muxing the *original authorized* Hindi audio.

## On Windows

Install Python 3.11 and FFmpeg/ffprobe, then:

```powershell
git clone https://github.com/mohdazizshaikh/podcast.git
cd podcast
.\START_PODCAST_WINDOWS.bat
```

After creating a signed original source/45 Hindi WAVs and obtaining a
legitimate local SadTalker model, open `CONTINUE_FULL_HINDI_NEURAL.bat`,
choose `MODEL`, then `PILOT` only with portrait rights and separate YES.
Inspect one actual original-speaking sample for Aarav, Meera and Kabir,
record human PASS/FAIL. Continue bounded BATCH/SESSION, COMPOSE, AUDITFULL,
and REVIEWFULL only when all genuine clips are verified.

## Still pending real-world validation

The CI test suite uses synthetic portraits/audio and fake model runners;
the extended 45-turn FFmpeg test does not load real SadTalker weights or
verify 10 minutes of natural speaking-face video. User-owned portraits,
real 540–660s natural Hindi WAVs, model installation, CPU time/RAM, lip
quality, human identity rights and publishing approval require local review.

Upstream SadTalker reference: https://github.com/OpenTalker/SadTalker
Upstream offline voice reference: https://github.com/thewh1teagle/kokoro-onnx

Read [Remaining acceptance](REMAINING.md), [Windows setup](SETUP_WINDOWS.md)
and [Architecture](ARCHITECTURE.md).
