"""Read actual Ground references and every referenced tile payload.
Supports 8 AND 24px native cells; does not shrink either. No engine is invoked.
Outputs study images only: never copy the reference palettes into the final pack.
"""
from pathlib import Path
from collections import Counter
import hashlib,io,json,struct
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=HERE/'audit';OUT.mkdir(exist_ok=True)

def tiles(path):
 raw=path.read_bytes();size,count=struct.unpack_from('<ii',raw);assert size in [8,24]
 bank={};cache={}
 for i in range(count):
  x,y,off=struct.unpack_from('<iiq',raw,8+i*16)
  assert off>=8+count*16
  if off not in cache:
   n,=struct.unpack_from('<q',raw,off);assert 0<n<=len(raw)-off-8
   im=Image.open(io.BytesIO(raw[off+8:off+8+n])).convert('RGBA');assert im.size==(size,size)
   cache[off]=im
  assert (x,y) not in bank;bank[x,y]=cache[off]
 return size,bank,len(cache)

def straight(im):
 a=np.array(im,dtype='uint32');alpha=a[:,:,3:4]
 a[:,:,:3]=np.minimum(255,(a[:,:,:3]*255+alpha//2)//np.maximum(alpha,1));a[alpha[:,:,0]==0]=0
 return Image.fromarray(a.astype('uint8'))

def main():
 provenance=json.loads((HERE/'references/provenance.json').read_text())
 for f in provenance:
  raw=(ROOT/f['local']).read_bytes()
  assert hashlib.sha256(raw).hexdigest()==f['sha256']
  assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==f['blob']
 report={'scope':'source reference study, not engine validation or final textures','runtime_tested':False,'maps':[]}
 for f in provenance:
  if not f['path'].endswith('.rsground'):continue
  source=ROOT/f['local'];o=json.loads(source.read_text(encoding='utf-8-sig'))['Object'];cell=o['TexSize']*8
  w,h=len(o['Layers'][0]['Tiles']),len(o['Layers'][0]['Tiles'][0]);native={};sheets=[];layers=[]
  names=sorted({frame['Sheet'] for l in o['Layers'] for col in l['Tiles'] for t in col for a in t['Layers'] for frame in a['Frames']})
  for name in names:
   entry=next(p for p in provenance if p['repo']==f['repo'] and p['path']=='Content/Tile/'+name+'.tile')
   size,bank,unique=tiles(ROOT/entry['local']);assert size==cell
   native[name]=bank
   alphas=sorted({int(v) for im in bank.values() for v in np.unique(np.array(im)[:,:,3])})
   sheets.append({'name':name,'tile_size':size,'index_entries':len(bank),'unique_png_payloads':unique,'alpha_values':alphas,'blob':entry['blob']})
  scene=Image.new('RGBA',(w*cell,h*cell))
  for i,l in enumerate(o['Layers']):
   im=Image.new('RGBA',scene.size);used=Counter();occupied=0;animated=0;frames=set()
   for x,col in enumerate(l['Tiles']):
    for y,t in enumerate(col):
     if t['Layers']:occupied+=1
     for a in t['Layers']:
      animated+=len(a['Frames'])>1;frames.add(a['FrameLength'])
      for frame in a['Frames']:
       name=frame['Sheet'];pos=frame['TexLoc'];assert (pos['X'],pos['Y']) in native[name];used[name]+=1
      frame=a['Frames'][0];pos=frame['TexLoc'];piece=straight(native[frame['Sheet']][pos['X'],pos['Y']])
      im.alpha_composite(piece,(x*cell,y*cell))
   im.save(OUT/f'{source.stem}_layer_{i}.png',optimize=True)
   if l['Visible']:scene=Image.alpha_composite(scene,im)
   layers.append({'name':l['Name'],'visible':l['Visible'],'draw_layer':l['Layer'],'occupied_cells':occupied,'animated_cells':animated,'frame_lengths':sorted(frames),'frame_references_by_sheet':dict(used)})
  scene.save(OUT/f'{source.stem}_composition.png',optimize=True)
  entity_counts={k:sum(len(e.get(k,[])) for e in o['Entities']) for k in ['MapChars','GroundObjects','Spawners','Markers']}
  walls=Counter(str(t['Tags']) for col in o['obstacles'] for t in col)
  report['maps'].append({'name':source.stem,'repo':f['repo'],'commit':f['commit'],'serialization_version':json.loads(source.read_text(encoding='utf-8-sig'))['Version'],
   'size_px':list(scene.size),'grid':[w,h],'TexSize':o['TexSize'],'tile_size':cell,'sheets':sheets,'layers':layers,
   'obstacle_tag_counts':dict(walls),'entity_counts':entity_counts,'composition':f'{source.stem}_composition.png'})
 (OUT/'references.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 print('PASS: all referenced frames resolve at original scale; source hashes verified; 3 source compositions reconstructed.')
 for m in report['maps']:print(m['name'],m['size_px'],m['tile_size'],[(l['name'],l['animated_cells']) for l in m['layers']])

if __name__=='__main__':main()
