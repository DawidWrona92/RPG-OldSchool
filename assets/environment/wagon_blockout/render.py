"""Orthographic software preview of the OBJ blockout; not a Blender render.
Requires Python 3, numpy and Pillow.  Outputs transparent RGBA and a contact sheet.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
vertices=[]; faces=[]
for line in (ROOT/'wagon-blockout.obj').read_text().splitlines():
    fields=line.split()
    if not fields: continue
    if fields[0]=='v': vertices.append([float(v) for v in fields[1:4]])
    if fields[0]=='f': faces.append([int(v.split('/')[0])-1 for v in fields[1:]])
verts=np.array(vertices)

def render(angle, name):
    size=768; scale=125
    eye=np.array([np.cos(angle),np.sin(angle),1.1]); eye/=np.linalg.norm(eye)
    right=np.array([-np.sin(angle),np.cos(angle),0.])
    up=np.cross(eye,right); up/=np.linalg.norm(up)
    center=np.array([.38,0.,.70]); rel=verts-center
    screen=np.column_stack((size/2+scale*(rel@right),size/2-scale*(rel@up),rel@eye))
    pix=np.zeros((size,size,4),dtype=np.uint8); depth=np.full((size,size),-np.inf)
    light=np.array([-0.4,-0.6,1.]); light/=np.linalg.norm(light)
    # Each original primitive contributes six quads. Colors reflect component type;
    # there are no textures or separate material IDs in the OBJ.
    for fi,f in enumerate(faces):
      pts=verts[f]; norm=np.cross(pts[1]-pts[0],pts[2]-pts[0]); n=np.linalg.norm(norm)
      if n<1e-10: continue
      norm/=n
      if np.dot(norm,eye)<=0: continue
      p=screen[f]; base=np.array([102.,75.,53.])
      # Plane-specific material coloration, only for visualization.
      shade=.40+.60*max(0.,np.dot(norm,light)); color=np.clip(base*shade,0,255).astype(np.uint8)
      for tri in ((0,1,2),(0,2,3)):
        q=p[list(tri)]; minx=max(0,int(np.floor(q[:,0].min()))); maxx=min(size-1,int(np.ceil(q[:,0].max())))
        miny=max(0,int(np.floor(q[:,1].min()))); maxy=min(size-1,int(np.ceil(q[:,1].max())))
        if maxx<minx or maxy<miny: continue
        x,y=np.meshgrid(np.arange(minx,maxx+1)+.5,np.arange(miny,maxy+1)+.5)
        x0,y0=q[0,:2]; x1,y1=q[1,:2]; x2,y2=q[2,:2]
        denom=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
        if abs(denom)<1e-9: continue
        a=((y1-y2)*(x-x2)+(x2-x1)*(y-y2))/denom
        b=((y2-y0)*(x-x2)+(x0-x2)*(y-y2))/denom; c=1-a-b
        z=a*q[0,2]+b*q[1,2]+c*q[2,2]
        region=depth[miny:maxy+1,minx:maxx+1]; mask=(a>=-1e-7)&(b>=-1e-7)&(c>=-1e-7)&(z>region)
        region[mask]=z[mask]
        tile=pix[miny:maxy+1,minx:maxx+1]; tile[mask,:3]=color; tile[mask,3]=255
    img=Image.fromarray(pix,'RGBA'); img.save(ROOT/(name+'.png'))
    bbox=img.getbbox()
    if not bbox or bbox[0]<=0 or bbox[1]<=0 or bbox[2]>=size or bbox[3]>=size: raise RuntimeError('empty or clipped render')
    return img,bbox

views=[]
for angle,name in [(np.deg2rad(45),'wagon-view-a'),(np.deg2rad(225),'wagon-view-b')]:
    img,bbox=render(angle,name); views.append((img,bbox,name))
sheet=Image.new('RGB',(1536,850),(64,65,62)); d=ImageDraw.Draw(sheet)
for i,(img,bbox,name) in enumerate(views):
    sheet.paste(img,(768*i,40),img); d.text((20+768*i,15),name+' | blockout, no textures',fill='white')
sheet.save(ROOT/'wagon-contact-sheet.png')
(ROOT/'render-metadata.json').write_text(json.dumps({'method':'numpy orthographic z-buffer','dimensions':[768,768],'alpha':'straight RGBA','views':[{'name':n,'bbox':list(b)} for _,b,n in views],'shadows':False,'game_camera_verified':False},indent=2)+'\n')
print('Rendered 2 views. Bboxes:',[(n,b) for _,b,n in views])
