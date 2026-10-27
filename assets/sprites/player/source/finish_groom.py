"""Zamknij widoczne gładkie przejście nasady włosów drobnymi pasmami na skórze głowy."""
import bpy,sys,random,math,json,hashlib
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE));import build_player as b
scene=bpy.context.scene;assert scene.get('art_revision')=='refinement-07-fine-groom';b.RIG=bpy.data.objects['Bohater_RIG'];rng=random.Random(725)
scalp=bpy.data.objects['Włosy / krótki nieregularny obrys'];scalp.data.update();vertices=[];faces=[]
for i in range(1400):
 poly=rng.choice(list(scalp.data.polygons));vv=[scalp.data.vertices[k].co for k in poly.vertices];ww=[rng.random() for _ in vv];p=sum((v*w for v,w in zip(vv,ww)),Vector())/sum(ww);n=poly.normal.normalized();direction=Vector((.8,.24,-.24));direction=(direction-n*direction.dot(n)).normalized();length=rng.uniform(.015,.035);points=[p+n*.002,p+n*.004+direction*length*.50,p+n*.003+direction*length];start=len(vertices)
 for j,q in enumerate(points):
  axis=(points[min(j+1,2)]-points[max(0,j-1)]).normalized();a=axis.cross(n).normalized();c=axis.cross(a);r=.0003*(1-.9*j/2)
  for k in range(4):vertices.append(tuple(q+r*(math.cos(k*math.pi/2)*a+math.sin(k*math.pi/2)*c)))
 for j in range(2):
  for k in range(4):faces.append((start+j*4+k,start+j*4+(k+1)%4,start+(j+1)*4+(k+1)%4,start+(j+1)*4+k))
obj=b.mesh('Włosy / włókna nasady i skroni',vertices,faces,bpy.data.materials['Włosy umbra / Chunk03'],[{'head':1} for _ in vertices]);uv=obj.data.uv_layers.new(name='Materiał / metry')
for poly in obj.data.polygons:
 for idx in poly.loop_indices:
  v=obj.data.vertices[obj.data.loops[idx].vertex_index].co;uv.data[idx].uv=(math.atan2(v.y,v.x-.04)/math.tau,v.z/.3)
scene['art_revision']='refinement-08-review';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'bohater.blend'))
p=HERE/'art-source.json';data=json.loads(p.read_text());data.update(art_revision=scene['art_revision'],source_sha256=hashlib.sha256((HERE/'bohater.blend').read_bytes()).hexdigest(),finish_groom_recipe='finish_groom.py');p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
