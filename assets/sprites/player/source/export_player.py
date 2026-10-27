"""Złóż rzeczywiste rendery Cycles w atlasy, podglądy i raport techniczny.

python3 -B assets/sprites/player/source/export_player.py
Nie uruchamia Blendera i nie zastępuje brakujących klatek kopiami.
"""
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[2]
DIRECTIONS=['S','SW','W','NW','N','NE','E','SE']
ANCHOR=[96.0,158.35382907247958]
BACKGROUND=(35,41,31,255)
COUNTS={'spoczynek':8,'chod':12}
DURATIONS={'spoczynek':400,'chod':80}
SPEED=.52/(.6*.96)


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):return json.loads(path.read_text())


def save_json(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')


def native(path):
    with Image.open(path) as image:
        assert image.mode=='RGBA' and image.size==(384,384),(str(path),image.mode,image.size)
        # Filtering in premultiplied alpha avoids dark fringes on pale cloth.
        return image.convert('RGBa').resize((192,192),Image.Resampling.LANCZOS).convert('RGBA')


def shadow(path):
    image=native(path)
    alpha=image.getchannel('A').filter(ImageFilter.GaussianBlur(.8))
    # Shadow catcher Monte Carlo noise has a small positive floor after taking
    # 1 - transmittance. Remove that floor, without substituting painted shadows.
    a=np.array(alpha).astype(float)
    a=np.maximum(0,a-12)*255/243
    # The 192 px contract has only 34 px below the anchor. Keep a contact
    # shadow patch with a smooth, documented world-space fade; the raw Cycles
    # shadow renders retain the longer fill-light tails for inspection.
    yy,xx=np.mgrid[:192,:192]
    radius=np.sqrt(((xx-ANCHOR[0])/60)**2+((yy-ANCHOR[1])/30)**2)
    t=np.clip((radius-.75)/.30,0,1)
    a*=1-(t*t*(3-2*t))
    result=Image.new('RGBA',(192,192),(0,0,0,0))
    result.putalpha(Image.fromarray(np.clip(a,0,255).astype(np.uint8)))
    return result


def on_background(body,cast_shadow=None):
    out=Image.new('RGBA',body.size,BACKGROUND)
    if cast_shadow:out.alpha_composite(cast_shadow)
    out.alpha_composite(body)
    return out


def make_previews(frames,shadows):
    previews=ROOT/'previews';previews.mkdir(exist_ok=True)
    directions=Image.new('RGB',(768,384),BACKGROUND[:3])
    for d,label in enumerate(DIRECTIONS):
        im=on_background(frames['spoczynek'][d][0],shadows['spoczynek'][d][0])
        directions.paste(im,(d%4*192,d//4*192))
        ImageDraw.Draw(directions).text((d%4*192+10,d//4*192+10),label+' / 1:1',fill=(215,210,190))
    directions.save(previews/'osiem-kierunkow-1x.png')
    high=Image.new('RGB',(384*4,384*2),BACKGROUND[:3])
    for d,label in enumerate(DIRECTIONS):
        with Image.open(ROOT/'renders'/f'spoczynek_{d}_00.png') as im:
            high.paste(im,(d%4*384,d//4*384),im)
        ImageDraw.Draw(high).text((d%4*384+10,d//4*384+10),label+' / render 384 px',fill=(215,210,190))
    high.save(previews/'osiem-kierunkow-render-384.png')
    for anim,count in COUNTS.items():
        sequence=[]
        for f in range(count):
            strip=Image.new('RGBA',(192*8,192),BACKGROUND)
            draw=ImageDraw.Draw(strip)
            for d,label in enumerate(DIRECTIONS):
                im=on_background(frames[anim][d][f],shadows[anim][d][f])
                strip.alpha_composite(im,(d*192,0))
                draw.text((d*192+8,8),label+' / 1:1',fill=(215,210,190,255))
            sequence.append(strip.convert('RGB'))
        sequence[0].save(previews/f'bohater_{anim}.gif',save_all=True,append_images=sequence[1:],
                         duration=[DURATIONS[anim]]*count,loop=0,disposal=2)
        sequence[0].save(previews/f'bohater_{anim}.webp',save_all=True,append_images=sequence[1:],
                         duration=DURATIONS[anim],loop=0,lossless=True)
    # A moving ground grid makes incorrect root speed / planted-foot drift
    # visible; the character remains at the same export anchor.
    sequence=[]
    for f in range(12):
        im=Image.new('RGBA',(384,220),BACKGROUND);draw=ImageDraw.Draw(im)
        shift=-SPEED*.08*f*60
        for x in np.arange(-300,700,30):
            draw.line((x+shift,174,x+shift+100,124),fill=(71,75,58),width=1)
        body=frames['chod'][2][f];cast=shadows['chod'][2][f]
        im.alpha_composite(cast,(96,10));im.alpha_composite(body,(96,10))
        draw.text((10,8),f'W / 1:1 / {SPEED:.3f} m/s / klatka {f}',fill=(215,210,190))
        sequence.append(im.convert('RGB'))
    sequence[0].save(previews/'chod-kontakt-stop.gif',save_all=True,append_images=sequence[1:],duration=80,loop=0,disposal=2)
    # The reference stays at its original pixel size. No cleanup or repainting
    # of its existing character, terrain, buildings or lights is performed.
    reference=REPO/'docs/koncepty/12-scena-postac-z-porozem-i-toporem.jpg'
    world=Image.open(reference).convert('RGBA')
    draw=ImageDraw.Draw(world)
    positions=[((650,655),'base','ziemia / światło bazowe'),
               ((925,640),'cool','chłodny wariant'),((1210,760),'warm','lokalna pochodnia')]
    variants=[]
    for (x,y),variant,label in positions:
        if variant=='base':
            body=frames['spoczynek'][1][0];cast=shadows['spoczynek'][1][0]
        else:
            path=ROOT/'renders'/variant/'spoczynek_1_00.png'
            if not path.exists():continue
            body=native(path);cast=shadow(path.parent/'shadows'/path.name)
        position=(round(x-ANCHOR[0]),round(y-ANCHOR[1]))
        world.alpha_composite(cast,position);world.alpha_composite(body,position)
        draw.text((x-65,y+9),label,fill=(220,212,190,255))
        # This is a native-resolution crop, without enlargement.
        crop=world.crop((x-140,y-170,x+140,y+45))
        crop.save(previews/f'swiat-{variant}-1x.png')
        variants.append(variant)
    world.convert('RGB').save(previews/'bohater-w-swiecie-1x.png')
    return variants


def main():
    audit=read_json(ROOT/'renders/motion_audit.json')
    generator=ROOT/'source/build_player.py'
    assert audit['generator_sha256']==sha(generator),'Rendery nie odpowiadają obecnemu generatorowi'
    expected={f'{a}_{d}_{f:02}.png' for a,n in COUNTS.items() for d in range(8) for f in range(n)}
    assert set(audit['frames'])==expected,('Brakujące/nadmiarowe klatki',expected-set(audit['frames']))
    atlas_dir=ROOT/'atlas';atlas_dir.mkdir(exist_ok=True)
    compat=atlas_dir/'compat';compat.mkdir(exist_ok=True)
    meta={'character':'bohater','frame_size':[192,192],'anchor_px':ANCHOR,'pixels_per_meter':60.0,
          'directions':DIRECTIONS,'direction_note':'Oddzielne rendery obrotu modelu o -45°; bez lustrzanych odbić',
          'layout':'kolumny = klatki animacji, wiersze = kierunki','camera_elevation_deg':30,
          'animations':{},'status':'eksperyment do oceny autora; niezatwierdzony asset produkcyjny'}
    frames={};shadows={};bboxes={};checks=0
    for anim,count in COUNTS.items():
        frames[anim]=[];shadows[anim]=[]
        body_atlas=Image.new('RGBA',(count*192,8*192))
        shadow_atlas=Image.new('RGBA',body_atlas.size)
        combined=Image.new('RGBA',body_atlas.size)
        for d in range(8):
            bodyrow=[];shadowrow=[]
            for f in range(count):
                file=f'{anim}_{d}_{f:02}.png';source=ROOT/'renders'/file
                info=audit['frames'][file]
                assert sha(source)==info['image_sha256'],('Suma renderu',file)
                assert sha(ROOT/'renders/shadows'/file)==info['shadow_sha256'],('Suma cienia',file)
                body=native(source);cast=shadow(ROOT/'renders/shadows'/file)
                alpha=np.array(body)[:,:,3]
                assert max(alpha[0].max(),alpha[-1].max(),alpha[:,0].max(),alpha[:,-1].max())==0,('Ucięta postać',file)
                cast_alpha=np.array(cast)[:,:,3]
                assert max(cast_alpha[0].max(),cast_alpha[-1].max(),cast_alpha[:,0].max(),cast_alpha[:,-1].max())==0,('Granica cienia',file)
                bbox=body.getchannel('A').point(lambda x:255 if x>=8 else 0).getbbox()
                assert bbox and bbox[0]>1 and bbox[1]>1 and bbox[2]<191 and bbox[3]<191,('Margines',file,bbox)
                info=audit['frames'][file]
                assert info['max_joint_gap_m']<.0001 and info['max_bone_length_error_m']<.0001,('Szkielet',file)
                position=(f*192,d*192)
                body_atlas.paste(body,position);shadow_atlas.paste(cast,position)
                c=cast.copy();c.alpha_composite(body);combined.paste(c,position)
                bodyrow.append(body);shadowrow.append(cast);bboxes[file]=bbox;checks+=1
            frames[anim].append(bodyrow);shadows[anim].append(shadowrow)
        body_atlas.save(atlas_dir/f'bohater_{anim}.png')
        shadow_atlas.save(atlas_dir/f'bohater_{anim}_shadow.png')
        combined.save(compat/f'bohater_{anim}.png')
        data={'file':f'bohater_{anim}.png','shadow_file':f'bohater_{anim}_shadow.png',
              'frames':count,'durations_ms':[DURATIONS[anim]]*count,'loop':True,'events':{}}
        if anim=='chod':data['root_speed_mps']=SPEED
        meta['animations'][anim]=data
    # Independent checks of the contact trajectory in world units.
    drift=[];contacts=[]
    for side in ['L','R']:
        for f in range(11):
            a=audit['frames'][f'chod_0_{f:02}.png']['feet'][side]
            b=audit['frames'][f'chod_0_{f+1:02}.png']['feet'][side]
            if a['stance'] and b['stance'] and b['ankle_m'][0]<a['ankle_m'][0]:
                drift.append(abs(b['ankle_m'][0]-a['ankle_m'][0]+SPEED*.08))
            if a['stance']:contacts.append(abs(a['ankle_m'][2]-.0778))
    assert len(drift)>5 and max(drift)<.00001,('Dryf stopy',drift)
    assert max(contacts)<.00001,('Wysokość podparcia',contacts)
    fingerprints=[hashlib.sha256(frames['spoczynek'][d][0].tobytes()).hexdigest() for d in range(8)]
    assert len(set(fingerprints))==8,'Powtórzony kierunek'
    save_json(atlas_dir/'bohater.json',meta)
    legacy=json.loads(json.dumps(meta))
    for anim in legacy['animations'].values():anim.pop('shadow_file',None)
    save_json(compat/'bohater.json',legacy)
    variants=make_previews(frames,shadows)
    report={'checked_frames':checks,'animations':COUNTS,'source_generator_sha256':sha(generator),
            'render':audit['render'],'max_joint_gap_m':max(v['max_joint_gap_m'] for v in audit['frames'].values()),
            'max_bone_length_error_m':max(v['max_bone_length_error_m'] for v in audit['frames'].values()),
            'max_stance_root_compensation_error_m':max(drift),'stance_samples_checked':len(drift),
            'frame_bounds':'passed / 160 body frames','body_alpha':'RGBA / transparent edges / premultiplied downsampling',
            'distinct_direction_images':len(set(fingerprints)),'anchor_px':ANCHOR,'world_lighting_variants':variants,
            'shadow_processing':'Cycles shadow catcher, 16 samples, 0.8 px blur, 12/255 noise floor removal, smooth contact-patch fade from 0.75 to 1.05 m',
            'unverified':['artistic acceptance','full garment/body/sword collision detection',
                          'target engine import (engine undecided)','all combat animations','fresh cloud task restoration'],
            'frame_bboxes':bboxes}
    save_json(ROOT/'previews/technical-report.json',report)
    output_paths=[p for folder in ['atlas','renders','previews'] for p in (ROOT/folder).rglob('*') if p.is_file() and p.name!='checksums.json']
    save_json(ROOT/'previews/checksums.json',{str(p.relative_to(ROOT)):sha(p) for p in sorted(output_paths)})
    print(f'PASS: {checks} klatek; 8 kierunków; szkielet; granice; alfa; {len(drift)} próbek podparcia.')
    print(f'Max błąd kompensacji ruchu: {max(drift):.9f} m. Warianty światła: {variants}.')


if __name__=='__main__':main()
