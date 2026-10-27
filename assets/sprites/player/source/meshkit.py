"""Meshkit — rasterizer siatek trójkątowych do sprite'ów Weleszy (prerender 3D -> 2D).

Nowy pipeline dla gęsto ubranych postaci (bohater): geometria jako zamknięte siatki
trójkątowe z prawdziwą anatomią, fałdy tkanin jako geometria, osobne siatki ubioru
skinowane (LBS) do szkieletu, render przez własny rasterizer z z-buforem, cieniowanie
Blinn-Phong z cieniem z shadow mapy, wypiekane AO i szum proceduralny materiałów.

Kontrakt kadru, kamera, światło i format eksportu są zgodne z
assets/sprites/prerender/sdfkit.py — importer gry pozostaje bez zmian.

Zależności: numpy, Pillow. Bez Blendera i bez zewnętrznych modeli.
"""
import math
import os
import sys

import numpy as np

np.seterr(divide="ignore", invalid="ignore")

# ---------- kontrakt kadru (zgodny z sdfkit.py — NIE ZMIENIAĆ) ----------

FRAME_SIZE = 192      # px, kwadratowa klatka
EXTENT = 3.2          # m świata mieszczące się w szerokości klatki (~60 px/m)
CENTER_Z = 1.2        # m: wysokość, na którą celuje kamera
SUPERSAMPLE = 4       # wygładzanie krawędzi (render 768x768 -> 192x192)
ELEVATION = math.radians(30)
DIRECTIONS = ["S", "SW", "W", "NW", "N", "NE", "E", "SE"]
ANCHOR = (FRAME_SIZE / 2, FRAME_SIZE / 2 + CENTER_Z * math.cos(ELEVATION) * FRAME_SIZE / EXTENT)
GROUND_RGB = (35, 41, 31)

# Kamera ortograficzna jak w sdfkit: patrzy wzdłuż FWD, 30° nad horyzontem.
RIGHT = np.array([0.0, 1.0, 0.0])          # oś ekranu w prawo (świat +y)
UP = np.array([-0.5, 0.0, math.cos(ELEVATION)])   # oś ekranu w górę
FWD = np.array([-math.cos(ELEVATION), 0.0, -0.5])  # kierunek patrzenia (w głąb ekranu)
TO_CAM = -FWD
KC = np.stack([RIGHT, UP, TO_CAM], axis=0)  # wiersze: a, b, c (c rośnie ku kamerze)
CAM_TARGET = np.array([0.0, 0.0, CENTER_Z])

# Oświetlenie stałe względem ekranu (jak w sdfkit).
LIGHT_WORLD = np.array([0.3, -0.5, 1.75])
LIGHT_WORLD = LIGHT_WORLD / np.linalg.norm(LIGHT_WORLD)
LIGHT_CAM = KC @ LIGHT_WORLD
KEY_COLOR = np.array([1.2, 1.08, 0.88])
SKY_COLOR = np.array([0.075, 0.095, 0.1])
BOUNCE_COLOR = np.array([0.05, 0.06, 0.04])
RIM_COLOR = np.array([0.34, 0.4, 0.44])


def yaw_matrix(deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def direction_matrix(dirIndex):
    """Świat = Rz(d*45°) · model (zgodne z sdfkit.to_local przy angle=-d*45°)."""
    return yaw_matrix(dirIndex * 45.0)


# ---------- szum proceduralny (z sdfkit) ----------

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


# ---------- siatka ----------

class Mesh:
    """verts (N,3), faces (M,3), matIds (M,), vnorm (N,3), vtint (N,3), vao (N,), vrest (N,3)."""

    def __init__(self, verts, faces, matIds=None, vtint=None):
        self.verts = np.asarray(verts, float)
        self.faces = np.asarray(faces, np.int64)
        self.matIds = np.asarray(matIds if matIds is not None else np.zeros(len(self.faces), np.int64), np.int64)
        self.vtint = np.asarray(vtint, float) if vtint is not None else np.ones((len(self.verts), 3))
        self.vao = np.ones(len(self.verts))
        self.vrest = self.verts.copy()
        self.two_sided = False   # True: renderuj też tylne ścianki (pojedyncza warstwa tkaniny)
        self.compute_normals()

    def compute_normals(self):
        v, f = self.verts, self.faces
        e1 = v[f[:, 1]] - v[f[:, 0]]
        e2 = v[f[:, 2]] - v[f[:, 0]]
        fn = np.cross(e1, e2)
        area = np.linalg.norm(fn, axis=1)
        fn = fn / np.maximum(area, 1e-12)[:, None]
        vn = np.zeros_like(v)
        for k in range(3):
            np.add.at(vn, f[:, k], fn * area[:, None])
        n = np.linalg.norm(vn, axis=1, keepdims=True)
        self.vnorm = vn / np.maximum(n, 1e-12)
        self.fnorm = fn
        self.farea = area
        return self

    def orient_outward(self):
        """Odwraca face'y, których normalna wskazuje do środka bounding boxa."""
        c = (self.verts.min(axis=0) + self.verts.max(axis=0)) / 2
        f = self.faces
        fc = self.verts[f].mean(axis=1)
        flip = np.sum((fc - c) * self.fnorm, axis=1) < 0
        f[flip] = f[flip][:, [0, 2, 1]]
        self.faces = f
        return self.compute_normals()

    def merge(self, other):
        off = len(self.verts)
        return Mesh(
            np.concatenate([self.verts, other.verts], axis=0),
            np.concatenate([self.faces, other.faces + off], axis=0),
            np.concatenate([self.matIds, other.matIds], axis=0),
            np.concatenate([self.vtint, other.vtint], axis=0),
        )


def merge_all(meshes):
    out = meshes[0]
    for m in meshes[1:]:
        out = out.merge(m)
    return out


def ring_pts(center, rx, ry, n, phase=0.0, disp=None):
    """Pierścień elipsy w płaszczyźnie poziomej; disp(a)->(dx,dy,dz) zaburza."""
    pts = np.empty((n, 3))
    for i in range(n):
        a = phase + 2.0 * math.pi * i / n
        x, y = math.cos(a) * rx, math.sin(a) * ry
        dx = dy = dz = 0.0
        if disp is not None:
            dx, dy, dz = disp(a)
        pts[i] = [center[0] + x + dx, center[1] + y + dy, center[2] + dz]
    return pts


def loft_capped(rings, mat, ring_tints=None):
    """Zamknięty loft przez pierścienie (każdy Nx3, CCW patrząc z góry)."""
    rings = [np.asarray(r, float) for r in rings]
    n = len(rings[0])
    allv = np.concatenate(rings, axis=0)
    nv = len(allv)
    faces = []
    for ri in range(len(rings) - 1):
        base = ri * n
        for i in range(n):
            j = (i + 1) % n
            faces.append([base + i, base + n + j, base + j])
            faces.append([base + i, base + n + i, base + n + j])
    cb = nv
    allv = np.concatenate([allv, rings[0].mean(axis=0)[None, :]], axis=0)
    for i in range(n):
        j = (i + 1) % n
        faces.append([cb, j, i])
    ct = nv + 1
    topBase = (len(rings) - 1) * n
    allv = np.concatenate([allv, rings[-1].mean(axis=0)[None, :]], axis=0)
    for i in range(n):
        j = (i + 1) % n
        faces.append([ct, topBase + i, topBase + j])
    mats = np.full(len(faces), mat, np.int64)
    vt = None
    if ring_tints is not None:
        cols = [np.tile(np.asarray(c, float)[None, :], (n, 1)) for c in ring_tints]
        vt = np.concatenate(cols + [np.ones((2, 3))], axis=0)
    return Mesh(allv, np.array(faces, np.int64), mats, vt).orient_outward()


def ellipsoid_mesh(center, radii, mat, nu=16, nv=12, rot=None, vtint=None):
    verts = []
    for iv in range(nv + 1):
        phi = math.pi * iv / nv
        for iu in range(nu):
            th = 2 * math.pi * iu / nu
            p = np.array([
                math.cos(th) * math.sin(phi) * radii[0],
                math.sin(th) * math.sin(phi) * radii[1],
                math.cos(phi) * radii[2],
            ])
            if rot is not None:
                p = rot @ p
            verts.append(p + np.asarray(center, float))
    faces = []
    for iv in range(nv):
        for iu in range(nu):
            a = iv * nu + iu
            b = iv * nu + (iu + 1) % nu
            c = (iv + 1) * nu + iu
            d = (iv + 1) * nu + (iu + 1) % nu
            faces.append([a, c, d])
            faces.append([a, d, b])
    return Mesh(np.array(verts), np.array(faces, np.int64),
                np.full(len(faces), mat, np.int64), vtint).orient_outward()


def box_mesh(center, half, mat, rot=None, vtint=None):
    c = np.asarray(center, float)
    h = np.asarray(half, float)
    v = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                p = np.array([sx * h[0], sy * h[1], sz * h[2]])
                if rot is not None:
                    p = rot @ p
                v.append(p + c)
    f = [
        (0, 3, 2), (0, 1, 3),  # -x
        (4, 7, 5), (4, 6, 7),  # +x
        (0, 5, 1), (0, 4, 5),  # -y
        (2, 7, 3), (2, 6, 7),  # +y
        (0, 2, 6), (0, 6, 4),  # -z
        (1, 5, 7), (1, 7, 3),  # +z
    ]
    return Mesh(np.array(v, float), np.array(f, np.int64),
                np.full(len(f), mat, np.int64), vtint).orient_outward()


def cylinder_mesh(a, b, r1, r2, mat, n=14, vtint=None):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    axis = b - a
    h = np.linalg.norm(axis)
    z = axis / h
    x = np.cross(z, [0, 0, 1.0])
    if np.linalg.norm(x) < 1e-6:
        x = np.cross(z, [1.0, 0, 0])
    x = x / np.linalg.norm(x)
    y = np.cross(z, x)
    rings = []
    for (pt, r) in ((a, r1), (b, r2)):
        ring = np.array([pt + math.cos(2 * math.pi * i / n) * r * x
                         + math.sin(2 * math.pi * i / n) * r * y for i in range(n)])
        rings.append(ring)
    return loft_capped(rings, mat, vtint)


# ---------- szkielet i skinning ----------

class Skeleton:
    """Łańcuch kości: każda ma rest_head/rest_tail (świat spoczynku) i pose_head/pose_tail."""

    def __init__(self):
        self.bones = {}  # name -> dict(parent, rest_head, rest_tail)

    def add(self, name, parent, rest_head, rest_tail):
        self.bones[name] = dict(parent=parent,
                                rest_head=np.asarray(rest_head, float),
                                rest_tail=np.asarray(rest_tail, float),
                                pose_head=None, pose_tail=None)

    def set_pose(self, name, head, tail):
        b = self.bones[name]
        b["pose_head"] = np.asarray(head, float)
        b["pose_tail"] = np.asarray(tail, float)

    def reset_pose(self):
        for b in self.bones.values():
            b["pose_head"] = b["rest_head"].copy()
            b["pose_tail"] = b["rest_tail"].copy()

    def world_matrix(self, name, rest=False):
        """Macierz 4x4 kości (łańcuch od korzenia). rest=True — pozycja spoczynkowa."""
        chain = []
        n = name
        while n is not None:
            chain.append(n)
            n = self.bones[n]["parent"]
        M = np.eye(4)
        for n in reversed(chain):
            b = self.bones[n]
            if rest:
                R = np.eye(3)
                head = b["rest_head"]
            else:
                R = rotate_onto(b["rest_tail"] - b["rest_head"], b["pose_tail"] - b["pose_head"])
                head = b["pose_head"]
            t = head - R @ b["rest_head"]
            T = np.eye(4)
            T[:3, :3] = R
            T[:3, 3] = t
            M = M @ T
        return M

    def skin_matrix(self, name):
        """M_skin = M_pose · M_rest^{-1} (dla LBS)."""
        return self.world_matrix(name) @ np.linalg.inv(self.world_matrix(name, rest=True))


def rotate_onto(src, dst):
    a = np.asarray(src, float)
    b = np.asarray(dst, float)
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-12 or nb < 1e-12:
        return np.eye(3)
    a, b = a / na, b / nb
    v = np.cross(a, b)
    c = float(np.dot(a, b))
    if c < -0.9999:
        perp = np.cross(a, [1.0, 0, 0]) if abs(a[0]) < 0.9 else np.cross(a, [0, 1.0, 0])
        perp = perp / np.linalg.norm(perp)
        return 2 * np.outer(perp, perp) - np.eye(3)
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx / (1 + c)


def ik2(start, target, len1, len2, pole):
    """Dwa odcinki od start do target; staw wypchnięty w stronę pole."""
    delta = target - start
    dist = np.linalg.norm(delta)
    reach = np.clip(dist, abs(len1 - len2) + 1e-3, len1 + len2 - 1e-3)
    axis = delta / max(dist, 1e-9)
    along = (len1 ** 2 - len2 ** 2 + reach ** 2) / (2 * reach)
    side = math.sqrt(max(len1 ** 2 - along ** 2, 0.0))
    bend = np.asarray(pole, float) - axis * np.dot(pole, axis)
    bend = bend / (np.linalg.norm(bend) + 1e-9)
    return start + axis * along + bend * side, start + axis * reach


def auto_weights(meshes, skel, segments, kmax=3, sigma=0.06, hard=None):
    """Wagi LBS: odległość od segmentów kości. hard: {mesh_index: bone_name} — 100% na kość."""
    names = list(segments.keys())
    segs = [(skel.bones[n]["rest_head"], skel.bones[n]["rest_tail"]) for n in names]
    out = []
    for mi, mesh in enumerate(meshes):
        v = mesh.verts
        if hard is not None and mi in hard:
            W = np.zeros((len(v), len(names)))
            W[:, names.index(hard[mi])] = 1.0
            out.append(W)
            continue
        d = np.full((len(v), len(names)), 1e9)
        for bi, (a, b) in enumerate(segs):
            ab = b - a
            t = np.clip(((v - a) @ ab) / max(ab @ ab, 1e-12), 0, 1)
            closest = a + t[:, None] * ab
            d[:, bi] = np.linalg.norm(v - closest, axis=1)
        idx = np.argsort(d, axis=1)[:, :kmax]
        w = np.exp(-d[np.arange(len(v))[:, None], idx] / sigma)
        W = np.zeros((len(v), len(names)))
        W[np.arange(len(v))[:, None], idx] = w
        W = W / np.maximum(W.sum(axis=1, keepdims=True), 1e-9)
        out.append(W)
    return {"names": names, "weights": out}


def skin_meshes(meshes, skel, weights):
    """Zwraca siatki w pozie (przestrzeń modelu, przed obrotem kierunku)."""
    Ms = {name: skel.skin_matrix(name) for name in weights["names"]}
    out = []
    for mi, mesh in enumerate(meshes):
        W = weights["weights"][mi]
        v = mesh.verts
        acc = np.zeros_like(v)
        for k, name in enumerate(weights["names"]):
            M = Ms[name]
            R = M[:3, :3]
            t = M[:3, 3]
            acc += W[:, k][:, None] * (v @ R.T + t)
        m = Mesh(acc, mesh.faces, mesh.matIds, mesh.vtint)
        m.vao = mesh.vao.copy()
        m.vrest = mesh.vrest.copy()
        out.append(m)
    return out


# ---------- AO (voxel grid, liczone raz w pozycji spoczynkowej) ----------

def compute_ao(meshes, bounds_min=(-1.3, -1.3, 0.0), bounds_max=(1.3, 1.3, 2.1),
               grid=72, rays=24, max_dist=0.28):
    lo = np.asarray(bounds_min, float)
    hi = np.asarray(bounds_max, float)
    vs = (hi - lo) / grid
    occ = np.zeros((grid, grid, grid), bool)
    for mesh in meshes:
        v = mesh.verts
        for tri in mesh.faces:
            p0, p1, p2 = v[tri[0]], v[tri[1]], v[tri[2]]
            n = np.cross(p1 - p0, p2 - p0)
            nn = np.linalg.norm(n)
            if nn < 1e-12:
                continue
            n = n / nn
            tmin = np.minimum(np.minimum(p0, p1), p2)
            tmax = np.maximum(np.maximum(p0, p1), p2)
            i0 = np.maximum(((tmin - lo) / vs).astype(int) - 1, 0)
            i1 = np.minimum(((tmax - lo) / vs).astype(int) + 1, grid - 1)
            for i in range(i0[0], i1[0] + 1):
                for j in range(i0[1], i1[1] + 1):
                    for k in range(i0[2], i1[2] + 1):
                        c = lo + (np.array([i, j, k]) + 0.5) * vs
                        rel = c - p0
                        if abs(np.dot(rel, n)) >= 0.75 * vs.max():
                            continue
                        # rzut na płaszczyznę trójkąta + test barycentryczny 2D
                        proj = c - n * np.dot(rel, n)
                        e1 = p1 - p0
                        e2 = p2 - p0
                        d00 = e1 @ e1
                        d01 = e1 @ e2
                        d11 = e2 @ e2
                        d20 = (proj - p0) @ e1
                        d21 = (proj - p0) @ e2
                        den = d00 * d11 - d01 * d01
                        if abs(den) < 1e-12:
                            continue
                        u = (d11 * d20 - d01 * d21) / den
                        w = (d00 * d21 - d01 * d20) / den
                        if u >= -0.05 and w >= -0.05 and u + w <= 1.05:
                            occ[i, j, k] = True
    rng = np.random.default_rng(7)
    dirs = rng.normal(size=(rays, 3))
    dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    steps = np.linspace(vs.max() * 0.8, max_dist, 10)
    for mesh in meshes:
        v = mesh.verts
        nrm = mesh.vnorm
        blocked = np.zeros(len(v))
        total = np.zeros(len(v))
        for d in dirs:
            usable = (nrm @ d) > 0
            if not np.any(usable):
                continue
            total += usable
            for s in steps:
                p = v + d[None, :] * s
                gi = np.clip(((p - lo) / vs).astype(int), 0, grid - 1)
                blocked += occ[gi[:, 0], gi[:, 1], gi[:, 2]] & usable
        ao = 1.0 - blocked / np.maximum(total * len(steps), 1)
        mesh.vao = np.clip(ao, 0.22, 1.0)
    return meshes


# ---------- shadow map (światło kierunkowe, stałe w świecie) ----------

class ShadowMap:
    def __init__(self, size=256, half=2.0):
        self.size = size
        self.half = half
        lz = LIGHT_WORLD
        lx = np.cross(lz, [0, 0, 1.0])
        if np.linalg.norm(lx) < 1e-6:
            lx = np.cross(lz, [1.0, 0, 0])
        lx = lx / np.linalg.norm(lx)
        ly = np.cross(lz, lx)
        self.basis = np.stack([lx, ly, lz], axis=1)  # kolumny
        self.depth = np.full((size, size), -1e9)

    def rasterize(self, meshes_world):
        S = self.size
        depth = np.full((S, S), -1e9)
        B = self.basis
        for mesh in meshes_world:
            v = mesh.verts @ B  # x,y -> mapa, z -> głębokość ku światłu
            for tri in mesh.faces:
                p = v[tri]
                u = (p[:, 0] / self.half * 0.5 + 0.5) * S
                w = (p[:, 1] / self.half * 0.5 + 0.5) * S
                z = p[:, 2]
                minx, maxx = int(max(u.min(), 0)), int(min(u.max() + 1, S))
                miny, maxy = int(max(w.min(), 0)), int(min(w.max() + 1, S))
                if minx >= maxx or miny >= maxy:
                    continue
                xs = np.arange(minx, maxx) + 0.5
                ys = np.arange(miny, maxy) + 0.5
                gx, gy = np.meshgrid(xs, ys)
                d = np.stack([gx.ravel(), gy.ravel()], axis=1)
                x0, x1, x2 = u
                y0, y1, y2 = w
                det = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
                if abs(det) < 1e-9:
                    continue
                l0 = ((x1 - d[:, 0]) * (y2 - d[:, 1]) - (x2 - d[:, 0]) * (y1 - d[:, 1])) / det
                l1 = ((x2 - d[:, 0]) * (y0 - d[:, 1]) - (x0 - d[:, 0]) * (y2 - d[:, 1])) / det
                l2 = 1.0 - l0 - l1
                inside = (l0 >= -0.02) & (l1 >= -0.02) & (l2 >= -0.02)
                if not np.any(inside):
                    continue
                zpix = l0 * z[0] + l1 * z[1] + l2 * z[2]
                xi = d[inside, 0].astype(int) - minx
                yi = d[inside, 1].astype(int) - miny
                np.maximum.at(depth, (yi, xi), zpix[inside])
        self.depth = depth
        return self

    def sample(self, world_pts, bias=0.02):
        S = self.size
        p = world_pts @ self.basis
        u = (p[:, 0] / self.half * 0.5 + 0.5) * S
        v = (p[:, 1] / self.half * 0.5 + 0.5) * S
        z = p[:, 2]
        out = np.ones(len(p))
        for du in (-1, 0, 1):
            for dv in (-1, 0, 1):
                ui = np.clip((u + du).astype(int), 0, S - 1)
                vi = np.clip((v + dv).astype(int), 0, S - 1)
                lit = (z > self.depth[vi, ui] + bias).astype(float)
                out = np.minimum(out, lit)
        return out


# ---------- rasterizer ----------

def _raster_triangles(meshes_world, S, extent):
    """Zwraca płaskie tablice wszystkich trójkątów w przestrzeni kamery (a,b,c)."""
    tris = []
    for mesh in meshes_world:
        vc = (mesh.verts - CAM_TARGET) @ KC.T  # (N,3): a, b, c
        for fi in range(len(mesh.faces)):
            idx = mesh.faces[fi]
            tris.append((vc[idx], mesh.matIds[fi], idx))
    return tris, meshes_world


def rasterize(meshes_world, materials, S, extent=EXTENT, shadow=None, shade_hook=None):
    """Renderuje klatkę RGBA float32 (S×S×4, premultiplied)."""
    color = np.zeros((S, S, 3))
    alpha = np.zeros((S, S))
    zbuf = np.full((S, S), -1e9)

    # atrybuty per mesh w przestrzeni kamery
    cam_cache = []
    for mesh in meshes_world:
        vc = (mesh.verts - CAM_TARGET) @ KC.T
        nc = mesh.vnorm @ KC.T
        cam_cache.append((vc, nc, mesh))

    for vc, nc, mesh in cam_cache:
        p2 = np.stack([(vc[:, 0] / extent + 0.5) * S,
                       (0.5 - vc[:, 1] / extent) * S], axis=1)
        # backface culling + filtr ekranowy (wektorowo, przed pętlą)
        fnc = mesh.fnorm @ KC.T
        if getattr(mesh, "two_sided", False):
            vis = np.ones(len(mesh.fnorm), bool)
        else:
            vis = fnc[:, 2] > -0.005
        fvis = mesh.faces[vis]
        if len(fvis) == 0:
            continue
        tri2 = p2[fvis]
        inb = ((tri2[:, :, 0] >= -2) & (tri2[:, :, 0] <= S + 2)
               & (tri2[:, :, 1] >= -2) & (tri2[:, :, 1] <= S + 2)).any(axis=1)
        fvis = fvis[inb]
        mvis = mesh.matIds[vis][inb]
        if len(fvis) == 0:
            continue
        for fi in range(len(fvis)):
            idx = fvis[fi]
            a, b, c = p2[idx[0]], p2[idx[1]], p2[idx[2]]
            area = (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])
            if abs(area) < 1e-9:
                continue
            minx = int(max(math.floor(min(a[0], b[0], c[0])), 0))
            maxx = int(min(math.ceil(max(a[0], b[0], c[0])), S))
            miny = int(max(math.floor(min(a[1], b[1], c[1])), 0))
            maxy = int(min(math.ceil(max(a[1], b[1], c[1])), S))
            if minx >= maxx or miny >= maxy:
                continue
            xs = np.arange(minx, maxx) + 0.5
            ys = np.arange(miny, maxy) + 0.5
            gx, gy = np.meshgrid(xs, ys)
            pts = np.stack([gx.ravel(), gy.ravel()], axis=1)
            w0 = ((b[0] - pts[:, 0]) * (c[1] - pts[:, 1]) - (c[0] - pts[:, 0]) * (b[1] - pts[:, 1])) / area
            w1 = ((c[0] - pts[:, 0]) * (a[1] - pts[:, 1]) - (a[0] - pts[:, 0]) * (c[1] - pts[:, 1])) / area
            w2 = 1.0 - w0 - w1
            inside = (w0 >= -0.02) & (w1 >= -0.02) & (w2 >= -0.02)
            if not np.any(inside):
                continue
            zi = zbuf[miny:maxy, minx:maxx].ravel()[inside]
            zw = w0[inside] * vc[idx[0], 2] + w1[inside] * vc[idx[1], 2] + w2[inside] * vc[idx[2], 2]
            closer = zw > zi
            if not np.any(closer):
                continue
            sel = np.where(inside)[0][closer]
            pi = pts[sel].astype(int)
            wa, wb, wc_ = w0[sel], w1[sel], w2[sel]

            # atrybuty
            nrm = wa[:, None] * nc[idx[0]] + wb[:, None] * nc[idx[1]] + wc_[:, None] * nc[idx[2]]
            nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-9)
            ao = wa * mesh.vao[idx[0]] + wb * mesh.vao[idx[1]] + wc_ * mesh.vao[idx[2]]
            tint = (wa[:, None] * mesh.vtint[idx[0]] + wb[:, None] * mesh.vtint[idx[1]]
                    + wc_[:, None] * mesh.vtint[idx[2]])
            vrest = (wa[:, None] * mesh.vrest[idx[0]] + wb[:, None] * mesh.vrest[idx[1]]
                     + wc_[:, None] * mesh.vrest[idx[2]])
            # pozycja świata piksela (do cienia)
            aa = (pts[sel, 0] / S - 0.5) * extent
            bb = (0.5 - pts[sel, 1] / S) * extent
            pw = (aa[:, None] * RIGHT[None, :] + bb[:, None] * UP[None, :]
                  + CAM_TARGET[None, :])

            # cieniowanie
            matDef = materials[mvis[fi]]
            V = np.array([0.0, 0.0, 1.0])
            flip = (nrm @ V) < 0
            nrm[flip] = -nrm[flip]
            ndl = np.clip(nrm @ LIGHT_CAM, 0, 1)
            if shadow is not None:
                Nw = nrm @ KC  # cam -> świat (KC ortonormalna, wiersze = osie kamery)
                sh = shadow.sample(pw + Nw * 0.012, bias=0.02 + 0.03 * (1 - ndl))
            else:
                sh = np.ones(len(nrm))
            H = LIGHT_CAM + V
            H = H / np.linalg.norm(H)
            ndh = np.clip(nrm @ H, 0, 1)
            spec = matDef["spec"] * ndh ** matDef["pw"] * sh
            hemi = 0.5 + 0.5 * nrm[:, 1]
            grit = fbm(vrest * 3.0)
            albedo = np.array(matDef["alb"])[None, :] * tint * np.clip(
                1.0 + matDef["grit"] * 1.6 * (grit - 0.5), 0.2, 2.0)[:, None]
            # brud/wilgoć nisko (jak sdfkit: grime na dole postaci)
            grime = np.clip(1.0 - vrest[:, 2] / 0.6, 0, 1) * 0.45
            albedo = albedo * (1.0 - grime)[:, None]
            emit = np.zeros((len(nrm), 3))
            if shade_hook is not None:
                albedo, spec, emit = shade_hook(mvis[fi], vrest, nrm, albedo, spec, emit)
            lit = albedo * (KEY_COLOR[None, :] * (ndl * sh)[:, None]
                            + (SKY_COLOR[None, :] * hemi[:, None]
                               + BOUNCE_COLOR[None, :] * (1 - hemi)[:, None]) * ao[:, None] * 2.6)
            lit += spec[:, None] * KEY_COLOR[None, :] * matDef.get("specTint", 0.35)
            ndv = np.clip(nrm @ V, 0, 1)
            rim = (1.0 - ndv) ** 3 * np.clip(-nrm[:, 0] * LIGHT_CAM[0] - nrm[:, 1] * LIGHT_CAM[1] + 0.3, 0, 1)
            lit += RIM_COLOR[None, :] * rim[:, None] * ao[:, None] * (0.25 + matDef["spec"] * 0.3)
            lit += emit

            zbuf[pi[:, 1], pi[:, 0]] = zw[closer]
            color[pi[:, 1], pi[:, 0]] = lit
            alpha[pi[:, 1], pi[:, 0]] = 1.0

    # cień na ziemi (piksele bez trafienia)
    if shadow is not None:
        pix = (np.arange(S) + 0.5) / S
        aa = (pix - 0.5) * extent
        bb = (0.5 - pix) * extent
        AA, BB = np.meshgrid(aa, bb)
        # promień: P(t) = T + a*R + b*U + t*F; z=0 -> t = (T_z + b*U_z) / 0.5
        t = (CAM_TARGET[2] + BB * UP[2]) / 0.5
        Px = CAM_TARGET[0] + BB * UP[0] + t * FWD[0]
        Py = AA
        near = (np.abs(Px) < 1.7) & (np.abs(Py) < 1.7) & (t > 0)
        if np.any(near):
            Pw = np.stack([Px[near], Py[near], np.zeros(near.sum())], axis=1)
            sh = shadow.sample(Pw + np.array([0, 0, 0.004]))
            contact = np.exp(-(Pw[:, 0] ** 2 + Pw[:, 1] ** 2) / 0.09) * 0.35
            a = np.clip((1.0 - sh) * 0.55 + contact, 0, 0.72)
            aimg = np.zeros((S, S))
            pi = np.where(near)
            aimg[pi] = a
            alpha = np.maximum(alpha, aimg * (alpha == 0))

    # tonemap + gamma + odbarwienie (jak sdfkit)
    color = color / (1.0 + color) * 1.2
    color = np.clip(color, 0, 1) ** (1 / 2.2)
    luma = color @ np.array([0.299, 0.587, 0.114])
    color = luma[:, :, None] + (color - luma[:, :, None]) * 0.82
    return np.concatenate([color * alpha[..., None], alpha[..., None]], axis=2)


def downsample(premul, factor):
    h, w, _ = premul.shape
    small = premul.reshape(h // factor, factor, w // factor, factor, 4).mean(axis=(1, 3))
    rgb = np.where(small[..., 3:4] > 1e-4, small[..., :3] / np.maximum(small[..., 3:4], 1e-4), 0)
    return np.concatenate([np.clip(rgb, 0, 1), small[..., 3:4]], axis=2)


def render_frame(meshes, materials, dirIndex, shadow=None, shade_hook=None,
                 frameSize=FRAME_SIZE, supersample=SUPERSAMPLE):
    meshes_world = prepare_world(meshes, dirIndex)
    img = rasterize(meshes_world, materials, frameSize * supersample, shadow=shadow,
                    shade_hook=shade_hook)
    frame = downsample(img, supersample)
    return (frame * 255 + 0.5).astype(np.uint8)


def prepare_world(meshes, dirIndex):
    """Obrót siatek do świata z zachowaniem atrybutów (vao, vrest)."""
    D = direction_matrix(dirIndex)
    out = []
    for m in meshes:
        w = Mesh(m.verts @ D.T, m.faces, m.matIds, m.vtint)
        w.vao = m.vao
        w.vrest = m.vrest
        out.append(w)
    return out


# ---------- eksport: atlas, GIF, JSON, arkusz (zgodne z sdfkit) ----------

def _save_atlas_gif(outDir, charId, name, frames_u8, durations, loop, dirs_count=8):
    from PIL import Image
    # frames_u8[d][f] -> (192,192,4): wiersz = kierunek, kolumna = klatka (jak sdfkit)
    count = len(frames_u8[0])
    atlas = Image.new("RGBA", (FRAME_SIZE * count, FRAME_SIZE * dirs_count), (0, 0, 0, 0))
    for d in range(dirs_count):
        for f in range(count):
            atlas.paste(Image.fromarray(frames_u8[d][f], "RGBA"), (f * FRAME_SIZE, d * FRAME_SIZE))
    atlas.save(os.path.join(outDir, f"{charId}_{name}.png"))
    # GIF: wszystkie kierunki obok siebie, na tle lasu
    gifFrames = []
    for f in range(count):
        strip = Image.new("RGBA", (FRAME_SIZE * dirs_count, FRAME_SIZE), GROUND_RGB + (255,))
        for d in range(dirs_count):
            strip.alpha_composite(Image.fromarray(frames_u8[d][f], "RGBA"), (d * FRAME_SIZE, 0))
        gifFrames.append(strip.convert("RGB").quantize(colors=255, method=Image.Quantize.MEDIANCUT))
    gifPath = os.path.join(outDir, f"{charId}_{name}.gif")
    gifFrames[0].save(gifPath, save_all=True, append_images=gifFrames[1:],
                      duration=durations, loop=0, disposal=1)
    return f"{charId}_{name}.png", gifPath


def write_json(outDir, charId, animations_meta):
    import json
    meta = {
        "character": charId,
        "frame_size": [FRAME_SIZE, FRAME_SIZE],
        "anchor_px": [round(ANCHOR[0], 1), round(ANCHOR[1], 1)],
        "pixels_per_meter": FRAME_SIZE / EXTENT,
        "directions": DIRECTIONS,
        "direction_note": "wiersz atlasu = indeks kierunku; S = przodem do kamery, kolejne co 45° zgodnie z ruchem wskazówek zegara na ekranie",
        "layout": "kolumny = klatki animacji, wiersze = kierunki",
        "pipeline": "meshkit (siatki trójkątowe + rasterizer), kontrakt zgodny z sdfkit",
        "animations": animations_meta,
    }
    with open(os.path.join(outDir, f"{charId}.json"), "w") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=2)


def save_pose_sheet(outDir, charId, poseName, frames_u8, suffix=""):
    """Arkusz 8 kierunków na tle lasu z podpisami (jak run_cli w sdfkit)."""
    from PIL import Image, ImageDraw
    sheet = Image.new("RGBA", (FRAME_SIZE * 8, FRAME_SIZE + 14), GROUND_RGB + (255,))
    draw = ImageDraw.Draw(sheet)
    for d in range(8):
        sheet.alpha_composite(Image.fromarray(frames_u8[d], "RGBA"), (d * FRAME_SIZE, 14))
        draw.text((d * FRAME_SIZE + 4, 1), f"{charId} {poseName} {d} {DIRECTIONS[d]}", fill=(200, 200, 190, 255))
    path = os.path.join(outDir, f"{charId}_{poseName}{suffix}_arkusz.png")
    sheet.save(path)
    return path


def run_jobs(jobs, worker):
    """Równoległe wykonanie jobs przez Pool; worker(job) -> wynik."""
    from multiprocessing import Pool
    with Pool(min(os.cpu_count() or 1, max(1, len(jobs)))) as pool:
        results = list(pool.imap_unordered(worker, jobs))
    return results
