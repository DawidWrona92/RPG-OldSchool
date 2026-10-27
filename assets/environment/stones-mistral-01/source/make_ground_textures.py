# Proceduralne tekstury podloza Weleszy (błotnisty trakt, ściółka leśna).
# Bezszwowe (tileable), generowane w numpy, bez zewnętrznych źródeł (CC0 własne).
import numpy as np
from PIL import Image
import os

rng = np.random.default_rng(20261026)


def _smooth_tileable(cells, shape, rng):
    """Smooth value-noise from a small random grid, tileable via wrapped interpolation."""
    h, w = shape
    g = rng.random((cells + 1, cells + 1))
    g[cells, :] = g[0, :]
    g[:, cells] = g[:, 0]
    ys = np.arange(h) * cells / h
    xs = np.arange(w) * cells / w
    y0 = np.floor(ys).astype(int) % cells
    x0 = np.floor(xs).astype(int) % cells
    y1 = (y0 + 1) % cells
    x1 = (x0 + 1) % cells
    ty = ys - np.floor(ys)
    tx = xs - np.floor(xs)
    sm = lambda t: t * t * (3 - 2 * t)
    ty = sm(ty)[:, None]
    tx = sm(tx)[None, :]
    g00 = g[np.ix_(y0, x0)]
    g01 = g[np.ix_(y0, x1)]
    g10 = g[np.ix_(y1, x0)]
    g11 = g[np.ix_(y1, x1)]
    top = g00 + (g10 - g00) * ty
    bot = g01 + (g11 - g01) * ty
    return top + (bot - top) * tx


def fbm2d(shape, octaves=(4, 8, 16, 32, 64), seed_off=0, weights=None):
    h, w = shape
    out = np.zeros(shape)
    if weights is None:
        weights = [1.0 / (2 ** i) for i in range(len(octaves))]
    for i, cells in enumerate(octaves):
        r = np.random.default_rng(1000 + seed_off + i)
        out += weights[i] * _smooth_tileable(cells, (h, w), r)
    out -= out.min()
    out /= out.ptp() + 1e-9
    return out


def tileable_fbm(shape, octaves, seed):
    return fbm2d(shape, octaves, seed)


def scattered_dots(shape, n, rmin, rmax, colors, seed, softness=1.5):
    """Random soft ellipses, wrap-around (tileable)."""
    h, w = shape[:2]
    r = np.random.default_rng(seed)
    img = np.zeros(shape, dtype=np.float64)
    for _ in range(n):
        cy = int(r.integers(0, h))
        cx = int(r.integers(0, w))
        rad = r.uniform(rmin, rmax)
        ry = rad * r.uniform(0.5, 1.2)
        rx = rad * r.uniform(0.7, 1.3)
        ang = r.uniform(0, np.pi)
        col = colors[r.integers(0, len(colors))]
        col = np.atleast_1d(np.asarray(col, dtype=float).flatten()[0])
        size = int(max(ry, rx)) + 2
        yy, xx = np.mgrid[-size:size + 1, -size:size + 1]
        ca, sa = np.cos(ang), np.sin(ang)
        u = (xx * ca + yy * sa) / rx
        v = (-xx * sa + yy * ca) / ry
        d = np.sqrt(u * u + v * v)
        mask = np.clip(1 - d * softness, 0, 1)
        mask = mask * mask * (3 - 2 * mask)
        for dy in (-h, 0, h):
            for dx in (-w, 0, w):
                y0, y1 = cy + dy - size, cy + dy + size + 1
                x0, x1 = cx + dx - size, cx + dx + size + 1
                sy0, sy1 = max(0, y0), min(h, y1)
                sx0, sx1 = max(0, x0), min(w, x1)
                if sy0 >= sy1 or sx0 >= sx1:
                    continue
                m = mask[sy0 - y0: sy1 - y0, sx0 - x0: sx1 - x0]
                img[sy0:sy1, sx0:sx1] = np.maximum(img[sy0:sy1, sx0:sx1], m[..., None] * np.asarray(col))
    return np.clip(img, 0, 1)


def rough_normal_map(height, strength=2.0):
    h, w = height.shape
    dy = np.roll(height, -1, 0) - np.roll(height, 1, 0)
    dx = np.roll(height, -1, 1) - np.roll(height, 1, 1)
    n = np.stack([-dx * strength, -dy * strength, np.ones_like(height)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n * 0.5 + 0.5


def make_mud(size=1024):
    """Mokry, ubity trakt: glina z koleinami, wilgotne plamy, drobne kamyki."""
    base = tileable_fbm((size, size), (3, 6, 12, 24, 48, 96, 192), 11)
    fine = tileable_fbm((size, size), (96, 192, 384), 12)
    # kolory gleby: glina, wilgotna glina, piach
    c_dry = np.array([0.50, 0.40, 0.28])
    c_wet = np.array([0.28, 0.21, 0.15])
    c_sand = np.array([0.58, 0.49, 0.35])
    wet = tileable_fbm((size, size), (4, 8, 16), 21)
    wet = np.clip((wet - 0.42) * 2.2, 0, 1)
    img = np.zeros((size, size, 3))
    img += (1 - wet)[..., None] * (c_dry + (base - 0.5)[..., None] * 0.18)
    img += wet[..., None] * (c_wet + (base - 0.5)[..., None] * 0.10)
    sand = np.clip((base - 0.62) * 4, 0, 1)
    img = img * (1 - sand[..., None] * 0.3) + sand[..., None] * c_sand * 0.3
    # drobne kamyki (jasne szarosci wystaja z gliny)
    pebbles = scattered_dots((size, size, 1), 260, 4, 12, [[0.55], [0.68], [0.38]], 31, softness=0.6)
    peb_col = np.array([0.62, 0.58, 0.52])
    img = img * (1 - pebbles) + pebbles * peb_col
    # ziarnista struktura gliny
    img = np.clip(img + (fine - 0.5)[..., None] * 0.10, 0, 1)
    # koleiny: wydluzone ciemniejsze pasy (kierunek drogi)
    ruts = tileable_fbm((size, size), (2, 3, 6), 61)
    ruts = np.clip((ruts - 0.45) * 2.5, 0, 1)
    img = np.clip(img * (1 - ruts[..., None] * 0.25), 0, 1)
    # wilgotne plamy (blysk)
    shine = tileable_fbm((size, size), (3, 5, 9), 41)
    shine = np.clip((shine - 0.58) * 3.0, 0, 1) * wet
    # height map: ubita glina + koleiny
    height = base * 0.6 + tileable_fbm((size, size), (2, 4, 8, 16), 51) * 0.4
    height = height - pebbles[..., 0] * 0.25
    return img, height, shine


def make_litter(size=1024):
    """Lesna sciolka: ziemia, liscie, igliwie, drobne galazki, plamy mchu."""
    base = tileable_fbm((size, size), (3, 6, 12, 24, 48, 96, 192), 71)
    img = np.zeros((size, size, 3))
    c_soil = np.array([0.28, 0.20, 0.13])
    c_soil2 = np.array([0.37, 0.27, 0.18])
    img += (base[..., None]) * (c_soil2 - c_soil) + c_soil
    # liscie: wyrazne bursztynowo-brazowe owale
    leaf_cols = [[0.52, 0.32, 0.14], [0.44, 0.27, 0.12], [0.58, 0.40, 0.18], [0.38, 0.24, 0.12]]
    leaves_mask = scattered_dots((size, size, 1), 520, 7, 18, [[1.0]], 81, softness=0.7)
    leaf_pick = np.zeros((size, size, 3))
    # losowy wybor koloru liscia: uzywamy niskoczęstotliwego szumu
    pick = tileable_fbm((size, size), (7, 13), 82)
    for i, lc in enumerate(leaf_cols):
        sel = np.clip(1 - np.abs(pick - i / (len(leaf_cols) - 1)) * 4, 0, 1)
        leaf_pick += sel[..., None] * np.array(lc)
    leaf_pick = np.clip(leaf_pick, 0, 1)
    img = np.clip(img * (1 - leaves_mask) + leaves_mask * leaf_pick, 0, 1)
    # igliwie (krotkie ciemne kreski)
    needles = scattered_dots((size, size, 1), 700, 2.5, 6, [[0.15], [0.19], [0.12]], 101, softness=0.8)
    img = np.clip(img * (1 - needles * 0.6) + needles * 0.6 * np.array([0.18, 0.15, 0.10]), 0, 1)
    # mech (stonowany zielono-szary)
    moss = tileable_fbm((size, size), (5, 10, 20), 111)
    moss = np.clip((moss - 0.55) * 2.6, 0, 1)
    img = img * (1 - moss[..., None] * 0.55) + moss[..., None] * 0.55 * np.array([0.16, 0.19, 0.13])
    # height
    height = base * 0.5 + (leaves_mask[..., 0] * 0.3 + needles[..., 0] * 0.1)
    return img, height, moss


def save_all(outdir, size=1024):
    os.makedirs(outdir, exist_ok=True)
    mud, mud_h, mud_shine = make_mud(size)
    lit, lit_h, lit_moss = make_litter(size)
    for name, img in [("mud", mud), ("litter", lit)]:
        Image.fromarray((img * 255).astype(np.uint8)).save(f"{outdir}/welesza_{name}_color.png")
    Image.fromarray((mud_h * 255).astype(np.uint8)).save(f"{outdir}/welesza_mud_height.png")
    Image.fromarray((lit_h * 255).astype(np.uint8)).save(f"{outdir}/welesza_litter_height.png")
    Image.fromarray((mud_shine * 255).astype(np.uint8)).save(f"{outdir}/welesza_mud_rough_inverted.png")
    Image.fromarray((rough_normal_map(mud_h, 1.5) * 255).astype(np.uint8)).save(f"{outdir}/welesza_mud_normal.png")
    Image.fromarray((rough_normal_map(lit_h, 2.0) * 255).astype(np.uint8)).save(f"{outdir}/welesza_litter_normal.png")
    print("saved textures to", outdir)


if __name__ == "__main__":
    save_all("/workspace/envwork/textures", 1024)
