"""Pass detali do oceny statycznej. Kontynuuje model08, nie przebudowuje postaci.
Zapisuje osobne, edytowalne źródło bohater_detale.blend; eksport08 pozostaje odzyskiwalny.
"""
import bpy,sys,math,random,json,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE));import build_player as b
from render_player import activate
scene=bpy.context.scene;assert scene.get('art_revision')=='refinement-08-review';DEST=HERE/'bohater_detale.blend'
if DEST.exists():raise RuntimeError('Wersja robocza istnieje; nie nadpisuję poprawek artystycznych.')
parent_sha=hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest();rig=activate('spoczynek');rig.rotation_euler.z=0;scene.frame_set(1);b.RIG=rig
cape=bpy.data.objects['Krótki płaszcz / miękkie fałdy'];rng=random.Random(3849)

def weights(obj,index):return {obj.vertex_groups[g.group].name:g.weight for g in obj.data.vertices[index].groups}
def mesh_uv(obj):
 uv=obj.data.uv_layers.get('Materiał / metry') or obj.data.uv_layers.new(name='Materiał / metry')
 for p in obj.data.polygons:
  for i in p.loop_indices:
   v=obj.data.vertices[obj.data.loops[i].vertex_index].co;uv.data[i].uv=(math.atan2(v.y,v.x-.015)/math.tau*4,v.z/.32)
 for name in ['edge_mask','wear_mask']:
  attr=obj.data.attributes.get(name) or obj.data.attributes.new(name,'FLOAT','POINT')
  for a in attr.data:a.value=.16 if name=='edge_mask' else 0
 return obj
# Length follows the new full-body reference; anatomy, camera and scale do not change.
def cape_warp(p,index=None):
 oldz=p.z;t=max(0,min(1,(1.1-oldz)/.48));theta=math.atan2(p.y,p.x+.025)
 if theta<0:theta+=math.tau
 if oldz<1.1:p.z=1.1+(oldz-1.1)*1.55;p.x=-.025+(p.x+.025)*(1+.09*t);p.y*=1+.10*t
 if index is None:hem=max(0,min(1,(.81-oldz)/.18))**4
 else:hem=(max(0,index//65-19)/5)**4
 damage=sum(depth*math.exp(-((theta-math.radians(angle))/.085)**2) for angle,depth in [(112,.067),(167,.048),(238,.076),(278,.040)])
 rag=.017*math.sin(theta*17+.8)+.010*math.sin(theta*31-.4)
 p.z+=(damage+rag)*hem
 return p
for key in cape.data.shape_keys.key_blocks:
 for i,v in enumerate(key.data):v.co=cape_warp(v.co.copy(),i)
for v,base in zip(cape.data.vertices,cape.data.shape_keys.key_blocks[0].data):v.co=base.co
cape.data.update()
for a,v in zip(cape.data.attributes['rest_position'].data,cape.data.vertices):a.vector=v.co
# Recreate edge cords from the edited cloth, so the former short edge cannot protrude.
for obj in list(bpy.data.objects):
 if obj.name.startswith('Płaszcz / boczny szew'):bpy.data.objects.remove(obj,do_unlink=True)
kd=KDTree(len(cape.data.vertices))
for v in cape.data.vertices:kd.insert(v.co,v.index)
kd.balance()
def cape_keys(obj):
 obj.shape_key_add(name='Spoczynek')
 nearest=[kd.find(v.co)[1] for v in obj.data.vertices]
 for sourcekey in list(cape.data.shape_keys.key_blocks)[1:]:
  key=obj.shape_key_add(name=sourcekey.name);key.slider_min=-1
  for point,base,idx in zip(key.data,obj.data.vertices,nearest):point.co=base.co+sourcekey.data[idx].co-cape.data.shape_keys.key_blocks[0].data[idx].co
 for anim in ['spoczynek','chod']:
  action=bpy.data.actions[anim+' / '+cape.name].copy();action.name=anim+' / '+obj.name;action.use_fake_user=True
 obj.data.shape_keys.animation_data_create();obj.data.shape_keys.animation_data.action=bpy.data.actions['spoczynek / '+obj.name]
 return obj
wool=bpy.data.materials['Mokry płaszcz / ciemnobrązowa wełna'];thread=bpy.data.materials['Konopna nić'];leather=bpy.data.materials['Skóra / kaftan i sakwa']
for side in [0,64]:
 pts=[tuple(cape.data.vertices[j*65+side].co) for j in range(25)]
 obj=b.tube('Płaszcz / miękki zużyty brzeg',pts,.0015,wool,lambda p:weights(cape,kd.find(Vector(p))[1]),6);mesh_uv(obj);cape_keys(obj)
# Two true, non-destructive holes in the lower cloth, before its thickness modifier.
group=cape.vertex_groups.new(name='Uszkodzenia / otwory dolnej połaci');group.add([22*65+23,21*65+44,23*65+34],1,'REPLACE')
mask=cape.modifiers.new('Podróż / rzeczywiste rozdarcia tkaniny','MASK');mask.vertex_group=group.name;mask.invert_vertex_group=True;mask.threshold=.72;mask.use_smooth=True
# Keep solidification after the cut, including real thickness around holes.
index=list(cape.modifiers).index(mask)
while index>0 and cape.modifiers[index-1].type=='SOLIDIFY':
 bpy.context.view_layer.objects.active=cape;bpy.ops.object.modifier_move_up(modifier=mask.name);index-=1
# Irregular hanging tabs and individual frays; same armature and cloth keys.
verts=[];faces=[];ws=[]
for i in [2,7,12,17,21,27,32,38,43,49,55,60,63]:
 p=cape.data.vertices[24*65+i].co.copy();n=Vector((p.x+.025,p.y,0)).normalized();across=Vector((-n.y,n.x,0));width=rng.uniform(.006,.013);length=rng.uniform(.012,.038);start=len(verts)
 for q in [p-across*width,p+across*width,p+across*width*.25+Vector((.003,0,-length)),p-across*width*.4+Vector((-.002,.002,-length*.8))]:verts.append(tuple(q));ws.append(weights(cape,24*65+i))
 faces.append(tuple(start+k for k in range(4)))
obj=b.mesh('Płaszcz / nieregularne strzępki brzegu',verts,faces,wool,ws,1,.0018);mesh_uv(obj);cape_keys(obj)
for i in rng.sample(range(3,62),18):
 p=cape.data.vertices[24*65+i].co.copy();q=p+Vector((rng.uniform(-.006,.006),rng.uniform(-.006,.006),-rng.uniform(.007,.020)))
 obj=b.tube('Płaszcz / luźne włókno', [tuple(p),tuple((p+q)/2+Vector((.001,0,0))),tuple(q)], [.00065,.00055,.00015],thread,lambda p:weights(cape,kd.find(Vector(p))[1]),4);mesh_uv(obj);cape_keys(obj)
# A repaired lower-back panel. It copies actual cloth geometry, weights and motion.
ids=[j*65+i for j in range(18,21) for i in range(26,33)];lookup={idx:k for k,idx in enumerate(ids)}
vv=[tuple(cape.data.vertices[i].co+cape.data.vertices[i].normal*.003) for i in ids];ff=[(lookup[j*65+i],lookup[j*65+i+1],lookup[(j+1)*65+i+1],lookup[(j+1)*65+i]) for j in range(18,20) for i in range(26,32)]
patchmat=wool.copy();patchmat.name='Łata płaszcza / brunatna naprawiana wełna'
for n in patchmat.node_tree.nodes:
 if n.name=='Kontrola makrokontrastu tekstury':n.inputs[1].default_value=(.087,.061,.036,1)
patch=b.mesh('Płaszcz / naszyta łata',vv,ff,patchmat,[weights(cape,i) for i in ids],1,.0015);mesh_uv(patch);cape_keys(patch)
# Individually placed stitch loops, not a trim repeated over the garment.
for edge in [list(range(7)),list(range(14,21)),[0,7,14],[6,13,20]]:
 for a,c in zip(edge,edge[1:]):
  p=Vector(vv[a]);q=Vector(vv[c]);mid=(p+q)/2;n=Vector((mid.x+.025,mid.y,0)).normalized();along=(q-p).normalized();side=n.cross(along).normalized()
  for t in [.25,.7]:
   center=p.lerp(q,t)+n*.002
   obj=b.tube('Łata płaszcza / fastryga',[tuple(center-side*.003),tuple(center+n*.001),tuple(center+side*.003)],.0007,thread,lambda p:weights(cape,kd.find(Vector(p))[1]),4);mesh_uv(obj);cape_keys(obj)
# Two leather lower panels overlap trousers instead of ending at the belt.
for sign in [-1,1]:
 vv=[];steps=19;rings=[(1.075,.154,.195),(1.04,.159,.201),(.985,.176,.218),(.935,.182,.228)]
 for j,(z,rx,ry) in enumerate(rings):
  gap=math.radians(10+12*j/3)
  for k in range(steps):
   a=gap+(math.radians(92)-gap)*k/(steps-1);hem=(.008*math.sin(a*9)+.005*math.sin(a*17))*(j/3)**4
   vv.append((.016+rx*math.cos(a),sign*ry*math.sin(a),z+hem+(.009 if sign<0 else 0)*(j/3)))
 ff=[(j*steps+k,j*steps+k+1,(j+1)*steps+k+1,(j+1)*steps+k) for j in range(3) for k in range(steps-1)]
 obj=b.mesh('Kaftan / dolna poła zachodząca na spodnie',vv,ff,leather,[b.torso_weight(p) for p in vv],2,.004);mesh_uv(obj)
 pts=[tuple(Vector(v)+Vector((.002,0,0))) for v in vv[-steps:]]
 obj=b.tube('Kaftan / zużyte obszycie dołu',pts,.0015,bpy.data.materials['Przetarte brzegi skóry'],b.torso_weight,6);mesh_uv(obj)
# The belt must sit OUTSIDE the added waist panels.
belt=bpy.data.objects['Pas skórzany']
for v in belt.data.vertices:
 a=math.atan2(v.co.y,v.co.x);v.co.x=.016+.180*math.cos(a);v.co.y=.216*math.sin(a)
for a,v in zip(belt.data.attributes['rest_position'].data,belt.data.vertices):a.vector=v.co
for name in ['Sprzączka pasa','Język sprzączki']:
 for v in bpy.data.objects[name].data.vertices:v.co.x+=.039
# A controlled linen hem at the hips: raised at front center, never a bright crotch block.
vv=[];n=97
for j in range(4):
 t=j/3
 for i in range(n):
  a=math.tau*i/(n-1);z=1.02*(1-t)+(.875+.060*max(0,math.cos(a))**8+.010*math.sin(a*17)+.006*math.sin(a*29))*t
  vv.append((.015+(.171+.003*t)*math.cos(a),(.209+.003*t)*math.sin(a),z))
ff=[(j*n+i,j*n+i+1,(j+1)*n+i+1,(j+1)*n+i) for j in range(3) for i in range(n-1)]
obj=b.mesh('Koszula / nierówny lniany brzeg pod kaftanem',vv,ff,bpy.data.materials['Znoszony len'],[b.torso_weight(p) for p in vv],1,.002);mesh_uv(obj)
# A soft, sewn knee patch with transferred trouser weights.
pants=bpy.data.objects['Spodnie / marszczenia kolan'];pkd=KDTree(len(pants.data.vertices))
for v in pants.data.vertices:pkd.insert((0,v.co.y,v.co.z),v.index)
pkd.balance()
def front(y,z):
 choices=[(v.co.y-y)**2+(v.co.z-z)**2 for v in pants.data.vertices if v.co.x>0]
 candidates=sorted([v for v in pants.data.vertices if v.co.x>0],key=lambda v:(v.co.y-y)**2+(v.co.z-z)**2)[:4]
 w=[1/(1e-6+(v.co.y-y)**2+(v.co.z-z)**2) for v in candidates];return sum(v.co.x*t for v,t in zip(candidates,w))/sum(w)
vv=[];pw=[]
for j in range(7):
 for i in range(6):
  y=.125+(i/5-.5)*.080;z=.49+(j/6-.5)*.105+.003*math.sin(i*1.7);p=Vector((front(y,z)+.004,y,z));vv.append(tuple(p));pw.append(weights(pants,pkd.find((0,y,z))[1]))
ff=[(j*6+i,j*6+i+1,(j+1)*6+i+1,(j+1)*6+i) for j in range(6) for i in range(5)]
mat=pants.data.materials[0].copy();mat.name='Łata kolana / zszarzała brunatna wełna'
for node in mat.node_tree.nodes:
 if node.name=='Kontrola makrokontrastu tekstury':node.inputs[1].default_value=(.090,.075,.052,1)
obj=b.mesh('Spodnie / miękka naszywana łata kolana',vv,ff,mat,pw,1,.0016);mesh_uv(obj)
for edge in [list(range(6)),list(range(36,42)),list(range(0,42,6)),list(range(5,42,6))]:
 for a,c in zip(edge,edge[1:]):
  p=Vector(vv[a]);q=Vector(vv[c]);mid=p.lerp(q,.5)+Vector((.002,0,0));direction=(q-p).normalized();side=Vector((1,0,0)).cross(direction).normalized()
  obj=b.tube('Łata kolana / ręczny ścieg',[tuple(mid-side*.003),tuple(mid+Vector((.001,0,0))),tuple(mid+side*.003)],.0007,thread,lambda p:weights(pants,pkd.find((0,p[1],p[2]))[1]),4);mesh_uv(obj)
# Knee wear is tied to front pressure zones, not random noise across the body.
attr=pants.data.attributes['edge_mask']
for a,v in zip(attr.data,pants.data.vertices):a.value=max(a.value,.22*math.exp(-((v.co.z-.48)/.10)**2)*max(0,min(1,(v.co.x-.03)/.07)))
scene['art_revision']='detail-render-01-clothing';scene['detail_parent_sha256']=parent_sha;scene['detail_status']='static review first; existing actions preserved, new cloth motion not accepted'
scene.frame_set(1);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(DEST))
(HERE/'bohater_detale.source.json').write_text(json.dumps({'source':'source/bohater_detale.blend','parent_source_sha256':parent_sha,'source_sha256':hashlib.sha256(DEST.read_bytes()).hexdigest(),'status':scene['detail_status'],'recipe':'detail_clothing.py','changes':['longer irregular cloak','actual cloak holes and frayed tabs','sewn cloak and knee patches','leather panels overlap trousers','controlled irregular linen hem']},ensure_ascii=False,indent=2)+'\n')
print('DETAIL_CLOTHING_SAVED')
