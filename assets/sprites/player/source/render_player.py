"""Read-only renderer of authoritative .blend. Never builds meshes or saves source.

blender -b source/bohater.blend -t 4 --python-exit-code 1 --python source/render_player.py -- --all
"""
import argparse,hashlib,json,math,sys
from pathlib import Path
import bpy
from mathutils import Vector,Matrix
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
DIRS=['S','SW','W','NW','N','NE','E','SE']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def activate(anim):
 rig=bpy.data.objects['Bohater_RIG'];rig.animation_data_create();rig.animation_data.action=bpy.data.actions[anim]
 for obj in bpy.data.objects:
  if obj.type=='MESH' and obj.data.shape_keys:
   keys=obj.data.shape_keys;keys.animation_data_create()
   action=bpy.data.actions.get(anim+' / '+obj.name) or bpy.data.actions.get(anim+' / płaszcz')
   keys.animation_data.action=action
 return rig

def audit_pose(phase,walking):
 rig=bpy.data.objects['Bohater_RIG'];gaps=[];errors=[];feet={}
 for side in ['L','R']:
  for child,parent in [('forearm','upper_arm'),('hand','forearm'),('shin','thigh'),('foot','shin')]:gaps.append((rig.pose.bones[child+'.'+side].head-rig.pose.bones[parent+'.'+side].tail).length)
  p=(phase+(0 if side=='L' else .5))%1
  foot=rig.pose.bones['foot.'+side];rest=rig.data.bones['foot.'+side];deform=foot.matrix@rest.matrix_local.inverted()
  # Actual transformed sole landmarks, not an ideal ankle-only trajectory.
  points=[deform@Vector((x,rest.head_local.y,0)) for x in [-.054,.168]]
  feet[side]={'ankle_m':list(foot.head),'stance':bool(walking and p<.6),'plant_reference_m':(.26-.52*p/.6) if walking and p<.6 else None,'sole_heel_toe_m':[list(v) for v in points]}
 for bone in rig.pose.bones:errors.append(abs((bone.tail-bone.head).length-bone.bone.length))
 return {'max_joint_gap_m':max(gaps),'max_bone_length_error_m':max(errors),'feet':feet}

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--all',action='store_true');parser.add_argument('--pilot',action='store_true');parser.add_argument('--directions',nargs='+',type=int,choices=range(8));parser.add_argument('--animations',nargs='+',choices=['spoczynek','chod']);parser.add_argument('--resume',action='store_true');parser.add_argument('--lighting',choices=['base','cool','warm'],default='base');parser.add_argument('--output',type=Path);parser.add_argument('--size',type=int,default=384);parser.add_argument('--samples',type=int,default=64);parser.add_argument('--sheathed',action='store_true');parser.add_argument('--portrait',action='store_true')
 args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
 source=Path(bpy.data.filepath);assert source.is_file(),'Open the saved artistic .blend first'
 source_sha=sha(source);scene=bpy.context.scene;rig=bpy.data.objects['Bohater_RIG']
 out=(args.output or ROOT/'renders').resolve()
 if not args.output and args.lighting!='base':out=out/args.lighting
 if args.sheathed:out=out/'sheathed'
 out.mkdir(exist_ok=True,parents=True);shadow_dir=out/'shadows';shadow_dir.mkdir(exist_ok=True)
 scene.render.resolution_x=scene.render.resolution_y=args.size;scene.cycles.samples=args.samples;scene.render.threads_mode='FIXED';scene.render.threads=4
 shadow=scene.node_tree.nodes['Oddzielny cień'];shadow.base_path=str(shadow_dir)
 if args.lighting=='cool':bpy.data.lights['Chłodne niebo / klucz z lewej'].color=(.63,.78,1)
 if args.lighting=='warm':
  data=bpy.data.lights.new('Próba lokalnej pochodni','POINT');data.energy=85;data.color=(1,.33,.075);data.shadow_soft_size=.15
  lamp=bpy.data.objects.new(data.name,data);scene.collection.objects.link(lamp);lamp.location=(1.2,-1,1.75)
 if args.portrait:
  # A genuine larger source render. Same orthographic scale, camera/light/exposure.
  args.size=1152;scene.render.resolution_x=scene.render.resolution_y=1152
 if args.sheathed:
  # Same sword geometry, rebind at the existing scabbard mouth; hide blade
  # inside the sheath and unfold the gloved fingers. This is a review option.
  wrist=rig.data.bones['hand.R'].head_local
  axis=Vector(scene.get('carry_axis',[.08,-.62,-.78])).normalized();down=Vector((-.146,.048,-.705)).normalized();mouth=Vector((.026,.227,1.045));guard=wrist+axis*.079+axis*0 # grip offset handled by blade vertex origin below
  blade=bpy.data.objects['Miecz / głownia z grzbietem'];root=sum((v.co for v in list(blade.data.vertices)[:4]),Vector())/4
  rot=axis.rotation_difference(down).to_matrix()
  for obj in bpy.data.objects:
   if obj.type!='MESH':continue
   if obj.name.startswith(('Miecz /','Szlif ostrza','Jelec','Rękojeść','Głowica miecza')):
    for v in obj.data.vertices:v.co=mouth+rot@(v.co-root)
    obj.vertex_groups.clear();group=obj.vertex_groups.new(name='pelvis');group.add(list(range(len(obj.data.vertices))),1,'REPLACE')
   if obj.name.startswith('Palec zgięty'):obj.hide_render=True
  # Leave the same gloved hand relaxed; no gameplay policy baked into source.
 audit={'directions':DIRS,'anchor_px':[96,158.35382907247958],'source_blend_sha256':source_sha,'renderer_sha256':sha(Path(__file__)),'art_revision':scene.get('art_revision','baseline'),'render':{'blender':bpy.app.version_string,'engine':'CYCLES','samples':args.samples,'shadow_samples':16,'size_px':args.size,'seed':1703,'denoising':False,'threads':4,'lighting':args.lighting,'sheathed':args.sheathed},'frames':{}}
 if args.resume and (out/'motion_audit.json').exists():
  cached=json.loads((out/'motion_audit.json').read_text())
  for key in ['source_blend_sha256','renderer_sha256','render']:assert cached.get(key)==audit[key],f'Cache differs: {key}. Render without --resume.'
  audit=cached
 targets=[('spoczynek',1,10)] if args.pilot else [('spoczynek',8,10),('chod',12,2)]
 if args.animations:targets=[t for t in targets if t[0] in args.animations]
 for anim,count,step in targets:
  activate(anim)
  for d in (args.directions if args.directions is not None else range(8)):
   rig.rotation_euler.z=-d*math.pi/4
   for i in range(count):
    # Pilot is first frame, not a retimed one-frame action.
    scene.frame_set(1+i*step);bpy.context.view_layer.update();phase=i/(8 if anim=='spoczynek' else 12)
    file=out/f'{anim}_{d}_{i:02}.png';cast=shadow_dir/file.name;old=audit['frames'].get(file.name,{})
    if args.resume and file.exists() and cast.exists() and old.get('image_sha256')==sha(file) and old.get('shadow_sha256')==sha(cast):print('WELESZA_REUSE',file.name,flush=True);continue
    info=audit_pose(phase,anim=='chod');scene.render.filepath=str(file);shadow.file_slots[0].path=file.stem+'_'
    bpy.ops.render.render(write_still=True)
    generated=shadow_dir/(file.stem+'_'+format(scene.frame_current,'04d')+'.png');generated.replace(cast)
    info.update(phase=phase,image_sha256=sha(file),shadow_sha256=sha(cast));audit['frames'][file.name]=info
    temporary=out/'motion_audit.json.tmp';temporary.write_text(json.dumps(audit,indent=2)+'\n');temporary.replace(out/'motion_audit.json')
    print('WELESZA_FRAME',file.name,flush=True)
 assert sha(source)==source_sha,'Source changed while rendering'
 print('WELESZA_DONE_READ_ONLY_SOURCE',source_sha,flush=True)
if __name__=='__main__':main()
