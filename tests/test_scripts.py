"""Tests for scope.sh and preflight.sh against a temporary git repository.

    python3 -m unittest discover -s tests
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, 'plugins', 'wh', 'skills', 'implementation', 'scripts')
SCOPE = os.path.join(SCRIPTS, 'scope.sh')
PREFLIGHT = os.path.join(SCRIPTS, 'preflight.sh')
MERGE = os.path.join(SCRIPTS, 'merge_lane.sh')
ENV = os.path.join(SCRIPTS, 'impl_env.sh')
BOARD = os.path.join(SCRIPTS, 'board.sh')
ACCEPT = os.path.join(SCRIPTS, 'acceptance.py')
CLEANUP = os.path.join(SCRIPTS, 'cleanup_worktrees.sh')
GIT_ENV = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t', GIT_COMMITTER_NAME='t',
               GIT_COMMITTER_EMAIL='t@t', HOME=tempfile.gettempdir())

LANE = """# f1 · demo · wave W1 · port — · ~100k tokens estimated
Context: x.
Owns: `src/*` (symbols apart). May touch the minimum of: `other/*`. Union: `union/*`.
Pair: —.
## demo-1 · item · internal
Item text that cites `lixo.cs` and May touch `qualquer/coisa` without counting.
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
        path = os.path.join(self.tmp, 'faixa.md')  # outside the repo, like .impl/ (excluded from git)
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

    # ---- scope.sh

    def test_scope_separates_owned_touchable_union_and_outside(self):
        for f in ('src/a.cs', 'other/b.cs', 'union/c.txt', 'lixo.cs'):
            self.write(f)
        self.commit_all()
        code, out = run(SCOPE, self.repo, self.lane(), self.base)
        self.assertEqual(code, 1)
        self.assertIn('OUTSIDE: lixo.cs', out)
        self.assertIn('WARNING expected: other/b.cs', out)
        self.assertNotIn('OUTSIDE: other/b.cs', out)
        self.assertNotIn('union/c.txt', out)
        self.assertNotIn('src/a.cs', out)

    def test_scope_ok_when_everything_is_owned(self):
        self.write('src/a.cs')
        self.write('src/deep/b.cs')
        self.commit_all()
        code, out = run(SCOPE, self.repo, self.lane(), self.base)
        self.assertEqual(code, 0, out)
        self.assertIn('SCOPE OK: 2 files', out)

    def test_scope_fails_without_owned_paths(self):
        code, out = run(SCOPE, self.repo, self.lane('# f\nOwns: nothing in backticks\n'), self.base)
        self.assertEqual(code, 2)
        self.assertIn('SCOPE FAILED', out)

    # ---- preflight.sh

    def exclude_progress(self):
        with open(os.path.join(self.repo, '.git', 'info', 'exclude'), 'a', encoding='utf-8') as fh:
            fh.write('.impl/\n')

    def test_preflight_refuses_the_main_checkout(self):
        self.exclude_progress()
        code, out = run(PREFLIGHT, self.repo, '--base', self.base)
        self.assertEqual(code, 1)
        self.assertIn('main checkout', out)

    def test_preflight_ok_in_a_fresh_agent_worktree(self):
        self.exclude_progress()
        self.write('.impl/demo/faixa.md', LANE)
        self.write('.impl/demo/BOARD.md', '')
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
        self.assertIn("is not worktree-agent-*", out)
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
        for msg in ('protected: main', 'local changes', 'base deadbeef does not exist', 'lane file unreadable',
                    '.impl/ is not ignored'):
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
        self.assertIn('PREFLIGHT FAILED: --base without a value', out)

    def test_preflight_outside_a_git_repository(self):
        code, out = run(PREFLIGHT, self.tmp, '--base', self.base, GIT_CEILING_DIRECTORIES=os.path.dirname(self.tmp))
        self.assertEqual(code, 1)
        self.assertIn('outside a git repository', out)

    def test_preflight_port_dash_is_skipped_and_busy_port_fails(self):
        import socket
        self.exclude_progress()
        wt = self.agent_worktree()
        code, out = run(PREFLIGHT, wt, '--base', self.base, '--port', '—')
        self.assertEqual(code, 0, out)
        self.assertNotIn('busy', out)
        with socket.socket() as srv:
            srv.bind(('127.0.0.1', 0))
            srv.listen(1)
            port = str(srv.getsockname()[1])
            code, out = run(PREFLIGHT, wt, '--base', self.base, '--port', port)
        if 'PREFLIGHT WARNING' in out:  # machine without ss or lsof
            self.assertEqual(code, 0, out)
        else:
            self.assertEqual(code, 1, out)
            self.assertIn('port %s busy' % port, out)

    def test_continuation_agent_takes_the_lane_branch_after_the_old_worktree_is_released(self):
        """LANES.md §3.9: the old worktree holds the branch; once freed, the new agent passes the preflight and renames it."""
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

    # ---- merge_lane.sh

    def remote_with_lane(self):
        """Bare remote with main and impl/demo-f1 (one commit on src/a.cs); the repo on impl/demo at the base."""
        remote = os.path.join(self.tmp, 'remote.git')
        git(self.tmp, 'init', '-q', '--bare', '-b', 'main', remote)
        git(self.repo, 'remote', 'add', 'origin', remote)
        git(self.repo, 'push', '-q', 'origin', 'main')
        git(self.repo, 'switch', '-q', '-c', 'impl/demo-f1')
        self.write('src/a.cs', 'lane\n')
        self.commit_all('demo-1: a')
        git(self.repo, 'push', '-q', '-u', 'origin', 'impl/demo-f1')
        git(self.repo, 'switch', '-q', '-c', 'impl/demo', self.base)
        return remote

    def test_merge_lane_merges_only_on_the_integration_branch(self):
        self.remote_with_lane()
        git(self.repo, 'switch', '-q', 'main')
        code, out = run(MERGE, self.tmp, self.repo, 'demo', 'f1', 'origin')
        self.assertEqual(code, 1)
        self.assertIn("MERGE REFUSED: %s is on 'main', not impl/demo" % self.repo, out)
        self.assertEqual(git(self.repo, 'rev-parse', 'HEAD'), self.base)  # main untouched
        git(self.repo, 'switch', '-q', 'impl/demo')
        code, out = run(MERGE, self.tmp, self.repo, 'demo', 'f1', 'origin')
        self.assertEqual(code, 0, out)
        self.assertIn('MERGED: f1 -> ', out)
        self.assertNotIn('MAIN MOVED', out)
        self.assertEqual(git(self.repo, 'log', '-1', '--format=%s'), 'impl: f1')
        self.assertTrue(os.path.exists(os.path.join(self.repo, 'src', 'a.cs')))

    def test_merge_lane_refuses_missing_lane_branch_and_dirty_worktree(self):
        self.remote_with_lane()
        code, out = run(MERGE, self.tmp, self.repo, 'demo', 'f2', 'origin')
        self.assertEqual(code, 1)
        self.assertIn('origin/impl/demo-f2 does not exist', out)
        self.write('dirty.txt')
        git(self.repo, 'add', 'dirty.txt')
        code, out = run(MERGE, self.tmp, self.repo, 'demo', 'f1', 'origin')
        self.assertEqual(code, 1)
        self.assertIn('local changes', out)

    def test_merge_lane_warns_when_main_moved_on_the_remote(self):
        remote = self.remote_with_lane()
        other = os.path.join(self.tmp, 'other')
        git(self.tmp, 'clone', '-q', remote, other)
        with open(os.path.join(other, 'hotfix.txt'), 'w') as fh:
            fh.write('x')
        git(other, 'add', 'hotfix.txt')
        git(other, 'commit', '-q', '-m', 'hotfix on main')
        git(other, 'push', '-q', 'origin', 'main')
        code, out = run(MERGE, self.tmp, self.repo, 'demo', 'f1', 'origin')
        self.assertEqual(code, 0, out)
        self.assertIn('MERGED: f1', out)
        self.assertIn('MAIN MOVED: 1 commit(s) on origin/main not in impl/demo', out)
        self.assertIn('hotfix.txt', git(self.repo, 'diff', '--stat', 'HEAD...origin/main'))

    def test_merge_lane_conflict_exits_3_and_leaves_the_merge_in_progress(self):
        self.remote_with_lane()
        self.write('src/a.cs', 'integration\n')
        self.commit_all('other lane')
        code, out = run(MERGE, self.tmp, self.repo, 'demo', 'f1', 'origin')
        self.assertEqual(code, 3, out)
        self.assertIn('MERGE CONFLICT: src/a.cs', out)
        self.assertTrue(os.path.exists(os.path.join(self.repo, '.git', 'MERGE_HEAD')))

    # ---- impl_env.sh

    def bare_remote(self):
        remote = os.path.join(self.tmp, 'remote.git')
        git(self.tmp, 'init', '-q', '--bare', '-b', 'main', remote)
        git(self.repo, 'remote', 'add', 'origin', remote)
        git(self.repo, 'push', '-q', 'origin', 'main')
        return remote

    def test_impl_env_prepares_folders_exclude_and_integration_worktree(self):
        self.bare_remote()
        code, out = run(ENV, self.repo, 'demo', '--no-pull', PATH='/usr/bin:/bin')  # no gh on PATH: no-PR mode
        self.assertEqual(code, 0, out)
        env = dict(l.split('=', 1) for l in out.splitlines() if '=' in l)
        self.assertEqual(env['BASE'], self.base)
        self.assertEqual(env['PR_MODE'], 'none')
        self.assertEqual(env['PROFILE'], 'missing')
        self.assertEqual(env['INTWT'], os.path.join(os.path.realpath(self.repo), '.claude', 'worktrees', 'impl-demo'))
        self.assertEqual(git(env['INTWT'], 'branch', '--show-current'), 'impl/demo')
        for sub in ('qa', 'retros', 'progress', 'acceptance'):
            self.assertTrue(os.path.isdir(os.path.join(self.repo, '.impl', 'demo', sub)), sub)
        self.assertTrue(os.path.isfile(env['BOARD']))
        with open(os.path.join(self.repo, '.git', 'info', 'exclude'), encoding='utf-8') as fh:
            lines = fh.read().splitlines()
        self.assertIn('.impl/', lines)
        self.assertIn('.claude/worktrees/', lines)
        self.assertEqual(git(self.repo, 'status', '--porcelain'), '')
        self.assertEqual(git(self.repo, 'branch', '--show-current'), 'main')
        code, out2 = run(ENV, self.repo, 'demo', '--no-pull', PATH='/usr/bin:/bin')  # idempotent
        self.assertEqual(code, 0, out2)
        with open(os.path.join(self.repo, '.git', 'info', 'exclude'), encoding='utf-8') as fh:
            self.assertEqual(lines, fh.read().splitlines())

    def test_impl_env_refuses_dirty_clone_wrong_branch_and_bad_slug(self):
        self.bare_remote()
        code, out = run(ENV, self.repo, 'Bad_Slug')
        self.assertEqual(code, 1)
        self.assertIn('not kebab-case', out)
        self.write('dirty.txt')
        code, out = run(ENV, self.repo, 'demo', '--no-pull')
        self.assertEqual(code, 1)
        self.assertIn('local changes', out)
        os.remove(os.path.join(self.repo, 'dirty.txt'))
        git(self.repo, 'switch', '-q', '-c', 'other')
        code, out = run(ENV, self.repo, 'demo', '--no-pull')
        self.assertEqual(code, 1)
        self.assertIn("on 'other', not main", out)
        self.assertFalse(os.path.exists(os.path.join(self.repo, '.impl')))

    # ---- board.sh

    def test_board_appends_a_timestamped_line(self):
        board = os.path.join(self.tmp, 'BOARD.md')
        code, out = run(BOARD, self.tmp, board, 'f1', 'start', 'abc123')
        self.assertEqual(code, 1)
        self.assertIn('does not exist', out)
        open(board, 'w').close()
        code, out = run(BOARD, self.tmp, board, 'f1', 'start', 'abc123')
        self.assertEqual(code, 0, out)
        code, out = run(BOARD, self.tmp, board, 'f1', 'CONTRACT', 'to=f2: GET /x: fields a, b')
        self.assertEqual(code, 0, out)
        with open(board, encoding='utf-8') as fh:
            lines = fh.read().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertRegex(lines[0], r'^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ \| f1 \| START \| abc123$')
        self.assertRegex(lines[1], r'^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ \| f1 \| CONTRACT \| to=f2: GET /x: fields a, b$')

    # ---- acceptance.py

    def accept(self, *args):
        p = subprocess.run([sys.executable, '-I', ACCEPT, *args], capture_output=True, text=True)
        return p.returncode, p.stdout

    def test_acceptance_runs_lane_items_and_logs(self):
        lane = self.lane('# f1 · demo\nOwns: `src/*`.\n## demo-1 · a · internal\nText. Acceptance: `test -f src/a.cs`.\n'
                         '## demo-2 · b · internal\nNo command here.\n## demo-3 · c · contract\nAcceptance: `false`.\n')
        self.write('src/a.cs')
        logs = os.path.join(self.tmp, 'acceptance')
        code, out = self.accept(lane, self.repo, '--log', logs, '--lane', 'f1')
        self.assertEqual(code, 0, out)
        self.assertIn('demo-1 · exit 0 · test -f src/a.cs', out)
        self.assertIn('demo-2 · no Acceptance command', out)
        self.assertIn('demo-3 · exit 1 · false', out)
        self.assertIn('ACCEPTANCE: 1 green, 1 red, 1 without command', out)
        self.assertEqual(sorted(os.listdir(logs)), ['f1-demo-1.log', 'f1-demo-3.log'])
        with open(os.path.join(logs, 'f1-demo-3.log'), encoding='utf-8') as fh:
            self.assertIn('exit 1', fh.read())
        code, out = self.accept(lane, self.repo, '--only', 'demo-3')
        self.assertNotIn('demo-1', out)
        self.assertIn('ACCEPTANCE: 0 green, 1 red, 0 without command', out)

    def test_acceptance_reads_plan_table_rows(self):
        plan = self.lane('# t\n| Id | Item | Files (symbol) | Type | Acceptance (command) |\n|---|---|---|---|---|\n'
                         '| demo-1 | a | `src/a.cs` (`A`) | internal | `true` |\n| demo-2 | b | `src/b.cs` | contract | `exit 3` |\n')
        code, out = self.accept(plan, self.repo)
        self.assertEqual(code, 0, out)
        self.assertIn('demo-1 · exit 0 · true', out)
        self.assertIn('demo-2 · exit 3 · exit 3', out)
        code, out = self.accept(self.lane('# nothing\n'), self.repo)
        self.assertEqual(code, 2)
        self.assertIn('ACCEPTANCE FAILED: no item', out)

    # ---- cleanup_worktrees.sh

    def test_cleanup_removes_only_the_run_worktrees_and_saves_changes(self):
        git(self.repo, 'branch', 'impl/demo')
        lane_wt = os.path.join(self.tmp, 'lane')
        git(self.repo, 'worktree', 'add', '-q', '-b', 'impl/demo-f1', lane_wt, 'impl/demo')
        with open(os.path.join(lane_wt, 'a.txt'), 'w') as fh:
            fh.write('x')
        git(lane_wt, 'add', 'a.txt')
        git(lane_wt, 'commit', '-q', '-m', 'demo-1: a')
        git(self.repo, 'switch', '-q', 'impl/demo')
        git(self.repo, 'merge', '-q', '--no-ff', 'impl/demo-f1', '-m', 'impl: f1')
        git(self.repo, 'switch', '-q', 'main')
        agent_wt = os.path.join(self.tmp, 'agent')
        git(self.repo, 'worktree', 'add', '-q', '-b', 'worktree-agent-1', agent_wt, 'impl/demo')
        with open(os.path.join(agent_wt, 'wip.txt'), 'w') as fh:
            fh.write('unsaved')
        other_wt = os.path.join(self.tmp, 'other')
        git(self.repo, 'worktree', 'add', '-q', '-b', 'worktree-agent-other', other_wt, 'main')  # HEAD on main: not the run's
        intwt = os.path.join(self.tmp, 'int')
        git(self.repo, 'worktree', 'add', '-q', intwt, 'impl/demo')
        code, out = run(CLEANUP, self.tmp, self.repo, 'demo', '--dry-run')
        self.assertEqual(code, 0, out)
        self.assertIn('WOULD REMOVE: %s' % lane_wt, out)
        self.assertTrue(os.path.isdir(agent_wt))
        code, out = run(CLEANUP, self.tmp, self.repo, 'demo')
        self.assertEqual(code, 0, out)
        self.assertIn('REMOVED: %s (impl/demo-f1)' % lane_wt, out)
        self.assertIn('SAVED: wip: worktree-agent-1', out)
        self.assertIn('REMOVED: %s (worktree-agent-1)' % agent_wt, out)
        self.assertIn('BRANCH DELETED: worktree-agent-1', out)
        self.assertIn('KEPT: %s (worktree-agent-other)' % other_wt, out)
        self.assertIn('KEPT: %s (impl/demo)' % intwt, out)
        self.assertIn('CLEANUP OK: 2 worktree(s) removed', out)
        self.assertFalse(os.path.exists(lane_wt))
        self.assertTrue(os.path.isdir(other_wt))
        self.assertTrue(os.path.isdir(intwt))
        self.assertIn('impl/demo-f1', git(self.repo, 'branch', '--list', 'impl/demo-f1'))  # impl/… branches stay
        self.assertEqual(git(self.repo, 'branch', '--list', 'worktree-agent-1'), '')
        code, out = run(CLEANUP, self.tmp, self.repo, 'demo', '--integration')
        self.assertIn('REMOVED: %s (impl/demo)' % intwt, out)
        self.assertFalse(os.path.exists(intwt))

    # ---- scope.sh: hard paths

    def test_scope_accepts_glob_characters_non_ascii_and_spaces(self):
        lane = self.lane('# f\nOwns: `app/[id]/page.tsx` `docs/revisão.md` `com espaço/*`. Union: —.\n## i\n')
        for f in ('app/[id]/page.tsx', 'docs/revisão.md', 'com espaço/a b.txt'):
            self.write(f)
        self.commit_all()
        code, out = run(SCOPE, self.repo, lane, self.base)
        self.assertEqual(code, 0, out)
        self.assertIn('SCOPE OK: 3 files', out)
        self.write('fora.txt')
        self.commit_all()
        code, out = run(SCOPE, self.repo, lane, self.base)
        self.assertEqual(code, 1)
        self.assertIn('OUTSIDE: fora.txt', out)

    def test_scope_without_union_or_touchable_lines(self):
        self.write('src/a.cs')
        self.write('union/c.txt')
        self.commit_all()
        code, out = run(SCOPE, self.repo, self.lane('# f\nOwns: `src/*`.\n## i\n'), self.base)
        self.assertEqual(code, 1)
        self.assertIn('OUTSIDE: union/c.txt', out)
        self.assertNotIn('src/a.cs', out)


if __name__ == '__main__':
    unittest.main()
