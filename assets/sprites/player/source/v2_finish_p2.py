"""Rasteryzacja wyeksportowanych UV, kontrola plików i uzupełnienie manifestu P2."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent.parent;out=ROOT/'handoff/p2';path=out/'manifest.json';m=json.loads(path.read_text())
for name,p in m['parts'].items():
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
path.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');print('P2_COMPLETE',len(m['parts']),'parts',sum(len(p['files']) for p in m['parts'].values()),'files')
