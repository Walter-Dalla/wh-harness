"""Tests for quick.sh (the /wh:quick light route) against a temporary repository with a bare remote.

    python3 -m unittest tests.test_quick
"""
import os
import shutil
import tempfile
import unittest

import tests.test_scripts as ts

QUICK = os.path.join(ts.ROOT, 'plugins', 'wh', 'skills', 'quick', 'scripts', 'quick.sh')
PROFILE = ('# Profile\n\n## Contract\nThe fixtures in `api/schema.json` and everything under `contracts/`, `dto/*.cs`, '
           '`src/*/Dto`, `tests/__snapshots__` and `proto`.\n\n## Tests\n`other/path.txt`\n')


class QuickTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.repo = os.path.join(self.tmp, 'repo')
        os.makedirs(self.repo)
        ts.git(self.repo, 'init', '-q', '-b', 'main', '.')
        self.remote = os.path.join(self.tmp, 'remote.git')
        ts.git(self.tmp, 'init', '-q', '--bare', '-b', 'main', self.remote)
        ts.git(self.repo, 'remote', 'add', 'origin', self.remote)
        for rel, text in (('src/a.txt', 'one\ntwo\n'), ('src/b.txt', 'b\n'), ('src/c.txt', 'c\n'), ('src/d.txt', 'd\n'),
                          ('api/schema.json', '{}\n'), ('contracts/x.txt', 'x\n'), ('dto/A.cs', 'a\n'),
                          ('other/path.txt', 'p\n'), ('src/Orders/Dto/O.cs', 'o\n'), ('tests/__snapshots__/a.snap', 's\n'),
                          ('proto/a.proto', 'p\n'), ('prototype.txt', 'p\n'), ('.claude/profile/implementation.md', PROFILE)):
            self.write(rel, text)
        ts.git(self.repo, 'add', '-A')
        ts.git(self.repo, 'commit', '-q', '-m', 'base files')
        ts.git(self.repo, 'push', '-q', 'origin', 'main')

    def write(self, rel, text='x\n'):
        path = os.path.join(self.repo, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(text)

    def start(self, slug='label'):
        code, out = ts.run(QUICK, self.repo, 'start', slug)
        self.assertEqual(code, 0, out)
        return dict(line.split('=', 1) for line in out.splitlines() if '=' in line)

    def edit(self, wt, rel, text):
        with open(os.path.join(wt, rel), 'w', encoding='utf-8') as fh:
            fh.write(text)

    def gate(self, wt, *args):
        return ts.run(QUICK, self.repo, 'gate', wt, *args)

    def test_start_creates_a_worktree_from_the_remote_main_without_touching_the_clone(self):
        self.write('dirty.txt')  # local change in the clone: allowed
        facts = self.start()
        wt = facts['WT']
        self.assertEqual(wt, os.path.join(os.path.realpath(self.repo), '.claude', 'worktrees', 'quick-label'))
        self.assertEqual(facts['BRANCH'], 'quick/label')
        self.assertEqual(facts['PROFILE'], 'ok')
        self.assertEqual(facts['BASE'], ts.git(self.repo, 'rev-parse', 'origin/main'))
        self.assertEqual(ts.git(wt, 'branch', '--show-current'), 'quick/label')
        self.assertEqual(ts.git(self.repo, 'branch', '--show-current'), 'main')
        self.assertTrue(os.path.exists(os.path.join(self.repo, 'dirty.txt')))
        code, out = ts.run(QUICK, self.repo, 'start', 'label')
        self.assertEqual(code, 1)
        self.assertIn('QUICK FAILED', out)
        code, out = ts.run(QUICK, self.repo, 'start', 'Bad Slug')
        self.assertEqual(code, 1)
        self.assertIn('not kebab-case', out)

    def test_gate_passes_a_small_edit_committed_or_not(self):
        wt = self.start()['WT']
        code, out = self.gate(wt)
        self.assertEqual(code, 1)
        self.assertIn('QUICK FAILED: no change', out)
        self.edit(wt, 'src/a.txt', 'one\nTWO\n')
        code, out = self.gate(wt)
        self.assertEqual((code, out.strip()), (0, 'QUICK OK: 1 file(s), 2 line(s)'))
        ts.git(wt, 'commit', '-q', '-am', 'label')
        code, out = self.gate(wt)
        self.assertEqual((code, out.strip()), (0, 'QUICK OK: 1 file(s), 2 line(s)'))

    def test_gate_escalates_on_size_new_file_and_contract_path(self):
        wt = self.start()['WT']
        for rel in ('src/a.txt', 'src/b.txt', 'src/c.txt', 'src/d.txt'):
            self.edit(wt, rel, 'changed\n')
        code, out = self.gate(wt)
        self.assertEqual(code, 3)
        self.assertIn('QUICK ESCALATE: 4 files (limit 3)', out)
        code, out = self.gate(wt, '--max-files', '4')
        self.assertEqual(code, 0, out)
        code, out = self.gate(wt, '--max-files', '4', '--max-lines', '5')
        self.assertEqual(code, 3)
        self.assertIn('changed lines (limit 5)', out)
        ts.git(wt, 'checkout', '-q', '.')
        self.edit(wt, 'src/new.txt', 'n\n')
        code, out = self.gate(wt)
        self.assertEqual(code, 3)
        self.assertIn('adds a file', out)
        os.remove(os.path.join(wt, 'src/new.txt'))
        for rel in ('api/schema.json', 'contracts/x.txt', 'dto/A.cs', 'src/Orders/Dto/O.cs', 'tests/__snapshots__/a.snap',
                    'proto/a.proto'):
            self.edit(wt, rel, 'z\n')
            code, out = self.gate(wt)
            self.assertEqual(code, 3, rel)
            self.assertIn('contract path (%s)' % rel, out)
            ts.git(wt, 'checkout', '-q', '.')
        self.edit(wt, 'other/path.txt', 'z\n')  # backticked in another section: not a contract path
        self.edit(wt, 'prototype.txt', 'z\n')   # `proto` is a folder token, not a name prefix
        code, out = self.gate(wt)
        self.assertEqual(code, 0, out)
        ts.git(wt, 'checkout', '-q', '.')
        os.chmod(os.path.join(wt, 'src/a.txt'), 0o755)
        code, out = self.gate(wt)
        self.assertEqual(code, 3, out)
        self.assertIn('changes a file mode or type', out)

    def test_finish_pushes_removes_the_worktree_and_prints_the_merge_command(self):
        wt = self.start()['WT']
        self.edit(wt, 'src/a.txt', 'one\nTWO\n')
        code, out = ts.run(QUICK, self.repo, 'finish', wt, PATH='/usr/bin:/bin')
        self.assertEqual(code, 1)
        self.assertIn('uncommitted changes', out)
        ts.git(wt, 'commit', '-q', '-am', 'quick: label')
        code, out = ts.run(QUICK, self.repo, 'finish', wt, GH_TOKEN='', PATH=self.path_without_gh())
        self.assertEqual(code, 0, out)
        self.assertIn('PR=none', out)
        self.assertIn('MERGE=git switch main && git merge --no-ff quick/label && git push origin main', out)
        self.assertIn('QUICK DONE', out)
        self.assertFalse(os.path.exists(wt))
        self.assertEqual(ts.git(self.repo, 'rev-parse', 'origin/quick/label'), ts.git(self.repo, 'rev-parse', 'quick/label'))
        self.assertEqual(ts.git(self.repo, 'branch', '--show-current'), 'main')

    def test_finish_refuses_to_push_an_escalated_change_and_drop_removes_it(self):
        wt = self.start()['WT']
        self.edit(wt, 'api/schema.json', '{"a": 1}\n')
        ts.git(wt, 'commit', '-q', '-am', 'quick: schema')
        code, out = ts.run(QUICK, self.repo, 'finish', wt, PATH=self.path_without_gh())
        self.assertEqual(code, 3)
        self.assertIn('QUICK ESCALATE: contract path (api/schema.json)', out)
        self.assertTrue(os.path.exists(wt))
        self.assertNotIn('quick/label', ts.git(self.repo, 'branch', '-r'))
        code, out = ts.run(QUICK, self.repo, 'drop', wt)
        self.assertEqual(code, 0, out)
        self.assertIn('QUICK DROPPED: quick/label', out)
        self.assertFalse(os.path.exists(wt))
        self.assertNotIn('quick/label', ts.git(self.repo, 'branch'))
        code, out = ts.run(QUICK, self.repo, 'drop', self.repo)  # the clone is on main: refused
        self.assertEqual(code, 1)
        self.assertIn("not a quick/* branch", out)

    def fake_gh(self, create_exit):
        """A PATH whose `gh` answers `repo view` and exits `create_exit` on `pr create`."""
        bindir = os.path.join(self.tmp, 'ghbin')
        os.makedirs(bindir, exist_ok=True)
        with open(os.path.join(bindir, 'gh'), 'w', encoding='utf-8') as fh:
            fh.write('#!/bin/sh\ncase "$1 $2" in\n"repo view") echo "{}"; exit 0 ;;\n"pr create") '
                     'if [ %d -eq 0 ]; then echo "https://example.test/pr/7"; else echo "GraphQL: boom" >&2; fi; exit %d ;;\n'
                     'esac\nexit 1\n' % (create_exit, create_exit))
        os.chmod(os.path.join(bindir, 'gh'), 0o755)
        return bindir + os.pathsep + os.environ['PATH']

    def test_finish_reports_the_pr_and_keeps_the_worktree_when_gh_fails(self):
        wt = self.start()['WT']
        self.edit(wt, 'src/a.txt', 'one\nTWO\n')
        ts.git(wt, 'commit', '-q', '-am', 'quick: label')
        code, out = ts.run(QUICK, self.repo, 'finish', wt, '--body', "it's `$HOME`", PATH=self.fake_gh(1))
        self.assertEqual(code, 1, out)
        self.assertIn('QUICK FAILED: gh pr create failed', out)
        self.assertIn('GraphQL: boom', out)
        self.assertNotIn('QUICK DONE', out)
        self.assertTrue(os.path.exists(wt))
        code, out = ts.run(QUICK, self.repo, 'finish', wt, PATH=self.fake_gh(0))
        self.assertEqual(code, 0, out)
        self.assertIn('PR=https://example.test/pr/7', out)
        self.assertNotIn('MERGE=', out)
        self.assertFalse(os.path.exists(wt))

    def test_drop_from_inside_the_worktree_and_start_inside_a_worktree(self):
        wt = self.start()['WT']
        code, out = ts.run(QUICK, wt, 'start', 'nested')
        self.assertEqual(code, 1)
        self.assertIn('main checkout', out)
        for slug in ('-x', 'x-', '--'):
            self.assertEqual(ts.run(QUICK, self.repo, 'start', slug)[0], 1, slug)
        code, out = ts.run(QUICK, wt, 'drop', wt)
        self.assertEqual(code, 0, out)
        self.assertFalse(os.path.exists(wt))
        self.assertNotIn('quick/label', ts.git(self.repo, 'branch'))

    def path_without_gh(self):
        """A PATH with git and the coreutils but no `gh`, so finish takes the no-PR branch."""
        bindir = os.path.join(self.tmp, 'bin')
        os.makedirs(bindir, exist_ok=True)
        for tool in ('git', 'bash', 'tail', 'dirname', 'mkdir', 'touch', 'grep', 'awk', 'tr', 'pwd'):
            src = shutil.which(tool)
            if src and not os.path.exists(os.path.join(bindir, tool)):
                os.symlink(src, os.path.join(bindir, tool))
        return bindir


if __name__ == '__main__':
    unittest.main()
