"""Quatre cartes forêt 928×1152 : entrée en lisière, fond de forêt, caverne verdoyante.
Scènes générées d’après PMD (Relic Forest / Vast Steppe / Crooked). Calques extraits,
nuit Abyss, exports multicalques (PNG + Aseprite + Tiled). Pixels générés ≠ natifs.
"""
from __future__ import annotations
import hashlib, io, json, struct, sys, zipfile, zlib, base64, shutil
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
import scipy.ndimage as nd
from PIL import Image

R = Path(__file__).resolve().parents[2]
BR = R / 'renders/forets_lisiere_v2/bruts'
OUT = R / 'renders/forets_lisiere_v2'
EXP = R / 'exports/forets_lisiere_v2'
sys.path.insert(0, str(R / 'source/cote_v4_abyss'))
from night import night  # noqa: E402

W, H, T = 928, 1152, 8
MAPS = [
    {'id': 'E_foret_entree_est', 'title': 'Forêt — entrée de donjon dans la lisière est',
     'scene': 'E_foret_entree_est.png', 'arrival': 'sud', 'objective': 'grotte est (lisière)'},
    {'id': 'F_couloir_foret_ne', 'title': 'Couloir de forêt — grotte dans la lisière nord-est',
     'scene': 'F_couloir_foret_ne.png', 'arrival': 'sud', 'objective': 'grotte NE'},
    {'id': 'G_caverne_mousse', 'title': 'Caverne moussue — ouverture sud vers la forêt',
     'scene': 'G_caverne_mousse.png', 'arrival': 'sud (lisière)', 'objective': 'tunnel nord'},
    {'id': 'H_clairiere_secrete', 'title': 'Clairière secrète — fond de forêt, petite grotte nord',
     'scene': 'H_clairiere_secrete.png', 'arrival': 'sud', 'objective': 'trou de grotte dans la lisière nord'},
]
ORDER = ['01_sol_herbe', '02_lisiere_foret', '03_chemin', '04_parois_roche', '05_entree_grotte',
         '06_rochers', '07_vegetation_basse', '08_troncs_ombres', '09_canopees']
NAMES = {
    '01_sol_herbe': 'Sol : herbe (généré)', '02_lisiere_foret': 'Lisière de forêt (généré)',
    '03_chemin': 'Chemin de terre (généré)', '04_parois_roche': 'Parois roche / Crooked (généré)',
    '05_entree_grotte': 'Entrée grotte (généré)', '06_rochers': 'Rochers (généré)',
    '07_vegetation_basse': 'Végétation basse (généré)', '08_troncs_ombres': 'Troncs + ombres (généré)',
    '09_canopees': 'Canopées (généré)',
}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def canvas(im: Image.Image) -> Image.Image:
    im = im.convert('RGBA')
    if im.size == (W, H):
        return im
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    src = im
    if src.height > H:
        y0 = (src.height - H) // 2
        src = src.crop((0, y0, src.width, y0 + H))
    if src.width > W:
        x0 = (src.width - W) // 2
        src = src.crop((x0, 0, x0 + W, src.height))
    x = (W - src.width) // 2
    y = (H - src.height) // 2
    out.paste(src, (x, y))
    return out


def key_magenta(im: Image.Image) -> Image.Image:
    a = np.array(canvas(im))
    r, g, b = a[:, :, 0].astype(int), a[:, :, 1].astype(int), a[:, :, 2].astype(int)
    bg = (r > 150) & (b > 150) & (g < 100)
    fringe = nd.binary_dilation(bg, iterations=3) & ~bg & (b > g + 10)
    a[bg | fringe] = 0
    return Image.fromarray(a)


def part(rgb: np.ndarray, m: np.ndarray) -> Image.Image:
    a = np.zeros((H, W, 4), np.uint8)
    a[m, :3] = rgb[m]
    a[m, 3] = 255
    return Image.fromarray(a)


def grass_fill(rgb: np.ndarray, keep: np.ndarray, seed=3) -> Image.Image:
    """Sous-couche opaque : tuile 16 px d’herbe prélevée dans keep."""
    rng = np.random.default_rng(seed)
    C = 16
    cells = [(y, x) for y in range(0, H, C) for x in range(0, W, C)
             if keep[y:y + C, x:x + C].mean() > 0.7]
    if not cells:
        cells = [(H // 2, W // 2)]
    a = np.zeros((H, W, 4), np.uint8)
    a[:, :, 3] = 255
    for y in range(0, H, C):
        for x in range(0, W, C):
            sy, sx = cells[int(rng.integers(len(cells)))]
            hh, ww = min(C, H - y), min(C, W - x)
            a[y:y + hh, x:x + ww, :3] = rgb[sy:sy + hh, sx:sx + ww]
    return Image.fromarray(a)


def split_scene(rgb: np.ndarray, kind: str):
    r, g, b = rgb[:, :, 0].astype(int), rgb[:, :, 1].astype(int), rgb[:, :, 2].astype(int)
    mx = np.maximum(np.maximum(r, g), b)
    green = (g > r + 6) & (g > b + 6)
    dark_f = green & (g < 130) & (r < 90)
    bright = green & (g > 150)
    dirt = (r > g + 8) & (r > 140) & (g > 80) & (b < 180) & ~green
    ochre = (r > 90) & (g > 40) & (b < r - 20) & (g < r) & ~green & (mx > 50)
    cave = (mx < 48) & ochre.astype(bool)
    # refine cave: dark pixels near ochre
    dark = mx < 55
    cave = nd.binary_dilation(nd.binary_erosion(dark, iterations=1), iterations=2)
    cave &= ~green
    if kind == 'H_clairiere_secrete':
        ochre = ochre & dirt
    if kind == 'G_caverne_mousse':
        dark_f = green & (g < 140)
        ochre = (~green) & (mx > 40)
        cave = dark & ~green
        cave = nd.binary_opening(cave, iterations=1)
    lisiere = nd.binary_closing(dark_f, iterations=2)
    canopee = nd.binary_closing(bright, iterations=1) & ~lisiere
    path = nd.binary_closing(dirt & ~ochre, iterations=2) if kind != 'G_caverne_mousse' else nd.binary_closing(dirt, iterations=2)
    if kind == 'G_caverne_mousse':
        path = nd.binary_closing((r > 150) & (g > 100) & (b < 100) & ~green, iterations=2)
    walls = nd.binary_closing(ochre & ~path, iterations=2)
    if kind != 'G_caverne_mousse':
        walls = walls & ~lisiere
    ent = nd.binary_fill_holes(cave) & ~path
    # rocks: small ochre components not walls
    rock_m = ochre & ~walls & ~path & ~ent
    lab, n = nd.label(rock_m)
    rocks = np.zeros_like(rock_m)
    for i in range(1, n + 1):
        c = lab == i
        if 80 < c.sum() < 8000:
            rocks |= c
    veg = green & ~lisiere & ~canopee
    veg = veg & ~nd.binary_dilation(path, iterations=2)
    # trunks: brown under canopies
    brown = (r > g + 4) & (g > b) & (r < 160) & ~green
    troncs = nd.binary_dilation(canopee, iterations=6) & brown
    grass_src = green & ~lisiere & ~canopee
    if grass_src.mean() < 0.05:
        grass_src = ~(walls | lisiere | ent) | green
    sol = grass_fill(rgb, grass_src | (~(lisiere | walls | ent) & green), seed=hash(kind) % 99)
    layers = {
        '01_sol_herbe': sol,
        '02_lisiere_foret': part(rgb, lisiere),
        '03_chemin': part(rgb, path),
        '04_parois_roche': part(rgb, walls & ~ent),
        '05_entree_grotte': part(rgb, ent),
        '06_rochers': part(rgb, rocks),
        '07_vegetation_basse': part(rgb, veg),
        '08_troncs_ombres': part(rgb, troncs),
        '09_canopees': part(rgb, canopee),
    }
    return layers


def ora(path: Path, layers: dict, name: str):
    root = ET.Element('image', w=str(W), h=str(H), name=name)
    stack = ET.SubElement(root, 'stack')
    comp = Image.new('RGBA', (W, H))
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', 'image/openraster', compress_type=zipfile.ZIP_STORED)
        items = list(layers.items())
        for i, (n, im) in reversed(list(enumerate(items))):
            fn = f'data/layer{i:02}.png'
            ET.SubElement(stack, 'layer', name=n, src=fn, x='0', y='0', opacity='1.0',
                          visibility='visible', **{'composite-op': 'svg:src-over'})
            bio = io.BytesIO(); im.save(bio, format='PNG'); z.writestr(fn, bio.getvalue())
        for im in layers.values():
            comp.alpha_composite(im)
        bio = io.BytesIO(); comp.save(bio, format='PNG'); z.writestr('mergedimage.png', bio.getvalue())
        z.writestr('stack.xml', ET.tostring(root, encoding='utf-8', xml_declaration=True))


def chunk(kind, data):
    return struct.pack('<IH', len(data) + 6, kind) + data


def astr(s):
    b = s.encode(); return struct.pack('<H', len(b)) + b


def aseprite(path: Path, images, names):
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
    struct.pack_into('<IHHHHHIH', header, 0, len(frame) + 128, 0xA5E0, 1, W, H, 32, 1, 100)
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


def export_mc(mid: str, layers: dict, tag: str, images: list):
    out = EXP / mid / 'multicalques'
    out.mkdir(parents=True, exist_ok=True)
    suffix = '' if tag == 'jour' else '_nuit'
    files = {}
    for lid, im in zip(ORDER, images):
        fn = f'{lid}{suffix}.png'
        im.save(out / fn); files[lid] = fn
    comp = Image.new('RGBA', (W, H))
    for im in images:
        comp.alpha_composite(im)
    aseprite(out / f'{mid}_{tag}.aseprite', images, [NAMES[i] for i in ORDER])
    atlas = Atlas(); arrays = []
    for im in images:
        arr = []
        for ty in range(H // T):
            for tx in range(W // T):
                arr.append(atlas.gid(im.crop((tx * T, ty * T, tx * T + T, ty * T + T))))
        arrays.append(arr)
    aname = f'{mid}_{tag}_8px'
    aimg = atlas.image(); aimg.save(out / f'{aname}.png')
    tsj = {'columns': 64, 'image': f'{aname}.png', 'imageheight': aimg.height, 'imagewidth': aimg.width,
           'margin': 0, 'name': aname, 'spacing': 0, 'tilecount': len(atlas.tiles), 'tiledversion': '1.10.2',
           'tileheight': T, 'tilewidth': T, 'type': 'tileset', 'version': '1.10',
           'properties': [{'name': 'provenance', 'type': 'string',
                           'value': 'tuiles 8 px de calques GÉNÉRÉS — pas un atlas canonique'}]}
    (out / f'{aname}.tsj').write_text(json.dumps(tsj, ensure_ascii=False, indent=1))
    tm = {'compressionlevel': -1, 'height': H // T, 'width': W // T, 'infinite': False,
          'orientation': 'orthogonal', 'renderorder': 'right-down', 'tiledversion': '1.10.2',
          'tileheight': T, 'tilewidth': T, 'type': 'map', 'version': '1.10', 'nextobjectid': 1,
          'nextlayerid': len(ORDER) + 1, 'tilesets': [{'firstgid': 1, 'source': f'{aname}.tsj'}], 'layers': []}
    for i, (lid, arr) in enumerate(zip(ORDER, arrays)):
        data = base64.b64encode(zlib.compress(struct.pack('<' + 'I' * len(arr), *arr), 9)).decode()
        tm['layers'].append({'id': i + 1, 'name': NAMES[lid], 'type': 'tilelayer', 'width': W // T,
                             'height': H // T, 'x': 0, 'y': 0, 'opacity': 1, 'visible': True,
                             'encoding': 'base64', 'compression': 'zlib', 'data': data})
    (out / f'{mid}_{tag}.tmj').write_text(json.dumps(tm, ensure_ascii=False, indent=1))
    comp.save(out / f'{mid}_composition_{tag}.png')
    return {'files': files, 'atlas_tiles': len(atlas.tiles), 'aseprite': f'{mid}_{tag}.aseprite',
            'tiled': f'{mid}_{tag}.tmj'}


def overlay_magenta(layers, path, dest_key):
    if not path.exists():
        return
    extra = key_magenta(Image.open(path))
    base = layers[dest_key]
    c = Image.new('RGBA', (W, H)); c.alpha_composite(base); c.alpha_composite(extra)
    layers[dest_key] = c


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    gallery_maps = []
    index = []
    for spec in MAPS:
        mid = spec['id']
        dest = OUT / mid
        for d in ('calques', 'masques', 'nuit'):
            (dest / d).mkdir(parents=True, exist_ok=True)
        scene = canvas(Image.open(BR / spec['scene']))
        rgb = np.array(scene.convert('RGB'))
        layers = split_scene(rgb, mid)
        if mid == 'E_foret_entree_est':
            overlay_magenta(layers, BR / 'E_calque_entree_est.png', '05_entree_grotte')
        if mid == 'G_caverne_mousse':
            overlay_magenta(layers, BR / 'G_calque_parois.png', '04_parois_roche')
        # force opaque sol
        sa = np.array(layers['01_sol_herbe'])
        if sa[:, :, 3].min() < 255:
            sa[:, :, 3] = 255; layers['01_sol_herbe'] = Image.fromarray(sa)
        comp = Image.new('RGBA', (W, H))
        for n in ORDER:
            im = layers[n]
            im.save(dest / 'calques' / f'{n}.png')
            Image.fromarray(((np.array(im)[:, :, 3] > 0) * 255).astype('uint8')).save(dest / 'masques' / f'{n}.png')
            night(im).save(dest / 'nuit' / f'{n}_nuit.png')
            comp.alpha_composite(im)
        assert np.array(comp)[:, :, 3].min() == 255
        comp.save(dest / 'composition_jour.png')
        cn = Image.new('RGBA', (W, H))
        for n in ORDER:
            cn.alpha_composite(Image.open(dest / 'nuit' / f'{n}_nuit.png'))
        cn.save(dest / 'composition_nuit.png')
        ora(dest / f'{mid}.ora', layers, spec['title'])
        mc_j = export_mc(mid, layers, 'jour', [layers[n] for n in ORDER])
        mc_n = export_mc(mid, layers, 'nuit', [night(layers[n]) for n in ORDER])
        man = {
            'id': mid, 'title': spec['title'], 'size': [W, H], 'grid': 8,
            'layers_order_bottom_to_top': ORDER,
            'terrain_origin': 'PIXELS GÉNÉRÉS d’après références PMD (Relic Forest, Vast Steppe, Crooked Cavern). PAS natifs.',
            'arrival': spec['arrival'], 'objective': spec['objective'],
            'scene_sha256': sha(BR / spec['scene']),
            'multicalques': {'jour': mc_j, 'nuit': mc_n},
            'not_tested': 'PMDO, Aseprite/Tiled apps',
        }
        (dest / 'manifest.json').write_text(json.dumps(man, ensure_ascii=False, indent=2) + '\n')
        (EXP / mid / 'multicalques' / 'multicalques.json').write_text(json.dumps({
            'zone': spec['title'], 'dimensions': [W, H], 'grid': T,
            'layers': [{'id': i, 'name': NAMES[i]} for i in ORDER],
            'provenance': man['terrain_origin'], 'variants': {'jour': mc_j, 'nuit': mc_n},
        }, ensure_ascii=False, indent=2) + '\n')
        gallery_maps.append({
            'id': mid, 'title': spec['title'],
            'layers': [{'id': n, 'jour': f'renders/forets_lisiere_v2/{mid}/calques/{n}.png',
                        'nuit': f'renders/forets_lisiere_v2/{mid}/nuit/{n}_nuit.png'} for n in ORDER],
        })
        index.append(mid)
        print('OK', mid)
    (OUT / 'index.json').write_text(json.dumps({'maps': index, 'size': [W, H]}, indent=2) + '\n')
    html = Path(__file__).with_name('gallery.html').read_text().replace('__DATA__', json.dumps(gallery_maps, ensure_ascii=False))
    (R / 'apercu_forets_lisiere_v2.html').write_text(html)
    # planche 0.25x
    board = Image.new('RGB', (W * 2 + 16, H * 2 + 16), (20, 24, 22))
    for i, spec in enumerate(MAPS):
        im = Image.open(OUT / spec['id'] / 'composition_jour.png').convert('RGB')
        board.paste(im, ((i % 2) * (W + 8), (i // 2) * (H + 8)))
        board.resize((board.width // 4, board.height // 4), Image.NEAREST).save(OUT / 'planche_E-H_0.25x.png')
    print('4 maps')


if __name__ == '__main__':
    build()
