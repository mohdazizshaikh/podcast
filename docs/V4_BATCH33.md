# Batch 33 — optional neural camera motion and verified local portrait preview

Batch 32 CI runs 45500115177 and 45500231172 both passed; latest 6/6. New optional studio camera push-in (fixed remains default) uses a centered 3% zoom over each active-speaker clip, one output frame per input frame, stationary labels and listener cells. Pauses remain still; no new facial animation or listener reactions. Configure before generating studio outputs:
```cmd
.venv\Scripts\python.exe -m podcast_gpt project-studio-configure --project-id ID --layout grid --camera push-in
```
Browser studio settings expose the same option. Existing fixed settings and receipts remain unchanged. New camera settings are hashed by existing studio binding; original output candidates preserved. Static preview remains static. This is a simple digital crop, not physical camera simulation or scene transitions. Existing frame count, subtitle and separate review gates apply.

Browser portrait audit exposes the local PNG path; select that file locally, compare SHA-256 to the audited candidate, show a blob image only on a match. No HTTP image serving or external upload. Changing candidate/file clears preview/rights checkbox and revokes prior blob. Browser media and portrait hashing use sequence guards to reject stale asynchronous file selections. Image preview is optional; manual OS inspection remains supported. Real browser interaction pending.

53 newly authored cases: 36 camera geometry, 8 invalid mode, 6 invalid geometry, 2 immutable settings, 1 markup; existing synthetic export test now exercises push-in and mixed studio. CI pending. Test cases not independent feature tasks.
