"""Krawieckie szwy i unikatowe UV do P2; gęstość z powierzchni w metrach."""
import sys,math,json,bmesh
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v2_common import *
assert bpy.context.scene.get('art_revision')=='v2-F3-final-clearance-08'
# Pochwa ma otwarty wlot. Jelec spoczywa nad jego obrzeżem, nie w skórzanym denku.
o=bpy.data.objects['pochwa'];bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();v=bm.verts[-2];bmesh.ops.delete(bm,geom=list(v.link_faces),context='FACES');bm.to_mesh(o.data);bm.free()
axis=Vector((-.22,.05,-.67)).normalized()
for name in ['rekojesc','jelec','glowica']:
    for v in bpy.data.objects[name].data.vertices:v.co-=axis*.005
report=[]
for o in bpy.context.scene.objects:
    if not o.get('p2_part'):continue
    active(o)
    if o.name in ['koszula','spodnie','kaftan','plaszcz','peleryna','kaptur']:
        def label(p):
            if o.name=='koszula':return (2 if p.y>.18 else 3 if p.y<-.18 else 0 if p.x>.025 else 1)
            if o.name=='spodnie':return int(p.x>.015)+2*int(p.y>0)
            if o.name=='kaftan':return 0 if p.x>.025 else 1
            return 0
        for e in o.data.edges:e.use_seam=label(o.data.vertices[e.vertices[0]].co)!=label(o.data.vertices[e.vertices[1]].co)
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.unwrap(method='ANGLE_BASED',margin=.01);bpy.ops.object.mode_set(mode='OBJECT')
    uv=o.data.uv_layers.active;area3=sum(p.area for p in o.data.polygons);area2=0
    for p in o.data.polygons:
        pp=[uv.data[i].uv for i in p.loop_indices];area2+=abs(sum(pp[i].x*pp[(i+1)%len(pp)].y-pp[(i+1)%len(pp)].x*pp[i].y for i in range(len(pp))))/2
    desired=math.sqrt(area3*.25/max(area2,1e-12));max_delta=max(abs(c-.5) for u in uv.data for c in u.uv);factor=min(desired,.495/max(max_delta,1e-12))
    for u in uv.data:u.uv=(u.uv-Vector((.5,.5)))*factor+Vector((.5,.5))
    density=2048*math.sqrt(area2*factor**2/max(area3,1e-12));o['texture_resolution']=2048;o['texel_density_px_m']=density;o['uv_method']='Szwy części krawieckich + Angle Based dla ubrań/tkanin; Smart Project dla drobnego wyposażenia; średnia gęstość skalowana z pola powierzchni.'
    report.append({'part':o.name,'surface_area_m2':area3,'density_px_m':density,'resolution':2048,'seam_edges':sum(e.use_seam for e in o.data.edges)})
bpy.context.scene['p2_uv_report']=json.dumps(report)
skinmat=bpy.data.objects['Ciało / MakeHuman / UV natywne'].data.materials[0];skinmat.name='Skóra / GPT6 v3 / natywne UV'
bpy.data.orphans_purge(do_recursive=True)
save('v2-F3-P2-ready-09');print('V2_UV_FINAL',json.dumps(report),flush=True)
