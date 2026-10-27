"""Validate actual deliverables, decoded PNG samples and current hashes.
python3 source/validate.py --mesh /tmp/base.obj [--write-report]
The manifest is intentionally not self-hashed.
"""
import argparse,hashlib,json,struct
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates
from build_maps import mesh_data
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--mesh',required=True);p.add_argument('--write-report',action='store_true');args=p.parse_args()
results={'status':'PROTOTYPE_NOT_APPROVED','png':[]}
expected=[f'hero_skin_body_{m}{s}.png' for m in ['basecolor','roughness','normal_opengl','height','sss_mask'] for s in ['', '_2048']]+['hero_eye_iris_basecolor.png','hero_eye_sclera_basecolor.png']
for name in expected:
 path=root/name;im=Image.open(path);im.verify();im=Image.open(path);im.load();a=np.array(im)
 size=512 if 'eye' in name else 2048 if '_2048' in name else 4096
 assert im.size==(size,size),(name,im.size)
 assert path.read_bytes()[24]==(16 if 'height' in name else 8),name
 if 'normal' in name:
  assert im.mode=='RGB'
  nn=a.astype(np.float32)/255*2-1
  err=np.abs(np.linalg.norm(nn,axis=2)-1)
  assert err.max()<.012,(name,float(err.max()))
  assert nn[:,:,2].min()>0
 if 'roughness' in name or 'sss_mask' in name:assert im.mode=='L',name
 if 'height' in name:assert im.mode in ('I;16','I;16B','I') and a.min()<32768<a.max(),name
 if 'body_basecolor' in name:assert a.min()>0 and im.mode=='RGB'
 results['png'].append({'file':name,'resolution':list(im.size),'mode':im.mode,'bits':path.read_bytes()[24],'min':int(a.min()),'max':int(a.max())})
# Green must agree with positive image-row height derivative for OpenGL (+v up).
h=np.array(Image.open(root/'hero_skin_body_height.png')).astype(np.float32)/65535
normal=np.array(Image.open(root/'hero_skin_body_normal_opengl.png')).astype(np.float32)/255*2-1
dy,dx=np.gradient(h);mask=(np.abs(dy)>1e-4)&(normal[:,:,2]>.4)
corr=float(np.corrcoef(dy[mask],normal[:,:,1][mask])[0,1]);assert corr>.95,corr
results['opengl_green_height_correlation']=corr
# True 2K scalar maps must derive from the 4K values, not nearest-neighbor duplicates.
for name in ['basecolor','roughness','height','sss_mask']:
 big=Image.open(root/f'hero_skin_body_{name}.png')
 if name!='basecolor':big=Image.fromarray(np.array(big).astype(np.float32)/(65535 if name=='height' else 255))
 small=big.resize((2048,2048),Image.Resampling.LANCZOS)
 ref=np.array(small)
 if name!='basecolor':ref=np.rint(np.clip(ref,0,1)*(65535 if name=='height' else 255))
 actual=np.array(Image.open(root/f'hero_skin_body_{name}_2048.png'))
 assert np.abs(ref.astype(np.int32)-actual.astype(np.int32)).max()<=1,name
# UV seam vertex pairs: useful numerical evidence, not a substitute for a final render.
v,uv,faces=mesh_data(args.mesh);byvertex={}
for face in faces:
 for vi,ui in face:byvertex.setdefault(vi,set()).add(ui)
a=np.array(Image.open(root/'hero_skin_body_basecolor.png')).astype(np.float32)
diffs=[]
for ids in byvertex.values():
 if len(ids)<2:continue
 coord=uv[list(ids)]
 samples=np.array([map_coordinates(a[:,:,ch],[(1-coord[:,1])*4096-.5,coord[:,0]*4096-.5],order=1,mode='nearest') for ch in range(3)]).T
 diffs.extend(np.max(np.abs(samples-samples[0]),axis=1)[1:].tolist())
results['seam_vertex_samples']={'count':len(diffs),'median_rgb_8bit':float(np.median(diffs)),'p95_rgb_8bit':float(np.percentile(diffs,95)),'max_rgb_8bit':float(np.max(diffs))}
assert np.percentile(diffs,95)<=2 and np.max(diffs)<=8,results['seam_vertex_samples']
results['seam_vertex_thresholds_rgb_8bit']={'p95_max':2,'absolute_max':8}
# Existing eye alpha correctly encodes 80% iris diameter.
eye=Image.open(root/'hero_eye_iris_basecolor.png');bbox=eye.getchannel('A').getbbox()
assert 405<=bbox[2]-bbox[0]<=414
results['iris_alpha_bbox']=list(bbox)
manifest_path=root/'manifest.json'
if manifest_path.exists() and json.loads(manifest_path.read_text()).get('material_version',0)>=4:
 from face_v4 import baseline
 region=np.array(Image.open(root.parents[4]/'docs/art/characters/tekstury-bohatera/uv-cialo-obszary-2048.png').convert('RGB'))
 protected=((region[:,:,0]==232)&(region[:,:,1]==150))|((region[:,:,0]==60)&(region[:,:,1]==120))
 for suffix,mult in [('',2),('_2048',1)]:
  pm=np.repeat(np.repeat(protected,mult,0),mult,1)
  for m in ['basecolor','roughness','height','normal_opengl','sss_mask']:
   name=f'hero_skin_body_{m}{suffix}.png';a=np.array(Image.open(root/name));b,_=baseline(root.parents[4],name)
   assert np.array_equal(a[pm],b[pm]),'Protected neck/hands changed: '+name
 results['v4_neck_hands_all_10_maps']='byte-identical to 35df59f'
 for name in ['hero_skin_body_sss_mask.png','hero_skin_body_sss_mask_2048.png','hero_eye_sclera_basecolor.png']:
  _,data=baseline(root.parents[4],name)
  assert (root/name).read_bytes()==data,'Preserved whole file changed: '+name
 results['v4_sss_sclera_complete_files']='byte-identical to 35df59f'
 eye=np.array(Image.open(root/'hero_eye_iris_basecolor.png')).astype(float)
 yy,xx=np.mgrid[:512,:512];rad=np.sqrt((xx-255.5)**2+(yy-255.5)**2)/204.8
 outer=eye[:,:,:3][(rad>.65)&(rad<.82)].mean(0);inner=eye[:,:,:3][(rad>.33)&(rad<.40)].mean(0)
 assert outer[1]>outer[0]+3 and outer[1]>outer[2]+3,outer
 assert inner[0]>inner[1]+2 and inner[1]>inner[2]+10,inner
 results['v4_iris_ring_rgb']={'gray_green_outer':outer.tolist(),'olive_brown_inner':inner.tolist()}
 feature=json.loads((root/'qa/v4_material_checks.json').read_text());assert feature['raised_scar_core_min']>.5
 assert [f['side'] for f in feature['scars'][:3]]==['left']*3
 results['v4_scar_core_min_height']=feature['raised_scar_core_min']

if manifest_path.exists():
 manifest=json.loads(manifest_path.read_text())
 actual={f.relative_to(root).as_posix() for f in root.rglob('*') if f.is_file() and f.name!='manifest.json' and '__pycache__' not in f.parts}
 assert actual=={e['file'] for e in manifest['files']},'Manifest inventory mismatch'
 for entry in manifest['files']:
  f=root/entry['file'];assert hashlib.sha256(f.read_bytes()).hexdigest()==entry['sha256'],entry['file']
 results['manifest_hashes']='passed'
if args.write_report:(root/'qa'/'validation.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(results,ensure_ascii=False,indent=2))
