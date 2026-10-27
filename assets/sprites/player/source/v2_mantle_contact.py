"""Gęstsza powierzchnia peleryny z zachowaniem miękkiego obrysu i luzu nad płaszczem."""
import sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v2_common import *
from mathutils.bvhtree import BVHTree
assert bpy.context.scene.get('art_revision')=='v2-F3-mantle-clearance-13'
o=bpy.data.objects['peleryna'];active(o);sub=next(m for m in o.modifiers if m.type=='SUBSURF');bpy.ops.object.modifier_apply(modifier=sub.name)
coat=bpy.data.objects['plaszcz'];solid=next(m for m in coat.modifiers if m.type=='SOLIDIFY');solid.show_viewport=False;bpy.context.view_layer.update();ev=coat.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();tree=BVHTree.FromPolygons([v.co.copy() for v in me.vertices],[tuple(p.vertices) for p in me.polygons]);ev.to_mesh_clear();solid.show_viewport=True
count=0
for iteration in range(6):
    for v in o.data.vertices:
        p,n,_,distance=tree.find_nearest(v.co)
        if distance<.055 and (v.co-p).dot(n)<.022:
            v.co=p+n*.022;count+=1
o.data.update();sub=o.modifiers.new('Miękka powierzchnia po kontakcie','SUBSURF');sub.levels=1;sub.render_levels=1;active(o);bpy.ops.object.modifier_move_up(modifier=sub.name);bpy.ops.object.modifier_move_up(modifier=sub.name)
uv=o.data.uv_layers.active;area3=sum(p.area for p in o.data.polygons);area2=0
for p in o.data.polygons:
    q=[uv.data[i].uv for i in p.loop_indices];area2+=abs(sum(q[i].x*q[(i+1)%len(q)].y-q[(i+1)%len(q)].x*q[i].y for i in range(len(q))))/2
factor=min(math.sqrt(area3*.25/max(area2,1e-12)),.495/max(abs(c-.5) for u in uv.data for c in u.uv))
for u in uv.data:u.uv=(u.uv-Vector((.5,.5)))*factor+Vector((.5,.5))
o['texel_density_px_m']=2048*math.sqrt(area2*factor*factor/area3);o['contact_corrected_vertex_steps']=count;save('v2-F3-mantle-contact-14')
