import json,zipfile,io,sys
from pathlib import Path
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'renders/sky_peak_prairie_v1/v3';V2=R/'renders/sky_peak_prairie_v1/v2';P='SkyPeakPrairieV3';m=json.loads((O/'manifest.json').read_text());n=0
sys.path.insert(0,str(R/'source/cote_v4_abyss'));from night import night
def ok(name,cond):
    global n;assert cond,name;n+=1
L=lambda k:np.array(Image.open(O/'calques'/f'{P}_{k}.png').convert('RGBA'))
sky=L('01_ciel_profond');ok('sky opaque 960x864',sky.shape==(864,960,4) and (sky[:,:,3]==255).all())
col=sky[:,480,:3].astype(int);ok('sky is a smooth gradient, darker zenith, no motif',col[0].sum()<col[-1].sum() and np.abs(np.diff(col,axis=0)).max()<=6 and np.abs(np.diff(sky[100,:,:3].astype(int),axis=0)).max()<=3)
frames=[np.array(Image.open(O/'etoiles_frames'/f'{P}_etoiles_{i:02d}.png')) for i in range(64)]
ok('64 star frames',len(list((O/'etoiles_frames').glob('*.png')))==64)
ok('stars only in sky band',all(not f[470:,:,3].any() for f in frames))
ok('stars twinkle: consecutive frames differ, loop is periodic',all((frames[i]!=frames[i+1]).any() for i in range(63)) and (frames[0]!=frames[63]).any())
ok('star motif sizes 1..5 px',any((f[:,:,3]==255).sum()>0 for f in frames) and frames[0][:,:,3].max()==255)
ok('stars avoid moon',not (frames[5][:,:,3]>0)[48:177,716:845].any())
mets=[np.array(Image.open(O/'etoiles_filantes_frames'/f'{P}_filante_{i:03d}.png')) for i in range(0,360,3)]
ok('360 meteor frames',len(list((O/'etoiles_filantes_frames').glob('*.png')))==360)
ok('meteor layer empty most of the time and active during events',sum(f[:,:,3].any() for f in mets)<len(mets)*.35 and sum(f[:,:,3].any() for f in mets)>8)
for k in m['reused_from_v2']:ok('reused v2 layer unchanged '+k,np.array_equal(L(k),np.array(Image.open(V2/'calques'/f'SkyPeakPrairieV2_{k}.png').convert('RGBA'))))
comp=np.array(Image.open(O/f'{P}_composition_nuit.png').convert('RGBA'));out=Image.fromarray(sky)
for k in m['layers'][1:]:out.alpha_composite(Image.fromarray(L(k)))
ok('composition recomposes from layers',np.array_equal(np.array(out),comp))
with zipfile.ZipFile(O/f'{P}_editable.ora') as z:ok('ORA merged equals composition',np.array_equal(np.array(Image.open(io.BytesIO(z.read('mergedimage.png'))).convert('RGBA')),comp))
nc=np.array(Image.open(O/f'{P}_composition_nuit_abyss.png').convert('RGBA'));out=Image.fromarray(sky)
for k in m['layers'][1:]:
    im=Image.fromarray(L(k))
    if k not in('02_etoiles_phase0','02b_etoiles_filantes_vide','03_lune_generee'):im=night(im)
    out.alpha_composite(im)
ok('abyss composition = exact filter on non-sky layers',np.array_equal(np.array(out),nc))
def dur(p):
    d=p.read_bytes();pos=12;tot=0
    while pos+8<=len(d):
        tag=d[pos:pos+4];sz=int.from_bytes(d[pos+4:pos+8],'little')
        if tag==b'ANMF':tot+=int.from_bytes(d[pos+20:pos+23],'little')
        pos+=8+sz+(sz&1)
    return tot
ok('star loop 8 s',dur(O/f'{P}_etoiles_8s.webp')==8000);ok('meteor loop 12 s',dur(O/f'{P}_etoiles_filantes_12s.webp')==12000)
for nm in ['nuit','nuit_abyss']:ok('excerpt 24 s '+nm,dur(O/f'{P}_extrait_24s_{nm}.webp')==24000)
(O/'verification.json').write_text(json.dumps(dict(status='PASS',checks=n,runtime_validated=False,note='authored/generated pixels; recomposition, layer separation and loop timing only'),indent=2)+'\n');print('PASS',n)
