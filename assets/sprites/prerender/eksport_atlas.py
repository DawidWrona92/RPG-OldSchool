"""Eksport atlasu i podgladow animacji postaci prerenderowanej (SDF). Nowy plik; nie zmienia sdfkit.py.

Uzycie: python3 eksport_atlas.py <id-postaci> [wariant ...]
        np. python3 eksport_atlas.py zdziczaly-pies wa wb wc
Wymaga, zeby plik postaci <id>.py mial POSES i ANIMACJE (slownik: nazwa -> klatki, ms, loop, opcjonalnie zapowiedz_ms),
a klatki byly wyrenderowane do output/<id>/ (wariant wa bez sufiksu, pozostale z sufiksem _<wariant>).

Wynik w output/<id>/atlas/:
  <id>_<wariant>.png   atlas: kolumny = 8 kierunkow (S, SW, W, NW, N, NE, E, SE), wiersze = pozy w kolejnosci animacji
  <id>_<wariant>.json  opis: wymiary klatki, kotwica stop, regiony (x, y, w, h) per poza i kierunek, animacje z czasami [ms]
  podglad/<id>_<wariant>_<animacja>_<kierunek>.gif   podglady ruchu na tle lesnej ziemi

Godot 4: kazda klatka = AtlasTexture z region = (x, y, w, h); Sprite2D z offset = (-kotwica_x + 96, -kotwica_y + 96) tak, aby punkt
stop (kotwica) lezal w pozycji wezla; czasy z "animacje[...].ms" (SpriteFrames.set_animation_speed lub AnimationPlayer).
"""
import importlib.util
import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
DIRS = ["S", "SW", "W", "NW", "N", "NE", "E", "SE"]
FRAME = 192
ANCHOR = (96, 158)          # punkt (0, 0, 0) swiata w kazdej klatce kontraktu kadru
GROUND = (35, 41, 31, 255)


def load(charId):
    path = os.path.join(HERE, f"{charId}.py")
    spec = importlib.util.spec_from_file_location(charId.replace("-", "_"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def frame_path(charId, pose, d, variant):
    suffix = "" if variant == "wa" else f"_{variant}"
    return os.path.join(HERE, "output", charId, f"{charId}_{pose}_{d}_{DIRS[d]}{suffix}.png")


def export(charId, variant):
    module = load(charId)
    order = []
    for anim in module.ANIMACJE.values():
        for pose in anim["klatki"]:
            if pose not in order:
                order.append(pose)
    outDir = os.path.join(HERE, "output", charId, "atlas")
    os.makedirs(os.path.join(outDir, "podglad"), exist_ok=True)
    atlas = Image.new("RGBA", (FRAME * 8, FRAME * len(order)), (0, 0, 0, 0))
    regions = {}
    for row, pose in enumerate(order):
        regions[pose] = {}
        for d in range(8):
            atlas.alpha_composite(Image.open(frame_path(charId, pose, d, variant)).convert("RGBA"), (d * FRAME, row * FRAME))
            regions[pose][DIRS[d]] = [d * FRAME, row * FRAME, FRAME, FRAME]
    base = os.path.join(outDir, f"{charId}_{variant}")
    atlas.save(base + ".png")
    meta = {
        "postac": charId, "wariant": variant, "atlas": os.path.basename(base) + ".png",
        "klatka": [FRAME, FRAME], "kotwica_stop": list(ANCHOR), "kierunki": DIRS,
        "uwagi": "Kierunek = obrot modelu, nie lustro. Kotwica = punkt stop w pikselach klatki. Czasy w milisekundach.",
        "regiony": regions,
        "animacje": module.ANIMACJE,
    }
    with open(base + ".json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    # podglady ruchu: kazda animacja w kierunku SE i S, 2x, na tle lasu
    for name, anim in module.ANIMACJE.items():
        for d in (7, 0):
            frames = []
            for pose in anim["klatki"]:
                im = Image.new("RGBA", (FRAME, FRAME), GROUND)
                im.alpha_composite(Image.open(frame_path(charId, pose, d, variant)).convert("RGBA"))
                frames.append(im.crop((16, 56, 176, 176)).resize((320, 240), Image.LANCZOS).convert("P", palette=Image.ADAPTIVE))
            frames[0].save(os.path.join(outDir, "podglad", f"{charId}_{variant}_{name}_{DIRS[d]}.gif"), save_all=True,
                           append_images=frames[1:], duration=anim["ms"], loop=0 if anim["loop"] else 1, disposal=2)
    return base


if __name__ == "__main__":
    charId = sys.argv[1]
    for variant in (sys.argv[2:] or ["wa"]):
        print("ok", export(charId, variant))
