"""Kandydat po pełnym teście: usuń zasłonięcie W4–7, bez powiększania broni."""
from pathlib import Path
import bpy,sys,json,hashlib
from mathutils import Vector
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE));import motion_player as motion
scene=bpy.context.scene;assert scene.get('art_revision')=='refinement-08-review'
rig=bpy.data.objects['Bohater_RIG'];wrist=rig.data.bones['hand.R'].head_local;old=Vector(scene['carry_axis']).normalized();axis=Vector((.55,-.55,-.63)).normalized();rot=old.rotation_difference(axis).to_matrix()
for obj in bpy.data.objects:
 if obj.type=='MESH' and obj.name.startswith(('Miecz /','Szlif ostrza','Jelec','Rękojeść','Głowica miecza','Palec zgięty','Prawa rękawica')):
  for v in obj.data.vertices:v.co=wrist+rot@(v.co-wrist)
  for a,v in zip(obj.data.attributes['rest_position'].data,obj.data.vertices):a.vector=v.co
motion.bind();motion.RIGHT_HAND_CARRY=(.07,-.48,1.07)
for anim,count,step in [('spoczynek',8,10),('chod',12,2)]:
 rig.animation_data.action=bpy.data.actions[anim]
 for obj in bpy.data.objects:
  if obj.type=='MESH' and obj.data.shape_keys:obj.data.shape_keys.animation_data.action=bpy.data.actions[anim+' / '+obj.name]
 for i in range(count+1):motion.set_pose(i/count,anim=='chod',frame=1+i*step)
 for action in bpy.data.actions:
  for c in action.fcurves:
   for k in c.keyframe_points:k.interpolation='LINEAR'
scene['art_revision']='refinement-09-carry-candidate';scene['carry_axis']=list(axis);scene['right_hand_carry']=[.07,-.48,1.07];scene.frame_set(1);bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath='/tmp/hero-carry-candidate.blend')
