# V4 reusable character profiles and cast

The local private character library stores immutable profile versions and optional user-authorized single-frame PNG files. A profile contains display name, personality, speaking style, appearance description, and voice engine/language/preset/style preferences. These preferences are metadata only: no actual voice compatibility, voice cloning, identity recognition, lip-sync, or image generation. Realistic portrait generation remains pending. Use a fictional or properly authorized image, including an externally generated image for which you have rights. The app does not independently certify identity or rights.

Create a UTF-8 profile JSON outside Git:

```json
{"name":"Aarav","personality":"Curious and analytical","speaking_style":"Conversational and warm","appearance":"Fictional adult presenter in a studio","voice_preferences":{"engine":"undecided","language":"Hindi","preset":"","style_notes":"Calm"}}
```

Engines: undecided, imported, kokoro, edge. The voice preference does not install a model or guarantee support. PNG must be 200–4096 pixels per dimension, at most 12 megapixels/12 MB, and single-frame. A portrait is copied into the private library after an explicit rights declaration and complete PNG validation.

```cmd
.venv\Scripts\python.exe -m podcast_gpt character-create --profile "%USERPROFILE%\PodcastGPTStudio\character.json" --portrait "D:\Portraits\aarav.png" --acknowledgment I_HAVE_RIGHTS_TO_USE_THIS_PORTRAIT
.venv\Scripts\python.exe -m podcast_gpt character-list
.venv\Scripts\python.exe -m podcast_gpt character-show --character-id CHARACTER_ID
```

You may omit the portrait when creating a metadata-only profile. To create a revised reusable profile, supply --parent-id with the previous character ID and provide the new profile and portrait explicitly. Existing casts never silently change. Assign one unique character ID to each presenter in a private mapping JSON such as {"Aarav":"CHARACTER_ID_1","Meera":"CHARACTER_ID_2"}. Names must exactly match the project request; replace placeholder IDs with real returned values.

```cmd
.venv\Scripts\python.exe -m podcast_gpt project-cast-assign --project-id PROJECT_ID --mapping "%USERPROFILE%\PodcastGPTStudio\cast-mapping.json"
.venv\Scripts\python.exe -m podcast_gpt project-cast-status --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-media-preflight --project-id PROJECT_ID
```

Cast assignment is immutable and binds the request and full profile records. Media preflight is a read-only handoff requiring current script self-attested PASS, complete authorized portraits and distinct portrait hashes. It does not generate audio/video or test actual engines. Different files do not prove different identities. Profiles and cast are not injected into older AI drafts; personality-aware script prompting and longitudinal conversational memory remain pending. No automatic downloads, image generation, cloud requests or paid API calls. Profile/cast files and portraits stay outside Git. Hashes detect ordinary changes, not malicious replacement of all manifests.

The media preflight now feeds V4 authorized WAV import and measured timeline. Voice preferences can be inspected with project-voice-status; real engine compatibility remains unverified. See V4_AUDIO.md.

Hindi Kokoro presets now feed an explicit local TTS adapter for compatible Hindi requests. Other voice preferences remain metadata or authorized import. See V4_TTS_MASTER.md.

Optional eSpeak profile engine and opt-in cast personality prompt snapshots are now available. See V4_MODEL_VOICES_PERSONA.md. Cross-episode memory and realistic portrait generation remain pending.

Local profile-bound portrait brief generation is available (V4_STUDIO_ENGLISH.md). This prepares prompts only, not real AI image generation.

Authorized portrait attachment can create a new character version directly from an existing profile ID; see V4_NEURAL_STUDIO.md. No image inference or cast reassignment.

The localhost dashboard supports character profile creation/revision, authorized portrait attachment and immutable cast selection; see V4_DASHBOARD_AUTHORING.md.

Explicit selected prior human-reviewed dialogue can now be frozen for local-only continuity drafting with matching immutable character versions (V4_NORMALIZATION_CONTINUITY.md). No automatic longitudinal capture.

Batch 29 and 30 CI completed successfully (45494573255, 45495891248 latest combined: 6/6 each). Batch 31 adds explicitly consented local CPU portrait candidate generation with safetensors inventory and immutable candidate receipt; new CI pending. Real model setup, physical acceptance and portrait quality remain unverified. See docs/V4_BATCH31.md (repository-relative).
