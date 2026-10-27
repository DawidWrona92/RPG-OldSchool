"""Jednorazowy, jawny pass artystyczny na zatwierdzonym .blend, bez odbudowy postaci.

Blender -b source/bohater.blend --python source/refine_player.py
Odmawia ponownego zastosowania. Dalsze ręczne poprawki zapisuj w bohater.blend;
render_player.py nigdy go nie zapisuje ani nie generuje geometrii.
"""
import hashlib,json,math,sys
from pathlib import Path
import bpy
from mathutils import Vector
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import build_player as b
import motion_player as motion
ROOT=HERE.parent;REPO=ROOT.parents[2];TEXTURES=REPO/'assets/textures/characters/hero'
scene=bpy.context.scene
if scene.get('art_revision'):raise RuntimeError('Pass już zastosowany; nie nadpisuję ręcznych poprawek.')
expected=json.loads((ROOT/'baseline/checkpoint.json').read_text())['source_sha256']
assert hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest()==expected,'Wymagany checkpoint a0a6c27'
b.RIG=bpy.data.objects['Bohater_RIG'];b.REST={bone.name:(bone.head_local.copy(),bone.tail_local.copy()) for bone in b.RIG.data.bones}
b.CAPE=bpy.data.objects['Krótki płaszcz / miękkie fałdy']
b.RIG.animation_data.action=None
for obj in bpy.data.objects:
 if obj.type=='MESH' and obj.data.shape_keys:obj.data.shape_keys.animation_data_clear()
for bone in b.RIG.pose.bones:bone.matrix_basis.identity()
b.RIG.rotation_euler.z=0

def edit(obj,fn):
 """Apply the same rest-space correction to basis and every existing shape."""
 if obj.data.shape_keys:
  for key in obj.data.shape_keys.key_blocks:
   for i,v in enumerate(key.data):v.co=fn(v.co.copy(),i)
 else:
  for i,v in enumerate(obj.data.vertices):v.co=fn(v.co.copy(),i)
 obj.data.update()
 attr=obj.data.attributes.get('rest_position')
 if attr:
  basis=obj.data.shape_keys.key_blocks[0].data if obj.data.shape_keys else obj.data.vertices
  for a,v in zip(attr.data,basis):a.vector=v.co

# Preserve the cloak topology and existing secondary keys. Break the regular
# pleats into long gravity folds, a diagonal tension fold and an asymmetric hem.
def cape_fold(p,i):
 j,k=divmod(i,65);t=j/24;theta=math.radians(65+230*k/64)
 old=(.016*math.sin(theta*6+t*3)+.007*math.sin(theta*13-t*5))*math.sin(math.pi*t/2)
 new=(.012*math.sin(theta*4.2+.9*t)+.008*math.sin(theta*8.6-1.7*t)+.005*math.sin(theta*13+3*t))*math.sin(math.pi*t/2)
 new+=.012*math.exp(-((theta-2.2-.5*t)/.24)**2)*math.sin(math.pi*t)
 p.x+=(new-old)*math.cos(theta);p.y+=(new-old)*math.sin(theta)
 oldhem=(.022*math.sin(theta*19)+.011*math.sin(theta*37))*t**9
 newhem=(.014*math.sin(theta*7+.4)+.006*math.sin(theta*23)+.007*math.sin(theta*3))*t**9
 p.z+=newhem-oldhem
 return p
edit(b.CAPE,cape_fold)
# Reduce the shirt bulk under the same leather panels; no change to anatomy.
obj=bpy.data.objects['Lniana tunika / krój i pionowe fałdy']
def tunic_fold(p,i):
 a=math.atan2(p.y,(p.x-.015)*1.25);z=p.z
 if z>1.05:p.x=.015+(p.x-.015)*.94;p.y*=.92
 t=max(0,min(1,(1.06-z)/.28))
 d=.008*math.sin(a*5+z*9)*t+.003*math.sin(a*11-z*15)
 p.x+=d*math.cos(a);p.y+=d*math.sin(a)
 p.z+=.009*math.sin(a*3+.8)*t**3
 return p
edit(obj,tunic_fold)
# Move the collar opening of the existing vest inward; retain its sewn pattern.
def vest_fit(p,i):
 j,k=divmod(i,49);z=p.z
 old=math.radians(10+max(0,(z-1.28)/.213)*50)
 new=math.radians(10+max(0,(z-1.28)/.213)*25)
 angle=old+(math.tau-2*old)*k/48
 target=new+(math.tau-2*new)*k/48
 p.x=.016+(p.x-.016)*math.cos(target)/math.cos(angle) if abs(math.cos(angle))>.0001 else p.x
 p.y=p.y*math.sin(target)/math.sin(angle) if abs(math.sin(angle))>.0001 else p.y
 return p
edit(bpy.data.objects['Kaftan / zszywane otwarte połacie'],vest_fit)
# Replace only the two border cords so they follow the adjusted edge.
for obj in list(bpy.data.objects):
 if obj.name.startswith('Kaftan / przetarty brzeg'):bpy.data.objects.remove(obj,do_unlink=True)
for sign in [-1,1]:
 pts=[]
 for z,rx,ry in [(1.055,.154,.192),(1.12,.159,.189),(1.24,.162,.196),(1.35,.146,.211),(1.435,.120,.221),(1.493,.079,.144)]:
  a=math.radians(10+max(0,(z-1.28)/.213)*25);pts.append((.021+rx*math.cos(a),sign*ry*math.sin(a),z))
 b.tube('Kaftan / przetarty brzeg',pts,.0026,bpy.data.materials['Przetarte brzegi skóry'],b.torso_weight)
# Broad compression folds, localized at elbows and knees rather than noisy pores.
for name in ['Lniana koszula / luźne rękawy','Spodnie / marszczenia kolan']:
 def fold(p,i,name=name):
  if name.startswith('Lniana'):
   mask=math.exp(-((p.z-1.23)/.085)**2);d=.009*mask*math.sin(p.z*79+abs(p.y)*12)
  else:
   mask=math.exp(-((p.z-.48)/.12)**2)+.5*math.exp(-((p.z-.31)/.065)**2)
   d=.007*mask*math.sin(p.z*88+abs(p.y)*18)
  p.x+=d;p.y+=d*.4*(1 if p.y>0 else -1);return p
 edit(bpy.data.objects[name],fold)

# Real sewn edges: dark understated piping, pack gusset and small side pockets.
leather=bpy.data.materials['Skóra / kaftan i sakwa'];edge=bpy.data.materials['Przetarte brzegi skóry'];wool=bpy.data.materials['Mokry płaszcz / ciemnobrązowa wełna']
for sign in [-1,1]:
 b.tube('Plecak / szew klinu',[(-.30,sign*.14,1.40),(-.336,sign*.153,1.33),(-.338,sign*.147,1.20),(-.29,sign*.12,1.125)],.0025,edge,b.bone_weight('chest'))
 b.pillow('Plecak / kieszeń boczna',(-.267,sign*.151,1.25),(.105,.065,.16),leather,'chest',roundness=.25)
 b.ribbon('Plecak / szelka połączona z korpusem',[(-.265,sign*.118,1.43),(-.12,sign*.19,1.51),(.035,sign*.217,1.49),(.122,sign*.19,1.41),(.165,sign*.155,1.27),(.155,sign*.135,1.16)],.023,leather,b.torso_weight)
 b.tube('Posłanie / brzeg płótna',[(-.246+.060*math.cos(a),sign*.195,1.498+.060*math.sin(a)) for a in [math.tau*i/48 for i in range(49)]],.0018,edge,b.bone_weight('chest'))
# Flatten the pack's inflated face, add a soft load crease to the flap.
for name in ['Plecak podróżny','Klapa plecaka']:
 def pack(p,i):
  if p.x<-.30:p.x+=.009*math.cos(p.y*17)*math.exp(-((p.z-1.28)/.15)**2)
  p.z+=.006*math.sin(p.y*15+.4);return p
 edit(bpy.data.objects[name],pack)
# Source-scale grooming, eyebrows/eyelids. No new facial rig claimed.
skin=bpy.data.materials['Skóra / zmęczona podróżą'];hair=bpy.data.materials['Ciemne włosy']
for sign in [-1,1]:
 b.tube('Brew / naturalny łuk',[(.127,sign*.018,1.690),(.138,sign*.034,1.695),(.123,sign*.053,1.686)],[.002,.0035,.0015],hair,b.bone_weight('head'))
 b.tube('Powieka górna',[(.137,sign*.020,1.673),(.146,sign*.033,1.676),(.132,sign*.046,1.672)],.0017,skin,b.bone_weight('head'))
 for i in range(11):
  y=sign*(.042+.003*i);z=1.770-i*.005
  b.tube('Włosy / boczne nieregularne pasmo',[(.015,y,z),(-.016,y+sign*.013,z-.014),(-.033,y+sign*.011,z-.052)],[.006,.008,.001],hair,b.bone_weight('head'),7)
# Keep the sword's length/width, rotate the existing weapon, fingers and glove
# together about the wrist into a relaxed down/out carry (a review proposal).
old=Vector((.92,-.01,-.392)).normalized();new=Vector((.35,-.52,-.78)).normalized()
rot=old.rotation_difference(new).to_matrix();wrist=b.REST['hand.R'][0]
weapon_prefix=('Miecz /','Szlif ostrza','Jelec','Rękojeść','Głowica miecza','Palec zgięty','Prawa rękawica')
for obj in bpy.data.objects:
 if obj.type=='MESH' and obj.name.startswith(weapon_prefix):edit(obj,lambda p,i:wrist+rot@(p-wrist))
# Wool thickness remains real; geometry above is edited in rest space.
for obj in bpy.data.objects:
 if obj.type=='MESH':
  for mod in obj.modifiers:
   if mod.type=='SOLIDIFY':mod.use_even_offset=True

# Stable UVs in rest space, per-face unwrap at the back seam. Metric repeat .32m.
# Cloth/boots: cylinders. Pack: face projection. Bedroll: cylinder along Y.
# Tangent normal maps are deliberately not combined with height: the latter
# tolerates these small nonuniform panels and does not depend on tangent handedness.
def uv_map(obj):
 uv=obj.data.uv_layers.get('Materiał / metry') or obj.data.uv_layers.new(name='Materiał / metry')
 pack=obj.name.startswith(('Plecak','Klapa'))
 roll=obj.name=='Zrolowane posłanie'
 for poly in obj.data.polygons:
  values=[]
  for idx in poly.vertices:
   p=obj.data.vertices[idx].co
   if roll:
    a=math.atan2(p.z-1.498,p.x+.246);u=a/math.tau;v=p.y/.32;circ=math.tau*.061/.32
   elif pack:
    u=p.y/.32;v=p.z/.32;circ=None
   else:
    cy=(.126 if p.y>0 else -.126) if obj.name.startswith(('Spodnie','But /','Podeszwa')) else 0
    a=math.atan2(p.y-cy,p.x);u=a/math.tau;v=p.z/.32;circ=math.tau*(.20 if obj.name.startswith(('Krótki','Naramienna','Lniana tunika','Kaftan')) else .065)/.32
   values.append([u,v,circ])
  if values[0][2] is not None and max(p[0] for p in values)-min(p[0] for p in values)>.5:
   for p in values:
    if p[0]<0:p[0]+=1
  for loop,p in zip(poly.loop_indices,values):uv.data[loop].uv=(p[0]*(p[2] or 1),p[1])
 obj['uv_mapping']='rest metric 0.32m / back seam cylinder; pack YZ; bedroll Y-axis'

MAP={
 'Znoszony len':('linen_shirt_worn',1.0,.88,.00032),
 'Mokry płaszcz / ciemnobrązowa wełna':('wool_cloak_dark_brown',.85,.91,.00050),
 'Przetarta warstwa naramienna':('wool_cloak_dark_brown',.96,.89,.00050),
 'Skóra / kaftan i sakwa':('leather_vest_weathered_brown',.85,.54,.00028),
 'Przetarte brzegi skóry':('leather_vest_weathered_brown',1.1,.67,.00028),
 'Skóra butów / wilgoć':('leather_boots_dark_mud',.9,.48,.00030),
 'Spodnie / brunatna wełna':('wool_trousers_charcoal',.87,.90,.00035)}
packmat=leather.copy();packmat.name='Plecak / postarzana skóra';MAP[packmat.name]=('leather_backpack_aged',.82,.62,.0003)
rollmat=bpy.data.materials['Znoszony len'].copy();rollmat.name='Posłanie / zszarzałe płótno';MAP[rollmat.name]=('canvas_bedroll_ashen',.91,.91,.00045)
for obj in bpy.data.objects:
 if obj.type!='MESH' or not obj.data.materials:continue
 if obj.name.startswith(('Plecak podróżny','Plecak / kieszeń','Klapa plecaka')):obj.data.materials[0]=packmat
 if obj.name=='Zrolowane posłanie':obj.data.materials[0]=rollmat
 uv_map(obj)
 # A vertex mask anchors dirt to plausible low/worn parts of THIS garment.
 attr=obj.data.attributes.get('wear_mask') or obj.data.attributes.new('wear_mask','FLOAT','POINT')
 for item,v in zip(attr.data,obj.data.vertices):
  p=v.co;noise=.72+.28*math.sin(p.x*43+p.y*27+p.z*31)
  low=0
  if obj.name.startswith(('But /','Podeszwa')):low=max(0,min(1,(.20-p.z)/.17))*.68
  elif obj.name.startswith('Spodnie'):low=max(0,min(1,(.49-p.z)/.25))*.42
  elif obj==b.CAPE:low=max(0,min(1,(.84-p.z)/.20))*.47
  item.value=low*noise
for name,(stem,tint,rough,depth) in MAP.items():
 mat=bpy.data.materials[name];mat.use_nodes=True;n,l=mat.node_tree.nodes,mat.node_tree.links;n.clear()
 out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled');l.new(bs.outputs[0],out.inputs['Surface'])
 bs.inputs['Roughness'].default_value=rough;bs.inputs['Specular IOR Level'].default_value=.23 if 'wool' in stem or 'linen' in stem or 'canvas' in stem else .32
 if 'wool' in stem or 'linen' in stem or 'canvas' in stem:bs.inputs['Sheen Weight'].default_value=.18
 uv=n.new('ShaderNodeUVMap');uv.uv_map='Materiał / metry'
 tex={}
 for channel in ['basecolor','roughness','height']:
  node=n.new('ShaderNodeTexImage');node.name=channel+' / '+stem;node.image=bpy.data.images.load(str(TEXTURES/f'{stem}_{channel}.png'),check_existing=True);node.image.colorspace_settings.name='sRGB' if channel=='basecolor' else 'Non-Color';node.interpolation='Linear';node.extension='REPEAT';l.new(uv.outputs[0],node.inputs['Vector']);node.image.pack();tex[channel]=node
 # Broad color grading is material-specific; exposure/key/camera stay identical.
 mul=n.new('ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=1;mul.inputs[2].default_value=(tint,tint*.98,tint*.94,1);l.new(tex['basecolor'].outputs['Color'],mul.inputs[1])
 wear=n.new('ShaderNodeAttribute');wear.attribute_name='wear_mask'
 dirt=n.new('ShaderNodeMixRGB');dirt.inputs[2].default_value=(.067,.052,.030,1);l.new(wear.outputs['Fac'],dirt.inputs[0]);l.new(mul.outputs[0],dirt.inputs[1]);l.new(dirt.outputs[0],bs.inputs['Base Color'])
 rr=n.new('ShaderNodeMapRange');rr.inputs['From Min'].default_value=0;rr.inputs['From Max'].default_value=1;rr.inputs['To Min'].default_value=max(.25,rough-.1);rr.inputs['To Max'].default_value=min(1,rough+.09);l.new(tex['roughness'].outputs[0],rr.inputs['Value']);l.new(rr.outputs[0],bs.inputs['Roughness'])
 bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.14;bump.inputs['Distance'].default_value=depth;l.new(tex['height'].outputs[0],bump.inputs['Height']);l.new(bump.outputs[0],bs.inputs['Normal'])
 mat['texture_set']=stem;mat['height_instead_of_normal']='No double bump; tangent normal maps preserved as supplied but unused'
# Tone down bright stitches, make edge bevels of steel catch the existing light.
for matname in ['Konopna nić']:
 mat=bpy.data.materials[matname]
 for node in mat.node_tree.nodes:
  if node.type=='VALTORGB':
   for e in node.color_ramp.elements:e.color=tuple(c*.55 for c in e.color[:3])+(1,)
for name in ['Kute żelazo','Szlifowane krawędzie']:
 mat=bpy.data.materials[name];bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.31 if name.startswith('Kute') else .25
# Secondary motion is a small deformation of the SAME edited mesh, not loose gear.
for name in ['Plecak podróżny','Klapa plecaka','Zrolowane posłanie','Naramienna warstwa płaszcza']:
 obj=bpy.data.objects[name];obj.shape_key_add(name='Basis');key=obj.shape_key_add(name='Bezwładność ładunku')
 for v,base in zip(key.data,obj.data.vertices):
  t=max(0,min(1,(1.55-base.co.z)/.45));v.co.x+=.004*t;v.co.z+=.003*t;v.co.y+=.003*t
# Bake edited idle/walk on the existing rig and every shape-keyed garment.
motion.bind()
for anim,count,step in [('spoczynek',8,10),('chod',12,2)]:
 old=bpy.data.actions.get(anim)
 if old:bpy.data.actions.remove(old)
 b.RIG.animation_data_create();b.RIG.animation_data.action=bpy.data.actions.new(anim);b.RIG.animation_data.action.use_fake_user=True
 for obj in bpy.data.objects:
  if obj.type=='MESH' and obj.data.shape_keys:
   keys=obj.data.shape_keys;keys.animation_data_create();old=bpy.data.actions.get(anim+' / '+obj.name)
   if old:bpy.data.actions.remove(old)
   keys.animation_data.action=bpy.data.actions.new(anim+' / '+obj.name);keys.animation_data.action.use_fake_user=True
 for i in range(count+1):motion.set_pose(i/count,anim=='chod',frame=1+i*step)
 for action in bpy.data.actions:
  for curve in action.fcurves:
   for key in curve.keyframe_points:key.interpolation='LINEAR'
# Discard archived empty cloak actions to keep the actual source unambiguous.
for name in ['spoczynek / płaszcz','chod / płaszcz']:
 if name in bpy.data.actions:bpy.data.actions.remove(bpy.data.actions[name])
scene['art_revision']='refinement-01';scene['baseline_commit']='a0a6c27e33b5d634e1ccad59e7634e4ab4d7ccde';scene['walk_speed_mps']=.52/(.6*.96)
scene['source_policy']='AUTHORITATIVE EDITABLE SOURCE; renderer never regenerates or saves this file'
scene['material_commits']='chunk01 7ce5c4b; chunk02 c6c1a67b11dfbb396920668ef7edc7ac3f1c95a3'
b.RIG.animation_data.action=bpy.data.actions['spoczynek']
for obj in bpy.data.objects:
 if obj.type=='MESH' and obj.data.shape_keys:obj.data.shape_keys.animation_data.action=bpy.data.actions['spoczynek / '+obj.name]
scene.frame_set(1);bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'bohater.blend'))
manifest={'baseline_commit':scene['baseline_commit'],'art_revision':scene['art_revision'],'authoritative_source':'source/bohater.blend','source_sha256':hashlib.sha256((HERE/'bohater.blend').read_bytes()).hexdigest(),'textures_packed':True,'materials':MAP,'texture_files_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in TEXTURES.glob('*.png')},'source_rule':'Do not run bootstrap over artistic source. Render reads saved actions only; edits to .blend are authoritative.'}
(HERE/'art-source.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print('WELESZA_ART_SOURCE_SAVED',manifest['source_sha256'])
