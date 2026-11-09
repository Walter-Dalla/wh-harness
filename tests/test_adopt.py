"""Tests for the adoption diagnostic (skills/adopt/scripts/check.py) against examples/demo and a bare directory.

    python3 -m unittest discover -s tests
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(ROOT, 'plugins', 'wh')
SCRIPT = os.path.join(PLUGIN, 'skills', 'adopt', 'scripts', 'check.py')
DEMO = os.path.join(ROOT, 'examples', 'demo')
SETTINGS = {'extraKnownMarketplaces': {'wh-harness': {'source': {'source': 'github', 'repo': 'Walter-Dalla/wh-harness'}}},
            'enabledPlugins': {'wh@wh-harness': True}}


def run(root, *extra):
    p = subprocess.run([sys.executable, '-I', SCRIPT, '--root', root, '--plugin-root', PLUGIN, '--json', *extra],
                       capture_output=True, text=True, env=dict(os.environ, WH_CACHE_DIR=tempfile.mkdtemp()))
    return p.returncode, {(it['item'], it['estado']) for it in json.loads(p.stdout)}, json.loads(p.stdout)


class ChecarTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def write(self, root, rel, text):
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(text)

    def test_bare_directory_lists_every_required_piece_as_missing(self):
        code, pares, itens = run(self.tmp)
        self.assertEqual(code, 1)
        for item in ('repo map', 'profile _common', 'profile implementation', 'context.json', 'settings.json'):
            self.assertIn((item, 'MISSING'), pares, item)
        self.assertNotIn(('glossario', 'MISSING'), pares)  # without context.json the sources are not required

    def test_demo_profiles_and_sources_are_ok_and_graph_builds(self):
        code, pares, itens = run(DEMO)
        for item in ('profile _common', 'profile implementation', 'context.json', 'glossario', 'features', 'indice_features', 'graph'):
            self.assertIn((item, 'OK'), pares, item)
        self.assertIn(('repo map', 'MISSING'), pares)
        self.assertIn(('settings.json', 'MISSING'), pares)
        grafo = next(it for it in itens if it['item'] == 'graph')
        self.assertIn('3 features', grafo['detalhe'])
        self.assertTrue(any(it['item'] == 'profile _common' and '[inferred]' in it['detalhe'] for it in itens))

    def copy_agents(self, repo):
        tpl_dir = os.path.join(PLUGIN, 'skills', 'adopt', 'templates', 'agents')
        for name in os.listdir(tpl_dir):
            with open(os.path.join(tpl_dir, name), encoding='utf-8') as fh:
                self.write(repo, '.claude/agents/' + name, fh.read())

    def test_complete_repo_exits_zero_and_flags_missing_sections_and_shadow_skill(self):
        repo = os.path.join(self.tmp, 'repo')
        shutil.copytree(DEMO, repo)
        self.write(repo, 'CLAUDE.md', '# mapa\n')
        self.write(repo, '.claude/settings.json', json.dumps(SETTINGS))
        self.write(repo, '.gitignore', '.codegraph/\n')
        self.copy_agents(repo)
        code, pares, _ = run(repo)
        self.assertEqual(code, 0, pares)
        self.assertIn(('settings.json', 'OK'), pares)
        self.assertIn(('.gitignore', 'OK'), pares)
        # a section short in the profile and an old skill shadowing
        common = os.path.join(repo, '.claude', 'profile', '_common.md')
        with open(common, encoding='utf-8') as fh:
            text = fh.read().replace('## Limits', '## Something else')
        with open(common, 'w', encoding='utf-8') as fh:
            fh.write(text)
        self.write(repo, '.claude/skills/implementation/SKILL.md', 'x')
        self.write(repo, '.claude/settings.json', json.dumps({'enabledPlugins': {}}))
        code, pares, itens = run(repo)
        self.assertEqual(code, 1)
        self.assertIn(('profile _common', 'MISSING'), pares)
        self.assertTrue(any(it['item'] == 'profile _common' and 'Limits' in it['detalhe'] for it in itens))
        self.assertIn(('old skill', 'WARN'), pares)
        self.assertTrue(any(it['item'] == 'settings.json' and 'extraKnownMarketplaces' in it['detalhe'] for it in itens))

    def test_agent_templates_missing_outdated_owner_and_ok(self):
        """Explore.md and Plan.md copied from skills/adopt/templates/agents/: MISSING, OUTDATED (older marker), WARN (no marker), OK."""
        repo = os.path.join(self.tmp, 'repo')
        shutil.copytree(DEMO, repo)
        self.write(repo, 'CLAUDE.md', '# map\n')
        self.write(repo, '.claude/settings.json', json.dumps(SETTINGS))
        self.write(repo, '.gitignore', '.codegraph/\n')
        tpl_dir = os.path.join(PLUGIN, 'skills', 'adopt', 'templates', 'agents')
        self.assertEqual(sorted(os.listdir(tpl_dir)), ['Explore.md', 'Plan.md'])
        code, pares, itens = run(repo)
        self.assertEqual(code, 1)
        missing = [it['detalhe'] for it in itens if it['item'] == 'agents' and it['estado'] == 'MISSING']
        self.assertEqual(len(missing), 2, itens)
        self.assertTrue(all('.claude/agents/' in d and '/wh:adopt agents' in d for d in missing), missing)
        # copies: OK, exit 0; an older marker: OUTDATED, exit 1; a file without marker: WARN, exit 0
        self.copy_agents(repo)
        code, pares, _ = run(repo)
        self.assertEqual(code, 0, pares)
        self.assertIn(('agents', 'OK'), pares)
        self.assertNotIn(('agents', 'MISSING'), pares)
        self.write(repo, '.claude/agents/Explore.md', '---\nname: Explore\n---\n<!-- wh-template: explore 0 -->\nold\n')
        code, pares, itens = run(repo)
        self.assertEqual(code, 1)
        self.assertTrue(any(it['item'] == 'agents' and it['estado'] == 'OUTDATED' and 'Explore.md' in it['detalhe'] for it in itens), itens)
        self.write(repo, '.claude/agents/Explore.md', '---\nname: Explore\n---\nmine\n')
        code, pares, itens = run(repo)
        self.assertEqual(code, 0, pares)
        self.assertTrue(any(it['item'] == 'agents' and it['estado'] == 'WARN' and "owner's" in it['detalhe'] for it in itens), itens)

    def test_links_warns_on_cited_paths_that_do_not_exist(self):
        repo = os.path.join(self.tmp, 'repo')
        shutil.copytree(DEMO, repo)
        self.write(repo, 'CLAUDE.md', 'Read `docs/GLOSSARY.md` and `docs/nope.md`; run `/wh:adopt`; glob `src/*`; url `https://x/y.md`.\n')
        code, pares, itens = run(repo)
        link = next(it for it in itens if it['item'] == 'links')
        self.assertEqual(link['estado'], 'WARN')
        self.assertIn('CLAUDE.md → docs/nope.md', link['detalhe'])
        for ok in ('GLOSSARY', '/wh:adopt', 'src/*', 'https'):
            self.assertNotIn(ok, link['detalhe'])
        self.write(repo, 'CLAUDE.md', 'Read `docs/GLOSSARY.md`.\n')
        for name in ('_common.md', 'implementation.md'):
            path = os.path.join(repo, '.claude', 'profile', name)
            with open(path, encoding='utf-8') as fh:
                text = fh.read()
            with open(path, 'w', encoding='utf-8') as fh:
                fh.write(re.sub(r'`[^`\s]*(?:/|\.md)[^`\s]*`', '`x`', text))
        code, pares, itens = run(repo)
        self.assertIn(('links', 'OK'), pares, [it for it in itens if it['item'] == 'links'])

    def test_agent_templates_have_frontmatter_marker_and_no_project_fact(self):
        tpl_dir = os.path.join(PLUGIN, 'skills', 'adopt', 'templates', 'agents')
        for name in os.listdir(tpl_dir):
            with open(os.path.join(tpl_dir, name), encoding='utf-8') as fh:
                text = fh.read()
            self.assertTrue(text.startswith('---\nname: %s\n' % name[:-3]), name)
            self.assertRegex(text, r'(?m)^description: .+$', name)
            self.assertRegex(text, r'(?m)^model: \w+$', name)
            self.assertRegex(text, r'<!-- wh-template: %s \d+ -->' % name[:-3].lower(), name)
            self.assertIn('.claude/profile/_common.md', text, name)
            self.assertNotIn('CLAUDE_PLUGIN_ROOT', text, name)  # the copy lives in the project, no plugin path there

    def test_invalid_context_json_is_reported_not_raised(self):
        repo = os.path.join(self.tmp, 'repo')
        self.write(repo, '.claude/profile/context.json', '{nope')
        code, pares, itens = run(repo)
        self.assertEqual(code, 1)
        self.assertTrue(any(it['item'] == 'context.json' and 'invalid JSON' in it['detalhe'] for it in itens))


if __name__ == '__main__':
    unittest.main()
