"""Blender 4.3, read-only diagnostic renderer. blender -b -t 4 -P source/render_check.py -- /tmp/base.obj
Does not save or modify a blend file. Body group only, unchanged native UV.
"""
import bpy,sys,math,argparse
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser()
ap.add_argument('mesh');ap.add_argument('--texture-dir',type=Path,default=root)
ap.add_argument('--output-dir',type=Path,default=root/'podglad')
ap.add_argument('--eyes',action='store_true');ap.add_argument('--normal-strength',type=float,default=.45)
ap.add_argument('--view',nargs='+');ap.add_argument('--body-only',action='store_true');ap.add_argument('--comparison',action='store_true')
args=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
meshpath=args.mesh;args.output_dir.mkdir(parents=True,exist_ok=True)
verts=[];uvs=[];faces=[];eye_faces={};group=''
for l in open(meshpath):
 s=l.split()
 if not s:continue
 if s[0]=='v':verts.append(tuple(map(float,s[1:4])))
 elif s[0]=='vt':uvs.append(tuple(map(float,s[1:3])))
 elif s[0]=='g':group=s[1]
 elif s[0]=='f' and group=='body':faces.append([tuple(int(t)-1 for t in x.split('/')[:2]) for x in s[1:]])
 elif s[0]=='f' and group in ['helper-l-eye','helper-r-eye']:eye_faces.setdefault(group,[]).append([int(q.split('/')[0])-1 for q in s[1:]])
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
 t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(args.texture_dir/('hero_skin_body_'+key+'.png')))
 if key!='basecolor':t.image.colorspace_settings.name='Non-Color'
 links.new(t.outputs['Color'],bs.inputs[socket])
t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(args.texture_dir/'hero_skin_body_normal_opengl.png'));t.image.colorspace_settings.name='Non-Color'
nm=n.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=args.normal_strength;links.new(t.outputs['Color'],nm.inputs['Color']);links.new(nm.outputs['Normal'],bs.inputs['Normal'])
t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(args.texture_dir/'hero_skin_body_sss_mask.png'));t.image.colorspace_settings.name='Non-Color'
mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';mul.inputs[1].default_value=.30;links.new(t.outputs['Color'],mul.inputs[0]);links.new(mul.outputs[0],bs.inputs['Subsurface Weight'])
ob.data.materials.append(mat)
sub=ob.modifiers.new('Diagnostic subdivision','SUBSURF');sub.levels=1
# Optional diagnostic eyes reuse the untouched OBJ eye helpers, not a remodeled head.
if args.eyes:
 for label,ef in eye_faces.items():
  ids=sorted({i for f in ef for i in f});vv=[verts[i] for i in ids]
  cx=sum(v[0] for v in vv)/len(vv);cy=sum(v[1] for v in vv)/len(vv)
  em=bpy.data.meshes.new(label);remap={i:j for j,i in enumerate(ids)}
  em.from_pydata([(z*scale,x*scale,(y+8.1676)*scale) for x,y,z in vv],[],[[remap[i] for i in f] for f in ef]);em.update()
  euv=em.uv_layers.new(name='PlanarEyeUV')
  for poly in em.polygons:
   poly.use_smooth=True
   for li in poly.loop_indices:
    v=vv[em.loops[li].vertex_index];euv.data[li].uv=(.5+(v[0]-cx)/.135,.5+(v[1]-cy)/.135)
  eo=bpy.data.objects.new(label,em);bpy.context.collection.objects.link(eo)
  sub=eo.modifiers.new('Eye subdivision','SUBSURF');sub.levels=2
  et=bpy.data.materials.new(label+' diagnostic material');et.use_nodes=True;en=et.node_tree.nodes;el=et.node_tree.links
  eb=en.get('Principled BSDF');eb.inputs['Roughness'].default_value=.26
  iris=en.new('ShaderNodeTexImage');iris.image=bpy.data.images.load(str(args.texture_dir/'hero_eye_iris_basecolor.png'));iris.extension='EXTEND'
  sclera=en.new('ShaderNodeTexImage');sclera.image=bpy.data.images.load(str(args.texture_dir/'hero_eye_sclera_basecolor.png'));sclera.extension='EXTEND'
  mix=en.new('ShaderNodeMixRGB');el.new(iris.outputs['Alpha'],mix.inputs[0]);el.new(sclera.outputs['Color'],mix.inputs[1]);el.new(iris.outputs['Color'],mix.inputs[2]);el.new(mix.outputs[0],eb.inputs['Base Color'])
  eo.data.materials.append(et)
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
if args.eyes:
 views.extend([('face_close',(4,0,1.67),(.12,0,1.67),.31),('eye',(4,.0333,1.67),(.145,.0333,1.67),.065)])
views.append(('hands_dorsal',(.23,4,1.10),(.23,.48,1.10),.40))
body_views=[('body_front',(4,0,.9),(0,0,.9),2.1),('body_profile',(0,4,.9),(0,0,.9),2.1),('body_back',(-4,0,.9),(0,0,.9),2.1)]
views=body_views if args.body_only else [v for v in views if v[0]!='back'] if args.comparison else views+body_views
if args.view:views=[v for v in views if v[0] in args.view]
for label,loc,target,ortho in views:
 co.location=loc;co.rotation_euler=(Vector(target)-co.location).to_track_quat('-Z','Y').to_euler();cam.ortho_scale=ortho
 sc.render.resolution_x=768;sc.render.resolution_y=768;sc.render.filepath=str(args.output_dir/('skin_'+label+'.png'));bpy.ops.render.render(write_still=True)
print('Rendered',len(views),'material checks in Blender',bpy.app.version_string)
