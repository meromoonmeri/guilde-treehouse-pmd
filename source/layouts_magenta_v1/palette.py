import colorsys
import numpy as np
from PIL import Image
from scipy import ndimage as nd

def key(im):
 a=np.array(im);r,g,b=a[:,:,:3].astype(float).transpose(2,0,1);bg=(r>70)&(b>70)&(r>g*1.45)&(b>g*1.45)
 fringe=nd.binary_dilation(bg,iterations=1)&(r>g*1.05)&(b>g*1.05)
 a[bg|fringe]=0;return Image.fromarray(a)

def tint(im,biome,palette):
 a=np.array(im);rgb=a[:,:,:3];colors,inv=np.unique(rgb.reshape(-1,3),axis=0,return_inverse=True);result=[]
 for r,g,b in colors:
  h,s,v=colorsys.rgb_to_hsv(r/255,g/255,b/255);blue=b>r*1.12 and b>g*.87;green=g>r*1.06 and g>b*1.12
  if biome=='cote':
   h=(.60 if palette==0 else .49) if blue else (.95 if palette==0 else .09);s*=.8 if blue else .68;v*=1 if palette==0 else 1.03
  elif biome=='cristal':h=.52 if palette==0 else .65;s*=.85 if palette==0 else .62;v*=1 if palette==0 else .98
  elif biome=='foret':
   if green:h=(h-.016)%1 if palette==0 else .365;s*=.93 if palette==0 else .82
   else:h=(h+.008)%1 if palette==0 else (h-.012)%1;s*=.9
  else:
   h=(h+.006)%1 if palette==0 else .055;s*=.93 if palette==0 else .6;v*=1 if palette==0 else .98
  result.append([round(x*255) for x in colorsys.hsv_to_rgb(h,min(1,s),min(1,v))])
 a[:,:,:3]=np.array(result,dtype='uint8')[inv].reshape(rgb.shape);a[a[:,:,3]==0]=0;return Image.fromarray(a)
