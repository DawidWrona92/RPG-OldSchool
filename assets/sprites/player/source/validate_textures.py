"""Zweryfikuj dostarczone PNG względem manifestów Git blob; bez zmiany biblioteki."""
import hashlib,json
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT.parents[2];T=REPO/'assets/textures/characters/hero'
first=json.loads((T/'manifest.json').read_text());entries=[(e['path'],e['sha'],[512,512]) for e in first['data']]
for number in ['02','03']:
 chunk=json.loads((T/f'manifest.chunk{number}.json').read_text())
 for m in chunk['materials']:
  for e in m['maps'].values():entries.append((e['path'],e.get('git_blob_sha',e.get('sha')),[512,512]))
 for e in chunk.get('overlays',[]):entries.append((e['path'],e['sha'],e['resolution']))
files=[]
for name,expected,resolution in entries:
 p=REPO/name;raw=p.read_bytes();actual=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest();assert actual==expected,p
 im=Image.open(p);assert list(im.size)==resolution;files.append({'path':name,'git_blob_sha':actual,'size':list(im.size),'stored_mode':im.mode,'decoded_alpha_extrema':list(im.convert('RGBA').getchannel('A').getextrema())})
(ROOT/'previews/texture-input-validation.json').write_text(json.dumps({'verified_png_files':len(files),'source_commits':['7ce5c4b','c6c1a67','ff74eb7'],'files':files},indent=2)+'\n');print('PASS',len(files),'PNG from three manifests')
