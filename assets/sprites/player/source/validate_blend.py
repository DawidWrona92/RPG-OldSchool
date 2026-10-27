"""Walidacja rzeczywistych zapisanych akcji; nie odtwarza proceduralnej pozy.
Ręczne poprawki kluczy są źródłem nadrzędnym, tak samo jak poprawki siatki.
"""
import bpy,json,math,sys,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE));from render_player import activate
scene=bpy.context.scene;rig=bpy.data.objects['Bohater_RIG']
# Bone checks do not need mesh deformation; collision validator checks meshes separately.
for obj in bpy.data.objects:
 if obj.type=='MESH':obj.hide_viewport=True
maxgap=0;maxlength=0;loopmax=0;poses=0;keys=0;actions={}
for anim,count,step,end in [('spoczynek',8,10,81),('chod',12,2,25)]:
 activate(anim);action=rig.animation_data.action
 assert tuple(action.frame_range)==(1.,float(end)),(anim,list(action.frame_range))
 keyframes={round(k.co.x,6) for curve in action.fcurves for k in curve.keyframe_points}
 assert {float(1+i*step) for i in range(count+1)}<=keyframes,('Missing export keys',anim)
 actions[anim]={'range':list(action.frame_range),'curves':len(action.fcurves),'export_keys':count+1};keys+=count+1
 for i in range(121):
  frame=1+(end-1)*i/120;scene.frame_set(math.floor(frame),subframe=frame%1);bpy.context.view_layer.update()
  for side in ['L','R']:
   for child,parent in [('forearm','upper_arm'),('hand','forearm'),('shin','thigh'),('foot','shin')]:
    gap=(rig.pose.bones[child+'.'+side].head-rig.pose.bones[parent+'.'+side].tail).length;maxgap=max(maxgap,gap)
  for bone in rig.pose.bones:maxlength=max(maxlength,abs((bone.tail-bone.head).length-bone.bone.length))
  poses+=1
 scene.frame_set(1);first={b.name:b.matrix.copy() for b in rig.pose.bones};scene.frame_set(end)
 error=max(abs(first[b.name][r][c]-b.matrix[r][c]) for b in rig.pose.bones for r in range(4) for c in range(4));loopmax=max(loopmax,error)
assert maxgap<.00002 and maxlength<.00002 and loopmax<.00002,(maxgap,maxlength,loopmax)
report={'source_blend_sha256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'sampled_saved_poses':poses,'export_keys_verified':keys,'bones':len(rig.pose.bones),'max_joint_gap_m':maxgap,'max_bone_length_error_m':maxlength,'max_loop_matrix_error':loopmax,'actions':actions,'scope':'saved bone actions; no comparison to regenerated poses; geometry disabled only in this bone validator','action_timing':'25 fps / idle 400 ms / walk 80 ms'}
(HERE.parent/'previews/blend-validation.json').write_text(json.dumps(report,indent=2)+'\n');print('WELESZA_BLEND_VALIDATION',json.dumps(report))
