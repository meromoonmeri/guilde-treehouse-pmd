from pathlib import Path
import sys,io,zipfile,xml.etree.ElementTree as ET
from PIL import Image
import numpy as np
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'source/cote_v4_abyss'));from night import night
W,H=640,480
NN=Image.Resampling.NEAREST
def load(p):return Image.open(p).convert('RGBA')
def cut(a,m):
 b=a.copy();b[~m]=0;return Image.fromarray(b)
def merge(ls,size=(W,H)):
 out=Image.new('RGBA',size)
 for n,im in ls:out.alpha_composite(im)
 return out
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def ora(p,ls):
 root=ET.Element('image',w=str(W),h=str(H));stack=ET.SubElement(root,'stack')
 with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
  for i,(n,im) in reversed(list(enumerate(ls))):
   f=f'data/{i}.png';z.writestr(f,png(im));ET.SubElement(stack,'layer',name=n,src=f,x='0',y='0',opacity='1',visibility='visible',**{'composite-op':'svg:src-over'})
  z.writestr('stack.xml',ET.tostring(root));z.writestr('mergedimage.png',png(merge(ls)))
def export_static(P,prefix,ls):
 P.mkdir(parents=True,exist_ok=True)
 for n,im in ls:im.save(P/f'{prefix}_{n}.png')
 merge(ls).save(P/'COMPOSITION.png');ora(P/f'{prefix}.ora',ls)
