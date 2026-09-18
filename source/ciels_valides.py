"""Ciels et six familles de nuages validés, c16efe12. Aucun resampling.
Reprise explicite du placement de source/cote_dix_zones/build.py.
"""
from pathlib import Path
import hashlib
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
REF=ROOT/'source/cote_dix_zones/reference_autre_agent'
CROPS=[(16,24,168,72),(176,8,272,72),(272,16,368,64),(72,80,168,128),(176,72,296,128),(320,64,472,128)]
DESTS=[(32,40),(272,16),(504,72),(728,32),(920,80),(1160,24)]
def load(name):return Image.open(REF/f'source__falaise__{name}.png').convert('RGBA')
def grade_clouds(im,mode):
 if mode=='jour':return im.copy()
 a=np.array(im);v=a[:,:,:3].astype(float);lum=(v@np.array([.2126,.7152,.0722]))[:,:,None]
 a[:,:,:3]=np.rint((lum*.20+v*.80)*np.array([.40,.42,.58])+[4,8,15]).clip(0,255).astype('uint8');a[a[:,:,3]==0]=0
 return Image.fromarray(a)
def sky(size,mode):
 w,h=size;a=np.array(load('ciel_'+mode+'_native'));xs=np.arange(w)%480;xs=np.where(xs<240,xs,479-xs)
 return Image.fromarray(a[np.minimum(np.arange(h),a.shape[0]-1)[:,None],xs[None,:]])
def clouds(mode):
 source=load('nuages_native');strip=Image.new('RGBA',(1440,208));rebuilt=Image.new('RGBA',source.size)
 for rect,dest in zip(CROPS,DESTS):
  strip.paste(source.crop(rect),dest);rebuilt.paste(source.crop(rect),rect[:2])
 assert rebuilt.tobytes()==source.tobytes()
 return grade_clouds(strip,mode)
def wrap(strip,size,offset=0):
 out=Image.new('RGBA',size)
 for x in range(-(int(offset)%strip.width),size[0],strip.width):out.paste(strip,(x,0))
 return out

def stars(size,mode,moon=False):
 out=Image.new('RGBA',size)
 if mode=='jour':return out
 src=load('astres_nuit_native');w,h=size
 edge=w-480 if moon and w>=480 else w
 for x in range(0,edge,240):out.paste(src.crop((0,0,min(240,edge-x),184)),(x,0))
 if moon and w>=480:out.paste(src,(w-480,0))
 return out

def provenance():
 return {'reference_commit':'c16efe12d74361df5ba8625abb68260f5f8fc6dd','method':'Ciel : répétition réfléchie de la moitié gauche sans lune cuite, lignes terminales prolongées. Nuages : six blocs natifs déplacés entiers, sans resampling. Nuit nuages : formule Guilde/Sharpedo, pas Abyss.','cloud_crops':CROPS,'cloud_destinations':DESTS,'cloud_strip_size':[1440,208],'cloud_speed_px_s':-4,'cloud_loop_s':360,'sources':[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(REF.glob('source__falaise__*.png'))]}
