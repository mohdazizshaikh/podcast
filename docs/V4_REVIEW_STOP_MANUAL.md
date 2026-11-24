# V4 review import, cooperative stop and structured verbatim script

The local dashboard can create private JSON templates and import completed files for script revisions, script approval, master audio, neural pilots, final video, neural studio, audio mix, mixed video, mixed studio and factual review. Choose exact kind, review the current content in full, complete each decision and enter the displayed exact declaration (script revision does not record approval). General authoring consent is also required. The browser sends only selected JSON to localhost, not an external service. Existing source/version-bound validators, locks and immutable review receipts remain authoritative. No default PASS, automatic media judgment or publication. Mixed/studio/fact templates are JSON rather than new graphical per-turn editors. File limit 8 MB, individual validators can be stricter.

The stop button targets the current local inference task ID and asks it to stop at the next verified action boundary. It never kills a running subprocess, releases another process lock or rolls back a checkpoint. It may need to finish an expensive current action before stopping. It is not a pause/resume process controller or persistent queue. Resume explicitly by invoking the eligible engine again; a stopped or failed process may need recovery. Other actions are not cancellable through this control.

## Structured verbatim custom script

Create a knowledge-mode project with input kind custom_script, and import a UTF-8 TXT file containing this JSON (example one minute, one presenter named A):

```json
{"title":"My episode","minutes":[{"turns":[{"speaker":"A","text":"This is my opening dialogue exactly as I intend to say it.","estimated_seconds":30},{"speaker":"A","text":"This is my closing dialogue exactly as I intend to say it.","estimated_seconds":30}]}]}
```

Select Import captured structured script verbatim in dashboard or:

```cmd
.venv\Scripts\python.exe -m podcast_gpt project-script-import-verbatim --project-id PROJECT_ID --acknowledgment I_AUTHORIZE_VERBATIM_IMPORT_OF_THIS_STRUCTURED_SCRIPT
```

Source text is limited to the existing 12,000-character ingestion budget. Exactly one minutes object per requested minute, 2–20 turns, 2–30 whole estimated seconds each, sum 60, 60–2500 total dialogue characters per minute, all cast members present in the first minute and no duplicate normalized dialogue. Text must already be trimmed; validated words/order are preserved. Estimates are not measured duration. Creates deterministic outline and source-bound manual_source parts; interrupted valid prefix resumes; rejects conflicting AI outline and changed source/parts. No AI provider call, no script approval. Existing revision and media gates apply. Unstructured raw prose, arbitrary timing/restructuring, repeated identical turns, web-research custom verbatim mode and unrestricted 60-minute input remain pending. Actual browser and real model acceptance are not established by synthetic tests.
