#!/usr/bin/env python3
"""Inspect reference artwork objectively; writes report and human-fillable style card.
Requires Pillow. Does not automatically 'learn' composition, occlusion, or licensing.
"""
import argparse,sys,json
from pathlib import Path
from PIL import Image
from pixelcraft import analyze_reference
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('image');p.add_argument('--out',default=None);a=p.parse_args()
    source=Path(a.image);out=Path(a.out or str(source.with_suffix(''))+'_style');out.mkdir(parents=True,exist_ok=True)
    report=analyze_reference(str(source))
    (out/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    im=Image.open(source).convert('RGBA');scale=max(1,min(8,768//max(im.size)))
    im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST).save(out/'zoom.png')
    mask=im.getchannel('A');sil=Image.new('RGBA',im.size,(40,45,48,0));sil.paste((19,21,29,255),(0,0,im.width,im.height),mask)
    sil.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST).save(out/'silhouette.png')
    md='''# Karta stylu — {name}

Wypełnij PO obejrzeniu `zoom.png` i `silhouette.png`, nie wyłącznie na podstawie statystyk.

- Natywna rozdzielczość: {size}
- Liczba kolorów: {colors}
- Udział konturu: [ocena wizualna, nie estymować bez obrazu]
- Światło: [kierunek, stopień kontrastu]
- Sylwetka: [proporcje głowy, kończyn i sprzętu]
- Paleta/rampy: [odcień cienia i światła dla metalu, skóry, kamienia]
- Tekstura/dithering: [gdzie i jak często]
- Ankrowanie i kamera: [wybrane konwencje]

## Reguły do naśladowania

- [reguły projektowania, bez kopiowania konkretnego cudzego assetu]

## Błędy i antywzorce

- [co świadomie omijać]
'''.format(name=source.name,size=report['size'],colors=report['colors'])
    (out/'style-card.md').write_text(md,encoding='utf-8')
    print('Report written:',out)
