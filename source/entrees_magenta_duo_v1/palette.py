import colorsys
import numpy as np
from PIL import Image
from scipy import ndimage as nd

def key(im):
    """Extraction magenta #FF00FF -> alpha. Copie palette.py layouts_magenta_v1, sans changer le seuil."""
    a=np.array(im.convert('RGBA'))
    r,g,b=a[:,:,:3].astype(float).transpose(2,0,1)
    bg=(r>70)&(b>70)&(r>g*1.45)&(b>g*1.45)
    fringe=nd.binary_dilation(bg,iterations=1)&(r>g*1.05)&(b>g*1.05)
    a[bg|fringe]=0
    return Image.fromarray(a)

def tint(im, biome, palette_idx):
    """Deux palettes cohérentes par biome, hue cohérente, sans recoloration sauvage."""
    a=np.array(im.convert('RGBA'))
    rgb=a[:,:,:3]
    # unique colors
    flat=rgb.reshape(-1,3)
    # fast path if small image: use unique
    colors, inv = np.unique(flat, axis=0, return_inverse=True)
    result=[]
    for r,g,b in colors:
        if r==0 and g==0 and b==0:
            result.append([0,0,0]); continue
        h,s,v=colorsys.rgb_to_hsv(r/255,g/255,b/255)
        blue=b>r*1.12 and b>g*.87
        green=g>r*1.06 and g>b*1.12
        red=r>g*1.08 and r>b*1.08
        if biome=='foret':
            if green:
                h=(h-0.016)%1 if palette_idx==0 else 0.365
                s*=0.93 if palette_idx==0 else 0.82
            else:
                h=(h+0.008)%1 if palette_idx==0 else (h-0.012)%1
                s*=0.9
        elif biome=='volcan':
            # chaud : rouge/orange vs sombre
            if red or (r>150 and g>80 and b<70):
                h=0.04 if palette_idx==0 else 0.08
                s*=0.88 if palette_idx==0 else 0.72
                v*=1.02 if palette_idx==0 else 0.96
            else:
                h=(h+0.01)%1 if palette_idx==0 else (h-0.015)%1
                s*=0.85
        elif biome=='vapeur':
            if blue:
                h=0.60 if palette_idx==0 else 0.52
                s*=0.78 if palette_idx==0 else 0.62
                v*=1.0 if palette_idx==0 else 1.03
            elif green:
                h=0.38 if palette_idx==0 else 0.42
                s*=0.75
            else:
                h=(h+0.005)%1 if palette_idx==0 else (h-0.008)%1
        else:
            h=(h+0.006)%1 if palette_idx==0 else 0.055
        r2,g2,b2=colorsys.hsv_to_rgb(h%1,min(1,s),min(1,v))
        result.append([round(r2*255),round(g2*255),round(b2*255)])
    a[:,:,:3]=np.array(result,dtype='uint8')[inv].reshape(rgb.shape)
    a[a[:,:,3]==0]=0
    return Image.fromarray(a)
