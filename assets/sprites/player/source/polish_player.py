"""Jawny drugi pass: tłumienie plam bazy tkaniny, płaski szlif stali, dokładny pivot stopy.
Działa na zapisanym modelu; nigdy nie jest wołany przez eksport.
"""
from pathlib import Path
import bpy,sys,json,hashlib
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import motion_player as motion
scene=bpy.context.scene
assert scene.get('art_revision')=='refinement-01','Pass wymaga konkretnego poprzedniego źródła'
for mat in bpy.data.materials:
 if not mat.use_nodes or not mat.get('texture_set'):continue
 stem=mat['texture_set'];nodes=mat.node_tree.nodes;links=mat.node_tree.links
 bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
 mul=next(n for n in nodes if n.type=='MIX_RGB' and n.blend_type=='MULTIPLY')
 dirt=next(n for n in nodes if n.type=='MIX_RGB' and n.blend_type=='MIX')
 mix=nodes.new('ShaderNodeMixRGB');mix.name='Kontrola makrokontrastu tekstury'
 if stem=='wool_cloak_dark_brown':strength=.22;color=(.064,.042,.026,1)
 elif 'leather' in stem:strength=.48;color=(.098,.055,.028,1) if 'vest' in stem else (.065,.040,.023,1)
 elif 'trousers' in stem:strength=.50;color=(.052,.049,.039,1)
 else:strength=.78;color=(.28,.235,.167,1)
 mix.inputs[0].default_value=strength;mix.inputs[1].default_value=color
 links.new(mul.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],dirt.inputs[1])
 mat['texture_color_strength']=strength
blade=bpy.data.objects['Miecz / głownia z grzbietem']
for poly in blade.data.polygons:poly.use_smooth=False
bevel=blade.modifiers.new('Szlif / fizyczna faza 0.8 mm','BEVEL');bevel.width=.0008;bevel.segments=2
# Existing metal material is also used by buckles; isolate the sword finish.
mat=blade.data.materials[0].copy();mat.name='Stal głowni / szeroki matowy szlif';blade.data.materials[0]=mat
bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.43;bs.inputs['Metallic'].default_value=.78
for node in mat.node_tree.nodes:
 if node.type=='VALTORGB':
  node.color_ramp.elements[0].color=(.28,.30,.31,1);node.color_ramp.elements[1].color=(.40,.42,.43,1)
# Re-bake the existing actions after a 1mm rest-ankle / sole-pivot correction.
motion.bind()
for anim,count,step in [('spoczynek',8,10),('chod',12,2)]:
 bpy.data.objects['Bohater_RIG'].animation_data.action=bpy.data.actions[anim]
 for obj in bpy.data.objects:
  if obj.type=='MESH' and obj.data.shape_keys:obj.data.shape_keys.animation_data.action=bpy.data.actions[anim+' / '+obj.name]
 for i in range(count+1):motion.set_pose(i/count,anim=='chod',frame=1+i*step)
 for action in bpy.data.actions:
  for curve in action.fcurves:
   for key in curve.keyframe_points:key.interpolation='LINEAR'
scene['art_revision']='refinement-02';scene.frame_set(1)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'bohater.blend'))
p=HERE/'art-source.json';data=json.loads(p.read_text());data['source_sha256']=hashlib.sha256((HERE/'bohater.blend').read_bytes()).hexdigest();data['art_revision']=scene['art_revision'];data['polish_recipe']='polish_player.py';p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
