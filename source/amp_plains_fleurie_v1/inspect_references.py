from pathlib import Path
import json,struct,io,math
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;REF=HERE/'references'
def decode(path):
 raw=path.read_bytes();size,count=struct.unpack_from('<ii',raw);bank={}
 for i in range(count):
  x,y,off=struct.unpack_from('<iiq',raw,8+i*16);length,=struct.unpack_from('<q',raw,off);im=Image.open(io.BytesIO(raw[off+8:off+8+length])).convert('RGBA');a=np.array(im,dtype='uint32');al=a[:,:,3:4];a[:,:,:3]=np.minimum(255,(a[:,:,:3]*255+al//2)//np.maximum(al,1));a[al[:,:,0]==0]=0;bank[x,y]=Image.fromarray(a.astype('uint8'))
 return size,bank
if __name__=='__main__':
 banks={}
 for p in REF.glob('*.tile'):
  size,bank=decode(p);banks[p.stem]=bank;w=(max(x for x,y in bank)+1)*size;h=(max(y for x,y in bank)+1)*size;im=Image.new('RGBA',(w,h))
  for (x,y),tile in bank.items():im.alpha_composite(tile,(x*size,y*size))
  im.save(REF/(p.stem+'.png'));print(p.stem,size,(w,h))
 obj=json.loads((REF/'vast_steppe_entrance.rsground').read_text(encoding='utf-8-sig'))['Object'];S=(512,512);scene=Image.new('RGBA',S);animated=[]
 for li,layer in enumerate(obj['Layers']):
  im=Image.new('RGBA',S)
  for x,col in enumerate(layer['Tiles']):
   for y,tile in enumerate(col):
    for sub in tile['Layers']:
     f=sub['Frames'][0];loc=f['TexLoc'];im.alpha_composite(banks[f['Sheet']][loc['X'],loc['Y']],(x*8,y*8))
     if len(sub['Frames'])>1:animated.append({'layer':li,'cell':[x,y],'frames':sub['Frames'],'duration_game_frames':sub['FrameLength']})
  im.save(REF/f'vast_steppe_layer_{li}.png')
  if layer['Visible']:scene.alpha_composite(im)
 scene.save(REF/'vast_steppe_composition.png');(REF/'animated_cells.json').write_text(json.dumps(animated,indent=2)+'\n');print('animated',len(animated),'timings',sorted(set((len(a['frames']),a['duration_game_frames']) for a in animated)))
