# Generuje env_01.json — metadane assetów środowiska wg kontraktu.
import json, os
import numpy as np
from PIL import Image

OUT = os.environ.get("WELESZA_OUT", "/workspace/envwork/renders_v43")
PPM = 60.0
ANCHOR = (96.0, 158.35382907247958)

def bbox_meters(png):
    a = np.asarray(Image.open(png).convert('RGBA'))
    al = a[..., 3] > 10
    ys, xs = np.where(al)
    if len(xs) == 0:
        return None
    w_px = xs.max() - xs.min()
    h_px = ys.max() - ys.min()
    return {
        "width_m": round(w_px / PPM, 3),
        "height_m": round(h_px / PPM, 3),
        "bbox_px": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
    }

# prawdziwe wymiary 3D odczytane z .blend (bbox świata w metrach)
def mesh_dims_3d(obj_name, blend="/workspace/envwork/welesza_env_01.blend"):
    import bpy, mathutils
    bpy.ops.wm.open_mainfile(filepath=blend)
    ob = bpy.data.objects[obj_name]
    bb = [ob.matrix_world @ mathutils.Vector(c) for c in ob.bound_box]
    xs = [p.x for p in bb]; ys = [p.y for p in bb]; zs = [p.z for p in bb]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return {
        "width_m": round(max(xs)-min(xs), 3),   # X
        "depth_m": round(max(ys)-min(ys), 3),    # Y
        "height_m": round(max(zs)-min(zs), 3),  # Z
    }

def collision_estimate_3d(obj_name):
    d = mesh_dims_3d(obj_name)
    radius = max(d["width_m"], d["depth_m"]) / 2
    return {"type": "circle", "radius_m": round(radius, 3),
            "footprint_m": [d["width_m"], d["depth_m"]],
            "note": "obrys w plaszczyznie X/Y swiata; orientacyjne, do weryfikacji w grze"}

def build():
    assets = {}
    specs = [
        ("kamien_a", ["", "_rot47", "_rot113"]),
        ("kamien_b", [""]),
        ("kamien_c", [""]),
        ("glaz", [""]),
        ("kepka_trawy_a", [""]), ("kepka_trawy_b", [""]), ("kepka_trawy_c", [""]),
        ("paproc_a", [""]), ("paproc_b", [""]),
        ("chrust_a", [""]), ("chrust_b", [""]),
    ]
    objs = {"kamien_a": "kamien_a", "kamien_b": "kamien_b", "kamien_c": "kamien_c",
            "glaz": "glaz", "kepka_trawy_a": "kepka_trawy_a", "kepka_trawy_b": "kepka_trawy_b",
            "kepka_trawy_c": "kepka_trawy_c", "paproc_a": "paproc_a", "paproc_b": "paproc_b",
            "chrust_a": "chrust_a", "chrust_b": "chrust_b"}
    for aid, variants in specs:
        obj_name = objs[aid]
        frame = 320 if aid == "glaz" else 192
        anchor = [160.0, 263.92304845413263] if aid == "glaz" else list(ANCHOR)  # 96;158.35 * 320/192
        entry = {
            "frame_size": [frame, frame],
            "anchor_px": anchor,
            "pixels_per_meter": PPM,
            "files": {},
        }
        for suf in variants:
            f = f"{aid}{suf}.png"
            path = os.path.join(OUT, f)
            if not os.path.exists(path):
                continue
            entry["files"][f] = {
                "shadow_file": f"{aid}{suf}_shadow.png",
                "variants_rotation_deg": {"": 0, "_rot47": 47, "_rot113": 113}.get(suf, 0),
                "screen_bbox_px": bbox_meters(path)["bbox_px"],
            }
        entry["dimensions_3d"] = mesh_dims_3d(obj_name)
        entry["collision_estimate"] = collision_estimate_3d(obj_name)
        assets[aid] = entry
    doc = {
        "pack": "stones-mistral-01",
        "version": "v2-kontrakt",
        "frame_size_default": [192, 192],
        "anchor_px": list(ANCHOR),
        "pixels_per_meter": PPM,
        "camera_elevation_deg": 30,
        "assets": assets,
    }
    with open(os.path.join(OUT, "env_01.json"), "w") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
    print("env_01.json saved")

if __name__ == "__main__":
    build()
