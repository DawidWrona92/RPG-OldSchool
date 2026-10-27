"""Poprawa kołnierza i pasa po lokalizacji ostatnich kolizji, bez wyjątków stroju."""
import sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v2_common import *
from mathutils.bvhtree import BVHTree
assert bpy.context.scene.get('art_revision')=='v2-F3-armholes-07'
for v in bpy.data.objects['peleryna'].data.vertices:v.co.z+=.019*max(0,min(1,(v.co.z-1.52)/.045))
vest=bpy.data.objects['kaftan'];bpy.context.view_layer.update();ev=vest.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();tree=BVHTree.FromPolygons([v.co.copy() for v in me.vertices],[tuple(p.vertices) for p in me.polygons]);ev.to_mesh_clear()
for name in ['pas_gorny','pas_dolny']:
    o=bpy.data.objects[name]
    for v in o.data.vertices:
        if v.co.x<0:
            hit=tree.ray_cast(Vector((-1,v.co.y,v.co.z)),Vector((1,0,0)),2)[0]
            if hit is not None and hit.x<0:v.co.x=min(v.co.x,hit.x-.012)
for name in ['rzemien_1','rzemien_2']:
    o=bpy.data.objects[name]
    for v in o.data.vertices:
        j=v.index//3;w=max(0,min(1,(j/40-.85)/.15));v.co.z+=.019*w
save('v2-F3-final-clearance-08')
