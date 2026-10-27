"""Ograniczona kontrola przecięć powierzchni zapisanych póz (bez symulacji kolizji).

Miecz vs skóra/strój/pakunek oraz dolny płaszcz vs spodnie. Nie bada objętości,
samoprzecięć całego modelu ani wszystkich chwil między kluczami.
"""
import json,sys
from pathlib import Path
import bpy
from mathutils.bvhtree import BVHTree
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
from render_player import activate
scene=bpy.context.scene;rig=bpy.data.objects['Bohater_RIG'];rig.rotation_euler.z=0

def tree(name,lower=None):
 obj=bpy.data.objects[name];evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh()
 verts=[evaluated.matrix_world@v.co for v in mesh.vertices]
 faces=[list(p.vertices) for p in mesh.polygons if lower is None or max(verts[i].z for i in p.vertices)<lower]
 result=BVHTree.FromPolygons(verts,faces,all_triangles=False,epsilon=0)
 evaluated.to_mesh_clear();return result

targets=['Anatomiczna głowa, szyja i odkryte przedramiona','Spodnie / marszczenia kolan','Lniana tunika / krój i pionowe fałdy','Kaftan / zszywane otwarte połacie','Krótki płaszcz / miękkie fałdy','Plecak podróżny','Zrolowane posłanie']
records=[]
for anim,count,step in [('spoczynek',8,10),('chod',12,2)]:
 activate(anim)
 for f in range(count):
  scene.frame_set(1+step*f);bpy.context.view_layer.update();sword=tree('Miecz / głownia z grzbietem')
  overlaps={name:len(sword.overlap(tree(name))) for name in targets}
  lower_cape=tree('Krótki płaszcz / miękkie fałdy',1.03);pants=tree('Spodnie / marszczenia kolan',1.03)
  records.append({'animation':anim,'frame':f,'sword_surface_intersections':overlaps,'lower_cape_pants_intersections':len(lower_cape.overlap(pants))})
  print('INTERSECTION_SAMPLE',anim,f,records[-1],flush=True)
report={'sampled_poses':len(records),'rotation_note':'Przecięcia nie zmieniają się po wspólnym obrocie do 8 kierunków.','method':'evaluated modifier meshes / triangle surface BVH overlap, epsilon=0','records':records,'scope_limits':['not continuous collision detection','no containment / solid volume proof','guard, grip and glove contacts excluded','layered upper torso intentional intersections excluded','pack straps, hair, fingers and self-collisions not exhaustively tested']}
p=HERE.parent/'previews/intersection-validation.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('INTERSECTION_DONE')
