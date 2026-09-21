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
layers['05b_brume_overlay']=L('05b_brume_overlay');comp=np.array(Image.open(O/f'{P}_composition_nuit.png').convert('RGBA'));out=Image.fromarray(layers['01_ciel_genere'])
for k in m['layers'][1:]:out.alpha_composite(Image.fromarray(layers[k]))
ok('composition recomposes from layers',np.array_equal(np.array(out),comp))
with zipfile.ZipFile(O/f'{P}_editable.ora') as z:ok('ORA merged equals composition',np.array_equal(np.array(Image.open(io.BytesIO(z.read('mergedimage.png'))).convert('RGBA')),comp))
t=np.array(Image.open(O/'calques'/f'{P}_terrain_complet.png').convert('RGBA'));g=layers['07_plateau_herbe'];r=layers['08_paroi_rocheuse']
ok('grass+rock partition terrain',np.array_equal(np.where(g[:,:,3:]>0,g,r),t) and not (g[:,:,3]>0)[r[:,:,3]>0].any())
ok('no magenta left in terrain/panorama',not any(((a[:,:,0]>a[:,:,1].astype(int)+60)&(a[:,:,2]>a[:,:,1].astype(int)+60)&(a[:,:,3]>0)).any() for a in [t,layers['05_panorama_skypeak_foret_montagnes']]))
ok('grass is Sky Peak green range',np.median(g[g[:,:,3]>0][:,1])>190)
pa=layers['05_panorama_skypeak_foret_montagnes'];ok('panorama forest is green Sky Peak range at bottom',np.median(pa[-40:,:,1])>np.median(pa[-40:,:,0])+20)
ok('forest sea reaches bottom edge',layers['05_panorama_skypeak_foret_montagnes'][-1,:,3].all())
data=(O/f'{P}_extrait_brume_nuages_24s.webp').read_bytes();pos=12;tot=0
while pos+8<=len(data):
    tag=data[pos:pos+4];sz=int.from_bytes(data[pos+4:pos+8],'little')
    if tag==b'ANMF':tot+=int.from_bytes(data[pos+20:pos+23],'little')
    pos+=8+sz+(sz&1)
ok('excerpt lasts 24 s (identical consecutive frames merged by encoder)',tot==24000)
# V2.1 mist overlay + Abyss night
import sys as _s;_s.path.insert(0,str(R/'source/cote_v4_abyss'));from night import night
mist=L('05b_brume_overlay');ok('mist layer present and translucent',(mist[:,:,3]>0).sum()>5000 and mist[:,:,3].max()<=230)
f0=np.array(Image.open(O/'brume_frames'/f'{P}_brume_000.png'));f1=np.array(Image.open(O/'brume_frames'/f'{P}_brume_010.png'));ok('mist frames animate',np.array_equal(f0,mist) and (f0!=f1).any())
ok('80 mist frames',len(list((O/'brume_frames').glob('*.png')))==80)
for k in range(3):st=np.array(Image.open(O/'calques'/f'{P}_bande_brume_{k}_1440.png'));ok(f'mist strip {k}',st.shape[1]==1440 and (st[:,:,3]>0).any())
NA=O/'nuit_abyss';NL=lambda n:np.array(Image.open(NA/'calques'/f'{P}_{n}.png').convert('RGBA'))
for k in ['01_ciel_genere','02_etoiles_generees','03_lune_generee']:ok('night keeps sky layer '+k,np.array_equal(NL(k),layers[k]))
for k in ['05_panorama_skypeak_foret_montagnes','07_plateau_herbe','08_paroi_rocheuse','04_nuages_lointains','06_nuages_overlay']:ok('night layer is exact Abyss filter '+k,np.array_equal(NL(k),np.array(night(Image.fromarray(layers[k])))))
ok('night mist is exact Abyss filter',np.array_equal(NL('05b_brume_overlay'),np.array(night(Image.fromarray(mist)))))
ncomp=np.array(Image.open(NA/f'{P}_composition_nuit_abyss.png').convert('RGBA'));out=Image.fromarray(NL('01_ciel_genere'))
for k in m['layers'][1:]:out.alpha_composite(Image.fromarray(NL(k)))
ok('night composition recomposes',np.array_equal(np.array(out),ncomp))
with zipfile.ZipFile(NA/f'{P}_editable.ora') as z:ok('night ORA merged equals night composition',np.array_equal(np.array(Image.open(io.BytesIO(z.read('mergedimage.png'))).convert('RGBA')),ncomp))
(O/'verification.json').write_text(json.dumps(dict(status='PASS',checks=n,runtime_validated=False,note='recomposition and layer separation only; every pixel is generated art'),indent=2)+'\n');print('PASS',n)
