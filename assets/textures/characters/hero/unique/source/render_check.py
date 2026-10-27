"""Blender 4.3, read-only diagnostic renderer. blender -b -t 4 -P source/render_check.py -- /tmp/base.obj
Does not save or modify a blend file. Body group only, unchanged native UV.
"""
import bpy,sys,math
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
meshpath=sys.argv[sys.argv.index('--')+1]
verts=[];uvs=[];faces=[];group=''
for l in open(meshpath):
 s=l.split()
 if not s:continue
 if s[0]=='v':verts.append(tuple(map(float,s[1:4])))
 elif s[0]=='vt':uvs.append(tuple(map(float,s[1:3])))
 elif s[0]=='g':group=s[1]
 elif s[0]=='f' and group=='body':faces.append([tuple(int(t)-1 for t in x.split('/')[:2]) for x in s[1:]])
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scale=1.8/16.6589
me=bpy.data.meshes.new('MakeHuman_body_native_UV')
me.from_pydata([(z*scale,x*scale,(y+8.1676)*scale) for x,y,z in verts],[],[[q[0] for q in f] for f in faces]);me.update()
uv=me.uv_layers.new(name='UVMap')
for poly,f in zip(me.polygons,faces):
 for li,q in zip(poly.loop_indices,f):uv.data[li].uv=uvs[q[1]]
 poly.use_smooth=True
ob=bpy.data.objects.new('body',me);bpy.context.collection.objects.link(ob)
mat=bpy.data.materials.new('Hero skin');mat.use_nodes=True;n=mat.node_tree.nodes;links=mat.node_tree.links;n.clear()
out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled');links.new(bs.outputs['BSDF'],out.inputs['Surface'])
bs.inputs['Subsurface Weight'].default_value=.22;bs.inputs['Subsurface Radius'].default_value=(.001,.00045,.00025)
# Scale is meters; low SSS amount avoids wax. SSS mask modulates weight.
for key,socket in [('basecolor','Base Color'),('roughness','Roughness')]:
 t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(root/('hero_skin_body_'+key+'.png')))
 if key!='basecolor':t.image.colorspace_settings.name='Non-Color'
 links.new(t.outputs['Color'],bs.inputs[socket])
t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(root/'hero_skin_body_normal_opengl.png'));t.image.colorspace_settings.name='Non-Color'
nm=n.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.25;links.new(t.outputs['Color'],nm.inputs['Color']);links.new(nm.outputs['Normal'],bs.inputs['Normal'])
t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(root/'hero_skin_body_sss_mask.png'));t.image.colorspace_settings.name='Non-Color'
mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';mul.inputs[1].default_value=.30;links.new(t.outputs['Color'],mul.inputs[0]);links.new(mul.outputs[0],bs.inputs['Subsurface Weight'])
ob.data.materials.append(mat)
sub=ob.modifiers.new('Diagnostic subdivision','SUBSURF');sub.levels=1
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=64;sc.cycles.use_denoising=False;sc.cycles.seed=1703
sc.render.threads_mode='FIXED';sc.render.threads=4
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGB';sc.render.resolution_percentage=100
sc.world.color=(.18,.21,.26)
sc.world.use_nodes=True;bg=sc.world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.18,.21,.26,1);bg.inputs['Strength'].default_value=.2
sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast';sc.view_settings.exposure=-.2
for label,loc,power,size,color in [('key',(2.8,-3.5,6),520,2.3,(.94,.92,.85)),('fill',(-3,1,4),140,3,(.60,.70,.85)),('bounce',(3,4,2.5),65,4,(.64,.68,.74))]:
 d=bpy.data.lights.new(label,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color;o=bpy.data.objects.new(label,d);bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,1.2))-o.location).to_track_quat('-Z','Y').to_euler()
cam=bpy.data.cameras.new('Diagnostic camera');co=bpy.data.objects.new('Diagnostic camera',cam);bpy.context.collection.objects.link(co);sc.camera=co;cam.type='ORTHO'
# Orthographic material review, not an approved game-sprite export.
views=[('front',(4,0,1.65),(.09,0,1.65),.48),('profile',(0,4,1.65),(.06,0,1.65),.48),('back',(-4,0,1.65),(0,0,1.65),.48),('hands_front',(4,.43,1.04),(.13,.43,1.04),.40),('hands_back',(-4,.43,1.04),(.13,.43,1.04),.40)]
body_views=[('body_front',(4,0,.9),(0,0,.9),2.1),('body_profile',(0,4,.9),(0,0,.9),2.1),('body_back',(-4,0,.9),(0,0,.9),2.1)]
views=body_views if '--body-only' in sys.argv else views+body_views
for label,loc,target,ortho in views:
 co.location=loc;co.rotation_euler=(Vector(target)-co.location).to_track_quat('-Z','Y').to_euler();cam.ortho_scale=ortho
 sc.render.resolution_x=768;sc.render.resolution_y=768;sc.render.filepath=str(root/'podglad'/('skin_'+label+'.png'));bpy.ops.render.render(write_still=True)
print('Rendered',len(views),'material checks in Blender',bpy.app.version_string)
