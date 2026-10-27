"""Rzeczywisty portret diagnostyczny źródła; nie zmienia kamery zapisanej w modelu."""
import bpy,sys,argparse
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE));from render_player import activate
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args(sys.argv[sys.argv.index('--')+1:]);args.output.mkdir(exist_ok=True,parents=True)
scene=bpy.context.scene;rig=activate('spoczynek');rig.rotation_euler.z=0;scene.frame_set(1)
for layer in scene.view_layers:layer.use=layer.name=='Bohater'
nodes,links=scene.node_tree.nodes,scene.node_tree.links;nodes.clear();r=nodes.new('CompositorNodeRLayers');r.layer='Bohater';c=nodes.new('CompositorNodeComposite');links.new(r.outputs['Image'],c.inputs[0])
scene.render.resolution_x=scene.render.resolution_y=768;scene.camera.data.ortho_scale=.48
for label,pos in [('front',(3,-1.4,2.05)),('side',(.3,-3,1.83))]:
 target=Vector((.01,0,1.65));scene.camera.location=pos;scene.camera.rotation_euler=(target-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(args.output/(label+'.png'));bpy.ops.render.render(write_still=True)
