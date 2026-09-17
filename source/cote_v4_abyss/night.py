"""Exact vectorized counterpart of Abyss V4 tools/tile_night.py (438383f4).
User explicitly requested this existing color filter, not a new night palette.
"""
import numpy as np
from PIL import Image

def night(image):
 a=np.array(image.convert('RGBA'));rgb=a[:,:,:3].astype('float64')
 r,g,b=rgb[:,:,0],rgb[:,:,1],rgb[:,:,2]
 gr=.299*r+.587*g+.114*b;lum=gr/255.;k=.20+.30*lum;sat=.95
 r2=(r*sat+gr*(1-sat))*(k*.52)
 g2=(g*sat+gr*(1-sat))*(k*.70)
 b2=(b*sat+gr*(1-sat))*(k*1.60)+6*lum
 out=np.stack([r2,g2,b2],axis=2).clip(0,255).astype('uint8')
 mask=a[:,:,3]>0;a[:,:,:3][mask]=out[mask]
 return Image.fromarray(a)

def grade(image,mode):return night(image) if mode=='nuit' else image.copy()
