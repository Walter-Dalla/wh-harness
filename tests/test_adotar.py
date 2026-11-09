"""Tests for the adoption diagnostic (skills/adotar/scripts/checar.py) against examples/demo and a bare directory.

    python3 -m unittest discover -s tests
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(ROOT, 'plugins', 'wh')
SCRIPT = os.path.join(PLUGIN, 'skills', 'adotar', 'scripts', 'checar.py')
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
        for item in ('mapa do repo', 'perfil _comum', 'perfil implementation', 'contexto.json', 'settings.json'):
            self.assertIn((item, 'FALTA'), pares, item)
        self.assertNotIn(('glossario', 'FALTA'), pares)  # sem contexto.json as fontes não são cobradas

    def test_demo_profiles_and_sources_are_ok_and_graph_builds(self):
        code, pares, itens = run(DEMO)
        for item in ('perfil _comum', 'perfil implementation', 'contexto.json', 'glossario', 'features', 'indice_features', 'grafo'):
            self.assertIn((item, 'OK'), pares, item)
        self.assertIn(('mapa do repo', 'FALTA'), pares)
        self.assertIn(('settings.json', 'FALTA'), pares)
        grafo = next(it for it in itens if it['item'] == 'grafo')
        self.assertIn('3 features', grafo['detalhe'])
        self.assertTrue(any(it['item'] == 'perfil _comum' and '[inferido]' in it['detalhe'] for it in itens))

    def test_complete_repo_exits_zero_and_flags_missing_sections_and_shadow_skill(self):
        repo = os.path.join(self.tmp, 'repo')
        shutil.copytree(DEMO, repo)
        self.write(repo, 'CLAUDE.md', '# mapa\n')
        self.write(repo, '.claude/settings.json', json.dumps(SETTINGS))
        self.write(repo, '.gitignore', '.codegraph/\n')
        code, pares, _ = run(repo)
        self.assertEqual(code, 0, pares)
        self.assertIn(('settings.json', 'OK'), pares)
        self.assertIn(('.gitignore', 'OK'), pares)
        # seção a menos no perfil e skill antiga sombreando
        comum = os.path.join(repo, '.claude', 'perfil', '_comum.md')
        with open(comum, encoding='utf-8') as fh:
            text = fh.read().replace('## Limites', '## Outra coisa')
        with open(comum, 'w', encoding='utf-8') as fh:
            fh.write(text)
        self.write(repo, '.claude/skills/implementation/SKILL.md', 'x')
        self.write(repo, '.claude/settings.json', json.dumps({'enabledPlugins': {}}))
        code, pares, itens = run(repo)
        self.assertEqual(code, 1)
        self.assertIn(('perfil _comum', 'FALTA'), pares)
        self.assertTrue(any(it['item'] == 'perfil _comum' and 'Limites' in it['detalhe'] for it in itens))
        self.assertIn(('skill antiga', 'AVISO'), pares)
        self.assertTrue(any(it['item'] == 'settings.json' and 'extraKnownMarketplaces' in it['detalhe'] for it in itens))

    def test_invalid_contexto_json_is_reported_not_raised(self):
        repo = os.path.join(self.tmp, 'repo')
        self.write(repo, '.claude/perfil/contexto.json', '{nope')
        code, pares, itens = run(repo)
        self.assertEqual(code, 1)
        self.assertTrue(any(it['item'] == 'contexto.json' and 'JSON inválido' in it['detalhe'] for it in itens))


if __name__ == '__main__':
    unittest.main()
