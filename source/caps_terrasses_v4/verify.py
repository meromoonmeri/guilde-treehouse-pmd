from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent;OUT=ROOT/'renders/caps_terrasses_v4'
sys.path.insert(0,str(HERE));from build import lab,chroma
sys.path.insert(0,str(ROOT/'source/cote_v4_abyss'));from night import night
from sample import decode

def main():
 cfg=json.loads((HERE/'palette_canonique.json').read_text());manifest=json.loads((OUT/'manifest.json').read_text());visual=json.loads((HERE/'audit_visuel.json').read_text())
 for f in cfg['source_files']:assert hashlib.sha256((ROOT/f['path']).read_bytes()).hexdigest()==f['sha256']
 assert np.allclose(lab([[255,255,255],[0,0,0],[255,0,0]]),[[100,0,0],[0,0,0],[53.2408,80.0925,67.2032]],atol=.001)
 p=ROOT/'source/falaises_metano';meta=json.loads((p/'provenance.json').read_text());banks=[decode(p/'natifs'/f'Metano_Town_{n}.tile') for n in ['Base','Cliffs']]
 sheet=Image.new('RGBA',(max(a.shape[1] for a in banks),max(a.shape[0] for a in banks)))
 for a in banks:sheet.alpha_composite(Image.fromarray(a))
 colors=[]
 for n in ['herbe','roche','rebord','pied']:
  im=sheet.crop(meta['patches_from_composed_Base_and_Cliffs_xyxy_px'][n]);assert im.tobytes()==Image.open(p/'patches'/f'{n}.png').convert('RGBA').tobytes();a=np.array(im);colors.extend(a[a[:,:,3]==255,:3].tolist())
 shadow=cfg['patch_checks'][-1];x,y=shadow['source_pixel_xy'];assert banks[1][y,x].tolist()==[96,56,88,255];colors.append([96,56,88])
 pal=np.unique(np.array(colors,dtype='uint8'),axis=0);assert pal.tolist()==cfg['allowed_rgb'];allowed={tuple(c) for c in pal.tolist()};tree=cKDTree(lab(pal))
 for z in manifest['zones']:
  rawfile=OUT/z['raw'];assert hashlib.sha256(rawfile.read_bytes()).hexdigest()==z['raw_sha256'];raw=Image.open(rawfile).convert('RGBA');a=chroma(raw);mask=a[:,:,3]>0
  colors,inv=np.unique(a[mask,:3],axis=0,return_inverse=True);_,near=tree.query(lab(colors));a[mask,:3]=pal[near][inv]
  expected=Image.new('RGBA',raw.size);expected.paste(Image.fromarray(a),tuple(z['offset_px']));actual=Image.open(OUT/z['terrain']).convert('RGBA');assert expected.tobytes()==actual.tobytes()
  a=np.array(actual);mask=a[:,:,3]>0;assert {tuple(c) for c in np.unique(a[mask,:3],axis=0).tolist()}<=allowed;assert (a[~mask]==0).all();assert set(np.unique(a[:,:,3]))=={0,255};assert all(v%8==0 for v in actual.size)
  assert night(actual).tobytes()==Image.open(OUT/z['night']).convert('RGBA').tobytes()
  r=next(r for r in visual['entries'] if r['id']==z['id']);assert r['status']==z['visual_status']
 assert sum(z['visual_status']=='RETENU_VISUELLEMENT' for z in manifest['zones'])==8
 assert [z['id'][:2] for z in manifest['zones'] if z['visual_status']=='A_REGENERER']==['07','11']
 count=0
 for f in OUT.rglob('*.png'):
  with Image.open(f) as im:im.verify()
  count+=1
 result={'technical_status':'PASS','artistic_status':'PARTIAL: 8 retained, 07 and 11 rejected','generated':10,'retained':8,'to_regenerate':2,'canonical_allowed_colors':len(pal),'all_opaque_day_terrain_pixels_in_native_palette':True,'out_of_palette_pixels':0,'canonical_patches_redecoded_and_equal':4,'extra_shadow_verified_in_native_cliff_bank':True,'Lab_reference_values_tested':True,'nearest_palette_mapping_recomputed':True,'night_matches_abyss_filter':10,'resampling_of_terrain':False,'pngs_decoded':count,'canonical_tile_identity_proved':False,'engine_or_gpu_tested':False}
 (HERE/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
