"""End-to-end local synthetic Git recovery tests; no external GitHub traffic."""
import contextlib
import io
import importlib.util
import tempfile
import unittest
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'migrate_from_local.py'
spec = importlib.util.spec_from_file_location('podcast_migration', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def git(cwd, *args):
    p = subprocess.run(['git', '-C', str(cwd), *args], text=True, capture_output=True)
    if p.returncode:
        raise AssertionError(p.stderr + '\n' + p.stdout)
    return p.stdout.strip()


class Migration(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp.cleanup)
        self.base = Path(self._temp.name)
        self.src = self.base / 'source'
        self.src.mkdir()
        git(self.src, 'init', '-b', 'main')
        git(self.src, 'config', 'user.email', 'unit@example.test')
        git(self.src, 'config', 'user.name', 'Migration Unit')
        (self.src / 'README.md').write_text('ORIGINAL PODCAST SOURCE\n')
        (self.src / 'deleted.txt').write_text('old\n')
        for rel in m.V297_REQUIRED:
            f = self.src / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            if f.name == 'README.md':
                continue
            if rel == 'CONTINUE_FULL_HINDI_NEURAL.bat':
                f.write_text('PILOT\n')
            elif rel == 'RUN_NEURAL_CHUNK_SESSION.bat':
                f.write_text('--pilot-three-speakers\n')
            else:
                f.write_text('Synthetic v2.97 test module - not real source\n')
        git(self.src, 'add', '-A')
        git(self.src, 'commit', '-m', 'first real podcast history')
        self.original_sha = git(self.src, 'rev-parse', 'HEAD')
        git(self.src, 'tag', 'original-v2')
        git(self.src, 'branch', 'alternate-record')
        (self.src / 'deleted.txt').unlink()
        (self.src / 'README.md').write_text('ORIGINAL PODCAST SOURCE WITH WORKTREE CHANGE\n')
        (self.src / 'UNTRACKED_BAT.bat').write_text('@echo off\necho original script\n')
        (self.src / '.gitignore').write_text('*.private\n')
        (self.src / 'video.private').write_bytes(b'secret ignored video')
        self.dest = self.base / 'destination.git'
        subprocess.run(['git', 'init', '--bare', '-b', 'main', str(self.dest)], check=True, capture_output=True)
        bootstrap = self.base / 'bootstrap'
        subprocess.run(['git', 'clone', str(self.dest), str(bootstrap)], check=True, capture_output=True)
        git(bootstrap, 'config', 'user.name', 'Migration Unit')
        git(bootstrap, 'config', 'user.email', 'unit@example.test')
        (bootstrap / '.migration').mkdir()
        (bootstrap / '.migration' / 'README.md').write_text('Bootstrap migration only\n')
        git(bootstrap, 'add', '-A')
        git(bootstrap, 'commit', '-m', 'bootstrap')
        git(bootstrap, 'push', 'origin', 'main')
        self.old_dest = m.DEST
        m.DEST = str(self.dest)
        self.addCleanup(setattr, m, 'DEST', self.old_dest)

    def invoke(self, *options):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return m.main(['--source', str(self.src), *options])

    def test_dry_run_stays_offline_preserves_source_and_target(self):
        old = git(self.dest, 'rev-parse', 'refs/heads/main')
        self.assertEqual(self.invoke(), 0)
        self.assertEqual(git(self.dest, 'rev-parse', 'refs/heads/main'), old)
        self.assertNotEqual(git(self.src, 'status', '--porcelain'), '')
        self.assertEqual(git(self.src, 'rev-parse', 'HEAD'), self.original_sha)

    def test_publication_includes_original_history_local_edits_and_alt_refs(self):
        self.assertEqual(self.invoke('--publish', '--backup-dir', str(self.base / 'backup')), 0)
        restored = self.base / 'restored'
        subprocess.run(['git', 'clone', str(self.dest), str(restored)], check=True, capture_output=True)
        self.assertEqual((restored / 'README.md').read_text(), 'ORIGINAL PODCAST SOURCE WITH WORKTREE CHANGE\n')
        self.assertEqual((restored / 'UNTRACKED_BAT.bat').read_text(), '@echo off\necho original script\n')
        self.assertFalse((restored / 'deleted.txt').exists())
        self.assertFalse((restored / 'video.private').exists())
        self.assertTrue((restored / '.migration' / 'README.md').exists())
        self.assertEqual(git(restored, 'merge-base', '--is-ancestor', self.original_sha, 'HEAD'), '')
        self.assertEqual(git(self.dest, 'rev-parse', 'refs/heads/archive/original/alternate-record'), self.original_sha)
        self.assertEqual(git(self.dest, 'rev-parse', 'refs/tags/original-v2'), self.original_sha)
        self.assertEqual(git(self.src, 'rev-parse', 'HEAD'), self.original_sha)
        bundles = list((self.base / 'backup').glob('*.bundle'))
        self.assertEqual(len(bundles), 1)
        git(restored, 'bundle', 'verify', str(bundles[0]))

    def test_v298_additive_patch_is_applied_only_after_full_original_merge(self):
        patch = self.base / 'v298-mini.patch'
        patch.write_text('diff --git a/QA_V298.txt b/QA_V298.txt\nnew file mode 100644\n'
                         '--- /dev/null\n+++ b/QA_V298.txt\n@@ -0,0 +1 @@\n'
                         '+Synthetic verified private QA module\n')
        result = self.invoke('--publish', '--backup-dir', str(self.base / 'backup'),
                             '--v298-patch', str(patch))
        self.assertEqual(result, 0)
        final = self.base / 'v298-dest'
        subprocess.run(['git', 'clone', str(self.dest), str(final)], check=True, capture_output=True)
        self.assertEqual((final / 'QA_V298.txt').read_text(), 'Synthetic verified private QA module\n')
        self.assertTrue((final / '.migration' / 'README.md').exists())
        self.assertTrue((final / 'README.md').exists())

    def test_incompatible_patch_does_not_publish_incomplete_main(self):
        original_main = git(self.dest, 'rev-parse', 'refs/heads/main')
        patch = self.base / 'bad-v298.patch'
        patch.write_text('diff --git a/README.md b/README.md\n'
                         '--- a/README.md\n+++ b/README.md\n'
                         '@@ -99,1 +99,1 @@\n-missing-source\n+fake-replacement\n')
        with self.assertRaises(RuntimeError):
            self.invoke('--publish', '--backup-dir', str(self.base / 'backup'),
                        '--v298-patch', str(patch))
        self.assertEqual(git(self.dest, 'rev-parse', 'refs/heads/main'), original_main)
        self.assertTrue(git(self.dest, 'rev-parse', 'refs/heads/migration/full-local-source'))

    def test_sensitive_media_blocks_before_writes(self):
        (self.src / 'face.png').write_bytes(b'fake private portrait')
        self.assertEqual(self.invoke('--publish', '--backup-dir', str(self.base / 'backup')), 2)
        self.assertFalse((self.base / 'backup').exists())
        (self.src / 'face.png').unlink()
        (self.src / '.env').write_text('SECRET=irrelevant')
        self.assertEqual(self.invoke(), 2)

    def test_incomplete_v297_source_clone_blocks_even_if_valid_git(self):
        (self.src / 'tests' / 'test_v297.py').unlink()
        self.assertEqual(self.invoke('--publish', '--backup-dir', str(self.base / 'backup')), 2)
        self.assertFalse((self.base / 'backup').exists())
        self.assertFalse(git(self.dest, 'branch', '--list', 'migration/full-local-source'))

    def test_fake_pilot_marker_blocks_before_any_upload(self):
        (self.src / 'CONTINUE_FULL_HINDI_NEURAL.bat').write_text('No pilot')
        self.assertEqual(self.invoke('--publish', '--backup-dir', str(self.base / 'backup')), 2)
        self.assertFalse((self.base / 'backup').exists())

    def test_unknown_source_or_wrong_clone_does_not_push(self):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(m.main(['--source', str(self.base / 'does-not-exist')]), 2)

    def test_shallow_repo_flag_rejects_before_publish(self):
        original = m.git
        def fake_git(path, *args, **kwargs):
            if args == ('rev-parse', '--is-shallow-repository'):
                return 'true'
            return original(path, *args, **kwargs)
        m.git = fake_git
        try:
            self.assertEqual(self.invoke('--publish', '--backup-dir', str(self.base / 'backup')), 2)
        finally:
            m.git = original

if __name__ == '__main__':
    unittest.main()