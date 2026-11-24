# V4 final neural candidate composition

Requires complete verified clips, current approved script/cast/master/listening review, and every presenter pilot PASS. The CLI refuses synthetic fixture-only receipts. The selected project format determines 1280x720 landscape, 720x1280 vertical or 720x720 square. No actual real-model acceptance has been performed.

```cmd
.venv\Scripts\python.exe -m podcast_gpt project-neural-compose --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-neural-audit --project-id PROJECT_ID
```

The composer normalizes each facial clip to a fitted, padded canvas, 25 fps and H.264, uses static portrait cards during silence, and computes cumulative frame boundaries from integer 16kHz PCM samples. This avoids cumulative independent rounding drift. Model audio is discarded. The verified master WAV is the only muxed audio input (AAC output is lossy). Separate UTF-8 SRT uses actual speech boundaries. Frame count, full decode, duration, codecs, dimensions, subtitle bytes and source/clip hashes are audited. Rendering is synchronous and CPU-intensive, with bounded subprocess timeouts. Disk estimate is a conservative starting threshold, not a guarantee.

Outputs are private current audio-version/neural-export/episode.mp4, episode.srt and receipt.json. Existing complete exports are audited, never overwritten. Incomplete output requires manual inspection; safe archive recovery is pending. Pause cards reuse static preview design, so silence may visibly switch from face video to a labeled still. Studio layout polish and smooth transitions remain pending. No burned-in subtitles, automated shorts trimming or multi-format simultaneous export.

The candidate is structurally decoded, not certified for actual mouth movement, face identity, speech fidelity, content rights, or publication. Complete per-turn visual QA, actual model acceptance and full-length Windows production test are still required. Tests inject short synthetic clips with deliberately different model audio; production CLI does not accept test fixture mode.

Full candidate-specific manual review is now available through V4_ACCEPTANCE.md. The immutable export receipt remains separate from human review. No automatic publication.

Optional post-produced audio-only mix is separate from this exporter. The original audited master remains the sole video audio input; mixed-video support is pending (V4_POST_AUDIO_RECOVERY.md).
