"""Build a coarse wagon OBJ and a diagnostic orthographic PNG. Requires Pillow.

Coordinates are provisional metres: X = length, Y = width, Z = height.
Run: python build.py
"""
from math import cos, sin, pi, sqrt
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
vertices, faces = [], []

def box(center, size, color, angle=0):
    x,y,z = center; a,b,c = (v/2 for v in size)
    base = len(vertices)
    for dx,dy,dz in [(-a,-b,-c),(a,-b,-c),(a,b,-c),(-a,b,-c),(-a,-b,c),(a,-b,c),(a,b,c),(-a,b,c)]:
        vertices.append((x+dx*cos(angle)+dz*sin(angle), y+dy, z-dx*sin(angle)+dz*cos(angle)))
    for f in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:
        faces.append(([base+i for i in f],color))

wood=(107,76,50); dark=(70,49,34); iron=(63,65,62)
# Frame, floorboards, removable walls, axles, and tongue.
for x in (-.9,.9): box((x,0,.76),(.12,1.85,.13),dark)
for y in (-.58,.58): box((0,y,.82),(2.9,.14,.14),dark)
for i in range(8): box((0,-.7+i*.2,.94),(2.65,.19,.08),wood)
for y in (-.76,.76):
    for z in (1.08,1.29,1.50): box((0,y,z),(2.75,.08,.18),wood)
    for x in (-1.20,1.20): box((x,y,1.30),(.12,.14,.72),dark)
for x in (-1.36,1.36):
    for z in (1.08,1.29,1.50): box((x,0,z),(.08,1.50,.18),wood)
for x in (-.9,.9): box((x,0,.57),(.13,2.07,.13),iron)
for y in (-.35,.35): box((2.08,y,.64),(1.55,.09,.10),dark)
# Wheel polygons are explicitly separate spoke and rim pieces, not a production mesh.
for x in (-.9,.9):
 for y in (-.94,.94):
    for k in range(12):
        t=2*pi*k/12
        box((x+.48*cos(t),y,.57+.48*sin(t)),(.255,.12,.12),dark,-t-pi/2)
        box((x+.24*cos(t),y,.57+.24*sin(t)),(.48,.08,.065),wood,-t)
    box((x,y,.57),(.22,.20,.22),iron)

with (ROOT/'wagon-blockout.obj').open('w',encoding='utf-8') as out:
    out.write('# Welesza wagon blockout, provisional dimensions in metres\n')
    for v in vertices: out.write('v %.5f %.5f %.5f\n'%v)
    for f,_ in faces: out.write('f '+' '.join(str(i+1) for i in f)+'\n')

# A painter-sorted diagnostic only; no shadows or material realism.
im=Image.new('RGB',(1000,700),(220,219,211)); d=ImageDraw.Draw(im)
def project(v):
    x,y,z=v
    return (500+155*(x-y)*.707, 490-155*z+155*(x+y)*.36)
ordered=sorted(faces,key=lambda item: sum(vertices[i][0]+vertices[i][1]+vertices[i][2]*.15 for i in item[0])/len(item[0]))
for inds,color in ordered:
    d.polygon([project(vertices[i]) for i in inds],fill=color,outline=(45,38,32),width=1)
d.text((20,20),'WAGON BLOCKOUT - diagnostic, not final art',fill=(25,25,25))
im.save(ROOT/'wagon-blockout.png')
print(f'{len(vertices)} vertices, {len(faces)} faces; OBJ and preview generated')
