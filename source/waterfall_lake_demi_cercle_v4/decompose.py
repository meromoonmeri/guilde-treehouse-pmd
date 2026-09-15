from pathlib import Path
import io,json,zipfile,xml.etree.ElementTree as ET
import numpy as np
from scipy import ndimage as nd
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];O=R/'renders/waterfall_lake_demi_cercle_v4';D=O/'origine_decomposee';D.mkdir(parents=True,exist_ok=True)
SOURCE='Game Boy Advance - Pokemon Mystery Dungeon_ Red Rescue Team - Friend Areas - Waterfall Lake.png';im=Image.open(R/SOURCE).convert('RGBA');a=np.array(im);H,W=a.shape[:2];yy,xx=np.mgrid[:H,:W];r,g,b=a[:,:,:3].astype(float).transpose(2,0,1)
foam=(xx>=176)&(xx<272)&(yy>=48)&(yy<81)&(r>120)&(g>180)&(b>180)
fall=(xx>=180)&(xx<268)&(yy<64)&(r<100)&(g>60)&(b>120)&~foam
island=(xx>=204)&(xx<254)&(yy>=160)&(yy<212)&(r>15)&(b<g*1.12)
blue=(r<70)&(b>120)&((b>g*1.05)|(g>150));labs,n=nd.label(blue,np.ones((3,3)));water=labs==labs[220,228];water|=((r>100)&(g>180)&(b>180)&nd.binary_dilation(water));water&=~(foam|fall|island)
land=~(water|foam|fall|island);rock=land&(yy<110)&(xx>=100)&(xx<=350)&(r>g*.9)&(b<g*.85);grass=land&~rock&(g>b*1.15)&(r>g*.38);veg=land&~rock&~grass
masks=[('01_eau_et_profondeurs',water),('02_falaise_originale_sans_eau',rock),('03_herbe_berges',grass),('04_vegetation_arriere',veg&(yy<205)),('05_vegetation_avant_gauche',veg&(yy>=205)&(xx<228)),('06_vegetation_avant_droite',veg&(yy>=205)&(xx>=228)),('07_rocher_central',island),('08_cascade_originale',fall),('09_ecume_originale',foam)]
assert np.all(np.sum([mask for _,mask in masks],axis=0)==1)
out=Image.new('RGBA',(W,H));layers=[]
for name,mask in masks:
 arr=a.copy();arr[~mask]=0;l=Image.fromarray(arr);l.save(D/f'origine_{name}.png');out.alpha_composite(l);layers.append((name,l))
assert np.array_equal(np.array(out),a);out.save(D/'COMPOSITION_ORIGINALE.png')
def png(im):
 f=io.BytesIO();im.save(f,format='PNG');return f.getvalue()
root=ET.Element('image',w=str(W),h=str(H));stack=ET.SubElement(root,'stack')
with zipfile.ZipFile(D/'waterfall_lake_originale.ora','w',zipfile.ZIP_DEFLATED) as z:
 z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
 for k,(name,l) in reversed(list(enumerate(layers))):
  fn=f'data/{k}.png';z.writestr(fn,png(l));ET.SubElement(stack,'layer',name=name,src=fn,x='0',y='0',opacity='1.0',visibility='visible',**{'composite-op':'svg:src-over'})
 z.writestr('stack.xml',ET.tostring(root));z.writestr('mergedimage.png',png(im))
# A visible projected semicircular footprint, not a claim the original cliff already spans this region.
guide=im.copy();overlay=Image.new('RGBA',im.size);draw=ImageDraw.Draw(overlay)
edge=[(16,180),(40,154),(76,128),(122,104),(170,92),(228,86),(286,92),(334,104),(380,128),(416,154),(440,180)]
poly=[(16,0),(440,0)]+list(reversed(edge));draw.polygon(poly,fill=(255,0,255,64));draw.line(edge,fill=(255,70,185,255),width=3);draw.line([(16,180),(440,180)],fill=(255,190,220,170),width=1)
overlayarr=np.array(overlay);overlayarr[fall|foam]=0;guide.alpha_composite(Image.fromarray(overlayarr));guide.save(O/'GUIDE_DEMI_CERCLE_SUR_ORIGINE.png')
# Expanded framing used by the existing approved platform scene, while original decomposition stays456x312.
expanded=Image.fromarray(np.pad(a,((16,32),(24,24),(0,0)),mode='reflect'));guide2=expanded.copy();guide2.alpha_composite(Image.fromarray(overlayarr),(24,16));guide2.save(O/'GUIDE_LAYOUT_504.png')
(O/'origine_manifest.json').write_text(json.dumps({'source':SOURCE,'size':[456,312],'layers':[n for n,_ in masks],'exact_recomposition':True,'guide':'projected new semicircle; original fall and foam excluded from the colored selection'},indent=2))
print('Original decomposed:9disjoint layers, exact recomposition; guide drawn.')
