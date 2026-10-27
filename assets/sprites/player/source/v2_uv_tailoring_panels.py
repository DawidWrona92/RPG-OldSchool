"""Szwy leżą na GRANICACH paneli, nie na poprzecznych krawędziach przecinających granicę."""
import sys,math,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v2_common import *
assert bpy.context.scene.get('art_revision')=='v2-F3-P2-ready-09'
report=[]
for name in ['koszula','spodnie','kaftan']:
    o=bpy.data.objects[name];active(o)
    def label(p):
        if name=='koszula':return (2+int(p.x>.025) if p.y>.18 else 4+int(p.x>.025) if p.y<-.18 else int(p.x>.025))
        if name=='spodnie':return int(p.x>.015)+2*int(p.y>0)
        return int(p.x>.025)
    labels=[label(p.center) for p in o.data.polygons];edges={tuple(sorted(e.vertices)):e.index for e in o.data.edges};adj=[[] for e in o.data.edges]
    for p in o.data.polygons:
        for pair in p.edge_keys:adj[edges[tuple(sorted(pair))]].append(p.index)
    for e,faces in zip(o.data.edges,adj):e.use_seam=len(faces)==2 and labels[faces[0]]!=labels[faces[1]]
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.unwrap(method='ANGLE_BASED',margin=.01);bpy.ops.object.mode_set(mode='OBJECT')
    uv=o.data.uv_layers.active;area3=sum(p.area for p in o.data.polygons);area2=0
    for p in o.data.polygons:
        q=[uv.data[i].uv for i in p.loop_indices];area2+=abs(sum(q[i].x*q[(i+1)%len(q)].y-q[(i+1)%len(q)].x*q[i].y for i in range(len(q))))/2
    factor=min(math.sqrt(area3*.25/max(area2,1e-12)),.495/max(abs(c-.5) for u in uv.data for c in u.uv))
    for u in uv.data:u.uv=(u.uv-Vector((.5,.5)))*factor+Vector((.5,.5))
    o['texel_density_px_m']=2048*math.sqrt(area2*factor*factor/area3);o['uv_method']='Angle Based; ciągłe szwy wzdłuż granic paneli krawieckich, 6 regionów koszuli, 4 nogawek, przód/tył kaftana.';report.append({'part':name,'seam_edges':sum(e.use_seam for e in o.data.edges),'density_px_m':o['texel_density_px_m']})
bpy.context.scene['uv_tailoring_panels']=json.dumps(report);save('v2-F3-P2-ready-10')
