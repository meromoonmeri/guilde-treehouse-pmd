"""Pixels, composition, room clearances and archives; not a PMDO/artist approval."""
from pathlib import Path
import json,hashlib,sys,io,zipfile,subprocess
import numpy as np
from PIL import Image
S=Path(__file__).resolve().parent;R=S.parents[1];O=R/'renders/spinda_decor_v1';sys.path.insert(0,str(S))
from archive import data,entries

def image(p):return Image.open(p).convert('RGBA')
def h(b):return hashlib.sha256(b).hexdigest()
def run():
 m=json.loads((O/'manifest.json').read_text());assert len(m['assets'])==9;assert m['accepted_generated_images']==8 and len(m['rejected'])==2
 for r in entries():
  raw=data(R/r['path']);assert h(raw)==r['sha256'];assert h(image(io.BytesIO(raw)).tobytes())==r['rgba_sha256']
 for obj in m['assets']:
  day=image(O/obj['files']['jour']);night=image(O/obj['files']['nuit']);assert day.size==tuple(obj['size']);assert day.width%8==day.height%8==0;assert day.getchannel('A').tobytes()==night.getchannel('A').tobytes()
  a=np.array(day);assert set(np.unique(a[:,:,3])).issubset({0,255});assert not ((a[:,:,0]>230)&(a[:,:,1]<30)&(a[:,:,2]>230)&(a[:,:,3]>0)).any();assert obj['native'] is False
 atlas=image(O/m['tilesheet']['file']);occupied=np.zeros((atlas.height,atlas.width),bool)
 for r in m['tilesheet']['rects']:
  x,y,w,hg=r['rect'];assert all(n%8==0 for n in r['rect']);assert not occupied[y:y+hg,x:x+w].any();occupied[y:y+hg,x:x+w]=True;obj=next(a for a in m['assets'] if a['id']==r['id']);assert atlas.crop((x,y,x+w,y+hg)).tobytes()==image(O/obj['files']['jour']).tobytes()
 composite=Image.new('RGBA',tuple(m['stage']['canvas']))
 for l in m['stage']['layers']:
  p=image(O/l['files']['jour']);assert p.size==composite.size;composite.alpha_composite(p)
 assert composite.tobytes()==image(O/'apercus/SpindaDecor_estrade_assemblee.png').tobytes();assert len(m['stage']['layers'])==3
 with zipfile.ZipFile(R/'renders/cafe_spinda_revisite_v7/SpindaV7_complet.zip') as z:
  old={r['id']:r for r in json.loads(z.read('manifest.json'))['rooms']}
  for r in m['room_layers']:
   day=Image.new('RGBA',(600,448));windows=np.zeros((448,600),bool)
   for l in old[r['id']]['layers']:
    im=image(io.BytesIO(z.read(l['file'])));day.alpha_composite(im)
    if l['id']=='fenetres':windows=np.array(im)[:,:,3]>0
   b=np.array(image(O/r['files']['jour']));bn=np.array(image(O/r['files']['nuit']));assert b.shape==(448,600,4);assert np.array_equal(b[:,:,3],bn[:,:,3]);assert not ((b[:,:,3]>0)&windows).any();assert not ((b[:,:,3]>0)&(np.array(day)[:,:,3]==0)).any()
   if r['id'] in ['accueil','casino']:assert not b[:192,232:368,3].any()
   for p in old[r['id']]['ports'].values():
    x,y=p['point'];assert not b[max(y-16,0):y+17,max(x-16,0):x+17,3].any()
   if r['id']=='cafe':assert image(O/'apercus/SpindaDecor_cafe_demonstration.png').getchannel('A').tobytes()==day.getchannel('A').tobytes()
 reference=(O/m['reference']['file']).read_bytes();assert reference==(R/'renders/cafe_spinda_revisite_v7/assets/SpindaV7_ruban_spinda.png').read_bytes();assert h(reference)==m['reference']['sha256']
 with zipfile.ZipFile(O/'Spinda_banderoles_tapis_estrade.zip') as z:
  assert z.testzip() is None;assert len(z.namelist())==len(set(z.namelist()));names=[Path(n).name for n in z.namelist() if n.endswith('.png')];assert len(names)==len(set(names))
  for name in z.namelist():assert z.read(name)==(O/name).read_bytes()
 # Every previous rendered delivery preserved; only three raw historical files moved to Git storage.
 changed=subprocess.check_output(['git','diff','--name-only','d73e6ac2','--','renders'],cwd=R,text=True).splitlines();allowed={'renders/casino_network_v1/bruts/'+n+'.webp' for n in ['estrade','rideaux','terrain']};assert all(f.startswith('renders/spinda_decor_v1/') or f in allowed for f in changed),changed
 report={'pass':True,'generated_originals':10,'accepted_generations':8,'native_reference_unchanged':True,'adapted_assets_are_non_native':True,'independent_assets':9,'red_rugs':3,'room_bunting_layers':10,'aligned_stage_layers':3,'windows_and_ports_clear':True,'stage_alpha_recomposition_exact':True,'day_night_alpha_identical':True,'ground_8px_canvases':True,'previous_rendered_deliveries_unchanged':True,'runtime_PMDO':'NOT TESTED'}
 (O/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':run()
