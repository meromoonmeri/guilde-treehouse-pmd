"""Native-scale PMDO PNG import samples. Whole cliff modules, no image reconstruction,
no independent 8px recoloring/selection, no resampling of any game asset.
Approved generator compositions remain guides for the cirque / terrace topology.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib
from zones_guidees.native_tools import Bank,BASE,CLIFF,ROOT
B=Bank();O=ROOT/'sprites/metano_import_png';O.mkdir(exist_ok=True)
# Complete rectangles in the native cliff sheet, including crown, face and foot.
RECTS={'descente_ouest':(456,208,680,544),'face_complete':(912,448,976,544),'retour_arrondi':(680,448,744,544),'remontee_est':(1296,304,1512,544)}
def extract(rect):
    x0,y0,x1,y1=rect;im=Image.new('RGBA',(x1-x0,y1-y0))
    for y in range(y0//8,y1//8):
        for x in range(x0//8,x1//8):
            g=B.get(CLIFF,x,y)
            if g:im.paste(B.image(g),(x*8-x0,y*8-y0))
    return im
MODULES={k:extract(v) for k,v in RECTS.items()}
for k,im in MODULES.items():im.save(O/('METANO_V3_MODULE_'+k.upper()+'.png'),optimize=True)
CONFIG=[{'id':'01_cirque','size':[1016,512],'walls':[{'offset_y':-208,'rounded':[2,5]}]}, {'id':'02_terrasses','size':[1016,768],'walls':[{'offset_y':-208,'rounded':[1,6]},{'offset_y':176,'rounded':[3,5]}]}]
m={'purpose':'PNG to Tileset in PMDO Dev; native-scale dry calibration scenes, not full replacements of the approved 2048x1536 guides','tile_size_for_import':8,'ground_texsize_reference':1,'asset_scale':1,'sources':B.source_info,'modules':{k:{'sheet':CLIFF,'source_rect_px':list(v),'size_px':list(MODULES[k].size),'file':'METANO_V3_MODULE_'+k.upper()+'.png'} for k,v in RECTS.items()},'zones':[],'limits':['New dry calibration layouts, not identical silhouettes to the generated proposals','No water animation or new nighttime palette in this calibration set','Whole modules retain their source pixels; joins between modules still require visual/game validation','Not executed inside the user PMDO installation']}
previews=[]
for cfg in CONFIG:
    d=O/cfg['id'];d.mkdir(exist_ok=True);prefix='METANO_V3_'+cfg['id'][3:].upper();w,h=cfg['size'];grass=Image.new('RGBA',(w,h))
    for y in range(h//8):
        for x in range(w//8):grass.paste(B.image(B.get(BASE,x%16,80+y%16)),(x*8,y*8))
    cliffs=Image.new('RGBA',(w,h));placements=[]
    for wall in cfg['walls']:
        offset=wall['offset_y'];sequence=['descente_ouest','retour_arrondi']+['retour_arrondi' if i in wall['rounded'] else 'face_complete' for i in range(8)]+['remontee_est'];x=0
        for name in sequence:
            im=MODULES[name];y=RECTS[name][1]+offset
            assert x%8==y%8==0 and y>=0 and y+im.height<=h
            cliffs.paste(im,(x,y));placements.append({'module':name,'dest_px':[x,y]});x+=im.width
        assert x==w
    full=Image.alpha_composite(grass,cliffs);grass.save(d/(prefix+'_SOL.png'),optimize=True);cliffs.save(d/(prefix+'_FALAISES.png'),optimize=True);full.save(d/(prefix+'_SCENE.png'),optimize=True)
    rec={**cfg,'placements':placements,'files':{},'grid':[w//8,h//8]}
    for p in d.glob('*.png'):rec['files'][p.name]={'size_px':[w,h],'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    m['zones'].append(rec);previews.append(full)
(O/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
# Exact native control block for comparing the imported result to Metano.
MODULES['retour_arrondi'].save(O/'METANO_V3_TEMOIN_64x96.png',optimize=True)
print('Built 2 dry calibration scenes; complete native modules and exact import control.')
