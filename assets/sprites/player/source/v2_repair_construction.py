"""Powtórzone F3 po odrzuceniu niestabilnego drapowania i źle wyciętych paneli."""
import sys,math,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v2_common import *
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
import bmesh
assert bpy.context.scene.get('art_revision')=='v2-F3-fit-rest-01'
sc=bpy.context.scene;rig=bpy.data.objects['Bohater_RIG'];body=bpy.data.objects['Ciało / MakeHuman / UV natywne']
old_sim=sc['cloth_simulations'];sc['rejected_drape_provenance']=old_sim
for o in list(sc.objects):
    if o.get('p2_part'):bpy.data.objects.remove(o,do_unlink=True)
parts=[];used=set(i for p in body.data.polygons for i in p.vertices);vs=[v.co.copy() for v in body.data.vertices];kd=KDTree(len(used))
for i in used:kd.insert(vs[i],i)
kd.balance();tree=BVHTree.FromPolygons(vs,[tuple(p.vertices) for p in body.data.polygons])
mats={key:bpy.data.materials.get(label) for key,label in [('linen','TEMP / len do teksturowania P2'),('leather','TEMP / kaftan do teksturowania P2'),('wool','TEMP / wełna do teksturowania P2'),('pants','TEMP / spodnie do teksturowania P2'),('strap','TEMP / skóra pasów do P2'),('boot','TEMP / buty do P2'),('pack','TEMP / plecak do P2'),('metal','TEMP / żelazo do P2')]}
def finish(o,key,sub=1,solid=.002,bone=None):
    if not o.data.materials:o.data.materials.append(mats[key])
    if sub:m=o.modifiers.new('Powierzchnia / fałdy','SUBSURF');m.levels=sub;m.render_levels=sub
    if solid:m=o.modifiers.new('Grubość warstwy','SOLIDIFY');m.thickness=solid;m.offset=0
    if bone:g=o.vertex_groups.new(name=bone);g.add(list(range(len(o.data.vertices))),1,'REPLACE')
    else:
        groups={}
        for v in o.data.vertices:
            _,i,_=kd.find(v.co)
            for g in body.data.vertices[i].groups:
                name=body.vertex_groups[g.group].name
                if name not in groups:groups[name]=o.vertex_groups.new(name=name)
                groups[name].add([v.index],g.weight,'REPLACE')
    m=o.modifiers.new('MakeHuman 163 / deformacja','ARMATURE');m.object=rig;m.use_deform_preserve_volume=True;o.parent=rig;o['p2_part']=True;o['temporary_materials']=True;parts.append(o);return o
def grid(name,rows,key,closed=False,cut=None):
    vv=[tuple(p) for r in rows for p in r];n=len(rows[0]);ff=[]
    for j in range(len(rows)-1):
        for i in range(n if closed else n-1):
            a=j*n+i;b=j*n+(i+1)%n;f=(a,b,b+n,a+n);c=sum((Vector(vv[k]) for k in f),Vector())/4
            if cut is None or not cut(c):ff.append(tuple(reversed(f)))
    o=mesh(name,vv,ff,mats[key]);o['grid_nu']=n;o['grid_nv']=len(rows);return o
def body_front(y,z):
    hit=tree.ray_cast(Vector((1,y,z)),Vector((-1,0,0)),2)[0];return hit.x if hit is not None else .12
def group_weight(poly,prefixes):
    return sum(g.weight for i in poly.vertices for g in body.data.vertices[i].groups if body.vertex_groups[g.group].name.startswith(prefixes))/len(poly.vertices)
# Koszula: luźna skorupa tylko TUŁOWIA i RAMION, bez fragmentów dłoni.
fs=[p for p in body.data.polygons if 1.035<p.center.z<1.535 and not (p.center.x>.04 and p.center.z>1.43+abs(p.center.y)*.65) and (abs(p.center.y)<.20 or p.center.z>1.205) and group_weight(p,('finger','wrist'))<.1]
ids=sorted(set(i for p in fs for i in p.vertices));remap={old:i for i,old in enumerate(ids)};vv=[]
for i in ids:
    p=vs[i];normal=body.data.vertices[i].normal;v=p+normal*(.025+.0015*math.sin(p.z*82+p.y*25)**2)
    if p.z<1.42 and abs(p.y)<.16 and p.x>.03:v.x=max(v.x,.165+.004*math.cos(p.z*30))
    vv.append(tuple(v))
shirt=finish(mesh('koszula',vv,[tuple(remap[i] for i in p.vertices) for p in fs],mats['linen']),'linen');shirt['construction']='Jedna siatka: lniany korpus, rozpięty dekolt, rękawy do łokcia; bez rękawic i obręczy na nadgarstkach.'
# Spodnie wyłącznie z miednicy/nóg; swobodne nogawki, bez skopiowanych dłoni.
fs=[p for p in body.data.polygons if .48<p.center.z<1.105 and group_weight(p,('upperleg','lowerleg','pelvis','spine05','root'))>.45 and group_weight(p,('finger','wrist','lowerarm','upperarm'))<.05]
ids=sorted(set(i for p in fs for i in p.vertices));remap={old:i for i,old in enumerate(ids)};vv=[]
for i in ids:
    p=vs[i];n=body.data.vertices[i].normal;vv.append(tuple(p+n*(.020+.003*math.sin(p.z*70+abs(p.y)*25)**2)))
pants=finish(mesh('spodnie',vv,[tuple(remap[i] for i in p.vertices) for p in fs],mats['pants']),'pants');pants['construction']='Pełne spodnie z dwóch nogawek połączonych w kroku; wykluczone wszystkie wagi rąk.'
# Kaftan z uszytych paneli o wspólnej powierzchni, bez kopiowania kształtu mięśni piersi.
rows=[];nu=96;nv=43
for j in range(nv):
    z=.88+j/(nv-1)*.61;row=[]
    for i in range(nu):
        a=math.tau*i/nu;ry=.222+.012*math.exp(-((z-1.30)/.13)**2)-.035*max(0,(z-1.40)/.09);front=.205-.04*max(0,(z-1.38)/.11);back=.158-.045*max(0,(z-1.38)/.11);rx=front if math.cos(a)>0 else back
        fold=.0025*math.sin(a*11+z*5)*math.exp(-((z-1.10)/.3)**2);row.append(((rx+fold)*math.cos(a),ry*math.sin(a),z))
    rows.append(row)
vest=grid('kaftan',rows,'leather',True,lambda c:(c.x>0 and (c.z>1.27+abs(c.y)*.95 or abs(c.y)<.008)) or (abs(c.y)>.18 and c.z>1.315));finish(vest,'leather',solid=.003,bone='spine03');vest['construction']='Cztery połączone panele kaftana; otwarty środek i dekolt V, wycięcia pach, dolne panele zachodzą na spodnie.'
def cloth(o,colliders):
    active(o);n=o['grid_nu'];g=o.vertex_groups.new(name='Przyszyte / pin');g.add(list(range(n*2)),1,'REPLACE')
    m=o.modifiers.new('Cloth / stabilne drapowanie','CLOTH');m.settings.quality=6;m.settings.mass=.28;m.settings.tension_stiffness=60;m.settings.compression_stiffness=60;m.settings.shear_stiffness=30;m.settings.bending_stiffness=1.2;m.settings.vertex_group_mass=g.name;m.settings.effector_weights.gravity=.35;m.settings.air_damping=5;m.collision_settings.distance_min=.006;m.collision_settings.collision_quality=6;m.collision_settings.use_self_collision=True;m.collision_settings.self_distance_min=.005
    mods=[]
    for c in colliders:
        mod=c.modifiers.new('Collision / tkanina','COLLISION');c.collision.thickness_outer=.006;mods.append((c,mod))
    original=[v.co.copy() for v in o.data.vertices];m.point_cache.frame_start=1;m.point_cache.frame_end=16
    for f in range(1,17):sc.frame_set(f);bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());temp=ev.to_mesh();ev.to_mesh_clear();print('CLOTH_FRAME',o.name,f,flush=True)
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();coords=[v.co.copy() for v in me.vertices];ev.to_mesh_clear();o.modifiers.remove(m)
    for v,p in zip(o.data.vertices,coords):v.co=p
    for c,m in mods:c.modifiers.remove(m)
    sc.frame_set(1);o['cloth_simulation']=json.dumps({'solver':'Blender 4.3 Cloth','frames':[1,16],'quality':6,'gravity_factor':.35,'collision_quality':6,'distance_min_m':.006,'colliders':[c.name for c in colliders],'pin_vertices':n*2,'max_displacement_m':max((a-b).length for a,b in zip(original,coords)),'cache':'Wynik utrwalony w siatce, bez zewnętrznego cache.'});finish(o,'wool',solid=.003,bone='spine02');return o
rows=[];nu=65;nv=39
for j in range(nv):
    t=j/(nv-1);edge=1.35+.52*min(1,t/.12);row=[]
    for i in range(nu):
        a=edge+i/(nu-1)*(math.tau-2*edge);fold=.014*math.sin(a*9+.3)*(.45+.55*t);rx=.220+.022*t;ry=.31+.015*t;z=1.48-1.22*t
        if t>.9:z+=(t-.9)*(.24*math.sin(i*2.2)+.10*math.cos(i*4.7))
        row.append(((rx+fold)*math.cos(a), (ry+fold)*math.sin(a),z))
    rows.append(row)
cloak=cloth(grid('plaszcz',rows,'wool'),[body,shirt,vest,pants]);cloak['construction']='Płaszcz z otwarciem po bokach i z przodu, pionowe fałdy, postrzępiony dół.'
rows=[];nu=57;nv=19
for j in range(nv):
    t=j/(nv-1);row=[]
    for i in range(nu):
        a=.85+.35*t+i/(nu-1)*(math.tau-2*(.85+.35*t));rx=.10+.16*math.sin(t*math.pi/2);ry=.12+.235*math.sin(t*math.pi/2)
        row.append(((rx+.004*t*math.sin(a*10))*math.cos(a),ry*math.sin(a),1.565-.225*t))
    rows.append(row)
mantle=cloth(grid('peleryna',rows,'wool'),[body,shirt,vest,cloak])
rows=[];nu=57;nv=15
for j in range(nv):
    t=j/(nv-1);row=[]
    for i in range(nu):
        a=.90+i/(nu-1)*(math.tau-1.8);rx=.085+.105*math.sin(t*math.pi/2);ry=.09+.07*math.sin(t*math.pi/2)
        row.append((rx*math.cos(a)-.012*t,ry*math.sin(a),1.607+.012*math.sin(t*math.pi)-.037*t))
    rows.append(row)
hood=cloth(grid('kaptur',rows,'wool'),[body,shirt,vest,cloak,mantle])
# Dalsze części i UV dodaje v2_equipment.py, bez ponownego drapowania.
sc['cloth_simulations']=json.dumps([{'part':o.name,'simulation':json.loads(o['cloth_simulation'])} for o in [cloak,mantle,hood]])
save('v2-F3-stable-drape-02')
