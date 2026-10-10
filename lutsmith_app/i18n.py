"""The app's text in the camera's 21 languages. English text is the key; translations live in assets/i18n."""
import json
import re
from pathlib import Path

from PySide6.QtCore import QLocale

import gr4_lutsmith as gl

ASSETS = Path(__file__).resolve().parent / 'assets'      # also inside the packaged app

LANGS = list(gl.CAMERA_LANGUAGES)
ENDONYMS = {'Czech': 'Čeština', 'Danish': 'Dansk', 'Dutch': 'Nederlands', 'English': 'English', 'Finnish': 'Suomi',
            'French': 'Français', 'German': 'Deutsch', 'Greek': 'Ελληνικά', 'Hungarian': 'Magyar',
            'Italian': 'Italiano', 'Japanese': '日本語', 'Korean': '한국어', 'Polish': 'Polski',
            'Portuguese': 'Português', 'Russian': 'Русский', 'Chinese-S': '简体中文', 'Chinese-T': '繁體中文',
            'Spanish': 'Español', 'Swedish': 'Svenska', 'Thai': 'ไทย', 'Turkish': 'Türkçe'}
QT_LOCALE = {'Czech': 'cs_CZ', 'Danish': 'da_DK', 'Dutch': 'nl_NL', 'English': 'en_GB', 'Finnish': 'fi_FI',
             'French': 'fr_FR', 'German': 'de_DE', 'Greek': 'el_GR', 'Hungarian': 'hu_HU', 'Italian': 'it_IT',
             'Japanese': 'ja_JP', 'Korean': 'ko_KR', 'Polish': 'pl_PL', 'Portuguese': 'pt_PT', 'Russian': 'ru_RU',
             'Chinese-S': 'zh_CN', 'Chinese-T': 'zh_TW', 'Spanish': 'es_ES', 'Swedish': 'sv_SE', 'Thai': 'th_TH',
             'Turkish': 'tr_TR'}
EAST_ASIAN = ('Japanese', 'Chinese-S', 'Chinese-T', 'Korean')
# the engine's names for writing systems -> the app's wording (translated keys)
SCRIPT_KEYS = {'accented Latin': 'accented Latin letters', 'Greek': 'Greek letters', 'Cyrillic': 'Cyrillic letters',
               'Thai': 'Thai script', 'Korean': 'Korean Hangul'}
MONO = ('mono-standard', 'mono-soft', 'mono-solid')
HIDDEN = ('high-contrast',) + MONO

_tables = {}
for _f in (ASSETS / 'i18n').glob('*.json'):
    if _f.stem in LANGS:
        _tables[_f.stem] = json.loads(_f.read_text(encoding='utf-8'))
_camera_words = json.loads((ASSETS / 'i18n' / 'camera-words.json').read_text(encoding='utf-8'))


def _slot_names():
    """{language: {slot: the camera's own name}} from the release data (the stock text of every renamable slot)."""
    out = {L: {} for L in LANGS}
    for slot, s in gl.SLOT_DATA['names']['slots'].items():
        for row in s['languages']:
            out[row[0]][slot] = bytes.fromhex(row[4]).decode('utf-16-le').rstrip('\x00')
    return out


_slots = _slot_names()
current = 'English'


def set_language(lang):
    global current
    current = lang if lang in LANGS else 'English'


def t(key, **values):
    text = _tables.get(current, {}).get(key) or key
    if values:
        text = re.sub(r'\{(\w+)\}', lambda m: str(values[m.group(1)]) if m.group(1) in values else m.group(0), text)
    return text


def language_for(ui_languages):
    """The first of the computer's preferred languages (e.g. ['ja-JP', 'en']) that the camera has, else English."""
    for tag in ui_languages:
        low = tag.lower().replace('_', '-')
        if low.startswith('zh'):
            trad = any(x in low.split('-') for x in ('hant', 'tw', 'hk', 'mo'))
            return 'Chinese-T' if trad else 'Chinese-S'
        if low[:2] in gl.LOCALES:
            return gl.LOCALES[low[:2]]
    return 'English'


def system_language():
    """The computer's display language (its preferred-language list, not its region format) when the camera has it,
    else English."""
    return language_for(QLocale.system().uiLanguages())


def lang_label(lang):
    return t({'Chinese-S': 'Chinese (Simplified)', 'Chinese-T': 'Chinese (Traditional)'}.get(lang, lang))


def cam(key):
    """One of the camera's own menu words in the current language."""
    return _camera_words.get(current, {}).get(key) or _camera_words['English'][key]


def slot_name(slot):
    own = cam('Standard') if slot == 'mono-standard' else (_slots[current].get(slot) or _slots['English'][slot])
    return t('{name} (monochrome)', name=own) if slot in MONO else own


def slot_replaces(slot):
    own = cam('Standard') if slot == 'mono-standard' else (_slots[current].get(slot) or _slots['English'][slot])
    return t('the hidden monochrome {name} look', name=own) if slot in HIDDEN else t("RICOH's {name} look", name=own)


def locale():
    return QLocale(QT_LOCALE[current])


def num(x, digits=2):
    return '–' if x is None else locale().toString(float(x), 'f', digits)


def integer(n):
    return locale().toString(int(n))


def join_and(items):
    items = list(items)
    return locale().createSeparatedList(items) if items else ''


def join_or(items):
    items = list(items)
    if len(items) < 2:
        return ''.join(items)
    sep = '、' if current in EAST_ASIAN[:3] else ', '
    return t('{items} or {last}', items=sep.join(items[:-1]), last=items[-1])


def script_label(engine_label):
    return t(SCRIPT_KEYS.get(engine_label, engine_label))
