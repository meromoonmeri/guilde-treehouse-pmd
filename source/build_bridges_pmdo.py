"""Normalise les deux images générées en ponts modulaires et ressources PMDO 8 px.
Exécution: python source/build_bridges_pmdo.py (Pillow).
Les images générées sont conservées pour une reconstruction déterministe.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json, struct, io, base64, hashlib
R=Path(__file__).resolve().parents[1]
O=R/'sprites/ponts_pmdo'; O.mkdir(exist_ok=True)
S=R/'source/ponts_generes'
NAMES=['ouest','centre_horizontal','est','nord','centre_vertical','sud']

def extract(name, size):
    im=Image.open(S/name).convert('RGBA')
    # Chroma key including antialiased magenta fringes; no partial alpha in game assets.
    im.putdata([(0,0,0,0) if (r>80 and b>g*1.05 and r>g*1.05) else (r,g,b,255) for r,g,b,a in im.getdata()])
    im=im.crop(im.getbbox()).resize(size,Image.Resampling.NEAREST)
    return im
h=Image.new('RGBA',(240,80)); h.paste(extract('pont_horizontal.png',(240,72)),(0,4))
v=Image.new('RGBA',(80,240)); v.paste(extract('pont_vertical.png',(72,240)),(4,0))
# Shared limited palette, no dithering: remove generation micro-noise without blurring pixels.
combined=Image.new('RGBA',(320,240)); combined.paste(h,(0,0)); combined.paste(v,(240,0))
combined=combined.quantize(colors=48,method=Image.Quantize.FASTOCTREE,dither=Image.Dither.NONE).convert('RGBA')
h=combined.crop((0,0,240,80)); v=combined.crop((240,0,320,240))
modules=[h.crop((i*80,0,(i+1)*80,80)) for i in range(3)]+[v.crop((0,i*80,80,(i+1)*80)) for i in range(3)]
# Align all joining rail/deck profiles exactly. Outer ends retain generated silhouette.
for k in range(3):
    seam=modules[1].crop((0,0,1,80))
    if k<2: modules[k].paste(seam,(79,0))
    if k>0: modules[k].paste(seam,(0,0))
for k in range(3,6):
    seam=modules[4].crop((0,0,80,1))
    if k<5: modules[k].paste(seam,(0,79))
    if k>3: modules[k].paste(seam,(0,0))

def phase(im,k,f):
    out=Image.new('RGBA',(80,80)); delta=[0,1,0,-1][f]
    for u in range(80):
        # Anchors do not translate: transition to the common moving seam away from posts.
        moving=True if k%3==1 else (u>=32 if k%3==0 else u<48)
        shift=delta if moving else 0
        if k<3: out.paste(im.crop((u,0,u+1,80)),(u,shift))
        else: out.paste(im.crop((0,u,80,u+1)),(shift,u))
    return out

def to_night(im):
    im=im.copy(); im.putdata([(int(r*.53),int(g*.59),min(255,int(b*.85+25)),a) if a else (0,0,0,0) for r,g,b,a in im.getdata()]); return im

def write_tile(path,im):
    """Native RogueEssence header/index and deduplicated length-prefixed PNG payloads."""
    cells=[]
    for y in range(im.height//8):
        for x in range(im.width//8): cells.append((x,y,im.crop((x*8,y*8,x*8+8,y*8+8))))
    head=bytearray(struct.pack('<II',8,len(cells))); payload=bytearray(); offsets={}; entries=[]
    for x,y,tile in cells:
        # Alpha is binary, so straight == premultiplied. Transparent RGB already zero.
        key=tile.tobytes()
        if key not in offsets:
            offsets[key]=8+16*len(cells)+len(payload)
            b=io.BytesIO(); tile.save(b,format='PNG'); raw=b.getvalue()
            payload.extend(struct.pack('<q',len(raw))+raw)
        entries.append(struct.pack('<IIQ',x,y,offsets[key]))
    path.write_bytes(head+b''.join(entries)+payload)

frames={}
for mode in ('jour','nuit'):
    atlas=Image.new('RGBA',(480,320)); frames[mode]=[]
    for f in range(4):
        row=Image.new('RGBA',(480,80))
        for k in range(6):
            tile=phase(modules[k],k,f)
            if mode=='nuit': tile=to_night(tile)
            row.paste(tile,(k*80,0))
        frames[mode].append(row)
        row.save(O/f'Ponts_Dores_{mode}_{f+1}.png')
        write_tile(O/f'Ponts_Dores_{mode}_{f+1}.tile',row)
        atlas.paste(row,(0,f*80))
    atlas.save(O/f'tilesheet_{mode}.png')
    tiles=[]; stamps=[]
    for k,name in enumerate(NAMES):
        cells=[]
        for y in range(10):
            for x in range(10):
                xx=k*10+x; tid=y*60+xx
                if not any(im.crop((xx*8,y*8,xx*8+8,y*8+8)).getbbox() for im in frames[mode]): continue
                tiles.append({'id':tid,'animation':[{'tileid':tid+600*f,'duration':180} for f in range(4)]})
                cells.append({'x':x,'y':y,'tile':{'AutoTileset':'','Associates':[],'NeighborCode':-1,'Layers':[{'Frames':[{'Sheet':f'Ponts_Dores_{mode}_{f+1}','TexLoc':{'X':xx,'Y':y}} for f in range(4)],'FrameLength':11}]}})
        stamps.append({'name':name,'width':10,'height':10,'cells':cells})
    (O/f'stamps_{mode}.json').write_text(json.dumps({'grid_px':8,'note':'Manifest de placement auxiliaire ; pas un format importé automatiquement par PMDO. Chaque tile utilise la structure native Tile du ground.','modules':stamps},ensure_ascii=False,indent=2))
    (O/f'tilesheet_{mode}.tsj').write_text(json.dumps({'type':'tileset','version':'1.10','name':f'Ponts_Dores_{mode}','tilewidth':8,'tileheight':8,'columns':60,'tilecount':2400,'spacing':0,'margin':0,'image':f'tilesheet_{mode}.png','imagewidth':480,'imageheight':320,'tiles':tiles},indent=2))
# A clear enlarged presentation, with separate importable data.
board=Image.new('RGB',(1040,1050),'#1b2926');d=ImageDraw.Draw(board)
fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
font=ImageFont.truetype(fontpath,22); small=ImageFont.truetype(fontpath,15)
d.text((32,24),'PONTS DORÉS / PMDO',font=font,fill='#f5d97f')
d.text((32,60),'Génération d’image • Modules 80 × 80 px • Découpage moteur 8 × 8 px',font=small,fill='#bac8b9')
for f in range(4):
    y=116+f*174
    d.text((32,y-23),f'PHASE {f+1}    Ouest / Centre / Est / Nord / Centre / Sud',font=small,fill='#dfc888')
    for yy in range(y,y+160,16):
        for xx in range(32,992,16): d.rectangle((xx,yy,xx+15,yy+15),fill='#34443b' if ((xx-32)//16+(yy-y)//16)%2 else '#2c3933')
    im=frames['jour'][f].resize((960,160),Image.Resampling.NEAREST);board.paste(im,(32,y),im)
y=850
d.text((32,y-28),'PALETTE NUIT · même géométrie',font=small,fill='#dfc888')
im=frames['nuit'][0].resize((960,160),Image.Resampling.NEAREST);board.paste(im,(32,y),im)
board.save(O/'planche.png')
# Animated sample bridges: phase matching and frozen anchors, no world-map claims.
samples=[]
for f in range(4):
    im=Image.new('RGB',(640,360),'#344944')
    row=frames['jour'][f]
    for j,k in enumerate([0,1,1,1,1,1,2]):
        t=row.crop((k*80,0,(k+1)*80,80));im.paste(t,(40+j*80,32),t)
    for j,k in enumerate([3,4,5]):
        t=row.crop((k*80,0,(k+1)*80,80));im.paste(t,(280,120+j*80),t)
    samples.append(im.resize((1280,720),Image.Resampling.NEAREST))
samples[0].save(O/'assemblage.gif',save_all=True,append_images=samples[1:],duration=180,loop=0,disposal=2)
def uri(p,mime='image/png'):return 'data:'+mime+';base64,'+base64.b64encode(p.read_bytes()).decode()
html='''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Ponts dorés PMDO</title><style>body{background:#1b2926;color:#eee8d5;font:16px system-ui;margin:0}main{max-width:1040px;margin:auto;padding:28px}h1{color:#f5d97f}p{line-height:1.6;color:#bfcbbd}img{display:block;max-width:100%;image-rendering:pixelated;margin:20px auto}a{color:#f5d97f}</style><main><p>GUILDE TREEHOUSE / NOUVELLE VERSION GÉNÉRÉE</p><h1>Ponts suspendus — bois doré</h1><p>Inspirés de ta référence PMD : planches jaunes, veinures ocre et cordages.<br>Modules répétables de 80 × 80 px, ressources moteur découpées en 8 × 8 px.</p><h2>Assemblage animé</h2><img src="__GIF__" alt="Ponts horizontaux et verticaux animés"><h2>Tilesheet · les quatre phases</h2><img src="__BOARD__" alt="Planche jour avec quatre phases et aperçu nuit"><p>Les PNG d’import ont un vrai fond transparent. Cette planche légendée sert uniquement à la présentation.</p><p>Fichiers dans sprites/ponts_pmdo : PNG, huit ressources .tile, TSJ et manifests de placement. Les .tile doivent être ajoutés à l’index de town02. Les manifests JSON sont auxiliaires, pas des cartes .rsground.</p><p>Grille Metano de 8 px vérifiée dans town02. Le fichier WaterfallVillageCapital.rsground est sous Git LFS et n’a pas pu être téléchargé : son TexSize et le placement dans cette carte restent à valider dans l’éditeur. Aucun fichier de town02 n’a été modifié.</p></main></html>'''
(R/'apercu_ponts_pmdo.html').write_text(html.replace('__GIF__',uri(O/'assemblage.gif','image/gif')).replace('__BOARD__',uri(O/'planche.png')))
print('Ponts générés normalisés : PNG / .tile 8px / TSJ / stamps / GIF / aperçu.')
