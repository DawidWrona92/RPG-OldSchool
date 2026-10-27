"""Buduje sceny środowiska Weleszy i renderuje assety: kamienie, głaz, podłoże, scena testowa.

Uruchomienie (wymaga bpy jako modułu Pythona — Blender 5.2 wheel):
    PYTHONPATH=<ścieżka do rozpakowanego bpy> \
    LD_LIBRARY_PATH=<ścieżka do bibliotek X11/GL> \
    python3.13 assets/environment/stones/source/build_env.py [--only NAZWA]

Sekcje (--only): stones, grounds, scene, all (domyślnie)
Wyniki zapisywane do assets/environment/stones/renders/ (384 px, PNG RGBA).
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
RENDERS = os.path.join(ROOT, "renders")
os.makedirs(RENDERS, exist_ok=True)

sys.path.insert(0, HERE)
import bpy  # noqa: E402
import envlib as E  # noqa: E402


# ---------- 1. Kamienie i głaz ----------

STONES = [
    # name, typ, rozmiar (średnica), wysokość, seed, opis kształtu
    dict(name="kamien_01_okrągły", kind="stone", radius=0.32, height=0.22,
         seed=1, flatness=0.72, wet=True, moss=False,
         desc="okrągławy, niski, jak otoczak spod korzenia"),
    dict(name="kamien_02_kanciasty", kind="stone", radius=0.28, height=0.30,
         seed=5, flatness=0.9, wet=True, moss=True,
         desc="kanciasty, wyższy, z płaską górą — stoi, nie leży"),
    dict(name="kamien_03_płaski", kind="stone", radius=0.40, height=0.14,
         seed=9, flatness=0.55, wet=False, moss=True,
         desc="płaski, szeroki — jak płyta wystająca z ziemi"),
    dict(name="glaz_01", kind="boulder", size=1.15,
         seed=7, wet=True, moss=True,
         desc="duży głaz przy drodze, niski i szeroki, z mchem"),
]


def build_stones(only=None):
    """Każdy kamień: render osobno (tło przezroczyste) na wspólnej kamerze."""
    scene, col = E.reset_scene()
    E.setup_camera(col, target=(0, 0, 0.5), ortho_w=2.2)
    E.setup_lights(col)
    mats = {
        "stone": E.stone_material("Kamien_Mokry", wet=True, moss=False),
        "stone_moss": E.stone_material("Kamien_Mchowy", wet=True, moss=True),
        "stone_dry": E.stone_material("Kamien_Suchy_Mchowy", wet=False, moss=True),
    }
    results = []
    # only=None -> wszystkie kamienie; set nazw -> tylko wybrane
    selected = only if isinstance(only, set) else None
    for spec in STONES:
        if selected and spec["name"] not in selected:
            continue
        # czysta scena per asset (bez innych kamieni)
        for obj in list(col.objects):
            if obj.name not in ("IsoCam", "Key_Cool", "Fill_Ground", "Rim_Cool"):
                bpy.data.objects.remove(obj, do_unlink=True)
        # materiał
        if spec["kind"] == "boulder":
            mat = mats["stone_moss"]
        elif spec.get("moss"):
            mat = mats["stone_dry"] if not spec.get("wet") else mats["stone_moss"]
        else:
            mat = mats["stone"]
        if spec["kind"] == "boulder":
            obj = E.make_boulder(spec["name"], col, size=spec["size"], seed=spec["seed"],
                                 mat=mat, location=(0, 0, 0),
                                 rotation=(0.06, -0.04, 0.15))
        else:
            obj = E.make_stone(spec["name"], col, radius=spec["radius"],
                               height=spec["height"], seed=spec["seed"],
                               flatness=spec["flatness"], mat=mat,
                               location=(0, 0, 0), rotation=(0.05, 0.03, 0.3))
        # obrót kamienia — pokażemy też wariant obrócony (dla kamienia 01)
        path = os.path.join(RENDERS, spec["name"] + ".png")
        E.render(scene, path, size=E.RENDER_HI)
        print("ok", path, flush=True)
        # wariant obrócony (tylko kamień 01 i głaz — pokazuje różnorodność z jednego modelu)
        if spec["name"] in ("kamien_01_okrągły", "glaz_01"):
            obj.rotation_euler = (obj.rotation_euler.x, obj.rotation_euler.y,
                                  obj.rotation_euler.z + math.radians(120))
            path2 = os.path.join(RENDERS, spec["name"] + "_rot120.png")
            E.render(scene, path2, size=E.RENDER_HI)
            print("ok", path2, flush=True)
        results.append(spec["name"])
    return results


# ---------- 2. Podłoże ----------

def build_grounds():
    """Dwa materiały podłoża: próbka 1×1 m i duża powierzchnia 6×6 m (test kafelkowania)."""
    out = []
    # --- próbki 1×1 m (pojedynczy kafelek, ortho z góry lekko z ukosa) ---
    for name, mat_name, maker in (
        ("bloto_trakt", "Bloto_Trakt_Mokre", E.mud_material),
        ("sciolka_lesna", "Sciółka_Leśna", E.litter_material),
    ):
        scene, col = E.reset_scene()
        E.setup_camera(col, target=(0, 0, 0.0), ortho_w=1.4)
        E.setup_lights(col)
        mat = maker(mat_name, wet=True) if "bloto" in name else maker(mat_name)
        E.make_ground_plane("Ground_1x1", col, size=1.0, mat=mat)
        if "sciolka" in name:
            # ściółka z liśćmi — więcej, różne rozmiary
            ml = E.leaf_material("Lisc", "leaf")
            mn = E.leaf_material("Igla", "needle")
            E.scatter_leaves(col, (-0.5, -0.5, 0.5, 0.5), 40,
                             size_range=(0.03, 0.07), mat_leaf=ml, mat_needle=mn, seed=11)
        path = os.path.join(RENDERS, f"probka_{name}_1x1.png")
        E.render(scene, path, size=E.RENDER_HI)
        print("ok", path, flush=True)
        out.append(path)

    # --- duże powierzchnie 6×6 m (test szwów / powtarzalności) ---
    for name, mat_name, maker, with_leaves in (
        ("bloto_trakt", "Bloto_Trakt_Mokre", E.mud_material, False),
        ("sciolka_lesna", "Sciółka_Leśna", E.litter_material, True),
    ):
        scene, col = E.reset_scene()
        # kamera bardziej z boku, żeby widać było nierówności
        E.setup_camera(col, target=(0, 0, 0.2), ortho_w=6.4)
        E.setup_lights(col)
        mat = maker(mat_name, wet=True) if "bloto" in name else maker(mat_name)
        E.make_ground_plane("Ground_6x6", col, size=6.0, mat=mat)
        if with_leaves:
            ml = E.leaf_material("Lisc", "leaf")
            mn = E.leaf_material("Igla", "needle")
            E.scatter_leaves(col, (-3, -3, 3, 3), 400,
                             size_range=(0.03, 0.08), mat_leaf=ml, mat_needle=mn, seed=42)
        path = os.path.join(RENDERS, f"powierzchnia_{name}_6x6.png")
        E.render(scene, path, size=768)
        print("ok", path, flush=True)
        out.append(path)

    # --- przejście błoto → ściółka (pół na pół, nieregularna granica) ---
    scene, col = E.reset_scene()
    E.setup_camera(col, target=(0, 0, 0.2), ortho_w=4.4)
    E.setup_lights(col)
    mud = E.mud_material("Bloto_Trakt_Mokre", wet=True)
    lit = E.litter_material("Sciółka_Leśna")
    # lewa połowa (x<0): błoto, prawa (x>0): ściółka; granica nieregularna przez noise
    bpy.ops.mesh.primitive_plane_add(size=4.0, location=(-1.0, 0, 0))
    mud_plane = bpy.context.active_object
    mud_plane.name = "Bloto"
    col.objects.link(mud_plane)
    try:
        bpy.context.collection.objects.unlink(mud_plane)
    except Exception:
        pass
    mud_plane.data.materials.append(mud)
    bpy.ops.mesh.primitive_plane_add(size=4.0, location=(1.0, 0, 0))
    lit_plane = bpy.context.active_object
    lit_plane.name = "Sciolka"
    col.objects.link(lit_plane)
    try:
        bpy.context.collection.objects.unlink(lit_plane)
    except Exception:
        pass
    lit_plane.data.materials.append(lit)
    # nieregularne "zęby" granicy: małe kliny ściółki wchodzące w błoto
    import random
    rng = random.Random(7)
    ml = E.leaf_material("Lisc", "leaf")
    mn = E.leaf_material("Igla", "needle")
    for i in range(14):
        x = rng.uniform(-0.55, -0.05)
        y = rng.uniform(-1.8, 1.8)
        w = rng.uniform(0.15, 0.45)
        bpy.ops.mesh.primitive_plane_add(size=1.0, location=(x + w / 2, y, 0.002))
        wedge = bpy.context.active_object
        wedge.name = f"Przejscie_{i}"
        col.objects.link(wedge)
        try:
            bpy.context.collection.objects.unlink(wedge)
        except Exception:
            pass
        wedge.scale = (w, rng.uniform(0.1, 0.3), 1.0)
        bpy.ops.object.transform_apply(scale=True)
        wedge.data.materials.append(lit)
    E.scatter_leaves(col, (-1.2, -1.8, 0.4, 1.8), 120,
                     size_range=(0.025, 0.06), mat_leaf=ml, mat_needle=mn, seed=23)
    path = os.path.join(RENDERS, "przejscie_bloto_sciolka.png")
    E.render(scene, path, size=768)
    print("ok", path, flush=True)
    out.append(path)
    return out


# ---------- 3. Scena testowa ----------

def build_scene():
    """Mały fragment traktu: błoto + ściółka + 3 kamienie + głaz + znacznik skali."""
    scene, col = E.reset_scene()
    E.setup_camera(col, target=(0.2, 0.0, 0.7), ortho_w=5.6)
    E.setup_lights(col)

    mud = E.mud_material("Bloto_Trakt_Mokre", wet=True)
    lit = E.litter_material("Sciółka_Leśna")
    stone = E.stone_material("Kamien_Mokry", wet=True)
    stone_moss = E.stone_material("Kamien_Mchowy", wet=True, moss=True)
    stone_dry = E.stone_material("Kamien_Suchy_Mchowy", wet=False, moss=True)
    boulder = E.stone_material("Glaz_Mchowy", wet=True, moss=True,
                               base=(0.38, 0.40, 0.36))

    # Podłoże: trakt błotnisty (pas wzdłuż osi X) + ściółka po bokach
    # trakt: pas y ∈ [-0.9, 0.9], x ∈ [-2.6, 2.6]
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 0, 0))
    trakt = bpy.context.active_object
    trakt.name = "Trakt_Blotnisty"
    col.objects.link(trakt)
    try:
        bpy.context.collection.objects.unlink(trakt)
    except Exception:
        pass
    trakt.scale = (5.2, 1.8, 1.0)
    bpy.ops.object.transform_apply(scale=True)
    trakt.data.materials.append(mud)

    # ściółka: dwa płaty po bokach traktu
    for sx, nm in ((-1, "Sciolka_Lewa"), (1, "Sciolka_Prawa")):
        bpy.ops.mesh.primitive_plane_add(size=1.0, location=(sx * 2.2, 0, -0.01))
        p = bpy.context.active_object
        p.name = nm
        col.objects.link(p)
        try:
            bpy.context.collection.objects.unlink(p)
        except Exception:
            pass
        p.scale = (2.6, 2.6, 1.0)
        bpy.ops.object.transform_apply(scale=True)
        p.data.materials.append(lit)

    # liście na ściółce
    ml = E.leaf_material("Lisc", "leaf")
    mn = E.leaf_material("Igla", "needle")
    E.scatter_leaves(col, (-4.6, -2.6, -1.0, 2.6), 180,
                     size_range=(0.03, 0.07), mat_leaf=ml, mat_needle=mn, seed=5, z=-0.008)
    E.scatter_leaves(col, (1.0, -2.6, 4.6, 2.6), 180,
                     size_range=(0.03, 0.07), mat_leaf=ml, mat_needle=mn, seed=6, z=-0.008)
    # kilka liści na skraju błota (przejście)
    E.scatter_leaves(col, (-1.1, -1.2, 1.1, 1.2), 40,
                     size_range=(0.025, 0.05), mat_leaf=ml, mat_needle=mn, seed=8, z=0.002)

    # Kamienie: trzy różne + głaz, rozmieszczone wzdłuż traktu
    E.make_stone("Kamien_01", col, radius=0.32, height=0.22, seed=1, flatness=0.72,
                 mat=stone, location=(-1.6, 1.35, 0.0), rotation=(0.05, 0.03, 0.3))
    E.make_stone("Kamien_02", col, radius=0.28, height=0.30, seed=5, flatness=0.9,
                 mat=stone_moss, location=(0.9, -1.45, 0.0), rotation=(-0.04, 0.06, 1.2))
    E.make_stone("Kamien_03", col, radius=0.40, height=0.14, seed=9, flatness=0.55,
                 mat=stone_dry, location=(1.9, 1.1, 0.0), rotation=(0.03, -0.05, 2.1))
    E.make_boulder("Glaz_01", col, size=1.15, seed=7, mat=boulder,
                   location=(-2.1, -1.5, 0.0), rotation=(0.06, -0.04, 0.15))

    # znacznik skali — człowiek 1,8 m przy głazie
    E.make_scale_marker(col, height=1.8, location=(-0.9, -1.9, 0.0))

    path = os.path.join(RENDERS, "scena_testowa_trakt.png")
    E.render(scene, path, size=768)
    print("ok", path, flush=True)

    # drugi kadr: zbliżenie na materiały (bez znacznika, niższa kamera)
    for obj in list(col.objects):
        if obj.name.startswith("ScaleMarker"):
            bpy.data.objects.remove(obj, do_unlink=True)
    cam = bpy.data.objects["IsoCam"]
    cam.data.ortho_scale = 2.8
    # przesuń kamerę bliżej centrum materiałów
    tgt = (0.0, 0.0, 0.35)
    dist = 20.0
    from mathutils import Vector
    loc = Vector((
        tgt[0] - dist * math.cos(E.ELEVATION) * math.cos(E.CAM_AZIMUTH),
        tgt[1] - dist * math.cos(E.ELEVATION) * math.sin(E.CAM_AZIMUTH),
        tgt[2] + dist * math.sin(E.ELEVATION),
    ))
    cam.location = loc
    cam.rotation_euler = (Vector(tgt) - loc).to_track_quat("-Z", "Y").to_euler()
    path2 = os.path.join(RENDERS, "scena_testowa_zblizenie.png")
    E.render(scene, path2, size=768)
    print("ok", path2, flush=True)
    return [path, path2]


# ---------- main ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="all",
                    help="all|stones|grounds|scene lub lista nazw assetów po przecinku "
                         "(np. kamien_01_okrągły,glaz_01)")
    args = ap.parse_args()
    only = None if args.only == "all" else set(args.only.split(","))
    # Rozpoznaj sekcje: all wykonuje wszystko; pojedyncze nazwy trafiają do kamieni
    names = only
    if names is None or names == {"stones"}:
        build_stones(only=None)
    elif names == {"grounds"}:
        build_grounds()
    elif names == {"scene"}:
        build_scene()
    else:
        # lista nazw assetów (mogą być kamienie) — przekaż tylko do build_stones
        build_stones(only=names)
    print("GOTOWE")


if __name__ == "__main__":
    main()
