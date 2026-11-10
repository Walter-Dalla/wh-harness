"""Tests for cleanup_inventory.py against a temporary git repository.

    python3 -m unittest tests.test_cleanup_inventory
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from tests.test_scripts import git, GIT_ENV

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, 'plugins', 'wh', 'skills', 'cleanup', 'scripts', 'cleanup_inventory.py')

PLAN = """# Demo plan
| Id | Item | Lane | Acceptance |
|---|---|---|---|
| demo-1 | rename | a | `true` |
| demo-2 | other | a | `true` |
"""
GUIDE = """# Guide

The helper `legacy_total` sums the rows.
Old module: src/gone.py.
"""


class CleanupInventoryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.repo = os.path.join(self.tmp, 'repo')
        os.makedirs(self.repo)
        git(self.repo, 'init', '-q', '-b', 'main', '.')
        self.write('src/old.py', 'def old_entry():\n    return 1\n')
        self.write('src/gone.py', 'GONE_FLAG = 1\n')
        self.write('src/calc.py', 'def legacy_total():\n    return 0\n\n\ndef keep_total():\n    return 1\n')
        self.write('docs/guide.md', GUIDE)
        self.commit_all('base')
        git(self.repo, 'checkout', '-q', '-b', 'impl/demo')
        git(self.repo, 'mv', 'src/old.py', 'src/new.py')
        git(self.repo, 'rm', '-q', 'src/gone.py')
        self.commit_all('demo-1: rename')
        self.write('src/calc.py', 'def keep_total():\n    return 1\n')
        self.commit_all('chore: x')
        git(self.repo, 'checkout', '-q', 'main')
        self.write('.impl/demo/PLAN.md', PLAN)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def write(self, rel, text):
        path = os.path.join(self.repo, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(text)

    def commit_all(self, msg):
        git(self.repo, 'add', '-A', '--', ':!.impl')
        git(self.repo, 'commit', '-q', '-m', msg)

    def run_script(self, *args):
        p = subprocess.run([sys.executable, '-I', SCRIPT, *args], cwd=self.repo, env=GIT_ENV,
                           capture_output=True, text=True)
        return p.returncode, p.stdout.splitlines()

    def short(self, rev):
        return git(self.repo, 'log', '-1', '--format=%h', rev)

    def block(self, lines, heading):
        start = lines.index(heading) + 1
        heads = ('ITEMS', 'COMMITS WITHOUT ITEM', 'OLD PATHS', 'OLD NAMES')
        end = next((i for i in range(start, len(lines)) if lines[i] in heads), len(lines))
        return lines[start:end]

    def test_inventory_blocks(self):
        code, lines = self.run_script('demo')
        self.assertEqual(code, 0, lines)
        heads = ['ITEMS', 'COMMITS WITHOUT ITEM', 'OLD PATHS', 'OLD NAMES']
        self.assertEqual([line for line in lines if line in heads], heads)
        self.assertEqual(self.block(lines, 'ITEMS'),
                         ['demo-1 · 1 commit(s) · %s' % self.short('impl/demo~1'), 'demo-2 · NO COMMIT'])
        self.assertEqual(self.block(lines, 'COMMITS WITHOUT ITEM'), ['%s chore: x' % self.short('impl/demo')])
        self.assertEqual(self.block(lines, 'OLD PATHS'),
                         ['src/gone.py (D) · docs/guide.md:4', 'src/old.py (R → src/new.py) · not cited'])
        self.assertEqual(self.block(lines, 'OLD NAMES'), ['legacy_total · docs/guide.md:3'])

    def test_missing_plan_still_runs(self):
        code, lines = self.run_script('demo', '--plan', os.path.join(self.tmp, 'nope.md'))
        self.assertEqual(code, 0, lines)
        self.assertEqual(lines[1], '— (no plan at %s)' % os.path.join(self.tmp, 'nope.md'))
        self.assertEqual(len(self.block(lines, 'COMMITS WITHOUT ITEM')), 2)
        self.assertIn('OLD NAMES', lines)

    def test_unknown_ref_exits_2(self):
        code, lines = self.run_script('demo', '--ref', 'impl/nothing')
        self.assertEqual(code, 2)
        self.assertTrue(lines[0].startswith('CLEANUP_INVENTORY FAILED: '), lines)

    def test_bad_call_and_non_repository_exit_2(self):
        self.assertEqual(self.run_script()[0], 2)
        self.assertEqual(self.run_script('demo', '--root', self.tmp)[0], 2)


if __name__ == '__main__':
    unittest.main()
