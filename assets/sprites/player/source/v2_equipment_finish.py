"""Osadzenie miękkiego plecaka, podparcie posłania i rzeczywiste paski/sprzączki butów."""
import sys,math,bmesh
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v2_common import *
from mathutils.bvhtree import BVHTree
assert bpy.context.scene.get('art_revision')=='v2-F3-static-review-15'
def tree(objects):
    vv=[];ff=[]
    for o in objects:
        bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();start=len(vv);vv.extend(ev.matrix_world@v.co for v in me.vertices);ff.extend(tuple(i+start for i in p.vertices) for p in me.polygons);ev.to_mesh_clear()
    return BVHTree.FromPolygons(vv,ff)
pack=bpy.data.objects['plecak'];support=tree([bpy.data.objects[n] for n in ['plaszcz','peleryna']])
for v in pack.data.vertices:
    if v.normal.x>.45:
        hit=support.ray_cast(Vector((-1,v.co.y,v.co.z)),Vector((1,0,0)),2)[0]
        if hit is not None and hit.x<0:
            target=max(-.33,min(-.252,hit.x-.012));v.co.x=v.co.x+(target-v.co.x)*min(1,(v.normal.x-.45)/.30)
pack.data.update();bpy.context.view_layer.update();ev=pack.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();pack_top=max(v.co.z for v in me.vertices);ev.to_mesh_clear()
roll=bpy.data.objects['poslanie'];center=sum((Vector(c) for c in roll.bound_box),Vector())/8;new_z=pack_top+.076;dz=new_z-center.z
for v in roll.data.vertices:v.co.z+=dz
center.z=new_z;strapmat=bpy.data.materials['TEMP / skóra pasów do P2'];metal=bpy.data.materials['TEMP / żelazo do P2']
def start(o,materials,bone):
    for mat in materials:
        if mat not in list(o.data.materials):o.data.materials.append(mat)
    bm=bmesh.new();bm.from_mesh(o.data);deform=bm.verts.layers.deform.verify();group=o.vertex_groups.get(bone) or o.vertex_groups.new(name=bone)
    def vertex(p):
        v=bm.verts.new(p);v[deform][group.index]=1;return v
    def face(vv,index):
        f=bm.faces.new(vv);f.material_index=index;f.smooth=True;return f
    return bm,vertex,face
bm,vertex,face=start(roll,[strapmat],'spine02')
for cy in [-.13,.13]:
    rows=[]
    for j in range(3):
        y=cy+(j/2-.5)*.016;rows.append([vertex((center.x+.072*math.cos(math.tau*i/64),y,center.z+.072*math.sin(math.tau*i/64))) for i in range(64)])
    for j in range(2):
        for i in range(64):k=(i+1)%64;face((rows[j][i],rows[j+1][i],rows[j+1][k],rows[j][k]),1)
bm.to_mesh(roll.data);bm.free();roll.data.update()
for name,sign in [('but_lewy',1),('but_prawy',-1)]:
    o=bpy.data.objects[name];surface=tree([o]);bm,vertex,face=start(o,[strapmat,metal],'lowerleg02.'+('L' if sign>0 else 'R'))
    def box(c,d,index):
        vv=[vertex(Vector(c)+Vector((sx*d[0]/2,sy*d[1]/2,sz*d[2]/2))) for sx,sy,sz in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
        for f in [(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]:face([vv[i] for i in f],index)
    for z,cx,cy in [(.12,.009,sign*.184),(.38,.001,sign*.174)]:
        rows=[];front=None
        for j in range(3):
            zz=z+(j/2-.5)*.022;row=[]
            for i in range(64):
                a=math.tau*i/64;direction=Vector((math.cos(a),math.sin(a),0));origin=Vector((cx,cy,zz));hit=surface.ray_cast(origin,direction,.5)[0];assert hit is not None,(name,z,i)
                p=hit+direction*.006;row.append(vertex(p))
                if j==1 and i==0:front=p.copy()
            rows.append(row)
        for j in range(2):
            for i in range(64):k=(i+1)%64;face((rows[j][i],rows[j][k],rows[j+1][k],rows[j+1][i]),1)
        x=front.x+.005
        for yy,zz,dy,dzz in [(cy-.017,z,.006,.029),(cy+.017,z,.006,.029),(cy,z-.0145,.040,.006),(cy,z+.0145,.040,.006)]:box((x,yy,zz),(.005,dy,dzz),2)
    bm.to_mesh(o.data);bm.free();o.data.update();o['construction']='Wysoka cholewa, wywinięcie, zamknięta podeszwa; dwa rzeczywiste paski i metalowe sprzączki w jednej siatce części. Material IDs rozróżniają skórę/pasy/metal.'
roll['construction']='Miękki zwój z denkami, dwa skórzane pasy, osadzony na szczycie plecaka z luzem dla grubości pasów.'
pack['construction']='Miękki skórzany plecak z kieszeniami/klapą; przednia wyściółka dopasowana do zapisanej peleryny/płaszcza.'
for o in [pack,roll,bpy.data.objects['but_lewy'],bpy.data.objects['but_prawy']]:
    active(o)
    if o!=pack:
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(70),island_margin=.004,area_weight=1);bpy.ops.object.mode_set(mode='OBJECT')
    uv=o.data.uv_layers.active;area3=sum(p.area for p in o.data.polygons);area2=0
    for p in o.data.polygons:
        q=[uv.data[i].uv for i in p.loop_indices];area2+=abs(sum(q[i].x*q[(i+1)%len(q)].y-q[(i+1)%len(q)].x*q[i].y for i in range(len(q))))/2
    factor=min(math.sqrt(area3*.25/max(area2,1e-12)),.495/max(abs(c-.5) for u in uv.data for c in u.uv))
    for u in uv.data:u.uv=(u.uv-Vector((.5,.5)))*factor+Vector((.5,.5))
    o['texel_density_px_m']=2048*math.sqrt(area2*factor*factor/area3)
save('v2-F3-equipment-review-16')
