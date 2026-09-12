"""Trois extensions de terrain Métano, 2048x1536, cellules 8 px.
Géométrie originale composée avec textures natives ; aucun agrandissement des sprites.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import json,random,math,io,struct,base64,zipfile
R=Path(__file__).resolve().parents[1];S=R/'source/falaises_metano';O=R/'sprites/falaises_metano';O.mkdir(exist_ok=True)
W,H=2048,1536;GW,GH=W//8,H//8
P={p.stem:Image.open(p).convert('RGBA') for p in (S/'patches').glob('*.png')}
C=[Image.open(R/f'sprites/eau_metano/cascade_frame_{i}.png').convert('RGBA') for i in range(1,5)]

def texture(p,size):
    out=Image.new('RGBA',size)
    for y in range(0,size[1],p.height):
        for x in range(0,size[0],p.width):out.paste(p,(x,y))
    return out
GRASS=texture(P['herbe'],(W,H));ROCK=texture(P['roche'],(W,H));SAND=texture(P['sable'],(W,H))

def front(poly):
    mask=Image.new('1',(GW,GH));ImageDraw.Draw(mask).polygon([(x//8,y//8) for x,y in poly],fill=1)
    return {x*8:max(y for y in range(GH) if mask.getpixel((x,y)))*8 for x in range(GW) if any(mask.getpixel((x,y)) for y in range(GH))}

def plateau(im,poly,height):
    # Extrude south-facing faces in native 8px columns. Back rims remain short in this camera.
    f=front(poly)
    for x,top in f.items():
        sx=x%64
        for y in range(top,top+height,48):
            t=P['roche'].crop((sx,0,sx+8,min(48,top+height-y)));im.paste(t,(x,y))
        im.paste(P['pied'].crop((sx,0,sx+8,16)),(x,top+height-16))
    mask=Image.new('L',(W,H));d=ImageDraw.Draw(mask);d.polygon(poly,fill=255)
    # Thin rear lip: the unseen north-facing wall is not drawn as a front wall.
    outline=mask.filter(ImageFilter.MaxFilter(9));im.paste(ROCK,(0,0),outline);im.paste(GRASS,(0,0),mask)
    # Reapply the visible face (outline compositing is restricted to the top surface).
    for x,top in f.items():
        sx=x%64
        for y in range(top+8,top+height,48):
            t=P['roche'].crop((sx,0,sx+8,min(48,top+height-y)));im.paste(t,(x,y))
        im.paste(P['pied'].crop((sx,0,sx+8,16)),(x,top+height-16))
        im.paste(P['rebord'].crop((sx,0,sx+8,24)),(x,top-8))
    return f

def path(im,points,width=48):
    mask=Image.new('L',(W,H));d=ImageDraw.Draw(mask);d.line(points,fill=255,width=width,joint='curve')
    for x,y in points:d.ellipse((x-width//2,y-width//2,x+width//2,y+width//2),fill=255)
    im.paste(SAND,(0,0),mask)

def stairs(im,x,top,height):
    # Keep native width and step rhythm; repeat middle steps, never stretch the staircase.
    patch=P['escalier'];im.paste(patch.crop((0,0,64,16)),(x-32,top-24))
    for y in range(top-8,top+height-8,16):im.paste(patch.crop((0,32,64,48)),(x-32,y))
    im.paste(patch.crop((0,96,64,112)),(x-32,top+height-8))

def curve(points,closed=False):
    # Smooth new geometry, rasterised at native resolution with NO texture resampling.
    pts=list(points);p=([pts[-1]]+pts+[pts[0],pts[1]]) if closed else ([pts[0]]+pts+[pts[-1]])
    result=[]
    for i in range(1,len(p)-2):
        for j in range(24):
            t=j/24;t2=t*t;t3=t2*t
            result.append(tuple(round(.5*((2*p[i][a])+(-p[i-1][a]+p[i+1][a])*t+(2*p[i-1][a]-5*p[i][a]+4*p[i+1][a]-p[i+2][a])*t2+(-p[i-1][a]+3*p[i][a]-3*p[i+1][a]+p[i+2][a])*t3)) for a in [0,1]))
    result.append(pts[0] if closed else pts[-1]);return result

def water_network(cfg,phase):
    # Union before drawing shores: intersections must not leave outlines INSIDE the water.
    mask=Image.new('L',(W,H));d=ImageDraw.Draw(mask)
    for pool in cfg['pools']+[cfg['basin']]:d.polygon(curve(pool,True),fill=255)
    for points,width in cfg['feeds']+cfg['outlets']:
        d.line(curve(points),fill=255,width=width,joint='curve')
        for x,y in points:d.ellipse((x-width//2,y-width//2,x+width//2,y+width//2),fill=255)
    im=Image.new('RGBA',(W,H));im.paste('#5787bf',(0,0,W,H),mask.filter(ImageFilter.MaxFilter(9)))
    im.paste('#5fb7cf',(0,0,W,H),mask.filter(ImageFilter.MaxFilter(5)))
    im.paste('#83dae6',(0,0,W,H),mask)
    # Colors sampled from the actual Metano river, not a replacement palette.
    d=ImageDraw.Draw(im)
    for y in range(32+phase*2,H,48):
        for x in range(16+(y%5)*8,W-16,80):
            if im.getpixel((x,y))[:3]==(131,218,230) and im.getpixel((x+12,y))[:3]==(131,218,230):
                d.line((x,y,x+8,y),fill='#94e6ee');d.point((x+9,y-1),fill='#94e6ee')
    return im

def fall(im,x,top,height,f):
    # Retain 64px width, the original crown and bottom, repeat only the falling-water middle.
    src=C[f];im.alpha_composite(src.crop((0,0,64,48)),(x-32,top-8))
    for y in range(top+40,top+height-24,32):
        length=min(32,top+height-24-y)
        if length>0:im.alpha_composite(src.crop((0,64,64,64+length)),(x-32,y))
    im.alpha_composite(src.crop((0,104,64,136)),(x-32,top+height-24))

LONG=[(0,0),(2048,0),(2048,520),(1856,520),(1856,584),(1632,584),(1632,640),(1344,640),(1344,616),(1152,616),(1152,704),(864,704),(864,656),(608,656),(608,592),(352,592),(352,544),(0,544)]
ISLAND=[(640,160),(1344,160),(1536,240),(1728,368),(1808,544),(1808,704),(1712,704),(1712,816),(1504,816),(1504,912),(1280,912),(1280,976),(768,976),(768,912),(544,912),(544,816),(336,816),(336,704),(240,704),(240,512),(336,336),(464,240)]
LOW=[(128,480),(320,320),(1728,320),(1920,480),(1920,960),(1728,960),(1728,1104),(1408,1104),(1408,1168),(640,1168),(640,1104),(320,1104),(320,960),(128,960)]
MID=[(352,256),(512,160),(1568,160),(1696,256),(1696,656),(1568,656),(1568,768),(512,768),(512,656),(352,656)]
HIGH=[(640,64),(1408,64),(1472,160),(1472,400),(1312,400),(1312,448),(736,448),(736,400),(576,400),(576,160)]
CONFIG=[
 {'id':'01_paroi','name':'La grande paroi','description':'Plateau ouvert au nord, longue face rocheuse et trois grandes chutes.','plateaus':[(LONG,320)],'falls':[(480,0),(1248,0),(1760,0)],'stairs':[(784,0),(1456,0)],'pools':[[(240,176),(352,104),(544,128),(624,256),(576,384),(400,416),(272,320)],[(1088,144),(1216,80),(1424,144),(1504,288),(1424,416),(1216,432),(1104,336)],[(1632,112),(1776,96),(1920,208),(1888,352),(1744,400),(1632,288)]], 'feeds':[([(480,304),(448,448),(480,584)],48), ([(1248,336),(1280,480),(1248,608)],56), ([(1760,304),(1792,448),(1760,576)],48)],'outlets':[([(480,912),(512,1104),(864,1200)],64), ([(1248,936),(1184,1088),(1024,1232)],72), ([(1760,904),(1664,1120),(1312,1264)],64), ([(1024,1296),(1088,1424),(1152,1536)],88)],'basin':[(704,1192),(896,1112),(1152,1144),(1392,1216),(1440,1352),(1200,1440),(896,1400),(720,1304)],'paths':[[(0,448),(240,448),(720,512),(784,648)],[(1456,632),(1456,480),(1840,480),(2048,424)],[(0,1160),(240,1104),(784,992),(864,1040)],[(1456,984),(1488,1120),(1840,1312),(2048,1312)]]},
 {'id':'02_plateau','name':'Le plateau des trois sources','description':'Grand plateau isolé, contour rocheux et espace central libre.','plateaus':[(ISLAND,256)],'falls':[(432,0),(1152,0),(1648,0)],'stairs':[(816,0),(1456,0)],'pools':[[(368,480),(416,384),(560,384),(624,496),(560,600),(400,608)],[(928,264),(1088,224),(1256,288),(1328,424),(1224,528),(1040,528),(936,416)],[(1472,432),(1584,384),(1696,472),(1696,592),(1584,648),(1488,576)]], 'feeds':[([(480,544),(464,688),(432,808)],48), ([(1152,480),(1120,736),(1152,968)],56), ([(1584,576),(1616,704),(1648,808)],48)],'outlets':[([(432,1072),(336,1200),(560,1400),(880,1392)],64), ([(1152,1232),(1120,1344),(1024,1416)],72), ([(1648,1072),(1792,1200),(1728,1376),(1408,1424)],64)],'basin':[(832,1336),(1040,1296),(1272,1336),(1464,1384),(1504,1536),(752,1536),(728,1440)],'paths':[[(816,960),(752,768),(720,560),(848,432)],[(1456,904),(1408,704),(1392,528),(1456,312)],[(0,1248),(288,1248),(592,1256),(816,1248)],[(1456,1184),(1584,1232),(1952,1184),(2048,1136)]]},
 {'id':'03_terrasses','name':'Les terrasses de Métano','description':'Trois niveaux superposés, chutes en chaîne et escaliers latéraux.','plateaus':[(LOW,160),(MID,160),(HIGH,160)],'falls':[(1024,2),(1024,1),(1024,0),(1600,0)],'stairs':[(656,2),(1456,1),(592,0)],'pools':[[(816,160),(944,104),(1168,128),(1264,232),(1192,336),(984,368),(824,280)]], 'feeds':[([(1024,288),(1008,368),(1024,440)],56), ([(1024,616),(1104,656),(1024,760)],56), ([(1024,936),(944,1024),(1024,1160)],56), ([(1472,928),(1568,992),(1600,1096)],48)],'outlets':[([(1024,1328),(1024,1416),(1120,1536)],72), ([(1600,1264),(1552,1392),(1312,1432)],56)],'basin':[(824,1344),(1008,1328),(1216,1368),(1336,1472),(1304,1536),(824,1536),(760,1440)],'paths':[[(656,392),(688,256),(768,200)],[(656,576),(608,624),(544,624)],[(1456,752),(1456,592),(1328,592)],[(1456,944),(1488,1024),(1728,1072)],[(592,1096),(560,960),(448,896)],[(0,1360),(320,1360),(592,1296),(704,1376)],[(1680,1456),(1920,1408),(2048,1424)]]}
]
# Global deduplicated tile bank. Animations reference native 8px pixels.
TILES=[];INDEX={};ANIMS={}
def tid(tile):
    key=tile.tobytes()
    if key not in INDEX:INDEX[key]=len(TILES);TILES.append(tile.copy())
    return INDEX[key]
blank=Image.new('RGBA',(8,8));tid(blank)
LAYOUTS=[];baseids={};waterids={};atlas_cols=64
for cfg in CONFIG:
    d=O/cfg['id'];d.mkdir(exist_ok=True);im=GRASS.copy();fronts=[]
    for poly,height in cfg['plateaus']:fronts.append(plateau(im,poly,height))
    for points in cfg['paths']:path(im,points,48)
    for x,p in cfg['stairs']:stairs(im,x,fronts[p][x],cfg['plateaus'][p][1])
    im.save(d/'terrain.png');waters=[];previews=[]
    for f in range(4):
        water=water_network(cfg,f)
        for x,p in cfg['falls']:fall(water,x,fronts[p][x],cfg['plateaus'][p][1],f)
        water.save(d/f'eau_{f+1}.png');waters.append(water)
        preview=Image.alpha_composite(im,water);preview.save(d/f'layout_{f+1}.png');previews.append(preview)
    bdata=[];wdata=[]
    for y in range(GH):
        for x in range(GW):
            rect=(x*8,y*8,x*8+8,y*8+8);bdata.append(tid(im.crop(rect))+1)
            frames=[tid(w.crop(rect)) for w in waters]
            if all(v==0 for v in frames):wdata.append(0)
            elif len(set(frames))==1:wdata.append(frames[0]+1)
            else:
                # Dedicated animation representative, even if its first frame matches a static tile.
                key=tuple(frames)
                if key not in ANIMS:ANIMS[key]=len(TILES);TILES.append(TILES[frames[0]].copy())
                wdata.append(ANIMS[key]+1)
    baseids[cfg['id']]=bdata;waterids[cfg['id']]=wdata
    desc={'id':cfg['id'],'name':cfg['name'],'description':cfg['description'],'size_px':[W,H],'grid_px':8,'grid_cells':[GW,GH],'plateaus':[{'top_polygon_px':poly,'face_height_px':height} for poly,height in cfg['plateaus']],'cascades':[{'x':x,'y':fronts[p][x],'height':cfg['plateaus'][p][1]} for x,p in cfg['falls']],'stairs':[{'x':x,'y':fronts[p][x],'height':cfg['plateaus'][p][1]} for x,p in cfg['stairs']],'suggested_edges':'Ouvertures visuelles seulement ; raccord à une carte existante à placer manuellement.'}
    (d/'layout.json').write_text(json.dumps(desc,ensure_ascii=False,indent=2));LAYOUTS.append(desc)
    thumb=previews[0].resize((1024,768),Image.Resampling.NEAREST);thumb.save(d/'apercu.png')
    print(cfg['id'],'rendered; bank',len(TILES))
# Build one common native atlas for all three maps.
rows=math.ceil(len(TILES)/atlas_cols);atlas=Image.new('RGBA',(atlas_cols*8,rows*8))
for i,t in enumerate(TILES):atlas.paste(t,((i%atlas_cols)*8,(i//atlas_cols)*8))
atlas.save(O/'Extension_Metano.png')
# .tile with all cells including padding, alpha premultiplied (binary alpha here).
records=[];payload=bytearray();offsets={};count=atlas_cols*rows
for i in range(count):
    tile=TILES[i] if i<len(TILES) else blank;key=tile.tobytes()
    if key not in offsets:
        offsets[key]=8+16*count+len(payload);b=io.BytesIO();tile.save(b,format='PNG');raw=b.getvalue();payload.extend(struct.pack('<q',len(raw))+raw)
    records.append(struct.pack('<IIQ',i%atlas_cols,i//atlas_cols,offsets[key]))
(O/'Extension_Metano.tile').write_bytes(struct.pack('<II',8,count)+b''.join(records)+payload)
ts={'type':'tileset','version':'1.10','name':'Extension_Metano','tilewidth':8,'tileheight':8,'columns':atlas_cols,'tilecount':count,'margin':0,'spacing':0,'image':'Extension_Metano.png','imagewidth':atlas.width,'imageheight':atlas.height,'tiles':[{'id':rep,'animation':[{'tileid':v,'duration':167} for v in seq]} for seq,rep in ANIMS.items()]}
(O/'Extension_Metano.tsj').write_text(json.dumps(ts,indent=2))
for desc in LAYOUTS:
    id=desc['id'];layers=[{'id':1,'name':'Terrain et falaises','type':'tilelayer','x':0,'y':0,'width':GW,'height':GH,'opacity':1,'visible':True,'data':baseids[id]},{'id':2,'name':'Rivière et cascades animées','type':'tilelayer','x':0,'y':0,'width':GW,'height':GH,'opacity':1,'visible':True,'data':waterids[id]}]
    tm={'type':'map','version':'1.10','tiledversion':'1.10.2','orientation':'orthogonal','renderorder':'right-down','width':GW,'height':GH,'tilewidth':8,'tileheight':8,'infinite':False,'nextlayerid':3,'nextobjectid':1,'layers':layers,'tilesets':[{'firstgid':1,'source':'../Extension_Metano.tsj'}]}
    (O/id/'layout.tmj').write_text(json.dumps(tm,separators=(',',':')))
meta={'size_px':[W,H],'grid_px':8,'maps':LAYOUTS,'atlas_tiles':count,'native_sheet':'Extension_Metano','native_animations':[{'tileid':rep,'Frames':[{'Sheet':'Extension_Metano','TexLoc':{'X':v%atlas_cols,'Y':v//atlas_cols}} for v in seq],'FrameLength':10} for seq,rep in ANIMS.items()],'limitations':['Layouts originaux, pas des zones officielles de Métano','Textures roche/herbe/escaliers natives répétées sans agrandissement','Contours de rivière et vaguelettes dessinés pour les nouveaux layouts','Grandes chutes allongées par répétition du milieu des frames originales','Pas de collisions ni de transitions configurées ; intégration moteur non testée']}
(O/'kit.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
# Overview sheet, not an import texture.
board=Image.new('RGB',(1584,500),'#1c2d26');draw=ImageDraw.Draw(board);fp='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';font=ImageFont.truetype(fp,19);small=ImageFont.truetype(fp,13)
draw.text((24,18),'MÉTANO / TROIS EXTENSIONS DE FALAISES',font=font,fill='#e8d493')
for i,desc in enumerate(LAYOUTS):
    preview=Image.open(O/desc['id']/'layout_1.png').resize((512,384),Image.Resampling.NEAREST);x=16+i*528;board.paste(preview,(x,62));draw.text((x,453),desc['name'],font=small,fill='#e8d493')
draw.text((24,479),'Chacune : 2048 × 1536 px · 256 × 192 cases · calques séparés · 4 phases d’eau',font=small,fill='#a9bda4');board.save(O/'planche.png')
def uri(p):return 'data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode()
data=[]
for desc in LAYOUTS:data.append({**desc,'terrain':uri(O/desc['id']/'terrain.png'),'water':[uri(O/desc['id']/f'eau_{i}.png') for i in range(1,5)]})
(R/'apercu_falaises_metano.html').write_text((S/'viewer.html').read_text().replace('__DATA__',json.dumps(data,ensure_ascii=False)))
print('3 layouts + Tiled + atlas PMDO + aperçu générés.',len(TILES),'tuiles.',len(ANIMS),'animations.')
