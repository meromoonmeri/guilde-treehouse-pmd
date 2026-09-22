"""Per-cell design audit of the V3/V4 generated sheets against the user's 64px Mega Clefable reference."""
import numpy as np,json,glob;from PIL import Image
import xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parents[2]
ref=np.array(Image.open(R/'source/mega_clefable_sprite_v3/references/megaclefable_v2_reference_utilisateur_64px_4dir.png').convert('RGBA'))
def sig(rgba):
    al=rgba[...,3]>0;px=rgba[al][:,:3].astype(int)
    if len(px)==0:return None
    r,g,b=px[:,0],px[:,1],px[:,2]
    return dict(white=((r>225)&(g>225)&(b>225)).mean(),yellow=((r>200)&(g>160)&(b<140)).mean(),rose=((r>150)&(g<130)&(b>80)&(r-g>60)).mean(),dark=((r<90)&(g<90)&(b<90)).mean())
def wings(rgba):
    al=rgba[...,3]>0;px=rgba[...,:3].astype(int);rose=al&(px[...,0]>150)&(px[...,1]<130)&(px[...,0]-px[...,1]>60);xs=np.nonzero(al.any(axis=0))[0];cx=int(xs.mean());return bool(rose[:,:cx].sum()>3),bool(rose[:,cx+1:].sum()>3)
rs=sig(ref);out={'reference_signature':rs}
for v in ['v3','v4','v5']:
    x=ET.parse(R/f'renders/mega_clefable_sprite_{v}/sprite/0036/0001/AnimData.xml').getroot()
    for p in sorted(glob.glob(str(R/f'renders/mega_clefable_sprite_{v}/sprite/0036/0001/*-Anim.png'))):
        n=Path(p).name.split('-')[0];a=[e for e in x.findall('Anims/Anim') if e.find('Name').text==n][0];fw,fh=int(a.find('FrameWidth').text),int(a.find('FrameHeight').text)
        A=np.array(Image.open(p).convert('RGBA'));rows,cols=A.shape[0]//fh,A.shape[1]//fw;bad=0;far=[];nowhite=0
        for r in range(rows):
            for c in range(cols):
                cell=A[r*fh:(r+1)*fh,c*fw:(c+1)*fw];s=sig(cell)
                if s is None:continue
                far.append(sum(abs(s[k]-rs[k]) for k in rs));l,rr=wings(cell);bad+=not(l and rr);nowhite+=s['white']<0.02
        far=np.array(far);out[f'{v}/{n}']=dict(cells=rows*cols,palette_dist_mean=round(float(far.mean()),3),palette_dist_std=round(float(far.std()),3),cells_missing_a_wing=int(bad),cells_without_white_cap=int(nowhite))
json.dump(out,open(Path(__file__).with_name('audit_v3_v4.json'),'w'),indent=1)
for k,v in out.items():print(k,v)
