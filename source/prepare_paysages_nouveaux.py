"""Découpe les nouveaux dessins générés en fond, eau, effets, astres et terrain."""
from pathlib import Path
from PIL import Image, ImageDraw
import cv2
import json
import numpy as np

R = Path(__file__).resolve().parents[1]
S = R / 'source/paysages_nouveaux'
CONFIG = {
    'littoral': {'size': [512,320], 'label': 'Cap du large', 'sky': 115, 'horizon':148, 'reference':'anothercliff reference to made.jpg'},
    'plateaux': {'size': [504,504], 'label': 'Plateaux fleuris', 'sky':64, 'horizon':0, 'reference':'2cwdrrs469f61.gif'},
    'etang': {'size': [456,624], 'label': 'Étang de la forêt', 'sky':0, 'horizon':0, 'reference':'pondourpmdàrefaire.png'},
    'cascades': {'size': [592,448], 'label': 'Cascades célestes', 'sky':65, 'horizon':0, 'reference':'232024.png'},
}


def rgba(rgb, mask):
    a = np.zeros((*mask.shape,4),np.uint8)
    a[:,:,:3] = rgb
    a[:,:,3] = mask.astype('uint8')*255
    a[~mask] = 0
    return Image.fromarray(a)


def save(q, path):
    q.convert('RGBA').save(path,optimize=True)


def grab_foreground(a, name):
    h,w = a.shape[:2]
    labels = np.full((h,w),cv2.GC_PR_BGD,np.uint8)
    if name == 'littoral':
        labels[int(h*.37):,:int(w*.66)] = cv2.GC_PR_FGD
        labels[int(h*.65):,:int(w*.4)] = cv2.GC_FGD
        labels[:int(h*.31)] = cv2.GC_BGD
        labels[:,int(w*.73):] = cv2.GC_BGD
    else:
        labels[int(h*.11):int(h*.72),int(w*.25):int(w*.77)] = cv2.GC_PR_FGD
        labels[int(h*.75):] = cv2.GC_FGD
        labels[int(h*.19):int(h*.40),int(w*.40):int(w*.60)] = cv2.GC_FGD
        labels[int(h*.40):int(h*.72),int(w*.49):int(w*.55)] = cv2.GC_FGD
        labels[int(h*.55):, :int(w*.15)] = cv2.GC_FGD
        labels[int(h*.55):, int(w*.86):] = cv2.GC_FGD
        labels[:int(h*.09)] = cv2.GC_BGD
        labels[:int(h*.48),:int(w*.15)] = cv2.GC_BGD
        labels[:int(h*.43),int(w*.86):] = cv2.GC_BGD
    cv2.setRNGSeed(117)
    cv2.grabCut(a.copy(),labels,None,np.zeros((1,65),float),np.zeros((1,65),float),5,cv2.GC_INIT_WITH_MASK)
    return (labels==cv2.GC_FGD)|(labels==cv2.GC_PR_FGD)


def separate_light(source, seed):
    """Vrai RGBA sur fond estimé, sans rectangles opaques autour des lumières."""
    base = cv2.inpaint(source,seed.astype('uint8')*255,5,cv2.INPAINT_TELEA).astype(float)
    raw = source.astype(float)
    needed = np.where(raw>=base,(raw-base)/np.maximum(255-base,1),(base-raw)/np.maximum(base,1))
    alpha = np.ceil(needed.max(2)*255).clip(0,255).astype('uint8')
    weight = alpha[:,:,None].astype(float)/255
    fg = np.rint((raw-base*(1-weight))/np.maximum(weight,1/255)).clip(0,255).astype('uint8')
    out=np.zeros((*alpha.shape,4),np.uint8);out[:,:,:3]=fg;out[:,:,3]=alpha;out[alpha==0]=0
    return base.astype('uint8'),Image.fromarray(out)


def prepare():
    for name,cfg in CONFIG.items():
        d=S/name;d.mkdir(parents=True,exist_ok=True)
        im=Image.open(d/'generation_jour.png').convert('RGB')
        w,h=cfg['size'];assert im.size==(w,h)
        a=np.array(im);r,g,b=[a[:,:,i].astype(int) for i in range(3)];yy,xx=np.indices((h,w))
        blue=(b>r+20)&(g>r+6)
        white=(a.min(2)>192)&(b>=r-5)
        if name=='littoral':
            land=grab_foreground(a,name)
            n,labels,stats,_=cv2.connectedComponentsWithStats(land.astype('uint8'),8)
            land=labels==max(range(1,n),key=lambda i:stats[i,4])
            water=(~land)&(yy>=cfg['horizon'])
            background=(~land)&~water
        elif name=='plateaux':
            green=(g>r+8)&(g>b+25)&(yy>95)
            top=np.full(w,160,int)
            for x in range(w):
                rows=np.where(green[:,x])[0]
                if len(rows):top[x]=max(95,int(rows.min())-3)
            land=yy>=top[None,:];water=np.zeros((h,w),bool);background=~land
        elif name=='etang':
            roi=yy<310
            seed=blue&roi
            near=cv2.dilate(seed.astype('uint8'),np.ones((9,9),np.uint8))>0
            water=seed|(white&near&roi);background=np.zeros((h,w),bool);land=~water
        else:
            land=grab_foreground(a,name)
            rock=Image.new('L',(w,h));draw=ImageDraw.Draw(rock)
            draw.polygon([(171,111),(200,88),(232,69),(275,57),(299,58),(339,74),(365,71),(406,107),(421,129),(415,161),(391,194),(370,223),(330,243),(315,275),(321,320),(287,326),(279,309),(286,267),(282,245),(243,235),(212,223),(186,193),(180,164)],fill=255)
            land |= np.array(rock)>0
            foliage=((g>r+10)&(g>b+15))|((r>b+25)&(g>b+15))|((a.max(2)<110)&(b<r+30))
            sides=(yy<320)&((xx<160)|(xx>432))
            land[sides]=foliage[sides]
            falls=np.zeros((h,w),bool)
            for x0,x1,y0,y1 in [(181,202,109,344),(246,270,77,344),(319,335,79,326),(344,362,223,326),(375,391,173,326),(389,405,92,326)]:
                falls[y0:y1,x0:x1]=True
            flowing=falls&(b>175)&(g>145)&(b>=r-5)
            pool=(yy>320)&blue
            near=cv2.dilate((pool|flowing).astype('uint8'),np.ones((3,3),np.uint8))>0
            water=flowing|pool|(white&near&(yy>310))
            background=~land&~water;land=~background&~water
        # Aucun pixel manquant : les trois masques partitionnent le dessin.
        assert np.all(land.astype(int)+water.astype(int)+background.astype(int)==1)
        clean=a.copy()
        if water.any():
            med=cv2.medianBlur(a,7).astype(int);light=(a.astype(int)-med).max(2)>12
            highlights=water&(light|white)
            highlights=cv2.dilate(highlights.astype('uint8'),np.ones((3,3),np.uint8)).astype(bool)&water
            clean=cv2.inpaint(a,highlights.astype('uint8')*255,3,cv2.INPAINT_TELEA)
        else:highlights=np.zeros((h,w),bool)
        # Fond complet : couleurs de ciel derrière les zones masquées, pas du terrain dupliqué.
        if background.any():
            color=np.median(a[background],axis=0).astype('uint8')
        else:color=np.array([27,48,45],np.uint8)
        bg=np.empty_like(a);bg[:]=color;bg[background]=a[background]
        save(Image.fromarray(bg),d/'00_fond_jour.png')
        save(rgba(clean,water),d/'02_eau_jour.png')
        save(rgba(a,highlights),d/'03_effets_jour.png')
        save(rgba(a,land),d/'04_terrain_jour.png')
        save(Image.new('RGBA',(w,h)),d/'05_decor.png')
        # Masques d'auteur pour reprises locales.
        Image.fromarray(land.astype('uint8')*255).save(d/'masque_terrain.png')
        Image.fromarray(water.astype('uint8')*255).save(d/'masque_eau.png')
        Image.fromarray(background.astype('uint8')*255).save(d/'masque_fond.png')
        combined=Image.open(d/'00_fond_jour.png').convert('RGBA')
        for p in ['02_eau_jour.png','03_effets_jour.png','04_terrain_jour.png']:combined.alpha_composite(Image.open(d/p).convert('RGBA'))
        assert np.array_equal(np.array(combined)[:,:,:3],a),name
        cfg['water_pixels']=int(water.sum());cfg['background_pixels']=int(background.sum())
        (d/'scene.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n')
        print(name,'— découpe exacte, eau',int(water.sum()),'pixels',flush=True)
    # Le littoral dispose d'un fond nocturne propre, avec pleine lune et reflet marin.
    d=S/'littoral';night=np.array(Image.open(d/'generation_fond_nuit.png').convert('RGB'))
    w,h=CONFIG['littoral']['size'];hor=CONFIG['littoral']['horizon']
    sky=night[:hor].copy();lum=sky.astype(float)@np.array([.2126,.7152,.0722]);med=cv2.medianBlur(sky,9).astype(float)@np.array([.2126,.7152,.0722])
    seed=(lum-med>16)|(lum>160);seed=cv2.dilate(seed.astype('uint8'),np.ones((3,3),np.uint8))>0
    base,astral=separate_light(sky,seed)
    out=Image.new('RGBA',(w,h));out.paste(astral,(0,0));save(out,d/'01_astres_nuit.png')
    bg=np.empty_like(night);bg[:hor]=base;bg[hor:]=base[-1:];save(Image.fromarray(bg),d/'00_fond_nuit.png')
    # Le reflet de lune devient un plan mobile au-dessus de l'eau sombre.
    sea=night[hor:].copy();med=cv2.medianBlur(sea,9);contrast=(sea.astype(int)-med.astype(int)).max(2)>10
    bright=(sea.min(2)>125)&(sea.max(2)>180);mask=cv2.dilate((contrast|bright).astype('uint8'),np.ones((3,3),np.uint8))>0
    clean,light=separate_light(sea,mask)
    water=Image.new('RGBA',(w,h));water.paste(Image.fromarray(clean).convert('RGBA'),(0,hor));save(water,d/'02_eau_nuit.png')
    glow=Image.new('RGBA',(w,h));glow.paste(light,(0,hor));save(glow,d/'03_effets_nuit.png')


if __name__=='__main__':prepare()
