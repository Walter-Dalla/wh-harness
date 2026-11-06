"""Tests for escopo.sh and preflight.sh against a temporary git repository.

    python3 -m unittest discover -s tests
"""
import os
import shutil
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, 'plugins', 'wh', 'skills', 'implementation', 'scripts')
ESCOPO = os.path.join(SCRIPTS, 'escopo.sh')
PREFLIGHT = os.path.join(SCRIPTS, 'preflight.sh')
GIT_ENV = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t', GIT_COMMITTER_NAME='t',
               GIT_COMMITTER_EMAIL='t@t', HOME=tempfile.gettempdir())

LANE = """# f1 · demo · onda W1 · porta — · ~100k tokens estimados
Contexto: x.
Dono de: `src/*` (símbolos à parte). Pode tocar o mínimo de: `other/*`. União: `union/*`.
Par: —.
## demo-1 · item · interno
Texto do item que cita `lixo.cs` e Pode tocar `qualquer/coisa` sem contar.
"""


def git(cwd, *args):
    return subprocess.run(['git', *args], cwd=cwd, env=GIT_ENV, capture_output=True, text=True, check=True).stdout.strip()


def run(script, cwd, *args, **env):
    p = subprocess.run(['bash', script, *args], cwd=cwd, env=dict(GIT_ENV, **env), capture_output=True, text=True)
    return p.returncode, p.stdout


class ScriptsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.repo = os.path.join(self.tmp, 'repo')
        os.makedirs(self.repo)
        git(self.repo, 'init', '-q', '-b', 'main', '.')
        git(self.repo, 'commit', '-q', '--allow-empty', '-m', 'base')
        self.base = git(self.repo, 'rev-parse', 'HEAD')

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def lane(self, text=LANE):
        path = os.path.join(self.tmp, 'faixa.md')  # fora do repo, como .impl/ (excluído do git)
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(text)
        return path

    def write(self, rel, text='x\n'):
        path = os.path.join(self.repo, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(text)

    def commit_all(self, msg='x'):
        git(self.repo, 'add', '-A')
        git(self.repo, 'commit', '-q', '-m', msg)

    # ---- escopo.sh

    def test_escopo_separates_owned_touchable_union_and_outside(self):
        for f in ('src/a.cs', 'other/b.cs', 'union/c.txt', 'lixo.cs'):
            self.write(f)
        self.commit_all()
        code, out = run(ESCOPO, self.repo, self.lane(), self.base)
        self.assertEqual(code, 1)
        self.assertIn('FORA: lixo.cs', out)
        self.assertIn('AVISO esperado: other/b.cs', out)
        self.assertNotIn('FORA: other/b.cs', out)
        self.assertNotIn('union/c.txt', out)
        self.assertNotIn('src/a.cs', out)

    def test_escopo_ok_when_everything_is_owned(self):
        self.write('src/a.cs')
        self.write('src/deep/b.cs')
        self.commit_all()
        code, out = run(ESCOPO, self.repo, self.lane(), self.base)
        self.assertEqual(code, 0, out)
        self.assertIn('ESCOPO OK: 2 arquivos', out)

    def test_escopo_fails_without_owned_paths(self):
        code, out = run(ESCOPO, self.repo, self.lane('# f\nDono de: nada entre crases\n'), self.base)
        self.assertEqual(code, 2)
        self.assertIn('ESCOPO FALHOU', out)

    # ---- preflight.sh

    def exclude_progress(self):
        with open(os.path.join(self.repo, '.git', 'info', 'exclude'), 'a', encoding='utf-8') as fh:
            fh.write('.impl/\n')

    def test_preflight_refuses_the_main_checkout(self):
        self.exclude_progress()
        code, out = run(PREFLIGHT, self.repo, '--base', self.base)
        self.assertEqual(code, 1)
        self.assertIn('checkout principal', out)

    def test_preflight_ok_in_a_fresh_agent_worktree(self):
        self.exclude_progress()
        self.write('.impl/demo/faixa.md', LANE)
        self.write('.impl/demo/QUADRO.md', '')
        wt = os.path.join(self.tmp, 'wt')
        git(self.repo, 'worktree', 'add', '-q', '-b', 'worktree-agent-abc', wt, 'main')
        code, out = run(PREFLIGHT, wt, '--base', self.base, '--branch', 'impl/demo-f1',
                        '--lane', os.path.join(self.repo, '.impl', 'demo', 'faixa.md'), '--protected', 'release/*')
        self.assertEqual(code, 0, out)
        self.assertIn('PREFLIGHT OK', out)

    def test_preflight_accepts_a_custom_agent_branch_prefix(self):
        self.exclude_progress()
        wt = os.path.join(self.tmp, 'wt')
        git(self.repo, 'worktree', 'add', '-q', '-b', 'agent-xyz', wt, 'main')
        code, out = run(PREFLIGHT, wt, '--base', self.base)
        self.assertEqual(code, 1)
        self.assertIn("não é worktree-agent-*", out)
        code, out = run(PREFLIGHT, wt, '--base', self.base, WH_AGENT_BRANCH_PREFIX='agent-')
        self.assertEqual(code, 0, out)

    def test_preflight_reports_each_problem(self):
        wt = os.path.join(self.tmp, 'wt')
        git(self.repo, 'worktree', 'add', '-q', '-b', 'worktree-agent-abc', wt, 'main')
        with open(os.path.join(wt, 'sujo.txt'), 'w') as fh:
            fh.write('x')
        code, out = run(PREFLIGHT, wt, '--base', 'deadbeef', '--branch', 'main',
                        '--lane', os.path.join(self.tmp, 'nao-existe.md'))
        self.assertEqual(code, 1)
        for msg in ('protegida: main', 'alterações locais', 'base deadbeef não existe', 'faixa ilegível',
                    '.impl/ não é ignorado'):
            self.assertIn(msg, out)

    def agent_worktree(self, name='wt', branch='worktree-agent-abc'):
        wt = os.path.join(self.tmp, name)
        git(self.repo, 'worktree', 'add', '-q', '-b', branch, wt, 'main')
        return wt

    def test_preflight_accepts_impl_ignored_by_gitignore(self):
        self.write('.gitignore', '.impl/\n')
        self.commit_all()
        code, out = run(PREFLIGHT, self.agent_worktree(), '--base', self.base)
        self.assertEqual(code, 0, out)

    def test_preflight_reports_an_option_without_value(self):
        code, out = run(PREFLIGHT, self.repo, '--base')
        self.assertEqual(code, 2)
        self.assertIn('PREFLIGHT FALHOU: --base sem valor', out)

    def test_preflight_outside_a_git_repository(self):
        code, out = run(PREFLIGHT, self.tmp, '--base', self.base, GIT_CEILING_DIRECTORIES=os.path.dirname(self.tmp))
        self.assertEqual(code, 1)
        self.assertIn('fora de um repositório git', out)

    def test_preflight_port_dash_is_skipped_and_busy_port_fails(self):
        import socket
        self.exclude_progress()
        wt = self.agent_worktree()
        code, out = run(PREFLIGHT, wt, '--base', self.base, '--port', '—')
        self.assertEqual(code, 0, out)
        self.assertNotIn('ocupada', out)
        with socket.socket() as srv:
            srv.bind(('127.0.0.1', 0))
            srv.listen(1)
            port = str(srv.getsockname()[1])
            code, out = run(PREFLIGHT, wt, '--base', self.base, '--port', port)
        if 'PREFLIGHT AVISO' in out:  # máquina sem ss nem lsof
            self.assertEqual(code, 0, out)
        else:
            self.assertEqual(code, 1, out)
            self.assertIn('porta %s ocupada' % port, out)

    def test_continuation_agent_takes_the_lane_branch_after_the_old_worktree_is_released(self):
        """FAIXAS.md §3.9: a worktree antiga segura a branch; liberada, o agente novo passa no preflight e a renomeia."""
        self.exclude_progress()
        old = self.agent_worktree('old', 'worktree-agent-old')
        git(old, 'branch', '-m', 'impl/demo-f1')
        new = self.agent_worktree('new', 'worktree-agent-new')
        held = subprocess.run(['git', 'branch', '-m', 'impl/demo-f1'], cwd=new, env=GIT_ENV, capture_output=True, text=True)
        self.assertNotEqual(held.returncode, 0)
        git(self.repo, 'worktree', 'remove', '--force', old)
        git(self.repo, 'branch', '-D', 'impl/demo-f1')
        code, out = run(PREFLIGHT, new, '--base', self.base, '--branch', 'impl/demo-f1')
        self.assertEqual(code, 0, out)
        git(new, 'branch', '-m', 'impl/demo-f1')
        self.assertEqual(git(new, 'branch', '--show-current'), 'impl/demo-f1')

    # ---- escopo.sh: caminhos difíceis

    def test_escopo_accepts_glob_characters_non_ascii_and_spaces(self):
        lane = self.lane('# f\nDono de: `app/[id]/page.tsx` `docs/revisão.md` `com espaço/*`. União: —.\n## i\n')
        for f in ('app/[id]/page.tsx', 'docs/revisão.md', 'com espaço/a b.txt'):
            self.write(f)
        self.commit_all()
        code, out = run(ESCOPO, self.repo, lane, self.base)
        self.assertEqual(code, 0, out)
        self.assertIn('ESCOPO OK: 3 arquivos', out)
        self.write('fora.txt')
        self.commit_all()
        code, out = run(ESCOPO, self.repo, lane, self.base)
        self.assertEqual(code, 1)
        self.assertIn('FORA: fora.txt', out)

    def test_escopo_without_union_or_touchable_lines(self):
        self.write('src/a.cs')
        self.write('union/c.txt')
        self.commit_all()
        code, out = run(ESCOPO, self.repo, self.lane('# f\nDono de: `src/*`.\n## i\n'), self.base)
        self.assertEqual(code, 1)
        self.assertIn('FORA: union/c.txt', out)
        self.assertNotIn('src/a.cs', out)


if __name__ == '__main__':
    unittest.main()
