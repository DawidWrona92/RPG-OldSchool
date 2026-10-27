"""Przenikania siatek w wybranej klatce pliku .blend (Blender 4.3 / bpy 4.3.0).

Liczy przecinające się pary trójkątów między wszystkimi renderowanymi siatkami,
po modyfikatorach (szkielet, wygładzanie, grubość). Zamierzone styki można
pominąć wzorcami nazw w --allow (np. "Oko*|Tęczówka*").

  python check_intersections.py postac.blend --action spoczynek --frame 1
  python check_intersections.py postac.blend --action chod --all-frames --allow "Oko*|Tęczówka*"

Kod wyjścia 1, jeżeli zostały przenikania spoza listy dozwolonych.
"""
import argparse, fnmatch, itertools, json, sys

import bpy
from mathutils.bvhtree import BVHTree


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument("blend")
    p.add_argument("--rig", default=None, help="obiekt szkieletu; domyślnie pierwszy ARMATURE")
    p.add_argument("--action", default=None)
    p.add_argument("--frame", type=int, default=1)
    p.add_argument("--all-frames", action="store_true", help="cały zakres klatek akcji")
    p.add_argument("--allow", default="", help="pary dozwolone: 'wzorA~wzorB|wzorC' lub 'wzor' (obiekt z każdym)")
    p.add_argument("--top", type=int, default=30)
    p.add_argument("--json", default=None, help="zapisz pełny wynik do pliku")
    return p.parse_args(argv)


def allowed(a, b, rules):
    for rule in rules:
        if "~" in rule:
            x, y = rule.split("~", 1)
            if (fnmatch.fnmatch(a, x) and fnmatch.fnmatch(b, y)) or (fnmatch.fnmatch(a, y) and fnmatch.fnmatch(b, x)):
                return True
        elif fnmatch.fnmatch(a, rule) or fnmatch.fnmatch(b, rule):
            return True
    return False


def frame_pairs(depsgraph):
    trees = {}
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH" or obj.hide_render:
            continue
        ev = obj.evaluated_get(depsgraph)
        mesh = ev.to_mesh()
        verts = [ev.matrix_world @ v.co for v in mesh.vertices]
        polys = [tuple(poly.vertices) for poly in mesh.polygons]
        if polys:
            trees[obj.name] = BVHTree.FromPolygons(verts, polys)
        ev.to_mesh_clear()
    result = {}
    for a, b in itertools.combinations(sorted(trees), 2):
        count = len(trees[a].overlap(trees[b]))
        if count:
            result[(a, b)] = count
    return result


def main():
    args = parse_args()
    bpy.ops.wm.open_mainfile(filepath=args.blend)
    scene = bpy.context.scene
    rig = bpy.data.objects.get(args.rig) if args.rig else next((o for o in bpy.data.objects if o.type == "ARMATURE"), None)
    frames = [args.frame]
    if args.action:
        action = bpy.data.actions[args.action]
        rig.animation_data_create()
        rig.animation_data.action = action
        if args.all_frames:
            start, end = (int(f) for f in action.frame_range)
            frames = list(range(start, end + 1))
    rules = [r for r in args.allow.split("|") if r]
    worst = {}
    for frame in frames:
        scene.frame_set(frame)
        for pair, count in frame_pairs(bpy.context.evaluated_depsgraph_get()).items():
            if count > worst.get(pair, (0, 0))[0]:
                worst[pair] = (count, frame)
    bad = {p: v for p, v in worst.items() if not allowed(*p, rules)}
    ranked = sorted(bad.items(), key=lambda kv: -kv[1][0])
    print(f"klatki {frames[0]}–{frames[-1]}; par obiektów z przenikaniem: {len(worst)}, "
          f"po odjęciu dozwolonych: {len(bad)}; suma par trójkątów (najgorsza klatka każdej pary): "
          f"{sum(v[0] for v in bad.values())}")
    for (a, b), (count, frame) in ranked[:args.top]:
        print(f"{count:7d}  kl. {frame:3d}  {a}  <->  {b}")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump([{"a": a, "b": b, "triangles": c, "frame": f} for (a, b), (c, f) in ranked], fh, ensure_ascii=False, indent=1)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
