# Welesza environment 01 — budowa sceny .blend (Blender 4.3, bpy).
# TEN PLIK TYLKO BUDUJE I ZAPISUJE .blend — jest źródłem.
# Render osobno: render_env.py (czyta .blend, nie modyfikuje go).
#
# Kontrakt: docs/art/KONTRAKT-RENDERU.md
# Kamera/światła skopiowane z source/bohater.blend (vibe/sprite-bohater-codex).
import bpy, math, random, os

BASE = os.path.dirname(os.path.abspath(__file__))
TEX = os.environ.get("WELESZA_TEX", "/workspace/envwork/textures_pbr")

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
random.seed(20261026)

# ============================== KAMERA (kontrakt) ==============================
bpy.ops.object.camera_add(location=(6.9282, 0.0, 5.2))
cam = bpy.context.active_object
cam.name = "KameraKontrakt"
cam.rotation_euler = (math.radians(60), 0, math.radians(90))
cam.data.type = "ORTHO"
cam.data.ortho_scale = 3.2
sc.camera = cam

# ============================== ŚWIATŁA (kontrakt, 1:1 z bohater.blend) ==============================
def add_area_light(name, energy, size, color, location):
    bpy.ops.object.light_add(type="AREA", location=location)
    l = bpy.context.active_object
    l.name = name
    l.data.energy = energy
    l.data.size = size
    l.data.color = color
    # światła celują w (0,0,~1) jak u bohatera
    import mathutils
    d = mathutils.Vector((0, 0, 1.0)) - mathutils.Vector(location)
    l.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return l

add_area_light("Klucz", 520.0, 2.3, (0.94, 0.92, 0.85), (2.8, -3.5, 6.0))
add_area_light("Wypelnienie_tyl", 140.0, 3.0, (0.60, 0.70, 0.85), (-3.0, 1.0, 4.0))
add_area_light("Odbicie_ziemi", 65.0, 4.0, (0.64, 0.68, 0.74), (3.0, 4.0, 2.5))

# ============================== ŚWIAT (kontrakt) ==============================
w = bpy.data.worlds.new("Swiat")
sc.world = w
w.use_nodes = True
bg = w.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.18, 0.21, 0.26, 1.0)
bg.inputs[1].default_value = 0.2

# ============================== USTAWIENIA RENDERU (kontrakt) ==============================
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = 64
sc.cycles.seed = 1703
sc.render.filter_size = 1.5
sc.render.threads = 4
sc.render.threads_mode = "FIXED"
sc.render.film_transparent = True
sc.render.resolution_x = 384
sc.render.resolution_y = 384
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Medium High Contrast"
sc.view_settings.exposure = -0.2
sc.view_layers[0].cycles.use_denoising = False  # PM: bez odszumiania (bohater.blend ma True, ale jego pipeline robi denoise inaczej)

# ============================== MATERIAŁY ==============================
def load_img(path, name, noncolor=False):
    im = bpy.data.images.load(path)
    im.name = name
    if noncolor:
        im.colorspace_settings.name = "Non-Color"
    return im

def make_rock_material(name, seed, texbase, mapping_scale):
    """Skała: albedo z biblioteki main (tileable PBR), Object-space mapping."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    r = random.Random(seed)
    col = load_img(os.path.join(TEX, f"{texbase}_color.png"), f"{name}_c")
    nrm = load_img(os.path.join(TEX, f"{texbase}_normal.png"), f"{name}_n", True)
    rgh = load_img(os.path.join(TEX, f"{texbase}_rough.png"), f"{name}_r", True)
    texc = nt.nodes.new("ShaderNodeTexImage"); texc.image = col
    texn = nt.nodes.new("ShaderNodeTexImage"); texn.image = nrm
    texr = nt.nodes.new("ShaderNodeTexImage"); texr.image = rgh
    nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = 1.2
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (mapping_scale, mapping_scale, mapping_scale)
    tco = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tco.outputs["Object"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], texc.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], texn.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], texr.inputs["Vector"])
    nt.links.new(texc.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(texn.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    nt.links.new(texr.outputs["Color"], bsdf.inputs["Roughness"])
    bsdf.inputs["Specular IOR Level"].default_value = 0.2
    return m

rock_mat_a = make_rock_material("WELESZA_rock_a", 1, "rock/rock_stones_mossy", 3.0)
rock_mat_b = make_rock_material("WELESZA_rock_b", 2, "rock/rock_cracked_with_moss", 2.8)
rock_mat_c = make_rock_material("WELESZA_rock_c", 3, "rock/rock_lichen_moss_ground", 3.2)
rock_mat_boulder = make_rock_material("WELESZA_rock_boulder", 4, "rock/rock_cracked_with_moss", 1.8)

def make_ground_mat(name, texbase):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    col = load_img(os.path.join(TEX, f"{texbase}_color.png"), f"{name}_c")
    nrm = load_img(os.path.join(TEX, f"{texbase}_normal.png"), f"{name}_n", True)
    hgt = load_img(os.path.join(TEX, f"{texbase}_height.png"), f"{name}_h", True)
    rgh = load_img(os.path.join(TEX, f"{texbase}_rough.png"), f"{name}_r", True)
    texc = nt.nodes.new("ShaderNodeTexImage"); texc.image = col
    texn = nt.nodes.new("ShaderNodeTexImage"); texn.image = nrm
    texd = nt.nodes.new("ShaderNodeTexImage"); texd.image = hgt
    texr = nt.nodes.new("ShaderNodeTexImage"); texr.image = rgh
    nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = 0.8
    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Scale"].default_value = 0.008
    uvmap = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    # 60 px/m; klatka 3.2 m szerokości; tekstura 1024 px => 1 kafel = ~1.28 m przy skali 0.4
    mapping.inputs["Scale"].default_value = (0.4, 0.4, 0.4)
    nt.links.new(uvmap.outputs["UV"], mapping.inputs["Vector"])
    for t in (texc, texn, texd, texr):
        nt.links.new(mapping.outputs["Vector"], t.inputs["Vector"])
    nt.links.new(texc.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(texn.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    nt.links.new(texd.outputs["Color"], disp.inputs["Height"])
    nt.links.new(disp.outputs["Displacement"], nt.nodes["Material Output"].inputs["Displacement"])
    nt.links.new(texr.outputs["Color"], bsdf.inputs["Roughness"])
    bsdf.inputs["Specular IOR Level"].default_value = 0.25
    return m

mud_mat = make_ground_mat("WELESZA_mud", "ground/wet_mud_with_puddles")
lit_mat = make_ground_mat("WELESZA_litter", "ground/forest_litter_mixed")

# ============================== GEOMETRIA SKAŁ ==============================
def make_rock(name, seed, base_r, squash, scale_xyz, spikes=0.35, subsurf=3):
    import mathutils
    from mathutils import noise as bnoise
    r = random.Random(seed)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subsurf, radius=base_r, location=(0,0,0))
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = scale_xyz
    bpy.ops.object.transform_apply(scale=True)
    mesh = ob.data
    for v in mesh.vertices:
        n = bnoise.noise(mathutils.Vector(v.co) * 1.6 + mathutils.Vector((seed*3.7, seed*1.3, seed*2.9)))
        v.co += v.normal * (n * spikes * base_r)
    zmin = min(v.co.z for v in mesh.vertices)
    for v in mesh.vertices:
        if v.co.z < zmin + 0.12 * abs(zmin):
            v.co.z = zmin + (v.co.z - zmin) * 0.15
    for p in mesh.polygons:
        p.use_smooth = True
    mod = ob.modifiers.new("dec", "DECIMATE")
    mod.ratio = 0.35
    sm = ob.modifiers.new("sm", "SMOOTH")
    sm.iterations = 8; sm.factor = 0.5
    return ob

# assety: (nazwa, seed, promień, squash, skala_xyz, spikes)
rock_specs = [
    ("kamien_a", 11, 0.22, 0.62, (1.25, 0.95, 1.0), 0.35),
    ("kamien_b", 22, 0.30, 0.80, (0.85, 1.30, 1.0), 0.45),
    ("kamien_c", 33, 0.16, 0.50, (1.10, 0.80, 1.0), 0.30),
]
mats = {"kamien_a": rock_mat_a, "kamien_b": rock_mat_b, "kamien_c": rock_mat_c}
for name, seed, rad, sq, s, sp in rock_specs:
    ob = make_rock(name, seed, rad, sq, s, sp)
    ob.data.materials.append(mats[name])

boulder = make_rock("glaz", 44, 0.85, 0.7, (1.35, 1.0, 1.0), 0.40, subsurf=4)
boulder.data.materials.append(rock_mat_boulder)

# płaszczyzna podłoża do podglądów (_mud/_litter) — NIE jest eksportem gry
bpy.ops.mesh.primitive_plane_add(size=12, location=(0,0,-0.001))
preview_ground = bpy.context.active_object
preview_ground.name = "PodgladPodloze"

# odbiornik cienia dla osobnej warstwy _shadow
bpy.ops.mesh.primitive_plane_add(size=6, location=(0,0,0))
shadow_catcher = bpy.context.active_object
shadow_catcher.name = "OdbiornikCienia"
shadow_catcher.is_shadow_catcher = True

# ============================== KOLEKCJE: porządek ==============================
col_assets = bpy.data.collections.new("Assety")
col_scene = bpy.data.collections.new("ScenaTestowa")
sc.collection.children.link(col_assets)
sc.collection.children.link(col_scene)
for o in list(sc.collection.objects):
    if o.name.startswith(("kamien", "glaz")):
        sc.collection.objects.unlink(o)
        col_assets.objects.link(o)

# ============================== ZAPIS .BLEND ==============================
out_blend = os.environ.get("WELESZA_BLEND", os.path.join(os.path.dirname(BASE), "welesza_env_01.blend"))
bpy.ops.wm.save_as_mainfile(filepath=out_blend)
print("SAVED", out_blend)
