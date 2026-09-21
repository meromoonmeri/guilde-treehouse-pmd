import json,zipfile,io,sys
from pathlib import Path
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'renders/sky_peak_prairie_v1';P='SkyPeakPrairieV1';m=json.loads((O/'manifest.json').read_text());sys.path.insert(0,str(R/'source'));import ciels_valides as c
L=lambda n:np.array(Image.open(O/'calques'/f'{P}_{n}.png').convert('RGBA'));n=0
def ok(name,cond):
    global n;assert cond,name;n+=1
layers={k:L(k) for k in m['layers']}
for k,a in layers.items():ok(k+' size',a.shape==(864,960,4))
ok('sky equals native helper',np.array_equal(layers['01_ciel_natif'],np.array(c.sky((960,864),'nuit'))))
st=np.array(c.stars((960,864),'nuit',moon=True));ok('stars+moon recompose native sheet',np.array_equal(np.where(layers['03_lune_native'][:,:,3:]>0,layers['03_lune_native'],layers['02_etoiles_natives']),st))
ok('moon box',layers['03_lune_native'][:,:,3].any() and (layers['03_lune_native'][:,:,3]>0)[m['moon_box'][1]:m['moon_box'][3],m['moon_box'][0]:m['moon_box'][2]].any())
strip=np.array(Image.open(O/'calques'/f'{P}_bande_nuages_native_1440.png'));ok('cloud strip equals validated helper',np.array_equal(strip,np.array(c.clouds('nuit'))))
comp=np.array(Image.open(O/f'{P}_composition_nuit.png').convert('RGBA'));out=Image.fromarray(layers['01_ciel_natif'])
for k in m['layers'][1:]:out.alpha_composite(Image.fromarray(layers[k]))
ok('composition recomposes from layers',np.array_equal(np.array(out),comp))
with zipfile.ZipFile(O/f'{P}_editable.ora') as z:ok('ORA merged equals composition',np.array_equal(np.array(Image.open(io.BytesIO(z.read('mergedimage.png'))).convert('RGBA')),comp))
t=np.array(Image.open(O/'calques'/f'{P}_terrain_complet.png').convert('RGBA'));g=layers['07_plateau_herbe'];r=layers['08_paroi_rocheuse']
ok('grass+rock partition terrain',np.array_equal(np.where(g[:,:,3:]>0,g,r),t) and not (g[:,:,3]>0)[r[:,:,3]>0].any())
ok('no magenta left in terrain/panorama',not any(((a[:,:,0]>a[:,:,1].astype(int)+60)&(a[:,:,2]>a[:,:,1].astype(int)+60)&(a[:,:,3]>0)).any() for a in [t,layers['05_panorama_montagnes_foret']]))
ok('grass is Sky Peak green range',np.median(g[g[:,:,3]>0][:,1])>190)
ok('forest sea reaches bottom edge',layers['05_panorama_montagnes_foret'][-1,:,3].all())
data=(O/f'{P}_extrait_nuages_24s.webp').read_bytes();pos=12;tot=0
while pos+8<=len(data):
    tag=data[pos:pos+4];sz=int.from_bytes(data[pos+4:pos+8],'little')
    if tag==b'ANMF':tot+=int.from_bytes(data[pos+20:pos+23],'little')
    pos+=8+sz+(sz&1)
ok('excerpt lasts 24 s (identical consecutive frames merged by encoder)',tot==24000)
(O/'verification.json').write_text(json.dumps(dict(status='PASS',checks=n,runtime_validated=False,note='pixel provenance and recomposition only; terrain and panorama are generated art'),indent=2)+'\n');print('PASS',n)
