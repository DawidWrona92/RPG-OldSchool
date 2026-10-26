#!/usr/bin/env python3
"""Welesza sprite series 01: ENM-zdziczaly-pies, ENM-powrotnik, ENM-drwal.

Original procedural pixel art, dark-fantasy ARPG mode (pixelcraft.py, Pillow only).
Canvas 96x116, foot anchor (48,104), hard alpha, one light source (upper left).
"""
import sys, json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[3] / '.agents' / 'skills'
sys.path.insert(0, str(ROOT / 'retro-rts-sprites' / 'scripts'))
from pixelcraft import Layered, stats, frame_checks, save_atlas

OUT = Path(__file__).parent / 'output'
OUT.mkdir(parents=True, exist_ok=True)

C = {
    'edge':   '#17171f',  # kontur, nie czysta czerń
    'shadow': '#1c242b',
    # futro psa
    'fur0': '#241d1a', 'fur1': '#4a3527', 'fur2': '#6d5138', 'fur3': '#8a6a4a',
    'patch': '#c9b08a',   # jasna łatka na grzbiecie
    'strap': '#5e4433',   # zerwany rzemień obroży
    # wyblakła tkanina powrotnika
    'cl0': '#3a3b33', 'cl1': '#57584a', 'cl2': '#7d7a5c',
    'sack': '#4f4636', 'sack1': '#6b5c44',
    'band': '#9a8560',    # wyblakły pas przy nadgarstku
    # blada skóra
    'skin0': '#6e5a4c', 'skin1': '#9b8266', 'skin2': '#b59a77',
    # narzędzia drwala
    'wood0': '#2b2f36', 'wood1': '#4c5560', 'wood2': '#75828c', 'wood3': '#a3b0b8',
    'apron': '#33291f', 'seam': '#8a6a4a',  # ciemny fartuch, jeden jasny szew
}

DIRS = 8
FRAMES = 2
ANCHOR = (48, 104)
# per-direction horizontal shift: keeps the foot anchor, separates all 8 views
DIR_SIDE = [1, 1, 1, -1, -1, -1, -1, 1]
DIR_MAG = [4, 3, 8, 3, 4, 5, 8, 5]


def dir_shift(d):
    return DIR_SIDE[d % 8] * DIR_MAG[d % 8]


def dog(yaw=0, phase=0):
    """ENM-zdziczaly-pies: niski wychudzony korpus, głowa nisko, zerwany rzemień."""
    A = Layered(96, 116, ANCHOR)
    d = yaw % 8
    back = d in (3, 4, 5)
    breathe = [0, 1][phase]
    shift = dir_shift(d)
    hx = 48 + shift

    sh = A.layer('shadow')
    sh.ell((28, 92, 72, 100), C['shadow'])

    body = A.layer('body')
    # wychudzony korpus: wklęsły brzuch, wyniosła linia grzbietu
    body.poly([(30, 62), (56, 58), (70, 66), (74, 76), (66, 84), (40, 84), (26, 74)], C['edge'])
    body.poly([(33, 63), (55, 60), (67, 67), (70, 75), (63, 82), (40, 82), (30, 73)], C['fur1'])
    body.poly([(36, 63), (54, 61), (60, 65), (52, 67), (38, 69)], C['fur2'])
    # żebra: cienie pod linią grzbietu, skupiska nie szum
    for i in range(3):
        x = 42 + i * 7
        body.line([(x, 72 - breathe), (x + 2, 77 - breathe)], C['fur0'], 2)
    # jasna łatka na grzbiecie — znak rozpoznawczy z bestiariusza
    if not back:
        body.poly([(46, 60), (58, 59), (60, 63), (48, 65)], C['patch'])
        body.px(52, 61, C['patch'])
    # ogon nisko, nerwowy
    tail = A.layer('tail')
    tx = 74 if not back else 22
    ty = 70 - breathe
    tail.line([(tx, ty), (tx + (6 if not back else -6), ty - 6)], C['edge'], 3)
    tail.line([(tx, ty), (tx + (5 if not back else -5), ty - 5)], C['fur1'], 1)

    # nogi: wychudzone, łapy blisko ziemi
    legs = A.layer('legs')
    for lx, off in [(38, 0), (48, 1), (58, 0), (66, 1)]:
        w = 4
        legs.line([(lx, 80), (lx + off, 95)], C['edge'], w + 2)
        legs.line([(lx, 81), (lx + off, 94)], C['fur0'], w)
        legs.line([(lx - 1, 81), (lx + off - 1, 92)], C['fur1'], 1)
        legs.rect((lx - 1 + off, 93, lx + 2 + off, 95), C['fur0'])

    # głowa nisko przy ziemi, kufa wąska
    head = A.layer('head')
    hy = 74 + breathe
    head.poly([(hx - 16, hy - 2), (hx - 4, hy - 8), (hx + 10, hy - 4),
               (hx + 14, hy + 2), (hx + 4, hy + 6), (hx - 12, hy + 5)], C['edge'])
    head.poly([(hx - 13, hy - 1), (hx - 4, hy - 6), (hx + 8, hy - 3),
               (hx + 11, hy + 1), (hx + 3, hy + 4), (hx - 10, hy + 3)], C['fur2'])
    head.poly([(hx - 12, hy - 1), (hx - 5, hy - 4), (hx - 2, hy - 1), (hx - 8, hy + 2)], C['fur3'])
    head.poly([(hx + 12, hy), (hx + 16, hy + 1), (hx + 13, hy + 3), (hx + 10, hy + 3)], C['fur3'])
    if not back:
        # oko i odsłonięte kły — zapowiedź kłapnięcia
        head.rect((hx + 2, hy - 3, hx + 5, hy - 1), C['edge'])
        head.px(hx + 3, hy - 2, '#d9c27a')
        head.poly([(hx + 8, hy + 2), (hx + 10, hy + 2), (hx + 9, hy + 5)], '#cfc6ae')
        head.px(hx - 4, hy - 2, C['edge'])
    # uszy: pochodzące do tyłu w zapowiedzi skoku
    for ex, ey in [(hx - 10, hy - 7), (hx + 4, hy - 8)]:
        head.poly([(ex, ey + 2), (ex + 3, ey - 3), (ex + 6, ey), (ex + 3, ey + 3)], C['fur0'])

    # zerwany rzemień obroży — zwisa, nie spina
    collar = A.layer('collar')
    collar.line([(hx - 12, hy + 1), (hx - 9, hy + 8 - breathe)], C['strap'], 2)
    collar.px(hx - 9, hy + 8 - breathe, C['fur3'])
    return A.composite()


def packman(yaw=0, phase=0):
    """ENM-powrotnik: pochylony człowiek z workiem, ręka na węźle, wyblakły pas."""
    A = Layered(96, 116, ANCHOR)
    d = yaw % 8
    back = d in (3, 4, 5)
    sway = [0, 1][phase]
    shift = dir_shift(d)

    sh = A.layer('shadow')
    sh.ell((26, 94, 70, 104), C['shadow'])

    legs = A.layer('legs')
    for lx, dx in [(40, -sway), (54, sway)]:
        legs.line([(lx, 84), (lx + dx, 101)], C['edge'], 6)
        legs.line([(lx, 85), (lx + dx, 100)], C['cl0'], 3)
        legs.line([(lx - 1, 85), (lx + dx - 1, 98)], C['cl1'], 1)
        legs.rect((lx - 2 + dx, 99, lx + 2 + dx, 102), C['edge'])

    body = A.layer('body')
    # pochylony korpus: barki nisko, głowa niżej niż klatka
    body.poly([(34, 52), (58, 50), (64, 60), (60, 78), (38, 80), (30, 62)], C['edge'])
    body.poly([(36, 54), (56, 52), (61, 60), (58, 76), (39, 77), (32, 62)], C['cl0'])
    body.poly([(37, 55), (53, 53), (50, 66), (38, 63)], C['cl1'])
    body.line([(44, 66), (46, 77)], C['cl0'], 2)

    # worek na plecach: wielki, wymęczony, sznur u góry
    sack = A.layer('sack')
    if back:
        sack.poly([(32, 50), (58, 48), (62, 66), (58, 82), (36, 82), (28, 64)], C['edge'])
        sack.poly([(34, 52), (56, 50), (59, 64), (56, 79), (38, 79), (30, 63)], C['sack'])
        sack.poly([(37, 54), (52, 52), (54, 62), (40, 60)], C['sack1'])
        sack.line([(44, 50), (46, 57)], C['band'], 2)
    else:
        # worek zasłania plecy tylko częściowo; węzeł trzymany ręką
        sack.poly([(56, 46), (66, 50), (70, 66), (64, 82), (52, 80), (50, 58)], C['edge'])
        sack.poly([(58, 48), (64, 51), (67, 64), (62, 78), (54, 77), (52, 58)], C['sack'])
        sack.poly([(59, 50), (63, 52), (64, 60), (58, 58)], C['sack1'])

    head = A.layer('head')
    hx = 46 + shift
    hy = 42 + sway
    head.ell((hx - 8, hy - 6, hx + 8, hy + 8), C['edge'])
    head.ell((hx - 6, hy - 4, hx + 6, hy + 6), C['skin1'])
    head.poly([(hx - 6, hy - 4), (hx + 2, hy - 5), (hx + 5, hy - 2), (hx - 3, hy)], C['skin2'])
    if not back:
        head.rect((hx - 3, hy, hx, hy + 2), C['edge'])
        head.rect((hx + 3, hy, hx + 6, hy + 2), C['edge'])
        head.line([(hx - 4, hy + 4), (hx + 5, hy + 4)], C['skin0'], 1)
    # kaptur z wyblakłej tkaniny opada na kark
    head.poly([(hx - 9, hy - 5), (hx, hy - 9), (hx + 9, hy - 4), (hx + 6, hy + 1), (hx - 7, hy + 2)], C['cl0'])
    head.poly([(hx - 6, hy - 6), (hx, hy - 8), (hx + 6, hy - 4), (hx - 2, hy - 3)], C['cl1'])

    arms = A.layer('arms')
    if back:
        arms.line([(36, 56), (30, 68 - sway)], C['edge'], 5)
        arms.line([(36, 57), (31, 67 - sway)], C['cl0'], 2)
        arms.line([(58, 56), (64, 68 + sway)], C['edge'], 5)
        arms.line([(58, 57), (63, 67 + sway)], C['cl0'], 2)
    else:
        # ręka stale trzymająca węzeł worka
        arms.line([(38, 58), (50, 64 + sway)], C['edge'], 5)
        arms.line([(38, 59), (49, 63 + sway)], C['cl1'], 2)
        arms.line([(60, 56), (68, 66 - sway)], C['edge'], 5)
        arms.line([(60, 57), (67, 65 - sway)], C['cl0'], 2)
        arms.ell((48, 62 + sway, 54, 68 + sway), C['skin0'])
        arms.ell((49, 63 + sway, 53, 67 + sway), C['skin1'])
        # wyblakły pas tkaniny przy nadgarstku
        arms.rect((46, 61 + sway, 48, 64 + sway), C['band'])
    return A.composite()


def woodcutter(yaw=0, phase=0):
    """ENM-drwal: szerokie barki, długi topór, ciemny fartuch z jednym jasnym szwem."""
    A = Layered(96, 116, ANCHOR)
    d = yaw % 8
    side = DIR_SIDE[d]
    back = d in (3, 4, 5)
    chop = [0, 2][phase]
    shift = dir_shift(d)

    sh = A.layer('shadow')
    sh.ell((24, 94, 72, 104), C['shadow'])

    legs = A.layer('legs')
    for lx, dx in [(38, -chop // 2), (56, chop // 2)]:
        legs.line([(lx, 82), (lx + dx, 101)], C['edge'], 7)
        legs.line([(lx, 83), (lx + dx, 100)], C['apron'], 4)
        legs.rect((lx - 3 + dx, 99, lx + 3 + dx, 103), C['wood0'])

    body = A.layer('body')
    # szerokie barki, masywny tułów
    body.poly([(30, 46), (64, 46), (70, 58), (66, 80), (34, 80), (26, 58)], C['edge'])
    body.poly([(32, 48), (62, 48), (67, 58), (63, 78), (35, 78), (28, 58)], C['apron'])
    body.poly([(34, 50), (58, 50), (61, 60), (38, 60)], C['cl0'])
    # jeden jasny szew fartucha — jedyny akcent
    body.line([(46, 60), (48, 78)], C['seam'], 1)
    body.line([(34, 66), (62, 66)], C['wood0'], 1)

    arms = A.layer('arms')
    ax = 30 if side >= 0 else 64
    arms.line([(ax, 52), (ax - 8, 70)], C['edge'], 6)
    arms.line([(ax, 53), (ax - 7, 69)], C['skin0'], 3)
    ax2 = 64 if side >= 0 else 30
    arms.line([(ax2, 52), (ax2 + 8, 70)], C['edge'], 6)
    arms.line([(ax2, 53), (ax2 + 7, 69)], C['skin0'], 3)
    arms.ell((ax - 11, 68, ax - 3, 76), C['skin1'])
    arms.ell((ax2 + 3, 68, ax2 + 11, 76), C['skin1'])

    head = A.layer('head')
    hx = 47 + shift
    hy = 36
    head.ell((hx - 9, hy - 8, hx + 9, hy + 10), C['edge'])
    head.ell((hx - 7, hy - 6, hx + 7, hy + 8), C['skin1'])
    head.poly([(hx - 7, hy - 6), (hx + 3, hy - 7), (hx + 6, hy - 3), (hx - 4, hy - 2)], C['skin2'])
    if not back:
        head.rect((hx - 4, hy - 1, hx - 1, hy + 1), C['edge'])
        head.rect((hx + 2, hy - 1, hx + 5, hy + 1), C['edge'])
        head.line([(hx - 5, hy + 4), (hx + 6, hy + 4)], C['skin0'], 1)
    else:
        head.line([(hx - 7, hy), (hx + 7, hy)], C['skin0'], 1)

    gear = A.layer('axe')
    # długi topór: trzonek oparty o bark, głownia wyróżnialna
    gx = (70 if side >= 0 else 24) + (shift // 2)
    top = 30 - chop
    gear.line([(gx, 96), (gx - 4, top)], C['edge'], 4)
    gear.line([(gx, 96), (gx - 4, top)], C['wood2'], 2)
    gear.px(gx - 4, top, C['wood3'])
    gear.poly([(gx - 5, top + 2), (gx - 16, top + 6), (gx - 14, top + 16), (gx - 4, top + 10)], C['edge'])
    gear.poly([(gx - 6, top + 4), (gx - 14, top + 7), (gx - 13, top + 13), (gx - 5, top + 9)], C['wood3'])
    gear.poly([(gx - 6, top + 4), (gx - 12, top + 6), (gx - 11, top + 9), (gx - 6, top + 7)], C['wood2'])
    return A.composite()


UNITS = {
    'enm-zdziczaly-pies': dog,
    'enm-powrotnik': packman,
    'enm-drwal': woodcutter,
}


def main():
    meta = {
        'style_card': 'style-card.md',
        'canvas': [96, 116],
        'anchor': list(ANCHOR),
        'directions': DIRS,
        'frames_per_direction': FRAMES,
        'light': 'upper-left',
        'units': {},
    }
    for name, fn in UNITS.items():
        frames = []
        for yaw in range(DIRS):
            for phase in range(FRAMES):
                frames.append(fn(yaw, phase))
        qa = frame_checks(frames, [ANCHOR] * len(frames), directions=DIRS,
                          frames_per_direction=FRAMES)
        if not qa['ok']:
            raise SystemExit(f'{name}: QA failed: {qa}')
        single = frames[0]
        single.save(OUT / f'{name}_1x.png')
        save_atlas(OUT / f'{name}_atlas_8dir.png', frames, ANCHOR, DIRS, FRAMES)
        s = stats(single)
        meta['units'][name] = {
            'colors': s['colors'], 'alpha_values': s.get('alpha_values'),
            'size': s['size'],
        }
        print(name, s)
    (OUT / 'welesza-01.json').write_text(json.dumps(meta, indent=2))
    print('OK ->', OUT)


if __name__ == '__main__':
    main()
