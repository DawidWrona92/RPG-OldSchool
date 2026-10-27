"""Technical PBR map synthesis over native MakeHuman UV, not an AI normal-map image.
Run with system Python + numpy/scipy/Pillow: python source/build_maps.py --mesh /tmp/base.obj
Mesh is CC0 MakeHuman hm08 from sprite branch; never rewrites it.
"""
import argparse
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt, gaussian_filter

ROOT=Path(__file__).resolve().parents[1]

def mesh_data(path):
    verts=[]; uvs=[]; faces=[]; group=''
    for line in open(path):
        s=line.split()
        if not s: continue
        if s[0]=='v': verts.append(tuple(map(float,s[1:4])))
        elif s[0]=='vt': uvs.append(tuple(map(float,s[1:3])))
        elif s[0]=='g': group=s[1]
        elif s[0]=='f' and group=='body': faces.append([tuple(int(t)-1 for t in x.split('/')[:2]) for x in s[1:]])
    return np.array(verts,np.float32),np.array(uvs,np.float32),faces

def rasterize(path,n):
    v,uv,faces=mesh_data(path)
    xyz=np.zeros((n,n,3),np.float32); valid=np.zeros((n,n),bool)
    for face in faces:
        for j in range(1,len(face)-1):
            f=np.array([face[0],face[j],face[j+1]])
            p=uv[f[:,1]]*n; p[:,1]=n-p[:,1]
            lo=np.maximum(np.floor(p.min(0)).astype(int),0); hi=np.minimum(np.ceil(p.max(0)).astype(int),n-1)
            if np.any(hi<lo): continue
            xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5)
            a,b,c=p; den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
            if abs(den)<1e-9: continue
            w0=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
            w1=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den
            w2=1-w0-w1; mask=(w0>=-1e-5)&(w1>=-1e-5)&(w2>=-1e-5)
            sl=np.s_[lo[1]:hi[1]+1,lo[0]:hi[0]+1]
            q=v[f[:,0]]
            xyz[sl][mask]=(w0[...,None]*q[0]+w1[...,None]*q[1]+w2[...,None]*q[2])[mask]
            valid[sl]|=mask
    return xyz,valid

def save_scalar(a,name,bits=8):
    if bits==16:
        im=Image.fromarray(np.rint(np.clip(a,0,1)*65535).astype(np.uint16))
    else: im=Image.fromarray(np.rint(np.clip(a,0,1)*255).astype(np.uint8))
    im.save(ROOT/(name+'.png'))
    # Float resampling preserves 16-bit height values (Pillow I;16 resize is unsupported).
    small=Image.fromarray(np.array(im).astype(np.float32)/(65535 if bits==16 else 255)).resize((2048,2048),Image.Resampling.LANCZOS)
    s=np.clip(np.array(small),0,1)
    if bits==16: out=Image.fromarray(np.rint(s*65535).astype(np.uint16))
    else: out=Image.fromarray(np.rint(s*255).astype(np.uint8))
    out.save(ROOT/(name+'_2048.png'))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mesh',required=True);args=ap.parse_args()
    n=4096
    xyz,valid=rasterize(args.mesh,n)
    np.save('/tmp/hero-xyz.npy',xyz); np.save('/tmp/hero-valid.npy',valid)
    x,y,z=np.moveaxis(xyz,-1,0); ax=np.abs(x)
    def gauss(cx,cy,cz,sx,sy,sz):
        return np.exp(-.5*(((ax-cx)/sx)**2+((y-cy)/sy)**2+((z-cz)/sz)**2))
    def smooth(a,b,t):
        t=np.clip((t-a)/(b-a),0,1);return t*t*(3-2*t)
    head=smooth(5.8,6.25,y)
    front=smooth(.25,1.1,z)
    scalp=smooth(7.80,8.10,y)*head
    # Physical anatomical pigment regions; no luminance-derived roughness or height.
    lips=gauss(0,6.50,1.50,.30,.080,.20)
    nose=gauss(0,6.96,1.64,.21,.30,.26)
    ears=gauss(.79,7.08,.45,.17,.35,.32)
    cheeks=gauss(.46,6.94,1.31,.25,.25,.27)
    beard=front*head*(1-smooth(6.85,7.15,y))*(1-lips*.8)
    hands=smooth(3.55,4.0,ax)*(1-smooth(3.7,4.5,y))
    fingers=hands*smooth(4.15,4.55,ax)
    # Stable 3-D frequencies avoid identical UV tile repetitions.
    micro=(np.sin(x*167+y*113+np.sin(z*87))*np.sin(z*181-x*89)+.5*np.sin(y*311-z*191+x*137))/1.5
    macro=(np.sin(x*8.7+y*6.1+np.sin(z*9.3))*.5+np.sin(x*19.1-y*17.7+z*13.9)*.25)
    edge=distance_transform_edt(valid)
    detail=smooth(32,56,edge)
    rng=np.random.default_rng(27062026)
    noise=rng.normal(0,1,(n,n)).astype(np.float32)
    pores=gaussian_filter(noise,.65)-gaussian_filter(noise,2.2)
    pores/=pores.std()
    # Creases are depressions, not dark albedo strokes. All restricted to UV interior.
    forehead=gauss(0,7.61,1.1,.60,.28,.35)
    wrinkles=np.zeros((n,n),np.float32)
    for cy in [7.49,7.61,7.72]:
        line=np.exp(-((y-(cy+.035*np.cos(x*4)))/.010)**2)
        wrinkles+=line*forehead
    # Outer-eye fine folds and nasolabial creases, shared in height/roughness.
    crows=gauss(.57,7.22,1.28,.17,.12,.25)
    wrinkles+=crows*(.5+.5*np.sin((y+x*.45)*155))**14
    nasolabial=np.exp(-((ax-(.19+.45*(6.95-y)))/.017)**2)*gauss(.28,6.78,1.42,.18,.22,.3)
    wrinkles+=nasolabial*.7
    # Palm/knuckle creases from anatomical region; not deep wounds.
    handlines=hands*(.5+.5*np.sin((ax*.7+y*.5+z*.6)*63))**20
    lipcracks=lips*(.5+.5*np.sin(x*175+y*13))**16
    height=.5+detail*(pores*.0018+micro*.0008-wrinkles*.010-handlines*.0025-lipcracks*.002)
    rough=.60+.018*macro+.015*micro
    rough=rough*(1-scalp)+.70*scalp
    rough=rough*(1-beard*.8)+.70*beard*.8
    rough=rough*(1-nose)+.45*nose
    rough=rough*(1-forehead*.75)+.46*forehead*.75
    rough=rough*(1-lips)+.45*lips
    rough=rough*(1-hands)+(.65+.02*macro)*hands
    rough+=detail*(pores*.006+wrinkles*.015)
    sss=np.clip(.26+.50*ears+.34*nose+.27*fingers+.12*lips-.06*scalp,0,1)
    # Copy nearest UV-interior samples into all unused space (unbounded dilation).
    _,nearest=distance_transform_edt(~valid,return_indices=True)
    # New unlit pigment material: regional tanning, natural redness, follicles and dirt.
    # All coordinates are from the real surface; no normals, light, AO or curvature enter albedo.
    exposure=np.maximum(head*.85,smooth(2.65,3.6,ax)*.85)
    exposure=np.maximum(exposure,gauss(0,5.7,.4,.8,.7,.8)*.65)
    color=np.zeros((n,n,3),np.float32)+np.array([181,149,131],np.float32)
    color+=exposure[...,None]*np.array([-22,-28,-30],np.float32)
    color+=macro[...,None]*np.array([2.4,1.9,1.6],np.float32)
    def pigment(mask,rgb,amount=1):
        nonlocal color
        w=np.clip(mask*amount,0,1)[...,None]
        color=color*(1-w)+np.array(rgb,np.float32)*w
    pigment(nose,[172,111,94],.32)
    pigment(cheeks,[171,111,96],.28)
    pigment(ears,[173,109,94],.42)
    socket=gauss(.34,7.20,1.32,.19,.13,.21)
    pigment(socket,[131,113,108],.32)
    # Skin of scalp under future hair fibers, including the back-of-head seam.
    scalp=np.maximum(scalp,head*(1-smooth(.18,.60,z))*smooth(6.70,7.25,y))
    scalp=np.maximum(scalp,gauss(.66,7.76,.69,.23,.30,.38)*.8)
    pigment(scalp,[49,38,31],.95)
    # Beard coverage follows cheek/jaw anatomy and leaves natural upper-cheek clear space.
    beardtop=7.04-.21*np.clip(ax,0,1)
    beard=front*head*(1-smooth(beardtop-.12,beardtop+.10,y))
    beard*=1-np.clip(nose*.9+lips*.9,0,1)
    beard=np.maximum(beard,gauss(.15,6.68,1.51,.18,.075,.17)*.8)
    beard=np.maximum(beard,gauss(.25,6.23,.91,.47,.19,.52)*.75)
    pigment(beard,[88,70,56],.60)
    # Multiscale, anisotropic sparse follicles, rather than a painted black beard patch.
    follicles=gaussian_filter(noise,(.45,1.0));follicles/=follicles.std()
    stubble=smooth(1.15,2.2,follicles)*beard*detail
    pigment(stubble,[47,36,28],.95)
    brow=gauss(.35,7.40,1.22,.25,.045,.25)*front
    pigment(brow,[63,48,37],.48)
    pigment(brow*smooth(.0,1.6,follicles)*detail,[45,35,28],.65)
    # Lips and hand details are pigment changes; height cracks remain separate.
    pigment(lips,[151,103,95],.8)
    pigment(lipcracks*detail,[130,93,86],.10)
    pigment(hands*smooth(1.72,2.06,z),[180,144,123],.65)
    dirt=hands*(.25+.75*(.5+.5*np.sin((ax*.7+y*.5+z*.6)*63))**20)
    pigment(dirt*detail,[94,78,57],.23)
    # Anatomically placed short nail plates, ellipsoids aligned to terminal phalanges.
    joints={}; group=''; ids=[]
    vv=[]
    for line in open(args.mesh):
        tok=line.split()
        if not tok:continue
        if tok[0]=='v':vv.append(tuple(map(float,tok[1:4])))
        elif tok[0]=='g':group=tok[1]
        elif tok[0]=='f' and group.startswith('joint-l-finger'):
            joints.setdefault(group,[]).extend(int(t.split('/')[0])-1 for t in tok[1:])
    vv=np.array(vv)
    for finger in range(1,6):
        tip=vv[np.unique(joints[f'joint-l-finger-{finger}-4'])].mean(0)
        base=vv[np.unique(joints[f'joint-l-finger-{finger}-3'])].mean(0)
        axis=tip-base;axis/=np.linalg.norm(axis)
        center=tip*.7+base*.3
        # Hands face inward in the neutral mesh; dorsal side is outward along X.
        center[0]+=.065 if finger!=1 else -.05
        dx0=ax-center[0];dy0=y-center[1];dz0=z-center[2]
        along=dx0*axis[0]+dy0*axis[1]+dz0*axis[2]
        perp2=np.maximum(dx0*dx0+dy0*dy0+dz0*dz0-along*along,0)
        plate=np.exp(-((along/.095)**4+(perp2/.0045)**2))*hands
        pigment(plate,[174,145,127],.7)
        dirtedge=plate*np.exp(-((along-.065)/.022)**2)
        pigment(dirtedge,[83,71,53],.6)
        rough=rough*(1-plate*.5)+.48*plate*.5
    # Keep the technical response aligned with final scalp/beard pigment regions.
    rough=rough*(1-scalp)+.70*scalp
    rough=rough*(1-beard*.8)+.70*beard*.8
    rough=rough*(1-lips)+.45*lips
    # Fine pores and subtle mottling are tonal pigment variation, not baked lighting.
    color+=detail[...,None]*(pores[...,None]*.65+micro[...,None]*1.1)
    color=np.clip(color,0,255)
    for a in [height,rough,sss]: a[~valid]=a[tuple(nearest[:,~valid])]
    color[~valid]=color[tuple(nearest[:,~valid])]
    base=Image.fromarray(np.rint(color).astype(np.uint8))
    base.save(ROOT/'hero_skin_body_basecolor.png')
    base.resize((2048,2048),Image.Resampling.LANCZOS).save(ROOT/'hero_skin_body_basecolor_2048.png')
    save_scalar(height,'hero_skin_body_height',16)
    save_scalar(rough,'hero_skin_body_roughness')
    save_scalar(sss,'hero_skin_body_sss_mask')
    # d/dv = -d/d(image row). OpenGL tangent +Y; Blender uses MikkTSpace TBN.
    # Height displacement convention: full 0..1 represents 0.002m, centered on .5.
    # UV scale sets strength; keep fine pore relief subdued.
    dy,dx=np.gradient(height)
    nx=-dx*180;ny=dy*180;nz=np.ones_like(nx)
    norm=np.sqrt(nx*nx+ny*ny+1)
    normal=np.stack((nx/norm,ny/norm,nz/norm),-1)
    for size,suffix in [(4096,''),(2048,'_2048')]:
        if size==2048:
            a=np.stack([np.array(Image.fromarray(normal[:,:,i]).resize((size,size),Image.Resampling.LANCZOS)) for i in range(3)],-1)
            a/=np.maximum(np.linalg.norm(a,axis=2,keepdims=True),1e-10)
        else:a=normal
        Image.fromarray(np.rint((a*.5+.5)*255).clip(0,255).astype(np.uint8)).save(ROOT/('hero_skin_body_normal_opengl'+suffix+'.png'))
    print('Wrote 10 body PNGs; height 16-bit; body faces mapped to native UV.')

if __name__=='__main__':main()
