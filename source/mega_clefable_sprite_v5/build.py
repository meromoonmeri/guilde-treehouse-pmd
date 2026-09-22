"""Mega Clefable V5 — design-consistent SpriteCollab package.
Audit of V3/V4 (per-animation generated sheets) showed the design drifting between cells (white cap missing in 7..100 % of
cells, palette far from the user's reference). V5 therefore uses ONE on-model sprite set — the generator turnaround
(source/mega_clefable_sprite_v4/gen/raw_turnaround.png) and action poses (raw_extra_poses.png), both made from the user's strict
reference — and animates them along the CANONICAL SpriteCollab Clefable trajectories: for every animation, direction and frame,
the body centre follows the green marker of the CHUNSOFT Offsets.png (measured: Attack wind-up -3 px / lunge +19 px / return,
Double +-6/10/12/13 px shake, Swing circular arc, Charge 1 px bob, Hop parabola...). Pose substitution per phase:
Attack/Strike/Swing/Double lunge frames -> attack pose, Hurt -> hurt pose, Sleep -> sleep pose, Charge -> charge pose, others -> idle view
with a wing-flap column shift (Mega Clefable hovers). Frames are enlarged (canonical + padding) because the wings are wider than
Clefable; Offsets/Shadow are the canonical ones shifted by the padding, AnimData.xml keeps canonical durations / Rush-Hit-Return.
Identical pixels in every frame of a given direction => zero design drift; disclosed as generated art (AI-drawn base set)."""
from pathlib import Path
import json,zipfile,hashlib,io
import numpy as np
from PIL import Image
from scipy import ndimage
import xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[2];S=Path(__file__).resolve().parent;G4=R/'source/mega_clefable_sprite_v4/gen';REF=R/'source/mega_clefable_sprite_v1/references/spritecollab_0036'
O=R/'renders/mega_clefable_sprite_v5';OUT=O/'sprite/0036/0001';OUT.mkdir(parents=True,exist_ok=True)
PAL=np.array([[254,204,186],[250,170,158],[222,126,120],   # body light/mid/shade (from the on-model drawing)
 [222,96,98],[186,58,80],[132,36,52],                      # wings coral light/mid/dark
 [244,224,110],[230,184,74],                               # yellow tips
 [255,255,255],[224,224,232],                              # cap
 [70,32,44],[110,60,72],                                   # cuffs / ear tips
 [246,150,150],[96,140,220],[200,60,120],[0,0,0]])         # cheeks / eyes / wing vein / outline
BODY_H=30  # px height of the front view body (Clefable is 21; Mega is 1.7 m vs 1.3 m)
PADX,PADY=24,8
def comps(path):
    a=np.array(Image.open(path).convert('RGB')).astype(int);bg=np.array([255,0,255]);m=np.abs(a-bg).sum(axis=2)>90
    sh=(a[...,1]<90)&(a[...,0]>80)&(a[...,2]>80)&(a[...,0]<215);m&=~sh;m=ndimage.binary_opening(m,iterations=2);m=ndimage.binary_fill_holes(m)
    lab,n=ndimage.label(m);objs=ndimage.find_objects(lab)
    boxes=sorted([(s[1].start,s[0].start,s[1].stop,s[0].stop) for s in objs if (s[0].stop-s[0].start)>100],key=lambda b:(b[1]//300,b[0]))
    return a,m,boxes
def quant(rgb):
    d=((rgb[...,None,:].astype(int)-PAL[None,None,:,:])**2).sum(-1);return PAL[d.argmin(-1)].astype('uint8')
def sprite(a,m,box,scale):
    x0,y0,x1,y1=box;rgb=a[y0:y1,x0:x1].astype('uint8');mm=m[y0:y1,x0:x1]
    pre=np.dstack([rgb*mm[...,None],(mm*255).astype('uint8')]).astype('uint8');w,h=max(2,round((x1-x0)*scale)),max(2,round((y1-y0)*scale))
    im=Image.fromarray(pre,'RGBA').resize((w,h),Image.BOX);arr=np.array(im).astype(float);al=arr[...,3]>100
    rgb2=np.zeros_like(arr[...,:3]);rgb2[al]=arr[...,:3][al]*255/arr[...,3:4][al];q=quant(np.clip(rgb2,0,255).astype('uint8'))
    out=np.dstack([q,(al*255).astype('uint8')]);out[~al]=0;edge=al&~ndimage.binary_erosion(al);out[edge,:3]=0;return out
a1,m1,b1=comps(G4/'raw_turnaround.png');a2,m2,b2=comps(G4/'raw_extra_poses.png')
scale=BODY_H/(b1[0][3]-b1[0][1])
T=[sprite(a1,m1,b,scale) for b in b1];E=[sprite(a2,m2,b,scale) for b in b2]
front,three_q,profile,back=T[0],T[1],T[2],T[3]
hurt_f,hurt_p,sleep_f,attack_f=E[0],E[1],E[2],E[3];attack_p,charge_f=E[6],E[7]
def M(s):return s[:,::-1].copy()
# 8 directions: down, down-right, right, up-right, up, up-left, left, down-left  (3/4 back views do not exist: back is used)
VIEW=[front,three_q,profile,back,back,back,M(profile),M(three_q)]
ATT=[attack_f,attack_p,attack_p,back,back,back,M(attack_p),M(attack_p)]
HURT=[hurt_f,hurt_p,hurt_p,back,back,back,M(hurt_p),M(hurt_p)]
CHG=[charge_f,three_q,profile,back,back,back,M(profile),M(three_q)]
SLP=[sleep_f]*8
def flap(s,k):
    """wing flap: rose pixels far from the body axis shift vertically by k px (k in -2..2)"""
    if k==0:return s
    out=np.zeros_like(s);h,w=s.shape[:2];al=s[...,3]>0;xs=np.nonzero(al.any(axis=0))[0];cx=(xs.min()+xs.max())/2;half=max(1,(xs.max()-xs.min())/2)
    for x in range(w):
        d=abs(x-cx)/half;sh=int(round(k*max(0,d-0.35)/0.65));col=np.roll(s[:,x],sh,axis=0)
        if sh>0:col[:sh]=0
        elif sh<0:col[sh:]=0
        out[:,x]=col
    return out
def centre(s):
    al=s[...,3]>0;ys,xs=np.nonzero(al);return xs.mean(),ys.min()+0.6*(ys.max()-ys.min())
x=ET.parse(REF/'AnimData.xml');root=x.getroot();report={}
for an in root.findall('Anims/Anim'):
    name=an.find('Name').text
    if an.find('CopyOf') is not None:continue
    fw0,fh0=int(an.find('FrameWidth').text),int(an.find('FrameHeight').text);fw,fh=fw0+2*PADX,fh0+2*PADY
    an.find('FrameWidth').text=str(fw);an.find('FrameHeight').text=str(fh);n=len(an.findall('Durations/Duration'))
    cA=np.array(Image.open(REF/f'{name}-Anim.png').convert('RGBA'));cO=np.array(Image.open(REF/f'{name}-Offsets.png').convert('RGBA'));cS=np.array(Image.open(REF/f'{name}-Shadow.png').convert('RGBA'));rows=cA.shape[0]//fh0
    anim=np.zeros((rows*fh,n*fw,4),'uint8');off=np.zeros_like(anim);sha=np.zeros_like(anim)
    rush=int(an.find('RushFrame').text) if an.find('RushFrame') is not None else 0;hit=int(an.find('HitFrame').text) if an.find('HitFrame') is not None else n-1;ret=int(an.find('ReturnFrame').text) if an.find('ReturnFrame') is not None else n-1
    for r in range(rows):
        for f in range(n):
            o=cO[r*fh0:(r+1)*fh0,f*fw0:(f+1)*fw0];g=np.nonzero((o[...,1]==255)&(o[...,3]>0));gx,gy=(int(g[1][0]),int(g[0][0])) if len(g[0]) else (fw0//2,fh0//2)
            d=r if rows==8 else 0
            if name=='Sleep':s=SLP[d]
            elif name=='Hurt':s=HURT[d]
            elif name=='Charge':s=flap(CHG[d],[0,1,2,1,0,-1,-2,-1,0,1][f%10])
            elif name in('Attack','Swing','Double'):
                lunge=(rush<=f<=ret) if name=='Attack' else (name=='Swing' and 1<=f<=7) or (name=='Double' and f not in(0,n-1))
                s=ATT[d] if lunge else VIEW[d]
            else:s=flap(VIEW[d],[0,1,2,1,0,-1,-2,-1][f%8])
            cx,cy=centre(s);h,w=s.shape[:2];X=int(round(gx+PADX-cx));Y=int(round(gy+PADY-cy));X=min(max(X,0),fw-w);Y=min(max(Y,0),fh-h)
            anim[r*fh+Y:r*fh+Y+h,f*fw+X:f*fw+X+w]=s
            off[r*fh+PADY:r*fh+PADY+fh0,f*fw+PADX:f*fw+PADX+fw0]=o;sha[r*fh+PADY:r*fh+PADY+fh0,f*fw+PADX:f*fw+PADX+fw0]=cS[r*fh0:(r+1)*fh0,f*fw0:(f+1)*fw0]
    Image.fromarray(anim).save(OUT/f'{name}-Anim.png');Image.fromarray(off).save(OUT/f'{name}-Offsets.png');Image.fromarray(sha).save(OUT/f'{name}-Shadow.png')
    report[name]=dict(frame=[fw,fh],canonical_frame=[fw0,fh0],frames=n,rows=rows,durations=[e.text for e in an.findall('Durations/Duration')])
x.write(OUT/'AnimData.xml',encoding='utf-8',xml_declaration=True)
(OUT/'credits.txt').write_text('2026-09-22 00:00:00.000000\tarena-agent (AI-drawn on-model base set from user reference; canonical CHUNSOFT motion; Mega proposal)\tCUR\tCC_BY-NC_4\t'+','.join(list(report)+['Strike'])+'\n')
with zipfile.ZipFile(O/'0036_0001_mega_clefable_v5_spritecollab.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(OUT.iterdir()):z.write(p,p.name)
# base set board + previews
board=Image.new('RGBA',(sum(s.shape[1]+4 for s in VIEW+[attack_f,attack_p,hurt_f,hurt_p,sleep_f,charge_f]),60),(90,90,90,255));xx=0
for s in VIEW+[attack_f,attack_p,hurt_f,hurt_p,sleep_f,charge_f]:board.alpha_composite(Image.fromarray(s),(xx,58-s.shape[0]));xx+=s.shape[1]+4
board.resize((board.width*4,board.height*4),Image.NEAREST).save(O/'jeu_de_base_on_model_x4.png')
for name in report:
    im=Image.open(OUT/f'{name}-Anim.png').convert('RGBA');b=Image.new('RGBA',im.size,(90,90,90,255));b.alpha_composite(im);sc=2 if im.width>700 else 3;b.resize((im.width*sc,im.height*sc),Image.NEAREST).save(O/f'planche_{name}_x{sc}.png')
    fw,fh=report[name]['frame'];durs=[int(e) for e in report[name]['durations']];frames=[];dd=[]
    for r in range(report[name]['rows']):
        for f in range(report[name]['frames']):
            fr=Image.new('RGBA',(fw,fh),(120,150,120,255));fr.alpha_composite(im.crop((f*fw,r*fh,(f+1)*fw,(r+1)*fh)));frames.append(fr.resize((fw*3,fh*3),Image.NEAREST));dd.append(max(20,durs[f]*1000//60))
    frames[0].save(O/f'apercu_{name}.webp',save_all=True,append_images=frames[1:],duration=dd,loop=0,lossless=True)
(O/'manifest.json').write_text(json.dumps(dict(base_set={'raw_turnaround.png':hashlib.sha256((G4/'raw_turnaround.png').read_bytes()).hexdigest(),'raw_extra_poses.png':hashlib.sha256((G4/'raw_extra_poses.png').read_bytes()).hexdigest()},body_height_px=BODY_H,padding=[PADX,PADY],anims=report,motion='canonical CHUNSOFT green-marker trajectories',views_note='up-right/up-left use the back view (no 3/4-back drawing)',generated=True,runtime_validated=False),indent=1))
print('ok',list(report))
