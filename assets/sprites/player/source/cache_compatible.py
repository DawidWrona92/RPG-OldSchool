"""Read-only decision for one pipeline component; incompatible generated cache is rebuilt."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--model',type=Path,required=True);p.add_argument('--audit',type=Path,required=True);p.add_argument('--lighting',default='base');p.add_argument('--size',type=int,default=384);p.add_argument('--sheathed',action='store_true');a=p.parse_args()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
try:
 data=json.loads(a.audit.read_text());version=subprocess.check_output(['blender','--version'],text=True).splitlines()[0].removeprefix('Blender ')
 expected={'blender':version,'engine':'CYCLES','samples':64,'shadow_samples':16,'size_px':a.size,'seed':1703,'denoising':False,'threads':4,'lighting':a.lighting,'sheathed':a.sheathed}
 compatible=data.get('source_blend_sha256')==sha(a.model) and data.get('renderer_sha256')==sha(Path(__file__).with_name('render_player.py')) and data.get('render')==expected
except (OSError,ValueError,KeyError,subprocess.SubprocessError):compatible=False
if not compatible:print('Odtworzę wygenerowany składnik z bieżącego źródła:',a.audit.parent)
sys.exit(0 if compatible else 1)
