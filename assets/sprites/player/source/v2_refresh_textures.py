"""Jawna podmiana paczki pod tymi samymi nazwami, bez przebudowy modelu/shaderów.

Nie uruchamia się przy renderze. Wymaga już skopiowanej paczki i jej manifestu.
Przykład dopiero po dostarczeniu v4: -- --version 4 --commit <pełny SHA>
"""
import sys,json,hashlib,argparse,re
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v2_common import *
import numpy as np
ap=argparse.ArgumentParser();ap.add_argument('--version',type=int,required=True);ap.add_argument('--commit',required=True);args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
assert re.fullmatch('[0-9a-f]{40}',args.commit),'Podaj pełny commit pochodzenia'
source=Path(bpy.data.filepath);assert source.resolve()==(HERE/'bohater_v2.blend').resolve();before_sha=sha(source)
manifest=json.loads((TEX/'manifest.json').read_text());assert manifest['material_version']==args.version
for entry in manifest['files']:assert sha(TEX/entry['file'])==entry['sha256'],entry['file']
def geometry_digest():
    h=hashlib.sha256()
    for o in sorted(bpy.context.scene.objects,key=lambda o:o.name):
        if o.type not in ['MESH','CURVES','ARMATURE']:continue
        h.update(o.name.encode());h.update(np.asarray(o.matrix_world,dtype='<f4').tobytes())
        if o.type=='MESH':
            h.update(np.array([v.co[:] for v in o.data.vertices],dtype='<f4').tobytes())
            h.update(json.dumps([list(p.vertices) for p in o.data.polygons]).encode())
            for uv in o.data.uv_layers:h.update(np.array([u.uv[:] for u in uv.data],dtype='<f4').tobytes())
        elif o.type=='CURVES':
            for name in ['position','radius']:
                a=o.data.attributes.get(name)
                if a:
                    vals=np.empty(len(a.data)*(3 if name=='position' else 1),dtype='<f4');a.data.foreach_get('vector' if name=='position' else 'value',vals);h.update(vals.tobytes())
        else:
            for b in o.data.bones:h.update(b.name.encode());h.update(np.asarray(b.matrix_local,dtype='<f4').tobytes())
    return h.hexdigest()
geometry_before=geometry_digest();updated=[]
for i in bpy.data.images:
    if i.source!='FILE':continue
    path=TEX/Path(i.filepath).name
    if not path.exists():continue
    colorspace=i.colorspace_settings.name
    if i.packed_file:i.unpack(method='REMOVE')
    i.filepath=str(path);i.reload();i.colorspace_settings.name=colorspace;i.pack();assert hashlib.sha256(i.packed_file.data).hexdigest()==sha(path);updated.append({'file':path.name,'sha256':sha(path)})
assert len(updated)==7 and geometry_digest()==geometry_before
sc=bpy.context.scene;revision=sc['art_revision'];sc['skin_texture_version']=args.version;sc['texture_package_commit']=args.commit
skin=bpy.data.objects['Ciało / MakeHuman / UV natywne'].data.materials[0];skin.name=f'Skóra / GPT6 v{args.version} / natywne UV';skin['texture_package']=args.commit
save(revision+f'-textures-v{args.version}')
(HERE/'texture-refresh.json').write_text(json.dumps({'parent_source_sha256':before_sha,'source_blend_sha256':sha(source),'package_commit':args.commit,'version':args.version,'geometry_uv_rig_curves_unchanged_sha256':geometry_before,'updated_images':updated,'note':'Po tej zmianie nowe podglądy/eksport muszą mieć nowe SHA źródła. Nie przepisywać po cichu manifestów starszych renderów/P2.'},indent=2)+'\n')
