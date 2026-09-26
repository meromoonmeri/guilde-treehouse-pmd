"""Entrée Mystifying Forest sud -> nord V1 (EMF1) — format 4:3 vaste (768 x 576 px, 96 x 72 cases).

Demande : « passe à la suite ! » (après EWC2). Map suivante de la série, biome choisi par l'agent (à confirmer) :
Mystifying Forest, référence `Mystifying_Forest_entrance_TDS.png` (PMD Explorers), jamais utilisée comme référence
principale. Méthode « textures canoniques » = rendu généré RÉFÉRENCÉ (rip passé au générateur en images=) :
- decor_magenta.png : décor complet 4:3 (1200 x 896), la mare en magenta ;
- sol_complet.png : herbe complète éditée depuis le décor (4e essai : 3 réponses vides du générateur) ; une bande
  sombre en haut (58 rangées) et un rectangle sombre en bas sont recouverts par recopie d'herbe du même brut ;
- feuilles_lucioles_poses.png : planche sur magenta (6 feuilles qui tournoient, 2 rangées de lucioles).
Calques : sol complet, herbe, chemin, herbes hautes, rochers, arbres (houppiers, troncs, racines et rochers
pris dans les racines), profondeur (ouverture sombre au nord).
Animations, chacune sur son calque, boucles fermées :
- mare façon rivière Métano, couleurs Métano exactes, SANS liseré de rive (water_phases d'EWC2), 4 x 10 ticks ;
- scintillements Métano natifs, 4 x 10 ticks ;
- feuilles qui tombent (poses générées), 48 x 5 ticks ;
- lucioles (poses générées), 48 x 5 ticks.
Scène : PPCM(40, 240) = 240 ticks = 4 s.
Lancer : .venv/bin/python source/entree_mystifying_forest_sud_nord_v1/build.py
"""
from pathlib import Path
import hashlib, importlib.util, io, json, shutil, uuid, zipfile

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
RAW = HERE / 'bruts'
REF = R / 'Mystifying_Forest_entrance_TDS.png'
OUT = R / 'renders/entree_mystifying_forest_sud_nord_v1'
STAGE = R / '.cache/entree_mystifying_forest_sud_nord_v1/entree_mystifying_forest_sud_nord'
NAMESPACE = 'entree_mystifying_forest_sud_nord'
ASSET = 'emf1_entree_mystifying_forest'
PFX = 'EMF1'
W, H = 768, 576
SRC = (1200, 896)
WATER_PHASES, WATER_TICKS = 4, 10
ANIM_PHASES, ANIM_TICKS = 48, 5       # feuilles et lucioles : 48 x 5 = 240 ticks
LOOP_TICKS = 240
TUFT_MAX = 250
GEN = [
    {'file': 'decor_magenta.png', 'images': ['Mystifying_Forest_entrance_TDS.png'], 'prompt':
     'Use EXACTLY the same textures, palette and pixel-art style as the reference image (Pokemon Mystery Dungeon '
     'Explorers of Sky, Mystifying Forest entrance): same bright green grass with fine blades, same pinkish-brown dirt '
     'path with ragged grass edges, same huge dark green trees with round clumpy canopies and pale twisted exposed '
     'roots, same grey-green mossy boulders, same dark green tall grass patches and dark shadows. Make a NEW, larger '
     'top-down map. WIDE LANDSCAPE 4:3, zoomed out so the area feels vast. Layout: the player arrives at the SOUTH '
     '(bottom edge) on the dirt path; the path winds NORTH through a wide grassy clearing, up to a dark opening between '
     'huge trees at the top center where the forest becomes very dark (the dungeon entrance). Huge trees fill the left '
     'and right sides and the top corners; two or three trees stand inside the clearing; boulders along the path; dark '
     'tall grass patches. A small calm pond on the left side of the clearing, away from the path. IMPORTANT: the pond '
     'water surface is filled with flat pure magenta #FF00FF, no ripples. No characters, no text, no UI, no border.'},
    {'file': 'sol_complet.png', 'images': ['source/entree_mystifying_forest_sud_nord_v1/bruts/decor_magenta.png'], 'prompt':
     'Same image, same size and pixel-art style, but showing only the plain bright green grass ground everywhere (the '
     'trees, path, rocks, dark grass and pink pond are all removed and replaced by that same grass).',
     'essais': 'quatrieme essai ; les trois precedents (deux editions du decor, un texte + rip) ont rendu une reponse sans image'},
    {'file': 'feuilles_lucioles_poses.png', 'images': ['Mystifying_Forest_entrance_TDS.png'], 'prompt':
     'Sprite sheet on a flat pure magenta #FF00FF background, in EXACTLY the pixel-art style and colors of the reference '
     'image (Pokemon Mystery Dungeon Explorers of Sky forest). 2 rows x 6 columns of separate small sprites. Row 1: a '
     'single green leaf (same greens as the tree canopies) falling and fluttering, 6 rotation poses. Row 2: a small '
     'glowing firefly light mote (pale yellow-green glow), 6 poses from dim to bright to dim. Each sprite isolated and '
     'centered in its cell, wide magenta spacing, no overlap, no text, no grid lines.'},
]


def loadmod(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


V2 = loadmod('ewc2_build', R / 'source/entree_waterfall_cave_sud_nord_v2/build.py')   # eau sans liseré
V1 = V2.V1                                                                            # EWC1 : utilitaires génériques
JM, BM = V1.JM, V1.BM
assert (JM.W, JM.H, JM.SRC) == (W, H, SRC)
keep_large, place, cell_grid, close_ = V1.keep_large, V1.place, V1.cell_grid, V1.close_
down_class, down_full, rgba, resize_plane, quantize_group = V1.down_class, V1.down_full, V1.rgba, V1.resize_plane, V1.quantize_group
PAL = BM.PAL
PALETTE_GROUPS = {'terrain': (['sol_complet', 'herbe', 'chemin', 'herbes_hautes'], 96),
                  'arbres': (['arbres'], 40), 'rochers': (['rochers'], 16), 'profondeur': (['profondeur'], 12)}


def open_(m, it):
    """Ouverture à bord répliqué : border_value=1 dans binary_opening dilatait aussi un anneau plein au bord de l'image
    (puis fill_holes remplissait toute la carte)."""
    p = it + 1
    return nd.binary_opening(np.pad(m, p, mode='edge'), iterations=it)[p:-p, p:-p]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rgb(p):
    return np.array(Image.open(p).convert('RGB')).astype(int)


def repair_ground(f):
    """Sol complet : bande sombre du haut (rangées 0-57, + dégradé jusqu'à 75) et rectangle sombre du bas
    (x 480-719, y 838-895) recouverts par l'herbe du même brut (recopie sans retournement)."""
    f = f.copy(); lum = f @ [.299, .587, .114]
    top = int(np.nonzero((lum < 45).mean(1) > 0.5)[0].max()) + 19          # 57 + dégradé -> 76 rangées
    f[:top] = f[top:2 * top]
    ys, xs = np.nonzero(lum[400:] < 45); y0, y1, x0, x1 = ys.min() + 400, ys.max() + 1 + 400, xs.min(), xs.max() + 1
    f[y0 - 4:y1, x0:x1] = f[y0 - 4:y1, x0 - (x1 - x0):x0]
    return f, {'bande_haut_rangees': top, 'rectangle_bas': [int(x0), int(y0 - 4), int(x1), int(y1)]}


# ---------------------------------------------------------------- fidélité au rip (même classifieur des deux côtés)
def materials(a):
    r, g, b = a.transpose(2, 0, 1); lum = a @ [.299, .587, .114]; sat = a.max(2) - a.min(2)
    mag = (r > g * 1.5) & (b > g * 1.3) & (r > 150) & (b > 130)
    path = (r >= g - 4) & (r - b > 12) & (lum > 118) & (lum < 215) & ~mag
    grass = (g > r + 45) & (g > b + 40) & (lum > 100) & ~mag
    canopy = (b > 0.74 * g) & (g > r + 15) & (lum < 90) & (lum > 35) & ~mag
    rock = (sat < 50) & (lum > 110) & (g >= r) & ~path & ~mag
    return {'herbe': grass, 'chemin': path, 'feuillage_sombre': canopy, 'roche_racines': rock}


def fidelity(decor, ref):
    fr, fd = materials(ref), materials(decor); out = {}
    for k in fr:
        mr, md = ref[fr[k]].mean(0), decor[fd[k]].mean(0)
        out[k] = {'rip_rgb': [round(float(v), 1) for v in mr], 'decor_rgb': [round(float(v), 1) for v in md],
                  'distance': round(float(np.linalg.norm(mr - md)), 1)}
    return out


# ---------------------------------------------------------------- segmentation pleine résolution
def classify(a):
    r, g, b = a.transpose(2, 0, 1); lum = a @ [.299, .587, .114]; sat = a.max(2) - a.min(2)
    hh, ww = lum.shape; yy, xx = np.mgrid[:hh, :ww]
    mag = (r > g * 1.5) & (b > g * 1.3) & (r > 150) & (b > 130)
    water = nd.binary_dilation(mag, iterations=2)
    bg = nd.uniform_filter(b / np.maximum(g, 1), 11); L = nd.uniform_filter(lum, 11)
    # Ouverture sombre au nord (mesurée (11,30,29), lum 24), reliée au bord nord, dans la zone centrale.
    dark = (lum < 42) & (xx > 450) & (xx < 750) & (yy < 300)
    lab, n = nd.label(close_(dark, 3)); top = set(np.unique(lab[:6][dark[:6]])) - {0}
    opening = nd.binary_fill_holes(np.isin(lab, list(top)))
    # Chemin (mesuré (168,162,145)) : grande composante rose-brun.
    path = (r >= g - 4) & (r - b > 12) & (lum > 118) & (lum < 215) & ~water
    path = nd.binary_fill_holes(keep_large(open_(close_(path, 2), 1), 5000)) & ~water & ~opening
    # Clair et peu saturé : rochers, troncs, racines.
    pale = (sat < 60) & (lum > 95) & ~path & ~water & ~opening
    pale = keep_large(close_(pale, 1), 30) & ~path & ~water & ~opening
    # Herbe claire praticable (mesurée (78,149,81)) : critère RÉGIONAL (lum lissée > 92, b/g lissé < 0,64) pour garder
    # les ombres de brins ; composantes reliées au chemin ; coutures chemin/herbe (touffes des bords, 2-3 px) et petits
    # trous (< 600 px) comblés, sinon des lignes de cases bloquées coupaient le chemin de la clairière.
    clear = (L > 92) & (bg < 0.64) & ~path & ~water & ~opening & ~pale
    clear = open_(close_(clear, 2), 2)
    cl, _ = nd.label(clear); touch = set(np.unique(cl[nd.binary_dilation(path, iterations=4) & clear])) - {0}
    walk = keep_large(np.isin(cl, list(touch)), 5000)
    U = close_(walk | path, 3)
    holes = nd.binary_fill_holes(U) & ~U; hl, _ = nd.label(holes)
    sizes = nd.sum(holes, hl, range(1, hl.max() + 1)) if hl.max() else []
    small = np.isin(hl, [i + 1 for i, v in enumerate(sizes) if v < 600])
    walk = (U | small) & ~path & ~water & ~opening & ~pale
    nonwalk = ~(water | opening | path | walk)
    # Houppiers : dessous vert sombre bleuté (b/g lissé 11 px > 0,74) OU densité de reflets clairs (lum > 115 sur
    # 15 px > 0,12) hors clairière ; les herbes hautes (vert moyen uniforme) n'ont ni l'un ni l'autre.
    hd = nd.uniform_filter((lum > 115).astype(float), 15)
    canopy = nonwalk & ~pale & (((bg > 0.74) & (L < 110)) | (hd > 0.12))
    canopy = nd.binary_fill_holes(keep_large(open_(close_(canopy, 3), 3), 1500)) & nonwalk & ~pale
    # Rochers : blobs pâles épais (ouverture disque r=7) de teinte gris-vert (r-b moyen < 10) ; les blobs beiges
    # (r-b ~ 13-24 : troncs, racines) restent avec les arbres.
    yk, xk = np.mgrid[-7:8, -7:8]; disk = (xk ** 2 + yk ** 2) <= 49
    seed = nd.binary_opening(np.pad(pale, 9, mode='edge'), structure=disk)[9:-9, 9:-9]
    blobs = keep_large(nd.binary_dilation(seed, iterations=3) & pale, 250)
    bl, _ = nd.label(blobs); rocks = np.zeros_like(blobs)
    for i, sl in enumerate(nd.find_objects(bl), 1):
        comp = bl[sl] == i; px = a[sl][comp]
        if (px[:, 0] - px[:, 2]).mean() < 10:
            rocks[sl] |= comp
    rocks = nd.binary_fill_holes(close_(rocks, 3)) & nonwalk
    trees = (canopy | pale) & ~rocks & nonwalk
    # Pas de berge : la mare du décor n'a pas de rive distincte (123 px sombres au premier essai) ; herbe ou herbes hautes.
    tall = nonwalk & ~trees & ~rocks
    return dict(water=water, herbe=walk, chemin=path, herbes_hautes=tall, rochers=rocks, arbres=trees,
                profondeur=opening)


# ---------------------------------------------------------------- poses générées (planche sur magenta, composantes)
def sheet_poses(path):
    src = rgb(path); r, g, b = src.transpose(2, 0, 1)
    bg = ((r - g) > 40) & ((b - g) > 40)
    obj = nd.binary_dilation(~bg, iterations=6); lab, n = nd.label(obj)
    items = []
    for i, sl in enumerate(nd.find_objects(lab), 1):
        m = (lab[sl] == i) & ~bg[sl]
        if m.sum() < 30:
            continue
        ys, xs = np.nonzero(m); items.append(((sl[0].start + ys.mean()), (sl[1].start + xs.mean()), sl, m))
    items.sort(key=lambda t: (round(t[0] / 150), t[1]))                 # rangées (feuilles, lucioles, lucioles)
    rows = {}
    for it in items:
        rows.setdefault(round(it[0] / 150), []).append(it)
    rows = [sorted(v, key=lambda t: t[1]) for _, v in sorted(rows.items())]
    return src, bg, rows


def reduce_pose(src, bg, cy, cx, win, k, pal, cov_min):
    h, w = bg.shape; y0, x0 = int(cy) - win // 2, int(cx) - win // 2; n = win // k
    pad = np.zeros((win, win, 3)); pm = np.zeros((win, win), bool)
    sy0, sx0, sy1, sx1 = max(0, y0), max(0, x0), min(h, y0 + win), min(w, x0 + win)
    pad[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = src[sy0:sy1, sx0:sx1]
    pm[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = ~bg[sy0:sy1, sx0:sx1]
    blk = pm.reshape(n, k, n, k); cov = blk.mean((1, 3))
    col = (pad * pm[..., None]).reshape(n, k, n, k, 3).sum((1, 3)) / np.maximum(blk.sum((1, 3)), 1)[..., None]
    o = np.zeros((n, n, 4), 'uint8'); o[..., :3] = pal[((col[..., None, :] - pal[None, None]) ** 2).sum(-1).argmin(-1)]
    o[..., 3] = 255; o[cov < cov_min] = 0
    return o


def paste(frame, spr, cx, cy):
    hh, ww = spr.shape[:2]; y0, x0 = int(round(cy)) - hh // 2, int(round(cx)) - ww // 2
    ys0, xs0 = max(0, -y0), max(0, -x0); ys1, xs1 = min(hh, H - y0), min(ww, W - x0)
    if ys1 <= ys0 or xs1 <= xs0:
        return
    s = spr[ys0:ys1, xs0:xs1]; m = s[..., 3] > 0
    frame[y0 + ys0:y0 + ys1, x0 + xs0:x0 + xs1][m] = s[m]


# ---------------------------------------------------------------- ORA et Ground
def write_ora(path, layers):
    import xml.etree.ElementTree as ET
    root = ET.Element('image', w=str(W), h=str(H), name='Entree Mystifying Forest sud-nord V1 (EMF1)')
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
    o.update(Name={'DefaultText': 'Entree Mystifying Forest - sud vers nord (4:3)', 'LocalTexts': {}}, AssetName=ASSET,
             Released=False, TexSize=1, Music='', EdgeView=1, ViewCenter=None, ViewOffset={'X': 0, 'Y': 0},
             ActiveChar=None, Status={}, Layers=layers,
             Background={'$type': 'RogueEssence.Dungeon.LayeredBG, RogueEssence', 'Layers': []},
             Comment='PMDO 0.8.12. Rendu genere 4:3 reference sur le rip Mystifying Forest ; mare facon Metano sans '
                     'liseré (couleurs Metano exactes), scintillements Metano natifs, feuilles et lucioles generees. '
                     'Collisions de base a verifier. Seuil non raccorde. Biome choisi par l agent, a confirmer.')
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
  <Name>Entree Mystifying Forest sud-nord 4:3 - Atelier 0.8.12</Name>
  <Author>meromoonmeri</Author>
  <Description>Projet d'edition : entree de foret generee au format 4:3 (ref. rip Mystifying Forest), mare facon Metano, feuilles et lucioles animees. Pas une aventure jouable.</Description>
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


# ---------------------------------------------------------------- animations créées (émetteurs, trajectoires)
LEAF_FALL = 30                                # phases de chute sur 48 : 18 phases de repos


def leaf_frames(poses, starts, clip, ts=range(ANIM_PHASES)):
    """ts : phases à calculer (le test calcule aussi la phase 48 pour vérifier qu'elle égale la phase 0)."""
    frames = [np.zeros((H, W, 4), 'uint8') for _ in ts]
    for cx, cy, off, drift in starts:
        for i, t in enumerate(ts):
            u = (t + off) % ANIM_PHASES
            if u >= LEAF_FALL:
                continue
            y = cy + u * 1.25                                              # ~37 px de chute, balancement +/- 6 px
            x = cx + drift * u * 0.25 + 6 * np.sin(2 * np.pi * u / 15)
            paste(frames[i], poses[(u // 2) % len(poses)], x, y)
    for f in frames:
        f[~clip] = 0
    return frames


FLY_PULSE = [0, 1, 2, 3, 3, 2, 3, 4, 5, -1, -1, -1]   # 12 phases : s'allume, brille, s'éteint, repos


def firefly_frames(poses, spots, ts=range(ANIM_PHASES)):
    frames = [np.zeros((H, W, 4), 'uint8') for _ in ts]
    for cx, cy, off, rad in spots:
        for i, t in enumerate(ts):
            p = FLY_PULSE[(t + off) % len(FLY_PULSE)]
            if p < 0:
                continue
            ph = 2 * np.pi * (t + off) / ANIM_PHASES                      # boucle de Lissajous fermée sur 48 phases
            paste(frames[i], poses[p], cx + rad * np.sin(ph), cy + 0.6 * rad * np.sin(2 * ph))
    return frames


# ---------------------------------------------------------------- main
def build():
    gfx = loadmod('pmdo_codec', R / 'source/pmdo_cote/build.py')
    tools = loadmod('index_tools', R / 'source/pmdo_cote/INSTALLER.py')
    v1 = loadmod('esn1', R / 'source/entree_sud_nord_generee_v1/build.py')
    ANIMS = ['eau', 'scintillements', 'feuilles', 'lucioles']
    if OUT.exists():
        for d in ['calques', 'animation', 'poses', 'masques', 'review']:
            shutil.rmtree(OUT / d, ignore_errors=True)
    for d in ['calques', 'poses', 'masques', 'review'] + [f'animation/{x}' for x in ANIMS]:
        (OUT / d).mkdir(parents=True, exist_ok=True)
    a = rgb(RAW / 'decor_magenta.png'); f0 = rgb(RAW / 'sol_complet.png'); ref = rgb(REF)
    assert a.shape[:2] == f0.shape[:2] == (SRC[1], SRC[0])
    f, repair = repair_ground(f0)
    m = classify(a)
    order = ['water', 'profondeur', 'chemin', 'rochers', 'arbres', 'herbes_hautes', 'herbe']
    ex, cols = down_class(a, m, order)
    water = ex['water']
    static = ['herbe', 'chemin', 'herbes_hautes', 'rochers', 'arbres', 'profondeur']
    layers = {'sol_complet': rgba(down_full(f), ~water)}
    for k in static:
        layers[k] = rgba(cols[k], ex[k])
    q = {}
    for keys, n in PALETTE_GROUPS.values():
        q.update(quantize_group({k: layers[k] for k in keys}, n))
    layers = q
    for k, v in ex.items():
        Image.fromarray((v * 255).astype('uint8')).save(OUT / 'masques' / f'{PFX}_masque_{k}.png')
    land = np.zeros((H, W), bool)
    for k in static:
        land |= layers[k][..., 3] == 255
    visible = water & ~land
    wf, dist = V2.water_phases(water, visible)                          # Métano exactes, sans liseré de rive
    fams = BM.sparkle_families(); taken = np.zeros((H, W), bool)
    sf = [np.zeros((H, W, 4), 'uint8') for _ in range(WATER_PHASES)]; sparkles = []
    for fi, (name, frames) in enumerate(fams.items()):
        hh, ww = frames[0].shape[:2]
        for (y, x) in place(visible & (dist > 4), (hh, ww), 2, 61 + fi, taken, core=8):
            sparkles.append({'famille': name, 'xy': [x, y]})
            for t in range(WATER_PHASES):
                mm = frames[t][..., 3] > 0; sf[t][y:y+hh, x:x+ww][mm] = frames[t][mm]
    for arr in sf:
        arr[~visible] = 0
    # Poses générées : feuilles (palette des arbres), lucioles (couleurs propres réduites à 8).
    src, bgm, rows = sheet_poses(RAW / 'feuilles_lucioles_poses.png')
    assert len(rows) >= 2 and len(rows[0]) == 6 and len(rows[1]) == 6, [len(r_) for r_ in rows]
    tree_pal = np.unique(layers['arbres'][ex['arbres']][:, :3], axis=0).astype(float)
    leaves = [reduce_pose(src, bgm, cy, cx, 120, 12, tree_pal, 0.3) for cy, cx, _, _ in rows[0]]
    fly_px = np.concatenate([src[sl][mm] for _, _, sl, mm in rows[1]])
    qf = Image.fromarray(fly_px.reshape(-1, 1, 3).astype('uint8')).quantize(colors=8, method=Image.Quantize.MEDIANCUT)
    fly_pal = np.array(qf.getpalette()[:24], float).reshape(-1, 3)
    flies = [reduce_pose(src, bgm, cy, cx, 72, 12, fly_pal, 0.3) for cy, cx, _, _ in rows[1]]
    for i, p in enumerate(leaves):
        Image.fromarray(p).save(OUT / 'poses' / f'{PFX}_feuille_{i}.png')
    for i, p in enumerate(flies):
        Image.fromarray(p).save(OUT / 'poses' / f'{PFX}_luciole_{i}.png')
    # Feuilles : départs sous le bord inférieur des houppiers qui dominent l'herbe praticable ou le chemin.
    walk_px = (layers['herbe'][..., 3] == 255) | (layers['chemin'][..., 3] == 255)
    can = ex['arbres']; edge = can & ~nd.binary_erosion(can, iterations=2) & np.roll(walk_px, -6, axis=0)
    rng = np.random.default_rng(5); cand = np.argwhere(edge[40:H - 70, 30:W - 30]) + [40, 30]
    starts, used = [], []
    for y, x in cand[rng.permutation(len(cand))]:
        if all(abs(x - ux) > 60 or abs(y - uy) > 60 for uy, ux in used):
            used.append((y, x)); starts.append((int(x), int(y) - 4, (len(starts) * 8) % ANIM_PHASES, 1 if len(starts) % 2 else -1))
        if len(starts) == 8:
            break
    feuilles = leaf_frames(leaves, starts, np.ones((H, W), bool))
    # Lucioles : zones sombres proches de la clairière (orée, herbes hautes, ouverture).
    darkish = (ex['herbes_hautes'] | ex['profondeur'] | (ex['arbres'] & nd.binary_dilation(walk_px, iterations=10)))
    darkish &= ~nd.binary_dilation(ex['water'], iterations=4)
    cand = np.argwhere(darkish[24:H - 24, 24:W - 24]) + [24, 24]; spots, used = [], []
    for y, x in cand[np.random.default_rng(8).permutation(len(cand))]:
        if all(abs(x - ux) > 48 or abs(y - uy) > 48 for uy, ux in used):
            used.append((y, x)); spots.append((int(x), int(y), (len(spots) * 5) % ANIM_PHASES, 4 + (len(spots) % 3) * 2))
        if len(spots) == 14:
            break
    lucioles = firefly_frames(flies, spots)
    # Exports
    anim = {'eau': (wf, WATER_TICKS), 'scintillements': (sf, WATER_TICKS), 'feuilles': (feuilles, ANIM_TICKS),
            'lucioles': (lucioles, ANIM_TICKS)}
    order_names = ['eau', 'scintillements', 'sol_complet'] + static + ['feuilles', 'lucioles']
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
    # Collisions : herbe de la clairière + chemin.
    blocked = cell_grid(~walk_px); gh_, gw_ = blocked.shape
    pth = layers['chemin'][..., 3] == 255
    pxs = np.nonzero(pth[H - 8])[0]; med = int(np.median(pxs)) // 8
    ecol = min((c for c in range(gw_ - 1) if not blocked[gh_ - 2:, c:c + 2].any()), key=lambda c: abs(c - med))
    entry_px = [ecol * 8, H - 16]
    py, px_ = np.nonzero(pth); top_y = int(py.min()); tx = int(np.median(px_[py < top_y + 8]))
    threshold_px = [tx // 8 * 8 - 8, top_y // 8 * 8]
    while blocked[threshold_px[1] // 8:threshold_px[1] // 8 + 2, threshold_px[0] // 8:threshold_px[0] // 8 + 2].any():
        threshold_px[1] += 8
    ok, explored = v1.reachable(blocked, (entry_px[1] // 8, entry_px[0] // 8), (threshold_px[1] // 8, threshold_px[0] // 8))
    assert ok, 'pas de chemin 16x16'

    def scene(tick):
        im = Image.new('RGBA', (W, H))
        for _, frames, ticks in stack_named:
            im.alpha_composite(Image.fromarray(frames[(tick // ticks) % len(frames)]))
        return im
    step = 5
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
    sheet = Image.new('RGBA', (6 * 68, 2 * 68), (60, 110, 60, 255))
    for r_, seq in enumerate((leaves, flies)):
        for i, p in enumerate(seq):
            im = Image.fromarray(p); sc = 60 // max(im.size)
            sheet.alpha_composite(im.resize((im.width * sc, im.height * sc), Image.Resampling.NEAREST), (i * 68 + 4, r_ * 68 + 4))
    sheet.save(OUT / 'review' / f'{PFX}_planche_poses.png')
    write_ora(OUT / f'{PFX}_entree_mystifying_forest_calques.ora',
              {f'{i:02d}_{t}' + ('_f00' if len(fr) > 1 else ''): fr[0] for i, (t, fr, _) in enumerate(stack_named)})
    counts = ground_project([(t.replace('_', ' ') + (f' {len(fr)} phases' if len(fr) > 1 else ''), fr, tk)
                             for t, fr, tk in stack_named], blocked, entry_px, threshold_px, gfx, tools)
    fid = fidelity(a, ref)
    final_fid = {}
    for k, nm in (('herbe', 'herbe'), ('chemin', 'chemin'), ('feuillage_sombre', 'arbres'), ('roche_racines', 'rochers')):
        lay = layers[nm]; px = lay[lay[..., 3] == 255][:, :3].astype(float)
        sel = materials(px.reshape(-1, 1, 3))[k][:, 0]
        px = px[sel] if sel.sum() > 50 else px
        final_fid[k] = {'calque': nm, 'rgb': [round(float(v), 1) for v in px.mean(0)],
                        'distance_rip': round(float(np.linalg.norm(px.mean(0) - np.array(fid[k]['rip_rgb']))), 1)}
    manifest = {
        'lot': 'entree_mystifying_forest_sud_nord_v1', 'prefix': PFX, 'format': '4:3 vaste', 'size_px': [W, H],
        'grid_8px': [W // 8, H // 8], 'base': 'branche de session (EWC2) ; aucun emprunt aux branches soeurs',
        'biome': 'Mystifying Forest, choisi par l agent : a confirmer',
        'method': 'textures canoniques = rendu genere REFERENCE : rip passe au generateur ; decor complet sur magenta '
                  '(mare = magenta), herbe complete editee depuis le decor, planche feuilles/lucioles sur magenta',
        'reference_da': {'file': REF.name, 'sha256': sha(REF), 'titre': 'Entree de Mystifying Forest (PMD Explorers)'},
        'generation': GEN,
        'raw_inputs': [{'file': f'source/entree_mystifying_forest_sud_nord_v1/bruts/{g["file"]}', 'sha256': sha(RAW / g['file']),
                        'size': list(Image.open(RAW / g['file']).size)} for g in GEN],
        'sol_complet_reparation': repair,
        'fidelite_rip': {'methode': 'moyenne RGB par matiere, meme classifieur pixel sur le rip et sur le brut ; distance euclidienne',
                         'brut': fid, 'calques_finaux': final_fid},
        'normalization': {'scale': JM.SCALE, 'scaled': [JM.SCALED_W, H], 'crop_x': [JM.CROP_X, JM.SCALED_W - W - JM.CROP_X],
                          'methode': 'moyenne ponderee par classe (BOX), attribution exclusive par poids maximal',
                          'palettes': {g: {'calques': k, 'couleurs': n} for g, (k, n) in PALETTE_GROUPS.items()}},
        'segmentation': 'eau = magenta dilate 2 px ; profondeur = sombre (lum<42) relie au bord nord, zone centrale ; chemin '
                        '= rose-brun (r>=g-4, r-b>12, 118<lum<215), grande composante ; houppiers = b/g lisse 11 px > 0,74 '
                        'et lum lissee < 110 ; herbes hautes = b/g 0,62-0,74 et lum lissee < 100 ; rochers = composantes '
                        'pales epaisses (EDT >= 6) sans contact avec un houppier ; arbres = houppiers + troncs, racines et '
                        'rochers pris dedans ; pas de berge (la mare n a pas de rive distincte) ; herbe praticable = herbe claire '
                        '(critere regional) reliee au chemin, coutures et petits trous combles ; le reste -> herbes hautes',
        'layers': layer_list,
        'water': {'phases': WATER_PHASES, 'frame_length_ticks': WATER_TICKS,
                  'couleurs': {k: list(v) for k, v in PAL.items() if k != 'clair'},
                  'modele': 'structure et cadence riviere Metano, couleurs Metano EXACTES, sans liseré de rive (water_phases d EWC2)',
                  'origine': 'pixels recalcules, pas de tuiles natives'},
        'sparkles': {'source': 'source/eau_metano/natifs/Metano_Town_River_Sparkles.tile', 'placements': sparkles,
                     'origine': 'pixels et couleurs Metano NATIFS inchanges (aplat de surface retire)'},
        'feuilles': {'poses': len(leaves), 'taille_px': list(leaves[0].shape[:2]), 'reduction': 'fenetre 120 px -> 10 px (x1/12)',
                     'palette': 'couleurs du calque arbres', 'departs': [list(s) for s in starts],
                     'chute_phases': LEAF_FALL, 'phases': ANIM_PHASES, 'frame_length_ticks': ANIM_TICKS,
                     'origine': 'dessin GENERE ; trajectoires (chute ~37 px, balancement +/- 6 px) et chronologie creees par nous'},
        'lucioles': {'poses': len(flies), 'taille_px': list(flies[0].shape[:2]), 'reduction': 'fenetre 72 px -> 6 px (x1/12)',
                     'palette': '8 couleurs tirees des lucioles generees', 'pulsation': FLY_PULSE,
                     'points': [list(s) for s in spots], 'phases': ANIM_PHASES, 'frame_length_ticks': ANIM_TICKS,
                     'origine': 'dessin GENERE ; boucles de Lissajous et pulsation creees par nous'},
        'shadows': 'pas de calque d ombres separe : les zones sombres du rendu sont des houppiers ou des herbes hautes '
                   '(aucune ombre portee separable) ; l ouverture sombre forme le calque profondeur',
        'scene_loop_ticks': LOOP_TICKS,
        'access': {'entry_px': entry_px, 'threshold_px': threshold_px, 'path_found_16x16': ok, 'cells_explored': explored,
                   'blocked_cells': int(blocked.sum()), 'total_cells': int(blocked.size), 'walkable_cells': int((~blocked).sum()),
                   'rule': 'case bloquee si > 25 % hors herbe de la clairiere et chemin',
                   'seuil': 'bout nord du chemin, a l entree de l ouverture sombre'},
        'pmdo': {'target': '0.8.12', 'asset': ASSET, 'namespace': NAMESPACE, 'tiles_per_bank': counts, 'banks': list(counts),
                 'runtime_tested': False, 'warp': 'aucun'},
        'art_approved': False,
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    shutil.copyfile(OUT / 'manifest.json', STAGE / 'manifest.json')
    print(json.dumps({'sparkles': len(sparkles), 'entry': entry_px, 'threshold': threshold_px, 'blocked': int(blocked.sum()),
                      'walkable': int((~blocked).sum()), 'leaves': len(starts), 'flies': len(spots), 'repair': repair,
                      'fidelite': {k: v['distance'] for k, v in fid.items()},
                      'final': {k: v['distance_rip'] for k, v in final_fid.items()}, 'tiles': sum(counts.values())}, indent=1))


if __name__ == '__main__':
    build()
