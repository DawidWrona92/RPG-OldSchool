"""P2: prawdziwe wypalenia Cycles, siatka UV i podglądy z zapisanego źródła.

Normal: ewaluowana powierzchnia stroju -> jej bazowa siatka UV, tangent OpenGL.
Curvature: podpisany lokalny Laplacian powierzchni, neutralnie 0.5; nie AO.
Height ground: światowe Z / 1.8, nie wysokość mikrodetalu.
"""
import sys,json,math,argparse,zlib,struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v2_common import *
import numpy as np
ap=argparse.ArgumentParser();ap.add_argument('--parts',nargs='+');ap.add_argument('--resume',action='store_true');args=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
source=Path(bpy.data.filepath);source_sha=sha(source);sc=bpy.context.scene;out=ROOT/'handoff/p2';out.mkdir(parents=True,exist_ok=True)
manifest_path=out/'manifest.json';manifest={'source_blend_sha256':source_sha,'baker_sha256':sha(__file__),'source':'../../source/bohater_v2.blend','status':'P2_TEMPORARY_CLOTHING_BEFORE_B2','parts':{},'maps':{'uv':'Unikatowe wyspy, szablon krawędzi bazowej siatki.','ao':'Cycles Ambient Occlusion, odległość 0.15 m; realna geometria całego stroju/ciała; nie do mnożenia przez skórę.','curvature':'Lokalny podpisany Laplacian geometrii, 0 wklęsłe / .5 płaskie / 1 wypukłe; brak high-poly ręcznej rzeźby.','normal_sculpt':'Cycles selected-to-active, ewaluowana geometria z fałdami/Subsurf/Solidify na bazową siatkę UV, tangent OpenGL; nie skan i nie ręczny high-poly.','height_ground':'Z w metrach / 1.8; 16-bit grayscale, 0 ziemia / 1 wysokość 1.8 m.','id':'Płaskie kolory regionów opisane przy części, nie końcowy kolor.','preview':'768 px, szary materiał, izolowany element; kamera diagnostyczna, nie skala gry.'}}
if args.resume and manifest_path.exists():
    old=json.loads(manifest_path.read_text());assert old['source_blend_sha256']==source_sha and old['baker_sha256']==sha(__file__),'Nie mieszaj rewizji P2';manifest=old
def png(path,array):
    a=np.ascontiguousarray(array);h,w=a.shape[:2];depth=16 if a.dtype==np.uint16 else 8;color=0 if a.ndim==2 else 2
    if depth==16:a=a.astype('>u2')
    raw=b''.join(b'\0'+row.tobytes() for row in a)
    def chunk(k,d):return struct.pack('>I',len(d))+k+d+struct.pack('>I',zlib.crc32(k+d)&0xffffffff)
    Path(path).write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,depth,color,0,0,0))+chunk(b'IDAT',zlib.compress(raw,6))+chunk(b'IEND',b''))
def write_image(img,path,scalar=False):
    size=img.size[0];a=np.empty(size*size*4,dtype=np.float32);img.pixels.foreach_get(a);a=a.reshape(size,size,4)[::-1]
    if scalar:png(path,np.round(np.clip(a[:,:,0],0,1)*65535).astype(np.uint16))
    else:png(path,np.round(np.clip(a[:,:,:3],0,1)*255).astype(np.uint8))
def assign_id(name,p):
    z=p.z
    if name=='koszula':return 2 if z<1.065 else 3 if z>1.42 else 4 if abs(p.y)>.21 and z<1.25 else 1
    if name=='kaftan':return 2 if z<1.12 else 3 if abs(p.y)<.025 else 1
    if name.startswith('but_'):return 2 if z<.04 else 3 if z>.49 else 1
    if name=='plecak':return 2 if z>1.32 else 3 if z<1.19 else 1
    if name in ['plaszcz','peleryna','kaptur']:return 2 if z<(.37 if name=='plaszcz' else 1.36 if name=='peleryna' else 1.56) else 1
    if name=='spodnie':return 2 if z<.65 else 3 if .7<z<.8 and p.y>.1 else 1
    return 1
palette=[(0,0,0),(1,0,0),(0,1,0),(0,0,1),(1,1,0)]
parts=[o for o in sc.objects if o.type=='MESH' and o.get('p2_part')]
sc.cycles.samples=32;sc.render.threads_mode='FIXED';sc.render.threads=4;sc.render.bake.margin=16;sc.render.bake.use_clear=True
for part in parts:
    if args.parts and part.name not in args.parts:continue
    old=manifest['parts'].get(part.name)
    if old and all((out/f).is_file() and sha(out/f)==h for f,h in old['files'].items()):print('P2_REUSE',part.name,flush=True);continue
    print('P2_START',part.name,flush=True)
    size=int(part.get('texture_resolution',2048));files={}
    # P2 low ma dokładnie bazowe UV części; siatki źródłowej nie zmieniamy.
    low=part.copy();low.data=part.data.copy();sc.collection.objects.link(low);low.name='P2_LOW_TEMP';low.parent=None;low.matrix_world=part.matrix_world.copy()
    for m in list(low.modifiers):low.modifiers.remove(m)
    low.data.materials.clear();mat=plain('P2_BAKE_TEMP',(.4,.4,.4));low.data.materials.append(mat);nodes=mat.node_tree.nodes;links=mat.node_tree.links;nodes.clear();output=nodes.new('ShaderNodeOutputMaterial');emit=nodes.new('ShaderNodeEmission');links.new(emit.outputs[0],output.inputs[0]);target=nodes.new('ShaderNodeTexImage');nodes.active=target
    # Curvature bazowej powierzchni, z grubością już wyłączoną.
    adj=[set() for v in low.data.vertices]
    for edge in low.data.edges:a,b=edge.vertices;adj[a].add(b);adj[b].add(a)
    attr=low.data.attributes.new('p2_curvature','FLOAT','POINT')
    for i,v in enumerate(low.data.vertices):
        avg=sum((low.data.vertices[j].co for j in adj[i]),Vector())/max(1,len(adj[i]));attr.data[i].value=max(0,min(1,.5-(avg-v.co).dot(v.normal)*60))
    attr=low.data.color_attributes.new(name='p2_id',type='FLOAT_COLOR',domain='CORNER')
    regions=set()
    for p in low.data.polygons:
        k=assign_id(part.name,p.center);regions.add(k)
        for li in p.loop_indices:attr.data[li].color=(*palette[k],1)
    hidden=part.hide_render;part.hide_render=True
    for kind in ['ao','curvature','height_ground','id','normal_sculpt']:
        img=bpy.data.images.new('P2_TARGET_TEMP',width=size,height=size,alpha=True,float_buffer=True);img.colorspace_settings.name='Non-Color';target.image=img;nodes.active=target;active(low);sc.render.bake.use_selected_to_active=False
        for link in list(emit.inputs['Color'].links):links.remove(link)
        if kind=='ao':
            n=nodes.new('ShaderNodeAmbientOcclusion');n.inputs['Distance'].default_value=.15;n.samples=16;links.new(n.outputs['AO'],emit.inputs['Color'])
        elif kind=='curvature':n=nodes.new('ShaderNodeAttribute');n.attribute_name='p2_curvature';links.new(n.outputs['Fac'],emit.inputs['Color'])
        elif kind=='id':n=nodes.new('ShaderNodeVertexColor');n.layer_name='p2_id';links.new(n.outputs['Color'],emit.inputs['Color'])
        elif kind=='height_ground':
            n=nodes.new('ShaderNodeNewGeometry');sep=nodes.new('ShaderNodeSeparateXYZ');links.new(n.outputs['Position'],sep.inputs[0]);mul=nodes.new('ShaderNodeMath');mul.operation='DIVIDE';mul.inputs[1].default_value=1.8;links.new(sep.outputs['Z'],mul.inputs[0]);links.new(mul.outputs[0],emit.inputs['Color'])
        if kind=='normal_sculpt':
            part.hide_render=False;bpy.context.view_layer.update();ev=part.evaluated_get(bpy.context.evaluated_depsgraph_get());hi=bpy.data.objects.new('P2_HIGH_TEMP',bpy.data.meshes.new_from_object(ev));sc.collection.objects.link(hi);hi.matrix_world=part.matrix_world.copy();part.hide_render=True;active(low);hi.select_set(True);sc.render.bake.use_selected_to_active=True;sc.render.bake.cage_extrusion=.025;sc.render.bake.max_ray_distance=.05;sc.render.bake.normal_space='TANGENT';sc.render.bake.normal_r='POS_X';sc.render.bake.normal_g='POS_Y';sc.render.bake.normal_b='POS_Z';bpy.ops.object.bake(type='NORMAL');bpy.data.objects.remove(hi,do_unlink=True)
        else:bpy.ops.object.bake(type='EMIT')
        file=part.name+'_'+kind+'.png';write_image(img,out/file,kind in ['ao','curvature','height_ground']);files[file]=sha(out/file);bpy.data.images.remove(img)
        print('P2_MAP',file,flush=True)
    # Dokładne współrzędne do szablonu rysowanego w Pillow, bez zależności od dodatku UV.
    uv=low.data.uv_layers.active;layout=[[list(uv.data[i].uv) for i in p.loop_indices] for p in low.data.polygons]
    layoutfile=out/(part.name+'_uv.json');layoutfile.write_text(json.dumps({'size':size,'polygons':layout},separators=(',',':')))
    bpy.data.objects.remove(low,do_unlink=True);part.hide_render=hidden
    # Podgląd oryginalnej EWALUOWANEJ części, nie uproszczonej geometrii bake.
    vis={o.name:o.hide_render for o in sc.objects};mats=list(part.data.materials)
    for o in sc.objects:
        if o.type in ['MESH','CURVE','CURVES']:o.hide_render=o!=part
    part.data.materials.clear();part.data.materials.append(plain('P2_PREVIEW_GRAY',(.32,.32,.32),.8));camera=sc.camera;oldcam=(camera.matrix_world.copy(),camera.data.ortho_scale)
    corners=[part.matrix_world@Vector(c) for c in part.bound_box];center=sum(corners,Vector())/8;maxdim=max(max(p[i] for p in corners)-min(p[i] for p in corners) for i in range(3));camera.location=center+Vector((4,-3,2));camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=max(.12,maxdim*1.6)
    sc.render.resolution_x=sc.render.resolution_y=768;sc.cycles.samples=64;sc.view_layers['Cień'].use=False;sc.node_tree.nodes['Oddzielny cień'].mute=True;file=part.name+'_preview.png';sc.render.filepath=str(out/file);bpy.ops.render.render(write_still=True);files[file]=sha(out/file)
    for o in sc.objects:
        if o.name in vis:o.hide_render=vis[o.name]
    part.data.materials.clear()
    for m in mats:part.data.materials.append(m)
    camera.matrix_world=oldcam[0];camera.data.ortho_scale=oldcam[1];sc.view_layers['Cień'].use=True;sc.node_tree.nodes['Oddzielny cień'].mute=False;sc.cycles.samples=32
    manifest['parts'][part.name]={'resolution':[size,size],'texel_density_px_m':part['texel_density_px_m'],'construction':part.get('construction','Osobna edytowalna część stroju.'),'id_regions':{str(k):{'rgb':palette[k],'meaning':{1:'główna powierzchnia',2:'dolny brzeg / podeszwa / panel dolny',3:'górny panel / zapięcie / łata',4:'podwinięcie rękawa'}[k]} for k in regions},'files':files,'uv_layout_pending':layoutfile.name}
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print('P2_PART_DONE',part.name,flush=True)
assert sha(source)==source_sha,'Źródło zmieniło się podczas bake'
