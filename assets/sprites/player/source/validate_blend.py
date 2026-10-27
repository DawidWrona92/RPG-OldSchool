"""Sprawdź zapisany szkielet i rzeczywiste klucze animacji, bez renderowania.

blender -b assets/sprites/player/source/bohater.blend --python-exit-code 1 \
  --python assets/sprites/player/source/validate_blend.py
"""
import importlib.util
import json
import math
from pathlib import Path

import bpy

HERE=Path(__file__).resolve().parent
import sys
sys.path.insert(0,str(HERE))
import motion_player as module
module.bind()
rig=module.RIG;cape=module.CAPE.data.shape_keys;scene=bpy.context.scene
rig.animation_data.action=None;cape.animation_data_clear()
max_gap=0;max_length=0;max_target=0;poses=0
for walking in [False,True]:
    for i in range(121):
        phase=i/120
        info=module.set_pose(phase,walking)
        max_gap=max(max_gap,info['max_joint_gap_m'])
        max_length=max(max_length,info['max_bone_length_error_m'])
        for side in ['L','R']:
            target,_=module.foot_target(phase,side,walking)
            error=(rig.pose.bones['foot.'+side].head-target).length
            max_target=max(max_target,error)
            assert error<.00001,(phase,side,error)
        poses+=1
    module.set_pose(0,walking)
    first={b.name:b.matrix.copy() for b in rig.pose.bones}
    module.set_pose(1,walking)
    loop_error=max(abs(first[b.name][r][c]-b.matrix[r][c]) for b in rig.pose.bones for r in range(4) for c in range(4))
    assert loop_error<.00001,('Szew pętli',walking,loop_error)

# The animation actions must reproduce the same poses at the actual export
# times; a .blend containing only an unanimated rig would fail here.
action_error=0;keys_checked=0
for anim,count,step in [('spoczynek',8,10),('chod',12,2)]:
    for i in range(count+1):
        rig.animation_data.action=bpy.data.actions[anim]
        cape.animation_data_create();cape.animation_data.action=bpy.data.actions[anim+' / Krótki płaszcz / miękkie fałdy']
        frame=1+i*step;scene.frame_set(math.floor(frame),subframe=frame%1)
        actual={b.name:b.matrix.copy() for b in rig.pose.bones}
        rig.animation_data.action=None;cape.animation_data.action=None
        module.set_pose(i/count,anim=='chod')
        error=max(abs(actual[b.name][r][c]-b.matrix[r][c]) for b in rig.pose.bones for r in range(4) for c in range(4))
        action_error=max(action_error,error)
        assert error<.00002,('Akcja różni się od renderowanych póz',anim,i,error)
        keys_checked+=1
report={'sampled_poses':poses,'keyed_poses_checked':keys_checked,'bones':len(rig.pose.bones),
        'max_joint_gap_m':max_gap,'max_bone_length_error_m':max_length,
        'max_actual_foot_target_error_m':max_target,'max_action_matrix_error':action_error,
        'loop_seams':'passed / idle and walk','action_timing':'25 fps / idle 400 ms / walk 80 ms'}
path=HERE.parent/'previews/blend-validation.json';path.write_text(json.dumps(report,indent=2)+'\n')
print('WELESZA_BLEND_VALIDATION',json.dumps(report))
