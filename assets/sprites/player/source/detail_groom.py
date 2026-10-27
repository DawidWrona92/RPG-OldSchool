"""Włókna Curves i łagodna korekta twarzy istniejącego modelu; bez nowej postaci."""
import bpy,sys,math,random,json,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE));import build_player as b
from render_player import activate
scene=bpy.context.scene;assert scene.get('art_revision')=='detail-render-01-clothing';rig=activate('spoczynek');rig.rotation_euler.z=0;scene.frame_set(1);b.RIG=rig;rng=random.Random(88231)
body=bpy.data.objects['Anatomiczna głowa, szyja i odkryte przedramiona']
# Millimetric changes to the SAME head: stronger jaw and brow, not a replacement head.
def face_wear(p):
 if p.z<1.54:return p
 jaw=math.exp(-((p.z-1.585)/.042)**2)
 p.y*=1+.065*jaw;p.x+=.003*jaw*max(0,min(1,(p.x-.08)/.07))
 p.x+=.003*math.exp(-((p.z-1.699)/.012)**2)*math.exp(-((abs(p.y)-.033)/.024)**2)
 p.x+=.003*math.exp(-((p.z-1.638)/.012)**2)*math.exp(-(p.y/.018)**2)
 return p
for obj in bpy.data.objects:
 if obj.type=='MESH' and obj.name.startswith(('Anatomiczna głowa','Zarost /','Brew /')):
  for v in obj.data.vertices:v.co=face_wear(v.co.copy())
  obj.data.update()
  if obj.data.attributes.get('rest_position'):
   for a,v in zip(obj.data.attributes['rest_position'].data,obj.data.vertices):a.vector=v.co
# Remove the rigid masses from the prior groom. Keep correctly placed beard undercoat/eyebrows.
for obj in list(bpy.data.objects):
 if obj.name.startswith(('Włosy /','Włókna fryzury')):bpy.data.objects.remove(obj,do_unlink=True)
# Actual skin surface is the follicle source; no smooth helmet as the visible hairstyle.
body.data.update()
def scalp_region(p):
 if p.z<1.635:return False
 if p.x<.015:return p.z>1.638
 if abs(p.y)>.058:return p.z>1.689+.025*max(0,(p.x-.07)/.10)
 return p.z>1.753+.004*math.sin(p.y*57)
scalp_faces=[p for p in body.data.polygons if scalp_region(p.center)]
if not scalp_faces:raise RuntimeError('Nie znaleziono powierzchni skóry głowy')
verts=[v.co.copy() for v in body.data.vertices];faces=[tuple(p.vertices) for p in scalp_faces]
# Subtle dark roots lie under the curves and share the anatomical surface.
root=b.subset('Włosy / nasada przy skórze',verts,faces,[{'head':1} for _ in verts],bpy.data.materials['Włosy umbra / Chunk03'],lambda p,f:True,offset=.0005,sub=1)
uv=root.data.uv_layers.new(name='Materiał / metry')
for poly in root.data.polygons:
 for idx in poly.loop_indices:
  p=root.data.vertices[root.data.loops[idx].vertex_index].co;uv.data[idx].uv=(math.atan2(p.y,p.x-.045)/math.tau,p.z/.3)

def hair_material(name,melanin,rough):
 m=bpy.data.materials.new(name);m.use_nodes=True;nodes,links=m.node_tree.nodes,m.node_tree.links;nodes.clear();out=nodes.new('ShaderNodeOutputMaterial');bs=nodes.new('ShaderNodeBsdfHairPrincipled');bs.parametrization='MELANIN';bs.inputs['Melanin'].default_value=melanin;bs.inputs['Melanin Redness'].default_value=.23;bs.inputs['Roughness'].default_value=rough;bs.inputs['Radial Roughness'].default_value=.55;bs.inputs['Coat'].default_value=.10;bs.inputs['Random Color'].default_value=.13;bs.inputs['Random Roughness'].default_value=.10;links.new(bs.outputs[0],out.inputs['Surface']);m['source']='Original authored Curves groom; dark umber palette of supplied hair material';return m
hairmat=hair_material('Włosy / fizyczne drobne włókna',.72,.43);beardmat=hair_material('Zarost / krótkie włókna',.76,.54)

def attach_curves(name,paths,radii,mat):
 data=bpy.data.hair_curves.new(name);data.add_curves([len(path) for path in paths]);obj=bpy.data.objects.new(name,data);bpy.context.scene.collection.objects.link(obj);data.materials.append(mat)
 data.attributes['position'].data.foreach_set('vector',[c for path in paths for point in path for c in point]);radius=data.attributes.new('radius','FLOAT','POINT');radius.data.foreach_set('value',[r*(1-.94*i/(len(path)-1)) for path,r in zip(paths,radii) for i in range(len(path))])
 # Bone parenting preserves the anatomical rest coordinates. Derive the bone-tail
 # offset from Blender's evaluated parent matrix instead of assuming an offset.
 obj.parent=rig;obj.parent_type='BONE';obj.parent_bone='head';obj.matrix_parent_inverse=Matrix.Identity(4);obj.matrix_basis=Matrix.Identity(4)
 bpy.context.view_layer.update();target=obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.copy()
 desired=rig.matrix_world@rig.pose.bones['head'].matrix@rig.data.bones['head'].matrix_local.inverted();obj.matrix_basis=target.inverted()@desired;bpy.context.view_layer.update()
 actual=obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world
 error=max(abs(actual[r][c]-desired[r][c]) for r in range(4) for c in range(4));assert error<1e-5,('Head attachment',error)
 obj['source']='authored native Curves; attached to existing head bone';obj['strand_count']=len(paths);return obj

def sample_face(poly,obj):
 vv=[obj.data.vertices[k].co for k in poly.vertices];ww=[rng.random() for _ in vv];return sum((v*w for v,w in zip(vv,ww)),Vector())/sum(ww)
# Coherent flow from crown to fringe, down the sides and nape, with small irregular waves.
paths=[];radii=[];C=Vector((.055,0,1.69));R=Vector((.112,.083,.112))
for poly in rng.choices(scalp_faces,weights=[max(p.area,1e-8) for p in scalp_faces],k=12000):
 p=sample_face(poly,body);normal=poly.normal.normalized();side=1 if p.y>=0 else -1
 if p.z>1.757:direction=Vector((.95,.28,-.14));length=rng.uniform(.050,.082)
 elif p.x<.012:direction=Vector((-.18,side*.12,-1));length=rng.uniform(.038,.070)
 else:direction=Vector((-.28,side*.10,-1));length=rng.uniform(.043,.073)
 direction=(direction-normal*normal.dot(direction)).normalized();across=normal.cross(direction).normalized();phase=rng.uniform(0,math.tau);lift=rng.uniform(.004,.011);path=[]
 for j in range(9):
  t=j/8;q=p+direction*(length*t)+normal*(.001+lift*math.sin(math.pi*t));q+=across*(.0018*t*(math.sin(t*5+phase)-math.sin(phase)))
  # Prevent the tangent path from cutting through the head as it follows curvature.
  v=q-C;scaled=Vector((v.x/R.x,v.y/R.y,v.z/R.z));norm=scaled.length
  limit=1.015+lift/.10*math.sin(math.pi*t)+.015*t
  if norm<1.015 or norm>limit:
   v*=max(1.015,min(limit,norm))/max(norm,1e-4);q=C+v
  path.append(tuple(q))
 paths.append(path);radii.append(rng.uniform(.00016,.00028))
hair=attach_curves('Włosy / naturalny przepływ pasm',paths,radii,hairmat)
# Corrected beard undercoat remains; replace flat coarse stubble with short curves.
beard=bpy.data.objects['Zarost / policzki żuchwa i podbródek'];beard.data.update();density=beard.data.attributes['beard_density'];paths=[];radii=[]
for i in range(6500):
 poly=rng.choice(list(beard.data.polygons));d=sum(density.data[k].value for k in poly.vertices)/len(poly.vertices)
 if rng.random()>.35+d:continue
 p=sample_face(poly,beard);n=poly.normal.normalized();length=rng.uniform(.002,.0055) if p.z<1.60 else rng.uniform(.0012,.0034)
 paths.append([tuple(p+n*.0005),tuple(p+n*.0013+Vector((0,0,-length*.4))),tuple(p+n*.0008+Vector((0,0,-length)))]);radii.append(rng.uniform(.00008,.00014))
facial=attach_curves('Zarost / włókna na żuchwie',paths,radii,beardmat)
# Verify attachment under two directions and another saved phase; never re-key animations.
attach_error=0
for d,frame in [(0,1),(3,21),(4,41)]:
 rig.rotation_euler.z=-d*math.pi/4;scene.frame_set(frame);bpy.context.view_layer.update();desired=rig.matrix_world@rig.pose.bones['head'].matrix@rig.data.bones['head'].matrix_local.inverted()
 for obj in [hair,facial]:attach_error=max(attach_error,max(abs(obj.matrix_world[r][c]-desired[r][c]) for r in range(4) for c in range(4)))
assert attach_error<1e-5,attach_error
rig.rotation_euler.z=0;scene.frame_set(1);scene['art_revision']='detail-render-02-native-groom';scene['groom_attachment_error']=attach_error
try:scene.cycles.curve_shape='THICK'
except (AttributeError,TypeError):pass
bpy.context.preferences.filepaths.save_version=0;dest=HERE/'bohater_detale.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest))
p=HERE/'bohater_detale.source.json';meta=json.loads(p.read_text());meta.update(source_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),revision=scene['art_revision'],groom_recipe='detail_groom.py',native_hair_strands=hair['strand_count'],native_beard_strands=facial['strand_count'],attachment_matrix_max_error=attach_error);p.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n');print('DETAIL_GROOM_SAVED',meta)
