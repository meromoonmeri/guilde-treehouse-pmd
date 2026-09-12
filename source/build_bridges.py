"""Ponts originaux inspirés de PMD. Reproduction : python source/build_bridges.py."""
from pathlib import Path
from PIL import Image, ImageDraw
import json, random, base64
R = Path(__file__).resolve().parents[1]
OUT = R / 'sprites/ponts'
OUT.mkdir(exist_ok=True)
SIZE = 64
NAMES = ['horizontal_ouest', 'horizontal_centre', 'horizontal_est', 'vertical_nord', 'vertical_centre', 'vertical_sud']
DURATIONS = [180, 180, 180, 180]

def bridge(kind, frame):
    im = Image.new('RGBA', (64,64))
    d = ImageDraw.Draw(im)
    vertical = kind >= 3
    end = kind % 3
    sway = [0,1,0,-1][frame]
    rng = random.Random(43 + kind)
    # Same displacement at every module boundary: no cracks when repeated.
    def point(u,v):
        return (v+sway,u) if vertical else (u,v+sway)
    def line(points, color, width=1):
        d.line([point(*p) for p in points], fill=color, width=width)
    def box(u0,v0,u1,v1,color):
        a,b=point(u0,v0),point(u1,v1)
        d.rectangle((min(a[0],b[0]),min(a[1],b[1]),max(a[0],b[0]),max(a[1],b[1])),fill=color)
    # Underslung structural beams, gaps between individual planks remain transparent.
    for v in (22,43): box(0,v,63,v+3,'#523d31')
    for u in range(0,64,8):
        lo = rng.choice([17,18,19]); hi=rng.choice([46,47,48])
        box(u,lo,u+6,hi,'#503a2c')
        box(u+1,lo+1,u+5,hi-2,rng.choice(['#aa7649','#b68450','#bd8a55']))
        line([(u+1,lo+1),(u+5,lo+1)],'#e3bc78')
        line([(u+1,lo+2),(u+1,hi-3)],'#cd9f61')
        line([(u+5,lo+3),(u+5,hi-1)],'#805534')
        for j in range(3):
            v=rng.randint(lo+4,hi-5)
            line([(u+3,v),(u+3,v+rng.randint(1,4))],'#95653e')
        for v in (22,43): box(u+3,v,u+3,v,'#574f40')
    # Rope stanchions, then double twisted handrails.
    for u in (4,28,52):
        for top,bottom in ((10,23),(37,48)):
            line([(u,top),(u+1,bottom)],'#564433',3)
            line([(u,top),(u+1,bottom-1)],'#c3a873')
    for v in (10,37):
        line([(0,v+1),(63,v+1)],'#513f30',4)
        line([(0,v),(63,v)],'#d6bd86',2)
        for u in range(0,64,4): line([(u,v-1),(u+1,v+1)],'#f1d99b')
    # Anchor posts are inset, never duplicated at repeating seams.
    if end != 1:
        u = 8 if end == 0 else 55
        for v in (9,38):
            box(u-4,v-5,u+4,v+16,'#44362e')
            box(u-3,v-4,u+3,v+14,'#98623e')
            box(u-2,v-3,u,v+12,'#ce995b')
            box(u-4,v-6,u+4,v-3,'#dbb278')
            line([(u-3,v-5),(u+3,v-5)],'#f4d89b')
            for y in (v+2,v+4,v+6): line([(u-4,y),(u+4,y)],'#e0c591')
    return im

def night(im):
    out=im.copy()
    out.putdata([(round(r*.48+8),round(g*.53+12),round(b*.72+20),a) if a else (0,0,0,0) for r,g,b,a in im.getdata()])
    return out

metadata={'tile_size':[64,64], 'columns':NAMES, 'rows':'4 phases synchronisées, de haut en bas', 'durations_ms':DURATIONS, 'origin':'Création originale inspirée de PMD, pas de sprites extraits du jeu.', 'walking_area':'Bande centrale, coordonnées transversales 20 à 44 px. Collisions à configurer dans le moteur.'}
for mode in ('jour','nuit'):
    atlas=Image.new('RGBA',(384,256))
    for frame in range(4):
        for k in range(6):
            tile=bridge(k,frame)
            if mode=='nuit': tile=night(tile)
            atlas.paste(tile,(k*64,frame*64))
    atlas.save(OUT/f'ponts_{mode}.png')
    tiles=[]
    for k,name in enumerate(NAMES):
        tiles.append({'id':k,'type':name,'animation':[{'tileid':f*6+k,'duration':DURATIONS[f]} for f in range(4)],'properties':[{'name':'usage','type':'string','value':'Répéter le centre entre les deux ancrages ; synchroniser les phases.'}]})
    ts={'type':'tileset','version':'1.10','tiledversion':'1.10.2','name':f'ponts_{mode}','tilewidth':64,'tileheight':64,'tilecount':24,'columns':6,'spacing':0,'margin':0,'image':f'ponts_{mode}.png','imagewidth':384,'imageheight':256,'tiles':tiles}
    (OUT/f'ponts_{mode}.tsj').write_text(json.dumps(ts,ensure_ascii=False,indent=2))
    data=[0]*90
    for x,k in enumerate([0,1,1,1,2]): data[2*10+x+1]=k+1
    for y,k in enumerate([3,4,4,5]): data[(y+4)*10+7]=k+1
    tm={'type':'map','version':'1.10','tiledversion':'1.10.2','orientation':'orthogonal','renderorder':'right-down','width':10,'height':9,'tilewidth':64,'tileheight':64,'infinite':False,'nextlayerid':2,'nextobjectid':1,'layers':[{'id':1,'name':'Ponts animés — exemples modulaires','type':'tilelayer','x':0,'y':0,'width':10,'height':9,'opacity':1,'visible':True,'data':data}],'tilesets':[{'firstgid':1,'source':f'ponts_{mode}.tsj'}]}
    (OUT/f'exemple_{mode}.tmj').write_text(json.dumps(tm,ensure_ascii=False,indent=2))
(OUT/'ponts.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
# Contact sheet: labels and checkerboard never contaminate the importable atlas.
board=Image.new('RGB',(816,660),'#19231f'); d=ImageDraw.Draw(board)
d.text((24,16),'PONTS SUSPENDUS / KIT MODULAIRE',fill='#e9cf97')
d.text((24,38),'64 x 64 px / 4 phases / 180 ms / Jour et nuit',fill='#b2beb0')
for i,mode in enumerate(('jour','nuit')):
    x=16+i*400
    d.text((x,72),mode.upper()+' : OUEST / CENTRE / EST / NORD / CENTRE / SUD',fill='#e9cf97')
    for y in range(256):
        for xx in range(384): board.putpixel((x+xx,100+y),(49,60,53) if (xx//8+y//8)%2 else (40,49,44))
    board.paste(Image.open(OUT/f'ponts_{mode}.png'),(x,100),Image.open(OUT/f'ponts_{mode}.png'))
d.text((24,380),'ASSEMBLAGE : ancrage + centres repetables + ancrage',fill='#e9cf97')
for i,k in enumerate([0,1,1,1,1,2]):
    tile=bridge(k,0).resize((128,128),Image.Resampling.NEAREST)
    board.paste(tile,(24+128*i,410),tile)
d.text((24,576),'PNG : fond transparent, sans marge. TSJ : animations deja configurees.',fill='#b2beb0')
d.text((24,604),'Creation originale inspiree de PMD / pas une extraction du jeu.',fill='#b2beb0')
board.save(OUT/'planche.png')
print('Ponts : PNG, TSJ, cartes, manifeste et planche générés.')
def uri(path):
    return 'data:image/png;base64,' + base64.b64encode(path.read_bytes()).decode()
html=(R/'source/bridges_preview.html').read_text().replace('__BOARD__',uri(OUT/'planche.png')).replace('__SOURCES__',json.dumps({m:uri(OUT/f'ponts_{m}.png') for m in ('jour','nuit')}))
(R/'apercu_ponts.html').write_text(html)
