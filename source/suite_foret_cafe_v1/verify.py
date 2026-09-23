"""Pixel, import-size, continuity and preservation checks; not artistic approval."""
import json,zipfile,sys,subprocess
import numpy as np
from scipy import ndimage
from PIL import Image
from build import O,C,R,S,IDS,image,png,previous,scene,palette,key
from storage import sha,records,raw

def run():
 checks=[]
 def ok(s):checks.append(s);print('PASS',s)
 for r in records('raw'):
  im=image(raw(r['id']));assert sha(im.tobytes())==r['rgba_sha256'];assert list(im.size)==r['size']
 ok('10 bruts Git lossless, tailles et RGBA SHA256')
 with zipfile.ZipFile(O/'LF1_finale_calques.zip') as z,previous() as old:
  m=json.loads(z.read('manifest.json'));prev=json.loads(old.read('manifest.json'));files={n:z.read(n) for n in z.namelist()};assert z.testzip() is None;assert len(m['static_layers'])==5 and m['semantic_groups']==6
  for i in [0,1,4]:assert files[m['static_layers'][i]]==old.read(prev['static_layers'][i])
  a=np.array(image(files[m['static_layers'][1]]));assert (a[160:,:,3]==255).all();assert not a[:96,:,3].any()
  obstacles=np.logical_or.reduce([np.array(image(files[p]))[:,:,3]>0 for p in m['static_layers'][2:]])
  assert not obstacles[200:296,176:304].any()
  safe=ndimage.binary_erosion((a[:,:,3]>0)&~obstacles,structure=np.ones((17,17)));labels,_=ndimage.label(safe);lab=labels[320,240];assert lab>0 and labels[208,240]==lab;assert np.argwhere(labels==lab)[:,0].min()>=128
  rock=np.array(image(files[m['static_layers'][2]]));src=np.array(image(old.read(prev['static_layers'][2])));expected=np.zeros_like(rock)
  for move in m['rock_moves']:
   x,y=move['before'];w,h=move['size'];xx,yy=move['after'];expected[yy:yy+h,xx:xx+w]=src[y:y+h,x:x+w]
  assert np.array_equal(rock,expected)
  _,col=palette();allowed={tuple(v) for v in col}
  for p in m['static_layers']:
   a=np.array(image(files[p]));assert set(map(tuple,a[:,:,:3][a[:,:,3]>0])).issubset(allowed)
  ok('6 groupes, 3 plans identiques, 4 rochers entiers, palette H07P03, sol continu, arene128x96, retourS/nord ferme avec marge8px')
  for k in ['rayons','particules']:
   rec=m['animations'][k];assert rec['frame_ticks']==prev['animations'][k]['frame_ticks']
   for p,q in zip(rec['frames'],prev['animations'][k]['frames']):assert files[p]==old.read(q)
  assert [len(m['animations'][k]['frames']) for k in ['rayons','particules']]==[32,14]
  assert scene(files,m).tobytes()==image((O/'LF1_finale.png').read_bytes()).tobytes()
  out=C/'verify_pack';out.mkdir(parents=True,exist_ok=True);z.extractall(out)
  subprocess.run([sys.executable,str(out/'assemble.py'),'--pack',str(out),'--out',str(out/'assembled')],check=True)
  assert Image.open(out/'assembled/LF1_composition_tick64.png').convert('RGBA').tobytes()==scene(files,m).tobytes()
  ok('46 PNG natifs1x inchanges, cadences32x8/14x7, fusion et assembleur autonome bitexact')
 with Image.open(O/'LF1_finale_animee.webp') as w:
  assert w.n_frames==32 and w.info['loop']==1;dur=0
  for n in range(w.n_frames):w.seek(n);w.load();dur+=w.info['duration']
  assert dur==4267
 ok('WebP32 frames /4267ms, lecture unique')
 with zipfile.ZipFile(O/'FC1_mobilier_taille_import.zip') as z,zipfile.ZipFile(R/'renders/cafe_spinda_revisite_v7/SpindaV7_complet.zip') as native:
  m=json.loads(z.read('manifest.json'));assert len(m['items'])==4;overlay=Image.new('RGBA',(600,448))
  for rec in m['items']:
   assert z.read(rec['native_reference'])==native.read(rec['native_source_file']);sp=image(z.read(rec['files']['jour']));assert list(sp.size)==rec['canvas'];bb=sp.getbbox();assert [bb[2]-bb[0],bb[3]-bb[1]]==rec['visible_size']
   src=key(image(raw(rec['raw_id'])));cut=src.crop(tuple(rec['raw_crop']));sz=rec['visible_size'];sc=min(x/y for x,y in zip(rec['native_target_visible'],cut.size));assert sz==[round(cut.width*sc),round(cut.height*sc)]
   assert cut.resize(tuple(sz),Image.Resampling.NEAREST).tobytes()==sp.crop(bb).tobytes()
   a=np.array(sp);n=np.array(image(z.read(rec['files']['nuit'])));expected=np.rint(a[:,:,:3]*[.42,.35,.40]).astype('uint8');assert np.array_equal(n[:,:,:3],expected) and np.array_equal(a[:,:,3],n[:,:,3]);overlay.alpha_composite(sp,tuple(m['demo']['positions'][rec['id']]))
  for mode,path in m['atlas']['files'].items():
   sheet=image(z.read(path));assert list(sheet.size)==m['atlas']['size']
   for rec,slot in zip(m['items'],m['atlas']['objects']):
    x,y,w,h=slot['rect'];assert all(v%8==0 for v in slot['rect']);assert sheet.crop((x,y,x+w,y+h)).tobytes()==image(z.read(rec['files'][mode])).tobytes()
  base=(R/m['demo']['base']).read_bytes();assert sha(base)==m['demo']['base_sha256'];demo=image(base);demo.alpha_composite(overlay);assert demo.tobytes()==image(z.read('apercus/FC1_cafe_echelle1x.png')).tobytes();assert overlay.tobytes()==image(z.read('demonstration/FC1_objets_seuls.png')).tobytes()
  ok('4 references natives intactes; 8 objets aux gabarits, ratios preservés, nuit, 2 atlas exacts; cafe1x non destructif')
 names=[]
 for pack in ['LF1_finale_calques.zip','FC1_mobilier_taille_import.zip']:
  with zipfile.ZipFile(O/pack) as z:
   for name in z.namelist():
    if not name.endswith('.png'):continue
    im=image(z.read(name));assert im.width%8==im.height%8==0;a=np.array(im);assert not ((a[:,:,0]>200)&(a[:,:,1]<50)&(a[:,:,2]>200)&(a[:,:,3]>0)).any();names.append(name.rsplit('/',1)[-1])
 assert len(names)==len(set(names));ok(f'{len(names)} PNG Ground8, basenames uniques, sans magenta visible')
 changed=subprocess.check_output(['git','diff','ac404578','--name-only'],cwd=R,text=True).splitlines();assert not any(p.startswith('renders/') and not p.startswith('renders/suite_foret_cafe_v1/') for p in changed)
 ok('anciens rendus/ZIP, entree approuvee, salles et Beach inchanges')
 (C/'verification.json').write_text(json.dumps({'checks':checks,'engine_validation':False,'artistic_approval':False},ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':run()
