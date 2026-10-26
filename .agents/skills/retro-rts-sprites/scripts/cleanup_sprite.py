#!/usr/bin/env python3
"""Intentional conversion from imported art to true hard-pixel palette.
DO NOT use for painterly/3D output unless conversion to pixel-art is intended.
"""
import argparse,json
from pathlib import Path
from PIL import Image
from pixelcraft import clean_import
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('--out',default=None);ap.add_argument('--max-colors',type=int,default=24)
    ap.add_argument('--alpha-threshold',type=int,default=128)
    a=ap.parse_args();inp=Path(a.input);out=Path(a.out or inp.with_name(inp.stem+'_clean.png'))
    if not 2<=a.max_colors<=256:ap.error('--max-colors must be 2..256')
    report=clean_import(str(inp),str(out),a.max_colors,a.alpha_threshold)
    out.with_suffix('.json').write_text(json.dumps(report,indent=2))
    print('Saved:',out)
