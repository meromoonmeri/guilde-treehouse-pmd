"""Exports « multicalques comme la guilde » pour la zone Crooked verdoyante V2 (calques générés sur magenta).

Conventions reprises de sprites/zones_guidees/README_multicalques.md : calques nommés et ordonnés, canevas commun
(512×640, origine 0,0), PNG RGBA transparents, fichiers Aseprite éditables (1 frame), grille 8 px, cartes Tiled
(.tmj base64/zlib) avec un atlas 8 px dédié construit à partir des calques, contrôle par recomposition.
Jour et nuit (nuit = filtre Abyss exact déjà appliqué dans renders/.../nuit/).

L'atlas 8 px est fabriqué à partir des pixels GÉNÉRÉS de cette zone : il n'est pas un atlas canonique.

Reproduction : .venv/bin/python source/crooked_verdoyant_v2_magenta/multicalques.py
"""
from __future__ import annotations
import base64, hashlib, json, struct, zlib, shutil
from pathlib import Path
import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[2]
REN = R / 'renders/crooked_verdoyant_v2_magenta'
OUT = R / 'exports/crooked_verdoyant_v2_magenta/multicalques'
PFX = 'CrookedMagentaV2'
W, H, T = 512, 640, 8
NAMES = {'01_sol_herbe': 'Sol : herbe pure (généré)', '02_lisiere_foret': 'Lisière de forêt (généré, magenta)',
         '03_chemin': 'Chemin de terre (généré, magenta)', '04_parois_crooked': 'Parois Crooked (généré, magenta)',
         '05_entree_grotte': 'Entrée : ouverture + sol du débouché (généré)', '06_rochers': 'Rochers et cailloux (généré, magenta)',
         '07_vegetation_basse': 'Végétation basse (feuille magenta)', '08_troncs_ombres': 'Troncs + ombres au sol (généré, magenta)',
         '09_canopees': 'Canopées, au-dessus du joueur (généré, magenta)'}
ORDER = json.loads((REN / 'manifest.json').read_text())['layers_order_bottom_to_top']
LAYERS = [(lid, NAMES.get(lid, lid)) for lid in ORDER]


def chunk(kind, data):
    return struct.pack('<IH', len(data) + 6, kind) + data


def astr(s):
    b = s.encode(); return struct.pack('<H', len(b)) + b


def aseprite(path: Path, images: list, names: list, duration_ms: int = 100):
    """Fichier .aseprite RGBA, 1 frame, un calque par image (même structure que source/build_zones_multicalques.py)."""
    chunks = []
    for name in names:
        chunks.append(chunk(0x2004, struct.pack('<HHHHHHB', 3, 0, 0, 0, 0, 0, 255) + b'\0' * 3 + astr(name)))
    for i, im in enumerate(images):
        box = im.getbbox(); x, y = (box[:2] if box else (0, 0))
        q = im.crop(box) if box else Image.new('RGBA', (1, 1))
        cel = struct.pack('<HhhBHh', i, x, y, 255, 2, 0) + b'\0' * 5 + struct.pack('<HH', q.width, q.height) + zlib.compress(q.tobytes(), 9)
        chunks.append(chunk(0x2005, cel))
    data = b''.join(chunks)
    frame = struct.pack('<IHHH2sI', len(data) + 16, 0xF1FA, len(chunks), duration_ms, b'\0\0', len(chunks)) + data
    header = bytearray(128)
    struct.pack_into('<IHHHHHIH', header, 0, len(frame) + 128, 0xA5E0, 1, W, H, 32, 1, duration_ms)
    struct.pack_into('<HBBhhHH', header, 32, 0, 1, 1, 0, 0, T, T)
    path.write_bytes(header + frame)


class Atlas:
    def __init__(self):
        self.tiles = []; self.index = {}

    def gid(self, cell: Image.Image) -> int:
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


def build_variant(tag: str, src_dir: Path, suffix: str, manifest: dict):
    images = []
    files = {}
    for lid, _ in LAYERS:
        p = src_dir / f'{PFX}_{lid}{suffix}.png'
        im = Image.open(p).convert('RGBA'); assert im.size == (W, H)
        dst = OUT / f'{PFX}_{lid}{suffix}.png'
        if p.resolve() != dst.resolve():
            shutil.copyfile(p, dst)
        images.append(im); files[lid] = dst.name
    comp = Image.new('RGBA', (W, H))
    for im in images:
        comp.alpha_composite(im)
    ref = Image.open(REN / ('composition_jour.png' if tag == 'jour' else 'composition_nuit.png')).convert('RGBA')
    assert comp.tobytes() == ref.tobytes(), f'recomposition {tag} ≠ composition de référence'
    aseprite(OUT / f'{PFX}_{tag}.aseprite', images, [n for _, n in LAYERS])
    atlas = Atlas(); arrays = []
    for im in images:
        arr = []
        for ty in range(H // T):
            for tx in range(W // T):
                arr.append(atlas.gid(im.crop((tx * T, ty * T, tx * T + T, ty * T + T))))
        arrays.append(arr)
    aname = f'{PFX}_{tag}_8px'
    aimg = atlas.image(); aimg.save(OUT / f'{aname}.png')
    tsj = {'columns': 64, 'image': f'{aname}.png', 'imageheight': aimg.height, 'imagewidth': aimg.width, 'margin': 0, 'name': aname,
           'spacing': 0, 'tilecount': len(atlas.tiles), 'tiledversion': '1.10.2', 'tileheight': T, 'tilewidth': T, 'type': 'tileset', 'version': '1.10',
           'properties': [{'name': 'provenance', 'type': 'string', 'value': 'tuiles 8 px découpées dans des calques GÉNÉRÉS (références PMD) — pas un atlas canonique'}]}
    (OUT / f'{aname}.tsj').write_text(json.dumps(tsj, ensure_ascii=False, indent=1))
    tm = {'compressionlevel': -1, 'height': H // T, 'width': W // T, 'infinite': False, 'orientation': 'orthogonal', 'renderorder': 'right-down',
          'tiledversion': '1.10.2', 'tileheight': T, 'tilewidth': T, 'type': 'map', 'version': '1.10', 'nextobjectid': 1, 'nextlayerid': len(LAYERS) + 1,
          'tilesets': [{'firstgid': 1, 'source': f'{aname}.tsj'}], 'layers': []}
    for i, ((lid, name), arr) in enumerate(zip(LAYERS, arrays)):
        data = base64.b64encode(zlib.compress(struct.pack('<' + 'I' * len(arr), *arr), 9)).decode()
        tm['layers'].append({'id': i + 1, 'name': name, 'type': 'tilelayer', 'width': W // T, 'height': H // T, 'x': 0, 'y': 0, 'opacity': 1,
                             'visible': True, 'encoding': 'base64', 'compression': 'zlib', 'data': data})
    (OUT / f'{PFX}_{tag}.tmj').write_text(json.dumps(tm, ensure_ascii=False, indent=1))
    comp.save(OUT / f'{PFX}_composition_{tag}.png')
    manifest['variants'][tag] = {
        'files': files, 'aseprite': f'{PFX}_{tag}.aseprite', 'tiled': f'{PFX}_{tag}.tmj', 'atlas': [f'{aname}.png', f'{aname}.tsj'],
        'atlas_tiles': len(atlas.tiles), 'composition': f'{PFX}_composition_{tag}.png',
        'sha256': {fn: hashlib.sha256((OUT / fn).read_bytes()).hexdigest() for fn in list(files.values()) + [f'{PFX}_composition_{tag}.png']},
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {'zone': 'Crooked Cavern verdoyante V2 — calques générés sur fond magenta', 'dimensions': [W, H], 'grid': T,
                'layers': [{'id': lid, 'name': name} for lid, name in LAYERS],
                'convention': 'sprites/zones_guidees/README_multicalques.md (PNG alignés + Aseprite + Tiled + recomposition)',
                'provenance': 'pixels GÉNÉRÉS d’après références PMD (audit source/crooked_verdoyant_v1/AUDIT.md) ; non natifs ; atlas 8 px dérivé de ces calques',
                'night': 'filtre Abyss exact (source/cote_v4_abyss/night.py) appliqué calque par calque', 'variants': {}}
    build_variant('jour', REN / 'calques', '', manifest)
    build_variant('nuit', REN / 'nuit', '_nuit', manifest)
    (OUT / 'multicalques.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print('OK multicalques :', {k: v['atlas_tiles'] for k, v in manifest['variants'].items()}, 'tuiles atlas')


if __name__ == '__main__':
    main()
