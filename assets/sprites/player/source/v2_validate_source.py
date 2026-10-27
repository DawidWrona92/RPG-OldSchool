"""Rzeczywisty odczyt kontraktu, źródeł i organizacji statycznego v2."""
import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v2_common import *
from bpy_extras.object_utils import world_to_camera_view
sc=bpy.context.scene;source=Path(bpy.data.filepath);source_sha=sha(source);rig=bpy.data.objects['Bohater_RIG'];body=bpy.data.objects['Ciało / MakeHuman / UV natywne'];raw,uv,faces=read_obj();errors=[]
assert len(body.data.vertices)==len(raw) and len(body.data.polygons)==len(faces)
for poly,f in zip(body.data.polygons,faces):
    assert list(poly.vertices)==[q[0] for q in f]
    for li,q in zip(poly.loop_indices,f):errors.append(max(abs(body.data.uv_layers.active.data[li].uv[a]-uv[q[1]][a]) for a in range(2)))
assert max(errors)<6e-8;assert len(rig.data.bones)==163
archives=json.loads((HERE/'archive-sources.json').read_text());assert all(sha(ROOT/a['path'])==a['sha256'] for a in archives['archives'])
cam=sc.camera;assert cam.data.type=='ORTHO' and abs(cam.data.ortho_scale-3.2)<1e-6
assert max(abs(a-b) for a,b in zip(cam.location,[6.9282032303,0,5.2]))<1e-5
assert abs(cam.rotation_euler.x-math.pi/3)<1e-6 and abs(cam.rotation_euler.z-math.pi/2)<1e-6
anchor=world_to_camera_view(sc,cam,Vector((0,0,0)));anchor192=[anchor.x*192,(1-anchor.y)*192]
assert max(abs(a-b) for a,b in zip(anchor192,[96,158.353829]))<1e-4
expected={'Chłodne niebo / klucz z lewej':(520,2.3,(.94,.92,.85),(2.8,-3.5,6)),'Chłodne niebo / tył':(140,3,(.60,.70,.85),(-3,1,4)),'Odbite światło ziemi':(65,4,(.64,.68,.74),(3,4,2.5))}
lights={}
for name,(power,size,color,pos) in expected.items():
    lamp=bpy.data.objects[name];d=lamp.data;assert d.energy==power and abs(d.size-size)<1e-6 and max(abs(a-b) for a,b in zip(d.color,color))<1e-6 and max(abs(a-b) for a,b in zip(lamp.location,pos))<1e-6
    lights[name]={'watts':d.energy,'size_m':d.size,'color':list(d.color),'location_m':list(lamp.location),'rotation_radians':list(lamp.rotation_euler)}
bg=sc.world.node_tree.nodes.get('Background');assert abs(bg.inputs['Strength'].default_value-.2)<1e-6;assert sc.view_settings.view_transform=='AgX' and sc.view_settings.look=='AgX - Medium High Contrast' and abs(sc.view_settings.exposure+.2)<1e-6
images=[{'name':i.name,'file':i.filepath,'packed':bool(i.packed_file),'size':list(i.size),'colorspace':i.colorspace_settings.name} for i in bpy.data.images if i.source=='FILE'];assert all(i['packed'] for i in images)
for entry in images:
    i=bpy.data.images[entry['name']];entry['packed_sha256']=__import__('hashlib').sha256(i.packed_file.data).hexdigest();external=TEX/Path(i.filepath).name
    assert external.exists() and entry['packed_sha256']==sha(external),'Spakowany obraz różni się od aktualnego dostarczonego pliku'
parts=[{'name':o.name,'vertices':len(o.data.vertices),'faces':len(o.data.polygons),'uv_layers':len(o.data.uv_layers),'texture_resolution':o.get('texture_resolution'),'texel_density_px_m':o.get('texel_density_px_m'),'cloth':json.loads(o['cloth_simulation']) if o.get('cloth_simulation') else None,'modifiers':[m.type for m in o.modifiers]} for o in sc.objects if o.get('p2_part')]
assert all(p['uv_layers']==1 for p in parts);assert not rig.animation_data or not rig.animation_data.action
hair=[]
for o in sc.objects:
    if o.type=='CURVES':hair.append({'name':o.name,'strands':o.get('strand_count'),'parent_bone':o.parent_bone})
report={'source_blend_sha256':source_sha,'revision':sc['art_revision'],'blender':bpy.app.version_string,'body':{'vertices':len(raw),'faces':len(faces),'uv_loop_count':len(errors),'native_uv_max_float_error':max(errors)},'bone_count':len(rig.data.bones),'active_animation':None,'frame':sc.frame_current,'camera':{'ortho_m':cam.data.ortho_scale,'location':list(cam.location),'rotation':list(cam.rotation_euler),'anchor_192_px':anchor192},'lights':lights,'color':{'view':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure},'images':images,'parts':parts,'hair_curves':hair,'archive_hashes_unchanged':True,'note':'Test źródła nie zastępuje B1/B2 ani pełnego testu deformacji/kolizji. Curves nie są siatkami w narzędziu PM.'}
out=ROOT/'reviews/v2-f0-f3';out.mkdir(parents=True,exist_ok=True);(out/'source-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');assert sha(source)==source_sha;print('V2_SOURCE_OK',source_sha,'parts',len(parts))
