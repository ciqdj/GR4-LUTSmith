"""Checks that need no RICOH file (run in CI before every build):  uv run python tests/test_app.py
With GR4_FIRMWARE=/path/to/fwdc248b.bin it also runs the self-test against the official file."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
for _stream in (sys.stdout, sys.stderr):          # the checks print names in many scripts (Windows consoles are not UTF-8)
    _stream.reconfigure(encoding='utf-8', errors='replace')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from PySide6.QtWidgets import QApplication  # noqa: E402

app = QApplication(sys.argv[:1])
# keep the app's real settings (language, appearance, the first-open answer) out of the tests
import tempfile  # noqa: E402
from PySide6.QtCore import QCoreApplication, QSettings  # noqa: E402
QCoreApplication.setOrganizationName('GR4-LUTSmith-tests')
QCoreApplication.setApplicationName('GR4-LUTSmith-tests')
QSettings.setDefaultFormat(QSettings.Format.IniFormat)
QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, tempfile.mkdtemp(prefix='gr4-lutsmith-tests-'))
import gr4_lutsmith as gl  # noqa: E402
from lutsmith_app import i18n, logic, main as M, theme  # noqa: E402

failures = []


def check(name, ok, detail=''):
    print(('ok    ' if ok else 'FAIL  ') + name + (f' — {detail}' if detail and not ok else ''))
    if not ok:
        failures.append(name)


# the computer's language: its preferred-language list decides (not the region format)
for prefs, want in [(['en-US', 'zh-Hans-AU'], 'English'), (['ja-JP', 'en-US'], 'Japanese'), (['zh-Hant-TW'], 'Chinese-T'),
                    (['zh-Hans-CN'], 'Chinese-S'), (['zh-HK'], 'Chinese-T'), (['pt-BR'], 'Portuguese'),
                    (['fa-IR', 'de-DE'], 'German'), (['fa-IR'], 'English'), ([], 'English')]:
    check(f'language from {prefs}: {want}', i18n.language_for(prefs) == want, i18n.language_for(prefs))
check('tests use their own settings', 'gr4-lutsmith-tests' in QSettings().fileName().lower(), QSettings().fileName())

# translations: every text in every language, placeholders intact
r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'i18n_check.py')], capture_output=True, encoding='utf-8',
                   errors='replace', env=dict(os.environ, QT_QPA_PLATFORM='offscreen', PYTHONIOENCODING='utf-8'))
check('translations complete in all 21 languages', r.returncode == 0, r.stdout[-600:])

# the app's name check and the command line's agree
for name, slot, lang in [('Portra', 'vivid', 'English'), ('ハッセル', 'vivid', 'English'), ('ハッセル', 'vivid', 'Japanese'),
                         ('Müller', 'retro', 'German'), ('Film 😀', 'vivid', 'English'), ('A very long name x', 'retro', 'English'),
                         (' x', 'vivid', 'English'), ('Std', 'mono-standard', 'English'), ('Плёнка ハ', 'vivid', 'English')]:
    problem, question, notes = logic.name_messages(name, slot, lang)
    try:
        cli_notes, cli_q = gl.check_name(name, slot, lang)
        cli_problem = False
    except gl.Refused:
        cli_problem, cli_q, cli_notes = True, None, []
    check(f'name check agrees with the CLI: {name!r} on {slot} ({lang})',
          bool(problem) == cli_problem and bool(question) == bool(cli_q) and len(notes) == len(cli_notes))

# shared looks: damaged files are refused, a good one passes
good = json.loads((ROOT / 'examples' / 'film-1d.look.json').read_text(encoding='utf-8'))
with tempfile.TemporaryDirectory() as d:
    def case(label, data, ok):
        p = Path(d) / f'{label}.json'
        p.write_text(data if isinstance(data, str) else json.dumps(data))
        try:
            logic.check_shared(p)
            passed = True
        except logic.Problem:
            passed = False
        check(f'shared look {label}: {"accepted" if ok else "refused"}', passed == ok)
    case('good', good, True)
    case('not-json', 'hello {', False)
    case('no-matrix', {'curves': good.get('curves')}, False)
    case('matrix-range', dict(good, matrix_q13=[[40000, -31808, 0], [0, 8192, 0], [0, 0, 8192]]), False)
    case('curve-text', dict(good, curves=[['x'] * 256] * 3), False)
    case('slot-unknown', dict(good, slot='standard'), False)
    case('name-emoji', dict(good, name='Film 😀'), False)
    case('icon-broken', dict(good, slot='vivid', icon={'w': 40, 'h': 40, 'rgba': '!!'}), False)

# every page, in every language and both themes, draws without an error
errors = []
sys.excepthook = lambda *e: errors.append(e)
w = M.Window(); w.show()
for lang in i18n.LANGS:
    w.set_language(lang)
    for choice in ('day', 'night'):
        w.set_theme(choice)
        for step in range(5):
            w.go(step); app.processEvents()
        w.show_check(); app.processEvents()
check('every page draws in 21 languages, day and night', not errors, str(errors[:1]))
sys.excepthook = sys.__excepthook__
check('no test or preview controls in the app', not any(
    s in (ROOT / 'lutsmith_app' / f).read_text(encoding='utf-8') for f in ('main.py', 'widgets.py', 'logic.py')
    for s in ('Reopen confirmation', 'Use a sample', 'Try a damaged file', 'in this preview')))

# the fit started with real clicks, as a user starts it (short fits; no RICOH file needed)
import time  # noqa: E402
from PySide6.QtWidgets import QPushButton  # noqa: E402
_fit_args = logic.fit_args
logic.fit_args = lambda *a: (lambda ns: (setattr(ns, 'iters', 40), ns)[1])(_fit_args(*a))
w = M.Window(); w.show()
w.set_language('English')
w.S.fw_status, w.S.fw_data, w.S.fw_path = 'ok', b'', 'fwdc248b.bin'   # the firmware step is not needed for fitting
w.choose_lut(str(ROOT / 'examples' / 'film-1d.cube')); w.set_slot('vivid'); w.go(3); app.processEvents()


def click(text):
    hits = [b for b in w.findChildren(QPushButton) if b.text() == text and b.isVisible() and b.isEnabled()]
    if hits:
        hits[0].click()
    return bool(hits)


def settle(limit=300):
    t0 = time.time()
    while (w.S.fitting or w.tasks) and time.time() - t0 < limit:
        app.processEvents(); time.sleep(0.02)
    app.processEvents()


started = click('Start fit')
app.processEvents()
check('clicking Start fit starts a fit', started and (w.S.fitting or bool(w.tasks)), f'fitting={w.S.fitting} tasks={len(w.tasks)}')
settle()
check('the fit finishes and shows its result', not w.S.fitting and bool(w.S.fit and w.S.fit['kept']), str(w.S.fit and len(w.S.fit['kept'])))
click('Run 1 more turn'); app.processEvents(); settle()
check('Run 1 more turn adds a turn', bool(w.S.fit) and len(w.S.fit['history_turns']) == 2, str(w.S.fit and w.S.fit['history_turns']))
logic.fit_args = _fit_args

fw = os.environ.get('GR4_FIRMWARE')
if fw:
    data = logic.check_firmware(fw)
    check('official firmware and self-test (GR4_FIRMWARE)', gl.sha256(data) == gl.OFFICIAL_SHA256)
print('\n' + ('all checks passed' if not failures else f'{len(failures)} check(s) failed'))
sys.exit(1 if failures else 0)
