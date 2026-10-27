"""Luz bocznych brzegów miękkiej peleryny, plecaka i kołnierza po audycie."""
import sys,math,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v2_common import *
from mathutils.bvhtree import BVHTree
assert bpy.context.scene.get('art_revision')=='v2-F3-settled-mantle-12'
coat=bpy.data.objects['plaszcz'];bpy.context.view_layer.update();ev=coat.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();tree=BVHTree.FromPolygons([v.co.copy() for v in me.vertices],[tuple(p.vertices) for p in me.polygons]);ev.to_mesh_clear()
o=bpy.data.objects['peleryna']
for v in o.data.vertices:
    p=v.co;sign=1 if p.y>=0 else -1
    if abs(p.y)>.24 and p.z<1.53:
        hit=tree.ray_cast(Vector((p.x,sign*1,min(p.z,1.462))),Vector((0,-sign,0)),2)[0]
        if hit is not None and hit.y*sign>0:p.y=sign*max(abs(p.y),abs(hit.y)+.024)
    if p.z>1.53:p.z+=.008*math.exp(-(p.x/.03)**2)*math.exp(-((abs(p.y)-.14)/.035)**2)
for name in ['plecak','poslanie','manierka']:
    for v in bpy.data.objects[name].data.vertices:v.co.x-=.032
for v in bpy.data.objects['sprzaczki'].data.vertices:
    if v.co.x<0:v.co.x-=.032
o.data.update();active(o);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.unwrap(method='ANGLE_BASED',margin=.01);bpy.ops.object.mode_set(mode='OBJECT')
uv=o.data.uv_layers.active;area3=sum(p.area for p in o.data.polygons);area2=0
for p in o.data.polygons:
    q=[uv.data[i].uv for i in p.loop_indices];area2+=abs(sum(q[i].x*q[(i+1)%len(q)].y-q[(i+1)%len(q)].x*q[i].y for i in range(len(q))))/2
factor=min(math.sqrt(area3*.25/max(area2,1e-12)),.495/max(abs(c-.5) for u in uv.data for c in u.uv))
for u in uv.data:u.uv=(u.uv-Vector((.5,.5)))*factor+Vector((.5,.5))
o['texel_density_px_m']=2048*math.sqrt(area2*factor*factor/area3);save('v2-F3-mantle-clearance-13')
