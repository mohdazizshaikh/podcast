# V4 private projects and encrypted keys

V4 projects live in v4-projects/<random project ID> under the private workspace. The V3 project.json, originals and render pipeline are unaffected. Each project stores an independently validated immutable request and optional outline with SHA256 bindings. Project creation and outline generation are explicit; no auto rendering, no background AI calls. A saved outline cannot be silently replaced. Make another project to revise it. Hashes detect changes, not malicious rewriting of both the data and its hash.

Use application venv:

```cmd
.venv\Scripts\python.exe -m podcast_gpt project-create --request "%USERPROFILE%\PodcastGPTStudio\request.json"
.venv\Scripts\python.exe -m podcast_gpt project-list
.venv\Scripts\python.exe -m podcast_gpt project-show --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-plan --project-id PROJECT_ID --offline-only
```

The local dashboard lists projects. CLI creates them and plans outlines. Topic-only input still applies until ingestion is implemented.

Windows persistent credentials use native current-user DPAPI; no plaintext fallback or key arguments. Key precedence: project encrypted override, default encrypted key, environment variable. The user can remove or replace saved keys. A key is not billing evidence. No cloud consent is stored. The encrypted blobs are tied to the Windows user/profile; do not expect portability to other accounts or computers. OS-level protection does not defend against malware running as the same user. On non-Windows use environment/session keys.

```cmd
.venv\Scripts\python.exe -m podcast_gpt key-store --provider openrouter
.venv\Scripts\python.exe -m podcast_gpt key-store --provider gemini --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt key-status --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-plan --project-id PROJECT_ID --allow-cloud-text --confirm-gemini-free-project
.venv\Scripts\python.exe -m podcast_gpt key-remove --provider gemini --project-id PROJECT_ID
```

Only confirm Gemini free-project status after ensuring billing is disabled. Otherwise omit that flag. Default offline execution does not decrypt stored keys. No credentials or user content belong in Git, screenshots or chat. Keep private projects outside Git and back up nonsecret project data separately. Real provider execution and physical desktop acceptance remain unverified.

Non-topic projects now support a bounded source attachment before outline generation. See [V4_INGESTION.md](V4_INGESTION.md). Existing schema-1 topic outlines remain readable; new outlines bind source evidence when present.

After saving an outline, project-script-generate/status/finalize/show provide resumable dialogue drafts; project-list and project-show now reflect script progress. See [V4_SCRIPT_GENERATION.md](V4_SCRIPT_GENERATION.md).
