"""Powtarzalny eksperyment bohatera. Uruchamiaj przez Blender 4.3, bez GUI.

blender -b -t 4 --python assets/sprites/player/source/build_player.py -- --pilot
Wszystkie odległości w metrach. Front = +X, lewa strona człowieka = +Y.
Siatka anatomii: MakeHuman CC0; pozostała geometria i animacja: ten generator.
"""
import argparse
import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
THIRD = HERE / 'third_party'
DIRS = ['S', 'SW', 'W', 'NW', 'N', 'NE', 'E', 'SE']
TAU = math.tau
PARTS = {}
REST = {}
ORIGINAL = {}
GEOMETRY = []
RIG = None
CAPE = None


def unit(v):
    v = Vector(v)
    return v.normalized()


def transform(a, b, c, d):
    """Rigid rotation plus translation; no rescaling of animated bones."""
    a, b, c, d = map(Vector, (a, b, c, d))
    rot = (b-a).rotation_difference(d-c).to_matrix().to_4x4()
    return Matrix.Translation(c) @ rot @ Matrix.Translation(-a)


def ik(a, target, l1, l2, pole):
    a, target, pole = map(Vector, (a, target, pole))
    delta = target-a
    reach = min(delta.length, l1+l2-0.00001)
    if delta.length > l1+l2+0.005:
        raise ValueError(f'IK poza zasięgiem: {delta.length-l1-l2:.4f} m')
    axis = delta.normalized()
    u = (reach*reach+l1*l1-l2*l2)/(2*reach)
    side = (pole-axis*pole.dot(axis)).normalized()
    return a+axis*u+side*math.sqrt(max(0, l1*l1-u*u))


def material(name, color, kind='cloth'):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    n, l = mat.node_tree.nodes, mat.node_tree.links
    bsdf = n.get('Principled BSDF')
    bsdf.inputs['Roughness'].default_value = {'cloth':.83,'leather':.47,'metal':.33,'skin':.62,'hair':.72}.get(kind,.8)
    bsdf.inputs['Metallic'].default_value = .92 if kind == 'metal' else 0
    bsdf.inputs['Specular IOR Level'].default_value = .25 if kind == 'cloth' else .35
    if kind == 'cloth':
        bsdf.inputs['Sheen Weight'].default_value = .2
        bsdf.inputs['Sheen Roughness'].default_value = .8
    if kind == 'skin':
        bsdf.inputs['Subsurface Weight'].default_value = .075
        bsdf.inputs['Subsurface Scale'].default_value = .012
    attr = n.new('ShaderNodeAttribute')
    attr.attribute_name = 'rest_position'
    noise = n.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 28 if kind != 'skin' else 45
    noise.inputs['Detail'].default_value = 3
    noise.inputs['Roughness'].default_value = .65
    l.new(attr.outputs['Vector'], noise.inputs['Vector'])
    ramp = n.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = .18
    ramp.color_ramp.elements[0].color = (*[c*.68 for c in color], 1)
    ramp.color_ramp.elements[1].position = .82
    ramp.color_ramp.elements[1].color = (*[c*1.18 for c in color], 1)
    l.new(noise.outputs['Fac'], ramp.inputs[0])
    l.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    fine = n.new('ShaderNodeTexNoise')
    fine.inputs['Scale'].default_value = 520 if kind == 'cloth' else 300
    fine.inputs['Detail'].default_value = 2
    l.new(attr.outputs['Vector'], fine.inputs['Vector'])
    bump = n.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = .24 if kind != 'skin' else .1
    bump.inputs['Distance'].default_value = .00065 if kind == 'cloth' else .00035
    l.new(fine.outputs['Fac'], bump.inputs['Height'])
    if kind == 'cloth':
        wave = n.new('ShaderNodeTexWave')
        wave.wave_type = 'BANDS'
        wave.bands_direction = 'Z'
        wave.inputs['Scale'].default_value = 620
        wave.inputs['Distortion'].default_value = 1.2
        l.new(attr.outputs['Vector'], wave.inputs['Vector'])
        l.new(wave.outputs['Color'], bump.inputs['Height'])
    l.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    return mat


def mesh(name, vertices, faces, mat, weights=None, sub=0, solid=0):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    if mat:
        data.materials.append(mat)
    for poly in data.polygons:
        poly.use_smooth = True
    attr = data.attributes.new('rest_position', 'FLOAT_VECTOR', 'POINT')
    for item, vertex in zip(attr.data, data.vertices):
        item.vector = vertex.co
    if weights:
        groups = {}
        for i, values in enumerate(weights):
            for bone, w in values.items():
                if w > .00001:
                    if bone not in groups:
                        groups[bone] = obj.vertex_groups.new(name=bone)
                    groups[bone].add([i], float(w), 'REPLACE')
        mod = obj.modifiers.new('Szkielet / stałe długości kości', 'ARMATURE')
        mod.object = RIG
        mod.use_deform_preserve_volume = True
        obj.parent = RIG
    if sub:
        mod = obj.modifiers.new('Gładka powierzchnia źródłowa', 'SUBSURF')
        mod.levels = sub
        mod.render_levels = sub
    if solid:
        mod = obj.modifiers.new('Grubość tkaniny', 'SOLIDIFY')
        mod.thickness = solid
    GEOMETRY.append(obj)
    return obj


def bone_weight(bone):
    return lambda _p: {bone: 1.0}


def torso_weight(p):
    z = p[2]
    if z > 1.37: return {'chest':1}
    if z < 1.03: return {'pelvis':1}
    if z < 1.18:
        t = (z-1.03)/.15
        return {'pelvis':1-t,'spine':t}
    t = (z-1.18)/.19
    return {'spine':1-t,'chest':t}


def loft(name, rings, mat, weight, count=48, sub=1, solid=0, wrinkles=0):
    """Elliptical tailored sections (z, x-center, y-center, x-radius, y-radius)."""
    verts=[]
    for j,(z,cx,cy,rx,ry) in enumerate(rings):
        for i in range(count):
            t=TAU*i/count
            dr=wrinkles*(math.sin(t*9+z*13)+.45*math.sin(t*17-z*25))
            verts.append((cx+(rx+dr)*math.cos(t),cy+(ry+dr)*math.sin(t),z))
    faces=[(j*count+i,j*count+(i+1)%count,(j+1)*count+(i+1)%count,(j+1)*count+i)
           for j in range(len(rings)-1) for i in range(count)]
    return mesh(name,verts,faces,mat,[weight(p) for p in verts],sub,solid)


def tube(name, points, radius, mat, weight, sides=8):
    verts=[]
    for j,p in enumerate(points):
        p=Vector(p)
        direction=Vector(points[min(j+1,len(points)-1)])-Vector(points[max(0,j-1)])
        axis=direction.normalized()
        tangent=axis.cross(Vector((0,0,1)))
        if tangent.length < .01: tangent=axis.cross(Vector((0,1,0)))
        tangent.normalize(); bitangent=axis.cross(tangent).normalized()
        r=radius[j] if isinstance(radius,list) else radius
        verts.extend([tuple(p+r*(math.cos(TAU*i/sides)*tangent+math.sin(TAU*i/sides)*bitangent)) for i in range(sides)])
    faces=[(j*sides+i,j*sides+(i+1)%sides,(j+1)*sides+(i+1)%sides,(j+1)*sides+i)
           for j in range(len(points)-1) for i in range(sides)]
    faces += [tuple(reversed(range(sides))), tuple((len(points)-1)*sides+i for i in range(sides))]
    return mesh(name,verts,faces,mat,[weight(p) for p in verts],1)


def ribbon(name, points, width, mat, weight, thickness=.003):
    verts=[]
    for i,p in enumerate(points):
        d=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(i-1,0)])
        side=Vector((0,-d.z,d.y)).normalized()*width/2
        verts.extend([tuple(Vector(p)-side),tuple(Vector(p)+side)])
    return mesh(name,verts,[(i*2,i*2+1,i*2+3,i*2+2) for i in range(len(points)-1)],mat,
                [weight(p) for p in verts],1,thickness)


def pillow(name, center, dims, mat, bone, roundness=.55):
    """A subdivided, irregular cloth/leather pack, not a hard box."""
    cx,cy,cz=center; dx,dy,dz=dims
    rings=[]
    for i in range(9):
        t=i/8
        r=max(.04,math.sin(math.pi*t))**roundness
        rings.append((cz+dz*(t-.5),cx,cy,dx/2*r,dy/2*r))
    return loft(name,rings,mat,bone_weight(bone),32,2,wrinkles=.002)


def load_anatomy():
    vertices=[]; faces=[]; groups=defaultdict(list); current=''
    for line in (THIRD/'base.obj').read_text().splitlines():
        if line.startswith('v '): vertices.append(tuple(map(float,line.split()[1:])))
        elif line.startswith('g '): current=line[2:]
        elif line.startswith('f '):
            f=tuple(int(p.split('/')[0])-1 for p in line.split()[1:])
            groups[current].append(f)
    raw=np.array(vertices)
    body_ids=np.unique(np.array(groups['body']).flatten())
    low,high=raw[body_ids,1].min(),raw[body_ids,1].max()
    scale=1.8/(high-low)
    v=np.column_stack([raw[:,2],raw[:,0],raw[:,1]-low])*scale
    skel=json.loads((THIRD/'default.mhskel').read_text())
    def joint(bone,end):
        return Vector(v[skel['joints'][skel['bones'][bone][end]]].mean(0))
    ORIGINAL.update({
        'pelvis':(Vector((.0133,0,.935)),joint('spine03','head')),
        'spine':(joint('spine03','head'),joint('spine01','head')),
        'chest':(joint('spine01','head'),joint('neck01','head')),
        'neck':(joint('neck01','head'),joint('head','head')),
        'head':(joint('head','head'),joint('head','tail'))})
    for side in ['L','R']:
        for name,start,end in [('upper_arm','upperarm01','upperarm02'),('forearm','lowerarm01','lowerarm02'),
                               ('thigh','upperleg01','upperleg02'),('shin','lowerleg01','lowerleg02')]:
            ORIGINAL[name+'.'+side]=(joint(start+'.'+side,'head'),joint(end+'.'+side,'tail'))
        ORIGINAL['hand.'+side]=(joint('wrist.'+side,'head'),joint('wrist.'+side,'tail'))
        ORIGINAL['foot.'+side]=(joint('foot.'+side,'head'),joint('foot.'+side,'tail'))
    REST.update({name:(a.copy(),b.copy()) for name,(a,b) in ORIGINAL.items()})
    for side,sign in [('L',1),('R',-1)]:
        shoulder=ORIGINAL['upper_arm.'+side][0]
        wrist=Vector((.075,sign*.265,.985))
        l1=(ORIGINAL['upper_arm.'+side][1]-shoulder).length
        l2=(ORIGINAL['forearm.'+side][1]-ORIGINAL['forearm.'+side][0]).length
        elbow=ik(shoulder,wrist,l1,l2,(-1,sign*.6,0))
        REST['upper_arm.'+side]=(shoulder,elbow)
        REST['forearm.'+side]=(elbow,wrist)
        oldhand=ORIGINAL['hand.'+side]
        handmat=transform(*ORIGINAL['forearm.'+side],elbow,wrist)
        REST['hand.'+side]=(wrist,handmat@oldhand[1])
        hip=ORIGINAL['thigh.'+side][0]
        knee=Vector((.027,sign*.125,.4833)); ankle=Vector((-.001,sign*.126,.0778))
        REST['thigh.'+side]=(hip,knee); REST['shin.'+side]=(knee,ankle)
        REST['foot.'+side]=(ankle,ankle+(ORIGINAL['foot.'+side][1]-ORIGINAL['foot.'+side][0]))
    def remap(name):
        suffix='.'+name.split('.')[-1] if name.endswith(('.L','.R')) else ''
        if name.startswith('upperarm'):return 'upper_arm'+suffix
        if name.startswith('lowerarm'):return 'forearm'+suffix
        if name.startswith(('wrist','finger','metacarpal')):return 'hand'+suffix
        if name.startswith('upperleg'):return 'thigh'+suffix
        if name.startswith('lowerleg'):return 'shin'+suffix
        if name.startswith(('foot','toe')):return 'foot'+suffix
        if name.startswith(('root','pelvis','spine04','spine05')):return 'pelvis'
        if name=='spine03':return 'spine'
        if name.startswith(('spine01','spine02','breast','clavicle','shoulder')):return 'chest'
        if name.startswith('neck'):return 'neck'
        return 'head'
    weights=[defaultdict(float) for _ in v]
    for name,entries in json.loads((THIRD/'default_weights.mhw').read_text())['weights'].items():
        for idx,w in entries: weights[idx][remap(name)]+=w
    mats={n:transform(*ORIGINAL[n],*REST[n]) for n in REST}
    new=[]
    for i,p in enumerate(v):
        total=sum(weights[i].values())
        if total < .00001:
            weights[i]={'head':1} if p[2]>1.55 else torso_weight(p)
        else: weights[i]={k:w/total for k,w in weights[i].items()}
        new.append(sum(((mats[k]@Vector(p))*w for k,w in weights[i].items()), Vector((0,0,0))))
    return new,groups['body'],weights


def create_rig():
    global RIG
    data=bpy.data.armatures.new('Welesza / szkielet deformujący')
    RIG=bpy.data.objects.new('Bohater_RIG',data)
    bpy.context.collection.objects.link(RIG)
    bpy.context.view_layer.objects.active=RIG
    RIG.select_set(True); bpy.ops.object.mode_set(mode='EDIT')
    parents={'spine':'pelvis','chest':'spine','neck':'chest','head':'neck'}
    for side in ['L','R']:
        parents.update({'upper_arm.'+side:'chest','forearm.'+side:'upper_arm.'+side,
                        'hand.'+side:'forearm.'+side,'thigh.'+side:'pelvis',
                        'shin.'+side:'thigh.'+side,'foot.'+side:'shin.'+side})
    for name,(head,tail) in REST.items():
        b=data.edit_bones.new(name); b.head=head; b.tail=tail
        b.use_deform=True
    for name,parent in parents.items():data.edit_bones[name].parent=data.edit_bones[parent]
    bpy.ops.object.mode_set(mode='OBJECT')
    RIG.select_set(False); RIG.show_in_front=True


def subset(name, v, faces, weights, mat, select, offset=0, sub=1, cloth=False):
    selected=[f for f in faces if select(np.mean([v[i] for i in f],axis=0), f)]
    ids=sorted({i for f in selected for i in f}); idx={old:i for i,old in enumerate(ids)}
    obj=mesh(name,[v[i] for i in ids],[tuple(idx[i] for i in f) for f in selected],mat,
             [weights[i] for i in ids],0)
    normals=[vert.normal.copy() for vert in obj.data.vertices]
    for vertex,normal in zip(obj.data.vertices,normals):
        p=vertex.co.copy()
        displacement=offset
        if cloth:
            # Anatomical shell relaxed into a garment; coherent folds, not random bumps.
            displacement += .0035*math.sin(p.z*85+math.atan2(p.y,p.x)*5)
            displacement += .002*math.sin(p.z*150-p.y*35)
            if abs(p.y)<.18 and 1.23<p.z<1.47 and p.x>.08:
                vertex.co.x=.10+(p.x-.10)*.4
        vertex.co+=normal*displacement
    attr=obj.data.attributes['rest_position']
    for a,vert in zip(attr.data,obj.data.vertices):a.vector=vert.co
    if sub:
        m=obj.modifiers.new('Powierzchnia organiczna','SUBSURF');m.levels=sub;m.render_levels=sub
    return obj


def build_character():
    global CAPE
    v, faces, weights=load_anatomy()
    create_rig()
    skin=material('Skóra / zmęczona podróżą',(.24,.155,.103),'skin')
    linen=material('Znoszony len',(.18,.145,.095))
    wool=material('Mokry płaszcz / szaro-oliwkowa wełna',(.072,.078,.052))
    dark=material('Spodnie / brunatna wełna',(.065,.060,.048))
    leather=material('Skóra / kaftan i sakwa',(.079,.049,.027),'leather')
    edge=material('Przetarte brzegi skóry',(.15,.107,.065),'leather')
    boots=material('Skóra butów / wilgoć',(.052,.037,.023),'leather')
    iron=material('Kute żelazo',(.25,.26,.26),'metal')
    blade=material('Szlifowane krawędzie',(.46,.48,.47),'metal')
    hair=material('Ciemne włosy',(.023,.017,.012),'hair')
    seam=material('Konopna nić',(.19,.165,.11))
    PARTS.update(locals())
    subset('Anatomiczna głowa, szyja i lewa dłoń',v,faces,weights,skin,
            lambda p,f:p[2]>1.49 or (p[1]>.22 and p[2]<.98),sub=2)
    def arm_face(f):
        return np.mean([sum(weights[i].get(b+'.'+s,0) for b in ['upper_arm','forearm'] for s in ['L','R']) for i in f])>.3
    subset('Lniana koszula / luźne rękawy',v,faces,weights,linen,
            lambda p,f:.99<p[2]<1.49 and arm_face(f) and not any(weights[i].get('hand.L',0)+weights[i].get('hand.R',0)>.5 for i in f),
            offset=.022,sub=2,cloth=True)
    subset('Spodnie / marszczenia kolan',v,faces,weights,dark,
            lambda p,f:.25<p[2]<1.08 and not any(sum(weights[i].get(b+'.'+s,0) for b in ['hand','forearm','upper_arm'] for s in ['L','R'])>.1 for i in f),
            offset=.019,sub=2,cloth=True)
    tunic=loft('Lniana tunika / krój i pionowe fałdy',[
         (.78,.015,0,.157,.207),(.80,.015,0,.155,.204),(.91,.015,0,.144,.193),
         (1.02,.015,0,.128,.174),(1.11,.015,0,.145,.180),(1.26,.015,0,.151,.193),
         (1.40,.015,0,.126,.214),(1.475,.015,0,.097,.19),(1.525,.015,0,.060,.095)],
         linen,torso_weight,wrinkles=.0045,solid=.003,count=64,sub=2)
    # A real vest pattern rather than an inflated copy of the bare chest.
    vest_profile=[(1.055,.154,.192),(1.12,.159,.189),(1.24,.162,.196),
                  (1.35,.146,.211),(1.435,.120,.221),(1.493,.079,.144)]
    vv=[]; steps=49
    for j,(z,rx,ry) in enumerate(vest_profile):
        gap=math.radians(10+max(0,(z-1.28)/.213)*50)
        for i in range(steps):
            a=gap+(TAU-2*gap)*i/(steps-1)
            fold=.0025*math.sin(a*7+z*38)
            vv.append((.016+(rx+fold)*math.cos(a),(ry+fold)*math.sin(a),z))
    vf=[(j*steps+i,j*steps+i+1,(j+1)*steps+i+1,(j+1)*steps+i) for j in range(len(vest_profile)-1) for i in range(steps-1)]
    mesh('Kaftan / zszywane otwarte połacie',vv,vf,leather,[torso_weight(p) for p in vv],2,.005)
    for sign in [-1,1]:
        pts=[]
        for z,rx,ry in vest_profile:
            a=math.radians(10+max(0,(z-1.28)/.213)*50)
            pts.append((.021+rx*math.cos(a),sign*ry*math.sin(a),z))
        tube('Kaftan / przetarty brzeg',pts,.003,edge,torso_weight)
        tube('Kaftan / szew boku',[(.018,sign*(ry+.002),z) for z,rx,ry in vest_profile],.0015,seam,torso_weight)
    for z in [1.14,1.225,1.30]:
        tube('Wiązanie kaftana',[(.180,-.031,z),(.184,0,z-.008),(.180,.031,z)],.0025,edge,torso_weight)
    collar=[(.017+.067*math.cos(a),.094*math.sin(a),1.527-.012*math.cos(a)) for a in np.linspace(0,TAU,50)]
    tube('Miękki kołnierz lnu',collar,.006,linen,bone_weight('chest'))
    # Short travelling cloak: open front, layered shoulders, geometric folds and uneven hem.
    verts=[]; nr=25; na=65
    profile=[(1.56,.083,.101),(1.51,.13,.23),(1.46,.17,.255),(1.31,.19,.25),
             (1.10,.19,.26),(.88,.20,.275),(.82,.205,.28)]
    for j in range(nr):
        t=j/(nr-1); u=t*(len(profile)-1); k=min(int(u),len(profile)-2); f=u-k
        z,rx,ry=[profile[k][i]*(1-f)+profile[k+1][i]*f for i in range(3)]
        for i in range(na):
            th=math.radians(65+230*i/(na-1))
            fold=(.009*math.sin(th*11+t*3)+.004*math.sin(th*23-t*5))*math.sin(math.pi*t/2)
            hem=(.014*math.sin(th*19)+.006*math.sin(th*37))*t**9
            verts.append((-.025+(rx+fold)*math.cos(th),(ry+fold)*math.sin(th),z+hem))
    fs=[(j*na+i,j*na+i+1,(j+1)*na+i+1,(j+1)*na+i) for j in range(nr-1) for i in range(na-1)]
    CAPE=mesh('Krótki płaszcz / miękkie fałdy',verts,fs,wool,[torso_weight(p) for p in verts],2,.004)
    CAPE.shape_key_add(name='Spoczynek')
    for name,axis in [('Opóźnienie przód-tył',0),('Kołysanie boczne',1)]:
        key=CAPE.shape_key_add(name=name)
        for p,base in zip(key.data,verts):
            t=max(0,min(1,(1.48-base[2])/.66))
            p.co[axis]+=.035*t*t
            p.co.z+=.009*t*math.sin(base[1]*18)
    # Folded hood, behind an exposed head (not a rigid ring).
    verts=[]
    for j in range(13):
        t=j/12
        for i in range(33):
            a=math.radians(75+210*i/32)
            r=.075+.075*math.sin(math.pi*t)
            verts.append((-.045+r*math.cos(a),(.105+.03*math.sin(t*math.pi))*math.sin(a),
                          1.575-.16*t+.01*math.sin(a*8)*math.sin(t*math.pi)))
    fs=[(j*33+i,j*33+i+1,(j+1)*33+i+1,(j+1)*33+i) for j in range(12) for i in range(32)]
    mesh('Opuszczony kaptur / warstwy tkaniny',verts,fs,wool,[{'chest':1} for _ in verts],2,.004)
    # A second shoulder layer and its actual sewn edge provide a readable
    # garment construction, rather than detail made solely by shader noise.
    shoulder_cloth=material('Przetarta warstwa naramienna',(.092,.088,.062))
    sv=[]; sn=49
    for j in range(7):
        t=j/6; z=1.54-.27*t
        for i in range(sn):
            a=math.radians(70+220*i/(sn-1))
            rx=.103+.095*math.sin(t*math.pi/2)
            ry=.137+.137*math.sin(t*math.pi/2)
            fold=.006*math.sin(a*12+t*3)*t
            sv.append((-.025+(rx+fold)*math.cos(a),(ry+fold)*math.sin(a),z+.009*math.sin(a*21)*t**5))
    sf=[(j*sn+i,j*sn+i+1,(j+1)*sn+i+1,(j+1)*sn+i) for j in range(6) for i in range(sn-1)]
    mesh('Naramienna warstwa płaszcza',sv,sf,shoulder_cloth,[{'chest':1} for _ in sv],2,.003)
    tube('Obszycie warstwy naramiennej',sv[-sn:],.0018,seam,bone_weight('chest'))
    # Seams at the opening stay attached to the same skinning as the cloak.
    for side in [0,na-1]:
        pts=[tuple(CAPE.data.vertices[j*na+side].co) for j in range(nr)]
        tube('Płaszcz / boczny szew',pts,.0016,seam,torso_weight)
    # Scalp and stubble follow the anatomical surface, including the real nose and ears.
    subset('Włosy / krótki nieregularny obrys',v,faces,weights,hair,
            lambda p,f:p[2]>1.755+.008*math.sin(p[1]*65) or (p[2]>1.671 and p[0]<-.015),
            offset=.005,sub=2)
    stubble=material('Zarost / kilka dni podróży',(.083,.057,.036),'hair')
    subset('Zarost / anatomiczna żuchwa',v,faces,weights,stubble,
            lambda p,f:1.585<p[2]<1.655 and p[0]>.074 and abs(p[1])<.071 and not (p[0]>.132 and p[2]>1.641),
            offset=.0003,sub=1)
    # Tangible locks soften the hairline, avoiding a helmet-shaped scalp.
    rng=np.random.default_rng(73)
    for i in range(32):
        y=float(rng.uniform(-.065,.065)); z=1.773-.18*abs(y)
        tube('Pasmo włosów',[(.018,y,z+.013),(.054,y+.005,z+.008),(.075,y+.009,z-.004),(.084,y+.007,z-.031)],
             [.0035,.004,.003,.0006],hair,bone_weight('head'),5)
    # Eye globes remain subdued; no emissive eye material.
    for sign in [-1,1]:
        pillow('Oko',(.1346,sign*.03325,1.670),(.021,.020,.018),
               material('Oko / ciepła szarość',(.20,.175,.14),'skin'),'head')
        pillow('Tęczówka',(.145,sign*.03325,1.670),(.003,.009,.009),hair,'head')
    # Belt, functional chest strap, hand-stitched edging.
    loft('Pas skórzany',[(1.015,0,0,.150,.195),(1.02,0,0,.151,.196),
         (1.052,0,0,.145,.193),(1.057,0,0,.143,.191)],leather,torso_weight,solid=.005)
    buckle=[(.161,-.04,1.019),(.165,.018,1.019),(.165,.018,1.054),(.161,-.04,1.054),(.161,-.04,1.019)]
    tube('Sprzączka pasa',buckle,.004,iron,torso_weight)
    tube('Język sprzączki',[(.166,-.01,1.019),(.17,-.01,1.052)],.002,iron,torso_weight)
    points=[(.132,.145,1.485),(.166,.115,1.41),(.184,.065,1.31),(.185,0,1.22),
            (.175,-.075,1.13),(.154,-.137,1.065)]
    ribbon('Pas naramienny / nośny',points,.033,leather,torso_weight)
    tube('Szew pasa naramiennego',[(x+.003,y+.012,z) for x,y,z in points],.0012,seam,torso_weight)
    for sign in [-1,1]:
        pillow('Sakwa przy pasie',(.01,sign*.224,1.005),(.122,.095,.148),leather,'pelvis')
        tube('Sakwa / sznur',[(.065,sign*.22,.96),(.075,sign*.23,1.04),(.055,sign*.22,1.077)],.002,seam,bone_weight('pelvis'))
    pillow('Plecak podróżny',(-.248,0,1.285),(.18,.265,.30),leather,'chest',roundness=.24)
    pillow('Klapa plecaka',(-.33,0,1.36),(.048,.27,.16),edge,'chest',roundness=.24)
    for sign in [-1,1]:
        tube('Plecak / pionowy rzemień',[(-.30,sign*.079,1.43),(-.354,sign*.079,1.34),(-.346,sign*.079,1.2),(-.29,sign*.079,1.15)],.009,boots,bone_weight('chest'))
        tube('Plecak / sprzączka',[(-.357,sign*.079-.013,1.275),(-.357,sign*.079+.013,1.275),(-.357,sign*.079+.013,1.30),(-.357,sign*.079-.013,1.30),(-.357,sign*.079-.013,1.275)],.0025,iron,bone_weight('chest'))
    # Bedroll: real ends, seams and straps; its geometry is retained in .blend.
    pts=[(-.246,-.205+i*.41/20,1.498) for i in range(21)]
    tube('Zrolowane posłanie',pts,[.061+.003*math.sin(i*.7) for i in range(21)],linen,bone_weight('chest'),32)
    for sign in [-1,1]:
        a=np.linspace(0,math.pi*4.8,90)
        tube('Spirala posłania',[( -.246+(.006+.0035*t)*math.cos(t),sign*.208,1.498+(.006+.0035*t)*math.sin(t)) for t in a],.002,wool,bone_weight('chest'))
        tube('Rzemień posłania',[( -.246+.064*math.cos(t),sign*.128,1.498+.064*math.sin(t)) for t in np.linspace(0,TAU,40)],.008,leather,bone_weight('chest'))
    # Boots: full toe boxes, folded shafts, raised seams, soles and laces.
    for side,sign in [('L',1),('R',-1)]:
        cy=sign*.126
        foot='foot.'+side; shin='shin.'+side
        def bw(p,foot=foot,shin=shin):
            t=max(0,min(1,(p[2]-.14)/.14));return {foot:1-t,shin:t}
        loft('But / organiczna cholewka '+side,[(.07,.005,cy,.065,.061),(.10,0,cy,.056,.056),
             (.16,0,cy,.054,.055),(.22,.006,cy,.064,.063),(.30,.011,cy,.072,.067),(.315,.011,cy,.075,.07)],
             boots,bw,wrinkles=.0025,solid=.003)
        loft('But / nosek '+side,[(.016,.065,cy,.116,.054),(.027,.064,cy,.121,.06),
             (.060,.060,cy,.118,.061),(.09,.041,cy,.094,.052),(.115,.015,cy,.056,.047)],boots,bone_weight(foot),sub=2)
        loft('Podeszwa '+side,[(0,.065,cy,.119,.057),(.008,.065,cy,.121,.06),(.03,.065,cy,.120,.061)],dark,bone_weight(foot),sub=1)
        for z in [.17,.255,.305]:
            tube('Obszycie buta '+side,[(.01+.069*math.cos(t),cy+.067*math.sin(t),z+.003*math.sin(t*4)) for t in np.linspace(0,TAU,40)],.002,edge,bw)
        for i in range(5):
            z=.15+i*.028
            tube('Sznur buta '+side,[(.065,cy-.027,z),(.073,cy+.027,z+.022)],.0018,seam,bw)
            tube('Sznur buta '+side,[(.065,cy+.027,z),(.073,cy-.027,z+.022)],.0018,seam,bw)
    # Close leather glove around a physical sword grip.
    wrist=REST['hand.R'][0]
    palm=Vector((.10,-.269,.928))
    pillow('Prawa rękawica / dłoń',tuple(palm),(.065,.046,.093),leather,'hand.R')
    grip=Vector((.125,-.279,.906))
    sword_axis=unit((.21,-.07,-.975))
    sideways=unit((0,1,-.07))
    normal=sword_axis.cross(sideways).normalized()
    guard=grip+sword_axis*.079
    def swordp(x,y,z):return tuple(guard+normal*x+sideways*y+sword_axis*z)
    verts=[]
    for z,w,thick in [(0,.022,.004),(.07,.021,.004),(.57,.014,.003),(.70,.001,.001)]:
        verts.extend([swordp(thick,0,z),swordp(0,w,z),swordp(-thick,0,z),swordp(0,-w,z)])
    fs=[(j*4+i,j*4+(i+1)%4,(j+1)*4+(i+1)%4,(j+1)*4+i) for j in range(3) for i in range(4)]
    sword=mesh('Miecz / głownia z grzbietem',verts,fs,iron,[{'hand.R':1} for _ in verts])
    for sign in [-1,1]:
        tube('Szlif ostrza', [swordp(0,sign*w,z) for z,w in [(0,.022),(.07,.021),(.57,.014),(.70,0)]],
             [.0015,.0015,.0012,.0005],blade,bone_weight('hand.R'),6)
    tube('Jelec', [swordp(0,-.085,.004),swordp(.005,-.065,-.005),swordp(0,.065,-.005),swordp(0,.085,.004)],.009,iron,bone_weight('hand.R'))
    tube('Rękojeść', [swordp(0,0,-.15),swordp(0,0,-.01)],.013,boots,bone_weight('hand.R'),12)
    pillow('Głowica miecza',swordp(0,0,-.165),(.035,.035,.036),iron,'hand.R')
    for i in range(4):
        z=-.115+i*.018
        points=[swordp(x,y,z) for x,y in [(-.015,-.015),(.012,-.020),(.023,-.006),(.020,.012),(.007,.017)]]
        tube('Palec zgięty na rękojeści',points,.008,leather,bone_weight('hand.R'))
    # Wrist wrappings follow the forearm, never a floating ornament.
    for side,sign in [('L',1),('R',-1)]:
        w=REST['forearm.'+side][1]
        e=REST['forearm.'+side][0]
        axis=(e-w).normalized(); tangent=axis.cross(Vector((1,0,0))).normalized(); b=axis.cross(tangent)
        points=[tuple(w+axis*(.035+.055*t/(TAU*3))+ .031*(math.cos(t)*tangent+math.sin(t)*b)) for t in np.linspace(0,TAU*3,85)]
        tube('Owijka nadgarstka '+side,points,.006,linen,bone_weight('forearm.'+side))


def foot_target(phase, side, walking=True):
    sign=1 if side=='L' else -1
    if not walking:return Vector((.045 if sign==1 else -.045,sign*.126,.0778)),0
    p=(phase+(0 if side=='L' else .5))%1
    if p<.6:
        x=.26-.52*p/.6; lift=0; pitch=0
    else:
        s=(p-.6)/.4
        x=-.26+.52*(.5-.5*math.cos(math.pi*s)); lift=.10*math.sin(math.pi*s)
        pitch=.28*math.sin(TAU*s)
    return Vector((x,sign*.126,.0778+lift)),pitch


def set_pose(phase, walking=True, frame=None):
    bob=.006*math.cos(TAU*phase*2) if walking else .002*math.sin(TAU*phase)
    sway=.012*math.sin(TAU*phase) if walking else .002*math.sin(TAU*phase)
    pelvis=Vector((.0133,sway,(.887 if walking else .929)+bob))
    base=Vector((.0133,0,.935))
    bodyyaw=.04*math.sin(TAU*phase) if walking else .008*math.sin(TAU*phase)
    pmat=Matrix.Translation(pelvis)@Matrix.Rotation(bodyyaw,4,'Z')@Matrix.Translation(-base)
    chestpivot=REST['chest'][0]
    cm=pmat@Matrix.Translation(chestpivot)@Matrix.Rotation(-bodyyaw*1.7,4,'Z')@Matrix.Rotation(.035,4,'Y')@Matrix.Translation(-chestpivot)
    maps={'pelvis':pmat,'spine':pmat,'chest':cm,'neck':cm,'head':cm}
    audit={'feet':{}}
    for side,sign in [('L',1),('R',-1)]:
        th,sh='thigh.'+side,'shin.'+side
        hip=pmat@REST[th][0]
        ankle,pitch=foot_target(phase,side,walking)
        l1=(REST[th][1]-REST[th][0]).length;l2=(REST[sh][1]-REST[sh][0]).length
        knee=ik(hip,ankle,l1,l2,(1,0,0))
        maps[th]=transform(*REST[th],hip,knee);maps[sh]=transform(*REST[sh],knee,ankle)
        restfoot=REST['foot.'+side]
        rot=Matrix.Rotation(pitch,4,'Y')
        maps['foot.'+side]=Matrix.Translation(ankle)@rot@Matrix.Translation(-restfoot[0])
        shoulder=cm@REST['upper_arm.'+side][0]
        arm_phase=TAU*(phase+(0 if side=='L' else .5))
        hand=Vector((.075-(.105*math.cos(arm_phase) if walking else .002*math.sin(arm_phase)),
                     sign*(.265+( .008*math.sin(arm_phase) if walking else 0)),
                     .985+bob+(.012*math.sin(arm_phase) if walking else 0)))
        up,fore='upper_arm.'+side,'forearm.'+side
        l1=(REST[up][1]-REST[up][0]).length;l2=(REST[fore][1]-REST[fore][0]).length
        # Keep arm targets on their reachable sphere as equipment subtly swings.
        delta=hand-shoulder
        if delta.length>l1+l2-.007:hand=shoulder+delta.normalized()*(l1+l2-.007)
        elbow=ik(shoulder,hand,l1,l2,(-1,sign*.7,0))
        maps[up]=transform(*REST[up],shoulder,elbow);maps[fore]=transform(*REST[fore],elbow,hand)
        maps['hand.'+side]=maps[fore]
        p=(phase+(0 if side=='L' else .5))%1
        audit['feet'][side]={'ankle_m':list(ankle),'stance':bool(walking and p<.6),'pitch_rad':pitch}
    def depth(b):return 0 if b.parent is None else 1+depth(b.parent)
    desired={name:maps[name]@RIG.data.bones[name].matrix_local for name in maps}
    for b in sorted(RIG.pose.bones,key=depth):
        # Assign the basis from explicit parent/rest matrices. Setting .matrix
        # successively uses stale evaluated parents and disconnects joints.
        rest=b.bone.matrix_local
        if b.parent:
            b.matrix_basis=(rest.inverted() @ b.parent.bone.matrix_local
                            @ desired[b.parent.name].inverted() @ desired[b.name])
        else:
            b.matrix_basis=rest.inverted()@desired[b.name]
        b.rotation_mode='QUATERNION'
        if frame is not None:
            b.keyframe_insert('location',frame=frame)
            b.keyframe_insert('rotation_quaternion',frame=frame)
            b.keyframe_insert('scale',frame=frame)
    if CAPE:
        for i,key in enumerate(list(CAPE.data.shape_keys.key_blocks)[1:]):
            key.slider_min=-1
            key.value=(.55 if walking else .08)*math.sin(TAU*phase-i*.8)
            if frame is not None:key.keyframe_insert('value',frame=frame)
    bpy.context.view_layer.update()
    gaps=[];length_errors=[]
    for side in ['L','R']:
        for child,parent in [('forearm','upper_arm'),('hand','forearm'),('shin','thigh'),('foot','shin')]:
            gaps.append((RIG.pose.bones[child+'.'+side].head-RIG.pose.bones[parent+'.'+side].tail).length)
    for b in RIG.pose.bones:
        length_errors.append(abs((b.tail-b.head).length-b.bone.length))
    audit['max_joint_gap_m']=max(gaps)
    audit['max_bone_length_error_m']=max(length_errors)
    if audit['max_joint_gap_m']>.0001 or audit['max_bone_length_error_m']>.0001:
        raise ValueError('Niespójny szkielet: '+str(audit))
    return audit


def setup_scene(samples=64, size=384, lighting='base'):
    scene=bpy.context.scene
    scene.render.engine='CYCLES'
    scene.cycles.device='CPU';scene.cycles.samples=samples
    # Debian's Blender build has no OpenImageDenoise. Supersampling and actual
    # path samples keep this workflow reproducible without an unavailable module.
    scene.cycles.use_denoising=False
    scene.cycles.seed=1703
    scene.cycles.use_animated_seed=False
    scene.render.resolution_x=size;scene.render.resolution_y=size;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
    scene.render.image_settings.color_depth='8'
    scene.render.film_transparent=True
    scene.view_settings.view_transform='AgX'
    scene.world.color=(.11,.125,.15)
    scene.world.use_nodes=True
    bg=scene.world.node_tree.nodes.get('Background');bg.inputs[0].default_value=(.18,.21,.26,1);bg.inputs[1].default_value=.20
    scene.view_settings.look='AgX - Medium High Contrast'
    scene.view_settings.exposure=-.2
    camera=bpy.data.cameras.new('Kamera / zgodny kontrakt 30 stopni')
    obj=bpy.data.objects.new('Kamera',camera);bpy.context.collection.objects.link(obj)
    target=Vector((0,0,1.2));obj.location=target+Vector((8*math.cos(math.pi/6),0,4))
    obj.rotation_euler=(target-obj.location).to_track_quat('-Z','Y').to_euler()
    camera.type='ORTHO';camera.ortho_scale=3.2;camera.lens=50
    scene.camera=obj
    for name,pos,power,color,size in [
        ('Chłodne niebo / klucz z lewej', (2.8,-3.5,6),520,(.94,.92,.85),2.3),
        ('Odbite światło ziemi',(3,4,2.5),65,(.64,.68,.74),4),
        ('Chłodne niebo / tył',(-3,1,4),140,(.60,.70,.85),3)]:
        data=bpy.data.lights.new(name,'AREA');data.energy=power;data.color=color;data.shape='DISK';data.size=size
        lamp=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(lamp);lamp.location=pos
        lamp.rotation_euler=(Vector((0,0,1))-lamp.location).to_track_quat('-Z','Y').to_euler()
    if lighting=='warm':
        data=bpy.data.lights.new('Próba lokalnej pochodni','POINT')
        data.energy=85;data.color=(1,.33,.075);data.shadow_soft_size=.15
        lamp=bpy.data.objects.new(data.name,data);bpy.context.collection.objects.link(lamp)
        lamp.location=(1.2,-1.0,1.75)
    elif lighting=='cool':
        bpy.data.lights['Chłodne niebo / klucz z lewej'].color=(.63,.78,1)
    # Two view layers retain a pure character RGBA and a separate physically
    # rendered shadow in the same invocation. Ground never enters the sprite.
    body_layer=scene.view_layers[0];body_layer.name='Bohater'
    ground_collection=bpy.data.collections.new('Tylko odbiornik cienia')
    scene.collection.children.link(ground_collection)
    bpy.ops.mesh.primitive_plane_add(size=12,location=(0,0,-.001))
    ground=bpy.context.object;ground.name='Odbiornik cienia / poza atlasem postaci'
    for collection in list(ground.users_collection):collection.objects.unlink(ground)
    ground_collection.objects.link(ground);ground.is_shadow_catcher=True
    body_layer.layer_collection.children[ground_collection.name].exclude=True
    shadow_layer=scene.view_layers.new('Cień')
    shadow_layer.samples=16
    shadow_layer.cycles.use_pass_shadow_catcher=True
    scene.use_nodes=True
    nodes,links=scene.node_tree.nodes,scene.node_tree.links;nodes.clear()
    beauty=nodes.new('CompositorNodeRLayers');beauty.layer='Bohater'
    shadow=nodes.new('CompositorNodeRLayers');shadow.layer='Cień'
    composite=nodes.new('CompositorNodeComposite');links.new(beauty.outputs['Image'],composite.inputs[0])
    bw=nodes.new('CompositorNodeRGBToBW');links.new(shadow.outputs['Shadow Catcher'],bw.inputs[0])
    sub=nodes.new('CompositorNodeMath');sub.operation='SUBTRACT';sub.inputs[0].default_value=1;sub.use_clamp=True
    links.new(bw.outputs[0],sub.inputs[1])
    alpha=nodes.new('CompositorNodeSetAlpha');alpha.inputs[0].default_value=(0,0,0,1)
    links.new(sub.outputs[0],alpha.inputs[1])
    output=nodes.new('CompositorNodeOutputFile');output.name='Oddzielny cień'
    output.format.file_format='PNG';output.format.color_mode='RGBA'
    links.new(alpha.outputs[0],output.inputs[0])
    scene.render.threads_mode='FIXED';scene.render.threads=4
    scene.render.fps=25
    return scene


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--pilot',action='store_true')
    parser.add_argument('--all',action='store_true')
    parser.add_argument('--samples',type=int,default=64)
    parser.add_argument('--size',type=int,default=384)
    parser.add_argument('--directions',type=int,nargs='+',choices=range(8))
    parser.add_argument('--animations',nargs='+',choices=['spoczynek','chod'])
    parser.add_argument('--save-only',action='store_true')
    parser.add_argument('--lighting',choices=['base','warm','cool'],default='base')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    for file,meta in json.loads((THIRD/'manifest.json').read_text()).items():
        if hashlib.sha256((THIRD/file).read_bytes()).hexdigest()!=meta['sha256']:
            raise ValueError('Niezgodna suma źródła '+file)
    build_character();scene=setup_scene(args.samples,args.size,args.lighting)
    bpy.context.preferences.filepaths.save_version=0
    # Animations are genuine keyed armature actions, retained in the .blend.
    for name,count in [('spoczynek',8),('chod',12)]:
        RIG.animation_data_create();RIG.animation_data.action=bpy.data.actions.new(name)
        CAPE.data.shape_keys.animation_data_create()
        CAPE.data.shape_keys.animation_data.action=bpy.data.actions.new(name+' / płaszcz')
        CAPE.data.shape_keys.animation_data.action.use_fake_user=True
        step=2 if name=='chod' else 4.5  # 80 ms / 180 ms at 25 fps.
        for i in range(count+1):set_pose(i/count,name=='chod',frame=1+i*step)
        for curve in RIG.animation_data.action.fcurves:
            for key in curve.keyframe_points:key.interpolation='LINEAR'
        RIG.animation_data.action.use_fake_user=True
    RIG.animation_data.action=None
    CAPE.data.shape_keys.animation_data_clear()
    set_pose(0,False)
    scene.frame_start=1;scene.frame_end=25
    if args.lighting=='base':bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'bohater.blend'),check_existing=False)
    out=ROOT/'renders'
    if args.lighting!='base':out=out/args.lighting
    out.mkdir(exist_ok=True,parents=True)
    shadow_dir=out/'shadows';shadow_dir.mkdir(exist_ok=True)
    shadow_output=scene.node_tree.nodes['Oddzielny cień'];shadow_output.base_path=str(shadow_dir)
    audit={'directions':DIRS,'anchor_px':[96,158.35382907247958],
           'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           'render':{'blender':bpy.app.version_string,'engine':'CYCLES','samples':args.samples,
                     'shadow_samples':16,'size_px':args.size,'seed':1703,'denoising':False,
                     'threads':4,'lighting':args.lighting},'frames':{}}
    targets=[('spoczynek',1,[0,1,2,4,7])] if args.pilot else [('spoczynek',8,range(8)),('chod',12,range(8))]
    if args.animations:targets=[t for t in targets if t[0] in args.animations]
    if args.save_only:targets=[]
    for anim,count,directions in targets:
        if args.directions is not None:directions=args.directions
        for direction in directions:
            RIG.rotation_euler.z=-direction*math.pi/4
            for i in range(count):
                info=set_pose(i/count,anim=='chod')
                file=out/f'{anim}_{direction}_{i:02}.png'
                scene.render.filepath=str(file)
                shadow_output.file_slots[0].path=file.stem+'_'
                bpy.ops.render.render(write_still=True)
                shadow_file=shadow_dir/(file.stem+'_0001.png')
                shadow_file.replace(shadow_dir/file.name)
                audit['frames'][file.name]=info
                print('WELESZA_FRAME',file.name,flush=True)
                (out/'motion_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    RIG.rotation_euler.z=0
    RIG.animation_data.action=bpy.data.actions['chod']
    CAPE.data.shape_keys.animation_data_create()
    CAPE.data.shape_keys.animation_data.action=bpy.data.actions['chod / płaszcz']
    scene.frame_set(1)
    scene.render.filepath=str(ROOT/'previews'/'manual_render.png')
    shadow_output.file_slots[0].path='manual_shadow_'
    if args.lighting=='base':bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'bohater.blend'),check_existing=False)
    print('WELESZA_DONE',flush=True)


if __name__=='__main__':main()
