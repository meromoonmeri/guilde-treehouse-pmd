from pathlib import Path
import sys,json,math
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];O=R/'renders/steam_cave_geysers_v1';O.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(R/'source/cote_v4_abyss'));from night import night
# Safe local utilities, no builder import with side effects.
def merge(ls):
 im=Image.new('RGBA',(648,624))
 for n,l in ls:im.alpha_composite(l)
 return im
src=Image.open(R/'Steam_Cave_Peak_TDS.png').convert('RGBA');a=np.array(src);mask=Image.new('L',src.size);d=ImageDraw.Draw(mask)
d.polygon([(280,90),(357,90),(450,210),(460,400),(414,515),(287,538),(187,417),(182,237)],fill=255);mask=np.array(mask)>0
floor=a.copy();floor[~mask]=0;wall=a.copy();wall[mask]=0;assert np.array_equal(np.array(merge([('',Image.fromarray(floor)),('',Image.fromarray(wall))])),a)
points=[(324,352,1,0),(242,228,.43,2),(411,253,.46,7),(236,389,.4,4),(419,410,.42,9)]
def vent(x,y,scale):
 im=Image.new('RGBA',src.size);d=ImageDraw.Draw(im);rx=round(27*scale);ry=max(6,round(12*scale))
 d.ellipse((x-rx,y-ry,x+rx,y+ry),fill=(75,61,48,255));d.ellipse((x-rx,y-ry-3,x+rx,y+ry-3),fill=(153,129,96,255));d.ellipse((x-rx+5,y-ry+2,x+rx-5,y+ry-6),fill=(46,49,44,255))
 for j in range(9):
  xx=round(x+(rx-2)*math.cos(j*math.tau/9));yy=round(y-2+(ry-2)*math.sin(j*math.tau/9));d.rectangle((xx-2,yy-2,xx+2,yy),fill=(192,169,130,255))
 return im
vents=[(f'03_bouche_geyser_{i}',vent(x,y,s)) for i,(x,y,s,o) in enumerate(points)]
# Hand-drawn deterministic pixel animation, fixed nozzles. Not a recovered canonical geyser sprite.
def plume(x,y,scale,phase):
 steam=Image.new('RGBA',(324,312));jet=Image.new('RGBA',src.size);d=ImageDraw.Draw(steam);j=ImageDraw.Draw(jet)
 energy=[.1,.12,.22,.5,.85,1,.95,.75,.48,.3,.17,.1][phase];height=round((18+energy*120)*scale);nozzle=max(2,round(4*scale))
 if energy>.2:
  for dy in range(height):
   age=dy/max(1,height);cx=x+round(math.sin(dy*.19+phase)*scale*1.5);width=max(1,round(nozzle*(1-age*.5)+(math.sin(dy*.61-phase)+1)*scale))
   j.line((cx-width,y-dy-4,cx+width,y-dy-4),fill=(111,184,203,235));j.point((cx+round(math.sin(dy*.5+phase)*width),y-dy-4),fill=(232,246,234,245))
  for k in range(13):
   t=(k/13+phase*.083)%1;dx=round(math.sin(k*2.4)*t*24*scale);cy=y-height+round((t*t*42-12)*scale);cx=x+dx
   j.line((cx,cy,cx,cy+max(1,round(4*scale))),fill=(218,243,229,230))
 sx=x//2;sy=y//2;hh=height//2
 for i in range(12):
  age=(i/12+phase/24)%1;cx=sx+round(math.sin(i*2.6+phase*.55)*(2+age*9)*scale);cy=sy-4-round(age*(hh+8));rad=max(2,round((3+age*9)*scale));alpha=round((85+energy*90)*(1-age*.35))
  d.ellipse((cx-rad,cy-rad,cx+rad,cy+rad),fill=(172,191,184,alpha));d.ellipse((cx-rad+1,cy-rad,cx+rad-1,cy+rad-2),fill=(229,235,219,min(235,alpha+35)))
 if energy>.35:
  for k in range(5):
   cx=sx+round(math.sin(k*2.3+phase*.25)*12*scale);cy=sy-hh-round((k%3)*5*scale);rad=max(3,round((8+(k%2)*3)*scale));alpha=round(135+energy*65)
   d.ellipse((cx-rad,cy-rad,cx+rad,cy+rad),fill=(176,195,185,alpha));d.ellipse((cx-rad+1,cy-rad,cx+rad-1,cy+rad-3),fill=(239,244,226,min(245,alpha+30)))
 return jet,steam.resize(src.size,Image.Resampling.NEAREST)
static=[('01_sol_original',Image.fromarray(floor)),('02_parois_originales',Image.fromarray(wall))]+vents
frames={};dur=[333,334,333]*4
for mode in ['jour','nuit']:
 P=O/mode;P.mkdir(exist_ok=True);frames[mode]=[]
 for p in range(12):
  ls=static.copy()
  for i,(x,y,s,offset) in enumerate(points):
   jet,steam=plume(x,y,s,(p+offset)%12);ls += [(f'04_jet_{i}',jet),(f'05_vapeur_{i}',steam)]
  if mode=='nuit':ls=[(n,night(im)) for n,im in ls]
  for n,im in ls:
   if p==0 or n.startswith(('04','05')):im.save(P/(f'steam1_{mode}_{n}_{p:02}.png' if n.startswith(('04','05')) else f'steam1_{mode}_{n}.png'))
  comp=merge(ls);comp.save(P/f'steam1_{mode}_composition_{p:02}.png');frames[mode].append(comp)
  if p==0:
   comp.save(P/'COMPOSITION.png')
   # OpenRaster of phase0.
   import io,zipfile,xml.etree.ElementTree as ET
   def png(im):
    b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
   root=ET.Element('image',w='648',h='624');stack=ET.SubElement(root,'stack')
   with zipfile.ZipFile(P/f'steam1_{mode}.ora','w',zipfile.ZIP_DEFLATED) as z:
    z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
    for k,(n,im) in reversed(list(enumerate(ls))):
     fn=f'data/{k}.png';z.writestr(fn,png(im));ET.SubElement(stack,'layer',name=n,src=fn,x='0',y='0',opacity='1.0',visibility='visible',**{'composite-op':'svg:src-over'})
    z.writestr('stack.xml',ET.tostring(root));z.writestr('mergedimage.png',png(comp))
 frames[mode][0].save(P/'ANIMATION.webp',save_all=True,append_images=frames[mode][1:],duration=dur,lossless=True,loop=0)
for f in (O/'jour').glob('steam1_jour_*.png'):
 if 'composition' not in f.name:
  counterpart=O/'nuit'/f.name.replace('_jour_','_nuit_');assert np.array_equal(np.array(Image.open(counterpart)),np.array(night(Image.open(f).convert('RGBA'))))
manifest=dict(size=[648,624],source='Steam_Cave_Peak_TDS.png',background_exact=True,geysers=[dict(x=x,y=y,scale=s,phase_offset=o) for x,y,s,o in points],frames=12,durations_ms=dur,layer_order=[n for n,im in ls],static=[n for n,im in static],animated=[n for n,im in ls if n.startswith(('04','05'))],provenance='Original Steam Cave Peak backdrop, losslessly partitioned; vent/jet/vapor authored procedurally in pixel art, not native geyser sprites.',runtime_validated=False)
(O/'manifest.json').write_text(json.dumps(manifest,indent=2));print('Steam Cave:5geysers,17layers,24scenes')
