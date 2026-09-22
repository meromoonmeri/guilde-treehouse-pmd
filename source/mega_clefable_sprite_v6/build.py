"""Mega Clefable V6 — user-validated design (front view of the V4 turnaround), animations DRAWN by the generator as per-view
strips (front / right profile / back / three-quarter), then laid out on the canonical SpriteCollab Clefable grids:
  * 8 direction rows: down=front, down-right=3/4, right=profile, up-right=back, up=back, up-left=back, left=mirror(profile), down-left=mirror(3/4)
  * frame count/durations/Rush-Hit-Return from CHUNSOFT AnimData.xml; each frame placed on the canonical green body-centre marker
    (so the motion path is the SpriteCollab one) with the generated pose for that frame.
  * generated strips: Attack (front/profile/back, 10 f), Swing (front/profile, 9 f), Hurt/Sleep/Charge poses, Idle (front 6 f), Walk (profile 8 f),
    Walk back (8 f), Walk 3/4 (8 f). Double = Attack punch frames on the Double shake path; Withdraw/Dance/Hop/Charge/Rotate use idle/fly cycles
    on their canonical paths (Rotate: view changes per frame like the canonical sheet).
Frames padded (+24,+8) for the wider wings; Offsets/Shadow = canonical shifted; 16-colour palette; 1 px outline; binary alpha."""
from pathlib import Path
import json,zipfile,hashlib
import numpy as np
from PIL import Image
from scipy import ndimage
import xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[2];S=Path(__file__).resolve().parent;G=S/'gen';REF=R/'source/mega_clefable_sprite_v1/references/spritecollab_0036'
O=R/'renders/mega_clefable_sprite_v6';OUT=O/'sprite/0036/0001';OUT.mkdir(parents=True,exist_ok=True)
PAL=np.array([[252,190,176],[246,150,148],[229,156,148],[220,106,108],[211,85,91],[187,51,104],[250,240,162],[236,196,90],[255,255,255],[226,226,236],[74,26,47],[156,96,94],[250,166,160],[96,140,220],[120,40,60],[0,0,0]])
BODY_H=34;PADX,PADY=24,10
def load(path,rows_expected):
    a=np.array(Image.open(path).convert('RGB')).astype(int);bg=np.array([255,0,255]);m=np.abs(a-bg).sum(axis=2)>90
    # key out only magenta-hue pixels (background, halo, generator drop-shadow): B close to R and G low
    mag=(a[...,1]<100)&(np.abs(a[...,0]-a[...,2])<70)&(a[...,2]>90);m&=~mag;m=ndimage.binary_opening(m,iterations=2);m=ndimage.binary_fill_holes(m)
    lab,n=ndimage.label(m);objs=ndimage.find_objects(lab);boxes=[(s[1].start,s[0].start,s[1].stop,s[0].stop) for s in objs if (s[0].stop-s[0].start)>60 and (s[1].stop-s[1].start)>40]
    # group into rows by y centre
    boxes.sort(key=lambda b:(b[1]+b[3])/2);rows=[];
    for b in boxes:
        cy=(b[1]+b[3])/2
        if rows and abs(cy-rows[-1]['cy'])<(b[3]-b[1])*0.6:rows[-1]['b'].append(b);rows[-1]['cy']=(rows[-1]['cy']+cy)/2
        else:rows.append(dict(cy=cy,b=[b]))
    rows=[sorted(r['b'],key=lambda b:b[0]) for r in rows]
    return a,m,rows
def quant(rgb):
    d=((rgb[...,None,:].astype(int)-PAL[None,None,:,:])**2).sum(-1);return PAL[d.argmin(-1)].astype('uint8')
def sprite(a,m,box,scale):
    x0,y0,x1,y1=box;rgb=a[y0:y1,x0:x1].astype('uint8');mm=m[y0:y1,x0:x1]
    pre=np.dstack([rgb*mm[...,None],(mm*255).astype('uint8')]).astype('uint8');w,h=max(2,round((x1-x0)*scale)),max(2,round((y1-y0)*scale))
    im=Image.fromarray(pre,'RGBA').resize((w,h),Image.BOX);arr=np.array(im).astype(float);al=arr[...,3]>100
    rgb2=np.zeros_like(arr[...,:3]);rgb2[al]=arr[...,:3][al]*255/arr[...,3:4][al];q=quant(np.clip(rgb2,0,255).astype('uint8'))
    out=np.dstack([q,(al*255).astype('uint8')]);out[~al]=0;edge=al&~ndimage.binary_erosion(al);out[edge,:3]=0;return out
def M(s):return s[:,::-1].copy()
def strip(path,nrows):
    a,m,rows=load(path,nrows);return a,m,rows
# scale from the Attack front standing frame (frame 0) -> BODY_H
a,m,rows=load(G/'raw_Attack_front.png',3);flat=[b for r in rows for b in r];scale=BODY_H/(flat[0][3]-flat[0][1])
def seq(path,take):
    # per-strip scale: median box height of the strip -> BODY_H (each strip is drawn at its own size)
    a,m,rows=load(path,0);flat=[b for r in rows for b in r];hs=sorted(b[3]-b[1] for b in flat);sc=BODY_H/hs[len(hs)//2];return [sprite(a,m,b,sc) for b in flat][:take],len(flat)
def seqrows(path):
    a,m,rows=load(path,0);out=[]
    for r in rows:
        hs=sorted(b[3]-b[1] for b in r);sc=BODY_H/hs[len(hs)//2];out.append([sprite(a,m,b,sc) for b in r])
    return out
ATT_F,n1=seq(G/'raw_Attack_front.png',10);ATT_P,n2=seq(G/'raw_Attack_profile.png',10);ATT_B,n3=seq(G/'raw_Attack_back.png',10)
SW_F,n4=seq(G/'raw_Swing_front.png',9);SW_P,n5=seq(G/'raw_Swing_profile.png',9)
POSES,n6=seq(G/'raw_Hurt_Sleep_Charge.png',8)
r7=seqrows(G/'raw_Idle_Walk_front_profile.png');IDLE_F=r7[0];WALK_P=r7[1]
r8=seqrows(G/'raw_Idle_Walk_back_3q.png');WALK_B=r8[0];WALK_Q=r8[-1]
print('found',n1,n2,n3,n4,n5,n6,len(IDLE_F),len(WALK_P),len(WALK_B),len(WALK_Q))
def cyc(lst,i):return lst[i%len(lst)] if lst else None
HURT=[POSES[0],POSES[1],POSES[2]] if len(POSES)>=3 else [POSES[0]]*3
SLEEP=[POSES[3],POSES[4]] if len(POSES)>=5 else [POSES[min(3,len(POSES)-1)]]*2
CHG=[POSES[5],POSES[6],POSES[7]] if len(POSES)>=8 else [POSES[-1]]*3
# per-direction view providers: returns sprite for (anim, dir, frame)
FRONT,Q,PROF,BACK=0,1,2,3
DIRVIEW=[(FRONT,False),(Q,False),(PROF,False),(BACK,False),(BACK,False),(BACK,False),(PROF,True),(Q,True)]
def pick(name,d,f,n):
    view,mir=DIRVIEW[d]
    if name=='Attack':
        base={FRONT:ATT_F,Q:ATT_F,PROF:ATT_P,BACK:ATT_B}[view];s=cyc(base,f)
    elif name=='Swing':
        base={FRONT:SW_F,Q:SW_F,PROF:SW_P,BACK:ATT_B}[view];s=cyc(base,f)
    elif name=='Double':
        base={FRONT:ATT_F,Q:ATT_F,PROF:ATT_P,BACK:ATT_B}[view];s=base[0] if f in(0,n-1) else base[4+(f%4)]
    elif name=='Hurt':s=HURT[{FRONT:0,Q:0,PROF:1,BACK:2}[view]]
    elif name=='Sleep':s=SLEEP[f%2]
    elif name=='Charge':s=CHG[{FRONT:0,Q:0,PROF:1,BACK:2}[view]]
    elif name=='Idle':s={FRONT:cyc(IDLE_F,f),Q:cyc(WALK_Q,f),PROF:cyc(WALK_P,f),BACK:cyc(WALK_B,f)}[view]
    else:  # Walk, Withdraw, Dance, Hop, Rotate: fly cycles
        s={FRONT:cyc(IDLE_F,f),Q:cyc(WALK_Q,f),PROF:cyc(WALK_P,f),BACK:cyc(WALK_B,f)}[view]
    return M(s) if mir else s
def centre(s):
    al=s[...,3]>0;ys,xs=np.nonzero(al);return xs.mean(),ys.min()+0.6*(ys.max()-ys.min())
x=ET.parse(REF/'AnimData.xml');root=x.getroot();report={}
ROT=[0,1,2,3,4,5,6,7,0]  # Rotate: facing per frame (canonical: full turn)
for an in root.findall('Anims/Anim'):
    name=an.find('Name').text
    if an.find('CopyOf') is not None:continue
    fw0,fh0=int(an.find('FrameWidth').text),int(an.find('FrameHeight').text);fw,fh=fw0+2*PADX,fh0+2*PADY
    an.find('FrameWidth').text=str(fw);an.find('FrameHeight').text=str(fh);n=len(an.findall('Durations/Duration'))
    cO=np.array(Image.open(REF/f'{name}-Offsets.png').convert('RGBA'));cS=np.array(Image.open(REF/f'{name}-Shadow.png').convert('RGBA'));rows=cO.shape[0]//fh0
    anim=np.zeros((rows*fh,n*fw,4),'uint8');off=np.zeros_like(anim);sha=np.zeros_like(anim)
    for r in range(rows):
        for f in range(n):
            o=cO[r*fh0:(r+1)*fh0,f*fw0:(f+1)*fw0];g=np.nonzero((o[...,1]==255)&(o[...,3]>0));gx,gy=(int(g[1][0]),int(g[0][0])) if len(g[0]) else (fw0//2,fh0//2)
            d=r if rows==8 else 0
            if name=='Rotate':d=(r+ROT[f])%8
            s=pick(name,d,f,n);cx,cy=centre(s);h,w=s.shape[:2]
            if w>fw-2 or h>fh-2:
                k=min((fw-2)/w,(fh-2)/h);s=np.array(Image.fromarray(s).resize((int(w*k),int(h*k)),Image.NEAREST));cx,cy=centre(s);h,w=s.shape[:2]
            X=int(round(gx+PADX-cx));Y=int(round(gy+PADY-cy));X=min(max(X,1),fw-w-1);Y=min(max(Y,1),fh-h-1)
            anim[r*fh+Y:r*fh+Y+h,f*fw+X:f*fw+X+w]=s
            off[r*fh+PADY:r*fh+PADY+fh0,f*fw+PADX:f*fw+PADX+fw0]=o;sha[r*fh+PADY:r*fh+PADY+fh0,f*fw+PADX:f*fw+PADX+fw0]=cS[r*fh0:(r+1)*fh0,f*fw0:(f+1)*fw0]
    Image.fromarray(anim).save(OUT/f'{name}-Anim.png');Image.fromarray(off).save(OUT/f'{name}-Offsets.png');Image.fromarray(sha).save(OUT/f'{name}-Shadow.png')
    report[name]=dict(frame=[fw,fh],canonical_frame=[fw0,fh0],frames=n,rows=rows,durations=[e.text for e in an.findall('Durations/Duration')])
x.write(OUT/'AnimData.xml',encoding='utf-8',xml_declaration=True)
(OUT/'credits.txt').write_text('2026-09-22 00:00:00.000000\tarena-agent (AI-drawn per-view animation strips from user-validated design; canonical CHUNSOFT layout/motion; Mega proposal)\tCUR\tCC_BY-NC_4\t'+','.join(list(report)+['Strike'])+'\n')
with zipfile.ZipFile(O/'0036_0001_mega_clefable_v6_spritecollab.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(OUT.iterdir()):z.write(p,p.name)
for name in report:
    im=Image.open(OUT/f'{name}-Anim.png').convert('RGBA');b=Image.new('RGBA',im.size,(90,90,90,255));b.alpha_composite(im);sc=2 if im.width>700 else 3;b.resize((im.width*sc,im.height*sc),Image.NEAREST).save(O/f'planche_{name}_x{sc}.png')
    fw,fh=report[name]['frame'];durs=[int(e) for e in report[name]['durations']];frames=[];dd=[]
    for r in range(report[name]['rows']):
        for f in range(report[name]['frames']):
            fr=Image.new('RGBA',(fw,fh),(120,150,120,255));fr.alpha_composite(im.crop((f*fw,r*fh,(f+1)*fw,(r+1)*fh)));frames.append(fr.resize((fw*3,fh*3),Image.NEAREST));dd.append(max(20,durs[f]*1000//60))
    frames[0].save(O/f'apercu_{name}.webp',save_all=True,append_images=frames[1:],duration=dd,loop=0,lossless=True)
(O/'manifest.json').write_text(json.dumps(dict(design_reference='user upload image-1.png (front view of V4 turnaround) -> references/',strips={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(G.glob('raw_*.png'))},found_frames=dict(attack_front=n1,attack_profile=n2,attack_back=n3,swing_front=n4,swing_profile=n5,poses=n6,idle_front=len(IDLE_F),walk_profile=len(WALK_P),walk_back=len(WALK_B),walk_3q=len(WALK_Q)),body_height_px=BODY_H,padding=[PADX,PADY],anims=report,generated=True,runtime_validated=False),indent=1))
print('ok')
