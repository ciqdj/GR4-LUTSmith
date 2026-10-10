"""Draw the app icon (camera-menu style: a dark tile, grey frame, film perforations, "LUT") and write
lutsmith_app/assets/app/icon.png, packaging/icon.icns (macOS) and packaging/icon.ico (Windows).
Run: uv run python tools/make_app_icon.py"""
import subprocess, sys, tempfile
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QFontDatabase, QGuiApplication, QImage, QPainter, QPainterPath, QPen

ROOT = Path(__file__).resolve().parents[1]
app = QGuiApplication(sys.argv[:1])
for f in (ROOT / 'lutsmith_app/assets/fonts').glob('*.ttf'):
    QFontDatabase.addApplicationFont(str(f))


def draw(size=1024):
    img = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing); p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    s = size / 1024
    body = QRectF(100 * s, 100 * s, 824 * s, 824 * s)                    # macOS grid: 824 of 1024
    path = QPainterPath(); path.addRoundedRect(body, 185 * s, 185 * s)
    p.fillPath(path, QColor('#2c3034'))                                   # the camera body
    tile = QRectF(232 * s, 232 * s, 560 * s, 560 * s)                     # the look icon, as in the camera menu
    p.fillRect(tile, QColor('#353536'))
    p.setPen(QPen(QColor('#808080'), 14 * s)); p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRect(tile.adjusted(7 * s, 7 * s, -7 * s, -7 * s))
    p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor('#ffffff'))
    hole, gap = 44 * s, (560 - 2 * 40 - 5 * 44) / 4 * s                 # five perforations, top and bottom
    for i in range(5):
        x = tile.left() + 40 * s + i * (hole + gap)
        p.drawRect(QRectF(x, tile.top() + 40 * s, hole, hole))
        p.drawRect(QRectF(x, tile.bottom() - 40 * s - hole, hole, hole))
    f = QFont('Barlow Semi Condensed'); f.setWeight(QFont.Weight.DemiBold); f.setPixelSize(int(250 * s))
    p.setFont(f); p.setPen(QColor('#ffffff'))
    p.drawText(tile.adjusted(0, 6 * s, 0, 0), Qt.AlignmentFlag.AlignCenter, 'LUT')
    p.end()
    return img


big = draw(1024)
out = ROOT / 'lutsmith_app/assets/app/icon.png'
big.save(str(out))
with tempfile.TemporaryDirectory() as d:
    iconset = Path(d) / 'icon.iconset'
    iconset.mkdir()
    for n in (16, 32, 128, 256, 512):
        draw(n).save(str(iconset / f'icon_{n}x{n}.png'))
        draw(n * 2).save(str(iconset / f'icon_{n}x{n}@2x.png'))
    if sys.platform == 'darwin':
        subprocess.run(['iconutil', '-c', 'icns', str(iconset), '-o', str(ROOT / 'packaging/icon.icns')], check=True)
from PIL import Image
Image.open(out).save(ROOT / 'packaging/icon.ico', sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print('wrote', out, 'packaging/icon.icns', 'packaging/icon.ico')
