"""Wspólne narzędzia źródła v2. Nie są wywoływane przez renderer."""
import bpy, hashlib, json, math
from pathlib import Path
from mathutils import Vector, Matrix
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
THIRD=HERE/'third_party'
TEX=HERE.parents[2]/'textures/characters/hero/unique'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read_obj():
    verts=[];uv=[];faces=[];group=''
    for line in (THIRD/'base.obj').read_text().splitlines():
        s=line.split()
        if not s:continue
        if s[0]=='v':verts.append(tuple(map(float,s[1:4])))
        elif s[0]=='vt':uv.append(tuple(map(float,s[1:3])))
        elif s[0]=='g':group=s[1]
        elif s[0]=='f' and group=='body':faces.append([tuple(int(t)-1 for t in x.split('/')[:2]) for x in s[1:]])
    return verts,uv,faces
def active(obj):
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
def plain(name,color,rough=.8,metal=0):
    m=bpy.data.materials.new(name);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal
    return m
def image_node(mat,path,linear=False):
    n=mat.node_tree.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(path),check_existing=True)
    n.image.colorspace_settings.name='Non-Color' if linear else 'sRGB';n.image.pack();n.image.filepath='//'+str(Path(path).relative_to(HERE.parents[3])) if False else str(path)
    return n
def skin():
    m=plain('Skóra / GPT6 v2 / natywne UV',(.2,.12,.08));n=m.node_tree.nodes;l=m.node_tree.links;b=n.get('Principled BSDF')
    for key,sock in [('basecolor','Base Color'),('roughness','Roughness')]:
        t=image_node(m,TEX/f'hero_skin_body_{key}.png',key!='basecolor');l.new(t.outputs['Color'],b.inputs[sock])
    t=image_node(m,TEX/'hero_skin_body_normal_opengl.png',True);normal=n.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.45;l.new(t.outputs['Color'],normal.inputs['Color']);l.new(normal.outputs['Normal'],b.inputs['Normal'])
    t=image_node(m,TEX/'hero_skin_body_sss_mask.png',True);mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';mul.inputs[1].default_value=.30;l.new(t.outputs['Color'],mul.inputs[0]);l.new(mul.outputs[0],b.inputs['Subsurface Weight'])
    b.inputs['Subsurface Radius'].default_value=(1,.45,.25);b.inputs['Subsurface Scale'].default_value=.001
    # Height dostarczony, jawnie nie podłączony obok normalnej: bez podwojenia reliefu.
    t=image_node(m,TEX/'hero_skin_body_height.png',True);t.label='Rezerwa mikrodetalu ≤0.002 m; NIE PODŁĄCZONA'
    m['texture_package']='27017148d13eb9c422ff54da760775f7eb16a331';return m
def mesh(name,verts,faces,material=None):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o)
    if material:me.materials.append(material)
    for p in me.polygons:p.use_smooth=True
    return o
def rigid(obj,bone='spine02'):
    rig=bpy.data.objects['Bohater_RIG'];g=obj.vertex_groups.new(name=bone);g.add(list(range(len(obj.data.vertices))),1,'REPLACE');m=obj.modifiers.new('Szkielet MakeHuman','ARMATURE');m.object=rig;m.use_deform_preserve_volume=True;obj.parent=rig
def save(rev):
    s=bpy.context.scene;s['art_revision']=rev;s['source_authority']='bohater_v2.blend';s['status']='WORK_IN_PROGRESS_BEFORE_B2';s.frame_set(1)
    bpy.context.preferences.filepaths.save_version=0
    for i in bpy.data.images:
        if i.source=='FILE':i.pack();i.filepath=bpy.path.relpath(i.filepath,start=str(HERE))
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'bohater_v2.blend'),compress=True)
