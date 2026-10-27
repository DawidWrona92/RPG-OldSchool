"""Opisz kontrast widocznej broni na dwóch tłach; bez progu akceptacji artystycznej."""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
from export_player import native
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT.parents[2];OUT=ROOT/'previews';D=['S','SW','W','NW','N','NE','E','SE'];records=[]
ref=Image.open(REPO/'docs/koncepty/17-bohater-i-woz.jpg').convert('RGBA').crop((370,680,562,872))
bgs={'dark_cool':np.full((192,192,3),(28,35,37),dtype=float),'varied_concept_crop':np.array(ref)[:,:,:3].astype(float)};weights=np.array([.2126,.7152,.0722])
for anim,count in [('spoczynek',8),('chod',12)]:
 for d,label in enumerate(D):
  for f in range(count):
   body=np.array(native(ROOT/'renders'/f'{anim}_{d}_{f:02}.png')).astype(float);mask=np.array(Image.open(OUT/'weapon_masks'/f'{anim}_{label}_{f:02}.png').convert('L'))>128
   mask&=body[:,:,3]>32;alpha=body[:,:,3:4]/255;record={'animation':anim,'direction':label,'frame':f,'masked_visible_pixels':int(mask.sum()),'backgrounds':{}}
   for name,bg in bgs.items():
    composite=body[:,:,:3]*alpha+bg*(1-alpha);delta=np.abs((composite-bg)@weights)[mask]
    record['backgrounds'][name]={'median_abs_luma_delta_0_255':float(np.median(delta)) if len(delta) else 0,'fraction_delta_below_8':float(np.mean(delta<8)) if len(delta) else 1}
   records.append(record)
worst=sorted(records,key=lambda r:r['backgrounds']['dark_cool']['median_abs_luma_delta_0_255'])[:12]
report={'source_blend_sha256':hashlib.sha256((ROOT/'source/bohater.blend').read_bytes()).hexdigest(),'checked_frames':len(records),'method':'8-bit display luma |sprite composite - background| on ObjectIndex mask >128, body alpha >32; descriptive only, not an artistic pass/fail test','backgrounds':['dark cool (28,35,37)','unchanged concept17 crop (370,680)-(562,872), illustration not game scene'],'weakest_dark_cool_samples':worst,'records':records}
(OUT/'weapon-contrast-validation.json').write_text(json.dumps(report,indent=2)+'\n');print('WEAPON_CONTRAST',[(r['animation'],r['direction'],r['frame'],round(r['backgrounds']['dark_cool']['median_abs_luma_delta_0_255'],2)) for r in worst])
