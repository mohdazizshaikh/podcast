# V4 English neural frontend, portrait preparation and static studio preview

The optional Kokoro English frontend uses Misaki non-transformer G2P with explicit American/British variants and local eSpeak fallback. See [upstream Misaki English usage](https://github.com/hexgrad/misaki#english-usage) and [Kokoro voice catalog](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md). Select English/en-us (American default) or British English/en-gb consistently in project and profile. Ten US and eight UK candidate voice IDs are available; installed pack availability and real speech quality still need verification. Existing language receipts and V3 Hindi adapter are unchanged. The explicit optional dependency group kokoro-english installs Misaki English extras; this does not install every external language resource or guarantee all third-party initialization is network-free. Prepare trusted dependencies and models manually before using offline. Japanese and Mandarin remain disabled pending model-specific setup verification; Edge remains pending.

```cmd
.venv\Scripts\python.exe -m podcast_gpt dependency-plan --group kokoro-english
.venv\Scripts\python.exe -m podcast_gpt dependency-install --group kokoro-english --acknowledgment I_AUTHORIZE_INSTALLING_FREE_OPTIONAL_PYTHON_PACKAGES
.venv\Scripts\python.exe -m podcast_gpt kokoro-language-catalog
```

## Portrait preparation
```cmd
.venv\Scripts\python.exe -m podcast_gpt character-portrait-brief --character-id CHARACTER_ID
```
The command returns a local reusable prompt, negative prompt and recommended import specifications for the profile appearance. It does not generate an image, transmit it or certify face identity. Use a trusted image tool independently and import the authorized single-frame PNG using a new profile version before assigning the cast. Local AI image inference remains pending.

## Static studio
```cmd
.venv\Scripts\python.exe -m podcast_gpt project-studio-configure --project-id PROJECT_ID --layout grid --background "D:\Private\studio.png" --acknowledgment I_HAVE_RIGHTS_TO_USE_THIS_STUDIO_BACKGROUND
.venv\Scripts\python.exe -m podcast_gpt project-studio-status --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-studio-render --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-studio-audit --project-id PROJECT_ID
```

Background is optional, otherwise a solid canvas is used. Imported backgrounds obey existing PNG size, frame and rights checks. Settings are immutable for the project. Layout focus displays the active presenter, grid shows 1–10 static portraits with a speaking highlight, fitted to selected landscape/vertical/square format. The backgrounds are behind rectangular portrait cards, not face cutouts or composited photorealistic scenes. Requires approved script, cast, master and listening PASS. Existing preview and neural exports stay unchanged. Private studio-preview/studio.mp4, studio.srt and receipt bind the settings, master, cast and current timeline. Video is H.264/AAC with original master audio and measured SRT sidecar; full decode and hashes audited. No lip-sync, actual camera movement, studio integration into neural output, custom branding, embedded subtitles or publication approval. Recovery protects dependent studio previews but incomplete studio output/settings still require manual inspection. Synthetic tests cover layout geometry and short preview; actual installed models and real Windows acceptance remain unverified.
