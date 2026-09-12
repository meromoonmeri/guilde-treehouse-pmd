"""Dix huttes générées : normalisation à l'échelle native Metano et exports PMDO.
python source/build_houses_metano.py — dépendance Pillow uniquement.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json, io, struct, base64, hashlib, argparse
parser=argparse.ArgumentParser();parser.add_argument("--organic-v2",action="store_true");args=parser.parse_args()
R=Path(__file__).resolve().parents[1]; S=R/'source/maisons_metano'; O=R/'sprites/maisons_metano'; O.mkdir(exist_ok=True)
NAMES=['Feuillue','Vannerie','Galets','Nénuphar','Gland','Argile','Pivoine','Mousse','Ginkgo','Coquille']
SLUGS=['feuillue','vannerie','galets','nenuphar','gland','argile','pivoine','mousse','ginkgo','coquille']
REF=R/'source/maisons_metano'
PREFIX='Maisons_Metano'
PREVIEW='apercu_maisons_metano.html'
if args.organic_v2:
    S=R/'source/maisons_organiques_v2';O=R/'sprites/maisons_organiques_v2';O.mkdir(exist_ok=True)
    NAMES=['Souche','Champignon','Calebasse','Fougère','Bambou','Cactus','Coco','Racines','Artichaut','Ruche']
    SLUGS=['souche','champignon','calebasse','fougere','bambou','cactus','coco','racines','artichaut','ruche']
    PREFIX='Maisons_Organiques_V2';PREVIEW='apercu_maisons_organiques_v2.html'
WIDTHS=[96,96,96,104,96,96,104,96,104,104]
W,H=112,128

def sprite(i):
    source=Image.open(S/f'paire_{i//2+1:02}.png').convert('RGBA')
    mid=source.width//2;gutter=16 if args.organic_v2 else 0
    source=source.crop((gutter if i%2==0 else mid+gutter,0,mid-gutter if i%2==0 else source.width-gutter,source.height))
    source.putdata([(0,0,0,0) if r>140 and b>100 and g<r*.45 and b>r*.80 else (r,g,b,255) for r,g,b,a in source.getdata()])
    bounds=source.getbbox(); assert bounds
    source=source.crop(bounds)
    scale=min(WIDTHS[i]/source.width,112/source.height)
    size=(round(source.width*scale),round(source.height*scale))
    source=source.resize(size,Image.Resampling.NEAREST).quantize(colors=48,method=Image.Quantize.FASTOCTREE,dither=Image.Dither.NONE).convert('RGBA')
    # Remove detached one-pixel generation debris; keep the connected structure only.
    opaque={(x,y) for y in range(source.height) for x in range(source.width) if source.getpixel((x,y))[3]}
    components=[]
    while opaque:
        start=opaque.pop();group={start};todo=[start]
        while todo:
            x,y=todo.pop()
            for dx,dy in [(-1,-1),(0,-1),(1,-1),(-1,0),(1,0),(-1,1),(0,1),(1,1)]:
                p=(x+dx,y+dy)
                if p in opaque:opaque.remove(p);group.add(p);todo.append(p)
        components.append(group)
    for group in components:
        if group is not max(components,key=len):
            for p in group:source.putpixel(p,(0,0,0,0))
    # Canvas and baseline are grid-aligned. Image content keeps its natural aspect ratio.
    out=Image.new('RGBA',(W,H));xy=((W-size[0])//2,120-size[1]);out.paste(source,xy)
    return out,{'content_size_px':list(size),'content_offset_px':list(xy),'scale_from_generated':scale}

def night(im):
    im=im.copy();im.putdata([(int(r*.49+5),int(g*.57+8),min(255,int(b*.77+23)),a) if a else (0,0,0,0) for r,g,b,a in im.getdata()]);return im

def write_tile(im,path):
    cells=[(x,y,im.crop((x*8,y*8,x*8+8,y*8+8))) for y in range(im.height//8) for x in range(im.width//8)]
    header=struct.pack('<II',8,len(cells));entries=[];payload=bytearray();offsets={}
    for x,y,t in cells:
        signature=t.tobytes()
        if signature not in offsets:
            offsets[signature]=8+16*len(cells)+len(payload)
            b=io.BytesIO();t.save(b,format='PNG');raw=b.getvalue();payload.extend(struct.pack('<q',len(raw))+raw)
        entries.append(struct.pack('<IIQ',x,y,offsets[signature]))
    path.write_bytes(header+b''.join(entries)+payload)

houses=[];atlases={m:Image.new('RGBA',(560,256)) for m in ['jour','nuit']}
for i in range(10):
    day,meta=sprite(i);paths={}
    for m,im in [('jour',day),('nuit',night(day))]:
        p=f'{i+1:02}_{SLUGS[i]}_{m}.png';im.save(O/p);paths[m]=p
        atlases[m].paste(im,((i%5)*W,(i//5)*H))
    houses.append({'id':i+1,'name':NAMES[i],'files':paths,'canvas_px':[W,H],'canvas_cells':[14,16], 'baseline_px':120,'placement_anchor_px':[56,120], 'atlas_rect_px':[(i%5)*W,(i//5)*H,W,H], 'atlas_rect_cells':[(i%5)*14,(i//5)*16,14,16],**meta})
for mode,atlas in atlases.items():
    atlas.save(O/f'{PREFIX}_{mode}.png');write_tile(atlas,O/f'{PREFIX}_{mode}.tile')
    (O/f'{PREFIX}_{mode}.tsj').write_text(json.dumps({'type':'tileset','version':'1.10','name':f'{PREFIX}_{mode}','tilewidth':8,'tileheight':8,'columns':70,'tilecount':2240,'margin':0,'spacing':0,'image':f'{PREFIX}_{mode}.png','imagewidth':560,'imageheight':256},indent=2))
manifest={'schema':1,'grid_px':8,'target':'PMDO Ground, TexSize=1','native_reference_sizes_px':[[80,111],[96,96],[110,99]],'reference':'Palikadude/Halcyon','source_commit':'da6c2130d641507447e6386a5e47a296e8cb4c71','origin':'10 nouvelles créations via générateur, pas des extractions du jeu','animation':'aucune, structures fixes','houses':houses}
(O/'maisons.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
# Contact sheet with labels; never used as an import texture.
fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';font=ImageFont.truetype(fontpath,22);small=ImageFont.truetype(fontpath,15)
board=Image.new('RGB',(1240,800),'#1d2b27');d=ImageDraw.Draw(board)
d.text((30,20),('MÉTANO / 10 NOUVELLES HUTTES — LOT 02' if args.organic_v2 else 'MÉTANO / 10 HUTTES ORGANIQUES'),font=font,fill='#ecdaa0')
d.text((30,57),'Échelle native PMDO • Grille 8 px • Dômes arrondis • PNG transparents',font=small,fill='#afc0a8')
for i,house in enumerate(houses):
    x=20+(i%5)*244;y=100+(i//5)*325
    d.rounded_rectangle((x,y,x+232,y+308),radius=8,fill='#2b3b31')
    im=Image.open(O/house['files']['jour']).resize((W*2,H*2),Image.Resampling.NEAREST);board.paste(im,(x+4,y+4),im)
    d.text((x+12,y+262),f'{i+1:02}  {house["name"]}',font=small,fill='#ecdaa0')
    d.text((x+12,y+284),'112 × 128 px · 14 × 16 cases',font=ImageFont.truetype(fontpath,12),fill='#afc0a8')
d.text((30,770),'Créations générées d’après Métano Town — référence : Palika / Halcyon. Vue agrandie ×2.',font=small,fill='#afc0a8')
board.save(O/'planche.png')
# Embedded assets make the viewer genuinely usable offline.
def uri(p):return 'data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode()
data={'houses':[{**h,'images':{m:uri(O/p) for m,p in h['files'].items()}} for h in houses], 'references':[{ 'name':n,'image':uri(REF/'references'/f'metano_{n}.png')} for n in ['normal','rock','fire']]}
html=(REF/'viewer.html').read_text()
if args.organic_v2:
    html=html.replace('Dix huttes pour Métano','Dix nouvelles huttes — lot 02').replace('feuillage, vannerie, galets, nénuphar, gland, argile, pivoine, mousse, ginkgo et coquille','souche, champignon, calebasse, fougère, bambou, cactus, coco, racines, artichaut et ruche').replace('sprites/maisons_metano/','sprites/maisons_organiques_v2/')
(R/PREVIEW).write_text(html.replace('__DATA__',json.dumps(data,ensure_ascii=False)))
print('10 maisons, 20 PNG individuels, 2 atlas, 2 .tile, 2 TSJ, manifeste, planche, aperçu.')
