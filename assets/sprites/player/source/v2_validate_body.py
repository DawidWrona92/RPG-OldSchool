"""Odczyt F1: topologia, UV, 163 kości, wagi i sześć diagnostycznych póz."""
import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v2_common import *
import numpy as np
source=Path(bpy.data.filepath);before=sha(source);body=bpy.data.objects['Ciało / MakeHuman / UV natywne'];rig=bpy.data.objects['Bohater_RIG'];raw,uv,faces=read_obj()
uv_errors=[]
for p,f in zip(body.data.polygons,faces):
    assert list(p.vertices)==[q[0] for q in f]
    for li,q in zip(p.loop_indices,f):uv_errors.append(max(abs(body.data.uv_layers.active.data[li].uv[a]-uv[q[1]][a]) for a in range(2)))
assert len(body.data.vertices)==len(raw) and len(body.data.polygons)==len(faces)
assert max(uv_errors)<6e-8
sk=json.loads((THIRD/'default.mhskel').read_text());assert set(rig.data.bones.keys())==set(sk['bones']) and len(rig.data.bones)==163
ids=set(q[0] for f in faces for q in f);sums=[sum(g.weight for g in body.data.vertices[i].groups) for i in ids];assert min(sums)>.9999 and max(sums)<1.0001
for m in body.modifiers:
    if m.type=='SUBSURF':m.show_viewport=False
dg=bpy.context.evaluated_depsgraph_get();bpy.context.view_layer.update()
ev=body.evaluated_get(dg);me=ev.to_mesh();rest=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear()
poses=[('barki',{'upperarm01.L':(0,0,45),'upperarm01.R':(0,0,-45)}),('lokcie',{'lowerarm01.L':(65,0,0),'lowerarm01.R':(65,0,0)}),('nadgarstki',{'wrist.L':(25,0,15),'wrist.R':(-25,0,-15)}),('palce',{f'finger{i}-1.{s}':(35,0,0) for i in range(1,6) for s in ['L','R']}),('kolana',{'lowerleg01.L':(55,0,0),'lowerleg01.R':(55,0,0)}),('skret_przedramion',{'lowerarm02.L':(0,45,0),'lowerarm02.R':(0,-45,0)})]
out=ROOT/'handoff/p1';out.mkdir(parents=True,exist_ok=True);reports=[]
for label,values in poses:
    for p in rig.pose.bones:p.rotation_mode='XYZ';p.rotation_euler=(0,0,0)
    for name,angles in values.items():rig.pose.bones[name].rotation_euler=[math.radians(a) for a in angles]
    bpy.context.view_layer.update();ev=body.evaluated_get(dg);me=ev.to_mesh();co=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear()
    delta=np.linalg.norm(co-rest,axis=1);length_error=max(abs(p.length-p.bone.length) for p in rig.pose.bones)
    assert np.isfinite(co).all() and delta.max()>.002
    reports.append({'pose':label,'rotations_deg':values,'moved_vertices_over_1mm':int((delta>.001).sum()),'max_displacement_m':float(delta.max()),'max_bone_length_error_m':length_error,'automatic_scope':'finite coordinates, nonzero deformation, fixed bone lengths; no artistic acceptance'})
    np.save('/tmp/v2-pose-'+label+'.npy',co)
result={'source_blend_sha256':before,'native_uv_max_float_error':max(uv_errors),'vertices':len(raw),'body_faces':len(faces),'native_loop_count':len(uv_errors),'bone_count':163,'body_weight_sum_range':[min(sums),max(sums)],'poses':reports,'B1':'DO_OCENY_AUTORA; liczby nie dowodzą braku zapadnięć'}
(out/'body-validation.json').write_text(json.dumps(result,indent=2)+'\n');assert sha(source)==before
print(json.dumps(result,indent=2))
