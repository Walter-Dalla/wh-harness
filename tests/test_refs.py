"""Every `perfil § X` / `_comum § X` reference in the plugin names a `## X` section of the matching template.

    python3 -m unittest discover -s tests
"""
import glob
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(ROOT, 'plugins', 'wh')
REF = re.compile(r'(perfil|_comum|Perfil)\s+§\s+([A-Za-zÀ-ú][A-Za-zÀ-ú ]*?)(?=[\s]*[`,.;:)(|]|\s+(?:e|ou|do|da|de|que|diz|existir|lista|para|por|com|na|no|valem|não)\b|\s*$)', re.M)


def headings(path):
    with open(path, encoding='utf-8') as fh:
        return [m.group(1).strip() for m in re.finditer(r'^## (.+)$', fh.read(), re.M)]


def template_for(path):
    """PERFIL.md of the skill that owns the file; agents and implementation helpers use implementation's."""
    rel = os.path.relpath(path, PLUGIN).replace(os.sep, '/')
    skill = rel.split('/')[1] if rel.startswith('skills/') else 'implementation'
    return os.path.join(PLUGIN, 'skills', skill, 'PERFIL.md')


class RefsTest(unittest.TestCase):
    def test_every_profile_reference_names_a_template_section(self):
        comum = headings(os.path.join(PLUGIN, 'skills', 'perfil', 'COMUM.md'))
        bad = []
        for path in glob.glob(os.path.join(PLUGIN, '**', '*.md'), recursive=True):
            if os.path.basename(path) in ('PERFIL.md', 'COMUM.md'):
                continue
            tpl = template_for(path)
            own = headings(tpl) if os.path.exists(tpl) else []
            with open(path, encoding='utf-8') as fh:
                for n, line in enumerate(fh, 1):
                    for m in REF.finditer(line):
                        name = m.group(2).strip()
                        pool = comum if m.group(1) == '_comum' else own
                        if name == 'X':
                            continue
                        if not any(h.lower().startswith(name.lower()) for h in pool):
                            bad.append('%s:%d: %s § %s' % (os.path.relpath(path, ROOT), n, m.group(1), name))
        self.assertEqual(bad, [], '\n' + '\n'.join(bad))


if __name__ == '__main__':
    unittest.main()
