"""Zones originales à plans séparés, texture Treasure Town et palette cycling."""
from pathlib import Path
from PIL import Image
import json
import math
import shutil
import numpy as np
from exterior_animation import export_variant, stars_spec
from export_palette_cycle import write_indexed
from rebuild_falaise import grade, SPECS

R=Path(__file__).resolve().parents[1]
S=R/'source/zones_treasure_town'
LAYERS=[
 ('00_ciel','Ciel — fond indépendant',False),
 ('01_astres','Lune fixe et étoiles',True),
 ('02_nuages','Nuages — défilement',True),
 ('03_fond_eau','Bassin / mer — fond fixe',False),
 ('04_eau_cycle','Eau — palette cycling',True),
 ('05_reliefs','Falaises et forêt du fond — texture TT',False),
 ('06_cascades','Cascades — palette cycling',True),
 ('07_ecume','Écume et rides — palette cycling',True),
 ('08_terrain','Terrain du premier plan — texture TT',False),
 ('09_vegetation','Végétation — overlay indépendant',False),
]


def png(path):return Image.open(path).convert('RGBA')


def cycle(src,out,prefix,mode):
    path=src/f'{prefix}_cycle.json'
    if not path.exists():return None,None,None
    data=json.loads(path.read_text());indices=Image.open(src/data['indices'])
    rel=f'animations/{prefix}_indices.png';(out/'animations').mkdir(parents=True,exist_ok=True);indices.save(out/rel,optimize=True)
    palettes=np.asarray(data['palettes'],dtype=np.uint8)
    if mode=='nuit':
        _,_,mul,add,sat=SPECS[mode];palettes=np.array(grade(Image.fromarray(palettes),mul,add,sat))
    data['palettes']=palettes.tolist();data['indices']=rel
    palette_file=f'animations/{prefix}_palettes_{mode}.json'
    (out/palette_file).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    indexed_file=f'aseprite_indexe/{prefix}_{mode}.aseprite'
    write_indexed(out/indexed_file,np.array(indices),data['palettes'],name=prefix+' — couleurs cycliques')
    first=Image.fromarray(palettes[0][np.array(indices).astype(int)])
    info={'indices':rel,'palettes':palette_file,'aseprite_indexe':indexed_file,
          'period':data['period'],'type':'indices_fixes_palettes_animees'}
    return first,data,info


def build():
    cfg=json.loads((S/'layouts.json').read_text())
    definitions=[{'id':k,'nom':n,'anime':a} for k,n,a in LAYERS]
    for name,c in cfg.items():
        src=S/name;out=R/'paysages'/name;out.mkdir(parents=True,exist_ok=True)
        for folder in ['calques','animations','aseprite','aseprite_indexe','bases','compositions','tiled']:
            if (out/folder).exists():shutil.rmtree(out/folder)
        size=tuple(c['size']);frames=math.lcm(size[0],24)
        stars=png(src/'astres_nuit.png');star_animation=stars_spec(stars,out)
        m={'version':3,'id':name,'titre':c['label'],'dimensions':list(size),'grille_px':8,
           'cellules':[size[0]//8,size[1]//8],'base_start':8,'calques':definitions,'ambiances':['jour','nuit'],
           'animation':{'frames':frames,'duree_image_ms':250,'duree_boucle_ms':frames*250},'fichiers':{},
           'note':c['label']+' — '+c['intent']+' Roches dans la texture de Treasure Town. Les plans ont leurs dessins propres ; eau, cascades et écume sont animées séparément par palettes.',
           'badge':'Texture Treasure Town · plans séparés',
           'animation_note':'Les pixels des plans d’eau restent en place : les entrées de palette cyclent. Nuages et étoiles ont leur animation propre. Les calques de terrain et de végétation restent fixes.',
           'regles':{'reference':c['reference'],'structures':False,'layout_original':True,'intention':c['intent'],
                     'texture':'Treasure Town — roche ocre stratifiée et pixel fin','plans_generes_separement':True,
                     'eau':'palette cycling sur cartes d’indices fixes','collisions':'non intégrées'}}
        for mode in ['jour','nuit']:
            _,_,mul,add,sat=SPECS[mode]
            empty=Image.new('RGBA',size)
            images=[png(src/f'ciel_{mode}.png'),stars if mode=='nuit' else empty,
                    grade(png(src/'nuages.png'),mul,add,sat),grade(png(src/'eau_fond.png'),mul,add,sat),empty,
                    grade(png(src/'reliefs.png'),mul,add,sat),empty,empty,
                    grade(png(src/'terrain_genere.png'),mul,add,sat),grade(png(src/'vegetation.png'),mul,add,sat)]
            specs={'02_nuages':{'kind':'scroll','period':size[0],'prefix':'nuages','ase_linked_motion':True}}
            if mode=='nuit':specs['01_astres']=star_animation
            cycling={}
            for prefix,index,key in [('eau',4,'04_eau_cycle'),('cascades',6,'06_cascades'),('ecume',7,'07_ecume')]:
                im,spec,info=cycle(src,out,prefix,mode)
                if im is not None:images[index]=im;specs[key]=spec;cycling[key]=info
            markers=[{'nom':'Arrivée — repère à configurer','rectangle_px':[size[0]//2-16,size[1]-32,32,32]}]
            files=export_variant(out,mode,definitions,images,specs,size,frames,8,markers)
            files['palette_assets']=cycling;m['fichiers'][mode]=files
            print(name,mode,'— 10 plans ; texture TT ; palettes cycliques',flush=True)
        (out/'kit.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':build()
