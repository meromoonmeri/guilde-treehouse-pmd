"""Cartes Halcyon NATIVES : modules complets (translation), pas de mosaïque 8 px.

- N1 / N2 : layouts 928×1152 assemblés (herbe Vast Steppe 48×48, chemin Relic en bande complète,
  entrée Crooked 320×240 entière, arbres 144×120, rochers Objects+Shadows, fleurs 24×24).
- N3 : Altere Pond 928×768, calques natifs L00–L07.
- N4 : Relic Forest 600×600, scène native complète.
- N5 : Vast Steppe entrance 512×512, calques natifs.

Nuit = Abyss exact. Multicalques PNG + Aseprite + Tiled.
"""
from __future__ import annotations
import hashlib, io, json, struct, sys, zipfile, zlib, base64
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[2]
O = R / 'renders/halcyon_natif_v1'
EXP = R / 'exports/halcyon_natif_v1'
B = R / 'banque_canonique'
sys.path.insert(0, str(R / 'source/cote_v4_abyss'))
from night import night  # noqa: E402

T = 8


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load(p):
    return Image.open(p).convert('RGBA')


def tile_patch(patch: Image.Image, w: int, h: int) -> Image.Image:
    a = np.array(patch)
    ph, pw = a.shape[:2]
    out = np.tile(a, (h // ph + 2, w // pw + 2, 1))[:h, :w]
    if out.shape[2] == 3:
        rgba = np.zeros((h, w, 4), np.uint8); rgba[:, :, :3] = out; rgba[:, :, 3] = 255
        return Image.fromarray(rgba)
    out[:, :, 3] = 255
    return Image.fromarray(out)


def stamp(canvas, spr, xy, placements, module, layer):
    canvas.alpha_composite(spr, xy)
    placements.append({'module': module, 'layer': layer, 'xy': list(xy), 'size': [spr.width, spr.height]})


def chunk(kind, data):
    return struct.pack('<IH', len(data) + 6, kind) + data


def astr(s):
    b = s.encode(); return struct.pack('<H', len(b)) + b


def aseprite(path, images, names, w, h):
    chunks = []
    for name in names:
        chunks.append(chunk(0x2004, struct.pack('<HHHHHHB', 3, 0, 0, 0, 0, 0, 255) + b'\0' * 3 + astr(name)))
    for i, im in enumerate(images):
        box = im.getbbox(); x, y = (box[:2] if box else (0, 0))
        q = im.crop(box) if box else Image.new('RGBA', (1, 1))
        cel = struct.pack('<HhhBHh', i, x, y, 255, 2, 0) + b'\0' * 5 + struct.pack('<HH', q.width, q.height) + zlib.compress(q.tobytes(), 9)
        chunks.append(chunk(0x2005, cel))
    data = b''.join(chunks)
    frame = struct.pack('<IHHH2sI', len(data) + 16, 0xF1FA, len(chunks), 100, b'\0\0', len(chunks)) + data
    header = bytearray(128)
    struct.pack_into('<IHHHHHIH', header, 0, len(frame) + 128, 0xA5E0, 1, w, h, 32, 1, 100)
    struct.pack_into('<HBBhhHH', header, 32, 0, 1, 1, 0, 0, T, T)
    path.write_bytes(header + frame)


class Atlas:
    def __init__(self):
        self.tiles = []; self.index = {}

    def gid(self, cell):
        b = cell.tobytes()
        if not any(b[3::4]):
            return 0
        if b not in self.index:
            self.index[b] = len(self.tiles) + 1; self.tiles.append(cell)
        return self.index[b]

    def image(self, columns=64):
        rows = max(1, -(-len(self.tiles) // columns))
        im = Image.new('RGBA', (columns * T, rows * T))
        for i, t in enumerate(self.tiles):
            im.paste(t, (i % columns * T, i // columns * T))
        return im


def export_mc(mid, layers, names, w, h, tag, images):
    out = EXP / mid / 'multicalques'
    out.mkdir(parents=True, exist_ok=True)
    suf = '' if tag == 'jour' else '_nuit'
    files = {}
    for lid, im in zip(layers, images):
        fn = f'{lid}{suf}.png'
        im.save(out / fn); files[lid] = fn
    aseprite(out / f'{mid}_{tag}.aseprite', images, names, w, h)
    atlas = Atlas(); arrays = []
    for im in images:
        arr = []
        for ty in range(h // T):
            for tx in range(w // T):
                arr.append(atlas.gid(im.crop((tx * T, ty * T, tx * T + T, ty * T + T))))
        arrays.append(arr)
    aname = f'{mid}_{tag}_8px'
    aimg = atlas.image(); aimg.save(out / f'{aname}.png')
    tsj = {'columns': 64, 'image': f'{aname}.png', 'imageheight': aimg.height, 'imagewidth': aimg.width,
           'margin': 0, 'name': aname, 'spacing': 0, 'tilecount': len(atlas.tiles), 'tiledversion': '1.10.2',
           'tileheight': T, 'tilewidth': T, 'type': 'tileset', 'version': '1.10',
           'properties': [{'name': 'provenance', 'type': 'string', 'value': 'tuiles 8 px découpées dans des calques NATIFS Halcyon (translation)'}]}
    (out / f'{aname}.tsj').write_text(json.dumps(tsj, ensure_ascii=False, indent=1))
    tm = {'compressionlevel': -1, 'height': h // T, 'width': w // T, 'infinite': False,
          'orientation': 'orthogonal', 'renderorder': 'right-down', 'tiledversion': '1.10.2',
          'tileheight': T, 'tilewidth': T, 'type': 'map', 'version': '1.10', 'nextobjectid': 1,
          'nextlayerid': len(layers) + 1, 'tilesets': [{'firstgid': 1, 'source': f'{aname}.tsj'}], 'layers': []}
    for i, (lid, name, arr) in enumerate(zip(layers, names, arrays)):
        data = base64.b64encode(zlib.compress(struct.pack('<' + 'I' * len(arr), *arr), 9)).decode()
        tm['layers'].append({'id': i + 1, 'name': name, 'type': 'tilelayer', 'width': w // T, 'height': h // T,
                             'x': 0, 'y': 0, 'opacity': 1, 'visible': True, 'encoding': 'base64',
                             'compression': 'zlib', 'data': data})
    (out / f'{mid}_{tag}.tmj').write_text(json.dumps(tm, ensure_ascii=False, indent=1))
    comp = Image.new('RGBA', (w, h))
    for im in images:
        comp.alpha_composite(im)
    comp.save(out / f'{mid}_composition_{tag}.png')
    return {'atlas_tiles': len(atlas.tiles), 'files': files}


def ora(path, layers, name, w, h):
    root = ET.Element('image', w=str(w), h=str(h), name=name)
    stack = ET.SubElement(root, 'stack')
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', 'image/openraster', compress_type=zipfile.ZIP_STORED)
        items = list(layers.items())
        for i, (n, im) in reversed(list(enumerate(items))):
            fn = f'data/{i:02}.png'
            ET.SubElement(stack, 'layer', name=n, src=fn, x='0', y='0', opacity='1.0',
                          visibility='visible', **{'composite-op': 'svg:src-over'})
            b = io.BytesIO(); im.save(b, format='PNG'); z.writestr(fn, b.getvalue())
        z.writestr('stack.xml', ET.tostring(root, encoding='utf-8', xml_declaration=True))


def write_map(mid, title, layers_dict, names, w, h, provenance, placements):
    dest = O / mid
    for d in ('calques', 'nuit', 'masques'):
        (dest / d).mkdir(parents=True, exist_ok=True)
    order = list(layers_dict)
    images = [layers_dict[k] for k in order]
    nms = [names[k] for k in order]
    comp = Image.new('RGBA', (w, h))
    for k, im in zip(order, images):
        im.save(dest / 'calques' / f'{k}.png')
        Image.fromarray(((np.array(im)[:, :, 3] > 0) * 255).astype('uint8')).save(dest / 'masques' / f'{k}.png')
        night(im).save(dest / 'nuit' / f'{k}_nuit.png')
        comp.alpha_composite(im)
    assert np.array(comp)[:, :, 3].min() == 255, mid
    comp.save(dest / 'composition_jour.png')
    cn = Image.new('RGBA', (w, h))
    for k in order:
        cn.alpha_composite(Image.open(dest / 'nuit' / f'{k}_nuit.png'))
    cn.save(dest / 'composition_nuit.png')
    ora(dest / f'{mid}.ora', layers_dict, title, w, h)
    mcj = export_mc(mid, order, nms, w, h, 'jour', images)
    mcn = export_mc(mid, order, nms, w, h, 'nuit', [night(im) for im in images])
    man = {
        'id': mid, 'title': title, 'size': [w, h],
        'terrain_origin': 'PIXELS NATIFS Halcyon — translation de modules complets (pas de mosaïque 8 px, pas de recolor/miroir/scale).',
        'layers_order_bottom_to_top': order,
        'placements': placements, 'provenance': provenance,
        'multicalques': {'jour': mcj, 'nuit': mcn},
        'not_tested': 'PMDO runtime, Aseprite/Tiled apps',
    }
    (dest / 'manifest.json').write_text(json.dumps(man, ensure_ascii=False, indent=2) + '\n')
    (EXP / mid / 'multicalques' / 'multicalques.json').write_text(json.dumps({
        'zone': title, 'dimensions': [w, h], 'grid': T,
        'layers': [{'id': i, 'name': names[i]} for i in order],
        'provenance': man['terrain_origin'], 'variants': {'jour': mcj, 'nuit': mcn},
    }, ensure_ascii=False, indent=2) + '\n')
    print('OK', mid, w, h)
    return {'id': mid, 'title': title, 'w': w, 'h': h,
            'layers': [{'id': n, 'jour': f'renders/halcyon_natif_v1/{mid}/calques/{n}.png',
                        'nuit': f'renders/halcyon_natif_v1/{mid}/nuit/{n}_nuit.png'} for n in order]}


def modules():
    m = {}
    grass = load(B / 'atlas/Vast_Steppe_Base.png').crop((240, 264, 288, 312))
    m['herbe_48'] = grass
    tree = load(R / 'source/zones_south_north_v3/references/native_tree_complete.png')
    m['arbre_steppe'] = tree
    atlas_f = load(B / 'atlas/Vast_Steppe_Flower_Animations.png')
    m['fleur'] = atlas_f.crop((0, 0, 24, 24))
    obj = load(B / 'atlas/Halcyon__Crooked_Cavern_Objects.png')
    shd = load(B / 'atlas/Halcyon__Crooked_Cavern_Shadows.png')
    for name, box in {
        'rocher_ouest': (53, 165, 133, 226),
        'rocher_est': (186, 157, 266, 240),
        'petit_rocher_a': (26, 217, 62, 240),
        'petit_rocher_b': (269, 218, 292, 236),
    }.items():
        im = Image.new('RGBA', (box[2] - box[0], box[3] - box[1]))
        im.alpha_composite(shd.crop(box)); im.alpha_composite(obj.crop(box))
        m[name] = im
    m['crooked_entree'] = load(B / 'cartes_natives/Halcyon__crooked_cavern_entrance.png')
    m['crooked_base'] = load(B / 'cartes_natives/Halcyon__crooked_cavern_entrance__L00_Base.png')
    m['crooked_obj'] = load(B / 'cartes_natives/Halcyon__crooked_cavern_entrance__L01_Objects.png')
    m['crooked_sh'] = load(B / 'cartes_natives/Halcyon__crooked_cavern_entrance__L02_Shadows.png')
    relic = load(B / 'atlas/Relic_Forest_Base.png')
    m['chemin_relic'] = relic.crop((272, 500, 328, 600))  # bande complète 56×100
    m['lisiere_relic_n'] = relic.crop((0, 0, 600, 96))
    m['lisiere_relic_w'] = relic.crop((0, 0, 64, 600))
    m['lisiere_relic_e'] = relic.crop((536, 0, 600, 600))
    m['relic_full'] = relic
    return m


def assemble_steppe(m, cave_xy, path_xs, tree_xy, rock_xy, flower_xy, w=928, h=1152):
    pl = []
    sol = tile_patch(m['herbe_48'], w, h)
    lisiere = Image.new('RGBA', (w, h))
    # lisière Relic : bandes complètes, pas de tuile 8 px
    ln = m['lisiere_relic_n']
    for x in range(0, w, ln.width):
        stamp(lisiere, ln, (x, 0), pl, 'lisiere_relic_n', '02_lisiere')
    lw, le = m['lisiere_relic_w'], m['lisiere_relic_e']
    for y in range(96, h, lw.height):
        stamp(lisiere, lw, (0, y), pl, 'lisiere_relic_w', '02_lisiere')
        stamp(lisiere, le, (w - le.width, y), pl, 'lisiere_relic_e', '02_lisiere')
    chemin = Image.new('RGBA', (w, h))
    seg = m['chemin_relic']
    for y in range(path_xs[1], h, seg.height):
        stamp(chemin, seg, (path_xs[0], min(y, h - seg.height)), pl, 'chemin_relic_56x100', '03_chemin')
    parois = Image.new('RGBA', (w, h))
    entree = Image.new('RGBA', (w, h))
    stamp(parois, m['crooked_base'], cave_xy, pl, 'crooked_L00_Base', '04_parois')
    stamp(entree, m['crooked_obj'], cave_xy, pl, 'crooked_L01_Objects', '05_entree')
    ombres = Image.new('RGBA', (w, h))
    stamp(ombres, m['crooked_sh'], cave_xy, pl, 'crooked_L02_Shadows', '06_ombres_grotte')
    rochers = Image.new('RGBA', (w, h))
    for name, xy in rock_xy:
        stamp(rochers, m[name], xy, pl, name, '07_rochers')
    fleurs = Image.new('RGBA', (w, h))
    for xy in flower_xy:
        stamp(fleurs, m['fleur'], xy, pl, 'fleur_vast_pose0', '08_fleurs')
    arbres = Image.new('RGBA', (w, h))
    for xy in tree_xy:
        stamp(arbres, m['arbre_steppe'], xy, pl, 'arbre_steppe_144x120', '09_arbres')
    layers = {
        '01_sol_herbe_steppe': sol,
        '02_lisiere_relic': lisiere,
        '03_chemin_relic': chemin,
        '04_parois_crooked': parois,
        '05_objets_grotte': entree,
        '06_ombres_grotte': ombres,
        '07_rochers_crooked': rochers,
        '08_fleurs_steppe': fleurs,
        '09_arbres_steppe': arbres,
    }
    names = {k: k.replace('_', ' ') for k in layers}
    return layers, names, pl


def build():
    O.mkdir(parents=True, exist_ok=True)
    m = modules()
    gallery = []
    prov = {
        'herbe': 'Vast_Steppe_Base.png crop 240,264,288,312 (48×48) — même pastille que amp_plains_fleurie_v1',
        'arbre': 'native_tree_complete.png 144×120 (Vast Steppe Objects+Fringe)',
        'fleur': 'Vast_Steppe_Flower_Animations.png pose 0, 24×24',
        'rochers': 'Halcyon Crooked Objects+Shadows, bboxes v1',
        'grotte': 'Halcyon__crooked_cavern_entrance calques L00/L01/L02 320×240 complets',
        'chemin': 'Relic_Forest_Base crop 272,500,328,600 (bande 56×100 complète, répétée par translation)',
        'lisiere': 'Relic_Forest_Base bandes N 600×96, O/E 64×600',
    }
    # N1 grotte nord
    W, H = 928, 1152
    cx = (W - 320) // 2
    layers, names, pl = assemble_steppe(
        m, cave_xy=(cx, 24), path_xs=(436, 220),
        tree_xy=[(80, 380), (80, 620), (80, 860), (704, 400), (704, 640), (704, 880), (200, 980), (580, 980)],
        rock_xy=[('rocher_ouest', (300, 300)), ('rocher_est', (540, 310)), ('petit_rocher_a', (250, 500)), ('petit_rocher_b', (620, 720))],
        flower_xy=[(200, 800), (240, 840), (680, 820), (360, 900), (560, 940), (400, 700), (500, 760)],
    )
    gallery.append(write_map('N1_steppe_grotte_nord', 'Vast Steppe — grotte Crooked au nord (modules Halcyon)',
                             layers, names, W, H, prov, pl))
    # N2 grotte ouest
    layers, names, pl = assemble_steppe(
        m, cave_xy=(24, 200), path_xs=(80, 440),
        tree_xy=[(400, 360), (640, 400), (400, 640), (700, 700), (480, 900), (720, 960), (200, 980)],
        rock_xy=[('rocher_ouest', (360, 480)), ('rocher_est', (520, 500)), ('petit_rocher_a', (400, 800))],
        flower_xy=[(480, 780), (520, 820), (600, 860), (360, 920), (700, 740)],
    )
    gallery.append(write_map('N2_steppe_grotte_ouest', 'Vast Steppe — grotte Crooked à l’ouest (modules Halcyon)',
                             layers, names, W, H, prov, pl))
    # N3 Altere Pond native
    altere = [
        ('L00_Base', 'altere_pond__L00_Base.png'),
        ('L01_River', 'altere_pond__L01_River.png'),
        ('L02_Cliffs', 'altere_pond__L02_Cliffs.png'),
        ('L03_Shadows', 'altere_pond__L03_Shadows.png'),
        ('L04_Objects_Under', 'altere_pond__L04_Objects_Under.png'),
        ('L05_Objects', 'altere_pond__L05_Objects.png'),
        ('L06_Objects_Over', 'altere_pond__L06_Objects_Over.png'),
        ('L07_Fringe', 'altere_pond__L07_Fringe.png'),
    ]
    ld = {}
    for k, fn in altere:
        ld[k] = load(B / 'cartes_natives' / fn)
    names = {k: k for k in ld}
    gallery.append(write_map('N3_altere_pond', 'Altere Pond — calques Halcyon natifs 928×768',
                             ld, names, 928, 768,
                             {'scene': 'banque_canonique/cartes_natives/altere_pond__L*.png'}, []))
    # N4 Relic Forest
    ld = {'01_relic_forest_base': m['relic_full']}
    gallery.append(write_map('N4_relic_forest', 'Relic Forest — scène Halcyon native 600×600',
                             ld, {'01_relic_forest_base': 'Relic Forest Base'}, 600, 600,
                             {'scene': 'banque_canonique/atlas/Relic_Forest_Base.png'}, []))
    # N5 Vast Steppe entrance layers
    vs = [
        ('L00_Base', 'vast_steppe_entrance__L00_Base.png'),
        ('L01_Cliffs', 'vast_steppe_entrance__L01_Cliffs.png'),
        ('L02_Objects_Under', 'vast_steppe_entrance__L02_Objects_Under.png'),
        ('L03_Objects', 'vast_steppe_entrance__L03_Objects.png'),
        ('L04_Fringe', 'vast_steppe_entrance__L04_Fringe.png'),
    ]
    ld = {k: load(B / 'cartes_natives' / fn) for k, fn in vs}
    gallery.append(write_map('N5_vast_steppe_entrance', 'Vast Steppe entrance — calques Halcyon natifs 512×512',
                             ld, {k: k for k in ld}, 512, 512,
                             {'scene': 'banque_canonique/cartes_natives/vast_steppe_entrance__L*.png'}, []))
    (O / 'index.json').write_text(json.dumps({'maps': [g['id'] for g in gallery]}, indent=2) + '\n')
    html = Path(__file__).with_name('gallery.html').read_text().replace('__DATA__', json.dumps(gallery, ensure_ascii=False))
    (R / 'apercu_halcyon_natif_v1.html').write_text(html)
    # planche
    thumbs = []
    for g in gallery:
        im = load(O / g['id'] / 'composition_jour.png')
        thumbs.append(im.resize((im.width // 4, im.height // 4), Image.NEAREST))
    bw = sum(t.width for t in thumbs) + 8 * len(thumbs)
    bh = max(t.height for t in thumbs)
    board = Image.new('RGB', (bw, bh), (18, 22, 20))
    x = 0
    for t in thumbs:
        board.paste(t.convert('RGB'), (x, 0)); x += t.width + 8
    board.save(O / 'planche_5maps.png')


if __name__ == '__main__':
    build()
