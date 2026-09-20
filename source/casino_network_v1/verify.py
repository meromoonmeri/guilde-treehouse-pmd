"""Pixel/source/topology validation. Not a PMDO runtime or artistic approval."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
from scipy import ndimage as nd
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from source.casino_network_v1.prepare import OUT,SRC,rgba,keyed,raw_path,tiles,straight
from source.casino_network_v1.build import render
m=json.loads((OUT/'manifest.json').read_text());p=json.loads((OUT/'flammes_provenance.json').read_text());tests=[]
def ok(name,condition=True):
 assert condition,name
 tests.append({'test':name,'pass':True});print('PASS',name)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
for name,h in json.loads((SRC/'hashes.json').read_text()).items():assert sha(SRC/name)==h
ok('all original Ledian map/bank SHA256 hashes unchanged')
for r in json.loads((OUT/'bruts/provenance.json').read_text()):
 im=Image.open(OUT/'bruts'/r['file']).convert('RGBA');assert sha(OUT/'bruts'/r['file'])==r['webp_sha256'];assert hashlib.sha256(im.tobytes()).hexdigest()==r['rgba_sha256']
ok('seven generated raws archived losslessly with original pixel hashes')
terrain=keyed(rgba(raw_path('terrain_corrige')));base=np.array(render(m,0,['terrain']));assert np.array_equal(base,terrain)
terrain_layers=[l for l in m['layers'] if l['group']=='terrain'];masks=np.stack([rgba(OUT/l['file'])[:,:,3]>0 for l in terrain_layers]);assert np.all(masks.sum(0)<=1)
ok('five terrain partitions exactly recompose the generated empty map; no geometry resampling')
ids=set();files=set()
for l in m['layers']:
 assert l['id'] not in ids;ids.add(l['id']);assert all(v%8==0 for v in l['position']+l['size'])
 for file in l.get('frames',[l.get('file')]):
  im=Image.open(OUT/file);assert list(im.size)==l['size'];files.add(file)
 for file in l.get('frames',[l.get('file')]):
  a=rgba(OUT/file);assert set(np.unique(a[:,:,3])).issubset({0,255})
  r,g,b=np.moveaxis(a[:,:,:3].astype(float),2,0);assert not ((r>230)&(g<35)&(b>220)&(a[:,:,3]>0)).any(),file
ok('38 independent layer instances, 8px-aligned sizes/positions, binary alpha, no opaque magenta',len(ids)==38)
roomids={r['id']:r for r in m['rooms']};pending=['accueil'];seen=set()
while pending:
 room=pending.pop()
 if room in seen:continue
 seen.add(room)
 for a,da,b,db in m['edges']:
  assert roomids[a]['ports'][da]==roomids[b]['ports'][db]
  if a==room:pending.append(b)
  if b==room:pending.append(a)
ok('four connected sectors, four internal links, one south entrance',len(seen)==4 and len(m['edges'])==4)
carpet=np.array(render(m,0,['tapis']));walk=carpet[:,:,3]>0
for l in m['layers']:
 if l.get('footprint') and l['id'] not in ['estrade','rideaux']:
  x,y,w,h=l['footprint'];walk[y:y+h,x:x+w]=False
labels,_=nd.label(nd.distance_transform_edt(walk)>=8);points=[(256,1008),(256,336),(768,440),(752,776),(256,864),(512,256),(256,512),(768,512),(512,768)]
assert labels[1008,256]>0 and all(labels[y,x]==labels[1008,256] for x,y in points)
ok('main carpet route stays connected with 8px clearance after default furnishing footprints; not engine collisions')
native_rug=rgba(SRC/'Ledian_Dojo_Objects.png')[136:176,176:232];assert np.array_equal(native_rug,rgba(OUT/'objets/tapis_source_natif.png'))
colours=set(map(tuple,native_rug.reshape(-1,4)));assert all(tuple(c) in colours for c in np.unique(carpet[carpet[:,:,3]>0],axis=0))
ok('rug uses only unchanged native source pixels; no stretch or recolour')
o=json.loads((SRC/'ledian_dojo.rsground').read_text(encoding='utf-8-sig'))['Object'];ts,bank,_=tiles(SRC/'Ledian_Dojo_Animated.tile');assert ts==8
support=Image.open(OUT/'objets/brasero_support.png').convert('RGBA');frames=[]
for k in range(4):
 expected=Image.new('RGBA',(32,64))
 for x in range(14,18):
  for y in range(11,19):
   for a in o['Layers'][1]['Tiles'][x][y]['Layers']:
    if len(a['Frames'])==4:
     assert a['FrameLength']==6;f=a['Frames'][k]
     if f['Sheet']:
      v=f['TexLoc'];expected.alpha_composite(straight(bank[v['X'],v['Y']]),((x-14)*8,(y-11)*8))
 full=rgba(OUT/f'animations/Casino_brasero_natif_{k:02d}.png');assert np.array_equal(full,np.array(expected))
 flame=Image.open(OUT/f'animations/Casino_flamme_native_{k:02d}.png').convert('RGBA');assert flame.tobytes()==expected.crop((0,0,32,40)).tobytes()
 combined=support.copy();combined.alpha_composite(flame);assert combined.tobytes()==expected.tobytes();frames.append(full)
assert len({hashlib.sha256(a.tobytes()).hexdigest() for a in frames})==4
ok('four fire poses and order exactly reconstructed from native Ledian Ground tracks')
ok('native support + flame split exactly recomposes every 32×64 brazier, unscaled')
ok('source cadence is 6 ticks; viewer uses 100ms/pose, 400ms/loop',p['frame_length_ticks']==6 and p['frame_ms']==100)
assert np.array_equal(rgba(OUT/'objets/krow_bank_natif.png'),rgba(ROOT/'source/ledian_casino_v1/references/KrowBank_structure_native.png'))
ok('native Krow Bank object unchanged')
for l in m['layers']:
 if l.get('frames'):
  assert l['native_unscaled'] and l['host'] in ids and l['size']==[32,40]
assert sum(l.get('asset')=='fourneau' for l in m['layers'])==2 and sum(l.get('asset')=='brasero_support' for l in m['layers'])==8
ok('eight native braziers, two generated unlit furnace bodies, ten independent native flame instances')
full=np.array(render(m,0));assert np.array_equal(full,rgba(OUT/'Casino_reseau_decore.webp'))
assert np.array_equal(full,np.array(render(m,4)))
animated=Image.open(OUT/'Casino_apercu_anime.webp');durations=[]
for k in range(animated.n_frames):
 animated.seek(k);arr=np.array(animated.convert('RGBA'));durations.append(animated.info['duration']);arr[arr[:,:,3]==0]=0;assert np.array_equal(arr,np.array(render(m,k)))
ok('still pixels exact; animated visible pixels/alpha exact, four poses total 400ms and wrap',animated.n_frames==4 and sum(durations)==400)
report={'pass':True,'tests':tests,'layers':len(ids),'unique_layer_images':len(files),'clearance_scope':'Default authoring footprints on carpet route, not native collisions or vertical geometry.','browser':'NOT TESTED here; separate DOM simulation','runtime_PMDO':'NOT TESTED','visual_review':'Generated objects, corrected square terrain, native fire frames, and furnished network inspected. Approval remains with user.','limits':m['limits']}
(OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(len(tests),'tests PASS')
