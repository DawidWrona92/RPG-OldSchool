"""Optional Blender 4.x/5.x scene prototype for Welesza ENV-01.

Launch from Blender, not plain Python:
    blender -b -t 8 --python assets/environment/forest_edge/blender_scene.py

This file is a *proposed render path*. It has been syntax checked but not run in
an environment containing bpy. Validate renders before claiming style acceptance.
No external downloaded assets; replace basic procedurals with authored scans/assets
of known licensing once look development is approved.
"""
from __future__ import annotations
import bpy
import math
import json
import random
from mathutils import Vector
from pathlib import Path

RNG = random.Random(424107)
DEST = Path(__file__).resolve().parent / 'output' / 'blender'
DEST.mkdir(parents=True, exist_ok=True)

# Separate Blender runtime namespace so unrelated project objects aren't modified.
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.samples=36
scene.cycles.use_denoising=True
scene.render.resolution_x=1536
scene.render.resolution_y=900
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=False
scene.view_settings.view_transform='AgX'

world=bpy.data.worlds.new('Welesza overcast sky')
scene.world=world
world.use_nodes=True
bg=world.node_tree.nodes.get('Background')
bg.inputs['Color'].default_value=(.19,.225,.24,1)
bg.inputs['Strength'].default_value=.32

def material(name,colors,scale=4,rough=.83,bump=.22):
    mat=bpy.data.materials.new(name)
    mat.use_nodes=True
    n=mat.node_tree.nodes; L=mat.node_tree.links
    bsdf=n.get('Principled BSDF')
    bsdf.inputs['Roughness'].default_value=rough
    tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=scale
    tex.inputs['Detail'].default_value=5.0
    tex.inputs['Roughness'].default_value=.69
    ramp=n.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position=.24
    ramp.color_ramp.elements[0].color=colors[0]
    ramp.color_ramp.elements[1].position=.76
    ramp.color_ramp.elements[1].color=colors[1]
    L.new(tex.outputs['Fac'],ramp.inputs['Fac']);L.new(ramp.outputs['Color'],bsdf.inputs['Base Color'])
    bumpN=n.new('ShaderNodeBump');bumpN.inputs['Strength'].default_value=bump
    bumpN.inputs['Distance'].default_value=.07
    L.new(tex.outputs['Fac'],bumpN.inputs['Height'])
    L.new(bumpN.outputs['Normal'],bsdf.inputs['Normal'])
    return mat

def c(r,g,b):return(r/255.,g/255.,b/255.,1.)

forest=material('Forest soil: needles moss and wet decay',(c(25,29,22),c(82,83,58)),3.0,.92,.26)
mud=material('Mud: trampled route',(c(28,26,23),c(84,72,57)),5.6,.70,.34)
bark=material('Bark: split moisture dark',(c(29,26,22),c(87,64,43)),9.1,.88,.28)
stone=material('Stone: cold weathered',(c(54,59,54),c(118,122,107)),4.9,.76,.29)
moss=material('Moss: subdued olive',(c(23,37,18),c(72,83,38)),7.0,.95,.22)
needles=[material('Fir needle shade '+str(i),(c(21+i*3,35+i*4,25+i*2),c(43+i*3,62+i*3,39+i*2)),3+i,.95,.12) for i in range(3)]
water=bpy.data.materials.new('Puddles: dark reflective water');water.use_nodes=True
wbsdf=water.node_tree.nodes.get('Principled BSDF')
wbsdf.inputs['Base Color'].default_value=(.13,.16,.14,1)
wbsdf.inputs['Metallic'].default_value=.07
wbsdf.inputs['Roughness'].default_value=.14

# Continuous low relief. A deterministic procedural scene, not final geology.
def height(x,y):
    return .04*math.sin(x*1.33+y*.84)+.03*math.sin(x*2.23-y*1.75)+.055*math.sin(x*.43+y*.63)

def road_y(x):return .37*math.sin(x*.21)+.20*math.sin(x*.51+.5)

def mesh_surface():
    nx,ny=124,86
    xs=[-25+i*50/(nx-1) for i in range(nx)]
    ys=[-18+i*36/(ny-1) for i in range(ny)]
    verts=[(x,y,height(x,y)) for y in ys for x in xs]
    faces=[(j*nx+i,j*nx+i+1,(j+1)*nx+i+1,(j+1)*nx+i) for j in range(ny-1) for i in range(nx-1)]
    m=bpy.data.meshes.new('Terrain mesh')
    m.from_pydata(verts,[],faces);m.update()
    ob=bpy.data.objects.new('Ground - full topography',m);bpy.context.collection.objects.link(ob)
    ob.data.materials.append(forest)
    for p in m.polygons:p.use_smooth=True
    return ob

def route_mesh():
    verts=[];faces=[]
    for i in range(231):
        x=-25+i*(50/230)
        ym=road_y(x)
        width=1.9+.20*math.sin(x*.33)+.12*math.sin(x*2.27)
        for yy in (ym-width,ym+width):verts.append((x,yy,height(x,yy)+.016))
        if i:faces.append((2*i-2,2*i-1,2*i+1,2*i))
    me=bpy.data.meshes.new('Muddy route');me.from_pydata(verts,[],faces);me.update()
    ob=bpy.data.objects.new('Route - wheel worn mud',me);bpy.context.collection.objects.link(ob)
    me.materials.append(mud)
    for poly in me.polygons:poly.use_smooth=True
    return ob

def apply_material(ob,mat):ob.data.materials.append(mat);return ob

def cylinder(name,p0,p1,r0,r1,mat,vertices=10):
    p0=Vector(p0);p1=Vector(p1)
    direction=p1-p0
    bpy.ops.mesh.primitive_cone_add(vertices=vertices,radius1=r0,radius2=r1,depth=direction.length,location=(p0+p1)*.5)
    ob=bpy.context.object;ob.name=name;ob.rotation_euler=direction.to_track_quat('Z','Y').to_euler()
    return apply_material(ob,mat)

def sphere(name,location,scale,mat,subdiv=1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdiv,radius=1,location=location)
    ob=bpy.context.object;ob.name=name;ob.scale=scale;return apply_material(ob,mat)

def add_tree(i,x,y,r=.96):
    z=height(x,y);h=RNG.uniform(7.2,10.0)*r
    trunk=cylinder(f'Fir {i} | bark',(x,y,z),(x+.10,y,h+z),.24*r,.065*r,bark,12)
    trunk['collision_radius_m']=.50*r
    for layer in range(9):
        t=(layer+.3)/9
        zz=z+1.3+t*(h-1.7)
        width=(1.9*(1-t)**1.05+.13)*r
        for branch in range(7):
            a=branch*2*math.pi/7+RNG.uniform(-.21,.21)
            bx=x+math.cos(a)*width;by=y+math.sin(a)*width
            ztip=zz-(.4+.25*t)*r
            cylinder(f'Fir {i} bough {layer}-{branch}',(x,y,zz+.30*r),(bx,by,ztip),(.29*(1-t)+.08)*r,.015,needles[(i+branch+layer)%3],7)
    return trunk

def add_rock(i,x,y,scale):
    z=height(x,y)
    ob=sphere(f'Rock {i}',(x,y,z+.38*scale),(.92*scale,.61*scale,.51*scale),stone,2)
    ob.rotation_euler=(RNG.uniform(-.2,.2),RNG.uniform(-.12,.12),RNG.uniform(0,math.pi))
    ob['collision_radius_m']=.7*scale
    if RNG.random()<.75:
        mossball=sphere(f'Rock {i} moss',(x+.13*scale,y+.05*scale,z+.75*scale),(.61*scale,.43*scale,.11*scale),moss,2)
        mossball.rotation_euler=(0,0,RNG.random()*math.pi)
    return ob

def add_log(i,x,y,length=2.6):
    z=height(x,y);dx=math.cos(i*.6)*length/2;dy=math.sin(i*.6)*length/2
    ob=cylinder(f'Fallen log {i}',(x-dx,y-dy,z+.18),(x+dx,y+dy,z+.22),.24,.19,bark,14)
    ob['collision_radius_m']=max(.65,length/2)
    return ob

def add_puddle(i,x,y):
    z=height(x,y)+.025
    bpy.ops.mesh.primitive_circle_add(vertices=34,radius=1.0,fill_type='NGON',location=(x,y,z))
    ob=bpy.context.object;ob.name=f'Wet depression {i}'
    ob.scale=(RNG.uniform(.25,.88),RNG.uniform(.12,.45),1)
    ob.rotation_euler[2]=RNG.uniform(0,math.pi)
    apply_material(ob,water)
    return ob

mesh_surface();route_mesh()
layout=[]
for idx,(x,y) in enumerate([(-19,-12),(-12,-13),(-4,-12),(8,-12),(18,-10),(-20,8),(-13,12),(-6,13),(7,13),(16,12),(20,3)]):
    dx=RNG.uniform(-1.3,1.3);dy=RNG.uniform(-1.2,1.2)
    obj=add_tree(idx,x+dx,y+dy,RNG.uniform(.86,1.2));layout.append(obj)
for i in range(35):
    x=RNG.uniform(-22,22);y=RNG.uniform(-14,14)
    if abs(y-road_y(x))<3.0:continue
    ob=add_rock(i,x,y,RNG.uniform(.25,.85));layout.append(ob)
for i,(x,y) in enumerate([(-10,4),(13,-4),(16,9)]):layout.append(add_log(i,x,y))
for i in range(18):
    x=RNG.uniform(-20,20);y=road_y(x)+RNG.choice((-1.2,1.1))*RNG.uniform(.35,1.3)
    add_puddle(i,x,y)

# Overcast sky and one restrained key light: NO baked torches across whole environment.
sun_data=bpy.data.lights.new(name='Cold overcast directional key',type='AREA')
sun=bpy.data.objects.new('Cold overcast directional key',sun_data);bpy.context.collection.objects.link(sun)
sun.location=(-9,-6,17);sun_data.energy=1750;sun_data.shape='DISK';sun_data.size=16

def point_camera(cam,target):
    direction=Vector(target)-cam.location
    cam.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()

camdata=bpy.data.cameras.new('Orthographic 30 deg')
cam=bpy.data.objects.new('Environment projection camera',camdata)
bpy.context.collection.objects.link(cam)
cam.location=(-20,-20,16.3)
point_camera(cam,(0,0,.5));camdata.type='ORTHO';camdata.ortho_scale=26
scene.camera=cam
# Note: camera framing and screen scale are to be validated after first actual Blender render.
# In a 2D game use pixel-per-metre contract, not Blender's preview pixel bounds directly.
scene.render.filepath=str(DEST/'forest_blender_preview.png')
bpy.ops.wm.save_as_mainfile(filepath=str(DEST/'forest_edge.blend'))
sceneMeta={
 'status':'prototype; camera/scale not validated in-game',
 'camera_elevation_nominal_degrees':30,
 'orthographic':True,
 'objects':[{'name':ob.name,'location_m':list(ob.location),'collision_radius_m':ob.get('collision_radius_m',0)} for ob in layout],
 'seed':424107,'render_engine':'CYCLES','samples':36,
}
(DEST/'scene_blender.json').write_text(json.dumps(sceneMeta,indent=2),encoding='utf8')
bpy.ops.render.render(write_still=True)
