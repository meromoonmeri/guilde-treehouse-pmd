"""V3: authored deep sky without motifs (smooth dithered gradient + faint far glow), and
PMD-style star animation on its own layers: twinkling stars (3-phase cross motifs), a faint
milky band, and shooting stars on a separate layer. Reuses V2 panorama/mist/clouds/terrain/moon
PNGs from disk unchanged. All pixels authored/generated; nothing native certified.
"""
from pathlib import Path
import json, io, zipfile, math, hashlib
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image, _webp
R=Path(__file__).resolve().parents[2];O=R/'renders/sky_peak_prairie_v1';V2=O/'v2';V=O/'v3';P='SkyPeakPrairieV3';P2='SkyPeakPrairieV2'
W,H=960,864;SKY_H=470  # sky visible above mountain ridge (~y 355+); stars stay above y=SKY_H
FULL='--full' in __import__('sys').argv
import sys;sys.path.insert(0,str(R/'source/cote_v4_abyss'));from night import night
def png(im):b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def L2(name):return Image.open(V2/'calques'/f'{P2}_{name}.png').convert('RGBA')
(V/'calques').mkdir(parents=True,exist_ok=True)
rng=np.random.default_rng(20260921)

# ---- 01 sky: authored gradient, no motifs. Deep indigo zenith -> teal-blue glow at the far horizon,
# plus an extremely faint wide glow around the moon region. Ordered 4x4 Bayer dither to avoid banding.
yy,xx=np.mgrid[:H,:W].astype(float)
t=np.clip(yy/(H-1),0,1)
stops=[(0.00,(4,6,22)),(0.35,(9,16,48)),(0.62,(20,40,92)),(0.80,(38,78,138)),(1.00,(70,120,170))]
def ramp(t):
    out=np.zeros((*t.shape,3))
    for (t0,c0),(t1,c1) in zip(stops,stops[1:]):
        m=(t>=t0)&(t<=t1);u=((t-t0)/(t1-t0))[m];u=u*u*(3-2*u)
        out[m]=np.array(c0)*(1-u[:,None])+np.array(c1)*u[:,None]
    return out
rgb=ramp(t)
mx,my=716+64,48+64  # moon centre from V2 manifest
glow=np.exp(-(((xx-mx)/260)**2+((yy-my)/200)**2))[:,:,None]*np.array([10,12,20])
rgb+=glow
bayer=np.array([[0,8,2,10],[12,4,14,6],[3,11,1,9],[15,7,13,5]])/16-0.5
rgb+=bayer[np.arange(H)[:,None]%4,np.arange(W)[None,:]%4][:,:,None]*1.0
sky=Image.fromarray(np.dstack([np.clip(np.rint(rgb),0,255).astype('uint8'),np.full((H,W),255,'uint8')]))
sky.save(V/'calques'/f'{P}_01_ciel_profond.png')

# ---- star motifs in PMD style: phase 0 = 1px dot, 1 = 3px plus, 2 = 5px plus with faint diagonals/halo
def motif(phase,color):
    c=np.array(color,dtype=int);s=np.zeros((7,7,4),dtype=int)
    def put(x,y,a):
        s[y,x,:3]=c;s[y,x,3]=max(s[y,x,3],a)
    if phase==0:put(3,3,235)
    elif phase==1:
        put(3,3,255)
        for d in (-1,1):put(3+d,3,200);put(3,3+d,200)
    else:
        put(3,3,255)
        for d in (-1,1):put(3+d,3,255);put(3,3+d,255)
        for d in (-2,2):put(3+d,3,150);put(3,3+d,150)
        for dx in (-1,1):
            for dy in (-1,1):put(3+dx,3+dy,90)
    return s
COLORS=[(255,255,255),(214,232,255),(255,244,214),(190,215,255)]
# star field: brighter twinklers + many faint fixed dots + a soft milky band (dense faint dots along a diagonal)
def gen_stars():
    stars=[]
    for _ in range(220):  # twinklers
        stars.append(dict(x=int(rng.integers(3,W-3)),y=int(rng.integers(3,SKY_H-40)),color=COLORS[int(rng.integers(0,4))],period=int(rng.integers(6,14)),offset=int(rng.integers(0,14)),kind='twinkle',maxphase=2 if rng.random()<.5 else 1))
    for _ in range(320):  # faint statics
        stars.append(dict(x=int(rng.integers(0,W)),y=int(rng.integers(0,SKY_H-20)),color=COLORS[int(rng.integers(0,4))],kind='static',alpha=int(rng.integers(110,210))))
    for _ in range(700):  # milky band from upper-left to mid-right
        u=rng.random();x=int(u*W);yc=60+u*220+40*math.sin(u*4);y=int(np.clip(rng.normal(yc,26),0,SKY_H-30))
        stars.append(dict(x=x,y=y,color=(200,210,240),kind='static',alpha=int(rng.integers(40,110))))
    return stars
STARS=gen_stars()
# avoid the moon disc and the mountain band
STARS=[s for s in STARS if (s['x']-mx)**2+(s['y']-my)**2>95**2]
FPS_STARS=8;N_STARS=64  # 8 s loop
def star_frame(i):
    a=np.zeros((H,W,4),dtype=int)
    for s in STARS:
        x,y=s['x'],s['y']
        if s['kind']=='static':
            a[y,x,:3]=s['color'];a[y,x,3]=max(a[y,x,3],s['alpha']);continue
        k=(i+s['offset'])%s['period']
        # PMD-like: mostly resting at dot, brief bloom: dot,dot,...,plus,big,plus
        seq=[0]*(s['period']-5)+[1,s['maxphase'],s['maxphase'],1,0]
        m=motif(seq[k],s['color'])
        y0,x0=y-3,x-3;sub=a[y0:y0+7,x0:x0+7];sub[:]=np.where(m[:,:,3:]>sub[:,:,3:],m,sub)
    return Image.fromarray(np.clip(a,0,255).astype('uint8'))
SF=V/'etoiles_frames';SF.mkdir(exist_ok=True);star_frames=[]
for i in range(N_STARS):
    f=star_frame(i);f.save(SF/f'{P}_etoiles_{i:02d}.png');star_frames.append(f)
star_frames[0].save(V/'calques'/f'{P}_02_etoiles_phase0.png')
# ---- shooting stars: own layer, 30 fps, 12 s loop, three meteors with different paths/lengths
FPS_METEOR=30;N_METEOR=360
METEORS=[dict(t0=1.2,dur=0.6,x0=150,y0=40,dx=420,dy=150,color=(255,255,255)),dict(t0=5.4,dur=0.45,x0=620,y0=20,dx=-260,dy=120,color=(230,240,255)),dict(t0=7.0,dur=0.35,x0=380,y0=70,dx=180,dy=60,color=(255,255,255)),dict(t0=9.1,dur=0.75,x0=40,y0=120,dx=560,dy=90,color=(255,248,220))]
def meteor_frame(i):
    a=np.zeros((H,W,4),dtype=float);t=i/FPS_METEOR
    for m in METEORS:
        u=(t-m['t0'])/m['dur']
        if not 0<=u<=1.25:continue
        hx=m['x0']+m['dx']*min(u,1);hy=m['y0']+m['dy']*min(u,1)
        fade=1.0 if u<=1 else 1-(u-1)/0.25
        L=min(1,u)*0.45+0.2  # tail fraction of path
        steps=int(max(abs(m['dx']),abs(m['dy']))*L)+1
        for k in range(steps):
            s=k/max(steps-1,1);px=hx-m['dx']*L*s;py=hy-m['dy']*L*s
            if not(0<=px<W-1 and 0<=py<SKY_H):continue
            al=(1-s)**1.4*255*fade
            xi,yi=int(px),int(py);a[yi,xi,:3]=m['color'];a[yi,xi,3]=max(a[yi,xi,3],al)
            if s<0.5 and yi+1<H:a[yi+1,xi,:3]=m['color'];a[yi+1,xi,3]=max(a[yi+1,xi,3],al*.45)
            if s<0.06:  # bright head: 3px cross + diagonals
                for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(2,0),(-2,0),(0,2),(0,-2),(1,1),(-1,-1),(1,-1),(-1,1)):
                    if 0<=xi+dx<W and 0<=yi+dy<H:a[yi+dy,xi+dx,:3]=m['color'];a[yi+dy,xi+dx,3]=max(a[yi+dy,xi+dx,3],al*.7)
    return Image.fromarray(np.clip(np.rint(a),0,255).astype('uint8'))
MF=V/'etoiles_filantes_frames';MF.mkdir(exist_ok=True);meteor_frames=[]
for i in range(N_METEOR):
    f=meteor_frame(i);f.save(MF/f'{P}_filante_{i:03d}.png');meteor_frames.append(f)
Image.new('RGBA',(W,H)).save(V/'calques'/f'{P}_02b_etoiles_filantes_vide.png')
# ---- reuse V2 layers unchanged
reuse=['03_lune_generee','04_nuages_lointains','05_panorama_skypeak_foret_montagnes','05b_brume_overlay','06_nuages_overlay','07_plateau_herbe','08_paroi_rocheuse']
for n in reuse:L2(n).save(V/'calques'/f'{P}_{n}.png')
for n in ['bande_nuages_lointains_1440','bande_nuages_overlay_1440','bande_brume_0_1440','bande_brume_1_1440','bande_brume_2_1440','lune_sprite']:Image.open(V2/'calques'/f'{P2}_{n}.png').save(V/'calques'/f'{P}_{n}.png')
m2=json.loads((V2/'manifest.json').read_text())
strips={k:Image.open(V/'calques'/f'{P}_bande_nuages_{k}_1440.png').convert('RGBA') for k in ['lointains','overlay']}
mist_strips=[Image.open(V/'calques'/f'{P}_bande_brume_{k}_1440.png').convert('RGBA') for k in range(3)]
FAR=m2['clouds']['far'];NEAR=m2['clouds']['overlay'];MIST=m2['mist']['bands']
def wrap(st,off,y,alpha):
    im=Image.new('RGBA',(W,H))
    for x in range(-(int(off)%1440),W,1440):im.alpha_composite(st,(x,y))
    if alpha<1:a=np.array(im);a[:,:,3]=(a[:,:,3]*alpha).astype('uint8');im=Image.fromarray(a)
    return im
def mist(t):
    im=Image.new('RGBA',(W,H))
    for b,st in zip(MIST,mist_strips):
        breath=0.65+0.35*(0.5+0.5*math.sin(2*math.pi*(t/b['breath_period_s'])+b['phase']))
        im.alpha_composite(wrap(st,-b['speed_px_s']*t,b['y'],breath))
    return im
static={n:L2(n) for n in reuse}
def compose(t,mode='jour'):
    out=sky.copy();out.alpha_composite(star_frames[int(t*FPS_STARS)%N_STARS]);out.alpha_composite(meteor_frames[int(t*FPS_METEOR)%N_METEOR])
    dyn={'04_nuages_lointains':wrap(strips['lointains'],-FAR['speed']*t,FAR['y'],FAR['alpha']/100),'06_nuages_overlay':wrap(strips['overlay'],700-NEAR['speed']*t,NEAR['y'],NEAR['alpha']/100),'05b_brume_overlay':mist(t)}
    for n in reuse:
        im=dyn.get(n,static[n])
        if mode=='nuit' and n!='03_lune_generee':im=night(im)
        out.alpha_composite(im)
    return out
layers=[('01_ciel_profond',sky),('02_etoiles_phase0',star_frames[0]),('02b_etoiles_filantes_vide',meteor_frames[0])]+[(n,static[n]) for n in reuse]
comp=compose(0);comp.save(V/f'{P}_composition_nuit.png')
root=ET.Element('image',w=str(W),h=str(H),version='0.0.3');stack=ET.SubElement(root,'stack')
with zipfile.ZipFile(V/f'{P}_editable.ora','w',zipfile.ZIP_DEFLATED) as z:
    z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
    for i,(name,im) in enumerate(reversed(layers)):ET.SubElement(stack,'layer',name=name,src=f'data/{i}.png',x='0',y='0',opacity='1.0',visibility='visible');z.writestr(f'data/{i}.png',png(im))
    z.writestr('stack.xml',ET.tostring(root));z.writestr('mergedimage.png',png(comp))
def webp(path,frames_iter,count,fps,size=(W,H)):
    enc=_webp.WebPAnimEncoder(size,0,0,False,9,17,False,False)
    for i,f in enumerate(frames_iter):enc.add(f.getim(),round(i*1000/fps),True,80,100,4)
    enc.add(None,round(count*1000/fps),True,80,100,0);path.write_bytes(enc.assemble('','',''))
webp(V/f'{P}_etoiles_8s.webp',(f.crop((0,0,W,SKY_H)) for f in star_frames),N_STARS,FPS_STARS,(W,SKY_H))
webp(V/f'{P}_etoiles_filantes_12s.webp',(f.crop((0,0,W,SKY_H)) for f in meteor_frames),N_METEOR,FPS_METEOR,(W,SKY_H))
# full composition excerpt 24 s at 15 fps (stars 8 fps and meteors 30 fps sampled), day + Abyss night
for mode in (['jour','nuit'] if FULL else []):
    webp(V/f'{P}_extrait_24s_{"nuit_abyss" if mode=="nuit" else "nuit"}.webp',(compose(i/15,mode) for i in range(360)),360,15)
compose(0,'nuit').save(V/f'{P}_composition_nuit_abyss.png')
manifest=dict(size=[W,H],layers=[n for n,_ in layers],sky=dict(kind='authored gradient, no motifs',stops=stops,dither='Bayer 4x4 ±0.5',moon_glow_centre=[mx,my]),stars=dict(count_twinkle=sum(s['kind']=='twinkle' for s in STARS),count_static=sum(s['kind']=='static' for s in STARS),motifs='PMD-like 3-phase: dot / 3px plus / 5px plus with faint diagonals',frames=N_STARS,fps=FPS_STARS,loop_s=N_STARS/FPS_STARS,folder='etoiles_frames'),shooting_stars=dict(frames=N_METEOR,fps=FPS_METEOR,loop_s=N_METEOR/FPS_METEOR,meteors=METEORS,folder='etoiles_filantes_frames'),reused_from_v2=reuse,clouds=m2['clouds'],mist=m2['mist'],night_abyss='filter on all layers except sky, stars, shooting stars, moon',all_pixels_generated_or_authored=True,runtime_validated=False)
(V/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print('OK v3',len(STARS),'stars')
