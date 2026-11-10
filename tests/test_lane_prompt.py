"""Tests for lane_prompt.sh against a temporary repository with a bare remote, plus the drift guard against the
prompt templates of LANES.md and SKILL.md.

    python3 -m unittest tests.test_lane_prompt
"""
import os
import re
import shutil
import unittest

import tests.test_scripts as ts
from tests.test_scripts import git, run

LANE_PROMPT = os.path.join(ts.SCRIPTS, 'lane_prompt.sh')
PLUGIN = os.path.dirname(os.path.dirname(os.path.dirname(ts.SCRIPTS)))
SKILL_DIR = os.path.join(ts.ROOT, 'plugins', 'wh', 'skills', 'implementation')
LANE = ts.LANE.replace('port —', 'port 5101')


def text_blocks(name):
    with open(os.path.join(SKILL_DIR, name), encoding='utf-8') as fh:
        return re.findall(r'```text\n(.*?)```', fh.read(), re.S)


def block_with(name, marker):
    found = [b for b in text_blocks(name) if marker in b]
    assert len(found) == 1, '%s: %d ```text blocks with %r' % (name, len(found), marker)
    return found[0]


def labels(text):
    return [re.split(r'[:=]', line, maxsplit=1)[0] for line in text.splitlines() if line.strip()]


class LanePromptTest(unittest.TestCase):
    setUp_repo = ts.ScriptsTest.setUp
    tearDown = ts.ScriptsTest.tearDown
    write = ts.ScriptsTest.write
    commit_all = ts.ScriptsTest.commit_all
    remote_with_lane = ts.ScriptsTest.remote_with_lane

    def setUp(self):
        self.setUp_repo()
        self.remote_with_lane()  # repo on impl/demo at the base; origin/impl/demo-f1 adds src/a.cs
        with open(os.path.join(self.repo, '.git', 'info', 'exclude'), 'a', encoding='utf-8') as fh:
            fh.write('.impl/\n')
        self.write('.impl/demo/f1.md', LANE)
        self.root = os.path.realpath(self.repo)
        self.impl = os.path.join(self.root, '.impl', 'demo')
        self.git = shutil.which('git')

    def prompt(self, *args):
        code, out = run(LANE_PROMPT, self.repo, 'demo', *args)
        self.assertEqual(code, 0, out)
        return out.splitlines()

    def test_lane_prompt(self):
        tip = git(self.repo, 'rev-parse', 'impl/demo')
        self.assertEqual(self.prompt('f1'), [
            'PLUGIN_ROOT=%s' % PLUGIN,
            'Lane: f1. File: %s/f1.md. Repo: %s. Profile: %s/.claude/profile/implementation.md and _common.md.'
            % (self.impl, self.root, self.root),
            'Branch: impl/demo-f1. Base: impl/demo @ %s. Remote: origin.' % tip,
            'Commands: profile § Worktree commands before the 1st command; git = %s -C <worktree> …, one command per call.'
            % self.git,
            'Port: 5101. Board: %s/BOARD.md.' % self.impl,
            'Retro: %s/retros/f1.md. Checkpoint: %s/progress/f1.md.' % (self.impl, self.impl),
            'Continuation: from scratch.',
        ])

    def test_lane_prompt_port_dash_and_continuation(self):
        self.write('.impl/demo/f1.md', ts.LANE)
        out = self.prompt('f1', '--continuation', 'checkpoint at progress/f1.md')
        self.assertEqual(out[4], 'Port: —. Board: %s/BOARD.md.' % self.impl)
        self.assertEqual(out[6], 'Continuation: checkpoint at progress/f1.md.')

    def test_code_qa_of_a_lane_writes_the_diff(self):
        out = self.prompt('f1', '--qa')
        tip = git(self.repo, 'rev-parse', 'origin/impl/demo-f1')
        diff = os.path.join(self.impl, 'qa', 'f1.diff')
        self.assertEqual(out, [
            'PLUGIN_ROOT=%s' % PLUGIN,
            'Mode: code. Task: demo. Repo: %s. Profile: %s/.claude/profile/implementation.md and _common.md. '
            'Plan: %s/PLAN.md. Lane: %s/f1.md.' % (self.root, self.root, self.impl, self.impl),
            'Branch: impl/demo-f1 @ %s. Diff base: %s. Remote: origin. Diff: %s.' % (tip, self.base, diff),
            'Output: %s/qa/f1.md. Retro: %s/retros/qa-f1.md.' % (self.impl, self.impl),
            'Commands: git = %s -C %s …, one command per call.' % (self.git, self.root),
            'Retest: no.',
        ])
        with open(diff, encoding='utf-8') as fh:
            text = fh.read()
        self.assertEqual(re.findall(r'^diff --git .*$', text, re.M), ['diff --git a/src/a.cs b/src/a.cs'])
        self.assertIn('+lane', text)

    def test_code_qa_retest(self):
        out = self.prompt('f1', '--qa', '--retest', 'QA-f1-01, QA-f1-02')
        self.assertEqual(out[-1], 'Retest: QA-f1-01, QA-f1-02.')

    def test_code_qa_of_a_small_task(self):
        self.write('src/b.cs', 'small\n')
        self.commit_all('demo-1: b')
        git(self.repo, 'push', '-q', 'origin', 'impl/demo')
        tip = git(self.repo, 'rev-parse', 'HEAD')
        out = self.prompt('code', '--qa')
        diff = os.path.join(self.impl, 'qa', 'code.diff')
        self.assertEqual(out[1:4], [
            'Mode: code. Task: demo. Repo: %s. Profile: %s/.claude/profile/implementation.md and _common.md. '
            'Plan: %s/PLAN.md. Lane: all.' % (self.root, self.root, self.impl),
            'Branch: impl/demo @ %s. Diff base: %s. Remote: origin. Diff: %s.' % (tip, self.base, diff),
            'Output: %s/qa/code.md. Retro: %s/retros/qa-code.md.' % (self.impl, self.impl),
        ])
        with open(diff, encoding='utf-8') as fh:
            self.assertEqual(re.findall(r'^diff --git .*$', fh.read(), re.M), ['diff --git a/src/b.cs b/src/b.cs'])

    def test_remote_and_main_options(self):
        remote = os.path.join(self.tmp, 'remote.git')
        git(self.repo, 'remote', 'add', 'up', remote)
        git(self.repo, 'switch', '-q', '-c', 'trunk', self.base)
        self.write('t.txt', 'trunk\n')
        self.commit_all('trunk moved')
        trunk = git(self.repo, 'rev-parse', 'HEAD')
        git(self.repo, 'switch', '-q', 'impl/demo')
        git(self.repo, 'merge', '-q', '--ff-only', 'trunk')
        self.write('src/b.cs', 'small\n')
        self.commit_all('demo-1: b')
        git(self.repo, 'push', '-q', 'up', 'impl/demo')
        tip = git(self.repo, 'rev-parse', 'HEAD')
        diff = os.path.join(self.impl, 'qa', 'code.diff')
        out = self.prompt('code', '--qa', '--remote', 'up', '--main', 'trunk')
        self.assertEqual(out[2], 'Branch: impl/demo @ %s. Diff base: %s. Remote: up. Diff: %s.' % (tip, trunk, diff))
        with open(diff, encoding='utf-8') as fh:
            self.assertEqual(re.findall(r'^diff --git .*$', fh.read(), re.M), ['diff --git a/src/b.cs b/src/b.cs'])
        out = self.prompt('code', '--qa', '--remote', 'up')  # default main: the diff base is where main stands
        self.assertIn('Diff base: %s. Remote: up.' % self.base, out[2])
        out = self.prompt('final', '--qa', '--remote', 'up', '--main', 'trunk')
        self.assertEqual(out[2], 'Branch: impl/demo @ %s. Diff base: trunk. Remote: up. Touched areas: none.' % tip)
        self.assertEqual(self.prompt('f1', '--remote', 'up')[2],
                         'Branch: impl/demo-f1. Base: impl/demo @ %s. Remote: up.' % tip)
        code, out = run(LANE_PROMPT, self.repo, 'demo', 'code', '--qa', '--remote', 'up', '--main', 'nobranch')
        self.assertEqual(code, 1)
        self.assertIn('LANE_PROMPT FAILED: ref nobranch missing', out)

    def test_final_qa(self):
        git(self.repo, 'push', '-q', 'origin', 'impl/demo')
        tip = git(self.repo, 'rev-parse', 'impl/demo')
        out = self.prompt('final', '--qa', '--areas', 'scripts', '--verify', 'QA-f1-01', '--gates', 'yes')
        self.assertEqual(out, [
            'PLUGIN_ROOT=%s' % PLUGIN,
            'Mode: final. Task: demo. Repo: %s. Profile: %s/.claude/profile/implementation.md and _common.md. '
            'Plan: %s/PLAN.md.' % (self.root, self.root, self.impl),
            'Branch: impl/demo @ %s. Diff base: main. Remote: origin. Touched areas: scripts.' % tip,
            'Output: %s/qa/final.md. Retro: %s/retros/qa-final.md.' % (self.impl, self.impl),
            'Commands: profile § Worktree commands before the 1st command; git = %s -C <worktree> …, one command per call.'
            % self.git,
            'Retest: no.',
            'Verify: QA-f1-01.',
            'Gates: yes.',
        ])
        self.assertFalse(os.path.exists(os.path.join(self.impl, 'qa', 'final.diff')))
        out = self.prompt('final', '--qa')
        self.assertEqual(out[2][-len('Touched areas: none.'):], 'Touched areas: none.')
        self.assertEqual(out[-2:], ['Verify: —.', 'Gates: no.'])

    def test_failures(self):
        for args in (('f2',), ('f2', '--qa'), ('f1', '--gates', 'maybe'), ('f1', '--retest')):
            code, out = run(LANE_PROMPT, self.repo, 'demo', *args)
            self.assertEqual(code, 1, args)
            self.assertTrue(out.startswith('LANE_PROMPT FAILED:'), out)
        os.makedirs(os.path.join(self.repo, 'sub'))
        code, out = run(LANE_PROMPT, os.path.join(self.repo, 'sub'), 'demo', 'f1')
        self.assertEqual(code, 1)
        self.assertIn('repository root', out)
        code, out = run(LANE_PROMPT, self.repo, 'demo', 'code', '--qa')  # origin/impl/demo was never pushed
        self.assertEqual(code, 1)
        self.assertIn('LANE_PROMPT FAILED: ref origin/impl/demo missing', out)

    def test_drift_guard_against_the_templates(self):
        git(self.repo, 'push', '-q', 'origin', 'impl/demo')
        for name, marker, args in (('LANES.md', '\nLane: <lane>', ('f1',)),
                                   ('SKILL.md', '\nMode: code.', ('f1', '--qa')),
                                   ('SKILL.md', '\nMode: final.', ('final', '--qa'))):
            with self.subTest(template=name, mode=args):
                self.assertEqual(labels('\n'.join(self.prompt(*args))), labels(block_with(name, marker)))


if __name__ == '__main__':
    unittest.main()
