"""Every text the app shows, checked against each language's translations (lutsmith_app/assets/i18n).

    uv run python tools/i18n_check.py            # report; exit 1 when a language misses a text or breaks one
    uv run python tools/i18n_check.py --missing  # print the missing texts (English), one JSON list"""
import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'lutsmith_app'
sys.path.insert(0, str(ROOT))
KEEP = ['ΔE00', 'LUT', 'DNG', 'sRGB', 'Adobe RGB', 'ColorChecker', 'SHA-256', 'GR4-LUTSmith', 'RICOH', 'GR IV', 'HDF', '1.11',
        '.cube', '.json', 'look.json', 'p95']


def app_keys():
    keys = []

    def keep(k):
        if k not in keys:
            keys.append(k)
    for f in sorted(APP.glob('*.py')):
        tree = ast.parse(f.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, 'id', None) == 't' and node.args:
                arg = node.args[0]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    keep(arg.value)
                elif isinstance(arg, ast.IfExp):
                    for v in (arg.body, arg.orelse):
                        if isinstance(v, ast.Constant):
                            keep(v.value)
    import gr4_lutsmith as gl
    from lutsmith_app import i18n, logic, main
    for title, sub in main.STEPS:
        keep(title); keep(sub)
    for v in logic.STAGES.values():
        keep(v)
    for k in ('good', 'approximate', 'poor', 'Chinese (Simplified)', 'Chinese (Traditional)', '{items} or {last}'):
        keep(k)
    for L in gl.CAMERA_LANGUAGES:
        if L not in ('Chinese-S', 'Chinese-T'):
            keep(L)
    for s in gl.SCRIPTS:
        keep(i18n.SCRIPT_KEYS.get(s[2], s[2]))
    for c in gl.COLORCHECKER:
        keep(c[0])
    return keys


def problems(keys, lang, table):
    out = []
    for k in keys:
        v = table.get(k)
        if v is None:
            out.append(('missing', k))
            continue
        if sorted(re.findall(r'\{\w+\}', k)) != sorted(re.findall(r'\{\w+\}', v)):
            out.append(('placeholders differ', k))
        if sorted(re.findall(r'</?\w+[^>]*>', k)) != sorted(re.findall(r'</?\w+[^>]*>', v)):
            out.append(('HTML differs', k))
        for w in KEEP:
            if w in k and w not in v and not (w == 'LUT' and 'LUT' in v.upper()):
                out.append((f'keep {w}', k))
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')   # texts in every script, on any console
    from PySide6.QtWidgets import QApplication
    QApplication(sys.argv[:1])
    keys = app_keys()
    files = {f.stem: json.loads(f.read_text(encoding='utf-8')) for f in (APP / 'assets' / 'i18n').glob('*.json')
             if f.stem != 'camera-words'}
    if '--missing' in sys.argv:
        missing = [k for k in keys if any(k not in tb for tb in files.values())]
        print(json.dumps(missing, ensure_ascii=False, indent=1))
        sys.exit(0)
    bad = 0
    for lang, table in sorted(files.items()):
        p = problems(keys, lang, table)
        bad += len(p)
        print(f'{lang:10s} {len(keys)} texts, {len(p)} problems' + ''.join(f'\n    {a}: {k!r}' for a, k in p[:5]))
    sys.exit(1 if bad else 0)
