"""Quatre nouvelles références : versions jour/nuit, calques et exports éditables."""
from pathlib import Path
from PIL import Image, ImageChops
import json
import cv2
import numpy as np
from exterior_animation import export_variant, stars_spec, save_png
from rebuild_falaise import grade, SPECS
from prepare_paysages_nouveaux import CONFIG

R=Path(__file__).resolve().parents[1]
S=R/'source/paysages_nouveaux'
DEFINITIONS=[
    {'id':'00_fond','nom':'Ciel et arrière-plan','anime':False},
    {'id':'01_astres','nom':'Lune fixe et étoiles nocturnes','anime':True},
    {'id':'02_eau','nom':'Eau — fond','anime':False},
    {'id':'03_effets','nom':'Reflets et cascades — overlay','anime':True},
    {'id':'04_terrain','nom':'Terrain et végétation naturels','anime':False},
    {'id':'05_decor','nom':'Structures — calque vide','anime':False},
]


def shared_stars(size, sky_height):
    result=Image.new('RGBA',size)
    if not sky_height:return result
    source=np.array(Image.open(R/'source/falaise/astres_nuit_native.png').convert('RGBA'))
    n,labels,stats,centers=cv2.connectedComponentsWithStats((source[:,:,3]>0).astype('uint8'),8)
    scale=min(1.,sky_height/105)
    # Adapter les positions au ciel disponible, sans aplatir la lune.
    for i in range(1,n):
        x,y,w,h,_=stats[i];part=source[y:y+h,x:x+w].copy();part[labels[y:y+h,x:x+w]!=i]=0
        q=Image.fromarray(part).resize((max(1,round(w*scale)),max(1,round(h*scale))),Image.Resampling.NEAREST)
        if not q.getbbox():continue
        px=round(centers[i,0]/480*size[0]-q.width/2)
        py=round(centers[i,1]/120*sky_height-q.height/2)
        px=min(size[0]-q.width,max(0,px));py=min(sky_height-q.height,max(0,py))
        result.alpha_composite(q,(px,py))
    return result


def effect_cycle(image, name):
    w,h=image.size
    if name=='littoral':
        phases=[]
        for i in range(24):
            phases.append([int(round(np.sin(2*np.pi*i/24))),0,int(round(255-24*np.sin(np.pi*i/24)**2))])
        return {'kind':'waves','period':24,'prefix':'reflets','phases':phases},None
    # Trois positions proches, comme un petit cycle de cascade PMD, masquées
    # derrière le terrain. Les silhouettes du paysage ne se déplacent pas.
    atlas=Image.new('RGBA',(w*3,h))
    a=np.array(image)
    for i in range(3):
        if name=='etang':limit=195
        else:limit=int(h*.76)
        upper=a.copy();upper[limit:]=0
        lower=a.copy();lower[:limit]=0
        q=ImageChops.offset(Image.fromarray(upper),0,i)
        q.alpha_composite(ImageChops.offset(Image.fromarray(lower),[0,1,0][i],0))
        atlas.paste(q,(i*w,0))
    return {'kind':'frames','period':3,'prefix':'cascades','source_frame_size':[w,h],'source_columns':3},atlas


def build():
    for name,cfg in CONFIG.items():
        src=S/name;out=R/'paysages'/name;out.mkdir(parents=True,exist_ok=True)
        size=tuple(cfg['size']);frames=24
        day=[Image.open(src/'00_fond_jour.png').convert('RGBA'),Image.new('RGBA',size),
             Image.open(src/'02_eau_jour.png').convert('RGBA'),Image.open(src/'03_effets_jour.png').convert('RGBA'),
             Image.open(src/'04_terrain_jour.png').convert('RGBA'),Image.open(src/'05_decor.png').convert('RGBA')]
        night_stars=Image.open(src/'01_astres_nuit.png').convert('RGBA') if name=='littoral' else shared_stars(size,cfg['sky'])
        star_animation=stars_spec(night_stars,out) if night_stars.getbbox() else None
        m={'version':1,'id':name,'titre':cfg['label'],'dimensions':list(size),'grille_px':8,
           'cellules':[size[0]//8,size[1]//8],'base_start':4,'calques':DEFINITIONS,'ambiances':['jour','nuit'],
           'animation':{'frames':frames,'duree_image_ms':250,'duree_boucle_ms':6000},'fichiers':{},
           'note':cfg['label']+' — référence redessinée au générateur, sans bâtiment, panneau, clôture ni installation. Arrière-plan, eau, effets et terrain sont séparés.',
           'badge':'Jour / nuit · sans structures',
           'animation_note':'Le terrain reste fixe. Les reflets ou cascades utilisent leur overlay ; les étoiles scintillent là où le ciel est visible.',
           'regles':{'reference':cfg['reference'],'structures':False,'methode':'génération puis découpe et palettes','collisions':'non intégrées'}}
        for mode in m['ambiances']:
            if mode=='jour':images=[q.copy() for q in day]
            else:
                _,_,mul,add,sat=SPECS['nuit'];images=[grade(q,mul,add,sat) for q in day];images[1]=night_stars
                if name=='littoral':
                    for i,file in [(0,'00_fond_nuit.png'),(2,'02_eau_nuit.png'),(3,'03_effets_nuit.png')]:images[i]=Image.open(src/file).convert('RGBA')
            specs={}
            if mode=='nuit' and star_animation:specs['01_astres']=star_animation
            if images[3].getbbox():
                spec,atlas=effect_cycle(images[3],name)
                if atlas is not None:
                    rel=f'animations/source_effets_{mode}.png';save_png(atlas,out/rel);spec['source_atlas']=rel
                specs['03_effets']=spec
            m['fichiers'][mode]=export_variant(out,mode,DEFINITIONS,images,specs,size,frames,4,[])
            print(name,mode,'— six calques, sans structures',flush=True)
        (out/'kit.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':build()
