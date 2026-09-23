"""Native-pixel, layout and source checks. Does not start or validate PMDO."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
from scipy import ndimage as nd
HERE=Path(__file__).resolve().parent;R=HERE.parents[1];sys.path.insert(0,str(HERE));from build import O,S,SIZE,geometry,keyed_native,load,sha
sys.path.insert(0,str(R/'source/cote_v5_expeditions'));from audit_references import tiles,straight

def main():
 m=json.loads((O/'manifest.json').read_text());checks=[]
 def passed(text):checks.append(text);print('PASS',text)
 for item in m['sources']:assert sha(R/item['file'])==item['sha256']
 assert m['source_commit']=='da6c2130d641507447e6386a5e47a296e8cb4c71'
 passed('Pinned native cafe Ground and five tile banks retain their source hashes')
 # Decode each actual native bank; do not trust a generated colour reference.
 for suffix in ['Base','Objects','Objects_Under','Objects_Over','Objects_Fringe']:
  name='Metano_Town_Cafe_'+suffix;size,bank,_=tiles(S/(name+'.tile'));assert size==8
  expected=load(S/(name+'.png'));rebuild=Image.new('RGBA',expected.size)
  for (x,y),tile in bank.items():rebuild.alpha_composite(straight(tile),(x*8,y*8))
  assert rebuild.tobytes()==expected.tobytes(),name
 passed('All five decoded cafe PNG sheets exactly match the native tile payloads')
 a,sx,sy=geometry();raw=np.array(load(S/'Metano_Town_Cafe_Base.png'));visible=a[:,:,3]>0
 assert np.array_equal(a[visible],raw[sy[visible],sx[visible]])
 assert np.array_equal(a,np.array(load(O/'CafeHalcyon_terrain_transparent.png')))
 assert a.shape==(576,840,4);assert round(840*576/(456*320),4)==m['canvas_area_ratio']
 passed('Every visible terrain RGBA pixel matches its recorded native source coordinate; no recolour/resampling')
 assert np.array_equal(a[:224,:224],keyed_native()[:224,:224])
 assert np.array_equal(a[:224,608:],keyed_native()[:224,224:])
 passed('Original north corners preserved intact; expansion inserts complete 64px bands')
 comp=Image.new('RGBA',SIZE);coverage=np.zeros((576,840),np.uint8)
 for l in m['layers']:
  im=load(O/l['file']);assert im.size==SIZE;assert l['origin']==[0,0] and l['role']=='terrain';assert set(np.unique(np.array(im)[:,:,3]))<={0,255};coverage+=(np.array(im)[:,:,3]>0).astype(np.uint8);comp.alpha_composite(im)
 assert comp.tobytes()==Image.fromarray(a).tobytes();assert np.array_equal(coverage,visible.astype(np.uint8))
 passed('Five aligned, non-overlapping alpha layers exactly recompose the terrain')
 mag=np.array(load(O/'CafeHalcyon_terrain_magenta.png'));assert np.all(mag[~visible]==[255,0,255,255]);assert np.array_equal(mag[visible],a[visible]);assert np.all(mag[:,:,3]==255)
 passed('Opaque #FF00FF exterior, no magenta alteration of any visible native pixel')
 floor=np.array(Image.open(O/'guides/CafeHalcyon_surface_libre.png'))>0
 assert nd.label(floor)[1]==1
 cells=np.flatnonzero(floor[-1]);assert np.array_equal(cells,np.arange(456,512));assert np.array_equal(np.flatnonzero(visible[-1]),np.arange(454,514))
 clearance=nd.distance_transform_edt(np.pad(floor,1))[1:-1,1:-1]>=8;labels,_=nd.label(clearance);points=[m['south_entrance']['point'],[200,160],[640,160],[160,360],[688,424]];components=[int(labels[y,x]) for x,y in points];assert components[0]>0 and len(set(components))==1
 passed('Exactly one 56px south floor exit; room and service areas connected with 8px clearance (guide, not engine collisions)')
 for z in m['reserved_zones']:
  x,y,w,h=z['rect'];assert floor[y:y+h,x:x+w].all()
 assert not m['placed_furniture'] and not m['placed_fire'] and not m['npc_entities'];assert len(m['layers'])==5
 passed('Reserved rectangles lie on free floor; no furniture, fire or NPC instance in the terrain')
 for item in m['furniture']:
  if 'source_rgba_sha256' in item:assert hashlib.sha256(load(O/item['file']).tobytes()).hexdigest()==item['source_rgba_sha256']
  assert item['placement'] is None
 passed('Four separate cafe furniture sheets retain exact source pixels; no placement coordinates applied')
 prov=json.loads((O/'flammes_provenance.json').read_text());assert sha(R/prov['source_map'])==prov['source_map_sha256'];assert sha(R/prov['source_bank'])==prov['source_bank_sha256'];tile_size,bank,_=tiles(R/prov['source_bank']);assert tile_size==8
 for k in range(4):
  expected=Image.new('RGBA',(32,64))
  for entry in prov['source_tracks']:
   track=entry['track'];assert track['FrameLength']==6;assert len(track['Frames'])==4;f=track['Frames'][k]
   if not f['Sheet']:continue
   assert f['Sheet']=='Ledian_Dojo_Animated';xy=f['TexLoc'];x,y=entry['map_tile'];expected.alpha_composite(straight(bank[xy['X'],xy['Y']]),((x-14)*8,(y-11)*8))
  assert load(O/m['animations']['brasero']['frames'][k]).tobytes()==expected.tobytes()
  flame=load(O/m['animations']['flamme']['frames'][k]);assert flame.tobytes()==expected.crop((0,0,32,40)).tobytes()
  support=load(O/'mobilier/CafeHalcyon_support_brasero.png');support.alpha_composite(flame);assert support.tobytes()==expected.tobytes()
 for kind,anim in m['animations'].items():
  strip=load(O/anim['sheet']);w,h=anim['frame_size'];assert strip.size==(4*w,h);assert anim['source_ticks']==6 and anim['frame_ms']==100
  assert len(set(load(O/p).tobytes() for p in anim['frames']))==4
  for i,p in enumerate(anim['frames']):assert strip.crop((i*w,0,(i+1)*w,h)).tobytes()==load(O/p).tobytes()
 passed('Four real Ledian poses decoded from source tracks; strips, separate flames and support recompose exactly; 6 ticks per pose')
 names=[]
 for folder in ['calques','mobilier','animations']:
  for p in (O/folder).glob('*.png'):
   im=load(p);assert im.width%8==0 and im.height%8==0;assert p.stem.startswith('CafeHalcyon_');names.append(p.name.lower())
 assert len(names)==len(set(names))
 passed('Import sheets use unique basenames, native pixel scale and 8px-compatible dimensions')
 report={'pass':True,'checks':checks,'native_visible_pixels':int(visible.sum()),'terrain_size':list(SIZE),'native_pixel_scale':1,'movable_decor_placed':0,'npc_entities':0,'runtime_PMDO':'NOT TESTED','artistic_review':'Original and enlarged native compositions inspected as still images; no engine approval implied.'}
 (O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(len(checks),'checks passed')
if __name__=='__main__':main()
