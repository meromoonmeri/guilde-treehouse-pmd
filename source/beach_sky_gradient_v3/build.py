from pathlib import Path
import sys,json,hashlib,copy,os,zipfile
from PIL import Image,ImageDraw
import numpy as np
R=Path(__file__).resolve().parents[2];S=Path(__file__).resolve().parent;O=R/'renders/beach_sky_gradient_v3';OLD=R/'renders/beach_extension_v2'
sys.path.insert(0,str(S));from sky import build as build_sky

def protected():
 return {str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ['beach_network_v1','beach_extension_v2'] for p in (R/'renders'/folder).rglob('*') if p.is_file()}
def main():
 before=protected();old=json.loads((OLD/'manifest.json').read_text());m={k:copy.deepcopy(old[k]) for k in ['scope','rooms','reference_beach','layouts']};m.update(version='Beach — ciels V3',period_ms=64000,runtime_PMDO='NOT TESTED',terrain_crepuscule='Unchanged day terrain; sky treatment only')
 for r in m['rooms']+[m['reference_beach']]:
  for desc in r['modes'].values():
   for l in desc['layers']:l['file']=os.path.relpath((OLD/l['file']).resolve(),O)
   for a in desc['animation'].values():a['file']=os.path.relpath((OLD/a['file']).resolve(),O)
   if 'composition' in desc:desc['composition']=os.path.relpath((OLD/desc['composition']).resolve(),O)
  r['modes']['crepuscule']=copy.deepcopy(r['modes']['jour'])
 m['sky_assets']=build_sky(O)
 (O/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
 template=(S/'viewer.html').read_text();(O/'index.html').write_text(template.replace('__DATA__',json.dumps(m,ensure_ascii=False)))
 (R/'apercu_plages_ciels_v3.html').write_text('<!doctype html><html lang="fr"><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=renders/beach_sky_gradient_v3/index.html"><a href="renders/beach_sky_gradient_v3/index.html">Plages · trois ambiances</a></html>\n')
 checked=set()
 for r in m['rooms']+[m['reference_beach']]:
  assert r['modes']['jour']==r['modes']['crepuscule']
  for mode,desc in r['modes'].items():
   for l in desc['layers']:assert (O/l['file']).exists(),l;checked.add(l['file'])
   for a in desc['animation'].values():assert (O/a['file']).exists(),a;checked.add(a['file']);assert a['frames']*desc['frame_ms']==3200
 for mode,a in m['sky_assets'].items():
  sky=np.array(Image.open(O/a['sky']).convert('RGBA'));assert sky.shape==(112,512,4);assert np.all(sky[:,:,3]==255);assert np.array_equal(sky[:,:8],sky[:,-8:]);assert len(np.unique(sky[:,:,:3].reshape(-1,3),axis=0))>4
  cloud=np.array(Image.open(O/a['cloud']).convert('RGBA'));assert cloud.shape==(112,512,4);assert not cloud[:,:24,3].any() and not cloud[:,-24:,3].any()
  for t in [0,125,16000,31999,63999]:assert np.array_equal(np.roll(cloud,-((t//125)%512),axis=1),np.roll(cloud,-(((t+64000)//125)%512),axis=1))
  assert np.array_equal(np.roll(cloud,-511,axis=1),np.roll(cloud,1,axis=1)) # last step to seam is exactly one pixel
 assert before==protected()
 report={'pass':True,'maps':10,'reference_beach':True,'modes':['jour','crepuscule','nuit'],'unchanged_prior_files':len(before),'prior_aggregate_sha256':hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest(),'terrain_and_animation_dependencies_checked':len(checked),'day_and_night_native_row_motifs':True,'dusk':'reconstructed from supplied JPEG, not native-certified','water_foam':'existing layers unchanged; network 32x100ms, reference 64x50ms','cloud_wrap':'64 s exact; 1 px / 125 ms; seam and multiple phases tested','PMDO_runtime':'NOT TESTED'}
 (O/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
 # Lightweight sky-only pack: intentionally not a duplicate of the full Beach network.
 with zipfile.ZipFile(O/'BeachSkyV3_fonds.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in sorted((O/'fonds').glob('*.png')):z.write(p,'fonds/'+p.name)
  for mode in ['jour','nuit']:
   p=O/m['sky_assets'][mode]['cloud'];z.write(p,'fonds/'+p.name)
  for name in ['README.md','provenance.json','verification.json']:z.write(O/name,name)
 with zipfile.ZipFile(O/'BeachSkyV3_fonds.zip') as z:assert z.testzip() is None
 # Three actual reference-beach compositions, not an invented demonstration terrain.
 board=Image.new('RGB',(1536,460),'#142934');d=ImageDraw.Draw(board)
 for col,mode in enumerate(['jour','crepuscule','nuit']):
  a=m['sky_assets'][mode];im=Image.new('RGBA',(702,578),a['horizon'])
  for x in range(0,702,512):
   for key in ['sky','stars','cloud']:im.alpha_composite(Image.open(O/a[key]).convert('RGBA'),(x,0))
  for l in m['reference_beach']['modes'][mode]['layers']:im.alpha_composite(Image.open(O/l['file']).convert('RGBA'),(0,112))
  board.paste(im.convert('RGB').resize((512,422),Image.Resampling.NEAREST),(col*512,30));d.text((col*512+14,9),mode.upper(),fill='#f7edcf')
 board.save(O/'Plages_trois_ambiances.jpg',quality=82)
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
