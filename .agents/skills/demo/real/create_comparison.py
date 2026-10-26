"""Optional montage generator. Requires Pillow; not used by the JS sprite engines."""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
O=Path(__file__).resolve().parent/'output'
items=[('RETRO / chałupa','retro_fortified_cottage.png'),('RETRO / piechur','retro_blue_swordsman.png'),('PAINTED / dom','painted_market_house_preview.png'),('PAINTED / wojownik','painted_swordsman_preview.png'),('3D / dom','prerender_timber_house_preview.png'),('3D / wieża','prerender_guard_tower_preview.png')]
W,H=1200,1350
canvas=Image.new('RGB',(W,H),(24,29,38));d=ImageDraw.Draw(canvas)
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
f=ImageFont.truetype(font,23); f2=ImageFont.truetype(font,16)
d.text((35,16),'RTS SPRITES — WYNIKI Z PRAWDZIWYCH SILNIKÓW',fill='#ffffff',font=f)
for idx,(name,file) in enumerate(items):
 col,row=idx%2,idx//2;x,y=25+col*590,70+row*420
 d.rounded_rectangle((x,y,x+570,y+398),radius=15,fill=(45,50,60),outline=(72,77,88),width=2)
 d.text((x+18,y+14),name,fill=(230,227,217),font=f)
 im=Image.open(O/file).convert('RGBA'); scale=min(524/im.width,330/im.height,3)
 new=(max(1,round(im.width*scale)),max(1,round(im.height*scale)))
 im=im.resize(new,Image.Resampling.NEAREST if 'retro' in file else Image.Resampling.LANCZOS)
 bg=Image.new('RGBA',new,(46,58,65,255));bg.alpha_composite(im)
 canvas.paste(bg.convert('RGB'),(x+(570-new[0])//2,y+51+(330-new[1])//2))
 d.text((x+18,y+365),file,fill='#c0c7cc',font=f2)
canvas.save(O/'real_engine_comparison.png')
