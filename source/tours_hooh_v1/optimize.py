from pathlib import Path
from PIL import Image
import numpy as np,json
entries=json.loads((Path(__file__).resolve().parents[2]/'renders/tours_hooh_v1/manifest.json').read_text())
O=Path(__file__).resolve().parents[2]/'renders/tours_hooh_v1'
for mode in ['jour','nuit']:
 C=O/'nuages_animes'/mode;C.mkdir(parents=True,exist_ok=True)
 for k,n in enumerate(['02_nuages_lavande','04_nuages_rose','06_nuages_ambre']):
  a=np.array(Image.open(O/'carillon_boss'/mode/f'th1_carillon_boss_{mode}_{n}.png').convert('RGBA'));ims=[Image.fromarray(np.roll(a,round(p*640/256*[1,-1,2][k]),axis=1)) for p in range(256)]
  ims[0].save(C/f'th1_{mode}_{n}_BOUCLE.webp',save_all=True,append_images=ims[1:],duration=250,lossless=True,loop=0,minimize_size=True,method=0,kmin=256,kmax=257);print(mode,n,flush=True)
 for tower in ['carillon','cendree']:
  p=O/f'{tower}_boss'/mode/'BOUCLE_64S.webp';entry=next(e for e in entries if e['id']==f'{tower}_boss');bank={n:Image.open(O/f'{tower}_boss'/mode/f'th1_{tower}_boss_{mode}_{n}.png').convert('RGBA') for n in entry['layers']};ims=[];dur=[250]*256
  for phase in range(256):
   frame=Image.new('RGBA',(640,480))
   for n in entry['layers']:
    im=bank[n]
    if n in entry['animated']:
     k=entry['animated'].index(n);im=Image.fromarray(np.roll(np.array(im),round(phase*640/256*[1,-1,2][k]),axis=1))
    frame.alpha_composite(im)
   ims.append(frame)

  tmp=p.with_name('optimized.webp');ims[0].save(tmp,save_all=True,append_images=ims[1:],duration=dur,lossless=True,loop=0,minimize_size=True,method=0,kmin=256,kmax=257);tmp.replace(p);print('scene',tower,mode,flush=True)
for p in O.glob('*_boss/*/*_BOUCLE.webp'):p.unlink()
print('Optimized loops and removed only redundant generated copies.',flush=True)
