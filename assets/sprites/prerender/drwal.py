"""ENM-drwal jako ożywieniec. Wzorcowa postać dla kolejnych potworów.

Wybór wykonawczy: ożywieniec (autor: „demon albo ożywieniec”); do potwierdzenia w kanonie.
Warianty (a–d) różnią się budową, głową, ubraniem i drobiazgami, ale zachowują sylwetkę z bestiariusza:
szerokie barki, długi topór, ciemny fartuch z jednym jasnym szwem. Animacje i ich czasy są wspólne.

Użycie:
  python3 drwal.py anim [nazwa|all] [--wariant=b] [--szkic]   atlas PNG + JSON + GIF w output/drwal[-b]/
  python3 drwal.py <poza|all> [kierunek 0-7|all] [--wariant=b] pojedyncze pozy z POSES
Flaga --bez-sygnalu wyłącza czerwone zarzewie na ostrzu.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sdfkit import Isect, Model, Prim, Sub, Xf, normalize, rotation, run_anim, run_cli, value_noise  # noqa: E402

(SKIN, SHIRT, TROUSERS, APRON, SEAM, LEATHER, WRAPS, BAST, WOOD, IRON, EDGE, HAIR, EYES, SOCKET, TEETH, EDGE_HOT,
 HOOD, FELT, FUR) = range(19)

MATERIALS = {
    SKIN: dict(alb=(0.13, 0.135, 0.115), spec=0.28, pw=18, grit=0.7),       # popielata, woskowa skóra
    SHIRT: dict(alb=(0.078, 0.07, 0.055), spec=0.05, pw=6, grit=0.9),     # brudny len
    TROUSERS: dict(alb=(0.042, 0.038, 0.033), spec=0.05, pw=6, grit=0.9),  # ciemna wełna
    APRON: dict(alb=(0.048, 0.03, 0.019), spec=0.3, pw=14, grit=0.6),      # mokra skóra fartucha
    SEAM: dict(alb=(0.34, 0.29, 0.19), spec=0.05, pw=6, grit=0.4),         # jedyny jasny szew
    LEATHER: dict(alb=(0.07, 0.044, 0.025), spec=0.2, pw=12, grit=0.6),    # pas, rzemienie, sakwa
    WRAPS: dict(alb=(0.12, 0.11, 0.09), spec=0.04, pw=4, grit=1.0),        # onuce
    BAST: dict(alb=(0.11, 0.085, 0.05), spec=0.05, pw=4, grit=1.2),        # łapcie z łyka
    WOOD: dict(alb=(0.085, 0.058, 0.034), spec=0.15, pw=10, grit=0.7),     # trzonek
    IRON: dict(alb=(0.055, 0.042, 0.033), spec=0.4, pw=22, grit=1.1, specTint=0.5),  # zardzewiały obuch
    EDGE: dict(alb=(0.2, 0.2, 0.21), spec=1.3, pw=60, grit=0.4, specTint=0.6),       # wyostrzona krawędź
    HAIR: dict(alb=(0.034, 0.032, 0.029), spec=0.18, pw=10, grit=0.8),     # zlepione włosy
    EYES: dict(alb=(0.0, 0.0, 0.0), spec=0.0, pw=1, grit=0.0, emit=(0.6, 0.72, 0.6)),  # mętny blask
    SOCKET: dict(alb=(0.008, 0.008, 0.008), spec=0.0, pw=1, grit=0.0),
    TEETH: dict(alb=(0.2, 0.17, 0.12), spec=0.2, pw=12, grit=0.6),
    EDGE_HOT: dict(alb=(0.2, 0.2, 0.21), spec=1.3, pw=60, grit=0.4, specTint=0.6),   # krawędź z sygnałem ataku nieparowalnego
    HOOD: dict(alb=(0.05, 0.05, 0.045), spec=0.04, pw=4, grit=1.0),        # wełniany kaptur
    FELT: dict(alb=(0.07, 0.055, 0.04), spec=0.04, pw=4, grit=0.9),        # filcowy kołpak
    FUR: dict(alb=(0.06, 0.045, 0.032), spec=0.06, pw=4, grit=1.4),        # futrzany otok
}

MOSS = np.array([0.034, 0.05, 0.022])

# ---------- warianty ----------
# tint: mnożnik albedo materiału; moss: próg mchu (niżej = więcej); hunch: dodatkowe pochylenie (stopnie)
VARIANTS = {
    "a": dict(scale=1.0, girth=1.0, hunch=0.0, head="dlugie", beard="dluga", sleeves=("cale", "cale"),
              tint={}, moss=0.55, pouch=False, blade="brodaty", apron=1.0),
    "b": dict(scale=0.95, girth=1.14, hunch=4.0, head="lysy", beard=None, sleeves=("brak", "brak"),
              tint={SKIN: (0.92, 1.05, 0.9), SHIRT: (1.35, 1.1, 0.85)}, moss=0.5, pouch=True, blade="brodaty", apron=0.9),
    "c": dict(scale=1.04, girth=0.9, hunch=9.0, head="kaptur", beard=None, sleeves=("cale", "cale"),
              tint={SKIN: (0.9, 0.95, 1.05), SHIRT: (0.85, 0.95, 1.2)}, moss=0.6, pouch=False, blade="waski", apron=1.1),
    "d": dict(scale=1.0, girth=1.04, hunch=2.0, head="kolpak", beard="krotka", sleeves=("brak", "cale"),
              tint={SKIN: (0.85, 0.92, 1.0), TROUSERS: (1.3, 1.15, 1.0)}, moss=0.45, pouch=True, blade="waski", apron=1.0),
}


def variant_of(flags):
    for flag in flags:
        if flag.startswith("wariant="):
            return flag.split("=", 1)[1]
    return "a"


# ---------- szkielet w pozycji spoczynkowej (współrzędne świata, metry) ----------
REST_PELVIS = np.array([0.0, 0.0, 0.97])
NECK_BASE = np.array([0.06, 0.0, 1.5])
HIP = {1: np.array([0.0, 0.11, 0.95]), -1: np.array([0.0, -0.11, 0.95])}
KNEE = {1: np.array([0.02, 0.13, 0.53]), -1: np.array([0.02, -0.13, 0.53])}
ANKLE = {1: np.array([0.0, 0.14, 0.1]), -1: np.array([0.0, -0.14, 0.1])}
SHOULDER = {1: np.array([0.0, 0.3, 1.5]), -1: np.array([0.0, -0.3, 1.5])}
ELBOW = {1: np.array([0.0, 0.34, 1.19]), -1: np.array([0.0, -0.34, 1.19])}
WRIST = {1: np.array([0.03, 0.36, 0.82]), -1: np.array([0.03, -0.36, 0.82])}
AXE_LEN = 1.0  # od końca trzonka do środka obucha

# ---------- pozy ----------
# Pozę opisują cele, nie kąty stawów: miednica, obrót tułowia i głowy, stopy, topór, dłonie.
# Łokcie i kolana liczy IK. Klatka animacji = pełna poza (BASE + zmiany).
BASE = dict(
    pelvis=(0.0, 0.0, 0.93),
    spine=(0.0, 8.0, 0.0),        # yaw (w lewo), pitch (do przodu), roll — stopnie, wokół miednicy
    hips=None,                    # obrót bioder i fartucha; None = część obrotu tułowia
    head=(0.0, 10.0),             # yaw, pitch głowy wokół nasady szyi
    footL=(0.12, 0.2, 0.1), footR=(-0.12, -0.2, 0.1),   # cele kostek
    footRotL=(10.0, 0.0), footRotR=(-15.0, 0.0),         # yaw, pitch stopy
    knob=(0.22, -0.18, 0.92),     # koniec trzonka
    haft=(0.25, 0.55, 0.8),       # kierunek trzonka (ku obuchowi)
    swing=None,                   # oś zamachu: ostrze patrzy w stronę ruchu (cross(oś, trzonek))
    edge=(1.0, 0.0, 0.0),         # albo jawny kierunek ostrza (gdy swing=None)
    gripR=0.07, gripL=0.42,       # chwyt dłoni na trzonku (m od końca)
    handR=None, handL=None,       # wolna dłoń: cel w świecie zamiast chwytu
    poleR=(-0.4, -1.0, -0.3), poleL=(-0.4, 1.0, -0.3),   # gdzie wychodzą łokcie (układ tułowia)
    hot=False,                    # czerwone zarzewie na ostrzu: sygnał ataku nieparowalnego
)


def pose(**changes):
    result = dict(BASE)
    result.update(changes)
    return result


def mix(a, b, t):
    """Interpolacja dwóch póz (liczby i krotki liniowo, kierunek trzonka po normalizacji)."""
    result = {}
    for key in a:
        va, vb = a[key], b[key]
        if va is None or vb is None or isinstance(va, bool):
            result[key] = va if t < 0.5 else vb
        elif isinstance(va, (int, float)):
            result[key] = va + (vb - va) * t
        else:
            result[key] = tuple(x + (y - x) * t for x, y in zip(va, vb))
    result["haft"] = tuple(normalize(normalize(a["haft"]) * (1 - t) + normalize(b["haft"]) * t))
    return result


# ---------- geometria pomocnicza ----------

def ik(start, target, len1, len2, pole):
    """Dwa odcinki od `start` do `target`; staw środkowy wypychany w stronę `pole`."""
    delta = target - start
    dist = np.linalg.norm(delta)
    if dist > len1 + len2 + 0.02:
        print(f"  uwaga: cel poza zasięgiem o {dist - len1 - len2:.3f} m", file=sys.stderr)
    reach = np.clip(dist, abs(len1 - len2) + 1e-3, len1 + len2 - 1e-3)
    axis = delta / max(dist, 1e-9)
    along = (len1 ** 2 - len2 ** 2 + reach ** 2) / (2 * reach)
    side = math.sqrt(max(len1 ** 2 - along ** 2, 0.0))
    bend = np.asarray(pole, float) - axis * np.dot(pole, axis)
    bend = bend / (np.linalg.norm(bend) + 1e-9)
    return start + axis * along + bend * side, start + axis * reach


def rotate_onto(src, dst):
    """Najmniejszy obrót przeprowadzający kierunek src na dst."""
    a, b = normalize(src), normalize(dst)
    v, c = np.cross(a, b), float(np.dot(a, b))
    if c < -0.9999:
        perp = normalize(np.cross(a, [1.0, 0, 0]) if abs(a[0]) < 0.9 else np.cross(a, [0, 1.0, 0]))
        return 2 * np.outer(perp, perp) - np.eye(3)
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx / (1 + c)


def bone(restA, restB, a, b):
    """Ruch kości: odcinek spoczynkowy restA→restB trafia na a→b."""
    return Xf(rotate_onto(restB - restA, b - a), restA, a - restA)


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

    # ---------- tułów: szerokie, kościste barki, zapadnięty brzuch ----------
    torso = [
        Prim("ellipsoid", SHIRT, c=[0.0, 0, 1.06], radii=[0.11 * g, 0.16 * g, 0.13]),
        Prim("ellipsoid", SHIRT, c=[0.02, 0, 1.31], radii=[0.145 * g, 0.25 * g, 0.17]),
        Prim("ellipsoid", SHIRT, c=[0.0, 0, 1.46], radii=[0.12, 0.32, 0.08]),
    ] + [Prim("ellipsoid", SHIRT, c=SHOULDER[s] + [0, 0, 0.02], radii=[0.08, 0.08, 0.075]) for s in (1, -1)]
    model.group(0.06, torso, disp=(0.004, 20), xf=upper)
    # szyja wysunięta do przodu — zgarbienie
    model.group(0.03, [Prim("cone", SKIN, a=[0.02, 0, 1.47], b=[0.1, 0, 1.6], r1=0.06, r2=0.045)], disp=(0.003, 40), xf=upper)
    straps = [Prim("cone", LEATHER, a=[0.13 * g, s * 0.13, 1.28], b=[0.06, s * 0.08, 1.56], r1=0.012, r2=0.012) for s in (1, -1)]
    model.group(0.0, straps, xf=upper)

    # miednica: spodnie, pas, fartuch (podąża za tułowiem tylko częściowo)
    model.group(0.03, [Prim("cone", TROUSERS, a=[0, 0, 1.0], b=[0, 0, 0.82], r1=0.15 * g, r2=0.17 * g)], disp=(0.004, 20), xf=lower)
    model.group(0.0, [Prim("cylinder", LEATHER, c=[0, 0, 0.99], R=np.eye(3), r=0.158 * g, h=0.028)], xf=lower)
    length = v["apron"]
    apronC = np.array([0.03, 0, 0.93])
    apronShell = Sub(Prim("ellipsoid", APRON, c=apronC, radii=[0.185 * g, 0.215 * g, 0.5]),
                     [Prim("ellipsoid", APRON, c=apronC, radii=[0.17 * g, 0.2 * g, 0.49])])
    bottom = 1.29 - 0.74 * length
    front = Prim("box", APRON, c=[0.2, 0, (1.29 + bottom) / 2], R=np.eye(3), half=[0.15 * g, 0.16 * g, (1.29 - bottom) / 2])
    tatters = [Prim("sphere", APRON, c=[0.2, y * g, bottom], r=r) for y, r in ((-0.11, 0.05), (0.02, 0.04), (0.12, 0.06))]
    apron = Sub(Isect([apronShell, front]), tatters)
    seamBand = Prim("box", SEAM, c=[0.2, 0.06 * g, 0.92], R=np.eye(3), half=[0.15, 0.006, 0.35])
    seamShell = Sub(Prim("ellipsoid", SEAM, c=apronC, radii=[0.19 * g, 0.22 * g, 0.505]),
                    [Prim("ellipsoid", SEAM, c=apronC, radii=[0.18 * g, 0.21 * g, 0.495])])
    model.group(0.0, [apron, Isect([seamShell, seamBand, front])], xf=lower)
    if v["pouch"]:
        # sakwa i nóż przy pasie, z boku
        pouch = [Prim("box", LEATHER, c=[-0.02, -0.17 * g, 0.92], R=np.eye(3), half=[0.05, 0.03, 0.06], round=0.015),
                 Prim("cone", WOOD, a=[-0.1, 0.15 * g, 1.0], b=[-0.12, 0.16 * g, 0.88], r1=0.016, r2=0.014),
                 Prim("cone", LEATHER, a=[-0.12, 0.16 * g, 0.9], b=[-0.14, 0.17 * g, 0.74], r1=0.022, r2=0.012)]
        model.group(0.0, pouch, disp=(0.003, 40), xf=lower)

    # ---------- nogi ----------
    for side, footKey, rotKey in ((1, "footL", "footRotL"), (-1, "footR", "footRotR")):
        hip = lower.apply(HIP[side])
        knee, ankle = ik(hip, np.array(p[footKey], float), np.linalg.norm(KNEE[side] - HIP[side]),
                         np.linalg.norm(ANKLE[side] - KNEE[side]), lower.R @ np.array([1.0, side * 0.15, 0.0]))
        model.group(0.03, [Prim("cone", TROUSERS, a=HIP[side], b=KNEE[side], r1=0.085, r2=0.064),
                           Prim("sphere", TROUSERS, c=KNEE[side], r=0.066)], disp=(0.006, 24), xf=bone(HIP[side], KNEE[side], hip, knee))
        shinXf = bone(KNEE[side], ANKLE[side], knee, ankle)
        model.group(0.02, [Prim("cone", WRAPS, a=KNEE[side], b=ANKLE[side], r1=0.062, r2=0.05)], disp=(0.006, 34), xf=shinXf)
        # rzemienie oplatające onuce
        legDir = normalize(ANKLE[side] - KNEE[side])
        ringR = np.stack([normalize(np.cross(legDir, [0, 1, 0])), [0, 1, 0], legDir], axis=1)
        rings = [Prim("torus", LEATHER, c=KNEE[side] + (ANKLE[side] - KNEE[side]) * t, R=ringR, major=0.058 - 0.01 * t, minor=0.007) for t in (0.25, 0.5, 0.75)]
        model.group(0.0, rings, xf=shinXf)
        footXf = Xf(rotation(*p[rotKey], 0.0), ANKLE[side], ankle - ANKLE[side])
        a = ANKLE[side]
        model.group(0.03, [Prim("box", BAST, c=[a[0] + 0.06, a[1], 0.045], R=np.eye(3), half=[0.09, 0.04, 0.028], round=0.022),
                           Prim("cone", BAST, a=[a[0], a[1], 0.06], b=a, r1=0.058, r2=0.052)], disp=(0.006, 30), xf=footXf)

    # ---------- topór: budowany w układzie własnym (x = trzonek, z = ostrze), potem ustawiany ----------
    knob = np.array(p["knob"], float)
    haft = normalize(p["haft"])
    edge = np.cross(p["swing"], haft) if p["swing"] is not None else np.array(p["edge"], float)
    edge = normalize(edge - haft * np.dot(edge, haft))
    axeXf = Xf(np.stack([haft, np.cross(edge, haft), edge], axis=1), (0, 0, 0), knob)
    headC = np.array([AXE_LEN, 0, 0])
    toBlade = np.array([[1.0, 0, 0], [0, 0, 1.0], [0, 1.0, 0]])   # oś walca wzdłuż grubości ostrza
    if v["blade"] == "brodaty":
        bladeC, bladeHalf, arc, arcR, notchOff = headC + [-0.02, 0, 0.13], 0.11, headC + [-0.02, 0, -0.1], 0.36, (-0.145, 0.135)
    else:  # węższa, dłuższa siekiera
        bladeC, bladeHalf, arc, arcR, notchOff = headC + [0.0, 0, 0.14], 0.075, headC + [0.0, 0, -0.18], 0.45, (-0.115, 0.115)
    notches = [Prim("cylinder", IRON, c=headC + [off, 0, 0.085], R=toBlade, r=0.07, h=0.05) for off in notchOff]
    edgeMat = EDGE_HOT if p["hot"] else EDGE
    blade = Sub(Isect([Prim("box", IRON, c=bladeC, R=np.eye(3), half=[bladeHalf, 0.011, 0.15], round=0.003),
                       Prim("sphere", IRON, c=arc, r=arcR)]), notches)
    edgeBand = Sub(Isect([Prim("box", edgeMat, c=bladeC, R=np.eye(3), half=[bladeHalf + 0.002, 0.013, 0.155]),
                          Prim("sphere", edgeMat, c=arc, r=arcR + 0.002),
                          Sub(Prim("sphere", edgeMat, c=arc, r=arcR + 0.04), [Prim("sphere", edgeMat, c=arc, r=arcR - 0.03)])]), notches)
    model.group(0.0, [Prim("cone", WOOD, a=[-0.03, 0, 0], b=[1.06, 0, 0], r1=0.021, r2=0.019)], disp=(0.002, 50), xf=axeXf)
    model.group(0.0, [blade, edgeBand], xf=axeXf)
    model.group(0.01, [Prim("box", IRON, c=headC + [0, 0, -0.015], R=np.eye(3), half=[0.04, 0.028, 0.045], round=0.008)], disp=(0.003, 60), xf=axeXf)

    # ---------- ręce: IK do chwytu na trzonku albo do wolnego celu ----------
    targets = {-1: p["handR"] if p["handR"] is not None else knob + haft * p["gripR"],
               1: p["handL"] if p["handL"] is not None else knob + haft * p["gripL"]}
    for side, poleKey, sleeveKind in ((-1, "poleR", v["sleeves"][1]), (1, "poleL", v["sleeves"][0])):
        shoulder = upper.apply(SHOULDER[side])
        elbow, wrist = ik(shoulder, np.asarray(targets[side], float), np.linalg.norm(ELBOW[side] - SHOULDER[side]),
                          np.linalg.norm(WRIST[side] - ELBOW[side]), upper.R @ np.array(p[poleKey], float))
        s0, e0, w0 = SHOULDER[side], ELBOW[side], WRIST[side]
        upperArm = bone(s0, e0, shoulder, elbow)
        if sleeveKind == "cale":
            # rękaw podarty przy łokciu
            sleeve = Sub(Prim("cone", SHIRT, a=s0, b=e0 + (e0 - s0) * 0.12, r1=0.068, r2=0.058),
                         [Prim("sphere", SHIRT, c=e0 + (e0 - s0) * 0.2 + np.array([0.03, 0.0, 0.0]), r=0.05)])
            model.group(0.04, [sleeve], disp=(0.006, 24), xf=upperArm)
        else:
            # rękaw oderwany: goła, chuda ręka i strzęp przy barku
            model.group(0.03, [Prim("cone", SKIN, a=s0, b=e0, r1=0.05, r2=0.042),
                               Sub(Prim("cone", SHIRT, a=s0 + [0, 0, 0.03], b=s0 + (e0 - s0) * 0.25, r1=0.072, r2=0.066),
                                   [Prim("sphere", SHIRT, c=s0 + (e0 - s0) * 0.32 + [0.03, 0, 0], r=0.06)])], disp=(0.004, 30), xf=upperArm)
        # wychudłe przedramię, kościsty łokieć, pięść
        forearm = normalize(w0 - e0)
        model.group(0.025, [Prim("cone", SKIN, a=e0, b=w0 - forearm * 0.04, r1=0.046, r2=0.03),
                            Prim("sphere", SKIN, c=e0, r=0.045),
                            Prim("ellipsoid", SKIN, c=w0, radii=[0.045, 0.042, 0.045])], disp=(0.003, 40), xf=bone(e0, w0, elbow, wrist))

    # ---------- głowa: zapadnięte oczodoły, opadnięta szczęka ----------
    hc = np.array([0.14, 0.0, 1.7])
    sockets = [Prim("sphere", SKIN, c=hc + [0.098, s * 0.036, 0.0], r=0.027) for s in (1, -1)]
    cheeks = [Prim("sphere", SKIN, c=hc + [0.07, s * 0.08, -0.05], r=0.03) for s in (1, -1)]
    mouth = Prim("ellipsoid", SKIN, c=hc + [0.1, 0, -0.098], radii=[0.04, 0.035, 0.016])
    skull = Sub(Prim("sphere", SKIN, c=hc, r=0.092), sockets + cheeks + [mouth], smooth=0.012)
    face = Sub(Prim("ellipsoid", SKIN, c=hc + [0.045, 0, -0.055], radii=[0.065, 0.068, 0.06]), sockets + cheeks + [mouth], smooth=0.012)
    jaw = Prim("ellipsoid", SKIN, c=hc + [0.06, 0, -0.125], radii=[0.05, 0.055, 0.028])
    nose = Prim("cone", SKIN, a=hc + [0.1, 0, -0.01], b=hc + [0.125, 0, -0.045], r1=0.014, r2=0.01)
    model.group(0.015, [skull, face, jaw, nose], disp=(0.0015, 40), xf=headXf)
    model.group(0.0, [Prim("sphere", SOCKET, c=hc + [0.084, s * 0.036, 0.0], r=0.016) for s in (1, -1)], xf=headXf)
    model.group(0.0, [Prim("sphere", EYES, c=hc + [0.094, s * 0.036, -0.002], r=0.0075) for s in (1, -1)], xf=headXf)
    model.group(0.0, [Prim("box", TEETH, c=hc + [0.098, 0, -0.088], R=np.eye(3), half=[0.008, 0.026, 0.008], round=0.003)], xf=headXf)

    faceCut = Prim("ellipsoid", HAIR, c=hc + [0.1, 0, -0.03], radii=[0.08, 0.075, 0.11])
    hair = []
    if v["head"] == "dlugie":
        # długie, zlepione włosy
        hair = [Sub(h, [faceCut]) for h in (Prim("ellipsoid", HAIR, c=hc + [-0.02, 0, 0.02], radii=[0.1, 0.1, 0.09]),
                                            Prim("ellipsoid", HAIR, c=hc + [-0.06, 0, -0.08], radii=[0.06, 0.1, 0.12]))]
    elif v["head"] == "lysy":
        # łysa czaszka, resztki włosów nad uszami
        hair = [Prim("ellipsoid", HAIR, c=hc + [-0.03, s * 0.075, -0.02], radii=[0.06, 0.03, 0.04]) for s in (1, -1)]
    elif v["head"] == "kaptur":
        hoodC = hc + [-0.01, 0, 0.0]
        hood = Sub(Prim("ellipsoid", HOOD, c=hoodC, radii=[0.13, 0.12, 0.13]),
                   [Prim("ellipsoid", HOOD, c=hoodC, radii=[0.112, 0.103, 0.112]),
                    Prim("ellipsoid", HOOD, c=hc + [0.14, 0, -0.04], radii=[0.09, 0.075, 0.12])])
        cape = Sub(Prim("ellipsoid", HOOD, c=[0.0, 0, 1.47], radii=[0.17, 0.36, 0.13]),
                   [Prim("ellipsoid", HOOD, c=[0.0, 0, 1.45], radii=[0.155, 0.345, 0.12]),
                    Prim("box", HOOD, c=[0, 0, 1.3], R=np.eye(3), half=[0.3, 0.4, 0.1])])
        model.group(0.02, [hood], disp=(0.006, 26), xf=headXf)
        model.group(0.02, [cape], disp=(0.006, 22), xf=upper)
    elif v["head"] == "kolpak":
        hair = [Sub(Prim("ellipsoid", HAIR, c=hc + [-0.05, 0, -0.05], radii=[0.06, 0.1, 0.07]), [faceCut])]
        cap = [Prim("cylinder", FELT, c=hc + [-0.01, 0, 0.08], R=np.eye(3), r=0.085, h=0.05, round=0.02),
               Prim("ellipsoid", FELT, c=hc + [-0.03, 0, 0.14], radii=[0.08, 0.07, 0.06])]
        model.group(0.02, cap, disp=(0.004, 30), xf=headXf)
        model.group(0.0, [Prim("torus", FUR, c=hc + [-0.01, 0, 0.045], R=np.eye(3), major=0.095, minor=0.025)], disp=(0.01, 45), xf=headXf)
    if v["beard"] == "dluga":
        hair.append(Prim("cone", HAIR, a=hc + [0.06, 0, -0.12], b=hc + [0.1, 0, -0.24], r1=0.05, r2=0.012))
    elif v["beard"] == "krotka":
        hair.append(Prim("ellipsoid", HAIR, c=hc + [0.07, 0, -0.14], radii=[0.045, 0.06, 0.04]))
    if hair:
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
        if matId in (SHIRT, TROUSERS, APRON, WRAPS, HOOD, FELT):
            # mech i pleśń tam, gdzie osiada wilgoć: na górnych powierzchniach
            moss = np.clip((value_noise(pts * 11 + 5.0) - v["moss"]) * 4.0, 0, 1) * np.clip(nrm[:, 2] * 1.5, 0, 1)
            albedo = albedo * (1 - moss[:, None]) + MOSS[None, :] * moss[:, None]
        if matId == EDGE_HOT and signal:
            # sygnał ataku nieparowalnego: zarzewie na krawędzi
            emit = emit + np.array([1.6, 0.18, 0.05])[None, :] * (0.7 + 0.3 * grain[:, None])
        return albedo, spec, emit
    return hook


# ---------- kluczowe pozy ----------
KEYS = {}
KEYS["gotowosc"] = pose()

# cięcie z boku (parowalne): obrót barków w prawo, potem zamach poziomy w lewo
KEYS["ciecie_zamach"] = pose(spine=(-40.0, 6.0, 0.0), head=(25.0, 8.0), knob=(0.1, -0.3, 1.25), haft=(-0.75, -0.55, 0.3),
                             swing=(0.0, 0.0, 1.0), gripR=0.03, gripL=0.12, footL=(0.2, 0.2, 0.1), footR=(-0.15, -0.24, 0.1))
KEYS["ciecie_trafienie"] = pose(spine=(15.0, 12.0, 0.0), head=(0.0, 8.0), knob=(0.35, -0.05, 1.15), haft=(1.0, 0.15, -0.05),
                                swing=(0.0, 0.0, 1.0), gripR=0.05, gripL=0.18, footL=(0.24, 0.2, 0.1), footR=(-0.15, -0.24, 0.1))
KEYS["ciecie_koniec"] = pose(spine=(45.0, 12.0, 0.0), head=(-10.0, 8.0), knob=(0.2, 0.2, 1.1), haft=(0.3, 1.0, -0.15),
                             swing=(0.0, 0.0, 1.0), gripR=0.05, gripL=0.18, footL=(0.24, 0.2, 0.1), footR=(-0.15, -0.24, 0.1))

# Rozłupanie (nieparowalne): obie dłonie nad głową, pionowe uderzenie, ostrze grzęźnie w ziemi
KEYS["rozlupanie"] = pose(pelvis=(0.0, 0.0, 0.95), spine=(0.0, -6.0, 0.0), head=(0.0, -5.0), knob=(0.06, 0.0, 1.86),
                          haft=(-0.6, -0.36, 0.2), swing=(0.0, 1.0, 0.0), gripR=0.07, gripL=0.2,
                          footL=(0.1, 0.21, 0.1), footR=(-0.2, -0.22, 0.1), poleR=(0.4, -1.0, 0.2), poleL=(0.2, 1.0, 0.2), hot=True)
KEYS["rozlupanie_cios"] = pose(pelvis=(0.03, 0.0, 0.9), spine=(0.0, 25.0, 0.0), head=(0.0, 10.0), knob=(0.36, -0.02, 1.35),
                               haft=(0.78, 0.0, 0.62), swing=(0.0, 1.0, 0.0), gripR=0.07, gripL=0.2,
                               footL=(0.2, 0.21, 0.1), footR=(-0.2, -0.22, 0.1), hot=True)
KEYS["rozlupanie_wbite"] = pose(pelvis=(0.05, 0.0, 0.82), spine=(0.0, 38.0, 0.0), head=(0.0, 15.0), knob=(0.3, -0.02, 0.82),
                                haft=(0.6, 0.0, -0.8), swing=(0.0, 1.0, 0.0), gripR=0.07, gripL=0.17,
                                footL=(0.25, 0.22, 0.1), footR=(-0.2, -0.24, 0.1), hot=True)
KEYS["rozlupanie_wyrywa"] = pose(pelvis=(0.0, 0.0, 0.85), spine=(0.0, 28.0, -4.0), head=(0.0, 0.0), knob=(0.26, -0.02, 0.86),
                                 haft=(0.62, 0.0, -0.78), swing=(0.0, 1.0, 0.0), gripR=0.07, gripL=0.17,
                                 footL=(0.25, 0.22, 0.1), footR=(-0.2, -0.24, 0.1))
KEYS["rozlupanie_wyrwane"] = pose(pelvis=(0.0, 0.0, 0.9), spine=(0.0, 18.0, 0.0), knob=(0.25, -0.05, 0.95), haft=(0.75, 0.1, -0.3),
                                  swing=(0.0, 1.0, 0.0), gripR=0.07, gripL=0.18)

# trafienie i śmierć
KEYS["trafiony"] = pose(pelvis=(-0.06, 0.0, 0.92), spine=(8.0, -14.0, 6.0), head=(10.0, -20.0), knob=(0.16, -0.18, 0.96))
_AXE_DOWN = dict(knob=(-0.35, -0.45, 0.03), haft=(1.0, -0.1, 0.0), swing=(0.0, 0.0, 1.0))
_KNEEL = dict(footL=(-0.35, 0.18, 0.08), footR=(-0.35, -0.18, 0.08), footRotL=(10.0, 60.0), footRotR=(-10.0, 60.0))
KEYS["umiera_kolana"] = pose(pelvis=(0.02, 0.0, 0.7), spine=(0.0, 10.0, 0.0), head=(0.0, 25.0), knob=(0.28, -0.18, 0.8),
                             haft=(0.2, 0.5, 0.85), poleR=(0.2, -1.0, -0.3), poleL=(0.2, 1.0, -0.3))
KEYS["umiera_kleczy"] = pose(pelvis=(0.05, 0.0, 0.5), spine=(0.0, 15.0, 0.0), hips=(0.0, 12.0, 0.0), head=(0.0, 30.0), handR=(0.22, -0.32, 0.55),
                             handL=(0.2, 0.32, 0.58), **_KNEEL, **_AXE_DOWN)
KEYS["umiera_pada"] = pose(pelvis=(0.08, 0.0, 0.46), spine=(0.0, 45.0, 0.0), hips=(0.0, 30.0, 0.0), head=(0.0, 20.0), handR=(0.5, -0.28, 0.15),
                           handL=(0.5, 0.28, 0.15), poleR=(-1.0, -0.5, 0.2), poleL=(-1.0, 0.5, 0.2), **_KNEEL, **_AXE_DOWN)
KEYS["umiera_lezy"] = pose(pelvis=(0.12, 0.0, 0.3), spine=(0.0, 84.0, 0.0), hips=(0.0, 72.0, 0.0), head=(15.0, 20.0), handR=(0.72, -0.34, 0.05),
                           handL=(0.82, 0.4, 0.05), poleR=(-1.0, -0.5, 0.5), poleL=(-1.0, 0.5, 0.5), **_KNEEL, **_AXE_DOWN)

POSES = KEYS  # dla `python3 drwal.py <poza> <kierunek>`


def breathing(i, count):
    phase = math.sin(2 * math.pi * i / count)
    return pose(pelvis=(0.0, 0.0, 0.93 - 0.008 * phase), spine=(0.0, 9.0 + 2.0 * phase, 0.0), head=(0.0, 11.0 + 3.0 * phase),
                knob=(0.22, -0.18, 0.92 - 0.012 * phase))


def walking(i, count):
    theta = 2 * math.pi * i / count
    stride = 0.22

    def foot(offset, side):
        t = theta + offset
        return (0.03 + stride * math.cos(t), side * 0.17, 0.1 + 0.11 * max(0.0, -math.sin(t)))
    return pose(pelvis=(0.0, 0.0, 0.93 - 0.018 * math.cos(2 * theta)), spine=(6.0 * math.cos(theta), 12.0, 0.0), head=(0.0, 14.0),
                footL=foot(0.0, 1), footR=foot(math.pi, -1), footRotL=(5.0, 0.0), footRotR=(-5.0, 0.0),
                knob=(0.24, -0.2, 1.12), haft=(-0.45, -0.05, 0.89), edge=(-1.0, 0.0, 0.0),
                gripR=0.07, handL=(0.06 - 0.16 * math.cos(theta), 0.36, 0.8), poleR=(-1.0, -0.6, -0.3))


ANIMS = {
    "spoczynek": dict(frames=[breathing(i, 4) for i in range(4)], durations=[220] * 4, loop=True, events={}),
    "chod": dict(frames=[walking(i, 8) for i in range(8)], durations=[110] * 8, loop=True,
                 root_speed_mps=round(4 * 0.22 / 0.88, 2), events={}),
    "ciecie": dict(
        frames=[KEYS["gotowosc"], mix(KEYS["gotowosc"], KEYS["ciecie_zamach"], 0.55), KEYS["ciecie_zamach"],
                pose(**{**KEYS["ciecie_zamach"], "knob": (0.08, -0.31, 1.23), "spine": (-43.0, 6.0, 0.0)}),
                KEYS["ciecie_trafienie"], KEYS["ciecie_koniec"], mix(KEYS["ciecie_koniec"], KEYS["gotowosc"], 0.5), KEYS["gotowosc"]],
        durations=[100, 120, 160, 200, 70, 80, 150, 150], loop=False,
        events=dict(parowalny=True, zapowiedz=[1, 2, 3], aktywne=[4, 5], trafienie=4, okazja=[5, 6])),
    "rozlupanie": dict(
        frames=[KEYS["gotowosc"], mix(KEYS["gotowosc"], KEYS["rozlupanie"], 0.5), KEYS["rozlupanie"],
                pose(**{**KEYS["rozlupanie"], "pelvis": (0.0, 0.0, 0.96), "spine": (0.0, -8.0, 0.0)}),
                KEYS["rozlupanie_cios"], KEYS["rozlupanie_wbite"], KEYS["rozlupanie_wyrywa"],
                pose(**{**KEYS["rozlupanie_wyrywa"], "spine": (0.0, 24.0, 5.0), "knob": (0.24, -0.02, 0.88)}),
                KEYS["rozlupanie_wyrwane"], KEYS["gotowosc"]],
        durations=[100, 140, 220, 240, 60, 90, 260, 260, 160, 140], loop=False,
        events=dict(parowalny=False, zapowiedz=[1, 2, 3], sygnal=[2, 3, 4, 5], aktywne=[4, 5], trafienie=5, okazja=[6, 7, 8])),
    "trafienie": dict(frames=[mix(KEYS["gotowosc"], KEYS["trafiony"], 0.6), KEYS["trafiony"], mix(KEYS["trafiony"], KEYS["gotowosc"], 0.5)],
                      durations=[70, 140, 160], loop=False, events={}),
    "smierc": dict(
        frames=[KEYS["trafiony"], KEYS["umiera_kolana"], KEYS["umiera_kleczy"], mix(KEYS["umiera_kleczy"], KEYS["umiera_pada"], 0.5),
                KEYS["umiera_pada"], mix(KEYS["umiera_pada"], KEYS["umiera_lezy"], 0.6), KEYS["umiera_lezy"],
                pose(**{**KEYS["umiera_lezy"], "head": (25.0, 25.0), "pelvis": (0.12, 0.0, 0.28)})],
        durations=[120, 130, 150, 140, 150, 160, 200, 600], loop=False,
        events=dict(ostatnia_klatka="zostaje jako zwłoki")),
}


if __name__ == "__main__":
    charId = "drwal" + ("" if variant_of([a[2:] for a in sys.argv]) == "a" else "-" + variant_of([a[2:] for a in sys.argv]))
    if len(sys.argv) > 1 and sys.argv[1] == "anim":
        run_anim(charId, __file__, sys.argv[2:])
    else:
        run_cli(charId, __file__)
