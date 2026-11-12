"""The flow page (site/flow.html) cites only plugin files, skills, agents and scripts that exist.

- every literal `plugins/wh/...` path (globs allowed) matches a file;
- every row of the "Plugin wh" group of the file tree (`[id, prefix, "a · b.md"]`) names existing files;
  a name without an extension takes the extension of the row's last name;
- every `wh:<skill>` is a skill, every `impl-<name>` agent is an agent, every `x.sh` / `x.py` is a plugin script;
- every text written in one language (`pt:`) has the other (`en:`), and the Pages workflow publishes both paths.

    python3 -m unittest discover -s tests
"""
import glob
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(ROOT, 'plugins', 'wh')
PAGE = os.path.join(ROOT, 'site', 'flow.html')


def page():
    with open(PAGE, encoding='utf-8') as fh:
        return fh.read()


def exists(rel):
    return bool(glob.glob(os.path.join(ROOT, rel)))


def tree_paths(text):
    """Repo paths of the rows of the "plugin" group of GROUPS."""
    start = text.index('{id:"plugin"')
    group = text[start:text.index(']]}', start)]
    out = []
    for prefix, names in re.findall(r'\["\w+","([^"]*)","([^"]*)"\]', group):
        base = prefix if prefix.startswith('plugins/') else 'plugins/wh/' + prefix
        parts = [n.strip() for n in names.split('·')]
        ext = os.path.splitext(parts[-1])[1]
        out += [base + (n if os.path.splitext(n)[1] else n + ext) for n in parts]
    return out


class SiteRefsTest(unittest.TestCase):
    def setUp(self):
        self.text = page()

    def test_literal_plugin_paths_exist(self):
        paths = set(re.findall(r'plugins/wh/[\w./*-]+', self.text))
        self.assertTrue(paths)
        self.assertEqual([p for p in sorted(paths) if not exists(p.rstrip('/'))], [])

    def test_plugin_tree_rows_exist(self):
        paths = tree_paths(self.text)
        self.assertGreater(len(paths), 10)
        self.assertEqual([p for p in paths if not exists(p)], [])

    def test_skills_exist(self):
        # `[wh:prompt-graph]` is the hook's output block, not a skill.
        names = set(re.findall(r'(?<![\[\w])wh:([a-z][a-z-]*)', self.text))
        self.assertIn('implementation', names)
        missing = [n for n in sorted(names) if not os.path.isfile(os.path.join(PLUGIN, 'skills', n, 'SKILL.md'))]
        self.assertEqual(missing, [])

    def test_agents_exist(self):
        names = set(re.findall(r'\b(impl-[a-z]+)\b(?!-)', self.text))
        self.assertIn('impl-dev', names)
        missing = [n for n in sorted(names) if not os.path.isfile(os.path.join(PLUGIN, 'agents', n + '.md'))]
        self.assertEqual(missing, [])

    def test_scripts_exist(self):
        names = set(re.findall(r'\b([a-z][\w-]*\.(?:sh|py))\b', self.text))
        self.assertIn('board.sh', names)
        on_disk = {os.path.basename(p) for p in glob.glob(os.path.join(PLUGIN, '**', '*.*'), recursive=True)}
        self.assertEqual(sorted(names - on_disk), [])

    def test_both_languages(self):
        # Texts are `{pt:..., en:...}` pairs (or one `pt:{...}` / `en:{...}` block each).
        pt = len(re.findall(r'[{,\s]pt:', self.text))
        self.assertGreater(pt, 50)
        self.assertEqual(pt, len(re.findall(r'[{,\s]en:', self.text)))
        with open(os.path.join(ROOT, '.github', 'workflows', 'pages.yml'), encoding='utf-8') as fh:
            workflow = fh.read()
        self.assertIn('for lang in pt en', workflow)
        self.assertIn('cp site/flow.html "_site/$lang/index.html"', workflow)


if __name__ == '__main__':
    unittest.main()
