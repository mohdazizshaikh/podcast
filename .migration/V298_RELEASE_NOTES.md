# v2.98 — private human review of the **three original Hindi AI presenter pilot faces**

**Distribution status:** Offline additive patch. NOT pushed to GitHub because the connected GitHub API returned HTTP 403 ("Sorry. Your account was suspended"). Last known pushed commit was `a7d86609`; the final v2.97 CI status could not be verified during this session.

## Why add this?

v2.97 can generate one *genuine, source-bound* SadTalker talking-face preview for each of **Aarav, Meera and Kabir** before the long CPU-only render. v2.96 can play saved previews in a local HTML viewer. Neither tool records a human's explicit yes/no assessment of **all three** pilot faces against the original Hindi speech, for later review.

This optional v2.98 tool adds a **private, source-bound human observation**. It does not automatically decide whether lips move accurately, verify presenter image rights, or authorize publishing. All original, signed Kokoro WAVs, AAC/SRT, PNG portraits and real neural MP4/JSON previews are unchanged.

## Applying this offline patch

Extract `podcast-gpt-v298-offline.zip` anywhere on your Windows computer. With an existing local clone of `podcast-gpt` at the **last known v2.97 codebase**, run `APPLY_V298_TO_LOCAL_REPO.bat` and enter the clone directory when asked. The installer only runs `git apply --check`, then `git apply`, using the local bundled patch. It **does not** pull/push code, install anything, run models, create audio/video, or touch existing user media. If the patch cannot be cleanly applied, it stops before changing the repository.

Alternatively, inside the repo in PowerShell (replace the patch path with where you extracted it):

```powershell
cd C:\Projects\podcast-gpt
git apply --check "C:\Downloads\v298-offline.patch"
git apply "C:\Downloads\v298-offline.patch"
```

The patch adds these previously nonexistent files:

- `scripts/pilot_quality_gate.py`
- `REVIEW_THREE_PRESENTER_PILOT.bat`
- `tests/test_v298.py`
- `docs/V298_RELEASE_NOTES.md`

It does not alter existing source scripts or Git history.

## Windows workflow after three genuine model face clips exist

Use the existing guided launcher to create the **one-per-speaker** real pilot if necessary. You still need all three authorized portraits, signed Kokoro Hindi speech, the source-bound PCM chunk export, real SadTalker CPU weights, and explicit `YES` before any model inference:

```powershell
.\CONTINUE_FULL_HINDI_NEURAL.bat
```

Choose `PILOT` at the neural stage, then inspect saved samples. After you have one source-verified MP4 for **each** presenter:

```powershell
.\REVIEW_THREE_PRESENTER_PILOT.bat "D:\HindiStudio"
```

The BAT performs a **read-only disk/source preflight**, independently verifies the full signed original source/portrait/PCM manifest, and independently decodes all saved real face previews. It creates or opens a local-only three-clip HTML reviewer, then pauses so you can inspect **each** presenter with the original Hindi voice. On returning to the terminal, enter `PASS` or `FAIL` separately for Aarav, Meera and Kabir, then type an exact uppercase review acknowledgment to store your own observation. If any face fails, the aggregate observation is **not passed**.

The private review record is saved as a new file beside your *existing signed neural chunk manifest*, such as `pilot-original-hindi-human-observations-<binding>-001.json`. Every new review creates a distinct file: no overwrites or deleted old decisions. The record is source-bound to original project SHA, each selected MP4 SHA and source chunk ID. Current source/preview integrity is independently rechecked **again** before recording any observation. Existing offline reviewer HTML is compared byte-for-byte with the expected generated page before reuse.

To inspect the most recent human note without writing anything:

```powershell
.\REVIEW_THREE_PRESENTER_PILOT.bat "D:\HindiStudio" "" INSPECT
```

**Important:** A `PASS` is merely a human *self-attested opinion on three short samples*; it **does not grant portrait publication rights**, prove natural phoneme alignment for all Hindi words, skip the full 45-turn human review, or cause the pipeline to automatically start the remaining model chunks. The existing full CPU model renderer is **not forcibly gated** by this new optional review; avoid continuing it yourself if any pilot is poor.

## Testing and limitations

- Offline local tests: 14/14 passed with synthetic 45-turn / 3-presenter data and **test-only mock validators**; no real neural AI, real Hindi voices or real video media were rendered or decoded.
- Tests cover first saved clip selection per speaker, local-only HTML and immutable reopening, exact three-user decisions and acknowledgment, failed→passed re-review without overwrite, changed MP4 SHA refusal, existing review tamper rejection, missing third presenter, source SHA mismatch, symlinked HTML refusal, read-only inspection without a human note, altered browser HTML refusal before record, old-review invalidation after an MP4 changes, the real CLI prepare→record→inspect sequence with mocked originals, and refusal of suspicious review note filenames.
- This patch has **not been integrated into GitHub CI or run on a real GPU-less Windows computer** while GitHub access is blocked. It requires the v2.96 viewer and v2.97 original signed PCM/batch modules already present in your clone.
- A self-attestation JSON can be manually forged; it is **not** a cryptographic signature or independent quality/rights certificate.
- Browser file access can vary. If Windows cannot auto-open the local HTML, open the reported `.html` file manually from your own private PCM workspace.
- The full 10-minute, three-presenter naturally lip-synced episode remains **unproven on the user's actual machine**, and requires expensive model rendering followed by full media and human quality audit.