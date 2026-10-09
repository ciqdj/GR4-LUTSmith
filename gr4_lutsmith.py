#!/usr/bin/env python3
"""GR4-LUTSmith: put the look of a .cube LUT into your RICOH GR IV (firmware 1.11).

Fits the LUT to the camera's own look processing (a colour matrix and tone
curves) and writes a firmware file that carries the result as an extra Image
Control look. Starts from the official RICOH firmware file you downloaded
yourself. A file is written only if every check passes.

Usage
  python3 gr4_lutsmith.py make     LUT.cube OFFICIAL_fwdc248b.bin [--space srgb|adobe] [--photo DNG] [-o DIR]
  python3 gr4_lutsmith.py fit      LUT.cube [--space srgb|adobe] [--photo DNG] [-o DIR]   (no firmware needed)
  python3 gr4_lutsmith.py build    DIR/look.json OFFICIAL_fwdc248b.bin [-o DIR]
  python3 gr4_lutsmith.py preview  DIR/look.json PHOTO.DNG [-o sheet.jpg]   (needs rawpy, pillow)
  python3 gr4_lutsmith.py check    ANY_fwdc248b.bin
  python3 gr4_lutsmith.py selftest OFFICIAL_fwdc248b.bin

Python 3.8 or newer with numpy. --photo and preview also need rawpy and pillow.
"""
import argparse
import base64
import hashlib
import json
import math
import struct
import sys
import zlib
from pathlib import Path

VERSION = '1.1.0'

OFFICIAL_SHA256 = 'a2f664dfca034059eb0fd6e18ab08684c326b4a034d85c164dad7e1ec9b5655f'
OFFICIAL_BYTES = 38648776

OTHER_KNOWN = {
    '4c04b48c65897f2edd028df0f5e04666ca241488c81502bae0f34e040ee454eb': 'GR4-MonoUnlock 1.0.0 (monochrome looks unlocked)',
}

# Built-in example: examples/film-1d.look.json must build to exactly this image (selftest).
SELFTEST_LOOK = 'examples/film-1d.look.json'
SELFTEST_SHA256 = 'd201add28bc3ab738bc92fcfdaafa3847bc881bfd7eecb6b7e8f331d1289f052'

HEADER, MAGIC, FOOTER_MAGIC = 128, b'RICOH\0\0\0', b'\xa5\x5a\x5a\xa5'
MAX_DISTANCE = 0x2000
LITERAL_CHUNK = 0x6000


class Refused(Exception):
    pass


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def word_sum(data):
    if len(data) % 4:
        raise Refused('data is not 4-byte aligned')
    return sum(w for (w,) in struct.iter_unpack('<I', data)) & 0xffffffff


def decode(data, limit=256 * 1024 * 1024):
    if len(data) < 160 or data[:8] != MAGIC:
        raise Refused('not a RICOH firmware container')
    out = bytearray()
    frames = []
    cursor = HEADER
    while True:
        start = cursor
        if cursor + 2 > len(data):
            raise Refused('container: missing frame terminator')
        descriptor = int.from_bytes(data[cursor:cursor + 2], 'big')
        cursor += 2
        if descriptor == 0:
            return bytes(out), frames, cursor
        size = descriptor & 0x7fff
        end = cursor + size
        if not size or end > len(data):
            raise Refused(f'container: invalid frame at {start:#x}')
        output_start = len(out)
        if descriptor & 0x8000:
            out += data[cursor:end]
            cursor = end
        else:
            while cursor < end:
                if cursor + 2 > end:
                    raise Refused(f'container: truncated flags at {cursor:#x}')
                flags = int.from_bytes(data[cursor:cursor + 2], 'big')
                cursor += 2
                for bit in range(15, -1, -1):
                    if cursor == end:
                        break
                    if not flags & (1 << bit):
                        out.append(data[cursor])
                        cursor += 1
                        continue
                    if cursor + 2 > end:
                        raise Refused('container: truncated reference')
                    a, b = data[cursor], data[cursor + 1]
                    cursor += 2
                    distance = ((a >> 3) << 8) | b
                    length = a & 7
                    if length == 7:
                        while True:
                            if cursor >= end:
                                raise Refused('container: truncated length')
                            extension = data[cursor]
                            cursor += 1
                            length += extension
                            if extension != 255:
                                break
                    if distance == 0:
                        break
                    if distance > len(out):
                        raise Refused('container: reference before start of output')
                    count = length + 3
                    if distance >= count:
                        out += out[-distance:len(out) - distance + count]
                    else:
                        pattern = bytes(out[-distance:])
                        out += (pattern * ((count + distance - 1) // distance))[:count]
                if len(out) > limit:
                    raise Refused('container: decoded size limit exceeded')
        frames.append((start, end, output_start, len(out)))


def check_container(data, payload=None, consumed=None):
    if payload is None:
        payload, _, consumed = decode(data)
    if data[-20:-16] != FOOTER_MAGIC:
        raise Refused('container: footer magic missing')
    enc, dec = struct.unpack_from('<II', data, len(data) - 12)
    if enc != consumed - HEADER or dec != len(payload):
        raise Refused('container: size fields do not match the content')
    if word_sum(data) or word_sum(payload):
        raise Refused('container: checksum mismatch')
    return payload


def sections(payload):
    out, pos = [], 0
    while pos + 16 <= len(payload):
        tag = payload[pos:pos + 8].rstrip(b'\0')
        if not tag or not tag.isalnum() or not tag.isupper():
            break
        size = struct.unpack_from('<I', payload, pos + 12)[0]
        if pos + 16 + size > len(payload):
            break
        out.append((tag.decode(), pos + 16, pos + 16 + size))
        pos += 16 + size
    return out


def differences(a, b, block=1 << 16):
    if len(a) != len(b):
        raise Refused('length mismatch')
    out = []
    for pos in range(0, len(a), block):
        x, y = a[pos:pos + block], b[pos:pos + block]
        if x != y:
            out += [pos + i for i in range(len(x)) if x[i] != y[i]]
    return out


def rezero(payload):
    buf = bytearray(payload)
    last = struct.unpack_from('<I', buf, len(buf) - 4)[0]
    struct.pack_into('<I', buf, len(buf) - 4, (last - word_sum(buf)) & 0xffffffff)
    return bytes(buf)


def literal_frames(data):
    out = bytearray()
    for pos in range(0, len(data), LITERAL_CHUNK):
        chunk = data[pos:pos + LITERAL_CHUNK]
        out += struct.pack('>H', 0x8000 | len(chunk)) + chunk
    return bytes(out)


def rebuild(source, frames, consumed, patched, changed):
    body = bytearray()
    reemitted = 0
    for (c0, c1, d0, d1) in frames:
        if any(d0 <= c < d1 or c < d0 < c + MAX_DISTANCE for c in changed):
            body += literal_frames(patched[d0:d1])
            reemitted += 1
        else:
            body += source[c0:c1]
    body += b'\0\0'
    trailer = bytearray(source[consumed:])
    struct.pack_into('<II', trailer, len(trailer) - 12, len(body), len(patched))
    struct.pack_into('<I', trailer, len(trailer) - 4, 0)
    padding = bytes((-HEADER - len(body) - len(trailer)) % 4)
    out = bytearray(source[:HEADER] + body + padding + trailer)
    struct.pack_into('<I', out, len(out) - 4, (-word_sum(out)) & 0xffffffff)
    return bytes(out), reemitted


# ------------------------------------------------------------------ firmware data
# Fixed changes (make the extra look slot available, colour processing and default
# slider settings for it) and where the look itself goes. Exported from the
# builds that were tested on a GR IV 1.11.
_DATA = '''
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
'''
DATA = json.loads(zlib.decompress(base64.b64decode(''.join(_DATA.split()))))
LOOK = DATA['look']


def look_changes(look):
    """(offset, old, new, what) for one look: matrix, curve table selection, curve(s)."""
    mat = look['matrix_q13']
    if any(abs(sum(r) - 8192) > 2 for r in mat) or max(abs(x) for r in mat for x in r) > 0x7fff:
        raise Refused('look matrix must be 3x3, Q13, rows summing to 8192')
    out = [(LOOK['matrix'][0], LOOK['matrix'][1], struct.pack('<9h', *[x for r in mat for x in r]).hex(),
            'look colour matrix')]
    curves = look.get('curves')
    if not curves:                                   # no look curve: the colour look's plain tone curve
        for off, old in LOOK['select']:
            out.append((off, old, struct.pack('<I', LOOK['select_none']).hex(), 'use the plain tone curve'))
        return out
    if len(curves) != 3 or any(len(c) != 256 or min(c) < 0 or max(c) > 16383 for c in curves):
        raise Refused('curves must be three lists of 256 values in 0..16383')
    distinct = []
    for c in curves:
        if list(c) not in distinct:
            distinct.append(list(c))
    if len(distinct) == 1:
        buf, bufs = LOOK['single'], [LOOK['single']]
    elif len(distinct) == 2:
        buf, bufs = LOOK['pair'], [LOOK['pair'], LOOK['single']]
    elif len(distinct) == 3:
        buf, bufs = LOOK['pair'], [LOOK['pair'], LOOK['single'], LOOK['third']]
    else:
        raise Refused('at most three different channel curves are supported')
    for off, old in LOOK['select']:
        out.append((off, old, struct.pack('<I', buf['set']).hex(), 'use the look\'s tone curves'))
    for k, (b, c) in enumerate(zip(bufs, distinct)):
        out.append((b['curve_off'], b['curve_old'], struct.pack('<256H', *c).hex(), f'tone curve {k + 1}'))
    ptrs = [bufs[distinct.index(list(c))]['curve'] for c in curves]
    if len(distinct) >= 2:
        out.append((LOOK['pair']['chan_off'], LOOK['pair']['chan_old'], struct.pack('<III', *ptrs).hex(),
                    'tone curve per colour channel'))
    return out


def all_changes(look):
    fixed = [(o, a, b, 'make the look slot available with its colour processing and defaults')
             for o, a, b in DATA['fixed']]
    return fixed + look_changes(look)


def make_firmware(source, look, log=print):
    digest = sha256(source)
    if digest != OFFICIAL_SHA256 or len(source) != OFFICIAL_BYTES:
        if digest in OTHER_KNOWN:
            raise Refused(f'this is {OTHER_KNOWN[digest]}; use the official RICOH file')
        raise Refused('input is not the official RICOH GR IV 1.11 fwdc248b.bin '
                      f'(SHA-256 {digest}, expected {OFFICIAL_SHA256})')
    log('input: official RICOH GR IV 1.11 firmware (SHA-256 verified)')
    log('decoding container ...')
    payload, frames, consumed = decode(source)
    check_container(source, payload, consumed)
    secs = sections(payload)
    rtos = next((s for s in secs if s[0] == 'RTOS'), None)
    if rtos is None:
        raise Refused('payload: RTOS section not found')
    buf = bytearray(payload)
    items = all_changes(look)
    spans = sorted((o, o + len(bytes.fromhex(a))) for o, a, _, _ in items)
    if any(b0 < a1 for (_, a1), (b0, _) in zip(spans, spans[1:])):
        raise Refused('internal: overlapping changes')
    for off, old, new, what in items:
        old, new = bytes.fromhex(old), bytes.fromhex(new)
        have = bytes(buf[off:off + len(old)])
        if have != old or len(new) != len(old):
            raise Refused(f'unexpected original bytes at {off:#x} ({what})')
        if not (rtos[1] <= off and off + len(new) <= rtos[2]):
            raise Refused(f'change at {off:#x} is outside the RTOS section')
        buf[off:off + len(new)] = new
    log(f'  {len(items)} changes applied ({len(items) - len(DATA["fixed"])} carry your look)')
    patched = rezero(bytes(buf))
    log('rebuilding container ...')
    changed = differences(payload, patched)
    out, reemitted = rebuild(source, frames, consumed, patched, changed)
    log('verifying result ...')
    again, _, used = decode(out)
    if again != patched:
        raise Refused('verification: rebuilt container does not decode to the patched firmware')
    check_container(out, again, used)
    if out[:HEADER] != source[:HEADER]:
        raise Refused('verification: header changed')
    allowed = {i for off, old, _, _ in items for i in range(off, off + len(bytes.fromhex(old)))}
    allowed |= set(range(len(payload) - 4, len(payload)))
    stray = [i for i in changed if i not in allowed]
    if stray:
        raise Refused(f'verification: unexpected changes at {[hex(i) for i in stray[:8]]}')
    if sections(again) != secs:
        raise Refused('verification: section layout changed')
    for tag, a, b in secs:
        if tag != 'RTOS' and again[a:b] != payload[a:b]:
            raise Refused(f'verification: section {tag} changed')
    log(f'verified: {len(changed)} payload bytes changed, {reemitted} frames re-encoded, '
        f'all other sections identical')
    return out


def write_atomic(data, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / 'fwdc248b.bin'
    if target.exists():
        raise Refused(f'{target} already exists; choose another output directory or remove it')
    tmp = target.with_name('.fwdc248b.bin.tmp')
    tmp.write_bytes(data)
    if sha256(tmp.read_bytes()) != sha256(data):
        tmp.unlink()
        raise Refused('write verification failed')
    tmp.rename(target)
    return target


def identify(data, log=print):
    digest = sha256(data)
    names = {OFFICIAL_SHA256: 'official RICOH GR IV 1.11 (unmodified)', **OTHER_KNOWN}
    log(f'SHA-256  {digest}')
    log(f'bytes    {len(data)}')
    try:
        payload = check_container(data)
        log('container: valid (size fields, footer, both checksums)')
    except Refused as exc:
        log(f'container: INVALID - {exc}')
        return 2
    if digest in names:
        log(f'file     {names[digest]}')
        return 0
    fixed_ok = all(payload[o:o + len(bytes.fromhex(b))] == bytes.fromhex(b) for o, _, b in DATA['fixed'])
    if fixed_ok:
        m = struct.unpack_from('<9h', payload, LOOK['matrix'][0])
        log(f'file     a GR4-LUTSmith firmware (look matrix {[list(m[i:i + 3]) for i in (0, 3, 6)]})')
        return 0
    log('file     unknown - not the official 1.11 file and not made by GR4-LUTSmith')
    return 1


# ------------------------------------------------------------------ LUT files
class Lut:
    """A .cube LUT (3D, or 1D expanded per channel), values as an (n,n,n,3) array [b][g][r]."""

    def __init__(self, path):
        import numpy as np
        text = Path(path).read_text(errors='replace')
        self.sha256 = hashlib.sha256(text.encode()).hexdigest()
        head, rows, self.ignored = {}, [], []
        for line in text.splitlines():
            line = line.split('#', 1)[0].strip()
            if not line:
                continue
            tok = line.split()
            if tok[0][0].isalpha():
                key = tok[0].upper()
                if key == 'TITLE':
                    head['TITLE'] = line[5:].strip().strip('"')
                elif key in ('LUT_3D_SIZE', 'LUT_1D_SIZE'):
                    head[key] = int(tok[1])
                elif key in ('DOMAIN_MIN', 'DOMAIN_MAX'):
                    head[key] = tuple(map(float, tok[1:4]))
                elif key in ('LUT_3D_INPUT_RANGE', 'LUT_1D_INPUT_RANGE'):
                    head['DOMAIN_MIN'], head['DOMAIN_MAX'] = (float(tok[1]),) * 3, (float(tok[2]),) * 3
                else:
                    self.ignored.append(tok[0])
                continue
            if len(tok) != 3:
                raise Refused(f'{path}: invalid data row {line[:40]!r}')
            rows.append(tuple(map(float, tok)))
        v = np.array(rows, float)
        if not len(v) or not np.isfinite(v).all():
            raise Refused(f'{path}: no data or non-finite values')
        self.lo = np.array(head.get('DOMAIN_MIN', (0., 0., 0.)))
        self.hi = np.array(head.get('DOMAIN_MAX', (1., 1., 1.)))
        if 'LUT_3D_SIZE' in head and 'LUT_1D_SIZE' in head:
            raise Refused(f'{path}: combined 1D + 3D LUTs are not supported')
        if 'LUT_3D_SIZE' in head:
            n = head['LUT_3D_SIZE']
            if not 2 <= n <= 129 or len(v) != n ** 3:
                raise Refused(f'{path}: LUT_3D_SIZE {n} but {len(v)} rows')
            self.kind, self.n, self.table = '3D', n, v.reshape(n, n, n, 3)
        elif 'LUT_1D_SIZE' in head:
            n = head['LUT_1D_SIZE']
            if not 2 <= n <= 65536 or len(v) != n:
                raise Refused(f'{path}: LUT_1D_SIZE {n} but {len(v)} rows')
            g = np.linspace(0, 1, 33)
            xs = np.linspace(0, 1, n)
            x = grid(33)
            out = np.stack([np.interp(x[:, c], xs, v[:, c]) for c in range(3)], 1)
            self.kind, self.n, self.table = '1D', 33, out.reshape(33, 33, 33, 3)
        else:
            raise Refused(f'{path}: no LUT_3D_SIZE or LUT_1D_SIZE')
        self.title = head.get('TITLE', '')
        if v.min() < -0.05 or v.max() > 1.05:
            raise Refused(f'{path}: output range {v.min():.2f}..{v.max():.2f} is not 0..1; '
                          'log or scene-referred LUTs are not supported')

    def __call__(self, rgb):
        """Trilinear lookup; inputs clamped to the LUT's domain."""
        import numpy as np
        n = self.n
        p = np.clip((rgb - self.lo) / (self.hi - self.lo), 0, 1) * (n - 1)
        a = np.minimum(np.floor(p).astype(int), n - 2)
        f = p - a
        out = 0
        for dr in (0, 1):
            for dg in (0, 1):
                for db in (0, 1):
                    w = ((f[:, 0] if dr else 1 - f[:, 0]) * (f[:, 1] if dg else 1 - f[:, 1])
                         * (f[:, 2] if db else 1 - f[:, 2]))
                    out = out + w[:, None] * self.table[a[:, 2] + db, a[:, 1] + dg, a[:, 0] + dr]
        return np.clip(out, 0, 1)


def grid(n):
    import numpy as np
    g = np.linspace(0, 1, n)
    b, gg, r = np.meshgrid(g, g, g, indexing='ij')
    return np.stack([r.ravel(), gg.ravel(), b.ravel()], 1)


# ------------------------------------------------------------------ colour
SRGB_TO_ADOBE = [[366 / 512, 146 / 512, 0], [0, 1, 0], [0, 21 / 512, 491 / 512]]
ADOBE_GAMMA = 563 / 256
XYZ = [[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]]
WHITE = [0.95047, 1.0, 1.08883]


def srgb_dec(x):
    import numpy as np
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def srgb_enc(x):
    import numpy as np
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * x ** (1 / 2.4) - 0.055)


def adobe_lut_on_srgb(lut, y):
    """Apply an Adobe RGB LUT to sRGB-encoded colours, result in sRGB (colorimetric, via linear light)."""
    import numpy as np
    m = np.array(SRGB_TO_ADOBE)
    ya = np.clip(srgb_dec(y) @ m.T, 0, 1) ** (1 / ADOBE_GAMMA)
    lin = (lut(ya) ** ADOBE_GAMMA) @ np.linalg.inv(m).T
    keep = (lin >= -1e-3).all(1) & (lin <= 1 + 1e-3).all(1)
    return srgb_enc(lin), keep


def lab(rgb):
    import numpy as np
    xyz = srgb_dec(rgb) @ np.array(XYZ).T / np.array(WHITE)
    f = np.where(xyz > 216 / 24389, np.cbrt(xyz), (24389 / 27 * xyz + 16) / 116)
    return np.stack([116 * f[:, 1] - 16, 500 * (f[:, 0] - f[:, 1]), 200 * (f[:, 1] - f[:, 2])], 1)


def de00(l1, l2):
    """CIEDE2000 (Sharma, Wu & Dalal 2005)."""
    import numpy as np
    L1, a1, b1 = l1.T
    L2, a2, b2 = l2.T
    C1, C2 = np.hypot(a1, b1), np.hypot(a2, b2)
    Cb = (C1 + C2) / 2
    G = 0.5 * (1 - np.sqrt(Cb ** 7 / (Cb ** 7 + 25 ** 7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = np.hypot(a1p, b1), np.hypot(a2p, b2)
    h1p = np.degrees(np.arctan2(b1, a1p)) % 360
    h2p = np.degrees(np.arctan2(b2, a2p)) % 360
    dLp, dCp = L2 - L1, C2p - C1p
    dh = h2p - h1p
    dh = np.where(dh > 180, dh - 360, np.where(dh < -180, dh + 360, dh))
    dh = np.where(C1p * C2p == 0, 0, dh)
    dHp = 2 * np.sqrt(C1p * C2p) * np.sin(np.radians(dh / 2))
    Lbp, Cbp = (L1 + L2) / 2, (C1p + C2p) / 2
    hs = h1p + h2p
    hbp = np.where(C1p * C2p == 0, hs, np.where(np.abs(h1p - h2p) <= 180, hs / 2,
                                                np.where(hs < 360, (hs + 360) / 2, (hs - 360) / 2)))
    T = (1 - 0.17 * np.cos(np.radians(hbp - 30)) + 0.24 * np.cos(np.radians(2 * hbp))
         + 0.32 * np.cos(np.radians(3 * hbp + 6)) - 0.20 * np.cos(np.radians(4 * hbp - 63)))
    dth = 30 * np.exp(-((hbp - 275) / 25) ** 2)
    Rc = 2 * np.sqrt(Cbp ** 7 / (Cbp ** 7 + 25 ** 7))
    Sl = 1 + 0.015 * (Lbp - 50) ** 2 / np.sqrt(20 + (Lbp - 50) ** 2)
    Sc, Sh = 1 + 0.045 * Cbp, 1 + 0.015 * Cbp * T
    Rt = -np.sin(np.radians(2 * dth)) * Rc
    return np.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2 + Rt * (dCp / Sc) * (dHp / Sh))


# ------------------------------------------------------------------ camera model
def base_curve(name):
    import numpy as np
    return np.array(DATA['curves'][name], float) / 16384


def inverse(c, y):
    """Inverse of a base curve on its rising part: output (0..1) -> curve index."""
    import numpy as np
    top = int(np.argmax(c >= 1.0)) if (c >= 1.0).any() else 255
    xs, ys = c[:top + 1], np.arange(256.)[:top + 1]
    keep = np.concatenate([[True], np.diff(xs) > 0])
    return np.interp(np.clip(y, 0, 1), xs[keep], ys[keep])


def to_index(y):
    """Camera output of its neutral rendering (0..1) -> linear signal in curve-index units."""
    return inverse(base_curve('neutral'), y)


def compose(curve, base):
    """The camera's composition of a look curve after the base curve (integer, as the firmware)."""
    out = []
    for v in base:
        i, f = v >> 6, v & 0x3f
        if i > 0xfe:
            out.append(int(curve[255]))
        else:
            p = (int(curve[i + 1]) - int(curve[i])) * f
            out.append(int(curve[i]) + ((p + 0x3f) >> 6 if p < 0 else p >> 6))
    return out


def exported(curves):
    """The camera's final per-channel tone curves (10-bit) for a look."""
    import numpy as np
    base = [int(x) for x in DATA['curves']['slot']]
    src = [base] * 3 if not curves else [compose(c, base) for c in curves]
    return [np.minimum(np.array(s) >> 4, 1023) for s in src]


def render(v, look):
    """Linear signal (N,3, index units) -> what the camera writes (0..1), firmware-exact curves."""
    import numpy as np
    M = np.array(look['matrix_q13'], float) / 8192
    z = v @ M.T
    ex = exported(look.get('curves'))
    return np.stack([np.interp(np.clip(z[:, c], 0, 255), np.arange(256.), ex[c]) / 1023 for c in range(3)], 1)


# ------------------------------------------------------------------ fitting
CHANNELS = {'single': [0, 0, 0], 'rg-b': [0, 0, 1], 'r-gb': [0, 1, 1], 'rb-g': [0, 1, 0], 'rgb': [0, 1, 2]}


def _softplus(x):
    import numpy as np
    return np.logaddexp(0, x)


class Fitter:
    """Gradient descent (Adam) on a perceptual colour difference.

    Model: out_c = C_c[ T(M v)_c ] with M a white-preserving 3x3 matrix, T the slot's
    base curve and C_c one or two free non-decreasing curves. Loss per colour: a
    CIE94/CIEDE2000-style weighted Lab distance in the target's lightness/chroma/hue
    frame, sqrt'ed so it behaves like ΔE; plus a smoothness penalty on the curves.
    """

    def __init__(self, v, target, mode='single', smooth=50.0, weight=None):
        import numpy as np
        self.v, self.mode, self.smooth = v, mode, smooth
        w = np.ones(len(v)) if weight is None else np.asarray(weight, float)
        self.w = w / w.sum()                                          # per-colour weights, sum 1
        self.chan = CHANNELS[mode]
        lt = lab(target)
        self.lt = lt
        C = np.hypot(lt[:, 1], lt[:, 2])
        self.u = np.where(C[:, None] > 1e-6, lt[:, 1:] / np.maximum(C, 1e-6)[:, None], [1.0, 0.0])
        self.h = np.stack([-self.u[:, 1], self.u[:, 0]], 1)
        self.SL = 1 + 0.015 * (lt[:, 0] - 50) ** 2 / np.sqrt(20 + (lt[:, 0] - 50) ** 2)
        self.SC, self.SH = 1 + 0.045 * C, 1 + 0.015 * C
        self.T = base_curve('slot')
        self.Tslope = np.diff(self.T)

    def curves(self, raw):
        import numpy as np
        return np.cumsum(_softplus(raw), 1)

    def loss_grad(self, theta, raw):
        import numpy as np
        v, N = self.v, len(self.v)
        M = np.concatenate([theta, 1 - theta.sum(1, keepdims=True)], 1)
        z = v @ M.T
        zc = np.clip(z, 0, 255)
        i = np.minimum(np.floor(zc).astype(int), 254)
        f = zc - i
        b = self.T[i] * (1 - f) + self.T[i + 1] * f
        mz = (z > 0) & (z < 255)
        Ck = self.curves(raw)
        Cc = Ck[self.chan]                                           # (3,256)
        idx = np.clip(b * 256, 0, 255)
        j = np.minimum(np.floor(idx).astype(int), 254)
        g = idx - j
        rows = np.arange(3)[None, :]
        c0, c1 = Cc[rows, j], Cc[rows, j + 1]
        out = c0 * (1 - g) + c1 * g
        mi = (b * 256 > 0) & (b * 256 < 255)
        # Lab of the prediction
        x = np.clip(out, 0, 1)
        lin = np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)
        dlin = np.where(x <= 0.04045, 1 / 12.92, 2.4 / 1.055 * ((x + 0.055) / 1.055) ** 1.4) * ((out > 0) & (out < 1))
        t = lin @ np.array(XYZ).T / np.array(WHITE)
        big = t > 216 / 24389
        F = np.where(big, np.cbrt(np.maximum(t, 1e-12)), (24389 / 27 * t + 16) / 116)
        dF = np.where(big, 1 / 3 * np.maximum(t, 1e-12) ** (-2 / 3), 24389 / 27 / 116)
        lp = np.stack([116 * F[:, 1] - 16, 500 * (F[:, 0] - F[:, 1]), 200 * (F[:, 1] - F[:, 2])], 1)
        d = lp - self.lt
        dL = d[:, 0]
        dC = (d[:, 1:] * self.u).sum(1)
        dH = (d[:, 1:] * self.h).sum(1)
        q = (dL / self.SL) ** 2 + (dC / self.SC) ** 2 + (dH / self.SH) ** 2
        e = np.sqrt(q + 1e-8)
        loss = (self.w * e).sum()
        w = self.w / (2 * e)
        gL = w * 2 * dL / self.SL ** 2
        gab = (w * 2)[:, None] * ((dC / self.SC ** 2)[:, None] * self.u + (dH / self.SH ** 2)[:, None] * self.h)
        gLab = np.concatenate([gL[:, None], gab], 1)
        J = np.array([[0, 116, 0], [500, -500, 0], [0, 200, -200]], float)
        gF = gLab @ J
        gt = gF * dF / np.array(WHITE)
        glin = gt @ np.array(XYZ)
        gout = glin * dlin
        # through the look curves
        gC = np.zeros_like(Ck)
        for c in range(3):
            k = self.chan[c]
            np.add.at(gC[k], j[:, c], gout[:, c] * (1 - g[:, c]))
            np.add.at(gC[k], j[:, c] + 1, gout[:, c] * g[:, c])
        gidx = gout * (c1 - c0) * mi
        gz = gidx * 256 * self.Tslope[i] * mz
        gtheta = np.stack([(gz * (v[:, 0:1] - v[:, 2:3])).sum(0), (gz * (v[:, 1:2] - v[:, 2:3])).sum(0)], 1)
        # smoothness penalty
        D = Ck[:, 2:] - 2 * Ck[:, 1:-1] + Ck[:, :-2]
        pen = self.smooth * (D ** 2).sum(1).mean()
        gD = 2 * self.smooth * D / len(Ck)
        gC[:, 2:] += gD
        gC[:, 1:-1] -= 2 * gD
        gC[:, :-2] += gD
        sig = 1 / (1 + np.exp(-raw))
        graw = sig * np.cumsum(gC[:, ::-1], 1)[:, ::-1]
        return loss + pen, loss, gtheta, graw

    def run(self, target, iters=1500, lr=5e-3, log=None):
        import numpy as np
        v = self.v
        # least-squares start for the matrix, identity start for the curves
        inv_t = inverse(self.T, target)
        theta = np.zeros((3, 2))
        xr = v[:, :2] - v[:, 2:3]
        for c in range(3):
            theta[c] = np.linalg.lstsq(xr, inv_t[:, c] - v[:, 2], rcond=None)[0]
        if not np.isfinite(theta).all() or np.abs(theta).max() > 3:
            theta = np.array([[1., 0.], [0., 1.], [0., 0.]])
        ident = np.arange(256) / 256.0
        dd = np.clip(np.diff(np.concatenate([[0.0], ident])), 1e-6, None)
        raw = np.tile(np.log(np.expm1(dd)), (max(self.chan) + 1, 1))
        state = [[np.zeros_like(p), np.zeros_like(p)] for p in (theta, raw)]
        hist = []
        for it in range(iters):
            total, loss, gt, gr = self.loss_grad(theta, raw)
            a = lr * 0.5 * (1 + math.cos(math.pi * it / iters))
            for p, gp, st in ((theta, gt, state[0]), (raw, gr, state[1])):
                st[0] = 0.9 * st[0] + 0.1 * gp
                st[1] = 0.999 * st[1] + 0.001 * gp ** 2
                mh, vh = st[0] / (1 - 0.9 ** (it + 1)), st[1] / (1 - 0.999 ** (it + 1))
                p -= a * mh / (np.sqrt(vh) + 1e-8)
            if it % max(1, iters // 10) == 0 or it == iters - 1:
                hist.append([it, round(float(loss), 4)])
                if log:
                    log(f'    step {it:5d}  loss {loss:.4f}')
        M = np.concatenate([theta, 1 - theta.sum(1, keepdims=True)], 1)
        q = np.round(M * 8192).astype(int)
        q[:, 2] = 8192 - q[:, 0] - q[:, 1]
        Ck = np.clip(np.round(self.curves(raw) * 16384), 0, 16383).astype(int)
        Ck = np.maximum.accumulate(Ck, axis=1)
        return dict(matrix_q13=q.tolist(), curve_mode=self.mode,
                    curves=[Ck[k].tolist() for k in self.chan], history=hist)


# ------------------------------------------------------------------ scoring
HUES = {'red': (330, 30), 'orange/skin': (30, 75), 'yellow': (75, 105), 'green': (105, 180),
        'cyan': (180, 240), 'blue': (240, 290), 'purple/magenta': (290, 330)}


def score(pred, target):
    import numpy as np
    lt, lp = lab(target), lab(np.clip(pred, 0, 1))
    e = de00(lt, lp)
    C = np.hypot(lt[:, 1], lt[:, 2])
    h = np.degrees(np.arctan2(lt[:, 2], lt[:, 1])) % 360

    def band(mk):
        return round(float(e[mk].mean()), 3) if mk.sum() >= 20 else None
    r = dict(colours=int(len(e)), de00_mean=round(float(e.mean()), 3), de00_p95=round(float(np.percentile(e, 95)), 3),
             brightness_shift=round(float((lp[:, 0] - lt[:, 0]).mean()), 2),
             hue={k: band((((h >= a) | (h < b)) if a > b else ((h >= a) & (h < b))) & (C >= 10))
                  for k, (a, b) in HUES.items()})
    r['verdict'] = 'good' if r['de00_mean'] < 1 and r['de00_p95'] < 2 else \
        'approximate' if r['de00_mean'] < 2 and r['de00_p95'] < 4 else 'poor'
    return r


def evaluate(look, y, target):
    return score(render(to_index(y), look), target)


def unchanged(y, target):
    """How far the LUT is from the camera's neutral rendering (no look at all)."""
    return score(neutral(to_index(y)), target)


# ------------------------------------------------------------------ photos (optional)
def photo_signal(dng, max_side=400):
    """Linear signal of a DNG in the camera model's units (needs rawpy)."""
    import numpy as np
    try:
        import rawpy
    except ImportError:
        raise Refused('--photo / preview need rawpy and pillow: python3 -m pip install rawpy pillow')
    with rawpy.imread(str(dng)) as r:
        img = r.raw_image_visible.astype(np.float32)
        s = r.sizes
        black = np.array(r.black_level_per_channel, np.float32)
        white = float(r.white_level)
        cl = r.raw_colors_visible
        wb = np.array(r.camera_whitebalance[:3], float)
    if s.crop_height and s.crop_width:
        t, l = s.crop_top_margin, s.crop_left_margin
        img, cl = img[t:t + s.crop_height, l:l + s.crop_width], cl[t:t + s.crop_height, l:l + s.crop_width]
    img = (img - black[cl]) / (white - black[cl])
    h, w = img.shape[0] // 2 * 2, img.shape[1] // 2 * 2
    q = img[:h, :w].reshape(h // 2, 2, w // 2, 2).transpose(0, 2, 1, 3).reshape(h // 2, w // 2, 4)
    qc = cl[:2, :2].reshape(4)
    rgb = np.stack([q[..., [k for k in range(4) if qc[k] in idx]].mean(-1) for idx in ([0], [1, 3], [2])], -1)
    f = max(1, int(np.ceil(max(rgb.shape[:2]) / max_side)))
    H, W = rgb.shape[0] // f * f, rgb.shape[1] // f * f
    rgb = rgb[:H, :W].reshape(H // f, f, W // f, f, 3).mean((1, 3))
    yy, xx = np.mgrid[0:rgb.shape[0], 0:rgb.shape[1]]
    r2 = ((yy - rgb.shape[0] / 2) / (rgb.shape[0] / 2)) ** 2 + ((xx - rgb.shape[1] / 2) / (rgb.shape[1] / 2)) ** 2
    cam = rgb * (wb / wb[1]) * np.exp(0.18 * r2)[..., None]
    return cam @ (np.array(DATA['camera_matrix']) / 8192).T * 100.0


def neutral(v):
    """The camera's neutral rendering of a linear signal (no look)."""
    import numpy as np
    T = base_curve('neutral')
    return np.stack([np.interp(np.clip(v[..., c], 0, 255), np.arange(256.), T) for c in range(3)], -1)


def apply_lut(lut, y, space):
    if space == 'adobe':
        return adobe_lut_on_srgb(lut, y)[0]
    return lut(y)


# ------------------------------------------------------------------ fit command
PAIR_GAIN, HELD_TOL, PHOTO_GAIN = 0.10, 0.02, 0.5
PHOTO_WEIGHT = 0.5      # the photo counts half as much as the LUT's own colours, however many pixels it has
GREY_WEIGHT = 0.5       # neutral greys count half as much too: a colour cast on greys is the most visible error
GREY_TOL, CC_TOL = 0.10, 0.10            # more curves must not make greys or the ColorChecker worse by more
GREY_GAIN, RANGE_TOL = 0.5, 0.05         # ... and count as a gain when greys improve by 0.5 (range within 5 %)
EVERYDAY_CC, EVERYDAY_GREY, EVERYDAY_CAST = 2.0, 2.0, 2.5
# "good on everyday colours": ColorChecker mean < 2 and greys < 2 (a small visible difference at most),
# and no visible colour cast on any grey (largest a*b* difference < 2.5)

# X-Rite ColorChecker Classic, widely published sRGB values (8-bit): everyday reference colours
COLORCHECKER = [
    ('dark skin', 115, 82, 68), ('light skin', 194, 150, 130), ('blue sky', 98, 122, 157),
    ('foliage', 87, 108, 67), ('blue flower', 133, 128, 177), ('bluish green', 103, 189, 170),
    ('orange', 214, 126, 44), ('purplish blue', 80, 91, 166), ('moderate red', 193, 90, 99),
    ('purple', 94, 60, 108), ('yellow green', 157, 188, 64), ('orange yellow', 224, 163, 46),
    ('blue', 56, 61, 150), ('green', 70, 148, 73), ('red', 175, 54, 60), ('yellow', 231, 199, 31),
    ('magenta', 187, 86, 149), ('cyan', 8, 133, 161), ('white', 243, 243, 242), ('neutral 8', 200, 200, 200),
    ('neutral 6.5', 160, 160, 160), ('neutral 5', 122, 122, 121), ('neutral 3.5', 85, 85, 85), ('black', 52, 52, 52)]


def greys(n=64):
    import numpy as np
    x = np.linspace(0.02, 1.0, n)
    return np.stack([x, x, x], 1)


def everyday(look, lut, space):
    """Scores on the ColorChecker and on a neutral grey ramp (with the largest colour cast on the greys)."""
    import numpy as np
    out = {}
    for name, y in (('colorchecker', np.array([c[1:] for c in COLORCHECKER], float) / 255), ('greys', greys())):
        t = apply_lut(lut, y, space)
        lt, lp = lab(t), lab(np.clip(render(to_index(y), look), 0, 1))
        e = de00(lt, lp)
        r = dict(de00_mean=round(float(e.mean()), 3), de00_max=round(float(e.max()), 3))
        if name == 'colorchecker':
            r['worst'] = COLORCHECKER[int(e.argmax())][0]
            r['skin'] = round(float(e[:2].mean()), 3)
        else:
            r['cast_max'] = round(float(np.hypot(*(lp[:, 1:] - lt[:, 1:]).T).max()), 2)
        out[name] = r
    return out


def fit_lut(path, space='srgb', curve='auto', photo=None, iters=1500, log=print):
    import numpy as np
    lut = Lut(path)
    if lut.lo.tolist() == [0, 0, 0] and lut.hi.tolist() == [1, 1, 1]:
        y = grid(lut.n)
    else:
        y = grid(33)
    if space == 'adobe':
        t, keep = adobe_lut_on_srgb(lut, y)
        y, t = y[keep], t[keep]
    else:
        t = lut(y)
    log(f'{Path(path).name}: {lut.kind} LUT, {len(y)} colours, {space}'
        + (f' (ignored: {", ".join(sorted(set(lut.ignored)))})' if lut.ignored else ''))
    ty = t
    gy = greys()
    v = np.concatenate([to_index(y), to_index(gy)])
    t = np.concatenate([t, apply_lut(lut, gy, space)])
    weight = np.concatenate([np.ones(len(y)) / len(y), np.full(len(gy), GREY_WEIGHT / len(gy))])
    held = None
    if photo:
        img = photo_signal(photo)
        top = np.zeros(img.shape[:2], bool)
        top[: img.shape[0] // 2] = True
        pv, top = img.reshape(-1, 3), top.ravel()
        yb = neutral(pv)
        ok = (yb.max(1) < 0.98) & (yb.min(1) > 0.01)
        tb = apply_lut(lut, yb, space)
        n_photo = int((ok & top).sum())
        v = np.concatenate([v, pv[ok & top]])
        t = np.concatenate([t, tb[ok & top]])
        weight = np.concatenate([weight, np.full(n_photo, PHOTO_WEIGHT / max(n_photo, 1))])
        held = (yb[ok & ~top], tb[ok & ~top])
        log(f'  photo: {int((ok & top).sum())} pixels join the fit, {int((ok & ~top).sum())} are held out')

    def one(mode):
        look = Fitter(v, t, mode, weight=weight).run(t, iters=iters)
        e = evaluate(look, y, ty)['de00_mean']
        h = evaluate(look, *held)['de00_mean'] if held else None
        ev = everyday(look, lut, space)
        log(f'  {mode:7s} ΔE00 {e:.3f}' + (f'  photo {h:.3f}' if h is not None else '')
            + f'  ColorChecker {ev["colorchecker"]["de00_mean"]:.3f}  greys {ev["greys"]["de00_mean"]:.3f}')
        return dict(e=e, h=h, cc=ev['colorchecker']['de00_mean'], grey=ev['greys']['de00_mean'], look=look)
    def better(new, old):
        """More curves only when they clearly help (whole range, everyday colours or greys)
        and make nothing worse (photo, greys, ColorChecker, whole range)."""
        gain = (new['e'] < old['e'] * (1 - PAIR_GAIN) or new['cc'] < old['cc'] * (1 - PAIR_GAIN)
                or new['grey'] <= old['grey'] - GREY_GAIN)
        no_worse = ((old['h'] is None or new['h'] <= old['h'] + HELD_TOL) and new['grey'] <= old['grey'] + GREY_TOL
                    and new['cc'] <= old['cc'] + CC_TOL and new['e'] <= old['e'] * (1 + RANGE_TOL))
        return gain and no_worse
    if curve == 'auto':
        use = one('single')
        p = min((one(m) for m in ('rg-b', 'r-gb', 'rb-g')), key=lambda r: r['e'])
        if better(p, use):
            use = p
        t3 = one('rgb')
        if better(t3, use):
            use = t3
    elif curve == 'pair':
        use = min((one(m) for m in ('rg-b', 'r-gb', 'rb-g')), key=lambda r: r['e'])
    else:
        use = one(curve)
    look = use['look']
    scores = dict(fit=evaluate(look, y, ty), unchanged=unchanged(y, ty), **everyday(look, lut, space))
    if held:
        scores['photo'] = evaluate(look, *held)
        scores['photo_unchanged'] = unchanged(*held)
    ok, why = decide(scores)
    return dict(tool=f'GR4-LUTSmith {VERSION}', lut=dict(file=str(Path(path).resolve()), sha256=lut.sha256, kind=lut.kind,
                                                          title=lut.title, space=space),
                matrix_q13=look['matrix_q13'], curve_mode=look['curve_mode'], curves=look['curves'],
                scores=scores, decision=dict(build=ok, reason=why), fit=dict(iters=iters, history=look['history']))


def decide(scores):
    """Build when the LUT's whole colour range fits, or when everyday colours do."""
    f = scores['fit']
    if f['verdict'] != 'poor':
        return True, f'fit {f["verdict"]}'
    cc, gr = scores['colorchecker'], scores['greys']
    p, p0 = scores.get('photo'), scores.get('photo_unchanged')
    photo_ok = p is None or (p['verdict'] != 'poor' and p['de00_mean'] <= p0['de00_mean'])
    no_cast = gr['de00_mean'] < EVERYDAY_GREY and gr['cast_max'] < EVERYDAY_CAST
    if cc['de00_mean'] < EVERYDAY_CC and no_cast and photo_ok:
        return True, (f'everyday colours fit (ColorChecker {cc["de00_mean"]}, greys {gr["de00_mean"]}, '
                      f'largest cast {gr["cast_max"]}); only extreme saturated colours deviate')
    if p and p['verdict'] == 'good' and p['de00_mean'] <= PHOTO_GAIN * p0['de00_mean'] and no_cast:
        return True, f'fit poor on extreme colours, but good on your photo ({p["de00_mean"]} vs {p0["de00_mean"]})'
    return False, (f'fit poor; ColorChecker {cc["de00_mean"]}, greys {gr["de00_mean"]} '
                   f'(largest cast {gr["cast_max"]})'
                   + (f'; photo {p["de00_mean"]} vs unchanged {p0["de00_mean"]}' if p else ''))


def describe(look, log=print):
    s = look['scores']
    f = s['fit']
    log(f'  result: {f["verdict"].upper()}  (ΔE00 {f["de00_mean"]}, p95 {f["de00_p95"]}; '
        f'without the look {s["unchanged"]["de00_mean"]})')
    if 'photo' in s:
        log(f'  on your photo: ΔE00 {s["photo"]["de00_mean"]} (without the look {s["photo_unchanged"]["de00_mean"]})')
    worst = sorted(((v, k) for k, v in f['hue'].items() if v is not None), reverse=True)[:3]
    log('  hardest colours: ' + ', '.join(f'{k} {v}' for v, k in worst))
    cc, gr = s.get('colorchecker'), s.get('greys')
    if cc and gr:
        log(f'  everyday colours: ColorChecker ΔE00 {cc["de00_mean"]} (skin {cc["skin"]}, worst {cc["worst"]}); '
            f'greys {gr["de00_mean"]} (largest cast {gr["cast_max"]})')
    log(f'  curves: {look["curve_mode"]}; decision: {look["decision"]["reason"]}')


def load_look(path):
    look = json.loads(Path(path).read_text())
    if 'look' in look and 'matrix_q13' not in look:         # look files written by earlier tools
        look = dict(look['look'], scores=look.get('scores'))
    for k in ('matrix_q13',):
        if k not in look:
            raise Refused(f'{path}: not a look file')
    return look


# ------------------------------------------------------------------ preview
def preview(look, dng, out, lut_path=None, space='srgb'):
    import numpy as np
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        raise Refused('preview needs pillow: python3 -m pip install rawpy pillow')
    v = photo_signal(dng, max_side=1200)
    flat = v.reshape(-1, 3)
    panels = [neutral(flat)]
    labels = ['camera, no look']
    if lut_path and Path(lut_path).exists():
        panels.append(apply_lut(Lut(lut_path), panels[0], space))
        labels.append('LUT')
    panels.append(render(flat, look))
    labels.append('camera with the look')
    ims = [Image.fromarray((np.clip(p.reshape(v.shape), 0, 1) * 255 + 0.5).astype(np.uint8)) for p in panels]
    w, h = ims[0].size
    sheet = Image.new('RGB', (len(ims) * w + 8 * (len(ims) - 1), h + 28), (24, 24, 24))
    d = ImageDraw.Draw(sheet)
    for k, (im, text) in enumerate(zip(ims, labels)):
        sheet.paste(im, (k * (w + 8), 28))
        d.text((k * (w + 8) + 6, 8), text, fill=(230, 230, 230))
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, quality=92)
    return out


# ------------------------------------------------------------------ main
def need_numpy():
    try:
        import numpy  # noqa: F401
    except ImportError:
        raise Refused('this command needs numpy: python3 -m pip install numpy')


def main(argv=None):
    ap = argparse.ArgumentParser(prog='gr4_lutsmith.py', description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--version', action='version', version=VERSION)
    sub = ap.add_subparsers(dest='cmd', required=True)

    def lut_args(p):
        p.add_argument('lut', type=Path, help='.cube file (3D or 1D)')
        p.add_argument('--space', choices=('srgb', 'adobe'), default='srgb',
                       help='colour space the LUT was made for (default srgb)')
        p.add_argument('--photo', type=Path, help='a DNG from your GR IV: judges the fit on real content (needs rawpy)')
        p.add_argument('--curve', choices=('auto', 'single', 'pair', 'rgb'), default='auto', help=argparse.SUPPRESS)
        p.add_argument('--iters', type=int, default=1500, help=argparse.SUPPRESS)
    m = sub.add_parser('make', help='LUT + official firmware -> firmware with the look')
    lut_args(m)
    m.add_argument('input', type=Path, help='official RICOH fwdc248b.bin (GR IV 1.11)')
    m.add_argument('--force', action='store_true', help='build even if the fit is poor')
    m.add_argument('-o', '--output-dir', type=Path)
    f = sub.add_parser('fit', help='fit a LUT only (writes look.json)')
    lut_args(f)
    f.add_argument('-o', '--output-dir', type=Path)
    b = sub.add_parser('build', help='look.json + official firmware -> firmware with the look')
    b.add_argument('look', type=Path)
    b.add_argument('input', type=Path)
    b.add_argument('-o', '--output-dir', type=Path)
    p = sub.add_parser('preview', help='render a DNG with the look (needs rawpy, pillow)')
    p.add_argument('look', type=Path)
    p.add_argument('photo', type=Path)
    p.add_argument('-o', '--output', type=Path)
    c = sub.add_parser('check', help='identify a fwdc248b.bin and validate its container')
    c.add_argument('input', type=Path)
    s = sub.add_parser('selftest', help='build the bundled example and compare with the verified result')
    s.add_argument('input', type=Path)
    a = ap.parse_args(argv)
    sys.stdout.reconfigure(line_buffering=True)
    if sys.version_info < (3, 8):
        print('Python 3.8 or newer is required', file=sys.stderr)
        return 2
    try:
        if a.cmd == 'check':
            return identify(a.input.read_bytes())
        print(f'GR4-LUTSmith {VERSION}')
        if a.cmd == 'selftest':
            look = load_look(Path(__file__).resolve().parent / SELFTEST_LOOK)
            out = make_firmware(a.input.read_bytes(), look)
            ok = sha256(out) == SELFTEST_SHA256
            print(f'selftest: {"PASSED" if ok else "FAILED"} (SHA-256 {sha256(out)})')
            return 0 if ok else 1
        need_numpy()
        if a.cmd == 'preview':
            look = load_look(a.look)
            lut = look.get('lut', {})
            src = lut.get('file') if lut else None
            out = preview(look, a.photo, a.output or a.look.with_name('preview.jpg'), src, lut.get('space', 'srgb'))
            print(f'wrote {out}')
            return 0
        if a.cmd in ('make', 'fit'):
            out_dir = a.output_dir or Path('output') / a.lut.stem
            if a.cmd == 'make':
                source = a.input.read_bytes()
                if sha256(source) != OFFICIAL_SHA256:
                    make_firmware(source, dict(matrix_q13=[[8192, 0, 0], [0, 8192, 0], [0, 0, 8192]]))
                if (out_dir / 'fwdc248b.bin').exists():
                    raise Refused(f'{out_dir / "fwdc248b.bin"} already exists; choose another output directory')
            look = fit_lut(a.lut, a.space, a.curve, a.photo, a.iters)
            describe(look)
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / 'look.json').write_text(json.dumps(look, indent=1) + '\n')
            print(f'wrote {out_dir / "look.json"}')
            if a.cmd == 'fit':
                return 0
            if not look['decision']['build'] and not a.force:
                raise Refused('the LUT cannot be reproduced well by the camera (see above); '
                              'use --force to build anyway')
            data = make_firmware(source, look)
            target = write_atomic(data, out_dir)
            print(f'wrote {target}  (SHA-256 {sha256(data)})')
            print('Copy this file to the root of the SD card and run the camera\'s firmware update.')
            return 0
        if a.cmd == 'build':
            look = load_look(a.look)
            out_dir = a.output_dir or a.look.parent
            data = make_firmware(a.input.read_bytes(), look)
            target = write_atomic(data, out_dir)
            print(f'wrote {target}  (SHA-256 {sha256(data)})')
            return 0
    except Refused as exc:
        print(f'refused: {exc}', file=sys.stderr)
        print('nothing was written.' if a.cmd in ('make', 'build', 'selftest') else '', file=sys.stderr)
        return 1
    except OSError as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
