"""Pogłębiona korekta pach, wykroju kaftana i luzów wyposażenia po audycie."""
import sys,math,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v2_common import *
assert bpy.context.scene.get('art_revision')=='v2-F2-concept19-groom-02'
sc=bpy.context.scene;rig=bpy.data.objects['Bohater_RIG']
for side,sgn in [('L',1),('R',-1)]:
    p=rig.pose.bones['upperarm01.'+side];m=p.matrix.copy();p.matrix=Matrix.Translation(m.translation)@Matrix.Rotation(math.radians(sgn*6),4,'X')@Matrix.Translation(-m.translation)@m;bpy.context.view_layer.update()
    p=rig.pose.bones['lowerarm01.'+side];m=p.matrix.copy();p.matrix=Matrix.Translation(m.translation)@Matrix.Rotation(math.radians(-8),4,'Y')@Matrix.Translation(-m.translation)@m;bpy.context.view_layer.update()
for o in list(sc.objects):
    if o.type!='MESH' or not any(m.type=='ARMATURE' for m in o.modifiers):continue
    temp=o.copy();temp.data=o.data.copy();sc.collection.objects.link(temp)
    for m in list(temp.modifiers):
        if m.type!='ARMATURE':temp.modifiers.remove(m)
    bpy.context.view_layer.update();ev=temp.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    for v,p in zip(o.data.vertices,me.vertices):v.co=p.co
    ev.to_mesh_clear();bpy.data.objects.remove(temp,do_unlink=True)
active(rig);bpy.ops.object.mode_set(mode='POSE');bpy.ops.pose.armature_apply(selected=False);bpy.ops.object.mode_set(mode='OBJECT')
vest=bpy.data.objects['kaftan'];nu=96;nv=43
for v in vest.data.vertices:
    j,i=divmod(v.index,nu);z=.88+j/(nv-1)*.61;a=math.tau*i/nu;c=math.cos(a);ry=.205-.013*math.exp(-((z-1.27)/.15)**2);rx=(.205-.04*max(0,(z-1.38)/.11)) if c>=0 else .13;fold=.002*math.sin(a*11+z*5);v.co=((rx+fold)*math.copysign(abs(c)**(.40 if c>=0 else .8),c),ry*math.sin(a),z)
for name in ['pas_gorny','pas_dolny']:
    o=bpy.data.objects[name]
    for v in o.data.vertices:v.co.y*=.210/.246
for name,y in [('sakwa_lewa',.13),('sakwa_prawa',-.13)]:
    o=bpy.data.objects[name];center=sum((v.co for v in o.data.vertices),Vector())/len(o.data.vertices);delta=Vector((.245,y,.98))-center
    for v in o.data.vertices:v.co+=delta
for name in ['pochwa','rekojesc','jelec','glowica']:
    for v in bpy.data.objects[name].data.vertices:v.co+=Vector((-.015,.016,0))
for name in ['but_lewy','but_prawy']:
    o=bpy.data.objects[name]
    for v in o.data.vertices:
        p=v.co
        if p.z<.10:
            w=max(0,1-p.z/.10);p.x=.07+(p.x-.07)*(1+.09*w)+.004*w;cy=.187 if p.y>0 else -.187;p.y=cy+(p.y-cy)*(1+.10*w)
# Artystyczne ułożenie peleryny po symulacji: szybciej rozszerzające się barki.
mantle=bpy.data.objects['peleryna'];nu=57;nv=19
for v in mantle.data.vertices:
    j,i=divmod(v.index,nu);t=j/(nv-1);a=.85+.35*t+i/(nu-1)*(math.tau-2*(.85+.35*t));old=Vector(((.10+.16*math.sin(t*math.pi/2)+.004*t*math.sin(a*10))*math.cos(a),(.12+.235*math.sin(t*math.pi/2))*math.sin(a),1.565-.225*t));residual=v.co-old
    if residual.length>.02:residual*=.02/residual.length
    ease=1-(1-t)**3;v.co=Vector(((.10+.17*ease+.004*t*math.sin(a*10))*math.cos(a),(.12+.28*ease)*math.sin(a),1.565-.225*t))+residual*.15
sc['art_directed_mantle']='Cloth 16 klatek zachowany jako punkt wyjścia; barki i fałdy następnie poprawione w geometrii. Nie jest to niezmieniony wynik solvera.'
save('v2-F3-clearance-05')
