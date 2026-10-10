# PyInstaller spec for the GR4-LUTSmith app: one folder (Windows) or one .app (macOS). Built by packaging/build.py.
import sys
from pathlib import Path

ROOT = Path(SPECPATH).parent
sys.path.insert(0, str(ROOT))
import gr4_lutsmith  # noqa: E402

VERSION = gr4_lutsmith.VERSION
mac, win = sys.platform == 'darwin', sys.platform == 'win32'

a = Analysis(
    [str(ROOT / 'lutsmith_app' / '__main__.py')],
    pathex=[str(ROOT)],
    datas=[(str(ROOT / 'lutsmith_app' / 'assets'), 'lutsmith_app/assets')],
    hiddenimports=['PySide6.QtSvg'],
    excludes=['tkinter', 'matplotlib', 'IPython', 'pytest', 'PySide6.QtNetwork', 'PySide6.QtQml', 'PySide6.QtQuick',
              'PySide6.QtWebEngineCore', 'PySide6.QtMultimedia', 'PySide6.QtPdf', 'PySide6.QtOpenGL'],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='GR4-LUTSmith', console=False,
          icon=str(ROOT / 'packaging' / ('icon.ico' if win else 'icon.icns')),
          disable_windowed_traceback=False, argv_emulation=False, target_arch=None, upx=False)
coll = COLLECT(exe, a.binaries, a.datas, name='GR4-LUTSmith', upx=False)
if mac:
    app = BUNDLE(coll, name='GR4-LUTSmith.app', icon=str(ROOT / 'packaging' / 'icon.icns'),
                 bundle_identifier='io.github.gr4-lutsmith',
                 info_plist={'CFBundleName': 'GR4-LUTSmith', 'CFBundleDisplayName': 'GR4-LUTSmith',
                             'CFBundleShortVersionString': VERSION, 'CFBundleVersion': VERSION,
                             'LSMinimumSystemVersion': '12.0', 'NSHighResolutionCapable': True,
                             'NSRequiresAquaSystemAppearance': False})
