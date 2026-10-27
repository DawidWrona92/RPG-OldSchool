"""Wspólna biblioteka środowiska Weleszy — budowanie sceny i renderowanie.

Uruchamiane przez Blender 5.2 jako moduł Pythona (bpy):
    PYTHONPATH=<bpy wheel> LD_LIBRARY_PATH=<xlibs> python3.13 source/build_env.py

Wszystkie odległości w metrach. Kontrakt kamery zgodny ze sprite'ami postaci:
- projekcja ortograficzna, 30° nad horyzontem, patrzy w kierunku +X,+Y
  (postać "S" = patrzy na -X,-Y, czyli przodem do kamery)
- skala 60 px/m (ortho_scale = szerokość kadru / 60)
- światło chłodne z lewej góry ekranu (Sun + słaby fill z dołu)
"""
import math

import bpy
from mathutils import Vector

# ---------- kontrakt kamery (zgodny z meshkit/sdfkit) ----------

ELEVATION = math.radians(30.0)     # nachylenie kamery nad horyzontem
FRAME_W_M = 3.2                     # szerokość kadru w metrach (192 px / 60 px/m)
PX_PER_M = 60.0
CENTER_Z = 1.2                      # kamera celuje na wysokość 1,2 m
RENDER_SIZE = 192                   # docelowy rozmiar klatki (px)
RENDER_HI = 384                     # render roboczy (2x supersampling)

# Kamera patrzy w kierunku +X,+Y (azymut 45°). Front postaci = -X,-Y.
CAM_AZIMUTH = math.radians(45.0)

# Paleta Weleszy (z NIEMIR_ART_DIRECTION.md)
PALETTE = {
    "stone":   (0.42, 0.44, 0.40),   # kamień #62685B
    "stone_d": (0.33, 0.35, 0.32),   # kamień ciemniejszy (wilgotny)
    "mud":     (0.25, 0.22, 0.18),   # błoto #3F3931
    "mud_wet": (0.18, 0.17, 0.15),   # mokre błoto (ciemniejsze, połysk)
    "litter":  (0.28, 0.24, 0.17),   # ściółka leśna
    "leaf":    (0.32, 0.30, 0.16),   # liść (brudna zieleń/żółć)
    "needle":  (0.30, 0.26, 0.14),   # igliwie
    "moss":    (0.22, 0.26, 0.14),   # mech
    "root":    (0.24, 0.18, 0.12),   # korzeń/kora
}


def reset_scene():
    """Czysta scena: jedna kolekcja 'Environment'."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 64
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = "OPENIMAGEDENOISE"
    scene.render.resolution_x = RENDER_HI
    scene.render.resolution_y = RENDER_HI
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    # zarządzanie kolorem: neutralny (bez filmowego tonemappingu)
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0
    # kolekcja na assety
    col = bpy.data.collections.new("Environment")
    scene.collection.children.link(col)
    return scene, col


def setup_camera(col, target=(0.0, 0.0, CENTER_Z), ortho_w=FRAME_W_M, azimuth=CAM_AZIMUTH):
    """Kamera ortograficzna 30° nad horyzontem, patrzy w kierunku (cos az, sin az)."""
    cam_data = bpy.data.cameras.new("IsoCam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = ortho_w
    cam_data.clip_start = 0.1
    cam_data.clip_end = 100.0
    cam = bpy.data.objects.new("IsoCam", cam_data)
    col.objects.link(cam)
    dist = 20.0
    tgt = Vector(target)
    loc = Vector((
        tgt.x - dist * math.cos(ELEVATION) * math.cos(azimuth),
        tgt.y - dist * math.cos(ELEVATION) * math.sin(azimuth),
        tgt.z + dist * math.sin(ELEVATION),
    ))
    cam.location = loc
    direction = tgt - loc
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    return cam


def setup_lights(col):
    """Chłodne światło bazowe z lewej góry ekranu + słaby ciepły fill (odbicie)."""
    # Key: sun, chłodny, z lewej góry (ekranowo lewo = -Y w świecie przy azymucie 45°)
    key_d = bpy.data.lights.new("Key_Cool", "SUN")
    key_d.energy = 2.2
    key_d.color = (0.72, 0.80, 0.96)
    key_d.angle = math.radians(8)
    key = bpy.data.objects.new("Key_Cool", key_d)
    col.objects.link(key)
    # kierunek światła: z lewej góry ekranu, lekko z przodu
    key.rotation_euler = (math.radians(52), 0.0, math.radians(-38))

    # Fill: zimne odbicie z dołu/przodu (ziemia), bardzo słabe
    fill_d = bpy.data.lights.new("Fill_Ground", "AREA")
    fill_d.energy = 12.0
    fill_d.color = (0.42, 0.40, 0.36)
    fill_d.shape = "DISK"
    fill_d.size = 8.0
    fill = bpy.data.objects.new("Fill_Ground", fill_d)
    col.objects.link(fill)
    fill.location = (0.5, 0.5, -2.5)
    fill.rotation_euler = (math.radians(180), 0, 0)

    # Rim: bardzo słabe chłodne światło z prawej (separacja sylwetki)
    rim_d = bpy.data.lights.new("Rim_Cool", "AREA")
    rim_d.energy = 6.0
    rim_d.color = (0.55, 0.65, 0.85)
    rim_d.shape = "DISK"
    rim_d.size = 6.0
    rim = bpy.data.objects.new("Rim_Cool", rim_d)
    col.objects.link(rim)
    rim.location = (4.0, -3.0, 3.0)
    rim.rotation_euler = (math.radians(60), 0, math.radians(140))
    return key, fill, rim


# ---------- materiały ----------

def _principled(mat, color, rough=0.9, spec=0.05):
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = spec
    elif "Specular" in bsdf.inputs:
        bsdf.inputs["Specular"].default_value = spec
    return mat


def _noise_displacement(mat, scale=2.0, strength=0.04, rough_boost=0.0):
    """Displacement przez Noise Texture + Bump — nierówności skały/ziemi."""
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Scale"].default_value = strength
    disp.inputs["Midlevel"].default_value = 0.0
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 8.0
    noise.inputs["Roughness"].default_value = 0.6
    nt.links.new(noise.outputs["Color"], disp.inputs["Height"])
    mat.displacement_method = "BOTH"
    return mat


def stone_material(name, base=None, wet=False, moss=False):
    """Materiał skały: szarozielony, matowy, z nierównościami.
    wet=True — połysk wilgoci (mniejsza roughness na górze)."""
    base = base or PALETTE["stone"]
    mat = bpy.data.materials.new(name)
    _principled(mat, base, rough=0.92 if not wet else 0.75, spec=0.04)
    _noise_displacement(mat, scale=3.0, strength=0.035)
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    if wet:
        # mieszanka: bardziej mokre (ciemniejsze) obniżenia przez noise
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 5.0
        noise.inputs["Detail"].default_value = 6.0
        mix = nt.nodes.new("ShaderNodeMixRGB")
        mix.inputs["Fac"].default_value = 0.0
        nt.links.new(noise.outputs["Color"], mix.inputs["Fac"])
        mix.inputs[1].default_value = (*PALETTE["stone_d"], 1.0)
        mix.inputs[2].default_value = (*base, 1.0)
        # połysk: zmniejsz roughness tam gdzie mokre
        rough_mix = nt.nodes.new("ShaderNodeMixRGB")
        rough_mix.blend_type = "MULTIPLY"
        nt.links.new(noise.outputs["Color"], rough_mix.inputs["Fac"])
        rough_mix.inputs[1].default_value = (0.55, 0.55, 0.55, 1.0)
        rough_mix.inputs[2].default_value = (1.0, 1.0, 1.0, 1.0)
        nt.links.new(rough_mix.outputs["Color"], bsdf.inputs["Roughness"])
        nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    if moss:
        # zielone plamy mchu w zagłębieniach
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 7.0
        noise.inputs["Detail"].default_value = 5.0
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.55
        ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
        ramp.color_ramp.elements[1].position = 0.75
        ramp.color_ramp.elements[1].color = (*PALETTE["moss"], 1.0)
        nt.links.new(noise.outputs["Color"], ramp.inputs["Fac"])
        mix = nt.nodes.new("ShaderNodeMixRGB")
        nt.links.new(ramp.outputs["Color"], mix.inputs["Fac"])
        mix.inputs[1].default_value = (*base, 1.0)
        mix.inputs[2].default_value = (*PALETTE["moss"], 1.0)
        nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def mud_material(name, wet=True):
    """Błotnisty trakt: ciemna ziemia, kałuże (połysk), koleiny."""
    mat = bpy.data.materials.new(name)
    base = PALETTE["mud_wet"] if wet else PALETTE["mud"]
    _principled(mat, base, rough=0.95 if not wet else 0.55, spec=0.08)
    _noise_displacement(mat, scale=1.5, strength=0.05)
    if wet:
        nt = mat.node_tree
        bsdf = nt.nodes["Principled BSDF"]
        # kałuże: bardzo gładkie, ciemne plamy (niska roughness)
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 2.5
        noise.inputs["Detail"].default_value = 4.0
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.6
        ramp.color_ramp.elements[0].color = (1, 1, 1, 1)
        ramp.color_ramp.elements[1].position = 0.85
        ramp.color_ramp.elements[1].color = (0, 0, 0, 1)
        nt.links.new(noise.outputs["Color"], ramp.inputs["Fac"])
        rough_mix = nt.nodes.new("ShaderNodeMixRGB")
        rough_mix.blend_type = "MULTIPLY"
        nt.links.new(ramp.outputs["Color"], rough_mix.inputs["Fac"])
        rough_mix.inputs[1].default_value = (0.25, 0.25, 0.25, 1.0)   # kałuża: gładka
        rough_mix.inputs[2].default_value = (1.0, 1.0, 1.0, 1.0)
        nt.links.new(rough_mix.outputs["Color"], bsdf.inputs["Roughness"])
        # kolor kałuż: ciemniejszy
        col_mix = nt.nodes.new("ShaderNodeMixRGB")
        nt.links.new(ramp.outputs["Color"], col_mix.inputs["Fac"])
        col_mix.inputs[1].default_value = (*PALETTE["mud_wet"], 1.0)
        col_mix.inputs[2].default_value = (*PALETTE["mud"], 1.0)
        nt.links.new(col_mix.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def litter_material(name):
    """Leśna ściółka: ziemia + drobne liście i igliwie (osobne obiekty w scenie)."""
    mat = bpy.data.materials.new(name)
    _principled(mat, PALETTE["litter"], rough=0.98, spec=0.02)
    _noise_displacement(mat, scale=2.0, strength=0.04)
    return mat


def leaf_material(name, color_key="leaf"):
    mat = bpy.data.materials.new(name)
    _principled(mat, PALETTE[color_key], rough=0.95, spec=0.03)
    return mat


# ---------- geometria kamieni ----------

def _displace_mesh(obj, amp, scale=3.0, seed=1):
    """Nierówności przez Displace modifier + Voronoi Texture (powtarzalne, bez sculpt).

    Voronoi F2 daje "ziarnistą" strukturę skały; noise_scale kontroluje skalę.
    """
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    mod = obj.modifiers.new("RockShape", "DISPLACE")
    tex = bpy.data.textures.new(f"RockNoise_{seed}", "VORONOI")
    tex.distance_metric = "DISTANCE"     # gładkie komórki
    tex.noise_scale = scale
    tex.noise_intensity = 1.0
    mod.texture = tex
    mod.strength = amp
    mod.mid_level = 0.0
    mod.texture_coords = "OBJECT"
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def make_stone(name, col, radius=0.35, height=0.28, seed=1, flatness=0.8,
               mat=None, location=(0, 0, 0), rotation=(0, 0, 0)):
    """Kamień: spłaszczona, nieregularna bryła (icosphere + displace + smooth)."""
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=radius, location=location)
    obj = bpy.context.active_object
    obj.name = name
    col.objects.link(obj)
    bpy.context.collection.objects.unlink(obj) if obj.name in bpy.context.collection.objects else None
    # spłaszczenie w Z
    obj.scale = (1.0, 1.0 * flatness, height / radius)
    bpy.ops.object.transform_apply(scale=True)
    # nierówności (kilka warstw: duże bryły + drobne ziarno)
    _displace_mesh(obj, amp=radius * 0.16, scale=2.2 + seed * 0.3, seed=seed)
    _displace_mesh(obj, amp=radius * 0.06, scale=6.0 + seed, seed=seed + 10)
    # wygładzenie
    mod = obj.modifiers.new("Smooth", "SMOOTH")
    mod.factor = 0.6
    mod.iterations = 2
    bpy.ops.object.modifier_apply(modifier=mod.name)
    # przesunięcie tak, żeby dół był na z=0
    zmin = min(v.co.z for v in obj.data.vertices)
    obj.location.z = location[2] - zmin
    obj.location.x = location[0]
    obj.location.y = location[1]
    obj.rotation_euler = rotation
    if mat:
        obj.data.materials.append(mat)
    return obj


def make_boulder(name, col, size=1.1, seed=7, mat=None, location=(0, 0, 0), rotation=(0, 0, 0)):
    """Głaz: większa, kanciasta bryła (cube + displace, mniej wygładzania)."""
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    obj = bpy.context.active_object
    obj.name = name
    col.objects.link(obj)
    try:
        bpy.context.collection.objects.unlink(obj)
    except Exception:
        pass
    bpy.ops.object.transform_apply(scale=True)
    # losowe rozciągnięcie — głaz leży nierówno
    obj.scale = (1.0, 0.75, 0.55)
    bpy.ops.object.transform_apply(scale=True)
    # mocne nierówności, kilka warstw (różne skale szumu)
    for i, (amp, sc) in enumerate(((0.16, 1.8), (0.09, 4.5), (0.05, 9.0), (0.025, 16.0))):
        _displace_mesh(obj, amp=amp * size, scale=sc + seed * 0.7, seed=seed + i * 3)
    # lekkie wygładzenie
    mod = obj.modifiers.new("Smooth", "SMOOTH")
    mod.factor = 0.35
    mod.iterations = 1
    bpy.ops.object.modifier_apply(modifier=mod.name)
    # dół na z=0 (przed obrotem)
    zmin = min(v.co.z for v in obj.data.vertices)
    obj.location.z = location[2] - zmin
    obj.location.x = location[0]
    obj.location.y = location[1]
    obj.rotation_euler = rotation
    if mat:
        obj.data.materials.append(mat)
    return obj


# ---------- podłoże ----------

def make_ground_plane(name, col, size=4.0, mat=None, location=(0, 0, 0), z=0.0):
    """Płaska płaszczyzna podłoża."""
    bpy.ops.mesh.primitive_plane_add(size=size, location=(location[0], location[1], z))
    obj = bpy.context.active_object
    obj.name = name
    col.objects.link(obj)
    try:
        bpy.context.collection.objects.unlink(obj)
    except Exception:
        pass
    if mat:
        obj.data.materials.append(mat)
    return obj


def make_leaf(name, col, size=0.06, mat=None, location=(0, 0, 0.01), rotation=None):
    """Pojedynczy liść: płaski, lekko wygięty dysk."""
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=size, location=location)
    obj = bpy.context.active_object
    obj.name = name
    col.objects.link(obj)
    try:
        bpy.context.collection.objects.unlink(obj)
    except Exception:
        pass
    obj.scale = (1.0, 0.7, 0.12)
    bpy.ops.object.transform_apply(scale=True)
    if rotation:
        obj.rotation_euler = rotation
    if mat:
        obj.data.materials.append(mat)
    return obj


def scatter_leaves(col, area, count, size_range=(0.04, 0.09), z=0.005, seed=3,
                   mat_leaf=None, mat_needle=None):
    """Rozrzuca liście/igliwie na prostokątnym obszarze (deterministycznie)."""
    import random
    rng = random.Random(seed)
    x0, y0, x1, y1 = area
    out = []
    for i in range(count):
        x = rng.uniform(x0, x1)
        y = rng.uniform(y0, y1)
        s = rng.uniform(*size_range)
        rot = (rng.uniform(0, math.pi), rng.uniform(0, math.pi), rng.uniform(0, 2 * math.pi))
        if rng.random() < 0.55:
            m = mat_leaf
        else:
            m = mat_needle
        obj = make_leaf(f"leaf_{i}", col, size=s, mat=m, location=(x, y, z), rotation=rot)
        out.append(obj)
    return out


# ---------- znacznik skali ----------

def make_scale_marker(col, height=1.8, location=(0, 0, 0)):
    """Prosty znacznik: pionowy słupek wysokości człowieka (1,8 m)."""
    bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=height, location=location)
    obj = bpy.context.active_object
    obj.name = "ScaleMarker_1m80"
    col.objects.link(obj)
    try:
        bpy.context.collection.objects.unlink(obj)
    except Exception:
        pass
    obj.location.z = location[2] + height / 2
    mat = bpy.data.materials.new("ScaleMarker")
    _principled(mat, (0.85, 0.75, 0.35), rough=0.6, spec=0.1)
    obj.data.materials.append(mat)
    # poprzeczka na wysokości głowy (1,8 m) i pasa (1,0 m)
    for h, nm in ((height, "head"), (1.0, "belt")):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.045, depth=0.02, location=(0, 0, h))
        bar = bpy.context.active_object
        bar.name = f"ScaleMarker_{nm}"
        col.objects.link(bar)
        try:
            bpy.context.collection.objects.unlink(bar)
        except Exception:
            pass
        bar.location = (location[0], location[1], location[2] + h)
        bar.rotation_euler = (math.radians(90), 0, 0)
        bar.data.materials.append(mat)
    return obj


# ---------- render ----------

def render(scene, filepath, size=RENDER_HI):
    scene.render.resolution_x = size
    scene.render.resolution_y = size
    scene.render.filepath = filepath
    bpy.ops.render.render(write_still=True)
    return filepath


def downscale_to_192(src_png, dst_png):
    """Zmniejsza render 384→192 Lanczosem (poza Blenderem, w Pillow)."""
    from PIL import Image
    with Image.open(src_png) as im:
        im = im.convert("RGBa").resize((RENDER_SIZE, RENDER_SIZE), Image.Resampling.LANCZOS)
        im.convert("RGBA").save(dst_png)
    return dst_png
