"""Powtórz jedną parę postać/cień z zapisanego roboczego modelu w izolowanym katalogu."""
import hashlib,json,subprocess,tempfile
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'reviews/detale-01';source=ROOT/'source/bohater_detale.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest();file='spoczynek_1_00.png'
assert json.loads((OUT/'renders/motion_audit.json').read_text())['source_blend_sha256']==digest
with tempfile.TemporaryDirectory(prefix='welesza-detail-repro-',dir='/tmp') as folder:
 command=['blender','-b',str(source),'-t','4','--python-exit-code','1','--python',str(ROOT/'source/render_player.py'),'--','--pilot','--directions','1','--output',folder]
 r=subprocess.run(command,capture_output=True,text=True);assert r.returncode==0,r.stdout[-2000:]+r.stderr[-2000:];results={}
 for name,sub in [('body',''),('shadow','shadows')]:
  expected=np.array(Image.open(OUT/'renders'/sub/file)).astype(int);actual=np.array(Image.open(Path(folder)/sub/file)).astype(int);delta=np.abs(expected-actual);results[name]={'identical_decoded_pixels':bool(np.array_equal(expected,actual)),'max_rgba_error_0_255':int(delta.max()),'mean_rgba_error_0_255':float(delta.mean())};assert results[name]['identical_decoded_pixels'],results
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(OUT/'reproduction-validation.json').write_text(json.dumps({'source_sha256':digest,'frame':file,'results':results,'scope':'one repeated body/shadow pair from saved working blend; source unchanged'},indent=2)+'\n');print('PASS detail reproduction',results)
