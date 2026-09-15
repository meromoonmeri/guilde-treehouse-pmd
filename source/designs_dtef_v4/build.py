from pathlib import Path
import sys,json,re,hashlib
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'renders/designs_dtef_v4';OLD=R/'renders/donjons_dtef_v2';sys.path.insert(0,str(R/'source/cote_v4_abyss'));from night import night
m0=json.loads((OLD/'manifest.json').read_text());mapping=m0['mapping'];themes=[];report=[]
settings=[('ruines','ruines','ruines_chateau',0),('chateau','ruines','ruines_chateau',1),('glace','glace','glace_foret_sombre',0),('foret_sombre','marais','glace_foret_sombre',1)]
yy,xx=np.mgrid[:24,:24];inside=(xx>=4)&(xx<20)&(yy>=4)&(yy<20)
for name,parent,pair,row in settings:
 src=next(e for e in m0['themes'] if e['id']==parent);raw=Image.open(O/'bruts'/f'{pair}.png').convert('RGBA');w,h=raw.size;donors=[np.array(raw.crop((c*w//2,row*h//2,(c+1)*w//2,(row+1)*h//2)).resize((96,96),Image.Resampling.NEAREST))[:,:,:3] for c in [0,1]];P=O/'matieres'/name;P.mkdir(parents=True,exist_ok=True)
 for typ,donor in zip(['mur','sol'],donors):Image.fromarray(donor).save(P/f'{typ}.png')
 source=OLD/'RAW/TileDtef'/f'd2_{parent}_jour';base=np.array(Image.open(source/'tileset_0.png').convert('RGBA'));bank={}
 for v in range(3):
  a=base.copy()
  for typ,donor in zip([0,2],donors):
   for slot,mask in enumerate(mapping):
    if mask<0:continue
    x=(typ*6+slot%6)*24;y=slot//6*24;cell=a[y:y+24,x:x+24];native=base[y:y+24,x:x+24];patch=donor[:24,:24].copy();alt=donor[(v*24):(v*24+24),24:48];patch[inside]=alt[inside]
    # Coherent original texture detail + native volume shading, not a recolored original tile.
    lum=native[:,:,:3]@np.array([.2126,.7152,.0722]);shading=np.clip((lum-100)/600,-.12,.12);rgb=np.clip(patch.astype(float)*(1+shading[:,:,None]),0,255).astype('uint8');cell[:,:,:3]=rgb;cell[cell[:,:,3]==0]=0
  bank[f'tileset_{v}.png']=Image.fromarray(a)
 # Native Secondary and its animations are copied to all3 variants so none becomes a frozen-water variant.
 spec={}
 for key,s in src['animation_layers'].items():
  av,layer=map(int,key.split(':'))
  if av!=0:continue
  for v in range(3):
   spec[f'{v}:{layer}']=s
   for fi in range(s['count']):bank[f'tileset_{v}_frame{layer}_{fi}.{s["duration"]}.png']=Image.open(source/f'tileset_0_frame{layer}_{fi}.{s["duration"]}.png').convert('RGBA')
 e={**src,'id':name,'source_geometry':src['source'],'files':list(bank),'animation_layers':spec,'design_generated':True,'demo_tiles':src['demo_tiles']};themes.append(e)
 def render(b,t):
  out=Image.new('RGBA',(576,432))
  for x,y,sx,sy,v in e['demo_tiles']:
   v=(x//24*7+y//24*13)%3;box=(sx,sy,sx+24,sy+24);out.alpha_composite(b[f'tileset_{v}.png'].crop(box),(x,y))
   for key,s in spec.items():
    av,l=map(int,key.split(':'))
    if av==v:out.alpha_composite(b[f'tileset_{v}_frame{l}_{t//s["duration"]%s["count"]}.{s["duration"]}.png'].crop(box),(x,y))
  return out
 for mode in ['jour','nuit']:
  D=O/'RAW/TileDtef'/f'd4_{name}_{mode}';D.mkdir(parents=True,exist_ok=True);b={f:night(im) if mode=='nuit' else im for f,im in bank.items()}
  for f,im in b.items():im.save(D/f)
  A=O/'apercus'/f'd4_{name}_{mode}';A.mkdir(parents=True,exist_ok=True);render(b,0).save(A/'COMPOSITION.png');frames=[render(b,t) for t in range(0,120,6)];frames[0].save(A/'EXTRAIT_2S.webp',save_all=True,append_images=frames[1:],duration=100,loop=0,lossless=True)
 for v in range(3):assert np.array_equal(np.array(bank[f'tileset_{v}.png'])[:,:,3],base[:,:,3])
 report.append(dict(theme=name,alpha_from_native_geometry=True,three_full_variants=True,own_generated_wall_and_floor=True,pngs=2*len(bank)))
(O/'manifest.json').write_text(json.dumps(dict(mapping=mapping,themes=themes,tile_px=24,runtime_validated=False),indent=2));(O/'verification_build.json').write_text(json.dumps(report,indent=2));print('Four new DTEF designs built')
