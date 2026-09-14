from pathlib import Path
import json,hashlib,io,zipfile,xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
from palette import tint
R=Path(__file__).resolve().parents[2];O=R/'renders/layouts_magenta_v1';base=json.loads((O/'manifest.json').read_text());extra=json.loads((O/'enhancements_manifest.json').read_text());BY={e['id']:e for e in base['scenes']}
def load(p):return Image.open(p).convert('RGBA')
def assert_ora(p,size,expected):
 with zipfile.ZipFile(p) as z:
  root=ET.fromstring(z.read('stack.xml'));im=Image.new('RGBA',size)
  for el in reversed(root.find('stack').findall('layer')):im.alpha_composite(load_bytes(z.read(el.attrib['src'])))
  assert np.array_equal(np.array(im),np.array(expected))
def load_bytes(b):return Image.open(io.BytesIO(b)).convert('RGBA')
records=[];native_total=0;extra_total=0
for e in base['scenes']:
 p=O/'zones'/e['id'];size=tuple(e['size']);layers=[load(p/l['file']) for l in e['layers']];src=Image.open(R/e['source']);count=getattr(src,'n_frames',1);preserve=np.array(Image.open(R/'source/layouts_magenta_v1/references'/(e['biome']+'_preserve.png')))>0
 assert hashlib.sha256((R/e['source']).read_bytes()).hexdigest()==e['source_sha256']
 for f in range(count):
  c=Image.new('RGBA',size);src.seek(f)
  if e['animation']:
   im=load(p/e['animation']['files'][f]);assert im.size==size;c.alpha_composite(im);assert e['animation']['durations_ms'][f]==src.info['duration']
  for im in layers:assert im.size==size;c.alpha_composite(im)
  assert np.all(np.array(c)[:,:,3]==255)
  if e['animation']:assert np.array_equal(np.array(c)[preserve],np.array(tint(src.convert('RGBA'),e['biome'],e['palette_index']))[preserve]);native_total+=1
  if f==0:assert np.array_equal(np.array(c),np.array(load(p/'COMPOSITION.png')))
 assert_ora(p/(e['id']+'.ora'),size,load(p/'COMPOSITION.png'));records.append({'id':e['id'],'source_sequences_and_durations_preserved':True,'ora_and_png_match':True})
for e in extra['scenes']:
 p=O/'variantes'/e['id'];parent=BY[e['parent']];pp=O/'zones'/parent['id'];size=tuple(e['size']);layers={l['name']:load(p/l['file']) for l in e['layers']};groups=e['animation_groups'];imgs=[[load(p/f) for f in g['files']] for g in groups]
 def frame(t,ds):
  t%=sum(ds)
  for i,d in enumerate(ds):
   if t<d:return i
   t-=d
 def render(t):
  c=Image.new('RGBA',size)
  for j,g in enumerate(groups):
   if g['position']=='under':c.alpha_composite(imgs[j][frame(t,g['durations_ms'])])
  for im in layers.values():assert im.size==size;c.alpha_composite(im)
  for j,g in enumerate(groups):
   if g['position']=='over':c.alpha_composite(imgs[j][frame(t,g['durations_ms'])])
  return c
 for t in range(0,e['cycle_ms'] or 1,e['preview_step_ms'] or 1):
  c=render(t);assert np.all(np.array(c)[:,:,3]==255)
  if t==0:assert np.array_equal(np.array(c),np.array(load(p/'COMPOSITION.png')))
 assert_ora(p/(e['id']+'.ora'),size,load(p/'COMPOSITION.png'))
 for j,g in enumerate(groups):
  assert len(g['files'])==len(g['durations_ms']);assert all(d>0 for d in g['durations_ms']);extra_total+=len(g['files'])
 if e['kind']=='forest':
  mask=np.zeros((size[1],size[0]),bool)
  for name in ['09_feuillage_gauche','10_feuillage_droit']:mask|=np.array(layers[name])[:,:,3]>0
  assert mask.any();assert not mask[:,int(size[0]*.31):int(size[0]*.69)].any()
 elif e['kind']=='iridescent':
  ref=imgs[1][0];arr=np.array(ref)
  for im in imgs[1]:assert np.array_equal(np.array(im)[:,:,:3],arr[:,:,:3])
  assert any(not np.array_equal(np.array(im)[:,:,3],arr[:,:,3]) for im in imgs[1][1:]);assert sum(groups[0]['durations_ms'])==sum(groups[1]['durations_ms'])==1920
 else:
  assert groups[0]['durations_ms']==parent['animation']['durations_ms']
  assert any(not np.array_equal(np.array(im),np.array(imgs[0][0])) for im in imgs[0][1:])
  for i,im in enumerate(imgs[0]):assert np.array_equal(np.array(im)[:,:,3],np.array(load(pp/parent['animation']['files'][i]))[:,:,3])
  if e['kind']=='water':assert e['proof']['pebble_shift']['delta']==[4,-2]
  if e['kind']=='lava':
   wet=np.array(imgs[0][0])[:,:,3]>0
   for im in imgs[1]:assert not np.any(np.array(im)[wet,3])
 records.append({'id':e['id'],'opaque_all_phases':True,'ora_and_png_match':True,'specific_effect_checks':True})
report={'base_variants':len(base['scenes']),'additional_variants':len(extra['scenes']),'native_color_transformed_frames_verified':native_total,'additional_animation_layer_pngs':extra_total,'records':records,'runtime_validated':False,'browser_gpu_validated':False};(O/'verification.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k!='records'})
