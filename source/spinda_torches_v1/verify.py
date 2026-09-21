"""Independent pixel/index/palette and package checks; no engine/artist approval."""
from pathlib import Path
import sys,json,zipfile,hashlib,io,subprocess
import numpy as np
from PIL import Image
S=Path(__file__).resolve().parent;R=S.parents[1];O=R/'renders/spinda_torches_v1';sys.path.insert(0,str(S))
from archive import entries,data
from direct_previews import resource

def sha(b):return hashlib.sha256(b).hexdigest()
def run():
 m=json.loads((O/'manifest.json').read_text());palette=json.loads((O/'palette_cycles.json').read_text());assert len(m['objects'])==8;assert len(entries())==9
 for r in entries():
  b=data(R/r['path']);assert sha(b)==r['sha256'];assert sha(Image.open(io.BytesIO(b)).convert('RGBA').tobytes())==r['rgba_sha256']
 with zipfile.ZipFile(O/'Spinda_torches_8angles_animees.zip') as z:
  assert z.testzip() is None;assert len(z.namelist())==len(set(z.namelist()));assert len([n for n in z.namelist() if n.startswith('lumiere/')])==128
  for o in m['objects']:
   support=Image.open(O/o['support']['jour']).convert('RGBA');night=Image.open(O/o['support']['nuit']).convert('RGBA');assert support.size==(64,88);assert support.getchannel('A').tobytes()==night.getchannel('A').tobytes();indices=np.array(Image.open(O/o['indices']));strip=Image.open(io.BytesIO(resource(o['light_strip']))).convert('RGBA');assert strip.size==(1536,96);hashes=set();alphas=[]
   for frame,file in enumerate(o['light_frames']):
    im=Image.open(io.BytesIO(z.read(file)));assert im.mode=='P';assert np.array_equal(np.array(im),indices);rgba=im.convert('RGBA');a=np.array(rgba);assert a[:,:,3].max()<=30;alphas.append(a[:,:,3]);hashes.add(sha(rgba.tobytes()));assert strip.crop((frame*96,0,(frame+1)*96,96)).tobytes()==rgba.tobytes()
    table=np.array(palette['base_rgba_palette'],dtype='uint8').copy()
    for ring in palette['rings']:
     start=ring['start'];n=ring['length'];table[start:start+n]=np.roll(table[start:start+n],-frame,axis=0)
    assert np.array_equal(table[indices],a)
   assert len(hashes)==16;assert all(np.array_equal(a,alphas[0]) for a in alphas)
   assert z.read(o['light_strip'])==resource(o['light_strip'])
  poses=[]
  for f in m['flame']['frames']:
   b=(O/f['file']).read_bytes();assert b==(R/f['source']).read_bytes()==z.read(f['file']);assert sha(b)==f['sha256'];poses.append(Image.open(io.BytesIO(b)).convert('RGBA'))
  assert len({p.tobytes() for p in poses})==4;assert len({p.getchannel('A').tobytes() for p in poses})==4
  # Background = exact V8 room without the old static halo, not a new architecture.
  with zipfile.ZipFile(R/'renders/cafe_spinda_revisite_v8/SpindaV8_atelier_lot1.zip') as old:
   r=next(r for r in json.loads(old.read('manifest.json'))['rooms'] if r['id']=='cafe');im=Image.new('RGBA',(600,448))
   for l in r['modes']['nuit']['layers']:
    if l['id']!='lumiere_tamisee':im.alpha_composite(Image.open(io.BytesIO(old.read(l['file']))).convert('RGBA'))
   assert Image.open(io.BytesIO(resource(m['background']))).convert('RGBA').tobytes()==im.tobytes()
  assert z.read('index.html')==(O/'index.html').read_bytes().replace(b'class="button primary" href="Spinda_torches_8angles_animees.zip"',b'hidden class="button primary" href="Spinda_torches_8angles_animees.zip"')
 animation=Image.open(O/'Torche_N_animation.webp');assert animation.n_frames==16 and animation.info['loop']==0
 assert all(v%8==0 for v in [64,88,96,32,40]);assert m['frame_count']*m['frame_ms']==1600
 changed=subprocess.check_output(['git','diff','--name-only','d9f9d46c'],cwd=R,text=True).splitlines();assert not any(p.startswith(('renders/cafe_spinda_revisite_v8/','renders/cafe_spinda_revisite_v7/','renders/beach_sky_gradient_v3/')) for p in changed)
 report={'pass':True,'generated_orientations':8,'raw_outputs':9,'rejected_frontal_attempts':1,'indexed_frames':128,'unique_frames_per_orientation':16,'identical_indices_and_alpha_over_time':True,'palette_rotation_pixel_exact':True,'rgba_strips_pixel_exact':True,'native_fire_poses_pixel_exact':4,'native_fire_poses_have_different_alpha':True,'period_ms':1600,'old_maps_unchanged':True,'background_exact_V8_minus_static_halo':True,'runtime_PMDO':'NOT TESTED'}
 (O/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':run()
