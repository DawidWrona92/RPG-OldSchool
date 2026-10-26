#!/usr/bin/env python3
import os,sys,hashlib,json,tempfile
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'retro-rts-sprites/scripts'))
sys.path.insert(0,str(ROOT/'rpg-godot-pipeline/scripts'))
from pixelcraft import ramp,stats,frame_checks,make_atlas,analyze_reference,clean_import
from verify_atlas import validate
p=ROOT/'demo/arpg/output'
n=0
def test(title,ok):
 global n
 assert ok,title
 n+=1;print('[PASS]',title)

r=ramp('#765047',5)
test('hue-shifted 5-color ramp',len(set(r))==5 and r[0]!=r[-1])
im=Image.open(p/'knight.png').convert('RGBA')
test('knight has compact palette and opaque pixels',stats(im)['colors']<=24 and stats(im)['opaque']>0)
test('stats counts clipped pixels on boundary',stats(Image.new('RGBA',(4,4),(255,0,0,255)))['edge_touch']==12)
frames=[im.copy() for _ in range(8)]
a=frame_checks(frames,[(48,104)]*8,8,1)
test('duplicate 8-direction frames fail',not a['ok'] and any('directions 1/2' in x for x in a['errors']))
a=frame_checks(frames,[(48,104)]*7+[(49,104)],8,1)
test('anchor drift fails',not a['ok'] and any('anchor drifts' in x for x in a['errors']))
test('clip fails',not frame_checks([Image.new('RGBA',(4,4),(255,0,0,255))]*8,[(2,2)]*8,8,1)['ok'])
for who in ('dark_knight','skeleton'):
  name=who+'_walk_8dir'
  a=validate(str(p/(name+'.png')),str(p/(name+'.json')))
  test(who+' Godot 8 dirs/4 frames, no clipping',a['ok'] and len(a['directions'])==8 and all(v==4 for v in a['directions'].values()))
for k in ('crypt','tree','altar'):
  img=Image.open(p/(k+'.png'))
  s=stats(img)
  test(k+' asset valid PNG with visible alpha and no clipping',s['opaque']>100 and s['edge_touch']==0)
with tempfile.TemporaryDirectory() as d:
  dest=Path(d)/'out.png'
  info=clean_import(str(p/'knight.png'),str(dest),max_colors=12)
  test('intentional cleanup creates valid palette-locked output',dest.exists() and info['after']['colors']<=12)
  card=analyze_reference(str(p/'knight.png'))
  test('style analyzer measures palette and reports limitation',card['colors']>4 and bool(card['style_card_template']))
for backend in ('retro-rts-sprites/scripts/spritekit.js','painted-rts-sprites/scripts/painter.js','rts-prerender-3d/scripts/rtcore.js'):
  test('original JS backend retained: '+backend,(ROOT/backend).is_file())
print('Passed:',n)
