"""Mega Clefable (0036/0001) SpriteCollab package derived frame-by-frame from the canonical CHUNSOFT Clefable
sprite (PMDCollab/SpriteCollab @aae4cee2, sprite/0036). Slot 0036/0001 'Mega' is EMPTY in tracker.json (sprite_complete 0),
so this is a new proposal, not a replacement.

Per frame, per animation (all 13 owned anims, 8 directions, same frame sizes and Durations):
  * palette transfer: Clefable pink/brown-wing palette -> Mega Clefable peach body, rose wings with yellow tips;
  * wings widened by one pixel of dilation (Mega's wings are much larger) using the wing colour mask;
  * white 'hair cap' painted over the upper part of the body silhouette (Mega's white mushroom-cap hair + top curl);
  * black hand cuffs placed with the canonical Offsets.png red/blue hand markers.
Offsets.png / Shadow.png are copied unchanged (same body centre, hands, head, shadow).
This is generated derivative pixel art: disclosed as such in the credits and README (not CHUNSOFT-native).
"""
from pathlib import Path
import json,shutil,zipfile,hashlib,io
import numpy as np
from PIL import Image
import xml.etree.ElementTree as ET
from scipy import ndimage
R=Path(__file__).resolve().parents[2];S=Path(__file__).resolve().parent;REF=S/'references/spritecollab_0036';O=R/'renders/mega_clefable_sprite_v1';OUT=O/'sprite/0036/0001';OUT.mkdir(parents=True,exist_ok=True)
PAL={(255,199,207):(255,222,206),(239,151,159):(243,183,168),   # body light / shade -> peach
     (215,63,0):(233,96,128),(255,135,95):(248,158,178),(175,95,55):(204,72,108),(119,63,0):(142,42,74),(167,95,31):(220,116,140),(223,119,31):(246,204,120),
     (255,255,255):(255,255,255),(0,0,0):(0,0,0),(159,0,0):(159,0,0),(199,215,215):(199,215,215),(143,223,255):(143,223,255)}
WING={(215,63,0),(255,135,95),(175,95,55),(119,63,0),(167,95,31),(223,119,31)}
BODY={(255,199,207),(239,151,159)}
CAP=(255,255,255);CAP_SHADE=(199,215,215);CUFF=(38,30,40);CUFF_HI=(142,42,74)
x=ET.parse(REF/'AnimData.xml').getroot();anims=[]
def key(a):return a[...,0].astype(int)*65536+a[...,1].astype(int)*256+a[...,2].astype(int)
def k3(c):return c[0]*65536+c[1]*256+c[2]
def transform(frame,off):
    a=np.array(frame);vis=a[...,3]>0;kk=key(a);out=a.copy()
    unknown=vis.copy()
    for src,dst in PAL.items():
        m=vis&(kk==k3(src));out[m,:3]=dst;unknown&=~m
    assert not unknown.any(),np.unique(a[unknown],axis=0)
    wing=np.zeros_like(vis)
    for c in WING:wing|=vis&(kk==k3(c))
    body=np.zeros_like(vis)
    for c in BODY:body|=vis&(kk==k3(c))
    # 1. wings one pixel wider (only into transparent pixels, keep frame bounds)
    if wing.any():
        grow=ndimage.binary_dilation(wing,iterations=1)&~vis;out[grow,:3]=PAL[(215,63,0)];out[grow,3]=255
        edge=ndimage.binary_dilation(grow,iterations=1)&~vis&~grow;out[edge,:3]=(0,0,0);out[edge,3]=255
    # 1b. yellow tips: wing pixels farthest from the body centroid (outer 40 % of each wing's radial span)
    if wing.any() and body.any():
        by,bx=np.nonzero(body);cy,cx=by.mean(),bx.mean();wm=wing.copy()
        wy,wx=np.nonzero(wm);d=np.hypot(wy-cy,wx-cx)
        if len(d)>4:
            thr=d.min()+(d.max()-d.min())*0.62;tip=np.zeros_like(wing);tip[wy[d>thr],wx[d>thr]]=True
            light=tip&(kk==k3((255,135,95)))|tip&(kk==k3((223,119,31)));out[tip,:3]=(246,214,110);out[light,:3]=(255,240,170)
    # 2. hair cap over the top of the body silhouette (rows above 34% of body height), not on wings
    ys,xs=np.nonzero(body)
    if len(ys):
        top=ys.min();h=ys.max()-top+1;cut=top+max(2,int(round(h*0.22)))
        cap=body&(np.arange(a.shape[0])[:,None]<cut);out[cap,:3]=CAP
        shade=cap&(np.arange(a.shape[0])[:,None]>=cut-2);out[shade,:3]=CAP_SHADE
        # top curl: 1 px bump above the highest cap column centre
        cols=np.nonzero(cap.any(axis=0))[0]
        if len(cols):
            cx=int(cols.mean());ty=int(np.nonzero(cap[:,cx])[0].min()) if cap[:,cx].any() else top
            for dx,dy in [(0,-1),(1,-1),(0,-2)]:
                px,py=cx+dx,ty+dy
                if 0<=px<a.shape[1] and 0<=py<a.shape[0] and out[py,px,3]==0:out[py,px]=(*CAP,255)
    # 3. cuffs at the canonical hand markers
    o=np.array(off);
    for col in [(255,0,0),(0,0,255)]:
        m=(o[...,3]>0)&(o[...,0]==col[0])&(o[...,2]==col[2])&(o[...,1]==0)
        # combined markers (e.g. red+blue = magenta) also count
        for (py,px) in zip(*np.nonzero(m)):
            for dy in (0,1):
                for dx in (-1,0,1):
                    qx,qy=px+dx,py+dy
                    if 0<=qx<a.shape[1] and 0<=qy<a.shape[0] and (a[qy,qx,3]>0) and tuple(a[qy,qx,:3]) in BODY|{(0,0,0)}:
                        out[qy,qx,:3]=CUFF_HI if (dy==0 and dx==0) else CUFF
    return Image.fromarray(out)
report=[]
for an in x.findall('Anims/Anim'):
    name=an.find('Name').text
    if an.find('CopyOf') is not None:continue
    fw,fh=int(an.find('FrameWidth').text),int(an.find('FrameHeight').text)
    src=Image.open(REF/f'{name}-Anim.png').convert('RGBA');off=Image.open(REF/f'{name}-Offsets.png').convert('RGBA')
    dst=Image.new('RGBA',src.size);cols,rows=src.width//fw,src.height//fh
    for r in range(rows):
        for c in range(cols):
            box=(c*fw,r*fh,c*fw+fw,r*fh+fh);dst.paste(transform(src.crop(box),off.crop(box)),box[:2])
    dst.save(OUT/f'{name}-Anim.png');shutil.copy(REF/f'{name}-Offsets.png',OUT/f'{name}-Offsets.png');shutil.copy(REF/f'{name}-Shadow.png',OUT/f'{name}-Shadow.png')
    report.append(dict(anim=name,frame=[fw,fh],sheet=list(src.size),frames=cols,directions=rows,durations=[d.text for d in an.findall('Durations/Duration')]))
shutil.copy(REF/'AnimData.xml',OUT/'AnimData.xml')
(OUT/'credits.txt').write_text('2026-09-22 00:00:00.000000\tarena-agent (derived from CHUNSOFT 0036 base; generated Mega proposal)\tCUR\tCC_BY-NC_4\t'+','.join(r['anim'] for r in report)+',Strike\n')
with zipfile.ZipFile(O/'0036_0001_mega_clefable_spritecollab.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(OUT.iterdir()):z.write(p,p.name)
# review sheets: canonical vs mega for Idle and Walk (x3)
for name in ['Idle','Walk','Attack','Sleep']:
    a=Image.open(REF/f'{name}-Anim.png').convert('RGBA');b=Image.open(OUT/f'{name}-Anim.png').convert('RGBA')
    board=Image.new('RGBA',(a.width*2+8,a.height),(90,90,90,255));board.alpha_composite(a,(0,0));board.alpha_composite(b,(a.width+8,0))
    board.resize((board.width*2,board.height*2),Image.NEAREST).save(O/f'comparatif_{name}_x2.png')
(O/'manifest.json').write_text(json.dumps(dict(slot='0036/0001 Mega (empty in tracker @aae4cee2)',base='PMDCollab/SpriteCollab@aae4cee282dc516de5e52e33634431d80ee6bf56 sprite/0036 (CHUNSOFT)',anims=report,palette={str(k):v for k,v in PAL.items()},
   references={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(REF.iterdir())},generated=True,runtime_validated=False),indent=1))
print('ok',[r['anim'] for r in report])
