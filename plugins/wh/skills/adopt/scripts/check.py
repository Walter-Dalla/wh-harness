#!/usr/bin/env python3
"""Adoption diagnosis of the `wh` harness in a repository: what exists, what is missing, what is off the template.

Deterministic, stdlib only, never writes to the repo. One line per item: `OK | MISSING | OUTDATED | WARN  <item>  <detail>`.
Exits with 1 when there is any MISSING or OUTDATED, 0 otherwise.

Usage:
  check.py [--root DIR] [--plugin-root DIR] [--json]
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PLUGIN = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
PROFILE_DIR = os.path.join('.claude', 'profile')
LIMIT_COMMON, LIMIT_SKILL = 40, 60
MARKETPLACE, PLUGIN_ID = 'wh-harness', 'wh@wh-harness'
CONTEXT_KEYS = {'glossario', 'features', 'indice_features', 'codegraph', 'class_name_globs', 'max_features',
                'max_termos', 'max_simbolos', 'max_interage', 'min_score', 'min_prompt', 'max_chars', 'idioma',
                'secoes'}
NO_PROFILE = {'profile', 'retro', 'adopt'}
AGENTS_DIR = os.path.join('.claude', 'agents')
TEMPLATE_MARK = re.compile(r'<!--\s*wh-template:\s*(\S+)\s+(\d+)\s*-->')
COMMAND_KEYS = ('build', 'suite', 'typecheck', 'service', 'health')
COMMAND_LINE = re.compile(r'^(build|suite|typecheck|service|health):[ \t]+(`[^`]+`|—)')


def headings(text):
    return [m.group(1).strip() for m in re.finditer(r'^## (.+)$', text, re.M)]


def read(path):
    try:
        with open(path, encoding='utf-8') as fh:
            return fh.read()
    except OSError:
        return None


def template(path):
    """`##` sections of the ```markdown block of a PROFILE.md/COMMON.md."""
    text = read(path) or ''
    m = re.search(r'```markdown\n(.*?)```', text, re.S)
    return headings(m.group(1) if m else text)


class Check:
    def __init__(self, root, plugin):
        self.root, self.plugin = root, plugin
        self.items = []
        self._names = None

    def add(self, state, item, detail=''):
        self.items.append({'estado': state, 'item': item, 'detalhe': detail})

    def p(self, *parts):
        return os.path.join(self.root, *parts)

    def skills(self):
        return sorted(os.path.basename(os.path.dirname(f)) for f in glob.glob(os.path.join(self.plugin, 'skills', '*', 'SKILL.md')))

    # ---- items ----

    def repo_map(self):
        for name in ('CLAUDE.md', 'AGENTS.md'):
            if os.path.isfile(self.p(name)):
                self.add('OK', 'repo map', name)
                return
        self.add('MISSING', 'repo map', 'CLAUDE.md or AGENTS.md at the root (first source of the profile skill)')

    def legacy(self):
        """A `.claude/perfil/` folder is the profile layout before 0.7.0: renamed files and Portuguese headings."""
        if not os.path.isdir(self.p('.claude', 'perfil')):
            return
        state = 'WARN' if os.path.isdir(self.p(PROFILE_DIR)) else 'MISSING'
        self.add(state, 'profile folder', '.claude/perfil/ is the layout before 0.7.0: git mv .claude/perfil .claude/profile, '
                 '_comum.md → _common.md, contexto.json → context.json, then /wh:profile (English headings)')

    def profile(self, path, tpl, limit, name):
        text = read(path)
        if text is None:
            self.add('MISSING', 'profile ' + name, path.replace(self.root + os.sep, ''))
            return
        missing = [s for s in template(tpl) if s not in headings(text)]
        if missing:
            self.add('MISSING', 'profile ' + name, 'missing sections: ' + ', '.join(missing))
        else:
            self.add('OK', 'profile ' + name)
        if name == 'implementation' and 'Commands' in headings(text):
            self.commands(text, name)
        lines = len(text.splitlines())
        if lines > limit:
            self.add('WARN', 'profile ' + name, '%d lines (target ≤ %d): the excess becomes a repo doc' % (lines, limit))
        inferred = text.count('[inferred]')
        if inferred:
            self.add('WARN', 'profile ' + name, '%d [inferred] line(s) to confirm with the owner' % inferred)
        empty = [s for s in headings(text) if re.search(r'^## %s\n+—' % re.escape(s), text, re.M)]
        if empty:
            self.add('WARN', 'profile ' + name, 'sections —: ' + ', '.join(empty))

    def commands(self, text, name):
        """§ Commands: one `<key>: `<command>`` (or `—`) line per key; build and suite judged by their exit code."""
        m = re.search(r'^## Commands[ \t]*\n(.*?)(?=^## |\Z)', text, re.M | re.S)
        found = {}
        for line in (m.group(1) if m else '').splitlines():
            km = COMMAND_LINE.match(line)
            if km:
                found.setdefault(km.group(1), km.group(2))
        bad = [k for k in COMMAND_KEYS if k not in found]
        if bad:
            self.add('MISSING', 'profile ' + name, 'Commands: missing or malformed keys: ' + ', '.join(bad))
        for key in ('build', 'suite'):
            cmd = found.get(key, '')
            if '|' in cmd and 'pipefail' not in cmd:
                self.add('WARN', 'profile ' + name, 'Commands: %s has a pipe (the verdict is the exit code: no pipe, or set -o pipefail)' % key)

    def profiles(self):
        self.profile(self.p(PROFILE_DIR, '_common.md'), os.path.join(self.plugin, 'skills', 'profile', 'COMMON.md'), LIMIT_COMMON, '_common')
        optional = []
        for skill in self.skills():
            if skill in NO_PROFILE:
                continue
            path = self.p(PROFILE_DIR, skill + '.md')
            tpl = os.path.join(self.plugin, 'skills', skill, 'PROFILE.md')
            if skill == 'implementation' or os.path.isfile(path):
                self.profile(path, tpl, LIMIT_SKILL, skill)
            else:
                optional.append(skill)
        if optional:
            self.add('WARN', 'optional profiles', 'absent (only if the repo uses the skill; /wh:profile <skill>): ' + ', '.join(optional))

    def shadow(self):
        for skill in self.skills():
            if os.path.isdir(self.p('.claude', 'skills', skill)):
                self.add('WARN', 'old skill', '.claude/skills/%s shadows /wh:%s: facts into the profile, then git rm -r' % (skill, skill))

    def context(self):
        path = self.p(PROFILE_DIR, 'context.json')
        text = read(path)
        if text is None:
            self.add('MISSING', 'context.json', 'prompt-graph hook off in this repo')
            return
        try:
            cfg = json.loads(text)
        except ValueError as exc:
            self.add('MISSING', 'context.json', 'invalid JSON: %s' % exc)
            return
        unknown = sorted(set(cfg) - CONTEXT_KEYS)
        if unknown:
            self.add('WARN', 'context.json', 'unknown keys: ' + ', '.join(unknown))
        self.add('OK', 'context.json')
        sources = {'glossario': 'docs/GLOSSARIO.md', 'features': 'docs/features', 'indice_features': 'docs/features/README.md',
                   'codegraph': '.codegraph/codegraph.db'}
        gives = {'glossario': 'terms', 'features': 'features', 'indice_features': 'index keywords', 'codegraph': 'file:line'}
        for key, default in sources.items():
            rel = cfg.get(key, default)
            if os.path.exists(self.p(rel)):
                self.add('OK', key, rel)
            else:
                level = 'WARN' if key == 'codegraph' else 'MISSING'
                self.add(level, key, '%s absent (without it the hook has no %s)' % (rel, gives[key]))
        self.graph()

    def graph(self):
        sys.path.insert(0, os.path.join(self.plugin, 'scripts'))
        try:
            import prompt_graph as pg  # noqa: E402
            cfg = pg.load_cfg(self.root)
            g = pg.build_graph(self.root, cfg)
            self.add('OK' if g['index'] else 'WARN', 'graph', '%d keys, %d features, %d terms, %d symbols' % (
                len(g['index']), len(g['features']), len(g['glossario']), len(g['simbolos'])))
        except Exception as exc:  # the diagnosis never aborts
            self.add('WARN', 'graph', 'did not build: %s' % exc)

    def settings(self):
        path = self.p('.claude', 'settings.json')
        text = read(path)
        if text is None:
            self.add('MISSING', 'settings.json', '.claude/settings.json without the plugin: whoever clones gets no offer')
            return
        try:
            cfg = json.loads(text)
        except ValueError as exc:
            self.add('MISSING', 'settings.json', 'invalid JSON: %s' % exc)
            return
        ok_mkt = MARKETPLACE in (cfg.get('extraKnownMarketplaces') or {})
        ok_plg = (cfg.get('enabledPlugins') or {}).get(PLUGIN_ID) is True
        if ok_mkt and ok_plg:
            self.add('OK', 'settings.json', 'plugin declared')
        else:
            self.add('MISSING', 'settings.json', 'missing: ' + ', '.join(n for n, ok in (('extraKnownMarketplaces.' + MARKETPLACE, ok_mkt), ('enabledPlugins.' + PLUGIN_ID, ok_plg)) if not ok))

    def gitignore(self):
        text = read(self.p('.gitignore')) or ''
        lines = {l.strip() for l in text.splitlines()}
        has_cg = os.path.isdir(self.p('.codegraph'))
        if '.codegraph/' in lines or '.codegraph' in lines:
            self.add('OK', '.gitignore', '.codegraph/')
        else:
            self.add('MISSING' if has_cg else 'WARN', '.gitignore', '.codegraph/ not in .gitignore')
        exclude = read(self.p('.git', 'info', 'exclude')) or ''
        if '.impl/' not in {l.strip() for l in exclude.splitlines()} and '.impl/' not in lines:
            self.add('WARN', 'exclude', '.impl/ not excluded yet (/wh:implementation does it once per clone)')

    def codegraph(self):
        if os.path.isfile(self.p('.codegraph', 'codegraph.db')):
            self.add('OK', 'codegraph', '.codegraph/codegraph.db')
        elif shutil.which('codegraph'):
            self.add('WARN', 'codegraph', 'CLI present, index absent: `codegraph init -y .` is the owner\'s decision')
        else:
            self.add('WARN', 'codegraph', 'CLI absent: symbols come without file:line')

    def git(self):
        if not os.path.exists(self.p('.git')):  # a `git worktree` has a .git file, not a folder
            self.add('WARN', 'git', 'root is not a git repository (/wh:implementation worktrees need one)')

    def basenames(self):
        """File names of the repository (`git ls-files`, else a walk without `.git`) and of the plugin, built once."""
        if self._names is None:
            names = set()
            try:
                out = subprocess.run(['git', '-C', self.root, 'ls-files', '-z'], capture_output=True, text=True, check=True).stdout
                names.update(os.path.basename(f) for f in out.split('\0') if f)
            except (OSError, subprocess.CalledProcessError):
                for _, dirs, files in os.walk(self.root):
                    dirs[:] = [d for d in dirs if d != '.git']
                    names.update(files)
            for _, _, files in os.walk(self.plugin):
                names.update(files)
            self._names = names
        return self._names

    def links(self):
        """Every path cited in backticks by the map, the profiles and context.json exists (adopt § 6.3)."""
        files = [self.p(n) for n in ('CLAUDE.md', 'AGENTS.md')] + sorted(glob.glob(self.p(PROFILE_DIR, '*.md')))
        bad = []
        for path in files:
            text = read(path)
            if text is None:
                continue
            for tok in set(re.findall(r'`([^`\s]+)`', text)):
                if not re.search(r'[/\\]|\.(md|json|ya?ml|toml|sh|py|cs|ts|js|csproj|sln)$', tok) or re.search(r'[<>*$§{}|…]|^https?:|^[-./~]', tok):
                    continue
                bare = not re.search(r'[/\\]', tok)  # a bare file name may live anywhere in the repo or the plugin
                if not os.path.exists(self.p(tok.rstrip('/'))) and not (bare and tok in self.basenames()):
                    bad.append('%s → %s' % (os.path.relpath(path, self.root), tok))
        cfg_path = self.p(PROFILE_DIR, 'context.json')
        try:
            cfg = json.loads(read(cfg_path) or '{}')
        except ValueError:
            cfg = {}
        for key in ('glossario', 'features', 'indice_features'):
            if key in cfg and not os.path.exists(self.p(cfg[key])):
                bad.append('context.json → %s' % cfg[key])
        if bad:
            self.add('WARN', 'links', 'cited paths absent: ' + '; '.join(sorted(bad)))
        elif any(os.path.isfile(f) for f in files):
            self.add('OK', 'links', 'every cited path exists')

    def agents(self):
        """Native agents the project overrides from the plugin templates (`<!-- wh-template: <name> <n> -->`)."""
        for tpl in sorted(glob.glob(os.path.join(self.plugin, 'skills', 'adopt', 'templates', 'agents', '*.md'))):
            name = os.path.basename(tpl)
            rel = os.path.join(AGENTS_DIR, name)
            want = TEMPLATE_MARK.search(read(tpl) or '')
            if not want:
                self.add('WARN', 'agents', 'template %s has no wh-template marker' % name)
                continue
            text = read(self.p(rel))
            if text is None:
                self.add('MISSING', 'agents', '%s (template %s %s; /wh:adopt agents copies it)' % (rel, want.group(1), want.group(2)))
                continue
            have = TEMPLATE_MARK.search(text)
            if not have:
                self.add('WARN', 'agents', "%s is the owner's (no wh-template marker): not overwritten" % rel)
            elif int(have.group(2)) < int(want.group(2)):
                self.add('OUTDATED', 'agents', '%s is at %s %s, template at %s (/wh:adopt agents recopies it)' % (
                    rel, have.group(1), have.group(2), want.group(2)))
            else:
                self.add('OK', 'agents', '%s (%s %s)' % (rel, have.group(1), have.group(2)))

    def run(self):
        self.git()
        self.repo_map()
        self.legacy()
        self.profiles()
        self.shadow()
        self.context()
        self.settings()
        self.gitignore()
        self.codegraph()
        self.links()
        self.agents()
        return self.items


def main(argv):
    rest = [a for a in argv[1:] if a != '--json']
    args = dict(zip(rest[0::2], rest[1::2]))
    root = os.path.abspath(args.get('--root', '.'))
    plugin = os.path.abspath(args.get('--plugin-root', DEFAULT_PLUGIN))
    items = Check(root, plugin).run()
    if '--json' in argv:
        json.dump(items, sys.stdout, ensure_ascii=False, indent=1)
    else:
        for it in items:
            print('%-8s  %-22s %s' % (it['estado'], it['item'], it['detalhe']))
        count = lambda state: sum(1 for it in items if it['estado'] == state)  # noqa: E731
        print('%d MISSING, %d OUTDATED, %d WARN' % (count('MISSING'), count('OUTDATED'), count('WARN')))
    return 1 if any(it['estado'] in ('MISSING', 'OUTDATED') for it in items) else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
