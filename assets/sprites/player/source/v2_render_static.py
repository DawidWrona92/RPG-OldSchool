"""Tylko odczyt źródła v2; statyka do bramek P1/B2, bez akcji i atlasów."""
import sys,math,argparse,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v2_common import *
from bpy_extras.object_utils import world_to_camera_view
ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--mode',choices=['p1','portrait','model','game'],default='game');ap.add_argument('--directions',nargs='+',type=int,default=list(range(8)));ap.add_argument('--samples',type=int,default=64);ap.add_argument('--size',type=int)
args=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source=Path(bpy.data.filepath);source_hash=sha(source);sc=bpy.context.scene;rig=bpy.data.objects['Bohater_RIG'];out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
sc.cycles.samples=args.samples;sc.cycles.seed=1703;sc.cycles.use_denoising=False;sc.render.threads=4;sc.render.threads_mode='FIXED';sc.frame_set(1)
shadow=sc.node_tree.nodes['Oddzielny cień'];shadow.base_path=str(out/'shadows');(out/'shadows').mkdir(exist_ok=True)
audit={'source_blend_sha256':source_hash,'renderer_sha256':sha(__file__),'mode':args.mode,'blender':bpy.app.version_string,'samples':args.samples,'shadow_samples':16,'frames':{},'note':'Statyczna bramka przed B2; bez animacji i bez atlasu.'}
body=bpy.data.objects['Ciało / MakeHuman / UV natywne'];cam=sc.camera
if args.mode=='p1':
    for o in sc.objects:
        if o.type in ['MESH','CURVES','CURVE'] and o!=body and not o.is_shadow_catcher:o.hide_render=True
    mat=plain('P1 / szablon UV / diagnostyka',(.4,.4,.4));n=mat.node_tree.nodes;l=mat.node_tree.links;b=n.get('Principled BSDF')
    checker=n.new('ShaderNodeTexChecker');checker.inputs['Scale'].default_value=32;checker.inputs['Color1'].default_value=(.07,.14,.2,1);checker.inputs['Color2'].default_value=(.46,.53,.5,1)
    tex=n.new('ShaderNodeTexCoord');l.new(tex.outputs['UV'],checker.inputs['Vector'])
    wire=n.new('ShaderNodeWireframe');wire.inputs['Size'].default_value=.0006;mix=n.new('ShaderNodeMixRGB');mix.inputs[2].default_value=(.8,.65,.22,1);l.new(wire.outputs[0],mix.inputs[0]);l.new(checker.outputs[0],mix.inputs[1]);l.new(mix.outputs[0],b.inputs['Base Color']);body.data.materials.clear();body.data.materials.append(mat)
if args.mode in ['p1','model']:
    sc.render.resolution_x=sc.render.resolution_y=args.size or 768
    cam.location=(6,0,.95);target=Vector((0,0,.95));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=2.15
    ds=[0,4,2] if args.mode=='model' else [0,2,1]
elif args.mode=='portrait':
    sc.render.resolution_x=sc.render.resolution_y=args.size or 768
    cam.location=(4,-.28,1.65);target=Vector((.025,0,1.64));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.49;ds=[0]
else:sc.render.resolution_x=sc.render.resolution_y=args.size or 384;ds=args.directions
for d in ds:
    rig.rotation_euler.z=-d*math.pi/4;bpy.context.view_layer.update();key=f'{args.mode}_{d}';file=out/(key+'.png');sc.render.filepath=str(file);shadow.file_slots[0].path=key+'_';bpy.ops.render.render(write_still=True)
    cast=out/'shadows'/(key+'_0001.png');renamed=out/'shadows'/(key+'.png');cast.replace(renamed)
    anchor=world_to_camera_view(sc,cam,Vector((0,0,0)));size=sc.render.resolution_x
    audit['frames'][file.name]={'image_sha256':sha(file),'shadow_sha256':sha(renamed),'direction_index':d,'anchor_px':[anchor.x*size,(1-anchor.y)*size],'size':size,'ortho_scale':cam.data.ortho_scale,'camera_location':list(cam.location),'camera_rotation':list(cam.rotation_euler)}
    (out/'audit.json').write_text(json.dumps(audit,indent=2)+'\n');print('V2_STATIC',key,flush=True)
assert sha(source)==source_hash
