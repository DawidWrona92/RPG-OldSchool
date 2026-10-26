"""ENM-korzeniec: przyroda zawlaszczajaca ludzkie slady. Prerender SDF, kamera Diablo 2.

Uzycie: python3 korzeniec.py [poza|all] [kierunek 0-7|all] [--wariant=b|c]
        python3 korzeniec.py anim [nazwa|all] [--szkic] [--wariant=b|c]

Wybor wykonawczy do potwierdzenia przez autora: to nie duch niematerialny, lecz ozywiony karl
kosny — "upiornosc" wynika z sylwetki i ruchu korzeni. Oczy pod kora to sygnal "zycia" (slaby,
mtny blask); karta postaci ich nie wymienia — do decyzji autora. Skrawek lnianej tkaniny tkwiacy
w korze to jedyny slad czlowieka; interpretacja pozostaje domyslem, zgodnie z karta.
Oba ataki nieparowalne: Zagarniecie (dlugi, stozkowy) i Przetoczenie (krotki, boczny).
Karta: docs/bestiariusz-demo.md (ENM-korzeniec): niski, szeroki kadlub; dlugie przednie korzenie
jak ramiona; przed wykryciem wyraznie porusza sie i oddycha; po chybieniu powoli sklada konczyny.
Uklad: x do przodu postaci, y w lewo, z w gore; metry; konczyki korzeni przy z ~ 0.
Zasieg: przy ziemi ku kamerze <= ~1,05 m (klatka ucina ponizej -1,6 m ekranu).
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sdfkit import Model, Prim, Sub, chain, normalize, run_anim, run_cli, value_noise  # noqa: E402


# ---------- pozy ----------
# Wszystkie pozy maja komplet kluczy (takze tilt i hot), zeby _mix nie gubil parametrow.
# Korzenie podane z DODATNIMI y po obu stronach; build() odbija strona side=-1 (jedno odbicie).
def _pose(rootFL, rootFR, rootHL, rootHR, breath=0.0, tilt=0.0, hot=False, lean=0.0):
    """rootFL/F R: 4 stawy przedniego korzenia (x, |y|, z); rootHL/HR: 3 stawy tylnego."""
    return dict(rootFL=rootFL, rootFR=rootFR, rootHL=rootHL, rootHR=rootHR,
                breath=breath, tilt=tilt, hot=hot, lean=lean)


POSES = {
    # spoczynek: korzenie przy kadlubie; oddech kadluba wyrazny (karta: "wyraznie sie porusza")
    "spoczynek": _pose(
        rootFL=((0.42, 0.3, 0.6), (0.68, 0.34, 0.42), (0.86, 0.36, 0.18), (0.92, 0.36, 0.04)),
        rootFR=((0.42, 0.28, 0.6), (0.66, 0.3, 0.42), (0.84, 0.32, 0.18), (0.9, 0.32, 0.04)),
        rootHL=((-0.5, 0.34, 0.44), (-0.66, 0.36, 0.22), (-0.74, 0.36, 0.04)),
        rootHR=((-0.5, 0.3, 0.44), (-0.64, 0.32, 0.22), (-0.72, 0.32, 0.04)),
    ),
    "oddech_gora": _pose(
        rootFL=((0.42, 0.3, 0.62), (0.68, 0.34, 0.44), (0.86, 0.36, 0.2), (0.92, 0.36, 0.06)),
        rootFR=((0.42, 0.28, 0.62), (0.66, 0.3, 0.44), (0.84, 0.32, 0.2), (0.9, 0.32, 0.06)),
        rootHL=((-0.5, 0.34, 0.46), (-0.66, 0.36, 0.24), (-0.74, 0.36, 0.06)),
        rootHR=((-0.5, 0.3, 0.46), (-0.64, 0.32, 0.24), (-0.72, 0.32, 0.06)),
        breath=0.04,
    ),
    # ---------- Zagarniecie (nieparowalne, dlugie) ----------
    "zagarniecie_napiecie": _pose(
        rootFL=((0.44, 0.32, 0.66), (0.78, 0.42, 0.54), (1.0, 0.46, 0.38), (1.06, 0.46, 0.32)),
        rootFR=((0.44, 0.3, 0.66), (0.76, 0.38, 0.54), (0.98, 0.42, 0.38), (1.04, 0.42, 0.32)),
        rootHL=((-0.52, 0.36, 0.48), (-0.7, 0.4, 0.26), (-0.78, 0.4, 0.06)),
        rootHR=((-0.52, 0.32, 0.48), (-0.68, 0.36, 0.26), (-0.76, 0.36, 0.06)),
        breath=0.03, hot=True,
    ),
    "zagarniecie_zapowiedz": _pose(
        rootFL=((0.46, 0.34, 0.7), (0.86, 0.48, 0.58), (1.1, 0.54, 0.46), (1.16, 0.54, 0.42)),
        rootFR=((0.46, 0.32, 0.7), (0.84, 0.44, 0.58), (1.08, 0.5, 0.46), (1.14, 0.5, 0.42)),
        rootHL=((-0.55, 0.38, 0.5), (-0.74, 0.42, 0.28), (-0.82, 0.42, 0.06)),
        rootHR=((-0.55, 0.34, 0.5), (-0.72, 0.38, 0.28), (-0.8, 0.38, 0.06)),
        breath=0.05, hot=True,
    ),
    "zagarniecie_cios": _pose(
        rootFL=((0.48, 0.28, 0.56), (0.82, 0.36, 0.32), (1.02, 0.4, 0.1), (1.06, 0.4, 0.04)),
        rootFR=((0.48, 0.26, 0.56), (0.8, 0.32, 0.32), (1.0, 0.36, 0.1), (1.04, 0.36, 0.04)),
        rootHL=((-0.55, 0.4, 0.48), (-0.76, 0.44, 0.22), (-0.85, 0.44, 0.04)),
        rootHR=((-0.55, 0.36, 0.48), (-0.74, 0.4, 0.22), (-0.83, 0.4, 0.04)),
        breath=0.0, hot=True,
    ),
    "zagarniecie_powrot": _pose(
        rootFL=((0.45, 0.3, 0.56), (0.74, 0.36, 0.38), (0.94, 0.4, 0.16), (1.0, 0.4, 0.04)),
        rootFR=((0.45, 0.28, 0.56), (0.72, 0.32, 0.38), (0.92, 0.36, 0.16), (0.98, 0.36, 0.04)),
        rootHL=((-0.52, 0.36, 0.46), (-0.7, 0.4, 0.24), (-0.78, 0.4, 0.05)),
        rootHR=((-0.52, 0.32, 0.46), (-0.68, 0.36, 0.24), (-0.76, 0.36, 0.05)),
        breath=0.01,
    ),
    # ---------- Przetoczenie (nieparowalne, krotkie, boczne): ciezark przenosi sie na lewa strone,
    # prawy korzen smyka szeroko po ziemi w bok — kara za ciagle obchodzenie ----------
    "przetoczenie_napiecie": _pose(
        rootFL=((0.42, 0.3, 0.6), (0.68, 0.36, 0.44), (0.88, 0.44, 0.2), (0.94, 0.48, 0.05)),
        rootFR=((0.42, 0.28, 0.6), (0.66, 0.32, 0.44), (0.86, 0.38, 0.2), (0.92, 0.4, 0.05)),
        rootHL=((-0.5, 0.34, 0.44), (-0.66, 0.36, 0.22), (-0.74, 0.36, 0.04)),
        rootHR=((-0.5, 0.3, 0.44), (-0.64, 0.32, 0.22), (-0.72, 0.32, 0.04)),
        breath=0.03, tilt=0.05, hot=True,
    ),
    "przetoczenie_cios": _pose(
        rootFL=((0.4, 0.32, 0.54), (0.6, 0.46, 0.36), (0.72, 0.66, 0.14), (0.76, 0.74, 0.04)),
        rootFR=((0.4, 0.3, 0.54), (0.58, 0.42, 0.36), (0.7, 0.6, 0.14), (0.74, 0.66, 0.04)),
        rootHL=((-0.48, 0.34, 0.4), (-0.62, 0.36, 0.18), (-0.7, 0.36, 0.04)),
        rootHR=((-0.48, 0.3, 0.4), (-0.6, 0.32, 0.18), (-0.68, 0.32, 0.04)),
        breath=-0.02, tilt=0.1, lean=0.1, hot=True,
    ),
    "przetoczenie_powrot": _pose(
        rootFL=((0.42, 0.3, 0.58), (0.66, 0.4, 0.42), (0.82, 0.5, 0.18), (0.86, 0.54, 0.04)),
        rootFR=((0.42, 0.28, 0.58), (0.64, 0.36, 0.42), (0.8, 0.44, 0.18), (0.84, 0.46, 0.04)),
        rootHL=((-0.5, 0.34, 0.44), (-0.66, 0.36, 0.22), (-0.74, 0.36, 0.04)),
        rootHR=((-0.5, 0.3, 0.44), (-0.64, 0.32, 0.22), (-0.72, 0.32, 0.04)),
        breath=0.0, tilt=0.03,
    ),
    # ---------- trafienie / smierc ----------
    "trafiony": _pose(
        rootFL=((0.4, 0.28, 0.54), (0.64, 0.32, 0.38), (0.82, 0.34, 0.16), (0.88, 0.34, 0.05)),
        rootFR=((0.4, 0.26, 0.54), (0.62, 0.28, 0.38), (0.8, 0.3, 0.16), (0.86, 0.3, 0.05)),
        rootHL=((-0.48, 0.32, 0.4), (-0.64, 0.34, 0.2), (-0.72, 0.34, 0.05)),
        rootHR=((-0.48, 0.28, 0.4), (-0.62, 0.3, 0.2), (-0.7, 0.3, 0.05)),
        breath=-0.05, tilt=-0.1,
    ),
    "umiera_kleczy": _pose(
        rootFL=((0.36, 0.26, 0.36), (0.54, 0.28, 0.24), (0.66, 0.3, 0.1), (0.7, 0.3, 0.04)),
        rootFR=((0.36, 0.24, 0.36), (0.52, 0.26, 0.24), (0.64, 0.28, 0.1), (0.68, 0.28, 0.04)),
        rootHL=((-0.44, 0.28, 0.24), (-0.56, 0.3, 0.12), (-0.62, 0.3, 0.04)),
        rootHR=((-0.44, 0.24, 0.24), (-0.54, 0.26, 0.12), (-0.6, 0.26, 0.04)),
        breath=-0.18, tilt=-0.16,
    ),
    "umiera_lezy": _pose(
        rootFL=((0.3, 0.22, 0.14), (0.44, 0.24, 0.06), (0.54, 0.26, 0.02), (0.58, 0.26, 0.02)),
        rootFR=((0.3, 0.2, 0.14), (0.42, 0.22, 0.06), (0.52, 0.24, 0.02), (0.56, 0.24, 0.02)),
        rootHL=((-0.4, 0.22, 0.1), (-0.5, 0.24, 0.04), (-0.56, 0.24, 0.02)),
        rootHR=((-0.4, 0.18, 0.1), (-0.48, 0.2, 0.04), (-0.54, 0.2, 0.02)),
        breath=-0.3, tilt=-0.2,
    ),
}


def _mix(a, b, t):
    """Przejscie miedzy pozami: interpoluje tylko klucz wspólne obu poza parametrami domyslnymi."""
    out = {}
    for key in set(a) | set(b):
        va, vb = a.get(key, 0.0), b.get(key, 0.0)
        if isinstance(va, (tuple, list)) and isinstance(va[0], (tuple, list)):
            out[key] = tuple(tuple(x + (y - x) * t for x, y in zip(ja, jb)) for ja, jb in zip(va, vb))
        elif isinstance(va, bool):
            out[key] = va or vb
        else:
            out[key] = va * (1 - t) + vb * t
    return out


# ---------- warianty (zeby w lesie nie bylo klonow) ----------
WARIANTY = {
    "a": dict(bark=(1.0, 1.0, 1.0), wide=1.0, rag=1.0, eye=(0.35, 0.5, 0.3), seed=0.0, hump=1.0),
    "b": dict(bark=(1.2, 1.05, 0.8), wide=1.12, rag=1.3, eye=(0.45, 0.4, 0.25), seed=5.3, hump=1.3),
    "c": dict(bark=(0.75, 0.9, 0.7), wide=0.92, rag=0.7, eye=(0.3, 0.45, 0.35), seed=11.7, hump=0.7),
}
WARIANT = "a"
for _arg in sys.argv[1:]:
    if _arg.startswith("--wariant=") and _arg.split("=")[1] in WARIANTY:
        WARIANT = _arg.split("=")[1]
V = WARIANTY[WARIANT]

BARK, BARK_DARK, WOOD_IN, LINEN, EYES, ROOT_TIP, ROOT_TIP_HOT = range(7)

MATERIALS = {
    BARK:         dict(alb=tuple(np.array((0.072, 0.055, 0.038)) * np.array(V["bark"])), spec=0.08, pw=8, grit=1.4),
    BARK_DARK:    dict(alb=tuple(np.array((0.05, 0.04, 0.03)) * np.array(V["bark"])), spec=0.06, pw=6, grit=1.2),
    WOOD_IN:      dict(alb=(0.16, 0.12, 0.072), spec=0.12, pw=10, grit=0.9),
    LINEN:        dict(alb=(0.2, 0.185, 0.15), spec=0.04, pw=5, grit=0.8),
    EYES:         dict(alb=(0.0, 0.0, 0.0), spec=0.0, pw=1, grit=0.0, emit=V["eye"]),
    ROOT_TIP:     dict(alb=(0.13, 0.1, 0.06), spec=0.14, pw=12, grit=0.7),
    ROOT_TIP_HOT: dict(alb=(0.13, 0.1, 0.06), spec=0.14, pw=12, grit=0.7),
}


def build(pose):
    model = Model()
    breath = pose.get("breath", 0.0)
    tilt = pose.get("tilt", 0.0)
    lean = pose.get("lean", 0.0)
    hot = pose.get("hot", False)
    tipMat = ROOT_TIP_HOT if hot else ROOT_TIP
    wide = V["wide"]

    # ---------- kadlub: niski, SZEROKI kopiec z korze (szerszy niz wyzszy) ----------
    trunk = [Prim("ellipsoid", BARK, c=[0.02 + tilt * 0.3, 0, 0.5], radii=[0.5, 0.68 * wide, 0.42]),
             Prim("ellipsoid", BARK, c=[-0.04, 0, 0.72], radii=[0.42, 0.55 * wide, 0.3])]
    model.group(0.05, trunk, disp=(0.012, 26))
    # garb na grzbiecie
    model.group(0.04, [Prim("ellipsoid", BARK_DARK, c=[-0.16 + tilt, 0, 0.86 + breath * 0.5],
                            radii=[0.24 * V["hump"], 0.34 * wide, 0.2 * V["hump"]])], disp=(0.01, 30))

    # wezel "glowy" — nisko nad kadlubem, z przodu; oczodoly zapadniete pod kora
    headC = np.array([0.34 + tilt * 0.5 + lean * 0.2, 0, 0.82 + breath * 0.4])
    headBulge = [Prim("ellipsoid", BARK, c=headC, radii=[0.2, 0.21, 0.18]),
                 Prim("ellipsoid", BARK_DARK, c=headC + [0.06, 0, -0.06], radii=[0.13, 0.14, 0.13])]
    sockets = [Prim("sphere", BARK_DARK, c=headC + [0.17, s * 0.07, 0.0], r=0.045) for s in (1, -1)]
    model.group(0.02, [Sub(headBulge[0], sockets, smooth=0.03),
                       Sub(headBulge[1], sockets, smooth=0.03)], disp=(0.006, 34))
    model.group(0.0, [Prim("sphere", EYES, c=headC + [0.19, s * 0.07, 0.01], r=0.018) for s in (1, -1)])

    # skrawek lnianej tkaniny tkwiacy w korze (rekwizyt karty; grubość >= 3 px w 1x)
    ragBand = Prim("box", LINEN, c=[0.02, 0.3 * wide, 0.66], R=np.eye(3),
                   half=[0.025 * V["rag"], 0.09 * V["rag"], 0.07 * V["rag"]], round=0.005)
    rag = Sub(ragBand, [Prim("sphere", LINEN, c=[0.02, 0.3 * wide, 0.57], r=0.06),
                        Prim("sphere", LINEN, c=[0.02, 0.36 * wide, 0.75], r=0.04)])
    model.group(0.0, [rag])

    # ---------- korzenie: PRZEDNIE ramiona i TYLNE zakotwiczenia, po OBU stronach ----------
    for key, side in (("rootFL", 1), ("rootFR", -1), ("rootHL", 1), ("rootHR", -1)):
        joints = [np.array([x, y * side, z], float) for x, y, z in pose[key]]
        if key.startswith("rootF"):
            radii = [0.1, 0.08, 0.06, 0.045]
            shoulder = joints[0]
            model.group(0.04, [Prim("sphere", BARK_DARK, c=shoulder, r=0.11),
                               Prim("ellipsoid", BARK_DARK, c=shoulder + np.array([-0.05, 0, 0.02]),
                                    radii=[0.13, 0.11, 0.1])], disp=(0.008, 28))
            model.group(0.03, chain(joints, radii, BARK), disp=(0.01, 22))
            model.group(0.02, chain(joints[1:], radii[1:], WOOD_IN), disp=(0.008, 22))
            tipDir = normalize(joints[-1] - joints[-2])
            model.group(0.0, [Prim("cone", tipMat, a=joints[-1], b=joints[-1] + tipDir * 0.12,
                                   r1=0.05, r2=0.016)])
        else:
            model.group(0.035, chain(joints, [0.12, 0.09, 0.07], BARK_DARK), disp=(0.01, 24))

    return model


ANIMS = {
    # oddech: pelny cykl 0 -> 0.5 -> 1 -> 0.5 (bez szarpniecia)
    "spoczynek": dict(frames=[POSES["spoczynek"],
                              _mix(POSES["spoczynek"], POSES["oddech_gora"], 0.5),
                              POSES["oddech_gora"],
                              _mix(POSES["spoczynek"], POSES["oddech_gora"], 0.5)],
                      durations=[600, 600, 600, 600], loop=True, events={}),
    # Zagarniecie: nieparowalny, dlugi atak stozkowy; 3 klatki zapowiedzi
    "zagarniecie": dict(
        frames=[POSES["spoczynek"],
                _mix(POSES["spoczynek"], POSES["zagarniecie_napiecie"], 0.5),
                POSES["zagarniecie_napiecie"],
                POSES["zagarniecie_zapowiedz"],
                _mix(POSES["zagarniecie_zapowiedz"], POSES["zagarniecie_cios"], 0.5),
                POSES["zagarniecie_cios"],
                POSES["zagarniecie_powrot"],
                _mix(POSES["zagarniecie_powrot"], POSES["spoczynek"], 0.5),
                POSES["spoczynek"]],
        durations=[280, 220, 260, 300, 110, 140, 320, 280, 280], loop=False,
        events=dict(parowalny=False, zapowiedz=[1, 2, 3], aktywne=[4, 5], trafienie=5, okazja=[6, 7])),
    # Przetoczenie: nieparowalny, krotki atak boczny przeciw obchodzeniu
    "przetoczenie": dict(
        frames=[POSES["spoczynek"],
                _mix(POSES["spoczynek"], POSES["przetoczenie_napiecie"], 0.6),
                POSES["przetoczenie_napiecie"],
                _mix(POSES["przetoczenie_napiecie"], POSES["przetoczenie_cios"], 0.5),
                POSES["przetoczenie_cios"],
                POSES["przetoczenie_powrot"],
                _mix(POSES["przetoczenie_powrot"], POSES["spoczynek"], 0.5),
                POSES["spoczynek"]],
        durations=[200, 180, 220, 90, 120, 260, 220, 200], loop=False,
        events=dict(parowalny=False, zapowiedz=[1, 2, 3], aktywne=[4, 5], trafienie=5, okazja=[6])),
    "trafienie": dict(frames=[_mix(POSES["spoczynek"], POSES["trafiony"], 0.6), POSES["trafiony"],
                              _mix(POSES["trafiony"], POSES["spoczynek"], 0.5)],
                      durations=[90, 180, 200], loop=False, events={}),
    "smierc": dict(frames=[POSES["trafiony"],
                           _mix(POSES["trafiony"], POSES["umiera_kleczy"], 0.5),
                           POSES["umiera_kleczy"],
                           _mix(POSES["umiera_kleczy"], POSES["umiera_lezy"], 0.5),
                           POSES["umiera_lezy"],
                           _mix(POSES["umiera_lezy"], POSES["umiera_lezy"], 0.0)],
                   durations=[140, 160, 200, 220, 260, 700], loop=False,
                   events=dict(ostatnia_klatka="kadlub osiada i zostaje jako kopiec korzeni")),
}


def make_hook(flags):
    signal = "bez-sygnalu" not in flags

    def hook(matId, pts, nrm, grain, albedo, spec, emit):
        if matId in (BARK, BARK_DARK, WOOD_IN, ROOT_TIP, ROOT_TIP_HOT):
            groove = np.clip((value_noise(pts * 13 + 1.3 + V["seed"]) - 0.55) * 4.0, 0, 1) * np.clip(abs(nrm[:, 1]) * 2.2, 0, 1)
            albedo = albedo * (1.0 - 0.5 * groove[:, None])
            moss = np.clip((value_noise(pts * 9 + 5.0 + V["seed"]) - 0.58) * 4.0, 0, 1) * np.clip(nrm[:, 2] * 1.4, 0, 1)
            albedo = albedo * (1 - moss[:, None]) + np.array([0.03, 0.05, 0.022])[None, :] * moss[:, None]
        if matId == LINEN:
            rot = np.clip((value_noise(pts * 20 + 3.0) - 0.5) * 3.0, 0, 1)
            albedo = albedo * (1 - 0.4 * rot[:, None])
        if matId == ROOT_TIP_HOT and signal:
            emit = emit + np.array([1.6, 0.18, 0.05])[None, :] * (0.7 + 0.3 * grain[:, None])
        return albedo, spec, emit

    return hook


if __name__ == "__main__":
    charId = "korzeniec" + ("" if WARIANT == "a" else "-" + WARIANT)
    if len(sys.argv) > 1 and sys.argv[1] == "anim":
        run_anim(charId, __file__, sys.argv[2:])
    else:
        run_cli(charId, __file__)
