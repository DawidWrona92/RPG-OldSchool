"""Sześć statycznych prób deformacji; nic nie zapisuje do modelu ani akcji."""
import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v2_common import *
import numpy as np
sc=bpy.context.scene;source=Path(bpy.data.filepath);source_sha=sha(source);rig=bpy.data.objects['Bohater_RIG'];body=bpy.data.objects['Ciało / MakeHuman / UV natywne'];out=ROOT/'handoff/p1/poses';out.mkdir(parents=True,exist_ok=True)
for o in sc.objects:
    if o.type in ['MESH','CURVE','CURVES']:o.hide_render=o!=body
sc.view_layers['Cień'].use=False;sc.node_tree.nodes['Oddzielny cień'].mute=True;sc.render.resolution_x=sc.render.resolution_y=512;sc.cycles.samples=64
mat=plain('P1 deformacje / szary',(.3,.3,.3),.75);body.data.materials.clear();body.data.materials.append(mat)
def reset():
    for p in rig.pose.bones:p.matrix_basis=Matrix.Identity(4)
    bpy.context.view_layer.update()
def world_rotate(name,axis,angle):
    p=rig.pose.bones[name];matrix=p.matrix.copy();p.matrix=Matrix.Translation(matrix.translation)@Matrix.Rotation(math.radians(angle),4,axis)@Matrix.Translation(-matrix.translation)@matrix;bpy.context.view_layer.update()
reset();base=np.array([v.co[:] for v in body.data.vertices]);reports=[]
poses=[('01_barki',[('upperarm01.L','X',45),('upperarm01.R','X',-45)],'spine01',1.5),('02_lokcie',[('lowerarm01.L','Y',-75),('lowerarm01.R','Y',-75)],'lowerarm01.L',.8),('03_nadgarstki',[('wrist.L','Y',-35)],'wrist.L',.30),('04_palce',[(f'finger{i}-{j}.L','LOCAL_X',35 if j==1 else 20) for i in range(1,6) for j in range(1,4)],'wrist.L',.30),('05_kolana',[('lowerleg01.L','Y',65),('lowerleg01.R','Y',35)],'lowerleg01.L',1.2),('06_skret_przedramienia',[('lowerarm02.L','LOCAL_Y',60)],'lowerarm01.L',.7)]
for label,rotations,focus,scale in poses:
    reset()
    for name,axis,angle in rotations:
        if axis.startswith('LOCAL_'):
            p=rig.pose.bones[name];p.rotation_mode='XYZ';p.rotation_euler['XYZ'.index(axis[-1])]=math.radians(angle);bpy.context.view_layer.update()
        else:world_rotate(name,axis,angle)
    pb=rig.pose.bones[focus];target=(pb.head+pb.tail)*.5
    if focus=='wrist.L':target=pb.tail+Vector((0,0,-.04))
    cam=sc.camera;cam.location=target+Vector((4,2,1.5));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;sc.render.filepath=str(out/(label+'.png'));bpy.ops.render.render(write_still=True)
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();finite=all(math.isfinite(c) for v in me.vertices for c in v.co);evaluated_count=len(me.vertices);ev.to_mesh_clear()
    reports.append({'pose':label,'rotations':rotations,'image':label+'.png','image_sha256':sha(out/(label+'.png')),'finite_coordinates':finite,'evaluated_vertices':evaluated_count,'max_bone_length_error_m':max(abs(p.length-p.bone.length) for p in rig.pose.bones)})
(out/'manifest.json').write_text(json.dumps({'source_blend_sha256':source_sha,'renderer_sha256':sha(__file__),'status':'DO_OCENY_B1','poses':reports,'scope':'Sześć osobnych póz diagnostycznych i obrazy do oceny zapadnięć; nie animacja, nie pełne QA deformacji.'},ensure_ascii=False,indent=2)+'\n');assert sha(source)==source_sha
