"""V3 refinement of the v2 skin fields: restrained, mature weathered traveler. Native surface units: 0.108m.
All marks are surface-position fields, never lighting/AO. Asymmetric healed scars
and moles are appearance only. Scalar relief is interpreted by the existing exporter.
"""
import json
import numpy as np
from scipy.ndimage import gaussian_filter

def apply(xyz, detail, noise, pores, micro, macro, meshpath, mesh_data, report_path, v4=False):
    x,y,z=np.moveaxis(xyz,-1,0);ax=np.abs(x)
    def smooth(a,b,t):
        q=np.clip((t-a)/(b-a),0,1);return q*q*(3-2*q)
    def g(cx,cy,cz,sx,sy,sz,symmetric=True):
        return np.exp(-.5*(((ax if symmetric else x)-cx)**2/sx**2+(y-cy)**2/sy**2+(z-cz)**2/sz**2))
    front=smooth(.15,1.05,z)
    head=smooth(5.82,6.38,y)
    hands=smooth(3.55,4,ax)*(1-smooth(3.7,4.5,y))
    nose=g(0,6.96,1.64,.23,.30,.30); cheeks=g(.46,6.94,1.31,.3,.32,.38)
    ears=g(.79,7.08,.45,.18,.36,.33)
    lips=g(0,6.5,1.5,.3,.08,.2)
    forehead=g(0,7.65,1.05,.65,.37,.6)
    neck=g(0,5.94,.45,.85,.58,.85)
    dorsal=hands*smooth(-.04,.10,ax-(4.25+.40*(2.45-y)+.30*(z-1.8)))
    # 0.46 source units = 49.7mm: smooth jaw/neck tanning transition.
    tan=np.clip((.34*head+.30*nose+.29*cheeks+.22*forehead+.18*ears)*smooth(5.87,6.33,y),0,1)
    tan=np.maximum(tan,.58*smooth(2.45,3.9,ax))
    tan=np.maximum(tan,neck*.24)
    color=np.zeros((*x.shape,3),np.float32)+np.array([183,151,132],np.float32)
    color+=tan[...,None]*np.array([-39,-43,-43],np.float32)
    color+=macro[...,None]*np.array([3.0,2.3,1.7],np.float32)
    def paint(mask,rgb,weight=1):
        nonlocal color
        a=np.clip(mask*weight,0,1)[...,None]
        color=color*(1-a)+np.array(rgb,np.float32)*a
    # Irregular soft hairline, sparse transition follicles; no horizontal cap stripe.
    hairline=8.06+.045*np.cos(x*5)+.016*np.sin(x*17+z*4)+.012*np.sin(x*31-z*7)
    scalp=smooth(hairline-.24,hairline+.36,y)
    scalp=np.maximum(scalp,head*(1-smooth(.05,.65,z))*smooth(6.90,7.51,y))
    scalp=np.maximum(scalp,g(.69,7.81,.64,.20,.26,.32)*.60)
    paint(scalp,[48,39,33],.90)
    follicle=gaussian_filter(noise,(.40,.85));follicle/=follicle.std()
    transition=np.exp(-((y-hairline)/.18)**2)*front
    paint(transition*smooth(.65,1.8,follicle)*detail,[54,46,39],.65)
    beardtop=7.02-.24*ax+.055*np.sin(x*19+z*6)+.025*np.sin(x*39)
    beard=front*(1-smooth(beardtop-.21,beardtop+.14,y))
    beard*=1-np.clip(nose*.92+lips*.9,0,1)
    beard=np.maximum(beard,g(.14,6.67,1.52,.21,.075,.21)*.95)
    beard=np.maximum(beard,g(.22,6.22,.87,.49,.23,.58)*.90)
    # Curved, softly irregular underside of jaw, not a plane at a fixed Y.
    lower=5.99+.52*np.minimum(ax/.8,1.4)**1.7+.06*(z-.9)
    lower+=.035*np.exp(-((x-.21)/.12)**2)-.030*np.exp(-((x+.38)/.16)**2)
    beard*=smooth(lower-.19,lower+.22,y)
    paint(beard,[94,89,83],.48)
    stubble=smooth(.35,1.7,follicle)*beard*detail
    paint(stubble,[48,42,35],.90)
    gray=stubble*smooth(.90,.98,np.sin(x*129+y*97+z*173)*.5+.5)
    paint(gray,[171,165,151],.76)
    brow=g(.35,7.4,1.22,.25,.05,.3)*front
    paint(brow,[62,51,41],.65)
    paint(brow*smooth(.1,1.5,follicle)*detail,[43,36,30],.65)
    paint(lips,[147,98,91],.80)
    paint(nose,[161,96,82],.40);paint(cheeks,[162,103,87],.28);paint(ears,[160,99,86],.35)
    bags=g(.34,7.095,1.32,.23,.10,.34)*front
    paint(bags,[113,99,94],.52)
    # Irregular non-tiling sun damage: signed coordinates, therefore not mirrored.
    sun=np.clip(nose+cheeks+forehead+ears+neck*.4+dorsal,0,1)
    mottling=(np.sin(x*27+y*19+np.sin(z*13))*.5+.5)*(np.sin(y*37-z*29+x*11)*.5+.5)
    paint(sun*mottling,[133,94,69],.17)
    spots=np.zeros_like(x)
    rng=np.random.default_rng(20261027)
    for i in range(25):
        cx=rng.uniform(-.73,.73);cy=rng.uniform(6.72,7.89)
        spots+=g(cx,cy,1.20,rng.uniform(.018,.045),rng.uniform(.018,.050),.55,False)
    for side in [-1,1]:
        for i in range(11):
            spots+=g(side*rng.uniform(4.22,4.85),rng.uniform(1.5,2.5),2.25,rng.uniform(.025,.055),rng.uniform(.025,.055),.7,False)*dorsal
    spots=np.clip(spots,0,1)*sun*detail*(1-scalp)
    paint(spots,[112,78,53],.42)
    # Fine broken capillaries: a few branching curves in nose/cheek pigmentation only.
    vessels=np.zeros_like(x)
    for center,slope in [(-.44,.35),(.39,-.28),(-.16,.22),(.12,-.16)]:
        path=center+slope*(y-6.98)+.014*np.sin(y*59+center*7)
        vessels+=np.exp(-((x-path)/.0045)**2)*np.exp(-((y-6.99)/.19)**2)
        branch=path+.06*(y-6.96)
        vessels+=.4*np.exp(-((x-branch)/.0035)**2)*np.exp(-((y-6.96)/.11)**2)
    vessels=np.clip(vessels,0,1)*np.clip(nose+cheeks,0,1)*detail
    paint(vessels,[143,91,78],0 if v4 else .23)
    # Three separate, non-periodic central forehead creases with unequal length,
    # curvature, skew, taper and depth. The temple field is exactly zero.
    wrinkles=np.zeros_like(x)
    forehead_specs=[(7.47,-.025,.36,.020,-.010,.48),
                    (7.59,.030,.43,.032,.006,.57),
                    (7.71,-.050,.31,.014,-.008,.35)]
    for cy,cx,halfwidth,bend,skew,depth in ([] if v4 else forehead_specs):
        q=(x-cx)/halfwidth
        taper=1-smooth(.57,1,np.abs(q))
        curve=cy+bend*q*q+skew*q+.005*q*q*q
        width=.012*(1+.16*q.clip(-1,1))
        wrinkles+=np.exp(-((y-curve)/width)**2)*forehead*taper*depth
    # Two short shallow crow's feet at each outer eye corner, asymmetrically weighted.
    corner=g(.555,7.22,1.28,.10,.075,.30)*smooth(.47,.52,ax)*(1-smooth(.59,.68,ax))
    for slope,offset,depth in ([] if v4 else [(-.35,-.002,.25),(.30,.007,.30)]):
        curve=7.215+offset+slope*(ax-.49)+.025*(ax-.53)**2
        wrinkles+=np.exp(-((y-curve)/.009)**2)*corner*depth*(1+.10*x)
    crease=np.exp(-((ax-(.19+.51*(6.98-y)+.014*np.sin(y*13)))/.022)**2)*g(.3,6.79,1.4,.26,.34,.45)
    wrinkles+=crease*1.1
    wrinkles+=g(.34,7.04,1.32,.24,.016,.32)*.7
    # No drawn neck creases: remove the horizontal seam-like relief strokes.
    lipcracks=lips*(.5+.5*np.sin(x*175+y*13))**16
    height=.5+detail*(pores*.0017+micro*.0007-wrinkles*.018-lipcracks*.003+bags*.006)
    rough=.61+.018*macro+.014*micro
    rough=rough*(1-forehead*.65)+.47*forehead*.65
    rough=rough*(1-nose)+.45*nose
    rough=rough*(1-lips)+.45*lips
    rough=rough*(1-hands)+.67*hands
    rough=rough*(1-scalp)+.71*scalp
    rough=rough*(1-beard*.8)+.71*beard*.8
    rough+=detail*(pores*.005+wrinkles*.018+spots*.025)
    # Snap mark anchors to real body vertices safely inside the UV island padding.
    vertices,uv,faces=mesh_data(meshpath)
    corners=np.array([q for face in faces for q in face]);uvp=uv[corners[:,1]]
    rr=np.clip(((1-uvp[:,1])*detail.shape[0]).astype(int),0,detail.shape[0]-1)
    cc=np.clip((uvp[:,0]*detail.shape[1]).astype(int),0,detail.shape[1]-1)
    safe=vertices[np.unique(corners[detail[rr,cc]>.8,0])]
    def snap(p):return safe[np.argmin(np.sum((safe-p)**2,axis=1))]
    # Healed scars: 2 facial signed-position capsules, no mirrored copy, no narrative.
    def stroke(a,b,width):
        d=np.array(b)-a;length2=float(d@d)
        t=np.clip(((x-a[0])*d[0]+(y-a[1])*d[1]+(z-a[2])*d[2])/length2,0,1)
        return np.exp(-.5*((x-a[0]-t*d[0])**2+(y-a[1]-t*d[1])**2+(z-a[2]-t*d[2])**2)/width**2)
    scar_segments=[((.32,7.32,1.34),(.29,7.49,1.25),.010),
                   ((-.50,6.86,1.29),(-.59,6.76,1.17),.011)]
    scars=np.zeros_like(x); scar_checks=[]
    for a,b,w in ([] if v4 else scar_segments):
        a=snap(a);b=snap(b)
        if np.linalg.norm(a-b)<.025:b=snap(np.array(b)+[0,.06,0])
        mark=stroke(a,b,w)*detail
        scar_checks.append({'a':a.tolist(),'b':b.tolist(),'width_source':w,'max_mask':float(mark.max()),'pixels_gt_025':int((mark>.25).sum())})
        assert mark.max()>.3 and (mark>.25).sum()>4,'Scar missed UV interior'
        scars+=mark
    scars=np.clip(scars,0,1)
    paint(scars,[188,158,135],.40)
    rough=rough*(1-scars)+.43*scars
    height=height*(1-scars)+(.5-.0035)*scars
    # Two small asymmetric moles: cheek and opposite side of neck.
    moles=np.zeros_like(x);mole_checks=[]
    for p,sx,sy in [((.56,6.94,1.29),.013,.014),((-.33,5.92,.77),.017,.018)]:
        c=snap(p);mark=g(*c,sx,sy,.055,False)*detail
        mole_checks.append({'center':c.tolist(),'max_mask':float(mark.max()),'pixels_gt_025':int((mark>.25).sum())})
        assert mark.max()>.3 and (mark>.25).sum()>1,'Mole missed UV interior'
        moles+=mark
    paint(moles,[77,55,40],.88)
    # Hands: only soft joint/callus fields, never strokes, sine creases, veins or tendons.
    vertices,_,_=mesh_data(meshpath);joints={};group=''
    for line in open(meshpath):
        tok=line.split()
        if not tok:continue
        if tok[0]=='g':group=tok[1]
        elif tok[0]=='f' and group.startswith('joint-l-'):
            joints.setdefault(group,[]).extend(int(t.split('/')[0])-1 for t in tok[1:])
    def joint(name):return vertices[np.unique(joints[name])].mean(0)
    knuckles=np.zeros_like(x)
    for f in range(1,6):
        for j in [1,2]:
            c=joint(f'joint-l-finger-{f}-{j}');knuckles+=g(*c,.11,.10,.12)*hands
    knuckles=np.clip(knuckles,0,1)
    height+=detail*knuckles*.0018
    paint(knuckles,[130,96,73],.20)
    paint(hands*(1-dorsal),[180,145,125],.42)
    recesses=g(4.46,1.99,2.65,.10,.14,.13)+g(4.65,1.85,2.4,.10,.14,.16)+g(4.15,2.18,2.45,.13,.12,.18)
    dirt=hands*(.08+.20*np.clip(recesses,0,1))*detail
    paint(dirt,[83,69,48],.25)
    rough=np.clip(rough+knuckles*.020,0,1)
    # Short nails retain pale keratin; their distal margins collect dirt.
    for f in range(1,6):
        tip=joint(f'joint-l-finger-{f}-4');base=joint(f'joint-l-finger-{f}-3');axis=tip-base;axis/=np.linalg.norm(axis)
        c=tip*.7+base*.3;c[0]+=.065 if f!=1 else -.05
        dx=ax-c[0];dy=y-c[1];dz=z-c[2];along=dx*axis[0]+dy*axis[1]+dz*axis[2]
        perp=np.maximum(dx*dx+dy*dy+dz*dz-along*along,0)
        plate=np.exp(-((along/.095)**4+(perp/.0045)**2))*hands
        paint(plate,[171,142,123],.75)
        edge=plate*np.exp(-((along-.063)/.024)**2)
        paint(edge,[73,62,43],.55)
        rough=rough*(1-plate*.6)+.48*plate*.6
    # Reapply the two healed facial scars after pigment layers; scar tissue remains smooth and pale.
    paint(scars,[188,158,135],.55)
    rough=rough*(1-scars)+.43*scars
    height=height*(1-scars)+(.5-.0035)*scars
    color+=detail[...,None]*(pores[...,None]*.60+micro[...,None]*.9)
    sss=np.clip(.25+.48*ears+.33*nose+.27*hands*smooth(4.15,4.55,ax)-.06*scalp,0,1)
    report={'version':3,'status':'PROTOTYPE_NOT_APPROVED','scars':scar_checks,'moles':mole_checks,
            'jaw_neck_blend_mm':.46*(1800/16.6589),'forehead_creases':3,'crowfeet_per_side':2,'neck_crease_strokes':False,'hand_lines':False,'veins':False,'tendons':False,'beard_lower_edge':'asymmetric curved field; 0.41 native units soft fade','recommended_normal_strength':.45,
            'scar_roughness':.43,'scar_height':.4965,'scar_tissue_rgb':[188,158,135],
            'tattoos':False,'fresh_wounds':False,'lighting_baked':False,
            'note':'Masks use native 3D coordinates. Counts confirm marks intersect the UV interior; artistic acceptance requires render review.'}
    if report_path is not None:report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return color,height,rough,sss
