"""ENM-zdziczaly-pies: wychudzony, porzucony pies. Pozy animacji z karty bestiariusza i 3 warianty wygladu.

Uzycie: python3 zdziczaly-pies.py [poza|all] [kierunek 0-7|all] [--wb|--wc]
Warianty: bez flagi = wa (bazowy); --wb (szary, kulawe ucho, kikut ogona, latka na krzyzu); --wc (rudawo-czarny,
ciezszy, laty lysej skory, kolnierz z latki na lopatkach). Wynik: output/zdziczaly-pies/<id>_<poza>_<n>_<kierunek>[_wb].png.

Wybor wykonawczy do potwierdzenia przez autora: to zwierze (nie ozywieniec, nie "magiczny wilk"); demoniczny odczyt
daje sylwetka, ciemne futro i bursztynowe oczy. Zaschnieta krew tylko na pysku i piersi, bez ran.
Karta: docs/bestiariusz-demo.md (ENM-zdziczaly-pies): niski wychudzony korpus, zerwany rzemien obrozy, jasna latka.
Uklad: x do przodu psa, y w lewo, z w gore; metry; lapy na z = 0.

Pozy liczone z kosci: pozycje lap (x, z) -> dwuczlonowe IK, reszta (kregoslup, glowa, ogon, uszy) z parametrow.
Klatka animacji = nowy wpis w POSES; model sie nie zmienia. Animacje (kolejnosc klatek) w ANIMACJE.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sdfkit import Model, Prim, frame_from_axes, normalize, run_cli, value_noise  # noqa: E402

FUR, FUR_DARK, SKIN, MOUTH, TEETH, CLAW, LEATHER, EYES, PATCH = range(9)

# ---------- warianty: zeby w grze nie bylo klonow ----------
# fur: mnoznik albedo futra; lean: grubosc korpusu i konczyn; head: skala glowy; ear_l/ear_r: dlugosc ucha;
# tail: dlugosc ogona; patch: ksztalt jasnej latki (s0 = polozenie wzdluz grzbietu od zadu [m], ws/wl = szerokosc);
# seed: przesuniecie szumu (inny wzor plam); blood: ilosc zaschnietej krwi; mange: lysiny.
WARIANTY = {
    "wa": dict(fur=(1.0, 1.0, 1.0), lean=1.0, head=1.0, ear_l=1.0, ear_r=1.0, tail=1.0, seed=0.0, blood=1.0, mange=0.0,
               patch=dict(s0=0.52, ws=0.17, wl=0.07, broken=0.0), eye=(1.6, 0.8, 0.16)),
    "wb": dict(fur=(1.45, 1.38, 1.3), lean=0.9, head=0.95, ear_l=0.4, ear_r=1.0, tail=0.4, seed=5.3, blood=0.5, mange=0.0,
               patch=dict(s0=0.1, ws=0.13, wl=0.09, broken=0.5), eye=(1.3, 1.0, 0.3)),
    "wc": dict(fur=(1.15, 0.82, 0.66), lean=1.1, head=1.08, ear_l=1.0, ear_r=1.0, tail=1.25, seed=11.7, blood=1.0, mange=0.8,
               patch=dict(s0=0.58, ws=0.07, wl=0.17, broken=0.0), eye=(1.5, 0.7, 0.12)),
}
WARIANT = "wa"
for _arg in sys.argv[1:]:
    if _arg.startswith("--") and _arg[2:] in WARIANTY:
        WARIANT = _arg[2:]
V = WARIANTY[WARIANT]

MATERIALS = {
    FUR: dict(alb=(0.036, 0.028, 0.021), spec=0.06, pw=6, grit=1.3),         # skolatane, wyblakle futro
    FUR_DARK: dict(alb=(0.026, 0.021, 0.017), spec=0.04, pw=4, grit=1.0),    # brzuch, wnetrza uszu
    SKIN: dict(alb=(0.04, 0.028, 0.026), spec=0.2, pw=14, grit=0.5),         # nos, wargi
    MOUTH: dict(alb=(0.05, 0.012, 0.012), spec=0.25, pw=12, grit=0.4),       # jama pyska
    TEETH: dict(alb=(0.24, 0.2, 0.14), spec=0.3, pw=16, grit=0.5),           # kly
    CLAW: dict(alb=(0.03, 0.026, 0.022), spec=0.4, pw=30, grit=0.3),         # pazury
    LEATHER: dict(alb=(0.07, 0.044, 0.025), spec=0.15, pw=10, grit=0.6),     # obroza, zerwany rzemien
    EYES: dict(alb=(0.0, 0.0, 0.0), spec=0.0, pw=1, grit=0.0, emit=V["eye"]),  # jedyny cieply punkt
    PATCH: dict(alb=(0.3, 0.25, 0.18), spec=0.05, pw=5, grit=1.1),           # jasna latka na grzbiecie
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
            wrist_target = (paw[0] - 0.05, paw[1] + 0.045)
            elbow, wrist = _ik((sh[0], sh[2]), wrist_target, FORE_L1, FORE_L2, -1)
            legs[name] = [sh, np.array([elbow[0], side * 0.115, elbow[1]]), np.array([wrist[0], side * 0.115, wrist[1]]),
                          np.array([paw[0], side * 0.115, paw[1]])]
        else:
            hip = r + [0.02, side * 0.105, 0.01]
            hock_target = (paw[0] - 0.12, paw[1] + 0.08)
            knee, hock = _ik((hip[0], hip[2]), hock_target, HIND_L1, HIND_L2, 1)
            legs[name] = [hip, np.array([knee[0], side * 0.14, knee[1]]), np.array([hock[0], side * 0.125, hock[1]]),
                          np.array([paw[0], side * 0.125, paw[1]])]
    out["legs"] = legs
    return out


def _mirror(joints):
    return [np.array([x, -y, z], float) for x, y, z in joints]


def _stand(fl=0.30, fr=0.34, hl=-0.34, hr=-0.30):
    return dict(FL=(fl, GROUND), FR=(fr, GROUND), HL=(hl, GROUND), HR=(hr, GROUND))


def _gait(p, x0f=0.33, x0h=-0.30, amp=0.16, lift=0.09):
    """Klus: FL i HR w fazie p, FR i HL w fazie p+0.5. p w [0,1): 0 = kontakt z przodu, 0.25 = podparcie, 0.5 = odbicie, 0.75 = przenoszenie."""
    def foot(x0, ph):
        s = ph % 1.0
        if s < 0.5:
            return (x0 + amp - 2 * amp * (s / 0.5), GROUND)
        t = (s - 0.5) / 0.5
        return (x0 - amp + 2 * amp * t, GROUND + lift * math.sin(math.pi * t))
    return dict(FL=foot(x0f, p), HR=foot(x0h, p), FR=foot(x0f, p + 0.5), HL=foot(x0h, p + 0.5))


# zapowiedz Skoku do gardla (zaakceptowana poza z pierwszego renderu): stawy podane recznie
_ZAP_FORE = [(0.27, 0.1, 0.36), (0.19, 0.115, 0.17), (0.4, 0.115, 0.09), (0.45, 0.115, 0.045)]
_ZAP_HIND = [(-0.4, 0.105, 0.44), (-0.24, 0.14, 0.27), (-0.5, 0.125, 0.12), (-0.38, 0.125, 0.04)]

POSES = {
    # --- zapowiedz i atak (kolejnosc wazna: zapowiedz zawsze czytelna) ---
    "zapowiedz": pose(legs=dict(FL=[np.array(j, float) for j in _ZAP_FORE], FR=_mirror(_ZAP_FORE),
                                HL=[np.array(j, float) for j in _ZAP_HIND], HR=_mirror(_ZAP_HIND)), feet=dict(FL=0, FR=0, HL=0, HR=0)),
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
    "klapniecie": pose(chest=(0.42, 0.38), rump=(-0.30, 0.42), head=(1.0, 0.34), pitch=0.3, open=0.25, ear=0.0,
                       feet=_stand(fl=0.62, fr=0.56, hl=-0.16, hr=-0.10)),
    # --- po ataku ---
    "odzyskanie_a": pose(chest=(0.30, 0.28), rump=(-0.36, 0.38), head=(0.70, 0.20), pitch=0.5, open=0.1, ear=0.3,
                         feet=dict(FL=(0.56, GROUND), FR=(0.50, GROUND), HL=(-0.16, GROUND), HR=(-0.12, GROUND))),
    "odzyskanie_b": pose(chest=(0.26, 0.44), rump=(-0.40, 0.45), head=(0.62, 0.40), pitch=0.1, open=0.5, ear=0.2,
                         feet=_stand(fl=0.34, fr=0.30, hl=-0.30, hr=-0.34)),
    # --- spoczynek (pilnuje miejsca): warkot, glowa nisko ---
    "czuwanie_a": pose(chest=(0.26, 0.47), rump=(-0.40, 0.47), head=(0.62, 0.40), pitch=0.25, open=0.2, ear=0.2, feet=_stand()),
    "czuwanie_b": pose(chest=(0.26, 0.455), rump=(-0.40, 0.47), head=(0.63, 0.385), pitch=0.3, open=0.28, ear=0.15,
                       feet=_stand(fl=0.34, fr=0.32), tail=[(-0.13, 0.0), (-0.30, -0.06), (-0.43, -0.17)]),
    # --- bieg / obiegniecie celu (4 klatki petli) ---
    **{f"bieg_{i}": pose(chest=(0.26, 0.43 + 0.015 * math.cos(2 * math.pi * 2 * (i / 4) + math.pi)),
                         rump=(-0.40, 0.45 + 0.015 * math.cos(2 * math.pi * 2 * (i / 4) + math.pi)),
                         head=(0.74, 0.33 + 0.01 * math.cos(2 * math.pi * 2 * (i / 4))), pitch=0.1, open=0.5, ear=0.0,
                         feet=_gait(i / 4, amp=0.2, lift=0.12),
                         tail=[(-0.13, 0.02), (-0.30, 0.02), (-0.46, 0.0)]) for i in range(4)},
    # --- trafienie i smierc ---
    "trafienie": pose(chest=(0.22, 0.44), rump=(-0.44, 0.44), head=(0.56, 0.52), pitch=-0.5, open=0.8, ear=0.0,
                      feet=_stand(fl=0.34, fr=0.28, hl=-0.40, hr=-0.34), tail=[(-0.13, 0.02), (-0.28, 0.1), (-0.4, 0.2)]),
    "smierc_a": pose(chest=(0.26, 0.28), rump=(-0.40, 0.30), head=(0.62, 0.20), pitch=0.45, open=0.3, ear=0.3,
                     feet=dict(FL=(0.40, GROUND), FR=(0.30, GROUND), HL=(-0.20, GROUND), HR=(-0.50, GROUND))),
    "smierc_b": pose(chest=(0.26, 0.40), rump=(-0.40, 0.40), head=(0.64, 0.30), pitch=0.3, open=0.4, ear=0.3, roll=math.pi / 2,
                     feet=dict(FL=(0.42, 0.12), FR=(0.36, 0.16), HL=(-0.30, 0.12), HR=(-0.36, 0.14)),
                     tail=[(-0.13, 0.0), (-0.3, -0.04), (-0.44, -0.1)]),
}

# Kolejnosc klatek i czasy [ms] w grze. loop = czy animacje zapetlac.
ANIMACJE = {
    "czuwanie": dict(klatki=["czuwanie_a", "czuwanie_b"], ms=[600, 600], loop=True),
    "bieg": dict(klatki=["bieg_0", "bieg_1", "bieg_2", "bieg_3"], ms=[90, 90, 90, 90], loop=True),
    "skok_do_gardla": dict(klatki=["zapowiedz", "skok_wybicie", "skok_lot", "skok_ladowanie"], ms=[500, 90, 260, 160], loop=False,
                           zapowiedz_ms=500),
    "klapniecie": dict(klatki=["klapniecie_zapowiedz", "klapniecie"], ms=[420, 120], loop=False, zapowiedz_ms=420),
    "odzyskanie": dict(klatki=["odzyskanie_a", "odzyskanie_b"], ms=[450, 350], loop=False),
    "trafienie": dict(klatki=["trafienie"], ms=[200], loop=False),
    "smierc": dict(klatki=["smierc_a", "smierc_b"], ms=[250, 1000], loop=False),
}

_ANCH = {}


def build(pose):
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
    model = Model()

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
    muzzleA, muzzleB = H(0.06, 0, -0.01), H(0.22, 0, -0.045)
    model.group(0.06, [cone(FUR, nA, nB, 0.11 * lean, 0.08 * lean),
                       ell(FUR, hc, [0.125 * hs, 0.092 * hs, 0.086 * hs]),
                       cone(SKIN, muzzleA, muzzleB, 0.066 * hs, 0.044 * hs)], disp=(0.005, 36))
    opn = float(pose["open"])
    jA, jB = H(0.06, 0, -0.07), H(0.20, 0, -0.065 - 0.1 * opn)
    model.group(0.03, [cone(FUR_DARK, jA, jB, 0.038 * hs, 0.026 * hs)])
    model.group(0.0, [ell(MOUTH, (jA + jB) / 2 + [0, 0, 0.03], [0.065, 0.036, 0.036])])
    model.group(0.0, [sph(SKIN, H(0.25, 0, -0.043), 0.028 * hs)])
    fangs = []
    for s in (1, -1):
        fangs.append(cone(TEETH, H(0.19, s * 0.035, -0.065), H(0.195, s * 0.035, -0.065 - 0.04 - 0.04 * opn), 0.011, 0.002))
        fangs.append(cone(TEETH, jB + [-0.02, s * 0.03, 0.02], jB + [-0.015, s * 0.03, 0.02 + 0.04 + 0.02 * opn], 0.01, 0.002))
    fangs += [cone(TEETH, H(0.12 + 0.02 * i, s * 0.034, -0.06), H(0.122 + 0.02 * i, s * 0.034, -0.095), 0.005, 0.001)
              for s in (1, -1) for i in range(2)]
    model.group(0.0, fangs)
    model.group(0.0, [sph(EYES, H(0.085, s * 0.066, 0.035), 0.014) for s in (1, -1)])
    # uszy: ear 0 = przylozone do karku, 1 = postawione; dlugosc z wariantu (lewe ucho wb jest kulawe)
    e = float(pose["ear"])
    for s, k in ((1, V["ear_l"]), (-1, V["ear_r"])):
        flat, perk = np.array([-0.17, s * 0.1, 0.065]), np.array([-0.03, s * 0.075, 0.2])
        base, tip = np.array([-0.04, s * 0.06, 0.065]), (1 - e) * flat + e * perk
        model.group(0.02, [cone(FUR_DARK, H(*base), H(*(base + (tip - base) * k)), 0.034, 0.008 + 0.012 * (1 - k))])

    # zerwana obroza: pierscien na karku i luzny rzemien (stale w kazdym wariancie: rekwizyt z karty)
    neckDir = normalize(M @ (nB - nA)) if roll else normalize(nB - nA)
    ringC = nA + (nB - nA) * 0.45 + [0, 0, -0.02]
    model.group(0.0, [Prim("torus", LEATHER, c=W(ringC), R=frame_from_axes(np.cross(neckDir, [0, 1, 0]), [0, 1, 0], neckDir),
                           major=0.098 * lean, minor=0.011)])
    strap = [ringC + [0.01, 0.1, 0], ringC + [0.05, 0.115, -0.1], ringC + [0.07, 0.11, -0.2]]
    model.group(0.01, chn(strap, [0.011, 0.01, 0.007], LEATHER))

    # nogi
    for name, joints in pose["legs"].items():
        radii = [0.062, 0.042, 0.03, 0.028] if name[0] == "F" else [0.1, 0.06, 0.036, 0.03]
        radii = [r * (lean if i < 2 else 1.0) for i, r in enumerate(radii)]
        model.group(0.03, chn(joints, radii, FUR), disp=(0.006, 30))
        px, py, pz = joints[-1]
        model.group(0.02, [ell(FUR_DARK, [px + 0.05, py, pz - 0.005], [0.06, 0.03, 0.022])])
        model.group(0.0, [cone(CLAW, [px + 0.09, py + s * 0.012, pz - 0.01], [px + 0.135, py + s * 0.016, pz - 0.022], 0.007, 0.002)
                          for s in (-1, 0, 1)])

    # ogon (dlugosc z wariantu)
    base = pose["tail"][0]
    tailPts = [base + (p - base) * V["tail"] for p in pose["tail"]]
    model.group(0.03, chn(tailPts, [0.04, 0.028, 0.012], FUR), disp=(0.005, 30))

    # punkty odniesienia do latek i krwi (w ukladzie modelu po obrocie)
    _ANCH.update(chest=W(chest), rump=W(rump), head=W(hc), up=(M @ [0, 0, 1]) if roll else np.array([0, 0, 1.0]),
                 fwd=W(H(1, 0, 0)) - W(H(0, 0, 0)), chestBlood=W(chest + [0.14, 0.04, -0.1]))
    return model


def make_hook(flags):
    tone = np.array(V["fur"])
    P = V["patch"]
    seed = V["seed"]

    def hook(matId, pts, nrm, grain, albedo, spec, emit):
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
            # jasna latka na grzbiecie: polozenie, szerokosc i "poszarpanie" zalezne od wariantu
            mask = np.exp(-(((s - P["s0"]) / P["ws"]) ** 2) - (lat / P["wl"]) ** 2) * np.clip((top - 0.2) * 3, 0, 1)
            if P["broken"] > 0:
                mask = mask * np.clip((value_noise(pts * 22 + 3.1 + seed) - P["broken"] * 0.6) * 5, 0, 1)
            patchColor = np.array(MATERIALS[PATCH]["alb"])
            albedo = albedo * (1 - mask[:, None]) + patchColor[None, :] * mask[:, None]
            # lysiny (wariant wc): jasniejsza, gola skora na bokach
            if V["mange"] > 0:
                flank = np.clip(np.abs(lat) * 9 - 0.6, 0, 1) * np.clip(1 - np.abs(s - length * 0.5) / (length * 0.45), 0, 1)
                bald = np.clip((value_noise(pts * 7 + 9.1 + seed) - 0.62) * 8, 0, 1) * flank * V["mange"]
                albedo = albedo * (1 - bald[:, None]) + np.array([0.075, 0.055, 0.05])[None, :] * bald[:, None]
            # zaschnieta krew: pysk i piers
            fwd = normalize(A["fwd"])
            muzzle = np.clip(((pts - A["head"]) @ fwd - 0.12) * 12, 0, 1) * np.clip((value_noise(pts * 20 + seed) - 0.3) * 4, 0, 1)
            chestB = np.clip(1 - np.linalg.norm(pts - A["chestBlood"], axis=1) * 9, 0, 1) * np.clip((value_noise(pts * 17 + 4 + seed) - 0.3) * 3, 0, 1)
            both = np.maximum(muzzle, chestB) * V["blood"]
            albedo = albedo * (1 - both[:, None]) + np.array([0.06, 0.008, 0.007])[None, :] * both[:, None]
        return albedo, spec, emit
    return hook


if __name__ == "__main__":
    run_cli("zdziczaly-pies", __file__)
