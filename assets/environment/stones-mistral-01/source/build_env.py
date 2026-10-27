# Welesza environment pack 01 — stones + ground materials (Blender, headless-safe).
# Run:  blender -b -P build_env.py   (or: python with bpy wheel, see README)
# Everything is procedural and self-contained (no external assets).
import bpy, math, random
import os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
TEX = os.environ.get("WELESZA_TEX", "/workspace/envwork/textures_pbr")
TEX_CATEGORY = {"mud": "ground/wet_mud_with_puddles", "litter": "ground/forest_litter_mixed"}
OUT = os.environ.get("WELESZA_OUT", os.path.join(os.path.dirname(BASE), "renders"))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = 256
sc.render.film_transparent = True
sc.render.resolution_x = 512
sc.render.resolution_y = 512
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGBA"
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Base Contrast"

random.seed(20261026)

# ============================== WORLD / LIGHT ==============================
bpy.ops.object.light_add(type="SUN", location=(4, -3, 8))
sun = bpy.context.active_object
sun.data.energy = 6.5
sun.data.color = (0.78, 0.85, 1.0)  # cool daylight
sun.rotation_euler = (math.radians(55), math.radians(12), math.radians(30))
sun.data.angle = math.radians(12)

bpy.ops.object.light_add(type="AREA", location=(-4, -2, 3), rotation=(math.radians(60), 0, math.radians(-40)))
sky = bpy.context.active_object
sky.data.energy = 320
sky.data.color = (0.55, 0.62, 0.75)
sky.data.size = 8

w = bpy.data.worlds.new("World")
sc.world = w
w.use_nodes = True
wn = w.node_tree
bg = wn.nodes["Background"]
bg.inputs[0].default_value = (0.05, 0.06, 0.08, 1.0)
bg.inputs[1].default_value = 1.0

# ============================== MATERIALS ==============================
def load_img(path, name, noncolor=False):
    im = bpy.data.images.load(path)
    im.name = name
    if noncolor:
        im.colorspace_settings.name = "Non-Color"
    return im

def make_ground_mat(name, prefix):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    texbase = TEX_CATEGORY[prefix]
    col = load_img(os.path.join(TEX, f"{texbase}_color.png"), f"{prefix}_color")
    nrm = load_img(os.path.join(TEX, f"{texbase}_normal.png"), f"{prefix}_normal", True)
    hgt = load_img(os.path.join(TEX, f"{texbase}_height.png"), f"{prefix}_height", True)
    texc = nt.nodes.new("ShaderNodeTexImage"); texc.image = col
    texn = nt.nodes.new("ShaderNodeTexImage"); texn.image = nrm
    nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = 0.6 if prefix=="mud" else 1.0
    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Scale"].default_value = 0.008
    texd = nt.nodes.new("ShaderNodeTexImage"); texd.image = hgt
    rgh = load_img(os.path.join(TEX, f"{texbase}_rough.png"), f"{prefix}_rough", True)
    texr = nt.nodes.new("ShaderNodeTexImage"); texr.image = rgh
    uvmap = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (0.5, 0.5, 0.5)  # repeat texture every ~2 m
    nt.links.new(uvmap.outputs["UV"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], texc.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], texn.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], texd.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], texr.inputs["Vector"])
    nt.links.new(texc.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(texn.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    nt.links.new(texd.outputs["Color"], disp.inputs["Height"])
    nt.links.new(disp.outputs["Displacement"], nt.nodes["Material Output"].inputs["Displacement"])
    nt.links.new(texr.outputs["Color"], bsdf.inputs["Roughness"])
    bsdf.inputs["Specular IOR Level"].default_value = 0.25
    return m

mud_mat = make_ground_mat("WELESZA_mud", "mud")
lit_mat = make_ground_mat("WELESZA_litter", "litter")

# roughness now comes from the generated PBR map (wet_mud_with_puddles_rough)

# ============================== ROCK GEOMETRY ==============================
def make_rock(name, seed, base_r, squash, scale_xyz, spikes=0.35, subsurf=3):
    r = random.Random(seed)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subsurf, radius=base_r, location=(0,0,0))
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = (scale_xyz[0], scale_xyz[1], scale_xyz[2] * squash)
    bpy.ops.object.transform_apply(scale=True)
    # displace vertices with deterministic noise
    mesh = ob.data
    import mathutils
    from mathutils import noise
    for v in mesh.vertices:
        n = noise.noise(mathutils.Vector(v.co) * 1.6 + mathutils.Vector((seed*3.7, seed*1.3, seed*2.9)))
        v.co += v.normal * (n * spikes * base_r)
    # flatten bottom
    zmin = min(v.co.z for v in mesh.vertices)
    for v in mesh.vertices:
        if v.co.z < zmin + 0.12 * abs(zmin):
            v.co.z = zmin + (v.co.z - zmin) * 0.15
    # shading
    for p in mesh.polygons:
        p.use_smooth = True
    mod = ob.modifiers.new("dec", "DECIMATE")
    mod.ratio = 0.35
    bpy.ops.object.shade_smooth()
    sm = ob.modifiers.new("sm", "SMOOTH")
    sm.iterations = 8; sm.factor = 0.5
    # remove decimate to keep shape? decimate helps readability at game scale
    return ob

def make_rock_material(name, seed, mossy=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    r = random.Random(seed)
    bsdf.inputs["Specular IOR Level"].default_value = 0.2
    # AI albedo (mossy rock) + generated PBR
    rock_tex = ["rock/rock_stones_mossy", "rock/rock_cracked_with_moss", "rock/rock_lichen_moss_ground"][(seed-1) % 3]
    col = load_img(os.path.join(TEX, f"{rock_tex}_color.png"), f"rock_{seed}_color")
    nrm = load_img(os.path.join(TEX, f"{rock_tex}_normal.png"), f"rock_{seed}_normal", True)
    rgh = load_img(os.path.join(TEX, f"{rock_tex}_rough.png"), f"rock_{seed}_rough", True)
    texc = nt.nodes.new("ShaderNodeTexImage"); texc.image = col
    texn = nt.nodes.new("ShaderNodeTexImage"); texn.image = nrm
    texr = nt.nodes.new("ShaderNodeTexImage"); texr.image = rgh
    nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = 1.2
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (r.uniform(2.0, 3.5), r.uniform(2.0, 3.5), 1.0)
    tco = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tco.outputs["Object"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], texc.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], texn.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], texr.inputs["Vector"])
    nt.links.new(texc.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(texn.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    nt.links.new(texr.outputs["Color"], bsdf.inputs["Roughness"])
    return m

rock_mat_a = make_rock_material("WELESZA_rock_a", 1)
rock_mat_b = make_rock_material("WELESZA_rock_b", 2)
rock_mat_c = make_rock_material("WELESZA_rock_c", 3)
rock_mat_boulder = make_rock_material("WELESZA_rock_boulder", 4)

# ============================== ROCK ASSETS ==============================
# 60 px/m like the hero sprite pipeline; hero is ~1.75 m tall.
def make_grass_tuft(name, seed, blades=48, height=(0.15, 0.38), radius=0.22):
    import mathutils
    r = random.Random(seed)
    mesh = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(ob)
    verts, faces = [], []
    for i in range(blades):
        ang = r.uniform(0, 2*math.pi)
        dist = r.uniform(0, radius) * math.sqrt(r.random())
        bx, by = math.cos(ang)*dist, math.sin(ang)*dist
        h = r.uniform(*height)
        lean = r.uniform(0.05, 0.35)
        lean_dir = r.uniform(0, 2*math.pi)
        w = 0.006 + r.random()*0.008
        # quad blade: base two verts, tip two verts
        pdir = mathutils.Vector((math.cos(lean_dir), math.sin(lean_dir), 0))
        side = mathutils.Vector((-math.sin(lean_dir), math.cos(lean_dir), 0))
        b0 = mathutils.Vector((bx, by, 0)) - side*w
        b1 = mathutils.Vector((bx, by, 0)) + side*w
        t0 = b0 + pdir*lean + mathutils.Vector((0,0,h))
        t1 = b1 + pdir*lean + mathutils.Vector((0,0,h))
        base = len(verts)
        verts += [b0, b1, t1, t0]
        faces.append((base, base+1, base+2, base+3))
    mesh.from_pydata(verts, [], faces)
    mesh.validate()
    return ob

def make_grass_material(name, seed):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    r = random.Random(seed)
    tex = ["ground/wet_grass_earth", "ground/forest_soil_sparse_grass", "ground/dense_forest_moss"][seed % 3]
    col = load_img(os.path.join(TEX, f"{tex}_color.png"), f"grass_{seed}_color")
    texc = nt.nodes.new("ShaderNodeTexImage"); texc.image = col
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (r.uniform(3.0, 6.0), r.uniform(3.0, 6.0), 1.0)
    tco = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tco.outputs["Object"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], texc.inputs["Vector"])
    # vertex-color-like gradient: darker at base — emulate with geometry Z
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tco.outputs["Object"], sep.inputs["Vector"])
    g = nt.nodes.new("ShaderNodeMapRange")
    g.inputs["From Min"].default_value = 0.0
    g.inputs["From Max"].default_value = 0.28
    nt.links.new(sep.outputs["Z"], g.inputs["Value"])
    mixc = nt.nodes.new("ShaderNodeMix"); mixc.data_type = "RGBA"
    mixc.inputs["Factor"].default_value = 0.55
    dark = nt.nodes.new("ShaderNodeRGB")
    dark.outputs[0].default_value = (0.05, 0.06, 0.035, 1.0)
    nt.links.new(dark.outputs[0], mixc.inputs[6])
    nt.links.new(texc.outputs["Color"], mixc.inputs[7])
    nt.links.new(g.outputs["Result"], mixc.inputs["Factor"])
    nt.links.new(mixc.outputs[2], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.9
    bsdf.inputs["Specular IOR Level"].default_value = 0.1
    # backside translucency look via SSS-ish
    bsdf.inputs["Subsurface Weight"].default_value = 0.15
    return m

grass_mats = [make_grass_material(f"WELESZA_grass_{i}", i) for i in range(3)]
tufts = []
for gi, (name, seed, pos) in enumerate([
    ("kepka_trawy_a", 101, (-3.4, 2.6, 0)),
    ("kepka_trawy_b", 102, (2.3, 2.9, 0)),
    ("kepka_trawy_c", 103, (4.6, -2.4, 0)),
]):
    ob = make_grass_tuft(name, seed)
    ob.data.materials.append(grass_mats[gi % 3])
    tufts.append((ob, pos))

def make_fern(name, seed, fronds=7, length=(0.18, 0.34)):
    """Paproc: kazdy frond = rachida z parami listkow (quad strip, lekko zwinieta)."""
    import mathutils
    r = random.Random(seed)
    mesh = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(ob)
    verts, faces = [], []
    for fi in range(fronds):
        ang = r.uniform(0, 2*math.pi)
        L = r.uniform(*length)
        tilt = r.uniform(0.5, 1.1)  # nachylenie fronda od pionu
        segs = 6
        prev_dir = mathutils.Vector((math.cos(ang)*math.sin(tilt), math.sin(ang)*math.sin(tilt), math.cos(tilt)))
        base_i = len(verts)
        # rachida jako ciag par wierzcholkow
        points = [mathutils.Vector((0,0,0))]
        for si in range(1, segs+1):
            t = si/segs
            p = points[-1] + prev_dir * (L/segs) * (1 - 0.15*t)
            p.z = max(p.z, 0)
            points.append(p)
        for si, p in enumerate(points):
            side = mathutils.Vector((-prev_dir.y, prev_dir.x, 0)).normalized()
            w = 0.004 * (1 - si/segs*0.5)
            verts.append(p - side*w)
            verts.append(p + side*w)
        for si in range(segs):
            b = base_i + si*2
            faces.append((b, b+1, b+3, b+2))
        # listki: pary malych quadow wzdiz rachidy
        for si in range(1, segs):
            t = si/segs
            p = points[si]
            side = mathutils.Vector((-prev_dir.y, prev_dir.x, 0)).normalized()
            leaf_len = 0.05 + 0.07*(1-t)
            for sgn in (-1, 1):
                ldir = (prev_dir*0.3 + side*sgn).normalized()
                tip = p + ldir*leaf_len
                tip.z = max(tip.z, 0.005)
                b = len(verts)
                verts += [p, p + mathutils.Vector((0,0,0.012)), tip + mathutils.Vector((0,0,0.006)), tip]
                faces.append((b, b+1, b+2, b+3))
    mesh.from_pydata(verts, [], faces)
    mesh.validate()
    return ob

def make_fern_material(name, seed):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    r = random.Random(seed)
    tex = ["ground/dense_forest_moss", "ground/wet_grass_earth"][seed % 2]
    col = load_img(os.path.join(TEX, f"{tex}_color.png"), f"fern_{seed}_color")
    texc = nt.nodes.new("ShaderNodeTexImage"); texc.image = col
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (r.uniform(4.0, 8.0), r.uniform(4.0, 8.0), 1.0)
    tco = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tco.outputs["Object"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], texc.inputs["Vector"])
    # ciemniejsza, chlodniejsza zielec paproci
    hsv = nt.nodes.new("ShaderNodeHueSaturation")
    hsv.inputs["Saturation"].default_value = 0.75
    hsv.inputs["Value"].default_value = 0.6
    hsv.inputs["Hue"].default_value = 0.45
    nt.links.new(texc.outputs["Color"], hsv.inputs["Color"])
    nt.links.new(hsv.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.85
    bsdf.inputs["Specular IOR Level"].default_value = 0.1
    bsdf.inputs["Subsurface Weight"].default_value = 0.2
    return m

fern_mats = [make_fern_material(f"WELESZA_fern_{i}", 10+i) for i in range(2)]
ferns = []
for gi, (name, seed, pos, rot) in enumerate([
    ("paproc_a", 201, (-4.6, 2.2, 0), 0.4),
    ("paproc_b", 202, (1.9, 3.1, 0), 2.1),
]):
    ob = make_fern(name, seed)
    ob.data.materials.append(fern_mats[gi % 2])
    ob.rotation_euler[2] = rot
    ferns.append((ob, pos))

def make_twigs(name, seed, count=5, radius=(0.008, 0.02), length=(0.25, 0.6)):
    """Chrust: kilka suchych galezi na ziemi."""
    import mathutils
    r = random.Random(seed)
    mesh = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(ob)
    verts, faces = [], []
    for i in range(count):
        ang = r.uniform(0, 2*math.pi)
        L = r.uniform(*length)
        rad = r.uniform(*radius)
        cx, cy = r.uniform(-0.25, 0.25), r.uniform(-0.25, 0.25)
        dirv = mathutils.Vector((math.cos(ang), math.sin(ang), 0))
        segs = 4
        base = len(verts)
        for si in range(segs+1):
            t = si/segs
            p = mathutils.Vector((cx, cy, rad*0.7)) + dirv*(t-0.5)*L
            rr = rad*(1-t*0.4)
            for k in range(5):
                a = k*2*math.pi/5
                verts.append(p + mathutils.Vector((math.cos(a)*rr, math.sin(a)*rr, 0)))
        for si in range(segs):
            b = base + si*5
            for k in range(5):
                b0, b1 = b+k, b+(k+1)%5
                faces.append((b0, b1, b1+5, b0+5))
        # piki na koncow
        tip = base + segs*5
        center = len(verts)
        verts.append(mathutils.Vector((cx, cy, rad*0.7)) + dirv*0.5*L)
        for k in range(5):
            faces.append((tip+k, tip+(k+1)%5, center))
    mesh.from_pydata(verts, [], faces)
    mesh.validate()
    return ob

def make_wood_material(name, seed):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    r = random.Random(seed)
    tex = ["bark/old_bark_weathered", "bark/pine_bark_reddish_flaky"][seed % 2]
    col = load_img(os.path.join(TEX, f"{tex}_color.png"), f"twig_{seed}_color")
    texc = nt.nodes.new("ShaderNodeTexImage"); texc.image = col
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (r.uniform(1.5, 3.0), r.uniform(1.5, 3.0), 1.0)
    tco = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tco.outputs["Object"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], texc.inputs["Vector"])
    # przyciemnione, desaturacja dla martwego drewna
    hsv = nt.nodes.new("ShaderNodeHueSaturation")
    hsv.inputs["Saturation"].default_value = 0.35
    hsv.inputs["Value"].default_value = 0.75
    nt.links.new(texc.outputs["Color"], hsv.inputs["Color"])
    nt.links.new(hsv.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.95
    return m

twig_mat = make_wood_material("WELESZA_chrust", 31)
twigs = []
for name, seed, pos in [
    ("chrust_a", 301, (-2.8, 2.9, 0)),
    ("chrust_b", 302, (3.8, 2.0, 0)),
]:
    ob = make_twigs(name, seed)
    ob.data.materials.append(twig_mat)
    twigs.append((ob, pos))

rock_specs = [
    # name, seed, radius(m), squash, (sx, sy, sz), spikes
    ("kamien_a", 11, 0.22, 0.62, (1.25, 0.95, 1.0), 0.35),
    ("kamien_b", 22, 0.30, 0.80, (0.85, 1.30, 1.0), 0.45),
    ("kamien_c", 33, 0.16, 0.50, (1.10, 0.80, 1.0), 0.30),
]
rocks = {}
mat_by_name = {"kamien_a": rock_mat_a, "kamien_b": rock_mat_b, "kamien_c": rock_mat_c}
for name, seed, rad, sq, s, sp in rock_specs:
    ob = make_rock(name, seed, rad, sq, s, sp)
    ob.data.materials.append(mat_by_name[name])
    rocks[name] = ob

boulder = make_rock("glaz", 44, 0.85, 0.7, (1.35, 1.0, 1.0), 0.40, subsurf=4)
boulder.data.materials.append(rock_mat_boulder)

# ============================== CAMERA SETUP ==============================
def add_camera(name="Cam"):
    bpy.ops.object.camera_add(location=(0, -3, 2.2))
    cam = bpy.context.active_object
    cam.name = name
    cam.data.lens = 50
    sc.camera = cam
    return cam

def aim(obj, cam, elev=30, dist=None, target=(0,0,0)):
    import mathutils
    o = obj if isinstance(obj, mathutils.Vector) else mathutils.Vector(target)
    d = dist
    az = 0
    x = o.x + d * math.cos(math.radians(az)) * math.cos(math.radians(elev))
    y = o.y - d * math.sin(math.radians(az)) * math.cos(math.radians(elev))
    z = o.z + d * math.sin(math.radians(elev))
    cam.location = (x, y, z)
    dvec = o - cam.location
    cam.rotation_euler = dvec.to_track_quat("-Z", "Y").to_euler()

# ============================== RENDER HELPERS ==============================
cam = add_camera("AssetCam")
os.makedirs(OUT, exist_ok=True)

sc.render.resolution_x = 512
sc.render.resolution_y = 512

shadow_plane = None
def ensure_ground(mat):
    global shadow_plane
    if shadow_plane is None:
        bpy.ops.mesh.primitive_plane_add(size=40, location=(0,0,-0.001))
        shadow_plane = bpy.context.active_object
        shadow_plane.name = "GroundPlane"
    shadow_plane.data.materials.clear()
    shadow_plane.data.materials.append(mat)
    return shadow_plane

def render_to(path):
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)

ensure_ground(mud_mat)  # create the shared ground plane up front

shadow_catcher_plane = None
def ensure_shadow_catcher():
    global shadow_catcher_plane
    if shadow_catcher_plane is None:
        bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
        shadow_catcher_plane = bpy.context.active_object
        shadow_catcher_plane.name = "ShadowCatcher"
        shadow_catcher_plane.is_shadow_catcher = True
    return shadow_catcher_plane

def render_asset(ob, out_prefix, mats=("neutral", "mud", "litter", "shadow"), rot=0.0):
    # isolate object: hide others
    others = [o for o in bpy.data.objects if o.type == "MESH" and o is not ob and o.name not in ("GroundPlane", "ShadowCatcher")]
    for o in others: o.hide_render = True
    ob.hide_render = False
    ob.rotation_euler[2] = rot
    r = max(max(abs(v.co.x) for v in ob.data.vertices), max(abs(v.co.y) for v in ob.data.vertices)) * 2.6 + 0.3
    for m in mats:
        if m == "neutral":
            shadow_plane.hide_render = True
            if shadow_catcher_plane is not None:
                shadow_catcher_plane.hide_render = True
        elif m == "shadow":
            shadow_plane.hide_render = True
            sc_plane = ensure_shadow_catcher()
            sc_plane.hide_render = False
        else:
            shadow_plane.hide_render = False
            if shadow_catcher_plane is not None:
                shadow_catcher_plane.hide_render = True
            ensure_ground(mud_mat if m == "mud" else lit_mat)
        aim(ob, cam, elev=30, dist=r * 2.2)
        render_to(os.path.join(OUT, f"{out_prefix}_{m}.png"))
    if shadow_catcher_plane is not None:
        shadow_catcher_plane.hide_render = True
    ob.rotation_euler[2] = 0.0
    for o in others: o.hide_render = False

# render each rock + boulder
for name, ob in rocks.items():
    render_asset(ob, name)
for ob, _pos in tufts:
    render_asset(ob, ob.name, mats=("neutral", "litter", "shadow"))
for ob, _ in ferns:
    render_asset(ob, ob.name, mats=("neutral", "litter", "shadow"))
for ob, _ in twigs:
    render_asset(ob, ob.name, mats=("neutral", "litter", "shadow"))
for ob, pos in tufts:
    ob.location = pos
for ob, pos in ferns:
    ob.location = pos
for ob, pos in twigs:
    ob.location = pos
render_asset(boulder, "glaz")
# rotation variants of kamien_a (3 variants) to prove reuse
for i, rotdeg in enumerate((47, 113, 251)):
    ob = rocks["kamien_a"]
    render_asset(ob, f"kamien_a_rot{rotdeg}", mats=("mud",), rot=math.radians(rotdeg))

# ============================== TILED SURFACE PREVIEWS ==============================
def render_surface(mat, name, tiles=3, mpp=0.02):
    # plane with heavily tiled texture to expose seams
    bpy.ops.mesh.primitive_plane_add(size=tiles*2, location=(0,0,0))
    pl = bpy.context.active_object
    pl.name = "TilePlane"
    m = mat
    # scale UVs to tile 'tiles' times
    uv = pl.data.uv_layers.active
    for loop in uv.data:
        loop.uv = loop.uv.copy() * tiles
    pl.data.materials.append(m)
    for o in bpy.data.objects:
        o.hide_render = not (o is pl or o.type == "LIGHT" or o.type == "CAMERA")
    aim(pl, cam, elev=30, dist=8)
    render_to(os.path.join(OUT, f"surface_{name}_tiled.png"))
    pl.hide_render = True
    pl.name = "TilePlane_done"

render_surface(mud_mat, "mud", tiles=3)
render_surface(lit_mat, "litter", tiles=3)

# ============================== TEST SCENE ==============================
# restore visibility
for o in bpy.data.objects: o.hide_render = False
# remove tile planes
for o in list(bpy.data.objects):
    if o.name.startswith("TilePlane"):
        bpy.data.objects.remove(o, do_unlink=True)

# terrain: road strip (mud) crossing litter
bpy.ops.mesh.primitive_plane_add(size=14, location=(0,0,0))
terr = bpy.context.active_object
terr.name = "Terrain"
pass
# simple vertex mix: mud in center band along X, litter outside
# use two overlapping planes instead
bpy.data.objects.remove(terr, do_unlink=True)

bpy.ops.mesh.primitive_plane_add(size=1, location=(0,0,0.004))
road = bpy.context.active_object
road.name = "Road"
road.scale = (30, 4.6, 1)
bpy.ops.object.transform_apply(scale=True)
road.data.materials.append(mud_mat)

bpy.ops.mesh.primitive_plane_add(size=60, location=(0,0,-0.01))
forest = bpy.context.active_object
forest.name = "ForestFloor"
forest.data.materials.append(lit_mat)

# transition strip between road and litter: blend material via mix
trans = None
def make_transition():
    global trans
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 2.48, 0.002))
    __t = bpy.context.active_object
    __t.scale = (30, 0.7, 1)
    bpy.ops.object.transform_apply(scale=True)
    trans = bpy.context.active_object
    trans.name = "Transition"
    m = bpy.data.materials.new("WELESZA_transition")
    m.use_nodes = True
    nt = m.node_tree
    mix = nt.nodes.new("ShaderNodeMixShader")
    bsdf_mud = mud_mat.node_tree.nodes["Principled BSDF"]
    # simpler: copy both materials' tex nodes is complex; use mix of colors only
    # gradient mask along local Y
    lt = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    g = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(lt.outputs["Object"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Y"], g.inputs["Value"])
    g.inputs["From Min"].default_value = -0.35
    g.inputs["From Max"].default_value = 0.35
    out = nt.nodes["Material Output"]
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    # mud side
    t1 = nt.nodes.new("ShaderNodeTexImage"); t1.image = bpy.data.images["mud_color"]
    b1 = nt.nodes.new("ShaderNodeBsdfDiffuse"); b1.inputs["Roughness"].default_value = 0.9
    nt.links.new(t1.outputs["Color"], b1.inputs["Color"])
    # litter side
    t2 = nt.nodes.new("ShaderNodeTexImage"); t2.image = bpy.data.images["litter_color"]
    b2 = nt.nodes.new("ShaderNodeBsdfDiffuse"); b2.inputs["Roughness"].default_value = 0.95
    nt.links.new(t2.outputs["Color"], b2.inputs["Color"])
    nt.links.new(g.outputs["Result"], mix.inputs["Fac"])
    nt.links.new(b1.outputs["BSDF"], mix.inputs[1])
    nt.links.new(b2.outputs["BSDF"], mix.inputs[2])
    trans.data.materials.append(m)
make_transition()
# second transition on far side of road
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -2.48, 0.002))
trans2 = bpy.context.active_object
trans2.scale = (30, 0.7, 1)
bpy.ops.object.transform_apply(scale=True)
trans2.name = "Transition2"
trans2.data.materials.append(bpy.data.materials["WELESZA_transition"])

# place rocks & boulder along road edge
rocks["kamien_a"].location = (-2.2, 1.7, 0)
rocks["kamien_a"].rotation_euler[2] = math.radians(20)
rocks["kamien_b"].location = (1.4, -1.9, 0)
rocks["kamien_b"].rotation_euler[2] = math.radians(-40)
rocks["kamien_c"].location = (3.1, 1.6, 0)
rocks["kamien_c"].rotation_euler[2] = math.radians(75)
boulder.location = (-4.2, -1.6, 0)
boulder.rotation_euler[2] = math.radians(10)

# hide leftover transition helper planes? keep both; hide asset-only ground plane
shadow_plane.hide_render = True
if shadow_catcher_plane is not None:
    shadow_catcher_plane.hide_render = True

# hero silhouette reference: simple 1.75m capsule (marked, external comparison later in 2D)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.16, location=(-1.2, -0.9, 0.16*0.62))
head = bpy.context.active_object; head.name = "RefHumanHead"
bpy.ops.mesh.primitive_cylinder_add(radius=0.21, depth=1.15, location=(-1.2, -0.9, 0.16+0.575))
body = bpy.context.active_object; body.name = "RefHumanBody"
bpy.ops.mesh.primitive_cylinder_add(radius=0.16, depth=0.75, location=(-1.2, -0.9, 1.31+0.375))
legs = bpy.context.active_object; legs.name = "RefHumanLegs"
refmat = bpy.data.materials.new("RefHuman")
refmat.use_nodes = True
refmat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.22, 0.24, 0.20, 1.0)
for o in (head, body, legs): o.data.materials.append(refmat)

# scene camera — game-like scale
aim(None, cam, elev=30, dist=8, target=(0, 0, 0.4))
sc.render.resolution_x = 960
sc.render.resolution_y = 540
sc.render.film_transparent = False
render_to(os.path.join(OUT, "scena_testowa.png"))

# close-up of materials in scene — high res for material evaluation
aim(None, cam, elev=30, dist=2.2, target=(-1.8, 1.4, 0.05))
sc.render.resolution_x = 1920
sc.render.resolution_y = 1080
render_to(os.path.join(OUT, "scena_zblizenie.png"))
# second close-up: puddle detail on the road
aim(None, cam, elev=30, dist=1.6, target=(0.8, -0.5, 0.02))
render_to(os.path.join(OUT, "scena_zblizenie_kaluze.png"))
sc.render.resolution_x = 960
sc.render.resolution_y = 540

# ============================== 2D COMPOSITE: hero sprite in test scene ==============================
# external reference sprite from vibe/sprite-bohater-codex (unchanged, comparison only)
try:
    from PIL import Image
    hero_path = os.path.join(os.path.dirname(OUT), "ref", "bohater_spoczynek.png")
    if os.path.exists(hero_path):
        atlas = Image.open(hero_path).convert("RGBA")
        # frame 0 of spoczynek atlas: 192x192 grid; take first cell
        frame = atlas.crop((0, 0, 192, 192))
        scene_img = Image.open(os.path.join(OUT, "scena_testowa.png")).convert("RGBA")
        # scale: 60 px/m in asset space; scene render is 960x540 with camera at 7m/30deg —
        # hero 1.75m tall => use atlas scale directly (60 px/m): hero ≈ 105 px tall in frame
        hero_h = 105
        frame = frame.resize((int(frame.width * hero_h / frame.height), hero_h), Image.LANCZOS)
        # place hero near the road, feet on ground
        px, py = 430, 345
        scene_img.alpha_composite(frame, (px, py))
        scene_img.save(os.path.join(OUT, "scena_testowa_z_bohaterem.png"))
        print("hero composited")
except Exception as e:
    print("hero composite skipped:", e)

# ============================== SAVE BLEND ==============================
blend_path = os.path.join(os.path.dirname(OUT), "welesza_env_01.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print("DONE", blend_path)
