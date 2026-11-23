"""Tests for cdp.mjs (the dependency-free page driver of /wh:qa-visual) against a local HTML file.

Skipped where it cannot run: no `node`, a Node without the global WebSocket (before 22), or no Chromium.

    python3 -m unittest tests.test_cdp
"""
import json
import os
import shutil
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CDP = os.path.join(ROOT, 'plugins', 'wh', 'skills', 'qa-visual', 'scripts', 'cdp.mjs')

PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>t</title>
<style>body{margin:0}#far{margin-top:3000px;width:200px;height:80px}</style></head>
<body><h1 id="h">hello</h1><input id="name"><button id="go">go</button><form id="f"><input id="q"></form><p id="out"></p>
<div id="far">far</div>
<script>
document.getElementById('h').dataset.lang = localStorage.getItem('lang') || 'none';
document.getElementById('go').addEventListener('click', () => {
  document.getElementById('out').textContent = 'clicked ' + document.getElementById('name').value; });
document.getElementById('f').addEventListener('submit', (e) => { e.preventDefault();
  document.getElementById('out').textContent = 'submitted ' + document.getElementById('q').value; });
if (location.hash === '#boom') console.error('boom happened');
</script></body></html>
"""


def png_size(path):
    with open(path, 'rb') as fh:
        head = fh.read(24)
    assert head[:8] == b'\x89PNG\r\n\x1a\n', path
    return int.from_bytes(head[16:20], 'big'), int.from_bytes(head[20:24], 'big')


class CdpTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which('node'):
            raise unittest.SkipTest('no node')
        cls.tmp = tempfile.mkdtemp()
        with open(os.path.join(cls.tmp, 'page.html'), 'w', encoding='utf-8') as fh:
            fh.write(PAGE)
        cls.url = 'file://' + os.path.join(os.path.realpath(cls.tmp), 'page.html')
        code, out = cls.drive([{'goto': cls.url}])
        if code == 2 and ('no browser' in out or 'no global WebSocket' in out):
            shutil.rmtree(cls.tmp)
            raise unittest.SkipTest(out.strip())

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    @classmethod
    def drive(cls, steps, *args):
        path = os.path.join(cls.tmp, 'steps.json')
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump(steps, fh)
        p = subprocess.run(['node', CDP, path, *args], cwd=cls.tmp, capture_output=True, text=True, timeout=120)
        return p.returncode, p.stdout

    def test_drives_the_page_measures_and_takes_screenshots(self):
        code, out = self.drive([
            {'storage': {'lang': 'en'}},
            {'goto': self.url},
            {'eval': "document.getElementById('h').dataset.lang", 'expect': 'en'},
            {'eval': '[innerWidth, innerHeight]', 'expect': [390, 844]},
            {'eval': "matchMedia('(prefers-color-scheme: dark)').matches", 'expect': True},
            {'type': ['#name', 'Ana']},
            {'click': '#go', 'name': 'save'},
            {'eval': "document.getElementById('out').textContent", 'expect': 'clicked Ana'},
            {'type': ['#q', 'abc']},
            {'key': 'Enter'},
            {'wait': "document.getElementById('out').textContent === 'submitted abc'"},
            {'shot': 'shots/view.png'},
            {'shot': 'shots/far.png', 'selector': '#far'},
            {'size': '1440x900'},
            {'eval': 'innerWidth', 'expect': 1440},
        ], '--size', '390x844', '--scheme', 'dark')
        self.assertEqual(code, 0, out)
        lines = out.splitlines()
        self.assertEqual(lines[-1], 'CDP: 15 ok, 0 failed, 0 console error(s)')
        self.assertEqual(lines[6], 'OK 7 click [save] #go')
        self.assertEqual(lines[7], 'OK 8 eval document.getElementById(\'out\').textContent = "clicked Ana"')
        self.assertEqual(png_size(os.path.join(self.tmp, 'shots', 'view.png')), (390, 844))
        self.assertEqual(png_size(os.path.join(self.tmp, 'shots', 'far.png')), (200, 80))  # an element below the fold

    def test_a_failed_step_stops_the_run(self):
        code, out = self.drive([{'goto': self.url}, {'click': '#nope', 'timeout': 200}, {'eval': '1'}])
        self.assertEqual(code, 1, out)
        self.assertEqual(out.splitlines(), ['OK 1 goto ' + self.url, 'XX 2 click no element #nope after 200 ms',
                                            'CDP: 1 ok, 1 failed, 0 console error(s)'])
        code, out = self.drive([{'goto': self.url}, {'eval': '1 + 1', 'expect': 3}])
        self.assertEqual(code, 1, out)
        self.assertIn('XX 2 eval 1 + 1 = 2, expected 3', out)

    def test_console_errors_fail_the_run_unless_told_otherwise(self):
        steps = [{'goto': self.url + '#boom'}]
        code, out = self.drive(steps)
        self.assertEqual(code, 1, out)
        self.assertEqual(out.splitlines()[1:], ['CONSOLE console.error: boom happened', 'CDP: 1 ok, 0 failed, 1 console error(s)'])
        code, out = self.drive(steps, '--console', 'show')
        self.assertEqual(code, 0, out)
        self.assertIn('CONSOLE console.error: boom happened', out)
        code, out = self.drive(steps, '--console', 'ignore')
        self.assertEqual((code, out.splitlines()[-1]), (0, 'CDP: 1 ok, 0 failed, 0 console error(s)'))

    def test_bad_calls_fail_before_the_browser_starts(self):
        for steps, args, reason in (([{'goto': 'x', 'eval': '1'}], (), 'needs exactly one of'),
                                    ([], (), 'not a non-empty array'),
                                    ([{'eval': '1'}], ('--size', 'big'), "--size 'big' is not <W>x<H>"),
                                    ([{'eval': '1'}], ('--console', 'maybe'), '--console is fail, show or ignore'),
                                    ([{'eval': '1'}], ('--nope', '1'), 'unknown option --nope')):
            code, out = self.drive(steps, *args)
            self.assertEqual(code, 2, out)
            self.assertTrue(out.startswith('CDP FAILED: '), out)
            self.assertIn(reason, out)


if __name__ == '__main__':
    unittest.main()
