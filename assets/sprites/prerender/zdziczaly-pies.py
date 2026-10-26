"""ENM-zdziczaly-pies: wychudzony, porzucony pies. Poza zapowiedzi "Skok do gardla" (przysiad, uszy do tylu, kly).

Uzycie: python3 zdziczaly-pies.py [poza|all] [kierunek 0-7|all] [--flaga]
Wynik: output/zdziczaly-pies/zdziczaly-pies_<poza>_<n>_<kierunek>.png oraz arkusz 8 kierunkow.

Wybor wykonawczy do potwierdzenia przez autora: to zwierze (nie ozywieniec, nie "magiczny wilk"); demoniczny odczyt
daje sylwetka, ciemne futro i bursztynowe oczy. Zaschnieta krew tylko na pysku i piersi, bez ran.
Karta: docs/bestiariusz-demo.md (ENM-zdziczaly-pies): niski wychudzony korpus, zerwany rzemien obrozy, jasna latka.
Uklad: x do przodu psa, y w lewo, z w gore; metry; lapy na z = 0.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sdfkit import Model, Prim, chain, frame_from_axes, normalize, run_cli, value_noise  # noqa: E402

# Pozy: wszystkie stawy w jednym miejscu. Nowa poza / klatka animacji = nowy wpis, model bez zmian.
POSES = {
    # zapowiedz Skoku do gardla: przycupniety, przednie lapy wysuniete, tylne skulone, szczeka rozwarta
    "zapowiedz": dict(
        foreL=((0.27, 0.1, 0.36), (0.19, 0.115, 0.17), (0.4, 0.115, 0.09), (0.45, 0.115, 0.045)),
        hindL=((-0.4, 0.105, 0.44), (-0.24, 0.14, 0.27), (-0.5, 0.125, 0.12), (-0.38, 0.125, 0.04)),
        neck=((0.36, 0, 0.44), (0.56, 0, 0.36)),
        head=(0.64, 0, 0.335),
        jaw=((0.7, 0, 0.265), (0.84, 0, 0.18)),   # dolna szczeka: rozwarcie
        tail=((-0.55, 0, 0.43), (-0.72, 0, 0.4), (-0.86, 0, 0.3)),
    ),
}

FUR, FUR_DARK, SKIN, MOUTH, TEETH, CLAW, LEATHER, EYES, PATCH = range(9)

MATERIALS = {
    FUR: dict(alb=(0.036, 0.028, 0.021), spec=0.06, pw=6, grit=1.3),         # skolatane, wyblakle futro
    FUR_DARK: dict(alb=(0.026, 0.021, 0.017), spec=0.04, pw=4, grit=1.0),    # brzuch, wnetrza uszu
    SKIN: dict(alb=(0.04, 0.028, 0.026), spec=0.2, pw=14, grit=0.5),         # nos, wargi
    MOUTH: dict(alb=(0.05, 0.012, 0.012), spec=0.25, pw=12, grit=0.4),       # jama pyska
    TEETH: dict(alb=(0.24, 0.2, 0.14), spec=0.3, pw=16, grit=0.5),           # kly
    CLAW: dict(alb=(0.03, 0.026, 0.022), spec=0.4, pw=30, grit=0.3),         # pazury
    LEATHER: dict(alb=(0.07, 0.044, 0.025), spec=0.15, pw=10, grit=0.6),     # obroza, zerwany rzemien
    EYES: dict(alb=(0.0, 0.0, 0.0), spec=0.0, pw=1, grit=0.0, emit=(1.6, 0.8, 0.16)),  # jedyny cieply punkt
    PATCH: dict(alb=(0.3, 0.25, 0.18), spec=0.05, pw=5, grit=1.1),           # jasna latka na grzbiecie
}


def leg(model, joints, radii, paw, side):
    pts = [[x, y * side, z] for x, y, z in joints]
    model.group(0.03, chain(pts, radii, FUR), disp=(0.006, 30))
    px, py, pz = pts[-1]
    model.group(0.02, [Prim("ellipsoid", FUR_DARK, c=[px + paw, py, pz - 0.005], radii=[0.06, 0.03, 0.022])])
    model.group(0.0, [Prim("cone", CLAW, a=[px + paw + 0.04, py + s * 0.012, pz - 0.01],
                           b=[px + paw + 0.085, py + s * 0.016, pz - 0.022], r1=0.007, r2=0.002) for s in (-1, 0, 1)])


def build(pose):
    model = Model()
    # tulow: wychudzony, zebra widoczne, garb kregoslupa i biodra
    torso = [Prim("ellipsoid", FUR, c=[0.24, 0, 0.40], radii=[0.19, 0.12, 0.17]),
             Prim("ellipsoid", FUR, c=[0.02, 0, 0.40], radii=[0.24, 0.115, 0.16]),
             Prim("ellipsoid", FUR, c=[-0.2, 0, 0.40], radii=[0.15, 0.095, 0.13]),
             Prim("ellipsoid", FUR, c=[-0.42, 0, 0.43], radii=[0.17, 0.12, 0.16])]
    model.group(0.09, torso, disp=(0.008, 26))
    model.group(0.04, [Prim("sphere", FUR, c=[-0.38, s * 0.1, 0.53], r=0.045) for s in (1, -1)] +
                [Prim("sphere", FUR, c=[-0.1 + 0.07 * i, 0, 0.545 - 0.01 * (i % 2)], r=0.032) for i in range(6)],
                disp=(0.004, 40))
    model.group(0.05, [Prim("ellipsoid", FUR_DARK, c=[0.02, 0, 0.3], radii=[0.28, 0.1, 0.08])])

    # kark, glowa niska, pysk rozwarty
    nA, nB = (np.array(v, float) for v in pose["neck"])
    hc = np.array(pose["head"], float)
    jA, jB = (np.array(v, float) for v in pose["jaw"])
    model.group(0.06, [Prim("cone", FUR, a=nA, b=nB, r1=0.11, r2=0.08),
                       Prim("ellipsoid", FUR, c=hc, radii=[0.125, 0.092, 0.086]),
                       Prim("cone", SKIN, a=hc + [0.06, 0, -0.01], b=hc + [0.22, 0, -0.045], r1=0.066, r2=0.044)], disp=(0.005, 36))
    model.group(0.03, [Prim("cone", FUR_DARK, a=jA, b=jB, r1=0.038, r2=0.026)])
    mouthC = (jA + jB) / 2 + [0, 0, 0.03]
    model.group(0.0, [Prim("ellipsoid", MOUTH, c=mouthC, radii=[0.065, 0.036, 0.036])])
    model.group(0.0, [Prim("sphere", SKIN, c=hc + [0.25, 0, -0.043], r=0.028)])
    fangs = []
    for s in (1, -1):
        fangs.append(Prim("cone", TEETH, a=hc + [0.19, s * 0.035, -0.065], b=hc + [0.195, s * 0.035, -0.145], r1=0.011, r2=0.002))
        fangs.append(Prim("cone", TEETH, a=jB + [-0.02, s * 0.03, 0.02], b=jB + [-0.015, s * 0.03, 0.08], r1=0.01, r2=0.002))
    fangs += [Prim("cone", TEETH, a=hc + [0.12 + 0.02 * i, s * 0.034, -0.06], b=hc + [0.122 + 0.02 * i, s * 0.034, -0.095], r1=0.005, r2=0.001)
              for s in (1, -1) for i in range(2)]
    model.group(0.0, fangs)
    model.group(0.0, [Prim("sphere", EYES, c=hc + [0.085, s * 0.066, 0.035], r=0.014) for s in (1, -1)])
    # uszy przylozone do karku
    for s in (1, -1):
        model.group(0.02, [Prim("cone", FUR_DARK, a=hc + [-0.04, s * 0.06, 0.065], b=hc + [-0.17, s * 0.1, 0.065], r1=0.034, r2=0.008)])

    # zerwana obroza: pierscien na karku i luzny rzemien
    neckDir = normalize(nB - nA)
    ringC = nA + (nB - nA) * 0.45 + [0, 0, -0.02]
    model.group(0.0, [Prim("torus", LEATHER, c=ringC, R=frame_from_axes(np.cross(neckDir, [0, 1, 0]), [0, 1, 0], neckDir),
                           major=0.098, minor=0.011)])
    model.group(0.01, chain([ringC + [0.01, 0.1, 0], ringC + [0.05, 0.115, -0.1], ringC + [0.07, 0.11, -0.2]], [0.011, 0.01, 0.007], LEATHER))

    # nogi: lewe z pozy, prawe lustrzane (y -> -y)
    for side in (1, -1):
        leg(model, pose["foreL"], [0.062, 0.042, 0.03, 0.028], 0.05, side)
        leg(model, pose["hindL"], [0.1, 0.06, 0.036, 0.03], 0.05, side)

    # ogon nisko, sztywny
    model.group(0.03, chain([list(p) for p in pose["tail"]], [0.04, 0.028, 0.012], FUR), disp=(0.005, 30))
    return model


def make_hook(flags):
    def hook(matId, pts, nrm, grain, albedo, spec, emit):
        if matId == FUR:
            blotch = value_noise(pts * 14 + 1.3)
            albedo = albedo * (0.7 + 0.6 * blotch)[:, None]
            # jasna latka na grzbiecie (miedzy lopatkami a krzyzem)
            on_back = np.clip((pts[:, 2] - 0.44) * 14, 0, 1) * np.clip(1 - np.abs(pts[:, 0] - 0.1) * 5.5, 0, 1) * np.clip(1 - np.abs(pts[:, 1]) * 9, 0, 1)
            patchColor = np.array(MATERIALS[PATCH]["alb"])
            albedo = albedo * (1 - on_back[:, None]) + patchColor[None, :] * on_back[:, None]
            # zaschnieta krew na pysku i piersi
            blood = np.clip((pts[:, 0] - 0.74) * 12, 0, 1) * np.clip((value_noise(pts * 20) - 0.3) * 4, 0, 1)
            chest = np.clip(1 - np.linalg.norm(pts - np.array([0.38, 0.04, 0.3]), axis=1) * 9, 0, 1) * np.clip((value_noise(pts * 17 + 4) - 0.3) * 3, 0, 1)
            both = np.maximum(blood, chest)
            albedo = albedo * (1 - both[:, None]) + np.array([0.06, 0.008, 0.007])[None, :] * both[:, None]
        return albedo, spec, emit
    return hook


if __name__ == "__main__":
    run_cli("zdziczaly-pies", __file__)
