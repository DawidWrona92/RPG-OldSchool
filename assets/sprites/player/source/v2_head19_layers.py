"""Warstwowe cięcie groomu: krótsza korona, dłuższy kark i pojedyncze pasma żuchwy."""
import sys,math,random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v2_common import *
import numpy as np
assert bpy.context.scene.get('art_revision')=='v2-F3-tailoring-06'
rng=random.Random(191029)
for o in bpy.context.scene.objects:
    if o.type!='CURVES' or not o.name.startswith('Włosy19'):continue
    d=o.data;a=np.empty(len(d.points)*3,dtype=np.float32);d.attributes['position'].data.foreach_get('vector',a);a=a.reshape(-1,13,3)
    for path in a:
        root=Vector(path[0]);old=path.copy();crop=1
        if root.z>1.772:crop=rng.uniform(.55,.72)
        elif root.x>.07 and root.z>1.73 and rng.random()<.7:crop=rng.uniform(.74,.90)
        for j in range(13):
            t=j/12;pos=t*crop*12;lo=int(pos);hi=min(12,lo+1);q=Vector(old[lo]*(1-pos+lo)+old[hi]*(pos-lo))
            if crop<.8:q+=Vector((rng.uniform(-.002,.002),.008*(1 if q.y>0 else -1)*t*t,.007*t*t))
            if root.x>.05 and abs(root.y)>.04:q.x-=.007*t*t
            path[j]=q
    d.attributes['position'].data.foreach_set('vector',a.reshape(-1))
save('v2-F2-layered-groom-03')
