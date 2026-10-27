"""Dopracuj przejścia groomingu i osadzenie łaty po pierwszym renderze źródła."""
import bpy,math,random,json,hashlib,bmesh
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent;scene=bpy.context.scene;assert scene.get('art_revision')=='detail-render-02-native-groom';rng=random.Random(77183)
# Move the patch outside the cloak's solidified exterior (its original normals face inward).
for obj in bpy.data.objects:
 if obj.type=='MESH' and obj.name.startswith(('Płaszcz / naszyta łata','Łata płaszcza / fastryga')):
  blocks=obj.data.shape_keys.key_blocks if obj.data.shape_keys else []
  arrays=[k.data for k in blocks] if blocks else [obj.data.vertices]
  for array in arrays:
   for v in array:v.co+=Vector((v.co.x+.025,v.co.y,0)).normalized()*.010
  if blocks:
   for v,base in zip(obj.data.vertices,blocks[0].data):v.co=base.co
  for a,v in zip(obj.data.attributes['rest_position'].data,obj.data.vertices):a.vector=v.co
# Consistent outward normals on the two new leather panels.
for obj in bpy.data.objects:
 if obj.type=='MESH' and obj.name.startswith('Kaftan / dolna poła'):
  bm=bmesh.new();bm.from_mesh(obj.data);bm.normal_update();reverse=[]
  for f in bm.faces:
   c=f.calc_center_median()
   if f.normal.dot(Vector((c.x-.016,c.y,0)))<0:reverse.append(f)
  bmesh.ops.reverse_faces(bm,faces=reverse);bm.to_mesh(obj.data);bm.free();obj.data.update()
cape=bpy.data.objects['Krótki płaszcz / miękkie fałdy']
for poly in cape.data.polygons:
 for idx in poly.loop_indices:
  v=cape.data.vertices[cape.data.loops[idx].vertex_index].co;cape.data.uv_layers['Materiał / metry'].data[idx].uv.y=v.z/.32
  cape.data.uv_layers['Brud lokalny'].data[idx].uv=((v.y+.36)/.72,(v.z-.32)/.30)
# A continuous growth field radiates from the crown; no horizontal direction seam.
obj=bpy.data.objects['Włosy / naturalny przepływ pasm'];data=obj.data;pos=data.attributes['position'];roots=[pos.data[c.first_point_index].vector.copy() for c in data.curves];count=len(roots)
# Short undercoat covers the sparse temple transition; the long strands remain distinct.
extra=2000;data.add_curves([9]*extra);roots += [rng.choice(roots).copy() for _ in range(extra)];points=[];radii=[];C=Vector((.055,0,1.69));R=Vector((.112,.083,.112));crown=Vector((.030,-.016,1.815))
for i,p in enumerate(roots):
 v=p-C;n=Vector((v.x/(R.x*R.x),v.y/(R.y*R.y),v.z/(R.z*R.z))).normalized();direction=p-crown+Vector((0,.008,-.018));direction=(direction-n*direction.dot(n)).normalized();side=n.cross(direction).normalized()
 short=i>=count
 length=rng.uniform(.016,.029) if short else rng.uniform(.040,.088)
 wave=.0015 if short else .004+.003*math.sin(p.y*47+p.x*27)**2
 phase=math.sin(p.x*37+p.y*61)*2.3+rng.uniform(-.5,.5);lift=rng.uniform(.002,.005) if short else .008+.009*math.sin(p.x*40-p.y*23)**2
 r=rng.uniform(.00013,.00023)
 for j in range(9):
  t=j/8;q=p+direction*length*t+n*(.001+lift*math.sin(math.pi*t));q+=side*(wave*t*(math.sin(t*5+phase)-math.sin(phase)))
  v=q-C;norm=Vector((v.x/R.x,v.y/R.y,v.z/R.z)).length;limit=1.018+lift/.1*math.sin(math.pi*t)+.02*t
  if norm<1.015 or norm>limit:q=C+v*(max(1.015,min(limit,norm))/max(norm,1e-5))
  points.extend(q);radii.append(r*(1-.94*t))
pos.data.foreach_set('vector',points);data.attributes['radius'].data.foreach_set('value',radii);obj['strand_count']=len(roots)
scene['art_revision']='detail-render-03-review';scene.frame_set(1);bpy.context.preferences.filepaths.save_version=0;dest=HERE/'bohater_detale.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest))
p=HERE/'bohater_detale.source.json';meta=json.loads(p.read_text());meta.update(source_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),revision=scene['art_revision'],native_hair_strands=len(roots),finish_recipe='detail_finish.py');p.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n');print('DETAIL_FINISH_SAVED',meta['source_sha256'])
