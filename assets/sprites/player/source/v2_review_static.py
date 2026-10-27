"""Plansze F0–F3 i kontrola rzeczywiście wyrenderowanych klatek; bez atlasu gry."""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageOps
ROOT=Path(__file__).resolve().parent.parent;REPO=ROOT.parents[2];OUT=ROOT/'reviews/v2-f0-f3';DIRS=['S','SW','W','NW','N','NE','E','SE']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
source=ROOT/'source/bohater_v2.blend';source_sha=sha(source);validation=json.loads((OUT/'source-validation.json').read_text());assert source_sha==validation['source_blend_sha256']
def background(im,color=(24,29,32)):
    im=im.convert('RGBA');bg=Image.new('RGBA',im.size,(*color,255));return Image.alpha_composite(bg,im).convert('RGB')
def native(path):
    im=Image.open(path);assert im.mode=='RGBA' and im.size==(384,384);return im.convert('RGBa').resize((192,192),Image.Resampling.LANCZOS).convert('RGBA')
def grid(items,cols,w,h):
    sheet=Image.new('RGB',(cols*w,((len(items)+cols-1)//cols)*h),(24,29,32));d=ImageDraw.Draw(sheet)
    for i,(im,label) in enumerate(items):
        x=i%cols*w;y=i//cols*h;sheet.paste(background(im),(x,y));d.text((x+8,y+h-27),label,font=font,fill=(220,221,213))
    return sheet
game_audit=json.loads((OUT/'game/audit.json').read_text());assert game_audit['source_blend_sha256']==source_sha and len(game_audit['frames'])==8
frames=[];checks=[];(OUT/'native/shadows').mkdir(parents=True,exist_ok=True);world=Image.open(REPO/'docs/koncepty/17-bohater-i-woz.jpg').convert('RGBA');patch=world.crop((205,705,397,897))
for d,label in enumerate(DIRS):
    path=OUT/f'game/game_{d}.png';shadow=OUT/f'game/shadows/game_{d}.png';entry=game_audit['frames'][path.name];assert sha(path)==entry['image_sha256'] and sha(shadow)==entry['shadow_sha256'];im=Image.open(path);a=np.array(im)[:,:,3];ys,xs=np.where(a>0);edge=np.concatenate([a[0],a[-1],a[:,0],a[:,-1]]);assert edge.max()==0
    body=native(path);cast=native(shadow);body.save(OUT/f'native/bohater_{label}.png');cast.save(OUT/f'native/shadows/bohater_{label}.png');composite=Image.alpha_composite(Image.alpha_composite(patch.copy(),cast),body);frames.append((composite,label))
    anchor=[v/2 for v in entry['anchor_px']];assert max(abs(a-b) for a,b in zip(anchor,[96,158.353829]))<1e-4
    shadow_image=Image.open(shadow);assert shadow_image.mode=='RGBA' and shadow_image.size==(384,384);sa=np.array(shadow_image)[:,:,3];shadow_edge=np.concatenate([sa[0],sa[-1],sa[:,0],sa[:,-1]])
    checks.append({'direction':label,'rgba':im.mode,'shadow_rgba':shadow_image.mode,'transparent_border_max_alpha':int(edge.max()),'shadow_border_max_alpha':int(shadow_edge.max()),'body_bounds_384':[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())],'anchor_192':anchor,'body_sha256':sha(path),'shadow_sha256':sha(shadow)})
assert len({x['body_sha256'] for x in checks})==8
grid(frames,4,192,224).save(OUT/'osiem-kierunkow-1x.png')
grid([(Image.open(OUT/f'native/bohater_{label}.png'),label) for label in DIRS],8,192,224).save(OUT/'osiem-kierunkow-ciemne-1x.png')
# Porównanie diagnostyczne: osobne kadry, bez sugerowania skali świata konceptu.
ref=world.convert('RGB');crops=[(0,0,550,462),(550,0,1005,462),(1005,0,1536,462)];sheet=Image.new('RGB',(1536,1112),(24,29,32));draw=ImageDraw.Draw(sheet)
for i,(d,label) in enumerate([(0,'PRZÓD'),(4,'TYŁ'),(2,'BOK')]):
    im=ImageOps.contain(ref.crop(crops[i]),(512,462));sheet.paste(im,(i*512+(512-im.width)//2,35));draw.text((i*512+10,8),'Koncept 17 / '+label,font=font,fill='white')
    path=OUT/f'model/model_{d}.png';audit=json.loads((OUT/'model/audit.json').read_text());assert audit['source_blend_sha256']==source_sha
    im=ImageOps.contain(background(Image.open(path)),(512,512));sheet.paste(im,(i*512,535));draw.text((i*512+10,506),'v2 / materiały tymczasowe',font=font,fill='white')
draw.text((12,1060),'Ilustracja koncepcyjna, nie scena gry. Kadry diagnostyczne dopasowane do planszy; skala gry jest osobno w 1×.',font=small,fill='white');sheet.save(OUT/'koncept17-model.png')
portrait_audit=json.loads((OUT/'portrait19/audit.json').read_text());assert portrait_audit['source_blend_sha256']==source_sha
head=Image.new('RGB',(1536,816),(24,29,32));head.paste(Image.open(REPO/'docs/koncepty/19-bohater-twarz.jpg').convert('RGB').resize((768,768),Image.Resampling.LANCZOS),(0,32));head.paste(background(Image.open(OUT/'portrait19/portrait_0.png')),(768,32));d=ImageDraw.Draw(head);d.text((10,6),'Koncept 19 / wymagania pisemne nadrzędne',font=font,fill='white');d.text((780,6),'v2 / skóra v3 / tęczówka tymczasowa, oczekiwane v4',font=font,fill='white');head.save(OUT/'koncept19-portret.png')
p1=ROOT/'handoff/p1';p1audit=json.loads((p1/'audit.json').read_text());assert p1audit['source_blend_sha256']==source_sha
grid([(Image.open(p1/f'p1_{d}.png').resize((384,384),Image.Resampling.LANCZOS),label) for d,label in [(0,'Przód / natywne UV'),(2,'Bok / natywne UV'),(1,'3/4 / natywne UV')]],3,384,416).save(OUT/'p1-cialo-uv.png')
posemanifest=json.loads((p1/'poses/manifest.json').read_text());assert posemanifest['source_blend_sha256']==source_sha
grid([(Image.open(p1/'poses'/p['image']),p['pose']) for p in posemanifest['poses']],3,512,544).save(OUT/'p1-szesc-poz.png')
# P1 manifest zbiera bieżące źródło, obrazy i faktyczny pomiar UV.
(p1/'manifest.json').write_text(json.dumps({'source_blend_sha256':source_sha,'body_validation':json.loads((p1/'body-validation.json').read_text()),'views':p1audit,'poses_manifest_sha256':sha(p1/'poses/manifest.json'),'files':{str(p.relative_to(p1)):sha(p) for p in p1.rglob('*') if p.is_file() and p.name!='manifest.json'}},ensure_ascii=False,indent=2)+'\n')
allpairs=json.loads((OUT/'intersections-all.json').read_text());bad=json.loads((OUT/'intersections.json').read_text());assert not bad
allow=[{'a':p['a'],'b':p['b'],'triangles':p['triangles'],'reason':'Oko celowo osadzone pod powieką.' if 'Oko /' in p['a']+p['b'] else 'Metalowa głowica celowo osadzona na końcu rękojeści.'} for p in allpairs];assert all('Oko /' in p['a']+p['b'] or {p['a'],p['b']}=={'glowica','rekojesc'} for p in allpairs)
report={'source_blend_sha256':source_sha,'frame':1,'action':None,'checker':'tools/art/check_intersections.py','checker_sha256':sha(REPO/'tools/art/check_intersections.py'),'raw_pairs':len(allpairs),'raw_triangle_pairs':sum(p['triangles'] for p in allpairs),'allow':allow,'unallowed_pairs':0,'unallowed_triangle_pairs':0,'scope':'Wszystkie renderowane MESH po modyfikatorach w statycznej klatce 1. Bez Curves, samoprzenikań jednej siatki, testu zawierania i ruchu.'}
(OUT/'intersection-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');(OUT/'frame-validation.json').write_text(json.dumps({'source_blend_sha256':source_sha,'frames':checks,'different_directions':8,'frame_size_preview':[192,192],'pixels_per_meter':60,'sprite_scale_changed':False,'forest_background':'Niezmieniony wycinek konceptu 17, bez pewnej skali świata. Przyjęto 60 px/m dla postaci, nie powiększano jej względem wycinka. Ilustracja, nie scena gry.'},ensure_ascii=False,indent=2)+'\n')
html='''<!doctype html><html lang="pl"><meta charset="utf-8"><title>Welesza — v2 F0–F3</title><style>body{background:#181d20;color:#ddd;font:17px system-ui;margin:24px}img{max-width:100%;height:auto}a{color:#a9c7dc}p{max-width:1000px}</style><h1>Bohater v2 — F0–F3, do oceny</h1><p>Pełne ciało MakeHuman z natywnym UV, rig 163 kości, głowa według 19 i skóra v3. Strój ma materiały tymczasowe. Oczy szarozielone oczekują v4. Bez animacji i atlasów przed B2.</p><p><a href="../../source/bohater_v2.blend">Model .blend</a> · <a href="../../HANDOFF.md">HANDOFF</a> · <a href="../../handoff/p2/manifest.json">P2 — manifest</a> · <a href="../../V2_REVIEW.md">Raport</a></p>'''
for file,title in [('osiem-kierunkow-1x.png','Osiem kierunków 1× na wycinku ilustracji koncepcyjnej'),('koncept17-model.png','Koncept 17 i model, materiały tymczasowe'),('koncept19-portret.png','Głowa według konceptu 19; portret źródłowy 768'),('p1-cialo-uv.png','P1 — natywne UV'),('p1-szesc-poz.png','P1 — sześć osobnych póz diagnostycznych')]:html+=f'<h2>{title}</h2><p><a href="{file}">Otwórz planszę</a></p><img src="{file}" alt="{title}">'
html+='<p>Koncepty są ilustracjami, nie działającą sceną gry. Plansze diagnostyczne nie zmieniają kontraktu. Pomiar przenikań nie obejmuje Curves ani wnętrza pojedynczej siatki. Wymagana ocena B1/B2 autora.</p></html>'
(OUT/'index.html').write_text(html);assert sha(source)==source_sha;print('V2_STATIC_REVIEW_READY',source_sha)
