"""Statyczny przegląd detali; osobny od zatwierdzanego eksportu animacji08."""
import json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from export_player import native,shadow
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT.parents[2];OUT=ROOT/'reviews/detale-01';BG=(28,35,37,255);DIRS=['S','SW','W','NW','N','NE','E','SE']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
meta=load(ROOT/'source/bohater_detale.source.json');digest=sha(ROOT/'source/bohater_detale.blend');assert digest==meta['source_sha256'];parent=meta['parent_source_sha256'];assert sha(ROOT/'source/bohater.blend')==parent
folders=[('renders',digest,384,range(8)),('duze',digest,1152,[1,3]),('cool',digest,384,[1]),('warm',digest,384,[1])];checked=[]
for folder,source,size,dirs in folders:
 path=OUT/folder;audit=load(path/'motion_audit.json');assert audit['source_blend_sha256']==source and audit['renderer_sha256']==sha(ROOT/'source/render_player.py')
 for d in dirs:
  file=f'spoczynek_{d}_00.png';a=audit['frames'][file];assert sha(path/file)==a['image_sha256'] and sha(path/'shadows'/file)==a['shadow_sha256']
  with Image.open(path/file) as im:
   assert im.mode=='RGBA' and im.size==(size,size);alpha=np.array(im)[:,:,3];assert max(alpha[0].max(),alpha[-1].max(),alpha[:,0].max(),alpha[:,-1].max())==0
  checked.append({'folder':folder,'file':file,'size_px':size})
before_audit=load(ROOT/'renders/details/after/motion_audit.json');assert before_audit['source_blend_sha256']==parent
body_old=Image.open(ROOT/'atlas/bohater_spoczynek.png').convert('RGBA');cast_old=Image.open(ROOT/'atlas/bohater_spoczynek_shadow.png').convert('RGBA')
assert load(ROOT/'previews/technical-report.json')['source_blend_sha256']==parent

def sprite(d,which='after',lighting='renders'):
 canvas=Image.new('RGBA',(192,192),BG)
 if which=='before':canvas.alpha_composite(cast_old.crop((0,d*192,192,(d+1)*192)));canvas.alpha_composite(body_old.crop((0,d*192,192,(d+1)*192)))
 else:
  file=f'spoczynek_{d}_00.png';canvas.alpha_composite(shadow(OUT/lighting/'shadows'/file));canvas.alpha_composite(native(OUT/lighting/file))
 return canvas
im=Image.new('RGBA',(768,384),BG);draw=ImageDraw.Draw(im)
compare=Image.new('RGBA',(1536,384),BG);cd=ImageDraw.Draw(compare)
for d,label in enumerate(DIRS):
 im.alpha_composite(sprite(d),(d%4*192,d//4*192));draw.text((d%4*192+5,d//4*192+5),label+' / 1:1',fill='white')
 for k,which in enumerate(['before','after']):
  x=d%4*384+k*192;y=d//4*192;compare.alpha_composite(sprite(d,which),(x,y));cd.text((x+5,y+5),label+' / '+('PRZED' if k==0 else 'DETALE')+' / 1:1',fill='white')
im.convert('RGB').save(OUT/'osiem-kierunkow-1x.png');compare.convert('RGB').save(OUT/'porownanie-1x.png')
im=Image.new('RGBA',(1024,1472),BG);draw=ImageDraw.Draw(im)
for row,d in enumerate([1,3]):
 for col,folder in enumerate([ROOT/'renders/details/after',OUT/'duze']):
  with Image.open(folder/f'spoczynek_{d}_00.png') as source:tile=source.convert('RGBA').crop((320,280,832,1016));im.alpha_composite(tile,(col*512,row*736))
  draw.text((col*512+8,row*736+8),DIRS[d]+' / '+('PRZED' if col==0 else 'DETALE')+' / render 1152, wycinek',fill='white')
im.convert('RGB').save(OUT/'model-przed-po.png')
im=Image.new('RGBA',(1536,768),BG);draw=ImageDraw.Draw(im)
for col,folder in enumerate(['glowa-przed','glowa-po']):
 with Image.open(OUT/folder/'front.png') as head:im.alpha_composite(head.convert('RGBA'),(col*768,0))
 draw.text((col*768+10,10),('PRZED' if col==0 else 'DETALE')+' / rzeczywisty portret 768 / 128 probek',fill='white')
im.convert('RGB').save(OUT/'glowa-przed-po.png')
im=Image.new('RGBA',(576,192),BG);draw=ImageDraw.Draw(im)
for k,folder in enumerate(['renders','cool','warm']):im.alpha_composite(sprite(1,lighting=folder),(k*192,0));draw.text((k*192+5,5),['bazowe','chlodne','ciepla proba'][k]+' / 1:1',fill='white')
im.convert('RGB').save(OUT/'swiatlo-1x.png')
ref=Image.open(REPO/'docs/koncepty/17-bohater-i-woz.jpg').convert('RGBA');file='spoczynek_1_00.png';position=(round(590-96),round(810-158.353829));ref.alpha_composite(shadow(OUT/'renders/shadows'/file),position);ref.alpha_composite(native(OUT/'renders'/file),position)
ImageDraw.Draw(ref).text((24,480),'ILUSTRACJA KONCEPCYJNA / nie scena gry / sprite 1:1',fill='white');ref.convert('RGB').save(OUT/'koncept17-1x.png')
with Image.open(OUT/'duze/spoczynek_3_00.png') as source:source.crop((390,570,790,1000)).save(OUT/'plaszcz-detal.png')
html='''<!doctype html><html lang="pl"><meta charset="utf-8"><title>Welesza — detale renderu</title><style>body{background:#1c2325;color:#ddd;font:16px system-ui;margin:20px}a{color:#cfc09d}.view{overflow:auto;margin-bottom:24px}img{display:block;max-width:none}p{max-width:1000px}</style><h1>Bohater — statyczny pass detali</h1><p>Ta sama postać i skala świata. Wersja robocza do oceny: dłuższy poszarpany płaszcz, łaty i ściegi, dolne połacie kaftana, nierówny brzeg lnu oraz nowe włókna włosów. Nowych detali nie włączono jeszcze do pełnych atlasów animacji.</p><p><a href="../../source/bohater_detale.blend">Model roboczy</a> · <a href="../../DETAIL_REVIEW.md">Opis zmian i ograniczeń</a> · <a href="../../previews/review.html">Wcześniejszy spoczynek/chód bez Blendera — rewizja 08</a></p><h2>Osiem kierunków 1:1</h2><div class="view"><img src="osiem-kierunkow-1x.png" width="768" height="384"></div><h2>Przed / detale, 1:1</h2><div class="view"><img src="porownanie-1x.png" width="1536" height="384"></div><h2>Model źródłowy — rzeczywiste większe rendery</h2><div class="view"><img src="model-przed-po.png" width="1024" height="1472"></div><h2>Włosy i zarost</h2><div class="view"><img src="glowa-przed-po.png" width="1536" height="768"></div><h2>Światło, 1:1</h2><div class="view"><img src="swiatlo-1x.png" width="576" height="192"></div><p><a href="plaszcz-detal.png">Detal naprawy płaszcza</a> · <a href="koncept17-1x.png">Kompozycja na ilustracji koncepcyjnej</a>. Tło bez skalibrowanej skali; przyjęto lokalnie 60 px/m przy kotwicy (590,810). Sprite nie jest powiększony.</p></html>'''
(OUT/'index.html').write_text(html)
report={'source_sha256':digest,'before_source_sha256':parent,'checked_body_shadow_pairs':len(checked),'checked_frames':checked,'native_frame_size':[192,192],'anchor_px':[96,158.353829],'pixels_per_meter':60,'status':'static detail review; existing animations preserved in working blend, not re-exported or accepted for new cloth','rgba_bounds':'all 12 body images checked, all transparent edges','comparison':'same game camera/exposure; full body 1152; diagnostic portraits 768 at 128 samples','source_validation':load(OUT/'source-validation.json')}
(OUT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
paths=[p for p in OUT.rglob('*') if p.is_file() and p.name!='checksums.json'];(OUT/'checksums.json').write_text(json.dumps({str(p.relative_to(OUT)):sha(p) for p in sorted(paths)},indent=2)+'\n')
print('PASS static review:',len(checked),'source-matched body/shadow pairs, RGBA bounds, native comparisons')
