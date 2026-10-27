"""Test-only: glaz from stones-mistral rendered with the render contract camera/lights."""
import sys,math,bpy
from math import radians as r
blend,obj_name,out=sys.argv[1:4]
bpy.ops.wm.open_mainfile(filepath=blend)
s=bpy.context.scene
for o in list(bpy.data.objects):
    if o.type in('LIGHT','CAMERA'):bpy.data.objects.remove(o)
    elif o.type=='MESH' and o.name not in(obj_name,'ShadowCatcher'):o.hide_render=True
ob=bpy.data.objects[obj_name];ob.hide_render=False
# put ground contact at world origin
from mathutils import Vector
bb=[ob.matrix_world@Vector(c) for c in ob.bound_box]
ob.location-=Vector(((min(v.x for v in bb)+max(v.x for v in bb))/2,(min(v.y for v in bb)+max(v.y for v in bb))/2,min(v.z for v in bb)))
cd=bpy.data.cameras.new('Kamera');cd.type='ORTHO';cd.ortho_scale=3.2
cam=bpy.data.objects.new('Kamera',cd);s.collection.objects.link(cam);cam.location=(6.9282,0,5.2);cam.rotation_euler=(r(60),0,r(90));s.camera=cam
for name,loc,rot,e,size,col in [('klucz',(2.8,-3.5,6),(41.874,0,38.66),520,2.3,(.94,.92,.85)),('tyl',(-3,1,4),(46.508,0,-108.435),140,3.0,(.6,.7,.85)),('ziemia',(3,4,2.5),(73.301,0,143.13),65,4.0,(.64,.68,.74))]:
    ld=bpy.data.lights.new(name,'AREA');ld.energy=e;ld.shape='DISK';ld.size=size;ld.color=col
    lo=bpy.data.objects.new(name,ld);s.collection.objects.link(lo);lo.location=loc;lo.rotation_euler=tuple(r(a) for a in rot)
w=s.world;bg=w.node_tree.nodes['Background'];bg.inputs[0].default_value=(.18,.21,.26,1);bg.inputs[1].default_value=.2
v=s.view_settings;v.view_transform='AgX';v.look='AgX - Medium High Contrast';v.exposure=-.2
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=64;s.cycles.seed=1703;s.cycles.use_denoising=False
s.cycles.filter_width=1.5;s.render.threads_mode='FIXED';s.render.threads=4;s.render.film_transparent=True
s.render.resolution_x=s.render.resolution_y=384;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA'
s.render.filepath=out+'_384.png';bpy.ops.render.render(write_still=True)
# shadow: object invisible to camera, catcher visible
catch=bpy.data.objects['ShadowCatcher'];catch.hide_render=False;catch.is_shadow_catcher=True;catch.location=(0,0,0)
ob.visible_camera=False;s.cycles.samples=16
s.render.filepath=out+'_shadow_384.png';bpy.ops.render.render(write_still=True)
print('GLAZ_DONE',bpy.app.version_string,tuple(round(x,2) for x in ob.dimensions))
