# Welesza environment pack 01 — stones + ground materials (Blender, headless-safe).
# Run:  blender -b -P build_env.py   (or: python with bpy wheel, see README)
# Everything is procedural and self-contained (no external assets).
import bpy, math, random
import os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
TEX = os.environ.get("WELESZA_TEX", os.path.join(os.path.dirname(BASE), "textures"))
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
sc.view_settings.look = "AgX - Medium High Contrast"

random.seed(20261026)

# ============================== WORLD / LIGHT ==============================
bpy.ops.object.light_add(type="SUN", location=(4, -3, 8))
sun = bpy.context.active_object
sun.data.energy = 2.2
sun.data.color = (0.78, 0.85, 1.0)  # cool daylight
sun.rotation_euler = (math.radians(55), math.radians(12), math.radians(30))
sun.data.angle = math.radians(12)

bpy.ops.object.light_add(type="AREA", location=(-4, -2, 3), rotation=(math.radians(60), 0, math.radians(-40)))
sky = bpy.context.active_object
sky.data.energy = 60
sky.data.color = (0.55, 0.62, 0.75)
sky.data.size = 8

w = bpy.data.worlds.new("World")
sc.world = w
w.use_nodes = True
wn = w.node_tree
bg = wn.nodes["Background"]
bg.inputs[0].default_value = (0.015, 0.02, 0.03, 1.0)
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
    col = load_img(os.path.join(TEX, f"welesza_{prefix}_color.png"), f"{prefix}_color")
    nrm = load_img(os.path.join(TEX, f"welesza_{prefix}_normal.png"), f"{prefix}_normal", True)
    hgt = load_img(os.path.join(TEX, f"welesza_{prefix}_height.png"), f"{prefix}_height", True)
    texc = nt.nodes.new("ShaderNodeTexImage"); texc.image = col
    texn = nt.nodes.new("ShaderNodeTexImage"); texn.image = nrm
    nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = 0.6 if prefix=="mud" else 1.0
    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Scale"].default_value = 0.02
    texd = nt.nodes.new("ShaderNodeTexImage"); texd.image = hgt
    nt.links.new(texc.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(texn.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    nt.links.new(texd.outputs["Color"], disp.inputs["Height"])
    nt.links.new(disp.outputs["Displacement"], nt.nodes["Material Output"].inputs["Displacement"])
    bsdf.inputs["Roughness"].default_value = 0.9
    bsdf.inputs["Specular IOR Level"].default_value = 0.25
    return m

mud_mat = make_ground_mat("WELESZA_mud", "mud")
lit_mat = make_ground_mat("WELESZA_litter", "litter")

# mud roughness: drier = rougher, wet spots = smoother+specular
def tune_mud_roughness():
    nt = mud_mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    rough_img = load_img(os.path.join(TEX, "welesza_mud_rough_inverted.png"), "mud_wet", True)
    tr = nt.nodes.new("ShaderNodeTexImage"); tr.image = rough_img
    inv = nt.nodes.new("ShaderNodeInvert")
    nt.links.new(tr.outputs["Color"], inv.inputs["Color"])
    mix = nt.nodes.new("ShaderNodeMath"); mix.operation = "MULTIPLY"
    nt.links.new(inv.outputs["Color"], mix.inputs[0])
    mix.inputs[1].default_value = 0.55
    base = nt.nodes.new("ShaderNodeMath"); base.operation = "ADD"
    nt.links.new(mix.outputs["Value"], base.inputs[0])
    base.inputs[1].default_value = 0.4
    nt.links.new(base.outputs["Value"], bsdf.inputs["Roughness"])
    bsdf.inputs["Specular IOR Level"].default_value = 0.35
tune_mud_roughness()

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
    base = (0.28 + r.random()*0.10, 0.26 + r.random()*0.09, 0.24 + r.random()*0.08, 1.0)
    bsdf.inputs["Base Color"].default_value = base
    bsdf.inputs["Roughness"].default_value = 0.85 + r.random()*0.10
    bsdf.inputs["Specular IOR Level"].default_value = 0.2
    # procedural noise breakup on base color
    no = nt.nodes.new("ShaderNodeTexNoise")
    no.inputs["Scale"].default_value = 6 + r.random()*6
    no.inputs["Detail"].default_value = 8
    no.inputs["Roughness"].default_value = 0.6
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.35, 0.33, 0.30, 1.0)
    ramp.color_ramp.elements[1].color = (0.70, 0.66, 0.60, 1.0)
    nt.links.new(no.outputs["Fac"], ramp.inputs["Fac"])
    mixc = nt.nodes.new("ShaderNodeMix")
    mixc.data_type = "RGBA"
    mixc.inputs["Factor"].default_value = 0.5
    mixc.inputs[6].default_value = base           # A: base color
    nt.links.new(ramp.outputs["Color"], mixc.inputs[7])  # B: noise-tinted color
    nt.links.new(mixc.outputs[2], bsdf.inputs["Base Color"])
    return m

rock_mat_a = make_rock_material("WELESZA_rock_a", 1)
rock_mat_b = make_rock_material("WELESZA_rock_b", 2)
rock_mat_c = make_rock_material("WELESZA_rock_c", 3)
rock_mat_boulder = make_rock_material("WELESZA_rock_boulder", 4)

# ============================== ROCK ASSETS ==============================
# 60 px/m like the hero sprite pipeline; hero is ~1.75 m tall.
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

def render_asset(ob, out_prefix, mats=("neutral", "mud", "litter"), rot=0.0):
    # isolate object: hide others
    others = [o for o in bpy.data.objects if o.type == "MESH" and o is not ob and o.name not in ("GroundPlane",)]
    for o in others: o.hide_render = True
    ob.hide_render = False
    ob.rotation_euler[2] = rot
    for m in mats:
        if m == "neutral":
            shadow_plane.hide_render = True
        else:
            shadow_plane.hide_render = False
            ensure_ground(mud_mat if m == "mud" else lit_mat)
        r = max(max(abs(v.co.x) for v in ob.data.vertices), max(abs(v.co.y) for v in ob.data.vertices)) * 2.6 + 0.3
        aim(ob, cam, elev=30, dist=r * 2.2)
        render_to(os.path.join(OUT, f"{out_prefix}_{m}.png"))
    ob.rotation_euler[2] = 0.0
    for o in others: o.hide_render = False

# render each rock + boulder
for name, ob in rocks.items():
    render_asset(ob, name)
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

bpy.ops.mesh.primitive_plane_add(size=1, location=(0,0,0))
road = bpy.context.active_object
road.name = "Road"
road.scale = (14, 4.6, 1)
bpy.ops.object.transform_apply(scale=True)
road.data.materials.append(mud_mat)

bpy.ops.mesh.primitive_plane_add(size=14, location=(0,0,-0.01))
forest = bpy.context.active_object
forest.name = "ForestFloor"
forest.data.materials.append(lit_mat)

# transition strip between road and litter: blend material via mix
trans = None
def make_transition():
    global trans
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 2.48, 0.002))
    __t = bpy.context.active_object
    __t.scale = (14, 0.7, 1)
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
trans2.scale = (14, 0.7, 1)
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

# hero silhouette reference: simple 1.75m capsule (marked, external comparison later in 2D)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.16, location=(0.5, 0.4, 0.16*0.62))
head = bpy.context.active_object; head.name = "RefHumanHead"
bpy.ops.mesh.primitive_cylinder_add(radius=0.21, depth=1.15, location=(0.5, 0.4, 0.16+0.575))
body = bpy.context.active_object; body.name = "RefHumanBody"
bpy.ops.mesh.primitive_cylinder_add(radius=0.16, depth=0.75, location=(0.5, 0.4, 1.31+0.375))
legs = bpy.context.active_object; legs.name = "RefHumanLegs"
refmat = bpy.data.materials.new("RefHuman")
refmat.use_nodes = True
refmat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.1, 0.12, 0.1, 1.0)
for o in (head, body, legs): o.data.materials.append(refmat)

# scene camera — game-like scale
aim(None, cam, elev=30, dist=7, target=(0, 0, 0.4))
sc.render.resolution_x = 960
sc.render.resolution_y = 540
sc.render.film_transparent = False
render_to(os.path.join(OUT, "scena_testowa.png"))

# close-up of materials in scene
aim(None, cam, elev=30, dist=2.5, target=(-1.5, 1.2, 0.1))
render_to(os.path.join(OUT, "scena_zblizenie.png"))

# ============================== SAVE BLEND ==============================
blend_path = os.path.join(os.path.dirname(OUT), "welesza_env_01.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print("DONE", blend_path)
