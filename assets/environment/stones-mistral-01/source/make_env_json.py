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

def collision_estimate(png):
    """Uproszczony obrys kolizji: okrąg o promieniu = połowa szerokości obrazu w metrach."""
    r = bbox_meters(png)
    if not r:
        return None
    return {"type": "circle", "radius_m": round(r["width_m"] / 2, 3), "note": "orientacyjne, do weryfikacji w grze"}

def build():
    assets = {}
    specs = [
        ("kamien_a", ["", "_rot47", "_rot113"]),
        ("kamien_b", [""]),
        ("kamien_c", [""]),
        ("glaz", [""]),
    ]
    for aid, variants in specs:
        entry = {
            "frame_size": [192, 192],
            "anchor_px": list(ANCHOR),
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
                **bbox_meters(path),
            }
        entry["collision_estimate"] = collision_estimate(os.path.join(OUT, f"{aid}.png"))
        # głaz nie mieści się w 192 — własna klatka (kontrakt: duże obiekty)
        if aid == "glaz":
            gb = bbox_meters(os.path.join(OUT, "glaz.png"))
            if gb:
                entry["frame_size"] = [192, 192]  # w tej wersji głaz przycięty do 192; patrz note
                entry["note"] = "glaz dotyka krawędzi klatki 192; wymaga większej klatki i własnej kotwicy — do poprawy w następnej iteracji"
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
