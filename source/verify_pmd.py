from pathlib import Path
from PIL import Image
import numpy as np,json,struct,zlib
R=Path(__file__).resolve().parents[1];M=json.loads((R/'kit.json').read_text());report={'salles':[],'animation':False}
assert len(M['salles'])==12
assert [r['id'] for r in M['salles'] if r['porte_nord']]==['02']
for room in M['salles']:
 w,h=room['dimensions'];assert w%8==h%8==0;hole=np.array(Image.open(R/'fenetres_exterieur'/room['id']/'masque.png'))>0;rec={'id':room['id'],'acces':room['acces'],'modes':{}}
 for weather in M['ambiances']:
  view=np.array(Image.open(R/'fenetres_exterieur'/room['id']/(weather+'.png')).convert('RGBA'))
  assert np.array_equal(view[:,:,3]>0,hole),'Landscape outside aperture'
 for mode in ['jour','nuit']:
  base=Image.open(R/room['fichiers'][mode]['base']).convert('RGBA');ba=np.array(base);assert not ba[:,:,3][hole].any(),'Opaque window in base'
  chroma=np.array(Image.open(R/room['fichiers'][mode]['magenta']).convert('RGB'));assert not hole.any() or np.all(chroma[hole]==[255,0,255])
  target=Image.open(R/room['fichiers'][mode]['png']).convert('RGBA');comp=Image.new('RGBA',(w,h))
  for i,l in enumerate(M['calques']):
   q=Image.open(R/'calques'/room['dossier']/mode/(l['id']+'.png')).convert('RGBA');assert q.size==(w,h)
   if i in [6,7]:assert q.getbbox() is None
   if i in [8,9]:assert q.getbbox() is not None
   if i==5 and room['id']!='02':assert q.getbbox() is None
   comp.alpha_composite(q)
  assert np.array_equal(np.array(comp),np.array(target)),'Layer reconstruction mismatch'
  assert np.array(target)[:,:,:3][np.array(target)[:,:,3]>0].mean()>(35 if mode=='jour' else 10),'Dark conversion error'
  data=(R/room['fichiers'][mode]['aseprite']).read_bytes();size,magic,n,w0,h0,depth,flags,speed=struct.unpack_from('<IHHHHHIH',data)
  assert size==len(data) and magic==0xa5e0 and n==1 and (w0,h0)==(w,h) and depth==32
  assert struct.unpack_from('<hhHH',data,36)==(0,0,8,8)
  fs,fm,nc,dt=struct.unpack_from('<IHHH',data,128);assert fm==0xf1fa;pos=144;cel={};layers=0
  for _ in range(nc):
   length,kind=struct.unpack_from('<IH',data,pos);p=data[pos+6:pos+length]
   if kind==0x2004:layers+=1
   if kind==0x2005:
    k,x,y,op,typ,zi=struct.unpack_from('<HhhBHh',p);cw,ch=struct.unpack_from('<HH',p,16);assert typ==2 and op==255
    cel[k]=(x,y,Image.frombytes('RGBA',(cw,ch),zlib.decompress(p[20:])))
   pos+=length
  assert pos==len(data) and layers==11
  c=Image.new('RGBA',(w,h))
  for _,(x,y,q) in sorted(cel.items()):c.alpha_composite(q,(x,y))
  assert np.array_equal(np.array(c),np.array(target)),'Aseprite reconstruction mismatch'
  tm=json.loads((R/'tiled'/f'{room["id"]}_{mode}.tmj').read_text());assert tm['tilewidth']==tm['tileheight']==8 and len(tm['layers'])==11
  c=Image.new('RGBA',(w,h));cols,rows=w//8,h//8
  for la,ts in zip(tm['layers'],tm['tilesets']):
   arr=np.array(Image.open((R/'tiled'/ts['image']).resolve()).convert('RGBA'));tiles=arr.reshape(rows,8,cols,8,4).transpose(0,2,1,3,4).reshape(-1,8,8,4)
   ids=np.array(la['data']);out=np.zeros_like(tiles);ok=ids>0;out[ok]=tiles[ids[ok]-ts['firstgid']];out=out.reshape(rows,cols,8,8,4).transpose(0,2,1,3,4).reshape(h,w,4);c.alpha_composite(Image.fromarray(out,'RGBA'))
  assert np.array_equal(np.array(c),np.array(target)),'Tiled reconstruction mismatch'
  rec['modes'][mode]={'calques':11,'frames':1,'PNG_Aseprite_Tiled':'identiques','base_fenetres_transparentes':True,'magenta_exact':True}
 report['salles'].append(rec)
report['unique_porte_fermee']='02 — nord vers le bureau 12'
report['ambiances']=M['ambiances'];report['grille']=8
(R/'controle_qualite.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('PASS: 12 salles, 24 Aseprite fixes, 11 calques, 6 vues, fenêtres transparentes, magenta exact, Tiled identique.')
