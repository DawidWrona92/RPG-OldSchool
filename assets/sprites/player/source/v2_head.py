"""F2: edycja pełnej siatki bez zmian UV; krzywe włosów, zarostu i brwi."""
import sys,random,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v2_common import *
from mathutils.bvhtree import BVHTree
assert bpy.context.scene.get('art_revision')=='v2-F1-body-rig'
body=bpy.data.objects['Ciało / MakeHuman / UV natywne'];rig=bpy.data.objects['Bohater_RIG'];rng=random.Random(172017)
def gauss(p,x,y,z,sx,sy,sz):return math.exp(-((p.x-x)/sx)**2-((p.y-y)/sy)**2-((p.z-z)/sz)**2)
# Makrokształt starej twarzy: policzki, bruzdy, brwi, żuchwa i podoczodołowa tkanka.
# Blizny i pieprzyki pozostają wyłącznie w dostarczonej teksturze.
used=set(i for f in body.data.polygons for i in f.vertices)
for v in body.data.vertices:
    if v.index not in used:continue
    p=v.co
    if p.z<1.53 or p.x<.065:continue
    front=max(0,min(1,(p.x-.09)/.04))
    p.x+=front*(.0045*math.exp(-((p.z-1.701)/.012)**2)*math.exp(-((abs(p.y)-.034)/.027)**2))
    p.x-=front*.004*math.exp(-((p.z-1.628)/.021)**2)*math.exp(-((abs(p.y)-.048)/.022)**2)
    p.y*=1+.035*math.exp(-((p.z-1.58)/.025)**2)
    p.x-=front*.0013*math.exp(-((abs(p.y)-(.016+.5*(1.65-p.z)))/.0035)**2)*math.exp(-((p.z-1.632)/.026)**2)
    for z in [1.724,1.736,1.748]:p.x-=front*.0007*math.exp(-((p.z-z-.6*p.y*p.y)/.0018)**2)*math.exp(-(p.y/.055)**4)
body.data.update()
white=plain('Oko / sclera GPT6',(.55,.49,.42),.3);t=image_node(white,TEX/'hero_eye_sclera_basecolor.png');white.node_tree.links.new(t.outputs['Color'],white.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
iris=plain('Oko / tęczówka GPT6',(.09,.06,.03),.36);t=image_node(iris,TEX/'hero_eye_iris_basecolor.png');iris.node_tree.links.new(t.outputs['Color'],iris.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
cornea=plain('Oko / rogówka IOR 1.376',(1,1,1),.025);bs=cornea.node_tree.nodes.get('Principled BSDF');bs.inputs['Transmission Weight'].default_value=1;bs.inputs['IOR'].default_value=1.376
for side in ['L','R']:
    center=rig.data.bones['eye.'+side].head_local.copy();radius=.0192
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=32,radius=radius,location=center);o=bpy.context.object;o.name='Oko / kula.'+side;active(o);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);o.data.materials.append(white);rigid(o,'eye.'+side)
    for p in o.data.polygons:p.use_smooth=True
    for name,r,opening,mat in [('tęczówka',radius+.0001,.0067,iris),('rogówka',radius+.00055,.010,cornea)]:
        vv=[];ff=[];uvs=[];n=64;nr=12
        for j in range(nr+1):
            rr=opening*j/nr
            for i in range(n):
                a=math.tau*i/n;yy=rr*math.cos(a);zz=rr*math.sin(a);vv.append(tuple(center+Vector((math.sqrt(r*r-rr*rr),yy,zz))));uvs.append((.5+yy/(2*opening),.5+zz/(2*opening)))
        for j in range(nr):
            for i in range(n):a=j*n+i;b=j*n+(i+1)%n;ff.append((a,b,b+n,a+n))
        o=mesh('Oko / '+name+'.'+side,vv,ff,mat);uv=o.data.uv_layers.new(name='UVMap')
        for p in o.data.polygons:
            for li in p.loop_indices:uv.data[li].uv=uvs[o.data.loops[li].vertex_index]
        rigid(o,'eye.'+side)
bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();vs=[v.co.copy() for v in me.vertices];polys=[(tuple(p.vertices),p.center.copy(),p.normal.copy(),p.area) for p in me.polygons];tree=BVHTree.FromPolygons(vs,[p[0] for p in polys]);ev.to_mesh_clear()
def hairmat(name,gray=False):
    m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial');b=n.new('ShaderNodeBsdfHairPrincipled');b.parametrization='COLOR';b.inputs['Color'].default_value=(.26,.27,.25,1) if gray else (.012,.009,.007,1);b.inputs['Roughness'].default_value=.48;b.inputs['Radial Roughness'].default_value=.6;l.new(b.outputs[0],out.inputs[0]);return m
dark=hairmat('Włókna / ciemny brąz');gray=hairmat('Włókna / siwizna',True)
def curves(name,paths,radii,mat):
    if not paths:return
    d=bpy.data.hair_curves.new(name);d.add_curves([len(p) for p in paths]);o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);d.materials.append(mat);d.attributes['position'].data.foreach_set('vector',[c for p in paths for v in p for c in v]);r=d.attributes.new('radius','FLOAT','POINT');r.data.foreach_set('value',[rr*(1-.96*i/(len(p)-1)) for rr,p in zip(radii,paths) for i in range(len(p))]);o.parent=rig;o.parent_type='BONE';o.parent_bone='head';o.matrix_parent_inverse=Matrix.Identity(4);o.matrix_basis=Matrix.Identity(4);bpy.context.view_layer.update();o.matrix_basis=o.matrix_world.inverted();o['strand_count']=len(paths)
def sample(p):
    ids=p[0];a,b,c=[vs[k] for k in ids[:3]];u=math.sqrt(rng.random());v=rng.random();return a*(1-u)+b*u*(1-v)+c*u*v
def scalp(p):
    _,c,n,_=p
    if c.z<1.645:return False
    if c.x<.025:return c.z>1.65
    return c.z>1.750+.007*math.cos(c.y*35) if abs(c.y)<.06 else c.z>1.713
def beard(p):
    _,c,n,_=p
    return c.x>.115 and ((1.565<c.z<1.625 and abs(c.y)<.076) or (1.623<c.z<1.646 and .012<abs(c.y)<.026))
def brows(p):
    _,c,n,_=p
    return c.x>.128 and .012<abs(c.y)<.057 and abs(c.z-(1.702-.15*abs(c.y)))<.0035
for label,test,count in [('Włosy',scalp,26000),('Zarost',beard,12000),('Brwi',brows,2200)]:
    candidates=[p for p in polys if test(p)];paths=[[],[]];radii=[[],[]]
    for poly in rng.choices(candidates,weights=[max(p[3],1e-10) for p in candidates],k=count):
        p=sample(poly);normal=poly[2].normalized();grayprob=(.5 if abs(p.y)>.064 else .25) if label=='Włosy' else .38
        k=int(rng.random()<grayprob)
        if label=='Włosy':
            direction=Vector((-.85,.28,-.16 if p.z>1.76 else -.65));length=rng.uniform(.022,.046);lift=rng.uniform(.0015,.005);rad=rng.uniform(.000045,.00008)
        elif label=='Zarost':direction=Vector((0,.08,-1));length=rng.uniform(.0018,.006);lift=.0006;rad=rng.uniform(.000045,.00007)
        else:direction=Vector((0,1 if p.y>0 else -1,.2));length=rng.uniform(.004,.008);lift=.0008;rad=.000055
        tangent=direction-normal*normal.dot(direction)
        if tangent.length<.01:tangent=normal.cross(Vector((0,1,0)))
        tangent.normalize();across=normal.cross(tangent);path=[];phase=rng.random()*6.28
        for i in range(7):
            t=i/6;q=p+tangent*length*t+normal*(.0003+lift*math.sin(math.pi*t));q+=across*.0007*t*(math.sin(t*4+phase)-math.sin(phase))
            nearest=tree.find_nearest(q)
            if nearest[0] is not None and (q-nearest[0]).dot(nearest[1])<.0002:q=nearest[0]+nearest[1]*(.0003+lift*math.sin(math.pi*t))
            path.append(tuple(q))
        paths[k].append(path);radii[k].append(rad)
    for k,mat in enumerate([dark,gray]):curves(label+(' / siwe' if k else ' / ciemne'),paths[k],radii[k],mat)
bpy.context.scene.cycles.curve_shape='THICK';save('v2-F2-aged-head')
