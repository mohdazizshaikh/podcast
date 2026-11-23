# Source migration audit — bootstrap state

- New target account: `mohdazizshaikh`, email: `mohd.aziz.sk@gmail.com`
- New target repo: https://github.com/mohdazizshaikh/podcast.git
- Suspended account: **never accessed by migration tooling**
- Initial new repo state: empty
- Original full v2.97 source snapshot in current ChatGPT runtime: **not available**
- Available offline v2.98 package: archived original additive patch and instructions under `.migration/`; it is not the full original repo
- Migration script: reconstructs **from user's local Git clone** and pushes source history + non-ignored working-tree changes
- Initial status: **BOOTSTRAP ONLY — full source not yet imported**

## Requirements before declaring full migration complete

1. Required v2.97 source modules/launchers/tests and PILOT markers present; Git clone scanned, full history confirmed (`--is-shallow-repository=false`).
2. Tracked/untracked source file inventory and secret/media audit passed.
3. All original Git refs/tags backed up to an offline `.bundle`.
4. Source import branch uploaded using **new** GitHub account.
5. Git merge with unrelated histories completed to target `main` without forced overwrite.
6. GitHub file tree and source inventory independently compared; expected files not missing.
7. Importer clean-applied the preserved v2.98 patch (or verified it was already applied), then actual platform tests passed.
8. GitHub Windows/Ubuntu CI re-run and reviewed.
9. Actual Windows PC CPU model deployment, authorized original portrait/voices, real lip-sync and 10-minute video QA still required.