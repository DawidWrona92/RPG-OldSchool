#!/usr/bin/env python3
"""Welesza ENV-01 / leśny skraj — deterministic, reproducible 2.5D asset test.

No external images or source assets. Dependency: Pillow, NumPy, SciPy.
This is a WORLD TEST, not a polished final scene or an approved level map.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import gaussian_filter, map_coordinates

HERE = Path(__file__).resolve().parent
OUT = HERE / 'output'
SEED = 424107
PPM = 60.0
ELEVATION = math.radians(30.0)
ISO_COS = 2 ** -.5
ISO_SIN = math.sin(ELEVATION)*ISO_COS
SCENE_W, SCENE_H = 1536, 900
CX, CY = SCENE_W * 0.52, SCENE_H * .49
GROUND = (35, 41, 31)
COLORS = {'wood':'#423d31','rock':'#62685b','moss':'#454a36','mud':'#3f3931','fog':'#72766f'}


def periodic_noise(size=512, cells=8, rng=None):
    """Band-limited, exactly periodic random field sampled at integer texels."""
    rng = np.random.default_rng(SEED) if rng is None else rng
    grid = rng.normal(0,1,(cells,cells))
    yy,xx = np.meshgrid(np.arange(size)*cells/size,np.arange(size)*cells/size,indexing='ij')
    return map_coordinates(grid,[yy,xx],order=3,mode='grid-wrap').astype(np.float32)


def periodic_fbm(size,seed):
    rng=np.random.default_rng(seed)
    a=np.zeros((size,size),dtype=np.float32)
    for cells,weight in ((4,.59),(12,.30),(42,.11)):
        a+=weight*periodic_noise(size,cells,rng)
    a-=np.mean(a)
    return a/(np.std(a)+1e-6)


def material_set(outdir:Path):
    """Tileable albedo, normal, roughness, height textures in local UV space."""
    outdir.mkdir(parents=True,exist_ok=True)
    mats={
        'forest_floor':{'base':(54,57,41),'tint':(18,23,13),'wet':.28,'rough':.88,'spec':-2,'seed':15},
        'mud':{'base':(61,54,44),'tint':(20,18,13),'wet':.58,'rough':.74,'spec':-4,'seed':22},
        'stone':{'base':(88,94,84),'tint':(28,29,25),'wet':.35,'rough':.78,'spec':-2,'seed':29},
        'moss':{'base':(60,70,42),'tint':(23,24,15),'wet':.22,'rough':.96,'spec':1,'seed':36},
    }
    report={}
    for name,m in mats.items():
        n=periodic_fbm(256,m['seed'])
        n2=periodic_fbm(256,m['seed']+200)
        n3=periodic_fbm(256,m['seed']+331)
        masks=(n2>.48).astype(float)
        rgb=np.stack([m['base'][i]+m['tint'][i]*n*.6+10*masks*n3 for i in range(3)],axis=2)
        # dark wet pores / pebbles are a sub-surface variation, not random static
        damp=(n2<-.4).astype(float)*(6+4*n3.clip(0,1))
        rgb-=damp[:,:,None]*m['wet']*3
        rgb=np.clip(rgb,8,225).astype(np.uint8)
        # Height only encodes microdetail. Tile edges are fixed for exact seamless wrap.
        h=np.clip(.50 + n*.105+n2*.025,.0,1.0)
        gy,gx=np.gradient(h)
        norm=np.stack([-gx*5.5,-gy*5.5,np.ones_like(h)],axis=-1)
        norm/=np.linalg.norm(norm,axis=-1,keepdims=True)
        nm=np.clip((norm*.5+.5)*255,0,255).astype('uint8')
        rough=np.clip((m['rough']+.045*n2-.06*(n3>.7))*255,0,255).astype('uint8')
        for arr in (rgb,nm,rough,h):
            arr[-1,...]=arr[0,...]
            arr[:,-1,...]=arr[:,0,...]
        Image.fromarray(rgb).save(outdir/f'{name}_albedo.png', optimize=True)
        Image.fromarray(nm).save(outdir/f'{name}_normal.png', optimize=True)
        Image.fromarray(rough).save(outdir/f'{name}_roughness.png', optimize=True)
        Image.fromarray((h*255).astype('uint8')).save(outdir/f'{name}_height.png', optimize=True)
        report[name]={'seamless_exact':bool((rgb[0]==rgb[-1]).all() and (rgb[:,0]==rgb[:,-1]).all()),'avg_rgb':[round(float(x),2) for x in rgb.mean(axis=(0,1))]}
    return report


def smooth_grid(seed, shape=(900,1536), gridsize=44):
    rng=np.random.default_rng(seed)
    z=rng.normal(0,1,(max(3,shape[0]//gridsize)+2,max(3,shape[1]//gridsize)+2)).astype(np.float32)
    ys=np.linspace(0,z.shape[0]-1,shape[0],dtype=np.float32)
    xs=np.linspace(0,z.shape[1]-1,shape[1],dtype=np.float32)
    return map_coordinates(z,np.meshgrid(ys,xs,indexing='ij'),order=3,mode='reflect').astype(np.float32)


def screen(x,y,z=0.0):
    return (CX + (x-y)*ISO_COS*PPM, CY+(x+y)*ISO_SIN*PPM-z*math.cos(ELEVATION)*PPM)


def scene_ground():
    yy,xx=np.indices((SCENE_H,SCENE_W),dtype=np.float32)
    a=(xx-CX)/(PPM*ISO_COS)
    b=(yy-CY)/(PPM*ISO_SIN)
    wx=(a+b)*.5; wy=(b-a)*.5
    # The old cart route bends slightly; wheel furrows track the projected road.
    path_y=.37*np.sin(wx*.21)+.20*np.sin(wx*.51+.5)
    side=wy-path_y
    detail=smooth_grid(101,gridsize=32)
    big=smooth_grid(102,gridsize=130)
    tiny=smooth_grid(103,gridsize=5)
    var=smooth_grid(104,gridsize=14)
    width=1.95+0.17*np.sin(wx*.42)+.10*big
    road=np.clip((width+.48-np.abs(side)*.86)/.93,0,1)
    road=road*road*(3-2*road)
    # Mudny wagon clearing near x=5.3, not a perfectly circular arena.
    oval=((wx-4.6)/4.9)**2+((wy+.30)/3.4)**2
    clearing=np.clip((1.35-oval)*1.4,0,1)**2
    dirt=np.maximum(road,clearing*.80)
    forest=np.zeros((*xx.shape,3),dtype=np.float32)
    for i,(v,m) in enumerate(zip((43,49,34),(68,60,45))):
        forest[:,:,i]=v+(detail*8+big*10+tiny*2.8)+dirt*((m-v)+detail*2.5)
    # ground moss islands and leaf litter clustered away from walking space
    moss=(np.clip(var*.28+big*.65+.16,.0,.72))*(1-dirt*.73)
    forest+=np.array([8,14,1],dtype=np.float32)*moss[:,:,None]
    # Wet areas and intermittent thin wagon furrows within road only
    tracks=(np.exp(-((np.abs(side)-.70)/.14)**2))*(road*.85)
    dark=((big<-.15).astype(np.float32)*.40+tracks*.55+road*np.maximum(0,-detail)*.10)
    forest-=np.array([15,13,9],dtype=np.float32)*dark[:,:,None]
    # Puddles shaped from coherent noise; concentrated in depressions and wheel tracks
    puddles=(big+detail*.32<-.55)&(road>.45)&(np.abs(side)>.2)
    puddles2=(tracks>.28)&(big<-.20)&(var<.05)
    wet=puddles|puddles2
    reflections=np.maximum(0,detail+tiny*.18)
    for i,base in enumerate((49,58,55)):
        forest[:,:,i]=np.where(wet,base+reflections*6+(i-1)*3,forest[:,:,i])
    forest+=tiny[:,:,None]*1.5
    rgb=np.clip(forest,8,180).astype('uint8')
    return Image.fromarray(rgb,'RGB').convert('RGBA'),dict(puddles=int(np.count_nonzero(wet)),road_fraction=round(float(np.mean(dirt>.5)),3),clearing_center_world=[4.6,-.3])


def shadow(img, box, width=70,depth=18,opacity=65):
    x,y=box
    lay=Image.new('RGBA',img.size,(0,0,0,0));d=ImageDraw.Draw(lay,'RGBA')
    d.ellipse((x-width,y-depth,x+width,y+depth),fill=(0,0,0,opacity))
    lay=lay.filter(ImageFilter.GaussianBlur(11))
    img.alpha_composite(lay)


def rock_sprite(seed=1, scale=1.0):
    rng=np.random.default_rng(seed)
    size=(310,230); im=Image.new('RGBA',size,(0,0,0,0));d=ImageDraw.Draw(im,'RGBA')
    anchor=(155,192)
    shadow(im,anchor,width=80*scale,depth=20*scale,opacity=78)
    # exposed upper rock top with irregular front-facing facets
    ang=np.linspace(0,2*np.pi,9)[:-1]+rng.normal(0,.18,8)
    rx=70*scale;ry=38*scale
    top=[(anchor[0]+math.cos(t)*rx*rng.uniform(.78,1.13),anchor[1]-47*scale+math.sin(t)*ry*.67) for t in ang]
    bot=[(x+rng.uniform(-8,8)*scale, y+53*scale) for x,y in top]
    sidebase=(58,66,60,255)
    for j in range(8):
        br=int(11+18*max(0,-math.sin(ang[j]))+rng.integers(-4,5))
        c=(sidebase[0]+br,sidebase[1]+br,sidebase[2]+br,255)
        d.polygon([top[j],top[(j+1)%8],bot[(j+1)%8],bot[j]],fill=c)
    d.polygon(top,fill=(100,106,92,255))
    # chipped facets and fissures (tightly constrained to upper surface)
    for j in range(15):
        ox=rng.uniform(-.75,.75)*rx; oy=rng.uniform(-.65,.65)*ry*.65
        pt=(anchor[0]+ox,anchor[1]-47*scale+oy)
        if (ox/rx)**2+(oy/(ry*.7))**2>.75:continue
        c=(48,55,47,200) if j%3==0 else (132,133,113,130)
        d.line([pt,(pt[0]+rng.uniform(4,21)*scale,pt[1]+rng.uniform(-2,8)*scale)],fill=c,width=max(1,int(2*scale)))
    for k in range(27):
        ox=rng.uniform(-.86,.86)*rx;oy=rng.uniform(-.55,.55)*ry*.8
        if (ox/rx)**2+(oy/(ry*.7))**2>.85:continue
        px=anchor[0]+ox;py=anchor[1]-47*scale+oy
        d.ellipse((px-2*scale,py-2*scale,px+2*scale,py+2*scale),fill=(65,85,51,rng.integers(120,220).item()))
    return im,anchor


def log_sprite(seed=11, scale=1.0):
    rng=np.random.default_rng(seed);im=Image.new('RGBA',(360,200),(0,0,0,0));d=ImageDraw.Draw(im,'RGBA')
    a=(180,165); shadow(im,a,99*scale,12*scale,60)
    x0=69;y0=120;x1=280;y1=148;r=22*scale
    points=[(x0,y0-r),(x1,y1-r*.7),(x1,y1+r*.9),(x0,y0+r)]
    d.polygon(points,fill=(65,51,39,255));d.line([points[0],points[1]],fill=(128,99,65,255),width=max(1,int(5*scale)))
    d.ellipse((x1-r*.35,y1-r,x1+r*.45,y1+r*.95),fill=(121,97,68,255),outline=(55,45,34,255),width=4)
    d.arc((x1-r*.24,y1-r*.56,x1+r*.25,y1+r*.52),20,300,fill=(75,55,39,255),width=2)
    for j in range(34):
        t=rng.uniform(.03,.95);bx=x0+(x1-x0)*t;by=y0+(y1-y0)*t
        shift=rng.uniform(-14,14)*scale
        d.line([(bx,by+shift-6*scale),(bx+rng.uniform(5,23)*scale,by+shift)],fill=tuple(int(x) for x in rng.choice([(46,39,31,255),(105,80,57,255),(135,110,72,200)])),width=rng.integers(1,3).item())
    return im,a


def stump_sprite(seed=26,scale=1.0):
    rng=np.random.default_rng(seed);im=Image.new('RGBA',(224,232),(0,0,0,0));d=ImageDraw.Draw(im,'RGBA');a=(112,191)
    shadow(im,a,55*scale,14*scale)
    body=[(76,126),(154,126),(149,191),(88,194)]
    d.polygon(body,fill=(76,54,38,255));d.line(body[:2],fill=(143,111,79,255),width=4)
    for k in range(13):
        xx=rng.uniform(84,148);d.line([(xx,132),(xx+rng.uniform(-9,8),184)],fill=(46,39,31,170),width=rng.integers(1,4).item())
    d.ellipse((74,109,157,142),fill=(140,117,82,255),outline=(55,46,33,255),width=5)
    for j in range(3):d.arc((81+j*6,113+j*3,150-j*7,137-j*3),10,320,fill=(85,69,49,210),width=2)
    return im,a


def bush_sprite(seed=33,scale=1.0):
    rng=np.random.default_rng(seed);im=Image.new('RGBA',(245,225),(0,0,0,0));d=ImageDraw.Draw(im,'RGBA');a=(122,194)
    shadow(im,a,74*scale,17*scale)
    for k in range(100):
        ox=rng.normal(0,38)*scale; oy=rng.normal(-32,20)*scale
        if abs(ox)>100:continue
        r=rng.uniform(9,20)*scale
        b=rng.integers(-16,20)
        col=(max(15,45+b),max(18,61+b),max(9,29+b),rng.integers(175,255).item())
        d.ellipse((a[0]+ox-r,a[1]+oy-r,a[0]+ox+r,a[1]+oy+r),fill=col)
        if k%3==0:
            d.line([(a[0]+ox-7,a[1]+oy-r*.25),(a[0]+ox+3,a[1]+oy-r*.5)],fill=(81,96,51,180),width=1)
    return im,a


def fir_sprite(seed=5, scale=1.0):
    rng=np.random.default_rng(seed);W,H=340,490; im=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(im,'RGBA');a=(170,460)
    shadow(im,a,94*scale,20*scale,100)
    trunk=(170,460);tip=(167,48)
    d.polygon([(161,457),(179,457),(175,58),(165,58)],fill=(62,45,30,255))
    # dark needle clusters in layered boughs, near branches are drawn brighter
    for level in range(12):
        t=level/12;cy=70+t*330
        width=(9+t*117)*scale
        l=rng.uniform(.76,1.17)
        colorbase=(25+int(5*t),39+int(9*t),28+int(4*t))
        p=[(170,cy-33*scale),(170-width*l,cy+31*scale),(170+width*l,cy+29*scale)]
        d.polygon(p,fill=(*colorbase,255))
        # needles 'limbs' as dense short tapered crossing segments
        for k in range(27):
            bx=rng.uniform(-width,width);fy=cy+14*scale-(1-abs(bx)/max(1,width))*36*scale
            r=rng.uniform(2,8)*scale
            shade=int(rng.uniform(-5,18))
            col=(31+shade,47+shade,31+int(shade*.7),rng.integers(150,235).item())
            d.line([(170+bx-r,fy-r),(170+bx+r,fy+r*.4)],fill=col,width=max(1,int(rng.uniform(1,3)*scale)))
    # canopy tip
    d.line([(167,54),(167,102)],fill=(64,75,49,225),width=2)
    return im,a


def place_prop(bg:Image.Image,sprite,anchor,world,scale=1.0):
    im,localAnchor=sprite
    sx,sy=screen(*world)
    sx,sy=int(sx),int(sy)
    # pillow crops outside canvas
    pos=(int(sx-localAnchor[0]),int(sy-localAnchor[1]))
    bg.alpha_composite(im,pos)
    return {'screen_anchor':[sx,sy], 'image_size':list(im.size),'screen_top_left':list(pos)}


def prepare_assets(outdir):
    assetdefs={
       'rock_a':(rock_sprite,11,1.00),'rock_b':(rock_sprite,18,.76),
       'fallen_log':(log_sprite,11,1.0),'stump':(stump_sprite,26,1.0),
       'bush_a':(bush_sprite,42,1.0),'bush_b':(bush_sprite,99,.9),
       'fir_a':(fir_sprite,6,1.),'fir_b':(fir_sprite,13,1.)}
    catalog={}
    for name,(func,seed,scale) in assetdefs.items():
        sprite=func(seed,scale)
        sprite[0].save(outdir/f'{name}.png',optimize=True)
        catalog[name]={'file':f'props/{name}.png','anchor_px':list(sprite[1]),'dimensions_px':list(sprite[0].size),'rough_collision_radius_m': {'fir_a':.46,'fir_b':.46,'stump':.46,'rock_a':.75,'rock_b':.55,'fallen_log':1.4,'bush_a':0,'bush_b':0}[name]}
    return catalog


def make_scene():
    (OUT/'props').mkdir(parents=True,exist_ok=True)
    ground,groundinfo=scene_ground()
    ground.save(OUT/'scene_ground.png',optimize=True)
    matReport=material_set(OUT/'materials')
    catalog=prepare_assets(OUT/'props')
    # Each placement keeps game-space position; renderer orders by projected ground Y.
    # Shared source locations; this is a staging ground, not approved map geometry.
    placements=[
      ('fir_a',-10,-9),('fir_b',-3.0,-11),('fir_a',6,-10),('fir_b',15,-10),
      ('fir_a',-14,-2),('fir_b',-12,5.2),('fir_a',-7,9),('fir_b',-1,11),
      ('fir_b',8.2,10.5),('fir_a',16,6.8),('fir_b',17,0.0),
      ('rock_a',-7,-3.9),('rock_b',-8.6,2.5),('rock_b',-4.5,6.2),
      ('rock_a',2.5,6.5),('rock_a',10.7,-4.9),('rock_b',13.1,4.4),
      ('fallen_log',-7.0,3.1),('stump',12.2,2.8),('stump',-10.3,-5.7),
      ('bush_a',-8.4,6.6),('bush_b',-.9,5.4),('bush_a',9.5,-4.4),
      ('bush_b',-6,-5.7),('bush_a',14.4,5.0),('bush_b',3.6,-6.2),
    ]
    # Composite physically painter-style: ground anchor controls front/back ordering.
    placements.sort(key=lambda q:screen(q[1],q[2])[1])
    props={name:(Image.open(OUT/d['file']).convert('RGBA'),tuple(d['anchor_px'])) for name,d in catalog.items()}
    preview=ground.copy()
    sceneobjects=[]
    for i,(name,x,y) in enumerate(placements):
        loc=place_prop(preview,props[name],props[name][1],(x,y))
        sceneobjects.append({'id':f'prop-{i:03}','type':name,'world_m':[x,y],**loc,'collision_radius_m':catalog[name]['rough_collision_radius_m']})
    # path layout safety: define intended walkable road corridor and clearing; needs real-engine collision test
    manifest={
      'version':1,'prototype':True,'status':'technical study / NOT final art',
      'projection':{'type':'orthographic','camera_elevation_degrees':30,'yaw_degrees':45,'pixels_per_meter':PPM,'screen_center_px':[CX,CY],'formula':'screen_x = cx + (x-y)*cos(45)*ppm; screen_y=cy + (x+y)*sin(45)*sin(30)*ppm - z*cos(30)*ppm'},
      'scene_image':[SCENE_W,SCENE_H],'ground':'scene_ground.png',
      'preview':'scene_preview.png','materials':'materials/','props_catalog':catalog,
      'objects':sceneobjects,
      'walkable_study':{'road_local_center_y':'0.37*sin(0.21*x)+0.20*sin(0.51*x+0.5)','clearing_center_world':[4.6,-.3], 'note':'NO navmesh; avoid placing collision circles over center path'},
      'scope':'Leśny skraj przy wozie: POC-ENV01 ground and scatter only. No wagon, horse, gameplay AI, gate yet.',
      'references':['docs/pakiet-04-mapa.md','docs/pakiet-04-poczatek.md','docs/art/niemir/NIEMIR_ART_DIRECTION.md']
    }
    # Cropped viewport preview with outside-the-world darkening, no fake text/UI overlay
    preview.save(OUT/'scene_preview.png',optimize=True)
    (OUT/'scene.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
    # Optional compositor debug for collision coverage
    debug=preview.copy();dr=ImageDraw.Draw(debug,'RGBA')
    for ob in sceneobjects:
      r=ob['collision_radius_m'];
      if r<=0:continue
      x,y=ob['screen_anchor'];rx=PPM*r;ry=rx*math.sin(ELEVATION)
      dr.ellipse((x-rx,y-ry,x+rx,y+ry),outline=(255,175,65,200),width=2)
    debug.save(OUT/'debug'/'collision_preview.png',optimize=True)
    report={'seed':SEED,'size':[SCENE_W,SCENE_H],'objects':len(sceneobjects),'materials':matReport,'ground':groundinfo,'rgba_props':all(Image.open(OUT/d['file']).mode=='RGBA' for d in catalog.values()),'needs_real_engine_tests':True,'integration':'game-engine independent metadata; no navmesh or validated gameplay movement'}
    (OUT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    make_scene()
