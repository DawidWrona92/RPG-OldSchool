"""Dopasowanie warstw po pełnym audycie, bez list wyjątków dla ubrań."""
import sys,json,math,bmesh
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v2_common import *
assert bpy.context.scene.get('art_revision')=='v2-F3-equipment-02'
for name in ['but_lewy','but_prawy']:
    o=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();v=bm.verts[-1];bmesh.ops.delete(bm,geom=list(v.link_faces),context='FACES');bm.to_mesh(o.data);bm.free()
for k,sgn in enumerate([1,-1]):
    o=bpy.data.objects['rzemien_'+str(k+1)]
    for j in range(41):
        t=j/40;y=sgn*(.175-.33*t);z=1.425-.285*t
        for i,f in enumerate([-.5,0,.5]):
            yy=y+f*.022;zz=z-f*sgn*.026;ry=.222+.012*math.exp(-((zz-1.30)/.13)**2)-.035*max(0,(zz-1.40)/.09);rx=.205-.04*max(0,(zz-1.38)/.11);xx=rx*max(.01,1-(yy/ry)**2)**.2+.008+k*.008;o.data.vertices[j*3+i].co=(xx,yy,zz)
    o.data.update()
save('v2-F3-fit-layers-03')
