"""Native-material calibration only. Does not replace the delivered PMDO pack.
8px source cells, no resampling, no generated RGB, no color grading.
Approved land/grass alpha masks guide placement; clipped cells are recorded.
"""
from pathlib import Path
import io,json,struct,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OUT=ROOT/'sprites/cote_v4_abyss_echantillon'
SLUG='07_balcon_haut'

def decode(path):
 raw=path.read_bytes();size,n=struct.unpack_from('<ii',raw);assert size==8
 records=[struct.unpack_from('<iiq',raw,8+i*16) for i in range(n)]
 out=Image.new('RGBA',((max(x for x,y,a in records)+1)*8,(max(y for x,y,a in records)+1)*8));cache={}
 for x,y,a in records:
  if a not in cache:
   k,=struct.unpack_from('<q',raw,a);cache[a]=Image.open(io.BytesIO(raw[a+8:a+8+k])).convert('RGBA')
  out.paste(cache[a],(x*8,y*8))
 return np.array(out)

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 old=ROOT/'sprites/cote_v3_0812'/SLUG
 land=np.array(Image.open(old/'TERRAIN.png'))[:,:,3]>0
 grass=np.array(Image.open(old/'00_HERBE.png'))[:,:,3]>0
 rock=land&~grass;h,w=land.shape
 layers=['00_HERBE_NATIVE','01_FACE_NATIVE','02_COURONNE_NATIVE','03_PIED_NATIF']
 sources={mode:{k:decode(HERE/'natifs'/f'Metano_Town_{k}{suffix}.tile') for k in ['Base','Cliffs']} for mode,suffix in [('jour',''),('nuit','_Night')]}
 records=[];variants={}
 for mode in sources:
  result=[np.zeros((h,w,4),dtype='uint8') for _ in layers]
  def cell(layer,x,y,bank,sx,sy,mask):
   src=sources[mode][bank][sy:sy+8,sx:sx+8]
   assert src.shape==(8,8,4)
   selected=mask&(src[:,:,3]==255)
   result[layer][y:y+8,x:x+8][selected]=src[selected]
   if mode=='jour' and selected.any():records.append({'layer':layer,'dest':[x,y],'bank':bank,'source':[sx,sy],'mask':np.packbits(selected).tobytes().hex()})
  for x in range(0,w,8):
   rows=np.flatnonzero(rock[:,x:x+8].any(axis=1))
   groups=np.split(rows,np.flatnonzero(np.diff(rows)>8)+1) if len(rows) else []
   runs=[(int(g[0])//8*8,int(g[-1])//8*8+8) for g in groups]
   for y in range(0,h,8):
    gm=grass[y:y+8,x:x+8];rm=rock[y:y+8,x:x+8]
    top,bottom=min(runs,key=lambda r:max(r[0]-y,y+8-r[1],0)) if runs else (h,h)
    cell(0,x,y,'Base',x%128,640+y%128,gm)
    cell(1,x,y,'Cliffs',912+x%64,464+y%48,rm)
    if 0<=y-top<16:cell(2,x,y,'Cliffs',912+x%64,448+y-top,rm)
    if bottom<h and 0<=bottom-y-8<16:cell(3,x,y,'Cliffs',912+x%64,544-(bottom-y),rm)
  composite=Image.new('RGBA',(w,h))
  for name,a in zip(layers,result):
   im=Image.fromarray(a);im.save(OUT/f'{mode}_{name}.png',optimize=True);composite=Image.alpha_composite(composite,im)
  assert np.array_equal(np.array(composite)[:,:,3]>0,land)
  composite.save(OUT/f'{mode}_TERRAIN.png',optimize=True);variants[mode]=composite
 # Verify every placed opaque pixel against the actual day/night bank at the same coordinate.
 for mode in sources:
  # Layer reload is done once, not once per cell.
  arrays=[np.array(Image.open(OUT/f'{mode}_{name}.png')) for name in layers]
  for rec in records:
   x,y=rec['dest'];sx,sy=rec['source'];mask=np.unpackbits(np.frombuffer(bytes.fromhex(rec['mask']),dtype='uint8')).reshape(8,8).astype(bool)
   assert np.array_equal(arrays[rec['layer']][y:y+8,x:x+8][mask],sources[mode][rec['bank']][sy:sy+8,sx:sx+8][mask])
 (OUT/'placements.json').write_text(json.dumps(records,separators=(',',':')))
 report={'scope':'one material calibration sample, NOT a completed corrected pack','zone':SLUG,'size':[w,h],
  'native_day_and_night_pixels_verified':True,'generated_color_pixels':0,'resampling':False,'generated_shadows':False,
  'land_mask_differences':0,'contacts':{k:int(v.sum()) for k,v in [('W',land[:,0]),('E',land[:,-1]),('S',land[-1])]},
  'limitations':['Native cap/foot module junctions still need artistic validation','Lateral returns not yet reconstructed','No PMDO map/runtime test for this sample'],
  'sources':json.loads((HERE/'provenance.json').read_text())}
 (OUT/'verification.json').write_text(json.dumps(report,indent=2))
 # Exact 1x terrain side by side. No image resizing in this deliverable.
 board=Image.new('RGB',(w*2, h+68),'#152333');d=ImageDraw.Draw(board)
 d.text((16,12),'ECHANTILLON - Haut balcon / JOUR NATIF',fill='white')
 d.text((w+16,12),'NUIT - tuiles Abyss to Ascension V4',fill='white')
 for i,mode in enumerate(['jour','nuit']):board.paste(variants[mode],(i*w,48),variants[mode])
 board.save(OUT/'COMPARATIF_NATIF_1X.png',optimize=True)
 # Source crops at 4x, explicitly a reference chart, not import assets.
 chart=Image.new('RGB',(1024,768),'#152333');d=ImageDraw.Draw(chart)
 for i,mode in enumerate(['jour','nuit']):
  d.text((i*512+12,12),mode.upper()+' - REFERENCES UNIQUEMENT (4x)',fill='white')
  g=Image.fromarray(sources[mode]['Base'][640:704,0:128]);c=Image.fromarray(sources[mode]['Cliffs'][432:544,912:976])
  chart.paste(g.resize((512,256),Image.Resampling.NEAREST),(i*512,40))
  chart.paste(c.resize((256,448),Image.Resampling.NEAREST),(i*512,312))
 chart.save(OUT/'REFERENCES_4X_NE_PAS_IMPORTER.png')
 print('PASS: native day/night sample; exact source pixels, unchanged alpha and edge contacts.')

if __name__=='__main__':main()
