"""Trois layouts faits EXCLUSIVEMENT de références aux tuiles canoniques 8x8.
Aucun ImageDraw pour les assets, aucune mise à l'échelle, aucun tracé de rivière.
Les seules images redimensionnées sont les planches de présentation nommées apercu.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json,struct,io,math,hashlib,base64

R=Path(__file__).resolve().parents[1]
O=R/'sprites/metano_pixel_perfect';O.mkdir(exist_ok=True)
W,H=2048,1536;GW,GH=256,192;COLS=64;SHEET='Metano_Canonique_8px'
BASE='Metano_Town_Base';CLIFF='Metano_Town_Cliffs';ANIM='Metano_Town_Animation_Tileset'
RIVERS=[f'Metano_Town_River_Animation_{i}' for i in range(1,5)]
PATHS={BASE:R/'source/falaises_metano/natifs'/f'{BASE}.tile',CLIFF:R/'source/falaises_metano/natifs'/f'{CLIFF}.tile'}
PATHS.update({n:R/'source/eau_metano/natifs'/f'{n}.tile' for n in [ANIM]+RIVERS})
SOURCE={};SOURCE_INFO={}
for name,path in PATHS.items():
    raw=path.read_bytes();size,n=struct.unpack_from('<II',raw);assert size==8
    tiles={}
    for i in range(n):
        x,y,off=struct.unpack_from('<IIQ',raw,8+16*i);length=struct.unpack_from('<q',raw,off)[0]
        im=Image.open(io.BytesIO(raw[off+8:off+8+length])).convert('RGBA');assert im.size==(8,8)
        tiles[x,y]=im
    SOURCE[name]=tiles
    SOURCE_INFO[name]={'path':str(path.relative_to(R)),'git_blob_sha1':hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest(),'sha256':hashlib.sha256(raw).hexdigest(),'tiles':n}

# Every real atlas entry has a source coordinate. No generated colors or anonymous artwork.
TILES=[];ORIGINS=[];LOOKUP={};PROXIES={};ANIMATIONS={}
def tile_id(sheet,x,y):
    key=(sheet,x,y)
    if key not in LOOKUP:
        im=SOURCE[sheet].get((x,y))
        if im is None:LOOKUP[key]=0
        else:
            LOOKUP[key]=len(TILES)+1;TILES.append(im.copy());ORIGINS.append({'sheet':sheet,'texloc':[x,y],'role':'native'})
    return LOOKUP[key]

def animated(refs):
    frames=tuple(tile_id(*ref) for ref in refs)
    if len(set(frames))==1:return frames[0]
    assert all(frames),'All placed water phases must have a source tile'
    if frames not in PROXIES:
        PROXIES[frames]=len(TILES)+1;TILES.append(TILES[frames[0]-1].copy())
        origin=dict(ORIGINS[frames[0]-1]);origin['role']='animation_first_frame';ORIGINS.append(origin)
        ANIMATIONS[PROXIES[frames]]=frames
    return PROXIES[frames]

def put(layer,x,y,gid):
    if gid and 0<=x<GW and 0<=y<GH:layer[y*GW+x]=gid

def ground():return [tile_id(BASE,x%16,80+y%16) for y in range(GH) for x in range(GW)]

def cliff_column(layer,dx,sx,offset,extension,minsy):
    """Conserve la couronne, la courbe et le pied source ; insère des rangées natives au milieu."""
    rows=[y for x,y in SOURCE[CLIFF] if x==sx and y>=minsy and SOURCE[CLIFF][x,y].getbbox()]
    if not rows:return
    last=max(rows);insert=last-4
    # All this column's body tiles are already rock in the chosen canonical slices.
    body=list(range(insert-4,insert))
    assert all((sx,y) in SOURCE[CLIFF] for y in body)
    for sy in range(minsy,insert):put(layer,dx,sy+offset,tile_id(CLIFF,sx,sy))
    for j in range(extension):put(layer,dx,insert+offset+j,tile_id(CLIFF,sx,body[j%4]))
    for sy in range(insert,last+1):put(layer,dx,sy+offset+extension,tile_id(CLIFF,sx,sy))

def ribbon(layer,start_x,offset_y,extra_px,flats):
    # Excludes the native stairs, cave and water columns: dry layouts contain no such objects.
    cols=list(range(57,93))
    for segment in range(flats):
        cols.extend(range(85,93) if segment in [5,9,16,21] else range(114,122))
    cols.extend(range(162,189))
    while start_x//8+len(cols)<GW:cols.append(188)
    for i,sx in enumerate(cols):
        dx=start_x//8+i
        if 0<=dx<GW:
            minsy=56 if 85<=sx<=92 and i>=36 else 26 if sx<93 else 38 if sx>=162 else 54
            cliff_column(layer,dx,sx,offset_y//8,extra_px//8,minsy)

CONFIG=[
 {'id':'01_rempart','name':'Le grand rempart','description':'Une grande paroi et trois chutes alimentées depuis le nord.','ribbons':[{'x':0,'offset':224,'extra':192,'flats':24}], 'streams':[{'x':512,'walls':[0]},{'x':1024,'walls':[0]},{'x':1536,'walls':[0]}]},
 {'id':'02_paliers','name':'Les deux paliers','description':'Deux niveaux rocheux et une rivière centrale continue.','ribbons':[{'x':0,'offset':544,'extra':128,'flats':24},{'x':-128,'offset':80,'extra':128,'flats':26}], 'streams':[{'x':1024,'walls':[1,0]}]},
 {'id':'03_terrasses','name':'Les terrasses canoniques','description':'Trois niveaux reliés par les mêmes frames natives de cascade.','ribbons':[{'x':0,'offset':800,'extra':128,'flats':24},{'x':-64,'offset':352,'extra':128,'flats':25},{'x':-192,'offset':0,'extra':64,'flats':27}], 'streams':[{'x':1024,'walls':[2,1,0]}]}
]

def river_row(banks,water,dest_y,source_y,dx,lake=False):
    if not 0<=dest_y<GH:return
    # Canonical full reservoir + grassy shores, or a canonical 80px river neck.
    lo,hi=(103,144) if lake else (123,133)
    for sx in range(lo,hi):
        tx=sx+dx
        put(banks,tx,dest_y,tile_id(BASE,sx,source_y))
        refs=[(sheet,sx,source_y) for sheet in RIVERS]
        ids=[tile_id(*ref) for ref in refs]
        if any(ids):
            # Missing river tiles are source transparency, not a new recolored tile.
            if all(ids):put(water,tx,dest_y,animated(refs))
            else:
                assert len(set(ids))==1,'Unexpected sparse animated source boundary'

def waterfall(water,cx,top,end):
    rows=(end-top)//8;assert rows>=17
    for y in range(rows):
        sy=y if y<6 else (13+y-(rows-4) if y>=rows-4 else 8+(y-6)%4)
        for x in range(8):
            refs=[(ANIM,1+9*f+x,62+sy) for f in range(4)]
            put(water,cx//8-4+x,top//8+y,animated(refs))

BLANK=Image.new('RGBA',(8,8));STRAIGHT={}
def straight_tile(gid):
    if gid not in STRAIGHT:
        im=TILES[gid-1].copy()
        im.putdata([(round(r*255/a),round(g*255/a),round(b*255/a),a) if 0<a<255 else (r,g,b,a) for r,g,b,a in im.getdata()]);STRAIGHT[gid]=im
    return STRAIGHT[gid]

def render(layer,frame=0):
    out=Image.new('RGBA',(W,H))
    for i,gid in enumerate(layer):
        if gid:
            actual=ANIMATIONS[gid][frame] if gid in ANIMATIONS else gid
            out.paste(straight_tile(actual),((i%GW)*8,(i//GW)*8))
    return out

MAPS=[];DATA=[]
for cfg in CONFIG:
    p=O/cfg['id'];p.mkdir(exist_ok=True)
    g=ground();cliffs=[0]*(GW*GH);banks=[0]*(GW*GH);water=[0]*(GW*GH)
    for r in cfg['ribbons']:ribbon(cliffs,r['x'],r['offset'],r['extra'],r['flats'])
    intervals=[]
    for stream in cfg['streams']:
        cx=stream['x'];dx=cx//8-128
        walls=[(456+cfg['ribbons'][j]['offset'],544+cfg['ribbons'][j]['offset']+cfg['ribbons'][j]['extra']) for j in stream['walls']]
        assert walls==sorted(walls)
        # Selected fall positions must be on a flat, native front rather than an ascending return.
        for j in stream['walls']:
            rr=cfg['ribbons'][j];assert rr['x']+288<=cx-32 and cx+32<=rr['x']+288+rr['flats']*64
        shift=(walls[0][0]-456)//8
        for y in range(shift):river_row(banks,water,y,0,dx,True)
        for sy in range(57):river_row(banks,water,shift+sy,sy,dx,True)
        for i,(top,end) in enumerate(walls):
            next_top=walls[i+1][0] if i+1<len(walls) else H
            # Start one tile above the foot so transparent pixels at the native waterfall's end expose water.
            for y in range(end//8-1,next_top//8):river_row(banks,water,y,50+(y-(end//8-1))%2,dx)
            waterfall(water,cx,top,end)
            intervals.append({'center_x_px':cx,'top_px':top,'bottom_px':end})
    layers=[g,cliffs,banks,water]
    grass_png=render(g);cliff_png=render(cliffs);bank_png=render(banks)
    grass_png.save(p/'herbe.png');cliff_png.save(p/'falaises_bordures.png');bank_png.save(p/'berges_eau.png')
    dry=Image.alpha_composite(grass_png,cliff_png);dry.save(p/'sans_eau_sans_chemins.png')
    wetbase=Image.alpha_composite(dry,bank_png)
    for f in range(4):
        w=render(water,f);w.save(p/f'eau_frame_{f+1}.png');Image.alpha_composite(wetbase,w).save(p/f'avec_eau_frame_{f+1}.png')
    record={**cfg,'dimensions_px':[W,H],'cellules':[GW,GH],'grid_px':8,'waterfalls':intervals,'dry_layers':['herbe','falaises_bordures'],'wet_layers':['herbe','falaises_bordures','berges_eau','eau_animee']}
    (p/'layout.json').write_text(json.dumps(record,ensure_ascii=False,indent=2));MAPS.append(record);DATA.append(layers)
    print(cfg['id'],'composed with',len(TILES),'source tiles so far')

# Atlas entries are copies of actual native tiles, including animation representatives.
rows=math.ceil(len(TILES)/COLS);atlas_raw=Image.new('RGBA',(COLS*8,rows*8));atlas_png=atlas_raw.copy()
for i,t in enumerate(TILES):atlas_raw.paste(t,((i%COLS)*8,(i//COLS)*8));atlas_png.paste(straight_tile(i+1),((i%COLS)*8,(i//COLS)*8))
atlas_png.save(O/(SHEET+'.png'))
count=COLS*rows;entries=[];payload=bytearray();offsets={}
for i in range(count):
    t=TILES[i] if i<len(TILES) else BLANK;key=t.tobytes()
    if key not in offsets:
        offsets[key]=8+16*count+len(payload);b=io.BytesIO();t.save(b,format='PNG');raw=b.getvalue();payload.extend(struct.pack('<q',len(raw))+raw)
    entries.append(struct.pack('<IIQ',i%COLS,i//COLS,offsets[key]))
(O/(SHEET+'.tile')).write_bytes(struct.pack('<II',8,count)+b''.join(entries)+payload)
TS={'type':'tileset','version':'1.10','name':SHEET,'tilewidth':8,'tileheight':8,'columns':COLS,'tilecount':count,'margin':0,'spacing':0,'image':SHEET+'.png','imagewidth':atlas_png.width,'imageheight':atlas_png.height,'tiles':[{'id':gid-1,'animation':[{'tileid':f-1,'duration':167} for f in frames]} for gid,frames in ANIMATIONS.items()]}
(O/(SHEET+'.tsj')).write_text(json.dumps(TS,indent=2))
for record,layers in zip(MAPS,DATA):
    for wet in [False,True]:
        names=record['wet_layers'] if wet else record['dry_layers'];ls=[]
        for i,name in enumerate(names):ls.append({'id':i+1,'name':name,'type':'tilelayer','x':0,'y':0,'width':GW,'height':GH,'opacity':1,'visible':True,'data':layers[i]})
        tm={'type':'map','version':'1.10','orientation':'orthogonal','renderorder':'right-down','width':GW,'height':GH,'tilewidth':8,'tileheight':8,'infinite':False,'nextlayerid':len(ls)+1,'nextobjectid':1,'layers':ls,'tilesets':[{'firstgid':1,'source':'../'+SHEET+'.tsj'}]}
        (O/record['id']/('anime.tmj' if wet else 'sec.tmj')).write_text(json.dumps(tm,separators=(',',':')))
manifest={'reference':'Palikadude/Halcyon','commit':'da6c2130d641507447e6386a5e47a296e8cb4c71','sources':SOURCE_INFO,'source_tile_px':8,'atlas':{'name':SHEET,'columns':COLS,'tilecount':count,'used_entries':len(TILES),'entries':[{'tileid':i,**v} for i,v in enumerate(ORIGINS)]},'maps':MAPS,'native_animations':[{'tileid':gid-1,'Frames':[{'Sheet':SHEET,'TexLoc':{'X':(v-1)%COLS,'Y':(v-1)//COLS}} for v in frames],'FrameLength':10} for gid,frames in ANIMATIONS.items()],'rules':['Every placed tile is copied from a canonical source tile','No generated artwork, painted shores, hue filters, rotations or resampling','Dry ground is only Base cells x=0..15, y=80..95','Dry cliffs use only canonical columns 57..92, 114..121, 162..188, excluding stairs/cave/water','Tall faces and falls repeat whole native tile rows, never stretch','New composition, not an official Metano map; collisions and transitions not provided']}
(O/'provenance.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
# Presentation only: these thumbnails are explicitly separate from native game PNGs.
fp='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';font=ImageFont.truetype(fp,24);small=ImageFont.truetype(fp,15)
board=Image.new('RGB',(1600,1992),'#1b2a23');d=ImageDraw.Draw(board)
d.text((28,22),'MÉTANO / TUILES CANONIQUES — PIXEL PERFECT',font=font,fill='#e6d493')
d.text((28,62),'3 layouts · 2048 × 1536 px chacun · grille 8 px · aucun chemin, aucune maison',font=small,fill='#b6c6ae')
d.text((28,96),'SANS EAU — falaises, herbe et bordures',font=small,fill='#e6d493');d.text((816,96),'AVEC EAU — 4 frames natives, calques séparés',font=small,fill='#a3dae3')
for i,m in enumerate(MAPS):
    y=132+i*616
    for j,file in enumerate(['sans_eau_sans_chemins.png','avec_eau_frame_1.png']):
        im=Image.open(O/m['id']/file).resize((768,576),Image.Resampling.NEAREST);board.paste(im,(24+j*792,y))
    d.text((28,y+586),f'0{i+1} · {m["name"]}',font=small,fill='#e6d493')
board.save(O/'apercu_comparatif.png')
def uri(p):return 'data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode()
view=[]
for m in MAPS:
    p=O/m['id'];view.append({**m,'dry':uri(p/'sans_eau_sans_chemins.png'),'banks':uri(p/'berges_eau.png'),'water':[uri(p/f'eau_frame_{i}.png') for i in range(1,5)]})
(R/'apercu_metano_pixel_perfect.html').write_text((R/'source/metano_pixel_perfect/viewer.html').read_text().replace('__DATA__',json.dumps(view,ensure_ascii=False)))
print('Done:',len(TILES),'canonical tile entries,',len(ANIMATIONS),'native animations; 3 dry + 12 wet native renders.')
