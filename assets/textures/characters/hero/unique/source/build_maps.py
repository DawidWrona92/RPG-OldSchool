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
    # Stable 3-D frequencies avoid identical UV tile repetitions.
    micro=(np.sin(x*167+y*113+np.sin(z*87))*np.sin(z*181-x*89)+.5*np.sin(y*311-z*191+x*137))/1.5
    macro=(np.sin(x*8.7+y*6.1+np.sin(z*9.3))*.5+np.sin(x*19.1-y*17.7+z*13.9)*.25)
    edge=distance_transform_edt(valid)
    detail=smooth(32,56,edge)
    rng=np.random.default_rng(27062026)
    noise=rng.normal(0,1,(n,n)).astype(np.float32)
    pores=gaussian_filter(noise,.65)-gaussian_filter(noise,2.2)
    pores/=pores.std()
    # V4 refines the v3 surface fields using concept 19 and the author's direction.
    from aging_v2 import apply
    color,height,rough,sss=apply(xyz,detail,noise,pores,micro,macro,args.mesh,mesh_data,None,v4=True)
    from face_v4 import apply as face_apply,head_weight,baseline,restore_outside_head
    weight=head_weight(xyz,detail,ROOT.parents[4]/'docs/art/characters/tekstury-bohatera/uv-cialo-obszary-2048.png')
    color,height,rough=face_apply(xyz,detail,noise,pores,color,height,rough,weight,args.mesh,mesh_data,ROOT/'qa'/'v4_material_checks.json')
    for field,m,scale in [(color,'basecolor',1),(height,'height',65535),(rough,'roughness',255)]:
        old,_=baseline(ROOT.parents[4],'hero_skin_body_'+m+'.png');old=old.astype(np.float32)/scale
        w=weight[...,None] if field.ndim==3 else weight
        field[:]=old+w*(field-old)
    # Preserve the established padding/export contracts after the v4 head edit.
    _,nearest=distance_transform_edt(~valid,return_indices=True)

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
    restore_outside_head(ROOT,weight)
    print('Wrote 10 body PNGs; height 16-bit; body faces mapped to native UV.')

if __name__=='__main__':main()
