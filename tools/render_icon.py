"""App icon "Tempered curve": a square steel bar bent into a film tone curve, carrying the colours steel takes when
it is tempered (blue, violet, bronze, straw), lying on an 18% grey card.

Every size is drawn from the same geometry with signed distances (nothing is scaled down); small sizes get their
own bar width and snap to whole pixels. Writes the app's icons: packaging/icon.icns (macOS, needs iconutil),
packaging/icon.ico (Windows) and lutsmith_app/assets/app/icon-<size>.png (the window icon, from the Windows sizes).
Run on a Mac: uv run --extra app python tools/render_icon.py
"""
import struct
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PACKAGING = ROOT / 'packaging'
WINDOW = ROOT / 'lutsmith_app' / 'assets' / 'app'

CARD = '#777777'                                     # 18% grey, L* 50
RAMP = [(0.00, '#2D4778'), (0.30, '#5B4472'), (0.55, '#93603A'), (0.80, '#D2AE66'), (1.00, '#EFE3C2')]
K = 1.9                                              # S steepness (slope at mid-grey = K x range); 2.6 at <= 24 px


# --- colour (OKLab) ---------------------------------------------------------------------------------------------
def hex_rgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float) / 255


def to_lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566],
               [0.0883024619, 0.2817188376, 0.6299787005]])
M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468], [1.9779984951, -2.4285922050, 0.4505937099],
               [0.0259040371, 0.7827717662, -0.8086757660]])
M1i, M2i = np.linalg.inv(M1), np.linalg.inv(M2)


def oklab(rgb):
    return np.cbrt(to_lin(rgb) @ M1.T) @ M2.T


def srgb(lab):
    return to_srgb(np.clip((lab @ M2i.T) ** 3, 0, None) @ M1i.T)


STOP_T = np.array([t for t, _ in RAMP])
STOP_LAB = np.array([oklab(hex_rgb(h)) for _, h in RAMP])


def ramp(t):
    return np.stack([np.interp(t, STOP_T, STOP_LAB[:, i]) for i in range(3)], -1)


# --- shape helpers ----------------------------------------------------------------------------------------------
def cov(sdf, px):
    return np.clip(0.5 - sdf / px, 0, 1)


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def tile_sdf(u, v, ext=0.344, n=3.3):
    """Rounded square with continuous corners like the macOS icon shape: straight sides, and superellipse corners
    that start 0.344 of the side from each corner (radius 0.225 with Apple's smoothing)."""
    x, y = np.abs(u - 0.5), np.abs(v - 0.5)
    c = 0.5 - ext
    cx, cy = np.clip(x - c, 0, None) + 1e-9, np.clip(y - c, 0, None) + 1e-9
    r = (cx ** n + cy ** n) ** (1 / n)
    g = np.hypot((cx / r) ** (n - 1), (cy / r) ** (n - 1))
    corner = (x > c) & (y > c)
    return np.where(corner, (r - ext) / g, np.maximum(x, y) - 0.5)


def segment_sdf(u, v, a, b, hw):
    p = np.stack([u - a[0], v - a[1]], -1)
    ab = np.array(b) - np.array(a)
    h = np.clip((p @ ab) / (ab @ ab), 0, 1)
    return np.hypot(p[..., 0] - ab[0] * h, p[..., 1] - ab[1] * h) - hw


def box(a, w, axis):
    r = w // 2
    pad = [(0, 0)] * a.ndim
    pad[axis] = (r + 1, r)
    c = np.cumsum(np.pad(a, pad, mode='edge'), axis=axis)
    n = a.shape[axis]
    return (np.take(c, np.arange(w, w + n), axis=axis) - np.take(c, np.arange(n), axis=axis)) / w


def blur(a, sigma):
    if sigma < 0.35:
        return a
    w = int(round(np.sqrt(4 * sigma ** 2 + 1)))
    w += 1 - w % 2
    for _ in range(3):
        a = box(box(a, w, 0), w, 1)
    return a


def shift(a, dy):
    """Move down by a whole number of pixels."""
    if dy <= 0:
        return a
    out = np.zeros_like(a)
    out[dy:] = a[:-dy]
    return out


# --- the bar ----------------------------------------------------------------------------------------------------
def centreline(x0, x1, y_toe, y_top, k=K, n=1200, ext=0.35):
    """Film S from the lifted toe (bottom left) to the soft shoulder (top right); straight extensions past both ends
    so the square-cut ends get exact distances. Returns points (tile units, y down), arc position of each point
    (0 at the toe end) and the bar's length."""
    x = np.linspace(0, 1, n)
    s = x ** k / (x ** k + (1 - x) ** k)
    pts = np.stack([x0 + x * (x1 - x0), y_toe + (y_top - y_toe) * s], -1)
    t0 = (pts[1] - pts[0]) / np.hypot(*(pts[1] - pts[0]))
    t1 = (pts[-1] - pts[-2]) / np.hypot(*(pts[-1] - pts[-2]))
    e = np.linspace(ext, 0, 40)[:-1]
    pts = np.concatenate([pts[0] - e[:, None] * t0, pts, pts[-1] + e[::-1, None] * t1])
    arc = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(pts, axis=0).T))])
    arc -= arc[39]
    return pts, arc, arc[39 + n - 1]


def stroke_field(P, V, arc):
    """Signed distance from the centreline (upper side positive) and arc position of the nearest point."""
    seg = V[1:] - V[:-1]
    sl = np.hypot(*seg.T)
    T = seg / sl[:, None]
    coarse = np.arange(0, len(V), 4)
    d_out, s_out = np.empty(len(P)), np.empty(len(P))
    rows = np.arange(-6, 6)
    for a in range(0, len(P), 16384):
        p = P[a:a + 16384]
        ic = coarse[((p[:, None, :] - V[coarse][None]) ** 2).sum(-1).argmin(1)]
        idx = np.clip(ic[:, None] + rows, 0, len(seg) - 1)
        A, tt, L = V[idx], T[idx], sl[idx]
        along = np.clip(((p[:, None, :] - A) * tt).sum(-1), 0, L)
        Q = A + tt * along[..., None]
        dd = ((p[:, None, :] - Q) ** 2).sum(-1)
        j = dd.argmin(1)
        r = np.arange(len(p))
        diff, tj = p - Q[r, j], tt[r, j]
        cross = tj[:, 0] * diff[:, 1] - tj[:, 1] * diff[:, 0]
        d_out[a:a + len(p)] = -np.sign(cross) * np.sqrt(dd[r, j])
        s_out[a:a + len(p)] = arc[idx[r, j]] + along[r, j]
    return d_out, s_out


# --- sizes ------------------------------------------------------------------------------------------------------
def params(size, plat):
    if plat == 'mac':
        body = {16: 14, 32: 26}.get(size, round(size * 824 / 1024))
    else:
        body = size if size <= 24 else size - 2 * round(size * 0.03)
    p = dict(body=body, k=2.6 if size <= 24 else K, x0=0.15, x1=0.85, y_toe=0.766, y_top=0.199, hw=0.042, side=0.032,
             grid='frame' if size >= 128 else None, grid_w=0.0026, grid_a=0.08, tick=0.03, grain=size >= 256, bevel=0.10 if size >= 64 else 0.05,
             sheen=0.04 if size >= 64 else 0.0, sh_dy=0.018, sh_sigma=0.018, sh_a=0.38,
             drop=plat == 'mac' or size > 24)
    if size <= 64:                                   # whole-pixel bar width and edges
        o = (size - body) / 2
        w = max(2, round(2 * p['hw'] * body))
        p['hw'] = w / 2 / body
        snap = lambda y: (round(o + body * y - w / 2) + w / 2 - o) / body
        p['y_toe'], p['y_top'] = snap(p['y_toe']), snap(p['y_top'])
        p['x0'] = (round(o + body * p['x0']) - o) / body
        p['x1'] = (round(o + body * p['x1']) - o) / body
        p['sh_a'] = 0.30
    return p


def render(size, plat='mac', **over):
    p = params(size, plat)
    p.update(over)
    S, B = size, p['body']
    o = (S - B) / 2
    ys, xs = np.mgrid[0:S, 0:S] + 0.5
    u, v, px = (xs - o) / B, (ys - o) / B, 1 / B
    rng = np.random.default_rng(7)

    tsdf = tile_sdf(u, v)
    tile = cov(tsdf, px)

    # grey card, lit from above
    card = oklab(hex_rgb(CARD))
    lab = np.broadcast_to(card, (S, S, 3)).copy()
    lab[..., 0] += 0.045 * (0.5 - v)
    if p['grain']:
        lab[..., 0] += rng.normal(0, 0.0035, (S, S))
    rgb = srgb(lab)

    # the curve's grid, printed faintly on the card
    if p['grid']:
        g0, g1 = p['x0'], p['x1']
        lw = max(px * 0.55, p['grid_w'] / 2)
        lines = np.zeros_like(u)
        quarters = [g0 + q * (g1 - g0) for q in (0, 0.25, 0.5, 0.75, 1)]
        if p['grid'] == 'ticks':                      # scale marks along the input and output axes
            a, b = g1 + 0.03, g1 + 0.03 + p['tick']
            for c in quarters:
                lines = np.maximum(lines, cov(segment_sdf(u, v, (c, a), (c, b), lw), px))
                lines = np.maximum(lines, cov(segment_sdf(u, v, (1 - a, c), (1 - b, c), lw), px))
        else:
            for c in quarters[1:-1] if p['grid'] == 'inner' else quarters:
                lines = np.maximum(lines, cov(segment_sdf(u, v, (c, g0), (c, g1), lw), px))
                lines = np.maximum(lines, cov(segment_sdf(u, v, (g0, c), (g1, c), lw), px))
        rgb = rgb * (1 - p['grid_a'] * lines[..., None])

    # bar
    V, arc, L = centreline(p['x0'], p['x1'], p['y_toe'], p['y_top'], p['k'])
    d, s = stroke_field(np.stack([u.ravel(), v.ravel()], -1), V, arc)
    d, s = d.reshape(S, S), s.reshape(S, S)
    hw = p['hw']
    bar_sdf = np.maximum(np.abs(d) - hw, np.maximum(-s, s - L))
    top = cov(bar_sdf, px)
    hp = max(1, round(p['side'] * B))
    side = np.zeros_like(top)
    for k in range(1, hp + 1):
        side = np.maximum(side, shift(top, k))
    solid = np.maximum(top, side)

    # shadows on the card: soft cast shadow below, tight contact shadow at the foot
    soft = blur(shift(solid, max(1, round(p['sh_dy'] * B))), p['sh_sigma'] * B) * p['sh_a']
    contact = blur(shift(solid, max(1, round(0.004 * B))), max(0.5, 0.004 * B)) * 0.30
    shade = 1 - (1 - soft) * (1 - contact)
    rgb = rgb * (1 - shade[..., None])

    t = np.clip(s / L, 0, 1)
    base = ramp(t)
    face = base.copy()                                # front face: same colours, in shade
    frac = np.clip(bar_sdf / (hp * px), 0, 1)
    face[..., 0] *= 0.70 - 0.14 * frac
    face[..., 1:] *= 0.92
    vis_side = side * (1 - top)
    rgb = rgb * (1 - vis_side[..., None]) + srgb(face) * vis_side[..., None]

    sn = np.clip(d / hw, -1, 1)                       # +1 upper edge, -1 lower edge
    lit = base.copy()
    lit[..., 0] += (p['bevel'] * smooth(0.74, 0.97, sn) - 0.04 * smooth(0.78, 0.98, -sn)
                    + p['sheen'] * np.exp(-((sn - 0.30) / 0.28) ** 2))
    if p['grain']:                                    # fine polish lines running along the bar
        lines = np.interp(sn * hw * B, np.arange(-200, 201), rng.normal(0, 1, 401))
        lit[..., 0] += 0.006 * lines
    rgb = rgb * (1 - top[..., None]) + srgb(lit) * top[..., None]

    # tile edge: light rim at the top, a faint dark rim all round
    rim_w = max(px, 0.0035)
    ring = tile - cov(tsdf + rim_w, px)
    rgb += (1 - rgb) * (0.20 * ring * np.clip(1.2 - 2.2 * v, 0, 1))[..., None]
    dark = tile - cov(tsdf + max(px * 0.8, 0.0015), px)
    rgb *= 1 - 0.14 * dark[..., None]

    # drop shadow under the tile, then composite
    if p['drop']:
        k = S / 1024
        drop = blur(shift(tile, max(1, round(10 * k))), max(0.5, 9 * k)) * (0.30 if plat == 'mac' else 0.22)
    else:
        drop = np.zeros_like(tile)
    alpha = tile + drop * (1 - tile)
    out = np.where(alpha[..., None] > 0, rgb * tile[..., None] / np.maximum(alpha, 1e-6)[..., None], 0)
    img = np.dstack([out, alpha])
    return Image.fromarray(np.round(np.clip(img, 0, 1) * 255).astype(np.uint8), 'RGBA')


# --- files ------------------------------------------------------------------------------------------------------
def write_ico(path, images):
    blobs = []
    for im in images:
        from io import BytesIO
        b = BytesIO()
        im.save(b, 'PNG')
        blobs.append(b.getvalue())
    head = struct.pack('<HHH', 0, 1, len(images))
    off = 6 + 16 * len(images)
    dirs = b''
    for im, blob in zip(images, blobs):
        w = im.width if im.width < 256 else 0
        dirs += struct.pack('<BBBBHHII', w, w, 0, 0, 1, 32, len(blob), off)
        off += len(blob)
    path.write_bytes(head + dirs + b''.join(blobs))


def main():
    mac = {s: render(s, 'mac') for s in (16, 32, 64, 128, 256, 512, 1024)}
    win = {s: render(s, 'win') for s in (16, 20, 24, 32, 40, 48, 64, 96, 128, 256)}
    WINDOW.mkdir(parents=True, exist_ok=True)
    for old in WINDOW.glob('icon*.png'):
        old.unlink()
    for s, im in win.items():
        im.save(WINDOW / f'icon-{s}.png')
    with tempfile.TemporaryDirectory() as d:
        iconset = Path(d) / 'AppIcon.iconset'
        iconset.mkdir()
        for pt in (16, 32, 128, 256, 512):
            mac[pt].save(iconset / f'icon_{pt}x{pt}.png')
            mac[pt * 2].save(iconset / f'icon_{pt}x{pt}@2x.png') if pt * 2 in mac else None
        subprocess.run(['iconutil', '-c', 'icns', str(iconset), '-o', str(PACKAGING / 'icon.icns')], check=True)
    write_ico(PACKAGING / 'icon.ico', [win[s] for s in sorted(win)])
    print('written', PACKAGING / 'icon.icns', PACKAGING / 'icon.ico', WINDOW)


if __name__ == '__main__':
    main()
