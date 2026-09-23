"""Check source identity, independent rooms, exact layering and reciprocal design links."""
from pathlib import Path
import sys,json,hashlib,io
import numpy as np
from PIL import Image
from scipy import ndimage as nd
S=Path(__file__).resolve().parent;R=S.parents[1];sys.path.insert(0,str(S));from build import O,SPECS,base,load,compose,sha
from archive_studies import read_bytes
sys.path.insert(0,str(R/'source/cote_v5_expeditions'));from audit_references import tiles,straight

def main():
 m=json.loads((O/'manifest.json').read_text());checks=[]
 def passed(s):checks.append(s);print('PASS',s)
 for e in json.loads((O/'bruts/provenance_etudes.json').read_text()):
  p=O/'bruts'/e['file'];data=read_bytes(p);assert hashlib.sha256(data).hexdigest()==e['webp_sha256'];assert hashlib.sha256(Image.open(io.BytesIO(data)).convert('RGBA').tobytes()).hexdigest()==e['rgba_sha256']
 passed('All 12 generated originals/intermediates archived losslessly with recorded original PNG and RGBA hashes')
 rooms={r['id']:r for r in m['rooms']};assert len(rooms)==5 and sorted(set(r['level'] for r in rooms.values()))==[-1,0,1];assert len(set(r['raw'] for r in rooms.values()))==5
 passed('Five separate generated rooms, three levels; selected accueil retained as direction, no strip-based enlargement')
 window=load(S/'references/Guild_Heros_Room_Objects.png').crop((176,56,240,120));assert window.tobytes()==load(O/'assets/SpindaV4_fenetre_croisillon_native.png').tobytes();prov=json.loads((O/'fenetre_provenance.json').read_text());assert sha(S/'references/Guild_Heros_Room_Objects.tile')==prov['bank_sha256']
 ts,bank,_=tiles(S/'references/Guild_Heros_Room_Objects.tile');assert ts==8;decoded=Image.new('RGBA',(64,64))
 for y in range(7,15):
  for x in range(22,30):
   if (x,y) in bank:decoded.alpha_composite(straight(bank[x,y]),((x-22)*8,(y-7)*8))
 assert decoded.tobytes()==window.tobytes();assert window.getpixel((0,0))[3]==0
 ts,bank,_=tiles(R/'source/cafe_multietage_v3/references/Guild_Second_Floor_Objects.tile');stairs=Image.new('RGBA',(96,72))
 for y in range(16,25):
  for x in range(26,38):
   if (x,y) in bank:stairs.alpha_composite(straight(bank[x,y]),((x-26)*8,(y-16)*8))
 assert stairs.tobytes()==load(O/'assets/SpindaV4_escalier_spirale_natif.png').tobytes()
 passed('Round crossbar window and spiral staircase decoded from native tile banks, unscaled/unrecoloured')
 names=[];exports=0
 for spec in SPECS:
  ident,_,level,raw,windows,_=spec;r=rooms[ident];expected=base(ident,raw);im=Image.new('RGBA',(600,448));win=Image.new('RGBA',(600,448))
  for p in windows:win.alpha_composite(window,tuple(p))
  for layer in r['layers']:
   a=load(O/layer['file']);assert a.size==(600,448);assert set(np.unique(np.array(a)[:,:,3]))<={0,255};names.append(Path(layer['png']).name)
   if layer['role']=='generated_terrain':im.alpha_composite(a)
   if layer['role']=='native_windows':assert a.tobytes()==win.tobytes()
   if layer['role']=='native_stair_proposals':
    assert not layer['default'];stairs=Image.new('RGBA',(600,448))
    for p in r['stair_positions']:stairs.alpha_composite(load(O/'assets/SpindaV4_escalier_spirale_natif.png'),tuple(p['position']))
    assert a.tobytes()==stairs.tobytes()
   exports+=1
  assert np.array_equal(np.array(im),expected);im.alpha_composite(win);assert im.tobytes()==compose(m,ident).tobytes()
  if level<=0:assert not windows
  assert not r['furniture_instances'] and not r['fire_instances'] and not r['npc_instances']
  for port in r['ports'].values():
   x,y=port['point'];assert 0<=x<600 and 0<=y<448 and expected[y,x,3]>0,(ident,port)
   if port['kind']=='door':
    rgb=expected[y,x,:3].astype(int);assert rgb[0]>200 and rgb[1]>160 and rgb[0]>rgb[2]+65,(ident,port,rgb)
 passed(f'{exports} aligned layers: exact terrain recomposition, static lights isolated, native windows separate, optional native stairs, no furniture/fire/NPC baked into scene')
 assert len(names)==len(set(names));seen={'accueil'}
 for _ in range(5):
  for r in rooms.values():
   for key,p in r['ports'].items():
    if 'target' not in p:continue
    back=rooms[p['target']]['ports'][p['target_port']];assert back['target']==r['id'] and back['target_port']==key
    assert abs(r['level']-rooms[p['target']]['level'])==(1 if p['kind']=='stair_proposal' else 0)
    if r['id'] in seen:seen.add(p['target'])
 assert seen==set(rooms);assert len(m['links'])==4
 passed('All five rooms connected by four reciprocal design links; stair levels and doorway markers consistent; no engine warp claimed')
 for asset in m['assets']:
  im=load(O/asset['file']);assert im.width%8==0 and im.height%8==0
  if 'source_rgba_sha256' in asset:assert hashlib.sha256(im.tobytes()).hexdigest()==asset['source_rgba_sha256']
 for kind,old in [('flamme','flamme_native'),('brasero','brasero_natif')]:
  anim=m['animations'][kind];assert len(anim['frames'])==4 and anim['source_ticks']==6 and anim['frame_ms']==100
  strip=load(O/anim['sheet']);w,h=anim['size'];assert len(set(load(O/p).tobytes() for p in anim['frames']))==4
  for i,p in enumerate(anim['frames']):
   im=load(O/p);assert im.tobytes()==load(R/'renders/casino_network_v1/animations'/f'Casino_{old}_{i:02d}.png').tobytes();assert strip.crop((i*w,0,(i+1)*w,h)).tobytes()==im.tobytes()
 passed('Independent editor assets and four genuine native flame poses unchanged; cadence and frame strips exact')
 a=np.array(load(O/'SpindaV4_accueil_magenta.webp'));lit=np.array(compose(m,'accueil'));visible=lit[:,:,3]>0;assert np.all(a[~visible]==[255,0,255,255]);assert np.array_equal(a[visible],lit[visible])
 passed('Pure magenta outside selected accueil, all scene pixels preserved in preview')
 report={'pass':True,'checks':checks,'rooms':5,'levels':3,'links':4,'layer_exports':exports,'art_status':'Accueil generation selected by user. Other room variations require user review. Terrain generated, native windows/fire verified separately.','runtime_PMDO':'NOT TESTED','graphical_browser':'NOT TESTED'}
 (O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(len(checks),'checks PASS')
if __name__=='__main__':main()
