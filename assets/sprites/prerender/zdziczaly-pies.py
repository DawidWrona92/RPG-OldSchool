"""ENM-zdziczaly-pies: wychudzony, porzucony pies. Szkielet z IK, 7 animacji z karty bestiariusza, 3 warianty wygladu.

Uzycie:
  python3 zdziczaly-pies.py anim [nazwa|all] [--wariant=b|c] [--szkic]   atlas PNG + JSON + GIF w output/zdziczaly-pies[-b|-c]/
  python3 zdziczaly-pies.py <poza|all> [kierunek 0-7|all] [--wariant=b]  pojedyncze pozy kluczowe z POSES
Format wyniku i kontrakt kadru: README.md oraz .agents/skills/welesza-sprites/SKILL.md.

Wybor wykonawczy do potwierdzenia przez autora: to zwierze (nie ozywieniec, nie "magiczny wilk"). Demoniczny odczyt daje
sylwetka i ciemne futro; oczy maja tylko slaby odblask (EYE_GLOW = 0.3, decyzja autora). Zaschnieta krew tylko na pysku i
piersi, bez ran. Karta: docs/bestiariusz-demo.md (ENM-zdziczaly-pies): niski wychudzony korpus, zerwany rzemien obrozy,
jasna latka widoczna w ciemnym futrze; zapowiedzi: przysiad, uszy do tylu, warkot (skok), odsuniecie lba i kly (kapniecie).
Ataki zwierzecia sa nieparowalne (parowalny: False) i nie maja sygnalu czerwieni — zapowiedz czyta sie z ruchu.

Uklad: x do przodu psa, y w lewo, z w gore; metry; lapy na z = 0.
Poza = polozenie piersi i zadu (kregoslup), glowa (pozycja, pochylenie, rozwarcie szczeki), uszy (0 = polozone, 1 = postawione),
ogon i cele czterech lap (x, z); stawy lap liczy dwuczlonowe IK. mix(a, b, t) interpoluje pozy.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sdfkit import Model, Prim, frame_from_axes, normalize, run_anim, run_cli, value_noise  # noqa: E402

FUR, FUR_DARK, SKIN, MOUTH, TEETH, CLAW, LEATHER, EYES, PATCH = range(9)

EYE_GLOW = 0.3   # mnoznik blasku oczu: slaby odblask zwierzecia (decyzja autora; 1.0 = mocne bursztynowe oczy z pierwszego renderu)

# ---------- warianty: zeby w grze nie bylo klonow ----------
# scale: wzrost (+-5%); fur: mnoznik albedo futra; lean: grubosc korpusu i konczyn; head: skala glowy; ear_l/ear_r: dlugosc
# ucha; tail: dlugosc ogona; patch: jasna latka na grzbiecie (s0 = polozenie od zadu [m], ws/wl = rozmiar, broken = poszarpanie);
# seed: przesuniecie szumu (inny wzor plam); blood: ilosc zaschnietej krwi; mange: lysiny.
# Sylwetka z karty zostaje w kazdym: niski wychudzony korpus, obroza z zerwanym rzemieniem, jasna latka na grzbiecie.
VARIANTS = {
    "a": dict(scale=1.0, fur=(1.0, 1.0, 1.0), lean=1.0, head=1.0, ear_l=1.0, ear_r=1.0, tail=1.0, seed=0.0, blood=1.0,
              mange=0.0, patch=dict(s0=0.52, ws=0.15, wl=0.07, broken=0.0), eye=(1.6, 0.8, 0.16)),
    "b": dict(scale=0.95, fur=(1.3, 1.25, 1.2), lean=0.92, head=0.95, ear_l=0.45, ear_r=1.0, tail=0.45, seed=5.3, blood=0.5,
              mange=0.0, patch=dict(s0=0.1, ws=0.15, wl=0.1, broken=0.5), eye=(1.3, 1.0, 0.3)),
    "c": dict(scale=1.05, fur=(1.15, 0.85, 0.7), lean=1.1, head=1.08, ear_l=1.0, ear_r=1.0, tail=1.25, seed=11.7, blood=1.0,
              mange=0.8, patch=dict(s0=0.58, ws=0.085, wl=0.19, broken=0.0), eye=(1.5, 0.7, 0.12)),
}


def variant_of(flags):
    for flag in flags:
        if flag.startswith("wariant="):
            return flag.split("=", 1)[1]
    return "a"


MATERIALS = {
    FUR: dict(alb=(0.064, 0.05, 0.037), spec=0.06, pw=6, grit=1.3),          # skolatane, wyblakle futro
    FUR_DARK: dict(alb=(0.046, 0.037, 0.029), spec=0.04, pw=4, grit=1.0),    # brzuch, wnetrza uszu
    SKIN: dict(alb=(0.05, 0.035, 0.032), spec=0.2, pw=14, grit=0.5),         # nos, wargi
    MOUTH: dict(alb=(0.05, 0.012, 0.012), spec=0.25, pw=12, grit=0.4),       # jama pyska
    TEETH: dict(alb=(0.26, 0.22, 0.16), spec=0.3, pw=16, grit=0.5),          # kly
    CLAW: dict(alb=(0.04, 0.034, 0.028), spec=0.4, pw=30, grit=0.3),         # pazury
    LEATHER: dict(alb=(0.13, 0.085, 0.05), spec=0.15, pw=10, grit=0.6),      # obroza, zerwany rzemien (jasniejsze: rekwizyt)
    EYES: dict(alb=(0.0, 0.0, 0.0), spec=0.0, pw=1, grit=0.0, emit=(1.6, 0.8, 0.16)),   # jedyny cieply punkt
    PATCH: dict(alb=(0.40, 0.34, 0.25), spec=0.05, pw=5, grit=1.1),          # jasna latka na grzbiecie
}

# ---------- szkielet i pozy ----------
FORE_L1, FORE_L2 = 0.206, 0.225      # lopatka -> lokiec -> nadgarstek
HIND_L1, HIND_L2 = 0.233, 0.30       # biodro -> kolano -> skok (staw skokowy)
TAIL_BASE = [(-0.13, 0.0), (-0.30, -0.03), (-0.44, -0.13)]   # odsuniecia (x, z) od zadu
GROUND = 0.045                       # z srodka lapy na ziemi


def _ik(top, tip, l1, l2, bend):
    """Dwuczlonowe IK w plaszczyznie x-z: zwraca (staw posredni, koniec) dla celu `tip`."""
    d = np.array([tip[0] - top[0], tip[1] - top[1]], float)
    dist = max(float(np.hypot(*d)), 1e-6)
    reach = l1 + l2 - 1e-3
    if dist > reach:
        d, dist = d * reach / dist, reach
    a = (l1 * l1 - l2 * l2 + dist * dist) / (2 * dist)
    h = math.sqrt(max(l1 * l1 - a * a, 0.0))
    mid = np.array(top, float) + d * (a / dist)
    joint = mid + np.array([-d[1], d[0]]) / dist * h * bend
    return joint, np.array(top, float) + d


def pose(chest=(0.24, 0.40), rump=(-0.42, 0.43), arch=0.0, head=(0.64, 0.335), pitch=0.0, open=0.9, ear=0.0,
         feet=None, legs=None, tail=None, roll=0.0):
    """Zbiera pozycje wszystkich czesci. feet: paw FL/FR/HL/HR jako (x, z) -> IK; legs: gotowe stawy (nadpisuja)."""
    c, r = np.array([chest[0], 0.0, chest[1]]), np.array([rump[0], 0.0, rump[1]])
    spine = [c, r + (c - r) * (2 / 3) + [0, 0, arch], r + (c - r) * (1 / 3) + [0, 0, arch], r]   # piers, srodek, talia, zad
    out = dict(spine=spine, head=np.array([head[0], 0.0, head[1]]), pitch=pitch, open=open, ear=ear, roll=roll,
               tail=[(r + [dx, 0, dz]) for dx, dz in (tail or TAIL_BASE)])
    legs = dict(legs or {})
    for name, paw in (feet or {}).items():
        side = 1 if name.endswith("L") else -1
        if name in legs:
            continue
        if name[0] == "F":
            sh = c + [0.03, side * 0.10, -0.04]
            elbow, wrist = _ik((sh[0], sh[2]), (paw[0] - 0.05, paw[1] + 0.045), FORE_L1, FORE_L2, -1)
            legs[name] = [sh, np.array([elbow[0], side * 0.115, elbow[1]]), np.array([wrist[0], side * 0.115, wrist[1]]),
                          np.array([paw[0], side * 0.115, paw[1]])]
        else:
            hip = r + [0.02, side * 0.105, 0.01]
            knee, hock = _ik((hip[0], hip[2]), (paw[0] - 0.12, paw[1] + 0.08), HIND_L1, HIND_L2, 1)
            legs[name] = [hip, np.array([knee[0], side * 0.14, knee[1]]), np.array([hock[0], side * 0.125, hock[1]]),
                          np.array([paw[0], side * 0.125, paw[1]])]
    out["legs"] = legs
    return out


def mix(a, b, t):
    """Interpolacja dwoch poz: kregoslup, glowa, ogon, stawy lap i liczby liniowo."""
    out = {}
    for key, va in a.items():
        vb = b[key]
        if key == "legs":
            out[key] = {n: [x + (y - x) * t for x, y in zip(va[n], vb[n])] for n in va}
        elif key in ("spine", "tail"):
            out[key] = [x + (y - x) * t for x, y in zip(va, vb)]
        elif isinstance(va, np.ndarray):
            out[key] = va + (vb - va) * t
        else:
            out[key] = va + (vb - va) * t
    return out


def _mirror(joints):
    return [np.array([x, -y, z], float) for x, y, z in joints]


def _stand(fl=0.30, fr=0.34, hl=-0.34, hr=-0.30):
    return dict(FL=(fl, GROUND), FR=(fr, GROUND), HL=(hl, GROUND), HR=(hr, GROUND))


GAIT_AMP, GAIT_LIFT = 0.2, 0.12


def _gait(p, x0f=0.33, x0h=-0.30):
    """Klus: FL i HR w fazie p, FR i HL w fazie p+0.5. p w [0,1): 0 = kontakt z przodu, 0.25 = podparcie,
    0.5 = odbicie, 0.75 = przenoszenie."""
    def foot(x0, ph):
        s = ph % 1.0
        if s < 0.5:
            return (x0 + GAIT_AMP - 2 * GAIT_AMP * (s / 0.5), GROUND)
        t = (s - 0.5) / 0.5
        return (x0 - GAIT_AMP + 2 * GAIT_AMP * t, GROUND + GAIT_LIFT * math.sin(math.pi * t))
    return dict(FL=foot(x0f, p), HR=foot(x0h, p), FR=foot(x0f, p + 0.5), HL=foot(x0h, p + 0.5))


def running(i, count):
    p = i / count
    bob = 0.015 * math.cos(2 * math.pi * 2 * p + math.pi)
    return pose(chest=(0.26, 0.43 + bob), rump=(-0.40, 0.45 + bob), head=(0.74, 0.33 + 0.01 * math.cos(4 * math.pi * p)),
                pitch=0.1, open=0.5, ear=0.7, feet=_gait(p), tail=[(-0.13, 0.02), (-0.30, 0.02), (-0.46, 0.0)])


# zapowiedz Skoku do gardla (zaakceptowana poza z pierwszego renderu): stawy podane recznie
_ZAP_FORE = [(0.27, 0.1, 0.36), (0.19, 0.115, 0.17), (0.4, 0.115, 0.09), (0.45, 0.115, 0.045)]
_ZAP_HIND = [(-0.4, 0.105, 0.44), (-0.24, 0.14, 0.27), (-0.5, 0.125, 0.12), (-0.38, 0.125, 0.04)]

# Pozy kluczowe. Uszy: 0 = polozone (celowy sygnal zapowiedzi), >0.5 = postawione (czuwanie, bieg).
KEYS = {
    "zapowiedz": pose(legs=dict(FL=[np.array(j, float) for j in _ZAP_FORE], FR=_mirror(_ZAP_FORE),
                                HL=[np.array(j, float) for j in _ZAP_HIND], HR=_mirror(_ZAP_HIND))),
    "skok_wybicie": pose(chest=(0.30, 0.46), rump=(-0.38, 0.40), head=(0.74, 0.46), pitch=-0.1, open=1.0, ear=0.0,
                         feet=dict(FL=(0.62, 0.30), FR=(0.56, 0.26), HL=(-0.62, GROUND), HR=(-0.58, GROUND)),
                         tail=[(-0.14, 0.02), (-0.3, 0.06), (-0.45, 0.1)]),
    "skok_lot": pose(chest=(0.26, 0.78), rump=(-0.34, 0.70), head=(0.72, 0.84), pitch=-0.2, open=1.0, ear=0.0,
                     feet=dict(FL=(0.66, 0.62), FR=(0.62, 0.58), HL=(-0.64, 0.52), HR=(-0.6, 0.5)),
                     tail=[(-0.14, 0.03), (-0.3, 0.08), (-0.46, 0.14)]),
    "skok_ladowanie": pose(chest=(0.30, 0.30), rump=(-0.36, 0.46), head=(0.72, 0.28), pitch=0.3, open=0.5, ear=0.0,
                           feet=dict(FL=(0.62, GROUND), FR=(0.58, GROUND), HL=(-0.1, GROUND), HR=(-0.06, GROUND))),
    "klapniecie_zapowiedz": pose(chest=(0.18, 0.40), rump=(-0.42, 0.36), arch=0.06, head=(0.40, 0.50), pitch=-0.35, open=1.0,
                                 ear=0.0, feet=_stand(fl=0.22, fr=0.26, hl=-0.26, hr=-0.22),
                                 tail=[(-0.13, 0.04), (-0.28, 0.12), (-0.40, 0.2)]),
    "klapniecie": pose(chest=(0.38, 0.38), rump=(-0.32, 0.42), head=(0.86, 0.34), pitch=0.3, open=0.25, ear=0.1,
                       feet=_stand(fl=0.56, fr=0.50, hl=-0.18, hr=-0.12)),   # wypad <= ~1,1 m od srodka (cien w klatce)
    "odzyskanie_a": pose(chest=(0.30, 0.28), rump=(-0.36, 0.38), head=(0.70, 0.20), pitch=0.5, open=0.1, ear=0.4,
                         feet=dict(FL=(0.56, GROUND), FR=(0.50, GROUND), HL=(-0.16, GROUND), HR=(-0.12, GROUND))),
    "odzyskanie_b": pose(chest=(0.26, 0.44), rump=(-0.40, 0.45), head=(0.62, 0.40), pitch=0.1, open=0.5, ear=0.6,
                         feet=_stand(fl=0.34, fr=0.30, hl=-0.30, hr=-0.34)),
    "czuwanie_a": pose(chest=(0.26, 0.47), rump=(-0.40, 0.47), head=(0.62, 0.40), pitch=0.25, open=0.2, ear=0.85, feet=_stand()),
    "czuwanie_b": pose(chest=(0.26, 0.455), rump=(-0.40, 0.47), head=(0.63, 0.385), pitch=0.3, open=0.28, ear=0.8,
                       feet=_stand(fl=0.34, fr=0.32), tail=[(-0.13, 0.0), (-0.30, -0.06), (-0.43, -0.17)]),
    "trafienie": pose(chest=(0.22, 0.44), rump=(-0.44, 0.44), head=(0.56, 0.52), pitch=-0.5, open=0.8, ear=0.9,
                      feet=_stand(fl=0.34, fr=0.28, hl=-0.40, hr=-0.34), tail=[(-0.13, 0.02), (-0.28, 0.1), (-0.4, 0.2)]),
    "smierc_a": pose(chest=(0.26, 0.28), rump=(-0.40, 0.30), head=(0.62, 0.20), pitch=0.45, open=0.3, ear=0.3,
                     feet=dict(FL=(0.40, GROUND), FR=(0.30, GROUND), HL=(-0.20, GROUND), HR=(-0.50, GROUND))),
    "smierc_b": pose(chest=(0.26, 0.40), rump=(-0.40, 0.40), head=(0.64, 0.30), pitch=0.3, open=0.4, ear=0.2, roll=math.pi / 2,
                     feet=dict(FL=(0.42, 0.12), FR=(0.36, 0.16), HL=(-0.30, 0.12), HR=(-0.36, 0.14)),
                     tail=[(-0.13, 0.0), (-0.3, -0.04), (-0.44, -0.1)]),
}
KEYS["smierc_c"] = pose(chest=(0.26, 0.40), rump=(-0.40, 0.40), head=(0.64, 0.25), pitch=0.45, open=0.2, ear=0.1, roll=math.pi / 2,
                        feet=dict(FL=(0.40, 0.10), FR=(0.34, 0.14), HL=(-0.32, 0.10), HR=(-0.38, 0.12)),
                        tail=[(-0.13, 0.0), (-0.3, -0.05), (-0.44, -0.08)])
K = KEYS
POSES = {**KEYS, **{f"bieg_{i}": running(i, 8) for i in range(8)}}    # dla `python3 zdziczaly-pies.py <poza> <kierunek>`


def _idle_cycle():
    a, b = K["czuwanie_a"], K["czuwanie_b"]
    return [a, mix(a, b, 0.5), b, mix(a, b, 0.5)]


ANIMS = {
    "czuwanie": dict(frames=_idle_cycle(), durations=[300] * 4, loop=True, events={}),
    "bieg": dict(frames=[running(i, 8) for i in range(8)], durations=[70] * 8, loop=True,
                 root_speed_mps=round(4 * GAIT_AMP / 0.56, 2), events={}),
    # Skok do gardla: przysiad narasta 3 klatki (uszy do tylu, warkot), skok po stalym torze, ladowanie i odzyskanie rownowagi.
    "skok_do_gardla": dict(
        frames=[mix(K["czuwanie_a"], K["zapowiedz"], 0.35), mix(K["czuwanie_a"], K["zapowiedz"], 0.7), K["zapowiedz"],
                K["skok_wybicie"], mix(K["skok_wybicie"], K["skok_lot"], 0.6), K["skok_lot"], K["skok_ladowanie"],
                mix(K["skok_ladowanie"], K["odzyskanie_a"], 0.5)],
        durations=[180, 180, 200, 80, 110, 180, 140, 220], loop=False,
        events=dict(parowalny=False, zapowiedz=[0, 1, 2], aktywne=[4, 5], trafienie=5, okazja=[6, 7])),
    # Klapniecie: odsuniecie lba i odsloniecie klow, krotki wypad, powrot.
    "klapniecie": dict(
        frames=[mix(K["czuwanie_a"], K["klapniecie_zapowiedz"], 0.5), K["klapniecie_zapowiedz"],
                mix(K["klapniecie_zapowiedz"], K["klapniecie"], 0.5), K["klapniecie"], mix(K["klapniecie"], K["czuwanie_a"], 0.5)],
        durations=[140, 260, 60, 90, 200], loop=False,
        events=dict(parowalny=False, zapowiedz=[0, 1], aktywne=[3], trafienie=3, okazja=[4])),
    "odzyskanie": dict(
        frames=[K["odzyskanie_a"], mix(K["odzyskanie_a"], K["odzyskanie_b"], 0.5), K["odzyskanie_b"],
                mix(K["odzyskanie_b"], K["czuwanie_a"], 0.5)],
        durations=[300, 200, 200, 200], loop=False, events={}),
    "trafienie": dict(frames=[mix(K["czuwanie_a"], K["trafienie"], 0.6), K["trafienie"], mix(K["trafienie"], K["czuwanie_a"], 0.5)],
                      durations=[60, 140, 160], loop=False, events={}),
    "smierc": dict(
        frames=[K["trafienie"], mix(K["trafienie"], K["smierc_a"], 0.5), K["smierc_a"], mix(K["smierc_a"], K["smierc_b"], 0.4),
                mix(K["smierc_a"], K["smierc_b"], 0.75), K["smierc_b"], K["smierc_c"]],
        durations=[100, 120, 150, 150, 160, 200, 700], loop=False, events=dict(ostatnia_klatka="zostaje jako zwłoki")),
}

_ANCH = {}


def build(pose, flags=()):
    V = VARIANTS[variant_of(flags)]
    roll = float(pose["roll"])
    cr, sr = math.cos(roll), math.sin(roll)
    M = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])
    pivot, lying = np.array([0, 0, 0.40]), np.array([0, 0, 0.14 if roll else 0.40])

    def W(p):
        p = np.asarray(p, float)
        return M @ (p - pivot) + lying if roll else p

    def sph(m, c, r):
        return Prim("sphere", m, c=W(c), r=r)

    def cone(m, a, b, r1, r2):
        return Prim("cone", m, a=W(a), b=W(b), r1=r1, r2=r2)

    def ell(m, c, radii):
        return Prim("ellipsoid", m, c=W(c), radii=radii, R=M)

    def chn(pts, radii, m):
        return [cone(m, pts[i], pts[i + 1], radii[i], radii[i + 1]) for i in range(len(pts) - 1)]

    lean, hs = V["lean"], V["head"]
    chest, mid, waist, rump = pose["spine"]
    model = Model(clip_ground=bool(roll), scale=V["scale"])

    # tulow: wychudzony, zebra widoczne, garb kregoslupa i biodra
    model.group(0.09, [ell(FUR, chest, [0.19, 0.12 * lean, 0.17 * lean]),
                       ell(FUR, mid, [0.24, 0.115 * lean, 0.16 * lean]),
                       ell(FUR, waist, [0.15, 0.095 * lean, 0.13 * lean]),
                       ell(FUR, rump, [0.17, 0.12 * lean, 0.16 * lean])], disp=(0.008, 26))
    ridge = [sph(FUR, rump + (chest - rump) * t + [0, 0, 0.145 * lean], 0.032) for t in (0.3, 0.42, 0.54, 0.66, 0.78, 0.9)]
    model.group(0.04, [sph(FUR, rump + [0.04, s * 0.1 * lean, 0.1], 0.045) for s in (1, -1)] + ridge, disp=(0.004, 40))
    model.group(0.05, [ell(FUR_DARK, mid + [0, 0, -0.1], [0.28, 0.1 * lean, 0.08])])

    # kark, glowa (obrot o `pitch`), pysk rozwarty
    hc = pose["head"]
    ph = pose["pitch"]
    cp, sp = math.cos(ph), math.sin(ph)

    def H(dx, dy, dz):
        return hc + np.array([dx * cp + dz * sp, dy, -dx * sp + dz * cp])

    nA, nB = chest + [0.12, 0, 0.04], H(-0.08, 0, 0.025)
    model.group(0.06, [cone(FUR, nA, nB, 0.11 * lean, 0.08 * lean),
                       ell(FUR, hc, [0.125 * hs, 0.092 * hs, 0.086 * hs]),
                       cone(SKIN, H(0.06, 0, -0.01), H(0.22, 0, -0.045), 0.066 * hs, 0.044 * hs)], disp=(0.005, 36))
    opn = float(pose["open"])
    jA, jB = H(0.06, 0, -0.07), H(0.20, 0, -0.065 - 0.1 * opn)
    model.group(0.03, [cone(FUR_DARK, jA, jB, 0.038 * hs, 0.026 * hs)])
    model.group(0.0, [ell(MOUTH, (jA + jB) / 2 + [0, 0, 0.03], [0.065, 0.036, 0.036])])
    model.group(0.0, [sph(SKIN, H(0.25, 0, -0.043), 0.028 * hs)])
    fangs = []
    for s in (1, -1):
        fangs.append(cone(TEETH, H(0.19, s * 0.035, -0.065), H(0.195, s * 0.035, -0.065 - 0.04 - 0.04 * opn), 0.012, 0.002))
        fangs.append(cone(TEETH, jB + [-0.02, s * 0.03, 0.02], jB + [-0.015, s * 0.03, 0.02 + 0.04 + 0.02 * opn], 0.011, 0.002))
    fangs += [cone(TEETH, H(0.12 + 0.02 * i, s * 0.034, -0.06), H(0.122 + 0.02 * i, s * 0.034, -0.095), 0.006, 0.001)
              for s in (1, -1) for i in range(2)]
    model.group(0.0, fangs)
    model.group(0.0, [sph(EYES, H(0.085, s * 0.066, 0.035), 0.014) for s in (1, -1)])
    # uszy: ear 0 = przylozone do karku, 1 = postawione; dlugosc z wariantu (lewe ucho wariantu b jest kulawe)
    e = float(pose["ear"])
    for s, k in ((1, V["ear_l"]), (-1, V["ear_r"])):
        flat, perk = np.array([-0.17, s * 0.1, 0.065]), np.array([-0.03, s * 0.07, 0.21])
        base, tip = np.array([-0.03, s * 0.055, 0.06]), (1 - e) * flat + e * perk
        model.group(0.02, [cone(FUR_DARK, H(*base), H(*(base + (tip - base) * k)), 0.05, 0.012 + 0.014 * (1 - k))])

    # zerwana obroza: pierscien na karku i dlugi luzny rzemien (stale w kazdym wariancie: rekwizyt z karty, >= 3 px w 1x)
    neckDir = normalize(M @ (nB - nA)) if roll else normalize(nB - nA)
    ringC = nA + (nB - nA) * 0.45 + [0, 0, -0.02]
    model.group(0.0, [Prim("torus", LEATHER, c=W(ringC), R=frame_from_axes(np.cross(neckDir, [0, 1, 0]), [0, 1, 0], neckDir),
                           major=0.1 * lean, minor=0.022)])
    strap = [ringC + [0.01, 0.1, 0], ringC + [0.05, 0.12, -0.12], ringC + [0.08, 0.12, -0.24]]
    model.group(0.01, chn(strap, [0.024, 0.022, 0.016], LEATHER))

    # nogi: konczyny ponizej stawu nie cienszej niz ~0,035 m
    for name, joints in pose["legs"].items():
        radii = [0.062, 0.045, 0.04, 0.036] if name[0] == "F" else [0.1, 0.062, 0.042, 0.038]
        radii = [r * (lean if i < 2 else 1.0) for i, r in enumerate(radii)]
        model.group(0.03, chn(joints, radii, FUR), disp=(0.006, 30))
        px, py, pz = joints[-1]
        model.group(0.02, [ell(FUR_DARK, [px + 0.05, py, pz - 0.005], [0.065, 0.034, 0.025])])
        model.group(0.0, [cone(CLAW, [px + 0.09, py + s * 0.012, pz - 0.01], [px + 0.135, py + s * 0.016, pz - 0.022], 0.008, 0.002)
                          for s in (-1, 0, 1)])

    # ogon (dlugosc z wariantu)
    base = pose["tail"][0]
    tailPts = [base + (p - base) * V["tail"] for p in pose["tail"]]
    model.group(0.03, chn(tailPts, [0.045, 0.032, 0.015], FUR), disp=(0.005, 30))

    # punkty odniesienia do latek i krwi (w ukladzie modelu po obrocie)
    _ANCH.update(chest=W(chest), rump=W(rump), head=W(hc), up=(M @ [0, 0, 1]) if roll else np.array([0, 0, 1.0]),
                 fwd=W(H(1, 0, 0)) - W(H(0, 0, 0)), chestBlood=W(chest + [0.14, 0.04, -0.1]))
    return model


def make_hook(flags):
    V = VARIANTS[variant_of(flags)]
    tone = np.array(V["fur"])
    P = V["patch"]
    seed = V["seed"]
    eye = np.array(V["eye"]) * EYE_GLOW

    def hook(matId, pts, nrm, grain, albedo, spec, emit):
        if matId == EYES:
            return albedo, spec, np.tile(eye, (len(pts), 1))
        if matId in (FUR, FUR_DARK):
            blotch = value_noise(pts * 14 + 1.3 + seed)
            albedo = albedo * (0.7 + 0.6 * blotch)[:, None] * tone[None, :]
        if matId == FUR:
            A = _ANCH
            axis = normalize(A["chest"] - A["rump"])
            length = float(np.linalg.norm(A["chest"] - A["rump"]))
            d = pts - A["rump"]
            s = d @ axis
            lateral = np.cross(A["up"], axis)
            lat = d @ lateral
            top = nrm @ A["up"]
            # jasna latka na grzbiecie: polozenie, rozmiar i "poszarpanie" zaleza od wariantu
            mask = np.exp(-(((s - P["s0"]) / P["ws"]) ** 2) - (lat / P["wl"]) ** 2) * np.clip((top - 0.2) * 3, 0, 1)
            if P["broken"] > 0:
                mask = mask * np.clip((value_noise(pts * 22 + 3.1 + seed) - P["broken"] * 0.6) * 5, 0, 1)
            patchColor = np.array(MATERIALS[PATCH]["alb"])
            albedo = albedo * (1 - mask[:, None]) + patchColor[None, :] * mask[:, None]
            # lysiny (wariant c): jasniejsza, gola skora na bokach
            if V["mange"] > 0:
                flank = np.clip(np.abs(lat) * 9 - 0.6, 0, 1) * np.clip(1 - np.abs(s - length * 0.5) / (length * 0.45), 0, 1)
                bald = np.clip((value_noise(pts * 7 + 9.1 + seed) - 0.62) * 8, 0, 1) * flank * V["mange"]
                albedo = albedo * (1 - bald[:, None]) + np.array([0.09, 0.065, 0.058])[None, :] * bald[:, None]
            # zaschnieta krew: pysk i piers
            fwd = normalize(A["fwd"])
            muzzle = np.clip(((pts - A["head"]) @ fwd - 0.12) * 12, 0, 1) * np.clip((value_noise(pts * 20 + seed) - 0.3) * 4, 0, 1)
            chestB = np.clip(1 - np.linalg.norm(pts - A["chestBlood"], axis=1) * 9, 0, 1) * np.clip((value_noise(pts * 17 + 4 + seed) - 0.3) * 3, 0, 1)
            both = np.maximum(muzzle, chestB) * V["blood"]
            albedo = albedo * (1 - both[:, None]) + np.array([0.07, 0.01, 0.009])[None, :] * both[:, None]
        return albedo, spec, emit
    return hook


if __name__ == "__main__":
    charId = "zdziczaly-pies" + ("" if variant_of([a[2:] for a in sys.argv]) == "a" else "-" + variant_of([a[2:] for a in sys.argv]))
    if len(sys.argv) > 1 and sys.argv[1] == "anim":
        run_anim(charId, __file__, sys.argv[2:])
    else:
        run_cli(charId, __file__)
