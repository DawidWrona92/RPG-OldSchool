# Welesza environment 01 — budowa sceny .blend (Blender 4.3, bpy).
# TEN PLIK TYLKO BUDUJE I ZAPISUJE .blend — jest źródłem.
# Render osobno: render_env_v43.py (czyta .blend, nie modyfikuje go).
#
# Kontrakt: docs/art/KONTRAKT-RENDERU.md
# Kamera/światła skopiowane z source/bohater.blend (vibe/sprite-bohater-codex).
import bpy, math, random, os

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = "/workspace/github__DawidWrona92__RPG-OldSchool"
_envwork = "/workspace/envwork/textures_pbr"
_repo_tex = os.path.join(REPO, "assets", "environment", "stones-mistral-01", "textures_src")
TEX = os.environ.get("WELESZA_TEX", _repo_tex if os.path.isdir(_repo_tex) else _envwork)

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
def add_area_light(name, energy, size, color, location, rotation_deg):
    bpy.ops.object.light_add(type="AREA", location=location)
    l = bpy.context.active_object
    l.name = name
    l.data.energy = energy
    l.data.size = size
    l.data.color = color
    l.data.shape = "DISK"
    l.rotation_euler = (math.radians(rotation_deg[0]), math.radians(rotation_deg[1]), math.radians(rotation_deg[2]))
    return l

# rotacje odczytane z bohater.blend (4.3): DISK, track-to na (0,0,~1)
add_area_light("Klucz", 520.0, 2.3, (0.94, 0.92, 0.85), (2.8, -3.5, 6.0), (41.87, 0.0, 38.66))
add_area_light("Wypelnienie_tyl", 140.0, 3.0, (0.60, 0.70, 0.85), (-3.0, 1.0, 4.0), (46.51, 0.0, -108.43))
add_area_light("Odbicie_ziemi", 65.0, 4.0, (0.64, 0.68, 0.74), (3.0, 4.0, 2.5), (73.30, 0.0, 143.13))

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

def make_rock_material(name, seed, texbase, mapping_scale, moss_strength=1.0):
    """Skala: albedo z biblioteki; MECH tylko na gorach (maska z normalnej Z),
    tekstura w skali ~1-2 m/powtorzenie z dwoma warstwami rozbijacymi powtorki."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    r = random.Random(seed)
    col = load_img(os.path.join(TEX, f"{texbase}_color.png"), f"{name}_c")
    nrm = load_img(os.path.join(TEX, f"{texbase}_normal.png"), f"{name}_n", True)
    rgh = load_img(os.path.join(TEX, f"{texbase}_rough.png"), f"{name}_r", True)
    moss = load_img(os.path.join(TEX, "ground/dense_forest_moss_color.png"), f"{name}_moss")
    texc = nt.nodes.new("ShaderNodeTexImage"); texc.image = col
    texc2 = nt.nodes.new("ShaderNodeTexImage"); texc2.image = col
    texn = nt.nodes.new("ShaderNodeTexImage"); texn.image = nrm
    texr = nt.nodes.new("ShaderNodeTexImage"); texr.image = rgh
    texm = nt.nodes.new("ShaderNodeTexImage"); texm.image = moss
    nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = 1.0
    # warstwa 1: skala ~1-2 m na powtorzenie (mapping 1.0 = kafel 1 m przy Object coords na obiekcie ~1 m)
    mp1 = nt.nodes.new("ShaderNodeMapping")
    mp1.inputs["Scale"].default_value = (mapping_scale, mapping_scale, mapping_scale)
    mp1.inputs["Rotation"].default_value = (0, 0, r.uniform(0, 0.6))
    # warstwa 2: przesuniecie + inna skala — rozbicie widocznego powtorzenia
    mp2 = nt.nodes.new("ShaderNodeMapping")
    mp2.inputs["Scale"].default_value = (mapping_scale*1.37, mapping_scale*0.83, mapping_scale)
    mp2.inputs["Location"].default_value = (r.uniform(0, 3), r.uniform(0, 3), 0)
    tco = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tco.outputs["Object"], mp1.inputs["Vector"])
    nt.links.new(tco.outputs["Object"], mp2.inputs["Vector"])
    nt.links.new(mp1.outputs["Vector"], texc.inputs["Vector"])
    nt.links.new(mp2.outputs["Vector"], texc2.inputs["Vector"])
    nt.links.new(mp1.outputs["Vector"], texn.inputs["Vector"])
    nt.links.new(mp1.outputs["Vector"], texr.inputs["Vector"])
    # mix warstw koloru 50/50
    mixc = nt.nodes.new("ShaderNodeMix"); mixc.data_type = "RGBA"
    mixc.inputs["Factor"].default_value = 0.5
    nt.links.new(texc.outputs["Color"], mixc.inputs[6])
    nt.links.new(texc2.outputs["Color"], mixc.inputs[7])
    # MECH: maska z geometrii — normal.wysokosc Z (geometry node -> separate z)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sepz = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Normal"], sepz.inputs["Vector"])
    moss_mask = nt.nodes.new("ShaderNodeMapRange")
    moss_mask.inputs["From Min"].default_value = 0.05
    moss_mask.inputs["From Max"].default_value = 0.65
    moss_mask.inputs["To Min"].default_value = 0.0
    moss_mask.inputs["To Max"].default_value = 1.0
    nt.links.new(sepz.outputs["Z"], moss_mask.inputs["Value"])
    # szum lamie maske (mech w kepkach)
    mno = nt.nodes.new("ShaderNodeTexNoise")
    mno.inputs["Scale"].default_value = 6.0; mno.inputs["Detail"].default_value = 6
    nt.links.new(mp1.outputs["Vector"], mno.inputs["Vector"])
    # noise zaweza maske do 0.25..1.0 (mech w kepkach, ale nigdy nie znika calkiem)
    nmr = nt.nodes.new("ShaderNodeMapRange")
    nmr.inputs["From Min"].default_value = 0.0; nmr.inputs["From Max"].default_value = 1.0
    nmr.inputs["To Min"].default_value = 0.25; nmr.inputs["To Max"].default_value = 1.0
    nt.links.new(mno.outputs["Fac"], nmr.inputs["Value"])
    mmul = nt.nodes.new("ShaderNodeMath"); mmul.operation = "MULTIPLY"
    nt.links.new(moss_mask.outputs["Result"], mmul.inputs[0])
    nt.links.new(nmr.outputs["Result"], mmul.inputs[1])
    mfin = nt.nodes.new("ShaderNodeMath")
    mfin.operation = "MULTIPLY"; mfin.inputs[1].default_value = moss_strength
    nt.links.new(mmul.outputs["Value"], mfin.inputs[0])
    nt.links.new(mp1.outputs["Vector"], texm.inputs["Vector"])
    # mech: jawna zielec boru modulowana luminancja tekstury mchu (tekstura zoltawa w bibliotece)
    mlum = nt.nodes.new("ShaderNodeRGBToBW")
    nt.links.new(texm.outputs["Color"], mlum.inputs["Color"])
    mmr = nt.nodes.new("ShaderNodeMapRange")
    mmr.inputs["From Min"].default_value = 0.1; mmr.inputs["From Max"].default_value = 0.9
    mmr.inputs["To Min"].default_value = 0.35; mmr.inputs["To Max"].default_value = 1.1
    nt.links.new(mlum.outputs["Val"], mmr.inputs["Value"])
    mgreen = nt.nodes.new("ShaderNodeRGB")
    mgreen.outputs[0].default_value = (0.13, 0.19, 0.08, 1.0)
    mmulv = nt.nodes.new("ShaderNodeVectorMath"); mmulv.operation = "MULTIPLY"
    nt.links.new(mgreen.outputs[0], mmulv.inputs[0])
    mvec = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(mmr.outputs["Result"], mvec.inputs["X"])
    nt.links.new(mmr.outputs["Result"], mvec.inputs["Y"])
    nt.links.new(mmr.outputs["Result"], mvec.inputs["Z"])
    nt.links.new(mvec.outputs["Vector"], mmulv.inputs[1])
    # jasny rim kupek mchu od strony klucza (+X -Y): dot(world_normal, klucz_dir)
    kdir = nt.nodes.new("ShaderNodeVectorMath"); kdir.operation = "DOT_PRODUCT"
    klucz_n = nt.nodes.new("ShaderNodeCombineXYZ")
    klucz_n.inputs["X"].default_value = 0.55; klucz_n.inputs["Y"].default_value = -0.55; klucz_n.inputs["Z"].default_value = 0.63
    nt.links.new(klucz_n.outputs["Vector"], kdir.inputs[0])
    nt.links.new(geo.outputs["Normal"], kdir.inputs[1])
    krange = nt.nodes.new("ShaderNodeMapRange")
    krange.inputs["From Min"].default_value = 0.0; krange.inputs["From Max"].default_value = 1.0
    krange.inputs["To Min"].default_value = 1.0; krange.inputs["To Max"].default_value = 1.8
    nt.links.new(kdir.outputs["Value"], krange.inputs["Value"])
    # zielec bazowa * jasny rim -> wektor
    mmulv2 = nt.nodes.new("ShaderNodeVectorMath"); mmulv2.operation = "MULTIPLY"
    nt.links.new(mmulv.outputs["Vector"], mmulv2.inputs[0])
    kvec = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(krange.outputs["Result"], kvec.inputs["X"])
    nt.links.new(krange.outputs["Result"], kvec.inputs["Y"])
    nt.links.new(krange.outputs["Result"], kvec.inputs["Z"])
    nt.links.new(kvec.outputs["Vector"], mmulv2.inputs[1])
    mixmoss = nt.nodes.new("ShaderNodeMix"); mixmoss.data_type = "RGBA"
    nt.links.new(mfin.outputs["Value"], mixmoss.inputs["Factor"])
    nt.links.new(mixc.outputs[2], mixmoss.inputs[6])
    nt.links.new(mmulv2.outputs["Vector"], mixmoss.inputs[7])
    nt.links.new(mixmoss.outputs[2], bsdf.inputs["Base Color"])
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
    """Kamien: amputujace ciecia zawszedomknieciem (fill), wiecej mniejszych
    nieregularnych plaszczyzn, szum bez rozwierania scian ciecia.
    Kryterium: 0 krawedzi brzegowych nad z=0 (weryfikowane po buildzie)."""
    import mathutils
    from mathutils import noise as bnoise
    import bmesh
    r = random.Random(seed)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subsurf, radius=base_r, location=(0,0,0))
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = scale_xyz
    bpy.ops.object.transform_apply(scale=True)
    mesh = ob.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()
    # ciecia: 5-7, wiekszosc plytkich (0.72-0.95), 2 gluche kluczowe ku swiatlu
    n_cuts = r.randint(5, 7)
    for ci in range(n_cuts):
        d = r.uniform(0.72, 0.95) * base_r
        ang = r.uniform(0, 2*math.pi)
        tilt = r.uniform(0.25, 1.3)
        nrm = mathutils.Vector((math.cos(ang)*math.sin(tilt), math.sin(ang)*math.sin(tilt), math.cos(tilt)))
        nrm.normalize()
        if ci < 2:
            nrm = mathutils.Vector((0.55, -0.55, 0.63)).normalized()
            nrm.rotate(mathutils.Quaternion(mathutils.Vector((0,0,1)), r.uniform(-0.6, 0.6)))
            d = r.uniform(0.38, 0.55) * base_r
        res = bmesh.ops.bisect_plane(
            bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
            plane_co=nrm*d, plane_no=nrm,
            clear_outer=True, clear_inner=False)
        # ZAWSZE domknij przekroj
        ce = [g for g in res.get("geom_cut", []) if isinstance(g, bmesh.types.BMEdge)]
        if ce:
            bmesh.ops.edgeloop_fill(bm, edges=ce)
    bm.to_mesh(mesh)
    bm.free()
    # szum tylko na wewnetrznych wierzcholkach (odleglosc od kazdej plaszczyzny ciecia > 18% R)
    cut_planes = []
    r2 = random.Random(seed)
    n2 = r2.randint(5, 7)
    for ci in range(n2):
        d2 = r2.uniform(0.72, 0.95) * base_r
        ang2 = r2.uniform(0, 2*math.pi)
        tilt2 = r2.uniform(0.25, 1.3)
        nrm2 = mathutils.Vector((math.cos(ang2)*math.sin(tilt2), math.sin(ang2)*math.sin(tilt2), math.cos(tilt2))).normalized()
        if ci < 2:
            nrm2 = mathutils.Vector((0.55, -0.55, 0.63)).normalized()
            nrm2.rotate(mathutils.Quaternion(mathutils.Vector((0,0,1)), r2.uniform(-0.6, 0.6)))
            d2 = r2.uniform(0.38, 0.55) * base_r
        cut_planes.append((nrm2, d2))
    for v in mesh.vertices:
        p = mathutils.Vector(v.co)
        on_cut = any(abs(p.dot(nrm) - d) < base_r * 0.18 for nrm, d in cut_planes)
        if not on_cut:
            n = bnoise.noise(p * 2.4 + mathutils.Vector((seed*3.7, seed*1.3, seed*2.9)))
            v.co += v.normal * (n * spikes * base_r * 0.30)
    # podstawa: splaszczona, wkopana ~15%
    zmin = min(v.co.z for v in mesh.vertices)
    for v in mesh.vertices:
        if v.co.z < zmin + 0.25*abs(zmin):
            v.co.z = zmin - (zmin - v.co.z) * 0.3
    # cieniowanie gladkie z ostrymi krawedziami >35°
    bpy.ops.object.shade_smooth()
    try:
        import math as _m
        bpy.ops.object.shade_smooth_by_angle(angle=_m.radians(35))
    except Exception:
        pass
    # KRYTERIUM: 0 krawedzi brzegowych nad z=0
    bmv = bmesh.new()
    bmv.from_mesh(mesh)
    leaks = sum(1 for e in bmv.edges if e.is_boundary and max(vv.co.z for vv in e.verts) > 0.001)
    bmv.free()
    if leaks:
        raise SystemExit(f"BLOKER: {name} ma {leaks} krawedzi brzegowych nad z=0")
    return ob

# assety bazowe: kamien a/b/c + glaz (1.0-1.4 m nad ziemia) + glaz_duzy (1.8-2.0 m)
rock_specs = [
    ("kamien_a", 11, 0.22, 0.62, (1.25, 0.95, 1.0), 0.35),
    ("kamien_b", 22, 0.30, 0.80, (0.85, 1.30, 1.0), 0.45),
    ("kamien_c", 33, 0.16, 0.50, (1.10, 0.80, 1.0), 0.30),
]
mat_by_name = {"kamien_a": rock_mat_a, "kamien_b": rock_mat_b, "kamien_c": rock_mat_c}
for name, seed, rad, sq, scl, sp in rock_specs:
    ob = make_rock(name, seed, rad, sq, scl, sp)
    ob.data.materials.append(mat_by_name[name])

boulder = make_rock("glaz", 44, 1.30, 0.55, (1.35, 1.0, 1.0), 0.28, subsurf=4)
boulder.data.materials.append(rock_mat_boulder)
boulder_big = make_rock("glaz_duzy", 45, 1.95, 0.52, (1.4, 1.1, 1.0), 0.30, subsurf=4)
boulder_big.data.materials.append(rock_mat_boulder)

# ============================== GRUPA A: warianty kamieni ==============================
wet_rock_mat = make_rock_material("WELESZA_rock_wet", 5, "rock/rock_stones_mossy", 2.6, moss_strength=0.35)
wet_rock_mat.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.8
wet_rock_mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.35

mossy_rock_mat = make_rock_material("WELESZA_rock_mossy", 6, "rock/rock_stones_mossy", 2.8, moss_strength=1.0)
lichen_rock_mat = make_rock_material("WELESZA_rock_lichen", 7, "rock/rock_lichen_moss_ground", 2.4, moss_strength=0.5)

_mats_a = {"kamien_mokry": wet_rock_mat, "kamien_z_mchem": mossy_rock_mat, "kamien_z_porostami": lichen_rock_mat}
for nm, sd, rad, sq, scl in [
    ("kamien_mokry", 51, 0.30, 0.52, (1.2, 0.9, 1.0)),
    ("kamien_z_mchem", 52, 0.34, 0.55, (1.05, 1.1, 1.0)),
    ("kamien_z_porostami", 53, 0.28, 0.48, (1.0, 0.85, 1.0)),
]:
    ob = make_rock(nm, sd, rad, sq, scl, spikes=0.30)
    ob.data.materials.append(_mats_a[nm])

def make_gravel(name, seed, n=(5, 9), rad=(0.03, 0.08)):
    """Zwir: domkniete brylki (kula z odcietym spodem), w rozsypie."""
    import mathutils
    r = random.Random(seed)
    mesh = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(ob)
    verts, faces = [], []
    for i in range(r.randint(*n)):
        ang = r.uniform(0, 2*math.pi)
        dist = r.uniform(0, 0.35)
        cx, cy = math.cos(ang)*dist, math.sin(ang)*dist
        rr = r.uniform(*rad)
        base = len(verts)
        # polkula domknieta: 2 pierscienie + top + spodni wierzcholek
        for ring, z, rf in ((0, 0.0, 1.0), (1, rr*0.55, 1.0)):
            for k in range(8):
                a = k*2*math.pi/8
                verts.append(mathutils.Vector((cx + math.cos(a)*rr*rf, cy + math.sin(a)*rr*rf, z + (rr*0.9 if ring else 0))))
        # gorny pierscien wyzej (polkula)
        for k in range(8):
            a = k*2*math.pi/8
            verts.append(mathutils.Vector((cx + math.cos(a)*rr*0.45, cy + math.sin(a)*rr*0.45, rr*1.25)))
        ctop = len(verts); verts.append(mathutils.Vector((cx, cy, rr*1.45)))
        cbot = len(verts); verts.append(mathutils.Vector((cx, cy, -rr*0.25)))
        for k in range(8):
            k2 = (k+1)%8
            # bok dolny
            faces.append((cbot, base+k, base+k2))
            # bok srodkowy
            faces.append((base+k, base+8+k, base+8+k2, base+k2))
            # bok gorny
            faces.append((base+8+k, base+16+k, base+16+k2, base+8+k2))
            # top
            faces.append((ctop, base+16+k2, base+16+k))
    mesh.from_pydata(verts, [], faces)
    mesh.validate()
    return ob

gravel_mat = make_rock_material("WELESZA_gravel", 8, "rock/rock_stones_mossy", 4.0, moss_strength=0.0)
gravel_mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.85
gravel = make_gravel("zwir", 61)
gravel.data.materials.append(gravel_mat)
gravel2 = make_gravel("zwir_b", 62, n=(6, 11))
gravel2.data.materials.append(gravel_mat)
gravel3 = make_gravel("zwir_c", 63, n=(7, 12))
gravel3.data.materials.append(gravel_mat)

def make_slab(name, seed, w=(0.5, 0.9), d=(0.4, 0.7), th=(0.08, 0.16)):
    import mathutils
    r = random.Random(seed)
    mesh = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(ob)
    W, D, T = r.uniform(*w), r.uniform(*d), r.uniform(*th)
    verts, faces = [], []
    nsides = r.randint(6, 8)
    for k in range(nsides):
        a = k*2*math.pi/nsides + r.uniform(-0.2, 0.2)
        rr = r.uniform(0.8, 1.2)
        x, y = math.cos(a)*W/2*rr, math.sin(a)*D/2*rr
        verts.append(mathutils.Vector((x, y, 0)))
        verts.append(mathutils.Vector((x, y, T)))
    for k in range(nsides):
        k2 = (k+1)%nsides
        b0, b1 = 2*k, 2*k2
        faces.append((b0, b0+1, b1+1, b1))
    c = len(verts); verts.append(mathutils.Vector((0, 0, T)))
    for k in range(nsides):
        k2 = (k+1)%nsides
        faces.append((2*k+1, 2*k2+1, c))
    c2 = len(verts); verts.append(mathutils.Vector((0, 0, 0)))
    for k in range(nsides):
        k2 = (k+1)%nsides
        faces.append((c2, 2*k2, 2*k))
    mesh.from_pydata(verts, [], faces)
    mesh.validate()
    return ob

slab = make_slab("plyta_kamienna", 71)
slab.data.materials.append(rock_mat_b)
slab2 = make_slab("plyta_kamienna_b", 72)
slab2.data.materials.append(rock_mat_c)

# ============================== RUNO: trawa, paprocie, chrust ==============================
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
        pdir = mathutils.Vector((math.cos(lean_dir), math.sin(lean_dir), 0))
        side = mathutils.Vector((-math.sin(lean_dir), math.cos(lean_dir), 0))
        b0 = mathutils.Vector((bx, by, 0)) - side*w
        b1 = mathutils.Vector((bx, by, 0)) + side*w
        # wygieta zdblka: 3 segmenty ze rosnacym przechyleniem
        seg_h = h / 3
        p_cur0, p_cur1 = b0.copy(), b1.copy()
        bend_axis = mathutils.Vector((-pdir.y, pdir.x, 0)).normalized()
        for seg in range(3):
            lean_seg = lean * (0.35 + 0.65*(seg+1)/3)
            dseg = (pdir*lean_seg + mathutils.Vector((0,0,1))).normalized()
            n0 = p_cur0 + dseg*seg_h
            n1 = p_cur1 + dseg*seg_h
            base = len(verts)
            verts += [p_cur0, p_cur1, n1, n0]
            faces.append((base, base+1, base+2, base+3))
            p_cur0, p_cur1 = n0, n1
    mesh.from_pydata(verts, [], faces)
    mesh.validate()
    return ob

def make_grass_material(name, seed):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; bsdf = nt.nodes["Principled BSDF"]
    r = random.Random(seed)
    tex = ["ground/wet_grass_earth", "ground/forest_soil_sparse_grass"][seed % 2]
    col = load_img(os.path.join(TEX, f"{tex}_color.png"), f"{name}_c")
    texc = nt.nodes.new("ShaderNodeTexImage"); texc.image = col
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (r.uniform(3.0, 6.0), r.uniform(3.0, 6.0), 1.0)
    tco = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tco.outputs["Object"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], texc.inputs["Vector"])
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tco.outputs["Object"], sep.inputs["Vector"])
    g = nt.nodes.new("ShaderNodeMapRange")
    g.inputs["From Min"].default_value = 0.0; g.inputs["From Max"].default_value = 0.28
    nt.links.new(sep.outputs["Z"], g.inputs["Value"])
    mixc = nt.nodes.new("ShaderNodeMix"); mixc.data_type = "RGBA"
    mixc.inputs["Factor"].default_value = 0.55
    dark = nt.nodes.new("ShaderNodeRGB")
    dark.outputs[0].default_value = (0.07, 0.095, 0.05, 1.0)
    nt.links.new(dark.outputs[0], mixc.inputs[6])
    nt.links.new(texc.outputs["Color"], mixc.inputs[7])
    nt.links.new(g.outputs["Result"], mixc.inputs["Factor"])
    nt.links.new(mixc.outputs[2], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.9
    bsdf.inputs["Specular IOR Level"].default_value = 0.1
    return m

grass_mats = [make_grass_material(f"WELESZA_grass_{i}", 50+i) for i in range(3)]
for gi, (name, seed) in enumerate([("kepka_trawy_a", 101), ("kepka_trawy_b", 102), ("kepka_trawy_c", 103)]):
    ob = make_grass_tuft(name, seed)
    ob.data.materials.append(grass_mats[gi % 3])

def make_fern(name, seed, fronds=8, length=(0.38, 0.62)):
    import mathutils
    r = random.Random(seed)
    mesh = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(ob)
    verts, faces = [], []
    for fi in range(fronds):
        ang = r.uniform(0, 2*math.pi)
        L = r.uniform(*length)
        tilt = r.uniform(0.5, 1.1)
        segs = 8
        prev_dir = mathutils.Vector((math.cos(ang)*math.sin(tilt), math.sin(ang)*math.sin(tilt), math.cos(tilt)))
        base_i = len(verts)
        points = [mathutils.Vector((0,0,0))]
        # wygiecie: kierunek stopniowo bardziej poziomy ku koncowi (luk paproci)
        d = prev_dir.copy()
        for si in range(1, segs+1):
            t = si/segs
            side0 = mathutils.Vector((-prev_dir.y, prev_dir.x, 0)).normalized()
            rot_amt = -0.12 * (1 if tilt < 0.8 else 0.4)
            d.rotate(mathutils.Quaternion(side0, rot_amt))
            d.z = max(d.z, -0.25)
            p = points[-1] + d * (L/segs)
            p.z = max(p.z, 0.01)
            points.append(p)
        for si, p in enumerate(points):
            side = mathutils.Vector((-prev_dir.y, prev_dir.x, 0)).normalized()
            w = 0.004 * (1 - si/segs*0.5)
            verts.append(p - side*w)
            verts.append(p + side*w)
        for si in range(segs):
            b = base_i + si*2
            faces.append((b, b+1, b+3, b+2))
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
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; bsdf = nt.nodes["Principled BSDF"]
    r = random.Random(seed)
    tex = ["ground/dense_forest_moss", "ground/wet_grass_earth"][seed % 2]
    col = load_img(os.path.join(TEX, f"{tex}_color.png"), f"{name}_c")
    texc = nt.nodes.new("ShaderNodeTexImage"); texc.image = col
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (r.uniform(4.0, 8.0), r.uniform(4.0, 8.0), 1.0)
    tco = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tco.outputs["Object"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], texc.inputs["Vector"])
    hsv = nt.nodes.new("ShaderNodeHueSaturation")
    hsv.inputs["Saturation"].default_value = 0.85
    hsv.inputs["Value"].default_value = 0.95
    hsv.inputs["Hue"].default_value = 0.42
    nt.links.new(texc.outputs["Color"], hsv.inputs["Color"])
    nt.links.new(hsv.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.85
    bsdf.inputs["Specular IOR Level"].default_value = 0.1
    return m

fern_mats = [make_fern_material(f"WELESZA_fern_{i}", 60+i) for i in range(2)]
for gi, (name, seed, rot) in enumerate([("paproc_a", 201, 0.4), ("paproc_b", 202, 2.1)]):
    ob = make_fern(name, seed)
    ob.data.materials.append(fern_mats[gi % 2])
    ob.rotation_euler[2] = rot

def make_twigs(name, seed, count=6, radius=(0.005, 0.02), length=(0.25, 0.6)):
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
        tip = base + segs*5
        center = len(verts)
        verts.append(mathutils.Vector((cx, cy, rad*0.7)) + dirv*0.5*L)
        for k in range(5):
            faces.append((tip+k, tip+(k+1)%5, center))
    mesh.from_pydata(verts, [], faces)
    mesh.validate()
    return ob

def make_wood_material(name, seed):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; bsdf = nt.nodes["Principled BSDF"]
    r = random.Random(seed)
    tex = ["bark/old_bark_weathered", "bark/pine_bark_reddish_flaky"][seed % 2]
    col = load_img(os.path.join(TEX, f"{tex}_color.png"), f"{name}_c")
    texc = nt.nodes.new("ShaderNodeTexImage"); texc.image = col
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (r.uniform(1.5, 3.0), r.uniform(1.5, 3.0), 1.0)
    tco = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tco.outputs["Object"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], texc.inputs["Vector"])
    hsv = nt.nodes.new("ShaderNodeHueSaturation")
    hsv.inputs["Saturation"].default_value = 0.22
    hsv.inputs["Value"].default_value = 0.85
    nt.links.new(texc.outputs["Color"], hsv.inputs["Color"])
    nt.links.new(hsv.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.95
    return m

twig_mat = make_wood_material("WELESZA_chrust", 70)
for name, seed in [("chrust_a", 301), ("chrust_b", 302)]:
    ob = make_twigs(name, seed)
    ob.data.materials.append(twig_mat)

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
bpy.ops.file.pack_all()
unpacked = [im.name for im in bpy.data.images if im.source == "FILE" and not im.packed_file]
if unpacked:
    raise SystemExit("BLOKER: tekstury niezapakowane: %s" % unpacked)
bpy.ops.wm.save_as_mainfile(filepath=out_blend)
print("SAVED", out_blend)
