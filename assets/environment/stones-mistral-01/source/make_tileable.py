# Robi tekstury bezszwowymi: offset o polowe + wygladzenie szwow (feathered blend).
# Wejscie: albedo z main; wyjscie: wersje tileable + PBR (height/normal/rough).
import numpy as np
from PIL import Image
import os, sys, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_pbr_from_albedo import luminance, blur, normal_from_height

SRC = "/workspace/github__DawidWrona92__RPG-OldSchool/assets/textures/environment"
DST = "/workspace/envwork/textures_pbr"

def feather_mask(h, w, axis, f):
    m = np.ones((h, w))
    if axis == 0:
        ramp = 0.5 - 0.5*np.cos(np.pi*np.arange(f)/f)
        m[:f, :] *= ramp[:, None]
        m[-f:, :] *= ramp[::-1][:, None]
    else:
        ramp = 0.5 - 0.5*np.cos(np.pi*np.arange(f)/f)
        m[:, :f] *= ramp[None, :]
        m[:, -f:] *= ramp[::-1][None, :]
    return m

def make_tileable(img, f=96):
    # 1) roll by half so seams move to the middle
    h, w = img.shape[:2]
    rolled = np.roll(img, (h//2, w//2), axis=(0, 1))
    # 2) blend a wrapped copy over the seam cross with feathered masks
    base = rolled.copy()
    for axis in (0, 1):
        m = feather_mask(h, w, axis, f)
        wrapped = np.roll(rolled, (h//2 if axis==0 else 0, w//2 if axis==1 else 0), axis=(0, 1))
        base = base*(1-m[..., None] if img.ndim==3 else 1-m) + (wrapped*(m[..., None] if img.ndim==3 else m))
    # 3) roll back — seams now at edges, blended
    out = np.roll(base, (h//2, w//2), axis=(0, 1))
    return out

def process(path, out_dir, strength, wet):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im, dtype=np.float64)/255.0
    a = make_tileable(a)
    lum = luminance(a)
    h1 = blur(lum.copy(), 2); h2 = blur(lum.copy(), 8); h3 = blur(lum.copy(), 24)
    height = np.clip(0.5*h1 + 0.3*h2 + 0.2*h3, 0, 1)
    if wet:
        height = np.clip(height - np.clip((0.25-lum)*2.2, 0, 0.5), 0, 1)
    normal = normal_from_height(height, strength)
    rough = np.clip(0.45 + (h1-lum)*2.0 + lum*0.25, 0.25, 0.95)
    if wet:
        rough = np.clip(rough - np.clip((0.25-lum)*2.5, 0, 0.45), 0.08, 0.95)
    name = os.path.splitext(os.path.basename(path))[0]
    os.makedirs(out_dir, exist_ok=True)
    Image.fromarray((a*255).astype(np.uint8)).save(f"{out_dir}/{name}_color.png")
    Image.fromarray((height*255).astype(np.uint8)).save(f"{out_dir}/{name}_height.png")
    Image.fromarray((normal*255).astype(np.uint8)).save(f"{out_dir}/{name}_normal.png")
    Image.fromarray((rough*255).astype(np.uint8)).save(f"{out_dir}/{name}_rough.png")
    d1 = np.abs(lum[0]-lum[-1]).mean(); d2 = np.abs(lum[:,0]-lum[:,-1]).mean()
    inner = np.abs(lum[2:, 2:] - lum[:-2, :-2]).mean() + 1e-9
    return {"name": name, "seam_ratio": round(float((d1+d2)/2/inner), 3)}

def main():
    results = []
    for sub in ("ground", "rock", "bark"):
        d = os.path.join(SRC, sub)
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".png"): continue
            wet = "mud" in fn or "puddle" in fn or "wet" in fn
            r = process(os.path.join(d, fn), os.path.join(DST, sub), 2.5 if sub=="rock" else 2.0, wet)
            r["category"] = sub; results.append(r)
    with open(os.path.join(DST, "tileable_report.json"), "w") as fh:
        json.dump(results, fh, indent=1)
    for r in results:
        print(f"{r['category']}/{r['name']}: seam_ratio={r['seam_ratio']}")

if __name__ == "__main__":
    main()
