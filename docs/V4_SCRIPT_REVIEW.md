# V4 manual script editing and human review

After finalizing a generated script, use the local CLI to inspect, create an editable JSON copy, and save a new immutable version. The original generated draft and each previous review are retained. The latest saved revision is the current version. Up to 20 revisions per project. The editor currently preserves unit boundaries, number of turns and stable IDs; to change structure, create a new project. A browser editor, arbitrary restructuring and verbatim timed-script import remain pending.

```cmd
.venv\Scripts\python.exe -m podcast_gpt project-script-current --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-script-edit-template --project-id PROJECT_ID
```

Edit the returned private edit-rNNN.json file in a UTF-8 text editor. Keep its version binding, turn IDs and ordering. You may change spoken text, speaker within the original section, and estimated seconds within the original one-minute unit. Preserve valid research citations if applicable. The same dialogue and citation validators apply to human edits. Then save:

```cmd
.venv\Scripts\python.exe -m podcast_gpt project-script-revise --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-script-current --project-id PROJECT_ID
.venv\Scripts\python.exe -m podcast_gpt project-script-review-template --project-id PROJECT_ID
```

Read the entire current script and original sources. Edit the returned review-rNNN.json with PASS or FAIL for each turn and four global criteria: accuracy/source context, language/dialogue, estimated timing/continuity and content rights. Do not change binding fields. No default PASS or automatic approval. Record:

```cmd
.venv\Scripts\python.exe -m podcast_gpt project-script-review-record --project-id PROJECT_ID --acknowledgment I_REVIEWED_THIS_ENTIRE_SCRIPT_VERSION
.venv\Scripts\python.exe -m podcast_gpt project-script-review-status --project-id PROJECT_ID
```

All PASS means the owner self-attested review of this exact text version only. A later revision starts UNREVIEWED; old review remains immutable. Failed versions require changes and another review. The local current_script(require_pass=True) gate is available for future media integration; it is not yet a generalized rendering workflow. No automated claim truth verification, measured audio duration, portrait/voice rights certification or publication approval. No API calls or secret transfer in editing/review. Hash bindings catch ordinary changes, not malicious rewriting of all evidence. Keep private files outside Git.
