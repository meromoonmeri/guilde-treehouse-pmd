from pathlib import Path
import json,hashlib,xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'exports/vegetation_treehouse_v1';SRC=Path(__file__).parent

def verify():
 m=json.loads((OUT/'manifest.json').read_text());assert len(m['assets'])==8
 sheets=[Image.open(OUT/'tilesheets'/f'VT1_vegetation_phase_{f}.png').convert('RGBA') for f in range(4)]
 atlas=Image.open(OUT/'tilesheets/VT1_vegetation_animated_atlas.png').convert('RGBA');assert atlas.size==(512,64)
 checks=[]
 for f,im in enumerate(sheets):
  assert im.size==(128,64);assert im.tobytes()==atlas.crop((f*128,0,f*128+128,64)).tobytes()
 for asset in m['assets']:
  imgs=[Image.open(OUT/'plants'/f"VT1_{asset['id']}_phase_{f}.png").convert('RGBA') for f in range(4)];arrays=[np.array(im) for im in imgs]
  assert all(im.size==(32,32) for im in imgs)
  assert imgs[0].tobytes()==imgs[2].tobytes();assert len({im.tobytes() for im in imgs})==3
  protected=slice(26,32) if asset['anchor_mode']=='bottom' else slice(0,6)
  assert arrays[0][protected,:,3].any()
  for f,a in enumerate(arrays):
   assert np.isin(a[:,:,3],[0,255]).all();assert np.all(a[a[:,:,3]==0]==0)
   assert np.array_equal(a[protected],arrays[0][protected])
   assert not a[0,:,3].any() and not a[-1,:,3].any() and not a[:,0,3].any() and not a[:,-1,3].any(),'Plant hits frame edge'
   assert not np.any(np.all(a[:,:,:3]==[255,0,255],axis=2)&(a[:,:,3]>0))
   x,y,w,h=asset['rect'];assert imgs[f].tobytes()==sheets[f].crop((x,y,x+w,y+h)).tobytes()
  checks.append({'id':asset['id'],'unique_wind_drawings':3,'anchor_region_identical':True,'frame_edges_clear':True,'opaque_colors':len(set(map(tuple,np.concatenate([a[a[:,:,3]>0,:3] for a in arrays]))))})
 ts=ET.parse(OUT/'tilesheets/VT1_vegetation_8px.tsx').getroot();assert ts.get('tilewidth')=='8' and ts.get('tileheight')=='8' and ts.get('columns')=='64'
 tiles=ts.findall('tile');assert len(tiles)==128
 for tile in tiles:
  base=int(tile.get('id'));frames=tile.findall('./animation/frame');assert len(frames)==4
  for f,frame in enumerate(frames):assert int(frame.get('tileid'))==base+f*16 and int(frame.get('duration'))==m['tiled_duration_ms'][f]
 placements=json.loads((OUT/'placement_recipe.json').read_text());assert len(placements['objects'])==8
 for obj in placements['objects']:
  assert len(obj['cells'])==16
  for cell in obj['cells']:
   assert cell['duration_game_frames']==14
   for f,frame in enumerate(cell['frames']):
    assert frame['Sheet']==f'VT1_vegetation_phase_{f}'
    assert 0<=frame['TexLoc']['X']<16 and 0<=frame['TexLoc']['Y']<8
 for name,sha in m['source_hashes'].items():assert hashlib.sha256((SRC/'generation'/name).read_bytes()).hexdigest()==sha
 gifs=list((OUT/'review').glob('*.gif'));assert len(gifs)==11
 for p in gifs:
  with Image.open(p) as im:assert im.n_frames>=3 and im.info.get('loop')==0
 assert m['runtime_PMDO']=='NOT TESTED' and m['runtime_Tiled']=='NOT TESTED' and not m['art_approved']
 result={'technical_precheck':'PASS','assets':checks,'phase_sheets':4,'animated_8px_tiles':128,'tiled_frame_references_exact':True,'pmdo_placement_recipe_bounds_valid':True,'gif_count':11,'no_runtime_import_claim':True}
 (OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n');m['technical_precheck']='PASS';(OUT/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
 return result
if __name__=='__main__':print(verify()['technical_precheck'])
