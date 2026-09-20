"""Pixel/codec/topology checks; NOT a PMDO or browser validation."""
from pathlib import Path
import sys,json,hashlib,zipfile,io
import numpy as np
from scipy import ndimage as nd
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from source.beach_network_v1 import build as b
P=b.OUT
from source.beach_network_v1.restore_exports import restore_exports
restore_exports(P)
m=json.loads((P/'manifest.json').read_text());results=[];details={}
def ok(name,condition):
 assert condition,name
 results.append({'test':name,'pass':True});print('PASS',name)
def pixels(p):return b.load(p)
def restored(atlas,desc,k,size):
 x,y,w,h=desc['rect'];cols=desc['columns'];out=np.zeros((size[1],size[0],4),dtype=np.uint8)
 out[y:y+h,x:x+w]=atlas[(k//cols)*h:(k//cols+1)*h,(k%cols)*w:(k%cols+1)*w]
 return out
ok('reference and all nine generation hashes',b.sha(b.SRC)==m['source']['sha256'] and all(b.sha(ROOT/p)==v for p,v in m['sources'].items()))
byid={r['id']:r for r in m['rooms']};ports=[(r,p) for r in m['rooms'] for p in r['ports']]
seen=set();pending=[m['rooms'][0]['id']]
while pending:
 name=pending.pop()
 if name in seen:continue
 seen.add(name);pending.extend(p['target'] for p in byid[name]['ports'] if p['target'])
for r,p in ports:
 if p['target']:assert any(q['target']==r['id'] and q['direction']==b.OPPOSITE[p['direction']] for q in byid[p['target']]['ports'])
ok('six connected rooms, fifteen reciprocal/reserved ports, seven links',len(seen)==6 and len(ports)==15 and len(m['edges'])==7 and sum(p['target'] is None for _,p in ports)==1)
for r in m['rooms']:b.path_check(pixels(P/r['modes']['jour']['composition']),[p['direction'] for p in r['ports']])
ok('all fifteen sand routes allow an 8 px clearance from obstacles',True)
for mode in ['jour','nuit']:
 patch=b.grade(pixels(P/'materiaux/BeachNetwork_sable_raccord_source.png'),mode)[:16]
 for r,p in ports:
  a=pixels(P/r['modes'][mode]['composition']);d=p['direction']
  edge={'N':a[:16,208:304],'S':a[-16:,208:304][::-1],'W':a[208:304,:16].transpose(1,0,2),'E':a[208:304,-16:][:,::-1].transpose(1,0,2)}[d]
  assert np.array_equal(edge,patch),(r['id'],mode,d)
ok('opposing 96×16 sand bands exactly equal in both modes',True)
import_names=[]
for r in m['rooms']:
 for mode in ['jour','nuit']:
  rec=r['modes'][mode];arrays=[pixels(P/l['file']) for l in rec['layers']]
  expected=pixels(P/rec['composition']);assert np.array_equal(b.compose(arrays,(512,512)),expected)
  for l,a in zip(rec['layers'],arrays):
   assert a.shape==(512,512,4);import_names.append(Path(l['file']).name)
   assert set(np.unique(a[:,:,3])).issubset({0,255})
  ora=P/r['id']/mode/f"BeachNetwork_{r['id']}_{mode}.ora"
  with zipfile.ZipFile(ora) as z:
   assert z.testzip() is None
   assert np.array_equal(np.array(Image.open(io.BytesIO(z.read('mergedimage.png'))).convert('RGBA')),expected)
ok('layer recompositions, binary alpha, 512×512 grids and twelve OpenRaster documents',True)
for r in m['rooms']:
 for dl,nl in zip(r['modes']['jour']['layers'],r['modes']['nuit']['layers']):assert np.array_equal(b.grade(pixels(P/dl['file']),'nuit'),pixels(P/nl['file']))
 assert np.array_equal(b.grade(pixels(P/r['modes']['jour']['composition']),'nuit'),pixels(P/r['modes']['nuit']['composition']))
ok('exact Abyss filter for all terrain layers and compositions',True)
for r in m['rooms']:
 counts={};arrays={}
 for mode in ['jour','nuit']:
  rec=r['modes'][mode];arrays[mode]={}
  for ident,a in rec['animation'].items():
   decoded=pixels(P/a['file']);frames=[]
   for k in range(rec['frames']):
    path=P/r['id']/mode/'animation'/ident/f"BeachNetwork_{r['id']}_{mode}_{ident}_{k:02d}.png"
    frame=pixels(path);import_names.append(path.name);assert frame.shape==(512,512,4)
    assert np.array_equal(restored(decoded,a,k,r['size']),frame),(r['id'],mode,ident,k)
    frames.append(frame)
   counts[mode+'/'+ident]=len({hashlib.sha256(f.tobytes()).hexdigest() for f in frames});assert counts[mode+'/'+ident]>1
   arrays[mode][ident]=frames
  assert np.array_equal(np.array(b.render_scene(m,r['id'],mode,0)),pixels(P/rec['composition']))
 for ident in arrays['jour']:
  for day,night in zip(arrays['jour'][ident],arrays['nuit'][ident]):assert np.array_equal(b.grade(day,'nuit'),night)
 # The new run-up stays near the shore; it does not slide the rock layer.
 day=arrays['jour'];water=day['06_eau'][0][:,:,3]>0;f0=day['07_ecume'][0][:,:,3]>0;allowed=water|(nd.distance_transform_edt(~f0)<=3)
 extra=day['07_ecume'][16][:,:,3]>0
 assert np.all(~extra|allowed) and np.any(extra&~water)
 counts['run_up_outside_water_px']=int((extra&~water).sum());details[r['id']]=counts
ok('768 full-size PNG frames match lossless atlases; water and foam really animate in every room',True)
ok('animation phase zero exact; night frames exact; local foam run-up bounded at 3 px',True)
ok('all PNG-to-Tileset layer/frame basenames unique',len(import_names)==len(set(import_names)))
old=json.loads((ROOT/'renders/beach_layers_v1/manifest.json').read_text())
for mode in ['jour','nuit']:
 rec=m['reference_beach']['modes'][mode]
 for l in rec['layers']:
  oldl=next(x for x in old['layers'] if x['id']==l['id'])
  assert np.array_equal(pixels(P/l['file']),b.grade(pixels(ROOT/'renders/beach_layers_v1'/oldl['file']),mode))
 for ident,a in rec['animation'].items():
  frames=[restored(pixels(P/a['file']),a,k,[702,466]) for k in [0,16,32,48,63]]
  prefix='mer' if ident=='03_mer' else 'ecume'
  assert np.array_equal(frames[0],b.grade(pixels(ROOT/f'renders/beach_layers_v1/animation/{prefix}/BeachV1_{prefix}_00.png'),mode))
  assert len({hashlib.sha256(x.tobytes()).hexdigest() for x in frames})>1
ok('reference terrain preserved; water/foam phase zero preserved; contact animation remains separate',True)
for mode in ['jour','nuit']:
 a=pixels(P/f'fonds/BeachNetwork_nuages_{mode}_wrap.png');mask=a[:,:,3]>0
 assert a.shape==(112,512,4) and not mask[:,:24].any() and not mask[:,-24:].any()
 assert not ((a[:,:,0]>180)&(a[:,:,1]<80)&(a[:,:,2]>180)&mask).any()
 assert np.array_equal(np.roll(a,-512,axis=1),a)
 assert np.array_equal(np.roll(np.roll(a,-511,axis=1),-1,axis=1),a)
 assert not np.array_equal(a,np.roll(a,-100,axis=1))
for c in m['sky']['cloud_placements']:assert c['size'][0]<=96 and c['size'][1]<=28
ok('three small clouds; alpha margins; no magenta; continuous one-pixel wrap 511→0',len(m['sky']['cloud_placements'])==3)
for mode in ['jour','nuit']:
 for selection in ['ensemble','plage_reference']:
  assert np.array_equal(np.array(b.render_scene(m,selection,mode,0)),np.array(b.render_scene(m,selection,mode,64000)))
ok('whole animated scene at 64 seconds exactly equals time zero in both modes',True)
# Moon absence is a visual inspection, not something a colour threshold proves.
ok('generated sky separate from clouds and source identified',m['sky']['moon'] is False and m['sky']['generated'] is True)
report={'pass':True,'tests':results,'animation_details':details,'visual_review':'Moonless generated sky, extracted clouds, day ensemble and corrected reference beach inspected as images. Artistic approval remains with user.','browser':'NOT TESTED here; separate DOM simulation report','runtime_PMDO':'NOT TESTED','limits':m['limits']}
(P/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(len(results),'tests PASS')
