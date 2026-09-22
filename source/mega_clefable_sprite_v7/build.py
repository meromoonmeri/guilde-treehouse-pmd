"""Mega Clefable V7 — validated design; flying Walk/Idle; sparkle-charge Attack; SpriteCollab-style presentation (GIF per anim).
Strips (gen/raw_*.png, flat magenta, generator): raw_Fly_front_profile_back (3 rows: fly cycle front/profile/back — frames 1-6 kept),
raw_Fly_3q_Sparkle_3q (row1 3/4 fly, row2 3/4 sparkle charge), raw_Sparkle_Attack (3 rows sparkle charge front/profile/back),
V6 raw_Hurt_Sleep_Charge (hurt f/p/b, sleep x2, charge f/p/b).
Rules: Walk/Idle/Hop/Dance/Withdraw/Rotate = fly cycle on the canonical CHUNSOFT path (green markers). Attack/Strike/Swing/Double/Charge
= character stays in place, sparkles appear then vanish (phase mapped on the canonical frame count). Same body height everywhere,
one 16-colour palette, binary alpha, 1 px outline around the body; eyes re-stamped from the source blue pixels (box-filter loses them)."""
from pathlib import Path
import json,zipfile,hashlib
import numpy as np
from PIL import Image
from scipy import ndimage
import xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[2];S=Path(__file__).resolve().parent;G=S/'gen';G6=R/'source/mega_clefable_sprite_v6/gen';REF=R/'source/mega_clefable_sprite_v1/references/spritecollab_0036'
O=R/'renders/mega_clefable_sprite_v7';OUT=O/'sprite/0036/0001';OUT.mkdir(parents=True,exist_ok=True)
PAL=np.array([[252,190,176],[246,150,148],[229,156,148],[220,106,108],[211,85,91],[187,51,104],[250,240,162],[236,196,90],[255,255,255],[226,226,236],[74,26,47],[156,96,94],[250,166,160],[70,120,230],[120,40,60],[0,0,0]])
BODY_H=34;PADX,PADY=24,10
def keymask(a):
    bg=(a[...,1]<70)&(a[...,2]>190)&(a[...,0]>200)&(np.abs(a[...,0]-a[...,2])<45)
    halo=(a[...,1]<60)&(a[...,2]>150)&(a[...,0]>150)&(np.abs(a[...,0]-a[...,2])<60)
    sh=(a[...,1]<60)&(a[...,0]>120)&(a[...,0]<215)&(a[...,2]>120)&(np.abs(a[...,0]-a[...,2])<40)
    return ~(bg|halo|sh)
def load(path,sparkle=False):
    a=np.array(Image.open(path).convert('RGB')).astype(int);m=keymask(a)
    body=ndimage.binary_opening(m,iterations=2);body=ndimage.binary_fill_holes(body)
    lab,n=ndimage.label(body);objs=ndimage.find_objects(lab);boxes=[(s[1].start,s[0].start,s[1].stop,s[0].stop) for s in objs if (s[0].stop-s[0].start)>120 and (s[1].stop-s[1].start)>60]
    boxes.sort(key=lambda b:(b[1]+b[3])/2);rows=[]
    for b in boxes:
        cy=(b[1]+b[3])/2
        if rows and abs(cy-rows[-1]['cy'])<(b[3]-b[1])*0.6:rows[-1]['b'].append(b)
        else:rows.append(dict(cy=cy,b=[b]))
    rows=[sorted(r['b'],key=lambda b:b[0]) for r in rows]
    if sparkle:
        H=a.shape[0];out=[]
        for r in rows:
            hb=int(np.median([b[3]-b[1] for b in r]));top=int(np.median([b[1] for b in r]))-hb//3;bot=int(np.median([b[3] for b in r]))+hb//3;cells=[]
            for i,b in enumerate(r):
                l=0 if i==0 else (r[i-1][2]+b[0])//2;rt=a.shape[1] if i==len(r)-1 else (b[2]+r[i+1][0])//2
                cells.append((l,max(0,top),rt,min(H,bot)))
            out.append(cells)
        rows=out
    return a,m,rows
def quant(rgb):
    d=((rgb[...,None,:].astype(int)-PAL[None,None,:,:])**2).sum(-1);return PAL[d.argmin(-1)].astype('uint8')
def sprite(a,m,box,scale,trim_border=False):
    x0,y0,x1,y1=box;rgb=a[y0:y1,x0:x1].astype('uint8');mm=m[y0:y1,x0:x1]
    pre=np.dstack([rgb*mm[...,None],(mm*255).astype('uint8')]).astype('uint8');w,h=max(2,round((x1-x0)*scale)),max(2,round((y1-y0)*scale))
    im=Image.fromarray(pre,'RGBA').resize((w,h),Image.BOX);arr=np.array(im).astype(float);al=arr[...,3]>100
    rgb2=np.zeros_like(arr[...,:3]);rgb2[al]=arr[...,:3][al]*255/arr[...,3:4][al];q=quant(np.clip(rgb2,0,255).astype('uint8'))
    eye=(rgb[...,2].astype(int)>rgb[...,0].astype(int)+25)&(rgb[...,2]>120)&mm
    lab,k=ndimage.label(eye)
    for i in range(1,k+1):
        ys,xs=np.nonzero(lab==i)
        if len(ys)<6:continue
        cy,cx=int(round(ys.mean()*scale)),int(round(xs.mean()*scale));eh=max(2,int(round((ys.max()-ys.min()+1)*scale)));ew=max(1,int(round((xs.max()-xs.min()+1)*scale)))
        y0e,x0e=max(0,cy-eh//2),max(0,cx-ew//2);q[y0e:y0e+eh,x0e:x0e+ew]=PAL[13];al[y0e:y0e+eh,x0e:x0e+ew]=True
        if eh>=3:q[y0e,x0e:x0e+ew]=PAL[10]
    out=np.dstack([q,(al*255).astype('uint8')]);out[~al]=0
    if trim_border:
        lab,n=ndimage.label(al);bad=set(np.unique(np.concatenate([lab[0],lab[-1],lab[:,0],lab[:,-1]])))-{0}
        for kk in bad:
            if (lab==kk).sum()<0.25*al.sum():al[lab==kk]=False
        out[~al]=0
    lab,n=ndimage.label(al)
    if n:
        big=np.argmax(np.bincount(lab.ravel())[1:])+1;body=lab==big;edge=body&~ndimage.binary_erosion(body);out[edge,:3]=0
    return out
def rows_scaled(path,sparkle=False):
    a,m,rows=load(path,sparkle);_,_,br=load(path,False);out=[]
    for r,rb in zip(rows,br):
        hs=sorted(b[3]-b[1] for b in rb);sc=BODY_H/hs[len(hs)//2];out.append([sprite(a,m,b,sc,trim_border=sparkle) for b in r])
    return out
FLY=rows_scaled(G/'raw_Fly_front_profile_back.png');FLY_F,FLY_P,FLY_B=FLY[0][:6],FLY[1][:6],FLY[2][:6]
FLY_Q=rows_scaled(G/'raw_Fly_3q_Sparkle_3q.png')[0]
SPK_Q=rows_scaled(G/'raw_Fly_3q_Sparkle_3q.png',sparkle=True)[1]
SPK=rows_scaled(G/'raw_Sparkle_Attack.png',sparkle=True);SPK_F,SPK_P,SPK_B=SPK[0],SPK[1],SPK[2]
POSES=[s for r in rows_scaled(G6/'raw_Hurt_Sleep_Charge.png') for s in r];HURT=POSES[0:3];SLEEP=POSES[3:5];CHG=POSES[5:8]
print('frames: fly',[len(x) for x in (FLY_F,FLY_P,FLY_B,FLY_Q)],'sparkle',[len(x) for x in (SPK_F,SPK_P,SPK_B,SPK_Q)],'poses',len(POSES))
def M(s):return s[:,::-1].copy()
FRONT,Q3,PROF,BACK=0,1,2,3
DIRVIEW=[(FRONT,False),(Q3,False),(PROF,False),(BACK,False),(BACK,False),(BACK,False),(PROF,True),(Q3,True)]
def cyc(l,i):return l[i%len(l)]
def pick(name,d,f,n):
    view,mir=DIRVIEW[d];fly={FRONT:FLY_F,Q3:FLY_F,PROF:FLY_P,BACK:FLY_B}[view]
    # 3/4 strips: eyes missing on 3 fly frames / cap missing on sparkle frames -> front sets used (audit)
    spk={FRONT:SPK_F,Q3:SPK_F,PROF:SPK_P,BACK:SPK_B}[view];spk={FRONT:SPK_F,Q3:SPK_F,PROF:SPK_P,BACK:SPK_B}[view]  # 3/4 sparkle strip lost the white cap -> front set
    if name in('Attack','Swing','Double','Charge'):
        k=len(spk);i=min(k-1,int(round(f*(k-1)/max(1,n-1))));s=spk[i]
    elif name=='Hurt':s=HURT[{FRONT:0,Q3:0,PROF:1,BACK:2}[view]]
    elif name=='Sleep':s=SLEEP[f%2]
    else:s=cyc(fly,f)
    return M(s) if mir else s
def centre(s):
    al=s[...,3]>0;lab,n=ndimage.label(al);big=np.argmax(np.bincount(lab.ravel())[1:])+1;ys,xs=np.nonzero(lab==big);return xs.mean(),ys.min()+0.6*(ys.max()-ys.min())
x=ET.parse(REF/'AnimData.xml');root=x.getroot();report={}
ROT=[0,1,2,3,4,5,6,7,0]
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
            if name in('Attack','Swing','Double','Charge'):
                o0=cO[r*fh0:(r+1)*fh0,0:fw0];g0=np.nonzero((o0[...,1]==255)&(o0[...,3]>0));gx,gy=int(g0[1][0]),int(g0[0][0])
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
(OUT/'credits.txt').write_text('2026-09-22 00:00:00.000000\tarena-agent (AI-drawn strips from user-validated design; canonical CHUNSOFT layout/motion; Mega proposal)\tCUR\tCC_BY-NC_4\t'+','.join(list(report)+['Strike'])+'\n')
with zipfile.ZipFile(O/'0036_0001_mega_clefable_v7_spritecollab.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(OUT.iterdir()):z.write(p,p.name)
# SpriteCollab-style presentation: one GIF per animation (direction down, like the site tiles) + 8-direction GIF + html page
ORDER=['Idle','Walk','Sleep','Hurt','Attack','Charge','Dance','Withdraw','Swing','Double','Rotate','Hop']
def gif(frames,dd,path):
    fr=[f.convert('RGBA') for f in frames];bg=(84,84,84)
    # one shared palette for every frame (per-frame adaptive palettes break GIF colours)
    cols=[tuple(c) for c in PAL.tolist()]+[bg]
    pimg=Image.new('P',(1,1));flat=[v for c in cols for v in c];pimg.putpalette(flat+[0]*(768-len(flat)))
    outf=[]
    for f in fr:
        b=Image.new('RGBA',f.size,bg+(255,));b.alpha_composite(f);outf.append(b.convert('RGB').quantize(palette=pimg,dither=Image.Dither.NONE))
    outf[0].save(path,save_all=True,append_images=outf[1:],duration=dd,loop=0,optimize=False)
for name in ORDER:
    im=Image.open(OUT/f'{name}-Anim.png').convert('RGBA');b=Image.new('RGBA',im.size,(90,90,90,255));b.alpha_composite(im);sc=2 if im.width>700 else 3;b.resize((im.width*sc,im.height*sc),Image.NEAREST).save(O/f'planche_{name}_x{sc}.png')
    fw,fh=report[name]['frame'];durs=[int(e) for e in report[name]['durations']];n=report[name]['frames'];rows=report[name]['rows']
    for tag,rr in (('',[0]),('_8dir',list(range(rows)))):
        frames=[];dd=[]
        for r in rr:
            for f in range(n):
                fr=im.crop((f*fw,r*fh,(f+1)*fw,(r+1)*fh)).resize((fw*2,fh*2),Image.NEAREST);frames.append(fr);dd.append(max(20,durs[f]*1000//60))
        gif(frames,dd,O/f'anim_{name}{tag}.gif')
html=['<!doctype html><meta charset=utf-8><title>#0036 Clefable — Mega (0001) proposition</title><style>body{background:#1c1c1c;color:#eee;font-family:sans-serif;text-align:center}h5{margin:20px 0 4px}.grid{display:flex;flex-wrap:wrap;justify-content:center;gap:18px}.t{background:#2a2a2a;border-radius:8px;padding:10px;width:150px}.t img{image-rendering:pixelated;height:120px}.t div{margin-top:6px;font-size:14px}</style>',
'<h5>0036 Clefable</h5><h6>Mega (0001) — proposition générée, design validé utilisateur</h6><h5>Sprites</h5><div class=grid>']
for name in ORDER:html.append(f'<div class=t><img src="anim_{name}.gif"><div>{name}</div></div>')
html.append('</div><h5>8 directions</h5><div class=grid>')
for name in ORDER:html.append(f'<div class=t><img src="anim_{name}_8dir.gif"><div>{name}</div></div>')
html.append('</div>');(O/'index.html').write_text('\n'.join(html))
(O/'manifest.json').write_text(json.dumps(dict(design_reference='user-validated front view (source/mega_clefable_sprite_v6/references)',strips={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(list(G.glob('raw_*.png'))+[G6/'raw_Hurt_Sleep_Charge.png'])},body_height_px=BODY_H,padding=[PADX,PADY],anims=report,generated=True,runtime_validated=False),indent=1))
print('ok')
