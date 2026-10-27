import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from meshkit import (Mesh, ShadowMap, ellipsoid_mesh, box_mesh, render_frame, ANCHOR)
from PIL import Image

MATS = {
    0: dict(alb=(0.1, 0.08, 0.06), spec=0.1, pw=8, grit=0.8),
    1: dict(alb=(0.06, 0.05, 0.045), spec=0.45, pw=24, grit=1.1, specTint=0.5),
}

# prosta "postać": tułów elipsoida 1,0 m, głowa 0,24, stopa na z=0
m1 = ellipsoid_mesh([0.0, 0.0, 1.05], [0.16, 0.2, 0.45], 0, nu=20, nv=14)
m2 = ellipsoid_mesh([0.0, 0.0, 1.68], [0.09, 0.09, 0.1], 0, nu=14, nv=10)
m3 = box_mesh([0.1, -0.25, 0.05], [0.09, 0.04, 0.03], 0)  # stopa
m4 = box_mesh([0.35, -0.2, 1.2], [0.02, 0.02, 0.3], 1)   # "miecz" pionowo
meshes = [m1, m2, m3, m4]
sm = ShadowMap(size=128, half=2.0)
sm.rasterize(meshes)
t0 = time.time()
img = render_frame(meshes, MATS, 0, shadow=sm, supersample=2)
dt = time.time() - t0
a = img[..., 3]
ys, xs = np.where(a > 10)
print(f"render {dt:.2f}s, pikseli alfa>10: {len(ys)}")
print(f"bbox x {xs.min()}..{xs.max()}, y {ys.min()}..{ys.max()}")
print(f"kotwica oczekiwana: {ANCHOR} (stopa powinna być w okolicy)")
# najniższy piksel postaci ~ stopa; oczekiwane y ~ ANCHOR[1] + mały offset (stopa ma grubość)
Image.fromarray(img, "RGBA").save("/workspace/.vibe/tool-results/smoke_d0.png")
# atlas 8 kierunków na szybko
sheet = Image.new("RGBA", (192 * 8, 192 + 14), (35, 41, 31, 255))
from PIL import ImageDraw
dr = ImageDraw.Draw(sheet)
for d in range(8):
    im = render_frame(meshes, MATS, d, shadow=sm, supersample=2)
    sheet.alpha_composite(Image.fromarray(im, "RGBA"), (d * 192, 14))
    dr.text((d * 192 + 4, 1), f"d{d}", fill=(200, 200, 190, 255))
sheet.save("/workspace/.vibe/tool-results/smoke_arkusz.png")
print("zapisano smoke_arkusz.png")
