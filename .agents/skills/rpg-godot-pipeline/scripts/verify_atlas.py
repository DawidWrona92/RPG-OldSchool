#!/usr/bin/env python3
"""Validate atlas PNG+JSON for both the existing Godot prototype and rpg-sprite-v4.
No Godot binary needed; this does NOT test in-engine playback.
"""
import argparse,json,sys
from collections import Counter
from PIL import Image

def validate(img_path, json_path):
    im=Image.open(img_path).convert('RGBA');m=json.load(open(json_path,encoding='utf-8'))
    width,height=map(int,m.get('frame_size',[]))
    anchor=m.get('anchor',[]);frames=m.get('frames',[])
    errors=[];warn=[];view=Counter();records=[]
    if not(0<=anchor[0]<width and 0<=anchor[1]<height):errors.append('anchor outside frame')
    for i,f in enumerate(frames):
        x,y=int(f['x']),int(f['y']);deg=float(f.get('view_angle_deg',f.get('direction',0)*45))
        direction=int(round(deg/45))%8;view[direction]+=1
        if x<0 or y<0 or x+width>im.width or y+height>im.height:
            errors.append(f'frame {i} outside atlas');continue
        crop=im.crop((x,y,x+width,y+height));alpha=crop.getchannel('A')
        if not alpha.getbbox():errors.append(f'frame {i} blank');continue
        bbox=alpha.getbbox()
        if bbox[0]==0 or bbox[1]==0 or bbox[2]==width or bbox[3]==height:
            errors.append(f'frame {i} touches edge')
        records.append((direction,crop.tobytes()))
    if len(view)!=8:errors.append(f'expected eight directions, present: {sorted(view)}')
    if len(set(view.values()))!=1:errors.append(f'uneven frame counts: {dict(view)}')
    # Only WARN for repeated alpha/RGBA: character can be symmetrical, requires human inspection.
    if len(view)==8:
        count=view[0]
        sig=[tuple(bytes_ for direc,bytes_ in records if direc==d) for d in range(8)]
        for d1 in range(8):
            for d2 in range(d1+1,8):
                if sig[d1]==sig[d2]:warn.append(f'exact duplicate directions {d1}/{d2}')
    result={'ok':not errors,'errors':errors,'warnings':warn,'directions':dict(view),
            'frame_size':[width,height],'anchor':anchor,'texture_size':list(im.size)}
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('png');ap.add_argument('json');a=ap.parse_args()
    result=validate(a.png,a.json)
    print(json.dumps(result,indent=2));sys.exit(0 if result['ok'] else 1)
