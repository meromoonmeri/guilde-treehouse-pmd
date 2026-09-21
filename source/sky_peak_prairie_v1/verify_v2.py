import json,zipfile,io,sys
from pathlib import Path
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'renders/sky_peak_prairie_v1/v2';P='SkyPeakPrairieV2';m=json.loads((O/'manifest.json').read_text());sys.path.insert(0,str(R/'source'));import ciels_valides as c
L=lambda n:np.array(Image.open(O/'calques'/f'{P}_{n}.png').convert('RGBA'));n=0
def ok(name,cond):
    global n;assert cond,name;n+=1
layers={k:L(k) for k in m['layers']}
for k,a in layers.items():ok(k+' size',a.shape==(864,960,4))
ok('sky fully opaque generated gradient',(layers['01_ciel_genere'][:,:,3]==255).all() and layers['01_ciel_genere'][10,480,2]>layers['01_ciel_genere'][10,480,0])
ok('stars and moon on separate layers, disjoint',(layers['02_etoiles_generees'][:,:,3]>0).sum()>60 and not ((layers['02_etoiles_generees'][:,:,3]>0)&(layers['03_lune_generee'][:,:,3]>0)).any())
mp=m['moon_position'];ms=m['moon_sprite_size'];ok('moon at declared position',(layers['03_lune_generee'][:,:,3]>0)[mp[1]:mp[1]+ms[1],mp[0]:mp[0]+ms[0]].any() and not np.delete(np.delete(layers['03_lune_generee'][:,:,3],range(mp[1],mp[1]+ms[1]),0),range(mp[0],mp[0]+ms[0]),1).any())
for nm in ['lointains','overlay']:
    strip=np.array(Image.open(O/'calques'/f'{P}_bande_nuages_{nm}_1440.png'));ok('cloud strip '+nm+' 1440 wide with sprites',strip.shape[1]==1440 and (strip[:,:,3]>0).sum()>2000 and not strip[:,0,3].any() and not strip[:,-1,3].any())
comp=np.array(Image.open(O/f'{P}_composition_nuit.png').convert('RGBA'));out=Image.fromarray(layers['01_ciel_genere'])
for k in m['layers'][1:]:out.alpha_composite(Image.fromarray(layers[k]))
ok('composition recomposes from layers',np.array_equal(np.array(out),comp))
with zipfile.ZipFile(O/f'{P}_editable.ora') as z:ok('ORA merged equals composition',np.array_equal(np.array(Image.open(io.BytesIO(z.read('mergedimage.png'))).convert('RGBA')),comp))
t=np.array(Image.open(O/'calques'/f'{P}_terrain_complet.png').convert('RGBA'));g=layers['07_plateau_herbe'];r=layers['08_paroi_rocheuse']
ok('grass+rock partition terrain',np.array_equal(np.where(g[:,:,3:]>0,g,r),t) and not (g[:,:,3]>0)[r[:,:,3]>0].any())
ok('no magenta left in terrain/panorama',not any(((a[:,:,0]>a[:,:,1].astype(int)+60)&(a[:,:,2]>a[:,:,1].astype(int)+60)&(a[:,:,3]>0)).any() for a in [t,layers['05_panorama_skypeak_foret_montagnes']]))
ok('grass is Sky Peak green range',np.median(g[g[:,:,3]>0][:,1])>190)
pa=layers['05_panorama_skypeak_foret_montagnes'];ok('panorama forest is green Sky Peak range at bottom',np.median(pa[-40:,:,1])>np.median(pa[-40:,:,0])+20)
ok('forest sea reaches bottom edge',layers['05_panorama_skypeak_foret_montagnes'][-1,:,3].all())
data=(O/f'{P}_extrait_nuages_24s.webp').read_bytes();pos=12;tot=0
while pos+8<=len(data):
    tag=data[pos:pos+4];sz=int.from_bytes(data[pos+4:pos+8],'little')
    if tag==b'ANMF':tot+=int.from_bytes(data[pos+20:pos+23],'little')
    pos+=8+sz+(sz&1)
ok('excerpt lasts 24 s (identical consecutive frames merged by encoder)',tot==24000)
(O/'verification.json').write_text(json.dumps(dict(status='PASS',checks=n,runtime_validated=False,note='recomposition and layer separation only; every pixel is generated art'),indent=2)+'\n');print('PASS',n)
