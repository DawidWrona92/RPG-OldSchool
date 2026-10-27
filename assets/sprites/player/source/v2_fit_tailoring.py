"""Ostatnie luzy konstrukcyjne kaftana i zapięć, według miejsc przecięć."""
import sys,math,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v2_common import *
from mathutils.bvhtree import BVHTree
assert bpy.context.scene.get('art_revision')=='v2-F3-clearance-05'
def interp(z,points):
    for (a,b),(c,d) in zip(points,points[1:]):
        if z<=c:return b+(d-b)*max(0,min(1,(z-a)/(c-a)))
    return points[-1][1]
vest=bpy.data.objects['kaftan'];nu=96;nv=43
for v in vest.data.vertices:
    j,i=divmod(v.index,nu);z=.88+j/(nv-1)*.61;a=math.tau*i/nu;c=math.cos(a);ry=interp(z,[(.88,.235),(1.0,.235),(1.1,.225),(1.2,.217),(1.3,.222),(1.49,.20)]);rx=.205-.04*max(0,(z-1.38)/.11) if c>=0 else .16;fold=.002*math.sin(a*11+z*5);v.co=((rx+fold)*math.copysign(abs(c)**(.4 if c>=0 else .8),c),ry*math.sin(a),z)
vest.data.update()
for name in ['pas_gorny','pas_dolny']:
    for v in bpy.data.objects[name].data.vertices:v.co.y*=.240/.210
mantle=bpy.data.objects['peleryna']
for v in mantle.data.vertices:
    w=max(0,min(1,(1.55-v.co.z)/.04));v.co.x*=1+.03*w;v.co.y*=1+.025*w
bpy.context.view_layer.update();solids=[m for m in vest.modifiers if m.type=='SOLIDIFY']
for m in solids:m.show_viewport=False
bpy.context.view_layer.update();ev=vest.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();tree=BVHTree.FromPolygons([v.co.copy() for v in me.vertices],[tuple(p.vertices) for p in me.polygons]);ev.to_mesh_clear()
for m in solids:m.show_viewport=True
for k,sgn in enumerate([1,-1]):
    o=bpy.data.objects['rzemien_'+str(k+1)]
    for j in range(41):
        t=j/40;y=sgn*(.175-.33*t);z=1.425-.285*t
        for i,f in enumerate([-.5,0,.5]):
            yy=y+f*.022;zz=z-f*sgn*.026;hit=tree.ray_cast(Vector((1,yy,zz)),Vector((-1,0,0)),2)[0];xx=(hit.x if hit is not None and hit.x>.09 else .19)+.010+k*.009;o.data.vertices[j*3+i].co=(xx,yy,zz)
    o.data.update()
save('v2-F3-tailoring-06')
