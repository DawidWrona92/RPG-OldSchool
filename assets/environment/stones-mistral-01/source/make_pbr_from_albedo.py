# Generuje height/normal/roughness z albedo (luminance-based) dla tekstur z main.
# Heurystyka: jasniejszy piksel = wyżej (kamyki, kępy), ciemniejszy = niżej (zagłębienia, woda).
import numpy as np
from PIL import Image
import os, sys, json

SRC = "/workspace/github__DawidWrona92__RPG-OldSchool/assets/textures/environment"
DST = "/workspace/envwork/textures_pbr"

def luminance(a):
    return 0.2126*a[...,0] + 0.7152*a[...,1] + 0.0722*a[...,2]

def blur(img, sigma):
    # tileable gaussian blur via numpy roll (wrap-around keeps seams intact)
    h, w = img.shape
    rad = int(3 * sigma)
    ax = np.arange(-rad, rad + 1)
    gx = np.exp(-(ax**2) / (2 * sigma**2)); gx /= gx.sum()
    gy = np.exp(-(ax**2) / (2 * sigma**2)); gy /= gy.sum()
    for kernel, axis in ((gy, 0), (gx, 1)):
        acc = np.zeros_like(img)
        for i, k in enumerate(range(-rad, rad + 1)):
            acc += kernel[i] * np.roll(img, k, axis=axis)
        img = acc
    return img

def normal_from_height(h, strength=2.0):
    dy = np.roll(h, -1, 0) - np.roll(h, 1, 0)
    dx = np.roll(h, -1, 1) - np.roll(h, 1, 1)
    n = np.stack([-dx*strength, -dy*strength, np.ones_like(h)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n*0.5 + 0.5

def process(path, out_dir, strength=2.0, wet_dark_means_water=False):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im, dtype=np.float64) / 255.0
    lum = luminance(a)
    # height: multi-scale blur of luminance
    h1 = blur(lum.copy(), 2)
    h2 = blur(lum.copy(), 8)
    h3 = blur(lum.copy(), 24)
    height = np.clip(0.5*h1 + 0.3*h2 + 0.2*h3, 0, 1)
    if wet_dark_means_water:
        # very dark patches -> depressions (puddles)
        height = np.clip(height - np.clip((0.25 - lum)*2.2, 0, 0.5), 0, 1)
    normal = normal_from_height(height, strength)
    # roughness: dark & smooth (wet) -> low rough; bright & grainy -> high rough
    rough = np.clip(0.45 + (h1 - lum)*2.0 + lum*0.25, 0.25, 0.95)
    if wet_dark_means_water:
        rough = np.clip(rough - np.clip((0.25 - lum)*2.5, 0, 0.45), 0.08, 0.95)
    name = os.path.splitext(os.path.basename(path))[0]
    os.makedirs(out_dir, exist_ok=True)
    Image.fromarray((height*255).astype(np.uint8)).save(f"{out_dir}/{name}_height.png")
    Image.fromarray((normal*255).astype(np.uint8)).save(f"{out_dir}/{name}_normal.png")
    Image.fromarray((rough*255).astype(np.uint8)).save(f"{out_dir}/{name}_rough.png")
    # seam check
    d1 = np.abs(lum[0]-lum[-1]).mean(); d2 = np.abs(lum[:,0]-lum[:,-1]).mean()
    inner = np.abs(lum[2:, 2:] - lum[:-2, :-2]).mean() + 1e-9
    return {"name": name, "seam_y": round(float(d1),4), "seam_x": round(float(d2),4),
            "inner_contrast": round(float(inner),4), "seam_ratio": round(float((d1+d2)/2/inner),2)}

def main():
    results = []
    for sub in ("ground", "rock", "bark"):
        d = os.path.join(SRC, sub)
        for f in sorted(os.listdir(d)):
            if not f.endswith(".png"): continue
            wet = "mud" in f or "puddle" in f or "wet" in f
            r = process(os.path.join(d, f), os.path.join(DST, sub), strength=2.5 if sub=="rock" else 2.0, wet_dark_means_water=wet)
            r["category"] = sub
            results.append(r)
    with open(os.path.join(DST, "pbr_report.json"), "w") as fh:
        json.dump(results, fh, indent=1)
    for r in results:
        print(f"{r['category']}/{r['name']}: seam_ratio={r['seam_ratio']} (y={r['seam_y']}, x={r['seam_x']}, inner={r['inner_contrast']})")

if __name__ == "__main__":
    main()
