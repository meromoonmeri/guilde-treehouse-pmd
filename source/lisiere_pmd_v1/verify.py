"""Pixels, source clocks, semantic layers and route tests. No engine approval."""
import io,json,sys,zipfile,hashlib,subprocess
from pathlib import Path
import numpy as np
from PIL import Image,ImageSequence
from scipy import ndimage
from build import R,S,O,C,P,N,SIZE,OLDPACK,static_layers,forest_parts,native,color,scene,sha,palette_reference

def release_file(name):
 p=O/name
 if p.exists():return p
 from release import materialize
 return materialize(name)

def main():
 checks=[]
 def ok(s):checks.append(s);print('PASS',s)
 with zipfile.ZipFile(OLDPACK) as z:
  with zipfile.ZipFile(io.BytesIO(z.read('native_sources.zip'))) as nz:nz.extractall(C/'native')
 pack=release_file('LE1_lisiere_calques_et_effets.zip')
 with zipfile.ZipFile(pack) as z:
  assert z.testzip() is None;m=json.loads(z.read('manifest.json'));imgs={n:Image.open(io.BytesIO(z.read(n))).convert('RGBA')for n in z.namelist()if n.endswith('.png')}
  names=[Path(p).name for p in imgs];assert len(names)==len(set(names))
  for n,im in imgs.items():assert im.width%8==im.height%8==0,(n,im.size)
  assert len(m['groups'])==6 and len(m['static_layers'])==5
  ok('six semantic groups, unique PNG basenames, Ground8 canvases, ZIP CRCs')
  ls,_=static_layers();expected=Image.new('RGBA',SIZE);actual=Image.new('RGBA',SIZE)
  for path,(_,im) in zip(m['static_layers'],ls):
   assert imgs[path].tobytes()==im.tobytes();a=np.array(im);assert a[:,:,3].any();assert not ((a[:,:,0]>230)&(a[:,:,1]<35)&(a[:,:,2]>220)&(a[:,:,3]>0)).any();actual.alpha_composite(imgs[path]);expected.alpha_composite(im)
  assert actual.tobytes()==expected.tobytes()
  assert (np.array(ls[1][1])[160:,:,3]==255).all()
  overlaps=np.stack([np.array(im)[:,:,3]>0 for _,im in ls]).sum(axis=0);assert overlaps.max()>=3
  ok('five separately generated layer images recompose exactly; ground continuous beneath scenery, overlapping layers not surface partitions')
  _,palette,_=palette_reference();allowed=set(map(tuple,palette))
  for _,im in ls:
   a=np.array(im);assert set(map(tuple,np.unique(a[:,:,:3][a[:,:,3]>0],axis=0)))<=allowed
  ok('generated art palette matches76reference colours; native animation colours not transformed')
  obstacle=np.zeros((336,480),bool)
  for _,im in ls[2:]:obstacle|=np.array(im)[:,:,3]>0
  assert not obstacle[144:336,208:272].any()
  walk=(np.array(ls[1][1])[:,:,3]>0)&~obstacle;walk=ndimage.binary_erosion(walk,iterations=8,border_value=1);labels,n=ndimage.label(walk)
  assert labels[312,240]>0 and labels[312,240]==labels[144,240]
  ok('south-to-north route:64pixel central strip clear of scenery, connected with8pixel conservative clearance')
  for b in range(14):
   for p in range(32):
    rays,motes=forest_parts(b,p)
    assert rays.tobytes()==imgs[m['animations']['rayons']['frames'][p]].tobytes()
    assert motes.tobytes()==imgs[m['animations']['particules']['frames'][b]].tobytes()
    idx=native('H07P04W',b*7)[2][0];assert Image.alpha_composite(rays,motes).tobytes()==color('H07P04W',idx,p*8).tobytes()
  ok('all448native forest states reconstructed exactly from32ray phases and14particle poses')
  idx=native('H26P01')[2][0];fullmask=idx//16==4
  for f in range(8):
   combined=Image.new('RGBA',(480,312));src=np.array(color('H26P01',idx,f*3));src[~fullmask]=0
   for rec in m['animations']['cascades']:
    im=imgs[rec['frames'][f]];x,y,X,Y=rec['source_box'];assert im.size==(X-x,Y-y);combined.alpha_composite(im,(x,y))
   assert np.array_equal(np.array(combined),src)
  ok('six complete visible lava-column windows recompose native palette4 exactly in all8phases, including feet/halos')
  for key in ['rayons','particules']:
   rec=m['animations'][key];assert len({sha(imgs[n].tobytes())for n in rec['frames']})>1
  for rec in m['animations']['cascades']:assert len({sha(imgs[n].tobytes())for n in rec['frames']})==8
  assert forest_parts(0,0)[0].tobytes()==forest_parts(0,32)[0].tobytes();assert forest_parts(0,0)[1].tobytes()==forest_parts(14,0)[1].tobytes()
  ok('true multiframe changes and independent source-cycle periods, no fake static scroll')
  for name,duration,loop in [('LE1_lisiere_animee.webp',4267,1),('LE1_cascades_animees.webp',400,0)]:
   im=Image.open(release_file(name));assert im.is_animated and im.info.get('loop')==loop;dt=[];hashes=[]
   for fr in ImageSequence.Iterator(im):hashes.append(sha(fr.convert('RGBA').tobytes()));dt.append(im.info.get('duration',0))
   assert sum(dt)==duration,(name,dt);assert len(set(hashes))>1
  ok('direct WebP decode: forest excerpt4267ms single-play, lava400ms complete loop')
  extracted=C/'verify_pack';extracted.mkdir(parents=True,exist_ok=True);z.extractall(extracted)
  subprocess.run([sys.executable,str(extracted/'assemble.py'),'--out',str(C/'assembled_verify'),'--tick','64'],check=True)
  assert Image.open(C/'assembled_verify/LE1_composition_tick64.png').convert('RGBA').tobytes()==scene(ls,64).tobytes()
  assert Image.open(O/'LE1_lisiere.png').convert('RGBA').tobytes()==scene(ls,64).tobytes()
  ok('standalone assembler and public PNG equal source-rendered map pixels')
 for rec in json.loads((S/'raws/archive.json').read_text()):
  raw=subprocess.check_output(['git','show',rec['commit']+':'+rec['path']],cwd=R);im=Image.open(io.BytesIO(raw)).convert('RGBA');assert sha(raw)==rec['sha256'] and sha(im.tobytes())==rec['rgba_sha256']
 ok('eight originals preserved losslessly, including rejected tree attempt and deferred finale guide')
 assert not subprocess.check_output(['git','diff','--name-only','47628495','--','renders/dungeon_biomes_v1','renders/beach*','source/beach*'],cwd=R).strip()
 ok('previous dungeon pack and Beach unchanged')
 (O/'verification.json').write_text(json.dumps({'pass':True,'checks':checks,'png_count':len(imgs),'zip_sha256':sha(pack.read_bytes()),'engine_validation':False,'artistic_approval':False},indent=2)+'\n')
if __name__=='__main__':main()
