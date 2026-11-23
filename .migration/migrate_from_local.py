#!/usr/bin/env python3
"""Preserve and move an existing complete LOCAL podcast-gpt Git clone.

Never reads a suspended GitHub account. Never modifies source clone. Public
repository import is explicitly confirmed, refuses secrets/private media.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath

DEST = 'https://github.com/mohdazizshaikh/podcast.git'
IMPORT_BRANCH = 'migration/full-local-source'
DANGEROUS = ('*.env', '.env*', '*.pem', '*.p12', '*.pfx', '*.key', 'id_rsa*',
             'id_ed25519*', '.npmrc', '.netrc', '.pypirc', '*credentials*',
             '*secret*.json', '*token*.json', '*password*')
MEDIA = ('.mp4', '.mov', '.wav', '.mp3', '.m4a', '.flac', '.png', '.jpg', '.jpeg',
         '.webp', '.ckpt', '.safetensors', '.pt', '.pth', '.onnx')
MAX_BYTES = 95 * 1024 * 1024
V297_REQUIRED = (
    'README.md', 'CONTINUE_FULL_HINDI_NEURAL.bat',
    'RUN_NEURAL_CHUNK_SESSION.bat', 'RUN_NEURAL_CHUNK_BATCH.bat',
    'REVIEW_VERIFIED_NEURAL_CHUNKS.bat',
    'scripts/neural_chunk_session.py', 'scripts/neural_chunk_batch.py',
    'scripts/review_verified_neural_chunks.py', 'scripts/full_neural_chunks.py',
    'scripts/review_full_hindi_turns.py',
    'tests/test_v297.py', 'docs/V297_RELEASE_NOTES.md',
    '.github/workflows/tests.yml',
)


def git(cwd: Path, *cmd: str, check: bool = True) -> str:
    p = subprocess.run(['git', '-C', str(cwd), *cmd], capture_output=True,
                       text=True, encoding='utf-8', errors='replace')
    if p.returncode and check:
        raise RuntimeError(f'git {" ".join(cmd[:3])} failed: {p.stderr[-850:]}')
    return p.stdout.strip()


def paths(cwd: Path, *args: str) -> list[str]:
    p = subprocess.run(['git', '-C', str(cwd), *args], capture_output=True)
    if p.returncode:
        raise RuntimeError('Cannot inventory source tracked/untracked files: ' +
                           p.stderr.decode(errors='replace')[-600:])
    return [os.fsdecode(x) for x in p.stdout.split(b'\0') if x]


def validate(repo: Path, items: list[str], allow_public_media: bool) -> dict:
    issues = []
    digest = hashlib.sha256()
    tracked = set(paths(repo, 'ls-files', '-z', '--cached'))
    for rel in sorted(set(items)):
        parsed = PurePosixPath(rel.replace('\\', '/'))
        if parsed.is_absolute() or '..' in parsed.parts or not parsed.parts:
            issues.append(f'Unsafe relative path: {rel}')
            continue
        file = repo / rel
        if not file.exists() and not file.is_symlink():
            # Deletion of an existing tracked file is preserved as a deletion.
            if rel not in tracked:
                issues.append(f'Untracked path disappeared: {rel}')
            continue
        if file.is_symlink() or not file.is_file():
            issues.append(f'Symlink/submodule/directory requires manual review: {rel}')
            continue
        name = file.name.lower()
        if any(fnmatch.fnmatch(name, pattern) for pattern in DANGEROUS):
            issues.append(f'Potential credential file: {rel}')
        if file.stat().st_size > MAX_BYTES:
            issues.append(f'GitHub >95MiB file: {rel}')
            continue
        if file.suffix.lower() in MEDIA and not allow_public_media:
            issues.append(f'Potential private media/model: {rel}; use --allow-public-media ONLY after rights/privacy review')
        hashval = hashlib.sha256(file.read_bytes()).hexdigest()
        digest.update(rel.encode('utf8', errors='surrogateescape') + b'\0' +
                      hashval.encode('ascii') + b'\n')
    return {'tracked_count': len(tracked), 'candidate_count': len(set(items)),
            'candidate_file_digest': digest.hexdigest(), 'blocking_findings': issues}


def prepare_source(src: Path, tmp: Path, items: list[str]) -> tuple[Path, str]:
    snapshot = tmp / 'source'
    subprocess.run(['git', 'clone', '--no-local', '--no-hardlinks', '--',
                    str(src), str(snapshot)], check=True, capture_output=True)
    source_head = git(src, 'rev-parse', 'HEAD')
    git(snapshot, 'checkout', '-B', 'migration-import-local', source_head)
    for rel in items:
        original = src / rel
        target = snapshot / rel
        if original.is_file() and not original.is_symlink():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(original, target)
        elif target.exists():
            target.unlink()
    git(snapshot, 'add', '-A')
    if git(snapshot, 'status', '--porcelain'):
        git(snapshot, '-c', 'user.name=Podcast Git Migration',
            '-c', 'user.email=mohd.aziz.sk@gmail.com', 'commit',
            '-m', 'snapshot: preserve existing local tracked and untracked podcast source')
    return snapshot, git(snapshot, 'rev-parse', 'HEAD')


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description='Offline-source migration into the new GitHub repo (never uses suspended account)')
    p.add_argument('--source', type=Path, required=True, help='Existing FULL local Git clone, not the new blank repo')
    p.add_argument('--publish', action='store_true', help='Explicitly push verified source and merge with new repo main')
    p.add_argument('--allow-public-media', action='store_true', help='Include tracked/untracked media after author confirms rights')
    p.add_argument('--backup-dir', type=Path, help='Where to store full local git bundle and JSON inventory')
    p.add_argument('--v298-patch', type=Path, help='Optional verified additive offline v2.98 patch to apply before main publication')
    args = p.parse_args(argv)
    if not shutil.which('git'):
        print('BLOCKED: Git for Windows is required.', file=sys.stderr)
        return 2
    src = args.source.expanduser().resolve()
    if not (src / '.git').exists() or not git(src, 'rev-parse', '--is-inside-work-tree') == 'true':
        print('BLOCKED: --source must be the existing FULL working Git clone.', file=sys.stderr)
        return 2
    if not git(src, 'branch', '--show-current'):
        print('BLOCKED: checkout a named original branch; detached HEAD cannot guarantee branch migration.', file=sys.stderr)
        return 2
    origin = git(src, 'remote', 'get-url', 'origin', check=False)
    if 'github.com/mohdazizshaikh/podcast' in origin.lower():
        print('BLOCKED: source is the NEW destination clone, not the original project.', file=sys.stderr)
        return 2
    if git(src, 'rev-parse', '--is-shallow-repository') == 'true':
        print('BLOCKED: shallow source clone cannot guarantee complete history.', file=sys.stderr)
        return 2
    missing_modules = [rel for rel in V297_REQUIRED if not (src / rel).is_file()]
    if missing_modules:
        print('BLOCKED: local clone lacks required v2.97 platform files: ' +
              ', '.join(missing_modules), file=sys.stderr)
        return 2
    if ('PILOT' not in (src / 'CONTINUE_FULL_HINDI_NEURAL.bat').read_text(encoding='utf8', errors='replace')
            or '--pilot-three-speakers' not in
            (src / 'RUN_NEURAL_CHUNK_SESSION.bat').read_text(encoding='utf8', errors='replace')):
        print('BLOCKED: original v2.97 PILOT stage markers absent in local clone.', file=sys.stderr)
        return 2
    items = paths(src, 'ls-files', '-z', '--cached', '--others', '--exclude-standard')
    inventory = validate(src, items, args.allow_public_media)
    inventory.update({'source_head': git(src, 'rev-parse', 'HEAD'),
                      'source_branch': git(src, 'branch', '--show-current'),
                      'destination': DEST,
                      'source_is_shallow': False,
                      'uncommitted_changes': bool(git(src, 'status', '--porcelain')),
                      'ignored_not_uploaded': len(paths(src, 'ls-files', '-z', '--others', '--ignored', '--exclude-standard'))})
    print(json.dumps(inventory, indent=2, ensure_ascii=False))
    if inventory['blocking_findings']:
        print('BLOCKED: review findings; nothing uploaded or modified.', file=sys.stderr)
        return 2
    if not items:
        print('BLOCKED: no source files in this local clone.', file=sys.stderr)
        return 2
    if not args.publish:
        print('DRY RUN ONLY: no network or changes. Re-run with --publish after review.')
        return 0
    if not args.backup_dir:
        print('BLOCKED: --publish requires --backup-dir OUTSIDE source for an independent Git bundle.', file=sys.stderr)
        return 2
    backup = args.backup_dir.expanduser().resolve()
    if backup == src or src in backup.parents:
        print('BLOCKED: backup must be outside source checkout.', file=sys.stderr)
        return 2
    backup.mkdir(parents=True, exist_ok=True)
    bundle = backup / ('podcast-original-all-refs-' + inventory['source_head'][:12] + '.bundle')
    report = backup / ('podcast-migration-inventory-' + inventory['source_head'][:12] + '.json')
    if bundle.exists() or report.exists():
        print('BLOCKED: backup already exists, refusing overwrite.', file=sys.stderr)
        return 2
    git(src, 'bundle', 'create', str(bundle), '--all')
    git(src, 'bundle', 'verify', str(bundle))
    report.write_text(json.dumps(inventory, indent=2, ensure_ascii=False) + '\n', encoding='utf8')
    print('BACKED UP original Git refs at:', bundle)
    with tempfile.TemporaryDirectory(prefix='podcast-new-git-migration-') as temp:
        tmp = Path(temp)
        snapshot, sha = prepare_source(src, tmp, items)
        # Recheck the working-tree files before publishing; the user may
        # have edited them while snapshot copy ran.
        if validate(src, items, args.allow_public_media)['candidate_file_digest'] != inventory['candidate_file_digest']:
            raise RuntimeError('Source changed during migration; no source push performed.')
        git(snapshot, 'remote', 'add', 'destination', DEST)
        git(snapshot, 'push', 'destination', f'HEAD:refs/heads/{IMPORT_BRANCH}')
        print('UPLOADED full source/history to import branch:', IMPORT_BRANCH, sha)
        # The new repo contains only .migration/* bootstrapping; merging
        # unrelated histories preserves BOTH repository trees and history.
        merged = tmp / 'destination'
        subprocess.run(['git', 'clone', '--', DEST, str(merged)],
                       check=True, capture_output=True)
        git(merged, 'fetch', 'origin', IMPORT_BRANCH)
        git(merged, '-c', 'user.name=Podcast Git Migration',
            '-c', 'user.email=mohd.aziz.sk@gmail.com',
            'merge', '--no-ff', '--allow-unrelated-histories', 'FETCH_HEAD',
            '-m', 'migration: preserve complete local podcast project and original commit lineage')
        # Bit-for-bit audit before any MAIN publication.
        for rel in items:
            actual = src / rel
            published = merged / rel
            if actual.is_file():
                if not published.is_file() or hashlib.sha256(actual.read_bytes()).digest() != hashlib.sha256(published.read_bytes()).digest():
                    raise RuntimeError('Merged Git tree differs from original source: ' + rel)
            elif published.exists():
                raise RuntimeError('Original deleted file unexpectedly exists in merged Git tree: ' + rel)
        if args.v298_patch:
            patch = args.v298_patch.expanduser().resolve()
            if not patch.is_file() or patch.is_symlink() or patch.stat().st_size > 1024 * 1024:
                raise RuntimeError('Invalid v2.98 patch location or unsafe patch size')
            chk = subprocess.run(['git', '-C', str(merged), 'apply', '--check', str(patch)],
                                 capture_output=True, text=True)
            if chk.returncode:
                reverse = subprocess.run(['git', '-C', str(merged), 'apply', '--reverse',
                                          '--check', str(patch)], capture_output=True)
                if reverse.returncode:
                    raise RuntimeError('v2.98 patch did not apply cleanly; refusing incomplete main publication: ' + chk.stderr[-500:])
                print('v2.98 patch already present in local project; no duplicate apply.')
            else:
                git(merged, 'apply', str(patch))
                git(merged, 'add', '-A')
                git(merged, '-c', 'user.name=Podcast Git Migration',
                    '-c', 'user.email=mohd.aziz.sk@gmail.com', 'commit',
                    '-m', 'feat(v2.98): restore private original Hindi three-presenter manual QA addon')
                print('APPLIED exact additive v2.98 offline patch to imported project.')
        git(merged, 'push', 'origin', 'HEAD:refs/heads/main')
        print('PUBLISHED complete imported source/history and requested addons on destination main.')
        # Do not discard alternate original source branches or tags.
        # They are separately archived under a non-conflicting namespace.
        branches = git(src, 'for-each-ref', '--format=%(refname:short)', 'refs/heads')
        for branch in branches.splitlines():
            original_sha = git(src, 'rev-parse', f'refs/heads/{branch}')
            git(snapshot, 'push', 'destination',
                f'{original_sha}:refs/heads/archive/original/{branch}')
        git(snapshot, 'push', 'destination', '--tags')
        print('ARCHIVED', len(branches.splitlines()),
              'original local branches plus Git tags. Keep offline bundle too.')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.CalledProcessError) as err:
        print('BLOCKED / PARTIAL: ' + str(err), file=sys.stderr)
        print('If a remote import branch exists, it preserves source; destination main is not claimed migrated until merge succeeds.', file=sys.stderr)
        raise SystemExit(1)