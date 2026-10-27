"""Rasteryzacja wyeksportowanych UV, kontrola plików i uzupełnienie manifestu P2."""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent.parent;out=ROOT/'handoff/p2';path=out/'manifest.json';m=json.loads(path.read_text())
source_validation=ROOT/'reviews/v2-f0-f3/source-validation.json';source=json.loads(source_validation.read_text())
assert source['source_blend_sha256']==m['source_blend_sha256']
assert set(m['parts'])=={p['name'] for p in source['parts']},'Niepełne przekazanie P2'
for name,p in m['parts'].items():
    if not p.get('normal_postprocess'):
        normalfile=name+'_normal_sculpt.png';normalpath=out/normalfile;rawsha=hashlib.sha256(normalpath.read_bytes()).hexdigest();assert rawsha==p['files'][normalfile]
        image=np.array(Image.open(normalpath));vectors=image.astype(np.float32)/127.5-1;length=np.linalg.norm(vectors,axis=2);valid=np.any(image!=0,axis=2);cancelled=valid&(length<.02)
        vectors/=np.maximum(length[:,:,None],1e-8);vectors[cancelled]=(0,0,1);result=np.round(np.clip((vectors+1)*127.5,0,255)).astype(np.uint8);result[~valid]=(0,0,0);Image.fromarray(result).save(normalpath)
        p['normal_postprocess']={'method':'Renormalizacja wektorów tangent po filtrowaniu bake, RGB8; tło czarne zachowane; bliskie zeru wektory po zniesieniu kierunków na krawędzi zastąpione neutralnym +Z.','source_bake_sha256':rawsha,'near_zero_vectors_set_neutral':int(cancelled.sum()),'processed_non_background_pixels':int(valid.sum())};p['files'][normalfile]=hashlib.sha256(normalpath.read_bytes()).hexdigest()
    layout=out/p.pop('uv_layout_pending',name+'_uv.json')
    if not layout.exists():
        assert name+'_uv.png' in p['files']
        for file,digest in p['files'].items():assert hashlib.sha256((out/file).read_bytes()).hexdigest()==digest
        continue
    data=json.loads(layout.read_text());size=data['size'];im=Image.new('RGBA',(size,size),(0,0,0,0));d=ImageDraw.Draw(im)
    for poly in data['polygons']:
        points=[(u*(size-1),(1-v)*(size-1)) for u,v in poly];d.polygon(points,fill=(220,220,220,255));d.line(points+[points[0]],fill=(35,35,35,255),width=1)
    file=name+'_uv.png';im.save(out/file);p['files'][file]=hashlib.sha256((out/file).read_bytes()).hexdigest()
    layout.unlink()
    assert len(p['files'])==7
    for file,digest in p['files'].items():
        assert hashlib.sha256((out/file).read_bytes()).hexdigest()==digest
        with Image.open(out/file) as img:img.load();assert img.size==((768,768) if file.endswith('_preview.png') else tuple(p['resolution']))
m['complete']=True;m['file_count']=sum(len(p['files']) for p in m['parts'].values());m['source_validation_sha256']=hashlib.sha256(source_validation.read_bytes()).hexdigest();m['finisher_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
m['maps']['normal_sculpt']='Cycles selected-to-active z ewaluowanych fałd/Subsurf/Solidify na bazowe UV, tangent OpenGL; po bake renormalizacja RGB8, bliskie zeru wektory po zniesieniu kierunków na krawędzi neutralne +Z. SHA surowego bake i liczby w normal_postprocess każdej części. Nie skan ani ręczny high-poly.'
path.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');print('P2_COMPLETE',len(m['parts']),'parts',m['file_count'],'files')
