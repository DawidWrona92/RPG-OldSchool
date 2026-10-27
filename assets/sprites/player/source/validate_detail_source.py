"""Kontrole statycznego źródła detali, bez deklaracji kontroli całych animacji."""
import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=ROOT/'reviews/detale-01';OUT.mkdir(exist_ok=True,parents=True)
source=Path(bpy.data.filepath);digest=hashlib.sha256(source.read_bytes()).hexdigest();meta=json.loads((HERE/'bohater_detale.source.json').read_text());assert digest==meta['source_sha256']
scene=bpy.context.scene;rig=bpy.data.objects['Bohater_RIG'];cape=bpy.data.objects['Krótki płaszcz / miękkie fałdy'];mask=next(m for m in cape.modifiers if m.type=='MASK')
def stats():
 bpy.context.view_layer.update();e=cape.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();result=[len(m.vertices),len(m.polygons)];e.to_mesh_clear();return result
mask.show_viewport=False;before=stats();mask.show_viewport=True;after=stats();assert before!=after,'Maska nie zmienia rzeczywistej geometrii'
packed={i.name:bool(i.packed_file) for i in bpy.data.images if i.source=='FILE'};assert all(packed.values())
origin=world_to_camera_view(scene,scene.camera,Vector());anchor=[origin.x*192,(1-origin.y)*192];assert abs(anchor[0]-96)<.01 and abs(anchor[1]-158.353829)<.01
assert scene.camera.data.type=='ORTHO' and abs(scene.camera.data.ortho_scale-3.2)<1e-6
error=0
for d in [0,3,4]:
 rig.rotation_euler.z=-d*math.pi/4;scene.frame_set(1);bpy.context.view_layer.update();D=rig.matrix_world@rig.pose.bones['head'].matrix@rig.data.bones['head'].matrix_local.inverted()
 for obj in bpy.data.objects:
  if obj.type=='CURVES':
   M=obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world;error=max(error,max(abs(M[r][c]-D[r][c]) for r in range(4) for c in range(4)))
assert error<1e-5,error
report={'source_sha256':digest,'parent_source_sha256':meta['parent_source_sha256'],'revision':scene['art_revision'],'anchor_px':anchor,'camera_ortho_m':scene.camera.data.ortho_scale,'exposure':scene.view_settings.exposure,'packed_images_verified':len(packed),'actual_cloak_cut_geometry':{'without_mask_vertices_faces':before,'with_mask_vertices_faces':after,'threshold':mask.threshold},'hair_curves':{o.name:len(o.data.curves) for o in bpy.data.objects if o.type=='CURVES'},'max_head_attachment_matrix_error':error,'tested_attachment_directions':['S','NW','N'],'scope':'static source and geometry cuts; not garment collision clearance or full animation validation'}
(OUT/'source-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');assert hashlib.sha256(source.read_bytes()).hexdigest()==digest;print('DETAIL_SOURCE_VALIDATION',report)
