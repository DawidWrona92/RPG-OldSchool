"""Sprawdź wznowienie i naprawę uszkodzonej klatki na izolowanej kopii w /tmp."""
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=ROOT/'source/bohater.blend';source_sha=sha(source);file='spoczynek_0_00.png';audit=json.loads((ROOT/'renders/motion_audit.json').read_text());audit['frames']={file:audit['frames'][file]}
with tempfile.TemporaryDirectory(prefix='welesza-cache-',dir='/tmp') as directory:
 folder=Path(directory);(folder/'shadows').mkdir();shutil.copy2(ROOT/'renders'/file,folder/file);shutil.copy2(ROOT/'renders/shadows'/file,folder/'shadows'/file);(folder/'motion_audit.json').write_text(json.dumps(audit))
 expected=[np.array(Image.open(folder/file)),np.array(Image.open(folder/'shadows'/file))]
 command=['blender','-b',str(source),'-t','4','--python-exit-code','1','--python',str(ROOT/'source/render_player.py'),'--','--pilot','--directions','0','--output',str(folder),'--resume']
 first=subprocess.run(command,cwd=REPO,capture_output=True,text=True);assert first.returncode==0,first.stdout[-2000:]+first.stderr[-2000:];assert first.stdout.count('WELESZA_REUSE')==1 and 'WELESZA_FRAME' not in first.stdout
 (folder/file).write_bytes(b'deliberately corrupted isolated fixture')
 second=subprocess.run(command,cwd=REPO,capture_output=True,text=True);assert second.returncode==0,second.stdout[-2000:]+second.stderr[-2000:];assert second.stdout.count('WELESZA_FRAME')==1
 identical=[np.array_equal(a,np.array(Image.open(p))) for a,p in zip(expected,[folder/file,folder/'shadows'/file])];assert all(identical),identical
 # A changed source fingerprint must reject the cache before any PNG changes.
 wrong=json.loads((folder/'motion_audit.json').read_text());wrong['source_blend_sha256']='0'*64;(folder/'motion_audit.json').write_text(json.dumps(wrong));previous=sha(folder/file)
 third=subprocess.run(command,cwd=REPO,capture_output=True,text=True);assert third.returncode!=0 and 'Cache differs: source_blend_sha256' in third.stdout+third.stderr;assert previous==sha(folder/file)
full=subprocess.run(['blender','-b',str(source),'-t','4','--python-exit-code','1','--python',str(ROOT/'source/render_player.py'),'--','--all','--resume'],cwd=REPO,capture_output=True,text=True)
assert full.returncode==0,full.stdout[-2000:]+full.stderr[-2000:]
assert full.stdout.count('WELESZA_REUSE')==160 and 'WELESZA_FRAME' not in full.stdout
assert sha(source)==source_sha
report={'source_blend_sha256':source_sha,'full_set_resume_reused_frames':160,'cache_reused_frames':1,'cache_rendered_frames':0,'isolated_corrupt_frame_repaired':1,'identical_decoded_body_pixels':identical[0],'identical_decoded_shadow_pixels':identical[1],'changed_source_cache_rejected':True,'canonical_blend_unchanged':True,'scope':'one body/shadow pair and source-mismatch rejection in isolated temporary directory; full 160-frame cache reused with zero renders'}
(ROOT/'previews/resume-validation.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',json.dumps(report))
