"""Korekta po wizualnym pilocie NW: ostrze prowadzone dalej na zewnątrz, bez skalowania."""
from pathlib import Path
import bpy,json,hashlib
from mathutils import Vector
HERE=Path(__file__).resolve().parent;scene=bpy.context.scene
assert scene.get('art_revision')=='refinement-02'
rig=bpy.data.objects['Bohater_RIG'];wrist=rig.data.bones['hand.R'].head_local
rot=Vector((.35,-.52,-.78)).normalized().rotation_difference(Vector((.08,-.62,-.78)).normalized()).to_matrix()
for obj in bpy.data.objects:
 if obj.type=='MESH' and obj.name.startswith(('Miecz /','Szlif ostrza','Jelec','Rękojeść','Głowica miecza','Palec zgięty','Prawa rękawica')):
  for v in obj.data.vertices:v.co=wrist+rot@(v.co-wrist)
  attr=obj.data.attributes.get('rest_position')
  if attr:
   for a,v in zip(attr.data,obj.data.vertices):a.vector=v.co
scene['art_revision']='refinement-03';bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'bohater.blend'))
p=HERE/'art-source.json';data=json.loads(p.read_text());data['source_sha256']=hashlib.sha256((HERE/'bohater.blend').read_bytes()).hexdigest();data['art_revision']=scene['art_revision'];data['carry_recipe']='adjust_carry.py';p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
