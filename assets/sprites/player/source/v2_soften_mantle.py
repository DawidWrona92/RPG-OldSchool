"""Artystyczne drapowanie barków po oględzinach dużego renderu.

Punktem wyjścia pozostaje zapisane Cloth. Końcowa powierzchnia spoczywa na
rzeczywistym ubraniu przez projekcję grawitacyjną i opada poza jego obrysem.
"""
import sys,math,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v2_common import *
from mathutils.bvhtree import BVHTree
assert bpy.context.scene.get('art_revision')=='v2-F3-P2-ready-10'
sc=bpy.context.scene;verts=[];faces=[]
for name in ['Ciało / MakeHuman / UV natywne','koszula','kaftan','plaszcz']:
    o=bpy.data.objects[name];bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();offset=len(verts);verts.extend(ev.matrix_world@v.co for v in me.vertices);faces.extend(tuple(i+offset for i in p.vertices) for p in me.polygons);ev.to_mesh_clear()
tree=BVHTree.FromPolygons(verts,faces);o=bpy.data.objects['peleryna'];nu=57;nv=19
cloak=bpy.data.objects['plaszcz'];bpy.context.view_layer.update();ev=cloak.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();cloak_tree=BVHTree.FromPolygons([v.co.copy() for v in me.vertices],[tuple(p.vertices) for p in me.polygons]);ev.to_mesh_clear()
for v in o.data.vertices:
    j,i=divmod(v.index,nu);t=j/(nv-1);a=.86+.40*t+i/(nu-1)*(math.tau-2*(.86+.40*t));rx=.102+.143*math.sin(t*math.pi/2);ry=.125+.225*math.sin(t*math.pi/2);fold=.0055*math.sin(a*11+.4)*t
    x=(rx+fold)*math.cos(a);y=(ry+fold)*math.sin(a);z=1.584-.365*t+.009*t*math.sin(a*6+.2)
    hit=tree.ray_cast(Vector((x,y,2.05)),Vector((0,0,-1)),2.5)[0]
    if hit is not None and hit.z>1.20:z=max(z,hit.z+.017)
    if x<0 and z<1.50:
        hit=cloak_tree.ray_cast(Vector((-1,y,z)),Vector((1,0,0)),2)[0]
        if hit is not None and hit.x<0:x=min(x,hit.x-.014)
    v.co=(x,y,z)
o.data.update()
# Brzeg kaftana nie jest sztywną poziomą listwą.
vest=bpy.data.objects['kaftan']
for v in vest.data.vertices:
    if v.co.z<.93:
        fade=max(0,1-(v.co.z-.88)/.05);v.co.z+=fade*(.007*math.sin(v.co.y*63+.5)+.004*math.cos(v.co.y*89))
# Ponownie rozłóż tylko zmienioną pelerynę, potem przeskaluj ich unikatowe UV.
for o in [bpy.data.objects['peleryna'],vest]:
    active(o)
    if o.name=='peleryna':
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.unwrap(method='ANGLE_BASED',margin=.01);bpy.ops.object.mode_set(mode='OBJECT')
    uv=o.data.uv_layers.active;area3=sum(p.area for p in o.data.polygons);area2=0
    for p in o.data.polygons:
        q=[uv.data[i].uv for i in p.loop_indices];area2+=abs(sum(q[i].x*q[(i+1)%len(q)].y-q[(i+1)%len(q)].x*q[i].y for i in range(len(q))))/2
    factor=min(math.sqrt(area3*.25/max(area2,1e-12)),.495/max(abs(c-.5) for u in uv.data for c in u.uv))
    for u in uv.data:u.uv=(u.uv-Vector((.5,.5)))*factor+Vector((.5,.5))
    o['texel_density_px_m']=2048*math.sqrt(area2*factor**2/area3)
sc['art_directed_mantle']='Cloth 16 klatek, następnie projekcja grawitacyjna na rzeczywiste koszula/kaftan/płaszcz i ręczne pole fałd; swobodny brzeg opuszczony do bicepsa, bez sztywnego skrzydła.'
save('v2-F3-soft-mantle-11')
