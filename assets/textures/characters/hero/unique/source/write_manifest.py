"""Complete versioned provenance and SHA-256 inventory; excludes circular self-hash."""
from pathlib import Path
import hashlib,json,platform
from PIL import Image
import PIL,numpy,scipy
root=Path(__file__).resolve().parents[1]
mesh=Path('/tmp/hero-base.obj');assert mesh.is_file()
base='35df59f4c19b473530fd3fe316b35fc7b1739327'
main='eb3a2ec6282855e8b659970b10a677b4232d68fe'
versions={1:'bdc6529908389f3422aca66945cd0b7c1ebcb8ec',2:'27017148d13eb9c422ff54da760775f7eb16a331',3:base,4:'current v4 files'}
methods={
 'basecolor':'Unlit 3D surface pigment: concept19 pink irregular healed scars with darker centers and suture traces, freckles, red nose/cheeks, dense beard/moustache with random gray follicles concentrated on chin; scalp gray follicles. No light/AO input.',
 'roughness':'Anatomical scalar response; smoother healed scar tissue. V3 hands/neck protected.',
 'height':'16-bit microrelief: interrupted forehead creases, glabellar frown, crowfeet, under-eye bags; positive raised scar rims/cores and tiny suture traces. No neck seam strokes or hand lines/veins.',
 'normal_opengl':'Normalized tangent OpenGL +Y height-gradient vectors; Blender MikkTSpace normal mapping, no high-poly bake. Protected v3 normal pixels restored exactly.',
 'sss_mask':'Unchanged byte-for-byte from v3, relative ears/nose/fingers thinness proxy, not physical thickness.'}
tools=['Python '+platform.python_version(),'NumPy '+numpy.__version__,'SciPy '+scipy.__version__,'Pillow '+PIL.__version__]
files=[]
for path in sorted(root.rglob('*')):
 if not path.is_file() or '__pycache__' in path.parts or path.name=='manifest.json':continue
 rel=path.relative_to(root).as_posix();e={'file':rel,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'status':'PROTOTYPE_NOT_APPROVED'}
 if path.suffix.lower() in ['.png','.jpg']:
  im=Image.open(path);im.load();e.update(resolution=list(im.size),channels=im.mode,bit_depth=path.read_bytes()[24] if path.suffix=='.png' else 8)
 else:e.update(resolution=None,channels=None,bit_depth=None)
 if path.name.startswith('hero_skin_body_'):
  m=path.stem.removeprefix('hero_skin_body_').removesuffix('_2048')
  e.update(map=m,color_space='sRGB' if m=='basecolor' else 'linear / Non-Color',method=methods[m]+' 4K with Lanczos 2K derivatives; v3 restored outside the protected head-edit mask.',tools=tools,models=None,material_version=4,sources=['source/build_maps.py','source/aging_v2.py','source/face_v4.py','baseline '+base,'concept19 v2 / brief main @ '+main,'pinned CC0 body mesh'])
 elif path.name=='hero_eye_iris_basecolor.png':
  e.update(map='iris_basecolor',color_space='sRGB',method='Procedural gray-green/gray-hazel radial iris fibers, warm olive-brown inner ring, dark limbus, no catchlight; RGBA 512, 80% iris diameter, 30% relative pupil.',tools=tools,models=None,material_version=4,sources=['source/build_eye.py','concept19 v2 and A2 brief @ '+main])
 elif path.name=='hero_eye_sclera_basecolor.png':
  e.update(map='sclera_basecolor',color_space='sRGB',method='Unchanged from v3; original generator not documented by predecessor.',tools=['Unknown original generator; validated with Pillow'],models=None,material_version=3,sources=['59966fbb59ef87f685dd6ef67bed5b8d0e540144 original sclera',base])
 elif rel=='podglad/v4/reference/concept19.jpg':
  e.update(map='reference',color_space='sRGB',method='Unaltered repository concept19 version2; comparison reference, not copied into albedo.',tools=['Git read-only extraction'],models=None,sources=[{'repository':'DawidWrona92/RPG-OldSchool','commit':main,'path':'docs/koncepty/19-bohater-twarz.jpg'}])
 elif rel.startswith('podglad/') and (path.name=='porownanie.png' or path.name=='koncept19-v4.png'):
  v=int(path.parent.name[1:]);e.update(map='comparison_sheet',color_space='sRGB / AgX for renders',method='Labeled deterministic review layout; render pixels unchanged. Concept is resized only for display and has its own illustration lighting.',tools=tools,models=None,material_version=[v-1,v],sources=['source/compare_v4.py' if v==4 else 'source/compare_v2.py',str(path.parent.relative_to(root))])
 elif rel.startswith('podglad/'):
  v=4
  for vv in [2,3,4]:
   if f'/v{vv}/before/' in rel:v=vv-1
   elif f'/v{vv}/after/' in rel:v=vv
  e.update(map='diagnostic_render',color_space='sRGB / AgX',method='Cycles rendering of unchanged native body UV/geometry; optional OBJ eye helpers with flat projected iris. Not final hair, sculpt or production cornea.',tools=['Blender 4.3.2 / 64 samples / seed1703 / 4 threads'],models=['MakeHuman hm08 CC0 body and, when marked, helper eyes'],material_version=v,normal_strength=.45,diagnostic_eye_helpers=('/v4/' in rel or '/v' not in rel),sources=['source/render_check.py',versions[v],'pinned OBJ'])
 else:
  e.update(map='validation_report' if rel.startswith('qa/') else 'documentation' if path.suffix=='.md' else 'source_script',color_space='not applicable',method='Authored source, documentation or recorded validation.',tools=['Codex / Python'],models=None,sources=['repository requirements and author review'])
 files.append(e)
m={'schema_version':1,'material_version':4,'status':'PROTOTYPE_NOT_APPROVED','scope':'Part A v4 per concept19 v2. Body formats/UV unchanged; v3 neck/hands restored exactly; no Part B.','repository':'DawidWrona92/RPG-OldSchool','branch':'vibe/hero-textures-gpt6','main_base_commit':'9bf3ff94dfa62aad057594425f4f4bf2b0a44208','previous_work_commit':base,'author_direction_main_commit':main,'mesh':{'repository':'DawidWrona92/RPG-OldSchool','commit':'421c7e895e6a029181dcb7c63ab277ad7bab4ca0','path':'assets/sprites/player/source/third_party/base.obj','group':'body','license':'CC0 per OBJ header','sha256':hashlib.sha256(mesh.read_bytes()).hexdigest()},'normal_convention':'OpenGL +Y, Blender MikkTSpace; normal strength .45','height_convention':{'neutral':.5,'suggested_full_range_meters':.002,'scar_relief':'positive, raised'},'preservation':'Pinned baseline '+base+' outside eroded red head edit mask; neck/hands compared in all ten maps. SSS and sclera completely unchanged.','manifest_self_hash':'Excluded to avoid circular hashing; all other delivered files listed.','files':files}
(root/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');print('Manifest:',len(files),'files')
