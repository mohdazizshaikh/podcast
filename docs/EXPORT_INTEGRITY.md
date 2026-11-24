# v3.7 maintenance — media export integrity

- STATIC and COMPOSE use a single exclusive workspace-local lock across independent CLI/browser processes. It is released on handled errors only if its marker still matches. A crashed process can leave a lock; inspect the process and output manually. Never delete an active lock.
- Exports create MP4 and SRT exclusively instead of overwriting a destination. Interrupted artifacts are not a complete export; preserve and inspect them before retrying.
- READINESS stops if a private media export or CPU inference session is active/interrupted. It does not mutate evidence or certify human lip-sync.
- FFprobe must independently report finite positive container, video and audio durations. Attached cover images are rejected. Final H.264 / 48 kHz AAC / 720p media must cover the signed timeline within 0.45 seconds (container/video) and 0.5 seconds (audio), rather than accepting a percentage of a ten-minute episode. Both streams still undergo complete FFmpeg decoding.
- Regression coverage includes competing export entrypoints and a second Python process, foreign marker preservation, invalid stream durations, shortened tracks and cover artwork. These are synthetic checks; actual SadTalker Windows quality and full authorized 10-minute playback are still pending.
