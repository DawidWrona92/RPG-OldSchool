"""F2 według nadrzędnego planu i referencji 19; skóra v3, bez zmian natywnego UV."""
import sys,math,json,random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v2_common import *
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
assert bpy.context.scene.get('art_revision')=='v2-F3-clearance-fit-04'
sc=bpy.context.scene;body=bpy.data.objects['Ciało / MakeHuman / UV natywne'];rig=bpy.data.objects['Bohater_RIG'];rng=random.Random(191027)
package=json.loads((TEX/'manifest.json').read_text());assert package['material_version']==3
for entry in package['files']:assert sha(TEX/entry['file'])==entry['sha256']
for image in bpy.data.images:
    if image.source=='FILE' and (TEX/Path(image.filepath).name).exists():
        path=TEX/Path(image.filepath).name
        if image.packed_file:image.unpack(method='REMOVE')
        image.filepath=str(path);image.reload();image.pack()
body.data.materials[0]['texture_package']='bc1da51 / v3 / names replaceable, native UV'
scale=body['scale_m_per_mh_unit'];used=set(i for p in body.data.polygons for i in p.vertices)
# Cofnięcie targetów wklęsłych policzków z F1; ta sama topologia i UV.
for side in ['l','r']:
    for line in (THIRD/'targets'/f'{side}-cheek-inner-decr.target').read_text().splitlines():
        s=line.split()
        if not s or s[0].startswith('#'):continue
        i=int(s[0]);x,y,z=map(float,s[1:4]);body.data.vertices[i].co-=Vector((z,x,y))*(scale*.18)
for v in body.data.vertices:
    if v.index not in used:continue
    p=v.co
    if p.z<1.53 or p.x<.06:continue
    front=max(0,min(1,(p.x-.085)/.045))
    p.x+=front*.004*math.exp(-((p.z-1.628)/.021)**2)*math.exp(-((abs(p.y)-.048)/.022)**2)
    p.x+=front*.0032*math.exp(-((p.z-1.643)/.024)**2)*math.exp(-((abs(p.y)-.047)/.027)**2)
    p.y*=1+.06*math.exp(-((p.z-1.58)/.030)**2)
    p.x+=front*.004*math.exp(-((p.z-1.565)/.023)**2)*math.exp(-(p.y/.04)**2)
    p.x+=front*.004*math.exp(-((p.z-1.702)/.010)**2)*math.exp(-((abs(p.y)-.030)/.024)**2)
    p.x-=front*.0015*math.exp(-(p.y/.0025)**2)*math.exp(-((p.z-1.707)/.018)**2)
    p.x+=front*.0024*math.exp(-((abs(p.y)-.007)/.0035)**2)*math.exp(-((p.z-1.708)/.014)**2)
    p.x+=front*.0027*math.exp(-((p.z-1.662)/.006)**2)*math.exp(-((abs(p.y)-.034)/.023)**2)
    # Usunięcie regularnego reliefu F2 i zastąpienie trzema przerwanymi bruzdami.
    for z in [1.724,1.736,1.748]:p.x+=front*.0007*math.exp(-((p.z-z-.6*p.y*p.y)/.0018)**2)*math.exp(-(p.y/.055)**4)
    for j,(z,width,depth) in enumerate([(1.722,.044,.0011),(1.734,.039,.0013),(1.747,.032,.0009)]):
        line=z+.002*math.sin(p.y*52+j)+.001*p.y/.04;fade=math.exp(-((p.y+.003*j)/width)**6);p.x-=front*depth*fade*math.exp(-((p.z-line)/.0022)**2)
    p.x+=front*.0018*math.exp(-(p.y/.008)**2)*math.exp(-((p.z-1.675)/.023)**2)
body.data.update()
for o in list(sc.objects):
    if o.type=='CURVES':bpy.data.objects.remove(o,do_unlink=True)
bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();vs=[v.co.copy() for v in me.vertices];tris=[]
for tri in me.loop_triangles:
    ids=tuple(tri.vertices);a,b,c=[vs[i] for i in ids];center=(a+b+c)/3;cross=(b-a).cross(c-a);area=cross.length/2
    if area>1e-12:tris.append((ids,center,cross.normalized(),area))
tree=BVHTree.FromPolygons(vs,[t[0] for t in tris],all_triangles=True);ev.to_mesh_clear()
def hm(name,gray):
    m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial');b=n.new('ShaderNodeBsdfHairPrincipled')
    if gray:b.parametrization='COLOR';b.inputs['Color'].default_value=(.13,.125,.11,1)
    else:b.parametrization='MELANIN';b.inputs['Melanin'].default_value=.80;b.inputs['Melanin Redness'].default_value=.23
    b.inputs['Roughness'].default_value=.55;b.inputs['Radial Roughness'].default_value=.68;b.inputs['Random Roughness'].default_value=.15;l.new(b.outputs[0],out.inputs[0]);return m
dark=hm('Koncept19 / ciemnobrązowe włókna',False);silver=hm('Koncept19 / przyprószenie siwizną',True)
def sample(t):
    a,b,c=[vs[i] for i in t[0]];u=math.sqrt(rng.random());v=rng.random();return a*(1-u)+b*u*(1-v)+c*u*v
def attach(name,paths,radii,mat):
    d=bpy.data.hair_curves.new(name);d.add_curves([len(p) for p in paths]);o=bpy.data.objects.new(name,d);sc.collection.objects.link(o);d.materials.append(mat);d.attributes['position'].data.foreach_set('vector',[c for p in paths for v in p for c in v]);rad=d.attributes.new('radius','FLOAT','POINT');rad.data.foreach_set('value',[r*(1-.97*i/(len(p)-1)) for r,p in zip(radii,paths) for i in range(len(p))]);o.parent=rig;o.parent_type='BONE';o.parent_bone='head';o.matrix_parent_inverse=Matrix.Identity(4);o.matrix_basis=Matrix.Identity(4);bpy.context.view_layer.update();o.matrix_basis=o.matrix_world.inverted();o['strand_count']=len(paths);o['reference']='Koncept19, plan autora; gęstość i długość robocza do oceny.'
def scalp(t):
    c=t[1]
    if c.x<.025:return c.z>1.655
    if abs(c.y)>.058:return c.z>1.709
    return c.z>1.752+.005*math.sin(c.y*42)
scalp_tri=[t for t in tris if scalp(t)];weights=[t[3] for t in scalp_tri];guides=[]
for t in rng.choices(scalp_tri,weights=weights,k=380):
    p=sample(t);side=1 if p.y>-.008 else -1
    if p.x>.086 and p.z>1.738:
        if rng.random()<.25:end=Vector((.164+rng.uniform(-.009,.008),p.y+side*rng.uniform(.004,.030),rng.uniform(1.701,1.728)))
        else:end=Vector((rng.uniform(.085,.12),side*rng.uniform(.084,.104),rng.uniform(1.588,1.635)))
    elif p.x<.025:end=Vector((rng.uniform(-.079,-.055),p.y+rng.uniform(-.012,.012),rng.uniform(1.565,1.602)))
    else:end=Vector((p.x-rng.uniform(.015,.045),side*rng.uniform(.092,.110),rng.uniform(1.565,1.610)))
    guides.append((p,end))
gk=KDTree(len(guides))
for i,(p,end) in enumerate(guides):gk.insert(p,i)
gk.balance();paths=[[],[]];radii=[[],[]]
for t in rng.choices(scalp_tri,weights=weights,k=34000):
    p=sample(t);normal=t[2];_,idx,_=gk.find(p);root,end=guides[idx];end=end+(p-root)*.30+Vector((rng.uniform(-.003,.003),rng.uniform(-.003,.003),rng.uniform(-.004,.004)));across=Vector((0,1,0)) if abs(normal.y)<.6 else Vector((1,0,0));phase=rng.random()*6.28;lift=rng.uniform(.008,.018);path=[]
    for j in range(13):
        s=j/12;tween=s*s*(3-2*s);q=p.lerp(end,tween);q+=normal*(.0004+lift*math.sin(math.pi*s));q+=across*(.003*math.sin(s*7+phase)*math.sin(math.pi*s))
        near,n,_,dist=tree.find_nearest(q)
        if near is not None and (q-near).dot(n)<.0012:q=near+n*(.0012+.003*math.sin(math.pi*s))
        path.append(tuple(q))
    k=int(rng.random()<(.33 if abs(p.y)>.064 else .18));paths[k].append(path);radii[k].append(rng.uniform(.000055,.000090))
for k,m in enumerate([dark,silver]):attach('Włosy19 / '+('siwe' if k else 'ciemne'),paths[k],radii[k],m)
def beard(t):
    c=t[1];return c.x>.075 and 1.548<c.z<1.631+.26*abs(c.y) and abs(c.y)<.082
def mustache(t):
    c=t[1];return c.x>.135 and .003<abs(c.y)<.029 and 1.621<c.z<1.641-.09*abs(c.y)
def brow(t):
    c=t[1];return c.x>.132 and .010<abs(c.y)<.058 and abs(c.z-(1.702-.15*abs(c.y)))<.004
for label,condition,count in [('Broda19',beard,21000),('Wąs19',mustache,6500),('Brwi19',brow,3500)]:
    candidates=[t for t in tris if condition(t)];paths=[[],[]];radii=[[],[]]
    for poly in rng.choices(candidates,weights=[t[3] for t in candidates],k=count):
        p=sample(poly);n=poly[2];chin=p.z<1.59 and abs(p.y)<.042;k=int(rng.random()<(.64 if chin else .20));length=rng.uniform(.007,.016) if label=='Broda19' else rng.uniform(.004,.008);length*=1.3 if chin else 1
        direction=Vector((.12,.10*(1 if p.y>0 else -1),-1)) if label!='Brwi19' else Vector((0,1 if p.y>0 else -1,.1));tangent=direction-n*direction.dot(n)
        if tangent.length<.001:tangent=n.cross(Vector((0,1,0)))
        tangent.normalize();path=[];phase=rng.random()*6.28
        for j in range(6):
            t=j/5;q=p+tangent*length*t+n*(.0004+.002*math.sin(t*math.pi));q+=n.cross(tangent)*(.00065*math.sin(t*5+phase)*t);near,nn,_,_=tree.find_nearest(q)
            if near is not None and (q-near).dot(nn)<.0003:q=near+nn*.0005
            path.append(tuple(q))
        paths[k].append(path);radii[k].append(rng.uniform(.00005,.00008))
    for k,m in enumerate([dark,silver]):attach(label+' / '+('siwe' if k else 'ciemne'),paths[k],radii[k],m)
sc['head_reference']='19-bohater-twarz.jpg / main eb3a2ec; plan i pisemne decyzje nadrzędne';sc['skin_texture_version']=3;sc['eye_texture_pending']='v4 GPT6: szarozielona tęczówka; obecna robocza brązowa z v3.';save('v2-F2-concept19-skin-v3')
