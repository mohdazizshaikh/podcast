# V4 human audio review and three-format static preview

After composing and auditing the exact master WAV, create a private listening review template. Listen to the whole master and each turn, then explicitly record PASS or FAIL for every turn and all five criteria (text/pronunciation, voice identity, clarity, timing, usage rights). No default PASS. The review is a human self-attestation for the exact master receipt, not independent voice or rights verification.

```cmd
.venv\Scripts\python.exe -m podcast_gpt project-audio-review-template --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-audio-review-record --project-id PROJECT_ID --acknowledgment I_LISTENED_TO_THIS_ENTIRE_MASTER_AND_ALL_TURNS
.venv\Scripts\python.exe -m podcast_gpt project-audio-review-status --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-preview-render --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-preview-audit --project-id PROJECT_ID
```

Edit the returned UTF-8 JSON template before recording. The template and receipt are tied to the current approved script, cast, timeline and exact master. An immutable FAIL blocks preview; correction currently requires a new project or approved script revision and new audio. No overwrite or automatic promotion.

The project video_format selects landscape 1280x720, vertical 720x1280 or square 720x720. Local Pillow creates numbered active-speaker cards with an explicit STATIC PREVIEW - NOT LIP SYNC label. FFmpeg produces 25 fps H.264/AAC MP4 using the measured timeline and master WAV. A separate UTF-8 SRT contains original current script text with measured speech boundaries (excluding pauses). Subtitles are not burned in; external players determine glyph rendering. The preview uses the selected project format only, not simultaneous multi-format export. No shorts trimming, camera animation, neural mouth movement or publication certification.

Output lives in the private current audio version's static-preview folder. Audit checks hashes, exact SRT, dimensions, codecs, absolute stream-duration tolerance and full FFmpeg decode. AAC is lossy; structural decode does not establish perceptual voice fidelity or visual identity. Review and preview receipts do not modify the master. Synthetic fixture tests use color images and tone PCM, not genuine speech or portraits. Physical Windows acceptance, neural pilot, generalized TTS, normalization/mixing, graphical dashboard and full rendering remain pending.

The reviewed master now also feeds the separate V4 local SadTalker pilot/clip pipeline (V4_NEURAL.md). Static preview is not neural rendering and is optional for that pipeline.
