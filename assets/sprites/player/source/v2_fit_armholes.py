"""Wykrój pach kaftana i dopasowanie paneli do rzeczywistej koszuli/spodni."""
import sys,math,json,bmesh
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v2_common import *
from mathutils.bvhtree import BVHTree
assert bpy.context.scene.get('art_revision')=='v2-F2-layered-groom-03'
def tree(o):
    bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();t=BVHTree.FromPolygons([v.co.copy() for v in me.vertices],[tuple(p.vertices) for p in me.polygons]);ev.to_mesh_clear();return t
shirt=tree(bpy.data.objects['koszula']);pants=tree(bpy.data.objects['spodnie']);vest=bpy.data.objects['kaftan'];bm=bmesh.new();bm.from_mesh(vest.data);bad=[f for f in bm.faces if f.calc_center_median().z>1.20 and abs(f.calc_center_median().y)>.16];bmesh.ops.delete(bm,geom=bad,context='FACES');bm.to_mesh(vest.data);bm.free()
for v in vest.data.vertices:
    for obstacle in [shirt,pants]:
        if v.co.x>0:
            hit=obstacle.ray_cast(Vector((1,v.co.y,v.co.z)),Vector((-1,0,0)),2)[0]
            if hit is not None and hit.x>.025:v.co.x=max(v.co.x,hit.x+.014)
        else:
            hit=obstacle.ray_cast(Vector((-1,v.co.y,v.co.z)),Vector((1,0,0)),2)[0]
            if hit is not None and hit.x<.025:v.co.x=min(v.co.x,hit.x-.014)
vest.data.update()
for k in range(2):
    o=bpy.data.objects['rzemien_'+str(k+1)]
    for v in o.data.vertices:v.co.x+=.009+k*.003
# Odsunięcie dolnej krawędzi peleryny od podwiniętych rękawów, bez wyjątku --allow.
mantle=bpy.data.objects['peleryna']
for v in mantle.data.vertices:
    if abs(v.co.y)>.20:v.co.y+=math.copysign(.006,v.co.y)
save('v2-F3-armholes-07')
