#!/usr/bin/env python3
"""Assembleur Reverie Town v1 : cartes de village en tuiles natives Métano (kit falaises + sol + objets + eau).

Principe : chaque tuile 8x8 posée sur la carte est une tuile native copiée telle quelle depuis une feuille de
banque_canonique/atlas (jour) ; la nuit utilise la feuille *_Night native quand elle existe (Base, Cliffs),
sinon le filtre Abyss exact (source/cote_v4_abyss/night.py) appliqué une seule fois à la tuile.
La provenance de chaque tuile (feuille, tx, ty) est conservée pour le paquet natif et la vérification.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
ATLAS = ROOT / 'banque_canonique/atlas'
sys.path.insert(0, str(ROOT / 'source/cote_v4_abyss'))
from night import night as abyss_night  # noqa: E402

T = 8
NIGHT_SHEETS = {'Metano_Town_Base': 'Metano_Town_Base_Night',
                'Metano_Town_Cliffs': 'Metano_Town_Cliffs_Night',
                'Metano_Town_Fringe': 'Metano_Town_Fringe_Night'}
KIT = json.loads((HERE / 'kit/modules.json').read_text())['modules']
GRASS = json.loads((HERE / 'kit/herbe_cliffs.json').read_text())


class Sheets:
    def __init__(self):
        self.cache = {}

    def get(self, name):
        if name not in self.cache:
            self.cache[name] = Image.open(ATLAS / f'{name}.png').convert('RGBA')
        return self.cache[name]


SHEETS = Sheets()


class Layer:
    def __init__(self, name, w, h, phases=1):
        self.name, self.w, self.h, self.phases = name, w, h, phases
        self.day = [Image.new('RGBA', (w * T, h * T)) for _ in range(phases)]
        self.night = [Image.new('RGBA', (w * T, h * T)) for _ in range(phases)]
        self.refs = [{} for _ in range(phases)]  # (col,row) -> (sheet, tx, ty)
        self.night_custom = [{} for _ in range(phases)]  # (col,row) -> True si nuit = filtre Abyss (pas de feuille native)
        self.cut = [set() for _ in range(phases)]  # tuiles découpées (pixels étrangers à l'objet retirés)


class Scene:
    def __init__(self, slug, w, h):
        self.slug, self.w, self.h = slug, w, h
        self.layers = {}
        self.order = []

    def layer(self, name, phases=1):
        if name not in self.layers:
            self.layers[name] = Layer(name, self.w, self.h, phases)
            self.order.append(name)
        return self.layers[name]

    def blit(self, layer, sheet, tx, ty, w, h, col, row, phase=0, skip_empty=True, only_mask=None, pixel_mask=None):
        """Copie le rectangle de tuiles (tx,ty,w,h) de la feuille native vers la carte en (col,row)."""
        L = self.layer(layer)
        src = SHEETS.get(sheet)
        nsheet = NIGHT_SHEETS.get(sheet)
        nsrc = SHEETS.get(nsheet) if nsheet else None
        for dy in range(h):
            for dx in range(w):
                c, r = col + dx, row + dy
                if not (0 <= c < self.w and 0 <= r < self.h):
                    continue
                box = ((tx + dx) * T, (ty + dy) * T, (tx + dx + 1) * T, (ty + dy + 1) * T)
                tile = src.crop(box)
                cut = False
                if pixel_mask is not None:
                    pm = pixel_mask[dy * T:(dy + 1) * T, dx * T:(dx + 1) * T]
                    arr = np.array(tile)
                    if (arr[..., 3] > 0).sum() != (pm & (arr[..., 3] > 0)).sum():
                        arr[~pm] = 0
                        tile = Image.fromarray(arr)
                        cut = True
                if skip_empty and not tile.getchannel('A').getbbox():
                    continue
                if only_mask is not None and not only_mask[dy, dx]:
                    continue
                dst = (c * T, r * T)
                L.day[phase].paste(tile, dst)  # remplace (pas de fusion alpha) : une tuile = une tuile native
                if cut:
                    L.cut[phase].add((c, r))
                else:
                    L.cut[phase].discard((c, r))
                if nsrc is not None and not cut:
                    L.night[phase].paste(nsrc.crop(box), dst)
                    L.night_custom[phase].pop((c, r), None)
                else:
                    L.night[phase].paste(abyss_night(tile), dst)
                    L.night_custom[phase][(c, r)] = True
                L.refs[phase][(c, r)] = (sheet, tx + dx, ty + dy)

    def module(self, name, col, crown_row, layer='falaises'):
        """Pose un module du kit : crown_row = rangée de couronne du bloc sur la carte."""
        m = KIT[name]
        top = crown_row - (m['crown_rel'] or 0)
        self.blit(layer, 'Metano_Town_Cliffs', m['tx'], m['ty'], m['w'], m['h'], col, top)
        return col + m['w']

    def face(self, col, crown_row, n, source='face_c', start=0):
        """n colonnes de face plate (rangées crown_row..crown_row+11) prises dans un module de face."""
        m = KIT[source]
        for i in range(n):
            k = (start + i) % m['w']
            self.blit('falaises', 'Metano_Town_Cliffs', m['tx'] + k, m['ty'], 1, m['h'], col + i, crown_row)
        return col + n

    def grass_fill(self, layer, col0, row0, col1, row1, seed=1, sheet='Metano_Town_Cliffs'):
        """Herbe native : tirage déterministe pondéré par la fréquence native des tuiles d'herbe pures."""
        rng = np.random.default_rng(seed)
        weights = np.array([g['count'] for g in GRASS], dtype=float)
        weights /= weights.sum()
        for r in range(row0, row1):
            for c in range(col0, col1):
                g = GRASS[int(rng.choice(len(GRASS), p=weights))]
                self.blit(layer, sheet, g['tx'], g['ty'], 1, 1, c, r)

    def rim_west(self, col, row0, row1):
        """Bord ouest du plateau (liseré rocheux natif, tx 57) de row0 à row1-1 ; le bas (row1-1) est la rangée
        juste au-dessus du bord gauche du bloc (raccord natif rangées 24..26)."""
        seq = []
        # raccord natif juste au-dessus du bloc T0 : rangées 24,25,26 (y 192-215)
        tail = [24, 25, 26]
        body = [15, 16, 17, 18, 19, 20, 21, 22, 23]
        n = row1 - row0
        rows = []
        while len(rows) < n - len(tail):
            rows = body + rows
        rows = rows[len(rows) - (n - len(tail)):] + tail
        for i, ty in enumerate(rows):
            self.blit('falaises', 'Metano_Town_Cliffs', 57, ty, 1, 1, col, row0 + i)
        return seq

    # ---- exports -------------------------------------------------------------------------------------------
    def composite(self, mode='day', phase=0):
        out = Image.new('RGBA', (self.w * T, self.h * T), (0, 0, 0, 255))
        for name in self.order:
            L = self.layers[name]
            im = (L.day if mode == 'day' else L.night)[phase % L.phases]
            out.alpha_composite(im)
        return out

    def export(self, outdir, prefix):
        outdir.mkdir(parents=True, exist_ok=True)
        files = {}
        for i, name in enumerate(self.order):
            L = self.layers[name]
            for p in range(L.phases):
                suffix = f'_p{p + 1}' if L.phases > 1 else ''
                for mode, imgs in (('jour', L.day), ('nuit', L.night)):
                    fn = f'{prefix}_{i:02d}_{name}{suffix}_{mode}.png'
                    imgs[p].save(outdir / fn)
                    files.setdefault(name, []).append(fn)
        for mode in ('jour', 'nuit'):
            for p in range(4):
                self.composite('day' if mode == 'jour' else 'night', p).convert('RGB').save(outdir / f'{prefix}_composite_{mode}_p{p + 1}.png')
            self.composite('day' if mode == 'jour' else 'night', 0).convert('RGB').save(outdir / f'{prefix}_composite_{mode}.png')
        prov = {}
        for name in self.order:
            L = self.layers[name]
            prov[name] = [{f'{c},{r}': list(v) for (c, r), v in refs.items()} for refs in L.refs]
        (outdir / f'{prefix}_provenance.json').write_text(json.dumps(
            {'slug': self.slug, 'tile_px': T, 'size_tiles': [self.w, self.h], 'layers': self.order,
             'night_sheets': NIGHT_SHEETS, 'files': files, 'tiles': prov}))
        return files

    def verify(self):
        """Chaque tuile posée (jour) est identique à sa tuile source native ; nuit idem quand feuille native."""
        n = 0
        for name in self.order:
            L = self.layers[name]
            for p in range(L.phases):
                for (c, r), (sheet, tx, ty) in L.refs[p].items():
                    src = SHEETS.get(sheet).crop((tx * T, ty * T, tx * T + T, ty * T + T))
                    dst = L.day[p].crop((c * T, r * T, c * T + T, r * T + T))
                    if (c, r) in L.cut[p]:
                        a, b = np.array(src), np.array(dst)
                        keep = b[..., 3] > 0
                        assert np.array_equal(a[keep], b[keep]) and keep.any(), ('découpe', name, c, r)
                        continue
                    assert src.tobytes() == dst.tobytes(), (name, c, r, sheet, tx, ty)
                    if sheet in NIGHT_SHEETS:
                        nsrc = SHEETS.get(NIGHT_SHEETS[sheet]).crop((tx * T, ty * T, tx * T + T, ty * T + T))
                        ndst = L.night[p].crop((c * T, r * T, c * T + T, r * T + T))
                        assert nsrc.tobytes() == ndst.tobytes(), ('nuit', name, c, r)
                    n += 1
        return n


def component_mask(sheet, x0, y0, x1, y1):
    """Masque des tuiles du rectangle contenant des pixels de l'objet (utilisé pour ne pas poser les tuiles vides)."""
    a = np.array(SHEETS.get(sheet).crop((x0, y0, x1, y1)))[..., 3] > 0
    h, w = (y1 - y0) // T, (x1 - x0) // T
    return a.reshape(h, T, w, T).any(axis=(1, 3))


def sand_tile_mask(x0, y0, x1, y1, keep_seed=None, dilate=1):
    """Masque de tuiles (h,w) des chemins de sable natifs de Metano_Town_Base dans la fenêtre pixel donnée.
    keep_seed = (px,py) : ne garder que la composante connexe contenant ce point (coordonnées feuille)."""
    from scipy import ndimage
    a = np.array(SHEETS.get('Metano_Town_Base').crop((x0, y0, x1, y1))).astype(int)
    r, g, b, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    sand = (al > 0) & (r > 185) & (g > 140) & (b > 80) & (r - b > 45) & (g < r)
    h, w = (y1 - y0) // T, (x1 - x0) // T
    tiles = sand.reshape(h, T, w, T).mean(axis=(1, 3)) > 0.05
    if keep_seed is not None:
        lab, _ = ndimage.label(tiles)
        sc, sr = (keep_seed[0] - x0) // T, (keep_seed[1] - y0) // T
        k = lab[sr, sc]
        assert k, 'graine hors sable'
        tiles = lab == k
    if dilate:
        tiles = ndimage.binary_dilation(tiles, iterations=dilate)
    return tiles


def blit_masked(scene, layer, sheet, x0, y0, mask, col, row):
    """Pose les tuiles (feuille, pixels x0,y0) dont mask[dy,dx] est vrai, en (col,row)."""
    h, w = mask.shape
    scene.blit(layer, sheet, x0 // T, y0 // T, w, h, col, row, only_mask=mask)


_CUT_CACHE = {}


def object_pixel_mask(sheet, x0, y0, x1, y1):
    """Découpe : pixels de la composante principale (hors sable) du rectangle, dilatée de 1 px."""
    key = (sheet, x0, y0, x1, y1)
    if key not in _CUT_CACHE:
        from scipy import ndimage
        a = np.array(SHEETS.get(sheet).crop((x0, y0, x1, y1))).astype(int)
        r, g, b, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
        sand = (al > 0) & (r > 185) & (g > 140) & (b > 80) & (r - b > 45) & (g < r)
        solid = (al > 0) & ~sand
        lab, _ = ndimage.label(ndimage.binary_dilation(solid, iterations=1))
        lab[al == 0] = 0
        ids, counts = np.unique(lab[lab > 0], return_counts=True)
        main = ids[np.argmax(counts)]
        _CUT_CACHE[key] = ndimage.binary_dilation(lab == main, iterations=1) & (al > 0)
    return _CUT_CACHE[key]


def place_object(scene, layer, name, col, row, phase=0, cutout=None):
    """cutout=None : découpe automatique si le rectangle contient des pixels étrangers (maisons) ;
    False : tuiles natives entières (objets propres) ; True : découpe forcée."""
    from objets import OBJETS
    sheet, x0, y0, x1, y1 = OBJETS[name]
    mask = component_mask(sheet, x0, y0, x1, y1)
    pm = None
    if cutout is not False:
        m = object_pixel_mask(sheet, x0, y0, x1, y1)
        al = np.array(SHEETS.get(sheet).crop((x0, y0, x1, y1)))[..., 3] > 0
        if cutout or (al & ~m).any():
            pm = m
    scene.blit(layer, sheet, x0 // T, y0 // T, (x1 - x0) // T, (y1 - y0) // T, col, row, phase=phase,
               only_mask=mask, pixel_mask=pm)


def place_animated(scene, layer, name, col, row, phases=4):
    from objets import ANIMES
    frames = ANIMES[name]
    for p in range(phases):
        sheet, x0, y0, x1, y1 = frames[p % len(frames)]
        mask = component_mask(sheet, x0, y0, x1, y1)
        scene.blit(layer, sheet, x0 // T, y0 // T, (x1 - x0) // T, (y1 - y0) // T, col, row, phase=p, only_mask=mask)


def river_animation(scene, layer, x0, y0, x1, y1, col, row, phases=4):
    """Eau animée native : River_Animation_1..4 aux mêmes coordonnées feuille (fenêtre pixel de la Base)."""
    for p in range(phases):
        sheet = f'Metano_Town_River_Animation_{p + 1}'
        scene.blit(layer, sheet, x0 // T, y0 // T, (x1 - x0) // T, (y1 - y0) // T, col, row, phase=p)


def dark_tile_mask(x0, y0, x1, y1, sheet='Metano_Town_Base', lum_max=70, min_px=6):
    """Tuiles de la fenêtre contenant au moins min_px pixels très sombres (grilles, ombres isolées)."""
    a = np.array(SHEETS.get(sheet).crop((x0, y0, x1, y1))).astype(int)
    lum = (a[..., 0] * 3 + a[..., 1] * 6 + a[..., 2]) // 10
    dark = (a[..., 3] > 0) & (lum < lum_max)
    h, w = (y1 - y0) // T, (x1 - x0) // T
    return dark.reshape(h, T, w, T).sum(axis=(1, 3)) >= min_px
