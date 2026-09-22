from pathlib import Path
import hashlib, json, shutil
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'renders/world_map_zones_v1'
LAY = OUT / 'layers'; ANIM = OUT / 'animations'; SPR = OUT / 'assetsprite'
# Rebuild only this deliverable; remove stale outputs from the earlier prototype.
for p in (LAY, ANIM, SPR):
    if p.exists(): shutil.rmtree(p)
    p.mkdir(parents=True, exist_ok=True)
WORLD = ROOT / 'Explorers_of_Sky_-_World_Map.png'
ASSETS = ROOT / 'MapAssetsPMD2.webp'
DISCOVER = ROOT / 'animationmapdiscover.png'

# Native world-map canvas: keep the supplied 504x336 source at 1x.
base = Image.open(WORLD).convert('RGBA')
W, H = base.size

def font(size):
    p = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    return ImageFont.truetype(p, size)

def transparent_black(im):
    a = im.convert('RGBA')
    px = a.load()
    for y in range(a.height):
        for x in range(a.width):
            r,g,b,al = px[x,y]
            if r < 18 and g < 18 and b < 18: px[x,y] = (0,0,0,0)
    return a

# Independent background: exact canonical map, no repaint or rescale.
background = base.copy()
background.save(LAY / '00_fond_canonique_1x.png')

# Place markers over landmarks. The map itself remains untouched underneath.
# Coordinates are on the supplied native 504x336 map.
places = [
    ('volcan', 'Volcan', (62, 47), (30, 0, 116, 157), True),
    ('foret', 'Forêt', (342, 57), (620, 0, 780, 145), True),
    ('plage', 'Plage', (165, 220), (365, 0, 480, 92), True),
    ('desert', 'Désert', (414, 101), (495, 190, 640, 315), False),
    ('glace', 'Glace', (99, 284), (1135, 315, 1320, 510), False),
    ('ruines', 'Ruines', (233, 145), (680, 116, 860, 275), False),
    ('tour', 'Tour', (286, 188), (970, 12, 1100, 170), False),
]
asset_sheet = transparent_black(Image.open(ASSETS))

# Separate unlock/state layer: rings and status dots are generated UI, not baked into map art.
state = Image.new('RGBA', (W,H), (0,0,0,0)); sd = ImageDraw.Draw(state)
for key,label,(x,y),box,unlocked in places:
    col = (78,177,82,255) if unlocked else (133,83,53,255)
    sd.ellipse((x-8,y-8,x+8,y+8), fill=(54,35,22,255), outline=(244,213,141,255), width=2)
    sd.ellipse((x-5,y-5,x+5,y+5), fill=col)
    sd.text((x, y+11), label, anchor='ma', font=font(8), fill=(74,43,24,255))
state.save(LAY / '03_etat_deblocage.png')

# Canonical location asset layer: exact crops from the supplied PMD2 asset sheet.
landmarks = Image.new('RGBA', (W,H), (0,0,0,0))
for key,label,(x,y),box,unlocked in places:
    crop = asset_sheet.crop(box)
    # Keep native pixels; fit only for the 504px map preview using nearest-neighbor.
    maxw, maxh = (30, 30)
    scale = min(maxw / crop.width, maxh / crop.height)
    nw, nh = max(1, int(crop.width*scale)), max(1, int(crop.height*scale))
    crop = crop.resize((nw,nh), Image.Resampling.NEAREST)
    landmarks.alpha_composite(crop, (x-nw//2, y-nh//2))
landmarks.save(LAY / '02_emblemes_canoniques.png')

# Routes and discovered-area highlight remain independent of the art and can be replaced in-game.
routes = Image.new('RGBA', (W,H), (0,0,0,0)); rd = ImageDraw.Draw(routes)
route = [(62,47),(142,106),(233,145),(286,188),(342,57)]
rd.line(route, fill=(76,48,28,185), width=2, joint='curve')
rd.line(route, fill=(251,218,141,230), width=1, joint='curve')
routes.save(LAY / '01_routes_zones.png')

# A discrete overlay marks the three unlocked areas; it is not baked into the canonical background.
highlight = Image.new('RGBA', (W,H), (0,0,0,0)); hd = ImageDraw.Draw(highlight)
for key,label,(x,y),box,unlocked in places:
    if unlocked:
        hd.ellipse((x-12,y-12,x+12,y+12), outline=(255,238,134,180), width=2)
highlight.save(LAY / '04_surlignage_debloque.png')

# Exact 504x336 frames from the supplied discovery sheet (2 columns x 6 rows).
frames=[]
for row in range(6):
    for col in range(2):
        frame = Image.open(DISCOVER).convert('RGBA').crop((col*504, row*336, (col+1)*504, (row+1)*336))
        frames.append(frame)
for i,frame in enumerate(frames): frame.save(ANIM / f'WorldMap_discover_{i:02d}.png')
frames[0].save(ANIM / 'WorldMap_discover.webp', save_all=True, append_images=frames[1:], duration=140, loop=0, lossless=True)

# Full composition uses the canonical map + independent layers.
full = base.copy()
for layer in (routes, landmarks, state, highlight): full.alpha_composite(layer)
full.save(OUT / 'WorldMap_Zones.png')

# AssetSprite sheet made from the same native source crops.
sheet = Image.new('RGBA', (7*48,48), (0,0,0,0)); entries=[]
for i,(key,label,(x,y),box,unlocked) in enumerate(places):
    crop = asset_sheet.crop(box)
    scale=min(44/crop.width,44/crop.height)
    crop=crop.resize((max(1,int(crop.width*scale)),max(1,int(crop.height*scale))),Image.Resampling.NEAREST)
    sheet.alpha_composite(crop, (i*48+(48-crop.width)//2,(48-crop.height)//2))
    entries.append({'id':key,'label':label,'rect':[i*48,0,48,48],'unlocked_by_default':unlocked,'source_box':list(box)})
sheet.save(SPR/'WorldMap_Lieux_AssetSprite.png')
(SPR/'WorldMap_Lieux_AssetSprite.json').write_text(json.dumps({'format':'AssetSprite','frame_size':[48,48],'entries':entries},ensure_ascii=False,indent=2))

files={}
for p in OUT.rglob('*'):
    if p.is_file(): files[str(p.relative_to(OUT))]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
manifest={'canvas_px':[W,H],'native_background':'Explorers_of_Sky_-_World_Map.png','layers':5,'animation_frames':12,'animation_source':'animationmapdiscover.png','asset_source':'MapAssetsPMD2.webp','files':files,'provenance':'Fond et frames repris directement des fichiers canoniques fournis dans le dernier commit; les routes, marqueurs d etat et surlignages sont des calques UI independants.'}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print(f'World map built: {W}x{H}, {len(frames)} frames, {len(places)} locations')
