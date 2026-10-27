"""Korekta po porównaniu pełnej sylwetki z nowymi artami: długość kaftana i swobodniejszy groom."""
import bpy,math,random,json,hashlib
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent;scene=bpy.context.scene;assert scene.get('art_revision')=='detail-render-04-review';meta_path=HERE/'bohater_detale.source.json';meta=json.loads(meta_path.read_text());dest=Path(bpy.data.filepath);assert hashlib.sha256(dest.read_bytes()).hexdigest()==meta['source_sha256']
# Hip-length leather panels, a narrow front split, not a cropped waistcoat.
for obj in bpy.data.objects:
 if obj.type=='MESH' and obj.name.startswith('Kaftan / dolna poła'):
  sign=1 if sum(v.co.y for v in obj.data.vertices)>0 else -1
  for i,v in enumerate(obj.data.vertices):
   j,k=divmod(i,19);z,rx,ry=[(1.075,.154,.195),(1.04,.159,.201),(.925,.179,.222),(.825,.185,.230)][j];gap=math.radians(10-2*j/3);a=gap+(math.radians(92)-gap)*k/18
   v.co=(.016+rx*math.cos(a)+.003*math.sin(a*7+z*17)*(j/3),sign*ry*math.sin(a),z+(.008*math.sin(a*9)+.005*math.sin(a*17))*(j/3)**4+(.010 if sign<0 else 0)*(j/3))
  for a,v in zip(obj.data.attributes['rest_position'].data,obj.data.vertices):a.vector=v.co
  uv=obj.data.uv_layers['Materiał / metry']
  for p in obj.data.polygons:
   for idx in p.loop_indices:
    v=obj.data.vertices[obj.data.loops[idx].vertex_index].co;uv.data[idx].uv=(math.atan2(v.y,v.x-.016)/math.tau*4,v.z/.32)
 if obj.type=='MESH' and obj.name.startswith('Kaftan / zużyte obszycie dołu'):
  for v in obj.data.vertices:
   v.co.z-=.110
   a=math.atan2(abs(v.co.y),v.co.x-.016);oldgap=math.radians(22);u=(a-oldgap)/(math.radians(92)-oldgap);newa=math.radians(8)+(math.radians(92)-math.radians(8))*u;r=math.sqrt((v.co.x-.016)**2+v.co.y**2);sign=1 if v.co.y>0 else -1;v.co.x=.016+r*math.cos(newa);v.co.y=sign*r*math.sin(newa)
shirt=bpy.data.objects['Koszula / nierówny lniany brzeg pod kaftanem']
for i,v in enumerate(shirt.data.vertices):
 j,k=divmod(i,97);t=j/3;a=math.tau*k/96;v.co.z=1.02*(1-t)+(.790+.055*max(0,math.cos(a))**8+.010*math.sin(a*17)+.006*math.sin(a*29))*t
for a,v in zip(shirt.data.attributes['rest_position'].data,shirt.data.vertices):a.vector=v.co
# Small bites in the visible linen hem expose the trouser layer, not empty anatomy.
g=shirt.vertex_groups.new(name='Uszkodzenia / nierówny lniany dół');g.add([3*97+4,3*97+17,3*97+80,3*97+91],1,'REPLACE');m=shirt.modifiers.new('Len / wyrwane nitki brzegu','MASK');m.vertex_group=g.name;m.invert_vertex_group=True;m.threshold=.4;m.use_smooth=True
bpy.context.view_layer.objects.active=shirt
while list(shirt.modifiers).index(m)>0 and shirt.modifiers[list(shirt.modifiers).index(m)-1].type=='SOLIDIFY':bpy.ops.object.modifier_move_up(modifier=m.name)
# Asymmetric, loose locks. Front strands sweep diagonally, leaving more forehead;
# varied tips stand off the scalp instead of all ending on one spherical contour.
obj=bpy.data.objects['Włosy / naturalny przepływ pasm'];data=obj.data;position=data.attributes['position'];roots=[position.data[c.first_point_index].vector.copy() for c in data.curves];C=Vector((.055,0,1.69));R=Vector((.112,.083,.112));crown=Vector((.030,-.016,1.815));rng=random.Random(51762);points=[];radii=[]
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
for i,p in enumerate(roots):
 v=p-C;n=Vector((v.x/R.x**2,v.y/R.y**2,v.z/R.z**2)).normalized();short=i>=12000;front=smooth((p.x-.025)/.12)*smooth((p.z-1.695)/.08)
 direction=p-crown+Vector((.030*front,.075*front+.008,-.018));direction=(direction-n*direction.dot(n)).normalized();side=n.cross(direction).normalized()
 if short:length=rng.uniform(.016,.030);lift=rng.uniform(.002,.005);tip=.001
 else:
  length=rng.uniform(.039,.080)
  if p.x>.10 and abs(p.y)<.042:length*=.72
  if p.z<1.75:length*=.82
  lift=.010+.010*math.sin(p.x*41-p.y*27)**2+rng.uniform(-.002,.003);tip=rng.uniform(.003,.010)
  if rng.random()<.12:tip+=.006
 wave=.0015 if short else .004+.004*math.sin(p.y*47+p.x*27)**2;phase=math.sin(p.x*37+p.y*61)*2.3+rng.uniform(-.5,.5);r=rng.uniform(.00012,.00022)
 for j in range(9):
  t=j/8;q=p+direction*length*t+n*(.001+lift*math.sin(math.pi*t)+tip*t*t);q+=side*(wave*t*(math.sin(t*5+phase)-math.sin(phase)));v=q-C;norm=Vector((v.x/R.x,v.y/R.y,v.z/R.z)).length;limit=1.018+lift/.1*math.sin(math.pi*t)+tip/.1*t*t
  if norm<1.015 or norm>limit:q=C+v*(max(1.015,min(limit,norm))/max(norm,1e-5))
  points.extend(q);radii.append(r*(1-.94*t))
position.data.foreach_set('vector',points);data.attributes['radius'].data.foreach_set('value',radii)
scene['art_revision']='detail-render-05-review';scene.frame_set(1);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(dest));meta.update(source_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),revision=scene['art_revision'],fit_groom_recipe='detail_refine_fit_groom.py',leather_hem_m=.825,linen_center_hem_m=.845);meta_path.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
