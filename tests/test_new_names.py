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
        for name, value in (('color.ui', 'always'), ('diff.noprefix', 'true'), ('diff.mnemonicPrefix', 'true')):
            git(repo, 'config', name, value)  # the script's git output must not depend on user config
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
        self.assertEqual(lines, ['NO GLOSSARY: 2 new names', 'src/widget.py:10 build_widget',
                                 'src/widget.py:13 label'])

    def test_only_declared_names(self):
        files = {
            'src/cart.py': ['import os', 'class Cart:', '    total_due: int = 0', '    def add_item(self, price, qty=1):',
                            '        self.last_price = price', '        print(len(price))', '        return sorted(items)',
                            '        if total_due == 0:', '            run_report(verbose=True,', '                flag_value=1)',
                            '        counter += 1'],
            'web/app.ts': ['export function loadData(url) {', 'const MAX_ROWS = 10;', 'let rowCount = 0;',
                           'interface RowShape { id: number }', 'type RowId = number;', 'enum Mode { On, Off }',
                           'export default class Store {}', 'console.log(rowCount);', 'this.cache = new Map();'],
            'bin/tool.sh': ['build_all() {', 'OUT_DIR=build', '  local count=0', '  echo "$OUT_DIR"', '  grep -n foo bar',
                            '      OWN:*|MAY:*) owned+="$lane · $line"$\'\\n\' ;;'],
            'srv/main.go': ['func (s *Server) ServeHTTP(w, r) {', 'type Handler struct {}'],
            'core/lib.rs': ['pub fn parse_line(text: &str) {', 'pub struct Token;', 'let mut cursor = 0;'],
            'App/Order.cs': ['public sealed record Order(int Id);'],
        }
        text = ''
        for path, body in files.items():
            text += '--- /dev/null\n+++ b/%s\n@@ -0,0 +1,%d @@\n' % (path, len(body)) + ''.join('+%s\n' % b for b in body)
        code, lines = self.run_script(self.write('decl.diff', text), '—')
        self.assertEqual(code, 0, lines)
        self.assertEqual(lines, [
            'NO GLOSSARY: 21 new names',
            'src/cart.py:2 Cart', 'src/cart.py:3 total_due', 'src/cart.py:4 add_item', 'src/cart.py:5 last_price',
            'web/app.ts:1 loadData', 'web/app.ts:2 MAX_ROWS', 'web/app.ts:3 rowCount', 'web/app.ts:4 RowShape',
            'web/app.ts:5 RowId', 'web/app.ts:6 Mode', 'web/app.ts:7 Store', 'web/app.ts:9 cache',
            'bin/tool.sh:1 build_all', 'bin/tool.sh:2 OUT_DIR', 'bin/tool.sh:3 count',
            'srv/main.go:1 ServeHTTP', 'srv/main.go:2 Handler',
            'core/lib.rs:1 parse_line', 'core/lib.rs:2 Token', 'core/lib.rs:3 cursor',
            'App/Order.cs:1 Order'])

    def test_markdown_and_lockfiles_are_skipped(self):
        parts = []
        for path in ('docs/guide.md', 'package-lock.json', 'web/yarn.lock', 'pnpm-lock.yaml', 'poetry.lock',
                     'Cargo.lock', 'go.sum', 'src/real.py'):
            parts.append('--- /dev/null\n+++ b/%s\n@@ -0,0 +1,2 @@\n+%s_one = 1\n+\n' % (path, path.replace('/', '_')
                                                                                        .replace('.', '_')
                                                                                        .replace('-', '_')))
        code, lines = self.run_script(self.write('mixed.diff', ''.join(parts)), '—')
        self.assertEqual(code, 0, lines)
        self.assertEqual(lines, ['NO GLOSSARY: 1 new names', 'src/real.py:1 src_real_py_one'])

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
