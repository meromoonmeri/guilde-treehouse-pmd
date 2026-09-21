"""Authored network, unchanged FrostyForest 24px DTEF cells. No generated terrain.
Run from repository root: .venv/bin/python source/winter_forest_native_v2/build.py
"""
from pathlib import Path
import hashlib, io, json, math, re, sys, zipfile
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
SRC = Path(__file__).resolve().parent
OUT = ROOT / 'renders/winter_forest_native_v2'
REF = SRC / 'references'
PREFIX = 'WinterNativeV2'
CELL, COLS, ROWS = 24, 21, 23
SIZE = (CELL * COLS, CELL * ROWS)
RAW_COMMIT = '03c80dad937911572f8fb19903771a47956fc696'
ENGINE_COMMIT = '8b7eafafa73ff0c10b9e8fd9348559ee1b5dfe8b'
SCENES = [
    dict(id='01_lisiere', title='La lisière', grid=[0, 2], ports='NSE', weather='cloudy', paths=[[(10,0),(10,4),(8,9),(10,14),(10,22)],[(9,11),(15,11),(20,11)]]),
    dict(id='02_lacets', title='Les lacets', grid=[1, 2], ports='NW', weather='cloudy', paths=[[(0,11),(4,11),(6,16),(13,16),(14,10),(9,6),(10,0)]]),
    dict(id='03_sapiniere', title='Le sentier des arbres givrés', grid=[0, 1], ports='NS', weather='boreal', paths=[[(10,0),(10,3),(6,8),(7,12),(13,17),(10,21),(10,22)]]),
    dict(id='04_clairiere', title='La clairière', grid=[1, 1], ports='NS', weather='cloudy', paths=[[(10,0),(10,22)]]),
    dict(id='05_corniche', title='Le détour du bosquet', grid=[0, 0], ports='SE', weather='boreal', paths=[[(10,22),(10,19),(5,15),(5,10),(10,7),(15,8),(17,11),(20,11)]]),
    dict(id='06_seuil', title='Le seuil de l’arène', grid=[1, 0], ports='NSW', weather='boreal', paths=[[(10,0),(10,5),(13,10),(12,16),(10,19),(10,22)],[(0,11),(5,11),(10,12),(13,11)]])
]
LINKS = [('01_lisiere','N','03_sapiniere','S'),('01_lisiere','E','02_lacets','W'),('02_lacets','N','04_clairiere','S'),('03_sapiniere','N','05_corniche','S'),('04_clairiere','N','06_seuil','S'),('05_corniche','E','06_seuil','W'),('06_seuil','N','arena_v5','S')]

def dump(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def png(image):
    b = io.BytesIO(); image.save(b, format='PNG'); return b.getvalue()

def font(size):
    return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', size)

def layout(scene):
    image = Image.new('L', (COLS, ROWS))
    d = ImageDraw.Draw(image)
    for points in scene['paths']:
        d.line(points, fill=255, width=5, joint='curve')
        for x,y in points[1:-1]:
            d.ellipse((x-2,y-2,x+2,y+2), fill=255)
    if scene['id']=='04_clairiere':
        d.ellipse((3,4,17,19), fill=255)
        d.rectangle((5,6,6,7), fill=0)
        d.point((15,15), fill=0)
    if scene['id']=='01_lisiere':
        d.ellipse((5,7,14,16), fill=255)
    if scene['id']=='06_seuil':
        d.ellipse((7,7,16,16), fill=255)
    # Seal every boundary except explicitly declared, 3-cell/72px ports.
    a = np.array(image) > 0
    a[:3,:] = a[-3:,:] = a[:,:3] = a[:,-3:] = False
    for direction in scene['ports']:
        if direction=='N': a[:3,9:12] = True
        if direction=='S': a[-3:,9:12] = True
        if direction=='W': a[10:13,:3] = True
        if direction=='E': a[10:13,-3:] = True
    return a

def mapping():
    text = (ROOT/'source/dungeon_autotiles_v1/references/engine/DtefImportHelper.cs').read_text()
    values = re.search(r'FieldDtefMapping\s*=\s*\{(.*?)\}',text,re.S).group(1)
    values = [int(x.strip(),0) for x in values.split(',') if x.strip()]
    assert len(values)==48 and len(set(values)-{-1})==47
    return {value:i for i,value in enumerate(values) if value>=0}

def neighbor_mask(world,x,y):
    # Wall connectivity continues outside the atlas except the two external gates.
    def wall(xx,yy):
        if 0<=xx<world.shape[1] and 0<=yy<world.shape[0]: return not world[yy,xx]
        if yy<0 and 30<=xx<33: return False  # 06.N -> legacy arena, logical only
        if yy>=ROWS*3 and 9<=xx<12: return False  # exterior -> 01.S
        return True
    card = [(0,1),(-1,0),(0,-1),(1,0)]
    diag = [(-1,1),(-1,-1),(1,-1),(1,1)]
    bits = [wall(x+dx,y+dy) for dx,dy in card]
    mask = sum(int(v)<<i for i,v in enumerate(bits))
    for i,(dx,dy) in enumerate(diag):
        if bits[i] and bits[(i+1)%4] and wall(x+dx,y+dy): mask |= 1<<(i+4)
    return mask

def ora(path, layers, merged):
    root = ET.Element('image', w=str(merged.width), h=str(merged.height), name=path.stem, version='0.0.3')
    stack = ET.SubElement(root,'stack')
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
        for i,(name,image) in enumerate(reversed(layers)):
            member=f'data/layer{i}.png'
            ET.SubElement(stack,'layer',name=name,src=member,x='0',y='0',opacity='1.0',visibility='visible',**{'composite-op':'svg:src-over'})
            z.writestr(member,png(image))
        z.writestr('stack.xml',ET.tostring(root,encoding='utf-8'))
        z.writestr('mergedimage.png',png(merged))

def build_terrain():
    OUT.mkdir(parents=True,exist_ok=True)
    sheets = [Image.open(REF/f'FrostyForest_tileset_{i}.png').convert('RGBA') for i in range(3)]
    slots = mapping()
    world = np.zeros((ROWS*3,COLS*2),bool)
    for scene in SCENES:
        gx,gy=scene['grid'];world[gy*ROWS:(gy+1)*ROWS,gx*COLS:(gx+1)*COLS]=layout(scene)
    fullsize = (world.shape[1]*CELL,world.shape[0]*CELL)
    floor,trees = Image.new('RGBA',fullsize),Image.new('RGBA',fullsize)
    placements=[]
    rng=np.random.default_rng(21092026)
    for y in range(world.shape[0]):
        for x in range(world.shape[1]):
            # Native floor variant1 contains stones: kept sparse, away from gates.
            edge = x%COLS<3 or x%COLS>=COLS-3 or y%ROWS<3 or y%ROWS>=ROWS-3
            variant = int(not edge and rng.random()<.10)
            fs = slots[255];fx=(12+fs%6)*CELL;fy=fs//6*CELL
            floor.paste(sheets[variant].crop((fx,fy,fx+CELL,fy+CELL)),(x*CELL,y*CELL))
            placements.append(dict(layer='snow',xy=[x,y],variant=variant,mask=255,rect=[fx,fy,CELL,CELL]))
            if not world[y,x]:
                mask=neighbor_mask(world,x,y);slot=slots[mask]
                sx=(slot%6)*CELL;sy=slot//6*CELL
                valid=[i for i,s in enumerate(sheets) if s.crop((sx,sy,sx+CELL,sy+CELL)).getextrema()[3]==(255,255)]
                variant=int(rng.choice(valid, p=[.55,.20,.25] if mask==255 else None));tile=sheets[variant].crop((sx,sy,sx+CELL,sy+CELL))
                trees.paste(tile,(x*CELL,y*CELL))
                placements.append(dict(layer='forest',xy=[x,y],variant=variant,mask=mask,rect=[sx,sy,CELL,CELL]))
    terrain=Image.alpha_composite(floor,trees)
    terrain.save(OUT/f'{PREFIX}_NetworkTerrain.png')
    records=[]
    for scene in SCENES:
        dest=OUT/scene['id'];dest.mkdir(exist_ok=True)
        x,y=scene['grid'];box=(x*SIZE[0],y*SIZE[1],(x+1)*SIZE[0],(y+1)*SIZE[1])
        stem=f'{PREFIX}_{scene["id"]}'
        layer_list=[('Neige native — sous-sol reconstitué',floor.crop(box)),('Bosquets natifs — modules complets avec leur fond',trees.crop(box))]
        for label,im in zip(['Snow','Forest'],[im for _,im in layer_list]): im.save(dest/f'{stem}_{label}.png')
        composite=terrain.crop(box);composite.save(dest/f'{stem}_Terrain.png')
        # Intent only, not PMDO collision data: floor=white, forest=black.
        walk=Image.fromarray((layout(scene)*255).astype('uint8')).resize(SIZE,Image.Resampling.NEAREST)
        walk.save(dest/f'{stem}_WalkIntent.png')
        ora(dest/f'{stem}_Layers.ora',layer_list,composite)
        local=[dict(p,xy=[p['xy'][0]-x*COLS,p['xy'][1]-y*ROWS]) for p in placements if x*COLS<=p['xy'][0]<(x+1)*COLS and y*ROWS<=p['xy'][1]<(y+1)*ROWS]
        dump(dest/f'{stem}_Placements.json',local)
        records.append(dict(scene,stem=stem,size=SIZE,walkable_cells=int(layout(scene).sum())))
    dump(OUT/'network.json',dict(tile_px=CELL,size=SIZE,grid_cells=[COLS,ROWS],port_width_px=72,scenes=records,links=LINKS,external=['01_lisiere.S'],arena='renders/ice_arena_northern_sky_v5',runtime_validated=False))
    dump(OUT/'native_placements.json',placements)
    dump(OUT/'world_grid.json',world.astype(int).tolist())
    return terrain

def build_board():
    board=Image.new('RGB',(1128,1950),'#10202a');d=ImageDraw.Draw(board)
    d.text((36,25),'FORÊT GIVRÉE · VERSION NATIVE 02',font=font(26),fill='#e4f3eb')
    d.text((36,67),'Neige et arbres Frosty Forest · pixels et échelle d’origine',font=font(17),fill='#b6d5c4')
    d.text((36,94),'6 cartes originales / modules 24 px / passages 72 px / aucun terrain généré',font=font(14),fill='#9cb4b5')
    for s in SCENES:
        gx,gy=s['grid'];x=36+gx*552;y=190+gy*580
        d.text((x,y-30),s['id'][:2]+'  '+s['title'],font=font(16),fill='#e4f3eb')
        im=Image.open(OUT/s['id']/f'{PREFIX}_{s["id"]}_Terrain.png');board.paste(im,(x,y))
        d.rectangle((x-1,y-1,x+SIZE[0],y+SIZE[1]),outline='#60756d')
    d.text((610,132),'↑ Vers l’arène V5 (inchangée)',font=font(16),fill='#98e0ca')
    d.text((185,1907),'↑ Arrivée extérieure',font=font(16),fill='#98e0ca')
    board.save(OUT/f'{PREFIX}_Board.png')

def build_provenance():
    sources=[]
    for p in sorted(REF.glob('*.png')):
        original=p.name.removeprefix('FrostyForest_')
        sources.append(dict(file=p.name,sha256=sha(p),git_blob=hashlib.sha1(f'blob {p.stat().st_size}\0'.encode()+p.read_bytes()).hexdigest(),url=f'https://github.com/PMDCollab/RawAsset/blob/{RAW_COMMIT}/TileDtef/FrostyForest/{original}',used_in_terrain=original in ['tileset_0.png','tileset_1.png','tileset_2.png']))
    engine=ROOT/'source/dungeon_autotiles_v1/references/engine'
    dump(SRC/'provenance.json',dict(repository='https://github.com/PMDCollab/RawAsset',commit=RAW_COMMIT,sources=sources,engine_commit=ENGINE_COMMIT,engine_files=[dict(path=str((engine/name).relative_to(ROOT)),sha256=sha(engine/name)) for name in ['DtefImportHelper.cs','AutoTileAdjacent.cs']],method='Unchanged opaque 24×24 source rectangles. Official 47-case connectivity across the complete 2×3 atlas. Authored layouts; not original game maps. No resizing, reflection, recolor, rotation, retouching or generated pixels in terrain.',rights='Original rights retained. Public repository availability is not a license grant.'))

if __name__=='__main__':
    build_terrain();build_board();build_provenance()
    print('Built six native maps and complete atlas:',OUT)
