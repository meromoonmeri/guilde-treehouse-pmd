from pathlib import Path
import io,json,hashlib,struct,sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'renders/caps_terrasses_v3'
sys.path.insert(0,str(ROOT/'source/cote_v4_abyss'))
from night import night

def idat(p):
 b=p.read_bytes();i=8;out=[]
 while i<len(b):
  n=int.from_bytes(b[i:i+4],'big');typ=b[i+4:i+8]
  if typ==b'IDAT':out.append(b[i+8:i+8+n])
  i+=12+n
 return b''.join(out)

def main():
 m=json.loads((OUT/'manifest.json').read_text());z0=json.loads((ROOT/'sprites/cote_v2/manifest.json').read_text())['zones'][0];folder=ROOT/'sprites/cote_v2'/z0['id']
 base=Image.open(folder/z0['files']['sea'][0]);indices=np.array(base);alpha=base.info['transparency'];cycle=z0['cycle_indices'];other=[i for i in range(256) if i not in cycle]
 startpal=np.array(base.getpalette()).reshape(256,3);palettes=[]
 for i in range(64):
  p=OUT/'ocean'/f'jour_{i:02d}.png';im=Image.open(p);assert im.mode=='P' and np.array_equal(np.array(im),indices);assert im.info['transparency']==alpha
  pal=np.array(im.getpalette()).reshape(256,3);assert np.array_equal(pal[other],startpal[other]);palettes.append(pal)
  if i%8==0:assert im.convert('RGBA').tobytes()==Image.open(folder/z0['files']['sea'][i//8]).convert('RGBA').tobytes()
  noct=Image.open(OUT/'ocean'/f'nuit_{i:02d}.png');assert np.array_equal(np.array(noct),indices) and noct.info['transparency']==alpha
  # Compare displayed colors; RGB behind fully transparent indexed pixels is irrelevant.
  expected=np.array(night(im.convert('RGBA')));actual=np.array(noct.convert('RGBA'));mask=expected[:,:,3]>0;assert np.array_equal(expected[mask],actual[mask])
 assert len({idat(p) for p in (OUT/'ocean').glob('jour_*.png')})==1
 assert len({a.tobytes() for a in palettes})==64
 assert max(np.abs(palettes[(i+1)%64].astype(int)-palettes[i]).max() for i in range(64))==7
 for z in m['zones']:
  raw=Image.open(OUT/z['source']).convert('RGBA');a=np.array(raw);key=(a[:,:,0]>210)&(a[:,:,1]<70)&(a[:,:,2]>210);a[key]=0
  expected=Image.new('RGBA',raw.size);expected.paste(Image.fromarray(a),tuple(z['offset_px']));terrain=Image.open(OUT/z['terrain']).convert('RGBA')
  assert expected.tobytes()==terrain.tobytes();assert night(terrain).tobytes()==Image.open(OUT/z['night']).convert('RGBA').tobytes();assert all(v%8==0 for v in terrain.size)
  assert hashlib.sha256((OUT/z['source']).read_bytes()).hexdigest()==z['source_sha256']
 count=0
 for p in OUT.rglob('*.png'):
  with Image.open(p) as im:im.verify()
  count+=1
 result={'status':'PASS','generated_foreground_layers':6,'night_terrain_layers':6,'png_files_decoded':count,'retained_day_terrain_pixels_unchanged':True,'terrain_resampled':False,'canvases_divisible_by_8':True,'indexed_sea_day_night_phases':128,'fixed_indices_and_alpha':True,'identical_IDAT_all_day_frames':True,'original_8_keyframes_preserved':True,'night_displayed_colors_match_abyss':True,'cyclic_max_rgb_step_including_last_to_first':7,'old_max_rgb_step':56,'loop_ms':3200,'native_mod_patched':False,'new_gpu_validation':False}
 (ROOT/'source/caps_terrasses_v3/verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
