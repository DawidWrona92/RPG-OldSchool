"""Jawny pass materiałów Chunk03 na wybranej kopii poprawionej postaci.
Nie jest wywoływany przez eksport. Zachowuje geometrię, rig i zapisane klucze.
"""
from pathlib import Path
from collections import Counter,defaultdict
import bpy,json,hashlib,heapq,math
from mathutils import Vector
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;REPO=ROOT.parents[2];TEX=REPO/'assets/textures/characters/hero';scene=bpy.context.scene
assert scene.get('art_revision')=='refinement-04-carry-option'

def image_node(nodes,links,path,uv,channel='basecolor'):
 n=nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(TEX/path),check_existing=True);n.image.colorspace_settings.name='sRGB' if channel in ['basecolor','decal'] else 'Non-Color';n.image.pack();n.interpolation='Linear';n.extension='REPEAT';links.new(uv.outputs[0],n.inputs['Vector']);return n

def image_material(name,stem,base,rough,metal=False,sss=False):
 mat=bpy.data.materials.new(name);mat.use_nodes=True;nodes,links=mat.node_tree.nodes,mat.node_tree.links;nodes.clear();out=nodes.new('ShaderNodeOutputMaterial');bs=nodes.new('ShaderNodeBsdfPrincipled');links.new(bs.outputs[0],out.inputs['Surface'])
 uv=nodes.new('ShaderNodeUVMap');uv.uv_map='Materiał / metry'
 tex={c:image_node(nodes,links,f'{stem}_{c}.png',uv,c) for c in ['basecolor','roughness','height']}
 mix=nodes.new('ShaderNodeMixRGB');mix.name='Kontrolowany kolor materiału';mix.inputs[0].default_value=.55;mix.inputs[1].default_value=(*base,1);links.new(tex['basecolor'].outputs[0],mix.inputs[2]);links.new(mix.outputs[0],bs.inputs['Base Color'])
 rr=nodes.new('ShaderNodeMapRange');rr.inputs['To Min'].default_value=rough-.08;rr.inputs['To Max'].default_value=min(1,rough+.08);links.new(tex['roughness'].outputs[0],rr.inputs[0]);links.new(rr.outputs[0],bs.inputs['Roughness'])
 if metal:
  tex['metallic']=image_node(nodes,links,f'{stem}_metallic.png',uv,'metallic');links.new(tex['metallic'].outputs[0],bs.inputs['Metallic'])
 else:bs.inputs['Metallic'].default_value=0
 bs.inputs['Specular IOR Level'].default_value=.30
 if sss:bs.inputs['Subsurface Weight'].default_value=.075;bs.inputs['Subsurface Scale'].default_value=.012
 bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.12;bump.inputs['Distance'].default_value=.00015 if sss or metal else .00025;links.new(tex['height'].outputs[0],bump.inputs['Height']);links.new(bump.outputs[0],bs.inputs['Normal']);mat['texture_set']=stem;return mat
straps=image_material('Rzemienie / Chunk03','leather_straps_worn',(.07,.040,.019),.61)
iron=image_material('Żelazo okuć / Chunk03','iron_hardware_blackened',(.14,.15,.15),.59,True)
steel=image_material('Stal głowni / Chunk03','steel_sword_weathered',(.37,.39,.40),.36,True)
steel_edge=steel.copy();steel_edge.name='Szlif krawędzi / Chunk03'
for node in steel_edge.node_tree.nodes:
 if node.type=='MIX_RGB':node.inputs[1].default_value=(.52,.55,.56,1)
skin=image_material('Skóra podróżnika / Chunk03','skin_traveler_weathered',(.24,.155,.103),.64,sss=True)
hair=image_material('Włosy umbra / Chunk03','hair_dark_umber',(.022,.015,.009),.77)
assignments={}
for obj in bpy.data.objects:
 if obj.type!='MESH' or not obj.data.materials:continue
 name=obj.name;mat=None
 if name.startswith(('Pas naramienny','Pas skórzany','Rzemień posłania','Rękojeść','Pusta pochwa','Plecak / pionowy','Plecak / szelka')):mat=straps
 elif name.startswith(('Jelec','Głowica miecza','Sprzączka','Język sprzączki','Plecak / sprzączka','Okucie')):mat=iron
 elif name.startswith('Miecz /'):mat=steel
 elif name.startswith('Szlif ostrza'):mat=steel_edge
 elif name.startswith(('Anatomiczna głowa','Powieka')):mat=skin
 elif name.startswith(('Włosy /','Pasmo włosów','Brew /')):mat=hair
 if mat:obj.data.materials[0]=mat;assignments[name]=mat.name
 # Close the cylindrical UV seam with an integer number of texture repeats.
 # World scale unchanged; effective cloth circumference repeat ~0.314m.
 uv=obj.data.uv_layers.get('Materiał / metry')
 if uv and not name.startswith(('Plecak','Klapa')):
  c=math.tau*(.061 if name=='Zrolowane posłanie' else (.20 if name.startswith(('Krótki','Naramienna','Lniana tunika','Kaftan')) else .065))/.32
  for v in uv.data:v.uv.x*=round(c)/c
 # Edge selection comes from ACTUAL mesh boundary distance, not the supplied noise.
 mesh=obj.data;counts=Counter(tuple(sorted(e)) for p in mesh.polygons for e in p.edge_keys);boundary={i for e,n in counts.items() if n==1 for i in e}
 adj=defaultdict(list)
 for e in mesh.edges:
  a,b=e.vertices;length=(mesh.vertices[a].co-mesh.vertices[b].co).length;adj[a].append((b,length));adj[b].append((a,length))
 distance=[1e9]*len(mesh.vertices);queue=[]
 for i in boundary:distance[i]=0;heapq.heappush(queue,(0,i))
 while queue:
  cost,i=heapq.heappop(queue)
  if cost!=distance[i] or cost>.05:continue
  for j,length in adj[i]:
   candidate=cost+length
   if candidate<distance[j]:distance[j]=candidate;heapq.heappush(queue,(candidate,j))
 attr=mesh.attributes.get('edge_mask') or mesh.attributes.new('edge_mask','FLOAT','POINT')
 for i,v in enumerate(attr.data):v.value=.18*math.exp(-distance[i]/.008)
 dirtuv=mesh.uv_layers.get('Brud lokalny') or mesh.uv_layers.new(name='Brud lokalny')
 for poly in mesh.polygons:
  for idx in poly.loop_indices:
   p=mesh.vertices[mesh.loops[idx].vertex_index].co
   if name.startswith(('But /','Podeszwa')):u=(p.x+.06)/.26;v=p.z/.22
   elif name.startswith('Spodnie'):u=(p.y+.23)/.46;v=(p.z-.24)/.30
   else:u=(p.y+.32)/.64;v=(p.z-.60)/.27
   dirtuv.data[idx].uv=(u,v)
# Blade map follows its physical length rather than a world cylinder.
blade=bpy.data.objects['Miecz / głownia z grzbietem'];root=sum((v.co for v in list(blade.data.vertices)[:4]),Vector())/4;axis=Vector(scene['carry_axis']).normalized();side=(blade.data.vertices[1].co-blade.data.vertices[3].co).normalized()
for poly in blade.data.polygons:
 for idx in poly.loop_indices:
  delta=blade.data.vertices[blade.data.loops[idx].vertex_index].co-root;blade.data.uv_layers['Materiał / metry'].data[idx].uv=(.5+delta.dot(side)/.05,delta.dot(axis)/.7)
# Apply geometry-bounded wear, wetness and a non-tileable local mud decal.
for mat in list(bpy.data.materials):
 if not mat.use_nodes or not mat.get('texture_set') or any(x in mat['texture_set'] for x in ['skin','hair','steel','iron']):continue
 nodes,links=mat.node_tree.nodes,mat.node_tree.links;bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED');uv=nodes.new('ShaderNodeUVMap');uv.uv_map='Materiał / metry'
 edge=image_node(nodes,links,'overlays/edge_wear_breakup_mask.png',uv,'mask');wet=image_node(nodes,links,'overlays/wetness_breakup_mask.png',uv,'mask')
 edgeattr=nodes.new('ShaderNodeAttribute');edgeattr.attribute_name='edge_mask';wearattr=nodes.new('ShaderNodeAttribute');wearattr.attribute_name='wear_mask'
 def multiply(a,b,scale=1):
  n=nodes.new('ShaderNodeMath');n.operation='MULTIPLY';links.new(a,n.inputs[0]);links.new(b,n.inputs[1]);return n.outputs[0]
 edgefac=multiply(edgeattr.outputs['Fac'],edge.outputs[0]);wetfac=multiply(wearattr.outputs['Fac'],wet.outputs[0])
 prior=bs.inputs['Base Color'].links[0].from_socket
 worn=nodes.new('ShaderNodeMixRGB');worn.name='Przetarcie tylko przy geometrii krawędzi';worn.inputs[2].default_value=(.16,.115,.066,1);links.new(edgefac,worn.inputs[0]);links.new(prior,worn.inputs[1])
 damp=nodes.new('ShaderNodeMixRGB');damp.blend_type='MULTIPLY';damp.inputs[2].default_value=(.79,.80,.80,1);links.new(wetfac,damp.inputs[0]);links.new(worn.outputs[0],damp.inputs[1])
 localuv=nodes.new('ShaderNodeUVMap');localuv.uv_map='Brud lokalny';mud=image_node(nodes,links,'overlays/mud_spatter_decal_rgba.png',localuv,'decal');mud.extension='CLIP';mudfac=multiply(wearattr.outputs['Fac'],mud.outputs['Alpha'])
 dirty=nodes.new('ShaderNodeMixRGB');dirty.name='Lokalny decal błota, alpha × maska dołu';links.new(mudfac,dirty.inputs[0]);links.new(damp.outputs[0],dirty.inputs[1]);links.new(mud.outputs['Color'],dirty.inputs[2]);links.new(dirty.outputs[0],bs.inputs['Base Color'])
 priorrough=bs.inputs['Roughness'].links[0].from_socket
 roughmix=nodes.new('ShaderNodeMixRGB');roughmix.inputs[2].default_value=(.36,.36,.36,1);links.new(wetfac,roughmix.inputs[0]);links.new(priorrough,roughmix.inputs[1]);links.new(roughmix.outputs[0],bs.inputs['Roughness'])
# The trim is restricted to existing stitched edge geometry, not all clothing.
seam=bpy.data.materials.new('Szew krawędzi / trim Chunk03');seam.use_nodes=True;nodes,links=seam.node_tree.nodes,seam.node_tree.links;bs=nodes.get('Principled BSDF');uv=nodes.new('ShaderNodeUVMap');uv.uv_map='Szew / trim';tex=image_node(nodes,links,'overlays/stitching_trim_strip_rgba.png',uv,'decal');tex.extension='REPEAT';mix=nodes.new('ShaderNodeMixRGB');mix.inputs[1].default_value=(.06,.04,.024,1);links.new(tex.outputs['Alpha'],mix.inputs[0]);links.new(tex.outputs['Color'],mix.inputs[2]);links.new(mix.outputs[0],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.88
for obj in bpy.data.objects:
 if obj.type!='MESH' or not obj.name.startswith(('Kaftan / przetarty brzeg','Plecak / szew klinu')):continue
 obj.data.materials[0]=seam;uv=obj.data.uv_layers.new(name='Szew / trim');points=[obj.data.vertices[i].co for i in range(0,len(obj.data.vertices),8)];distances=[0]
 for i in range(1,len(points)):distances.append(distances[-1]+(points[i]-points[i-1]).length)
 for poly in obj.data.polygons:
  for idx in poly.loop_indices:
   vertex=obj.data.loops[idx].vertex_index;ring,side=divmod(vertex,8);uv.data[idx].uv=(distances[ring]/.08,side/7)
scene['art_revision']='refinement-05-chunk03';scene['material_commits']=scene['material_commits']+'; chunk03 ff74eb7';scene.frame_set(1);bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'bohater.blend'))
p=HERE/'art-source.json';data=json.loads(p.read_text());data.update(art_revision=scene['art_revision'],source_sha256=hashlib.sha256((HERE/'bohater.blend').read_bytes()).hexdigest(),chunk03_commit='ff74eb7',chunk03_assignments=assignments,mask_policy='mesh boundary distance × edge breakup; low garment mask × local mud alpha; low mask × wetness; trim only existing seam tubes',carry_axis=list(scene['carry_axis']),right_hand_carry=list(scene['right_hand_carry']),texture_files_sha256={str(p.relative_to(TEX)):hashlib.sha256(p.read_bytes()).hexdigest() for p in TEX.rglob('*.png')});p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print('CHUNK03_SAVED',data['source_sha256'])
