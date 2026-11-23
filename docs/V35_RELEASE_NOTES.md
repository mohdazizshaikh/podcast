# Podcast GPT v3.5.0 — optional online TTS source safety

Canonical new repository: https://github.com/mohdazizshaikh/podcast

**This is a reconstructed project, not a byte-identical migration from the
suspended GitHub account. That account was not accessed.**

## Fixed

Optional `tts-one` originally copied FFmpeg-converted audio with a
nonexclusive file copy, which could overwrite an existing original WAV
after a time-of-check race. It also did not refuse audio regeneration once
the original-source SHA manifest existed. v3.5 fixes both:

- Requires explicit `--allow-network-tts` BEFORE trying the provider.
- Refuses to touch a voice if the source is SHA-bound, or if a WAV/online
  receipt already exists. Never silently overwrite originals.
- Performs private temporary MP3-to-16k mono PCM conversion in the
  owner's existing `scratch/` folder with symlink and free-space checks.
- Revalidates the script and source-bound marker AFTER remote synthesis
  but BEFORE exclusively creating the new WAV with `open('xb')`.
- Adds a local `voices/NNN.edge-tts-source.json` source/voice/WAV SHA
  receipt, containing no user dialogue text.
- Adds independent fake-provider tests that run FFmpeg locally without
  sending any script to the internet; they cover opt-in, overwrite refusal,
  source immutability and changes to project text mid-network-call.

## Important limitations

This feature uses Microsoft Edge TTS online voice generation, and sends the
selected Hindi text externally. It uses only two Hindi voice presets
(Kabir differs by speech rate), so it is NOT proof of three unique,
natural voice personalities. Fully local Kokoro ONNX and imported authorized
real recordings remain available alternatives. Neither provider was run
against the user's actual Windows machine in CI.

The full real 10-minute speaking-face podcast is still pending real
licensed SadTalker weights, actual authorized portraits/voices, user CPU
performance measurement, lip/identity quality review and publication rights.
