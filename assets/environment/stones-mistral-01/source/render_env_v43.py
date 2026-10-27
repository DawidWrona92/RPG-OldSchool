# Welesza environment 01 — RENDER (Blender 4.3, bpy).
# Czyta .blend (źródło), renderuje assety wg kontraktu i zapisuje audyt SHA-256.
# NIE modyfikuje .blend.
import bpy, os, sys, json, hashlib, math

BASE = os.path.dirname(os.path.abspath(__file__))
BLEND = os.environ.get("WELESZA_BLEND", os.path.join(os.path.dirname(BASE), "welesza_env_01.blend"))
OUTDIR = os.environ.get("WELESZA_OUT", os.path.join(os.path.dirname(BASE), "renders_v43"))
AUDIT = os.path.join(OUTDIR, "audit.json")

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

bpy.ops.wm.open_mainfile(filepath=BLEND)
sc = bpy.context.scene
cam = sc.camera
os.makedirs(OUTDIR, exist_ok=True)

# ---------- AUDYT: odczyt ustawień z .blend (nie z pamięci) ----------
def read_settings():
    lights = []
    for o in bpy.data.objects:
        if o.type == "LIGHT":
            lights.append({
                "name": o.name, "type": o.data.type, "energy": round(o.data.energy, 1),
                "size": round(o.data.size, 2), "color": tuple(round(c, 3) for c in o.data.color),
                "location": tuple(round(c, 3) for c in o.location),
            })
    return {
        "blender_version": bpy.app.version_string,
        "blend_sha256": sha256(BLEND),
        "render_script_sha256": sha256(os.path.abspath(__file__)),
        "camera": {
            "type": cam.data.type, "ortho_scale": round(cam.data.ortho_scale, 4),
            "location": tuple(round(c, 4) for c in cam.location),
            "rotation_deg": tuple(round(math.degrees(a), 2) for a in cam.rotation_euler),
        },
        "lights": lights,
        "world": {"color": (0.18, 0.21, 0.26), "strength": 0.2},
        "render": {
            "engine": sc.render.engine, "samples": sc.cycles.samples, "seed": sc.cycles.seed,
            "filter_size": sc.render.filter_size, "threads": sc.render.threads,
            "film_transparent": sc.render.film_transparent,
            "resolution": [sc.render.resolution_x, sc.render.resolution_y],
            "view_transform": sc.view_settings.view_transform,
            "look": sc.view_settings.look, "exposure": round(sc.view_settings.exposure, 2),
            "denoising": sc.view_layers[0].cycles.use_denoising,
        },
    }

settings = read_settings()

# ---------- WSPÓLNE USTAWIENIA KAFELKI ----------
FRAME = 384   # render
FINAL = 192   # po zmniejszeniu
PPM = 60.0
ANCHOR_PX = (96.0, 158.35382907247958)

from PIL import Image

def resize_premultiplied(src, dst, size):
    """Zmniejszenie 384->192 z premultiplikowaną alfą (jak u bohatera)."""
    im = Image.open(src).convert("RGBA")
    a = im.split()[3]
    rgb = im.convert("RGB")
    # premultiply
    pm = Image.merge("RGBA", (*[rgb.split()[i].point(lambda v, i=i: int(v * (a.getpixel((0,0)) if False else 1))) for i in range(3)], a)) if False else None
    # prościej: numpy
    import numpy as np
    arr = np.asarray(im, dtype=np.float64)
    alpha = arr[..., 3:4] / 255.0
    prem = arr.copy()
    prem[..., :3] = arr[..., :3] * alpha
    pm_im = Image.fromarray(prem.astype("uint8"), "RGBA")
    small = pm_im.resize((size, size), Image.LANCZOS)
    # un-premultiply
    sa = np.asarray(small, dtype=np.float64)
    salpha = sa[..., 3:4] / 255.0
    out = sa.copy()
    nz = salpha > 0.003
    out[..., :3] = np.where(nz, sa[..., :3] / np.maximum(salpha, 1e-6), 0)
    Image.fromarray(np.clip(out, 0, 255).astype("uint8"), "RGBA").save(dst)

def render_object(obj_name, out_prefix, variants=((0.0, ""), )):
    """Render assetu: warianty rotacji Z; RGBA (sam asset) + osobny cień."""
    ob = bpy.data.objects[obj_name]
    catcher = bpy.data.objects.get("OdbiornikCienia")
    preview = bpy.data.objects.get("PodgladPodloze")
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    results = []
    for rot, suffix in variants:
        ob.rotation_euler[2] = rot
        # --- RGBA pass: TYLKO asset ---
        for o in meshes:
            o.hide_render = (o is not ob)
        sc.render.filepath = os.path.join(OUTDIR, f"{out_prefix}{suffix}.png")
        bpy.ops.render.render(write_still=True)
        # --- shadow pass: asset + catcher ---
        for o in meshes:
            o.hide_render = not (o is ob or o is catcher)
        if preview is not None:
            preview.hide_render = True
        sc.render.filepath = os.path.join(OUTDIR, f"{out_prefix}{suffix}_shadow.png")
        bpy.ops.render.render(write_still=True)
        results.append(f"{out_prefix}{suffix}.png")
        results.append(f"{out_prefix}{suffix}_shadow.png")
    ob.rotation_euler[2] = 0.0
    for o in meshes:
        o.hide_render = False
    return results

# ---------- RENDER ASSETÓW ----------
assets = {
    "kamien_a": {"obj": "kamien_a", "variants": ((0.0, ""), (math.radians(47), "_rot47"), (math.radians(113), "_rot113"))},
    "kamien_b": {"obj": "kamien_b", "variants": ((0.0, ""),)},
    "kamien_c": {"obj": "kamien_c", "variants": ((0.0, ""),)},
    "glaz": {"obj": "glaz", "variants": ((0.0, ""),)},
}
rendered = []
for aid, spec in assets.items():
    rendered += render_object(spec["obj"], aid, spec["variants"])

# ---------- ZMNIEJSZENIE 384->192 (premultiplied alpha) ----------
final_files = []
for f in rendered:
    src = os.path.join(OUTDIR, f)
    if os.path.exists(src):
        resize_premultiplied(src, src, FINAL)
        final_files.append(f)

# ---------- AUDYT ----------
audit = {"settings": settings, "rendered": {f: sha256(os.path.join(OUTDIR, f)) for f in final_files},
         "contract": {"frame": [FINAL, FINAL], "render_frame": [FRAME, FRAME],
                      "pixels_per_meter": PPM, "anchor_px": ANCHOR_PX}}
with open(AUDIT, "w") as fh:
    json.dump(audit, fh, indent=1, ensure_ascii=False)
print("RENDERED", len(final_files), "files; audit:", AUDIT)
