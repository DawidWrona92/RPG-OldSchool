#!/usr/bin/env python3
"""Original procedural pixel art demonstration. No generative image model used.
Run from anywhere: python demo/arpg/render_demo.py (Pillow only).
"""
import sys,json,random,math,os
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'retro-rts-sprites/scripts'))
from pixelcraft import Layered, stats, frame_checks,save_atlas, ramp
OUT=Path(__file__).parent/'output';OUT.mkdir(parents=True,exist_ok=True)
C={
'edge':'#171723','edge2':'#25232b',
'shadow':'#343541','steel0':'#343f48','steel1':'#61717b','steel2':'#8b9aa5','steel3':'#b6c0c6','steel4':'#ebdfc5',
'leather0':'#302423','leather1':'#704239','leather2':'#ac7650',
'red0':'#301d2d','red1':'#5c2639','red2':'#983d48','red3':'#bb6351',
'gold0':'#58412a','gold1':'#a57c44','gold2':'#e4be79',
'bone0':'#534c4c','bone1':'#998b76','bone2':'#cbb89b','bone3':'#f1dcc0',
'fire0':'#7b271d','fire1':'#d15d32','fire2':'#ffa343','fire3':'#fff0ad',
'green0':'#202c2c','green1':'#394e38','green2':'#5e7446','green3':'#9a985a',
'stone0':'#2e313a','stone1':'#4e555b','stone2':'#697371','stone3':'#9b9b88','stone4':'#bab3a1',
}

def knight(yaw=0,phase=0):
    A=Layered(96,116,(48,104));bg=A.layer('shadow')
    bg.ell((24,97,72,108),'#1c242b')
    body=A.layer('body'); d=yaw%8;side=[1,1,0,-1,-1,-1,0,1][d]
    back=d in (3,4,5);near_side= d in (0,1,6,7)
    step=[0,2,0,-2][phase];armswing=[-1,1,1,-1][phase]
    # Ground boots, planted around a constant pivot, silhouette remains centered
    body.poly([(33,70),(44,70),(44,86),(42+step,102),(31+step,102),(29+step,96)],C['edge'])
    body.poly([(52,70),(65,72),(65,96),(63-step,103),(51-step,103),(49,86)],C['edge'])
    body.poly([(33,73),(43,74),(42+step,97),(33+step,97)],C['steel0'])
    body.poly([(53,74),(63,73),(61-step,97),(51-step,97)],C['steel0'])
    for x,dx in [(33,step),(52,-step)]:
        body.line([(x+2,82),(x+10,84)],C['steel2'],2)
        body.line([(x+2+dx,96),(x+8+dx,97)],C['steel2'],2)
    body.poly([(29+step,97),(43+step,98),(42+step,105),(26+step,105)],C['edge'])
    body.poly([(52-step,98),(66-step,96),(70-step,104),(52-step,105)],C['edge'])
    body.rect((29+step,99,39+step,101),C['leather1'])
    body.rect((56-step,99,65-step,101),C['leather1'])
    # dark red asymmetrical cape with cloth folds
    cape=A.layer('cape')
    if back:
        cape.poly([(31,47),(61,46),(67,83),(77,93),(62,88),(52,97),(32,88),(22,92),(26,73)],C['edge'])
        cape.poly([(33,49),(60,48),(64,80),(70,88),(54,91),(47,88),(30,85),(29,72)],C['red1'])
        cape.poly([(37,51),(45,51),(39,80),(31,84)],C['red2'])
        cape.line([(54,54),(57,80),(53,87)],C['red0'],3)
    else:
        cape.poly([(30,49),(38,52),(33,80),(22,94),(18,85),(24,70)],C['edge'])
        cape.poly([(30,52),(34,56),(29,78),(21,89),(22,77)],C['red1'])
        cape.line([(29,60),(27,78)],C['red2'],2)
    # layered steel cuirass, dark separating seams
    torso=A.layer('armor')
    torso.poly([(33,45),(61,45),(68,57),(64,76),(31,76),(26,57)],C['edge'])
    torso.poly([(35,48),(60,48),(64,58),(61,69),(35,68),(31,59)],C['steel0'])
    torso.poly([(36,49),(58,48),(60,61),(54,65),(38,63)],C['steel1'])
    torso.poly([(37,49),(54,48),(49,52),(39,55)],C['steel3'] if not back else C['steel2'])
    torso.line([(36,58),(57,61),(60,65)],C['steel2'],2)
    torso.line([(35,67),(61,68)],C['gold0'],3)
    torso.line([(35,67),(55,68)],C['gold1'],1)
    torso.poly([(33,70),(61,70),(66,80),(50,83),(30,80)],C['edge'])
    for y in (73,77):torso.line([(34,y),(62,y+1)],C['steel2'],2)
    for x in (34,59):torso.rect((x,65,x+3,69),C['gold1'])
    # shoulder plates, dark outlines and reflective edge clusters
    hands=A.layer('arms')
    hands.ell((23,45,38,62),C['edge']);hands.ell((25,47,36,57),C['steel1']);hands.line([(27,48),(33,48)],C['steel4'],2)
    hands.ell((58,44,74,62),C['edge']);hands.ell((60,46,71,59),C['steel1']);hands.line([(62,47),(68,48)],C['steel3'],2)
    hands.poly([(24,60),(36,62),(31,80),(22,79)],C['edge']);hands.poly([(26,61),(34,64),(29,77),(25,76)],C['steel0'])
    hands.poly([(61,61),(71,59),(78,75),(68,79)],C['edge']);hands.poly([(63,63),(69,62),(74,75),(69,76)],C['steel1'])
    hands.line([(26,69),(30,72)],C['steel3'],2);hands.line([(67,68),(71,71)],C['steel4'],2)
    # helmet: asymmetric forehead and direction-dependent visor, back plate visible when rotated
    helm=A.layer('helm')
    hx=48+side*3
    helm.poly([(hx-15,26),(hx-10,18),(hx+6,17),(hx+14,25),(hx+15,42),(hx+8,47),(hx-11,46),(hx-16,40)],C['edge'])
    helm.poly([(hx-12,25),(hx-8,20),(hx+5,20),(hx+11,27),(hx+10,42),(hx-8,43),(hx-13,38)],C['steel1'])
    helm.poly([(hx-10,24),(hx-6,20),(hx+5,20),(hx+9,24),(hx+1,29)],C['steel3'])
    helm.line([(hx-9,25),(hx-4,22),(hx+5,22)],C['steel4'],2)
    if not back:
        helm.rect((hx-9,33,hx+8,38),C['edge'])
        helm.rect((hx-8+side*2,34,hx+4+side*2,35),C['gold0'])
        for x in (hx-6,hx,hx+6):helm.line([(x,35),(x+1,40)],C['steel3'])
        helm.line([(hx,26),(hx,33)],C['gold1'],2)
    else:
        helm.line([(hx-9,29),(hx-8,40)],C['steel0'],3)
        helm.line([(hx+8,30),(hx+7,41)],C['steel3'],2)
    helm.poly([(hx-3,17),(hx,10),(hx+6,13),(hx+7,17)],C['red0'])
    helm.line([(hx-1,13),(hx+3,13)],C['red3'],2)
    # Shield should change sides with yaw. Shield design has a white sun sigil.
    gear=A.layer('equipment')
    sx=20 if side>=0 else 74
    sy=67+armswing
    gear.poly([(sx-12,sy-20),(sx+12,sy-20),(sx+15,sy-1),(sx+7,sy+20),(sx,sy+26),(sx-7,sy+19),(sx-15,sy-2)],C['edge'])
    gear.poly([(sx-9,sy-16),(sx+9,sy-17),(sx+11,sy-1),(sx+4,sy+17),(sx,sy+21),(sx-4,sy+15),(sx-11,sy-2)],C['red1'])
    gear.line([(sx,sy-15),(sx,sy+14)],C['gold1'],2)
    gear.poly([(sx-5,sy-6),(sx,sy-12),(sx+5,sy-6),(sx,sy+2)],C['gold2'])
    gear.poly([(sx-4,sy+4),(sx,sy+8),(sx+4,sy+4),(sx,sy+12)],C['gold1'])
    gear.px(sx,sy-6,C['fire3'])
    # longsword on opposite hand, asymmetrical direction in each view
    ox=80 if side>=0 else 15
    angle=[-12,-20,-36,-16,3,16,30,10][d]
    shift=[0,3,1,-2][phase]
    blade=[(ox,79+shift),(ox+angle*.18,38+shift),(ox+angle*.2,23+shift)]
    gear.line(blade,C['edge'],6)
    gear.line(blade,C['steel2'],3)
    gear.line([blade[1],blade[2]],C['steel4'],1)
    gear.line([(ox-7,76+shift),(ox+7,73+shift)],C['gold2'],3)
    gear.rect((ox-2,78+shift,ox+1,89+shift),C['leather1'])
    # belt buckles and dots, native pixel clusters
    torso.px(47,69,C['gold2']); torso.px(48,69,C['gold2'])
    return A.composite()

def skeleton(yaw=0,phase=0):
    A=Layered(96,116,(48,104));p=A.layer('body');d=yaw%8;side=[1,1,0,-1,-1,-1,0,1][d]
    back=d in (3,4,5);walk=[0,2,0,-2][phase]
    p.ell((24,98,72,108),'#202729')
    p.line([(37,71),(33+walk,102)],C['bone0'],7)
    p.line([(59,71),(62-walk,101)],C['bone0'],7)
    p.line([(37,71),(33+walk,100)],C['bone2'],4)
    p.line([(59,71),(62-walk,101)],C['bone2'],4)
    p.line([(28+walk,102),(41+walk,104)],C['bone1'],4);p.line([(55-walk,102),(70-walk,104)],C['bone1'],4)
    cape=A.layer('rags')
    cape.poly([(32,46),(64,46),(67,76),(73,88),(59,82),(47,91),(35,81),(22,87),(29,70)],C['edge'])
    cape.poly([(34,48),(62,49),(62,72),(67,81),(52,84),(47,79),(35,79),(28,84)],C['green0'])
    cape.poly([(37,50),(44,51),(41,79),(32,81)],C['green1'])
    chest=A.layer('bones')
    chest.line([(47,52),(48,80)],C['bone2'],4)
    for j in range(4):
        y=55+j*6;w=14-j*1.2
        chest.line([(48-w,y),(48,y+3),(48+w,y)],C['bone1'],4)
        chest.line([(48-w+2,y-1),(48,y+2),(48+w-2,y-1)],C['bone3'],1)
    chest.poly([(43,78),(53,78),(55,85),(40,84)],C['bone0'])
    for sx in (25,70):
        chest.line([(sx,53),(sx+(-5 if sx<48 else 4),75)],C['bone0'],7)
        chest.line([(sx,54),(sx+(-5 if sx<48 else 4),75)],C['bone2'],3)
    head=A.layer('head');hx=48+side*3
    head.ell((hx-14,21,hx+14,50),C['edge']);head.ell((hx-12,23,hx+12,47),C['bone2'])
    head.poly([(hx-11,27),(hx-7,23),(hx+5,23),(hx+8,27)],C['bone3'])
    if not back:
        head.rect((hx-9,33,hx-3,37),C['green0']);head.rect((hx+3,33,hx+9,37),C['green0'])
        head.px(hx-6,35,'#c4e686');head.px(hx+6,35,'#c4e686')
        head.poly([(hx,36),(hx-3,42),(hx+3,42)],C['bone0'])
        for xx in (hx-8,hx-4,hx+2,hx+6):head.line([(xx,44),(xx+1,48)],C['edge'],1)
    else:
        head.line([(hx-8,36),(hx+9,38)],C['bone1'],2)
    gear=A.layer('scythe');ox=79 if side>=0 else 30
    # asymmetric swing projection; EACH of the eight world directions has distinct orientation
    ang=[-11,-6,0,5,10,-4,6,12][d]
    X=lambda x:x+ang
    gear.line([(ox,96),(X(ox-5),30)],C['edge'],6);gear.line([(ox,96),(X(ox-5),30)],C['leather2'],3)
    gear.poly([(X(ox-5),30),(X(ox-18),24),(X(ox-21),16),(X(ox-23),34),(X(ox-10),40)],C['edge'])
    gear.poly([(X(ox-8),31),(X(ox-18),24),(X(ox-19),20),(X(ox-18),32),(X(ox-11),36)],C['steel3'])
    return A.composite()

def crypt():
    A=Layered(184,176,(92,150));s=A.layer('ground');s.ell((22,130,164,158),'#242b2d')
    for x,y in [(12,136),(155,132),(34,150),(123,149),(160,153)]:
        s.poly([(x,y),(x+5,y-4),(x+11,y-2),(x+13,y+4),(x-2,y+4)],C['stone0'])
        s.line([(x+3,y-1),(x+9,y-2)],C['stone2'],2)
    wall=A.layer('wall')
    wall.poly([(30,70),(109,43),(152,65),(154,128),(101,157),(31,133)],C['edge'])
    wall.poly([(35,75),(108,49),(147,69),(148,123),(100,150),(35,128)],C['stone0'])
    wall.poly([(101,75),(148,66),(148,123),(101,151)],C['stone1'])
    wall.poly([(35,75),(102,50),(104,151),(35,128)],C['stone2'])
    wall.poly([(36,76),(98,54),(99,146),(36,126)],C['stone1'])
    # irregular stone coursing with breaks -- material not procedural random noise
    rng=random.Random(91)
    for y in range(80,130,8):
        wall.line([(37,y),(98,y+8)],C['stone0'],1)
        x=37+rng.randrange(-1,7)
        while x<96:
            x+=rng.randrange(10,22)
            yy=y+int((x-37)*.12)
            wall.line([(x,yy-5),(x,yy+1)],C['stone3'] if rng.random()<.17 else C['stone0'],1)
    for y in range(83,129,9):
        wall.line([(105,y+5),(145,y-1)],C['stone0'],1)
        for x in (117,136):wall.line([(x,y+4),(x,y+8)],C['stone0'],1)
    roof=A.layer('roof')
    roof.poly([(23,73),(75,28),(109,40),(151,64),(106,85),(74,55),(36,91)],C['edge'])
    roof.poly([(27,72),(75,33),(106,41),(144,63),(106,80),(75,53),(34,87)],C['stone0'])
    roof.poly([(28,72),(75,33),(105,41),(74,53),(36,84)],C['stone1'])
    roof.poly([(75,33),(106,41),(144,63),(107,78),(75,52)],C['stone2'])
    for y in (48,56,64,72):
        roof.line([(43+(y-49)*-.20,y),(92+(y-49)*.44,y+9)],C['stone0'],1)
    roof.line([(74,31),(75,52),(108,79)],C['stone4'],2)
    # facade Gothic arch, door set into dark opening
    entry=A.layer('entrance')
    entry.poly([(58,134),(58,105),(63,93),(76,80),(92,95),(96,109),(96,147),(79,152)],C['edge'])
    entry.poly([(63,132),(63,106),(76,87),(91,107),(91,143),(78,147)],C['stone3'])
    entry.poly([(68,135),(68,110),(76,94),(86,110),(86,142),(78,145)],'#191820')
    entry.poly([(72,134),(72,111),(76,100),(82,111),(82,142),(78,142)],C['leather0'])
    entry.line([(76,104),(76,140)],C['gold0'],2)
    entry.rect((79,123,82,126),C['gold2'])
    # Columns, keystone and lintel
    entry.poly([(56,94),(60,92),(62,135),(55,132)],C['stone3'])
    entry.poly([(91,94),(95,98),(97,145),(91,142)],C['stone2'])
    entry.poly([(73,83),(76,78),(80,84),(77,89)],C['stone4'])
    # gargoyles/finials and stained glass in tower niche
    detail=A.layer('ornament')
    for x,y in [(34,69),(106,38),(145,62)]:
        detail.rect((x-5,y-11,x+5,y+1),C['stone0'])
        detail.poly([(x-6,y-11),(x,y-20),(x+6,y-11)],C['stone3'])
        detail.line([(x-3,y-10),(x+4,y-10)],C['stone4'],1)
    for x,y in [(48,112),(131,95)]:
        detail.poly([(x-5,y-10),(x,y-18),(x+5,y-10),(x+5,y+11),(x-5,y+11)],C['edge'])
        detail.poly([(x-3,y-8),(x,y-14),(x+3,y-8),(x+3,y+6),(x-3,y+6)],C['fire1'])
        detail.line([(x,y-11),(x,y+5)],C['fire3'],2)
        detail.line([(x-3,y),(x+3,y)],C['edge'],1)
    # torches, orange fire halo optional distinct from shadow
    for x,y in ((36,124),(111,146)):
        detail.rect((x-2,y-5,x+2,y+4),C['gold0'])
        detail.poly([(x-2,y-6),(x-4,y-12),(x,y-19),(x+5,y-11),(x+2,y-7)],C['fire1'])
        detail.poly([(x-1,y-8),(x,y-14),(x+2,y-9)],C['fire3'])
    # fragments/moss
    for x,y in ((39,133),(49,136),(110,151),(126,141),(24,139)):
        detail.line([(x,y),(x+4,y-2)],C['green2'],2)
        detail.px(x+2,y-4,C['green3'])
    return A.composite()

def oak():
    A=Layered(142,175,(71,158));root=A.layer('roots');root.ell((27,146,119,163),'#252c2b')
    for x,y,dx in ((69,146,-21),(70,147,22),(68,149,33)):
        root.line([(x,y),(x+dx,y+5)],C['leather0'],5)
        root.line([(x+2,y-1),(x+dx//2,y+1)],C['leather2'],1)
    trunk=A.layer('trunk')
    trunk.poly([(61,150),(62,112),(53,91),(49,71),(59,75),(71,95),(83,77),(92,74),(80,99),(78,128),(81,151)],C['edge'])
    trunk.poly([(65,146),(66,110),(58,83),(66,96),(72,108),(85,82),(76,105),(74,150)],C['leather1'])
    trunk.line([(68,110),(70,143)],C['leather2'],3)
    trunk.line([(65,126),(64,144)],C['leather0'],2)
    leaves=A.layer('foliage');rng=random.Random(277)
    cluster=[(69,36,25,17),(42,51,27,21),(89,54,27,21),(74,70,32,22),(110,77,18,17),
         (29,77,19,19),(51,26,20,19),(95,26,21,19),(70,18,22,13),(42,87,21,15),(99,93,21,14)]
    pal=['#242c32','#39403b','#596044','#818053','#a6a067','#b9a66d']
    # each cluster is a separate organic lobe, not one shaded broccoli ellipsoid
    for x,y,rx,ry in cluster:
        points=[]
        for k in range(10):
            a=k*math.tau/10;rr=rng.uniform(.75,1.1)
            points.append((x+math.cos(a)*rx*rr,y+math.sin(a)*ry*rr))
        leaves.poly(points,pal[0]);leaves.poly([(px-2,py-3) for px,py in points[:5]]+[points[5],points[6]],pal[2])
        for i in range(22):
            xx=x+rng.randrange(-rx+3,rx-2);yy=y+rng.randrange(-ry+3,ry-2)
            if ((xx-x)/rx)**2+((yy-y)/ry)**2<.72:
                col=pal[rng.choice([1,2,2,3,3,4,5])]
                leaves.rect((xx,yy,xx+rng.choice([1,2,3]),yy+rng.choice([1,2])),col)
    # Dark occlusion pockets (negative space) and dangling leaves
    for x,y in ((48,59),(81,68),(68,43),(99,59),(45,89)):
        leaves.poly([(x-3,y-2),(x+2,y-5),(x+6,y),(x,y+2)],pal[0])
    for x,y in ((32,98),(57,112),(102,104),(85,117)):
        leaves.rect((x,y,x+2,y+4),pal[3])
    return A.composite()

def altar():
    A=Layered(98,113,(49,101));s=A.layer('prop');s.ell((10,94,89,107),'#202729')
    s.poly([(22,81),(48,68),(81,80),(80,93),(50,104),(19,91)],C['edge'])
    s.poly([(26,82),(49,73),(76,82),(48,91)],C['stone3'])
    s.poly([(22,83),(48,94),(48,101),(21,90)],C['stone0'])
    s.poly([(48,94),(78,83),(79,91),(48,101)],C['stone1'])
    for x,y in ((32,82),(47,86),(63,80)):
        s.line([(x,y),(x+4,y+3)],C['stone0'],1)
    s.poly([(38,76),(38,51),(49,38),(60,50),(60,76),(48,83)],C['edge'])
    s.poly([(42,72),(42,51),(49,43),(56,51),(56,72),(48,78)],C['stone1'])
    s.poly([(47,53),(49,47),(52,53),(52,68),(48,72)],C['fire1'])
    s.poly([(48,51),(50,45),(51,55),(50,65)],C['fire3'])
    s.line([(48,75),(48,91)],C['gold1'],2)
    for x,y in ((27,77),(71,76)):
        s.line([(x,y+8),(x,y-2)],C['steel2'],2)
        s.poly([(x-5,y-1),(x,y-14),(x+5,y-1)],C['fire1'])
        s.poly([(x-2,y-2),(x,y-10),(x+2,y-2)],C['fire3'])
    return A.composite()

def build_scene(images):
    W,H=1110,835
    scene=Image.new('RGB',(W,H),(22,29,32));d=ImageDraw.Draw(scene)
    rng=random.Random(217)
    for i in range(8000):
        x=rng.randrange(W);y=rng.randrange(38,H-30);shade=rng.choice(['#202f2d','#2a3630','#303b33','#232c2f'])
        d.point((x,y),fill=shade)
    for i in range(240):
        x=rng.randrange(W);y=rng.randrange(45,H-40);d.line([(x,y),(x+2,y-2)],fill='#344c37')
    def place(name,x,y,k=2):
        im=images[name];im=im.resize((im.width*k,im.height*k),Image.Resampling.NEAREST)
        scene.paste(im,(x,y),im)
    place('crypt',12,58,3);place('tree',595,53,3);place('knight',265,352,3);place('skeleton',550,358,3);place('altar',823,334,3)
    try:
        font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
        fbold=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',28)
    except OSError:
        font=ImageFont.load_default(); fbold=font
    d=ImageDraw.Draw(scene);d.rectangle([0,0,W,48],fill='#15191f')
    d.text((28,8),'RETRO DARK FANTASY  •  GODOT / 2D PIXEL-ART',font=fbold,fill='#d9c8a8')
    d.text((35,755),'Krypta  |  korona drzewa  |  rycerz  |  szkielet  |  ołtarz',font=font,fill='#dfd1b9')
    d.text((35,787),'Wszystkie piksele rysowane kodem Pillow w natywnej rozdzielczości 1×',font=font,fill='#98a9a5')
    scene.save(OUT/'pixelart_showcase.png')

def build():
    frames=[knight(d,p) for d in range(8) for p in range(4)]
    anchors=[(48,104)]*len(frames)
    check=frame_checks(frames,anchors,8,4)
    assert check['ok'],check
    meta=save_atlas(str(OUT/'dark_knight_walk_8dir.png'),frames,(48,104),8,4)
    meta['animation']='walk';meta['duration_ms']=110
    with open(OUT/'dark_knight_walk_8dir.json','w') as f:json.dump(meta,f,indent=2)
    sframes=[skeleton(d,p) for d in range(8) for p in range(4)]
    schk=frame_checks(sframes,anchors,8,4)
    assert schk['ok'],schk
    save_atlas(str(OUT/'skeleton_walk_8dir.png'),sframes,(48,104),8,4)
    images={'knight':frames[0],'skeleton':sframes[0],'crypt':crypt(),'tree':oak(),'altar':altar()}
    for k,img in images.items():img.save(OUT/(k+'.png'))
    build_scene(images)
    (OUT/'validation.json').write_text(json.dumps({'knight':check,'skeleton':schk,'sprites':{k:stats(im) for k,im in images.items()}},indent=2))
    print('Output:',OUT)
    print('knight:',check)
    print('skeleton:',schk)
    print('styles:',[(k,stats(im)['colors']) for k,im in images.items()])
if __name__=='__main__':build()
