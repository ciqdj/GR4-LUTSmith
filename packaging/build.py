"""Build the downloadable GR4-LUTSmith app for this computer, in a clean environment of its own.

    uv run python packaging/build.py                 # this Mac's chip, or Windows x64
    uv run python packaging/build.py --arch x86_64   # Intel Mac build on Apple Silicon (runs under Rosetta)

Writes dist/GR4-LUTSmith-<version>-<platform>.zip (the app and its licences) and prints its SHA-256.
macOS builds target macOS 12 and later; Windows builds target Windows 10 and 11 (x64)."""
import argparse
import hashlib
import os
import platform
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import gr4_lutsmith  # noqa: E402

VERSION = gr4_lutsmith.VERSION
DEPS = ['numpy>=1.21', 'pyside6-essentials>=6.8,<6.9', 'rawpy>=0.18', 'pillow>=9', 'pyinstaller>=6.6']
LICENSED = {'numpy': 'numpy', 'pillow': 'pillow', 'rawpy': 'rawpy'}


def run(cmd, **kw):
    print('>', ' '.join(map(str, cmd)), flush=True)
    subprocess.run([str(c) for c in cmd], check=True, **kw)


def target(arch):
    if sys.platform == 'darwin':
        arch = arch or platform.machine()
        if arch == 'arm64':
            return dict(label='macOS-AppleSilicon', python='cpython-3.12-macos-aarch64-none',
                        platform='aarch64-apple-darwin', prefix=[])
        return dict(label='macOS-Intel', python='cpython-3.12-macos-x86_64-none', platform='x86_64-apple-darwin',
                    prefix=['arch', '-x86_64'])
    if sys.platform == 'win32':
        return dict(label='Windows-x64', python='cpython-3.12-windows-x86_64-none', platform='x86_64-pc-windows-msvc',
                    prefix=[])
    raise SystemExit('the app is built on macOS or Windows')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--arch', choices=('arm64', 'x86_64'), help='macOS only: the chip to build for')
    a = ap.parse_args()
    tg = target(a.arch)
    build = ROOT / 'build' / tg['label']
    env = dict(os.environ, MACOSX_DEPLOYMENT_TARGET='12.0')
    venv = build / 'venv'
    py = venv / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
    run(['uv', 'python', 'install', tg['python']])
    run(['uv', 'venv', '--clear', '--python', tg['python'], venv])
    run(['uv', 'pip', 'install', '--python', py, '--python-platform', tg['platform'], '--only-binary', ':all:', *DEPS],
        env=env)                                              # ready-made packages only, never compiled here

    dist, work = build / 'dist', build / 'work'
    run([*tg['prefix'], py, '-m', 'PyInstaller', ROOT / 'packaging' / 'gr4-lutsmith.spec', '--noconfirm',
         '--distpath', dist, '--workpath', work], env=env)
    app = dist / ('GR4-LUTSmith.app' if sys.platform == 'darwin' else 'GR4-LUTSmith')
    smoke(tg, app)

    name = f'GR4-LUTSmith-{VERSION}-{tg["label"]}'
    stage = build / name
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir()
    licences(py, stage / 'Licences')
    out = ROOT / 'dist'
    out.mkdir(exist_ok=True)
    zpath = out / f'{name}.zip'
    if zpath.exists():
        zpath.unlink()
    if sys.platform == 'darwin':
        run(['ditto', app, stage / app.name])                     # keeps the app's signature and links intact
        run(['ditto', '-c', '-k', '--keepParent', stage, zpath])
    else:
        shutil.copytree(app, stage / app.name)
        with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as z:
            for f in sorted(stage.rglob('*')):
                z.write(f, f.relative_to(stage.parent))
    digest = hashlib.sha256(zpath.read_bytes()).hexdigest()
    (out / f'{name}.zip.sha256').write_text(f'{digest}  {zpath.name}\n')
    print(f'\nbuilt {zpath}  ({zpath.stat().st_size / 1e6:.0f} MB)\nSHA-256 {digest}')


def smoke(tg, app):
    """The packaged app must start and keep running (no window shown: offscreen)."""
    exe = app / 'Contents' / 'MacOS' / 'GR4-LUTSmith' if sys.platform == 'darwin' else app / 'GR4-LUTSmith.exe'
    p = subprocess.Popen([*tg['prefix'], str(exe)], env=dict(os.environ, QT_QPA_PLATFORM='offscreen'),
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    time.sleep(12)
    alive = p.poll() is None
    p.kill()
    out = p.communicate()[0].decode(errors='replace')
    if not alive:
        raise SystemExit(f'smoke test: the app stopped on its own:\n{out[-3000:]}')
    print('smoke test: the app starts and runs')


def licences(py, folder):
    folder.mkdir(parents=True)
    site = Path(subprocess.run([py, '-c', 'import numpy, os; print(os.path.dirname(os.path.dirname(numpy.__file__)))'],
                               capture_output=True, text=True, check=True).stdout.strip())
    for dist, dest in LICENSED.items():
        info = next(site.glob(f'{dist}-*.dist-info'))
        files = [f for f in info.rglob('*') if f.is_file() and any(k in f.name.upper() for k in ('LICEN', 'COPYING', 'NOTICE'))]
        (folder / dest).mkdir()
        for f in files:
            shutil.copy(f, folder / dest / f.name)
    base = Path(subprocess.run([py, '-c', 'import sys; print(sys.base_prefix)'], capture_output=True, text=True,
                               check=True).stdout.strip())
    lic = next(iter(list(base.glob('lib/python3*/LICENSE.txt')) + list(base.glob('LICENSE.txt'))), None)
    (folder / 'Python').mkdir()
    if lic:
        shutil.copy(lic, folder / 'Python' / 'LICENSE.txt')
    for f in (ROOT / 'packaging' / 'licenses').glob('*.txt'):
        shutil.copy(f, folder / f.name)
    shutil.copy(ROOT / 'lutsmith_app' / 'assets' / 'fonts' / 'OFL.txt', folder / 'Barlow-OFL.txt')
    shutil.copy(ROOT / 'packaging' / 'NOTICE.txt', folder / 'NOTICE.txt')


if __name__ == '__main__':
    main()
