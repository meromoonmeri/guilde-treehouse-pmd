"""Ten approved organic shapes reconstructed with native Metano material modules.
No generated RGB, no old generated lighting. Preserve exact land alpha masks.
Faces use coherent 64x48 slabs; returns, crowns and feet are distinct modules.
All translations are on the 8px grid. Native pixels are clipped, never warped.
"""
from pathlib import Path
import hashlib,json,io
import numpy as np
from PIL import Image
from sample import decode
from night import night
import tile_night_reference as reference
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=ROOT/'sprites/cote_v4_abyss'
NAMES=['00_HERBE_NATIVE.png','01_FACES_NATIVE.png','02_RETOURS_NATIVE.png','03_COURONNES_NATIVE.png','04_PIEDS_NATIVE.png']
MODULES={'herbe':('Base',(0,640,128,768)), 'face':('Cliffs',(912,464,976,512)),
 'retour':('Cliffs',(680,464,744,512)), 'couronne':('Cliffs',(912,448,976,464)),
 'pied':('Cliffs',(912,528,976,544))}

def runs(row,gap=0):
 ids=np.flatnonzero(row)
 if not len(ids):return []
 return [(int(g[0]),int(g[-1])+1) for g in np.split(ids,np.flatnonzero(np.diff(ids)>gap+1)+1)]

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 sheets={name:decode(HERE/'natifs'/f'Metano_Town_{name}.tile') for name in ['Base','Cliffs','Fringe']}
 # Compare our vectorization to the actual reference function on every source color.
 colors=np.unique(np.concatenate([v.reshape(-1,4) for v in sheets.values()]),axis=0)
 swatch=Image.fromarray(colors.reshape(1,-1,4));buf=io.BytesIO();swatch.save(buf,format='PNG')
 expected=Image.open(io.BytesIO(reference.to_night(buf.getvalue()))).convert('RGBA')
 assert night(swatch).tobytes()==expected.tobytes()
 for name,day in sheets.items():
  actual=decode(HERE/'natifs'/f'Metano_Town_{name}_Night.tile')
  assert np.array_equal(np.array(night(Image.fromarray(day))),actual),name
 prep=json.loads((ROOT/'sprites/cote_v3_0812/preparation.json').read_text())
 report={'target_pmdo':'0.8.12','filter_source_blob':'438383f479e2d80a6a0b3be4cced4087470d9835',
 'filter_source_colors_checked':len(colors),'existing_three_night_sheets_exact':True,'generated_rgb_pixels':0,
 'modules':MODULES,'rock_source':prep['rock_source'],'runtime_tested':False,'zones':[]}
 for rec in prep['zones']:
  slug=rec['id'];old=ROOT/'sprites/cote_v3_0812'/slug;dest=OUT/slug;dest.mkdir(exist_ok=True)
  original=np.array(Image.open(old/'TERRAIN.png'));land=original[:,:,3]>0
  grass=np.array(Image.open(old/'00_HERBE.png'))[:,:,3]>0
  rock=land&~grass;h,w=land.shape;arrays=[np.zeros((h,w,4),dtype='uint8') for _ in NAMES];placements=[]
  def stamp(layer,module,x,y,mask):
   assert x%8==0 and y%8==0
   bank,rect=MODULES[module];sx,sy,ex,ey=rect;mw,mh=ex-sx,ey-sy
   left,top=max(0,x),max(0,y);right,bottom=min(w,x+mw),min(h,y+mh)
   if right<=left or bottom<=top:return
   source=sheets[bank][sy+top-y:sy+bottom-y,sx+left-x:sx+right-x]
   selected=mask[top:bottom,left:right]&(source[:,:,3]==255)
   if module=='couronne':
    c=source.astype('int16');selected &= ~((c[:,:,1]>c[:,:,0]-10)&(c[:,:,1]-c[:,:,2]>60))
   if not selected.any():return
   arrays[layer][top:bottom,left:right][selected]=source[selected]
   placements.append({'layer':layer,'module':module,'dest':[x,y]})
  for y in range(0,h,128):
   for x in range(0,w,128):stamp(0,'herbe',x,y,grass)
  for y in range(0,h,48):
   for x in range(0,w,64):stamp(1,'face',x,y,rock)
  # Edge returns follow actual horizontal cliff spans, not artificial periodic pillars.
  # Each return is a whole 64x48 source slab; no per-cell texture scrambling.
  for y in range(0,h,48):
   row=rock[y:min(h,y+48)].mean(axis=0)>.55
   for left,right in runs(row,gap=8):
    if right-left<40:continue
    xs=[left//8*8]
    if right-left>=160:xs.append((right-64)//8*8)
    for x in xs:stamp(2,'retour',x,y,rock)
  # Surface profiles detect each terrace independently. Caps/feet remain contiguous
  # native strips; their overlap is clipped by the approved rock mask.
  for x in range(0,w,32):
   col=rock[:,x:min(w,x+32)].mean(axis=1)>.4
   for top,bottom in runs(col,gap=8):
    if bottom-top<24:continue
    cap_y=top//8*8
    stamp(3,'couronne',x,cap_y,rock)
    if bottom<h:stamp(4,'pied',x,(bottom//8)*8-16,rock)
  scene=Image.new('RGBA',(w,h))
  for name,a in zip(NAMES,arrays):
   im=Image.fromarray(a);im.save(dest/name,optimize=True);scene=Image.alpha_composite(scene,im)
  assert np.array_equal(np.array(scene)[:,:,3],original[:,:,3]),slug
  scene.save(dest/'TERRAIN.png',optimize=True)
  # Reconstruct all layers solely from source rectangles and the original masks.
  rebuilt=[np.zeros_like(a) for a in arrays]
  for p in placements:
   layer=p['layer'];bank,(sx,sy,ex,ey)=MODULES[p['module']];x,y=p['dest']
   l,t,r,b=max(0,x),max(0,y),min(w,x+ex-sx),min(h,y+ey-sy)
   src=sheets[bank][sy+t-y:sy+b-y,sx+l-x:sx+r-x]
   select=(grass if layer==0 else rock)[t:b,l:r]&(src[:,:,3]==255)
   if p['module']=='couronne':
    c=src.astype('int16');select &= ~((c[:,:,1]>c[:,:,0]-10)&(c[:,:,1]-c[:,:,2]>60))
   rebuilt[layer][t:b,l:r][select]=src[select]
  assert all(np.array_equal(a,b) for a,b in zip(arrays,rebuilt))
  (dest/'placements.json').write_text(json.dumps(placements,separators=(',',':')))
  report['zones'].append({**rec,'layers':NAMES,'shape_differences_after_crop':0,'generated_rgb_pixels':0,
   'native_module_placements':len(placements),'edge_contact_pixels':{k:int(v.sum()) for k,v in [('W',land[:,0]),('E',land[:,-1]),('S',land[-1])]},
   'terrain_sha256':hashlib.sha256(scene.tobytes()).hexdigest()})
  print('PASS',slug,'native modules',len(placements),flush=True)
 Image.fromarray(sheets['Cliffs'][464:512,912:976]).save(OUT/'METANO_ROCHE_NATIVE_64x48.png')
 (OUT/'preparation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 print('Filter identical to Abyss reference and all three complete night sheets; 10 native terrains.')

if __name__=='__main__':main()
