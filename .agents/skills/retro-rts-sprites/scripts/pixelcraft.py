"""Pixelcraft: original pixel-art workbench for RTS Sprite Skills v4.
Pillow only. Every operation is done at native 1x pixel resolution.
Design ideas informed by the MIT-licensed Gamezxz/pixel-art-studio project;
this file does not contain copied upstream source.
"""
from __future__ import annotations
import colorsys, json, math, os
from collections import Counter, deque
from PIL import Image, ImageDraw


def hexrgb(s):
    return tuple(int(s.lstrip('#')[i:i+2], 16) for i in (0,2,4))

def ramp(base, shades=5, shift=16):
    r,g,b=hexrgb(base); h,s,v=colorsys.rgb_to_hsv(r/255,g/255,b/255)
    out=[]
    for i in range(shades):
        t= i/(shades-1) if shades>1 else 0.5
        target=240 if t<0.5 else 60
        amount=abs(t-0.5)*2*shift
        delta=(target-h*360+180)%360-180
        hue=(h*360+max(-amount,min(amount,delta)))%360
        val= (0.46*v+(v-0.46*v)*t*2) if t<=.5 else (v+(1-v)*.60*(t-.5)*2)
        sat=min(1, s*(1.15 if t<.5 else 1-.3*(t-.5)*2))
        out.append(tuple(round(k*255) for k in colorsys.hsv_to_rgb(hue/360,sat,val))+(255,))
    return out

def color(s):
    if isinstance(s,str): return hexrgb(s)+(255,)
    return s if len(s)==4 else tuple(s)+(255,)

class Layered:
    def __init__(self,w,h,anchor):
        self.w,self.h=w,h; self.anchor=tuple(anchor); self.layers={}; self.order=[]
    def layer(self,name):
        if name not in self.layers:
            self.layers[name]=Image.new('RGBA',(self.w,self.h));self.order.append(name)
        return PixelPen(self.layers[name])
    def composite(self):
        out=Image.new('RGBA',(self.w,self.h))
        for name in self.order:out.alpha_composite(self.layers[name])
        return out

class PixelPen:
    def __init__(self,image):self.im=image;self.draw=ImageDraw.Draw(image)
    def poly(self,points,c):self.draw.polygon([(round(x),round(y)) for x,y in points],fill=color(c))
    def rect(self,box,c):self.draw.rectangle(tuple(round(v) for v in box),fill=color(c))
    def ell(self,box,c):self.draw.ellipse(tuple(round(v) for v in box),fill=color(c))
    def line(self,points,c,width=1):self.draw.line([(round(x),round(y)) for x,y in points],fill=color(c),width=width,joint='curve')
    def px(self,x,y,c):self.draw.point((round(x),round(y)),fill=color(c))
    def clipped_ellipse(self,box,shade,offset=(-2,-2)):
        mask=Image.new('L',self.im.size);d=ImageDraw.Draw(mask);d.ellipse(box,fill=255)
        self.im.paste(color(shade), (0,0,self.im.width,self.im.height),mask)
        inset=Image.new('L',self.im.size);d2=ImageDraw.Draw(inset)
        d2.ellipse(tuple(v+offset[i%2] for i,v in enumerate(box)),fill=255)
        # shifted brighter shape cannot enlarge outside the original dark outline
        from PIL import ImageChops
        both=ImageChops.multiply(mask,inset)
        return both


def stats(img,backgrounds=((25,27,34),(57,68,51))):
    im=img.convert('RGBA');p=im.load();w,h=im.size
    used=Counter((r,g,b) for r,g,b,a in im.getdata() if a>=128)
    alpha=[a for *_,a in im.getdata()]
    edges=[]; isolated=0
    for y in range(h):
        for x in range(w):
            if p[x,y][3]<128:continue
            neighbors=[p[xx,yy][3] for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)) if 0<=xx<w and 0<=yy<h]
            if not any(a>=128 for a in neighbors):isolated+=1
            if x==0 or y==0 or x==w-1 or y==h-1:edges.append((x,y))
    return {'size':[w,h],'colors':len(used),'opaque':sum(a>=128 for a in alpha),
       'semi_alpha':sum(0<a<255 for a in alpha),'isolated':isolated,
       'edge_touch':len(edges),'top_colors':[{'rgb':list(k),'count':v} for k,v in used.most_common(12)]}

def frame_checks(images,anchors,directions=8,frames_per_direction=1,allow_duplicates=False):
    assert len(images)==len(anchors)==directions*frames_per_direction,'frame count mismatch'
    if not images:raise ValueError('empty frames')
    size=images[0].size;errors=[];warn=[]
    if any(im.size!=size for im in images):errors.append('canvas size varies')
    if len(set(map(tuple,anchors)))!=1:errors.append('anchor drifts')
    if not(0<=anchors[0][0]<size[0] and 0<=anchors[0][1]<size[1]):errors.append('anchor outside canvas')
    for i,im in enumerate(images):
        x=stats(im)
        if x['opaque']==0:errors.append(f'frame {i} empty')
        if x['edge_touch']:errors.append(f'frame {i} clipped ({x["edge_touch"]} boundary pixels)')
    # Exact RGBA image duplicates across all pairs of directions, not just dir 0.
    sig=[]
    for d in range(directions):
        sig.append(tuple(images[d*frames_per_direction+k].tobytes() for k in range(frames_per_direction)))
    for a in range(directions):
        for b in range(a+1,directions):
            if sig[a]==sig[b]:
                (warn if allow_duplicates else errors).append(f'directions {a}/{b} identical RGBA')
    return {'ok':not errors,'errors':errors,'warnings':warn,'size':list(size),'directions':directions,
            'frames_per_direction':frames_per_direction,'anchor':list(anchors[0])}

def make_atlas(images,anchor,dirs,fpd,padding=2,cols=None):
    if not images:raise ValueError('no frames')
    if len(images)!=dirs*fpd:raise ValueError('frame count != directions * frames')
    w,h=images[0].size
    if any(x.size!=(w,h) for x in images):raise ValueError('mixed frame dimensions')
    cols=cols or fpd;rows=math.ceil(len(images)/cols)
    out=Image.new('RGBA',(cols*(w+padding)+padding,rows*(h+padding)+padding));rects=[]
    for i,img in enumerate(images):
        x=padding+(i%cols)*(w+padding);y=padding+(i//cols)*(h+padding)
        out.alpha_composite(img,(x,y));rects.append({'index':i,'x':x,'y':y,'direction':i//fpd,'phase':i%fpd,
                                                   'view_angle_deg':(i//fpd)*45,'duration_ms':100})
    meta={'schema':'rpg-sprite-v4','frame_size':[w,h],'columns':cols,'rows':rows,'padding':padding,'anchor':list(anchor),
          'directions':dirs,'frames_per_direction':fpd,'direction_order':'yaw_0_then_45_counterclockwise_world_xy',
          'frames':rects,'texture_filter':'nearest','loop':True}
    return out,meta

def save_atlas(path,images,anchor,dirs,fpd,padding=2):
    atlas,meta=make_atlas(images,anchor,dirs,fpd,padding)
    atlas.save(path)
    with open(os.path.splitext(path)[0]+'.json','w',encoding='utf8') as f:json.dump(meta,f,ensure_ascii=False,indent=2)
    return meta

def analyze_reference(path):
    im=Image.open(path).convert('RGBA');report=stats(im)
    pixels=[(r,g,b) for r,g,b,a in im.getdata() if a>=128]
    def lum(c):return sum(c[i]*w for i,w in enumerate((.2126,.7152,.0722)))
    report['luminance_range']=[round(min(map(lum,pixels)),2),round(max(map(lum,pixels)),2)] if pixels else None
    hues=Counter(); luminance=[]
    for c in pixels:
        h,s,v=colorsys.rgb_to_hsv(*(x/255 for x in c));
        if s>.12:hues[round(h*12)%12]+=1
        luminance.append(v)
    report['hue_groups']={str(int(k*30)):v for k,v in hues.most_common(12)}
    report['style_card_template']=['Estimate actual visible sprite size and silhouette before drawing',
      'Choose ONE palette across characters of the same faction',
      'Judge clusters and occlusion with the reference side by side',
      'Do not pretend color/hue statistics capture composition or quality']
    return report

def clean_import(path,out_path,max_colors=24,alpha_threshold=128,preserve_soft_alpha=False):
    im=Image.open(path).convert('RGBA');a=im.getchannel('A')
    if not preserve_soft_alpha:
        a=a.point(lambda v:255 if v>=alpha_threshold else 0)
    pixels=Image.new('RGB',im.size); pixels.paste(im.convert('RGB'))
    pal=pixels.quantize(colors=max_colors,method=Image.Quantize.FASTOCTREE,dither=Image.Dither.NONE).convert('RGB')
    pal.putalpha(a)
    pal.save(out_path)
    return {'before':stats(im),'after':stats(pal),'note':'Lossy quantization: use ONLY when intentionally making pixel art, not on painterly/3D sprite masks.'}
