"""Ten coastal layouts guided by guide_compositions.png, native Metano material.
Shared Guild/Sharpedo clouds and exact night grading, 24 native Ground variants.
No engine runtime claim. Build outputs go to ~/.cache/cote_dix_pack.
"""
from pathlib import Path
import copy
import importlib.util
import json
import math
import sys
import zipfile

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'source'))
from zones_guidees.native_tools import Bank, BASE, CLIFF
spec = importlib.util.spec_from_file_location('native_ground', ROOT / 'source/pmdo_cote/build.py')
N = importlib.util.module_from_spec(spec)
spec.loader.exec_module(N)
REF = HERE / 'reference_autre_agent'
OUT = Path.home() / '.cache/cote_dix_pack'
WEB = ROOT / 'sprites/cote_dix_zones'
SIZE = (1312, 1024)
# x, native-sheet Y offset, number of 64px middle modules, wall extension, rear Y.
# Topology follows the ten panels of the generated composition guide, not its pixels.
CONFIG = [
 ('01_long_cap', 'Le grand cap', [(-112, 104, 17, 96, 216)]),
 ('02_mesa', 'La mesa marine', [(112, 112, 10, 144, 200)]),
 ('03_detroit', 'Les deux rives', [(-184, 144, 3, 144, 208), (848, 64, 4, 144, 176)]),
 ('04_deux_paliers', 'Les deux paliers', [(48, 328, 13, 96, 472), (-80, 0, 10, 96, 168)]),
 ('05_crique', 'La crique ouverte', [(-408, 208, 5, 144, 208), (816, 208, 5, 144, 208), (248, -72, 6, 48, 120)]),
 ('06_cap_est', 'Le cap de l est', [(384, 96, 15, 192, 200)]),
 ('07_cap_ouest', 'Le cap de l ouest', [(-640, 128, 15, 192, 192)]),
 ('08_corniche', 'La haute corniche', [(-64, 16, 15, 288, 312)]),
 ('09_archipel', 'Les trois mesas', [(-160, -8, 3, 96, 160), (888, -40, 3, 96, 136), (312, 376, 4, 144, 528)]),
 ('10_trois_terrasses', 'Les trois terrasses', [(-64, 480, 15, 96, 640), (-224, 192, 11, 144, 368), (576, -72, 8, 96, 120)]),
]
RECTS = {'ouest': (456,208,680,544), 'face': (912,448,976,544),
         'retour': (680,448,744,544), 'est': (1296,304,1512,544)}


def grade(im, mode):
    if mode == 'jour':
        return im.copy()
    # Exact formula and constants from the other agent's rebuild_falaise.py.
    a = np.array(im.convert('RGBA'))
    v = a[:,:,:3].astype(float)
    lum = (v @ np.array([.2126,.7152,.0722]))[:,:,None]
    a[:,:,:3] = np.rint((lum*.20 + v*.80)*np.array([.40,.42,.58])+np.array([4,8,15])).clip(0,255).astype('uint8')
    a[a[:,:,3] == 0] = 0
    return Image.fromarray(a)


def png(im, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, optimize=True)


def reference(name):
    return Image.open(REF / ('source__falaise__' + name + '.png')).convert('RGBA')


def backgrounds():
    # Six existing cloud families, moved as whole native-size blocks, never resized.
    source = reference('nuages_native')
    crops = [(16,24,168,72),(176,8,272,72),(272,16,368,64),
             (72,80,168,128),(176,72,296,128),(320,64,472,128)]
    dests = [(32,40),(272,16),(504,72),(728,32),(920,80),(1160,24)]
    strip = Image.new('RGBA', (1440,208))
    for rect, dest in zip(crops, dests):
        strip.paste(source.crop(rect), dest)
    # Prove extraction is lossless and that rectangles partition ALL cloud pixels.
    rebuilt = Image.new('RGBA', source.size)
    for rect in crops:
        rebuilt.paste(source.crop(rect), rect[:2])
    assert rebuilt.tobytes() == source.tobytes(), 'A cloud was cut by its extraction rectangle'
    stars = reference('astres_nuit_native')
    out = {}
    for mode in ['jour','nuit']:
        src = reference('ciel_'+mode+'_native')
        # The source sky has a faint baked moon in its right half. Use only
        # the moon-free left 240px, mirrored at the joins (no texture resampling).
        # The original 144px sky band ends at our new sea horizon as in Sharpedo.
        a = np.array(src)
        xs = np.arange(SIZE[0]) % 480
        xs = np.where(xs < 240, xs, 479-xs)
        sky = Image.fromarray(a[np.minimum(np.arange(SIZE[1]),src.height-1)[:,None], xs[None,:]])
        astres = Image.new('RGBA', SIZE)
        if mode == 'nuit':
            # One moon only. Extra left-hand stars use the moon-free source half.
            astres.paste(stars, (SIZE[0]-480, 0))
            for x in range(0, SIZE[0]-480, 240):
                astres.paste(stars.crop((0,0,min(240,SIZE[0]-480-x),184)), (x,0))
        clouds = grade(strip, mode)
        out[mode] = (sky, astres, clouds)
        for kind, im in [('CIEL',sky),('ASTRES',astres),('NUAGES',clouds)]:
            name = 'C10_'+mode.upper()+'_'+kind
            N.write_dir(OUT / f'Content/BG/{name}.dir', im)
            png(im, WEB / 'fonds' / f'{mode}_{kind.lower()}.png')
    return out, {'source_size': source.size, 'crops': crops, 'destinations': dests,
                 'strip_size': strip.size, 'speed_px_s': -4}


def clouds_at(strip, size, offset=0):
    out = Image.new('RGBA', size)
    for x in range(-(offset % strip.width), size[0], strip.width):
        out.paste(strip, (x,0))
    return out


def terrain_planes(bank, config):
    planes, provenance = [], []
    w,h = SIZE
    for p, (start, offset, count, extension, rear) in enumerate(config):
        # All columns belong to contiguous COMPLETE native modules. Their crown,
        # curves and foot are kept; only the native middle six rows repeat.
        sequence = ['ouest'] + ['retour' if i in (3,8,13) else 'face' for i in range(count)] + ['est']
        surface, rock = Image.new('RGBA',SIZE), Image.new('RGBA',SIZE)
        refs_ground, refs_rock, modules = {}, {}, []
        width = 224 + count*64 + 216
        x = start
        def put(im, refs, dx, dy, sheet, sx, sy, shore=False):
            if not (0 <= dx < w and 0 <= dy < h):
                return
            gid = bank.get(sheet,sx,sy)
            if not gid:
                return
            tile = bank.image(gid).copy()
            if shore:
                # Separate native north-shore grass from native river-blue pixels.
                # RGB of surviving pixels is untouched; this is an alpha cutout,
                # explicitly NOT a byte-identical original 8x8 tile.
                a = np.array(tile)
                remove = (a[:,:,2].astype(int) > a[:,:,0].astype(int)+8)
                a[remove] = 0
                tile = Image.fromarray(a)
            im.paste(tile,(dx,dy))
            refs[f'{dx//8},{dy//8}'] = [sheet,sx,sy,int(shore)]
        for module_index, name in enumerate(sequence):
            # Move complete modules on the grid, never rotate/repaint them.
            local_offset = offset + round(3*math.sin(module_index*.45))*8
            x0,y0,x1,y1 = RECTS[name]
            modules.append({'module':name,'source_rect':RECTS[name],'x':x,'offset_y':local_offset,
                            'extension_px':extension,'body_repeat_rows':6})
            for sx in range(x0//8,x1//8):
                dx = x + (sx-x0//8)*8
                if not 0 <= dx < w:
                    continue
                ys = [sy for sy in range(y0//8,y1//8)
                      if bank.get(CLIFF,sx,sy) and bank.image(bank.get(CLIFF,sx,sy)).getchannel('A').getbbox()]
                if not ys:
                    continue
                first,last = min(ys),max(ys)
                insertion = last-3
                # Source module body is indexed relative to its own foot; never
                # select colors independently or resample the cliff texture.
                body = list(range(insertion-6,insertion))
                assert all(bank.get(CLIFF,sx,sy) for sy in body)
                curve = round(7 * ((dx-start-width/2)/(width/2))**2)*8
                top = max(0, min(rear+curve, first*8+local_offset-32))
                top = top//8*8
                for dy in range(top,first*8+local_offset,8):
                    if dy < top+16:
                        put(surface,refs_ground,dx,dy,BASE,80+(dx//8)%16,96+(dy-top)//8,True)
                    elif dx-start < 16:
                        put(surface,refs_ground,dx,dy,BASE,72+(dx-start)//8,104+((dy-top)//8)%6,True)
                    elif start+width-dx <= 16:
                        put(surface,refs_ground,dx,dy,BASE,112+(dx-(start+width-16))//8,104+((dy-top)//8)%6,True)
                    else:
                        put(surface,refs_ground,dx,dy,BASE,(dx//8)%16,80+(dy//8)%16)
                for sy in range(first,insertion):
                    put(rock,refs_rock,dx,sy*8+local_offset,CLIFF,sx,sy)
                for i in range(extension//8):
                    put(rock,refs_rock,dx,insertion*8+local_offset+i*8,CLIFF,sx,body[i%6])
                for sy in range(insertion,last+1):
                    put(rock,refs_rock,dx,sy*8+local_offset+extension,CLIFF,sx,sy)
            x += x1-x0
        planes.extend([(f'Prairie {p+1}',surface),(f'Falaise {p+1}',rock)])
        provenance.append({'modules':modules,'ground':refs_ground,'cliffs':refs_rock})
    return planes, provenance


def make_map(asset, title, mode, planes, sea, banks, template):
    size = planes[0][1].size
    w,h = size[0]//8,size[1]//8
    obj = copy.deepcopy(template)
    obj['TexSize'] = 1
    obj['Name'] = {'DefaultText': title+' - '+mode, 'LocalTexts':{}}
    obj['AssetName'] = asset
    obj['Comment'] = 'Base editable. Collisions libres. Nuages et nuit Guild/Sharpedo. Voir README du pack.'
    obj['obstacles'] = [[{'Bounds':{'X':x*8,'Y':y*8,'Width':8,'Height':8},'Tags':0} for y in range(h)] for x in range(w)]
    sky_name = 'C10_'+mode.upper()
    obj['Background'] = {'$type':'RogueEssence.Dungeon.LayeredBG, RogueEssence', 'Layers':[
        {'BG':N.background(sky_name+'_CIEL')}, {'BG':N.background(sky_name+'_ASTRES')},
        {'BG':N.background(sky_name+'_NUAGES',0,-4,True)}]}
    layers = []
    def frames_for(images, bank):
        if not hasattr(bank, 'frame_cache'):
            bank.frame_cache = {}
        def frame(im,x,y):
            tile = im.crop((x*8,y*8,x*8+8,y*8+8))
            key = tile.tobytes()
            if key not in bank.frame_cache:
                bank.frame_cache[key] = bank.add(tile,x,y)
            return bank.frame_cache[key]
        def at(x,y):
            frames = [frame(im,x,y) for im in images]
            assert all(f is None for f in frames) or all(f is not None for f in frames)
            return frames if frames[0] is not None else []
        return at
    layers.append(N.layer('00 Mer - 8 phases palette',w,h,frames_for(sea,banks['sea']),10))
    for n,(label,im) in enumerate(planes):
        layers.append(N.layer(f'{n+1:02d} {label}',w,h,frames_for([im],banks['terrain'])))
    for label,draw in [('Vos sols et chemins',0),('Vos structures - base',0),('Vos structures - avant-plan',4)]:
        layers.append(N.layer(label,w,h,draw=draw))
    obj['Layers'] = layers
    return {'Version':'0.7.15.1','Object':obj}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    WEB.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(ROOT/'cote_metano_v2_pmdo.zip') as z:
        template = json.loads(z.read('Data/Ground/cote_v2_promontoire.rsground'))['Object']
    template.pop('Layers');template.pop('obstacles')
    bg, cloud_info = backgrounds()
    source_bank = Bank()
    banks = {mode:{'sea':N.TileBank('C10_'+mode.upper()+'_MER'),
                   'terrain':N.TileBank('C10_'+mode.upper()+'_TERRAIN')} for mode in ['jour','nuit']}
    original_sea = [Image.open(ROOT/f'sprites/cote_v2/01_promontoire/COTEV2_01_02_MER_PALETTE_{i:02d}.png').convert('RGBA') for i in range(8)]
    extended = []
    for im in original_sea:
        a = np.array(im)
        rows = np.arange(SIZE[1])+216  # V2 horizon 360 -> Guild/Sharpedo horizon 144.
        rows[rows>=im.height] = im.height-256+(rows[rows>=im.height]-im.height)%256
        moved = a[rows].copy()
        moved[:144] = 0
        extended.append(Image.fromarray(moved))
    seas = {mode:[grade(im,mode) for im in extended] for mode in ['jour','nuit']}
    for mode in seas:
        for i,im in enumerate(seas[mode]):
            png(im,WEB/'fonds'/f'{mode}_mer_{i:02d}.png')
    manifest = {'reference_agent_commit':'c16efe12d74361df5ba8625abb68260f5f8fc6dd',
                'clouds':cloud_info,'night':{'multiply':[.40,.42,.58],'add':[4,8,15],'saturation':.8},
                'sources':source_bank.source_info,'sea_frame_length':10,'zones':[],
                'native_runtime_tested':False}
    configs = [(slug,title,walls,None) for slug,title,walls in CONFIG]
    for i,slug in enumerate(['promontoire','terrasse'],1):
        path = ROOT/f'sprites/cote_v2/{i:02d}_{slug}/COTEV2_{i:02d}_03_TERRAIN.png'
        configs.append(('v2_'+slug,'V2 '+slug,None,path))
    for slug,title,walls,existing in configs:
        if walls:
            planes, provenance = terrain_planes(source_bank,walls)
        else:
            planes, provenance = [('Terrain V2 conserve',Image.open(existing).convert('RGBA'))],[]
        size = planes[0][1].size
        composed = Image.new('RGBA',size)
        for _,im in planes:
            composed = Image.alpha_composite(composed,im)
        # Entry marker on an opaque, grassy 24px area, chosen before night grading.
        a = np.array(composed).astype(int)
        grass = (a[:,:,1] >= a[:,:,0]-8)&(a[:,:,1]>a[:,:,2]+50)&(a[:,:,1]>160)&(a[:,:,3]==255)
        candidates=[]
        for y in range(24,size[1]-24,16):
            for x in range(24,size[0]-24,16):
                candidates.append((grass[y-12:y+12,x-12:x+12].mean(),-abs(x-size[0]//2)-abs(y-size[1]//3),x,y))
        score,_,cx,cy=max(candidates)
        assert score>.85,(slug,score)
        rec={'id':slug,'title':title,'size':size,'new':bool(walls),'entry':[cx-8,cy-8],
             'terrain_provenance':'native modules + alpha-separated north shore' if walls else 'previous generated V2 artwork unchanged',
             'planes':[name for name,_ in planes],'variants':{}}
        directory=WEB/slug;directory.mkdir(exist_ok=True)
        if provenance:
            N.save(OUT/f'provenance/{slug}.json',json.dumps(provenance,separators=(',',':')).encode())
        for mode in ['jour','nuit']:
            variants=[(name,grade(im,mode)) for name,im in planes]
            sea=[im.crop((0,0,*size)) for im in seas[mode]]
            asset='cote10_'+slug+'_'+mode
            doc=make_map(asset,title,mode,variants,sea,banks[mode],template)
            doc['Object']['Entities'][0]['Markers'][0]['Collider'].update(X=cx-8,Y=cy-8)
            N.save(OUT/f'Data/Ground/{asset}.rsground',json.dumps(doc,separators=(',',':')).encode())
            N.save(OUT/f'Data/Script/ground/{asset}/init.lua',f'-- Native background and tile animations.\nreturn {{}}\n'.encode())
            files=[]
            for i,(_,im) in enumerate(variants):
                filename=f'{mode}_{i:02d}.png';png(im,directory/filename);files.append(filename)
            sky,stars,clouds=bg[mode]
            image=Image.alpha_composite(sky.crop((0,0,*size)),stars.crop((0,0,*size)))
            image=Image.alpha_composite(image,clouds_at(clouds,size))
            image=Image.alpha_composite(image,sea[0])
            for _,im in variants:
                image=Image.alpha_composite(image,im)
            png(image,directory/f'{mode}_composition.png')
            rec['variants'][mode]={'asset':asset,'layers':files,'composition':f'{mode}_composition.png'}
        manifest['zones'].append(rec)
        print(slug,'jour/nuit',size,'planes',len(planes),flush=True)
    for mode in banks:
        for bank in banks[mode].values():
            bank.write(OUT/f'Content/Tile/{bank.name}.tile')
    for path in [WEB/'manifest.json',OUT/'manifest.json']:
        N.save(path,json.dumps(manifest,ensure_ascii=False,indent=2).encode())
    print('24 native Ground maps generated; validation still required.')


if __name__=='__main__':
    main()
