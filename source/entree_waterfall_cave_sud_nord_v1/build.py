"""Entrée Waterfall Cave sud -> nord V1 (EWC1) — format 4:3 vaste (768 x 576 px, 96 x 72 cases).

Demande : « tu dois utiliser la méthode et reprendre seulement de ta branche parente. Et refaire waterfall avec la
génération fond majenta multicalque ». Base : branche parente uniquement (Entrée Jungle V1, `0eaa002c`).
Méthode « textures canoniques » = rendu généré RÉFÉRENCÉ : le rip `entrancecascade.png` (entrée de Waterfall Cave,
PMD Explorers) est passé au générateur comme image de référence.
Bruts (voir manifest.json -> generation, prompts complets) :
- decor_magenta.png : décor complet 4:3 (1200 x 896), toutes les surfaces d'eau plate en magenta ;
- sol_complet.png : sable complet édité depuis le décor ;
- ecume_poses.png : planche d'écume et d'embruns sur magenta (grille 4 x 4 rendue au lieu de 2 x 6).
Normalisation UNIFORME x(576/896) puis recadrage centré à 768 ; réduction par classe (down_class du gabarit Jungle).
Calques : sol complet, sable, cailloux, touffes, plateaux, berge, falaises, arbres, entrée sombre, écume du pied.
Animations, chacune sur son calque :
- eau des bassins et de la vasque « façon rivière Métano », COULEURS MÉTANO EXACTES, 4 x 10 ticks ;
- scintillements Metano_Town_River_Sparkles NATIFS, 4 x 10 ticks ;
- rideau de la cascade : pixels générés du décor rendus périodiques (période 72 px, fondu 24 px), défilement
  vers le sud de 6 px par phase, 12 x 4 ticks ;
- écume (bouillons) et embruns : poses générées, émetteurs déphasés, 12 x 4 ticks.
Scène : PPCM(40, 48) = 240 ticks = 4 s.
Lancer : .venv/bin/python source/entree_waterfall_cave_sud_nord_v1/build.py
"""
from pathlib import Path
import hashlib, importlib.util, io, json, shutil, uuid, zipfile

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
RAW = HERE / 'bruts'
REF = R / 'entrancecascade.png'
OUT = R / 'renders/entree_waterfall_cave_sud_nord_v1'
STAGE = R / '.cache/entree_waterfall_cave_sud_nord_v1/entree_waterfall_cave_sud_nord'
NAMESPACE = 'entree_waterfall_cave_sud_nord'
ASSET = 'ewc1_entree_waterfall_cave'
PFX = 'EWC1'
W, H = 768, 576                      # 4:3, 96 x 72 cases
SRC = (1200, 896)
WATER_PHASES, WATER_TICKS = 4, 10
FALL_PHASES, FALL_TICKS = 12, 4
FALL_PERIOD, FALL_BLEND, FALL_Y0 = 72, 24, 4   # période mesurée ~74 px (autocorrélation des crêtes, 115 px pleine rés.)
FALL_STEP = FALL_PERIOD // FALL_PHASES         # 6 px vers le sud par phase
FOAM_PHASES, FOAM_TICKS = 12, 4
LOOP_TICKS = 240                     # PPCM(4 x 10, 12 x 4)
FCELL, FK = 32, 5                    # poses : fenêtre 160 px -> 32 px (x1/5)
Y_FOOT, Y_POOL = 268, 306            # pleine rés. : pied du rideau / début de la vasque (profil des blancs, mesuré)
TUFT_MAX = 300                       # touffes du décor ~60-120 px ; au-delà : morceaux d'arbres coupés
PUFF_SEQ = [0, 1, 2, 3, 4, 5, 6, 7, -1, -1, -1, -1]   # bouillon : naît, gonfle, éclate, se disperse, repos
SPRAY_SEQ = [0, 1, 2, 3, -1, -1, -1, -1, -1, -1, -1, -1]
GEN = [
    {'file': 'decor_magenta.png', 'images': ['entrancecascade.png'], 'prompt':
     'Use EXACTLY the same textures, palette and pixel-art style as the reference image (Pokemon Mystery Dungeon '
     'Explorers of Sky, Waterfall Cave entrance): same tan layered rock cliffs, same bonsai trees with bright green '
     'foliage and brown twisted trunks, same warm sand ground with tiny green tufts and pebbles, same blue waterfall '
     'with white streaks and white foam. Make a NEW, larger top-down map. WIDE LANDSCAPE 4:3, zoomed out so the area '
     'feels vast. Layout: the player arrives at the SOUTH (bottom edge) on a wide sandy beach; a long sandy path goes '
     'NORTH through the middle between two pools, up to a huge waterfall at the top center. At the foot of the '
     'waterfall, where the path ends, a dark cave opening is visible behind the falling water. Tall rock cliffs with '
     'bonsai trees fill the left and right sides and the top corners, round tan boulders along the pools. IMPORTANT: '
     'every flat water surface (pools, lake, streams) is filled with flat pure magenta #FF00FF, no ripples and no foam '
     'on it. The waterfall and its white foam at the base stay drawn normally. No characters, no text, no UI, no border.'},
    {'file': 'sol_complet.png', 'images': ['source/entree_waterfall_cave_sud_nord_v1/bruts/decor_magenta.png'], 'prompt':
     'Edit this image: keep the exact same framing, size and pixel-art style, but remove EVERYTHING except the ground: '
     'no cliffs, no trees, no waterfall, no cave, no water, no magenta, no boulders. The whole image becomes the same '
     'warm tan sand ground as the sandy path (faint grain, a few tiny pebbles), flat top-down, seamless, uniform lighting.'},
    {'file': 'ecume_poses.png', 'images': ['entrancecascade.png'], 'prompt':
     'Sprite sheet on a flat pure magenta #FF00FF background, in EXACTLY the pixel-art style and colors of the white '
     'water foam at the foot of the waterfall in the reference image. 2 rows x 6 columns of separate foam splash puffs '
     '(white, very light blue, light cyan). Row 1: a foam puff bubbling up then fading, 6 poses (small, medium, large, '
     'bursting, breaking apart, small remnants). Row 2: a spray of droplets, 6 poses. Each pose isolated and centered '
     'in its cell, wide magenta spacing, no overlap, no text, no grid lines.'},
]


def loadmod(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


JM = loadmod('ejn1_utils', R / 'source/entree_jungle_sud_nord_v1/build.py')   # même 4:3 : down_class, down_full, rgba
BM = JM.BM                                                                      # utilitaires Bristle, W/H déjà réglés
assert (JM.W, JM.H, JM.SRC, BM.W, BM.H) == (W, H, SRC, W, H)
keep_large, place, cell_grid = BM.keep_large, BM.place, BM.cell_grid
down_class, down_full, rgba, resize_plane = JM.down_class, JM.down_full, JM.rgba, JM.resize_plane


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# Palettes par groupe : dans la palette commune, le rideau virait au vert-gris (B 204 -> 143) et la bouche au brun.
PALETTE_GROUPS = {'terrain': (['sol_complet', 'sable', 'cailloux', 'touffes', 'plateaux', 'berge', 'falaises'], 96),
                  'arbres': (['arbres'], 24), 'eau_dessinee': (['cascade', 'ecume_pied'], 24), 'bouche': (['entree_sombre'], 12)}


def quantize_group(layers, n):
    opaque = np.concatenate([l[l[..., 3] == 255][:, :3] for l in layers.values()])
    q = Image.fromarray(opaque.reshape(-1, 1, 3)).quantize(colors=n, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = np.array(q.getpalette()[:n * 3], 'uint8').reshape(-1, 3); out = {}
    for k, l in layers.items():
        a = l.copy(); m = a[..., 3] == 255
        if m.any():
            a[..., :3] = pal[np.array(Image.fromarray(a[..., :3]).quantize(palette=q, dither=Image.Dither.NONE))]
        a[~m] = 0; out[k] = a
    return out


def rgb(p):
    return np.array(Image.open(p).convert('RGB')).astype(int)


def close_(m, it):
    """Fermeture sans rognage des bords (bord répliqué) : les rangées du haut de la cascade restaient hors masque."""
    p = it + 1
    return nd.binary_closing(np.pad(m, p, mode='edge'), iterations=it)[p:-p, p:-p]


def local_sd(lum, k=9):
    return np.sqrt(np.maximum(nd.uniform_filter(lum ** 2, k) - nd.uniform_filter(lum, k) ** 2, 0))


def feats(a):
    r, g, b = a.transpose(2, 0, 1); lum = a @ [.299, .587, .114]
    mx, mn = a.max(2), a.min(2); sat = (mx - mn) * 255 / np.maximum(mx, 1)
    return r, g, b, lum, mn, sat, local_sd(lum)


# ---------------------------------------------------------------- fidélité au rip (même classifieur des deux côtés)
def materials(a):
    r, g, b, lum, mn, sat, sd = feats(a)
    mag = (r > g * 1.5) & (b > g * 1.3) & (r > 150) & (b > 130)
    green = (g > r + 8) & (g > b + 20)
    blue = ((b > r + 30) & (b > g - 10)) | ((mn > 175) & (b >= r - 10) & (sat < 95))
    sand = (lum > 158) & (sat > 112) & (sd < 12) & ~green & ~blue & ~mag
    rock = ~sand & ~green & ~blue & ~mag & (r > b + 25) & (lum > 70)
    return {'sable': sand, 'roche': rock, 'feuillage': green & (lum > 60), 'eau_cascade': blue & ~mag}


def fidelity(decor, ref, curtain):
    fr, fd = materials(ref), materials(decor); out = {}
    yy, xx = np.mgrid[:ref.shape[0], :ref.shape[1]]
    fr['rideau'] = fr.pop('eau_cascade') & (xx >= 150) & (xx <= 355) & (yy <= 180)   # rideau du rip (boîte mesurée)
    fd.pop('eau_cascade'); fd['rideau'] = curtain                                     # rideau segmenté du brut
    for k in fr:
        mr, md = ref[fr[k]].mean(0), decor[fd[k]].mean(0)
        out[k] = {'rip_rgb': [round(float(v), 1) for v in mr], 'decor_rgb': [round(float(v), 1) for v in md],
                  'distance': round(float(np.linalg.norm(mr - md)), 1)}
    return out


# ---------------------------------------------------------------- segmentation pleine résolution
def classify(a):
    r, g, b, lum, mn, sat, sd = feats(a)
    yy, xx = np.mgrid[:a.shape[0], :a.shape[1]]
    mag = (r > g * 1.5) & (b > g * 1.3) & (r > 150) & (b > 130)
    magenta = nd.binary_dilation(mag, iterations=2)                    # liseré rose du magenta
    zone = (xx > 430) & (xx < 780) & (yy < 400)                       # cascade + vasque (mesuré)
    aqua = zone & ~magenta & (((b > r + 30) & (b > g - 10)) | ((mn > 175) & (b >= r - 10) & (sat < 95)))
    aqua = keep_large(close_(aqua, 2), 2000) & zone
    core = nd.binary_fill_holes(keep_large(close_(zone & (lum < 60) & (sat < 60), 3), 1500))   # bouche (34,34,34)
    cave = nd.binary_fill_holes(nd.binary_dilation(core, iterations=9)) & ~aqua   # + rebord rocheux et sol de la bouche
    curtain = aqua & (yy < Y_FOOT) & ~cave
    foam = aqua & (yy >= Y_FOOT) & (yy < Y_POOL) & ~cave & (mn > 170) & (sat < 100)
    foam = keep_large(close_(foam, 1), 40)
    plunge = aqua & ~curtain & ~foam & ~cave
    water = magenta | plunge
    green = (g > r + 8) & (g > b + 20) & ~water & ~aqua & ~cave
    gl, gn = nd.label(close_(green, 2)); gs = nd.sum(np.ones_like(gl), gl, range(1, gn + 1))
    big = np.isin(gl, 1 + np.flatnonzero(gs >= TUFT_MAX))
    small = np.isin(gl, 1 + np.flatnonzero((gs >= 6) & (gs < TUFT_MAX)))
    trunk = (lum < 115) & (r > b + 15) & nd.binary_dilation(big, iterations=16) & ~water & ~aqua & ~cave & ~small
    tl, tn = nd.label(trunk); touch = set(np.unique(tl[nd.binary_dilation(big, iterations=2) & trunk])) - {0}
    trees = big | np.isin(tl, list(touch))
    dw = nd.distance_transform_edt(~water)
    berge = (dw > 0) & (dw <= 4) & (lum < 140) & ~trees & ~aqua & ~cave & ~small
    sand = (lum > 158) & (sat > 112) & (sd < 12) & ~water & ~aqua & ~cave & ~trees & ~berge
    sand = keep_large(nd.binary_opening(close_(sand, 2), iterations=2), 400) & ~water & ~aqua & ~cave & ~trees & ~berge
    lab, _ = nd.label(sand)
    south = sorted(set(np.unique(lab[-4:][sand[-4:]])) - {0})
    walk = lab == max(south, key=lambda l: int((lab == l).sum()))      # plage principale reliée au sud ; poches -> plateaux
    holes = nd.binary_fill_holes(walk) & ~walk & ~water & ~trees & ~berge
    pebbles = keep_large(holes & ~small, 4) & ~keep_large(holes & ~small, 600)
    plateau = sand & ~walk
    plateau = nd.binary_fill_holes(plateau) & ~walk & ~small & ~trees & ~water & ~aqua & ~cave & ~berge & ~pebbles
    taken = water | curtain | foam | cave | trees | small | berge | walk | pebbles | plateau
    return dict(water=water, cascade=curtain, ecume_pied=foam, entree_sombre=cave, sable=walk, cailloux=pebbles,
                touffes=small, plateaux=plateau, berge=berge, falaises=~taken, arbres=trees)


# ---------------------------------------------------------------- rideau de cascade : texture générée rendue périodique
def fall_frames(layer, mask, cave):
    ys, xs = np.nonzero(mask); x0, x1 = int(xs.min()), int(xs.max()) + 1
    src = layer[..., :3].astype(float); n = FALL_PERIOD + FALL_BLEND
    strip = np.zeros((n, x1 - x0, 3)); valid = np.zeros((n, x1 - x0), bool); src_row = np.full(x1 - x0, -1)
    for x in range(x0, x1):
        # texture VERTICALE de la colonne elle-même : bande [Y0, Y0+n) ou une période plus bas (rideau plus étroit en
        # haut) -> même phase des crêtes, indice (y - Y0) mod P. On garde la bande la mieux couverte, sans la bouche.
        cands = [(mask[b0:b0 + n, x].mean(), b0) for b0 in (FALL_Y0, FALL_Y0 + FALL_PERIOD)
                 if b0 + n <= H and not cave[b0:b0 + n, x].any()]
        if cands and max(cands)[0] >= 0.6:
            b0 = max(cands)[1]; i = x - x0
            strip[:, i] = src[b0:b0 + n, x]; valid[:, i] = mask[b0:b0 + n, x]; src_row[i] = b0
    assert (src_row >= 0).mean() > 0.6, 'rideau trop court pour la période'
    holes = int((~valid).sum())
    for r_ in range(n):                    # trous sous les arbres en surplomb + colonnes extrêmes : pixel valide le plus
        ok, miss = np.flatnonzero(valid[r_]), np.flatnonzero(~valid[r_])   # proche SUR LA MÊME RANGÉE de la bande
        if len(miss):
            strip[r_, miss] = strip[r_, ok[np.abs(ok[None] - miss[:, None]).argmin(1)]]
    T = strip[:FALL_PERIOD].copy()
    for k in range(FALL_BLEND):                                        # raccord : T[P-1] -> T[0] = rangée P de la bande
        w = k / FALL_BLEND; T[k] = (1 - w) * strip[FALL_PERIOD + k] + w * strip[k]
    pal = np.unique(layer[mask][:, :3], axis=0).astype(float)
    Tq = pal[((T[..., None, :] - pal[None, None]) ** 2).sum(-1).argmin(-1)].astype('uint8')
    frames, rows = [], np.arange(H)
    for t in range(FALL_PHASES):
        f = np.zeros((H, W, 4), 'uint8')
        f[:, x0:x1, :3] = Tq[(rows - FALL_Y0 - t * FALL_STEP) % FALL_PERIOD]   # la texture descend de 6 px par phase
        f[..., 3] = 255; f[~mask] = 0; frames.append(f)
    return frames, {'x_range': [x0, x1], 'bandes_source': {str(b): int((src_row == b).sum()) for b in (FALL_Y0, FALL_Y0 + FALL_PERIOD)},
                    'colonnes_sans_bande': int((src_row < 0).sum()), 'pixels_bouches': holes, 'palette_colors': int(len(pal))}


# ---------------------------------------------------------------- poses générées (planche sur magenta)
def sheet_poses(path, grid, picks, pal, cov_min=0.25):
    src = rgb(path); h, w = src.shape[:2]; r, g, b = src.transpose(2, 0, 1)
    bg = ((r - g) > 40) & ((b - g) > 40)                               # magenta + liseré rose du détourage
    rows, cols = grid; ch, cw = h / rows, w / cols; win = FCELL * FK; out = []
    for ry, cx in picks:
        by0, by1, bx0, bx1 = int(ry * ch), int((ry + 1) * ch), int(cx * cw), int((cx + 1) * cw)
        obj = np.zeros((h, w), bool); obj[by0:by1, bx0:bx1] = ~bg[by0:by1, bx0:bx1]
        ys, xs = np.nonzero(obj); cy0, cx0 = (ys.min() + ys.max()) // 2, (xs.min() + xs.max()) // 2
        y0, x0 = cy0 - win // 2, cx0 - win // 2
        pad = np.zeros((win, win, 3)); pm = np.zeros((win, win), bool)
        sy0, sx0, sy1, sx1 = max(0, y0), max(0, x0), min(h, y0 + win), min(w, x0 + win)
        pad[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = src[sy0:sy1, sx0:sx1]
        pm[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = obj[sy0:sy1, sx0:sx1]
        blk = pm.reshape(FCELL, FK, FCELL, FK); cov = blk.mean((1, 3))
        col = (pad * pm[..., None]).reshape(FCELL, FK, FCELL, FK, 3).sum((1, 3)) / np.maximum(blk.sum((1, 3)), 1)[..., None]
        o = np.zeros((FCELL, FCELL, 4), 'uint8'); o[..., :3] = pal[((col[..., None, :] - pal[None, None]) ** 2).sum(-1).argmin(-1)]
        o[..., 3] = 255; o[cov < cov_min] = 0; out.append(o)
    return out


def sprite_frames(poses, emitters, seq, clip):
    frames = [np.zeros((H, W, 4), 'uint8') for _ in seq]
    for cx, cy, off in emitters:
        for t in range(len(seq)):
            p = seq[(t + off) % len(seq)]
            if p < 0:
                continue
            spr = poses[p]; hh, ww = spr.shape[:2]; y0, x0 = cy - hh // 2, cx - ww // 2
            assert 0 <= y0 and y0 + hh <= H and 0 <= x0 and x0 + ww <= W
            m = spr[..., 3] > 0; frames[t][y0:y0 + hh, x0:x0 + ww][m] = spr[m]
    for f in frames:
        f[~clip] = 0
    return frames


# ---------------------------------------------------------------- ORA (titre du lot)
def write_ora(path, layers):
    import xml.etree.ElementTree as ET
    root = ET.Element('image', w=str(W), h=str(H), name='Entree Waterfall Cave sud-nord V1 (EWC1)')
    stack = ET.SubElement(root, 'stack'); comp = Image.new('RGBA', (W, H))
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', 'image/openraster', compress_type=zipfile.ZIP_STORED)
        items = list(layers.items())
        for i, (name, a) in reversed(list(enumerate(items))):
            fn = f'data/layer{i:02d}.png'
            ET.SubElement(stack, 'layer', name=name, src=fn, x='0', y='0', opacity='1.0', visibility='visible',
                          **{'composite-op': 'svg:src-over'})
            b = io.BytesIO(); Image.fromarray(a).save(b, format='PNG'); z.writestr(fn, b.getvalue())
        for _, a in items:
            comp.alpha_composite(Image.fromarray(a))
        b = io.BytesIO(); comp.save(b, format='PNG'); z.writestr('mergedimage.png', b.getvalue())
        th = comp.copy(); th.thumbnail((256, 256)); b = io.BytesIO(); th.save(b, format='PNG')
        z.writestr('Thumbnails/thumbnail.png', b.getvalue())
        z.writestr('stack.xml', ET.tostring(root, encoding='utf-8', xml_declaration=True))


# ---------------------------------------------------------------- Ground PMDO 0.8.12
def ground_project(stack, blocked, entry_px, threshold_px, gfx, tools):
    if STAGE.exists():
        shutil.rmtree(STAGE)
    with zipfile.ZipFile(R / 'mod_metano_expeditions_pmdo_0812.zip') as z:
        tpl = json.loads(z.read('metano_expeditions/Data/Ground/v50812_01_crete_sillage_jour.rsground'))
    o = tpl['Object']; gw, gh = W // 8, H // 8; layers, banks = [], []
    for i, (title, frames, ticks) in enumerate(stack):
        bank = gfx.TileBank(f'{PFX}_{i:02d}_{title.split()[0].upper()}')
        bank.ids[bytes(256)] = (0, 0); bank.data[(0, 0)] = bytes(256)

        def cell(x, y, frames=frames, bank=bank):
            fs = []
            for a in frames:
                f = bank.add(Image.fromarray(a[y*8:y*8+8, x*8:x*8+8]), x, y)
                fs.append(f if f else {'Sheet': bank.name, 'TexLoc': {'X': 0, 'Y': 0}})
            if all(f['TexLoc'] == {'X': 0, 'Y': 0} for f in fs):
                return []
            return [fs[0]] if all(f == fs[0] for f in fs) else fs
        layers.append(gfx.layer(f'{i:02d} {title}', gw, gh, cell, ticks)); banks.append(bank)
    layers.append(gfx.layer(f'{len(layers):02d} Vos elements avant-plan (Top)', gw, gh, draw=4))
    for bank in banks:
        bank.write(STAGE / f'Content/Tile/{bank.name}.tile')
    o.update(Name={'DefaultText': 'Entree Waterfall Cave - sud vers nord (4:3)', 'LocalTexts': {}}, AssetName=ASSET,
             Released=False, TexSize=1, Music='', EdgeView=1, ViewCenter=None, ViewOffset={'X': 0, 'Y': 0},
             ActiveChar=None, Status={}, Layers=layers,
             Background={'$type': 'RogueEssence.Dungeon.LayeredBG, RogueEssence', 'Layers': []},
             Comment='PMDO 0.8.12. Rendu genere 4:3 reference sur le rip Waterfall Cave (entrancecascade.png) ; '
                     'eau facon Metano (couleurs Metano exactes), scintillements Metano natifs, cascade, ecume et '
                     'embruns generes. Collisions de base a verifier. Seuil non raccorde.')
    o['obstacles'] = [[{'Bounds': {'X': x*8, 'Y': y*8, 'Width': 8, 'Height': 8}, 'Tags': int(blocked[y, x])}
                       for y in range(gh)] for x in range(gw)]
    mk = lambda n, p: {'EntName': n, 'Direction': 4, 'EntEnabled': True, 'triggerType': 0,
                       'Collider': {'X': p[0], 'Y': p[1], 'Width': 16, 'Height': 16}}
    o['Entities'] = [{'Name': 'Entrees et vos acteurs', 'Visible': True, 'MapChars': [], 'GroundObjects': [], 'Spawners': [],
                      'Markers': [mk('entrance', entry_px), mk('donjon_seuil', threshold_px)]}]
    o['Decorations'] = [{'Name': 'Vos decorations', 'Layer': 2, 'Visible': True, 'Anims': []}]
    tpl['Version'] = '0.8.12.0'
    gfx.save(STAGE / f'Data/Ground/{ASSET}.rsground', json.dumps(tpl, ensure_ascii=False, separators=(',', ':')).encode())
    gfx.save(STAGE / f'Data/Script/{NAMESPACE}/ground/{ASSET}/init.lua',
             f'-- {ASSET} : base d edition, aucun warp.\nlocal {ASSET} = {{}}\nreturn {ASSET}\n'.encode())
    nodes = {}
    for p in sorted((STAGE / 'Content/Tile').glob('*.tile')):
        with p.open('rb') as f:
            nodes[p.stem] = tools.read_node(f)
    (STAGE / 'Content/Tile/index.idx').write_bytes(tools.encode_index(nodes))
    ident = uuid.uuid5(uuid.NAMESPACE_URL, 'https://github.com/meromoonmeri/guilde-treehouse-pmd/' + NAMESPACE)
    (STAGE / 'Mod.xml').write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<Header>
  <Name>Entree Waterfall Cave sud-nord 4:3 - Atelier 0.8.12</Name>
  <Author>meromoonmeri</Author>
  <Description>Projet d'edition : entree de Waterfall Cave generee au format 4:3 (ref. rip entrancecascade), bassins facon Metano, cascade, ecume et embruns animes. Pas une aventure jouable.</Description>
  <Namespace>{NAMESPACE}</Namespace>
  <UUID>{ident}</UUID>
  <Version>1.0.0.0</Version>
  <GameVersion>0.8.12.0</GameVersion>
  <ModType>Quest</ModType>
  <Relationships />
</Header>
''')
    script = (R / 'source/pmdo_cote/INSTALLER.py').read_text()
    needle = '            relative = src.relative_to(source)\n'
    assert needle in script
    script = script.replace(needle, needle + "            if relative.as_posix() == 'Content/Tile/index.idx':\n                continue\n")
    (STAGE / 'INSTALLER.py').write_text(script)
    shutil.copyfile(HERE / 'README_PACK.md', STAGE / 'README.md')
    return {b.name: len(b.data) for b in banks}


# ---------------------------------------------------------------- main
def build():
    gfx = loadmod('pmdo_codec', R / 'source/pmdo_cote/build.py')
    tools = loadmod('index_tools', R / 'source/pmdo_cote/INSTALLER.py')
    v1 = loadmod('esn1', R / 'source/entree_sud_nord_generee_v1/build.py')
    if OUT.exists():
        for d in ['calques', 'animation', 'poses', 'masques', 'review']:
            shutil.rmtree(OUT / d, ignore_errors=True)
    for d in ['calques', 'animation/eau', 'animation/scintillements', 'animation/cascade', 'animation/ecume',
              'animation/embruns', 'poses', 'masques', 'review']:
        (OUT / d).mkdir(parents=True, exist_ok=True)
    a = rgb(RAW / 'decor_magenta.png'); f = rgb(RAW / 'sol_complet.png'); ref = rgb(REF)
    assert a.shape[:2] == f.shape[:2] == (SRC[1], SRC[0])
    m = classify(a)
    order = ['water', 'cascade', 'ecume_pied', 'entree_sombre', 'sable', 'cailloux', 'touffes', 'plateaux', 'berge',
             'falaises', 'arbres']
    ex, cols = down_class(a, m, order)
    water = ex['water']
    static = ['sable', 'cailloux', 'touffes', 'plateaux', 'berge', 'falaises', 'arbres', 'entree_sombre']
    layers = {'sol_complet': rgba(down_full(f), ~water)}
    for k in static + ['cascade', 'ecume_pied']:
        layers[k] = rgba(cols[k], ex[k])
    q = {}
    for keys, n in PALETTE_GROUPS.values():
        q.update(quantize_group({k: layers[k] for k in keys}, n))
    layers = q
    for k, v in ex.items():
        Image.fromarray((v * 255).astype('uint8')).save(OUT / 'masques' / f'{PFX}_masque_{k}.png')
    land = np.zeros((H, W), bool)
    for k in static + ['cascade', 'ecume_pied']:
        land |= layers[k][..., 3] == 255
    visible = water & ~land
    wf, dist = BM.water_phases(water, visible)                          # couleurs Métano exactes
    fams = BM.sparkle_families(); taken = np.zeros((H, W), bool)
    sf = [np.zeros((H, W, 4), 'uint8') for _ in range(WATER_PHASES)]; sparkles = []
    for fi, (name, frames) in enumerate(fams.items()):
        hh, ww = frames[0].shape[:2]
        for (y, x) in place(visible & (dist > 4), (hh, ww), 4, 41 + fi, taken, core=8):
            sparkles.append({'famille': name, 'xy': [x, y]})
            for t in range(WATER_PHASES):
                mm = frames[t][..., 3] > 0; sf[t][y:y+hh, x:x+ww][mm] = frames[t][mm]
    for arr in sf:
        arr[~visible] = 0
    # Cascade : rideau animé (remplace le rideau fixe du décor, mêmes pixels générés rendus périodiques).
    fall, fall_info = fall_frames(layers['cascade'], ex['cascade'], ex['entree_sombre'])
    # Écume et embruns : poses générées, palette = couleurs de l'écume du pied du décor.
    foam_pal = np.unique(layers['ecume_pied'][ex['ecume_pied']][:, :3], axis=0).astype(float)
    puffs = sheet_poses(RAW / 'ecume_poses.png', (4, 4), [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3)], foam_pal)
    sprays = sheet_poses(RAW / 'ecume_poses.png', (4, 4), [(3, 3), (3, 0), (3, 1), (3, 2)], foam_pal)
    for i, p in enumerate(puffs):
        Image.fromarray(p).save(OUT / 'poses' / f'{PFX}_bouillon_{i}.png')
    for i, p in enumerate(sprays):
        Image.fromarray(p).save(OUT / 'poses' / f'{PFX}_embrun_{i}.png')
    cy_, cx_ = np.nonzero(ex['entree_sombre']); cave_x = (int(cx_.min()), int(cx_.max()))
    fy, fx = np.nonzero(ex['ecume_pied']); foot_y = int(np.median(fy))
    xs_c = np.nonzero(ex['cascade'].any(0))[0]
    puff_em = [(x, foot_y, (i * 5) % FOAM_PHASES) for i, x in enumerate(range(int(xs_c.min()) + 12, int(xs_c.max()) - 11, 13))
               if not (cave_x[0] - 4 <= x <= cave_x[1] + 4)]
    pool_y = foot_y + 18; span = int(xs_c.max() - xs_c.min())
    spray_em = [(int(xs_c.min() + span * fr_), pool_y, off) for fr_, off in ((0.22, 0), (0.42, 3), (0.60, 6), (0.80, 9))]
    clip = (ex['water'] | ex['ecume_pied'] | ex['cascade']) & ~ex['entree_sombre']
    ecume = sprite_frames(puffs, puff_em, PUFF_SEQ, clip)
    embruns = sprite_frames(sprays, spray_em, SPRAY_SEQ, clip & ~ex['cascade'])
    # Exports
    anim = {'eau': (wf, WATER_TICKS), 'scintillements': (sf, WATER_TICKS), 'cascade': (fall, FALL_TICKS),
            'ecume': (ecume, FOAM_TICKS), 'embruns': (embruns, FOAM_TICKS)}
    order_names = ['eau', 'scintillements', 'sol_complet'] + static + ['cascade', 'ecume_pied', 'ecume', 'embruns']
    stack_named, layer_list = [], []
    for i, nm in enumerate(order_names):
        if nm in anim:
            frames, ticks = anim[nm]
            for t, fr in enumerate(frames):
                Image.fromarray(fr).save(OUT / 'animation' / nm / f'{PFX}_{i:02d}_{nm}_f{t:02d}.png')
            layer_list.append({'file': f'animation/{nm}/{PFX}_{i:02d}_{nm}_fNN.png', 'phases': len(frames), 'ticks': ticks})
        else:
            frames, ticks = [layers[nm]], 60
            Image.fromarray(layers[nm]).save(OUT / 'calques' / f'{PFX}_{i:02d}_{nm}.png')
            layer_list.append({'file': f'calques/{PFX}_{i:02d}_{nm}.png', 'phases': 1, 'ticks': 60})
        stack_named.append((nm, frames, ticks))
    # Collisions : sable relié au sud, cailloux, touffes enclavées dans ce sable.
    ground = (layers['sable'][..., 3] == 255) | (layers['cailloux'][..., 3] == 255)
    walk = ground | ((layers['touffes'][..., 3] == 255) & nd.binary_fill_holes(ground))
    blocked = cell_grid(~walk); gh_, gw_ = blocked.shape
    pxs = np.nonzero(walk[H - 8])[0]; med = int(np.median(pxs)) // 8
    ecol = min((c for c in range(gw_ - 1) if not blocked[gh_ - 2:, c:c + 2].any()), key=lambda c: abs(c - med))
    entry_px = [ecol * 8, H - 16]
    ccx = (cave_x[0] + cave_x[1]) // 2
    north = int(np.nonzero(walk[:, ccx])[0].min())                     # bord nord du parvis sous la bouche
    threshold_px = [ccx // 8 * 8 - 8, (north + 7) // 8 * 8]
    while blocked[threshold_px[1] // 8:threshold_px[1] // 8 + 2, threshold_px[0] // 8:threshold_px[0] // 8 + 2].any():
        threshold_px[1] += 8
    ok, explored = v1.reachable(blocked, (entry_px[1] // 8, entry_px[0] // 8), (threshold_px[1] // 8, threshold_px[0] // 8))
    assert ok, 'pas de chemin 16x16'

    def scene(tick):
        im = Image.new('RGBA', (W, H))
        for _, frames, ticks in stack_named:
            im.alpha_composite(Image.fromarray(frames[(tick // ticks) % len(frames)]))
        return im
    step = 4
    scenes = [scene(t) for t in range(0, LOOP_TICKS, step)]
    scenes[0].save(OUT / 'review' / f'{PFX}_scene_t000.png')
    scenes[0].save(OUT / 'review' / f'{PFX}_scene_animee.webp', save_all=True, append_images=scenes[1:],
                   duration=round(step * 1000 / 60), loop=0, lossless=True)
    col = scenes[0].copy(); ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(ov)
    for y, x in zip(*np.nonzero(blocked)):
        dr.rectangle([x*8, y*8, x*8+7, y*8+7], fill=(220, 40, 40, 90))
    for (qx, qy), c in ((entry_px, (255, 230, 40, 255)), (threshold_px, (60, 220, 255, 255))):
        dr.rectangle([qx, qy, qx + 15, qy + 15], outline=c, width=2)
    col.alpha_composite(ov); col.save(OUT / 'review' / f'{PFX}_collisions_marqueurs.png')
    sheet = Image.new('RGBA', (8 * 136, 2 * 136), (40, 110, 150, 255))
    for r_, seq in enumerate((puffs, sprays)):
        for i, p in enumerate(seq):
            sheet.alpha_composite(Image.fromarray(p).resize((128, 128), Image.Resampling.NEAREST), (i * 136 + 4, r_ * 136 + 4))
    sheet.save(OUT / 'review' / f'{PFX}_planche_ecume_x4.png')
    write_ora(OUT / f'{PFX}_entree_waterfall_cave_calques.ora',
              {f'{i:02d}_{t}' + ('_f00' if len(fr) > 1 else ''): fr[0] for i, (t, fr, _) in enumerate(stack_named)})
    counts = ground_project([(t.replace('_', ' ') + (f' {len(fr)} phases' if len(fr) > 1 else ''), fr, tk)
                             for t, fr, tk in stack_named], blocked, entry_px, threshold_px, gfx, tools)
    fid = fidelity(a, ref, m['cascade'])
    final_fid = {}
    for k, nm in (('sable', 'sable'), ('roche', 'falaises'), ('feuillage', 'arbres'), ('rideau', 'cascade')):
        lay = layers[nm] if nm != 'cascade' else fall[0]
        px = lay[lay[..., 3] == 255][:, :3].astype(float)
        if nm == 'arbres':
            px = px[(px[:, 1] > px[:, 0] + 8) & (px[:, 1] > px[:, 2] + 20)]
        final_fid[k] = {'calque': nm, 'rgb': [round(float(v), 1) for v in px.mean(0)],
                        'distance_rip': round(float(np.linalg.norm(px.mean(0) - np.array(fid[k]['rip_rgb']))), 1)}
    manifest = {
        'lot': 'entree_waterfall_cave_sud_nord_v1', 'prefix': PFX, 'format': '4:3 vaste', 'size_px': [W, H],
        'grid_8px': [W // 8, H // 8], 'base': 'branche parente uniquement (Entree Jungle V1, 0eaa002c)',
        'method': 'textures canoniques = rendu genere REFERENCE : rip passe au generateur ; decor complet sur magenta '
                  '(eau plate = magenta), sol de sable complet edite depuis le decor, planche d ecume sur magenta',
        'reference_da': {'file': 'entrancecascade.png', 'sha256': sha(REF), 'titre': 'Entree cascade (Waterfall Cave, PMD Explorers)'},
        'generation': GEN,
        'raw_inputs': [{'file': f'source/entree_waterfall_cave_sud_nord_v1/bruts/{g["file"]}', 'sha256': sha(RAW / g['file']),
                        'size': list(Image.open(RAW / g['file']).size)} for g in GEN],
        'fidelite_rip': {'methode': 'moyenne RGB par matiere, meme classifieur sur le rip et sur le brut (rideau : boite '
                                    'x 150-355, y 0-180 du rip contre rideau segmente) ; distance euclidienne',
                         'brut': fid, 'calques_finaux': final_fid},
        'normalization': {'scale': JM.SCALE, 'scaled': [JM.SCALED_W, H], 'crop_x': [JM.CROP_X, JM.SCALED_W - W - JM.CROP_X],
                          'methode': 'moyenne ponderee par classe (BOX), attribution exclusive par poids maximal',
                          'palettes': {g: {'calques': k, 'couleurs': n} for g, (k, n) in PALETTE_GROUPS.items()}},
        'segmentation': 'eau = magenta dilate 2 px + vasque (bleu sous le pied du rideau) ; cascade = bleu/blanc de la zone '
                        'centrale nord au-dessus de y=268 (pleine res.) ; ecume du pied = blancs entre y=268 et 306 ; entree '
                        'sombre = aplat (34,34,34) + rebord de 9 px ; arbres = composantes vertes >= 300 px + troncs bruns '
                        'relies ; touffes = composantes vertes < 300 px ; berge = pixels sombres a <= 4 px de l eau ; sable = '
                        'lum>158, sat>112, ecart local<12, relie au bord sud ; plateaux = meme sable non relie ; cailloux = '
                        'trous du sable praticable ; falaises = reste',
        'layers': layer_list,
        'water': {'phases': WATER_PHASES, 'frame_length_ticks': WATER_TICKS, 'couleurs': {k: list(v) for k, v in BM.PAL.items()},
                  'modele': 'structure et cadence riviere Metano, couleurs Metano EXACTES (fonction water_phases du lot Bristle)',
                  'origine': 'pixels recalcules, pas de tuiles natives'},
        'sparkles': {'source': 'source/eau_metano/natifs/Metano_Town_River_Sparkles.tile', 'placements': sparkles,
                     'origine': 'pixels et couleurs Metano NATIFS inchanges (aplat de surface retire)'},
        'cascade': dict(fall_info, phases=FALL_PHASES, frame_length_ticks=FALL_TICKS, period_px=FALL_PERIOD,
                        blend_px=FALL_BLEND, step_px=FALL_STEP,
                        origine='pixels GENERES du rideau du decor, rendus periodiques par fondu puis ramenes a la palette '
                                'du rideau ; defilement cree par nous, pas une animation officielle'),
        'foam': {'brut': 'source/entree_waterfall_cave_sud_nord_v1/bruts/ecume_poses.png', 'grille_rendue': [4, 4],
                 'bouillon': {'cases': [[0, c] for c in range(4)] + [[1, c] for c in range(4)], 'sequence': PUFF_SEQ,
                              'emetteurs': [list(e) for e in puff_em]},
                 'embruns': {'cases': [[3, 3], [3, 0], [3, 1], [3, 2]], 'sequence': SPRAY_SEQ, 'emetteurs': [list(e) for e in spray_em]},
                 'reduction': f'fenetre {FCELL * FK} px -> {FCELL} px (x1/{FK}) centree, palette = couleurs de l ecume du pied',
                 'phases': FOAM_PHASES, 'frame_length_ticks': FOAM_TICKS,
                 'origine': 'dessin GENERE, emetteurs et chronologie crees ; pas une animation officielle'},
        'shadows': 'aucun calque d ombres : le rendu genere ne contient pas d ombre portee separable (595 px candidats epars)',
        'scene_loop_ticks': LOOP_TICKS,
        'access': {'entry_px': entry_px, 'threshold_px': threshold_px, 'path_found_16x16': ok, 'cells_explored': explored,
                   'blocked_cells': int(blocked.sum()), 'total_cells': int(blocked.size),
                   'rule': 'case bloquee si > 25 % hors sable praticable/cailloux/touffes enclavees',
                   'seuil': 'bord nord du parvis, face a la bouche derriere la cascade (on entre en marchant vers la cascade)'},
        'pmdo': {'target': '0.8.12', 'asset': ASSET, 'namespace': NAMESPACE, 'tiles_per_bank': counts, 'banks': list(counts),
                 'runtime_tested': False, 'warp': 'aucun'},
        'art_approved': False,
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    shutil.copyfile(OUT / 'manifest.json', STAGE / 'manifest.json')
    print(json.dumps({'sparkles': len(sparkles), 'entry': entry_px, 'threshold': threshold_px, 'blocked': int(blocked.sum()),
                      'cells': int(blocked.size), 'puff_emitters': len(puff_em), 'fidelite': {k: v['distance'] for k, v in fid.items()},
                      'final': {k: v['distance_rip'] for k, v in final_fid.items()}, 'tiles': counts}, indent=1))


if __name__ == '__main__':
    build()
