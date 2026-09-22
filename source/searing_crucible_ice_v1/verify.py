"""Checks for searing_crucible_ice_v1: native cells identical to the RawAsset sheets, geometry identical to the reference rsmap,
animation counts/timing identical to the reference, WebP loops of 252 game frames, references SHA256 intact."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];S=Path(__file__).resolve().parent;O=R/'renders/searing_crucible_ice_v1'
sys.path.insert(0,str(S));from decode import rsmap,load_dir
m=json.loads((O/'manifest.json').read_text());ok=[]
def chk(n,c):ok.append((n,bool(c)));print(('PASS' if c else 'FAIL'),n)
ground=Image.open(O/'calques/01_sol_vast_ice_mountain_peak_natif.png').convert('RGBA');sheets=[Image.open(S/f'references/rawasset/VastIceMountainPeak/tileset_{i}.png').convert('RGBA') for i in range(3)]
bad=0
for c in m['cells']:
    a=np.array(ground.crop((c['x']*24,c['y']*24,c['x']*24+24,c['y']*24+24)));b=np.array(sheets[c['variant']].crop(tuple(c['box'])))
    if not np.array_equal(a,b):bad+=1
chk(f'441 ground cells pixel-identical to canonical sheets (bad={bad})',bad==0 and len(m['cells'])==441)
o=rsmap();g=o['Tiles'];fl=sum(g[x][y]['Data']['ID']=='floor' for x in range(21) for y in range(21))
chk('floor/wall counts identical to reference rsmap (72/369)',fl==72==m['floor_cells'] and m['wall_cells']==369)
ref=[(a['ObjectAnim']['AnimIndex'],a['MapLoc']['X'],a['MapLoc']['Y'],a['ObjectAnim']['FrameTime'],a['ObjectAnim']['AnimFlip']) for dl in o['Decorations'] for a in dl['Anims']]
got=[(d['source'],d['x'],d['y'],d['frame_time'],d['flip']) for d in m['decorations']]
chk('8 decorations: same source, MapLoc, FrameTime, flip as reference',ref==got and len(got)==8)
for n,info in m['animations'].items():
    st=Image.open(O/'objets_animes'/f"{n}_{info['w']}x{info['h']}_{info['frames']}f.png");chk(f'{n}: 63 frames strip {st.size}',st.size==(info['w']*63,info['h']) and info['frames']==63)
for n,src in sorted({(d['name'],d['source']) for d in m['decorations']}):
    fr,w,h=load_dir(S/f'references/nev5/Content/Object/{src}.dir');st=np.array(Image.open(O/'objets_animes'/f'{n}_{w}x{h}_63f.png').convert('RGBA'))
    same=all(np.array_equal((np.array(f)[...,3]>0)&(np.array(f)[...,0]!=127),(st[:,i*w:(i+1)*w,3]>0)) for i,f in enumerate(fr[:5]))
    chk(f'{n}: silhouette (alpha minus floor backing) identical to native frames 0-4',same)
for wp in ['creuset_glace_anime.webp','creuset_glace_anime_sans_brume.webp']:
    im=Image.open(O/wp);tot=0
    for i in range(im.n_frames):im.seek(i);tot+=im.info.get('duration',67)
    chk(f'{wp}: ~4.2 s loop ({tot} ms, {im.n_frames} frames)',abs(tot-4200)<=100 and im.size==(504,504))
shas={k:hashlib.sha256((S/k).read_bytes()).hexdigest() for k in m['references']};chk('reference SHA256 unchanged',shas==m['references'])
chk('runtime_validated flag is False (no engine test)',m['runtime_validated'] is False)
print(sum(c for _,c in ok),'/',len(ok),'PASS');sys.exit(0 if all(c for _,c in ok) else 1)
