"""Porównania kontrolowanego checkpointu z bieżącym eksportem, bez zmiany skali."""
import json,math,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT.parents[2];OUT=ROOT/'previews';OUT.mkdir(exist_ok=True)
DIRS=['S','SW','W','NW','N','NE','E','SE'];ANCHOR=(96,158.35382907248);BG=(28,35,37,255);SPEED=.52/(.6*.96)

def cell(which,anim,d,f,cast=False):
 prefix=ROOT/('baseline/atlas' if which=='before' else 'atlas')
 p=prefix/f'bohater_{anim}{"_shadow" if cast else ""}.png'
 with Image.open(p) as im:return im.crop((f*192,d*192,(f+1)*192,(d+1)*192)).convert('RGBA')

def composite(which,anim,d,f,bg=None):
 im=bg.copy().convert('RGBA') if bg is not None else Image.new('RGBA',(192,192),BG)
 im.alpha_composite(cell(which,anim,d,f,True));im.alpha_composite(cell(which,anim,d,f));return im

def animation(path,sequence,duration):
 sequence=[im.convert('RGB') for im in sequence]
 sequence[0].save(path,save_all=True,append_images=sequence[1:],duration=duration,loop=0,disposal=2)
 with Image.open(path) as im:
  assert im.n_frames==len(sequence),(path,im.n_frames,len(sequence))
  for i in range(im.n_frames):im.seek(i);assert im.info['duration']==duration

# Pairs are always 192px + 192px, in the original game contract.
im=Image.new('RGBA',(1536,384),BG);draw=ImageDraw.Draw(im)
for d,label in enumerate(DIRS):
 for k,which in enumerate(['before','after']):
  x=d%4*384+k*192;y=d//4*192;im.alpha_composite(composite(which,'spoczynek',d,0),(x,y));draw.text((x+6,y+6),label+' / '+('PRZED' if k==0 else 'PO')+' / 1:1',fill='white')
im.convert('RGB').save(OUT/'porownanie-kierunki-1x.png')
old=Image.open(ROOT/'baseline/previews/osiem-kierunkow-render-384.png');new=Image.open(OUT/'osiem-kierunkow-render-384.png')
im=Image.new('RGB',(1536,1536),BG[:3]);draw=ImageDraw.Draw(im)
for d,label in enumerate(DIRS):
 for k,source in enumerate([old,new]):
  tile=source.crop((d%4*384,d//4*384,(d%4+1)*384,(d//4+1)*384));x=d%2*768+k*384;y=d//2*384;im.paste(tile,(x,y));draw.text((x+8,y+25),('PRZED' if k==0 else 'PO')+' / ten sam kadr 384',fill='white')
im.save(OUT/'porownanie-render384.png')
for anim,count,ms in [('spoczynek',8,400),('chod',12,80)]:
 sequence=[]
 for f in range(count):
  im=Image.new('RGBA',(1536,384),BG);draw=ImageDraw.Draw(im)
  for d,label in enumerate(DIRS):
   for k,which in enumerate(['before','after']):
    x=d%4*384+k*192;y=d//4*192;im.alpha_composite(composite(which,anim,d,f),(x,y));draw.text((x+6,y+6),f'{label} / {which} / {f}',fill='white')
  sequence.append(im)
 animation(OUT/f'porownanie-{anim}-1x.gif',sequence,ms)
# Same physical world speed, projected along every facing direction.
sequence=[]
for f in range(12):
 im=Image.new('RGBA',(768,432),BG)
 for d,label in enumerate(DIRS):
  tile=Image.new('RGBA',(192,216),BG);draw=ImageDraw.Draw(tile);theta=-d*math.pi/4;wx=-SPEED*.08*f*math.cos(theta);wy=-SPEED*.08*f*math.sin(theta)
  def project(x,y):return (96+60*(y+wy),166.353829+30*(x+wx))
  for t in np.arange(-5,5,.5):
   draw.line((*project(-5,t),*project(5,t)),fill=(52,63,64),width=1);draw.line((*project(t,-5),*project(t,5)),fill=(52,63,64),width=1)
  tile.alpha_composite(cell('after','chod',d,f,True),(0,8));tile.alpha_composite(cell('after','chod',d,f),(0,8));draw.text((6,6),f'{label} / 1:1 / {SPEED:.3f} m/s',fill='white');im.alpha_composite(tile,(d%4*192,d//4*216))
 sequence.append(im)
animation(OUT/'chod-podloze-8-kierunkow-1x.gif',sequence,80)
# A varied background comes directly from concept 17, without rescaling.
ref=Image.open(REPO/'docs/koncepty/17-bohater-i-woz.jpg').convert('RGBA');varied=ref.crop((370,680,562,872));sequence=[]
for f in range(12):
 im=Image.new('RGBA',(768,384),BG);draw=ImageDraw.Draw(im)
 for row,bg in enumerate([None,varied]):
  for col,(d,which) in enumerate([(4,'before'),(4,'after'),(3,'before'),(3,'after')]):
   im.alpha_composite(composite(which,'chod',d,f,bg),(col*192,row*192));draw.text((col*192+5,row*192+5),f'{DIRS[d]} / {which} / {f:02}',fill='white')
 sequence.append(im)
animation(OUT/'bron-N-NW-1x.gif',sequence,80)
# Concept composition: same anchor and sprite dimensions before/after. Scale of
# the illustration is unknown; assume 60px/m near the chosen trail position.
worlds={}
for which in ['before','after']:
 world=ref.copy();pos=(round(590-ANCHOR[0]),round(810-ANCHOR[1]));world.alpha_composite(cell(which,'spoczynek',1,0,True),pos);world.alpha_composite(cell(which,'spoczynek',1,0),pos)
 ImageDraw.Draw(world).text((24,480),'ILUSTRACJA KONCEPCYJNA 17 / nie jest scena gry / sprite 1:1 / '+which,fill='white')
 world.convert('RGB').save(OUT/f'koncept17-{which}-1x.png');worlds[which]=world.crop((398,570,782,954))
im=Image.new('RGB',(768,384));im.paste(worlds['before'],(0,0));im.paste(worlds['after'],(384,0));ImageDraw.Draw(im).text((8,8),'PRZED / koncept 17 / 1:1',fill='white');ImageDraw.Draw(im).text((392,8),'PO / koncept 17 / 1:1',fill='white');im.save(OUT/'koncept17-porownanie-1x.png')
# Optional source-size comparisons are crops of ACTUAL 1152 px renders.
if (ROOT/'renders/details/after/spoczynek_3_00.png').exists():
 im=Image.new('RGBA',(1024,1472),BG);draw=ImageDraw.Draw(im)
 for row,d in enumerate([1,3]):
  for col,which in enumerate(['before','after']):
   source=Image.open(ROOT/f'renders/details/{which}/spoczynek_{d}_00.png').convert('RGBA');tile=source.crop((320,280,832,1016));im.alpha_composite(tile,(col*512,row*736));draw.text((col*512+8,row*736+8),f'{DIRS[d]} / {which} / render 1152, wycinek 1:1',fill='white')
 im.convert('RGB').save(OUT/'model-zrodlowy-przed-po.png')
# Lighting tests and sheathed option remain outside the base atlases.
from export_player import native,shadow
im=Image.new('RGBA',(1536,576),BG);draw=ImageDraw.Draw(im)
for row,lighting in enumerate(['base','cool','warm']):
 for d,label in enumerate(DIRS):
  folder=ROOT/'renders' if lighting=='base' else ROOT/'renders'/lighting;p=folder/f'spoczynek_{d}_00.png'
  if not p.exists():continue
  tile=Image.new('RGBA',(192,192),BG);tile.alpha_composite(shadow(folder/'shadows'/p.name));tile.alpha_composite(native(p));im.alpha_composite(tile,(d*192,row*192));draw.text((d*192+6,row*192+6),label+' / '+lighting+' / 1:1',fill='white')
im.convert('RGB').save(OUT/'materialy-swiatlo-8-kierunkow-1x.png')
if (ROOT/'renders/sheathed/spoczynek_0_00.png').exists():
 im=Image.new('RGBA',(1536,384),BG);draw=ImageDraw.Draw(im)
 for d,label in enumerate(DIRS):
  im.alpha_composite(composite('after','spoczynek',d,0),(d%4*384,d//4*192))
  folder=ROOT/'renders/sheathed';p=folder/f'spoczynek_{d}_00.png';tile=Image.new('RGBA',(192,192),BG);tile.alpha_composite(shadow(folder/'shadows'/p.name));tile.alpha_composite(native(p));im.alpha_composite(tile,(d%4*384+192,d//4*192))
  draw.text((d%4*384+5,d//4*192+6),label+' / dobyty',fill='white');draw.text((d%4*384+197,d//4*192+6),label+' / pochwa, propozycja',fill='white')
 im.convert('RGB').save(OUT/'bron-dobyta-pochwa-1x.png')
# Atlas consistency verifies every cell, including the compatibility adapter.
checks=0
for anim,n in [('spoczynek',8),('chod',12)]:
 compat=Image.open(ROOT/f'atlas/compat/bohater_{anim}.png').convert('RGBA')
 for d in range(8):
  for f in range(n):
   c=cell('after',anim,d,f,True);c.alpha_composite(cell('after',anim,d,f));expected=compat.crop((f*192,d*192,(f+1)*192,(d+1)*192));assert np.array_equal(np.array(c),np.array(expected));checks+=1
report={'native_comparison_frames':160,'compat_cells_verified':checks,'baseline_commit':json.loads((ROOT/'baseline/checkpoint.json').read_text())['commit'],'same_camera_exposure_scale':True,'world_background':'concept illustration 17, not a playable scene','background_scale_assumption':'60 px/m near anchor (590,810); image has no calibrated world scale; sprite not enlarged','moving_ground_mps':SPEED,'material_maps':'UV metric 0.32 m repeat; scalar height bump, tangent normal files unused to avoid double relief','visual_limits':['No claim of production acceptance','Microdetail largely disappears at 192px','Sheathed option only a preview; hand pose not a finished exploration animation']}
(OUT/'comparison-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
# Interactive preview reads atlases directly at 1:1 and retains per-animation timing.
html='''<!doctype html><html lang="pl"><meta charset="utf-8"><title>Welesza — przegląd bohatera</title><style>body{background:#1c2325;color:#ddd;font:15px system-ui;margin:20px}canvas{width:768px;height:432px}section{display:flex;gap:16px}label{margin-right:20px}button,select,input{margin:8px}small{display:block;max-width:1000px}</style><h1>Bohater — prototyp do oceny</h1><p>Przed: a0a6c27. Po: dopracowanie tego samego modelu. Klatki 192×192, 60 px/m. Osiem kierunków, bez powiększania.</p><label>Animacja <select id="anim"><option value="chod">Chód</option><option value="spoczynek">Spoczynek</option></select></label><button id="play">Pauza</button><label>Klatka <input id="frame" type="range" min="0" max="11" value="0"></label><span id="info"></span><section><div><p>PRZED</p><canvas id="before" width="768" height="432"></canvas></div><div><p>PO</p><canvas id="after" width="768" height="432"></canvas></div></section><small>Podłoże przesuwa się z prędkością 0,902778 m/s, cykl chodu 0,96 s. W spoczynku pozostaje nieruchome. To podgląd assetu, nie działająca scena gry. Decyzja o dobytej broni w eksploracji pozostaje otwarta.</small><p><a href="porownanie-kierunki-1x.png">Kierunki 1:1</a> · <a href="model-zrodlowy-przed-po.png">Model źródłowy przed/po</a> · <a href="bron-N-NW-1x.gif">Broń N/NW w ruchu</a> · <a href="bron-dobyta-pochwa-1x.png">Dobyty / pochwa</a> · <a href="materialy-swiatlo-8-kierunkow-1x.png">Światło bazowe / chłodne / ciepłe</a> · <a href="../REPORT.md">Raport i ograniczenia</a></p><script>
const labels=['S','SW','W','NW','N','NE','E','SE'],imgs={},canvases=['before','after'],slider=document.getElementById('frame'),select=document.getElementById('anim');let frame=0,playing=true,then=0;
const promises=[];for(const which of canvases)for(const anim of ['chod','spoczynek'])for(const shadow of [false,true]){const key=[which,anim,shadow].join('/'),im=new Image();imgs[key]=im;promises.push(new Promise(r=>{im.onload=r;im.src=(which==='before'?'../baseline/atlas/':'../atlas/')+'bohater_'+anim+(shadow?'_shadow':'')+'.png'}));}
function draw(){const anim=select.value;for(const which of canvases){const ctx=document.getElementById(which).getContext('2d');ctx.fillStyle='#1c2325';ctx.fillRect(0,0,768,432);for(let d=0;d<8;d++){let x=d%4*192,y=Math.floor(d/4)*216,theta=-d*Math.PI/4,t=anim==='chod'?frame*.08:0,wx=-.9027777778*t*Math.cos(theta),wy=-.9027777778*t*Math.sin(theta);ctx.save();ctx.beginPath();ctx.rect(x,y,192,216);ctx.clip();ctx.strokeStyle='#343f40';const p=(a,b)=>[x+96+60*(b+wy),y+166.353829+30*(a+wx)];for(let a=-5;a<5;a+=.5){for(const ends of [[p(-5,a),p(5,a)],[p(a,-5),p(a,5)]]){ctx.beginPath();ctx.moveTo(...ends[0]);ctx.lineTo(...ends[1]);ctx.stroke()}}for(const shadow of [true,false])ctx.drawImage(imgs[[which,anim,shadow].join('/')],frame*192,d*192,192,192,x,y+8,192,192);ctx.fillStyle='#ddd';ctx.font='12px system-ui';ctx.fillText(labels[d]+' / 1:1',x+6,y+14);ctx.restore()}}document.getElementById('info').textContent=frame+' / '+(select.value==='chod'?'80 ms':'400 ms');slider.value=frame}
select.onchange=()=>{frame=0;slider.max=select.value==='chod'?11:7;draw()};slider.oninput=()=>{frame=+slider.value;draw()};document.getElementById('play').onclick=()=>{playing=!playing;document.getElementById('play').textContent=playing?'Pauza':'Odtwórz'};Promise.all(promises).then(()=>{draw();function tick(now){const ms=select.value==='chod'?80:400;if(playing&&now-then>=ms){frame=(frame+1)%(select.value==='chod'?12:8);then=now;draw()}requestAnimationFrame(tick)}requestAnimationFrame(tick)});
</script></html>'''
(OUT/'review.html').write_text(html)
paths=[p for folder in ['atlas','renders','previews'] for p in (ROOT/folder).rglob('*') if p.is_file() and p.name!='checksums.json']
(OUT/'checksums.json').write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)},indent=2)+'\n')
print('PASS: before/after 160 native frames; decoded GIF timing; 160 compatibility cells; 8-direction moving ground.')
