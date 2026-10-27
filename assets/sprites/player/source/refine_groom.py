"""Dopracowanie zbliżenia: drobne pasma zamiast grubych płatów, oczy wewnątrz powiek."""
import bpy,sys,math,random,json,hashlib
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE));import build_player as b
scene=bpy.context.scene;assert scene.get('art_revision')=='refinement-06-groom-shirt';b.RIG=bpy.data.objects['Bohater_RIG'];rng=random.Random(18733)
# The first socket pilot overexposed the eyeball surface: retain anatomical
# center from MakeHuman and move the globes back behind the lid rim.
for obj in bpy.data.objects:
 if obj.type=='MESH' and obj.name.startswith(('Oko','Tęczówka')):
  for v in obj.data.vertices:v.co.x-=.013
  for a,v in zip(obj.data.attributes['rest_position'].data,obj.data.vertices):a.vector=v.co
hair=bpy.data.materials['Włosy umbra / Chunk03'];beardmat=hair.copy();beardmat.name='Zarost / drobne włókna brunatne'
for node in beardmat.node_tree.nodes:
 if node.type=='MIX_RGB':node.inputs[0].default_value=.25;node.inputs[1].default_value=(.047,.030,.019,1)
# Use the existing guide locks to build a dense, irregular set of fine strands.
vertices=[];faces=[];material_ids=[]
def strand(points,radius,matid=0):
 points=list(map(Vector,points));start=len(vertices);sides=4
 for j,p in enumerate(points):
  direction=(points[min(j+1,len(points)-1)]-points[max(0,j-1)]).normalized();t=direction.cross(Vector((1,0,0)))
  if t.length<.01:t=direction.cross(Vector((0,1,0)))
  t.normalize();u=direction.cross(t);r=radius*(1-.90*j/(len(points)-1))
  for i in range(sides):vertices.append(tuple(p+r*(math.cos(math.tau*i/sides)*t+math.sin(math.tau*i/sides)*u)))
 for j in range(len(points)-1):
  for i in range(sides):faces.append((start+j*sides+i,start+j*sides+(i+1)%sides,start+(j+1)*sides+(i+1)%sides,start+(j+1)*sides+i));material_ids.append(matid)
 guides=[]
for obj in list(bpy.data.objects):
 if obj.type!='MESH':continue
 if obj.name.startswith('Zarost / krótkie pasmo'):bpy.data.objects.remove(obj,do_unlink=True);continue
 if obj.name.startswith(('Włosy / nieregularna grzywka','Włosy / pasmo przy uchu','Włosy / postrzępiony kark','Zarost / wąs')):
  pts=[sum((v.co for v in list(obj.data.vertices)[i:i+8]),Vector())/8 for i in range(0,len(obj.data.vertices),8)]
  widths=[max((v.co-p).length for v in list(obj.data.vertices)[i*8:i*8+8]) for i,p in enumerate(pts)]
  count=45 if obj.name.startswith('Włosy') else 12
  for k in range(count):
   spread=rng.uniform(-.9,.9);path=[]
   for j,p in enumerate(pts):
    tangent=(pts[min(j+1,len(pts)-1)]-pts[max(0,j-1)]).normalized();normal=(p-Vector((.045,0,1.70))).normalized();across=tangent.cross(normal).normalized()
    q=p+across*widths[j]*spread+normal*rng.uniform(-.001,.0025)+Vector((rng.uniform(-.001,.001),rng.uniform(-.001,.001),rng.uniform(-.001,.001)))
    path.append(q)
   path[-1]+=Vector((rng.uniform(-.003,.003),rng.uniform(-.003,.003),rng.uniform(-.004,.003)))
   strand(path,rng.uniform(.00022,.00042),0 if obj.name.startswith('Włosy') else 1)
  # Coarse guides remain only as a narrow underlying mass, never a rubber slab.
  for j,p in enumerate(pts):
   for v in list(obj.data.vertices)[j*8:j*8+8]:v.co=p+(v.co-p)*.38
  for a,v in zip(obj.data.attributes['rest_position'].data,obj.data.vertices):a.vector=v.co
# Replace the painted beard opacity with sparse undercoat and fine surface hair.
beard=bpy.data.objects['Zarost / policzki żuchwa i podbródek'];attr=beard.data.attributes['beard_density']
for a in attr.data:a.value*=.46
polys=list(beard.data.polygons)
for i in range(1850):
 poly=polys[rng.randrange(len(polys))];vv=[beard.data.vertices[k].co for k in poly.vertices];p=sum((v*rng.random() for v in vv),Vector())/len(vv)
 # Barycentric convex sampling; avoid the earlier weighted sum shrinking positions.
 weights=[rng.random() for _ in vv];p=sum((v*w for v,w in zip(vv,weights)),Vector())/sum(weights)
 density=sum(attr.data[k].value for k in poly.vertices)/len(poly.vertices)
 if rng.random()>.3+density:continue
 normal=poly.normal.copy();p+=normal*.001
 length=rng.uniform(.0025,.0065) if p.z<1.595 else rng.uniform(.0015,.0038)
 strand([p,p+normal*.0015+Vector((0,0,-length*.45)),p+normal*.001+Vector((0,0,-length))],rng.uniform(.00013,.00024),1)
obj=b.mesh('Włókna fryzury i zarostu / głowa',vertices,faces,hair,[{'head':1} for _ in vertices]);obj.data.materials.append(beardmat)
for p,index in zip(obj.data.polygons,material_ids):p.material_index=index
uv=obj.data.uv_layers.new(name='Materiał / metry')
for p in obj.data.polygons:
 for idx in p.loop_indices:
  v=obj.data.vertices[obj.data.loops[idx].vertex_index].co;uv.data[idx].uv=(math.atan2(v.y,v.x-.04)/math.tau,v.z/.3)
scene['art_revision']='refinement-07-fine-groom';scene['groom_fiber_vertices']=len(vertices);bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'bohater.blend'))
p=HERE/'art-source.json';data=json.loads(p.read_text());data.update(art_revision=scene['art_revision'],source_sha256=hashlib.sha256((HERE/'bohater.blend').read_bytes()).hexdigest(),fine_groom_recipe='refine_groom.py');p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
