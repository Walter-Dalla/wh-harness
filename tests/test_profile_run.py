"""Tests for profile_run.sh against a profile written by the test and against the demo fixture.

    python3 -m unittest tests.test_profile_run
"""
import os
import shutil
import tempfile
import unittest

from tests.test_scripts import ROOT, SCRIPTS, run

PROFILE_RUN = os.path.join(SCRIPTS, 'profile_run.sh')

PROFILE = """# Profile of /wh:implementation

## Commands
build: `echo built`
suite: `sh -c 'echo out; exit 3'` [inferred]
typecheck: —
service: `serve --port <port> --db x-<slug>`
health: `true`

## Build
—
"""


class ProfileRunTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.wt = os.path.join(self.tmp, 'wt')
        self.profile(PROFILE)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def profile(self, text):
        folder = os.path.join(self.wt, '.claude', 'profile')
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, 'implementation.md'), 'w', encoding='utf-8') as fh:
            fh.write(text)

    def test_build_runs_and_reports_exit_zero(self):
        code, out = run(PROFILE_RUN, self.tmp, 'build', self.wt)
        self.assertEqual(code, 0, out)
        self.assertEqual(out.splitlines(), ['built', 'PROFILE_RUN build: exit 0'])

    def test_suite_exit_code_is_the_commands(self):
        code, out = run(PROFILE_RUN, self.wt, 'suite')
        self.assertEqual(code, 3, out)
        self.assertEqual(out.splitlines()[-1], 'PROFILE_RUN suite: exit 3')
        self.assertIn('out', out.splitlines())

    def test_dash_value_is_skipped(self):
        code, out = run(PROFILE_RUN, self.tmp, 'typecheck', self.wt)
        self.assertEqual(code, 0, out)
        self.assertEqual(out, 'PROFILE_RUN typecheck: skipped\n')

    def test_print_replaces_port_and_slug(self):
        code, out = run(PROFILE_RUN, self.tmp, 'service', self.wt, '--print', '--port', '5101', '--slug', 'demo')
        self.assertEqual(code, 0, out)
        self.assertEqual(out, 'serve --port 5101 --db x-demo\n')

    def test_placeholder_left_without_option_fails(self):
        code, out = run(PROFILE_RUN, self.tmp, 'service', self.wt, '--print')
        self.assertEqual(code, 2)
        self.assertIn('PROFILE_RUN FAILED:', out)
        code, out = run(PROFILE_RUN, self.tmp, 'service', self.wt, '--print', '--port', '5101')
        self.assertEqual(code, 2)
        self.assertIn('--slug', out)

    def test_port_and_slug_are_validated(self):
        for opt, value in (('--port', '51&01'), ('--port', 'abc'), ('--slug', 'de&mo'), ('--slug', 'Demo_X'),
                           ('--slug', 'a b')):
            with self.subTest(option=opt, value=value):
                code, out = run(PROFILE_RUN, self.tmp, 'service', self.wt, '--print', '--port', '5101',
                                '--slug', 'demo', opt, value)
                self.assertEqual(code, 2, out)
                self.assertTrue(out.startswith('PROFILE_RUN FAILED: %s' % opt), out)

    def test_replacement_is_literal(self):
        self.profile('## Commands\nservice: `a <port> & b <slug>-<port> && c`\n')
        code, out = run(PROFILE_RUN, self.tmp, 'service', self.wt, '--print', '--port', '7', '--slug', 's-1')
        self.assertEqual(code, 0, out)
        self.assertEqual(out, 'a 7 & b s-1-7 && c\n')

    def test_unknown_key_fails(self):
        code, out = run(PROFILE_RUN, self.tmp, 'deploy', self.wt)
        self.assertEqual(code, 2)
        self.assertIn('PROFILE_RUN FAILED:', out)

    def test_profile_without_the_section_fails(self):
        self.profile('# Profile\n\n## Build\n`echo x`\n')
        code, out = run(PROFILE_RUN, self.tmp, 'build', self.wt)
        self.assertEqual(code, 2)
        self.assertIn('PROFILE_RUN FAILED:', out)
        self.assertIn('(/wh:profile implementation)', out)

    def test_missing_profile_fails(self):
        code, out = run(PROFILE_RUN, self.tmp, 'build', self.tmp)
        self.assertEqual(code, 2)
        self.assertIn('PROFILE_RUN FAILED:', out)

    def test_key_line_missing_or_malformed_fails(self):
        self.profile('## Commands\nbuild: echo no backticks\n\n## Tests\nsuite: `x`\n')
        code, out = run(PROFILE_RUN, self.tmp, 'build', self.wt)
        self.assertEqual(code, 2)
        self.assertIn('malformed', out)
        code, out = run(PROFILE_RUN, self.tmp, 'suite', self.wt)  # the line is in another section
        self.assertEqual(code, 2)
        self.assertIn('PROFILE_RUN FAILED:', out)

    def test_log_keeps_the_commands_output(self):
        log = os.path.join(self.tmp, 'suite.log')
        code, out = run(PROFILE_RUN, self.tmp, 'suite', self.wt, '--log', log)
        self.assertEqual(code, 3, out)
        with open(log, encoding='utf-8') as fh:
            self.assertEqual(fh.read(), 'out\n')

    def test_demo_fixture_suite(self):
        code, out = run(PROFILE_RUN, ROOT, 'suite', 'examples/demo', '--print')
        self.assertEqual(code, 0, out)
        self.assertEqual(out, 'dotnet test --nologo -v q\n')


if __name__ == '__main__':
    unittest.main()
