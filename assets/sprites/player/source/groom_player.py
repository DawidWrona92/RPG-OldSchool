"""Korekta po uwagach autora: fryzura i zarost z planszy 17, koszula wpuszczona w spodnie.
Jawna edycja źródła, nie część eksportera. Zastępuje wyłącznie błędne włosy/zarost/oczy.
"""
import bpy,sys,math,random,json,hashlib
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE));import build_player as b
scene=bpy.context.scene;assert scene.get('art_revision')=='refinement-05-chunk03'
b.RIG=bpy.data.objects['Bohater_RIG'];b.REST={bone.name:(bone.head_local.copy(),bone.tail_local.copy()) for bone in b.RIG.data.bones};rng=random.Random(17027)
# Shirt belongs under the belt and trousers. The former long lower rings gave
# the light patch between the legs. Keep the existing upper shirt and sleeves.
shirt=bpy.data.objects['Lniana tunika / krój i pionowe fałdy']
for v in shirt.data.vertices:
 if v.co.z<1.06:
  v.co.z=1.045+(v.co.z-.78)*.05;v.co.x=.015+(v.co.x-.015)*.79;v.co.y*=.79
for a,v in zip(shirt.data.attributes['rest_position'].data,shirt.data.vertices):a.vector=v.co
# Keep the face anatomy. The old beard selected the nose-height region instead
# of the jaw: use actual facial landmarks from the pinned MakeHuman rig.
body=bpy.data.objects['Anatomiczna głowa, szyja i odkryte przedramiona'];body.data.update();skin=bpy.data.materials['Skóra podróżnika / Chunk03'];hair=bpy.data.materials['Włosy umbra / Chunk03']
verts=[v.co.copy() for v in body.data.vertices];faces=[tuple(p.vertices) for p in body.data.polygons]
weights=[{'head':1} for v in verts]
face=[v for v in verts if v.z>1.54 and v.x>.07]
def surface_x(y,z):
 closest=sorted(face,key=lambda v:(v.y-y)**2+(v.z-z)**2)[:4]
 ww=[1/(1e-6+(v.y-y)**2+(v.z-z)**2) for v in closest]
 return sum(v.x*w for v,w in zip(closest,ww))/sum(ww)
for obj in list(bpy.data.objects):
 if obj.type=='MESH' and obj.name.startswith(('Pasmo włosów','Włosy / boczne','Zarost /','Brew /','Powieka','Oko','Tęczówka')):bpy.data.objects.remove(obj,do_unlink=True)
# The old scalp remains as a root under the new overlapping, tapered locks.
scalp=bpy.data.objects['Włosy / krótki nieregularny obrys']
for v in scalp.data.vertices:v.co+=v.normal*.001
highlight=hair.copy();highlight.name='Włosy / delikatna jaśniejsza odmiana'
for n in highlight.node_tree.nodes:
 if n.type=='MIX_RGB':n.inputs[1].default_value=(.035,.024,.015,1)

def uv(obj):
 layer=obj.data.uv_layers.get('Materiał / metry') or obj.data.uv_layers.new(name='Materiał / metry')
 for p in obj.data.polygons:
  for idx in p.loop_indices:
   v=obj.data.vertices[obj.data.loops[idx].vertex_index].co;layer.data[idx].uv=(math.atan2(v.y,v.x-.04)/math.tau,v.z/.30)

def lock(name,points,widths,mat):
 points=[Vector(p) for p in points];vertices=[];sides=8
 for i,p in enumerate(points):
  tangent=(points[min(i+1,len(points)-1)]-points[max(0,i-1)]).normalized();normal=(p-Vector((.045,0,1.70))).normalized();normal=(normal-tangent*normal.dot(tangent)).normalized();across=tangent.cross(normal).normalized();w=widths[i]
  for k in range(sides):
   a=math.tau*k/sides;vertices.append(tuple(p+across*math.cos(a)*w+normal*math.sin(a)*w*.32))
 faces=[(i*sides+k,i*sides+(k+1)%sides,(i+1)*sides+(k+1)%sides,(i+1)*sides+k) for i in range(len(points)-1) for k in range(sides)];faces += [tuple(reversed(range(sides))),tuple((len(points)-1)*sides+k for k in range(sides))]
 obj=b.mesh(name,vertices,faces,mat,[{'head':1} for _ in vertices],1);uv(obj);return obj
# Uneven side-swept top, rather than round tubes embedded under a smooth cap.
for i in range(27):
 y=rng.uniform(-.063,.063);x=rng.uniform(.015,.105);sweep=rng.uniform(.008,.033);endz=rng.uniform(1.724,1.767)
 points=[(x,y,1.791-rng.uniform(0,.006)),(x+.015,y+sweep*.4,1.816+rng.uniform(-.004,.008)),(.137,y+sweep,1.785),(.165,y+sweep*.85,endz)]
 lock('Włosy / nieregularna grzywka',points,[.007,.014+rng.uniform(0,.005),.012,.0008],highlight if i%5==0 else hair)
# Side locks and nape reach the ears and neck, as on the concept sheet.
for sign in [-1,1]:
 for i in range(12):
  x=rng.uniform(-.015,.096);dy=rng.uniform(.071,.084);endz=rng.uniform(1.635,1.682)
  lock('Włosy / pasmo przy uchu',[(x,sign*dy,1.765),(x-.008,sign*(dy+.011),1.730),(x-.012,sign*(dy+.012),1.685),(x-.025,sign*(dy+.008),endz)],[.007,.012,.011,.0007],highlight if i%6==0 else hair)
 for i in range(7):
  y=sign*rng.uniform(.004,.065)
  lock('Włosy / postrzępiony kark',[(-.027,y,1.748),(-.057,y,1.705),(-.064,y+.004*sign,1.660),(-.060,y+.006*sign,rng.uniform(1.606,1.638))],[.006,.013,.010,.0006],hair)
# A short beard along jaw, cheek and chin. Nose and lips remain exposed.
beardmat=hair.copy();beardmat.name='Zarost / krótka broda z przejściem'
beard=b.subset('Zarost / policzki żuchwa i podbródek',verts,faces,weights,beardmat,
 lambda p,f:1.544<p[2]<1.625+.020*min(1,abs(p[1])/.075) and p[0]>.070 and not(abs(p[1])<.026 and 1.582<p[2]<1.612 and p[0]>.150),offset=.0012,sub=1)
uv(beard);density=beard.data.attributes.new('beard_density','FLOAT','POINT')
for a,v in zip(density.data,beard.data.vertices):
 top=1.625+.020*min(1,abs(v.co.y)/.075);fade=max(0,min(1,(top-v.co.z)/.010));a.value=fade*(.65+.23*rng.random())
n,l=beardmat.node_tree.nodes,beardmat.node_tree.links;out=next(n for n in n if n.type=='OUTPUT_MATERIAL');bs=out.inputs['Surface'].links[0].from_socket;attr=n.new('ShaderNodeAttribute');attr.attribute_name='beard_density';transparent=n.new('ShaderNodeBsdfTransparent');mix=n.new('ShaderNodeMixShader');l.new(attr.outputs['Fac'],mix.inputs[0]);l.new(transparent.outputs[0],mix.inputs[1]);l.new(bs,mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface'])
# Small tapered clumps soften the chin silhouette; no long fantasy beard.
candidates=[v for v in beard.data.vertices if v.co.z<1.595 and v.co.x>.10]
for i in range(min(85,len(candidates))):
 p=candidates[(i*13)%len(candidates)].co.copy();p.x+=.002
 lock('Zarost / krótkie pasmo', [tuple(p),tuple(p+Vector((.002,rng.uniform(-.001,.001),-.003))),tuple(p+Vector((.001,0,-rng.uniform(.005,.009))))],[.0012,.0016,.0001],hair)
# Mustache sits below the nose (1.639m) and above the upper lip (1.612m).
for sign in [-1,1]:
 for i in range(9):
  z=1.620+i*.0007;ys=[sign*.003,sign*.014,sign*.026]
  points=[(surface_x(y,z-dz)+.0018,y,z-dz) for y,dz in zip(ys,[0,.001,.006])]
  lock('Zarost / wąs',points,[.0018,.0022,.00025],hair)
 # Eyebrows follow the actual brow surface, not the old recessed coordinates.
 points=[(surface_x(sign*y,z)+.002,sign*y,z) for y,z in [(.018,1.695),(.035,1.698),(.053,1.689)]]
 lock('Brew / łuk nad okiem',points,[.0017,.0038,.0010],hair)
# Fill actual eye sockets with physically sized globes and subdued irises.
eye=b.material('Oko / ciepła kość słoniowa',(.30,.28,.235),'skin');eye.node_tree.nodes.get('Principled BSDF').inputs['Subsurface Weight'].default_value=0
dark=b.material('Tęczówka / ciemny brąz',(.035,.023,.012),'hair')
for sign in [-1,1]:
 obj=b.pillow('Oko',(.149,sign*.03325,1.66957),(.028,.028,.028),eye,'head');uv(obj)
 obj=b.pillow('Tęczówka',(.1632,sign*.03325,1.66957),(.0025,.010,.010),dark,'head');uv(obj)
# Update rest coordinates for the scalp correction; keep all animation data.
for a,v in zip(scalp.data.attributes['rest_position'].data,scalp.data.vertices):a.vector=v.co
scene['art_revision']='refinement-06-groom-shirt';scene['groom_note']='messy medium hair, ear/nape locks, short beard and mustache; fixed eye sockets; shirt tucked under belt'
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'bohater.blend'))
p=HERE/'art-source.json';data=json.loads(p.read_text());data.update(art_revision=scene['art_revision'],source_sha256=hashlib.sha256((HERE/'bohater.blend').read_bytes()).hexdigest(),groom_recipe='groom_player.py',shirt_note='lower linen tucked inside belt/trousers; removed light crotch patch');p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');print('GROOM_SAVED',data['source_sha256'])
