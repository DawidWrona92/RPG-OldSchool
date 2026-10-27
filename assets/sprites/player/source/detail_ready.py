"""Ostatnie ustawienie szerokości rozdarć przed statycznym przeglądem."""
import bpy,json,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;scene=bpy.context.scene;p=HERE/'bohater_detale.source.json';meta=json.loads(p.read_text());source=Path(bpy.data.filepath)
assert scene.get('art_revision')=='detail-render-03-review'
assert hashlib.sha256(source.read_bytes()).hexdigest()==meta['source_sha256'],'Źródło ma niezapisane w manifeście poprawki; nie nadpisuję.'
cape=bpy.data.objects['Krótki płaszcz / miękkie fałdy'];mask=next(m for m in cape.modifiers if m.type=='MASK');mask.threshold=.45
scene['art_revision']='detail-render-04-review';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(source))
meta.update(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),revision=scene['art_revision'],cloak_hole_threshold=.45,ready_recipe='detail_ready.py');p.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
