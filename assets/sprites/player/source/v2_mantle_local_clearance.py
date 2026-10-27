"""Lokalne usunięcie resztkowych przecięć po wygładzeniu miękkiej peleryny."""
import sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v2_common import *
from mathutils.bvhtree import BVHTree
assert bpy.context.scene.get('art_revision')=='v2-F3-mantle-contact-14'
o=bpy.data.objects['peleryna'];coat=bpy.data.objects['plaszcz']
def evaluated(obj):
    bpy.context.view_layer.update();ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();vv=[ev.matrix_world@v.co for v in me.vertices];ff=[tuple(t.vertices) for t in me.loop_triangles];ev.to_mesh_clear();return vv,ff,BVHTree.FromPolygons(vv,ff,all_triangles=True)
cv,cf,ct=evaluated(coat)
solid=next(m for m in coat.modifiers if m.type=='SOLIDIFY');solid.show_viewport=False;_,_,surface=evaluated(coat);solid.show_viewport=True
for iteration in range(8):
    vv,ff,target=evaluated(o);pairs=target.overlap(ct);print('MANTLE_LOCAL_PAIRS',iteration,len(pairs),flush=True)
    if not pairs:break
    centers=[sum((vv[k] for k in ff[a]),Vector())/3 for a,b in pairs]
    for v in o.data.vertices:
        distance=min((v.co-p).length for p in centers)
        if distance<.045:
            near,n,_,_=surface.find_nearest(v.co);v.co+=n*(.009*(1-distance/.045))
    o.data.update()
uv=o.data.uv_layers.active;area3=sum(p.area for p in o.data.polygons);area2=0
for p in o.data.polygons:
    q=[uv.data[i].uv for i in p.loop_indices];area2+=abs(sum(q[i].x*q[(i+1)%len(q)].y-q[(i+1)%len(q)].x*q[i].y for i in range(len(q))))/2
factor=min(math.sqrt(area3*.25/max(area2,1e-12)),.495/max(abs(c-.5) for u in uv.data for c in u.uv))
for u in uv.data:u.uv=(u.uv-Vector((.5,.5)))*factor+Vector((.5,.5))
o['texel_density_px_m']=2048*math.sqrt(area2*factor*factor/area3);save('v2-F3-static-review-15')
