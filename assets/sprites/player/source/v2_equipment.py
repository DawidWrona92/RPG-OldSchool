"""Konstrukcja wyposażenia i rozłożenie UV po stabilnym drapowaniu F3."""
import sys,math,json,bmesh
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v2_common import *
assert bpy.context.scene.get('art_revision')=='v2-F3-stable-drape-02'
sc=bpy.context.scene;rig=bpy.data.objects['Bohater_RIG'];parts=[o for o in sc.objects if o.get('p2_part')]
keys={'linen':'len','leather':'kaftan','wool':'wełna','pants':'spodnie','strap':'skóra pasów','boot':'buty','pack':'plecak','metal':'żelazo'}
def mat(key):return next(m for m in bpy.data.materials if m.name.startswith('TEMP / '+keys[key]+' do'))
def finish(o,key,sub=1,solid=.002,bone='spine05'):
    if not o.data.materials:o.data.materials.append(mat(key))
    for p in o.data.polygons:p.use_smooth=True
    if sub:m=o.modifiers.new('Powierzchnia wyposażenia','SUBSURF');m.levels=sub;m.render_levels=sub
    if solid:m=o.modifiers.new('Grubość części','SOLIDIFY');m.thickness=solid;m.offset=0
    g=o.vertex_groups.new(name=bone);g.add(list(range(len(o.data.vertices))),1,'REPLACE');m=o.modifiers.new('MakeHuman / wyposażenie','ARMATURE');m.object=rig;m.use_deform_preserve_volume=True;o.parent=rig;o['p2_part']=True;o['temporary_materials']=True;parts.append(o);return o
def grid(name,rows,key,closed=False,cap=False):
    vv=[tuple(p) for row in rows for p in row];n=len(rows[0]);ff=[]
    for j in range(len(rows)-1):
        for i in range(n if closed else n-1):a=j*n+i;b=j*n+(i+1)%n;ff.append((a,b,b+n,a+n))
    if cap:
        for start in [0,len(vv)-n]:
            center=sum((Vector(vv[i]) for i in range(start,start+n)),Vector())/n;idx=len(vv);vv.append(tuple(center))
            for i in range(n):ff.append((start+i,start+(i+1)%n,idx))
    o=mesh(name,vv,ff,mat(key));bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();return o
# Szyte fronty kaftana są bardziej płaskie niż przekrój mięśni.
vest=bpy.data.objects['kaftan']
for v in vest.data.vertices:
    p=v.co
    if p.x>0:
        rx=.205-.04*max(0,(p.z-1.38)/.11);p.x=rx*min(1,abs(p.x/rx))**.4
vest.data.update()
# Cholewy obejmują spodnie; grubość i rzeczywista podeszwa.
for side,sign in [('lewy',1),('prawy',-1)]:
    rings=[(.002,.07,.16,.069,.187),(.024,.07,.16,.071,.187),(.05,.065,.157,.071,.187),(.09,.015,.105,.065,.187),(.14,.008,.067,.063,.18),(.20,.012,.059,.064,.17),(.30,0,.082,.087,.177),(.40,.001,.094,.094,.174),(.50,.018,.101,.103,.16),(.526,.018,.108,.111,.16),(.540,.018,.116,.118,.16),(.517,.018,.120,.121,.16)]
    rows=[]
    for z,cx,rx,ry,cy in rings:
        row=[]
        for i in range(64):a=math.tau*i/64;wr=.002*math.cos(z*92+a*3) if .12<z<.49 else 0;row.append((cx+(rx+wr)*math.cos(a),sign*cy+(ry+wr)*math.sin(a),z))
        rows.append(row)
    o=grid('but_'+side,rows,'boot',True,True);finish(o,'boot',solid=.003,bone='lowerleg02.'+('L' if sign>0 else 'R'));o['construction']='Wysoka cholewa do kolana, wywinięty mankiet, zamknięta podeszwa i szeroki nosek.'
def belt(name,z,width):
    rows=[]
    for j in range(3):
        zz=z+(j/2-.5)*width;row=[]
        for i in range(96):
            a=math.tau*i/96;c=math.cos(a);rx=.224 if c>=0 else .176;row.append((rx*math.copysign(abs(c)**(.4 if c>=0 else 1),c),.246*math.sin(a),zz))
        rows.append(row)
    return finish(grid(name,rows,'strap',True),'strap',solid=.004)
belt('pas_gorny',1.12,.038);belt('pas_dolny',1.058,.029)
for k,sgn in enumerate([1,-1]):
    rows=[]
    for j in range(41):
        t=j/40;y=sgn*(.175-.33*t);z=1.425-.285*t;row=[]
        for f in [-.5,0,.5]:
            yy=y+f*.023;zz=z+f*.021;ry=.222+.012*math.exp(-((zz-1.30)/.13)**2)-.035*max(0,(zz-1.40)/.09);rx=.205-.04*max(0,(zz-1.38)/.11);xx=rx*max(.01,1-(yy/ry)**2)**.2+.008+k*.008;row.append((xx,yy,zz))
        rows.append(row)
    finish(grid('rzemien_'+str(k+1),rows,'strap'),'strap',solid=.003,bone='spine03')
def box(name,loc,dims,key,bevel=.018,subdivide=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=dims;active(o);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);m=o.modifiers.new('Szyte zaokrąglenie','BEVEL');m.width=bevel;m.segments=3;bpy.ops.object.modifier_apply(modifier=m.name)
    if subdivide:m=o.modifiers.new('Konstrukcja powierzchni','SUBSURF');m.levels=subdivide;bpy.ops.object.modifier_apply(modifier=m.name)
    return o
pack=box('plecak',(-.37,0,1.225),(.22,.33,.39),'pack',.035,2)
for v in pack.data.vertices:
    p=v.co
    if p.x>-.32:p.x-=.04*min(1,max(0,(p.z-1.30)/.06))
    if p.x<-.43:
        weight=min(1,(-p.x-.43)/.03);p.x-=weight*(.016*math.exp(-((p.z-1.13)/.05)**4)*math.exp(-((abs(p.y)-.08)/.05)**4)+.009*math.exp(-((p.z-1.33)/.055)**4)*math.exp(-(p.y/.13)**6))
finish(pack,'pack',solid=.003,bone='spine02');pack['construction']='Duży skórzany plecak: wypukłe kieszenie dolne i klapa są częścią jednej ciągłej siatki.'
rows=[]
for j in range(21):
    y=-.225+j/20*.45;row=[]
    for i in range(64):a=math.tau*i/64;r=.067+.002*math.sin(a*9+y*20)+.001*math.sin(y*55);row.append((-.385+r*math.cos(a),y,1.525+r*math.sin(a)))
    rows.append(row)
o=grid('poslanie',rows,'wool',True,True);finish(o,'wool',solid=.003,bone='spine02');o['construction']='Miękki zwój z zamkniętymi denkami; docelowy splot, paski i brud przez P2.'
o=box('manierka',(-.38,-.252,1.18),(.09,.10,.15),'metal',.035);finish(o,'metal',solid=.002,bone='spine02')
for s in [1,-1]:
    o=box('sakwa_'+('lewa' if s>0 else 'prawa'),(-.065,s*.275,1.025),(.09,.075,.11),'pack',.02);finish(o,'pack',solid=.002)
mouth=Vector((.14,.294,1.10));axis=Vector((-.22,.05,-.67)).normalized();across=Vector((0,1,0));across=(across-axis*across.dot(axis)).normalized();other=axis.cross(across).normalized();rows=[]
for j in range(25):
    t=j/24;c=mouth+axis*.70*t;w=.020*(1-.50*t**8);row=[]
    for i in range(32):a=math.tau*i/32;row.append(tuple(c+across*w*math.cos(a)+other*.010*math.sin(a)))
    rows.append(row)
o=grid('pochwa',rows,'strap',True,True);finish(o,'strap',solid=.002);o['construction']='Pochwa przy lewym biodrze, zamknięta końcówka. D1: brak dobytego ostrza.'
def cylinder(name,a,b,r,key):
    d=b-a;bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=r,depth=d.length,location=(a+b)*.5);o=bpy.context.object;o.name=name;o.rotation_euler=d.to_track_quat('Z','Y').to_euler();active(o);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);m=o.modifiers.new('Zaokrąglenie krawędzi','BEVEL');m.width=.002;m.segments=2;bpy.ops.object.modifier_apply(modifier=m.name);return finish(o,key,sub=0,solid=0)
cylinder('rekojesc',mouth-axis*.015,mouth-axis*.13,.012,'strap');cylinder('jelec',mouth-across*.07-axis*.004,mouth+across*.07-axis*.004,.006,'metal')
bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=.018,location=mouth-axis*.145);o=bpy.context.object;o.name='glowica';active(o);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);finish(o,'metal',sub=0,solid=0)
# Widoczne sprzączki na pasach i klapie: ramki ponad skórą, bez przecinania tkanin.
frames=[]
for z,y,x in [(1.12,0,.232),(1.058,.052,.232),(1.30,-.08,-.493),(1.30,.08,-.493)]:
    for yy,zz,dy,dz in [(y-.020,z,.006,.037),(y+.020,z,.006,.037),(y,z-.0185,.045,.006),(y,z+.0185,.045,.006)]:
        o=box('TEMP_sprzaczka',(x,yy,zz),(.007,dy,dz),'metal',.0015);frames.append(o)
active(frames[0])
for o in frames:o.select_set(True)
bpy.ops.object.join();o=bpy.context.object;o.name='sprzaczki';finish(o,'metal',sub=0,solid=0)
for v in o.data.vertices:
    if v.co.x<0:
        for g in list(v.groups):o.vertex_groups[g.group].remove([v.index])
        group=o.vertex_groups.get('spine02') or o.vertex_groups.new(name='spine02');group.add([v.index],1,'REPLACE')
# Unikatowe UV wszystkich części. Duże tkaniny zachowują ciągły rozkrój siatki.
uvs=[]
for o in parts:
    active(o)
    if o.get('grid_nu'):
        n=o['grid_nu'];nv=o['grid_nv'];layer=o.data.uv_layers.new(name='UVMap')
        for p in o.data.polygons:
            for li in p.loop_indices:
                i=o.data.loops[li].vertex_index;layer.data[li].uv=(i%n/(n-1),i//n/(nv-1))
    else:
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(70),island_margin=.004,area_weight=1);bpy.ops.object.mode_set(mode='OBJECT')
    uv=o.data.uv_layers.active;area3=sum(p.area for p in o.data.polygons);area2=0
    for p in o.data.polygons:
        pp=[uv.data[i].uv for i in p.loop_indices];area2+=abs(sum(pp[i].x*pp[(i+1)%len(pp)].y-pp[(i+1)%len(pp)].x*pp[i].y for i in range(len(pp))))/2
    factor=min(.98,math.sqrt(area3*.25/max(area2,1e-12)))
    for u in uv.data:u.uv=(u.uv-Vector((.5,.5)))*factor+Vector((.5,.5))
    density=2048*math.sqrt(area2*factor**2/max(area3,1e-12));o['texture_resolution']=2048;o['texel_density_px_m']=density;uvs.append({'part':o.name,'area_m2':area3,'density_px_m':density})
sc['p2_uv_report']=json.dumps(uvs);save('v2-F3-equipment-02');print('V2_EQUIPMENT',json.dumps(uvs),flush=True)
