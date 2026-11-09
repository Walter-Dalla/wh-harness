"""Section references inside the plugin point at sections that exist.

- `profile § X` / `_common § X` names, in full, a `## X` section of the matching profile template
  (a prefix such as `profile § QA` for `## Visual or e2e QA` fails), including chained `and § Y`.
- `FILE.md § X` names a `## X` heading (or a `**X:**` label) of that plugin file; `§N` a `## N.` heading.

    python3 -m unittest discover -s tests
"""
import glob
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(ROOT, 'plugins', 'wh')
REF = re.compile(r'(profile|Profile|_common)`?\s+§\s+')
CHAIN = re.compile(r'^(?:\s*\([^)]*\))?\s*(?:,|and|or)\s+§\s+')
PLACEHOLDER = re.compile(r'^(X\b|<|Section)')
FILE_REF = re.compile(r'([A-Z]+\.md)`(?:\]\([^)]*\))?\s+§\s*')


def headings(path):
    with open(path, encoding='utf-8') as fh:
        return [m.group(1).strip() for m in re.finditer(r'^## (.+)$', fh.read(), re.M)]


def anchors(path):
    """`##` headings without the trailing parenthetical, plus `**Label:**` paragraphs."""
    with open(path, encoding='utf-8') as fh:
        text = fh.read()
    out = [re.sub(r'\s*\(.*$', '', h) for h in headings(path)]
    return out + [m.group(1).strip() for m in re.finditer(r'^\*\*([^*:]+):?\*\*', text, re.M)]


def named(rest, pool):
    """The longest name of `pool` that `rest` starts with, ending at a word boundary."""
    best = None
    for h in pool:
        if rest.lower().startswith(h.lower()) and not rest[len(h):len(h) + 1].isalnum():
            if best is None or len(h) > len(best):
                best = h
    return best


def template_for(path):
    """PROFILE.md of the skill that owns the file; agents and implementation helpers use implementation's."""
    rel = os.path.relpath(path, PLUGIN).replace(os.sep, '/')
    skill = rel.split('/')[1] if rel.startswith('skills/') else 'implementation'
    return os.path.join(PLUGIN, 'skills', skill, 'PROFILE.md')


def plugin_docs():
    for path in sorted(glob.glob(os.path.join(PLUGIN, '**', '*.md'), recursive=True)):
        if os.path.basename(path) not in ('PROFILE.md', 'COMMON.md'):
            with open(path, encoding='utf-8') as fh:
                yield path, list(enumerate(fh, 1))


class RefsTest(unittest.TestCase):
    def test_named_requires_the_full_section_name(self):
        pool = ['Visual or e2e QA', 'Tests', 'Enricher reading']
        self.assertIsNone(named('Visual (if any)', pool))
        self.assertIsNone(named('Enricher notes the lane touches', pool))
        self.assertEqual(named('Visual or e2e QA is not', pool), 'Visual or e2e QA')
        self.assertEqual(named('Tests and § Checks', pool), 'Tests')

    def test_every_profile_reference_names_a_template_section(self):
        common = headings(os.path.join(PLUGIN, 'skills', 'profile', 'COMMON.md'))
        bad = []
        for path, lines in plugin_docs():
            tpl = template_for(path)
            own = headings(tpl) if os.path.exists(tpl) else []
            for n, line in lines:
                for m in REF.finditer(line):
                    pool = common if m.group(1) == '_common' else own
                    pos = m.end()
                    while True:
                        rest = line[pos:]
                        if PLACEHOLDER.match(rest):
                            break
                        name = named(rest, pool)
                        if name is None:
                            bad.append('%s:%d: %s § %s' % (os.path.relpath(path, ROOT), n, m.group(1), rest[:30].strip()))
                            break
                        pos += len(name)
                        chain = CHAIN.match(line[pos:])
                        if not chain:
                            break
                        pos += chain.end()
        self.assertEqual(bad, [], '\n' + '\n'.join(bad))

    def test_every_file_section_reference_names_a_heading_of_that_file(self):
        bad = []
        for path, lines in plugin_docs():
            for n, line in lines:
                for m in FILE_REF.finditer(line):
                    target = os.path.join(os.path.dirname(path), m.group(1))
                    if not os.path.exists(target):
                        target = os.path.join(PLUGIN, 'skills', 'implementation', m.group(1))
                    if not os.path.exists(target):
                        continue  # file outside the plugin (repo docs)
                    rest = line[m.end():]
                    num = re.match(r'\d+', rest)
                    if num:
                        ok = any(h.startswith(num.group(0) + '.') for h in headings(target))
                    else:
                        ok = named(rest, anchors(target)) is not None
                    if not ok:
                        bad.append('%s:%d: %s § %s' % (os.path.relpath(path, ROOT), n, m.group(1), rest[:30].strip()))
        self.assertEqual(bad, [], '\n' + '\n'.join(bad))


if __name__ == '__main__':
    unittest.main()
