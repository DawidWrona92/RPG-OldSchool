"""Jednorazowe F1; nowy plik wymagany, bez regeneracji przy renderze."""
import sys,math,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v2_common import *
import numpy as np
from mathutils import Matrix,Vector
assert not (HERE/'bohater_v2.blend').exists(),'Nie nadpisuj dopracowanego źródła; użyj edycji istniejącego .blend'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
raw,uv,faces=read_obj();raw=np.array(raw);targets=json.loads((THIRD/'targets/manifest.json').read_text())
for t in targets:
    p=THIRD/'targets'/t['file'];assert sha(p)==t['sha256']
    for line in p.read_text().splitlines():
        s=line.split()
        if not s or s[0].startswith('#'):continue
        i=int(s[0]);raw[i]+=np.array(list(map(float,s[1:4])))*t['weight']
ids=np.unique([q[0] for f in faces for q in f]);low=raw[ids,1].min();scale=1.8/(raw[ids,1].max()-low)
verts=np.column_stack([raw[:,2],raw[:,0],raw[:,1]-low])*scale
body=mesh('Ciało / MakeHuman / UV natywne',verts,[[q[0] for q in f] for f in faces],skin());layer=body.data.uv_layers.new(name='UVMap')
for poly,f in zip(body.data.polygons,faces):
    for li,q in zip(poly.loop_indices,f):layer.data[li].uv=uv[q[1]]
body['native_uv']='base.obj / body / unchanged loop order';body['base_obj_sha256']=sha(THIRD/'base.obj')
body['shape_targets']=json.dumps(targets);body['scale_m_per_mh_unit']=scale
sk=json.loads((THIRD/'default.mhskel').read_text());data=bpy.data.armatures.new('MakeHuman default / 163 kości');rig=bpy.data.objects.new('Bohater_RIG',data);bpy.context.collection.objects.link(rig);active(rig);bpy.ops.object.mode_set(mode='EDIT')
def j(name):return Vector(verts[sk['joints'][name]].mean(0))
for name,b in sk['bones'].items():
    bone=data.edit_bones.new(name);bone.head=j(b['head']);bone.tail=j(b['tail'])
    if (bone.tail-bone.head).length<1e-6:bone.tail.z+=.001
    plane=sk['planes'].get(b['rotation_plane'])
    if plane:
        a,c,d=map(j,plane);normal=(c-a).cross(d-a)
        if normal.length>1e-8:bone.align_roll(normal)
for name,b in sk['bones'].items():
    if b['parent']:data.edit_bones[name].parent=data.edit_bones[b['parent']]
bpy.ops.object.mode_set(mode='OBJECT');rig.show_in_front=True
weights=json.loads((THIRD/'default_weights.mhw').read_text())['weights'];sums=np.zeros(len(verts))
for values in weights.values():
    for i,w in values:sums[i]+=w
for name,values in weights.items():
    g=body.vertex_groups.new(name=name)
    for i,w in values:
        if sums[i]>0:g.add([i],float(w/sums[i]),'REPLACE')
m=body.modifiers.new('163 kości / wagi default_weights.mhw','ARMATURE');m.object=rig;m.use_deform_preserve_volume=True;body.parent=rig
# Spokojne opuszczenie rąk na pełnym rigu; zapis jako spoczynkowa geometria.
# Obrót całego łańcucha w świecie, następnie lokalne macierze potomków.
bpy.context.view_layer.update()
for side,sgn in [('L',1),('R',-1)]:
    pb=rig.pose.bones['upperarm01.'+side];old=pb.matrix.copy();rot=Matrix.Rotation(math.radians(-sgn*31),4,'X');pb.matrix=Matrix.Translation(old.translation)@rot@Matrix.Translation(-old.translation)@old
bpy.context.view_layer.update();active(body);bpy.ops.object.modifier_apply(modifier=m.name)
active(rig);bpy.ops.object.mode_set(mode='POSE');bpy.ops.pose.armature_apply(selected=False);bpy.ops.object.mode_set(mode='OBJECT')
m=body.modifiers.new('163 kości / wagi natywne','ARMATURE');m.object=rig;m.use_deform_preserve_volume=True
s=body.modifiers.new('Powierzchnia anatomiczna','SUBSURF');s.levels=2;s.render_levels=2
# Kopia wyłącznie sprawdzonego setupu kamery/świateł, nie starego modelu.
import build_player
build_player.setup_scene();scene=bpy.context.scene;scene.frame_end=1
rig['source_skeleton_sha256']=sha(THIRD/'default.mhskel');rig['source_weights_sha256']=sha(THIRD/'default_weights.mhw');rig['rest_note']='Natywny rig, główne ramiona opuszczone o 31 stopni i utrwalone jako rest. Bez akcji.'
save('v2-F1-body-rig')
print('V2_BODY',len(body.data.vertices),len(body.data.polygons),'bones',len(rig.data.bones),'UV loops',len(layer.data),flush=True)
