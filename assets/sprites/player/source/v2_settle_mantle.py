"""Drapowanie końcowe: barki poniżej szyi, wolne zapięcie przodu, warstwa nad płaszczem."""
import sys,math,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v2_common import *
from mathutils.bvhtree import BVHTree
assert bpy.context.scene.get('art_revision')=='v2-F3-soft-mantle-11'
def tree(names):
    vv=[];ff=[]
    for name in names:
        obj=bpy.data.objects[name];bpy.context.view_layer.update();ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();offset=len(vv);vv.extend(ev.matrix_world@v.co for v in me.vertices);ff.extend(tuple(i+offset for i in p.vertices) for p in me.polygons);ev.to_mesh_clear()
    return BVHTree.FromPolygons(vv,ff)
support=tree(['Ciało / MakeHuman / UV natywne','koszula','kaftan','plaszcz']);coat=tree(['plaszcz']);o=bpy.data.objects['peleryna'];nu=57;nv=19
for v in o.data.vertices:
    j,i=divmod(v.index,nu);t=j/(nv-1);edge=.86+.66*t;a=edge+i/(nu-1)*(math.tau-2*edge);rx=.102+.143*math.sin(t*math.pi/2);ry=.125+.225*math.sin(t*math.pi/2);fold=.005*math.sin(a*11+.4)*t;x=(rx+fold)*math.cos(a);y=(ry+fold)*math.sin(a);z=1.584-.365*t+.008*t*math.sin(a*6+.2)
    hit=support.ray_cast(Vector((x,y,1.57)),Vector((0,0,-1)),2)[0]
    if hit is not None and hit.z>1.20:z=max(z,hit.z+.026)
    if x<0 and z<1.545:
        hit=coat.ray_cast(Vector((-1,y,min(z,1.462))),Vector((1,0,0)),2)[0]
        if hit is not None and hit.x<0:x=min(x,hit.x-.028)
    v.co=(x,y,z)
o.data.update();active(o);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.unwrap(method='ANGLE_BASED',margin=.01);bpy.ops.object.mode_set(mode='OBJECT')
uv=o.data.uv_layers.active;area3=sum(p.area for p in o.data.polygons);area2=0
for p in o.data.polygons:
    q=[uv.data[i].uv for i in p.loop_indices];area2+=abs(sum(q[i].x*q[(i+1)%len(q)].y-q[(i+1)%len(q)].x*q[i].y for i in range(len(q))))/2
factor=min(math.sqrt(area3*.25/max(area2,1e-12)),.495/max(abs(c-.5) for u in uv.data for c in u.uv))
for u in uv.data:u.uv=(u.uv-Vector((.5,.5)))*factor+Vector((.5,.5))
o['texel_density_px_m']=2048*math.sqrt(area2*factor*factor/area3);save('v2-F3-settled-mantle-12')
