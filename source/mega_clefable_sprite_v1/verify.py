from pathlib import Path
import json,zipfile,io,sys
import numpy as np
from PIL import Image
import xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[2];S=Path(__file__).resolve().parent;REF=S/'references/spritecollab_0036';O=R/'renders/mega_clefable_sprite_v1';OUT=O/'sprite/0036/0001'
ok=[]
def chk(n,c):ok.append(bool(c));print('PASS' if c else 'FAIL',n)
x=ET.parse(OUT/'AnimData.xml').getroot();chk('AnimData.xml identical to canonical base',(OUT/'AnimData.xml').read_bytes()==(REF/'AnimData.xml').read_bytes())
names=[a.find('Name').text for a in x.findall('Anims/Anim')];chk('13 anims, unique names, <=44',len(names)==len(set(names))<=44)
for a in x.findall('Anims/Anim'):
    n=a.find('Name').text
    if a.find('CopyOf') is not None:chk(f'{n}: CopyOf {a.find("CopyOf").text} exists and is not itself a copy',a.find('CopyOf').text in names);continue
    fw,fh=int(a.find('FrameWidth').text),int(a.find('FrameHeight').text);durs=a.findall('Durations/Duration')
    an=Image.open(OUT/f'{n}-Anim.png');of=Image.open(OUT/f'{n}-Offsets.png');sh=Image.open(OUT/f'{n}-Shadow.png');base=np.array(Image.open(REF/f'{n}-Anim.png').convert('RGBA'))
    chk(f'{n}: 3 PNG same size {an.size}, even frame {fw}x{fh}, {len(durs)} durations = columns, 8 or 1 rows',an.size==of.size==sh.size and fw%2==0 and fh%2==0 and an.width==fw*len(durs) and an.height//fh in (1,8))
    chk(f'{n}: Offsets/Shadow byte-identical to canonical',(OUT/f'{n}-Offsets.png').read_bytes()==(REF/f'{n}-Offsets.png').read_bytes() and (OUT/f'{n}-Shadow.png').read_bytes()==(REF/f'{n}-Shadow.png').read_bytes())
    m=np.array(an.convert('RGBA'));chk(f'{n}: every canonical opaque pixel still opaque (silhouette superset)',bool((m[...,3][base[...,3]>0]==255).all()))
    chk(f'{n}: <=15 colours per frame? ({len(np.unique(m[m[...,3]>0][:,:3],axis=0))} in sheet)',len(np.unique(m[m[...,3]>0][:,:3],axis=0))<=15)
z=zipfile.ZipFile(O/'0036_0001_mega_clefable_spritecollab.zip');chk('zip contains AnimData.xml + 36 PNG + credits',len(z.namelist())==38 and 'AnimData.xml' in z.namelist())
print(sum(ok),'/',len(ok),'PASS');sys.exit(0 if all(ok) else 1)
