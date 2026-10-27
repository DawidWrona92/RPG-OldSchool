"""Utrwalenie swobodniejszej pozy i poprawek konstrukcji po drapowaniu F3."""
import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v2_common import *
assert bpy.context.scene.get('art_revision')=='v2-F3-clothing-first-drape'
rig=bpy.data.objects['Bohater_RIG'];body=bpy.data.objects['Ciało / MakeHuman / UV natywne']
for side in ['L','R']:
    center=rig.data.bones['eye.'+side].head_local+Vector((.006,0,-.002))
    for o in bpy.data.objects:
        if o.type!='MESH' or not o.name.startswith('Oko /') or not o.name.endswith('.'+side):continue
        for v in o.data.vertices:
            v.co.z-=.0035
            if 'tęczówka' in o.name or 'rogówka' in o.name:
                yy=(v.co.y-center.y)*1.2;zz=(v.co.z-center.z)*1.2;r=.01158 if 'tęczówka' in o.name else .01185
                v.co=Vector((center.x+math.sqrt(max(0,r*r-yy*yy-zz*zz)),center.y+yy,center.z+zz))
for name in ['pochwa','rekojesc','jelec','glowica','sakwa_lewa','sakwa_prawa','pas_gorny','pas_dolny']:
    o=bpy.data.objects[name];o.vertex_groups.clear();g=o.vertex_groups.new(name='spine05');g.add(list(range(len(o.data.vertices))),1,'REPLACE')
# Przedramiona były zbyt wysunięte w przód w odziedziczonej pozie A.
for side in ['L','R']:
    p=rig.pose.bones['lowerarm01.'+side];m=p.matrix.copy();p.matrix=Matrix.Translation(m.translation)@Matrix.Rotation(math.radians(32),4,'Y')@Matrix.Translation(-m.translation)@m;bpy.context.view_layer.update()
# Zachowaj bazową topologię i UV: przenieś wyłącznie współrzędne po ARMATURE.
for o in list(bpy.context.scene.objects):
    if o.type!='MESH':continue
    arms=[m for m in o.modifiers if m.type=='ARMATURE' and m.object==rig]
    if not arms:continue
    mod=arms[0];temp=o.copy();temp.data=o.data.copy();bpy.context.scene.collection.objects.link(temp)
    for m in list(temp.modifiers):
        if m.type!='ARMATURE':temp.modifiers.remove(m)
    bpy.context.view_layer.update();ev=temp.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();assert len(me.vertices)==len(o.data.vertices)
    for v,p in zip(o.data.vertices,me.vertices):v.co=p.co
    ev.to_mesh_clear();bpy.data.objects.remove(temp,do_unlink=True)
active(rig);bpy.ops.object.mode_set(mode='POSE');bpy.ops.pose.armature_apply(selected=False);bpy.ops.object.mode_set(mode='OBJECT')
for name in ['sakwa_lewa','sakwa_prawa']:
    o=bpy.data.objects[name]
    for v in o.data.vertices:v.co.y+=.025 if name.endswith('lewa') else -.025
# Worek z wypukłymi kieszeniami i klapą w JEDNEJ ciągłej powierzchni, nie nakładki-płytki.
pack=bpy.data.objects['plecak'];active(pack)
sub=pack.modifiers.new('Podział konstrukcyjny','SUBSURF');sub.levels=2;sub.render_levels=2;bpy.ops.object.modifier_apply(modifier=sub.name)
for v in pack.data.vertices:
    p=v.co
    if p.x<-.36:
        back=max(0,min(1,(-p.x-.36)/.07))
        pocket=math.exp(-((p.z-1.16)/.055)**4)*math.exp(-((abs(p.y)-.085)/.050)**4)
        flap=math.exp(-((p.z-1.34)/.055)**4)*math.exp(-(p.y/.125)**6)
        seam=math.exp(-((p.z-1.295)/.004)**2)*math.exp(-(p.y/.13)**6)
        p.x-=back*(.018*pocket+.010*flap-.003*seam)
pack.data.update()
# Podwinięcia w jednej powierzchni koszuli i wzmocnienie fałd przy łokciach.
shirt=bpy.data.objects['koszula']
for v in shirt.data.vertices:
    p=v.co
    if abs(p.y)>.205 and 1.20<p.z<1.24:
        v.co+=v.normal*(.007*math.sin(math.pi*(p.z-1.20)/.04)**2)
# Łata spodni jako milimetrowa miękka wypukłość, maskowana w P2 (bez osobnej płytki).
pants=bpy.data.objects['spodnie']
for v in pants.data.vertices:
    p=v.co
    if p.y>.10:v.co+=v.normal*(.0015*math.exp(-((p.z-.73)/.045)**6)*math.exp(-((p.y-.16)/.055)**6))
# Zamknięte podeszwy i materiałowe denka posłania (ciągłe brzegi części).
for name in ['but_lewy','but_prawy','poslanie']:
    o=bpy.data.objects[name];vv=[tuple(v.co) for v in o.data.vertices];ff=[tuple(p.vertices) for p in o.data.polygons];n=48
    rings=[list(range(n))]
    if name=='poslanie':rings.append(list(range(len(vv)-n,len(vv))))
    for ring in rings:
        center=sum((Vector(vv[i]) for i in ring),Vector())/n;idx=len(vv);vv.append(tuple(center))
        for i in range(n):ff.append((ring[(i+1)%n],ring[i],idx))
    old=o.data;new=bpy.data.meshes.new(name+' / zamknięte');new.from_pydata(vv,[],ff);new.update()
    for m in old.materials:new.materials.append(m)
    # Zachowaj grupy; dopisane środki otrzymują najbliższy zestaw wag.
    weights=[[(g.group,g.weight) for g in v.groups] for v in old.vertices];group_names=[g.name for g in o.vertex_groups];o.data=new
    o.vertex_groups.clear()
    for name in group_names:o.vertex_groups.new(name=name)
    for i,values in enumerate(weights):
        for group,w in values:o.vertex_groups[group].add([i],w,'REPLACE')
    for i in range(len(weights),len(vv)):
        nearest=min(range(len(weights)),key=lambda j:(Vector(vv[j])-Vector(vv[i])).length_squared)
        for group,w in weights[nearest]:o.vertex_groups[group].add([i],w,'REPLACE')
    for p in o.data.polygons:p.use_smooth=True
# Przelicz UV zagęszczonego plecaka i wszystkie gęstości po ustawieniu pozy.
for o in bpy.context.scene.objects:
    if not o.get('p2_part'):continue
    if o==pack or o.name in ['but_lewy','but_prawy','poslanie']:
        active(o);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.012,area_weight=1);bpy.ops.object.mode_set(mode='OBJECT')
    uv=o.data.uv_layers.active;area3=sum(p.area for p in o.data.polygons);area2=0
    for p in o.data.polygons:
        pp=[uv.data[i].uv for i in p.loop_indices];area2+=abs(sum(pp[i].x*pp[(i+1)%len(pp)].y-pp[(i+1)%len(pp)].x*pp[i].y for i in range(len(pp))))/2
    factor=min(1,math.sqrt(area3*(1024/2048)**2/max(area2,1e-12)))
    for u in uv.data:u.uv=(u.uv-Vector((.5,.5)))*factor+Vector((.5,.5))
    o['texel_density_px_m']=2048*math.sqrt(area2*factor**2/max(area3,1e-12))
rig['rest_note']='Natywny MakeHuman 163 kości; ramiona opuszczone 31° X, przedramiona cofnięte 32° Y; utrwalone rest, bez akcji.'
save('v2-F3-fit-rest-01')
