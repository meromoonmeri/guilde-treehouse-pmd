"""Zones : DA guilde/cap, nuages wrap indépendants et un calque par cascade."""
from pathlib import Path
from PIL import Image
import json
import math
import shutil
import numpy as np
from exterior_animation import export_variant, stars_spec
from export_palette_cycle import write_indexed
from rebuild_falaise import grade, SPECS
from prepare_zones_tt import FLOW

R=Path(__file__).resolve().parents[1]
S=R/'source/zones_treasure_town'


def png(path):return Image.open(path).convert('RGBA')


def definitions(name):
    rows=[('00_ciel','Ciel — fond fixe',False),('01_astres','Lune fixe et étoiles',True),
          ('02_nuages_lointains','Nuages lointains — wrap 4 px/s',True),
          ('03_nuages_proches','Nuages proches — wrap 8 px/s',True),
          ('04_fond_eau','Fond du bassin / de la mer',False),('05_eau_cycle','Eau — palette cycling',True),
          ('06_reliefs','Reliefs et forêt du fond',False)]
    if name=='plateaux':rows.append(('brume_wrap','Mer de nuages — wrap overlay',True))
    for n in range(1,len(FLOW.get(name,[]))+1):rows.append((f'cascade_{n:02d}',f'Cascade {n} — cycle indépendant',True))
    rows.append(('ecume','Écume et rides — overlay cyclique',True))
    if name=='littoral':rows.append(('reflet_lunaire','Reflet de lune — overlay animé',True))
    base_start=len(rows)
    rows.extend([('terrain','Terrain, prairie et chemin',False),('vegetation','Végétation — overlay fixe',False)])
    return [{'id':key,'nom':label,'anime':animated} for key,label,animated in rows],base_start


def cycle(src,out,prefix,mode):
    path=src/f'{prefix}_cycle.json'
    if not path.exists():return None,None,None
    data=json.loads(path.read_text());indices=Image.open(src/data['indices'])
    rel=f'animations/{prefix}_indices.png';(out/'animations').mkdir(parents=True,exist_ok=True);indices.save(out/rel,optimize=True)
    palettes=np.asarray(data['palettes'],dtype=np.uint8)
    if mode=='nuit':
        _,_,mul,add,sat=SPECS[mode];palettes=np.array(grade(Image.fromarray(palettes),mul,add,sat))
    data['palettes']=palettes.tolist();data['indices']=rel
    palette_file=f'animations/{prefix}_palettes_{mode}.json';(out/palette_file).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    indexed_file=f'aseprite_indexe/{prefix}_{mode}.aseprite'
    write_indexed(out/indexed_file,np.array(indices),data['palettes'],name=prefix+' — couleurs cycliques')
    first=Image.fromarray(palettes[0][np.array(indices).astype(int)])
    return first,data,{'indices':rel,'palettes':palette_file,'aseprite_indexe':indexed_file,'period':data['period'],'type':'indices_fixes_palettes_animees'}


def build(only=None):
    cfg=json.loads((S/'layouts.json').read_text())
    for name,c in cfg.items():
        if only and name not in only:continue
        src=S/name;out=R/'paysages'/name;out.mkdir(parents=True,exist_ok=True)
        for folder in ['calques','animations','aseprite','aseprite_indexe','bases','compositions','tiled']:
            if (out/folder).exists():shutil.rmtree(out/folder)
        size=tuple(c['size']);w,h=size;frames=math.lcm(w,24)
        stars=png(src/'astres_nuit.png');star_op=stars_spec(stars,out)
        defs,base_start=definitions(name)
        m={'version':4,'id':name,'titre':c['label'],'dimensions':list(size),'grille_px':8,'cellules':[w//8,h//8],
           'base_start':base_start,'calques':defs,'ambiances':['jour','nuit'],
           'animation':{'frames':frames,'duree_image_ms':250,'duree_boucle_ms':frames*250},'fichiers':{},
           'note':c['label']+' — '+c['intent']+' Sommet et roche harmonisés avec la guilde et le cap. Chaque mouvement est séparé du décor fixe.',
           'badge':'DA guilde / cap · overlays indépendants',
           'animation_note':'Deux plans de nuages traversent le ciel en wrap continu à des vitesses différentes. Eau, chaque cascade et écume ont leur cycle propre ; le terrain reste fixe.',
           'regles':{'reference':c['reference'],'structures':False,'layout_original':True,'intention':c['intent'],
                     'texture':'DA des falaises de guilde et du cap approuvées','plans_generes_separement':True,
                     'nuages':'deux overlays au-dessus du ciel, boucle horizontale sans couture',
                     'cascades':'un calque par chute, phases indépendantes','collisions':'non intégrées'}}
        for mode in ['jour','nuit']:
            _,_,mul,add,sat=SPECS[mode];empty=Image.new('RGBA',size)
            def tinted(file):return grade(png(src/file),mul,add,sat)
            by_id={'00_ciel':png(src/f'ciel_{mode}.png'),'01_astres':stars if mode=='nuit' else empty,
                   '02_nuages_lointains':tinted('nuages_lointains.png'),'03_nuages_proches':tinted('nuages_proches.png'),
                   '04_fond_eau':tinted('eau_fond.png'),'05_eau_cycle':empty,'06_reliefs':tinted('reliefs.png'),
                   'ecume':empty,'terrain':tinted('terrain_genere.png'),'vegetation':tinted('vegetation.png')}
            specs={'02_nuages_lointains':{'kind':'scroll','period':w,'step':1,'prefix':'nuages_lointains','ase_linked_motion':True},
                   '03_nuages_proches':{'kind':'scroll','period':w//2,'step':2,'prefix':'nuages_proches','ase_linked_motion':True}}
            if mode=='nuit':specs['01_astres']=star_op
            if name=='plateaux':
                by_id['brume_wrap']=tinted('brume_wrap.png')
                specs['brume_wrap']={'kind':'scroll','period':w,'step':1,'prefix':'brume','ase_linked_motion':True}
            cycling={};items=[('eau','05_eau_cycle'),('ecume','ecume')]
            items.extend((f'cascade_{n:02d}',f'cascade_{n:02d}') for n in range(1,len(FLOW.get(name,[]))+1))
            for prefix,key in items:
                im,spec,info=cycle(src,out,prefix,mode)
                by_id[key]=im if im is not None else empty
                if im is not None:specs[key]=spec;cycling[key]=info
            if name=='littoral':
                by_id['reflet_lunaire']=png(src/'reflet_lunaire.png') if mode=='nuit' else empty
                if mode=='nuit':
                    phases=[[0,0,int(round(255-24*math.sin(math.pi*i/24)**2))] for i in range(24)]
                    specs['reflet_lunaire']={'kind':'waves','period':24,'prefix':'reflet_lunaire','phases':phases,'preview_exact':True}
            images=[by_id[d['id']] for d in defs]
            markers=[{'nom':'Arrivée — repère à configurer','rectangle_px':[w//2-16,h-32,32,32]}]
            files=export_variant(out,mode,defs,images,specs,size,frames,base_start,markers)
            files['palette_assets']=cycling;m['fichiers'][mode]=files
            print(name,mode,'—',len(defs),'plans, wrap superposé au ciel et chutes indépendantes',flush=True)
        (out/'kit.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':build()
