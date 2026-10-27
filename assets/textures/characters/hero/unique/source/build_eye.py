"""Unlit gray-green / gray-hazel iris A2, explicit radial fibers, no catchlight.
512px RGBA, centered 80% diameter iris and 30% relative diameter pupil.
"""
from pathlib import Path
import numpy as np
from PIL import Image
root=Path(__file__).resolve().parents[1]
n=512;yy,xx=np.mgrid[:n,:n].astype(np.float64);xx-=255.5;yy-=255.5
r=np.sqrt(xx*xx+yy*yy)/(n*.4);theta=np.arctan2(yy,xx)
def smooth(a,b,t):
 q=np.clip((t-a)/(b-a),0,1);return q*q*(3-2*q)
base=np.zeros((n,n,3))+[112.,123.,113.]
fibers=(np.sin(theta*151+np.sin(theta*23)*2+r*13)+.45*np.sin(theta*287-r*19)+.3*np.sin(theta*71+r*41))/1.75
fiber_mask=smooth(.29,.4,r)*(1-smooth(.92,1,r))
base+=fibers[...,None]*fiber_mask[...,None]*np.array([17,20,16])
# Warm olive-brown central heterochromia is pigment, without radial light falloff.
inner=(1-smooth(.37,.51,r))*(1-smooth(.58,.68,r+.025*np.sin(theta*39)))
base=base*(1-inner[...,None])+(np.array([125,118,90])+fibers[...,None]*11)*inner[...,None]
crypt=(.5+.5*np.sin(theta*109+r*27))**12*np.exp(-((r-.42-.035*np.sin(theta*13))/.07)**2)
base-=crypt[...,None]*18
limbus=smooth(.88,.99,r);base=base*(1-limbus[...,None])+np.array([47,57,51])*limbus[...,None]
pupil=1-smooth(.294,.306,r);base=base*(1-pupil[...,None])+np.array([14,17,15])*pupil[...,None]
alpha=np.clip((1-r)*n*.4+.5,0,1)
a=np.concatenate((base,np.rint(alpha[...,None]*255)),axis=2)
Image.fromarray(np.rint(a).clip(0,255).astype(np.uint8),'RGBA').save(root/'hero_eye_iris_basecolor.png')
print('Iris: 512 RGBA, gray green, olive-brown ring, dark limbus, no painted highlight.')
