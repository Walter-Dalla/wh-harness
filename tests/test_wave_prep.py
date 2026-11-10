"""Tests for wave_prep.sh against a temporary repository with an integration worktree on impl/demo.

    python3 -m unittest tests.test_wave_prep
"""
import os
import re
import unittest

import tests.test_scripts as ts
from tests.test_scripts import git, run

WAVE_PREP = os.path.join(ts.SCRIPTS, 'wave_prep.sh')

LANE = """# f1 · demo · wave W2 · port — · ~50k tokens estimated
Context: x.
Owns: `src/*` (symbols apart). May touch the minimum of: `other/*`. Union: `union/*`.
Pair: —.
## demo-1 · item · internal
Item text.
Acceptance: `%s`.
"""

BOARD = """2026-01-01T00:00:00Z | orchestrator | WAVE | W1 base x
2026-01-01T00:01:00Z | a | CONTRACT | to=b: old interface
2026-01-01T00:02:00Z | orchestrator | WAVE | W2 base y
2026-01-01T00:03:00Z | a | END | DONE · 1 items · abc
"""

SECTIONS = ['## Acceptance at the tip', '## CONTRACT lines of the board', '## Moved files',
            '## Moved files inside a pending lane']


class WavePrepTest(unittest.TestCase):
    setUp_repo = ts.ScriptsTest.setUp
    tearDown = ts.ScriptsTest.tearDown
    write = ts.ScriptsTest.write

    def setUp(self):
        self.setUp_repo()
        with open(os.path.join(self.repo, '.git', 'info', 'exclude'), 'a', encoding='utf-8') as fh:
            fh.write('.impl/\n.claude/worktrees/\n')
        self.intwt = os.path.join(self.repo, '.claude', 'worktrees', 'impl-demo')
        git(self.repo, 'worktree', 'add', '-q', '-b', 'impl/demo', self.intwt, 'main')
        self.commit_in_intwt('notes.txt')
        self.lane('test -f never')
        self.write('.impl/demo/BOARD.md', BOARD)
        self.wave_file = os.path.join(os.path.realpath(self.repo), '.impl', 'demo', 'wave-W2.md')

    def lane(self, acceptance):
        self.write('.impl/demo/f1.md', LANE % acceptance)

    def commit_in_intwt(self, rel):
        path = os.path.join(self.intwt, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write('x\n')
        git(self.intwt, 'add', '-A')
        git(self.intwt, 'commit', '-q', '-m', rel)

    def prep(self, *lanes):
        return run(WAVE_PREP, self.repo, 'demo', 'W2', self.base, *(lanes or ('f1',)))

    def read_wave(self):
        with open(self.wave_file, encoding='utf-8') as fh:
            return fh.read()

    def test_clean_wave(self):
        code, out = self.prep()
        self.assertEqual(code, 0, out)
        self.assertEqual(out.splitlines(), [self.wave_file, 'WAVE CLEAN'])
        text = self.read_wave()
        tip = git(self.intwt, 'rev-parse', 'HEAD')
        self.assertEqual(text.splitlines()[0], '# WAVE W2 · demo · base %s · tip %s' % (self.base, tip))
        self.assertEqual(re.findall(r'^## .*$', text, re.M), SECTIONS)
        self.assertIn('### f1\ndemo-1 · exit 1 · test -f never\n', text)
        self.assertIn('## CONTRACT lines of the board\n—\n', text)
        self.assertIn('## Moved files\nA\tnotes.txt\n', text)
        self.assertTrue(text.endswith('## Moved files inside a pending lane\n—\n'), text)

    def test_green_item_calls_the_enricher(self):
        self.lane('true')
        code, out = self.prep()
        self.assertEqual(code, 3, out)
        self.assertEqual(out.splitlines()[-1],
                         'WAVE ENRICHER: 1 green item(s), 0 CONTRACT line(s), 0 owned file(s) moved')

    def test_contract_after_the_last_wave_line(self):
        with open(os.path.join(self.repo, '.impl', 'demo', 'BOARD.md'), 'a', encoding='utf-8') as fh:
            fh.write('2026-01-01T00:04:00Z | a | CONTRACT | to=f1: new interface\n')
        code, out = self.prep()
        self.assertEqual(code, 3, out)
        self.assertEqual(out.splitlines()[-1],
                         'WAVE ENRICHER: 0 green item(s), 1 CONTRACT line(s), 0 owned file(s) moved')
        text = self.read_wave()
        self.assertIn('new interface', text)
        self.assertNotIn('old interface', text)

    def test_board_without_wave_line_counts_every_contract(self):
        self.write('.impl/demo/BOARD.md', '2026-01-01T00:01:00Z | a | CONTRACT | to=b: one\n'
                                          '2026-01-01T00:02:00Z | a | CONTRACT | to=b: two\n')
        code, out = self.prep()
        self.assertEqual(code, 3, out)
        self.assertIn('2 CONTRACT line(s)', out)

    def test_owned_file_moved_and_union_file_ignored(self):
        self.commit_in_intwt('union/c.txt')
        code, out = self.prep()
        self.assertEqual(code, 0, out)
        self.commit_in_intwt('src/a.cs')
        code, out = self.prep()
        self.assertEqual(code, 3, out)
        self.assertEqual(out.splitlines()[-1],
                         'WAVE ENRICHER: 0 green item(s), 0 CONTRACT line(s), 1 owned file(s) moved')
        self.assertIn('## Moved files inside a pending lane\nf1 · OWN: src/a.cs\n', self.read_wave())

    def test_failures(self):
        code, out = self.prep('f1', 'f2')
        self.assertEqual(code, 1)
        self.assertTrue(out.startswith('WAVE_PREP FAILED:'), out)
        self.assertIn('f2.md', out)
        code, out = run(WAVE_PREP, self.repo, 'demo', 'W2', 'deadbeef', 'f1')
        self.assertEqual(code, 1)
        self.assertIn('WAVE_PREP FAILED: base deadbeef unknown', out)
        code, out = run(WAVE_PREP, self.repo, 'demo', '2', self.base, 'f1')
        self.assertEqual(code, 1)
        self.assertIn('WAVE_PREP FAILED:', out)


if __name__ == '__main__':
    unittest.main()
