# Podcast GPT — new repository migration

**Destination:** https://github.com/mohdazizshaikh/podcast.git (`main` branch). This `.migration/` folder is **bootstrap tooling only**, not the original podcast platform. Do not mistake this initial commit for the full project.

**Source requirement:** An existing, full **local** `podcast-gpt` clone on your Windows PC containing actual source and `.git` history. The suspended remote is **never contacted**. The migration tool copies from the local disk only.

1. Clone **this new repo** to a **separate** Windows folder: `git clone https://github.com/mohdazizshaikh/podcast.git podcast-new`
2. Open `podcast-new\.migration\MIGRATE_FROM_WINDOWS.bat`.
3. Specify your full original `podcast-gpt` clone (folder containing `.git`).
4. Check printed file count, uncommitted changes, source SHA and blocking findings. It scans tracked and untracked **non-ignored** files and refuses secret-looking/media/model artifacts by default. Ignored media, virtual environments and downloaded model weights stay local; they are **not** silently published to this public repo.
5. Confirm `Y` to publish. Git for Windows and Python 3 are needed, along with an authenticated **new** GitHub account through Git Credential Manager.
6. A separate offline Git bundle of all original refs/tags is saved under `%USERPROFILE%\Podcast-Git-Migration-Backups` **before** any upload. Original source directory is never modified.
7. The new repo's `main` receives a merge commit connecting the original project Git lineage and this bootstrap branch. Verify `git log --all --oneline`, tracked files and CI; don't delete original local clone/bundle until the result is verified.

### Important limitations

- The migration tool is **not a full original source copy**. It cannot re-create code that is absent from the local clone.
- If the original project was a **shallow** clone, lacks `.git`, contains symlinks/submodules, secrets, large files or potentially private media, the tool refuses. An authorized expert can inspect those items before extending the migration. `--allow-public-media` exists for separately inspected public-safe media but the interactive `.bat` does not enable it.
- Untracked **ignored** content is not uploaded or backed up in the `.bundle`. Private portraits, generated clips, downloads and model weights should remain on the Windows workspace and be backed up separately, not pushed publicly.
- `v2.98` was an **offline patch**, not a previous GitHub commit. Apply that patch only after successfully importing source, using the downloadable `podcast-gpt-v298-offline.zip` from the chat, and inspect/test it before committing. This repo does not yet contain full v2.98 source.
- Unexpected merge conflicts leave the original import branch on GitHub; no forced overwrite or fake success. Resolve conflicts locally before retrying a safe merge.

## Project milestone (prior development record)

v2.97 implemented guarded 3-presenter Hindi CPU pilot (`PILOT`) selecting one sample per Aarav/Meera/Kabir; v2.96 local offline sample viewer (`SAMPLES`); v2.95 bounded batch/session/budget modes; previous source/audio/PCM/final composition, verification and human review modules. Prior automated CI used synthetic models/media; natural 10-minute lip-sync quality on the user's real Windows GPU-less machine remains unverified.

**Do not deploy from this bootstrap-only GitHub state.** The full project must be imported, verified and its dependencies installed first.