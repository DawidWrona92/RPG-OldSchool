"""ENM-drwal jako ożywieniec — poza zapowiedzi Rozłupania (obie dłonie nad głową).

Użycie: python3 drwal.py [kierunek 0-7 | all] [--bez-sygnalu] [--rozmiar 192]
Wynik: output/drwal_rozlupanie_<n>_<kierunek>.png (RGBA, wygładzone krawędzie, cień półprzezroczysty).
"""
import os
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sdfkit import DIRECTIONS, Isect, Model, Prim, Sub, chain, downsample, frame_from_axes, normalize, render, value_noise  # noqa: E402

SKIN, SHIRT, TROUSERS, APRON, SEAM, LEATHER, WRAPS, BAST, WOOD, IRON, EDGE, HAIR, EYES, SOCKET, TEETH = range(15)

MATERIALS = {
    SKIN: dict(alb=(0.13, 0.135, 0.115), spec=0.28, pw=18, grit=0.7),       # popielata, woskowa skóra
    SHIRT: dict(alb=(0.078, 0.07, 0.055), spec=0.05, pw=6, grit=0.9),     # brudny len
    TROUSERS: dict(alb=(0.042, 0.038, 0.033), spec=0.05, pw=6, grit=0.9),  # ciemna wełna
    APRON: dict(alb=(0.048, 0.03, 0.019), spec=0.3, pw=14, grit=0.6),      # mokra skóra fartucha
    SEAM: dict(alb=(0.34, 0.29, 0.19), spec=0.05, pw=6, grit=0.4),         # jedyny jasny szew
    LEATHER: dict(alb=(0.07, 0.044, 0.025), spec=0.2, pw=12, grit=0.6),    # pas, rzemienie
    WRAPS: dict(alb=(0.12, 0.11, 0.09), spec=0.04, pw=4, grit=1.0),        # onuce
    BAST: dict(alb=(0.11, 0.085, 0.05), spec=0.05, pw=4, grit=1.2),        # łapcie z łyka
    WOOD: dict(alb=(0.085, 0.058, 0.034), spec=0.15, pw=10, grit=0.7),     # trzonek
    IRON: dict(alb=(0.055, 0.042, 0.033), spec=0.4, pw=22, grit=1.1, specTint=0.5),  # zardzewiały obuch
    EDGE: dict(alb=(0.2, 0.2, 0.21), spec=1.3, pw=60, grit=0.4, specTint=0.6),       # wyostrzona krawędź
    HAIR: dict(alb=(0.034, 0.032, 0.029), spec=0.18, pw=10, grit=0.8),     # zlepione włosy
    EYES: dict(alb=(0.0, 0.0, 0.0), spec=0.0, pw=1, grit=0.0, emit=(0.6, 0.72, 0.6)),  # mętny blask
    SOCKET: dict(alb=(0.008, 0.008, 0.008), spec=0.0, pw=1, grit=0.0),
    TEETH: dict(alb=(0.2, 0.17, 0.12), spec=0.2, pw=12, grit=0.6),
}

MOSS = np.array([0.034, 0.05, 0.022])


def build_drwal():
    model = Model()

    # ---------- tułów: szerokie, kościste barki, zapadnięty brzuch ----------
    torso = [
        Prim("ellipsoid", SHIRT, c=[0.0, 0, 1.06], radii=[0.11, 0.16, 0.13]),
        Prim("ellipsoid", SHIRT, c=[0.02, 0, 1.31], radii=[0.145, 0.25, 0.17]),
        Prim("ellipsoid", SHIRT, c=[0.0, 0, 1.46], radii=[0.12, 0.32, 0.08]),
        Prim("cone", TROUSERS, a=[0, 0, 1.0], b=[0, 0, 0.82], r1=0.15, r2=0.17),
    ]
    model.group(0.06, torso, disp=(0.004, 20))
    # szyja wysunięta do przodu — zgarbienie
    model.group(0.03, [Prim("cone", SKIN, a=[0.02, 0, 1.47], b=[0.1, 0, 1.6], r1=0.06, r2=0.045)], disp=(0.003, 40))

    # pas
    model.group(0.0, [Prim("cylinder", LEATHER, c=[0, 0, 0.99], R=np.eye(3), r=0.158, h=0.028)])

    # fartuch: skórzana płachta opinająca przód tułowia i ud; postrzępiony dół
    apronC = np.array([0.03, 0, 0.93])
    apronShell = Sub(Prim("ellipsoid", APRON, c=apronC, radii=[0.185, 0.215, 0.5]),
                     [Prim("ellipsoid", APRON, c=apronC, radii=[0.17, 0.2, 0.49])])
    front = Prim("box", APRON, c=[0.2, 0, 0.92], R=np.eye(3), half=[0.15, 0.16, 0.37])
    tatters = [Prim("sphere", APRON, c=[0.2, y, 0.55], r=r) for y, r in ((-0.11, 0.05), (0.02, 0.04), (0.12, 0.06))]
    apron = Sub(Isect([apronShell, front]), tatters)
    seamBand = Prim("box", SEAM, c=[0.2, 0.06, 0.92], R=np.eye(3), half=[0.15, 0.006, 0.35])
    seamShell = Sub(Prim("ellipsoid", SEAM, c=apronC, radii=[0.19, 0.22, 0.505]),
                    [Prim("ellipsoid", SEAM, c=apronC, radii=[0.18, 0.21, 0.495])])
    seam = Isect([seamShell, seamBand, front])
    straps = [Prim("cone", LEATHER, a=[0.13, s * 0.13, 1.28], b=[0.06, s * 0.08, 1.56], r1=0.012, r2=0.012) for s in (1, -1)]
    model.group(0.0, [apron, seam] + straps)

    # ---------- nogi: szeroki, zaparty rozkrok ----------
    legs = [((0, 0.11, 0.95), (0.17, 0.18, 0.55), (0.1, 0.21, 0.1)),
            ((0, -0.11, 0.95), (-0.05, -0.18, 0.52), (-0.2, -0.22, 0.1))]
    for hip, knee, ankle in legs:
        hip, knee, ankle = (np.array(v, float) for v in (hip, knee, ankle))
        model.group(0.03, [Prim("cone", TROUSERS, a=hip, b=knee, r1=0.085, r2=0.064),
                           Prim("sphere", TROUSERS, c=knee, r=0.066)], disp=(0.006, 24))
        shin = [Prim("cone", WRAPS, a=knee, b=ankle, r1=0.062, r2=0.05)]
        model.group(0.02, shin, disp=(0.006, 34))
        # rzemienie oplatające onuce
        legDir = normalize(ankle - knee)
        for t in (0.25, 0.5, 0.75):
            center = knee + (ankle - knee) * t
            model.group(0.0, [Prim("torus", LEATHER, c=center, R=frame_from_axes(np.cross(legDir, [0, 1, 0]), [0, 1, 0], legDir), major=0.058 - 0.01 * t, minor=0.007)])
        model.group(0.03, [Prim("box", BAST, c=[ankle[0] + 0.06, ankle[1], 0.045], R=np.eye(3), half=[0.09, 0.04, 0.028], round=0.022),
                           Prim("cone", BAST, a=[ankle[0], ankle[1], 0.06], b=ankle, r1=0.058, r2=0.052)], disp=(0.006, 30))

    # ---------- topór: zamach znad głowy, ostrze za plecami ----------
    knob = np.array([0.08, 0.0, 1.97])
    haftDir = normalize([-0.62, -0.32, 0.38])
    edgeDir = normalize(np.cross(np.cross(haftDir, [0, 0, 1]), haftDir))  # w płaszczyźnie zamachu, „w górę” względem trzonka
    if edgeDir[2] < 0:
        edgeDir = -edgeDir
    head = knob + haftDir * 1.0
    model.group(0.0, [Prim("cone", WOOD, a=knob - haftDir * 0.03, b=knob + haftDir * 1.06, r1=0.021, r2=0.019)], disp=(0.002, 50))
    bladeR = frame_from_axes(haftDir, edgeDir, np.cross(haftDir, edgeDir))
    # brodaty topór: wąska szyjka przy oku, szerokie, łukowate ostrze
    bladeC = head + edgeDir * 0.13 - haftDir * 0.02
    arcCenter = head - edgeDir * 0.1 - haftDir * 0.02
    notches = [Prim("cylinder", IRON, c=head + edgeDir * 0.085 + haftDir * off, R=bladeR, r=0.07, h=0.05) for off in (-0.145, 0.135)]
    blade = Sub(Isect([Prim("box", IRON, c=bladeC, R=bladeR, half=[0.11, 0.15, 0.011], round=0.003),
                       Prim("sphere", IRON, c=arcCenter, r=0.36)]), notches)
    edge = Sub(Isect([Prim("box", EDGE, c=bladeC, R=bladeR, half=[0.112, 0.155, 0.013]),
                      Prim("sphere", EDGE, c=arcCenter, r=0.362),
                      Sub(Prim("sphere", EDGE, c=arcCenter, r=0.4), [Prim("sphere", EDGE, c=arcCenter, r=0.33)])]), notches)
    eye = Prim("box", IRON, c=head - edgeDir * 0.015, R=bladeR, half=[0.04, 0.045, 0.028], round=0.008)
    model.group(0.0, [blade, edge])
    model.group(0.01, [eye], disp=(0.003, 60))

    # ---------- ręce: obie dłonie na trzonku nad głową ----------
    gripR = knob + haftDir * 0.07 + np.array([0, -0.01, 0])
    gripL = knob + haftDir * 0.3 + np.array([0, 0.01, 0])
    arms = [((0.0, -0.3, 1.5), (0.13, -0.4, 1.76), gripR),
            ((0.0, 0.3, 1.5), (0.04, 0.41, 1.72), gripL)]
    for shoulder, elbow, grip in arms:
        shoulder, elbow = np.array(shoulder, float), np.array(elbow, float)
        # rękaw podarty przy łokciu
        sleeve = Sub(Prim("cone", SHIRT, a=shoulder, b=elbow + (elbow - shoulder) * 0.12, r1=0.068, r2=0.058),
                     [Prim("sphere", SHIRT, c=elbow + (elbow - shoulder) * 0.2 + np.array([0.0, 0.0, 0.03]), r=0.05)])
        model.group(0.04, [sleeve, Prim("ellipsoid", SHIRT, c=shoulder + np.array([0, 0, 0.02]), radii=[0.08, 0.08, 0.075])], disp=(0.006, 24))
        # wychudłe przedramię, kościsty łokieć, pięść na trzonku
        wristDir = normalize(grip - elbow)
        model.group(0.025, [Prim("cone", SKIN, a=elbow, b=grip - wristDir * 0.04, r1=0.046, r2=0.03),
                            Prim("sphere", SKIN, c=elbow, r=0.045),
                            Prim("ellipsoid", SKIN, c=grip, radii=[0.045, 0.042, 0.045])], disp=(0.003, 40))

    # ---------- głowa: zapadnięte oczodoły, opadnięta szczęka, zlepione włosy ----------
    hc = np.array([0.14, 0.0, 1.7])
    skullBase = [Prim("sphere", SKIN, c=hc, r=0.092),
                 Prim("ellipsoid", SKIN, c=hc + [0.045, 0, -0.055], radii=[0.065, 0.068, 0.06])]
    sockets = [Prim("sphere", SKIN, c=hc + [0.098, s * 0.036, 0.0], r=0.027) for s in (1, -1)]
    cheeks = [Prim("sphere", SKIN, c=hc + [0.07, s * 0.08, -0.05], r=0.03) for s in (1, -1)]
    mouth = Prim("ellipsoid", SKIN, c=hc + [0.1, 0, -0.098], radii=[0.04, 0.035, 0.016])
    skull = Sub(Prim("sphere", SKIN, c=hc, r=0.092), sockets + cheeks + [mouth], smooth=0.012)
    face = Sub(skullBase[1], sockets + cheeks + [mouth], smooth=0.012)
    jaw = Prim("ellipsoid", SKIN, c=hc + [0.06, 0, -0.125], radii=[0.05, 0.055, 0.028])
    nose = Prim("cone", SKIN, a=hc + [0.1, 0, -0.01], b=hc + [0.125, 0, -0.045], r1=0.014, r2=0.01)
    model.group(0.015, [skull, face, jaw, nose], disp=(0.0015, 40))
    model.group(0.0, [Prim("sphere", SOCKET, c=hc + [0.084, s * 0.036, 0.0], r=0.016) for s in (1, -1)])
    model.group(0.0, [Prim("sphere", EYES, c=hc + [0.094, s * 0.036, -0.002], r=0.0075) for s in (1, -1)])
    model.group(0.0, [Prim("box", TEETH, c=hc + [0.098, 0, -0.088], R=np.eye(3), half=[0.008, 0.026, 0.008], round=0.003)])
    # długie, zlepione włosy i broda
    hair = [Prim("ellipsoid", HAIR, c=hc + [-0.02, 0, 0.02], radii=[0.1, 0.1, 0.09]),
            Prim("ellipsoid", HAIR, c=hc + [-0.06, 0, -0.08], radii=[0.06, 0.1, 0.12])]
    hair = [Sub(h, [Prim("ellipsoid", HAIR, c=hc + [0.1, 0, -0.03], radii=[0.08, 0.075, 0.11])]) for h in hair]
    beard = [Prim("cone", HAIR, a=hc + [0.06, 0, -0.12], b=hc + [0.1, 0, -0.24], r1=0.05, r2=0.012)]
    model.group(0.02, hair + beard, disp=(0.012, 38))
    return model


def make_hook(signal):
    def hook(matId, pts, nrm, grain, albedo, spec, emit):
        if matId == SKIN:
            blotch = value_noise(pts * 9 + 2.7)
            vein = np.clip(1.0 - np.abs(value_noise(pts * 16) - 0.5) * 16, 0, 1)
            albedo = albedo * (0.75 + 0.45 * blotch)[:, None] * (1.0 - 0.35 * vein)[:, None]
        if matId in (SHIRT, TROUSERS, APRON, WRAPS):
            # mech i plesń tam, gdzie osiada wilgoć: na górnych powierzchniach
            moss = np.clip((value_noise(pts * 11 + 5.0) - 0.55) * 4.0, 0, 1) * np.clip(nrm[:, 2] * 1.5, 0, 1)
            albedo = albedo * (1 - moss[:, None]) + MOSS[None, :] * moss[:, None]
        if matId == EDGE and signal:
            # sygnał ataku nieparowalnego: zarzewie na krawędzi
            emit = emit + np.array([1.6, 0.18, 0.05])[None, :] * (0.7 + 0.3 * grain[:, None])
        return albedo, spec, emit
    return hook


def render_dir(args):
    dirIndex, signal, frameSize, outDir = args
    import math
    supersample = 3
    model = build_drwal()
    angle = -dirIndex * math.pi / 4
    image = render(model, MATERIALS, angle, frameSize * supersample, extent=3.2, centerZ=1.2, shade_hook=make_hook(signal))
    frame = downsample(image, supersample)
    suffix = "" if signal else "_bez-sygnalu"
    path = os.path.join(outDir, f"drwal_rozlupanie_{dirIndex}_{DIRECTIONS[dirIndex]}{suffix}.png")
    Image.fromarray((frame * 255 + 0.5).astype(np.uint8), "RGBA").save(path)
    return path


if __name__ == "__main__":
    args = sys.argv[1:]
    signal = "--bez-sygnalu" not in args
    frameSize = int(args[args.index("--rozmiar") + 1]) if "--rozmiar" in args else 192
    which = args[0] if args and not args[0].startswith("--") else "7"
    dirs = range(8) if which == "all" else [int(which)]
    outDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(outDir, exist_ok=True)
    with Pool(min(4, len(dirs))) as pool:
        for path in pool.imap(render_dir, [(d, signal, frameSize, outDir) for d in dirs]):
            print("ok", path)
