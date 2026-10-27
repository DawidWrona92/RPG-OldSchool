"""Concept 19 v2: healed pink raised scars and gray-green eyes, unlit pigment fields.
Only the red head UV interior changes. Pinned v3 neck/hand/body samples are restored
byte for byte after export, including both normal map resolutions.
"""
from pathlib import Path
from io import BytesIO
import json,subprocess
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt,gaussian_filter,maximum_filter
BASE='35df59f4c19b473530fd3fe316b35fc7b1739327'
PREFIX='assets/textures/characters/hero/unique/'

def baseline(root,name):
    data=subprocess.check_output(['git','show',BASE+':'+PREFIX+name],cwd=root)
    im=Image.open(BytesIO(data));im.load()
    return np.array(im),data

def head_weight(xyz,detail,region_path):
    reg=np.array(Image.open(region_path).convert('RGB'))
    red=(reg[:,:,0]==214)&(reg[:,:,1]==72)
    red=np.repeat(np.repeat(red,2,0),2,1)&(xyz[:,:,1]>6.12)
    t=np.clip((distance_transform_edt(red)-16)/16,0,1)
    return (t*t*(3-2*t)).astype(np.float32)

def apply(xyz,detail,noise,pores,color,height,rough,weight,meshpath,mesh_data,report_path):
    x,y,z=np.moveaxis(xyz,-1,0);ax=np.abs(x)
    def smooth(a,b,t):
        q=np.clip((t-a)/(b-a),0,1);return q*q*(3-2*q)
    def g(cx,cy,cz,sx,sy,sz,sym=True):
        return np.exp(-.5*((((ax if sym else x)-cx)/sx)**2+((y-cy)/sy)**2+((z-cz)/sz)**2))
    def paint(mask,rgb,amount=1):
        nonlocal color
        a=np.clip(mask*amount,0,1)[...,None];color=color*(1-a)+np.array(rgb,np.float32)*a
    front=smooth(.3,1.05,z)
    forehead=g(0,7.65,1.12,.61,.36,.48)
    # Broken, independently bent creases; deepest low over brows. No periodic pattern.
    wrinkles=np.zeros_like(x)
    specs=[(7.46,-.02,.44,.030,-.010,.90),(7.59,.03,.48,.025,.012,.67),(7.75,-.06,.38,.044,-.006,.43)]
    for i,(cy,cx,span,bend,skew,depth) in enumerate(specs):
        q=(x-cx)/span;curve=cy+bend*q*q+skew*q+.007*q**3
        taper=1-smooth(.65,1,np.abs(q))
        # Offset gaps create actual interrupted segments, not equally spaced waves.
        gap1=np.exp(-((x-[-.12,.18,-.21][i])/.035)**2)
        gap2=np.exp(-((x-[.27,-.30,.06][i])/.025)**2)
        broken=(1-.88*gap1)*(1-.78*gap2)
        wrinkles+=np.exp(-((y-curve)/(.014+.002*i))**2)*forehead*taper*broken*depth
    frown=g(.075,7.43,1.35,.090,.20,.30)*np.exp(-((ax-(.045+.04*(y-7.35)))/.015)**2)
    wrinkles+=frown*1.15
    corner=g(.57,7.22,1.28,.13,.11,.30)*smooth(.46,.51,ax)*(1-smooth(.64,.75,ax))
    for slope,offset,amp in [(-.45,-.005,.45),(.12,.007,.30),(.55,.012,.25)]:
        curve=7.215+offset+slope*(ax-.49)+.015*(ax-.52)**2
        wrinkles+=np.exp(-((y-curve)/.009)**2)*corner*amp
    height-=detail*wrinkles*.034
    # Fine pores, under-eye folds and warm/cold pigment variation, never lighting.
    face=front*g(0,7.05,1.3,.78,.88,.60)
    bags=g(.33,7.10,1.32,.23,.09,.30)
    paint(bags,[114,93,86],.24)
    height+=detail*(face*pores*.0004+bags*.002)
    rough+=detail*(wrinkles*.012+face*pores*.003)
    nose=g(0,6.96,1.64,.24,.30,.3);cheek=g(.44,6.96,1.30,.27,.31,.36)
    paint(nose,[168,101,83],.24);paint(cheek,[166,108,89],.19)
    freckles=np.zeros_like(x);rng=np.random.default_rng(190427)
    for i in range(85):
        cx=rng.uniform(-.69,.69);cy=rng.uniform(6.78,7.92)
        freckles+=g(cx,cy,1.20,rng.uniform(.008,.022),rng.uniform(.008,.024),.55,False)
    freckles=np.clip(freckles,0,1)*face*detail
    paint(freckles,[115,77,50],.45)
    # Dense short beard/moustache. Neck-side coverage remains the v3 mask at UV boundary.
    top=7.035-.23*ax+.05*np.sin(x*17+z*4)+.025*np.sin(x*37)
    beard=front*(1-smooth(top-.15,top+.12,y))*(1-nose*.94)
    beard*=1-g(0,6.50,1.50,.30,.08,.20)*.96
    beard=np.maximum(beard,g(.13,6.67,1.52,.23,.075,.20)*.98)
    beard*=smooth(6.06,6.22,y)
    follicles=gaussian_filter(noise,(.30,2.1));follicles/=follicles.std()
    paint(beard,[77,74,69],.52)
    dots=smooth(-.3,1.35,follicles)*beard*detail
    paint(dots,[46,38,31],.88)
    chin=g(0,6.30,1.22,.39,.24,.43)
    gray_signal=gaussian_filter(np.roll(noise,137,axis=0),(.38,.74));gray_signal/=gray_signal.std()
    gray=dots*smooth(1.65-1.80*chin,2.2-1.55*chin,gray_signal)
    paint(gray,[193,190,180],.95)
    rough=rough*(1-beard*.6)+.71*beard*.6
    scalp=smooth(7.88,8.24,y)
    scalp=np.maximum(scalp,(1-smooth(.18,.62,z))*smooth(6.95,7.6,y))
    paint(scalp,[47,40,34],.45)
    scalp_gray=scalp*smooth(1.1,2.1,follicles)*smooth(1.4,2.25,gray_signal)*detail
    paint(scalp_gray,[168,166,157],.75)
    # No nose-crossing vessel strokes: previous v3 capillary paths are faded by a
    # warm pigment wash, new marks are tiny isolated patches on the cheeks/nose.
    # The legacy capillary contribution is disabled in aging_v2 when v4=True.
    # Pin all scar anchors to the real surface safely inside the head UV mask.
    vertices,uv,faces=mesh_data(meshpath);corners=np.array([q for f in faces for q in f])
    uvp=uv[corners[:,1]];rr=np.clip(((1-uvp[:,1])*4096).astype(int),0,4095);cc=np.clip((uvp[:,0]*4096).astype(int),0,4095)
    safe=vertices[np.unique(corners[weight[rr,cc]>.80,0])]
    def snap(p):return safe[np.argmin(np.sum((safe-p)**2*np.array([5.,5.,.5]),axis=1))]
    # Character left is +X in native OBJ (+Y after the diagnostic world transform).
    paths=[('left_forehead',[(.17,7.97,1.08),(.27,7.80,1.18),(.40,7.57,1.28),(.46,7.44,1.30)],.0085),
           ('cross_cut',[(.30,7.73,1.40),(.39,7.81,1.35),(.48,7.83,1.26)],.0065),
           ('left_cheek',[(.39,7.05,1.34),(.48,6.94,1.30),(.59,6.77,1.17)],.009),
           ('right_scratch_1',[(-.53,7.02,1.30),(-.62,6.96,1.22)],.005),
           ('right_scratch_2',[(-.48,6.91,1.30),(-.59,6.83,1.20)],.0045),
           ('right_scratch_3',[(-.59,6.89,1.20),(-.66,6.85,1.12)],.004)]
    def segment(a,b):
        d=b-a;den=float(d@d)
        if den<1e-8:return np.full_like(x,100),np.zeros_like(x)
        t=np.clip(((x-a[0])*d[0]+(y-a[1])*d[1]+(z-a[2])*d[2])/den,0,1)
        dist=np.sqrt((x-a[0]-t*d[0])**2+(y-a[1]-t*d[1])**2+(z-a[2]-t*d[2])**2)
        return dist,t
    edge_noise=gaussian_filter(noise,2.0);edge_noise/=edge_noise.std()
    scar_records=[];allscar=np.zeros_like(x);allrim=np.zeros_like(x);stitches=np.zeros_like(x)
    for name,anchors,width in paths:
        points=[snap(a) for a in anchors];dist=np.full_like(x,100)
        for a,b in zip(points,points[1:]):
            dd,_=segment(a,b);dist=np.minimum(dist,dd)
        irregular=1+.16*np.clip(edge_noise,-1,1)
        core=np.exp(-.5*(dist/(width*irregular))**2)*detail
        rim=np.exp(-.5*((dist-width*1.4)/(width*.62))**2)*detail
        scar_records.append({'name':name,'side':'left' if name.startswith('left') or name=='cross_cut' else 'right','anchors':[p.tolist() for p in points],'max_mask':float((core*weight).max()),'pixels_gt_025':int(((core*weight)>.25).sum())})
        assert (core*weight).max()>.25,name
        allscar=np.maximum(allscar,core);allrim=np.maximum(allrim,rim)
        if name.startswith('left'):
            for a,b in zip(points,points[1:]):
                axis=b-a;length=np.linalg.norm(axis)
                if length<.02:continue
                tangent=np.cross(axis,[0,0,1]);tangent/=max(np.linalg.norm(tangent),1e-7)
                dd,tt=segment(a,b)
                for t in [.24,.63]:
                    stitch=np.exp(-.5*(((tt-t)*length/.0035)**2+(dd/.026)**2))*detail
                    stitches=np.maximum(stitches,stitch)
    # Healed raised tissue: rose pigment, darker pigmented center, pale pink rims.
    paint(allrim,[180,125,114],.48)
    paint(allscar,[155,96,87],.52)
    paint(stitches,[148,92,83],.60)
    scarfield=np.maximum(allscar,allrim*.7)
    height=height*(1-scarfield*.82)+(.5+allrim*.0045+allscar*.0030)*scarfield*.82
    height+=stitches*.0015
    height=np.where(scarfield>.6,np.maximum(height,.5+allrim*.003+allscar*.0025),height)
    rough=rough*(1-scarfield*.85)+.43*scarfield*.85
    raised=(allscar>.85)&(weight>.95)
    assert raised.any() and height[raised].min()>.5,'Scar core must be raised above neutral height'
    report={'version':4,'raised_scar_core_min':float(height[raised].min()),'baseline':BASE,'normal_strength':.45,'scars':scar_records,
            'scar_relief':'positive pink raised rims with fine healed suture traces; no depressed cut',
            'character_left_native_axis':'+X','hands_neck_protection':'pinned v3 outside eroded red head UV mask; y<=6.12 protected',
            'neck_crease_strokes':False,'iris':'gray green / gray hazel, warm olive brown inner ring','status':'PROTOTYPE_NOT_APPROVED'}
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return color,height,rough

def restore_outside_head(root,weight):
    repo=root.parents[4]
    allowed=[weight>0, maximum_filter(weight,size=13)[1::2,1::2]>0]
    for suffix,mask in zip(['','_2048'],allowed):
        for m in ['basecolor','roughness','height','normal_opengl','sss_mask']:
            name=f'hero_skin_body_{m}{suffix}.png';a=np.array(Image.open(root/name));b,data=baseline(repo,name)
            if m=='sss_mask':(root/name).write_bytes(data);continue
            a[~mask]=b[~mask];Image.fromarray(a).save(root/name)
