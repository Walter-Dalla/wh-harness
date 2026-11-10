"""Tests for new_names.py: new identifiers of a diff checked against a glossary.

    python3 -m unittest tests.test_new_names
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from tests.test_scripts import git, GIT_ENV

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, 'plugins', 'wh', 'skills', 'implementation', 'scripts', 'new_names.py')

BEFORE = 'class Base:\n    existing_name = 0\n'
AFTER = BEFORE + '\n\nclass DisplayCase:\n    counter_total = 0\n    tmp_value = existing_name\n'
DIFF = """diff --git a/src/shop.py b/src/shop.py
index 1111111..2222222 100644
--- a/src/shop.py
+++ b/src/shop.py
@@ -1,2 +1,7 @@
 class Base:
     existing_name = 0
+
+
+class DisplayCase:
+    counter_total = 0
+    tmp_value = existing_name
"""
GLOSSARY = """# Glossary

## Any section

| Business | Code | Avoid / note |
|---|---|---|
| Counter | `Counter` | "display case" |
| Table / chair | `Table` / `Chair` | |
| Customer (anonymous customer) | NPC: `ActiveNpc`, `Npc` | "patron" for the anonymous one |

## Pitfalls

| In the code | Means | Why |
|---|---|---|
| `Entrace` | entrance / door | historical typo |
"""
EXPECTED = ['NEW NAMES: 2 without a glossary term (of 3)',
            'src/shop.py:5 DisplayCase · avoid → Counter',
            'src/shop.py:7 tmp_value']


class NewNamesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.diff = self.write('change.diff', DIFF)
        self.glossary = self.write('GLOSSARY.md', GLOSSARY)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def write(self, rel, text):
        path = os.path.join(self.tmp, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(text)
        return path

    def run_script(self, *args, cwd=None):
        p = subprocess.run([sys.executable, '-I', SCRIPT, *args], cwd=cwd or self.tmp, env=GIT_ENV,
                           capture_output=True, text=True, encoding='utf-8')
        return p.returncode, p.stdout.splitlines()

    def test_names_against_glossary(self):
        code, lines = self.run_script(self.diff, self.glossary)
        self.assertEqual(code, 0, lines)
        self.assertEqual(lines, EXPECTED)
        self.assertFalse(any('counter_total' in line for line in lines))
        self.assertFalse(any('existing_name' in line for line in lines))

    def test_no_glossary_lists_every_new_name(self):
        for glossary in ('—', os.path.join(self.tmp, 'absent.md')):
            code, lines = self.run_script(self.diff, glossary)
            self.assertEqual(code, 0, lines)
            self.assertEqual(lines, ['NO GLOSSARY: 3 new names', 'src/shop.py:5 DisplayCase',
                                     'src/shop.py:6 counter_total', 'src/shop.py:7 tmp_value'])

    def test_range_gives_the_same_list(self):
        repo = os.path.join(self.tmp, 'repo')
        os.makedirs(repo)
        git(repo, 'init', '-q', '-b', 'main', '.')
        self.write('repo/src/shop.py', BEFORE)
        git(repo, 'add', '-A')
        git(repo, 'commit', '-q', '-m', 'base')
        git(repo, 'checkout', '-q', '-b', 'impl/demo')
        self.write('repo/src/shop.py', AFTER)
        git(repo, 'commit', '-q', '-am', 'demo-1: display case')
        code, lines = self.run_script('--range', 'main...impl/demo', '--git', shutil.which('git'), self.glossary,
                                      cwd=repo)
        self.assertEqual(code, 0, lines)
        self.assertEqual(lines, EXPECTED)
        self.assertEqual(self.run_script('--range', 'main...nothing', self.glossary, cwd=repo)[0], 2)

    def test_comments_and_docstrings_are_not_names(self):
        body = ['"""Module prose about widgets.', '', 'More prose here.', '"""', '# hash comment words',
                '// slash comment words', '/* block comment', ' * star comment words', ' */',
                'def build_widget(size):  # trailing remark', '    """One line docstring prose."""',
                '    return size', "    label = '''inline", "    quoted prose'''", '    return label']
        text = '--- /dev/null\n+++ b/src/widget.py\n@@ -0,0 +1,%d @@\n' % len(body) + ''.join('+%s\n' % b for b in body)
        code, lines = self.run_script(self.write('new.diff', text), '—')
        self.assertEqual(code, 0, lines)
        self.assertEqual(lines, ['NO GLOSSARY: 5 new names', 'src/widget.py:10 def', 'src/widget.py:10 build_widget',
                                 'src/widget.py:10 size', 'src/widget.py:12 return', 'src/widget.py:13 label'])

    def test_cut_at_200(self):
        body = ''.join('+name_%03d = 1\n' % n for n in range(205))
        path = self.write('big.diff', '--- a/x.py\n+++ b/x.py\n@@ -0,0 +1,205 @@\n' + body)
        code, lines = self.run_script(path, '—')
        self.assertEqual(code, 0)
        self.assertEqual(lines[0], 'NO GLOSSARY: 205 new names')
        self.assertEqual(len(lines), 202)
        self.assertEqual(lines[-1], '… 5 more')

    def test_missing_diff_and_bad_call_exit_2(self):
        code, lines = self.run_script(os.path.join(self.tmp, 'absent.diff'), self.glossary)
        self.assertEqual(code, 2)
        self.assertTrue(lines[0].startswith('NEW_NAMES FAILED: '), lines)
        self.assertEqual(self.run_script(self.diff)[0], 2)


if __name__ == '__main__':
    unittest.main()
