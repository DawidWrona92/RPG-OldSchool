"""Side-by-side review, with separate illustration/reference lighting identified."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
r=Path(__file__).resolve().parents[1]/'podglad/v4'
font=ImageFont.load_default(size=21)
rows=[('front','Front'),('profile','Profile'),('face_close','Face close-up'),('eye','Eye')]
im=Image.new('RGB',(1536,len(rows)*812),(29,31,33));d=ImageDraw.Draw(im)
for i,(name,label) in enumerate(rows):
 for j,v in enumerate(['before','after']):
  src=Image.open(r/v/f'skin_{name}.png').convert('RGB');assert src.size==(768,768)
  im.paste(src,(j*768,i*812+44));d.text((j*768+12,i*812+10),label+f' / V{3+j} / normal 0.45',font=font,fill=(225,225,220))
im.save(r/'porownanie.png')
im=Image.new('RGB',(1536,812),(29,31,33));d=ImageDraw.Draw(im)
ref=ImageOps.contain(Image.open(r/'reference/concept19.jpg').convert('RGB'),(768,768),Image.Resampling.LANCZOS)
im.paste(ref,((768-ref.width)//2,44+(768-ref.height)//2));im.paste(Image.open(r/'after/skin_face_close.png').convert('RGB'),(768,44))
d.text((12,10),'Concept19 v2 / illustration lighting',font=font,fill=(225,225,220));d.text((780,10),'V4 / unchanged base OBJ / contract lighting',font=font,fill=(225,225,220))
im.save(r/'koncept19-v4.png')
