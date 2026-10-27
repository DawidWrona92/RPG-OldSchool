"""Kontrola eksportu assetów otoczenia według kontraktu renderu.

Sprawdza katalog eksportu z env_01.json:
- każdy asset ma obraz i cień w rozmiarze frame_size z JSON;
- obraz obiektu nie dotyka krawędzi klatki (cień może — wtedy ostrzeżenie);
- kotwica = (N/2; N/2 + 62,354) dla klatki N;
- opcjonalnie (--fresh KATALOG) identyczność pikseli ze świeżym renderem;
- opcjonalnie (--blend PLIK, wymaga bpy) szczelność brył: brak krawędzi brzegowych
  nad ziemią (z > 0,01 m) w siatkach po modyfikatorach.

  python check_env_export.py EKSPORT [--fresh OUT] [--blend SCENA.blend] [--prefix kamien glaz]

Kod wyjścia 1 przy jakimkolwiek błędzie.
"""
import argparse, glob, json, os, sys

import numpy as np
from PIL import Image

ANCHOR_DROP = 62.35382907247958  # 1,2 m · cos 30° · 60 px/m


def rgba(path):
    return np.asarray(Image.open(path).convert("RGBA")).astype(int)


def touches_edge(alpha):
    return bool(alpha[0].any() or alpha[-1].any() or alpha[:, 0].any() or alpha[:, -1].any())


def check_export(export, fresh):
    data = json.load(open(os.path.join(export, "env_01.json"), encoding="utf-8"))
    errors, warnings = [], []
    for aid, spec in data["assets"].items():
        size = spec["frame_size"][0]
        ax, ay = spec["anchor_px"]
        if abs(ax - size / 2) > 0.01 or abs(ay - (size / 2 + ANCHOR_DROP)) > 0.01:
            errors.append(f"{aid}: kotwica {spec['anchor_px']} zamiast ({size / 2}; {size / 2 + ANCHOR_DROP:.3f})")
        for name, file_spec in spec.get("files", {}).items():
            for path, is_shadow in ((name, False), (file_spec.get("shadow_file"), True)):
                if not path:
                    errors.append(f"{aid}: brak pliku cienia dla {name}")
                    continue
                full = os.path.join(export, path)
                if not os.path.exists(full):
                    errors.append(f"{path}: brak pliku")
                    continue
                img = rgba(full)
                if img.shape[0] != size or img.shape[1] != size:
                    errors.append(f"{path}: {img.shape[1]}×{img.shape[0]} zamiast {size}×{size}")
                if touches_edge(img[..., 3] > 0):
                    (warnings if is_shadow else errors).append(f"{path}: dotyka krawędzi klatki")
                if fresh:
                    other = os.path.join(fresh, path)
                    if not os.path.exists(other):
                        errors.append(f"{path}: brak w świeżym renderze")
                    elif int(np.abs(img - rgba(other)).max()) != 0:
                        errors.append(f"{path}: różni się od świeżego renderu")
    pngs = {os.path.basename(p) for p in glob.glob(os.path.join(export, "*.png"))}
    listed = {f for s in data["assets"].values() for n, fs in s.get("files", {}).items() for f in (n, fs.get("shadow_file")) if f}
    for extra in sorted(pngs - listed):
        warnings.append(f"{extra}: plik spoza env_01.json")
    return errors, warnings


def check_blend(blend, prefixes):
    import bpy
    import bmesh
    bpy.ops.wm.open_mainfile(filepath=blend)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    errors = []
    for obj in bpy.data.objects:
        if obj.type != "MESH" or not obj.name.startswith(tuple(prefixes)):
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        bm = bmesh.new()
        bm.from_mesh(mesh)
        open_edges = [e for e in bm.edges if e.is_boundary
                      and (evaluated.matrix_world @ ((e.verts[0].co + e.verts[1].co) / 2)).z > 0.01]
        if open_edges:
            errors.append(f"{obj.name}: {len(open_edges)} otwartych krawędzi nad ziemią")
        bm.free()
        evaluated.to_mesh_clear()
    return errors


def main():
    p = argparse.ArgumentParser()
    p.add_argument("export")
    p.add_argument("--fresh", help="katalog świeżego renderu do porównania pikseli")
    p.add_argument("--blend", help="scena .blend do kontroli szczelności (wymaga bpy)")
    p.add_argument("--prefix", nargs="+", default=["kamien", "glaz", "plyta", "zwir"],
                   help="obiekty-bryły do kontroli szczelności")
    args = p.parse_args()
    errors, warnings = check_export(args.export, args.fresh)
    if args.blend:
        errors += check_blend(args.blend, args.prefix)
    for w in warnings:
        print("UWAGA ", w)
    for e in errors:
        print("BŁĄD  ", e)
    print(f"wynik: {len(errors)} błędów, {len(warnings)} uwag")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
