from pathlib import Path
import json,sys,hashlib
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'renders/donjons_generes_dtef_v3';OLD=R/'renders/donjons_dtef_v2';sys.path.insert(0,str(R/'source/cote_v4_abyss'));from night import night
m=json.loads((OLD/'manifest.json').read_text());m['themes']=m['themes'][:10];yy,xx=np.mgrid[:24,:24];weight=np.clip(np.minimum.reduce([xx-3,yy-3,20-xx,20-yy])/4,0,1);pairs=['foret_jungle','marais_roche','cristal_glace','volcan_desert','ruines_vapeur'];report=[]
for i,e in enumerate(m['themes']):
 raw=Image.open(O/'bruts'/f'{pairs[i//2]}.png').convert('RGBA');w,h=raw.size;row=i%2;donors=[np.array(raw.crop((col*w//2,row*h//2,(col+1)*w//2,(row+1)*h//2)).resize((96,96),Image.Resampling.NEAREST))[:,:,:3] for col in [0,1]];D=O/'matieres'/e['id'];D.mkdir(parents=True,exist_ok=True)
 for typ,donor in zip(['murs','sol'],donors):Image.fromarray(donor).save(D/f'{typ}.png')
 bank={};pixels=0
 for f in e['files']:
  orig=np.array(Image.open(OLD/'RAW/TileDtef'/f'd2_{e["id"]}_jour'/f).convert('RGBA'));a=orig.copy()
  if '_frame' not in f:
   for typ,donor in zip([0,2],donors):
    for slot,mask in enumerate(m['mapping']):
     if mask<0:continue
     x=(typ*6+slot%6)*24;y=slot//6*24;cell=a[y:y+24,x:x+24];seed=int(hashlib.sha256(f'{e["id"]}:{f}:{slot}:{typ}'.encode()).hexdigest()[:8],16);rng=np.random.default_rng(seed);ox,oy=rng.integers(0,73,size=2);patch=donor[oy:oy+24,ox:ox+24];mix=weight*(.30 if typ==0 else .42)*(cell[:,:,3]==255)
     cell[:,:,:3]=np.rint(cell[:,:,:3]*(1-mix[:,:,None])+patch*mix[:,:,None]).astype('uint8')
  gy,gx=np.mgrid[:192,:432];border=(gx%24<4)|(gx%24>=20)|(gy%24<4)|(gy%24>=20);assert np.array_equal(a[border],orig[border]);assert np.array_equal(a[:,:,3],orig[:,:,3]);assert np.array_equal(a[:,144:288],orig[:,144:288]);pixels+=int(np.any(a!=orig,axis=2).sum());bank[f]=Image.fromarray(a)
  if '_frame' in f:assert np.array_equal(a,orig)
 e['generated_donors']=dict(image=f'bruts/{pairs[i//2]}.png',row=row,weights=dict(wall=.30,floor=.42),protected_border_px=4);e['changed_pixels']=pixels
 def render(bank,t):
  out=Image.new('RGBA',(576,432))
  for x,y,sx,sy,v in e['demo_tiles']:
   box=(sx,sy,sx+24,sy+24);out.alpha_composite(bank[f'tileset_{v}.png'].crop(box),(x,y))
   for key,s in e['animation_layers'].items():
    av,l=map(int,key.split(':'))
    if av==v:out.alpha_composite(bank[f'tileset_{v}_frame{l}_{t//s["duration"]%s["count"]}.{s["duration"]}.png'].crop(box),(x,y))
  return out
 for mode in ['jour','nuit']:
  P=O/'RAW/TileDtef'/f'd3_{e["id"]}_{mode}';P.mkdir(parents=True,exist_ok=True);b={f:night(im) if mode=='nuit' else im for f,im in bank.items()}
  for f,im in b.items():im.save(P/f)
  A=O/'apercus'/f'd3_{e["id"]}_{mode}';A.mkdir(parents=True,exist_ok=True);render(b,0).save(A/'COMPOSITION.png');frames=[render(b,t) for t in range(0,120,6)];frames[0].save(A/'EXTRAIT_2S.webp',save_all=True,append_images=frames[1:],duration=100,loop=0,lossless=True)
  for f in e['files']:
   if mode=='nuit':assert np.array_equal(np.array(b[f]),np.array(night(bank[f])))
 report.append(dict(biome=e['id'],pngs=2*len(e['files']),modified_static_pixels=pixels,alpha_borders_secondary_preserved=True,all_native_animations_preserved=True,night_exact=True))
m['generated']=True;m['runtime_validated']=False;(O/'manifest.json').write_text(json.dumps(m,indent=2));(O/'verification.json').write_text(json.dumps(report,indent=2));print('Generated donor materials fitted to ten native DTEF sets:',sum(x['pngs'] for x in report),'PNGs')
