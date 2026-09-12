"""Rebuild source-layer pixels independently from recorded native rectangles."""
from pathlib import Path
import hashlib,io,json
import numpy as np
from PIL import Image
from sample import decode
from night import night
import tile_night_reference as reference
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
WEB=ROOT/'sprites/cote_v4_abyss'

def audit():
 provenance=json.loads((HERE/'provenance.json').read_text())
 for f in provenance['files']:
  raw=(ROOT/f['local']).read_bytes()
  assert hashlib.sha256(raw).hexdigest()==f['sha256']
  assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==f['sha']
 raw=(HERE/'tile_night_reference.py').read_bytes()
 assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()=='438383f479e2d80a6a0b3be4cced4087470d9835'
 banks={k:decode(HERE/'natifs'/f'Metano_Town_{k}.tile') for k in ['Base','Cliffs','Fringe']}
 colors=np.unique(np.concatenate([a.reshape(-1,4) for a in banks.values()]),axis=0)
 swatch=Image.fromarray(colors.reshape(1,-1,4));b=io.BytesIO();swatch.save(b,format='PNG')
 assert night(swatch).tobytes()==Image.open(io.BytesIO(reference.to_night(b.getvalue()))).convert('RGBA').tobytes()
 for k,a in banks.items():
  assert np.array_equal(np.array(night(Image.fromarray(a))),decode(HERE/'natifs'/f'Metano_Town_{k}_Night.tile'))
 prep=json.loads((WEB/'preparation.json').read_text());count=0
 for z in prep['zones']:
  base=WEB/z['id'];old=ROOT/'sprites/cote_v3_0812'/z['id']
  land=np.array(Image.open(old/'TERRAIN.png'))[:,:,3]>0
  grass=np.array(Image.open(old/'00_HERBE.png'))[:,:,3]>0
  h,w=land.shape;out=[np.zeros((h,w,4),dtype='uint8') for _ in z['layers']]
  records=json.loads((base/'placements.json').read_text())
  for rec in records:
   x,y=rec['dest'];assert x%8==0 and y%8==0
   bank,(sx,sy,ex,ey)=prep['modules'][rec['module']];layer=rec['layer']
   l,t,r,b=max(x,0),max(y,0),min(x+ex-sx,w),min(y+ey-sy,h)
   src=banks[bank][sy+t-y:sy+b-y,sx+l-x:sx+r-x]
   mask=(grass if layer==0 else land&~grass)[t:b,l:r]&(src[:,:,3]==255)
   if rec['module']=='couronne':
    rgb=src.astype('int16');mask &= ~((rgb[:,:,1]>rgb[:,:,0]-10)&(rgb[:,:,1]-rgb[:,:,2]>60))
   out[layer][t:b,l:r][mask]=src[mask]
  scene=Image.new('RGBA',(w,h))
  for i,(name,a) in enumerate(zip(z['layers'],out)):
   assert np.array_equal(np.array(Image.open(base/name)),a)
   assert np.array_equal(np.array(Image.open(base/f'jour_{i:02d}.png')),a)
   assert np.array_equal(np.array(Image.open(base/f'nuit_{i:02d}.png')),np.array(night(Image.fromarray(a))))
   scene=Image.alpha_composite(scene,Image.fromarray(a))
  assert np.array_equal(np.array(scene)[:,:,3]>0,land)
  assert scene.tobytes()==Image.open(base/'TERRAIN.png').convert('RGBA').tobytes()
  assert hashlib.sha256(scene.tobytes()).hexdigest()==z['terrain_sha256']
  count+=len(records)
 for phase in range(8):
  day=Image.open(WEB/'fonds'/f'jour_mer_{phase:02d}.png').convert('RGBA')
  assert night(day).tobytes()==Image.open(WEB/'fonds'/f'nuit_mer_{phase:02d}.png').convert('RGBA').tobytes()
 return {'source_files_hash_checked':len(provenance['files']),'native_module_placements_rebuilt':count,
 'generated_terrain_rgb_pixels':0,'filter_reference_colors_checked':len(colors),
 'entire_base_cliffs_fringe_night_sheets_equal':True,'land_alpha_differences':0}
