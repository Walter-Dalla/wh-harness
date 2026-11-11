"""Tests for agent_cost.py against fabricated session transcripts.

    python3 -m unittest tests.test_agent_cost
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

import tests.test_scripts as ts

AGENT_COST = os.path.join(ts.SCRIPTS, 'agent_cost.py')


def assistant(msg_id, model, inp, write, read, out, long_write=0):
    return json.dumps({'type': 'assistant', 'message': {'id': msg_id, 'model': model, 'usage': {
        'input_tokens': inp, 'cache_creation_input_tokens': write, 'cache_read_input_tokens': read, 'output_tokens': out,
        'cache_creation': {'ephemeral_1h_input_tokens': long_write, 'ephemeral_5m_input_tokens': write - long_write},
        'service_tier': 'standard'}}})


class AgentCostTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.cwd = os.path.join(self.tmp, 'my.repo')
        os.makedirs(self.cwd)
        self.projects = os.path.join(self.tmp, 'projects')
        self.folder = os.path.join(self.projects, re.sub(r'[^A-Za-z0-9]', '-', os.path.realpath(self.cwd)))
        os.makedirs(os.path.join(self.folder, 's-1', 'subagents'))

    def put(self, rel, lines):
        with open(os.path.join(self.folder, rel), 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(lines) + '\n')

    def cost(self, *args):
        p = subprocess.run([sys.executable, '-I', AGENT_COST, *args], capture_output=True, text=True)
        return p.returncode, p.stdout

    def test_table_counts_each_message_once_and_ranks_by_weighted_tokens(self):
        self.put('s-1.jsonl', [
            json.dumps({'type': 'user', 'message': {'content': 'the word "usage" in a user line'}}),
            assistant('m1', 'claude-opus-5-5', 10, 100, 0, 5),
            assistant('m1', 'claude-opus-5-5', 10, 100, 0, 20),   # same message, later block: the last usage wins
            assistant('m2', 'claude-opus-5-5', 5, 0, 1000, 10),
            assistant('m3', '<synthetic>', 999, 999, 999, 999),
            'not json "usage"',
        ])
        self.put('s-1/subagents/agent-a1.jsonl', [assistant('x1', 'claude-sonnet-5-5', 1, 2000, 0, 400)])
        self.put('s-1/subagents/agent-a1.meta.json', [json.dumps({'agentType': 'wh:impl-qa', 'description': 'final | QA'})])
        self.put('s-1/subagents/agent-a2.jsonl', [json.dumps({'type': 'user'})])   # no request: no row
        code, out = self.cost('--session', 's-1', '--cwd', self.cwd, '--projects', self.projects)
        self.assertEqual(code, 0, out)
        rows = out.strip().splitlines()
        self.assertEqual(rows[0], '| Agent | Model | Requests | Input | Cache write | Cache read | Output | Share |')
        # qa: 1 + 2500 + 0 + 2000 = 4501; orchestrator: 15 + 125 + 100 + 150 = 390
        self.assertEqual(rows[2], '| wh:impl-qa · final / QA | claude-sonnet-5-5 | 1 | 1 | 2000 | 0 | 400 | 92% |')
        self.assertEqual(rows[3], '| orchestrator (main session) | claude-opus-5-5 | 2 | 15 | 100 | 1000 | 30 | 8% |')
        self.assertEqual(rows[4], '| Total | | 3 | 16 | 2100 | 1000 | 430 | 100% |')
        self.assertEqual(len(rows), 5)

    def test_a_one_hour_cache_write_weighs_double(self):
        self.put('s-1.jsonl', [assistant('m1', 'claude-opus-5-5', 0, 1000, 0, 0)])                  # 1250
        self.put('s-1/subagents/agent-a1.jsonl', [assistant('x1', 'claude-opus-5-5', 0, 1000, 0, 0, long_write=1000)])  # 2000
        code, out = self.cost('--session', 's-1', '--cwd', self.cwd, '--projects', self.projects)
        self.assertEqual(code, 0, out)
        rows = out.strip().splitlines()
        self.assertTrue(rows[2].startswith('| a1 |') and rows[2].endswith('| 62% |'), rows[2])
        self.assertTrue(rows[3].endswith('| 38% |'), rows[3])

    def test_failures(self):
        code, out = self.cost('--session', 'nope', '--cwd', self.cwd, '--projects', self.projects)
        self.assertEqual(code, 2)
        self.assertIn('AGENT_COST FAILED: no transcript at', out)
        code, out = self.cost('--cwd', self.cwd)
        self.assertEqual(code, 2)
        self.assertIn('AGENT_COST FAILED: --session', out)
        code, out = self.cost('--session', '../x', '--projects', self.projects)
        self.assertEqual(code, 2)


if __name__ == '__main__':
    unittest.main()
