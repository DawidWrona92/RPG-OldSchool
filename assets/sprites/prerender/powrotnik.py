"""ENM-powrotnik: pochylony wedrowiec z workiem na plecach, dawna ofiara traktu. Szkielet z IK, 6 animacji, 3 warianty.

Wybor wykonawczy do potwierdzenia przez autora: karta nie rozstrzyga, czy to czlowiek, duch czy obraz; rysuje go jako
wyczerpanego czlowieka o woskowej, popielatej skorze (jak Drwala), bez wyjasnien i bez makabry. Oczy: tylko metny blask.
Karta (docs/bestiariusz-demo.md): pochylony czlowiek z workiem na plecach; reka stale trzymajaca wezel; wyblakly pas tkaniny
przy nadgarstku. Ataki, oba nieparowalne: oburecz chwyt (odklada worek, prostuje ramiona, nabiera powietrza; krotki frontalny)
i uderzenie tobolem (worek nad bark, szeroki bliski zamach). Slabosc: wolne odzyskiwanie pozycji.
Sygnal nieparowalnego ataku (czerwone zarzewie): wezel na worku i pas na nadgarstku, tylko w klatkach zapowiedzi/ataku.

Uzycie:
  python3 powrotnik.py anim [nazwa|all] [--wariant=b|c] [--szkic]   atlas PNG + JSON + GIF w output/powrotnik[-b|-c]/
  python3 powrotnik.py <poza|all> [kierunek 0-7|all] [--wariant=b]  pojedyncze pozy z POSES
Flaga --bez-sygnalu wylacza czerwone zarzewie.
Szkielet, IK i pozy jak w drwal.py (kopia wzorca); worek ma wlasna kosc i moze byc odlozony na ziemie albo zamachniety.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sdfkit import Isect, Model, Prim, Sub, Xf, normalize, rotation, run_anim, run_cli, value_noise  # noqa: E402

(SKIN, LINEN, COAT, TROUSERS, WRAPS, BAST, LEATHER, SACK, ROPE, KNOT, KNOT_HOT, BAND, BAND_HOT, HAIR, EYES, SOCKET, TEETH,
 HOOD, FELT, ITEM) = range(20)

MATERIALS = {
    SKIN: dict(alb=(0.13, 0.135, 0.115), spec=0.28, pw=18, grit=0.7),         # popielata, woskowa skora
    LINEN: dict(alb=(0.115, 0.104, 0.082), spec=0.05, pw=6, grit=0.9),         # brudna plocienna koszula
    COAT: dict(alb=(0.074, 0.058, 0.043), spec=0.3, pw=14, grit=0.8),          # mokry, ciezki kaftan z welny
    TROUSERS: dict(alb=(0.062, 0.054, 0.046), spec=0.05, pw=6, grit=0.9),      # ciemna welna
    WRAPS: dict(alb=(0.12, 0.11, 0.09), spec=0.04, pw=4, grit=1.0),           # onuce
    BAST: dict(alb=(0.11, 0.085, 0.05), spec=0.05, pw=4, grit=1.2),           # lapcie z lyka
    LEATHER: dict(alb=(0.08, 0.05, 0.03), spec=0.2, pw=12, grit=0.6),         # pas, rzemienie
    SACK: dict(alb=(0.13, 0.105, 0.07), spec=0.04, pw=4, grit=1.3),           # worek z grubego plotna
    ROPE: dict(alb=(0.14, 0.11, 0.07), spec=0.05, pw=4, grit=1.0),            # sznur worka
    KNOT: dict(alb=(0.15, 0.12, 0.08), spec=0.05, pw=4, grit=0.9),            # wezel trzymany w dloni
    KNOT_HOT: dict(alb=(0.15, 0.12, 0.08), spec=0.05, pw=4, grit=0.9),        # wezel z sygnalem ataku nieparowalnego
    BAND: dict(alb=(0.32, 0.29, 0.22), spec=0.04, pw=4, grit=0.6),            # wyblakly pas tkaniny przy nadgarstku
    BAND_HOT: dict(alb=(0.32, 0.29, 0.22), spec=0.04, pw=4, grit=0.6),        # pas z sygnalem ataku nieparowalnego
    HAIR: dict(alb=(0.04, 0.037, 0.033), spec=0.18, pw=10, grit=0.8),         # zlepione wlosy
    EYES: dict(alb=(0.0, 0.0, 0.0), spec=0.0, pw=1, grit=0.0, emit=(0.5, 0.6, 0.5)),   # metny blask
    SOCKET: dict(alb=(0.008, 0.008, 0.008), spec=0.0, pw=1, grit=0.0),
    TEETH: dict(alb=(0.2, 0.17, 0.12), spec=0.2, pw=12, grit=0.6),
    HOOD: dict(alb=(0.075, 0.072, 0.064), spec=0.04, pw=4, grit=1.0),         # welniany kaptur
    FELT: dict(alb=(0.1, 0.08, 0.058), spec=0.04, pw=4, grit=0.9),          # filcowa czapka ludowa
    ITEM: dict(alb=(0.1, 0.09, 0.08), spec=0.5, pw=20, grit=0.5),             # przedmiot wystajacy z worka (rondel)
}

MOSS = np.array([0.034, 0.05, 0.022])

# ---------- warianty ----------
# Sylwetka z karty zostaje w kazdym: pochylony, worek na prawym ramieniu, reka na wezle, wyblakly pas na nadgarstku.
# sack: wielkosc worka; head: nakrycie glowy; coat: dlugosc kaftana; tint: mnoznik albedo materialu.
VARIANTS = {
    "a": dict(scale=1.0, girth=1.0, hunch=0.0, sack=1.0, head="czapka", coat=1.0, item=False, tint={}, moss=0.55),
    "b": dict(scale=0.95, girth=1.12, hunch=5.0, sack=1.2, head="kaptur", coat=0.85, item=False,
              tint={COAT: (1.15, 1.0, 0.8), SKIN: (0.95, 1.05, 0.9)}, moss=0.5),
    "c": dict(scale=1.05, girth=0.9, hunch=3.0, sack=0.85, head="goly", coat=1.1, item=True,
              tint={COAT: (0.85, 0.95, 1.2), LINEN: (0.9, 0.95, 1.15)}, moss=0.6),
}


def variant_of(flags):
    for flag in flags:
        if flag.startswith("wariant="):
            return flag.split("=", 1)[1]
    return "a"


# ---------- szkielet w pozycji spoczynkowej (wspolrzedne swiata, metry) ----------
REST_PELVIS = np.array([0.0, 0.0, 0.97])
NECK_BASE = np.array([0.06, 0.0, 1.5])
HIP = {1: np.array([0.0, 0.11, 0.95]), -1: np.array([0.0, -0.11, 0.95])}
KNEE = {1: np.array([0.02, 0.13, 0.53]), -1: np.array([0.02, -0.13, 0.53])}
ANKLE = {1: np.array([0.0, 0.14, 0.1]), -1: np.array([0.0, -0.14, 0.1])}
SHOULDER = {1: np.array([0.0, 0.29, 1.5]), -1: np.array([0.0, -0.29, 1.5])}
ELBOW = {1: np.array([0.0, 0.33, 1.2]), -1: np.array([0.0, -0.33, 1.2])}
WRIST = {1: np.array([0.03, 0.35, 0.84]), -1: np.array([0.03, -0.35, 0.84])}

# ---------- pozy ----------
# Cele, nie katy stawow. Cel dloni / worka: ("t", (x, y, z)) = we wspolrzednych tulowia (podaza za nim), albo zwykla krotka = swiat.
BASE = dict(
    pelvis=(0.0, 0.0, 0.9),
    spine=(0.0, 24.0, 0.0),       # yaw, pitch, roll [stopnie] wokol miednicy
    hips=None,
    head=(0.0, 8.0),              # yaw, pitch glowy
    footL=(0.08, 0.16, 0.1), footR=(-0.1, -0.16, 0.1),
    footRotL=(6.0, 0.0), footRotR=(-6.0, 0.0),
    handR=("t", (0.17, -0.2, 1.2)),   # reka stale trzymajaca wezel
    handL=("t", (0.1, 0.34, 0.8)),    # druga reka zwisa
    poleR=(-0.5, -1.0, -0.3), poleL=(-0.4, 1.0, -0.2),
    fingersR=(0.1, 0.9), fingersL=(0.25, 0.45),   # rozwarcie, zgiecie palcow
    neck=("t", (-0.16, -0.3, 1.52)),   # szyja worka (przy ramieniu)
    dir=("t", (-0.5, -0.14, -0.85)),   # os worka od szyi w dol
    via=("t", (0.0, -0.28, 1.62)),     # sznur przechodzi przez ramie (None = prosty)
    hot=False,
    hold=True,                    # prawa reka trzyma wezel (sznur do dloni); False = worek lezy / spada
)


def pose(**changes):
    result = dict(BASE)
    result.update(changes)
    return result


def _vec(spec, upper, point):
    if isinstance(spec, tuple) and len(spec) == 2 and spec[0] == "t":
        v = np.array(spec[1], float)
        return upper.apply(v) if point else upper.R @ v
    return None if spec is None else np.array(spec, float)


def mix(a, b, t):
    """Interpolacja dwoch poz; cele we wspolrzednych tulowia i swiata mozna mieszac, gdy maja ten sam uklad."""
    result = {}
    for key in a:
        va, vb = a[key], b[key]
        if va is None or vb is None or isinstance(va, (bool, str)):
            result[key] = va if t < 0.5 else vb
        elif isinstance(va, (int, float)):
            result[key] = va + (vb - va) * t
        elif isinstance(va, tuple) and len(va) == 2 and va[0] == "t" or isinstance(vb, tuple) and len(vb) == 2 and vb[0] == "t":
            if isinstance(va, tuple) and va[0] == "t" and isinstance(vb, tuple) and vb[0] == "t":
                result[key] = ("t", tuple(x + (y - x) * t for x, y in zip(va[1], vb[1])))
            else:
                result[key] = va if t < 0.5 else vb
        else:
            result[key] = tuple(x + (y - x) * t for x, y in zip(va, vb))
    return result


def ik(start, target, len1, len2, pole):
    delta = target - start
    dist = np.linalg.norm(delta)
    if dist > len1 + len2 + 0.02:
        print(f"  uwaga: cel poza zasiegiem o {dist - len1 - len2:.3f} m", file=sys.stderr)
    reach = np.clip(dist, abs(len1 - len2) + 1e-3, len1 + len2 - 1e-3)
    axis = delta / max(dist, 1e-9)
    along = (len1 ** 2 - len2 ** 2 + reach ** 2) / (2 * reach)
    side = math.sqrt(max(len1 ** 2 - along ** 2, 0.0))
    bend = np.asarray(pole, float) - axis * np.dot(pole, axis)
    bend = bend / (np.linalg.norm(bend) + 1e-9)
    return start + axis * along + bend * side, start + axis * reach


def rotate_onto(src, dst):
    a, b = normalize(src), normalize(dst)
    v, c = np.cross(a, b), float(np.dot(a, b))
    if c < -0.9999:
        perp = normalize(np.cross(a, [1.0, 0, 0]) if abs(a[0]) < 0.9 else np.cross(a, [0, 1.0, 0]))
        return 2 * np.outer(perp, perp) - np.eye(3)
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx / (1 + c)


def bone(restA, restB, a, b):
    return Xf(rotate_onto(restB - restA, b - a), restA, a - restA)


def frame_x(direction, ref=(1.0, 0.0, 0.0)):
    """Uklad prawoskretny: x = kierunek, z = ref zrzutowany prostopadle, y = z x x."""
    x = normalize(direction)
    ref = np.array(ref, float)
    if abs(np.dot(normalize(ref), x)) > 0.95:
        ref = np.array([0.0, 0.0, 1.0])
    z = normalize(ref - x * np.dot(ref, x))
    return np.stack([x, np.cross(z, x), z], axis=1)


# ---------- model ----------

def build(p, flags=()):
    v = VARIANTS[variant_of(flags)]
    g = v["girth"]
    model = Model(clip_ground=True, scale=v["scale"])
    pelvis = np.array(p["pelvis"], float)
    yaw, pitch, roll = p["spine"]
    pitch += v["hunch"]
    upper = Xf(rotation(yaw, pitch, roll), REST_PELVIS, pelvis - REST_PELVIS)
    hips = p["hips"] if p["hips"] is not None else (yaw * 0.4, pitch * 0.25, roll * 0.4)
    lower = Xf(rotation(*hips), REST_PELVIS, pelvis - REST_PELVIS)
    headXf = Xf(rotation(p["head"][0], p["head"][1] - v["hunch"] * 0.5, 0.0), NECK_BASE).then(upper)
    hot = bool(p["hot"])

    # ---------- tulow: waskie, opadajace barki, zapadniety brzuch ----------
    torso = [Prim("ellipsoid", LINEN, c=[0.0, 0, 1.06], radii=[0.1 * g, 0.15 * g, 0.13]),
             Prim("ellipsoid", LINEN, c=[0.02, 0, 1.31], radii=[0.13 * g, 0.22 * g, 0.17]),
             Prim("ellipsoid", LINEN, c=[0.0, 0, 1.46], radii=[0.11, 0.29, 0.08])]
    torso += [Prim("ellipsoid", LINEN, c=SHOULDER[s] + [0, 0, 0.02], radii=[0.075, 0.075, 0.07]) for s in (1, -1)]
    model.group(0.06, torso, disp=(0.004, 20), xf=upper)
    model.group(0.03, [Prim("cone", SKIN, a=[0.02, 0, 1.47], b=[0.11, 0, 1.6], r1=0.055, r2=0.042)], disp=(0.003, 40), xf=upper)

    # kaftan: powloka wokol tulowia i bioder, rozciety z przodu, postrzepiony dol
    hemTop = 1.5
    coatLen = v["coat"]
    hem = 1.0 - 0.52 * coatLen
    coatUp = Sub(Isect([Prim("ellipsoid", COAT, c=[0.0, 0, 1.12], radii=[0.19 * g, 0.25 * g, 0.42]),
                        Prim("box", COAT, c=[0, 0, 1.25], R=np.eye(3), half=[0.5, 0.5, 0.26])]),
                 [Prim("ellipsoid", COAT, c=[0.0, 0, 1.12], radii=[0.17 * g, 0.23 * g, 0.4]),
                  Prim("box", COAT, c=[0.22, 0, 1.12], R=np.eye(3), half=[0.08, 0.045, 0.5])])
    model.group(0.02, [coatUp], disp=(0.005, 22), xf=upper)
    skirtC = np.array([0.0, 0, 0.78])
    skirt = Sub(Isect([Prim("ellipsoid", COAT, c=skirtC, radii=[0.2 * g, 0.25 * g, 0.5]),
                       Prim("box", COAT, c=[0, 0, (1.02 + hem) / 2], R=np.eye(3), half=[0.5, 0.5, (1.02 - hem) / 2])]),
                [Prim("ellipsoid", COAT, c=skirtC, radii=[0.18 * g, 0.23 * g, 0.48]),
                 Prim("box", COAT, c=[0.22, 0, 0.8], R=np.eye(3), half=[0.08, 0.05, 0.5])] +
                [Prim("sphere", COAT, c=[0.1, y * g, hem], r=r) for y, r in ((-0.2, 0.05), (-0.05, 0.04), (0.1, 0.06), (0.22, 0.045))])
    model.group(0.02, [skirt], disp=(0.006, 20), xf=lower)
    model.group(0.0, [Prim("cylinder", LEATHER, c=[0, 0, 1.0], R=np.eye(3), r=0.17 * g, h=0.025)], xf=lower)
    model.group(0.03, [Prim("cone", TROUSERS, a=[0, 0, 1.0], b=[0, 0, 0.82], r1=0.14 * g, r2=0.16 * g)], disp=(0.004, 20), xf=lower)

    # ---------- nogi ----------
    for side, footKey, rotKey in ((1, "footL", "footRotL"), (-1, "footR", "footRotR")):
        hip = lower.apply(HIP[side])
        knee, ankle = ik(hip, np.array(p[footKey], float), np.linalg.norm(KNEE[side] - HIP[side]),
                         np.linalg.norm(ANKLE[side] - KNEE[side]), lower.R @ np.array([1.0, side * 0.15, 0.0]))
        model.group(0.03, [Prim("cone", TROUSERS, a=HIP[side], b=KNEE[side], r1=0.08, r2=0.06),
                           Prim("sphere", TROUSERS, c=KNEE[side], r=0.062)], disp=(0.006, 24), xf=bone(HIP[side], KNEE[side], hip, knee))
        shinXf = bone(KNEE[side], ANKLE[side], knee, ankle)
        model.group(0.02, [Prim("cone", WRAPS, a=KNEE[side], b=ANKLE[side], r1=0.058, r2=0.05)], disp=(0.006, 34), xf=shinXf)
        legDir = normalize(ANKLE[side] - KNEE[side])
        ringR = np.stack([normalize(np.cross(legDir, [0, 1, 0])), [0, 1, 0], legDir], axis=1)
        rings = [Prim("torus", LEATHER, c=KNEE[side] + (ANKLE[side] - KNEE[side]) * t, R=ringR, major=0.056 - 0.008 * t, minor=0.008) for t in (0.3, 0.6)]
        model.group(0.0, rings, xf=shinXf)
        footXf = Xf(rotation(*p[rotKey], 0.0), ANKLE[side], ankle - ANKLE[side])
        a = ANKLE[side]
        model.group(0.03, [Prim("box", BAST, c=[a[0] + 0.06, a[1], 0.045], R=np.eye(3), half=[0.09, 0.04, 0.028], round=0.022),
                           Prim("cone", BAST, a=[a[0], a[1], 0.06], b=a, r1=0.056, r2=0.05)], disp=(0.006, 30), xf=footXf)

    # ---------- rece: IK do celow; prawa trzyma wezel, lewa zwisa z blednym pasem na nadgarstku ----------
    targets = {-1: _vec(p["handR"], upper, True), 1: _vec(p["handL"], upper, True)}
    poles = {-1: p["poleR"], 1: p["poleL"]}
    fingers = {-1: p["fingersR"], 1: p["fingersL"]}
    handPos = {}
    for side in (-1, 1):
        shoulder = upper.apply(SHOULDER[side])
        elbow, wrist = ik(shoulder, targets[side], np.linalg.norm(ELBOW[side] - SHOULDER[side]),
                          np.linalg.norm(WRIST[side] - ELBOW[side]), upper.R @ np.array(poles[side], float))
        s0, e0, w0 = SHOULDER[side], ELBOW[side], WRIST[side]
        handPos[side] = wrist
        upperArm = bone(s0, e0, shoulder, elbow)
        sleeve = Sub(Prim("cone", LINEN, a=s0, b=e0 + (e0 - s0) * 0.1, r1=0.066, r2=0.056),
                     [Prim("sphere", LINEN, c=e0 + (e0 - s0) * 0.2 + np.array([0.03, 0.0, 0.0]), r=0.05)])
        model.group(0.04, [sleeve], disp=(0.006, 24), xf=upperArm)
        forearmXf = bone(e0, w0, elbow, wrist)
        f0 = normalize(w0 - e0)
        lat = normalize(np.cross(f0, [1.0, 0, 0]))
        palm = normalize(np.cross(lat, f0))
        spread, curl = fingers[side]
        digits = []
        for i in range(4):
            l = (i - 1.5)
            base = w0 + f0 * 0.03 + lat * l * 0.016
            tip = base + f0 * 0.075 + lat * l * 0.02 * (1 + 2.0 * spread) + palm * curl * 0.045 - f0 * curl * 0.02
            digits.append(Prim("cone", SKIN, a=base, b=tip, r1=0.0115, r2=0.008))
        model.group(0.02, [Prim("cone", SKIN, a=e0, b=w0 - f0 * 0.04, r1=0.044, r2=0.03), Prim("sphere", SKIN, c=e0, r=0.043),
                           Prim("ellipsoid", SKIN, c=w0 + f0 * 0.02, radii=[0.05, 0.042, 0.05])] + digits, disp=(0.003, 40), xf=forearmXf)
        if side == 1:
            # wyblakly pas tkaniny przy nadgarstku (wolna reka): opaska i luzny koniec
            bandMat = BAND_HOT if hot else BAND
            ringR = np.stack([lat, palm, f0], axis=1)
            model.group(0.0, [Prim("torus", bandMat, c=w0 - f0 * 0.035, R=ringR, major=0.046, minor=0.02),
                              Prim("cone", bandMat, a=w0 - f0 * 0.03 + palm * 0.03, b=w0 + f0 * 0.1 + palm * 0.045, r1=0.014, r2=0.008)],
                        xf=forearmXf)

    # ---------- worek: wlasna kosc; szyja z wezlem, sznur przez ramie do wezla w dloni ----------
    neck = _vec(p["neck"], upper, True)
    sackDir = normalize(_vec(p["dir"], upper, False))
    sackXf = Xf(frame_x(sackDir), (0, 0, 0), neck)
    sz = v["sack"]
    body = [Prim("ellipsoid", SACK, c=[0.42 * sz, 0, 0], radii=[0.3 * sz, 0.19 * sz, 0.2 * sz]),
            Prim("ellipsoid", SACK, c=[0.3 * sz, 0.02, 0.03], radii=[0.18 * sz, 0.16 * sz, 0.17 * sz]),
            Prim("cone", SACK, a=[0.0, 0, 0], b=[0.2, 0, 0], r1=0.035, r2=0.1 * sz)]
    lumps = [Prim("sphere", SACK, c=[0.5 * sz, 0.13 * sz, 0.07 * sz], r=0.09 * sz), Prim("sphere", SACK, c=[0.38 * sz, -0.12 * sz, -0.1 * sz], r=0.08 * sz),
             Prim("box", SACK, c=[0.52 * sz, -0.02, -0.12 * sz], R=np.eye(3), half=[0.07 * sz, 0.06 * sz, 0.05 * sz], round=0.03)]
    model.group(0.07, body + lumps, disp=(0.008, 22), xf=sackXf)
    swapAxis = np.array([[0, 0, 1.0], [0, 1.0, 0], [1.0, 0, 0]])
    model.group(0.0, [Prim("torus", ROPE, c=[0.16, 0, 0], R=swapAxis, major=0.06, minor=0.014)], xf=sackXf)
    if v["item"]:
        # rondel wystajacy z worka (cecha wariantu)
        model.group(0.0, [Prim("cone", ITEM, a=[0.6 * sz, 0.05, 0.1], b=[0.85 * sz, 0.12, 0.28], r1=0.014, r2=0.012),
                          Prim("torus", ITEM, c=[0.9 * sz, 0.13, 0.3], R=np.eye(3), major=0.05, minor=0.012)], xf=sackXf)
    # sznur od szyi worka do wezla w prawej dloni (przez ramie, gdy podano `via`)
    via = _vec(p["via"], upper, True)
    knotPos = handPos[-1]
    if p["hold"]:
        route = [neck] + ([via] if via is not None else []) + [knotPos]
        model.group(0.0, [Prim("cone", ROPE, a=route[i], b=route[i + 1], r1=0.02, r2=0.02) for i in range(len(route) - 1)])
        model.group(0.02, [Prim("sphere", KNOT_HOT if hot else KNOT, c=knotPos + np.array([0.0, 0.0, 0.015]), r=0.052)], disp=(0.004, 40))
    model.group(0.02, [Prim("sphere", KNOT_HOT if hot else KNOT, c=neck, r=0.05)], disp=(0.004, 40))

    # ---------- glowa ----------
    hc = np.array([0.14, 0.0, 1.7])
    sockets = [Prim("sphere", SKIN, c=hc + [0.098, s * 0.036, 0.0], r=0.027) for s in (1, -1)]
    cheeks = [Prim("sphere", SKIN, c=hc + [0.07, s * 0.08, -0.05], r=0.03) for s in (1, -1)]
    mouth = Prim("ellipsoid", SKIN, c=hc + [0.1, 0, -0.098], radii=[0.04, 0.035, 0.016])
    skull = Sub(Prim("sphere", SKIN, c=hc, r=0.092), sockets + cheeks + [mouth], smooth=0.012)
    face = Sub(Prim("ellipsoid", SKIN, c=hc + [0.045, 0, -0.055], radii=[0.065, 0.068, 0.06]), sockets + cheeks + [mouth], smooth=0.012)
    jaw = Prim("ellipsoid", SKIN, c=hc + [0.06, 0, -0.13], radii=[0.05, 0.055, 0.03])      # opadnieta szczeka
    nose = Prim("cone", SKIN, a=hc + [0.1, 0, -0.01], b=hc + [0.125, 0, -0.045], r1=0.014, r2=0.01)
    model.group(0.015, [skull, face, jaw, nose], disp=(0.0015, 40), xf=headXf)
    model.group(0.0, [Prim("sphere", SOCKET, c=hc + [0.084, s * 0.036, 0.0], r=0.016) for s in (1, -1)], xf=headXf)
    model.group(0.0, [Prim("sphere", EYES, c=hc + [0.094, s * 0.036, -0.002], r=0.0075) for s in (1, -1)], xf=headXf)
    model.group(0.0, [Prim("box", TEETH, c=hc + [0.098, 0, -0.092], R=np.eye(3), half=[0.008, 0.026, 0.008], round=0.003)], xf=headXf)
    faceCut = Prim("ellipsoid", HAIR, c=hc + [0.1, 0, -0.03], radii=[0.08, 0.075, 0.11])
    if v["head"] == "czapka":
        # ludowa filcowa czapka: sciety stozek z miekkim czubkiem lekko do tylu, podwiniety rulon u nasady (bez ronda), jak sredniowieczna czapka chlopska
        cap = [Prim("cone", FELT, a=hc + [-0.01, 0, 0.05], b=hc + [-0.06, 0, 0.17], r1=0.105, r2=0.06),
               Prim("ellipsoid", FELT, c=hc + [-0.01, 0, 0.06], radii=[0.108, 0.104, 0.08]),
               Prim("sphere", FELT, c=hc + [-0.065, 0, 0.175], r=0.062)]
        model.group(0.04, cap, disp=(0.006, 26), xf=headXf)
        model.group(0.0, [Prim("torus", FELT, c=hc + [0.0, 0, 0.03], R=np.eye(3), major=0.105, minor=0.024)], disp=(0.006, 34), xf=headXf)
        model.group(0.02, [Sub(Prim("ellipsoid", HAIR, c=hc + [-0.06, 0, -0.06], radii=[0.07, 0.1, 0.11]), [faceCut])], disp=(0.012, 38), xf=headXf)
    elif v["head"] == "kaptur":
        hoodC = hc + [-0.01, 0, 0.0]
        hood = Sub(Prim("ellipsoid", HOOD, c=hoodC, radii=[0.13, 0.12, 0.13]),
                   [Prim("ellipsoid", HOOD, c=hoodC, radii=[0.112, 0.103, 0.112]),
                    Prim("ellipsoid", HOOD, c=hc + [0.14, 0, -0.04], radii=[0.09, 0.075, 0.12])])
        model.group(0.02, [hood], disp=(0.006, 26), xf=headXf)
    else:
        hair = [Sub(h, [faceCut]) for h in (Prim("ellipsoid", HAIR, c=hc + [-0.03, 0, 0.03], radii=[0.095, 0.095, 0.08]),
                                           Prim("ellipsoid", HAIR, c=hc + [-0.07, 0, -0.08], radii=[0.05, 0.09, 0.1]))]
        model.group(0.02, hair, disp=(0.012, 38), xf=headXf)
    return model


def make_hook(flags):
    signal = "bez-sygnalu" not in flags
    v = VARIANTS[variant_of(flags)]
    tints = {mat: np.array(t)[None, :] for mat, t in v["tint"].items()}

    def hook(matId, pts, nrm, grain, albedo, spec, emit):
        if matId in tints:
            albedo = albedo * tints[matId]
        if matId == SKIN:
            blotch = value_noise(pts * 9 + 2.7)
            vein = np.clip(1.0 - np.abs(value_noise(pts * 16) - 0.5) * 16, 0, 1)
            albedo = albedo * (0.75 + 0.45 * blotch)[:, None] * (1.0 - 0.35 * vein)[:, None]
        if matId in (LINEN, COAT, TROUSERS, WRAPS, HOOD, FELT, SACK):
            moss = np.clip((value_noise(pts * 11 + 5.0) - v["moss"]) * 4.0, 0, 1) * np.clip(nrm[:, 2] * 1.5, 0, 1)
            albedo = albedo * (1 - moss[:, None]) + MOSS[None, :] * moss[:, None]
        if matId == COAT:
            # mokra tkanina: ciemniejsze wilgotne pasy przy dole
            wet = np.clip((0.95 - pts[:, 2]) * 2.0, 0, 1) * 0.35
            albedo = albedo * (1 - wet)[:, None]
        if matId in (KNOT_HOT, BAND_HOT) and signal:
            k = 1.6 if matId == KNOT_HOT else 0.7
            emit = emit + np.array([k, 0.18 * k / 1.6, 0.05 * k / 1.6])[None, :] * (0.7 + 0.3 * grain[:, None])
        return albedo, spec, emit
    return hook


# ---------- pozy kluczowe ----------
KEYS = {}
KEYS["spoczynek"] = pose()

# --- Oburecz chwyt (nieparowalny): odklada worek, prostuje ramiona, nabiera powietrza, krotki chwyt do przodu ---
_SACK_GROUND = dict(neck=(0.02, -0.4, 0.12), dir=(-0.2, -1.0, 0.0), via=None)
KEYS["chwyt_opuszcza"] = pose(pelvis=(0.04, 0.0, 0.8), spine=(8.0, 42.0, 0.0), head=(0.0, 4.0), footL=(0.12, 0.17, 0.1), footR=(-0.04, -0.2, 0.1),
                              handR=(0.12, -0.38, 0.5), handL=("t", (0.14, 0.3, 0.9)), neck=(-0.04, -0.42, 0.5), dir=(-0.3, -0.4, -0.85),
                              via=None, poleR=(-0.5, -1.0, 0.0), fingersR=(0.1, 0.9))
KEYS["chwyt_odlozony"] = pose(hold=False, pelvis=(0.05, 0.0, 0.78), spine=(12.0, 44.0, 0.0), head=(0.0, 0.0), footL=(0.12, 0.17, 0.1), footR=(-0.04, -0.2, 0.1),
                              handR=(0.08, -0.4, 0.2), handL=("t", (0.14, 0.3, 0.9)), poleR=(-0.5, -1.0, 0.0), fingersR=(0.5, 0.2), **_SACK_GROUND)
_ARMS_WIDE = dict(handR=(0.32, -0.62, 1.3), handL=(0.32, 0.62, 1.3), poleR=(-0.6, -0.3, -1.0), poleL=(-0.6, 0.3, -1.0),
                  fingersR=(1.0, 0.25), fingersL=(1.0, 0.25))
KEYS["chwyt_prostuje"] = pose(hold=False, pelvis=(0.0, 0.0, 0.93), spine=(0.0, 12.0, 0.0), head=(0.0, 0.0), hot=True, **_ARMS_WIDE, **_SACK_GROUND)
KEYS["chwyt_wdech"] = pose(hold=False, pelvis=(-0.02, 0.0, 0.97), spine=(0.0, -2.0, 0.0), head=(0.0, -14.0), hot=True,
                           footL=(0.14, 0.2, 0.1), footR=(-0.1, -0.2, 0.1),
                           **{**_ARMS_WIDE, "handR": (0.2, -0.74, 1.38), "handL": (0.2, 0.74, 1.38)}, **_SACK_GROUND)
KEYS["chwyt_wypad"] = pose(hold=False, pelvis=(0.16, 0.0, 0.86), spine=(0.0, 30.0, 0.0), head=(0.0, 12.0), hot=True,
                           footL=(0.34, 0.2, 0.1), footR=(-0.2, -0.2, 0.1),
                           handR=(0.72, -0.2, 1.18), handL=(0.72, 0.2, 1.18), poleR=(-0.4, -1.0, -0.2), poleL=(-0.4, 1.0, -0.2),
                           fingersR=(0.7, 0.8), fingersL=(0.7, 0.8), **_SACK_GROUND)
KEYS["chwyt_zlapany"] = pose(hold=False, pelvis=(0.2, 0.0, 0.82), spine=(0.0, 38.0, 0.0), head=(0.0, 14.0), hot=True,
                             footL=(0.38, 0.2, 0.1), footR=(-0.2, -0.2, 0.1),
                             handR=(0.74, -0.07, 1.1), handL=(0.74, 0.07, 1.1), poleR=(-0.4, -1.0, -0.2), poleL=(-0.4, 1.0, -0.2),
                             fingersR=(0.1, 1.0), fingersL=(0.1, 1.0), **_SACK_GROUND)
KEYS["chwyt_pusty"] = pose(hold=False, pelvis=(0.2, 0.0, 0.8), spine=(0.0, 42.0, 0.0), head=(0.0, 10.0),
                           footL=(0.38, 0.2, 0.1), footR=(-0.2, -0.2, 0.1),
                           handR=(0.56, -0.12, 0.95), handL=(0.56, 0.12, 0.95), poleR=(-0.4, -1.0, -0.2), poleL=(-0.4, 1.0, -0.2),
                           fingersR=(0.3, 0.7), fingersL=(0.3, 0.7), **_SACK_GROUND)

# --- Uderzenie tobolem (nieparowalne): worek znad barku, szeroki bliski zamach ---
_ROPE_HANDS = lambda n, d, up=0.0: dict(handR=tuple(np.array(n) + np.array([0.02, -0.03, up])),
                                       handL=tuple(np.array(n) + np.array(d) * 0.16 + np.array([0.02, 0.05, 0.0])))
KEYS["tobol_unosi"] = pose(pelvis=(0.0, 0.0, 0.9), spine=(-20.0, 14.0, 0.0), head=(15.0, 4.0), footL=(0.12, 0.2, 0.1), footR=(-0.14, -0.2, 0.1),
                           neck=(-0.06, -0.34, 1.7), dir=(-0.8, -0.25, -0.55), via=None,
                           handR=(-0.02, -0.34, 1.62), handL=(-0.12, -0.18, 1.5), poleR=(-0.4, -1.0, 0.2), poleL=(-0.5, 0.2, -1.0),
                           fingersR=(0.1, 1.0), fingersL=(0.3, 0.9))
KEYS["tobol_zamach"] = pose(pelvis=(-0.02, 0.0, 0.94), spine=(-38.0, 2.0, 0.0), head=(25.0, -4.0), hot=True,
                            footL=(0.16, 0.22, 0.1), footR=(-0.18, -0.2, 0.1),
                            neck=(-0.2, -0.28, 2.02), dir=(-0.95, 0.15, -0.3), via=None,
                            handR=(-0.18, -0.3, 1.94), handL=(-0.3, -0.12, 1.86), poleR=(0.3, -1.0, 0.2), poleL=(-0.4, 0.6, -1.0),
                            fingersR=(0.1, 1.0), fingersL=(0.3, 0.9))
KEYS["tobol_cios"] = pose(pelvis=(0.12, 0.0, 0.88), spine=(28.0, 22.0, 0.0), head=(-8.0, 10.0), hot=True,
                          footL=(0.3, 0.2, 0.1), footR=(-0.2, -0.24, 0.1),
                          neck=(0.42, -0.1, 1.12), dir=(0.7, 0.1, -0.7), via=None,
                          handR=(0.4, -0.12, 1.2), handL=(0.34, 0.06, 1.2), poleR=(-0.4, -1.0, 0.0), poleL=(-0.4, 1.0, 0.0),
                          fingersR=(0.1, 1.0), fingersL=(0.2, 1.0))
KEYS["tobol_uderzenie"] = pose(pelvis=(0.16, 0.0, 0.82), spine=(34.0, 34.0, 0.0), head=(-14.0, 14.0), hot=True,
                               footL=(0.34, 0.2, 0.1), footR=(-0.2, -0.24, 0.1),
                               neck=(0.5, 0.02, 0.62), dir=(0.5, 0.45, -0.75), via=None,
                               handR=(0.46, -0.04, 0.7), handL=(0.44, 0.1, 0.7), poleR=(-0.4, -1.0, 0.0), poleL=(-0.4, 1.0, 0.0),
                               fingersR=(0.1, 1.0), fingersL=(0.2, 1.0))
KEYS["tobol_ciagnie"] = pose(pelvis=(0.2, 0.0, 0.78), spine=(20.0, 40.0, 0.0), head=(-8.0, 10.0),
                             footL=(0.34, 0.2, 0.1), footR=(-0.2, -0.24, 0.1),
                             neck=(0.5, 0.05, 0.5), dir=(0.3, 0.5, -0.8), via=None,
                             handR=(0.46, -0.02, 0.56), handL=(0.44, 0.1, 0.56), poleR=(-0.4, -1.0, 0.0), poleL=(-0.4, 1.0, 0.0),
                             fingersR=(0.1, 1.0), fingersL=(0.2, 1.0))

# --- trafienie i smierc ---
KEYS["trafiony"] = pose(pelvis=(-0.06, 0.0, 0.89), spine=(8.0, 6.0, 6.0), head=(10.0, -16.0), neck=("t", (-0.2, -0.3, 1.5)))
KEYS["umiera_kolana"] = pose(pelvis=(0.02, 0.0, 0.68), spine=(0.0, 24.0, 0.0), head=(0.0, 22.0), footL=(-0.1, 0.18, 0.1), footR=(-0.3, -0.18, 0.1),
                             footRotL=(10.0, 30.0), footRotR=(-10.0, 50.0), neck=("t", (-0.2, -0.3, 1.45)), dir=("t", (-0.6, -0.1, -0.8)))
_KNEEL = dict(footL=(-0.35, 0.18, 0.08), footR=(-0.35, -0.18, 0.08), footRotL=(10.0, 60.0), footRotR=(-10.0, 60.0))
KEYS["umiera_kleczy"] = pose(hold=False, pelvis=(0.05, 0.0, 0.5), spine=(0.0, 28.0, 0.0), hips=(0.0, 12.0, 0.0), head=(0.0, 30.0),
                             handR=(0.24, -0.34, 0.5), handL=(0.22, 0.32, 0.55), neck=(-0.3, -0.5, 0.4), dir=(-0.4, -1.0, 0.0),
                             via=None, **_KNEEL)
KEYS["umiera_pada"] = pose(hold=False, pelvis=(0.08, 0.0, 0.46), spine=(0.0, 50.0, 0.0), hips=(0.0, 30.0, 0.0), head=(0.0, 20.0),
                           handR=(0.5, -0.28, 0.15), handL=(0.5, 0.28, 0.15), poleR=(-1.0, -0.5, 0.2), poleL=(-1.0, 0.5, 0.2),
                           neck=(-0.3, -0.55, 0.12), dir=(-0.3, -1.0, 0.0), via=None, **_KNEEL)
KEYS["umiera_lezy"] = pose(hold=False, pelvis=(0.12, 0.0, 0.3), spine=(0.0, 84.0, 0.0), hips=(0.0, 72.0, 0.0), head=(15.0, 20.0),
                           handR=(0.72, -0.34, 0.05), handL=(0.82, 0.4, 0.05), poleR=(-1.0, -0.5, 0.5), poleL=(-1.0, 0.5, 0.5),
                           neck=(-0.3, -0.6, 0.1), dir=(-0.2, -1.0, 0.0), via=None, **_KNEEL)

POSES = KEYS


def breathing(i, count):
    phase = math.sin(2 * math.pi * i / count)
    return pose(pelvis=(0.0, 0.0, 0.9 - 0.006 * phase), spine=(0.0, 24.0 + 1.5 * phase, 0.0), head=(0.0, 8.0 + 2.5 * phase),
                handL=("t", (0.1 + 0.01 * phase, 0.34, 0.8)))


def walking(i, count):
    """Powlokanie: krotki krok, stopy ledwo odrywane od ziemi, prawa reka stale na wezle, lewa lekko sie kolysze."""
    theta = 2 * math.pi * i / count
    stride = 0.12

    def foot(offset, side):
        t = theta + offset
        return (0.0 + stride * math.cos(t), side * 0.15, 0.1 + 0.035 * max(0.0, -math.sin(t)))
    return pose(pelvis=(0.0, 0.0, 0.9 - 0.012 * math.cos(2 * theta)), spine=(4.0 * math.cos(theta), 24.0, 3.0 * math.sin(theta)),
                head=(-3.0 * math.cos(theta), 8.0), footL=foot(0.0, 1), footR=foot(math.pi, -1), footRotL=(6.0, 0.0), footRotR=(-6.0, 0.0),
                handL=("t", (0.1 - 0.07 * math.cos(theta), 0.34, 0.8)))


def _sack_lerp(a, b, t):
    """Pozy, w ktorych worek jest we wspolrzednych tulowia i swiata, interpolowane przez posredni krok."""
    return mix(a, b, t)


ANIMS = {
    "spoczynek": dict(frames=[breathing(i, 4) for i in range(4)], durations=[260] * 4, loop=True, events={}),
    "chod": dict(frames=[walking(i, 8) for i in range(8)], durations=[120] * 8, loop=True,
                 root_speed_mps=round(4 * 0.12 / 0.96, 2), events={}),
    # Oburecz chwyt: odlozenie worka, prostowanie ramion i wdech (zapowiedz), krotki chwyt do przodu, wolny powrot
    "chwyt": dict(
        frames=[KEYS["spoczynek"], KEYS["chwyt_opuszcza"], KEYS["chwyt_odlozony"], KEYS["chwyt_prostuje"], KEYS["chwyt_wdech"],
                KEYS["chwyt_wypad"], KEYS["chwyt_zlapany"], KEYS["chwyt_pusty"],
                mix(KEYS["chwyt_pusty"], KEYS["chwyt_odlozony"], 0.6), KEYS["chwyt_opuszcza"]],
        durations=[120, 160, 200, 260, 320, 80, 110, 380, 320, 240], loop=False,
        events=dict(parowalny=False, zapowiedz=[1, 2, 3, 4], sygnal=[3, 4, 5, 6], aktywne=[5, 6], trafienie=6, okazja=[7, 8, 9])),
    # Uderzenie tobolem: worek znad barku, szeroki zamach, uderzenie w ziemie i ciagniecie
    "uderzenie_tobolem": dict(
        frames=[KEYS["spoczynek"], mix(KEYS["spoczynek"], KEYS["tobol_unosi"], 0.6), KEYS["tobol_unosi"], KEYS["tobol_zamach"],
                KEYS["tobol_cios"], KEYS["tobol_uderzenie"], KEYS["tobol_ciagnie"], mix(KEYS["tobol_ciagnie"], KEYS["spoczynek"], 0.5),
                KEYS["spoczynek"]],
        durations=[120, 160, 260, 320, 70, 110, 380, 320, 200], loop=False,
        events=dict(parowalny=False, zapowiedz=[1, 2, 3], sygnal=[3, 4, 5], aktywne=[4, 5], trafienie=5, okazja=[6, 7])),
    "trafienie": dict(frames=[mix(KEYS["spoczynek"], KEYS["trafiony"], 0.6), KEYS["trafiony"], mix(KEYS["trafiony"], KEYS["spoczynek"], 0.5)],
                      durations=[70, 150, 170], loop=False, events={}),
    "smierc": dict(
        frames=[KEYS["trafiony"], KEYS["umiera_kolana"], mix(KEYS["umiera_kolana"], KEYS["umiera_kleczy"], 0.5), KEYS["umiera_kleczy"],
                mix(KEYS["umiera_kleczy"], KEYS["umiera_pada"], 0.5), KEYS["umiera_pada"], mix(KEYS["umiera_pada"], KEYS["umiera_lezy"], 0.6),
                KEYS["umiera_lezy"]],
        durations=[110, 140, 140, 160, 140, 170, 180, 700], loop=False, events=dict(ostatnia_klatka="zostaje jako zwloki")),
}


if __name__ == "__main__":
    charId = "powrotnik" + ("" if variant_of([a[2:] for a in sys.argv]) == "a" else "-" + variant_of([a[2:] for a in sys.argv]))
    if len(sys.argv) > 1 and sys.argv[1] == "anim":
        run_anim(charId, __file__, sys.argv[2:])
    else:
        run_cli(charId, __file__)
