"""Korekta luzów w statyce; kompletna geometria pozostaje widoczna w audycie PM."""
import sys,math,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v2_common import *
from mathutils.bvhtree import BVHTree
assert bpy.context.scene.get('art_revision')=='v2-F3-fit-layers-03'
sc=bpy.context.scene;rig=bpy.data.objects['Bohater_RIG'];body=bpy.data.objects['Ciało / MakeHuman / UV natywne']
# Luźno zgięte palce, kciuki odwrócone od brzegów kaftana.
for side,angle in [('L',-35),('R',35)]:
    p=rig.pose.bones['wrist.'+side];m=p.matrix.copy();p.matrix=Matrix.Translation(m.translation)@Matrix.Rotation(math.radians(angle),4,'Z')@Matrix.Translation(-m.translation)@m;bpy.context.view_layer.update()
for o in list(sc.objects):
    if o.type!='MESH' or not any(m.type=='ARMATURE' for m in o.modifiers):continue
    temp=o.copy();temp.data=o.data.copy();sc.collection.objects.link(temp)
    for m in list(temp.modifiers):
        if m.type!='ARMATURE':temp.modifiers.remove(m)
    bpy.context.view_layer.update();ev=temp.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();assert len(o.data.vertices)==len(me.vertices)
    for v,p in zip(o.data.vertices,me.vertices):v.co=p.co
    ev.to_mesh_clear();bpy.data.objects.remove(temp,do_unlink=True)
active(rig);bpy.ops.object.mode_set(mode='POSE');bpy.ops.pose.armature_apply(selected=False);bpy.ops.object.mode_set(mode='OBJECT')
for name in ['pochwa','rekojesc','jelec','glowica']:
    for v in bpy.data.objects[name].data.vertices:v.co+=Vector((-.12,.04,0))
for name in ['sakwa_lewa','sakwa_prawa']:
    for v in bpy.data.objects[name].data.vertices:v.co+=Vector((.11,0,-.045))
for name in ['kaftan','rzemien_1','rzemien_2']:bpy.data.objects[name].data.flip_normals()
def surface(o):
    mods=[m for m in o.modifiers if m.type=='SOLIDIFY'];old=[m.show_viewport for m in mods]
    for m in mods:m.show_viewport=False
    bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();vv=[ev.matrix_world@v.co for v in me.vertices];ff=[tuple(p.vertices) for p in me.polygons];tree=BVHTree.FromPolygons(vv,ff);ev.to_mesh_clear()
    for m,v in zip(mods,old):m.show_viewport=v
    mins=Vector([min(p[i] for p in vv) for i in range(3)]);maxs=Vector([max(p[i] for p in vv) for i in range(3)]);return tree,mins,maxs
cache={};moves=[]
def fit(name,obstacles,gap):
    o=bpy.data.objects[name];initial=[v.co.copy() for v in o.data.vertices];count=0
    for iteration in range(5):
        moved=0
        for other in obstacles:
            if other not in cache:cache[other]=surface(bpy.data.objects[other])
            tree,low,high=cache[other]
            for v in o.data.vertices:
                p,n,_,distance=tree.find_nearest(v.co)
                if p is None:continue
                bounded=all(low[i]-.002<v.co[i]<high[i]+.002 for i in range(3))
                signed=(v.co-p).dot(n)
                if signed<gap and (distance<gap*2 or (bounded and distance<.055)):
                    v.co=p+n*gap;moved+=1
        o.data.update();count+=moved
        if not moved:break
    cache.pop(name,None);moves.append({'part':name,'moved_vertex_steps':count,'max_displacement_m':max((v.co-p).length for v,p in zip(o.data.vertices,initial)),'gap_m':gap});print('FIT',moves[-1],flush=True)
bodyname=body.name
fit('koszula',[bodyname],.012);fit('spodnie',[bodyname],.013)
fit('kaftan',[bodyname,'koszula','spodnie'],.010)
fit('plaszcz',[bodyname,'koszula','kaftan','spodnie'],.014)
fit('peleryna',[bodyname,'koszula','kaftan','plaszcz'],.014)
fit('kaptur',[bodyname,'koszula','peleryna'],.010)
for name in ['but_lewy','but_prawy']:fit(name,[bodyname,'spodnie'],.010)
for name in ['pas_gorny','pas_dolny']:fit(name,[bodyname,'kaftan'],.007)
fit('rzemien_1',[bodyname,'kaftan','koszula'],.007);fit('rzemien_2',[bodyname,'kaftan','koszula','rzemien_1'],.007)
sc['layer_fit_record']=json.dumps(moves);save('v2-F3-clearance-fit-04')
