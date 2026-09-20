"""Asset/topology tests, not artistic approval or PMDO validation."""
from pathlib import Path
import sys,json,hashlib,tempfile
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from source.beach_extension_v2 import build as e
from source.beach_network_v1 import build as b
from source.beach_network_v1.restore_exports import restore_exports
restore_exports(e.OLD)
P=e.OUT;m=json.loads((P/'manifest.json').read_text());tests=[];stats={}
def ok(name,condition=True):
 assert condition,name
 tests.append({'test':name,'pass':True});print('PASS',name)
def load(path):return b.load(P/path)
def decoded(a,size=[512,512]):
 atlas=load(a['file']);x,y,w,h=a['rect'];result=[]
 for k in range(a['frames']):
  out=np.zeros((size[1],size[0],4),dtype=np.uint8);cx=k%a['columns']*w;cy=k//a['columns']*h;out[y:y+h,x:x+w]=atlas[cy:cy+h,cx:cx+w];result.append(out)
 return result
def band(a,d):return {'N':a[:16,208:304],'S':a[-16:,208:304][::-1],'W':a[208:304,:16].transpose(1,0,2),'E':a[208:304,-16:][:,::-1].transpose(1,0,2)}[d]
assert b.sha(b.SRC)==m['source']['sha256']
for name,h in m['preserved_v1_hashes'].items():assert b.sha(e.OLD/name)==h,name
ok('V1 source, six maps, reference scene, sky, clouds and delivery archive unchanged')
for raw in m['generation_archive']:
 f=P/'bruts'/raw['file'];assert b.sha(f)==raw['archived_webp_sha256'];assert hashlib.sha256(b.load(f).tobytes()).hexdigest()==raw['decoded_rgba_sha256']
ok('five original generations archived with exact decoded pixels, including corrected 07')
byid={r['id']:r for r in m['rooms']};ports=[(r,p) for r in m['rooms'] for p in r['ports']];seen=set();todo=['01_anse_ouest']
while todo:
 name=todo.pop()
 if name in seen:continue
 seen.add(name);todo.extend(p['target'] for p in byid[name]['ports'] if p['target'])
for r,p in ports:
 if p['target']:assert any(q['direction']==b.OPPOSITE[p['direction']] and q['target']==r['id'] for q in byid[p['target']]['ports'])
ok('10 connected maps, 12 reciprocal links, 27 ports, exactly 3 free extensions',len(seen)==10 and len(m['edges'])==12 and len(ports)==27 and sum(p['target'] is None for _,p in ports)==3)
ok('05 south now connects to 07 north only in the combined manifest',next(p for p in byid['05_carrefour_croix']['ports'] if p['direction']=='S')['target']=='07_carrefour_dunes')
for r in m['rooms']:b.path_check(load(r['modes']['jour']['composition']),[p['direction'] for p in r['ports']])
ok('all 27 declared accesses connect to their centre with 8 px obstacle clearance')
for mode in ['jour','nuit']:
 patch=b.grade(b.load(b.SRC)[168:184,296:392],mode)
 for r,p in ports:assert np.array_equal(band(load(r['modes'][mode]['composition']),p['direction']),patch)
ok('all 96×16 port cores are pixel-identical, including the old/new seam, day and night')
new=[r for r in m['rooms'] if r['new']];names=[]
for r in new:
 for mode in ['jour','nuit']:
  rec=r['modes'][mode];layers=[load(l['file']) for l in rec['layers']]
  assert all(a.shape==(512,512,4) for a in layers)
  assert np.array_equal(b.compose(layers,(512,512)),load(rec['composition']))
  for l,a in zip(rec['layers'],layers):
   names.append(Path(l['file']).name);assert set(np.unique(a[:,:,3])).issubset({0,255})
 for dl,nl in zip(r['modes']['jour']['layers'],r['modes']['nuit']['layers']):assert np.array_equal(b.grade(load(dl['file']),'nuit'),load(nl['file']))
ok('80 new aligned PNG layers, binary alpha, exact recompositions, unique import names',len(names)==80 and len(names)==len(set(names)))
ok('exact Abyss grading on every new terrain layer')
palette=Image.open(b.SRC).convert('P');heights=b.wave_guide();total_rock_wetting=0
for r in new:
 raw=np.array(Image.open(P/'bruts'/r['raw']).convert('RGB').resize((512,512),Image.Resampling.NEAREST).quantize(palette=palette,dither=Image.Dither.NONE).convert('RGBA'))
 _,water,foam=b.classify(raw);render,_=b.animator(raw[:,:,:3],water,foam,heights);contact=b.contact_foam(raw[:,:,:3],water,foam)
 decoded_modes={mode:{ident:decoded(a) for ident,a in r['modes'][mode]['animation'].items()} for mode in ['jour','nuit']}
 counts={}
 for k in range(32):
  w,f=render(k*2);expected={'06_eau':w,'07_ecume':contact(f,k,32)}
  for mode in ['jour','nuit']:
   rec=r['modes'][mode]
   for ident in expected:assert np.array_equal(b.grade(expected[ident],mode),decoded_modes[mode][ident][k])
   if k==0:
    layers=[decoded_modes[mode][l['id']][0] if l['id'] in decoded_modes[mode] else load(l['file']) for l in rec['layers']]
    assert np.array_equal(b.compose(layers,(512,512)),load(rec['composition']))
 for ident,frames in decoded_modes['jour'].items():
  counts[ident]=len({hashlib.sha256(f.tobytes()).hexdigest() for f in frames});assert counts[ident]>1
 w0,f0=render(0);w64,f64=render(64);assert np.array_equal(w0,w64) and np.array_equal(contact(f0,0,32),contact(f64,32,32))
 rock=(raw[:,:,0].astype(float)>raw[:,:,1]*1.16)&(raw[:,:,1]<160);wet=(decoded_modes['jour']['07_ecume'][16][:,:,3]>0)&~water&rock
 counts['rock_contact_pixels_at_peak']=int(wet.sum());total_rock_wetting+=int(wet.sum());stats[r['id']]=counts
ok('512 new atlas frames equal expected animation pixels; every water and foam track changes')
ok('phase zero exact, 3.2-second cycle closed, 64-second common cycle closed')
ok('new independent foam deposits on rock contacts without moving rock layers',total_rock_wetting>0)
for key,layout in m['layouts'].items():
 im=np.array(e.composed_layout(m,key,'jour'));ox,oy=layout['origin']
 for r in e.layout_rooms(m,key):
  x=(r['position'][0]-ox)*512;y=(r['position'][1]-oy)*512;assert np.array_equal(im[y:y+512,x:x+512],load(r['modes']['jour']['composition']))
 if key=='reseau':assert not im[1024:,:512,3].any()
ok('both assembled layouts preserve all module pixels; two empty grid slots stay transparent')
with tempfile.TemporaryDirectory(dir=ROOT/'.cache') as tmp:
 dest=Path(tmp);(dest/'BeachNetwork_pack.zip').symlink_to(e.OLD/'BeachNetwork_pack.zip');count=restore_exports(dest);assert count==792
 for name in m['preserved_v1_hashes']:
  if (dest/name).exists() and name!='BeachNetwork_pack.zip':assert b.sha(dest/name)==b.sha(e.OLD/name)
ok('792 redundant V1 frame/ORA/composition files recover byte-exactly from preserved archive')
report={'pass':True,'tests':tests,'new_animation_detail':stats,'new_modules':4,'new_crossroads':3,'total_modules':10,'browser':'NOT TESTED here; separate DOM simulation','runtime_PMDO':'NOT TESTED','visual_review':'Four raw generations, corrected east exit of 07 and assembled network inspected. Not user approval.','limits':m['limits']}
(P/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(len(tests),'tests PASS')
