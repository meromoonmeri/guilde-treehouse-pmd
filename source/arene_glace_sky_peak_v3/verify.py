from pathlib import Path
import importlib.util, json, io, zipfile
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent;O=R/'renders/arene_glace_sky_peak_v3'
spec=importlib.util.spec_from_file_location('arena_v3',HERE/'build.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
def main():
 m=json.loads((O/'manifest.json').read_text());checks=[]
 def check(name,ok):assert ok,name;checks.append(name)
 layers={k:b.load(O/p) for k,p in m['layers'].items()}
 check('Ten aligned PNG layers, 960×896 divisible by8',len(layers)==10 and all(im.size==b.SIZE for im in layers.values()) and all(n%8==0 for n in b.SIZE))
 check('All raw generations retained and hash-pinned',all(b.sha(O/p['path'])==p['sha256'] for p in m['raws']))
 check('Canonical reference files unchanged',all(b.sha(R/p['path'])==p['sha256'] for p in m['references']))
 for p in m['retained']:
  source=b.load(R/p['source']);assert b.sha(R/p['source'])==p['sha256'];assert layers[p['layer']].crop((0,0,960,720)).tobytes()==source.tobytes()
 check('Sky/stars/moon/aurora retain original V2 pixels, positions and scale',True)
 terrain=b.compose({k:v for k,v in layers.items() if k[:2] in ['06','07','08','09']})
 raw=b.key(b.load(O/'bruts/arene_matiere_canonique_magenta.png'));expected,_=b.place(raw,960,(0,270))
 check('Visible terrain split reconstructs the generated master exactly',terrain.tobytes()==expected.tobytes())
 floor=np.array(Image.open(O/'controle'/f'{b.P}_masque_sol_visible.png'))
 check('Geometric southern approach remains open through visible floor mask',bool((floor[590:896,476:484]==255).all()))
 check('Mountain ridge is shallow at horizon, not foreground-scale',m['normalization']['mountains']['output_size'][1]<90 and m['normalization']['mountains']['xy']==[0,160])
 forest=np.array(layers['05_vallee_mer_de_sapins'])
 check('Forest fills entire lower field below distant horizon',bool((forest[230:,:,3]==255).all()))
 check('Forest shown between mountains and rear arena rim',bool((np.array(terrain)[220:345,400:550,3]==0).all()) and bool((forest[230:345,400:550,3]==255).all()))
 moon=np.array(layers['03_lune_canonique']);mm=moon[:,:,3]>0;tm=np.array(terrain)[:,:,3]==255
 check('Native crescent remains 33×36 at 800,64 with 516 visible pixels',layers['03_lune_canonique'].getbbox()==(800,64,833,100) and int(mm.sum())==516)
 initial=np.array(b.compose(layers));counts=[]
 with Image.open(O/m['webp']) as webp:
  check('Lossless WebP has32 frames, indefinite 4-second loop',webp.n_frames==32 and webp.info['loop']==0)
  for f,rel in enumerate(m['effect_frames']):
   effect=b.blank();effect.paste(b.load(O/rel),(0,0));current={k:effect if k=='02b_aurore_panoramique' else im for k,im in layers.items()};scene=b.compose(current)
   webp.seek(f);actual=np.array(webp.convert('RGBA'));assert np.array_equal(actual,np.array(scene)) and webp.info['duration']==125
   assert np.array_equal(actual[tm],initial[tm]) and np.array_equal(actual[moon[:,:,3]==255],moon[moon[:,:,3]==255])
   if str(f) in m['scene_frames']:assert b.load(O/m['scene_frames'][str(f)]).tobytes()==scene.tobytes()
   alpha=np.array(effect)[:,:,3];counts.append([int((alpha[:160,:120]>0).sum()),int((alpha[:160,-120:]>0).sum())])
 check('All32 frames exactly recompose; terrain and moon stationary',True)
 check('Four individually viewable composition keyframe PNGs',len(m['scene_frames'])==4)
 check('Panoramic aurora remains visible on both sky edges',min(min(v) for v in counts)>7000)
 check('No horizontal aurora scroll or new palette processing',m['aurora']['horizontal_scroll'] is False and len(m['effect_frames'])==32)
 with zipfile.ZipFile(O/m['ora']) as z:
  check('OpenRaster CRC and merged preview correct',z.testzip() is None and Image.open(io.BytesIO(z.read('mergedimage.png'))).convert('RGBA').tobytes()==b.compose(layers).tobytes())
 for name,im in layers.items():
  a=np.array(im);r,g,blue=a[:,:,:3].astype(int).transpose(2,0,1)
  assert not (((r>230)&(blue>230)&(g<50))&(a[:,:,3]>0)).any(),name
 check('No saturated magenta backdrop left in any layer',True)
 report={'status':'PASS','checks':checks,'count':len(checks),'engine_tested':False,'limits':'Image geometry/pixel checks only; no native-texture, collision or GPU certification.'}
 (HERE/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(len(checks),'V3 asset checks PASS')
if __name__=='__main__':main()
