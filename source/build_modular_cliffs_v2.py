"""Morceaux de falaise natifs + placement du nouveau lot de maisons.
Prérequis : build_houses_metano.py --organic-v2 et build_cliff_layouts.py avec layout_config.json.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import io,json,struct,hashlib,math
R=Path(__file__).resolve().parents[1];O=R/'sprites/falaises_modulaires_v2';O.mkdir(exist_ok=True)
D=O/'decor/04_balcon';H=R/'sprites/maisons_organiques_v2';F=R/'source/falaises_metano'

def decode(path):
    raw=path.read_bytes();s,n=struct.unpack_from('<II',raw);assert s==8
    entries=[struct.unpack_from('<IIQ',raw,8+16*i) for i in range(n)];im=Image.new('RGBA',((max(x for x,y,o in entries)+1)*8,(max(y for x,y,o in entries)+1)*8))
    for x,y,o in entries:
        ln=struct.unpack_from('<q',raw,o)[0];t=Image.open(io.BytesIO(raw[o+8:o+8+ln])).convert('RGBA');im.paste(t,(x*8,y*8))
    return im

def straight(im):
    out=im.copy();out.putdata([(round(r*255/a),round(g*255/a),round(b*255/a),a) if 0<a<255 else (r,g,b,a) for r,g,b,a in im.getdata()]);return out

def native(im,path):
    entries=[];payload=bytearray();offsets={};n=im.width*im.height//64
    for y in range(im.height//8):
        for x in range(im.width//8):
            tile=im.crop((x*8,y*8,x*8+8,y*8+8));key=tile.tobytes()
            if key not in offsets:
                offsets[key]=8+16*n+len(payload);b=io.BytesIO();tile.save(b,format='PNG');v=b.getvalue();payload.extend(struct.pack('<q',len(v))+v)
            entries.append(struct.pack('<IIQ',x,y,offsets[key]))
    path.write_bytes(struct.pack('<II',8,n)+b''.join(entries)+payload)

cliff=decode(F/'natifs/Metano_Town_Cliffs.tile');spec=[]
def patch(name,slug,source,rect=None):
    path=R/source
    if path.suffix=='.tile':im=cliff.crop(rect)
    else:
        im=Image.open(path).convert('RGBA')
        if rect:im=im.crop(rect)
    spec.append((name,slug,im,{'file':source,'rect_xyxy_px':rect,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}))
root='source/falaises_metano/patches/'
patch('Rebord herbeux','rebord',root+'rebord.png')
patch('Paroi répétable','paroi',root+'roche.png')
patch('Pied de paroi','pied',root+'pied.png')
src='source/falaises_metano/natifs/Metano_Town_Cliffs.tile'
patch('Section complète','section',src,[912,432,976,544])
patch('Escalier natif','escalier',root+'escalier.png')
patch('Coude ouest','coude_ouest',src,[680,432,744,544])
patch('Coude est','coude_est',src,[1296,432,1360,544])
patch('Palier ouest','palier_ouest',src,[584,272,616,384])
patch('Palier est','palier_est',src,[1440,320,1472,448])
patch('Entrée rocheuse','entree',src,[848,400,912,544])
patch('Sol herbeux','herbe',root+'herbe.png',[0,0,64,64])
for i in range(4):patch(f'Cascade · phase {i+1}',f'cascade_{i+1}',f'sprites/eau_metano/cascade_frame_{i+1}.png')
# Slots 80x160, fragments placed on 8px grid with baseline 144. No source pixel moved within a fragment.
atlas=Image.new('RGBA',(400,480));items=[]
for i,(name,slug,im,provenance) in enumerate(spec):
    w,h=im.size;assert w<=80 and h<=144 and w%8==h%8==0
    x=(i%5)*80+((80-w)//16)*8;y=(i//5)*160+144-h
    atlas.paste(im,(x,y));file=f'{i+1:02}_{slug}.png';straight(im).save(O/file)
    items.append({'id':i+1,'name':name,'file':file,'size_px':[w,h],'atlas_rect_px':[x,y,w,h],'atlas_rect_cells':[x//8,y//8,w//8,h//8],'source':provenance})
straight(atlas).save(O/'Falaises_Metano_Modules.png');native(atlas,O/'Falaises_Metano_Modules.tile')
anims=[];native_anims=[]
for y in range(17):
    for x in range(8):
        ids=[];fr=[]
        for i in range(11,15):
            xx,yy,_,_=items[i]['atlas_rect_cells'];idx=(yy+y)*50+xx+x;ids.append(idx);fr.append({'Sheet':'Falaises_Metano_Modules','TexLoc':{'X':xx+x,'Y':yy+y}})
        anims.append({'id':ids[0],'animation':[{'tileid':v,'duration':167} for v in ids]});native_anims.append({'id':ids[0],'Frames':fr,'FrameLength':10})
(O/'Falaises_Metano_Modules.tsj').write_text(json.dumps({'type':'tileset','version':'1.10','name':'Falaises_Metano_Modules','tilewidth':8,'tileheight':8,'columns':50,'tilecount':3000,'margin':0,'spacing':0,'image':'Falaises_Metano_Modules.png','imagewidth':400,'imageheight':480,'tiles':anims},indent=2))
(O/'modules.json').write_text(json.dumps({'grid_px':8,'slot_size_px':[80,160],'reference':'Palikadude/Halcyon','commit':'da6c2130d641507447e6386a5e47a296e8cb4c71','modules':items,'native_animations':native_anims,'note':'Fragments natifs à sélectionner par rectangle, pas un autotile universel. Cadence cascade proposée à 10 ticks.'},ensure_ascii=False,indent=2))
# Legended PNG, enlarged x2 nearest only for presentation.
board=Image.new('RGB',(920,1136),'#1d2e29');draw=ImageDraw.Draw(board);fp='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';font=ImageFont.truetype(fp,22);small=ImageFont.truetype(fp,12)
draw.text((24,20),'FALAISES DE MÉTANO / MORCEAUX NATIFS',font=font,fill='#ead491')
draw.text((24,57),'Tuiles de 8 px • 11 fragments fixes + 4 phases de cascade • aucun redessin',font=small,fill='#b2c7b3')
for i,item in enumerate(items):
    x=16+(i%5)*180;y=96+(i//5)*336;draw.rounded_rectangle((x,y,x+168,y+324),radius=7,fill='#2b4136')
    im=Image.open(O/item['file']).resize(tuple(v*2 for v in item['size_px']),Image.Resampling.NEAREST);board.paste(im,(x+(168-im.width)//2,y+288-im.height),im)
    draw.text((x+8,y+294),f'{i+1:02} {item["name"]}',font=small,fill='#ead491');draw.text((x+8,y+310),' × '.join(str(v) for v in item['size_px'])+' px',font=small,fill='#b2c7b3')
board.save(O/'planche_modules.png')
# Separate placement layer: no house is baked into the terrain.
houses=json.loads((H/'maisons.json').read_text())['houses']
positions=[(64,256),(224,128),(480,288),(528,96),(816,176),(1200,112),(1472,256),(1840,96),(1744,1184),(160,1168)]
layer=Image.new('RGBA',(2048,1536));placements=[]
for house,(x,y) in zip(houses,positions):
    im=Image.open(H/house['files']['jour']).convert('RGBA');layer.alpha_composite(im,(x,y));placements.append({'house_id':house['id'],'name':house['name'],'image':'../maisons_organiques_v2/'+house['files']['jour'],'position_px':[x,y]})
layer.save(D/'structures.png')
for f in range(1,5):
    scene=Image.open(D/f'layout_{f}.png').convert('RGBA');Image.alpha_composite(scene,layer).save(D/f'village_{f}.png')
Image.open(D/'layout_1.png').save(O/'rendu_falaise.png');Image.open(D/'village_1.png').save(O/'rendu_village.png')
(O/'placements_maisons.json').write_text(json.dumps(placements,ensure_ascii=False,indent=2))
# Optional editable map with a third, independent house layer and separate house tileset.
tm=json.loads((D/'layout.tmj').read_text());terrain_ts=json.loads((O/'decor/Falaises_V2_Decor.tsj').read_text());first=terrain_ts['tilecount']+1
house_data=[0]*(256*192)
for house,(px,py) in zip(houses,positions):
    sx,sy,w,h=house['atlas_rect_cells']
    for y in range(h):
        for x in range(w):house_data[(py//8+y)*256+px//8+x]=first+(sy+y)*70+sx+x
house_layer={'id':3,'name':'Maisons organiques — placements indicatifs','type':'tilelayer','x':0,'y':0,'width':256,'height':192,'opacity':1,'visible':True,'data':house_data}
tm['layers'].append(house_layer);tm['nextlayerid']=4;tm['tilesets'].append({'firstgid':first,'source':'../../../maisons_organiques_v2/Maisons_Organiques_V2_jour.tsj'})
(D/'village.tmj').write_text(json.dumps(tm,separators=(',',':')))
# Main requested PNG: village composition and house contact sheet together, not an import texture.
summary=Image.new('RGB',(1600,1480),'#1a2d26');d=ImageDraw.Draw(summary)
d.text((28,22),'MÉTANO / NOUVELLES HABITATIONS & FALAISES',font=ImageFont.truetype(fp,28),fill='#edda9b')
d.text((28,64),'10 maisons originales · textures de falaises natives · grille 8 px · rendu complet : 2048 × 1536 px',font=ImageFont.truetype(fp,15),fill='#b4c8b0')
scene=Image.open(O/'rendu_village.png').resize((1024,768),Image.Resampling.NEAREST);summary.paste(scene,(24,112))
# Native detail crop at x2 for readable rock and falling-water texture.
close=Image.open(O/'rendu_falaise.png').crop((928,680,1184,1032)).resize((512,704),Image.Resampling.NEAREST);summary.paste(close,(1064,144));d.text((1064,112),'Détail falaise / cascade ×2',font=small,fill='#edda9b')
for i,house in enumerate(houses):
    x=24+i*156;im=Image.open(H/house['files']['jour']).resize((112,128),Image.Resampling.NEAREST);summary.paste(im,(x+20,924),im);d.text((x+8,1064),f'{i+1:02} {house["name"]}',font=small,fill='#edda9b')
# A representative subset of the native modular library, shown at double size.
d.text((28,1120),'MORCEAUX À ASSEMBLER / EXTRAITS DES TUILES DE RÉFÉRENCE',font=font,fill='#edda9b')
for j,i in enumerate([0,1,2,4,5,6,9,11]):
    item=items[i];im=Image.open(O/item['file']).resize(tuple(v*2 for v in item['size_px']),Image.Resampling.NEAREST);x=24+j*196;summary.paste(im,(x+(168-im.width)//2,1430-im.height),im);d.text((x+4,1448),item['name'],font=small,fill='#b4c8b0')
summary.save(O/'rendu_collection.png')
print('15 modules natifs, un nouveau décor, un village PNG et une carte Tiled à maisons séparées.')
