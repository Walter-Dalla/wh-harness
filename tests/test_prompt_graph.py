"""Tests for the prompt-graph hook, run against examples/demo with a fake CodeGraph database.

    python3 -m unittest discover -s tests
"""
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, 'plugins', 'wh', 'scripts', 'prompt_graph.py')
DEMO = os.path.join(ROOT, 'examples', 'demo')
sys.path.insert(0, os.path.dirname(SCRIPT))
import prompt_graph as pg  # noqa: E402

NODES = [
    ('OrderService', 'class', 'src/Orders/OrderService.cs', 12),
    ('OrderService', 'class', 'tests/Orders/OrderServiceTests.cs', 3),
    ('Order', 'class', 'src/Orders/Order.cs', 5),
    ('PickupSlot', 'struct', 'src/Orders/PickupSlot.cs', 1),
    ('BakeSchedule', 'class', 'src/Stock/BakeSchedule.cs', 20),
    ('Shelf', 'class', 'src/Stock/Shelf.cs', 8),
    ('StampCard', 'class', 'src/Loyalty/StampCard.cs', 4),
]

EXPECTED_SHOWCASE = '\n'.join([
    '[wh:prompt-graph] Deterministic context (glossary + features + CodeGraph); pointers only, verify before asserting.',
    'Avoid "showcase": the term is Shelf (finished goods for sale) (`Shelf`, `ShelfStock`)',
    'Terms: Order = `Order`, `OrderService`',
    'Read: docs/features/stock.md (Pantry, shelf and baking) · docs/features/orders.md (Orders and pickup)',
    'Symbols: Order src/Orders/Order.cs:5 · BakeSchedule src/Stock/BakeSchedule.cs:20'
    ' · OrderService src/Orders/OrderService.cs:12 · Shelf src/Stock/Shelf.cs:8 · PickupSlot src/Orders/PickupSlot.cs:1',
])


class PromptGraphTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.repo = os.path.join(self.tmp, 'repo')
        shutil.copytree(DEMO, self.repo)
        os.makedirs(os.path.join(self.repo, '.codegraph'))
        con = sqlite3.connect(os.path.join(self.repo, '.codegraph', 'codegraph.db'))
        con.execute('CREATE TABLE nodes (name TEXT, kind TEXT, file_path TEXT, start_line INTEGER)')
        con.executemany('INSERT INTO nodes VALUES (?, ?, ?, ?)', NODES)
        con.commit()
        con.close()
        self.env = dict(os.environ, WH_CACHE_DIR=os.path.join(self.tmp, 'cache'))
        pg.CACHE_DIR = self.env['WH_CACHE_DIR']

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def query(self, prompt):
        cfg = pg.load_cfg(self.repo)
        return pg.render(pg.load_graph(self.repo, cfg), cfg, prompt)

    def hook(self, prompt, cwd=None, **env):
        event = json.dumps({'prompt': prompt, 'cwd': cwd or self.repo})
        out = subprocess.run([sys.executable, '-I', SCRIPT], input=event, capture_output=True, text=True,
                             env=dict(self.env, **env), check=True)
        return out.stdout

    def test_normalization_folds_accents_case_and_plurals(self):
        self.assertEqual(pg.tokens('Balcões, Mesas e PORÇÕES'), ['balcao', 'mesa', 'e', 'porcao'])
        self.assertEqual(pg.tokens('StampCards'), ['stampcard'])

    def test_full_output_is_deterministic(self):
        prompt = 'the showcase shows a sold out croissant but the order still goes through'
        self.assertEqual(self.query(prompt), EXPECTED_SHOWCASE)
        self.assertEqual(self.query(prompt), EXPECTED_SHOWCASE)

    def test_avoided_synonym_points_to_the_term_and_its_feature(self):
        out = self.query('customers want a coupon after ten stamps')
        self.assertIn('Avoid "coupon": the term is Free item reward (`Reward`)', out)
        self.assertIn('Read: docs/features/loyalty.md (Loyalty stamps)', out)
        self.assertIn('StampCard src/Loyalty/StampCard.cs:4', out)

    def test_symbol_prefers_source_over_tests(self):
        self.assertIn('OrderService src/Orders/OrderService.cs:12', self.query('refactor OrderService'))

    def test_prompt_without_domain_words_injects_nothing(self):
        self.assertEqual(self.query('deploy the README changes and run the tests'), '')

    def test_hook_emits_additional_context(self):
        data = json.loads(self.hook('the pickup slot is wrong for late orders'))
        ctx = data['hookSpecificOutput']['additionalContext']
        self.assertEqual(data['hookSpecificOutput']['hookEventName'], 'UserPromptSubmit')
        self.assertIn('docs/features/orders.md', ctx)

    def test_hook_is_silent_without_config_short_prompt_or_opt_out(self):
        os.remove(os.path.join(self.repo, '.claude', 'perfil', 'contexto.json'))
        self.assertEqual(self.hook('the pickup slot is wrong for late orders'), '')
        shutil.copytree(DEMO, self.repo, dirs_exist_ok=True)
        self.assertEqual(self.hook('orders'), '')
        self.assertEqual(self.hook('the pickup slot is wrong for late orders', WH_PROMPT_GRAPH='0'), '')

    def test_hook_finds_config_from_a_subdirectory(self):
        sub = os.path.join(self.repo, 'src', 'deep')
        os.makedirs(sub)
        self.assertIn('orders.md', self.hook('the pickup slot is wrong for late orders', cwd=sub))

    def test_hook_is_silent_with_invalid_config(self):
        with open(os.path.join(self.repo, '.claude', 'perfil', 'contexto.json'), 'w', encoding='utf-8') as fh:
            fh.write('{nope')
        self.assertEqual(self.hook('the pickup slot is wrong for late orders'), '')

    def test_hook_works_without_a_writable_cache(self):
        blocker = os.path.join(self.tmp, 'arquivo')
        with open(blocker, 'w') as fh:
            fh.write('x')
        out = self.hook('the pickup slot is wrong for late orders', WH_CACHE_DIR=os.path.join(blocker, 'cache'))
        self.assertIn('docs/features/orders.md', json.loads(out)['hookSpecificOutput']['additionalContext'])

    def test_corrupted_cache_is_rebuilt(self):
        self.assertIn('orders.md', self.query('the pickup slot is wrong for late orders'))
        for name in os.listdir(pg.CACHE_DIR):
            with open(os.path.join(pg.CACHE_DIR, name), 'w') as fh:
                fh.write('{"sig": ')
        self.assertIn('orders.md', self.query('the pickup slot is wrong for late orders'))

    def test_cache_rebuilds_when_a_source_changes(self):
        self.assertEqual(self.query('a croissant recipe'), '')
        path = os.path.join(self.repo, 'docs', 'features', 'README.md')
        with open(path, 'a', encoding='utf-8') as fh:
            fh.write('| [stock.md](stock.md) | Pantry | croissant |\n')
        os.utime(path, ns=(1, 1))
        self.assertIn('docs/features/stock.md', self.query('a croissant recipe'))


if __name__ == '__main__':
    unittest.main()


class PromptGraphLimitsTest(PromptGraphTest):
    def test_max_chars_keeps_whole_lines(self):
        cfg = pg.load_cfg(self.repo)
        full = pg.render(pg.load_graph(self.repo, cfg), cfg, 'the showcase shows a sold out croissant but the order still goes through')
        cfg['max_chars'] = len(full.split('\n')[0]) + 1 + len(full.split('\n')[1]) + 5
        out = pg.render(pg.load_graph(self.repo, cfg), cfg, 'the showcase shows a sold out croissant but the order still goes through')
        self.assertEqual(out.split('\n')[:2], full.split('\n')[:2])
        self.assertLessEqual(len(out), cfg['max_chars'])
        self.assertEqual(len(out.split('\n')), 2)  # the third line does not fit, so it is dropped, not cut mid-word

    def test_class_name_globs_resolve_godot_scripts(self):
        os.makedirs(os.path.join(self.repo, 'client', 'ui'))
        with open(os.path.join(self.repo, 'client', 'ui', 'stamp_card.gd'), 'w', encoding='utf-8') as fh:
            fh.write('extends Control\nclass_name StampCardView\n')
        cfg_path = os.path.join(self.repo, '.claude', 'perfil', 'contexto.json')
        with open(cfg_path, encoding='utf-8') as fh:
            cfg = json.load(fh)
        cfg['class_name_globs'] = ['client/**/*.gd']
        with open(cfg_path, 'w', encoding='utf-8') as fh:
            json.dump(cfg, fh)
        loyalty = os.path.join(self.repo, 'docs', 'features', 'loyalty.md')
        with open(loyalty, encoding='utf-8') as fh:
            text = fh.read()
        with open(loyalty, 'w', encoding='utf-8') as fh:
            fh.write(text.replace('## Entry symbols\n', '## Entry symbols\n\nClient: `StampCardView`.\n', 1))
        cfg = pg.load_cfg(self.repo)
        graph = pg.load_graph(self.repo, cfg)
        self.assertEqual(graph['simbolos']['StampCardView'], 'client/ui/stamp_card.gd:1')
        self.assertIn('StampCardView client/ui/stamp_card.gd:1', pg.render(graph, cfg, 'the stamp card rewards a free item'))
