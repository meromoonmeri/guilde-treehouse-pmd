"""Non-destructive layered beach. Source pixels at phase zero, new guided water motion.
Run from any directory; only writes this version's outputs and its root viewer.
"""
from pathlib import Path
import base64
import hashlib
import io
import json
import math
import shutil
import zipfile
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
from scipy import ndimage as nd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'renders/beach_layers_v1'
SRC = ROOT / 'DSVFS.png'
WAVE_REF = ROOT / 'DS _ DSi - Pokemon Mystery Dungeon_ Explorers of Time _ Darkness - Backgrounds - Beach & Path to Beach.png'
N, MS = 64, 50
WAVE_ROWS = [8, 63, 117, 171, 225, 279, 334, 390, 444, 500, 558, 612, 665, 719, 772, 823, 877]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def masked(rgb, mask):
    a = np.zeros((*mask.shape, 4), np.uint8)
    a[mask, :3] = rgb[mask]
    a[mask, 3] = 255
    return a

def save_png(a, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(a).save(path, optimize=True)

def masks_for(a):
    h, w = a.shape[:2]
    yy, xx = np.mgrid[:h, :w]
    r, g, b = np.moveaxis(a.astype(float), 2, 0)
    blue = ((b > r + 18) & (g > r + 10))
    pale = (b > 185) & (g > 185) & (b > r - 25)
    sea = (yy > 270) & (blue | pale)
    sky = (yy < 100) & blue
    # The foam includes pale cyan edge pixels, not just pure white.
    foam = sea & (r > 132) & (g > 180) & (b > 180)
    green = (g > r * 1.025) & (g > b * 1.18) & ~sea & ~sky
    # Keep woody palm stems with the palms, not the rock layer.
    trunks = np.zeros((h, w), bool)
    for x0, y0, x1, y1 in [(339,102,350,126),(357,106,367,132),
                           (56,254,65,279),(84,252,95,280),(692,244,702,267)]:
        trunks[y0:y1, x0:x1] = True
    vegetation = green | (trunks & (r < 190) & (g < 170) & ~sea)
    rock = (r > g * 1.16) & (g < 148) & (b < 135) & ~vegetation & ~sea & ~sky
    # The input has antialiased edge colours: do not leave isolated cliff highlights
    # or one-pixel island outlines on the sand layer. Resolve these residual components
    # to the nearest plausible material, without changing any source RGB.
    sand_seed = ~(sea | sky | vegetation | rock)
    sl, _ = nd.label(sand_seed)
    counts = np.bincount(sl.ravel()); counts[0] = 0
    main_sand = sl == counts.argmax()
    ambiguous = sand_seed & ~main_sand
    families = [sky, sea, vegetation, rock]
    scores = []
    for family in families:
        distance, xy = nd.distance_transform_edt(~family, return_indices=True)
        donor = a[xy[0], xy[1]].astype(float)
        colour = np.linalg.norm(a.astype(float)-donor, axis=2)
        scores.append(distance * 12 + colour * .5)
    choice = np.argmin(scores, axis=0)
    for i, family in enumerate(families):
        family |= ambiguous & (choice == i)
    foam = sea & (r > 132) & (g > 180) & (b > 180)
    labels, count = nd.label(rock)
    islets = np.zeros_like(rock)
    for i, box in enumerate(nd.find_objects(labels), 1):
        if box and box[0].start >= 340 and box[0].stop < h - 8 and box[1].stop-box[1].start < 65:
            islets |= labels == i
    rear = rock & (yy < 210)
    shore_rocks = rock & ~rear & ~islets
    sand = ~(sea | sky | vegetation | rock)
    return [
        ('01_ciel', 'Ciel visible', sky),
        ('02_sable', 'Sable et accès', sand),
        ('03_mer', 'Mer · surface', sea & ~foam),
        ('04_ecume', 'Écume et liserés', foam),
        ('05_falaises_fond', 'Falaises du fond', rear),
        ('06_vegetation_fond', 'Palmiers et plantes du fond', vegetation & (yy < 200)),
        ('07_vegetation_proche', 'Palmiers et plantes proches', vegetation & (yy >= 200)),
        ('08_rochers_rivage', 'Rochers du rivage', shore_rocks),
        ('09_ilots', 'Îlots rocheux', islets),
    ], sea, foam

def wave_guide():
    a = np.array(Image.open(WAVE_REF).convert('RGB')).astype(float)
    heights = []
    for y in WAVE_ROWS:
        p = a[y:y+47,865:1180]
        light = (p.min(2) > 190) & (p.max(2)-p.min(2) < 50)
        # A nearly dissolved wave has no reliable bright crest: return to the rest position.
        heights.append(float(np.where(light)[0].mean()) if light.sum() > 30 else None)
    heights = np.array([heights[0] if x is None else x for x in heights])
    return heights

def animator(rgb, sea, foam, heights):
    h, w = sea.shape
    yy, xx = np.mgrid[:h, :w]
    # Fill ONLY the hidden water beneath the extracted foam from nearby visible water.
    # Nearest-neighbour propagation also supplies safe off-footprint samples for the warp.
    clear_blue = sea & ~foam & (rgb[:,:,0] < 125) & (rgb[:,:,2] > 190)
    nearest = nd.distance_transform_edt(~clear_blue, return_distances=False, return_indices=True)
    base = rgb[nearest[0], nearest[1]].copy()
    base[sea & ~foam] = rgb[sea & ~foam]
    rock_distance = nd.distance_transform_edt(sea)
    # Anchor all contact edges. A broad taper avoids compression/folds and dragged
    # antialiased rock colours. The offshore foam line and blue depth bands can swell.
    edge_gain = np.clip((rock_distance - 5) / 18, 0, 1)
    # Foam displacement is constrained to the water footprint. No sand/rock moves.
    def frame(k):
        k %= N
        theta = 2 * math.pi * k / N
        p = k / N * len(heights)
        j, f = int(p), p % 1
        f = (1-math.cos(math.pi*f))/2
        crest = heights[j] * (1-f) + heights[(j+1) % len(heights)] * f
        run = max(0, (heights[0]-crest)*0.23)
        local = .7*(np.sin(theta + xx/47)-np.sin(xx/47))
        dy = (run + local) * edge_gain
        dx = .65*(np.sin(theta + yy/29)-np.sin(yy/29))*edge_gain
        sx = np.clip(np.rint(xx-dx).astype(int), 0, w-1)
        sy = np.clip(np.rint(yy-dy).astype(int), 0, h-1)
        surface = masked(base[sy,sx], sea)
        fm = foam[sy,sx] & sea
        froth = masked(rgb[sy,sx], fm)
        return surface, froth
    return frame, base

def write_ora(layers, composite):
    stack = ET.Element('image', w=str(composite.shape[1]), h=str(composite.shape[0]), name='Beach · référence exacte')
    group = ET.SubElement(stack, 'stack')
    with zipfile.ZipFile(OUT/'BeachV1_calques.ora', 'w') as z:
        z.writestr('mimetype', 'image/openraster', compress_type=zipfile.ZIP_STORED)
        for ident, label, a in reversed(layers):
            file = f'data/{ident}.png'
            ET.SubElement(group, 'layer', name=label, src=file, opacity='1.0', visibility='visible', x='0', y='0', **{'composite-op':'svg:src-over'})
            b = io.BytesIO(); Image.fromarray(a).save(b,format='PNG'); z.writestr(file,b.getvalue())
        z.writestr('stack.xml',ET.tostring(stack,encoding='utf-8',xml_declaration=True))
        b=io.BytesIO();Image.fromarray(composite).save(b,format='PNG');z.writestr('mergedimage.png',b.getvalue())
        thumb=Image.fromarray(composite);thumb.thumbnail((256,256));b=io.BytesIO();thumb.save(b,format='PNG');z.writestr('Thumbnails/thumbnail.png',b.getvalue())

def uri(im):
    b = io.BytesIO(); im.save(b,format='PNG',optimize=True)
    return 'data:image/png;base64,'+base64.b64encode(b.getvalue()).decode()

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rgb = np.array(Image.open(SRC).convert('RGB'))
    h,w = rgb.shape[:2]
    definitions, sea, foam = masks_for(rgb)
    layers = [(i,n,masked(rgb,m)) for i,n,m in definitions]
    reference = np.dstack([rgb,np.full((h,w),255,np.uint8)])
    stack = np.stack([m for _,_,m in definitions])
    assert np.all(stack.sum(0) == 1)
    assert np.array_equal(np.sum([a.astype(np.uint16) for _,_,a in layers],axis=0).astype(np.uint8),reference)
    save_png(reference,OUT/'BeachV1_reference_recomposee.png')
    for i,n,a in layers:
        save_png(a,OUT/'calques'/f'BeachV1_{i}.png')
    save_png(np.uint8(sea)*255,OUT/'masques/mer.png')
    save_png(np.uint8(foam)*255,OUT/'masques/ecume.png')
    heights=wave_guide();frame,base=animator(rgb,sea,foam,heights)
    fixed=Image.new('RGBA',(w,h))
    for i,n,a in layers:
        if i not in ['03_mer','04_ecume']:fixed.alpha_composite(Image.fromarray(a))
    surfaces=[];froths=[];scenes=[];water=[]
    for k in range(N):
        a,b=frame(k)
        save_png(a,OUT/'animation/mer'/f'BeachV1_mer_{k:02d}.png')
        save_png(b,OUT/'animation/ecume'/f'BeachV1_ecume_{k:02d}.png')
        s=Image.fromarray(a);s.alpha_composite(Image.fromarray(b));water.append(s.copy())
        s.alpha_composite(fixed);scenes.append(s)
        surfaces.append(Image.fromarray(a));froths.append(Image.fromarray(b))
    assert np.array_equal(np.array(scenes[0]),reference)
    for k,s in enumerate(scenes):assert np.array_equal(np.array(s)[~sea],reference[~sea]),k
    assert all(np.array_equal(x,y) for x,y in zip(frame(0),frame(N)))
    scenes[0].save(OUT/'BeachV1_plage_animee.webp',save_all=True,append_images=scenes[1:],duration=MS,loop=0,lossless=True,method=4)
    water[0].save(OUT/'BeachV1_eau_transparente.webp',save_all=True,append_images=water[1:],duration=MS,loop=0,lossless=True,method=4)
    # The provided reference is a 256-colour image; reuse that very palette for review GIFs.
    pal=Image.open(SRC).convert('P')
    gs=[s.convert('RGB').quantize(palette=pal,dither=Image.Dither.NONE) for s in scenes]
    gs[0].save(OUT/'BeachV1_plage_animee.gif',save_all=True,append_images=gs[1:],duration=MS,loop=0,optimize=False,disposal=1)
    write_ora(layers,reference)
    # Optional PNG-to-Tileset route: transparent padding, NEVER rescale the art.
    pw,ph=math.ceil(w/8)*8,math.ceil(h/8)*8
    for path in list((OUT/'calques').glob('*.png'))+list((OUT/'animation').rglob('*.png')):
        im=Image.open(path).convert('RGBA');pad=Image.new('RGBA',(pw,ph));pad.paste(im,(0,0))
        dest=OUT/'import_8px'/path.relative_to(OUT);dest.parent.mkdir(parents=True,exist_ok=True)
        pad.save(dest.with_name(path.stem+'_PAD8.png'),optimize=True)
    m={'source':{'file':str(SRC.relative_to(ROOT)),'sha256':sha(SRC),'size':[w,h]},
       'wave_reference':{'file':str(WAVE_REF.relative_to(ROOT)),'sha256':sha(WAVE_REF),'credit':'Beach & Path to Beach, rip redblueyellow; PMD / Nintendo / Creatures / GAME FREAK / Chunsoft',
                         'sample_rectangles':[[865,y,1180,y+47] for y in WAVE_ROWS], 'crest_height_px':heights.tolist(),
                         'usage':'Crest-height progression guides a new integer-coordinate displacement. No sheet pixels substituted into the supplied map; official cadence unknown.'},
       'layers':[{'id':i,'name':n,'file':f'calques/BeachV1_{i}.png','origin':[0,0]} for i,n,a in layers],
       'animation':{'frames':N,'duration_ms':MS,'cycle_ms':N*MS,'ticks_at_60hz':3,'water':'animation/mer/BeachV1_mer_{frame:02d}.png','foam':'animation/ecume/BeachV1_ecume_{frame:02d}.png','phase_zero_exact':True,'official_cycle':False,'method':'Beach-reference-guided surf oscillation; local swell; integer nearest-neighbour remapping of input colours; fixed water footprint.'},
       'import':{'native_size':[w,h],'padded_size':[pw,ph],'offset':[0,0],'tile_size':8,'padding':'Right and bottom transparent; no resampling','runtime':'NOT TESTED'},
       'limits':['Visible-surface partitions, not recovered native layers or complete movable objects.','Hidden water below foam is completed from nearest visible water samples.','Original fixed shoreline: water never invades sand or rocks.','New adapted motion, not an extracted official Sky cycle.','No collisions, Ground, warps or engine validation.']}
    (OUT/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
    prefix='renders/beach_layers_v1/'
    data={'width':w,'height':h,'ms':MS,'layers':[{'id':i,'name':n,'uri':prefix+'calques/BeachV1_'+i+'.png'} for i,n,a in layers],
          'surface':[prefix+f'animation/mer/BeachV1_mer_{k:02d}.png' for k in range(N)],
          'foam':[prefix+f'animation/ecume/BeachV1_ecume_{k:02d}.png' for k in range(N)],
          'reference':prefix+'BeachV1_reference_recomposee.png'}
    template=(Path(__file__).parent/'viewer.html').read_text()
    page=template.replace('__BEACH_DATA__',json.dumps(data,ensure_ascii=False))
    (ROOT/'apercu_beach_calques_v1.html').write_text(page)
    # Repo viewer reuses PNGs; package.py embeds images in the portable viewer.
    (OUT/'index.html').write_text('<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=../../apercu_beach_calques_v1.html"><title>Beach · ouvrir l’atelier</title></head><body><p><a href="../../apercu_beach_calques_v1.html">Ouvrir l’atelier Beach V1</a></p></body></html>\n')
    print(f'Built {len(layers)} layers, {N} water + {N} foam frames, native {w}×{h}, import {pw}×{ph}.')

if __name__=='__main__':main()
