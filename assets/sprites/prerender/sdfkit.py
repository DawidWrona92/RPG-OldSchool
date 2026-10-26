"""Prerender SDF dla sprite'ów Weleszy.

Rdzeń (bryły SDF, materiały, raymarching, miękkie cienie, AO) pochodzi z renderera
rycerza i demona dostarczonego przez autora. Rozszerzenia: odejmowanie i przecinanie
brył, zaburzenie powierzchni szumem, cieniowanie materiałów pod paletę Weleszy
(ciemniej, mniej nasycenia), wyższe światło dające krótszy cień.
"""
import math
import numpy as np

np.seterr(divide="ignore", invalid="ignore")

# ---------- geometria SDF ----------


def normalize(vector):
    vector = np.asarray(vector, float)
    return vector / np.linalg.norm(vector)


def frame_from_axis(axis, hint=(0.0, 0.0, 1.0)):
    axisZ = normalize(axis)
    hintVec = np.asarray(hint, float)
    if abs(np.dot(hintVec, axisZ)) > 0.95:
        hintVec = np.array([1.0, 0.0, 0.0])
    axisX = normalize(np.cross(hintVec, axisZ))
    axisY = np.cross(axisZ, axisX)
    return np.stack([axisX, axisY, axisZ], axis=1)


def frame_from_axes(axisX, axisY, axisZ):
    return np.stack([normalize(axisX), normalize(axisY), normalize(axisZ)], axis=1)


class Prim:
    def __init__(self, kind, mat, **params):
        self.kind = kind
        self.mat = mat
        self.params = {key: (np.asarray(value, float) if isinstance(value, (list, tuple, np.ndarray)) else value) for key, value in params.items()}

    def eval(self, points):
        par = self.params
        if self.kind == "sphere":
            return np.linalg.norm(points - par["c"], axis=1) - par["r"]
        if self.kind == "ellipsoid":
            local = points - par["c"]
            if "R" in par:
                local = local @ par["R"]
            k0 = np.linalg.norm(local / par["radii"], axis=1)
            k1 = np.linalg.norm(local / (par["radii"] ** 2), axis=1)
            return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)
        if self.kind == "cone":
            pa = points - par["a"]
            ba = par["b"] - par["a"]
            h = np.clip(pa @ ba / np.dot(ba, ba), 0.0, 1.0)
            return np.linalg.norm(pa - h[:, None] * ba, axis=1) - (par["r1"] + (par["r2"] - par["r1"]) * h)
        if self.kind == "box":
            local = (points - par["c"]) @ par["R"]
            q = np.abs(local) - par["half"]
            outside = np.linalg.norm(np.maximum(q, 0.0), axis=1)
            inside = np.minimum(np.max(q, axis=1), 0.0)
            return outside + inside - par.get("round", 0.0)
        if self.kind == "cylinder":
            local = (points - par["c"]) @ par["R"]
            dx = np.sqrt(local[:, 0] ** 2 + local[:, 1] ** 2) - par["r"]
            dz = np.abs(local[:, 2]) - par["h"]
            return np.minimum(np.maximum(dx, dz), 0.0) + np.sqrt(np.maximum(dx, 0) ** 2 + np.maximum(dz, 0) ** 2) - par.get("round", 0.0)
        if self.kind == "torus":
            local = (points - par["c"]) @ par["R"]
            ring = np.sqrt(local[:, 0] ** 2 + local[:, 1] ** 2) - par["major"]
            return np.sqrt(ring ** 2 + local[:, 2] ** 2) - par["minor"]
        raise ValueError(self.kind)


class Sub:
    """Bryła `base` z wyciętymi bryłami `cuts` (materiał bazy)."""

    def __init__(self, base, cuts, smooth=0.0):
        self.base, self.cuts, self.smooth, self.mat = base, cuts, smooth, base.mat

    def eval(self, points):
        dist = self.base.eval(points)
        for cut in self.cuts:
            other = -cut.eval(points)
            dist = -smin(-dist, -other, self.smooth) if self.smooth > 0 else np.maximum(dist, other)
        return dist


class Isect:
    """Część wspólna brył (materiał pierwszej)."""

    def __init__(self, parts):
        self.parts, self.mat = parts, parts[0].mat

    def eval(self, points):
        dist = self.parts[0].eval(points)
        for part in self.parts[1:]:
            dist = np.maximum(dist, part.eval(points))
        return dist


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b + (a - b) * h - k * h * (1.0 - h)


class Model:
    def __init__(self):
        self.groups = []

    def group(self, smooth, prims, disp=None):
        """disp=(amplituda, częstotliwość): zaburzenie kształtu powierzchni szumem."""
        self.groups.append((smooth, prims, disp))

    def eval(self, points, wantMat=False):
        dist = np.full(len(points), 1e9)
        mat = np.full(len(points), -1, dtype=np.int32) if wantMat else None
        for smooth, prims, disp in self.groups:
            groupDist = None
            for prim in prims:
                d = prim.eval(points)
                if groupDist is None:
                    groupDist = d
                    if wantMat:
                        rawDist = d.copy()
                        groupMat = np.full(len(points), prim.mat, dtype=np.int32)
                    continue
                if wantMat:
                    closer = d < rawDist
                    rawDist = np.where(closer, d, rawDist)
                    groupMat = np.where(closer, prim.mat, groupMat)
                groupDist = smin(groupDist, d, smooth) if smooth > 0 else np.minimum(groupDist, d)
            if disp is not None:
                amp, freq = disp
                near = groupDist < amp * 3
                if np.any(near):
                    sel = np.where(near)[0]
                    groupDist[sel] += amp * (2.0 * value_noise(points[sel] * freq + 11.3) - 1.0)
            if wantMat:
                mat = np.where(groupDist < dist, groupMat, mat)
            dist = np.minimum(dist, groupDist)
        return (dist, mat) if wantMat else dist


def chain(points, radii, mat):
    return [Prim("cone", mat, a=points[i], b=points[i + 1], r1=radii[i], r2=radii[i + 1]) for i in range(len(points) - 1)]


# ---------- szum proceduralny ----------


def hash3(cells):
    value = np.sin(cells @ np.array([127.1, 311.7, 74.7])) * 43758.5453
    return value - np.floor(value)


def value_noise(points):
    cell = np.floor(points)
    frac = points - cell
    frac = frac * frac * (3 - 2 * frac)
    result = 0.0
    for ox in (0, 1):
        for oy in (0, 1):
            for oz in (0, 1):
                corner = hash3(cell + np.array([ox, oy, oz]))
                wx = frac[:, 0] if ox else 1 - frac[:, 0]
                wy = frac[:, 1] if oy else 1 - frac[:, 1]
                wz = frac[:, 2] if oz else 1 - frac[:, 2]
                result = result + corner * wx * wy * wz
    return result


def fbm(points):
    return 0.45 * value_noise(points * 5) + 0.35 * value_noise(points * 12 + 7.1) + 0.2 * value_noise(points * 28 + 3.3)


# ---------- renderer ----------

ELEVATION = math.radians(30)
FORWARD = -np.array([math.cos(ELEVATION), 0.0, math.sin(ELEVATION)])
RIGHT = normalize(np.cross(FORWARD, [0, 0, 1]))
UP = np.cross(RIGHT, FORWARD)
# wyżej niż u rycerza: krótszy cień, skupiony pod postacią
LIGHT = normalize([0.3, -0.5, 1.75])
KEY_COLOR = np.array([1.2, 1.08, 0.88])
SKY_COLOR = np.array([0.075, 0.095, 0.1])
BOUNCE_COLOR = np.array([0.05, 0.06, 0.04])
RIM_COLOR = np.array([0.34, 0.4, 0.44])


def to_local(points, angle):
    cosA, sinA = math.cos(angle), math.sin(angle)
    local = np.empty_like(points)
    local[:, 0] = cosA * points[:, 0] + sinA * points[:, 1]
    local[:, 1] = -sinA * points[:, 0] + cosA * points[:, 1]
    local[:, 2] = points[:, 2]
    return local


def to_world_dir(vectors, angle):
    return to_local(vectors, -angle)


def march(model, angle, origins, dirs, tStart, tEnd, steps=200):
    t = tStart.copy()
    hit = np.zeros(len(t), bool)
    active = np.where(tStart < tEnd)[0]
    for _ in range(steps):
        if len(active) == 0:
            break
        points = to_local(origins[active] + dirs[active] * t[active, None], angle)
        dist = model.eval(points)
        done = dist < 0.0012
        hit[active[done]] = True
        t[active] += np.maximum(dist, 0.0005) * 0.75
        keep = (~done) & (t[active] < tEnd[active])
        active = active[keep]
    return hit, t


def soft_shadow(model, angle, points, steps=48):
    result = np.ones(len(points))
    t = np.full(len(points), 0.02)
    lightLocal = to_local(LIGHT[None, :], angle)[0]
    localStart = to_local(points, angle)
    active = np.arange(len(points))
    for _ in range(steps):
        if len(active) == 0:
            break
        dist = model.eval(localStart[active] + lightLocal * t[active, None])
        result[active] = np.minimum(result[active], 10.0 * dist / t[active])
        t[active] += np.clip(dist, 0.01, 0.15)
        keep = (dist > 0.0008) & (t[active] < 2.8)
        result[active[dist <= 0.0008]] = 0.0
        active = active[keep]
    return np.clip(result, 0.0, 1.0)


def render(model, materials, angle, size, extent, centerZ=1.0, shade_hook=None):
    pixels = np.arange(size) + 0.5
    sx = (pixels / size - 0.5) * extent
    sy = (0.5 - pixels / size) * extent
    gridX, gridY = np.meshgrid(sx, sy)
    target = np.array([0.0, 0.0, centerZ])
    origins = target + gridX.reshape(-1, 1) * RIGHT + gridY.reshape(-1, 1) * UP - FORWARD * 8.0
    dirs = np.tile(FORWARD, (len(origins), 1))

    boundR, boundTop = 1.2, 2.8
    tStart = np.zeros(len(origins))
    tEnd = np.zeros(len(origins))
    for axis in range(3):
        lo, hi = (-boundR, boundR) if axis < 2 else (-0.01, boundTop)
        dirAxis = dirs[:, axis]
        t1 = (lo - origins[:, axis]) / dirAxis
        t2 = (hi - origins[:, axis]) / dirAxis
        near, far = np.minimum(t1, t2), np.maximum(t1, t2)
        tStart = near if axis == 0 else np.maximum(tStart, near)
        tEnd = far if axis == 0 else np.minimum(tEnd, far)
    tStart = np.maximum(tStart, 0)

    hit, t = march(model, angle, origins, dirs, tStart, tEnd)
    color = np.zeros((len(origins), 3))
    alpha = np.zeros(len(origins))

    hitIdx = np.where(hit)[0]
    if len(hitIdx):
        worldPts = origins[hitIdx] + dirs[hitIdx] * t[hitIdx, None]
        localPts = to_local(worldPts, angle)
        _, mats = model.eval(localPts, wantMat=True)

        eps = 0.0015
        offsets = np.array([[1, -1, -1], [-1, -1, 1], [-1, 1, -1], [1, 1, 1]], float)
        normalLocal = np.zeros_like(localPts)
        for offset in offsets:
            normalLocal += offset * model.eval(localPts + offset * eps)[:, None]
        normalLocal /= np.linalg.norm(normalLocal, axis=1, keepdims=True) + 1e-9
        normals = to_world_dir(normalLocal, angle)

        occlusion = np.zeros(len(hitIdx))
        for sample in range(1, 6):
            step = 0.035 * sample
            occlusion += (step - model.eval(localPts + normalLocal * step)) / (2 ** sample)
        ao = np.clip(1.0 - 3.0 * occlusion, 0.15, 1.0)

        shadow = soft_shadow(model, angle, worldPts + normals * 0.004)
        viewDir = -FORWARD
        diffuse = np.clip(normals @ LIGHT, 0, 1) * shadow
        halfVec = normalize(LIGHT + viewDir)
        nDotH = np.clip(normals @ halfVec, 0, 1)
        hemi = 0.5 + 0.5 * normals[:, 2]
        rim = (1.0 - np.clip(normals @ viewDir, 0, 1)) ** 3 * np.clip(-normals @ normalize([LIGHT[0], LIGHT[1], 0]) + 0.3, 0, 1)

        grain = fbm(localPts)
        for matId, matDef in materials.items():
            sel = mats == matId
            if not np.any(sel):
                continue
            albedo = np.array(matDef["alb"])[None, :] * np.clip(1.0 + matDef["grit"] * 1.6 * (grain[sel] - 0.5), 0.2, 2.0)[:, None]
            grime = np.clip(1.0 - localPts[sel, 2] / 0.6, 0, 1) * 0.5
            albedo = albedo * (1.0 - grime)[:, None]
            emit = np.array(matDef.get("emit", (0.0, 0.0, 0.0)))[None, :].repeat(sel.sum(), 0)
            spec_k = np.full(sel.sum(), matDef["spec"])
            if shade_hook is not None:
                albedo, spec_k, emit = shade_hook(matId, localPts[sel], normalLocal[sel], grain[sel], albedo, spec_k, emit)
            spec = spec_k * nDotH[sel] ** matDef["pw"] * shadow[sel]
            lit = albedo * (KEY_COLOR * diffuse[sel, None] + (SKY_COLOR * hemi[sel, None] + BOUNCE_COLOR * (1 - hemi[sel, None])) * ao[sel, None] * 1.4)
            lit += spec[:, None] * KEY_COLOR * matDef.get("specTint", 0.35)
            lit += RIM_COLOR * rim[sel, None] * ao[sel, None] * (0.25 + matDef["spec"] * 0.3)
            lit += emit
            color[hitIdx[sel]] = lit
        alpha[hitIdx] = 1.0

    missIdx = np.where(~hit)[0]
    groundT = -origins[missIdx, 2] / dirs[missIdx, 2]
    groundPts = origins[missIdx] + dirs[missIdx] * groundT[:, None]
    near = np.linalg.norm(groundPts[:, :2], axis=1) < 2.0
    groundIdx = missIdx[near]
    if len(groundIdx):
        groundShadow = soft_shadow(model, angle, groundPts[near] + np.array([0, 0, 0.003]))
        contact = np.exp(-np.linalg.norm(groundPts[near][:, :2], axis=1) ** 2 / 0.1) * 0.3
        alpha[groundIdx] = np.clip((1.0 - groundShadow) * 0.6 + contact, 0, 0.72)

    color = color / (1.0 + color) * 1.2
    color = np.clip(color, 0, 1) ** (1 / 2.2)
    # lekkie odbarwienie: jednostka nie może być bardziej nasycona niż las
    luma = color @ np.array([0.299, 0.587, 0.114])
    color = luma[:, None] + (color - luma[:, None]) * 0.82
    image = np.concatenate([color * alpha[:, None], alpha[:, None]], axis=1).reshape(size, size, 4)
    return image


def downsample(premul, factor):
    height, width, _ = premul.shape
    small = premul.reshape(height // factor, factor, width // factor, factor, 4).mean(axis=(1, 3))
    rgb = np.where(small[..., 3:4] > 1e-4, small[..., :3] / np.maximum(small[..., 3:4], 1e-4), 0)
    return np.concatenate([np.clip(rgb, 0, 1), small[..., 3:4]], axis=2)


DIRECTIONS = ["S", "SW", "W", "NW", "N", "NE", "E", "SE"]


# ---------- wspólny kontrakt kadru i CLI postaci ----------
# Te wartości są wspólne dla WSZYSTKICH postaci: skala, kamera i punkt stóp muszą się zgadzać w grze.
FRAME_SIZE = 192      # px, kwadratowa klatka
EXTENT = 3.2          # m świata mieszczące się w szerokości klatki (~60 px/m)
CENTER_Z = 1.2        # m: wysokość, na którą celuje kamera
SUPERSAMPLE = 3       # wygładzanie krawędzi


def render_frame(model, materials, dirIndex, shade_hook=None, frameSize=FRAME_SIZE):
    """Renderuje jedną klatkę w kierunku 0..7 (DIRECTIONS) i zwraca tablicę RGBA uint8."""
    angle = -dirIndex * math.pi / 4
    image = render(model, materials, angle, frameSize * SUPERSAMPLE, extent=EXTENT, centerZ=CENTER_Z, shade_hook=shade_hook)
    frame = downsample(image, SUPERSAMPLE)
    return (frame * 255 + 0.5).astype(np.uint8)


def _render_job(job):
    import importlib
    from PIL import Image
    moduleName, poseName, dirIndex, flags, path = job
    module = importlib.import_module(moduleName)
    model = module.build(module.POSES[poseName])
    hook = module.make_hook(flags) if hasattr(module, "make_hook") else None
    Image.fromarray(render_frame(model, module.MATERIALS, dirIndex, hook), "RGBA").save(path)
    return path


def run_cli(charId, moduleFile):
    """Wspólne CLI postaci: python3 <postac>.py <poza|all> <kierunek 0-7|all> [--flaga ...]

    Wynik: output/<charId>/<charId>_<poza>_<n>_<kierunek>[_flagi].png oraz arkusz <charId>_<poza>_arkusz.png.
    Moduł postaci musi mieć: POSES (słownik póz), MATERIALS, build(pose) -> Model; opcjonalnie make_hook(flags).
    """
    import importlib
    import os
    import sys
    from multiprocessing import Pool
    from PIL import Image, ImageDraw

    here = os.path.dirname(os.path.abspath(moduleFile))
    sys.path.insert(0, here)
    moduleName = os.path.splitext(os.path.basename(moduleFile))[0]
    module = importlib.import_module(moduleName)
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = sorted(a[2:] for a in sys.argv[1:] if a.startswith("--"))
    poseArg = args[0] if args else "all"
    dirArg = args[1] if len(args) > 1 else "all"
    poses = list(module.POSES) if poseArg == "all" else [poseArg]
    dirs = list(range(8)) if dirArg == "all" else [int(dirArg)]
    outDir = os.path.join(here, "output", charId)
    os.makedirs(outDir, exist_ok=True)
    suffix = "".join("_" + f for f in flags)
    jobs = [(moduleName, p, d, tuple(flags), os.path.join(outDir, f"{charId}_{p}_{d}_{DIRECTIONS[d]}{suffix}.png")) for p in poses for d in dirs]
    with Pool(min(os.cpu_count() or 1, len(jobs))) as pool:
        for path in pool.imap(_render_job, jobs):
            print("ok", path)
    if len(dirs) == 8:
        for p in poses:
            sheet = Image.new("RGBA", (FRAME_SIZE * 8, FRAME_SIZE + 14), (35, 41, 31, 255))
            draw = ImageDraw.Draw(sheet)
            for d in range(8):
                frame = Image.open(os.path.join(outDir, f"{charId}_{p}_{d}_{DIRECTIONS[d]}{suffix}.png"))
                sheet.alpha_composite(frame, (d * FRAME_SIZE, 14))
                draw.text((d * FRAME_SIZE + 4, 1), f"{charId} {p} {d} {DIRECTIONS[d]}", fill=(200, 200, 190, 255))
            sheetPath = os.path.join(outDir, f"{charId}_{p}{suffix}_arkusz.png")
            sheet.save(sheetPath)
            print("ok", sheetPath)
