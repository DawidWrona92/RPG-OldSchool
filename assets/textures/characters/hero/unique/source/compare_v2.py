"""Deterministic review sheet; original renders are copied without alteration."""
from pathlib import Path
import argparse
from PIL import Image,ImageDraw,ImageFont
ap=argparse.ArgumentParser();ap.add_argument('--version',type=int,default=2);args=ap.parse_args()
root=Path(__file__).resolve().parents[1]/'podglad'/f'v{args.version}'
rows=[('front','Portret / front'),('profile','Profil'),('hands_dorsal','Grzbiet dloni')]
out=Image.new('RGB',(1536,3*(768+44)),(29,31,33))
d=ImageDraw.Draw(out);font=ImageFont.load_default(size=22)
for i,(name,label) in enumerate(rows):
 for j,version in enumerate(['before','after']):
  with Image.open(root/version/f'skin_{name}.png') as im:
   assert im.size==(768,768);out.paste(im,(j*768,i*812+44))
  d.text((j*768+16,i*812+10),label+' / '+f'V{args.version-1 if j==0 else args.version}'+' | normal 0.45',font=font,fill=(224,223,216))
out.save(root/'porownanie.png')
