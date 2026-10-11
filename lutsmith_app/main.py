"""The GR4-LUTSmith window: a top bar with the window-wide settings, the steps on the left, the current step's page."""
import base64
import json
import sys
from pathlib import Path

from PySide6.QtCore import QSettings, Qt, QTimer
from PySide6.QtGui import QFont, QGuiApplication, QIcon, QImage
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog, QFileDialog, QFrame, QGraphicsOpacityEffect,
                               QGridLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMainWindow, QProgressBar,
                               QScrollArea, QSizePolicy, QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

import gr4_lutsmith as gl

from . import i18n, logic, theme
from .i18n import t
from .widgets import (Board, Compare, DropZone, IconTile, Meter, Segmented, SlotButton, StepButton, Toast, add, box,
                      button, facts, filecard, glyph, label, pill, qimage_from_pil, qimage_from_rgb, row, set_role)
from .workers import Task

STEPS = [('Official firmware', 'From your own camera'), ('LUT and photo', 'What to put in'),
         ('Slot, name, icon', 'Where it goes'), ('Fit', 'How close it gets'), ('Build', 'The file for your card')]
FIRMWARE_FILTER = 'fwdc248b.bin (*.bin)'


class State:
    def __init__(self):
        self.step, self.view = 0, 'steps'
        self.fw_path = self.fw_data = None
        self.fw_status = None                        # None, 'checking', 'ok' or a problem (text)
        self.source = 'lut'
        self.shared = self.shared_error = None
        self.lut = None
        self.lut_error = None
        self.space = 'srgb'
        self.dng = None
        self.reset_look()
        self.basket = []                             # finished looks: dict(look=…, lut=…, shared=bool)
        self.built = None                            # (bytes, sha)
        self.check_file = self.check_result = None

    def reset_look(self):
        self.slot, self.name, self.name_accepted = None, '', False
        self.icon_path, self.icon_image, self.keep_shared_icon = None, None, True
        self.turns, self.after = 1, False
        self.fit = None                              # the fit's state (kept results, history)
        self.selected = None
        self.fitting = False
        self.fit_log = []
        self.photo = None                            # cached photo images (without the look, the LUT)
        self.photo_cam = {}                          # result name -> camera image


class FirstRun(QDialog):
    """Shown once: the user confirms where the firmware comes from."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName('firstRun')
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        self.setWindowTitle('GR4-LUTSmith')
        self.setMinimumWidth(460)
        self.setMaximumWidth(520)
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(24, 22, 24, 20)
        self.lay.setSpacing(12)
        self.show_question()

    def clear(self):
        while self.lay.count():
            it = self.lay.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
            elif it.layout():
                while it.layout().count():
                    w = it.layout().takeAt(0).widget()
                    if w:
                        w.deleteLater()

    def heading(self, text):
        h = label(text)
        f = h.font(); f.setPixelSize(17); f.setWeight(QFont.Weight.Medium); h.setFont(f)
        return h

    def show_question(self):
        self.clear()
        self.lay.addWidget(self.heading(t('Before you start')))
        self.lay.addWidget(label(t('Firmware downloaded from RICOH and firmware extracted from the camera are the same, '
                                   'and GR4-LUTSmith works with both.')))
        self.lay.addWidget(label(t("In line with RICOH's software distribution terms, please confirm that the firmware "
                                   "you will use was extracted directly from your own RICOH GR IV, in its original "
                                   "factory-shipped condition, with firmware version 1.11."), 'aside'))
        no = button(t('Cancel'), slot=self.show_declined); no.setObjectName('frNo')
        yes = button(t('Confirm'), 'primary', self.accept); yes.setObjectName('frYes')
        yes.setDefault(True); yes.setAutoDefault(True)
        self.lay.addSpacing(6)
        self.lay.addWidget(row(None, spacing=10, stretch_end=False) if False else self.buttons(no, yes))
        yes.setFocus()

    def buttons(self, *bs):
        w = QWidget()
        h = QHBoxLayout(w); h.setContentsMargins(0, 0, 0, 0); h.setSpacing(10); h.addStretch(1)
        for b in bs:
            h.addWidget(b)
        return w

    def show_declined(self):
        self.clear()
        self.lay.addWidget(self.heading(t('Confirmation needed')))
        self.lay.addWidget(label(t('GR4-LUTSmith can only be used with firmware extracted directly from your own '
                                   'camera in its original factory-shipped condition.')))
        back = button(t('Back'), slot=self.show_question); back.setDefault(True)
        self.lay.addSpacing(6)
        self.lay.addWidget(self.buttons(back))

    def reject(self):                                # Esc and the window's close do not skip the question
        pass


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings()                    # the app's own (set in main(); tests use a separate place)
        self.S = State()
        self.tasks = []
        i18n.set_language(self.settings.value('language') or i18n.system_language())
        self.theme_choice = self.settings.value('theme') or 'system'
        self.setWindowTitle(f'GR4-LUTSmith {gl.VERSION}')
        self.setMinimumSize(1060, 720)
        self.resize(1240, 860)
        root = QWidget(); self.setCentralWidget(root)
        outer = QVBoxLayout(root); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)
        self.outer = outer
        self.topbar = QFrame(); outer.addWidget(self.topbar)
        body = QHBoxLayout(); body.setContentsMargins(0, 0, 0, 0); body.setSpacing(0)
        outer.addLayout(body, 1)
        self.body = body
        self.rail = QFrame(); body.addWidget(self.rail)
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True); self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        body.addWidget(self.scroll, 1)
        self.toast = Toast(root)
        QGuiApplication.styleHints().colorSchemeChanged.connect(lambda _: self.apply_theme())
        self.apply_theme(render=False)
        self.render()

    # ------------------------------------------------------------ window-wide
    def apply_theme(self, render=True):
        theme.TOKENS = theme.NIGHT if theme.is_night(self.theme_choice) else theme.DAY
        QApplication.instance().setStyleSheet(theme.style_sheet(theme.TOKENS))
        if render:
            self.render()

    def say(self, text):
        self.toast.show_text(text)

    def run_task(self, fn, done, failed=None, progress=None, stopped=None):
        task = Task(fn, self)
        task.succeeded.connect(done)
        task.failed.connect(failed or (lambda msg: (self.say(msg), self.render())))
        if progress:
            task.progress.connect(progress)
        if stopped:
            task.stopped.connect(stopped)
        task.finished.connect(lambda: self.tasks.remove(task) if task in self.tasks else None)
        self.tasks.append(task)
        task.start()
        return task

    def swap(self, old, new, layout):
        """Put a freshly built part of the window in place of the old one."""
        layout.replaceWidget(old, new)
        old.hide()
        old.deleteLater()
        new.show()
        return new

    def build_topbar(self):
        bar = QFrame(); bar.setObjectName('topbar')
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(20, 12, 20, 12); lay.setSpacing(12)
        brand = QLabel('GR4-LUTSmith'); brand.setObjectName('brand')
        note = QLabel(t('for RICOH GR IV, firmware 1.11')); note.setObjectName('brandNote')
        lay.addWidget(brand); lay.addWidget(note, 0, Qt.AlignmentFlag.AlignBottom); lay.addStretch(1)
        lab = QLabel(t('App and camera language'))
        combo = QComboBox(); combo.setObjectName('language')
        for L in i18n.LANGS:
            combo.addItem(i18n.ENDONYMS[L], L)
        combo.setCurrentIndex(i18n.LANGS.index(i18n.current))
        combo.setToolTip(t('Names in the camera menu are checked against this language.'))
        combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        combo.currentIndexChanged.connect(lambda i: self.set_language(i18n.LANGS[i]))
        lab.setBuddy(combo)
        lay.addWidget(lab); lay.addWidget(combo); lay.addSpacing(16)
        lay.addWidget(QLabel(t('Appearance')))
        seg = Segmented([('system', t('System')), ('day', t('Day')), ('night', t('Night'))], self.theme_choice)
        seg.changed.connect(self.set_theme)
        lay.addWidget(seg)
        self.topbar = self.swap(self.topbar, bar, self.outer)        # filled first, so it appears complete

    def set_language(self, lang):
        if lang == i18n.current:
            return
        i18n.set_language(lang)
        self.settings.setValue('language', lang)
        self.S.name_accepted = False
        self.render()
        self.say(t('Language: {lang}', lang=i18n.ENDONYMS[lang]))

    def set_theme(self, choice):
        self.theme_choice = choice
        self.settings.setValue('theme', choice)
        self.apply_theme()

    # ------------------------------------------------------------ steps
    def name_blocked(self):
        S = self.S
        if not S.slot or not S.name:
            return False
        problem, question, _ = logic.name_messages(S.name, S.slot, i18n.current)
        return bool(problem) or (bool(question) and not S.name_accepted)

    def skipped(self, i):
        return self.S.source == 'shared' and i in (1, 3)

    def done(self, i):
        S = self.S
        return [S.fw_status == 'ok' and (S.source == 'lut' or bool(S.shared)), bool(S.lut),
                bool(S.slot) and not self.name_blocked(), bool(S.fit and S.fit['kept']), bool(S.built)][i]

    def first_open(self):
        for i in range(4):
            if not self.skipped(i) and not self.done(i):
                return i
        return 4

    def locked(self, i):
        if i == 4 and self.S.basket and self.S.fw_status == 'ok':
            return False
        return i > self.first_open()

    def go(self, i):
        self.S.view, self.S.step = 'steps', i
        self.render()
        self.scroll.verticalScrollBar().setValue(0)

    def build_rail(self):
        rail = QFrame(); rail.setObjectName('rail'); rail.setFixedWidth(236)
        lay = QVBoxLayout(rail)
        lay.setContentsMargins(16, 20, 16, 20); lay.setSpacing(2)
        for i, (title, sub) in enumerate(STEPS):
            skip = self.skipped(i)
            state = 'skip' if skip else 'done' if self.done(i) and not (self.S.view == 'steps' and self.S.step == i) \
                else 'ahead' if self.locked(i) else 'open'
            current = self.S.view == 'steps' and self.S.step == i
            b = StepButton(i + 1, t(title), t('Not needed: shared look') if skip else t(sub),
                           'open' if current else state, current)
            if not skip:
                b.clicked.connect(lambda _=False, k=i: self.go(k))
            lay.addWidget(b)
        lay.addSpacing(32)
        n = len(self.S.basket)
        lay.addWidget(label(t('Looks in this firmware: {n}', n=n) if n else t('No looks in this firmware yet.'), wrap=True))
        lay.addSpacing(6)
        chk = button(t('Check a firmware file'), slot=self.show_check)
        lay.addWidget(chk)
        lay.addStretch(1)
        self.rail = self.swap(self.rail, rail, self.body)            # filled first, so it appears complete

    def show_check(self):
        self.S.view = 'check'
        self.render()

    def render(self):
        self.build_topbar()
        self.build_rail()
        page = QWidget(); page.setObjectName('sheet')
        lay = QVBoxLayout(page); lay.setContentsMargins(48, 36, 48, 36); lay.setSpacing(24)
        S = self.S
        if S.view == 'check':
            content = self.page_check()
        else:
            content = [self.page_firmware, self.page_lut, self.page_slot, self.page_fit, self.page_build][S.step]()
        if S.view == 'steps' and self.locked(S.step):
            o = self.first_open()
            bar = QFrame(); set_role(bar, 'lockbar')
            h = QHBoxLayout(bar); h.setContentsMargins(16, 10, 12, 10)
            h.addWidget(label(t('Finish {step} first.', step=f'<b>{o + 1}. {t(STEPS[o][0])}</b>'), rich=True), 1)
            h.addWidget(button(t('Go to {step}', step=t(STEPS[o][0])), 'primary', lambda: self.go(o)))
            lay.addWidget(bar)
            content.setEnabled(False)
            eff = QGraphicsOpacityEffect(content); eff.setOpacity(0.5); content.setGraphicsEffect(eff)
        lay.addWidget(content)
        lay.addStretch(1)
        old = self.scroll.takeWidget()
        if old:
            old.hide()
            old.deleteLater()
        self.scroll.setWidget(page)

    # ------------------------------------------------------------ page parts
    def head(self, title, lede=None, rich=False):
        w = QWidget(); v = QVBoxLayout(w); v.setContentsMargins(0, 0, 0, 0); v.setSpacing(8)
        v.addWidget(label(title, 'h2'))
        if lede:
            l = label(lede, 'lede', rich=rich)
            line = QHBoxLayout(); line.setContentsMargins(0, 0, 0, 0)
            line.addWidget(l, 7); line.addStretch(3)              # about 70 characters a line
            v.addLayout(line)
        return w

    def nav(self, back, nxt, next_label, enabled=True):
        f = QFrame(); set_role(f, 'foot')
        h = QHBoxLayout(f); h.setContentsMargins(0, 16, 0, 0)
        if back is not None:
            h.addWidget(button(t('Back'), slot=lambda: self.go(back)))
        h.addStretch(1)
        if nxt is not None:
            b = button(next_label, 'primary', lambda: self.go(nxt), enabled)
            b.setObjectName('next')
            h.addWidget(b)
        self.next_button = f.findChild(type(button('')), 'next')
        return f

    @staticmethod
    def page(*parts):
        w = QWidget(); v = QVBoxLayout(w); v.setContentsMargins(0, 0, 0, 0); v.setSpacing(20)
        for p in parts:
            add(v, p)
        return w

    @staticmethod
    def grid2(a, b):
        w = QWidget(); g = QGridLayout(w); g.setContentsMargins(0, 0, 0, 0); g.setSpacing(16)
        g.addWidget(a, 0, 0, Qt.AlignmentFlag.AlignTop); g.addWidget(b, 0, 1, Qt.AlignmentFlag.AlignTop)
        g.setColumnStretch(0, 1); g.setColumnStretch(1, 1)
        return w

    # ------------------------------------------------------------ 1 firmware
    def page_firmware(self):
        S = self.S
        parts = [self.head(t("Start from your camera's firmware"),
                           t("Choose the file {file} that you extracted from your own GR IV, in its original "
                             "factory-shipped condition with version 1.11. The app checks that it is RICOH's unmodified "
                             "1.11 and runs its self-test. Nothing is changed on your computer.",
                             file='<b>fwdc248b.bin</b>'), rich=True)]
        if S.fw_status in (None,) or (S.fw_status not in ('ok', 'checking')):
            dz = DropZone(t('Choose {file}', file='fwdc248b.bin'), t('or drop it here'), FIRMWARE_FILTER)
            dz.chosen.connect(self.choose_firmware)
            parts.append(dz)
            if S.fw_status not in (None, 'ok', 'checking'):
                parts.append(label(S.fw_status, 'msg-bad'))
        else:
            checking = S.fw_status == 'checking'
            card = filecard(glyph('BIN'), Path(S.fw_path).name,
                            t('Checking…') if checking else t('RICOH GR IV 1.11, official; self-test passed'),
                            pill(t('Checking'), 'info') if checking else pill(t('Verified'), 'good'))
            parts.append(box(card, label(t('The camera must already be on firmware 1.11. Charge the battery fully '
                                           'before you install anything.'), 'note'),
                             row(button(t('Choose another file'), 'small', self.forget_firmware, not checking))))
            if S.fw_status == 'ok':
                parts.append(self.source_box())
        shared = S.source == 'shared'
        parts.append(self.nav(None, 2 if shared else 1, t('Next: slot, name, icon') if shared else t('Next: LUT and photo'),
                              S.fw_status == 'ok' and (not shared or bool(S.shared))))
        return self.page(*parts)

    def choose_firmware(self, path):
        S = self.S
        S.fw_path, S.fw_status, S.fw_data, S.built = path, 'checking', None, None
        self.render()

        def ok(data):
            S.fw_data, S.fw_status = data, 'ok'
            self.render()
            self.say(t('Official firmware verified'))

        def bad(msg):
            S.fw_status = msg
            self.render()
        self.run_task(lambda _: logic.check_firmware(path), ok, bad)

    def forget_firmware(self):
        self.S.fw_path = self.S.fw_data = self.S.fw_status = None
        self.S.built = None
        self.render()

    def source_box(self):
        S = self.S
        seg = Segmented([('lut', t('A LUT to fit')), ('shared', t('A shared look (.json)'))], S.source)
        seg.changed.connect(self.set_source)
        parts = [label(t('What do you start from?'), 'h3'), seg,
                 label(t('Fit your own .cube LUT. Takes a few minutes per turn.') if S.source == 'lut' else
                       t('A look.json someone shared already holds a finished look: no LUT and no fitting needed. '
                         'Any file name works.'), 'hint')]
        if S.source == 'shared':
            if S.shared:
                parts.append(self.shared_card())
            else:
                dz = DropZone(t('Choose a shared look (.json)'), t('or drop it here. It is checked before anything else.'),
                              'look (*.json)')
                dz.chosen.connect(self.choose_shared)
                parts.append(dz)
                if S.shared_error:
                    parts.append(label(t('{file} cannot be used: {why}. Nothing was changed. Ask its maker for the file '
                                         'again.', file=S.shared_error[0], why=S.shared_error[1]), 'msg-bad'))
        return box(*parts)

    def set_source(self, source):
        S = self.S
        if S.source == source:
            return
        S.source, S.built, S.shared_error = source, None, None
        if source == 'lut' and S.shared:
            S.shared = None
            S.reset_look()
        self.render()

    def choose_shared(self, path):
        S = self.S
        try:
            sh = logic.check_shared(path)
        except logic.Problem as exc:
            S.shared_error = (Path(path).name, str(exc))
            self.render()
            return
        S.shared, S.shared_error, S.lut, S.built = sh, None, None, None
        S.reset_look()
        S.slot = sh['slot'] if not any(b['look']['slot'] == sh['slot'] for b in S.basket) else None
        S.name = sh['name']
        self.render()
        self.say(t('Shared look checked'))

    def shared_card(self):
        sh, S = self.S.shared, self.S
        hint = (t('fitted from {file}', file=sh['lut_file']) if sh['lut_file'] else t('a fitted look')) \
            + (' · ' + t('hue sectors') if sh['hue'] else '') + (' · ' + t('colour after the curves') if sh['post'] else '')
        parts = [filecard(glyph('JSON'), sh['file'], hint, button(t('Choose another file'), 'small', self.forget_shared))]
        v = sh['verdict']
        if v:
            parts.append(row(pill(t(v), {'good': 'good', 'approximate': 'warn'}.get(v, 'bad')),
                             label(t('How close the look gets to its LUT, as measured by its maker. Lower is closer.'), 'hint')))
            pairs = [(t('Whole range'), f'ΔE00 {i18n.num(sh["e"])} (p95 {i18n.num(sh["p95"])})'),
                     ('ColorChecker', i18n.num(sh['cc'])), (t('Greys'), i18n.num(sh['grey']))]
            if sh['photo'] is not None:
                pairs.append((t("Maker's photo"), i18n.num(sh['photo'])))
            parts.append(facts(pairs))
        else:
            parts.append(label(t('This file has no fit results to show. It can still be built.'), 'note'))
        slot = f'<b>{i18n.slot_name(sh["slot"])}</b>'
        has_icon = bool(sh['look'].get('icon'))
        if sh['name']:
            chose = t('Its maker chose {slot}, named “{name}”, with an own icon.' if has_icon else
                      'Its maker chose {slot}, named “{name}”.', slot=slot, name=html(sh['name']))
        else:
            chose = t('Its maker chose {slot}, with an own icon.' if has_icon else 'Its maker chose {slot}.', slot=slot)
        parts.append(label(chose + ' ' + t("You can change any of it in the next step. The firmware is the same as the "
                                             "maker's for the same choices."), 'note', rich=True))
        return box(*parts, margins=14)

    def forget_shared(self):
        self.S.shared = None
        self.S.reset_look()
        self.render()

    # ------------------------------------------------------------ 2 LUT and photo
    def page_lut(self):
        S = self.S
        lut_parts = [label('LUT', 'h3')]
        if S.lut:
            lut_parts.append(filecard(glyph('CUBE'), S.lut['file'], S.lut['label'],
                                      button(t('Change'), 'small', self.forget_lut)))
        else:
            dz = DropZone(t('Choose a .cube file'), t('or drop it here'), 'LUT (*.cube)')
            dz.chosen.connect(self.choose_lut)
            lut_parts.append(dz)
            if S.lut_error:
                lut_parts.append(label(S.lut_error, 'msg-bad'))
        seg = Segmented([('srgb', 'sRGB'), ('adobe', 'Adobe RGB')], S.space)
        seg.changed.connect(self.set_space)
        lut_parts += [label(t('The LUT was made for'), 'hint'), seg]
        dng_parts = [label(f'{t("Your photo")} <span style="font-weight:400">{t("(optional)")}</span>', 'h3', rich=True)]
        if S.dng:
            dng_parts.append(filecard(glyph('DNG'), Path(S.dng).name, t('Half joins the fit, half stays aside to check it'),
                                      button(t('Remove'), 'small', self.forget_dng)))
        else:
            dz = DropZone(t('Choose a DNG from your GR IV'), t('Everyday content works best: people, sky, foliage.'),
                          'DNG (*.dng *.DNG)')
            dz.chosen.connect(self.choose_dng)
            dng_parts.append(dz)
        return self.page(
            self.head(t('Choose your LUT'), t('A creative {cube} LUT made for normal pictures (sRGB or Adobe RGB). Log LUTs '
                                              'with gamma are not supported. A DNG from your GR IV is optional but helps: '
                                              'the fit is then checked on real content.', cube='<b>.cube</b>'), rich=True),
            self.grid2(box(*lut_parts), box(*dng_parts)),
            self.nav(0, 2, t('Next: slot, name, icon'), bool(S.lut)))

    def choose_lut(self, path):
        S = self.S
        try:
            S.lut, S.lut_error = logic.open_lut(path), None
        except logic.Problem as exc:
            S.lut, S.lut_error = None, str(exc)
        self.clear_fit()
        self.render()

    def forget_lut(self):
        self.S.lut = None
        self.clear_fit()
        self.render()

    def set_space(self, space):
        self.S.space = space
        self.clear_fit()
        self.render()

    def choose_dng(self, path):
        self.S.dng = path
        self.clear_fit()
        self.render()

    def forget_dng(self):
        self.S.dng = None
        self.clear_fit()
        self.render()

    def clear_fit(self):
        S = self.S
        S.fit, S.selected, S.photo, S.photo_cam, S.fit_log, S.built = None, None, None, {}, [], None

    # ------------------------------------------------------------ 3 slot, name, icon
    def own_icon(self):
        """The icon the slot will get, as an image (your picture, or the shared look's), or None (the camera's)."""
        S = self.S
        if S.icon_image is not None:
            return S.icon_image
        icon = (S.shared or {}).get('look', {}).get('icon') if S.shared and S.keep_shared_icon else None
        if icon:
            raw = base64.b64decode(icon['rgba'])
            return QImage(raw, 40, 40, 160, QImage.Format.Format_RGBA8888).copy()
        return None

    def page_slot(self):
        S = self.S
        lede = t('The picture comes out the same in every slot. The slot only decides which look you give up, the '
                 'sliders you keep, and the longest name it takes.')
        if S.shared:
            lede += ' ' + t("The shared look starts with its maker's choices; change any of them.")
        menu = QFrame(); set_role(menu, 'menu')
        grid = QGridLayout(menu); grid.setContentsMargins(12, 12, 12, 12); grid.setSpacing(6)
        taken = {b['look']['slot'] for b in S.basket}
        own = self.own_icon()
        for i, slot in enumerate(gl.SLOT_ORDER):
            info = gl.SLOT_INFO[slot]
            sub = t('already has a look') if slot in taken else t('default') if slot == gl.DEFAULT_SLOT else \
                t('stills and movie') if info[1] else t('stills only')
            b = SlotButton(slot, i18n.slot_name(slot), sub, S.slot == slot, own)
            b.setEnabled(slot not in taken)
            b.clicked.connect(lambda _=False, s=slot: self.set_slot(s))
            grid.addWidget(b, i // 5, i % 5)
        for c in range(5):
            grid.setColumnStretch(c, 1)
        menu.setAccessibleName(i18n.cam('Image Control'))
        parts = [self.head(t('Choose the slot your look replaces'), lede), menu]
        if S.slot:
            parts.append(self.grid2(self.slot_info(), self.name_and_icon()))
            parts.append(self.room_box())
        shared = S.source == 'shared'
        parts.append(self.nav(0 if shared else 1, 4 if shared else 3, t('Next: build') if shared else t('Next: fit'),
                              bool(S.slot) and not self.name_blocked()))
        return self.page(*parts)

    def set_slot(self, slot):
        S = self.S
        S.slot = slot
        most = gl.name_slot_limit(slot)
        if most and len(S.name) > most:
            self.say(t('{slot} takes up to {max} characters', slot=i18n.slot_name(slot), max=most))
        S.built = None
        self.render()

    def slot_info(self):
        slot = self.S.slot
        info = gl.SLOT_INFO[slot]
        most = gl.name_slot_limit(slot)
        extra = i18n.join_and([i18n.cam('Saturation'), i18n.cam('Hue')]) if info[2] != '-' else '—'
        return box(label(i18n.slot_name(slot), 'h3'),
                   facts([(t('Replaces'), i18n.slot_replaces(slot)),
                          (t('Movie'), t('yes') if info[1] else t('no, stills only')),
                          (t('Extra sliders'), extra),
                          (t('Own name'), t('up to {max} characters', max=most) if most else t('not possible')),
                          (t('Own icon'), t('yes') if slot in gl.SLOT_DATA['icons']['slots'] else t('not possible'))]),
                   label(t('Your look opens with every slider at 0 and grain off.'), 'note'))

    def name_and_icon(self):
        S = self.S
        slot = S.slot
        most = gl.name_slot_limit(slot)
        edit = QLineEdit(S.name)
        edit.setPlaceholderText(i18n.slot_name(slot))
        edit.setMaxLength(40)
        edit.setEnabled(bool(most))
        count, msg = label('', 'hint'), label('')
        confirm = QCheckBox(t('Use this name anyway'))
        confirm.setChecked(S.name_accepted)

        def update():
            problem, question, notes = logic.name_messages(S.name, slot, i18n.current)
            count.setText(t('{n} of {max} characters', n=len(S.name), max=most) if most else '')
            text = problem or question or ' '.join(notes) or ('' if S.name else t('Leave empty to keep the stock name.'))
            set_role(msg, 'msg-bad' if problem else 'msg-warn' if question or notes else 'hint')
            msg.setText(text)
            msg.setVisible(bool(text))
            confirm.setVisible(bool(question))
            nxt = self.findChild(QWidget, 'next')
            if nxt:
                nxt.setEnabled(not self.name_blocked())
            self.build_rail()

        def changed(text):
            S.name, S.name_accepted, S.built = text, False, None
            confirm.setChecked(False)
            update()

        def accepted(on):
            S.name_accepted = on
            update()
        edit.textChanged.connect(changed)
        confirm.toggled.connect(accepted)
        QTimer.singleShot(0, update)
        strip = QFrame(); set_role(strip, 'strip'); strip.setFixedHeight(100)
        sh = QHBoxLayout(strip); sh.setContentsMargins(10, 10, 10, 10); sh.setSpacing(10)
        sh.addWidget(IconTile(slot, self.own_icon(), 80))
        for other in [s for s in ('mono-standard', 'vivid', 'positive-film', 'cinema-yellow') if s != slot][:3]:
            sh.addWidget(IconTile(other, None, 80))
        sh.addStretch(1)
        can_icon = slot in gl.SLOT_DATA['icons']['slots']
        pick = button(t('Choose a picture'), 'small', self.choose_icon, can_icon)
        stock = button(t('Keep the stock icon'), 'small', self.stock_icon, self.own_icon() is not None)
        name_label = label(t('Name in the camera menu'), 'field')
        name_label.setBuddy(edit)
        return box(name_label, edit, count, msg, confirm, 6, label(t('Icon'), 'field'), strip, row(pick, stock),
                   label(t('Any picture. It becomes 40 × 40 pixels; a non-square picture keeps its centre.'), 'hint'))

    def choose_icon(self):
        path, _ = QFileDialog.getOpenFileName(self, '', '', 'Pictures (*.png *.jpg *.jpeg *.gif *.bmp *.tif *.tiff *.webp)')
        if not path:
            return
        try:
            img = gl.make_icon(path, (40, 40))
        except gl.Refused:
            self.say(t('That file is not a picture the app can read'))
            return
        self.S.icon_path, self.S.icon_image, self.S.built = path, qimage_from_pil(img), None
        self.render()
        self.say(t('Icon ready: 40 × 40'))

    def stock_icon(self):
        S = self.S
        S.icon_path, S.icon_image, S.keep_shared_icon, S.built = None, None, False, None
        self.render()

    def current_estimate(self):
        """The look being made, for the room meter (the real look when there is one)."""
        S = self.S
        if not S.slot:
            return []
        if S.shared:
            return [dict(S.shared['look'], slot=S.slot)]
        rec = self.selected_record()
        if rec:
            return [dict(rec, slot=S.slot)]
        return [dict(slot=S.slot, post=S.after)]

    def room_box(self):
        S = self.S
        looks = [b['look'] for b in S.basket if b['look']['slot'] != S.slot] + self.current_estimate()
        r = logic.room(looks)
        hc = any(lk['slot'] == gl.DEFAULT_SLOT for lk in looks)
        over = r['need'] > r['free']
        head = row(label(t('Room for looks in this firmware'), 'h3', wrap=False), stretch_end=True)
        head.layout().addWidget(label(t('{used} of {total} bytes', used=i18n.integer(r['need']),
                                        total=i18n.integer(r['free'])), 'msg-bad' if over else 'hint', wrap=False))
        hcname = i18n.slot_name(gl.DEFAULT_SLOT)
        note = t('{hc} and the two Cinema slots keep a whole look in their own room. The other slots share this space.',
                 hc=hcname) + (' ' + t('A look on {hc} leaves less of it.', hc=hcname) if hc else '')
        return box(head, Meter(r['need'] / max(1, r['free']), over), label(note, 'note'))

    # ------------------------------------------------------------ 4 fit
    def selected_record(self):
        S = self.S
        if not S.fit or not S.fit['kept']:
            return None
        by = {gl.result_name(r): r for r in S.fit['kept']}
        return by.get(S.selected) or gl.recommended(S.fit['kept'])

    def page_fit(self):
        S = self.S
        title = t('Fit {lut}', lut=S.lut['file'].rsplit('.', 1)[0]) if S.lut else t('Fit your LUT')
        turns = QSpinBox(); turns.setRange(1, 9); turns.setValue(S.turns); turns.setFixedWidth(80)
        turns.valueChanged.connect(lambda v: setattr(S, 'turns', v))
        after = QCheckBox(t('Also try colour after the curves')); after.setChecked(S.after)
        after.toggled.connect(lambda on: setattr(S, 'after', on))
        go = button(t('Fit again') if S.fit else t('Start fit'), 'primary', self.start_fit, not S.fitting and bool(S.lut))
        stop = button(t('Stop'), slot=self.stop_fit); stop.setVisible(S.fitting)
        turns_label = label(t('Turns'), 'field'); turns_label.setBuddy(turns)
        controls = row(turns_label, turns, 16, after, stretch_end=True)
        controls.layout().addWidget(go); controls.layout().addWidget(stop)
        parts = [controls, label(t('Each turn starts from a new point and takes a few minutes. Turn 1 always uses the '
                                   'usual start, so one turn gives the same result every time.'), 'hint')]
        if S.fitting or S.fit_log:
            bar = QProgressBar(); bar.setTextVisible(False)
            if S.fitting:
                bar.setRange(0, 0)
            else:
                bar.setRange(0, 1); bar.setValue(1)
            log = label('\n'.join(S.fit_log[-6:]), 'hint')
            self.fit_progress = log
            parts += [bar, log]
        page = [self.head(title, t('The camera has a few colour controls. The fit finds the settings that come closest '
                                   'to your LUT and measures the difference in ΔE00: below 1 is hard to see, around 2 '
                                   'is a small visible difference.')), box(*parts)]
        if S.fit and S.fit['kept']:
            page += self.results()
        rec = self.selected_record()
        page.append(self.nav(2, 4, t('Next: build'), bool(rec) and not S.fitting and rec['decision']['build']))
        return self.page(*page)

    def start_fit(self, *, more=None, post=None):
        """A new fit (more=None) or more turns of the current one; never leaves the page stuck in 'fitting'."""
        try:
            self._start_fit(more, post)
        except Exception as exc:
            self.S.fitting = False
            gl.STOP = None
            self.render()
            self.say(t('Something went wrong: {error}', error=f'{type(exc).__name__}: {exc}'))

    def _start_fit(self, more, post):
        S = self.S
        if more is None or S.fit is None:
            S.fit, S.selected, S.photo_cam = logic.new_fit_state(), None, {}
            n, post = (S.turns, S.after) if more is None else (more, post)
        else:
            n = more
        S.fitting, S.fit_log, S.built = True, [], None
        args = logic.fit_args(S.lut['path'], S.space, S.dng, S.slot)
        state = S.fit
        self.stop_requested = False
        gl.STOP = lambda: self.stop_requested
        self.render()

        def work(report):
            for k in range(n):
                logic.run_turns(args, 1, state, post, log=report)
            return True

        first_turn = len(state['history_turns']) + 1

        def progress(line):
            turn = len(state['history_turns']) or first_turn
            text = logic.progress_line(str(line), turn)
            if text is None:
                return
            S.fit_log.append(text)
            if getattr(self, 'fit_progress', None) is not None:
                try:
                    self.fit_progress.setText('\n'.join(S.fit_log[-6:]))
                except RuntimeError:
                    pass

        def finished(_=None):
            S.fitting = False
            gl.STOP = None
            rec = gl.recommended(S.fit['kept']) if S.fit['kept'] else None
            S.selected = gl.result_name(rec) if rec else None
            self.render()
            self.say(t('Fit finished: {n} kept', n=len(S.fit['kept'])))

        def stopped():
            S.fitting = False
            gl.STOP = None
            if S.fit and S.fit['kept'] and not S.selected:
                S.selected = gl.result_name(gl.recommended(S.fit['kept']))
            self.render()
            self.say(t('Fit stopped'))

        def failed(msg):
            S.fitting = False
            gl.STOP = None
            self.render()
            self.say(msg)
        self.run_task(work, finished, failed, progress, stopped)

    def stop_fit(self):
        self.stop_requested = True

    def results(self):
        S = self.S
        rows = logic.result_rows(S.fit)
        rec = self.selected_record()
        sel = gl.result_name(rec)
        verdict = rec['scores']['fit']['verdict']
        if verdict == 'poor':
            hint = t('Everyday colours fit, so the firmware can still be built.') if rec['decision']['build'] else \
                t('The camera cannot follow this LUT closely enough.')
        else:
            hint = t('Ready to build.')
        head = row(label(t('Results'), 'h3'), pill(t(verdict), {'good': 'good', 'approximate': 'warn'}.get(verdict, 'bad')),
                   label(hint, 'hint'), stretch_end=True)
        head.layout().addWidget(button(t('Run 1 more turn'), 'small', lambda: self.start_fit(more=1, post=False), not S.fitting))
        head.layout().addWidget(button(t('1 more with colour after the curves'), 'small',
                                       lambda: self.start_fit(more=1, post=True), not S.fitting))
        cols = [t('Result'), t('Whole range'), 'ColorChecker', t('Greys'), t('Photo'), t('Fit score')]
        table = QTableWidget(len(rows), len(cols))
        table.setHorizontalHeaderLabels(cols)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setShowGrid(False)
        table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        for i, r in enumerate(rows):
            tag = t('recommended') if r['recommended'] else '' if r['kept'] else t('not kept')
            vals = [logic.result_label(r['name']) + (f'   ({tag})' if tag else ''), i18n.num(r['e']), i18n.num(r['cc']),
                    i18n.num(r['grey']), i18n.num(r['h']), i18n.num(r['score'], 3)]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(v)
                it.setTextAlignment((Qt.AlignmentFlag.AlignLeft if c == 0 else Qt.AlignmentFlag.AlignRight) | Qt.AlignmentFlag.AlignVCenter)
                if not r['kept']:
                    it.setFlags(Qt.ItemFlag.ItemIsEnabled)
                    it.setForeground(theme.colour(theme.TOKENS, 'muted'))
                table.setItem(i, c, it)
            if r['name'] == sel:
                table.selectRow(i)
        hh = table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for c in range(1, len(cols)):
            hh.setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        table.setFixedHeight(min(320, 40 + 38 * len(rows)))
        table.verticalHeader().setDefaultSectionSize(38)

        def picked():
            ix = table.currentRow()
            if 0 <= ix < len(rows) and rows[ix]['kept'] and rows[ix]['name'] != S.selected:
                S.selected = rows[ix]['name']
                S.built = None
                self.render()
        table.itemSelectionChanged.connect(picked)
        note = label(t('A result is kept when no other is at least as good on every measure. The recommended one has '
                       'the best fit score. Lower is closer to the LUT.'), 'note')
        return [head, table, note, self.grid2(self.board_box(rec), self.compare_box(rec))]

    def board_box(self, rec):
        S = self.S
        patches = logic.board_patches(rec, S.lut['path'], S.space)
        mean = sum(p[3] for p in patches) / len(patches)
        head = row(label(f'ColorChecker, {logic.result_label(gl.result_name(rec))}', 'h3'), stretch_end=True)
        head.layout().addWidget(label(t('average {n}', n=i18n.num(mean)), 'hint', wrap=False))
        key = row(label(t('top: your LUT'), 'hint', wrap=False), label(t('bottom: the camera'), 'hint', wrap=False),
                  label(t('red number: 2 or more, visible'), 'hint', wrap=False), spacing=16)
        return box(head, Board(patches), key)

    def compare_box(self, rec):
        S = self.S
        if not S.dng:
            return box(label(t('Preview'), 'h3'),
                       label(t('Add a DNG from your GR IV in step 2 to compare the look on your own photo.'), 'note'))
        name = gl.result_name(rec)
        pair = getattr(self, 'compare_pair', 'lut')
        seg = Segmented([('lut', t('LUT vs camera')), ('neutral', t('Without vs with look'))], pair)
        seg.changed.connect(lambda k: (setattr(self, 'compare_pair', k), self.render()))
        head = row(label(t('Preview'), 'h3'), stretch_end=True)
        head.layout().addWidget(seg)
        if S.photo is None or name not in S.photo_cam:
            self.load_photo(rec)
            return box(head, label(t('Preparing your photo…'), 'note'))
        base, lut = S.photo
        left = lut if pair == 'lut' else base
        cmp = Compare(qimage_from_rgb(left), qimage_from_rgb(S.photo_cam[name]),
                      t('your LUT') if pair == 'lut' else t('without the look'), t('camera with the look'))
        return box(head, cmp, label(t('Drag the divider, or use the arrow keys.'), 'note'))

    def load_photo(self, rec):
        S = self.S
        name = gl.result_name(rec)
        if getattr(self, 'photo_loading', None) == name:
            return
        self.photo_loading = name
        dng, lut, space = S.dng, S.lut['path'], S.space

        def work(_):
            import numpy as np
            if S.photo is None:
                base, lut_img, cam = logic.photo_images(rec, dng, lut, space)
                return name, (base, lut_img), cam
            v = gl.photo_signal(dng, max_side=900)
            cam = np.clip(gl.render(v.reshape(-1, 3), rec).reshape(v.shape), 0, 1)
            return name, None, cam

        def done(res):
            n, both, cam = res
            if both is not None:
                S.photo = both
            S.photo_cam[n] = cam
            self.photo_loading = None
            if S.view == 'steps' and S.step == 3 and not S.fitting:
                self.render()

        def failed(msg):
            self.photo_loading = None
            self.say(t('The photo cannot be read: {reason}', reason=msg))
        self.run_task(work, done, failed)

    # ------------------------------------------------------------ 5 build
    def current_look(self):
        """This look, finished (slot, name, icon), or None when it is not ready."""
        S = self.S
        if not S.slot or self.name_blocked() or any(b['look']['slot'] == S.slot for b in S.basket):
            return None
        base = S.shared['look'] if S.shared else self.selected_record()
        if base is None or (not S.shared and not base['decision']['build']):
            return None
        look = logic.finished_look(base, S.slot, S.name, S.icon_path, bool(S.shared) and S.keep_shared_icon,
                                   i18n.current, S.name_accepted)
        return dict(look=look, lut=S.shared['file'] if S.shared else S.lut['file'], shared=bool(S.shared))

    def page_build(self):
        S = self.S
        current = self.current_look()
        items = S.basket + ([current] if current else [])
        rows_ = [label(t('Looks in this firmware'), 'h3')]
        if not items:
            rows_.append(label(t('No look yet. Fit a LUT or use a shared look first.'), 'note'))
        for i, it in enumerate(items):
            lk = it['look']
            own = None
            if lk.get('icon'):
                own = QImage(base64.b64decode(lk['icon']['rgba']), 40, 40, 160, QImage.Format.Format_RGBA8888).copy()
            hint = (t('shared look {file}', file=it['lut']) if it['shared'] else it['lut']) + ' · ' + \
                t('replaces {slot}', slot=i18n.slot_name(lk['slot'])) + (' · ' + t('own icon') if own else '') + \
                (' · ' + t('colour after the curves') if lk.get('post_matrix_q9') else '')
            trailing = pill(t('this look'), 'info') if it is current else button(t('Remove'), 'small',
                                                                                    lambda _=False, k=i: self.remove_look(k))
            rows_.append(filecard(IconTile(lk['slot'], own, 40), lk.get('name') or i18n.slot_name(lk['slot']), hint, trailing))
        add_btn = button(t('Add another look'), slot=self.add_look, enabled=bool(current))
        rows_.append(row(add_btn, label(t('Keeps this look and starts a new one for another slot.'), 'hint')))
        parts = [self.head(t('Build the firmware'), t('Every look below goes into one file. You can add looks for other '
                                                      'slots before you build.')), box(*rows_)]
        looks = [it['look'] for it in items]
        if items:
            r = logic.room(looks)
            hc = any(lk['slot'] == gl.DEFAULT_SLOT for lk in looks)
            over = r['need'] > r['free']
            head = row(label(t('Room for looks in this firmware'), 'h3', wrap=False), stretch_end=True)
            head.layout().addWidget(label(t('{used} of {total} bytes', used=i18n.integer(r['need']),
                                            total=i18n.integer(r['free'])), 'msg-bad' if over else 'hint', wrap=False))
            hcname = i18n.slot_name(gl.DEFAULT_SLOT)
            parts.append(box(head, Meter(r['need'] / max(1, r['free']), over), label(
                t('{hc} and the two Cinema slots keep a whole look in their own room. The other slots share this space.',
                  hc=hcname) + (' ' + t('A look on {hc} leaves less of it.', hc=hcname) if hc else ''), 'note')))
        else:
            over = False
        if S.built:
            data, sha = S.built
            names = i18n.join_and(f'<b>{html(lk.get("name") or i18n.slot_name(lk["slot"]))}</b>' for lk in looks)
            steps = ''.join(f'<li style="margin-bottom:6px">{s}</li>' for s in (
                t('Format the SD card in the camera.'),
                t('Copy {file} to the top level of the card. Keep the name exactly.', file='<b>fwdc248b.bin</b>'),
                t('Full battery. Turn the camera on with the card inserted and start the firmware update. It shows '
                  '1.11 → 1.11; that is expected.'),
                t('Do not turn the camera off until it has restarted.'),
                t('Then choose {looks} in {menu}.', looks=names, menu=i18n.cam('Image Control'))))
            head = row(label(t('{file} is ready', file='fwdc248b.bin'), 'h3'), pill(t('Checked'), 'good'))
            parts.append(box(head, label(f'SHA-256 {sha}', 'sha', selectable=True), label(f'<ol style="margin-left:-20px">{steps}</ol>', rich=True),
                             row(button(t('Save the file…'), 'primary', self.save_firmware),
                                 button(t('Copy SHA-256'), slot=lambda: self.copy(sha)),
                                 button(t('Save looks to share…'), slot=lambda: self.save_looks(looks))),
                             label(t('Each look can be saved as a .json file. Others build it without the LUT and without '
                                     'fitting; name the file as you like.'), 'note'),
                             label(t("To go back, install RICOH's official 1.11 file the normal way."), 'note')))
        else:
            b = button(t('Build {file}', file='fwdc248b.bin'), 'primary', lambda: self.build(looks),
                       bool(items) and S.fw_status == 'ok' and not over)
            self.build_state = label(t('Takes about a minute: decode, apply, rebuild and check.') if S.fw_status == 'ok'
                                     else t('Choose the official firmware first.'), 'hint')
            parts.append(row(b, self.build_state))
        parts.append(self.nav(2 if S.source == 'shared' else 3, None, ''))
        return self.page(*parts)

    def remove_look(self, k):
        del self.S.basket[k]
        self.S.built = None
        self.render()

    def add_look(self):
        S = self.S
        cur = self.current_look()
        if not cur:
            return
        S.basket.append(cur)
        S.shared, S.shared_error, S.lut, S.built = None, None, None, None
        S.reset_look()
        self.go(0)
        self.say(t('Look added. Choose what the next one starts from.'))

    def build(self, looks):
        S = self.S
        if getattr(self, 'build_state', None) is not None:
            try:
                self.build_state.setText(t('Applying your looks…'))
            except RuntimeError:
                pass
        source = S.fw_data

        def done(data):
            S.built = (data, gl.sha256(data))
            self.render()
            self.say(t('Firmware built and checked'))
        self.run_task(lambda _: logic.build(source, looks), done)

    def save_firmware(self):
        path, _ = QFileDialog.getSaveFileName(self, '', 'fwdc248b.bin', FIRMWARE_FILTER)
        if not path:
            return
        if Path(path).name != 'fwdc248b.bin':
            path = str(Path(path).with_name('fwdc248b.bin'))
        Path(path).write_bytes(self.S.built[0])
        self.say(t('Saved: {file}', file=path))

    def save_looks(self, looks):
        folder = QFileDialog.getExistingDirectory(self, '')
        if not folder:
            return
        for lk in looks:
            stem = ''.join(c if c.isalnum() or c in ' -_' else '_' for c in (lk.get('name') or lk['slot'])).strip() or 'look'
            target = Path(folder) / f'{stem}.json'
            n = 2
            while target.exists():
                target = Path(folder) / f'{stem} {n}.json'
                n += 1
            out = dict(lk)
            out.pop('name_accepted', None)
            target.write_text(json.dumps(out, indent=1) + '\n', encoding='utf-8')
        self.say(t('Saved: {file}', file=folder))

    def copy(self, text):
        QGuiApplication.clipboard().setText(text)
        self.say(t('SHA-256 copied'))

    # ------------------------------------------------------------ check a firmware file
    def page_check(self):
        S = self.S
        dz = DropZone(t('Choose {file}', file='fwdc248b.bin'), t('or drop it here'), FIRMWARE_FILTER)
        dz.chosen.connect(self.check_firmware_file)
        parts = [self.head(t('Check a firmware file'),
                           t("Find out whether a {file} is RICOH's official 1.11, made by GR4-LUTSmith (and with which "
                             "looks), or something else. Do this before copying any file you were sent to your card.",
                             file='fwdc248b.bin')), dz]
        r = S.check_result
        if r:
            if not r['valid']:
                kind, tag = 'bad', t('Damaged')
                pairs = [(t('File'), t('not valid: the file is damaged or not a GR IV firmware'))]
            elif r['kind'] == 'official':
                kind, tag = 'good', t('Official RICOH 1.11')
                pairs = [(t('File'), t('valid (sizes, footer, both checksums)')), (t('Status'), t('unmodified'))]
            elif r['kind'] == 'lutsmith':
                kind, tag = 'info', t('GR4-LUTSmith firmware')
                looks = []
                for lk in r['looks']:
                    text = i18n.slot_name(lk['slot'])
                    if lk['name'] and lk['icon']:
                        text = t('{slot} named “{name}” with its own icon', slot=text, name=lk['name'])
                    elif lk['name']:
                        text = t('{slot} named “{name}”', slot=text, name=lk['name'])
                    elif lk['icon']:
                        text = t('{slot} with its own icon', slot=text)
                    looks.append(text)
                pairs = [(t('File'), t('valid (sizes, footer, both checksums)')),
                         (t('Looks'), '; '.join(looks) if looks else t('no personal look')),
                         (t('Made from'), t('official RICOH GR IV 1.11'))]
            else:
                kind, tag = 'warn', t('Unknown')
                pairs = [(t('File'), t('valid (sizes, footer, both checksums)')),
                         (t('Status'), t('not the official 1.11 file and not made by GR4-LUTSmith'))]
            head = row(label(Path(S.check_file).name, 'h3'), pill(tag, kind))
            parts.append(box(head, facts(pairs), label(f'SHA-256 {r["sha256"]}', 'sha', selectable=True)))
        f = QFrame(); set_role(f, 'foot')
        h = QHBoxLayout(f); h.setContentsMargins(0, 16, 0, 0)
        h.addWidget(button(t('Back to the steps'), slot=lambda: self.go(S.step))); h.addStretch(1)
        parts.append(f)
        return self.page(*parts)

    def check_firmware_file(self, path):
        S = self.S
        S.check_file, S.check_result = path, None

        def done(r):
            S.check_result = r
            self.render()
        self.run_task(lambda _: logic.inspect(path), done)

    # ------------------------------------------------------------ first open
    def confirm_once(self):
        if self.settings.value('firmware_confirmed') == '1':
            return
        dlg = FirstRun(self)
        dlg.accepted.connect(lambda: self.settings.setValue('firmware_confirmed', '1'))
        dlg.open()


def clear(widget):
    lay = widget.layout()
    if lay is None:
        return
    while lay.count():
        it = lay.takeAt(0)
        if it.widget():
            it.widget().hide()                       # gone at once, not only when Qt deletes it
            it.widget().deleteLater()


def html(text):
    return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def main():
    if sys.platform == 'win32':
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('GR4-LUTSmith')
        except Exception:
            pass
    app = QApplication(sys.argv)
    app.setApplicationName('GR4-LUTSmith')
    app.setOrganizationName('GR4-LUTSmith')
    app.setApplicationVersion(gl.VERSION)
    icon = i18n.ASSETS / 'app' / 'icon.png'
    if icon.exists():
        app.setWindowIcon(QIcon(str(icon)))
    theme.load_fonts()
    f = QFont(theme.BODY); f.setPixelSize(15)
    app.setFont(f)
    win = Window()
    win.show()
    QTimer.singleShot(0, win.confirm_once)
    return app.exec()
