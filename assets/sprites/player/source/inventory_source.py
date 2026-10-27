"""Zapisz bieżący inwentarz źródła, bez zmiany modelu."""
import bpy,json,hashlib,sys,argparse
from pathlib import Path
HERE=Path(__file__).resolve().parent;source=Path(bpy.data.filepath);digest=hashlib.sha256(source.read_bytes()).hexdigest();parser=argparse.ArgumentParser();parser.add_argument('--manifest',type=Path,default=HERE/'art-source.json');args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []);p=args.manifest;data=json.loads(p.read_text()) if p.exists() else {}
if 'materials' in data:data['historical_pass1_materials']=data.pop('materials')
if 'chunk03_assignments' in data:data['historical_chunk03_assignments']=data.pop('chunk03_assignments')
data['object_materials']={o.name:[{'material':m.name,'texture_set':m.get('texture_set','procedural')} for m in o.data.materials if m] for o in bpy.data.objects if o.type in {'MESH','CURVES'} and o.data.materials}
data['packed_images']={im.name:{'packed':im.packed_file is not None,'color_space':im.colorspace_settings.name,'size':list(im.size)} for im in bpy.data.images if im.source=='FILE'}
assert all(i['packed'] for i in data['packed_images'].values()),'Unpacked image dependency'
data['actions']={a.name:list(a.frame_range) for a in bpy.data.actions};data['source_sha256']=digest;data['art_revision']=bpy.context.scene['art_revision'];data['source_policy']='Canonical artistic blend; render reads saved geometry/actions and never writes blend; recipes are explicit one-time edits only.'
p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
print('SOURCE_INVENTORY',len(data['object_materials']),'objects',len(data['packed_images']),'packed images')
