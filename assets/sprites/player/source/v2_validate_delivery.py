"""Niezależny od Blendera odczyt paczki, formatów map i powtórzonych pikseli."""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'reviews/v2-f0-f3';P2=ROOT/'handoff/p2'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
source_sha=sha(ROOT/'source/bohater_v2.blend');m=json.loads((P2/'manifest.json').read_text());assert m['complete'] and m['file_count']==154 and len(m['parts'])==22 and m['source_blend_sha256']==source_sha
assert m['baker_sha256']==sha(ROOT/'source/v2_bake_p2.py')
reports=[]
for name,part in m['parts'].items():
    for file,digest in part['files'].items():assert sha(P2/file)==digest
    uv=np.array(Image.open(P2/(name+'_uv.png')));mask=uv[:,:,3]>0
    for i in range(2):mask=mask&np.roll(mask,1,0)&np.roll(mask,-1,0)&np.roll(mask,1,1)&np.roll(mask,-1,1)
    n=np.array(Image.open(P2/(name+'_normal_sculpt.png')));assert n.shape==(2048,2048,3) and n.dtype==np.uint8
    norm=np.linalg.norm(n[mask].astype(np.float32)/127.5-1,axis=1);bad=int((abs(norm-1)>.012).sum())
    scalars={}
    for kind in ['ao','curvature','height_ground']:
        im=Image.open(P2/(name+'_'+kind+'.png'));assert im.size==(2048,2048) and im.mode=='I;16',(name,kind,im.mode);a=np.array(im);assert a.dtype==np.uint16;values=a[mask];scalars[kind]={'min':float(values.min()/65535),'max':float(values.max()/65535),'bit_depth':16}
    ids=Image.open(P2/(name+'_id.png'));assert ids.mode=='RGB' and ids.size==(2048,2048)
    preview=Image.open(P2/(name+'_preview.png'));assert preview.mode=='RGBA' and preview.size==(768,768)
    reports.append({'part':name,'verified_files':7,'resolution':part['resolution'],'texel_density_px_m':part['texel_density_px_m'],'normal_sampled_interior_pixels':int(mask.sum()),'normal_unit_length_outliers':bad,'normal_unit_length_outlier_fraction':bad/max(1,int(mask.sum())),'scalars':scalars})
repro=Path('/tmp/hero-v2-reproduction');audit=json.loads((repro/'audit.json').read_text());assert audit['source_blend_sha256']==source_sha
pixels=[]
for relative in ['game_0.png','shadows/game_0.png']:
    a=np.array(Image.open(OUT/'game'/relative));b=np.array(Image.open(repro/relative));assert a.shape==b.shape;delta=abs(a.astype(np.int16)-b.astype(np.int16));pixels.append({'file':relative,'identical_decoded_rgba_pixels':bool(np.array_equal(a,b)),'max_channel_difference_255':int(delta.max()),'different_pixels':int(np.any(delta!=0,axis=2).sum())})
reproduction={'source_blend_sha256':source_sha,'renderer_sha256':audit['renderer_sha256'],'scope':'Ponownie uruchomiony Blender 4.3, zapisane źródło, kierunek S, klatka 1, postać i cień. Nie jest to powtórzenie wszystkich 8 kierunków ani całego P2.','frames':pixels}
(OUT/'reproduction-validation.json').write_text(json.dumps(reproduction,ensure_ascii=False,indent=2)+'\n')
report={'source_blend_sha256':source_sha,'p2_manifest_sha256':sha(P2/'manifest.json'),'p2_verified_png_files':154,'part_count':22,'parts':reports,'note':'Długość normalnych sprawdzona na wnętrzach wysp UV; odstające piksele są raportowane, nie ukrywane. Kontrola formatów/hash nie zastępuje oceny malarskiej.'}
(OUT/'p2-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');assert sha(ROOT/'source/bohater_v2.blend')==source_sha
print('V2_DELIVERY_VALIDATED',source_sha,'P2',len(reports),'normal outliers',sum(p['normal_unit_length_outliers'] for p in reports),'reproduction',pixels)
