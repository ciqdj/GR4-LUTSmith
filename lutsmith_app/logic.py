"""What the window does, without the window: every decision goes through the gr4_lutsmith engine."""
import base64
import json
from pathlib import Path
from types import SimpleNamespace

import gr4_lutsmith as gl

from . import i18n
from .i18n import t

EXAMPLE_LOOK = i18n.ASSETS / 'selftest' / 'film-1d.look.json'


class Problem(Exception):
    """Something the user should see, already worded in their language."""


# ---------------------------------------------------------------- official firmware
def check_firmware(path):
    """The official 1.11 file's bytes after the self-test, or Problem."""
    data = Path(path).read_bytes()
    if gl.sha256(data) != gl.OFFICIAL_SHA256 or len(data) != gl.OFFICIAL_BYTES:
        kind = gl.inspect_firmware(data)['kind'] if len(data) < 64 * 1024 * 1024 else None
        if kind == 'lutsmith':
            raise Problem(t('This file was already changed by GR4-LUTSmith. Start from the unmodified 1.11 file.'))
        raise Problem(t("This is not RICOH's unmodified GR IV 1.11 firmware. Choose the unmodified file {file}, "
                        "version 1.11.", file='fwdc248b.bin'))
    out = gl.make_firmware(data, gl.load_look(EXAMPLE_LOOK), log=lambda _: None)
    if gl.sha256(out) != gl.SELFTEST_SHA256:
        raise Problem(t('The self-test failed: this copy of the app may be damaged. Download it again.'))
    return data


# ---------------------------------------------------------------- LUT and photo
def open_lut(path):
    try:
        lut = gl.Lut(path)
    except (gl.Refused, OSError, ValueError, UnicodeError):
        raise Problem(t('This file is not a .cube LUT the app can read.'))
    size = ' × '.join([str(lut.n)] * (3 if lut.kind == '3D' else 1))
    return dict(path=str(path), file=Path(path).name, kind=lut.kind,
                label=t('3D LUT, {size}', size=size) if lut.kind == '3D' else t('1D LUT, {size}', size=size))


# ---------------------------------------------------------------- shared looks
def check_shared(path):
    """A shared look.json, checked before anything else (same rules as `build`), with the reason in the user's
    language when it is refused."""
    try:
        o = json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError, UnicodeError):
        raise Problem(t('the file is damaged or not a look file (it is not readable JSON)'))
    if isinstance(o, dict) and 'look' in o and 'matrix_q13' not in o:
        o = dict(o['look'], scores=o.get('scores'))
    if not isinstance(o, dict) or 'matrix_q13' not in o:
        raise Problem(t('this is not a look file'))
    reasons = [('matrix_q13', 'its colour matrix is damaged or outside what the camera can take'),
               ('curves', 'its tone curves are damaged or outside what the camera can take'),
               ('hue_sectors', 'its hue sectors are damaged or outside what the camera can take'),
               ('post_matrix_q9', 'its colour after the curves is damaged or outside what the camera can take')]
    slot = o.get('slot') or gl.DEFAULT_SLOT
    if slot not in gl.SLOT_NAMES:
        raise Problem(t('it names a slot this version does not know ({slot})', slot=str(slot)[:40]))
    for key, reason in reasons:                    # pinpoint the part the engine would refuse
        if o.get(key) is None:
            continue
        probe = {'matrix_q13': [[8192, 0, 0], [0, 8192, 0], [0, 0, 8192]], 'slot': slot, key: o[key]}
        try:
            gl.check_look(probe)
        except (gl.Refused, ValueError, TypeError, KeyError, IndexError, AttributeError):
            raise Problem(t(reason))
    if o.get('name') is not None:
        if not isinstance(o['name'], str):
            raise Problem(t('its name is damaged'))
        if o['name'] and gl.name_report(o['name'], slot)['problem']:
            raise Problem(t('its name cannot be shown on {slot}', slot=i18n.slot_name(slot)))
    if o.get('icon'):
        if slot not in gl.SLOT_DATA['icons']['slots']:
            raise Problem(t('its icon cannot go on {slot}', slot=i18n.slot_name(slot)))
        try:
            ok = len(base64.b64decode(o['icon']['rgba'], validate=True)) == 6400 and o['icon']['w'] == o['icon']['h'] == 40
        except (ValueError, TypeError, KeyError):
            ok = False
        if not ok:
            raise Problem(t('its icon is damaged'))
    try:
        look = gl.load_look(path)                  # the engine's own check decides
    except gl.Refused:
        raise Problem(t('this is not a look file'))
    sc = look.get('scores') or {}
    fit = sc.get('fit') or {}
    return dict(look=look, file=Path(path).name, slot=slot, name=look.get('name') or '',
                e=fit.get('de00_mean'), p95=fit.get('de00_p95'), verdict=fit.get('verdict'),
                cc=(sc.get('colorchecker') or {}).get('de00_mean'), grey=(sc.get('greys') or {}).get('de00_mean'),
                photo=(sc.get('photo') or {}).get('de00_mean'),
                hue=bool((look.get('hue_sectors') or {}).get('matrices_q10')), post=bool(look.get('post_matrix_q9')),
                lut_file=Path(str((look.get('lut') or {}).get('file') or '')).name or None)


# ---------------------------------------------------------------- names
def name_messages(name, slot, language):
    """(refusal, question, notes) for a name, worded for the user."""
    if not name:
        return None, None, []
    r = gl.name_report(name, slot, language)
    sname = i18n.slot_name(slot)
    if r['problem'] == 'fixed':
        return t('{slot} cannot be renamed: it shares its name with the colour Standard look.', slot=sname), None, []
    if r['problem'] == 'space':
        return t('Remove the space at the start or end.'), None, []
    if r['problem'] == 'characters':
        chars = ' '.join(f'“{c}”' for c in r['detail'])
        return t("The camera cannot show {chars} in any of its languages. Use letters and characters of one of the "
                 "camera's languages.", chars=chars), None, []
    if r['problem'] == 'length':
        return t('{slot} takes names of up to {max} characters. This one has {n}.', slot=sname, max=r['most'],
                 n=len(name)), None, []
    scripts = i18n.join_and(i18n.script_label(s) for s in r['scripts'])
    question, notes = None, []
    if r['question']:
        if r['languages']:
            question = t('This name uses {scripts}. Your camera language is {lang}, so they may not show. They show '
                         'when the camera is set to {langs}.', scripts=scripts, lang=i18n.lang_label(language),
                         langs=i18n.join_or(i18n.lang_label(l) for l in r['languages']))
        else:
            question = t('This name uses {scripts}. Your camera language is {lang}, so they may not show. No single '
                         'camera language shows all of them.', scripts=scripts, lang=i18n.lang_label(language))
    elif r['scripts']:
        notes.append(t('Uses {scripts}: shown with the camera set to {lang}. If you switch to a language that does '
                       'not use them, they may not show.', scripts=scripts, lang=i18n.lang_label(language)))
    if r['long']:
        notes.append(t('Long names may be cut off on some screens.'))
    return None, question, notes


# ---------------------------------------------------------------- room
STUB_CURVES = [[0] * 256] * 3
STUB_POST = [[512, 0, 0], [0, 512, 0], [0, 0, 512]]


def room(looks):
    """{'need', 'free'} for looks: real look dicts, or estimates {'slot', 'post'} before a fit."""
    real = []
    for lk in looks:
        if 'matrix_q13' in lk:
            real.append(lk)
        else:
            real.append(dict(slot=lk['slot'], curves=STUB_CURVES, **({'post_matrix_q9': STUB_POST} if lk.get('post') else {})))
    return gl.room(real)


# ---------------------------------------------------------------- fitting
def fit_args(lut, space, dng, slot):
    """The settings one turn of fitting needs (as the command line gives them)."""
    return SimpleNamespace(lut=Path(lut), space=space, photo=Path(dng) if dng else None, curve='auto', iters=1500,
                           no_hue=False, slot=slot or gl.DEFAULT_SLOT, name=None, camera_language='English',
                           seed=None)


def new_fit_state():
    return dict(kept=[], history=[], history_turns=[], icon=None, name_accepted=False)


def run_turns(args, n, state, post, log):
    gl.run_turns(args, n, state, post, log=log)


STAGES = {'single': 'single tone curve', 'rg-b': 'two tone curves (R+G / B)', 'r-gb': 'two tone curves (R / G+B)',
          'rb-g': 'two tone curves (R+B / G)', 'rgb': 'three tone curves', 'hue': 'hue sectors'}


def progress_line(line, turn):
    """The engine's progress line in the user's words ('Turn 2: three tone curves, ΔE00 1.23'), or None."""
    import re
    m = re.match(r'\s*(single|rg-b|r-gb|rb-g|rgb|hue)\s+(\+ after.*?)?ΔE00 ([0-9.]+)', line)
    if not m:
        return None
    stage = t('colour after the curves') if m.group(2) else t(STAGES[m.group(1)])
    return t('Turn {n}: {stage}', n=turn, stage=stage) + f', ΔE00 {i18n.num(float(m.group(3)))}'


def result_rows(state):
    """Every result so far (kept ones carry their look), best first among the kept."""
    kept = {gl.result_name(r): r for r in state['kept']}
    best = gl.result_name(gl.recommended(state['kept'])) if state['kept'] else None
    rows = []
    for h in state['history']:
        rec = kept.get(h['result'])
        rows.append(dict(name=h['result'], rec=rec, kept=rec is not None, recommended=h['result'] == best,
                         e=h['e'], cc=h['cc'], grey=h['grey'], h=h['h'], score=h['fit_score']))
    return rows


def result_label(name):
    turn = name.split('-')[1]
    return t('Turn {n} with colour after the curves', n=turn) if name.endswith('after-curves') else t('Turn {n}', n=turn)


def board_patches(rec, lut_path, space):
    """[(patch name, LUT colour, camera colour, ΔE00)] for the ColorChecker."""
    import numpy as np
    y = np.array([c[1:] for c in gl.COLORCHECKER], float) / 255
    target = np.clip(gl.apply_lut(gl.Lut(lut_path), y, space), 0, 1)
    camera = np.clip(gl.render(gl.to_index(y), rec), 0, 1)
    d = gl.de00(gl.lab(target), gl.lab(camera))
    to8 = lambda v: tuple(int(round(x * 255)) for x in v)
    return [(gl.COLORCHECKER[i][0], to8(target[i]), to8(camera[i]), float(d[i])) for i in range(24)]


def photo_images(rec, dng, lut_path, space, max_side=900):
    """(without the look, the LUT, the camera with the look) for the photo, as (h, w, 3) arrays 0..1."""
    import numpy as np
    v = gl.photo_signal(dng, max_side=max_side)
    flat = v.reshape(-1, 3)
    base = gl.neutral(flat)
    lut = gl.apply_lut(gl.Lut(lut_path), base, space)
    cam = gl.render(flat, rec)
    shape = v.shape
    return tuple(np.clip(a.reshape(shape), 0, 1) for a in (base, lut, cam))


# ---------------------------------------------------------------- building
def finished_look(base, slot, name, icon_path, keep_icon, camera_language, accepted):
    """The look as it goes into the firmware: your slot, name and icon on the fitted or shared look."""
    look = gl.adapt_look(base, slot=slot, name=name or None, no_name=not name,
                         icon=icon_path if icon_path else None, no_icon=not icon_path and not keep_icon)
    if name:
        look['camera_language'] = camera_language
        look.pop('name_accepted', None)
        if accepted:
            look['name_accepted'] = True
    return look


def build(source, looks):
    return gl.make_firmware(source, looks, log=lambda _: None)


def inspect(path):
    return gl.inspect_firmware(Path(path).read_bytes())
