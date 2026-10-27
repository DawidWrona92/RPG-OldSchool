"""Usuń przenikanie lnu przed skórę w nowym kaftanie; zachowaj nierówny brzeg."""
import bpy,math,json,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;scene=bpy.context.scene;assert scene.get('art_revision')=='detail-render-05-review';p=HERE/'bohater_detale.source.json';meta=json.loads(p.read_text());source=Path(bpy.data.filepath);assert hashlib.sha256(source.read_bytes()).hexdigest()==meta['source_sha256']
obj=bpy.data.objects['Koszula / nierówny lniany brzeg pod kaftanem'];uv=obj.data.uv_layers.new(name='Brud lokalny')
for i,v in enumerate(obj.data.vertices):
 j,k=divmod(i,97);t=j/3;a=math.tau*k/96;v.co.x=.015+(.142+.021*t)*math.cos(a);v.co.y=(.174+.037*t)*math.sin(a);obj.data.attributes['wear_mask'].data[i].value=.15+.10*t
for poly in obj.data.polygons:
 for idx in poly.loop_indices:
  v=obj.data.vertices[obj.data.loops[idx].vertex_index].co;uv.data[idx].uv=((v.y+.22)/.44,(v.z-.78)/.18)
for a,v in zip(obj.data.attributes['rest_position'].data,obj.data.vertices):a.vector=v.co
scene['art_revision']='detail-render-06-review';scene.frame_set(1);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(source));meta.update(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),revision=scene['art_revision'],layer_fit_recipe='detail_layer_fit.py');p.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
