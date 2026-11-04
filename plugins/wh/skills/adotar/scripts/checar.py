#!/usr/bin/env python3
"""Diagnóstico de adoção do harness `wh` num repositório: o que existe, o que falta, o que está fora do modelo.

Determinístico, só stdlib, nunca escreve no repo. Uma linha por item: `OK | FALTA | AVISO  <item>  <detalhe>`.
Sai com 1 quando há algum FALTA, 0 caso contrário.

Uso:
  checar.py [--root DIR] [--plugin-root DIR] [--json]
"""
import glob
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PLUGIN = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
PERFIL_DIR = os.path.join('.claude', 'perfil')
LIMITE_COMUM, LIMITE_SKILL = 40, 60
MARKETPLACE, PLUGIN_ID = 'wh-harness', 'wh@wh-harness'
CHAVES_CONTEXTO = {'glossario', 'features', 'indice_features', 'codegraph', 'class_name_globs', 'max_features',
                   'max_termos', 'max_simbolos', 'max_interage', 'min_score', 'min_prompt', 'max_chars', 'idioma',
                   'secoes'}
SEM_PERFIL = {'perfil', 'retro', 'adotar'}


def headings(text):
    return [m.group(1).strip() for m in re.finditer(r'^## (.+)$', text, re.M)]


def read(path):
    try:
        with open(path, encoding='utf-8') as fh:
            return fh.read()
    except OSError:
        return None


def modelo(path):
    """Seções `##` do bloco ```markdown de um PERFIL.md/COMUM.md."""
    text = read(path) or ''
    m = re.search(r'```markdown\n(.*?)```', text, re.S)
    return headings(m.group(1) if m else text)


class Checagem:
    def __init__(self, root, plugin):
        self.root, self.plugin = root, plugin
        self.itens = []

    def add(self, estado, item, detalhe=''):
        self.itens.append({'estado': estado, 'item': item, 'detalhe': detalhe})

    def p(self, *parts):
        return os.path.join(self.root, *parts)

    def skills(self):
        return sorted(os.path.basename(os.path.dirname(f)) for f in glob.glob(os.path.join(self.plugin, 'skills', '*', 'SKILL.md')))

    # ---- itens ----

    def mapa(self):
        for nome in ('CLAUDE.md', 'AGENTS.md'):
            if os.path.isfile(self.p(nome)):
                self.add('OK', 'mapa do repo', nome)
                return
        self.add('FALTA', 'mapa do repo', 'CLAUDE.md ou AGENTS.md na raiz (primeira fonte da skill perfil)')

    def perfil(self, path, template, limite, nome):
        text = read(path)
        if text is None:
            self.add('FALTA', 'perfil ' + nome, path.replace(self.root + os.sep, ''))
            return
        faltam = [s for s in modelo(template) if s not in headings(text)]
        if faltam:
            self.add('FALTA', 'perfil ' + nome, 'seções a menos: ' + ', '.join(faltam))
        else:
            self.add('OK', 'perfil ' + nome)
        linhas = len(text.splitlines())
        if linhas > limite:
            self.add('AVISO', 'perfil ' + nome, '%d linhas (alvo ≤ %d): excesso vira doc do repo' % (linhas, limite))
        inferidos = text.count('[inferido]')
        if inferidos:
            self.add('AVISO', 'perfil ' + nome, '%d linha(s) [inferido] a confirmar com o dono' % inferidos)
        vazias = [s for s in headings(text) if re.search(r'^## %s\n+—' % re.escape(s), text, re.M)]
        if vazias:
            self.add('AVISO', 'perfil ' + nome, 'seções —: ' + ', '.join(vazias))

    def perfis(self):
        self.perfil(self.p(PERFIL_DIR, '_comum.md'), os.path.join(self.plugin, 'skills', 'perfil', 'COMUM.md'), LIMITE_COMUM, '_comum')
        opcionais = []
        for skill in self.skills():
            if skill in SEM_PERFIL:
                continue
            path = self.p(PERFIL_DIR, skill + '.md')
            tpl = os.path.join(self.plugin, 'skills', skill, 'PERFIL.md')
            if skill == 'implementation' or os.path.isfile(path):
                self.perfil(path, tpl, LIMITE_SKILL, skill)
            else:
                opcionais.append(skill)
        if opcionais:
            self.add('AVISO', 'perfis opcionais', 'ausentes (só se o repo usa a skill; /wh:perfil <skill>): ' + ', '.join(opcionais))

    def sombra(self):
        for skill in self.skills():
            if os.path.isdir(self.p('.claude', 'skills', skill)):
                self.add('AVISO', 'skill antiga', '.claude/skills/%s sombreia /wh:%s: fatos para o perfil, depois git rm -r' % (skill, skill))

    def contexto(self):
        path = self.p(PERFIL_DIR, 'contexto.json')
        text = read(path)
        if text is None:
            self.add('FALTA', 'contexto.json', 'hook prompt-graph desligado neste repo')
            return
        try:
            cfg = json.loads(text)
        except ValueError as exc:
            self.add('FALTA', 'contexto.json', 'JSON inválido: %s' % exc)
            return
        desconhecidas = sorted(set(cfg) - CHAVES_CONTEXTO)
        if desconhecidas:
            self.add('AVISO', 'contexto.json', 'chaves desconhecidas: ' + ', '.join(desconhecidas))
        self.add('OK', 'contexto.json')
        fontes = {'glossario': 'docs/GLOSSARIO.md', 'features': 'docs/features', 'indice_features': 'docs/features/README.md',
                  'codegraph': '.codegraph/codegraph.db'}
        for chave, padrao in fontes.items():
            rel = cfg.get(chave, padrao)
            if os.path.exists(self.p(rel)):
                self.add('OK', chave, rel)
            else:
                nivel = 'AVISO' if chave == 'codegraph' else 'FALTA'
                self.add(nivel, chave, '%s ausente (sem ele o hook não tem %s)' % (rel, {'glossario': 'termos', 'features': 'features', 'indice_features': 'palavras-chave do índice', 'codegraph': 'arquivo:linha'}[chave]))
        self.grafo()

    def grafo(self):
        sys.path.insert(0, os.path.join(self.plugin, 'scripts'))
        try:
            import prompt_graph as pg  # noqa: E402
            cfg = pg.load_cfg(self.root)
            g = pg.build_graph(self.root, cfg)
            self.add('OK' if g['index'] else 'AVISO', 'grafo', '%d chaves, %d features, %d termos, %d símbolos' % (
                len(g['index']), len(g['features']), len(g['glossario']), len(g['simbolos'])))
        except Exception as exc:  # diagnóstico nunca aborta
            self.add('AVISO', 'grafo', 'não construiu: %s' % exc)

    def settings(self):
        path = self.p('.claude', 'settings.json')
        text = read(path)
        if text is None:
            self.add('FALTA', 'settings.json', '.claude/settings.json sem o plugin: quem clona não recebe a oferta')
            return
        try:
            cfg = json.loads(text)
        except ValueError as exc:
            self.add('FALTA', 'settings.json', 'JSON inválido: %s' % exc)
            return
        ok_mkt = MARKETPLACE in (cfg.get('extraKnownMarketplaces') or {})
        ok_plg = (cfg.get('enabledPlugins') or {}).get(PLUGIN_ID) is True
        if ok_mkt and ok_plg:
            self.add('OK', 'settings.json', 'plugin declarado')
        else:
            self.add('FALTA', 'settings.json', 'faltam: ' + ', '.join(n for n, ok in (('extraKnownMarketplaces.' + MARKETPLACE, ok_mkt), ('enabledPlugins.' + PLUGIN_ID, ok_plg)) if not ok))

    def gitignore(self):
        text = read(self.p('.gitignore')) or ''
        linhas = {l.strip() for l in text.splitlines()}
        tem_cg = os.path.isdir(self.p('.codegraph'))
        if '.codegraph/' in linhas or '.codegraph' in linhas:
            self.add('OK', '.gitignore', '.codegraph/')
        else:
            self.add('FALTA' if tem_cg else 'AVISO', '.gitignore', '.codegraph/ fora do .gitignore')
        exclude = read(self.p('.git', 'info', 'exclude')) or ''
        if '.impl/' not in {l.strip() for l in exclude.splitlines()} and '.impl/' not in linhas:
            self.add('AVISO', 'exclude', '.impl/ ainda não excluído (o /wh:implementation faz uma vez por clone)')

    def codegraph(self):
        if os.path.isfile(self.p('.codegraph', 'codegraph.db')):
            self.add('OK', 'codegraph', '.codegraph/codegraph.db')
        elif shutil.which('codegraph'):
            self.add('AVISO', 'codegraph', 'CLI presente, índice ausente: `codegraph init -y .` é decisão do dono')
        else:
            self.add('AVISO', 'codegraph', 'CLI ausente: símbolos saem sem arquivo:linha')

    def git(self):
        if not os.path.isdir(self.p('.git')):
            self.add('AVISO', 'git', 'raiz não é um repositório git (worktrees do /wh:implementation precisam)')

    def run(self):
        self.git()
        self.mapa()
        self.perfis()
        self.sombra()
        self.contexto()
        self.settings()
        self.gitignore()
        self.codegraph()
        return self.itens


def main(argv):
    rest = [a for a in argv[1:] if a != '--json']
    args = dict(zip(rest[0::2], rest[1::2]))
    root = os.path.abspath(args.get('--root', '.'))
    plugin = os.path.abspath(args.get('--plugin-root', DEFAULT_PLUGIN))
    itens = Checagem(root, plugin).run()
    if '--json' in argv:
        json.dump(itens, sys.stdout, ensure_ascii=False, indent=1)
    else:
        for it in itens:
            print('%-5s  %-22s %s' % (it['estado'], it['item'], it['detalhe']))
        n = sum(1 for it in itens if it['estado'] == 'FALTA')
        print('%d FALTA, %d AVISO' % (n, sum(1 for it in itens if it['estado'] == 'AVISO')))
    return 1 if any(it['estado'] == 'FALTA' for it in itens) else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
