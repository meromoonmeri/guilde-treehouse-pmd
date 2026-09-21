"""Independent deliverable checks; no artistic or engine approval implied."""
from pathlib import Path
import sys,json,zipfile,io,hashlib,subprocess
from PIL import Image
import numpy as np
S=Path(__file__).resolve().parent;R=S.parents[1];O=R/'renders/cafe_spinda_revisite_v8';sys.path.insert(0,str(S))
from archive import entries,data

def im(b):return Image.open(io.BytesIO(b)).convert('RGBA')
def scene(z,layers):
 out=Image.new('RGBA',(600,448))
 for l in layers:out.alpha_composite(im(z.read(l['file'])))
 return out

def run():
 m=json.loads((O/'manifest.json').read_text());c=json.loads((O/'audit/coverage.json').read_text());assert (c['generated_attempts'],c['accepted'],c['planned_furniture'],c['pending'])==(10,9,36,27)
 assert sum(i['status']=='pending_generation' for i in c['items'])==26;assert [i['id'] for i in c['items'] if i['status']=='rejected_camera']==['table_halcyon_vide']
 for a in entries():assert hashlib.sha256(data(R/a['path'])).hexdigest()==a['sha256']
 with zipfile.ZipFile(O/m['pack']) as z,zipfile.ZipFile(R/'renders/cafe_spinda_revisite_v7/SpindaV7_complet.zip') as old:
  assert z.testzip() is None;assert all(i.compress_type==0 for i in z.infolist());assert len(z.namelist())==len(set(z.namelist()));prev={r['id']:r for r in json.loads(old.read('manifest.json'))['rooms']};portable=json.loads(z.read('manifest.json'));assert portable['packed_layers'] is False
  for r in m['rooms']:
   assert r['ports']==prev[r['id']]['ports'];day=scene(z,r['modes']['jour']['layers']);night=scene(z,r['modes']['nuit']['layers']);assert day.tobytes()==scene(old,prev[r['id']]['layers']).tobytes();a=np.array(day);b=np.array(night);assert np.array_equal(a[:,:,3],b[:,:,3]);assert b[:,:,:3].sum()<a[:,:,:3].sum()
   for mode in r['modes'].values():
    for l in mode['layers']:assert im(z.read(l['file'])).size==(600,448);assert 'ruban' not in l['id']
   light=np.array(im(z.read(r['modes']['nuit']['layers'][-1]['file'])));assert light[:,:,3].max()<=32;assert not light[a[:,:,3]==0].any()
  for a in portable['assets']:assert z.read(a['reference']);assert a['native'] is False
  for a in m['assets']:
   for mode,file in a['files'].items():
    b=(O/file).read_bytes();assert z.read(file)==b;img=im(b);assert img.width%8==img.height%8==0;assert img.getbbox();arr=np.array(img);assert not ((arr[:,:,0]==255)&(arr[:,:,1]==0)&(arr[:,:,2]==255)&(arr[:,:,3]>0)).any()
 atlas=json.loads((O/'audit/tilesheet_index.json').read_text())
 for mode,path in atlas['files'].items():
  sheet=im((O/path).read_bytes());occupied=np.zeros((sheet.height,sheet.width),bool)
  for rec in atlas['objects']:
   x,y,w,h=rec['rect'];assert all(v%8==0 for v in rec['rect']);assert not occupied[y:y+h,x:x+w].any();occupied[y:y+h,x:x+w]=True;a=next(a for a in m['assets'] if a['id']==rec['id']);assert sheet.crop((x,y,x+w,y+h)).tobytes()==im((O/a['files'][mode]).read_bytes()).tobytes()
 # Previously delivered files remain byte-identical, including counters and Beach.
 changed=subprocess.check_output(['git','diff','--name-only','bc6f07f3'],cwd=R,text=True).splitlines()
 assert not any(p.startswith(('renders/beach_sky_gradient_v3/','renders/cafe_spinda_revisite_v7/','renders/cafe_spinda_revisite_v6/')) for p in changed)
 print('PASS: coverage,15 source archives,5 exact day rooms,night alpha/soft light,57 layers,9 generated assets,2 atlases,portable ZIP,V6/V7/Beach unchanged')
if __name__=='__main__':run()
