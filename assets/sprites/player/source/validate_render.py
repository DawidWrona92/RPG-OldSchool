"""Sprawdź odtworzenie obrazu z .blend i widoczność miecza w 8 kierunkach.

blender -b assets/sprites/player/source/bohater.blend --python-exit-code 1 \
  --python assets/sprites/player/source/validate_render.py
"""
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'previews'
TMP=Path('/tmp/welesza-render-check');TMP.mkdir(exist_ok=True)
scene=bpy.context.scene;rig=bpy.data.objects['Bohater_RIG']
cape=bpy.data.objects['Krótki płaszcz / miękkie fałdy'].data.shape_keys
rig.animation_data.action=bpy.data.actions['spoczynek']
cape.animation_data_create();cape.animation_data.action=bpy.data.actions['spoczynek / płaszcz']
rig.rotation_euler.z=0;scene.frame_set(1)
for layer in scene.view_layers:layer.use=layer.name=='Bohater'
nodes,links=scene.node_tree.nodes,scene.node_tree.links;nodes.clear()
r=nodes.new('CompositorNodeRLayers');r.layer='Bohater'
c=nodes.new('CompositorNodeComposite');links.new(r.outputs['Image'],c.inputs[0])


def pixels(path):
    im=bpy.data.images.load(str(path),check_existing=False)
    a=np.array(im.pixels[:],dtype=np.float32)
    size=list(im.size);bpy.data.images.remove(im)
    return a,size


repro={'status':'not_run / weapon-only diagnostic'}
if '--weapon-only' not in sys.argv:
    scene.render.filepath=str(TMP/'reproduced.png')
    bpy.ops.render.render(write_still=True)
    expected,size=pixels(ROOT/'renders/spoczynek_0_00.png')
    actual,size2=pixels(TMP/'reproduced.png')
    assert size==size2==[384,384],(size,size2)
    diff=np.abs(expected-actual)
    assert diff.max()<.02 and diff.mean()<.0002,('Odtworzenie pikseli',float(diff.max()),float(diff.mean()))
    repro={'source':'source/bohater.blend','frame':'spoczynek_0_00.png',
           'identical_decoded_pixels':bool(np.array_equal(expected,actual)),
           'mean_decoded_rgba_error':float(diff.mean()),'max_decoded_rgba_error':float(diff.max())}

# Object Index tests actual occlusion by the clothed body, not the existence
# of the sword somewhere in the source scene.
for obj in bpy.data.objects:
    obj.pass_index=int(obj.name.startswith(('Miecz /','Szlif ostrza','Jelec','Rękojeść','Głowica miecza')))
scene.view_layers['Bohater'].use_pass_object_index=True
scene.view_layers['Bohater'].samples=1;scene.cycles.samples=1
scene.render.resolution_x=192;scene.render.resolution_y=192
nodes.clear();r=nodes.new('CompositorNodeRLayers');r.layer='Bohater'
mask=nodes.new('CompositorNodeIDMask');mask.index=1;mask.use_antialiasing=True
links.new(r.outputs['IndexOB'],mask.inputs[0])
c=nodes.new('CompositorNodeComposite');links.new(mask.outputs[0],c.inputs[0])
maskdir=OUT/'weapon_masks';maskdir.mkdir(exist_ok=True)
origin=world_to_camera_view(scene,scene.camera,Vector((0,0,0)))
anchor=[origin.x*192,(1-origin.y)*192]
assert abs(anchor[0]-96)<.01 and abs(anchor[1]-158.35382907248)<.01,anchor
visibility={'spoczynek':{},'chod':{}};orientation={}
for d,label in enumerate(['S','SW','W','NW','N','NE','E','SE']):
    rig.rotation_euler.z=-d*math.pi/4;bpy.context.view_layer.update()
    point=rig.matrix_world.to_3x3()@Vector((1,0,0))
    screen=world_to_camera_view(scene,scene.camera,point)
    delta=[(screen.x-origin.x)*192,-(screen.y-origin.y)*192]
    orientation[label]={'model_facing_world':list(point),'projected_ground_heading_px':delta}
    if label=='S':assert delta[1]>25 and abs(delta[0])<.01
    if label=='W':assert delta[0]<-55 and abs(delta[1])<.01
    if label=='N':assert delta[1]<-25 and abs(delta[0])<.01
    if label=='E':assert delta[0]>55 and abs(delta[1])<.01
    for anim,frames,step in [('spoczynek',[0],10),('chod',[0,4,8],2)]:
        for frame in frames:
            rig.animation_data.action=bpy.data.actions[anim]
            cape.animation_data.action=bpy.data.actions[anim+' / płaszcz']
            position=1+frame*step;scene.frame_set(math.floor(position),subframe=position%1)
            file=maskdir/(f'{anim}_{label}_{frame:02}.png')
            scene.render.filepath=str(file);bpy.ops.render.render(write_still=True)
            a,size=pixels(file)
            count=int(np.sum(a.reshape(-1,4)[:,0]>.5))
            assert count>=4,('Miecz niewidoczny',anim,label,frame,count)
            visibility[anim][label+'_'+str(frame)]=count
report={'reproduction':repro,'anchor_projection_px':anchor,'visible_sword_pixels_at_192px':visibility,
        'orientation':orientation,'tested_poses':'first idle frame and walk frames 0, 4, 8 in eight directions (32 masks)',
        'limits':['weapon masks do not prove absence of all garment collisions',
                  'all walk frames were visually reviewed on contact sheets, not motion-captured']}
(OUT/'render-validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('WELESZA_RENDER_VALIDATION',json.dumps(report))
