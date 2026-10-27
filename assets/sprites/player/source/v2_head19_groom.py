"""Rozbicie prostej kurtyny na nierówne, falujące pasma i kosmyki czoła."""
import sys,math,random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v2_common import *
from mathutils.bvhtree import BVHTree
import numpy as np
assert bpy.context.scene.get('art_revision')=='v2-F2-concept19-skin-v3'
body=bpy.data.objects['Ciało / MakeHuman / UV natywne'];bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();vv=[v.co.copy() for v in me.vertices];tree=BVHTree.FromPolygons(vv,[tuple(p.vertices) for p in me.polygons]);ev.to_mesh_clear()
rng=random.Random(191028)
for o in bpy.context.scene.objects:
    if o.type!='CURVES' or not o.name.startswith('Włosy19'):continue
    d=o.data;a=np.empty(len(d.points)*3,dtype=np.float32);d.attributes['position'].data.foreach_get('vector',a);a=a.reshape(-1,13,3)
    r=np.empty(len(d.points),dtype=np.float32);d.attributes['radius'].data.foreach_get('value',r);r=r.reshape(-1,13)
    for k,path in enumerate(a):
        root=Vector(path[0]);phase=math.floor(root.y*180)*1.73+math.floor(root.x*160)*.87;long=path[-1,2]<1.635
        crop=rng.uniform(.69,1.0) if long else rng.uniform(.9,1.0);old=path.copy();amp=rng.uniform(.006,.011)
        fringe=root.x>.08 and root.z>1.76 and abs(root.y)<.024 and rng.random()<.25
        for j in range(13):
            t=j/12;idx=t*crop*12;lo=int(idx);hi=min(12,lo+1);q=Vector(old[lo]*(1-idx+lo)+old[hi]*(idx-lo))
            q.x+=amp*.65*math.sin(t*8+phase)*math.sin(math.pi*t);q.y+=amp*math.sin(t*8+phase)*math.sin(math.pi*t)
            if long:q.y+=(1 if q.y>0 else -1)*.008*t**3;q.x-=.008*t**3
            if fringe:
                target=Vector((.163,root.y+.025,1.699+rng.random()*.012));q=root.lerp(target,t*t*(3-2*t))+Vector((.008*math.sin(math.pi*t),.003*math.sin(t*6+phase),.012*math.sin(math.pi*t)))
            near,n,_,_=tree.find_nearest(q)
            if near is not None and (q-near).dot(n)<.0008:q=near+n*.001
            path[j]=q
        r[k]*=rng.uniform(.45,.65)
    d.attributes['position'].data.foreach_set('vector',a.reshape(-1));d.attributes['radius'].data.foreach_set('value',r.reshape(-1))
save('v2-F2-concept19-groom-02')
