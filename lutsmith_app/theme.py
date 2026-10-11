"""Day and night colours (the approved design's tokens), fonts, and the style sheet built from them."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFontDatabase, QGuiApplication

from .i18n import ASSETS

DAY = dict(paper='#eceeeb', panel='#f8f9f7', ink='#1d2023', muted='#5d6560', rule='#c8cdc8',
           rail_bg='#dde3de', rail_ink='#1d2023', rail_dim='#59615c', rail_hover='rgba(29,32,35,0.05)',
           rail_current='#f8f9f7', rail_edge='#c8cdc8', rail_field='#f8f9f7',
           accent='#2f8f7d', accent_ink='#ffffff', good='#2f7d48', warn='#a86b12', bad='#b8433a',
           menu='#e3e8e4', menu_ink='#1d2023', menu_dim='#5d6560', menu_hover='rgba(29,32,35,0.05)',
           camera='#1e1e1e', select_bg='rgba(47,143,125,0.14)', focus='#1f6fd0', board='#151515')
NIGHT = dict(DAY, paper='#191c1e', panel='#222629', ink='#e5e8e5', muted='#9aa39d', rule='#363c3f',
             rail_bg='#0f1112', rail_ink='#e5e8e5', rail_dim='#7d857f', rail_hover='rgba(255,255,255,0.05)',
             rail_current='rgba(255,255,255,0.08)', rail_edge='#0f1112', rail_field='#0f1112',
             accent='#5cc0ab', accent_ink='#0d1a17', good='#63b67f', warn='#d9a04a', bad='#e07a70',
             menu='#101010', menu_ink='#f2f2f2', menu_dim='#a8a8a8', menu_hover='rgba(255,255,255,0.06)',
             camera='#101010', select_bg='rgba(92,192,171,0.14)', focus='#6aa7ff')

BODY, DISPLAY = 'Barlow', 'Barlow Semi Condensed'


def load_fonts():
    for f in sorted((ASSETS / 'fonts').glob('*.ttf')):
        QFontDatabase.addApplicationFont(str(f))


def is_night(choice):
    """choice: 'system', 'day' or 'night'."""
    if choice == 'system':
        return QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark
    return choice == 'night'


def colour(tokens, name):
    return QColor(tokens[name]) if not tokens[name].startswith('rgba') else _rgba(tokens[name])


def _rgba(v):
    r, g, b, a = [float(x) for x in v[5:-1].split(',')]
    c = QColor(int(r), int(g), int(b)); c.setAlphaF(a)
    return c


def style_sheet(k):
    """The whole window's look. Widgets choose a role with setProperty('role', …)."""
    CHEVRON = (ASSETS / 'ui' / f"chevron-{k['rail_ink'].lstrip('#')}.svg").as_posix()
    return f'''
* {{ font-family: "{BODY}"; font-size: 15px; color: {k['ink']}; }}
QMainWindow, #sheet, QScrollArea, QScrollArea > QWidget > QWidget {{ background: {k['paper']}; }}
QToolTip {{ background: {k['panel']}; color: {k['ink']}; border: 1px solid {k['rule']}; padding: 4px 6px; }}

#topbar {{ background: {k['rail_bg']}; border-bottom: 1px solid {k['rail_edge']}; }}
#topbar QLabel {{ color: {k['rail_ink']}; font-size: 13px; font-weight: 500; }}
#topbar #brand {{ font-family: "{DISPLAY}"; font-size: 22px; font-weight: 700; }}
#topbar #brandNote {{ color: {k['rail_dim']}; font-size: 13px; font-weight: 500; }}
#rail {{ background: {k['rail_bg']}; border-right: 1px solid {k['rail_edge']}; }}
#rail QLabel {{ color: {k['rail_dim']}; font-size: 13px; }}
#rail QPushButton {{ background: transparent; border: 1px solid {k['rail_dim']}; color: {k['rail_ink']};
  border-radius: 8px; padding: 0 10px; min-height: 30px; max-height: 30px; text-align: left; font-size: 13px; }}
#rail QPushButton:hover {{ border-color: {k['rail_ink']}; }}

QComboBox#language {{ background: {k['rail_field']}; color: {k['rail_ink']}; border: 1px solid {k['rail_dim']};
  border-radius: 8px; padding: 0 30px 0 12px; min-height: 30px; max-height: 30px; font-size: 14px; }}
QComboBox#language:hover {{ border-color: {k['rail_ink']}; }}
QComboBox#language::drop-down {{ border: 0; width: 28px; subcontrol-origin: padding; subcontrol-position: center right; }}
QComboBox#language::down-arrow {{ image: url({CHEVRON}); width: 12px; height: 8px; margin-right: 12px; }}
QComboBox#language QAbstractItemView {{ background: {k['panel']}; color: {k['ink']}; selection-background-color: {k['select_bg']};
  selection-color: {k['ink']}; border: 1px solid {k['rule']}; outline: 0; }}

/* segmented controls */
QPushButton[role="seg"] {{ background: {k['panel']}; border: 1px solid {k['rule']}; border-radius: 0; padding: 0 12px;
  min-height: 30px; max-height: 30px; font-size: 14px; }}
QPushButton[role="seg"][first="true"] {{ border-top-left-radius: 8px; border-bottom-left-radius: 8px; }}
QPushButton[role="seg"][last="true"] {{ border-top-right-radius: 8px; border-bottom-right-radius: 8px; }}
QPushButton[role="seg"]:checked {{ background: {k['ink']}; color: {k['paper']}; border-color: {k['ink']}; }}
#topbar QPushButton[role="seg"] {{ background: transparent; color: {k['rail_ink']}; border-color: {k['rail_dim']}; font-size: 13px; }}
#topbar QPushButton[role="seg"]:checked {{ background: {k['rail_ink']}; color: {k['rail_bg']}; border-color: {k['rail_ink']}; }}

/* buttons */
QPushButton {{ background: {k['panel']}; border: 1px solid {k['rule']}; border-radius: 8px; padding: 7px 14px; font-weight: 500; }}
QPushButton:hover {{ border-color: {k['muted']}; }}
QPushButton:disabled {{ color: {k['muted']}; border-color: {k['rule']}; }}
QPushButton[role="primary"] {{ background: {k['accent']}; border-color: {k['accent']}; color: {k['accent_ink']}; }}
QPushButton[role="primary"]:hover {{ background: {k['accent']}; border-color: {k['ink']}; }}
QPushButton[role="primary"]:disabled {{ background: {k['rule']}; border-color: {k['rule']}; color: {k['muted']}; }}
QPushButton[role="small"] {{ padding: 4px 10px; font-size: 14px; }}
QPushButton[role="quiet"] {{ color: {k['muted']}; }}
QPushButton[role="quiet"]:hover {{ color: {k['ink']}; }}

/* text */
QLabel[role="h2"] {{ font-family: "{DISPLAY}"; font-size: 30px; font-weight: 600; }}
QLabel[role="h3"] {{ font-family: "{DISPLAY}"; font-size: 18px; font-weight: 600; }}
QLabel[role="lede"] {{ color: {k['muted']}; }}
QLabel[role="hint"] {{ color: {k['muted']}; font-size: 13px; }}
QLabel[role="note"] {{ color: {k['muted']}; font-size: 14px; }}
QLabel[role="field"] {{ font-weight: 600; font-size: 14px; }}
QLabel[role="laneTitle"] {{ font-weight: 500; }}
QLabel[role="laneStatus"] {{ font-size: 14px; }}
QLabel[role="laneTitle"][dim="true"], QLabel[role="laneStatus"][dim="true"] {{ color: {k['muted']}; }}
QLabel[role="msg-bad"] {{ color: {k['bad']}; font-size: 14px; }}
QLabel[role="msg-warn"] {{ color: {k['warn']}; font-size: 14px; }}
QLabel[role="msg-good"] {{ color: {k['good']}; font-size: 14px; }}
QLabel[role="dt"] {{ color: {k['muted']}; }}
QLabel[role="sha"] {{ color: {k['muted']}; font-size: 13px; }}
QLabel[role="pill-good"], QLabel[role="pill-warn"], QLabel[role="pill-bad"], QLabel[role="pill-info"] {{
  border: 1px solid; border-radius: 11px; padding: 1px 9px; font-size: 13px; font-weight: 600; }}
QLabel[role="pill-good"] {{ color: {k['good']}; border-color: {k['good']}; }}
QLabel[role="pill-warn"] {{ color: {k['warn']}; border-color: {k['warn']}; }}
QLabel[role="pill-bad"] {{ color: {k['bad']}; border-color: {k['bad']}; }}
QLabel[role="pill-info"] {{ color: {k['accent']}; border-color: {k['accent']}; }}
QLabel[role="glyph"] {{ border: 1px solid {k['rule']}; border-radius: 4px; color: {k['muted']}; font-family: "{DISPLAY}";
  font-size: 11px; font-weight: 700; }}

/* boxes */
QFrame[role="box"] {{ background: {k['panel']}; border: 1px solid {k['rule']}; border-radius: 10px; }}
QFrame[role="menu"] {{ background: {k['menu']}; border-radius: 10px; }}
QFrame[role="strip"] {{ background: {k['menu']}; border-radius: 8px; }}
QFrame[role="drop"] {{ background: {k['panel']}; border: 2px dashed {k['rule']}; border-radius: 10px; }}
QFrame[role="drop"]:hover, QFrame[role="drop"][over="true"] {{ border-color: {k['accent']}; }}
QFrame[role="lockbar"] {{ background: {k['panel']}; border: 1px solid {k['rule']}; border-left: 3px solid {k['warn']}; border-radius: 8px; }}
QFrame[role="foot"] {{ border-top: 1px solid {k['rule']}; }}

QLineEdit, QSpinBox {{ background: {k['panel']}; border: 1px solid {k['rule']}; border-radius: 8px; padding: 7px 10px;
  selection-background-color: {k['accent']}; selection-color: {k['accent_ink']}; }}
QLineEdit:focus, QSpinBox:focus {{ border-color: {k['accent']}; }}
QLineEdit:disabled {{ color: {k['muted']}; }}
QCheckBox {{ spacing: 8px; font-size: 14px; }}
QProgressBar {{ background: {k['rule']}; border: 0; border-radius: 4px; max-height: 8px; min-height: 8px; }}
QProgressBar::chunk {{ background: {k['accent']}; border-radius: 4px; }}

QTableWidget {{ background: {k['panel']}; border: 1px solid {k['rule']}; border-radius: 10px; gridline-color: transparent;
  selection-background-color: {k['select_bg']}; selection-color: {k['ink']}; outline: 0; }}
QTableWidget::item {{ padding: 6px 10px; border-bottom: 1px solid {k['rule']}; }}
QHeaderView::section {{ background: {k['panel']}; color: {k['muted']}; border: 0; border-bottom: 1px solid {k['rule']};
  padding: 7px 10px; font-size: 13px; font-weight: 600; }}
QScrollBar:vertical {{ background: transparent; width: 10px; }}
QScrollBar::handle:vertical {{ background: {k['rule']}; border-radius: 5px; min-height: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}

QDialog#firstRun {{ background: {k['panel']}; }}
QDialog#firstRun QLabel[role="aside"] {{ color: {k['muted']}; font-size: 14px; }}
QDialog#firstRun QPushButton#frNo {{ color: {k['muted']}; }}
QDialog#firstRun QPushButton#frNo:hover {{ color: {k['ink']}; }}
'''
TOKENS = DAY                # the current theme; set by the window
