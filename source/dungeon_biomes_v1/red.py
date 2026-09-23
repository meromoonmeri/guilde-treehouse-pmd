"""Read uncompressed Red Rescue Team BPC/BPL/BPA + BMA NRL, from pinned public source."""
from pathlib import Path
import struct,re,math,json
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];BASE=R/'.cache/redport_audit/port/data/map_bg'
def u16(b,p=0):return struct.unpack_from('<H',b,p)[0]
def palettes(b,tick=0):
 count,animated=struct.unpack_from('<HH',b);base=np.frombuffer(b[4:4+count*60],dtype=np.uint8).reshape(count,15,4).copy();spec=[];p=4+count*60
 if animated:
  spec=[struct.unpack_from('<HH',b,p+i*4) for i in range(count)];p+=count*4
  for i,(duration,n) in enumerate(spec):
   if n:
    frames=np.frombuffer(b[p:p+n*60],dtype=np.uint8).reshape(n,15,4);base[i]=frames[(tick//max(1,duration))%n];p+=n*60
 out=np.zeros((count,16,4),np.uint8);out[:,1:,:3]=base[:,:,:3];out[:,1:,3]=255
 return out,spec

def bma(b):
 tw,th,cw,ch,w,h,layers,dat,coll=struct.unpack_from('<6B3H',b);p=12;result=[]
 for _ in range(layers):
  rows=[]
  for y in range(h):
   row=[]
   while len(row)<w:
    cmd=b[p];p+=1
    if cmd>=192:
     for i in range(cmd-191):v=int.from_bytes(b[p:p+3],'little');p+=3;row.extend([v&4095,v>>12])
    elif cmd>=128:
     v=int.from_bytes(b[p:p+3],'little');p+=3;row.extend([v&4095,v>>12]*(cmd-127))
    else:row.extend([0,0]*(cmd+1))
   assert len(row) in [w,w+1]
   row=np.array(row[:w],np.uint16)
   if y:row^=rows[-1]
   rows.append(row)
  result.append(np.stack(rows))
 return result,{'size':[tw*8,th*8],'chunks':[w,h],'layers':layers,'consumed':p,'header':list(b[:12])}

def tiles(b):
 a=np.frombuffer(b,dtype=np.uint8);out=np.empty(a.size*2,np.uint8);out[::2]=a&15;out[1::2]=a>>4;return out.reshape(-1,8,8)
def bpa(b,tick=0):
 nframes=u16(b,2);dur=list(struct.unpack_from('<'+'I'*nframes,b,4));raw=b[4+4*nframes:];n=len(raw)//(32*nframes);assert len(raw)==n*32*nframes and n==u16(b,0)
 # ground_bg.c uses counter-- <= 0, hence stored duration + 1 update ticks.
 timings=[d+1 for d in dur];elapsed=tick%sum(timings);frame=0
 while elapsed>=timings[frame]:elapsed-=timings[frame];frame+=1
 return tiles(raw[frame*n*32:(frame+1)*n*32]),{'tiles':n,'frames':nframes,'stored_ticks':dur,'display_ticks':timings}

def decode(name,tick=0,folder=BASE):
 b=(folder/(name+'c.bpc')).read_bytes();hdr=struct.unpack_from('<8H',b);cw,ch,nt,*_=hdr;slots=list(hdr[3:7]);nc=hdr[7];p=16;static=tiles(b[p:p+(nt-1)*32]);p+=(nt-1)*32;bank=np.concatenate([np.zeros((1,8,8),np.uint8),static]);animations=[]
 for slot,n in enumerate(slots):
  if n:
   ab=(folder/(name+str(slot+1)+'.bpa')).read_bytes();anim,meta=bpa(ab,tick);assert len(anim)==n;bank=np.concatenate([bank,anim]);animations.append({'slot':slot,**meta})
 chunks=np.concatenate([np.zeros((1,ch,cw),np.uint16),np.frombuffer(b[p:p+(nc-1)*cw*ch*2],dtype='<u2').reshape(nc-1,ch,cw)])
 pal,spec=palettes((folder/(name+'.bpl')).read_bytes(),tick);grids,meta=bma((folder/(name+'m.bma')).read_bytes());images=[];indices=[];tileids=[]
 for grid in grids:
  H,W=grid.shape;arr=np.zeros((H*ch*8,W*cw*8,4),np.uint8);idx=np.zeros(arr.shape[:2],np.uint8);ids=np.zeros(arr.shape[:2],np.uint16)
  for y in range(H):
   for x in range(W):
    cells=chunks[grid[y,x]]
    for yy in range(ch):
     for xx in range(cw):
      v=int(cells[yy,xx]);tid=v&1023;pi=v>>12;tile=bank[tid]
      if v&1024:tile=tile[:,::-1]
      if v&2048:tile=tile[::-1]
      Y=y*ch*8+yy*8;X=x*cw*8+xx*8
      # Palette bits on fully transparent tiles have no visible colour lookup.
      # Never wrap a nonzero pixel into an unrelated palette bank.
      if pi>=len(pal):
       assert not tile.any(), (name,pi,tid,'nontransparent unbound palette')
       rgba=np.zeros((8,8,4),np.uint8)
      else:rgba=pal[pi,tile]
      arr[Y:Y+8,X:X+8]=rgba;idx[Y:Y+8,X:X+8]=pi*16+tile;ids[Y:Y+8,X:X+8]=tid
  images.append(Image.fromarray(arr));indices.append(idx);tileids.append(ids)
 meta.update(name=name,bpc_header=list(hdr),bpa=animations,palette_spec=[list(s) for s in spec],palette_count=len(pal))
 return images,meta,indices,tileids
if __name__=='__main__':
 out=R/'.cache/redport_audit/decoded';out.mkdir(exist_ok=True);report={}
 for p in BASE.glob('*m.bma'):
  name=p.name[:-5]
  if not (BASE/(name+'c.bpc')).exists():continue
  imgs,meta,_,_=decode(name);result=Image.new('RGBA',imgs[0].size)
  for im in reversed(imgs):result.alpha_composite(im)
  result.save(out/(name+'.png'));report[name]=meta
 (out/'report.json').write_text(json.dumps(report,indent=2));print('Decoded',len(report),'native backgrounds')
