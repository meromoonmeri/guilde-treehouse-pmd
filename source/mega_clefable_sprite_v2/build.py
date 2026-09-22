"""Mega Clefable SpriteCollab package V2 — DRAWN by the image generator (gen/mega_clefable_8dir_sheet.png, prompted with
the canonical Clefable 8-direction sheet as style reference), then converted to true pixel art:
 background keying -> 40 px tall -> 16-colour quantization -> 1 px black outline -> 56x48 frames -> 8 direction rows
 (5 drawn views, the 3 remaining ones mirrored as in the CHUNSOFT sheets).
Animations built from these views with pixel-level transforms (bob, wing flap = wing columns shifted, walk = alternate leg pixels,
hurt = tilt+flash-free recoil, sleep = squashed body, attack = lunge). Offsets/Shadow generated per frame (green body centre,
red/blue hands at the cuff positions, black head; shadow disk under the feet). AnimData.xml with the canonical Clefable durations.
Disclosed as generated art (not CHUNSOFT-native)."""
from pathlib import Path
import json,zipfile,hashlib
import numpy as np
from PIL import Image
from scipy import ndimage
R=Path(__file__).resolve().parents[2];S=Path(__file__).resolve().parent;G=S/'gen';O=R/'renders/mega_clefable_sprite_v2';OUT=O/'sprite/0036/0001';OUT.mkdir(parents=True,exist_ok=True)
FW,FH=64,56;H=36;BASE_Y=FH-3  # feet line
im=Image.open(G/'mega_clefable_8dir_sheet.png').convert('RGB');a=np.array(im).astype(int)
bg=np.array([187,200,206]);mask=np.abs(a-bg).sum(axis=2)>40;mask=ndimage.binary_closing(mask,iterations=2);mask=ndimage.binary_fill_holes(mask)
BOXES=[(17,80,310,268),(341,62,569,270),(644,62,870,269),(957,62,1140,270),(1229,62,1484,270)]  # down, down-left, left, up-left, up
def cut(b):
    x0,y0,x1,y1=b;rgba=np.dstack([a[y0:y1,x0:x1].astype('uint8'),(mask[y0:y1,x0:x1]*255).astype('uint8')]);src=Image.fromarray(rgba,'RGBA')
    s=H/src.height;src=src.resize((round(src.width*s),H),Image.BOX);arr=np.array(src);al=arr[...,3]>127
    q=src.convert('RGB').quantize(colors=15,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE).convert('RGB');qa=np.dstack([np.array(q),(al*255).astype('uint8')])
    edge=al&~ndimage.binary_erosion(al);qa[edge,:3]=0;qa[~al]=0;return Image.fromarray(qa)
views=[cut(b) for b in BOXES]
def frame(view,dx=0,dy=0,squash=0,wing=0,legs=0,lean=0):
    """place a view into a 56x48 frame with simple pixel transforms"""
    v=np.array(view);h,w=v.shape[:2]
    if squash:  # squash vertically by `squash` px (keeps width)
        v=np.array(Image.fromarray(v).resize((w,h-squash),Image.NEAREST));h-=squash
    out=np.zeros((h,w,4),'uint8')
    body_cols=np.arange(w);cx=w//2
    for x in range(w):
        col=v[:,x].copy()
        # wing flap: columns far from centre move up/down
        d=abs(x-cx)/max(1,cx);sh=int(round(wing*d*d*2))
        if legs and x!=cx:  # walk: alternate legs -> shift bottom 6 rows by 1px for left/right halves
            shift=legs if x<cx else -legs
            if shift>0:col[h-1]=0  # this leg lifted: drop its last row
        col=np.roll(col,sh,axis=0)
        if sh>0:col[:sh]=0
        elif sh<0:col[sh:]=0
        out[:,x]=col
    if lean:  # shear: rows shifted horizontally proportional to height (top moves `lean` px)
        sheared=np.zeros_like(out)
        for y in range(h):
            s=int(round(lean*(h-1-y)/(h-1)));sheared[y]=np.roll(out[y],s,axis=0)
        out=sheared
    fr=Image.new('RGBA',(FW,FH));fr.alpha_composite(Image.fromarray(out),((FW-w)//2+dx,BASE_Y-h+dy));return fr
def mirror(v):return v.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
DIRS=[(0,False),(1,True),(2,True),(3,True),(4,False),(3,False),(2,False),(1,False)]  # down,down-right,right,up-right,up,up-left,left,down-left
def dirview(i):v,m=DIRS[i];return mirror(views[v]) if m else views[v]
def markers(fr,facing):
    """Offsets: green centre, black head, red/blue hands from cuff (dark) pixels; Shadow: white centre + green/red/blue disc"""
    ar=np.array(fr);al=ar[...,3]>0;ys,xs=np.nonzero(al)
    if not len(ys):return Image.new('RGBA',fr.size),Image.new('RGBA',fr.size)
    cy=int((ys.min()+ys.max())/2);cx=int(round(xs.mean()));hy=ys.min()+3
    dark=al&(ar[...,0]<60)&(ar[...,1]<60)&(ar[...,2]<60)&~(al&~ndimage.binary_erosion(al,iterations=2))
    hy_,hx_=np.nonzero(dark);left=(cx-6,cy+4);right=(cx+6,cy+4)
    if len(hx_):
        l=hx_<cx
        if l.any():left=(int(hx_[l].mean()),int(hy_[l].mean()))
        if (~l).any():right=(int(hx_[~l].mean()),int(hy_[~l].mean()))
    off=np.zeros_like(ar);sh=np.zeros_like(ar)
    def put(img,p,c):
        x,y=min(max(p[0],0),FW-1),min(max(p[1],0),FH-1);img[y,x,:3]=np.maximum(img[y,x,:3],c);img[y,x,3]=255
    put(off,(cx,cy),(0,255,0));put(off,(cx,hy),(0,0,0));put(off,left,(255,0,0));put(off,right,(0,0,255))
    fy=ys.max()-1;yy,xx=np.mgrid[:FH,:FW]
    for rad,c in [(9,(0,0,255)),(7,(255,0,0)),(5,(0,255,0))]:  # nested exclusive discs like the canonical sheets
        d=((xx-cx)/rad)**2+((yy-fy)/(rad*0.5))**2<=1;sh[d,:3]=c;sh[d,3]=255
    put(sh,(cx,fy),(255,255,255));return Image.fromarray(off),Image.fromarray(sh)
ANIMS={  # name: (durations, frame builder(direction index, frame index) )
 'Idle':(['30','6','6','6','6','6'],lambda i,f:frame(dirview(i),dy=[0,0,-1,-1,0,0][f],wing=[0,1,2,2,1,0][f])),
 'Walk':(['8','6','6','6','8','6','6','6'],lambda i,f:frame(dirview(i),dy=[0,-1,0,0,0,-1,0,0][f],legs=[0,1,1,0,0,-1,-1,0][f],wing=[0,1,2,1,0,1,2,1][f])),
 'Hurt':(['2','8'],lambda i,f:frame(dirview(i),lean=[0,3][f],dy=[0,1][f],wing=[-2,-3][f])),
 'Sleep':(['30','35'],lambda i,f:frame(dirview(i),squash=[10,12][f],wing=-3)),
 'Attack':(['2','4','1','1','1','2','2','2','2','2'],lambda i,f:frame(dirview(i),lean=[0,-2,-2,2,4,3,2,1,0,0][f],dy=[0,1,1,-1,-2,-1,0,0,0,0][f],wing=[0,-2,-2,3,4,3,2,1,0,0][f])),
 'Charge':(['2']*10,lambda i,f:frame(dirview(i),dy=[0,0,-1,-1,-2,-2,-1,-1,0,0][f],wing=[0,1,2,3,4,3,2,1,0,0][f])),
 'Dance':(['6','4','6','4','6','4'],lambda i,f:frame(dirview(i),lean=[-2,0,2,0,-2,0][f],dy=[0,-1,0,-1,0,-1][f],wing=[3,0,3,0,3,0][f])),
 'Hop':(['2','1','2','3','4','4','3','2','1','2'],lambda i,f:frame(dirview(i),dy=[0,-2,-5,-8,-10,-10,-8,-5,-2,0][f],wing=[0,2,3,4,4,4,3,2,1,0][f])),
}
report={};xml=['<?xml version="1.0" ?>','<AnimData>',' <ShadowSize>1</ShadowSize>',' <Anims>']
IDX={'Walk':0,'Attack':1,'Strike':2,'Sleep':5,'Hurt':6,'Idle':7,'Charge':11,'Dance':13,'Hop':10}
for name,(durs,fn) in ANIMS.items():
    n=len(durs);anim=Image.new('RGBA',(FW*n,FH*8));off=Image.new('RGBA',anim.size);sh=Image.new('RGBA',anim.size)
    for i in range(8):
        for f in range(n):
            fr=fn(i,f);o,s=markers(fr,i);anim.alpha_composite(fr,(f*FW,i*FH));off.alpha_composite(o,(f*FW,i*FH));sh.alpha_composite(s,(f*FW,i*FH))
    anim.save(OUT/f'{name}-Anim.png');off.save(OUT/f'{name}-Offsets.png');sh.save(OUT/f'{name}-Shadow.png')
    xml+=['  <Anim>',f'   <Name>{name}</Name>',f'   <Index>{IDX[name]}</Index>',f'   <FrameWidth>{FW}</FrameWidth>',f'   <FrameHeight>{FH}</FrameHeight>']
    if name=='Attack':xml+=['   <RushFrame>2</RushFrame>','   <HitFrame>4</HitFrame>','   <ReturnFrame>6</ReturnFrame>']
    xml+=['   <Durations>']+[f'    <Duration>{d}</Duration>' for d in durs]+['   </Durations>','  </Anim>']
    report[name]=dict(frames=n,durations=durs,sheet=list(anim.size))
xml+=['  <Anim>','   <Name>Strike</Name>','   <Index>2</Index>','   <CopyOf>Attack</CopyOf>','  </Anim>',' </Anims>','</AnimData>','']
(OUT/'AnimData.xml').write_text('\n'.join(xml))
(OUT/'credits.txt').write_text('2026-09-22 00:00:00.000000\tarena-agent (AI-generated drawing, pixel-converted; Mega proposal)\tCUR\tCC_BY-NC_4\t'+','.join(list(ANIMS)+['Strike'])+'\n')
with zipfile.ZipFile(O/'0036_0001_mega_clefable_v2_spritecollab.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(OUT.iterdir()):z.write(p,p.name)
# review boards
idle=Image.open(OUT/'Idle-Anim.png');walk=Image.open(OUT/'Walk-Anim.png')
for nm,img in [('Idle',idle),('Walk',walk),('Attack',Image.open(OUT/'Attack-Anim.png')),('Sleep',Image.open(OUT/'Sleep-Anim.png')),('Hop',Image.open(OUT/'Hop-Anim.png'))]:
    b=Image.new('RGBA',img.size,(90,90,90,255));b.alpha_composite(img.convert('RGBA'));b.resize((b.width*3,b.height*3),Image.NEAREST).save(O/f'planche_{nm}_x3.png')
# animated preview: Walk down + Idle right, 8 dirs Walk loop
frames=[]
for i in range(8):
    for f in range(8):
        fr=walk.crop((f*FW,i*FH,f*FW+FW,i*FH+FH)).convert('RGBA');b=Image.new('RGBA',(FW,FH),(120,150,120,255));b.alpha_composite(fr);frames.append(b.resize((FW*4,FH*4),Image.NEAREST))
frames[0].save(O/'apercu_walk_8_directions.webp',save_all=True,append_images=frames[1:],duration=110,loop=0,lossless=True)
colours=len(np.unique(np.array(idle.convert('RGBA'))[np.array(idle.convert('RGBA'))[...,3]>0][:,:3],axis=0))
(O/'manifest.json').write_text(json.dumps(dict(generator_sheet=hashlib.sha256((G/'mega_clefable_8dir_sheet.png').read_bytes()).hexdigest(),style_reference='CHUNSOFT Clefable Idle sheet (SpriteCollab@aae4cee2 sprite/0036)',frame=[FW,FH],anims=report,colours_idle=colours,generated=True,runtime_validated=False),indent=1))
print('ok',report.keys(),'colours',colours)
