"""Diagnostyczne współrzędne przenikań; nie zastępuje narzędzia PM."""
import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v2_common import *
from mathutils.bvhtree import BVHTree
import numpy as np
cache={}
def data(name):
    if name in cache:return cache[name]
    o=bpy.data.objects[name];ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();v=[ev.matrix_world@p.co for p in me.vertices];f=[tuple(t.vertices) for t in me.loop_triangles];centers=np.array([tuple(sum((v[i] for i in t),Vector())/3) for t in f]);tree=BVHTree.FromPolygons(v,f,all_triangles=True);ev.to_mesh_clear();cache[name]=(tree,centers);return tree,centers
body='Ciało / MakeHuman / UV natywne';pairs=[(body,x) for x in ['kaftan','koszula','but_lewy','pas_gorny','sakwa_lewa','jelec']]+[('kaftan','koszula'),('peleryna','plaszcz'),('kaftan','rzemien_2'),('koszula','peleryna'),('kaftan','pas_dolny'),('pas_gorny','rzemien_1')]
out=[]
for a,b in pairs:
    ta,ca=data(a);tb,cb=data(b);over=ta.overlap(tb)
    if over:
        p=np.array([ca[i] for i,j in over]);q=np.array([cb[j] for i,j in over]);out.append({'a':a,'b':b,'triangle_pairs':len(over),'first_object_xyz_quantiles':np.quantile(p,[0,.1,.5,.9,1],axis=0).tolist(),'second_object_xyz_quantiles':np.quantile(q,[0,.1,.5,.9,1],axis=0).tolist()})
print('INTERSECTION_LOCATIONS',json.dumps(out,indent=2))
