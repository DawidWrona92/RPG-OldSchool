"""Bohater Weleszy — główny bohater, zwykły podróżnik (~1,80 m), w nowym pipeline'u meshkit.

Tożsamość (z zlecenia): nie heros, nie wybraniec. Mężczyzna 30–40 lat, sprawna budowa,
zmęczony kilkudniową podróżą w deszczu. Ubiór: znoszona lniana koszula, ciemny kaftan,
krótki płaszcz podróżny z kapturem, skórzany pas, sakwa, ciemne spodnie, buty do wędrówki,
owijki, plecak z posłaniem. Broń startowa (propozycja): prosty jednoręczny miecz, zużyte żelazo.

Model: proceduralne siatki trójkątowe z prawidłową anatomią (7,5 głowy, szerokość barków
~2,3 głowy), szkielet z LBS, fałdy tkanin jako geometria (displacement na pierścieniach
i osobne "fałdowe" siatki na płaszczu/kaftanie). Kontrakt kadru zgodny z sdfkit.

Użycie:
  python3 bohater.py arkusz <poza>          # arkusz 8 kierunków + PNG (previews/)
  python3 bohater.py anim <nazwa|all>        # atlas PNG + GIF + JSON (atlas/)
  python3 bohater.py anim <nazwa> --szkic    # szybki podgląd 96 px, kierunek SE
  python3 bohater.py test                    # kontrola techniczna (kotwica, alfa, granice)
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from meshkit import (  # noqa: E402
    ANCHOR, DIRECTIONS, FRAME_SIZE, GROUND_RGB, Mesh, ShadowMap, Skeleton, auto_weights,
    compute_ao, cylinder_mesh, ellipsoid_mesh, box_mesh,
    fbm, ik2, loft_capped, render_frame, ring_pts, rotate_onto, value_noise,
    run_jobs, save_pose_sheet, skin_meshes, write_json,
    yaw_matrix,
)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "renders")
ATLAS = os.path.join(HERE, "..", "atlas")
PREVIEWS = os.path.join(HERE, "..", "previews")
for d in (OUT, ATLAS, PREVIEWS):
    os.makedirs(d, exist_ok=True)

# ---------- materiały (albedo liniowe, jak w sdfkit; paleta Weleszy) ----------

(SKIN, HAIR, SHIRT, KAFTAN, CAPE, TROUSERS, BOOTS, LEATHER, WRAP, WOOD, IRON, EDGE, BAG) = range(13)

MATERIALS = {
    SKIN:     dict(alb=(0.42, 0.315, 0.245), spec=0.10, pw=8,  grit=0.8),   # skóra, lekko tłusta, zmęczona
    HAIR:     dict(alb=(0.20, 0.16, 0.13),   spec=0.06, pw=6,  grit=1.0),   # ciemne, tłuste włosy
    SHIRT:    dict(alb=(0.40, 0.335, 0.245), spec=0.04, pw=5,  grit=1.1),   # znoszony len, brudny
    KAFTAN:   dict(alb=(0.34, 0.245, 0.155), spec=0.08, pw=7,  grit=1.0),   # ciemna wełna
    CAPE:     dict(alb=(0.26, 0.205, 0.16),  spec=0.05, pw=5,  grit=1.2),   # ciemniejszy, mokry płaszcz
    TROUSERS: dict(alb=(0.26, 0.215, 0.165), spec=0.04, pw=5,  grit=1.0),   # ciemna wełna
    BOOTS:    dict(alb=(0.28, 0.19, 0.125),  spec=0.18, pw=10, grit=0.9),   # skóra butów, lekki połysk
    LEATHER:  dict(alb=(0.33, 0.205, 0.115), spec=0.22, pw=12, grit=0.7),   # pas, rękawice, sakwa
    WRAP:     dict(alb=(0.36, 0.29, 0.20),   spec=0.05, pw=5,  grit=1.3),   # onuce lniane
    WOOD:     dict(alb=(0.36, 0.24, 0.14),   spec=0.12, pw=9,  grit=0.8),   # trzonek miecza
    IRON:     dict(alb=(0.28, 0.23, 0.20),   spec=0.45, pw=24, grit=1.1, specTint=0.5),  # zużyte żelazo
    EDGE:     dict(alb=(0.75, 0.75, 0.78),   spec=1.2,  pw=60, grit=0.4, specTint=0.6),  # krawędź
    BAG:      dict(alb=(0.30, 0.225, 0.155), spec=0.06, pw=6,  grit=1.2),   # płótno plecaka
}

# ---------- proporcje (metry, wzrost 1,80 m = 7,5 głowy) ----------

HEAD_H = 0.24                    # wysokość głowy
PELVIS_Z = 0.98                  # wysokość miednicy
NECK_Z = 1.52                    # nasada szyi
SHOULDER_Z = 1.50
SHOULDER_Y = 0.21                # połowa szerokości barków (razem 0,42 m ≈ 1,75 głowy)
HIP_Y = 0.095
KNEE_Z = 0.52
ANKLE_Z = 0.09
FOOT_HALF_X = 0.085
FOOT_HALF_Y = 0.04

REST_PELVIS = np.array([0.0, 0.0, PELVIS_Z])
REST_NECK = np.array([0.03, 0.0, NECK_Z])
REST_HIP = {1: np.array([0.0, HIP_Y, PELVIS_Z - 0.02]), -1: np.array([0.0, -HIP_Y, PELVIS_Z - 0.02])}
REST_KNEE = {1: np.array([0.03, HIP_Y + 0.015, KNEE_Z]), -1: np.array([0.03, -(HIP_Y + 0.015), KNEE_Z])}
REST_ANKLE = {1: np.array([0.0, HIP_Y + 0.01, ANKLE_Z]), -1: np.array([0.0, -(HIP_Y + 0.01), ANKLE_Z])}
REST_SHOULDER = {1: np.array([0.02, SHOULDER_Y, SHOULDER_Z]), -1: np.array([0.02, -SHOULDER_Y, SHOULDER_Z])}
REST_ELBOW = {1: np.array([0.02, SHOULDER_Y + 0.02, 1.18]), -1: np.array([0.02, -(SHOULDER_Y + 0.02), 1.18])}
REST_WRIST = {1: np.array([0.03, SHOULDER_Y - 0.02, 0.88]), -1: np.array([0.03, -(SHOULDER_Y - 0.02), 0.88])}
HEAD_CENTER = np.array([0.08, 0.0, 1.68])

# długości kości (do IK)
LEN_THIGH = float(np.linalg.norm(REST_KNEE[1] - REST_HIP[1]))
LEN_SHIN = float(np.linalg.norm(REST_ANKLE[1] - REST_KNEE[1]))
LEN_UPPER = float(np.linalg.norm(REST_ELBOW[1] - REST_SHOULDER[1]))
LEN_FORE = float(np.linalg.norm(REST_WRIST[1] - REST_ELBOW[1]))

SWORD_LEN = 0.60                 # długość klingi (od jelca); miecz razem ~0,89 m


def make_skeleton():
    sk = Skeleton()
    sk.add("pelvis", None, REST_PELVIS, np.array([0.02, 0.0, 1.18]))
    sk.add("spine", "pelvis", np.array([0.02, 0.0, 1.18]), REST_NECK)
    sk.add("neck", "spine", REST_NECK, HEAD_CENTER)
    sk.add("head", "neck", HEAD_CENTER, HEAD_CENTER + np.array([0.05, 0.0, 0.09]))
    for side in (1, -1):
        s = "L" if side == 1 else "R"
        sk.add(f"clav{s}", "spine", REST_NECK + np.array([0.0, side * 0.06, 0.0]),
               REST_SHOULDER[side])
        sk.add(f"upper{s}", f"clav{s}", REST_SHOULDER[side], REST_ELBOW[side])
        sk.add(f"fore{s}", f"upper{s}", REST_ELBOW[side], REST_WRIST[side])
        sk.add(f"hand{s}", f"fore{s}", REST_WRIST[side], REST_WRIST[side] + np.array([0.02, 0.0, -0.06]))
        sk.add(f"thigh{s}", "pelvis", REST_HIP[side], REST_KNEE[side])
        sk.add(f"shin{s}", f"thigh{s}", REST_KNEE[side], REST_ANKLE[side])
        sk.add(f"foot{s}", f"shin{s}", REST_ANKLE[side], REST_ANKLE[side] + np.array([FOOT_HALF_X * 1.6, 0.0, -0.05]))
    sk.reset_pose()
    return sk


def pose_skeleton(sk, p):
    """Ustawia pozycję szkieletu z opisu pozy (jak w drwal.py: cele + obroty tułowia)."""
    sk.reset_pose()
    pelvis = np.asarray(p["pelvis"], float)
    yaw, pitch, roll = p["spine"]
    Rspine = yaw_matrix(yaw) @ rotate_onto([0, 0, 1], _rot_axis(pitch, roll))
    # kręgosłup: pelvis -> szyja (dwie kości: pelvis obraca biodra, spine górę)
    sk.set_pose("pelvis", pelvis, pelvis + Rspine @ (np.array([0.02, 0.0, 1.18]) - REST_PELVIS))
    neck = pelvis + Rspine @ (REST_NECK - REST_PELVIS)
    sk.set_pose("spine", pelvis + Rspine @ (np.array([0.02, 0.0, 1.18]) - REST_PELVIS), neck)
    hyaw, hpitch = p["head"][0], p["head"][1]
    hroll = p["head"][2] if len(p["head"]) > 2 else 0.0
    Rh = yaw_matrix(hyaw) @ rotate_onto([0, 0, 1], _rot_axis(hpitch, hroll))
    headC = neck + Rh @ (HEAD_CENTER - REST_NECK)
    sk.set_pose("neck", neck, headC)
    sk.set_pose("head", headC, headC + Rh @ np.array([0.05, 0.0, 0.09]))
    # nogi: IK od bioder do stóp
    for side, fk in ((1, "footL"), (-1, "footR")):
        s = "L" if side == 1 else "R"
        hip = pelvis + Rspine @ (REST_HIP[side] - REST_PELVIS)
        ankle = np.asarray(p[fk], float)
        knee, an = ik2(hip, ankle, LEN_THIGH, LEN_SHIN,
                       hip + np.array([0.25, side * 0.12, -0.1]))
        sk.set_pose(f"thigh{s}", hip, knee)
        sk.set_pose(f"shin{s}", knee, an)
        # stopa: od kostki w przód (+x) i w dół; obrót footRot (yaw, pitch)
        fyaw, fpitch = p.get(f"footRot{s}", (0.0, 0.0))
        foot_dir = yaw_matrix(fyaw) @ rotate_onto([0, 0, -1], _rot_axis(fpitch, 0.0)) @ np.array([1.0, 0.0, 0.0])
        # kierunek "do przodu stopy" w rest = +x z lekkim zejściem; w pozie: obrót względem rest
        rest_dir = (REST_ANKLE[side] + np.array([FOOT_HALF_X * 1.6, 0.0, -0.05])) - REST_ANKLE[side]
        Rf = rotate_onto(rest_dir, foot_dir)
        sk.set_pose(f"foot{s}", an, an + Rf @ rest_dir)
    # ręce: prawa trzyma miecz (jedną dłonią, opuszczony wzdłuż uda, klingą w dół),
    # lewa swobodna wzdłuż ciała (lekko ugięta, jak u zmęczonego wędrowca)
    knob = np.asarray(p["knob"], float)
    haft = np.asarray(p["haft"], float)
    haft = haft / np.linalg.norm(haft)
    gripR = knob - haft * p["gripR"]          # dłoń na trzonku (między jelec a głowicę)
    for side, grip, pole in ((-1, gripR, p["poleR"]), (1, p.get("handL"), p["poleL"])):
        s = "L" if side == 1 else "R"
        sh = neck + Rspine @ (REST_SHOULDER[side] - REST_NECK)
        clav_mid = neck + Rspine @ (REST_NECK + np.array([0.0, side * 0.06, 0.0]) - REST_NECK)
        sk.set_pose(f"clav{s}", clav_mid, sh)
        if grip is None:
            # lewa ręka swobodna: cel wyznaczony względem bioder (wisi wzdłuż tułowia)
            hip = pelvis + Rspine @ (REST_HIP[side] - REST_PELVIS)
            grip = hip + Rspine @ np.array([0.035, 0.055, -0.06])
        elbow, wrist = ik2(sh, np.asarray(grip, float), LEN_UPPER, LEN_FORE,
                           sh + Rspine @ np.asarray(pole, float))
        sk.set_pose(f"upper{s}", sh, elbow)
        sk.set_pose(f"fore{s}", elbow, wrist)
        # dłoń: prawa chwyta trzonek (wzdłuż haftu), lewa otwarta wzdłuż uda
        if side == -1:
            Rh_ = rotate_onto([0, 0, -1], Rspine @ haft)
        else:
            Rh_ = rotate_onto([0, 0, -1], Rspine @ np.array([0.2, 0.0, -1.0]))
        sk.set_pose(f"hand{s}", wrist, wrist + Rh_ @ np.array([0.02, 0.0, -0.06]))
    return sk


def _rot_axis(pitch_deg, roll_deg):
    """Wektor kierunkowy dla małego obrotu pitch/roll (do rotate_onto z [0,0,1])."""
    pr, rr = math.radians(pitch_deg), math.radians(roll_deg)
    # oś z pochylona do przodu (pitch wokół y) i w bok (roll wokół x)
    v = np.array([math.sin(rr) * 0.0 + 0.0, 0.0, 1.0])
    # budujemy przez obroty: najpierw pitch wokół y, potem roll wokół x
    ry = np.array([[math.cos(pr), 0, math.sin(pr)], [0, 1, 0], [-math.sin(pr), 0, math.cos(pr)]])
    rx = np.array([[1, 0, 0], [0, math.cos(rr), -math.sin(rr)], [0, math.sin(rr), math.cos(rr)]])
    return (rx @ ry) @ np.array([0.0, 0.0, 1.0])


# ---------- geometria: ciało (nagi człowiek, baza pod ubranie) ----------

def _torso_ring(z, rx, ry, n=20, mat=SHIRT, seed=0.0):
    wob = 0.006 * (fbm(np.array([[z * 9 + seed, 1.3, 0.5]]))[0] - 0.5)
    return ring_pts([0.015, 0.0, z], rx + wob, ry + wob, n,
                    disp=lambda a: (0.005 * math.sin(a * 4 + z), 0.004 * math.cos(a * 3), 0))


def body_meshes():
    ms = []
    # tułów nagi (baza pod ubranie): klatka + brzuch + miednica, lekko wcięte w talii
    ms.append(loft_capped([
        _torso_ring(0.98, 0.115, 0.155, 20, SKIN, 1.1),
        _torso_ring(1.12, 0.125, 0.165, 20, SKIN, 1.1),
        _torso_ring(1.28, 0.135, 0.175, 20, SKIN, 1.1),
        _torso_ring(1.40, 0.125, 0.165, 20, SKIN, 1.1),
        _torso_ring(1.50, 0.105, 0.145, 20, SKIN, 1.1),
    ], SKIN))
    # barki (deltoidy)
    for s in (1, -1):
        ms.append(ellipsoid_mesh(REST_SHOULDER[s], [0.065, 0.065, 0.06], SKIN, nu=12, nv=9))
    # szyja (węższa, lekko wysunięta — zmęczona postawa)
    ms.append(cylinder_mesh([0.03, 0.0, 1.42], [0.05, 0.0, 1.55], 0.042, 0.038, SKIN, n=12))
    # głowa: czaszka + twarz + żuchwa + nos (7,5 głowy: głowa ~0,24 m)
    hc = HEAD_CENTER
    skull = ellipsoid_mesh(hc + [0.0, 0.0, 0.01], [0.082, 0.088, 0.095], SKIN, nu=16, nv=12)
    face = ellipsoid_mesh(hc + [0.045, 0.0, -0.045], [0.062, 0.066, 0.058], SKIN, nu=14, nv=10)
    jaw = ellipsoid_mesh(hc + [0.05, 0.0, -0.115], [0.048, 0.052, 0.026], SKIN, nu=12, nv=8)
    nose = ellipsoid_mesh(hc + [0.095, 0.0, -0.02], [0.016, 0.02, 0.03], SKIN, nu=8, nv=6)
    # brwi (cień nad oczodołami — daje zmęczenie spojrzeniu w skali sprite'a)
    brow = box_mesh(hc + [0.088, 0.0, 0.015], [0.045, 0.052, 0.008], SKIN)
    ms += [skull, face, jaw, nose, brow]
    # oczy: zagłębienia (ciemniejsze, bez świecenia — żywy człowiek)
    for s in (1, -1):
        ms.append(ellipsoid_mesh(hc + [0.082, s * 0.034, 0.002], [0.012, 0.008, 0.006], SKIN, nu=6, nv=5))
    # uszy
    for s in (1, -1):
        ms.append(ellipsoid_mesh(hc + [-0.02, s * 0.082, 0.0], [0.014, 0.028, 0.022], SKIN, nu=8, nv=6))
    # szyja/klatka: mięśnie — delikatne wypukłości (proporcje, nie kulturysta)
    # nogi: udo + łydka + kolano (łagodne, mięśniowe)
    for s in (1, -1):
        ms.append(cylinder_mesh(REST_HIP[s] + [0.0, 0.0, -0.02], REST_KNEE[s] + [0.0, 0.0, 0.01],
                                0.072, 0.058, SKIN, n=14))
        ms.append(ellipsoid_mesh(REST_KNEE[s], [0.055, 0.05, 0.06], SKIN, nu=10, nv=8))
        ms.append(cylinder_mesh(REST_KNEE[s] + [0.0, 0.0, -0.01], REST_ANKLE[s] + [0.0, 0.0, 0.01],
                                0.052, 0.042, SKIN, n=12))
        # stopa
        a = REST_ANKLE[s]
        ms.append(box_mesh([a[0] + 0.05, a[1], 0.035], [FOOT_HALF_X, FOOT_HALF_Y, 0.035], SKIN, vtint=None))
    # ręce: ramię + przedramię + dłoń
    for s in (1, -1):
        ms.append(cylinder_mesh(REST_SHOULDER[s], REST_ELBOW[s], 0.05, 0.042, SKIN, n=12))
        ms.append(ellipsoid_mesh(REST_ELBOW[s], [0.038, 0.036, 0.038], SKIN, nu=10, nv=8))
        ms.append(cylinder_mesh(REST_ELBOW[s], REST_WRIST[s], 0.038, 0.03, SKIN, n=12))
        w = REST_WRIST[s]
        ms.append(ellipsoid_mesh(w + [0.01, 0.0, -0.02], [0.038, 0.030, 0.024], SKIN, nu=10, nv=8))
    return ms


def hair_mesh():
    """Krótkie, nieco przetłuszczone ciemne włosy + kilkudniowy zarost."""
    hc = HEAD_CENTER
    # czupryna: elipsoida nad czaszką, lekko z tyłu
    cap = ellipsoid_mesh(hc + [-0.015, 0.0, 0.045], [0.088, 0.09, 0.075], HAIR, nu=16, nv=10)
    # włosy opadają na kark
    back = ellipsoid_mesh(hc + [-0.05, 0.0, 0.0], [0.05, 0.075, 0.085], HAIR, nu=12, nv=9)
    # zarost: cienka maska na żuchwie i policzkach
    beard = ellipsoid_mesh(hc + [0.045, 0.0, -0.1], [0.052, 0.055, 0.03], HAIR, nu=12, nv=8)
    return [cap, back, beard]


def _arc_pts(center, rx, ry, n, a0, a1, disp=None):
    """Łuk elipsy w płaszczyźnie poziomej od kąta a0 do a1 (a=0 to przód postaci +x)."""
    pts = np.empty((n, 3))
    for i in range(n):
        a = a0 + (a1 - a0) * i / (n - 1)
        x, y = math.cos(a) * rx, math.sin(a) * ry
        dx = dy = dz = 0.0
        if disp is not None:
            dx, dy, dz = disp(a)
        pts[i] = [center[0] + x + dx, center[1] + y + dy, center[2] + dz]
    return pts


def _loft_open(rings, mat):
    """Loft przez otwarte łuki — pojedyncza warstwa tkaniny (bez capów)."""
    rings = [np.asarray(r, float) for r in rings]
    n = len(rings[0])
    allv = np.concatenate(rings, axis=0)
    faces = []
    for ri in range(len(rings) - 1):
        b0 = ri * n
        for i in range(n - 1):
            faces.append([b0 + i, b0 + n + i, b0 + i + 1])
            faces.append([b0 + i + 1, b0 + n + i, b0 + n + i + 1])
    m = Mesh(allv, np.array(faces, np.int64),
             np.full(len(faces), mat, np.int64), None).orient_outward()
    m.two_sided = True  # pojedyncza warstwa tkaniny — widoczna też od spodu/tyłu
    return m


def _blade_mesh(x0, x1, w0, w1, t0, t1, mat, nseg=4):
    """Klinga miecza: prostokątny przekrój (szerokość w y, grubość w z),
    zwężający się lekko wklęśle od x0 do x1."""
    rings = []
    for i in range(nseg + 1):
        t = i / nseg
        x = x0 + (x1 - x0) * t
        w = w0 + (w1 - w0) * t * t
        th = t0 + (t1 - t0) * t * t
        rings.append(np.array([
            [x, -w / 2, -th / 2], [x, w / 2, -th / 2],
            [x, w / 2, th / 2], [x, -w / 2, th / 2],
        ]))
    return loft_capped(rings, mat)


def _cloth_rings(points, radii, n, mat, fold_amp, seed=0.0):
    """Pierścienie wzdłuż krzywej (punkty + promienie), z fałdami jako displasement."""
    rings = []
    for i, (c, r) in enumerate(zip(points, radii)):
        t = i / max(1, len(points) - 1)
        wob = fold_amp * (fbm(np.array([[t * 7 + seed, 2.3, 1.0]]))[0] - 0.5)
        rings.append(ring_pts(c, r + wob, r * 0.94 + wob * 0.5, n,
                              disp=lambda a, f=fold_amp: (f * math.sin(a * 3 + i), f * 0.7 * math.cos(a * 4), 0)))
    return loft_capped(rings, mat)


def _seg_points(a, b, n):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    return [a + (b - a) * t for t in np.linspace(0, 1, n)]


def clothes_meshes():
    """Ubiór: koszula, kaftan, płaszcz z kapturem, spodnie, buty, pas, sakwa, owijki, plecak.

    Każdy element to osobna siatka (większa niż ciało — ubranie "owija"), skinowana do
    najbliższych kości. Fałdy: pierścienie z displasementem szumowym (kształt, nie tekstura).
    """
    ms = []
    # ---- koszula (len, znoszony): rękawy, kołnierz, luźny dół
    for s in (1, -1):
        pts = _seg_points(REST_SHOULDER[s] + np.array([0, 0, 0.01]), REST_ELBOW[s], 5)
        radii = [0.068 - 0.014 * t for t in np.linspace(0, 1, 5)]
        ms.append(_cloth_rings(pts, radii, 12, SHIRT, 0.007, seed=s))
        pts = _seg_points(REST_ELBOW[s], REST_WRIST[s] + np.array([0.0, 0.0, -0.01]), 4)
        radii = [0.052 - 0.014 * t for t in np.linspace(0, 1, 4)]
        ms.append(_cloth_rings(pts, radii, 10, SHIRT, 0.006, seed=s + 2))
        # owijka lniana na nadgarstku (poniżej rękawa); na prawej dłoni
        # bliżej kciuka — tam, gdzie chwyta się miecz
        off = np.array([-0.015, -0.045, 0.0]) if s == -1 else np.array([0.0, 0.0, -0.015])
        ms.append(cylinder_mesh(REST_WRIST[s] + off, REST_WRIST[s] + [0.01, 0.0, -0.065],
                                0.038, 0.032, WRAP, n=10))
        # dłoń wystaje z rękawa (skóra)
    # koszulowy tułów: od bioder do barków, najszerszy w klatce, fałdy przy pasie
    prof = [(0.97, 0.135, 0.175), (1.10, 0.145, 0.185), (1.26, 0.15, 0.19),
            (1.40, 0.14, 0.18), (1.48, 0.125, 0.155)]
    rings = []
    for z, rx, ry in prof:
        rings.append(_torso_ring(z, rx, ry, 20, SHIRT, 3.3))
    ms.append(loft_capped(rings, SHIRT))
    # kołnierz (stójka)
    ms.append(loft_capped([
        ring_pts([0.04, 0.0, 1.49], 0.075, 0.058, 12),
        ring_pts([0.055, 0.0, 1.56], 0.082, 0.06, 12),
    ], SHIRT))
    # guziki (ciemniejsze punkty z przodu koszuli — czytelne w 1x)
    for z in (1.15, 1.25, 1.35, 1.45):
        ms.append(ellipsoid_mesh([0.14, 0.0, z], [0.008, 0.008, 0.008], KAFTAN, nu=6, nv=5))

    # ---- kaftan (wełniany, ciemny): bez rękawów, otwarty z przodu — widać koszulę,
    # dwie połówki (lewa/prawa) lekko rozchylone, dół rozszerzony, falujący
    for s in (1, -1):
        prof = [(0.97, 0.150, 0.185), (1.12, 0.155, 0.195), (1.28, 0.150, 0.190),
                (1.42, 0.135, 0.175), (1.50, 0.120, 0.160)]
        rings = []
        for k, (z, rx, ry) in enumerate(prof):
            wob = 0.010 * (fbm(np.array([[z * 6 + s, 4.4, 1.0]]))[0] - 0.5)
            amp = 0.012 * (1.0 - z / 1.5)
            # łuk: od kąta ~35° (przód-bok) przez bok do ~200° (tył-bok) — otwarty przód
            a0, a1 = math.radians(38 * s), math.radians(195 * s)
            if s < 0:
                a0, a1 = math.radians(-195), math.radians(-38)
            cx = -0.01 * s  # lekko przesunięty do swojej strony
            rings.append(_arc_pts([cx, 0.0, z], rx + wob, ry + wob, 14, a0, a1,
                                  disp=lambda a, z=z, amp=amp: (amp * math.sin(a * 3 + z * 5),
                                                                amp * 0.8 * math.cos(a * 4), 0)))
        ms.append(_loft_open(rings, KAFTAN))
    # dół kaftana: rozchylone "poły" poniżej pasa (fałda, nie sztywna spódnica)
    for s in (1, -1):
        pts = [[-0.005 * s, s * 0.10, 0.97], [-0.01 * s, s * 0.125, 0.90],
               [-0.015 * s, s * 0.145, 0.83], [-0.02 * s, s * 0.16, 0.76]]
        rings = [_arc_pts(p, 0.045, 0.05, 8, math.radians(20 * s) if s > 0 else math.radians(-160),
                          math.radians(160 * s) if s > 0 else math.radians(-20))
                 for p in pts]
        ms.append(_loft_open(rings, KAFTAN))

    # ---- płaszcz podróżny z kapturem: szerokie poły od barków do połowy łydki,
    # otwarte z przodu, falujący hem (osobne "fałdowe" panele na dole z tyłu)
    prof = [(1.46, 0.20, 0.24), (1.28, 0.23, 0.28), (1.04, 0.26, 0.31), (0.80, 0.30, 0.35), (0.62, 0.34, 0.40)]
    rings = []
    for z, rx, ry in prof:
        wob = 0.012 * (fbm(np.array([[z * 6, 3.3, 1.1]]))[0] - 0.5)
        amp = 0.022 * (1.0 - z / 1.5)
        # łuk: przód-bok lewy -> tył -> przód-bok prawy (przód otwarty między -55° a 55°)
        rings.append(_arc_pts([0.0, 0.0, z], rx + wob, ry + wob, 22,
                              math.radians(55), math.radians(305),
                              disp=lambda a, z=z, amp=amp: (amp * math.sin(a * 3 + z * 5),
                                                            amp * 0.8 * math.cos(a * 4), 0)))
    ms.append(_loft_open(rings, CAPE))
    # hem płaszcza: nieregularne, rozchylone końcówki z tyłu/boków
    for s in (1, -1):
        hem_pts = [[-0.02, s * 0.22, 0.60], [-0.04, s * 0.30, 0.58],
                   [-0.06, s * 0.36, 0.55], [-0.07, s * 0.40, 0.50]]
        rings = [_arc_pts(p, 0.05, 0.06, 7,
                          math.radians(100 * s) if s > 0 else math.radians(-280),
                          math.radians(260 * s) if s > 0 else math.radians(-100))
                 for p in hem_pts]
        ms.append(_loft_open(rings, CAPE))
    # kaptur: otwarty z przodu, opadający na plecy
    hc = HEAD_CENTER
    hood = ellipsoid_mesh(hc + [-0.05, 0.0, 0.04], [0.115, 0.105, 0.115], CAPE, nu=16, nv=12)
    ms.append(hood)

    # ---- spodnie (ciemna wełna): uda i łydki, luźne z fałdami nad kolanem
    for s in (1, -1):
        pts = _seg_points(REST_HIP[s] + np.array([0, 0, -0.03]), REST_KNEE[s], 6)
        radii = [0.088 - 0.022 * t for t in np.linspace(0, 1, 6)]
        ms.append(_cloth_rings(pts, radii, 14, TROUSERS, 0.007, seed=s * 3))
        pts = _seg_points(REST_KNEE[s] + np.array([0, 0, 0.01]), REST_ANKLE[s] + np.array([0, 0, 0.01]), 5)
        radii = [0.066 - 0.02 * t for t in np.linspace(0, 1, 5)]
        ms.append(_cloth_rings(pts, radii, 12, TROUSERS, 0.006, seed=s * 5 + 1))
        # but (skóra): podeszwa + cholewka — stopa wskazuje w przód (+x)
        a = REST_ANKLE[s]
        ms.append(box_mesh([a[0] + 0.04, a[1], 0.012], [FOOT_HALF_X + 0.012, FOOT_HALF_Y + 0.009, 0.012], BOOTS))
        ms.append(box_mesh([a[0] + 0.055, a[1], 0.055], [FOOT_HALF_X - 0.004, FOOT_HALF_Y - 0.002, 0.043], BOOTS))

    # ---- pas skórzany + sakwa + klamra
    # pas: pierścień wokół talii z lekkim zwisem z tyłu (fałda)
    rings = []
    for z, ry in ((1.0, 0.185), (0.955, 0.19)):
        wob = 0.006 * (fbm(np.array([[z * 11, 4.2, 0.9]]))[0] - 0.5)
        rings.append(ring_pts([0.0, 0.0, z], 0.155 + wob, ry + wob, 20,
                              disp=lambda a: (0.004 * math.sin(a * 6), 0.003 * math.cos(a * 5), 0)))
    ms.append(loft_capped(rings, LEATHER))
    ms.append(box_mesh([-0.02, -0.185, 0.93], [0.045, 0.028, 0.05], LEATHER))   # sakwa (prawy bok)
    ms.append(box_mesh([-0.06, -0.175, 0.97], [0.012, 0.008, 0.014], IRON))     # klamra z przodu pasa

    # ---- plecak z posłaniem (na plecach — x ujemne, za płaszczem; widoczny z tyłu/boków)
    ms.append(box_mesh([-0.17, 0.0, 1.16], [0.075, 0.175, 0.25], BAG))
    ms.append(cylinder_mesh([-0.27, 0.0, 1.45], [-0.31, 0.0, 1.43], 0.055, 0.055, WRAP, n=10))  # zwinięte posłanie
    # pasek przez ramię (prawy bark -> lewy biodro)
    ms.append(cylinder_mesh([0.0, -0.2, 1.42], [-0.05, 0.17, 1.02], 0.014, 0.014, LEATHER, n=8))
    return ms


def make_shade_hook():
    """Proceduralne detale materiałów: skóra (plamy, żyłki), tkaniny (mech, wilgoć, przetarcia),
    żelazo (rdza, rysy), skóra butów (połysk na noskach)."""
    def hook(matId, pts, nrm, albedo, spec, emit):
        if matId == SKIN:
            blotch = value_noise(pts * 9 + 2.7)
            vein = np.clip(1.0 - np.abs(value_noise(pts * 16) - 0.5) * 16, 0, 1)
            albedo = albedo * (0.85 + 0.3 * blotch)[:, None] * (1.0 - 0.25 * vein)[:, None]
        if matId in (SHIRT, KAFTAN, CAPE, TROUSERS, WRAP, BAG):
            # mech i pleśń na górnych powierzchniach (wilgoć osiada z góry)
            moss = np.clip((value_noise(pts * 11 + 5.0) - 0.45) * 4.0, 0, 1) * np.clip(nrm[:, 1] * 1.5, 0, 1)
            albedo = albedo * (1 - moss[:, None]) + np.array([0.10, 0.14, 0.065])[None, :] * moss[:, None]
            # przetarcia na łokciach/kolanach (nisko i z boku)
            wear = np.clip(1.0 - np.abs(pts[:, 2] - 1.15) * 6, 0, 1) * 0.25
            albedo = albedo * (1.0 + wear[:, None])
        if matId == IRON:
            rust = np.clip((value_noise(pts * 13 + 8.0) - 0.55) * 5.0, 0, 1)
            albedo = albedo * (1 - rust[:, None]) + np.array([0.16, 0.09, 0.05])[None, :] * rust[:, None]
        if matId == BOOTS:
            # połysk na noskach (przód buta)
            toe = np.clip((pts[:, 0] - 0.0) * 8, 0, 1)
            spec = spec * (0.6 + 0.8 * toe)
        return albedo, spec, emit
    return hook


def sword_mesh(p):
    """Prosty jednoręczny miecz (~0,89 m: rękojeść 0,24 + klinga 0,62 + jelec).
    Układ lokalny: oś y = wzdłuż miecza (czubek klingi y=-0,62, głowica y=+0,265),
    oś z = ostrze. Potem jedna macierz świata: lokal -> (X, knob)."""
    knob = np.asarray(p["knob"], float)
    haft = np.asarray(p["haft"], float)
    haft = haft / np.linalg.norm(haft)
    edge = np.asarray(p.get("edge", (0.0, 0.0, 1.0)), float)
    edge = edge - haft * np.dot(edge, haft)
    edge = edge / np.linalg.norm(edge)
    X = np.stack([np.cross(edge, haft), haft, edge], axis=1)  # kolumny: x, y(trzonek), z(ostrze)
    parts = []
    # głowica (pommel)
    parts.append(ellipsoid_mesh([0, 0.265, 0], [0.018, 0.02, 0.018], IRON, nu=10, nv=8))
    # trzonek (rękojeść drewniana z lekkim owijkowym zgrubieniem na środku)
    parts.append(cylinder_mesh([0, -0.035, 0], [0, 0.155, 0], 0.015, 0.013, WOOD, n=10))
    parts.append(ellipsoid_mesh([0, 0.055, 0], [0.021, 0.075, 0.021], WOOD, nu=10, nv=8))
    # jelec (prosty, lekko rozszerzony ku rękojeści)
    parts.append(box_mesh([0, 0.175, 0], [0.008, 0.026, 0.045], IRON))
    # klinga: prostokątny przekrój, lekko zwężający się ku czubkowi
    parts.append(_blade_mesh(0.20, 0.20 + SWORD_LEN, 0.024, 0.004, 0.005, 0.0015, IRON))
    # krawędź tnąca (jasny pas wzdłuż klingi — ostrze w -z)
    parts.append(_blade_mesh(0.21, 0.20 + SWORD_LEN * 0.97, 0.0035, 0.0008, 0.0042, 0.0012, EDGE, nseg=3))
    out = []
    for mm in parts:
        v = mm.verts @ X.T + knob[None, :]
        out.append(Mesh(v, mm.faces, mm.matIds, mm.vtint))
    return out


# ---------- pozy (jak w drwal.py: cele + obroty) ----------

BASE = dict(
    pelvis=(0.0, 0.0, PELVIS_Z),
    spine=(0.0, 0.0, 0.0),
    head=(0.0, 0.0),
    footL=(0.05, HIP_Y + 0.05, ANKLE_Z), footR=(-0.05, -(HIP_Y + 0.05), ANKLE_Z),
    footRotL=(0.0, 0.0), footRotR=(0.0, 0.0),
    knob=(0.045, -0.265, 0.88),      # oś miecza przy prawej dłoni (trzonek, nadgarstkowo)
    haft=(0.02, 0.0, -1.0),          # kierunek ku czubkowi klingi (w dół, lekko na zewnątrz)
    edge=(1.0, 0.0, 0.3),            # ostrze — lekko w płaszczyźnie poziomej
    gripR=0.07,                      # dłoń na środku trzonka
    poleR=(0.10, -0.32, -0.28), poleL=(0.0, 0.28, -0.30),
)


def pose(**changes):
    r = dict(BASE)
    r.update(changes)
    return r


def build_meshes(p):
    """Buduje siatki w pozie (skinning) + miecz. Zwraca listę Mesh w przestrzeni modelu."""
    sk = make_skeleton()
    pose_skeleton(sk, p)
    body = body_meshes()
    hair = hair_mesh()
    clothes = clothes_meshes()
    meshes = body + hair + clothes
    segments = {}
    for name, b in sk.bones.items():
        segments[name] = (b["rest_head"], b["rest_tail"])
    hard = {}
    # głowa, włosy, zarost, szyja -> kość head/neck; miecz osobno (rigid)
    n_body = len(body)
    weights = auto_weights(meshes, sk, segments, kmax=3, sigma=0.055)
    skinned = skin_meshes(meshes, sk, weights)
    sword = sword_mesh(p)
    return skinned + sword


# ---------- pozy kluczowe i animacje ----------

def breathing(i, count):
    ph = math.sin(2 * math.pi * i / count)
    return pose(pelvis=(0.0, 0.0, PELVIS_Z - 0.006 * ph),
                spine=(0.0, 1.5 * ph, 0.0), head=(0.0, 2.0 * ph),
                knob=(0.045, -0.265, 0.88 - 0.006 * ph))


def _gait(u, stride, lift_h):
    """Cykl chodu względem bioder. u w [0,1): faza podporowa 60% (stopa nieruchoma
    względem ziemi -> liniowy ruch względem bioder), faza lotu 40% (szybkie
    wahnięcie do przodu z uniesieniem). Zwraca (x_rel, z_lift)."""
    if u < 0.6:
        s = u / 0.6
        return stride * (0.5 - s), 0.0
    s = (u - 0.6) / 0.4
    e = s * s * (3 - 2 * s)
    return stride * (-0.5 + e), lift_h * math.sin(math.pi * s)


def walking(i, count):
    th = 2 * math.pi * i / count
    stride = 0.46
    xL, zL = _gait(i / count, stride, 0.07)
    xR, zR = _gait((i / count + 0.5) % 1.0, stride, 0.07)
    return pose(pelvis=(0.0, 0.022 * math.sin(th), PELVIS_Z - 0.012 * math.cos(2 * th)),
                spine=(5.0 * math.cos(th), 3.5 + math.cos(2 * th), -2.5 * math.sin(th)),
                head=(1.5 * math.cos(th), 2.0),
                footL=(0.05 + xL, HIP_Y + 0.05, ANKLE_Z + zL),
                footR=(0.05 + xR, -(HIP_Y + 0.05), ANKLE_Z + zR),
                knob=(0.045, -0.265, 0.88 - 0.008 * math.cos(2 * th)),
                haft=(0.02 + 0.02 * math.sin(th), 0.0, -1.0),
                poleR=(0.10, -0.32, -0.28 + 0.03 * math.sin(th)),
                poleL=(0.0, 0.28, -0.30 + 0.05 * math.sin(th)))


POSES = {"spoczynek": pose()}

ANIMS = {
    "spoczynek": dict(frames=[breathing(i, 4) for i in range(4)], durations=[260] * 4, loop=True),
    "chod": dict(frames=[walking(i, 8) for i in range(8)], durations=[115] * 8, loop=True,
                 root_speed_mps=round(0.46 / (0.6 * 8 * 0.115), 2)),
}


# ---------- render ----------

def render_pose_all_dirs(p, shadow, hook=None, frameSize=FRAME_SIZE, supersample=4):
    """Renderuje pozę we wszystkich 8 kierunkach. Zwraca listę 8 tablic uint8 RGBA."""
    meshes = build_meshes(p)
    return [render_frame(meshes, MATERIALS, d, shadow=shadow, shade_hook=hook,
                         frameSize=frameSize, supersample=supersample) for d in range(8)]


_SHADE_HOOK = None


def shade_hook():
    global _SHADE_HOOK
    if _SHADE_HOOK is None:
        _SHADE_HOOK = make_shade_hook()
    return _SHADE_HOOK


def _shadow():
    meshes = build_meshes(pose())
    sm = ShadowMap(size=256, half=2.0)
    sm.rasterize(meshes)
    return sm


def cmd_arkusz(pozaName):
    from PIL import Image
    p = POSES.get(pozaName) or ANIMS.get(pozaName, {}).get("frames", [None])[0]
    if p is None:
        print("nieznana poza:", pozaName)
        return
    sm = _shadow()
    frames = render_pose_all_dirs(p, sm, hook=shade_hook())
    path = save_pose_sheet(PREVIEWS, "bohater", pozaName, frames)
    print("ok", path)
    for d in range(8):
        Image.fromarray(frames[d], "RGBA").save(
            os.path.join(PREVIEWS, f"bohater_{pozaName}_{d}_{DIRECTIONS[d]}.png"))
        print("ok", os.path.join(PREVIEWS, f"bohater_{pozaName}_{d}_{DIRECTIONS[d]}.png"))


def _anim_job(job):
    from PIL import Image
    name, f, d, frameSize, supersample = job
    p = ANIMS[name]["frames"][f]
    sm = _shadow()
    img = render_frame(build_meshes(p), MATERIALS, d, shadow=sm, shade_hook=shade_hook(),
                       frameSize=frameSize, supersample=supersample)
    return (name, f, d, img)


def cmd_anim(names, sketch=False):
    import tempfile
    frameSize, supersample = (96, 1) if sketch else (FRAME_SIZE, 4)
    dirs = [7] if sketch else list(range(8))
    jobs = [(n, f, d, frameSize, supersample)
            for n in names for f in range(len(ANIMS[n]["frames"])) for d in dirs]
    results = {}
    tmp = tempfile.mkdtemp(prefix="bohater-")
    for done, (n, f, d, img) in enumerate(run_jobs(jobs, _anim_job), 1):
        results[(n, f, d)] = img
        if done % 8 == 0 or done == len(jobs):
            print(f"{done}/{len(jobs)}", flush=True)
    meta = {}
    for n in names:
        frames_u8 = [[results[(n, f, d)] for f in range(len(ANIMS[n]["frames"]))] for d in dirs]
        if not sketch:
            outDir = ATLAS
            fileName, gifPath = _save_atlas_gif(outDir, "bohater", n, frames_u8,
                                               ANIMS[n]["durations"], ANIMS[n]["loop"])
            meta[n] = {
                "file": fileName,
                "frames": len(ANIMS[n]["frames"]),
                "durations_ms": ANIMS[n]["durations"],
                "loop": ANIMS[n]["loop"],
                **({"root_speed_mps": ANIMS[n]["root_speed_mps"]} if "root_speed_mps" in ANIMS[n] else {}),
                "events": ANIMS[n].get("events", {}),
            }
            print("ok", os.path.join(outDir, fileName), "+", gifPath)
        else:
            from PIL import Image
            strip = Image.new("RGBA", (frameSize, frameSize), GROUND_RGB + (255,))
            strip.alpha_composite(Image.fromarray(frames_u8[0][0], "RGBA"), (0, 0))
            strip = strip.resize((frameSize * 4, frameSize * 4), Image.NEAREST)
            strip.convert("RGB").save(os.path.join(tmp, f"bohater_{n}_szkic.png"))
            print("szkic", n, "->", os.path.join(tmp, f"bohater_{n}_szkic.png"))
    if not sketch:
        write_json(ATLAS, "bohater", meta)
        print("ok", os.path.join(ATLAS, "bohater.json"))


def _save_atlas_gif(outDir, charId, name, frames_u8, durations, loop):
    from meshkit import _save_atlas_gif as _s
    return _s(outDir, charId, name, frames_u8, durations, loop)


def cmd_test():
    """Kontrola techniczna: kotwica, alfa, granice, proporcje.

    W projekcji izo 30° wysokość 1,78 m to ~93 px na ekranie (1,78*cos30*60),
    więc zakres wysokości 88-112 px. Stopa mierzona po alfa>0.85, żeby cień
    na ziemi (alfa<=~0.75) nie przesuwał kotwicy.
    """
    sm = _shadow()
    frames = render_pose_all_dirs(pose(), sm, hook=shade_hook(), supersample=2)
    ok = True
    for d in range(8):
        a = frames[d][..., 3] / 255.0
        ys, xs = np.where(a > 0.85)
        ysA, xsA = np.where(a > 0.02)
        if len(ys) == 0:
            print(f"dir {d}: PUSTA KLATKA"); ok = False; continue
        foot_px = ys.max()          # dolna krawędź ciała (bez cienia)
        top_px = ys.min()           # góra włosów
        height_px = foot_px - top_px
        print(f"dir {d} {DIRECTIONS[d]}: cialo y {top_px}..{foot_px} (wys {height_px}px), "
              f"x {xs.min()}..{xs.max()}, z alfa y {ysA.min()}..{ysA.max()}, "
              f"pikseli {len(ys)}")
        # kotwica: środek stóp (z=0, x=0) rzutuje się na ANCHOR=(96,158.35);
        # w dir S prawy but (przód postaci) ląduje ~2-4 px niżej (izo 30°)
        if not (152 <= foot_px <= 164):
            print(f"  BLAD: dol ciala na y={foot_px}, oczekiwano ~152-164 (kotwica {ANCHOR[1]:.1f})")
            ok = False
        if not (88 <= height_px <= 112):
            print(f"  UWAGA: wysokosc ciala {height_px}px poza zakresem 88-112")
            ok = False
        # marginesy klatki (w tym cien): nic nie może dotykać brzegów
        if ysA.min() < 3 or ysA.max() > FRAME_SIZE - 3 or xsA.min() < 3 or xsA.max() > FRAME_SIZE - 3:
            print(f"  UWAGA: element przy krawędzi klatki")
            ok = False
        # alfa: przezroczystość poza postacią, pełne krycie na ciele
        if a.max() < 0.98 or a[0, 0] != 0 or a[-1, -1] != 0:
            print("  UWAGA: problem z maską alfa (krawędzie lub max)")
            ok = False
    print("kotwica oczekiwana:", ANCHOR)
    print("test", "OK" if ok else "z uwagami")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__)
    elif args[0] == "arkusz":
        cmd_arkusz(args[1] if len(args) > 1 else "spoczynek")
    elif args[0] == "anim":
        rest = [a for a in args[1:] if not a.startswith("--")]
        names = rest if rest and rest[0] != "all" else list(ANIMS)
        cmd_anim(names, sketch="--szkic" in args)
    elif args[0] == "test":
        cmd_test()
