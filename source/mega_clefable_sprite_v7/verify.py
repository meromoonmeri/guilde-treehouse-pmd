from pathlib import Path
import sys,zipfile
import numpy as np
from PIL import Image
import xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[2];O=R/'renders/mega_clefable_sprite_v7';OUT=O/'sprite/0036/0001';ok=[]
def chk(n,c):ok.append(bool(c));print('PASS' if c else 'FAIL',n)
x=ET.parse(OUT/'AnimData.xml').getroot();anims=x.findall('Anims/Anim');names=[a.find('Name').text for a in anims]
chk(f'{len(names)} anims, unique, <=44',len(names)==len(set(names))<=44);idx=[a.find('Index').text for a in anims];chk('indices unique',len(idx)==len(set(idx)))
for a in anims:
    n=a.find('Name').text;c=a.find('CopyOf')
    if c is not None:
        tgt=[b for b in anims if b.find('Name').text==c.text];chk(f'{n}: CopyOf {c.text} exists, no chaining',len(tgt)==1 and tgt[0].find('CopyOf') is None);continue
    fw,fh=int(a.find('FrameWidth').text),int(a.find('FrameHeight').text);durs=a.findall('Durations/Duration')
    an=Image.open(OUT/f'{n}-Anim.png').convert('RGBA');of=Image.open(OUT/f'{n}-Offsets.png').convert('RGBA');sh=Image.open(OUT/f'{n}-Shadow.png').convert('RGBA')
    chk(f'{n}: same size {an.size}, even {fw}x{fh}, cols={len(durs)}, 8 or 1 rows',an.size==of.size==sh.size and fw%2==0 and fh%2==0 and an.width==fw*len(durs) and an.height in (fh*8,fh))
    REF=R/'source/mega_clefable_sprite_v1/references/spritecollab_0036';import json as _j;man=_j.loads((O/'manifest.json').read_text());PX,PY=man['padding'];fw0,fh0=man['anims'][n]['canonical_frame']
    def unpad(img):
        A_=np.array(img.convert('RGBA'));rows_=A_.shape[0]//fh;cols_=A_.shape[1]//fw;out=np.zeros((rows_*fh0,cols_*fw0,4),'uint8')
        for r_ in range(rows_):
            for c_ in range(cols_):out[r_*fh0:(r_+1)*fh0,c_*fw0:(c_+1)*fw0]=A_[r_*fh+PY:r_*fh+PY+fh0,c_*fw+PX:c_*fw+PX+fw0]
        return out
    chk(f'{n}: Offsets/Shadow identical to CHUNSOFT base once padding removed',np.array_equal(unpad(of),np.array(Image.open(REF/f'{n}-Offsets.png').convert('RGBA'))) and np.array_equal(unpad(sh),np.array(Image.open(REF/f'{n}-Shadow.png').convert('RGBA'))))
    # design consistency: every cell of a direction row that uses the idle view must contain white cap + rose on both sides
    Acell=np.array(an);drift=0
    for r_ in range(Acell.shape[0]//fh):
        for c_ in range(Acell.shape[1]//fw):
            cell=Acell[r_*fh:(r_+1)*fh,c_*fw:(c_+1)*fw];al_=cell[...,3]>0;px_=cell[...,:3].astype(int)
            white=(al_&(px_.min(axis=2)>220)).sum();rose=al_&(px_[...,0]>150)&(px_[...,1]<130)
            xs_=np.nonzero(al_.any(axis=0))[0];cx_=(xs_.min()+xs_.max())//2
            if white<3 or (rose[:,:cx_].sum()<3 and rose[:,cx_+1:].sum()<3) or rose.sum()<8:drift+=1
    chk(f'{n}: design present in every cell (white cap + both wings) drift={drift}',drift==0)
    A=np.array(an);Of=np.array(of);Sh=np.array(sh);good=True
    for r in range(an.height//fh):
        for f in range(len(durs)):
            fr=A[r*fh:(r+1)*fh,f*fw:(f+1)*fw];o=Of[r*fh:(r+1)*fh,f*fw:(f+1)*fw];s=Sh[r*fh:(r+1)*fh,f*fw:(f+1)*fw]
            al=fr[...,3]>0;touch=al[0].any()|al[-1].any()|al[:,0].any()|al[:,-1].any()
            g=((o[...,1]==255)&(o[...,3]>0)).sum();w=((s[...,:3]==255).all(axis=2)&(s[...,3]>0)).sum()
            good&=al.any() and not touch and g==1 and w==1
    chk(f'{n}: every frame non-empty, not touching frame border, exactly one green centre and one white shadow centre',good)
    chk(f'{n}: alpha binary, <=16 colours ({len(np.unique(A[A[...,3]>0][:,:3],axis=0))})',set(np.unique(A[...,3]).tolist())<={0,255} and len(np.unique(A[A[...,3]>0][:,:3],axis=0))<=16)
z=zipfile.ZipFile(O/'0036_0001_mega_clefable_v7_spritecollab.zip');chk('zip complete',set(z.namelist())=={p.name for p in OUT.iterdir()})
print(sum(ok),'/',len(ok),'PASS');sys.exit(0 if all(ok) else 1)
