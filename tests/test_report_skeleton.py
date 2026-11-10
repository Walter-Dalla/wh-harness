"""Tests for report_skeleton.py against a fixture `.impl/demo/` folder.

    python3 -m unittest tests.test_report_skeleton
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, 'plugins', 'wh', 'skills', 'implementation')
SCRIPT = os.path.join(SKILL, 'scripts', 'report_skeleton.py')
REPORT = os.path.join(SKILL, 'REPORT.md')

FILES = {
    'PLAN.md': '# Demo plan\n\n| Id | Item |\n|---|---|\n| demo-1 | x |\n',
    'BOARD.md': (
        '2026-11-10T10:00:00Z | a | START | abc1234\n'
        '2026-11-10T10:05:00Z | a | WARNING | demo-1: touched other/b.py\n'
        '2026-11-10T10:06:00Z | b | HUMAN | demo-2: token only the owner has; done: the rest\n'
        '2026-11-10T10:10:00Z | a | END | DONE · 1 items · def5678\n'
        '2026-11-10T10:11:00Z | b | END | HUMAN_DECISION · 1 items · 0123abc\n'),
    'qa/code.md': (
        '# QA · code\n\n| Id | Type | Severity | Where | Evidence | Fix |\n|---|---|---|---|---|---|\n'
        '| QA-a-01 | bug | high | `src/a.py:3` | off by one | fix the range |\n'
        '| QA-a-02 | name | low | `src/a.py:9` | `tmp` | rename |\n'),
    'agent_chat/01-a-demo-1.md': (
        '# Chat 01 · a demo-1 · 2026-11-10T10:01:00Z\n\n## Question (a)\n\nShould the parser accept tabs?\n'),
    'agent_chat/02-b-demo-2.md': (
        '# Chat 02 · b demo-2 · 2026-11-10T10:02:00Z\n\n## Question (b)\n\n' + 'Q' * 130 + '\n'
        '\n## Answer (impl-enrich) · impact: item · 2026-11-10T10:03:00Z\n\nFirst answer.\n'
        '\n## Answer (orchestrator) · impact: lane · 2026-11-10T10:04:00Z\n\nSecond answer wins.\n'),
    'retros/a.md': (
        '# Retro · a · 2026-11-10\n'
        '| # | Severity | Category | Evidence (what happened, command/file) | Proposal (file and change) | Who applies |\n'
        '|---|---|---|---|---|---|\n'
        '| 1 | low | docs | readme stale | Fix the readme | repo |\n'
        '| 2 | medium | tools | guard refused heredoc | Document the guard | repo |\n'),
    'retros/b.md': (
        '# Retro · b · 2026-11-10\n'
        '| # | Severity | Category | Evidence (what happened, command/file) | Proposal (file and change) | Who applies |\n'
        '|---|---|---|---|---|---|\n'
        '| 1 | High |  tools | heredoc refused again |  Document the guard  | owner |\n'
        '| 2 | low | docs | guide stale | Fix the guide | repo |\n'),
}


def report_headings():
    with open(REPORT, encoding='utf-8') as fh:
        text = fh.read()
    block = re.search(r'^## Report.*?```markdown\n(.*?)```', text, re.S | re.M).group(1)
    return [line for line in block.splitlines() if line.startswith('## ')]


class ReportSkeletonTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        for rel, text in FILES.items():
            path = os.path.join(self.tmp, '.impl', 'demo', rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as fh:
                fh.write(text)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_script(self, *args):
        p = subprocess.run([sys.executable, '-I', SCRIPT, 'demo', '--root', self.tmp, *args],
                           capture_output=True, text=True, encoding='utf-8')
        return p.returncode, p.stdout

    def test_headings_follow_report_md(self):
        code, out = self.run_script('--pr', 'none')
        self.assertEqual(code, 0, out)
        headings = report_headings()
        self.assertEqual(headings[0], '## Errors')
        self.assertEqual([line for line in out.splitlines() if line.startswith('## ')], headings)

    def test_title_lanes_errors_and_open_items(self):
        lines = self.run_script('--pr', 'github')[1].splitlines()
        self.assertEqual(lines[0], '# Demo plan · impl/demo · PR on GitHub')
        self.assertEqual(lines[1:4], ['Lanes:', 'a: DONE · 1 items · def5678', 'b: HUMAN_DECISION · 1 items · 0123abc'])
        self.assertIn('a: demo-1: touched other/b.py', lines)
        self.assertIn('b: demo-2: token only the owner has; done: the rest', lines)
        self.assertEqual(self.run_script()[1].splitlines()[0], '# Demo plan · impl/demo · TODO(orchestrator): PR')

    def test_consultations(self):
        lines = self.run_script()[1].splitlines()
        start = lines.index('## Consultations')
        self.assertEqual(lines[start + 1:start + 3], [
            'a demo-1 · Should the parser accept tabs? · unanswered',
            'b demo-2 · %s… · Second answer wins. · impact lane · orchestrator' % ('Q' * 120)])

    def test_qa_rows_verbatim(self):
        lines = self.run_script()[1].splitlines()
        start = lines.index('## QA')
        self.assertEqual(lines[start + 1], '| Id | Type | Severity | Where | Evidence | Fix |')
        self.assertEqual(lines[start + 3:start + 5], [
            '| QA-a-01 | bug | high | `src/a.py:3` | off by one | fix the range |',
            '| QA-a-02 | name | low | `src/a.py:9` | `tmp` | rename |'])

    def test_retro_merges_exact_duplicates_only(self):
        lines = self.run_script()[1].splitlines()
        rows = lines[lines.index('## Consolidated retro') + 3:]
        self.assertEqual(rows, [
            '| 1 | High | tools | a: guard refused heredoc / b: heredoc refused again | Document the guard | repo |',
            '| 2 | low | docs | a: readme stale | Fix the readme | repo |',
            '| 3 | low | docs | b: guide stale | Fix the guide | repo |'])

    def test_out_writes_the_same_text(self):
        out_path = os.path.join(self.tmp, 'report.md')
        stdout = self.run_script('--pr', 'none')[1]
        code, _ = self.run_script('--pr', 'none', '--out', out_path)
        self.assertEqual(code, 0)
        with open(out_path, encoding='utf-8') as fh:
            self.assertEqual(fh.read(), stdout)

    def test_missing_sources_become_todo(self):
        shutil.rmtree(os.path.join(self.tmp, '.impl', 'demo', 'retros'))
        os.remove(os.path.join(self.tmp, '.impl', 'demo', 'BOARD.md'))
        code, out = self.run_script()
        self.assertEqual(code, 0, out)
        self.assertIn('TODO(orchestrator): no BOARD.md', out)
        self.assertIn('TODO(orchestrator): no retros/ folder', out)

    def test_missing_folder_and_bad_call_exit_2(self):
        p = subprocess.run([sys.executable, '-I', SCRIPT, 'nothing', '--root', self.tmp], capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)
        self.assertTrue(p.stdout.startswith('REPORT_SKELETON FAILED: '), p.stdout)
        self.assertEqual(self.run_script('--pr', 'gitlab')[0], 2)


if __name__ == '__main__':
    unittest.main()
