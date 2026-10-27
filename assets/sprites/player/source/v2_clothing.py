"""F3, zapisane warstwy stroju. Nie uruchamiać przy eksporcie/renderze.

Wynik jest edytowalnym źródłem. Trzy oddzielne drapowania Cloth zostają
utrwalone w wierzchołkach i opisane w provenance, bez zależności od cache /tmp.
"""
import sys,math,json,random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v2_common import *
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
assert bpy.context.scene.get('art_revision')=='v2-F2-aged-head'
body=bpy.data.objects['Ciało / MakeHuman / UV natywne'];rig=bpy.data.objects['Bohater_RIG'];rng=random.Random(1721);parts=[]
# Osadzenie oczu: mniejsza anatomiczna kula głębiej pod powieką, a nie wystający glob.
for side in ['L','R']:
    center=rig.data.bones['eye.'+side].head_local.copy()
    for o in bpy.data.objects:
        if o.type=='MESH' and o.name.startswith('Oko /') and o.name.endswith('.'+side):
            for v in o.data.vertices:v.co=center+(v.co-center)*.60+Vector((.006,0,.0015))
# Ciemne włosy z siwizną, bez jasnej dominującej czapy.
bpy.data.materials['Włókna / siwizna'].node_tree.nodes.get('Principled Hair BSDF').inputs['Color'].default_value=(.13,.14,.13,1)
# Stopy pozostają pełne, ale mieszczą się wewnątrz podeszwy.
used=set(i for p in body.data.polygons for i in p.vertices)
for v in body.data.vertices:
    if v.index in used and v.co.z<.07:v.co.z+=.018*max(0,1-v.co.z/.07)
body.data.update();bpy.context.view_layer.update()
vertices=[v.co.copy() for v in body.data.vertices];tree=BVHTree.FromPolygons(vertices,[tuple(p.vertices) for p in body.data.polygons]);kd=KDTree(len(used))
for i in used:kd.insert(vertices[i],i)
kd.balance()
linen=plain('TEMP / len do teksturowania P2',(.27,.245,.19),.88)
leather=plain('TEMP / kaftan do teksturowania P2',(.075,.039,.022),.72)
wool=plain('TEMP / wełna do teksturowania P2',(.045,.036,.027),.95)
pantsmat=plain('TEMP / spodnie do teksturowania P2',(.065,.057,.044),.93)
strapmat=plain('TEMP / skóra pasów do P2',(.055,.027,.013),.72)
bootmat=plain('TEMP / buty do P2',(.045,.024,.013),.76)
packmat=plain('TEMP / plecak do P2',(.078,.043,.023),.79)
metal=plain('TEMP / żelazo do P2',(.24,.26,.27),.43,.9)
def finish(o,mat,solid=.002,sub=1,bind=True):
    if not o.data.materials:o.data.materials.append(mat)
    if sub:
        m=o.modifiers.new('Fałdy / powierzchnia','SUBSURF');m.levels=sub;m.render_levels=sub
    if solid:
        m=o.modifiers.new('Rzeczywista grubość','SOLIDIFY');m.thickness=solid;m.offset=0
    if bind:
        groups={}
        for v in o.data.vertices:
            _,idx,_=kd.find(v.co)
            for g in body.data.vertices[idx].groups:
                name=body.vertex_groups[g.group].name
                if name not in groups:groups[name]=o.vertex_groups.new(name=name)
                groups[name].add([v.index],g.weight,'REPLACE')
        m=o.modifiers.new('163 kości / transfer wag ciała','ARMATURE');m.object=rig;m.use_deform_preserve_volume=True;o.parent=rig
    o['p2_part']=True;o['temporary_materials']=True;parts.append(o);return o
def shell(name,test,offset,mat):
    fs=[p for p in body.data.polygons if test(p.center)];ids=sorted(set(i for p in fs for i in p.vertices));idx={old:i for i,old in enumerate(ids)};vv=[]
    for i in ids:
        p=vertices[i];normal=body.data.vertices[i].normal;amount=offset(p)
        vv.append(tuple(p+normal*amount))
    o=mesh(name,vv,[tuple(idx[i] for i in p.vertices) for p in fs],mat);return finish(o,mat)
shirt=shell('koszula',lambda c:1.035<c.z<1.535 and not (c.x>.04 and c.z>1.43+abs(c.y)*.65) and (abs(c.y)<.20 or c.z>1.205),lambda p:.028+.0025*math.sin(p.z*122+p.y*28)**2,linen)
shirt['construction']='Jedna powierzchnia koszuli i rękawów; otwarty dekolt; rękawy do łokci, odsłonięte przedramiona.'
trousers=shell('spodnie',lambda c:.48<c.z<1.105,lambda p:.014+.008*math.sin(p.z*82+abs(p.y)*17)**2,pantsmat)
vest=shell('kaftan',lambda c:.885<c.z<1.485 and abs(c.y)<.207 and not (c.x>.04 and (c.z>1.28+abs(c.y)*.95 or abs(c.y)<.009)),lambda p:.048+.0015*math.cos(p.z*75+p.y*20),leather)
def grid(name,rows,mat,closed=False):
    vv=[p for row in rows for p in row];n=len(rows[0]);ff=[]
    for j in range(len(rows)-1):
        for i in range(n if closed else n-1):a=j*n+i;b=j*n+(i+1)%n;ff.append((a,b,b+n,a+n))
    return mesh(name,vv,ff,mat)
def cloth(name,rows,pinned,mat,colliders):
    o=grid(name,rows,mat);active(o);g=o.vertex_groups.new(name='Przyszyte / pin');g.add(pinned,1,'REPLACE');m=o.modifiers.new('Cloth / drapowanie z kolizjami','CLOTH');m.settings.quality=8;m.settings.mass=.34;m.settings.tension_stiffness=28;m.settings.compression_stiffness=28;m.settings.shear_stiffness=12;m.settings.bending_stiffness=.6;m.settings.vertex_group_mass=g.name;m.settings.air_damping=3
    m.collision_settings.use_collision=True;m.collision_settings.distance_min=.009;m.collision_settings.collision_quality=6;m.collision_settings.use_self_collision=True;m.collision_settings.self_distance_min=.008
    mods=[]
    for c in colliders:
        mod=c.modifiers.new('Collision / drapowanie','COLLISION');c.collision.thickness_outer=.009;mods.append((c,mod))
    sc=bpy.context.scene;m.point_cache.frame_start=1;m.point_cache.frame_end=36
    for frame in range(1,37):sc.frame_set(frame);bpy.context.view_layer.update();o.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh_clear()
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();pos=[v.co.copy() for v in me.vertices];ev.to_mesh_clear();o.modifiers.remove(m)
    for v,p in zip(o.data.vertices,pos):v.co=p
    for c,mod in mods:c.modifiers.remove(mod)
    sc.frame_set(1);o['cloth_simulation']=json.dumps({'solver':'Blender 4.3 Cloth','frames':[1,36],'quality':8,'collision_quality':6,'distance_min_m':.009,'colliders':[c.name for c in colliders],'pin_vertices':len(pinned),'cache':'Utrwalony wynik w siatce; cache niepotrzebny.'});finish(o,mat,.003,1);return o
# Płaszcz otwarty z przodu; szeroka góra, pionowe fałdy i nieregularny dół.
rows=[];nu=65;nv=43
for j in range(nv):
    t=j/(nv-1);row=[]
    for i in range(nu):
        u=i/(nu-1);a=.78+u*(math.tau-1.56);fold=.012*math.sin(a*10+.2)*(.25+.75*t);rx=.19+.06*t;ry=.255+.045*t
        z=1.46-1.17*t
        if j>nv-4:z+=(.026*math.sin(i*2.2)+.014*math.cos(i*4.7))*((j-(nv-4))/3)
        row.append(((rx+fold)*math.cos(a)-.012*t,(ry+fold)*math.sin(a),z))
    rows.append(row)
cloak=cloth('plaszcz',rows,list(range(nu*2)),wool,[body,shirt,trousers,vest]);cloak['construction']='Długi otwarty płaszcz; pionowe fałdy; poszarpany dolny krój. Symulacja utrwalona.'
rows=[];nu=57;nv=17
for j in range(nv):
    t=j/(nv-1);row=[]
    for i in range(nu):
        a=.92+i/(nu-1)*(math.tau-1.84);r=.004*math.sin(a*12)*t
        row.append(((.105+.145*t+r)*math.cos(a),(.128+.185*t+r)*math.sin(a),1.54-.205*t+.01*math.cos(a)))
    rows.append(row)
mantle=cloth('peleryna',rows,list(range(nu*2)),wool,[body,shirt,vest,cloak])
rows=[];nu=57;nv=17
for j in range(nv):
    t=j/(nv-1);row=[]
    for i in range(nu):
        a=.82+i/(nu-1)*(math.tau-1.64);rx=.074+.075*math.sin(t*math.pi/2);ry=.081+.055*math.sin(t*math.pi/2)
        row.append((rx*math.cos(a)-.015*t,ry*math.sin(a),1.577+.017*math.sin(t*math.pi)-.025*t))
    rows.append(row)
hood=cloth('kaptur',rows,list(range(nu*2)),wool,[body,shirt,vest,cloak,mantle])
# Cholewy z wywiniętym brzegiem, jedna siatka na but; stopa zakryta szerokim noskiem.
for side,sign in [('lewy',1),('prawy',-1)]:
    rings=[(.002,.055,.16,.067),(.024,.055,.16,.068),(.056,.050,.151,.069),(.09,.020,.109,.066),(.14,.003,.071,.067),(.25,.015,.071,.077),(.36,.023,.075,.084),(.485,.028,.08,.091),(.515,.028,.085,.096),(.529,.028,.092,.103),(.510,.028,.096,.106),(.495,.028,.095,.105)]
    rows=[];n=48
    for j,(z,cx,rx,ry) in enumerate(rings):
        cy=sign*(.183-.025*min(1,z/.5));row=[]
        for i in range(n):
            a=math.tau*i/n;wr=.002*math.cos(z*88+a*3) if .12<z<.48 else 0
            row.append((cx+(rx+wr)*math.cos(a),cy+(ry+wr)*math.sin(a),z))
        rows.append(row)
    o=grid('but_'+side,rows,bootmat,True);o.data.polygons.foreach_set('use_smooth',[True]*len(o.data.polygons));finish(o,bootmat,.003,1)
# Pasy/rzemienie leżą na rzeczywistej powierzchni kaftana, nie na idealnym cylindrze.
def front(y,z,offset=.06):
    hit=tree.ray_cast(Vector((1,y,z)),Vector((-1,0,0)),2)[0]
    return (hit.x if hit is not None else .11)+offset
def belt(name,z,width):
    rows=[];n=80
    for j in range(3):
        zz=z+(j/2-.5)*width;row=[]
        for i in range(n):
            a=math.tau*i/n;d=Vector((math.cos(a),math.sin(a),0));h=tree.ray_cast(Vector((0,0,zz)),d,1)[0];p=(h if h is not None else d*.15)+d*.058;p.z=zz;row.append(tuple(p))
        rows.append(row)
    return finish(grid(name,rows,strapmat,True),strapmat,.004,1)
belt('pas_gorny',1.12,.039);belt('pas_dolny',1.055,.031)
for k,sgn in enumerate([1,-1]):
    rows=[]
    for j in range(35):
        t=j/34;y=sgn*(.175-.33*t);z=1.425-.295*t;row=[]
        for f in [-.5,0,.5]:
            yy=y+f*.028;zz=z+f*.022;row.append((front(yy,zz,.065+k*.007),yy,zz))
        rows.append(row)
    finish(grid('rzemien_'+str(k+1),rows,strapmat),strapmat,.003,1)
def box(name,loc,scale,mat,bevel=.02):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=scale;active(o);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);m=o.modifiers.new('Miękkie szyte krawędzie','BEVEL');m.width=bevel;m.segments=3;bpy.ops.object.modifier_apply(modifier=m.name);return o
pack=box('plecak',(-.345,0,1.25),(.22,.33,.40),packmat,.045);finish(pack,packmat,.004,1);pack['construction']='Duży plecak, powierzchnia korpusu. Klapa, kieszenie i przeszycia oznaczone ID/UV dla teksturzysty.'
# Posłanie z miękkimi nieregularnymi przekrojami, bez jasnej idealnej spirali.
rows=[];n=48
for j in range(19):
    y=-.225+j/18*.45;row=[]
    for i in range(n):
        a=math.tau*i/n;r=.069+.0025*math.sin(a*8+y*35)+.0015*math.cos(y*60);row.append((-.35+r*math.cos(a),y,1.535+r*math.sin(a)))
    rows.append(row)
bed=grid('poslanie',rows,wool,True);finish(bed,wool,.004,1)
flask=box('manierka',(-.36,-.255,1.19),(.09,.105,.15),metal,.04);finish(flask,metal,.002,1)
for s in [1,-1]:
    o=box('sakwa_'+('lewa' if s>0 else 'prawa'),(.07,s*.236,1.02),(.075,.08,.115),packmat,.021);finish(o,packmat,.002,1)
# Pochwa i rękojeść; brak dobytej głowni w eksploracji (decyzja D1).
mouth=Vector((.12,.30,1.065));axis=Vector((-.16,.04,-.70));axis.normalize();across=Vector((1,0,0));across=(across-axis*across.dot(axis)).normalized();other=axis.cross(across).normalized();rows=[]
for j in range(24):
    t=j/23;center=mouth+axis*(.7*t);w=.020*(1-.45*t**8);row=[]
    for i in range(24):
        a=math.tau*i/24;row.append(tuple(center+across*w*math.cos(a)+other*.009*math.sin(a)))
    rows.append(row)
scabbard=grid('pochwa',rows,strapmat,True);finish(scabbard,strapmat,.003,1)
def cylinder_between(name,a,b,r,mat):
    d=b-a;bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=r,depth=d.length,location=(a+b)/2);o=bpy.context.object;o.name=name;o.rotation_euler=d.to_track_quat('Z','Y').to_euler();active(o);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);finish(o,mat,0,1);return o
cylinder_between('rekojesc',mouth-axis*.016,mouth-axis*.132,.013,strapmat)
cylinder_between('jelec',mouth-across*.075-axis*.007,mouth+across*.075-axis*.007,.006,metal)
bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=.019,location=mouth-axis*.145);o=bpy.context.object;o.name='glowica';active(o);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);finish(o,metal,0,1)
# Rozłożenie unikatowego UV; skala wyliczana z rzeczywistych powierzchni w metrach.
uv_report=[]
for o in parts:
    active(o);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.012,area_weight=1);bpy.ops.object.mode_set(mode='OBJECT')
    uv=o.data.uv_layers.active;area3=sum(p.area for p in o.data.polygons);area2=0
    for p in o.data.polygons:
        pp=[uv.data[i].uv for i in p.loop_indices]
        area2+=abs(sum(pp[i].x*pp[(i+1)%len(pp)].y-pp[(i+1)%len(pp)].x*pp[i].y for i in range(len(pp))))/2
    factor=min(1,math.sqrt(area3*(1024/2048)**2/max(area2,1e-12)))
    for u in uv.data:u.uv=(u.uv-Vector((.5,.5)))*factor+Vector((.5,.5))
    density=2048*math.sqrt(area2*factor**2/max(area3,1e-12));o['texture_resolution']=2048;o['texel_density_px_m']=density;o['uv_method']='Unikatowe wyspy Smart Project; skala z pola powierzchni. Bez rzutowania metrycznego.'
    uv_report.append({'part':o.name,'base_vertices':len(o.data.vertices),'base_faces':len(o.data.polygons),'area_m2':area3,'texel_density_px_m':density,'resolution':2048})
bpy.context.scene['cloth_simulations']=json.dumps([{'part':o.name,'simulation':json.loads(o['cloth_simulation'])} for o in [cloak,mantle,hood]])
bpy.context.scene['p2_uv_report']=json.dumps(uv_report)
save('v2-F3-clothing-first-drape')
print('V2_CLOTHING',json.dumps(uv_report),flush=True)
