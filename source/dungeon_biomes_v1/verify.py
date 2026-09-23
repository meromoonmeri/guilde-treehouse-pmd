"""Asset/provenance tests, not artistic approval or an engine validation."""
from native_archive import native_source_archive

from pathlib import Path
import io,json,zipfile,hashlib,subprocess,sys
import numpy as np
from PIL import Image,ImageSequence
from build import S,O,C,N,BIOMES,normalized,native,colorize,component,lava,render
from archive import data,entries
checks=[]
def ok(s):checks.append(s);print('PASS',s)
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 with zipfile.ZipFile(O/'DB1_cinq_duos_multicalques.zip') as z:
  assert z.testzip() is None;m=json.loads(z.read('manifest.json'));names=z.namelist();assert len(names)==len(set(names))
  images={n:Image.open(io.BytesIO(z.read(n))).convert('RGBA') for n in names if n.endswith('.png')}
  basenames=[Path(n).name for n in images];assert len(basenames)==len(set(basenames))
  for n,im in images.items():assert im.width%8==im.height%8==0,(n,im.size)
  ok('ZIP CRC, unique PNG basenames, all PNG canvases Ground8-aligned')
  assert len(m['maps'])==10 and len(m['remaining'])==6
  for rec in m['maps']:
   expected=normalized(rec['id'],tuple(rec['size']));actual=Image.new('RGBA',expected.size);coverage=np.zeros(expected.size[::-1],np.uint8)
   for f in rec['layers']:
    im=images[f];a=np.array(im);assert im.size==expected.size and a[:,:,3].any();coverage+=(a[:,:,3]>0);actual.alpha_composite(im)
    assert not ((a[:,:,0]>230)&(a[:,:,1]<35)&(a[:,:,2]>220)&(a[:,:,3]>0)).any(),f
   assert coverage.max()==1;assert actual.tobytes()==expected.tobytes(),rec['id']
  ok('42 nonempty transparent surface layers exactly reconstruct ten generated terrains, no magenta or overlap')
  for r in entries():assert sha(data(S.parent.parent/r['path']))==r['sha256']
  ok('ten lossless generated originals retrievable from pinned Git history')
  a=json.loads(z.read('audit.json'));assert a['H_bank_comparison']=={'count':207,'identical':207}
  assert len(a['references'])==11
  with zipfile.ZipFile(io.BytesIO(z.read('native_sources.zip'))) as nz:
   for rec in a['files']:
    b=nz.read(rec['path']);assert sha(b)==rec['sha256'];assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==rec['git_sha1']
    if rec['path'].startswith('data/map_bg/H'):assert rec['identical_to_pret']
  ok('eleven-reference audit and all pinned source SHA256/Git-blob hashes')
  with zipfile.ZipFile(native_source_archive()) as nz:nz.extractall(C/'native')
  for b in range(14):
   idx=native('H07P04W',b*7)[2][0]
   for p in range(32):assert images[m['animations']['foret']['frames'][b*32+p]].tobytes()==colorize('H07P04W',idx,p*8).tobytes()
  ok('all 448 forest BPA/BPL joint states equal the decoded 1x source pixels')
  for key,name,layer,count,dt in [('ile','H29P04',1,36,6),('marin','H02P02W',0,32,8),('desert_voile','W05',0,32,8),('volcan_cendres','W04',0,16,7)]:
   for f in range(count):
    expected=component(name,f*dt,layer)
    if key=='volcan_cendres':expected=expected.crop((0,0,480,312))
    assert images[m['animations'][key]['frames'][f]].tobytes()==expected.tobytes()
  ok('all sky/current/veil/ash states equal their native 1x source windows')
  for pi in [8,9]:
   rec=m['animations'][f'reference_desert_p{pi}'];idx=native('H20P01')[2][0]
   for f,path in enumerate(rec['frames']):
    expected=np.array(colorize('H20P01',idx,f*rec['frame_ticks']));expected[idx//16!=pi]=0
    assert np.array_equal(np.array(images[path]),expected)
  ok('all21original desert palette-channel states match the source; no placement on new terrain')
  co=np.array(images['provenance/DB1_lava_source_coordinates.png']).astype(np.uint32);coords=co[:,:,0]+256*co[:,:,1]+65536*co[:,:,2]
  assert coords.max()<480*312
  for f in range(31):
   full=np.array(component('H26P01',f*4));expected=full.reshape(-1,4)[coords]
   assert np.array_equal(np.array(images[m['animations']['volcan_lave']['frames'][f]]),expected)
  ok('every lava pixel in all31frames maps to unchanged native source pixels, no interpolation/flip/scale')
  for key,rec in m['animations'].items():
   assert len({sha(images[f].tobytes())for f in rec['frames']})>1,key
  ok('each exported animation bank contains genuinely different visible states')
  for name,period in [('H07P04W',12544),('H29P04',216),('H02P02W',256),('W04',112)]:
   layer=1 if name=='H29P04' else 0
   assert component(name,0,layer).tobytes()==component(name,period,layer).tobytes()
  assert lava(0).tobytes()==lava(124).tobytes()
  ok('independent source-cycle periods close exactly; excerpt is not claimed as their combined loop')
  for b in BIOMES:
   im=Image.open(O/'apercus'/f'DB1_{b}_duo.webp');assert im.is_animated and im.n_frames>1 and im.info.get('loop')==1
   durations=[];digests=[]
   for frame in ImageSequence.Iterator(im):
    digests.append(sha(frame.convert('RGBA').tobytes()));durations.append(im.info.get('duration',0))
   assert sum(durations)==m['preview']['duration_ms'],(b,durations)
   assert len(set(digests))>1
  ok(f"five WebP files decode as changing animations with the documented {m['preview']['duration_ms']}ms duration and single playback")
  extracted=C/'verify_pack';extracted.mkdir(exist_ok=True);z.extractall(extracted)
 subprocess.run([sys.executable,str(extracted/'assemble.py'),'--tick','64','--out',str(C/'assembled_verify')],check=True)
 for rec in m['maps']:
  biome=rec['id'].split('_')[0];terrain=normalized(rec['id'],tuple(rec['size']));out=C/'assembled_verify'
  assert Image.open(out/(rec['id']+'_terrain.png')).convert('RGBA').tobytes()==terrain.tobytes()
  assert Image.open(out/(rec['id']+'_tick64.png')).convert('RGB').tobytes()==render(biome,terrain,64).tobytes()
 ok('standalone ZIP assembler reproduces all ten transparent terrains and source-rendered demonstrations')
 # Existing Beach work is explicitly out of scope; no change since prior release.
 changed=subprocess.check_output(['git','diff','--name-only','943f6f15','--','renders/beach*','source/beach*'],cwd=S.parents[1]).decode().strip();assert not changed
 ok('Beach source and deliverables untouched since previous release')
 result={'pass':True,'checks':checks,'png_count':len(images),'layer_count':sum(len(r['layers'])for r in m['maps']),'animation_state_count':sum(len(r['frames'])for r in m['animations'].values()),'zip_sha256':sha((O/'DB1_cinq_duos_multicalques.zip').read_bytes()),'validation':'No PMDO/GBA/PC-port runtime or artistic approval claimed.'}
 (O/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
