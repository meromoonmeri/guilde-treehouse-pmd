"""Entrée Underground Lake sud -> nord V1 (EUL1) — format 4:3 vaste (768 x 576 px, 96 x 72 cases).

Demande : « go carte suivante choisis ! » (après EWC3). Carte suivante de la série, biome choisi par l'agent sur
demande de l'utilisateur : Underground Lake, référence `Underground_Lake_shore_TDS.png` (PMD Explorers), jamais
utilisée comme référence principale, toutes branches confondues. Méthode « textures canoniques » = rendu généré
RÉFÉRENCÉ (rip passé au générateur en images=) :
- decor_magenta.png : décor complet 4:3 (1200 x 896), l'eau du lac en magenta ;
- sol_complet.png : édité depuis le décor ; le générateur a retiré lac, piliers, stalagmites et bouche, mais a GARDÉ
  les parois (recalées au pixel près) : il sert de sol sous tout et de témoin pour isoler les piliers ;
- gouttes_ronds_poses.png : planche sur magenta (gouttes, éclaboussures, ronds dans l'eau).
Calques : sol complet, sable, ombres au pied des parois, berge du lac, parois, piliers et stalagmites, entrée sombre.
Animations, chacune sur son calque, boucles fermées :
- lac façon rivière Métano (structure, cadence 4 x 10), couleurs EXACTES du rip, sans liseré clair de rive ;
- lueur du lac : anneaux aux 9 couleurs exactes du rip qui respirent, 12 x 10 ticks (animation créée) ;
- scintillements Métano natifs, 4 x 10 ticks ;
- gouttes qui tombent du plafond et ronds dans l'eau (poses générées), 24 x 5 ticks.
Scène : PPCM(40, 120, 120) = 120 ticks = 2 s.
Lancer : .venv/bin/python source/entree_underground_lake_sud_nord_v1/build.py
"""
from pathlib import Path
import hashlib, importlib.util, io, json, shutil, uuid, zipfile

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
RAW = HERE / 'bruts'
REF = R / 'Underground_Lake_shore_TDS.png'
OUT = R / 'renders/entree_underground_lake_sud_nord_v1'
STAGE = R / '.cache/entree_underground_lake_sud_nord_v1/entree_underground_lake_sud_nord'
NAMESPACE = 'entree_underground_lake_sud_nord'
ASSET = 'eul1_entree_underground_lake'
PFX = 'EUL1'
W, H = 768, 576
SRC = (1200, 896)
WATER_PHASES, WATER_TICKS = 4, 10
GLOW_PHASES, GLOW_TICKS = 12, 10          # lueur : 12 x 10 = 120 ticks
DROP_PHASES, DROP_TICKS = 24, 5           # gouttes : 24 x 5 = 120 ticks
LOOP_TICKS = 120
GEN = [
    {'file': 'decor_magenta.png', 'images': ['Underground_Lake_shore_TDS.png'], 'prompt':
     'Use EXACTLY the same textures, palette and pixel-art style as the reference image (Pokemon Mystery Dungeon '
     'Explorers of Sky, Underground Lake shore): same pale yellow sand with soft stippled texture, same olive-khaki '
     'bumpy cave walls made of stacked rounded rock lumps with dark gaps, same tall rock pillars rising from the water, '
     'same small pointed stalagmites standing in the water. Make a NEW, larger top-down map. WIDE LANDSCAPE 4:3, zoomed '
     'out so the cave feels vast. Layout: the player arrives at the SOUTH (bottom edge center) on a sand path between '
     'bumpy rock walls; the sand opens into a wide beach; NORTH of the beach a large underground lake spans the width; '
     'a natural sand causeway crosses the lake from the beach NORTH up to a dark cave tunnel opening in the rock wall at '
     'the top center, and the causeway reaches the opening dry, no water in front of it. Two tall rock pillars stand in '
     'the lake on each side of the causeway, a few small stalagmites dot the lake, rock walls fill the left and right '
     'sides and the top. IMPORTANT: the whole lake water surface is filled with flat pure magenta #FF00FF, no ripples, '
     'no glow, no reflections. No characters, no text, no UI, no border.'},
    {'file': 'sol_complet.png', 'images': ['source/entree_underground_lake_sud_nord_v1/bruts/decor_magenta.png'], 'prompt':
     'Same image, same framing and pixel-art style, but only plain pale yellow sand ground everywhere, nothing else.',
     'essais': 'deuxieme essai ; le premier (prompt plus long) a rendu une reponse sans image. Le generateur a garde '
               'les parois : elles restent sous le calque parois'},
    {'file': 'gouttes_ronds_poses.png', 'images': ['Underground_Lake_shore_TDS.png'], 'prompt':
     'Pixel-art sprite sheet on a flat pure magenta #FF00FF background, same style and colors as the reference. 2 rows '
     'of 6 small separate sprites. Row 1: a pale blue water drop falling then splashing. Row 2: a thin pale blue ripple '
     'ring growing from small to large. Sprites well separated, no text.',
     'essais': 'deuxieme essai ; le premier (prompt plus long) a rendu une reponse sans image. La grille n est pas '
               'respectee (4 rangees) : poses choisies a la main par fenetre'},
]
# Couleurs EXACTES du rip (mesurées : 69 couleurs). Eau : aplat (39,39,95) ; bande de rive (55,55,111) ; accent de
# frange (63,63,119). Le liseré clair du rip contre le sable ((119,127,175), (167,167,223)) n'est PAS repris (retour
# EWC1 : pas de petits traits blancs au bord des rives).
WPAL = {'surface': (39, 39, 95), 'bande': (55, 55, 111), 'accent': (63, 63, 119)}
# Lueur : cœur puis 8 anneaux, du plus clair au plus sombre (ordre spatial vérifié sur le rip, du nord vers le sud).
GLOW = [(31, 223, 167), (31, 207, 167), (31, 183, 167), (31, 151, 159), (39, 135, 151), (39, 119, 135), (39, 95, 135),
        (39, 79, 119), (39, 63, 111)]
GLOW_RING_PX = 4                  # anneaux du rip : ~5 px ; décor ~0,8 x l'échelle du rip
GLOW_BREATH, GLOW_WOBBLE = 0.04, 0.02
# Planche : fenêtres (cy, cx, côté) choisies à la main (la grille demandée n'est pas respectée), réduction x1/8.
POSE_K = 8
POSE_COV = 0.3                    # couverture mini d'un bloc 8 x 8 ; 0,12-0,2 épaississait les ronds à 2 px et bouchait le petit
POSE_WIN = {'goutte': (96, 86, 96), 'goutte_etiree': (125, 603, 96), 'impact': (130, 874, 128),
            'eclaboussure': (412, 138, 176), 'rond_0': (608, 156, 32), 'rond_1': (608, 495, 64),
            'rond_2': (607, 847, 144), 'rond_3': (869, 156, 192), 'rond_4': (865, 495, 272), 'rond_5': (863, 847, 288)}
# Chronologie d'une goutte (24 phases) : chute (décalage vertical), impact, éclaboussure, ronds qui grandissent, repos.
DROP_SEQ = ([('goutte', -16), ('goutte', -12), ('goutte', -8), ('goutte_etiree', -4), ('impact', 0), ('eclaboussure', 0),
             ('rond_0', 0), ('rond_1', 0), ('rond_1', 0), ('rond_2', 0), ('rond_2', 0), ('rond_3', 0), ('rond_3', 0),
             ('rond_4', 0), ('rond_4', 0), ('rond_5', 0), ('rond_5', 0)] + [None] * 7)
assert len(DROP_SEQ) == DROP_PHASES


def loadmod(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


V2 = loadmod('ewc2_build', R / 'source/entree_waterfall_cave_sud_nord_v2/build.py')
V1 = V2.V1                                                                            # EWC1 : utilitaires génériques
JM, BM = V1.JM, V1.BM
assert (JM.W, JM.H, JM.SRC) == (W, H, SRC)
keep_large, place, cell_grid, close_ = V1.keep_large, V1.place, V1.cell_grid, V1.close_
down_class, down_full, rgba, resize_plane, quantize_group = V1.down_class, V1.down_full, V1.rgba, V1.resize_plane, V1.quantize_group
PALETTE_GROUPS = {'terrain': (['sol_complet', 'sable', 'ombres', 'berge'], 96),
                  'roche': (['roche', 'piliers'], 64), 'profondeur': (['profondeur'], 12)}
STATIC = ['sable', 'ombres', 'berge', 'roche', 'piliers', 'profondeur']


def open_(m, it):
    p = it + 1
    return nd.binary_opening(np.pad(m, p, mode='edge'), iterations=it)[p:-p, p:-p]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rgb(p):
    return np.array(Image.open(p).convert('RGB')).astype(int)


# ---------------------------------------------------------------- fidélité au rip (même classifieur des deux côtés)
def materials(a):
    r, g, b = a.transpose(2, 0, 1); lum = a @ [.299, .587, .114]; sat = a.max(2) - a.min(2)
    mag = (r - g > 60) & (b - g > 60)
    sand = (r > 150) & (r - b > 50) & (lum > 140) & ~mag
    rock = (r >= b + 15) & (g >= b + 10) & (lum > 40) & (lum < 175) & (sat < 90) & ~sand & ~mag
    return {'sable': sand, 'roche': rock}


def fidelity(decor, ref):
    fr, fd = materials(ref), materials(decor); out = {}
    for k in fr:
        mr, md = ref[fr[k]].mean(0), decor[fd[k]].mean(0)
        out[k] = {'rip_rgb': [round(float(v), 1) for v in mr], 'decor_rgb': [round(float(v), 1) for v in md],
                  'distance': round(float(np.linalg.norm(mr - md)), 1)}
    return out


# ---------------------------------------------------------------- segmentation pleine résolution
def classify(a, f):
    """a : décor, f : sol complet (parois recalées (0, 0) : écart 3,8 contre 7,1 à 1 px)."""
    r, g, b = a.transpose(2, 0, 1); lum = a @ [.299, .587, .114]
    hh, ww = lum.shape; yy, xx = np.mgrid[:hh, :ww]
    # Eau : magenta et sa frange violette antialiasée (r-g et b-g > 60), dilatée de 2 px.
    water = nd.binary_dilation((r - g > 60) & (b - g > 60), iterations=2)
    # Entrée sombre (mesurée lum ~30) : composante sombre qui contient le haut-centre du décor.
    dark = (lum < 48) & (yy < 260) & (xx > 450) & (xx < 750)
    lab, n = nd.label(close_(dark, 2)); sizes = nd.sum(dark, lab, range(1, n + 1))
    box = np.zeros_like(dark); box[40:160, 540:660] = True
    cand = [i + 1 for i in range(n) if (lab[box] == i + 1).any()]
    opening = nd.binary_fill_holes(lab == max(cand, key=lambda i: sizes[i - 1]))
    # Sable (mesuré (225,196,120)) : grande composante jaune claire, petits trous comblés.
    sandish = (r > 150) & (r - b > 50) & (lum > 140) & ~water & ~opening
    sand = keep_large(open_(close_(sandish, 2), 1), 20000)
    holes = nd.binary_fill_holes(sand) & ~sand; hl, _ = nd.label(holes)
    hs = nd.sum(holes, hl, range(1, hl.max() + 1)) if hl.max() else []
    sand = (sand | np.isin(hl, [i + 1 for i, v in enumerate(hs) if v < 300])) & ~water & ~opening
    rockish = ~sand & ~water & ~opening
    # Ombres : le sable s'assombrit au pied des parois (lum 159 à 0-3 px, 173 à 3-6, 185 à 6-10, 196 au-delà de 15).
    Ls = nd.uniform_filter(lum, 5); dr = nd.distance_transform_edt(~rockish)
    shade = sand & (dr <= 16) & (Ls < 187)
    shade = keep_large(close_(shade, 1), 60) & sand
    # Berge : rebord entre le lac et le sable (<= 14 px de l'eau ET du sable).
    dw = nd.distance_transform_edt(~water); ds = nd.distance_transform_edt(~sand)
    berge = rockish & (dw <= 14) & (ds <= 14)
    # Piliers et stalagmites : roche du décor là où le sol complet diffère (le générateur les a retirés, parois gardées).
    diff = nd.uniform_filter(np.abs(a - f).mean(2), 5)
    rest = rockish & ~berge
    pil = rest & (diff > 20) & ~nd.binary_dilation(opening, iterations=40)
    pil = nd.binary_fill_holes(keep_large(open_(close_(pil, 2), 1), 150)) & rest
    roche = rest & ~pil
    return dict(water=water, profondeur=opening, sable=sand & ~shade, ombres=shade, berge=berge, piliers=pil,
                roche=roche), {'ecart_parois': round(float(diff[roche].mean()), 2),
                               'ecart_piliers': round(float(diff[pil].mean()), 2)}


# ---------------------------------------------------------------- eau et lueur
def lake_water(water, visible):
    """Structure de water_phases d'EWC2 (bande, frange dentelée, accent, aplat ; onde voyageuse ; 4 x 10 ; aucun
    liseré clair), couleurs exactes du rip : la bande sert aussi d'intermédiaire."""
    d = nd.distance_transform_edt(visible); yy, xx = np.mgrid[:H, :W]
    jag = nd.gaussian_filter(np.random.default_rng(9).random((H, W)), 1.0); jag = (jag - jag.min()) / np.ptp(jag)
    frames = []
    for t in range(WATER_PHASES):
        ph = 2 * np.pi * t / WATER_PHASES
        n = 0.6 * np.sin(yy * 0.23 + xx * 0.08 - ph) + 0.4 * np.sin(yy * 0.09 - xx * 0.19 + 1.3 - ph)
        T = 4.5 + 1.1 * n; jr = np.roll(jag, t * 2, axis=0); fringe = T + 0.6 + 2.6 * jr
        a = np.zeros((H, W, 4), 'uint8'); a[..., 3] = 255; a[..., :3] = WPAL['surface']
        a[d <= fringe] = (*WPAL['bande'], 255)
        a[(d <= fringe) & (jr > 0.62)] = (*WPAL['accent'], 255)
        a[d <= T] = (*WPAL['bande'], 255)
        a[~water] = 0; a[water & ~visible] = (*WPAL['bande'], 255)
        frames.append(a)
    return frames, d


def glow_frames(visible, centres, ts=range(GLOW_PHASES)):
    """Cœur elliptique qui respire (+/- 4 %) avec une ondulation qui tourne (5 lobes), puis 8 anneaux de 4 px
    (distance au cœur) ; dessiné seulement sur l'eau visible. Période 12 phases : la phase 12 égale la phase 0."""
    yy, xx = np.mgrid[:H, :W]; frames = []
    for t in ts:
        ph = 2 * np.pi * t / GLOW_PHASES; a = np.zeros((H, W, 4), 'uint8')
        for cx, cy, rx, ry in centres:
            dx, dy = (xx - cx) / rx, (yy - cy) / ry
            rho = np.hypot(dx, dy) * (1 + GLOW_WOBBLE * np.sin(5 * np.arctan2(dy, dx) - ph)) / (1 + GLOW_BREATH * np.sin(ph))
            core = rho < 1
            ring = np.ceil(nd.distance_transform_edt(~core) / GLOW_RING_PX).astype(int)      # 0 = cœur, 1..8 anneaux
            for i, c in enumerate(GLOW):
                a[visible & (ring == i)] = (*c, 255)
        frames.append(a)
    return frames


# ---------------------------------------------------------------- poses générées (planche sur magenta)
def sheet_poses(path):
    src = rgb(path); r, g, b = src.transpose(2, 0, 1)
    bg = ((r - g) > 40) & ((b - g) > 40)
    px = np.concatenate([src[cy - s // 2:cy + s // 2, cx - s // 2:cx + s // 2][~bg[cy - s // 2:cy + s // 2, cx - s // 2:cx + s // 2]]
                         for cy, cx, s in POSE_WIN.values()])
    q = Image.fromarray(px.reshape(-1, 1, 3).astype('uint8')).quantize(colors=8, method=Image.Quantize.MEDIANCUT)
    pal = np.array(q.getpalette()[:24], float).reshape(-1, 3)
    poses = {}
    for name, (cy, cx, s) in POSE_WIN.items():
        poses[name] = reduce_pose(src, bg, cy, cx, s, POSE_K, pal, POSE_COV)
    return poses, pal


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


def paste(frame, spr, cx, cy, clip=None):
    hh, ww = spr.shape[:2]; y0, x0 = int(round(cy)) - hh // 2, int(round(cx)) - ww // 2
    ys0, xs0 = max(0, -y0), max(0, -x0); ys1, xs1 = min(hh, H - y0), min(ww, W - x0)
    if ys1 <= ys0 or xs1 <= xs0:
        return
    s = spr[ys0:ys1, xs0:xs1]; m = s[..., 3] > 0
    if clip is not None:
        m &= clip[y0 + ys0:y0 + ys1, x0 + xs0:x0 + xs1]
    frame[y0 + ys0:y0 + ys1, x0 + xs0:x0 + xs1][m] = s[m]


def drop_frames(poses, emitters, visible, ts=range(DROP_PHASES)):
    """La goutte qui tombe n'est pas détourée (sa trajectoire est choisie au-dessus de l'eau) ; impact, éclaboussure
    et ronds sont détourés à l'eau visible."""
    frames = [np.zeros((H, W, 4), 'uint8') for _ in ts]
    for cx, cy, off in emitters:
        for i, t in enumerate(ts):
            st = DROP_SEQ[(t + off) % DROP_PHASES]
            if st is None:
                continue
            name, dy = st
            paste(frames[i], poses[name], cx, cy + dy, None if name.startswith('goutte') else visible)
    return frames


# ---------------------------------------------------------------- ORA et Ground
def write_ora(path, layers):
    import xml.etree.ElementTree as ET
    root = ET.Element('image', w=str(W), h=str(H), name='Entree Underground Lake sud-nord V1 (EUL1)')
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
    o.update(Name={'DefaultText': 'Entree Underground Lake - sud vers nord (4:3)', 'LocalTexts': {}}, AssetName=ASSET,
             Released=False, TexSize=1, Music='', EdgeView=1, ViewCenter=None, ViewOffset={'X': 0, 'Y': 0},
             ActiveChar=None, Status={}, Layers=layers,
             Background={'$type': 'RogueEssence.Dungeon.LayeredBG, RogueEssence', 'Layers': []},
             Comment='PMDO 0.8.12. Rendu genere 4:3 reference sur le rip Underground Lake ; lac facon Metano aux '
                     'couleurs exactes du rip sans liseré clair, lueur du lac animee, scintillements Metano natifs, '
                     'gouttes et ronds generes. Collisions de base a verifier. Seuil non raccorde. Biome choisi par l agent.')
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
  <Name>Entree Underground Lake sud-nord 4:3 - Atelier 0.8.12</Name>
  <Author>meromoonmeri</Author>
  <Description>Projet d'edition : entree de grotte generee au format 4:3 (ref. rip Underground Lake), lac facon Metano, lueur, gouttes et ronds animes. Pas une aventure jouable.</Description>
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
def glow_centres(water):
    """Une lueur par bassin, collée à sa rive nord comme sur le rip (le haut de l'ellipse passe sous les parois)."""
    lab, n = nd.label(water); sizes = nd.sum(water, lab, range(1, n + 1)); out = []
    for i in sorted(np.argsort(sizes)[-2:] + 1, key=lambda i: nd.center_of_mass(water, lab, i)[1]):
        ys, xs = np.nonzero(lab == i); y0, y1 = ys.min(), ys.max(); hgt = y1 - y0
        top = ys < y0 + 0.3 * hgt
        out.append((int(round(xs[top].mean())), int(round(y0 + 0.10 * hgt)),
                    int(round(0.30 * (xs.max() - xs.min()))), int(round(0.20 * hgt))))
    return out


def build():
    gfx = loadmod('pmdo_codec', R / 'source/pmdo_cote/build.py')
    tools = loadmod('index_tools', R / 'source/pmdo_cote/INSTALLER.py')
    v1 = loadmod('esn1', R / 'source/entree_sud_nord_generee_v1/build.py')
    ANIMS = ['eau', 'lueur', 'scintillements', 'gouttes']
    if OUT.exists():
        for d in ['calques', 'animation', 'poses', 'masques', 'review']:
            shutil.rmtree(OUT / d, ignore_errors=True)
    for d in ['calques', 'poses', 'masques', 'review'] + [f'animation/{x}' for x in ANIMS]:
        (OUT / d).mkdir(parents=True, exist_ok=True)
    a = rgb(RAW / 'decor_magenta.png'); f = rgb(RAW / 'sol_complet.png'); ref = rgb(REF)
    assert a.shape[:2] == f.shape[:2] == (SRC[1], SRC[0])
    m, seg = classify(a, f)
    order = ['water', 'profondeur', 'sable', 'ombres', 'berge', 'piliers', 'roche']
    ex, cols = down_class(a, m, order)
    water = ex['water']
    layers = {'sol_complet': rgba(down_full(f), ~water)}
    for k in STATIC:
        layers[k] = rgba(cols[k], ex[k])
    q = {}
    for keys, n in PALETTE_GROUPS.values():
        q.update(quantize_group({k: layers[k] for k in keys}, n))
    layers = q
    for k, v in ex.items():
        Image.fromarray((v * 255).astype('uint8')).save(OUT / 'masques' / f'{PFX}_masque_{k}.png')
    land = np.zeros((H, W), bool)
    for k in STATIC:
        land |= layers[k][..., 3] == 255
    visible = water & ~land
    wf, dist = lake_water(water, visible)
    centres = glow_centres(water)
    lueur = glow_frames(visible, centres)
    glow_any = np.zeros((H, W), bool); glow_core = np.ones((H, W), bool)
    for fr in lueur:
        glow_any |= fr[..., 3] == 255
        glow_core &= (fr[..., :3] == GLOW[0]).all(-1) & (fr[..., 3] == 255)
    # Scintillements natifs (quasi blancs) sur le coeur de la lueur, pas sur l'eau sombre : sur le bleu nuit, ils
    # faisaient de petits traits blancs très visibles.
    free = visible & (dist > 4) & nd.binary_erosion(glow_core, iterations=2)
    fams = BM.sparkle_families(); taken = np.zeros((H, W), bool)
    sf = [np.zeros((H, W, 4), 'uint8') for _ in range(WATER_PHASES)]; sparkles = []
    for fi, (name, frames) in enumerate(fams.items()):
        hh, ww = frames[0].shape[:2]
        for (y, x) in place(free, (hh, ww), 2, 71 + fi, taken, core=8):
            sparkles.append({'famille': name, 'xy': [x, y]})
            for t in range(WATER_PHASES):
                mm = frames[t][..., 3] > 0; sf[t][y:y+hh, x:x+ww][mm] = frames[t][mm]
    for arr in sf:
        arr[~visible] = 0
    # Gouttes : poses générées ; émetteurs sur l'eau sombre dégagée, trajectoire de chute au-dessus de l'eau.
    poses, pose_pal = sheet_poses(RAW / 'gouttes_ronds_poses.png')
    for name, p in poses.items():
        Image.fromarray(p).save(OUT / 'poses' / f'{PFX}_{name}.png')
    fall_ok = visible & (dist > 6)
    ok = visible & (dist > 20) & ~nd.binary_dilation(glow_any, iterations=10) & ~taken
    for s in range(1, 19):
        ok &= np.roll(fall_ok, s, axis=0)
    cand = np.argwhere(ok); emitters, used = [], []
    for y, x in cand[np.random.default_rng(12).permutation(len(cand))]:
        if all(abs(x - ux) > 56 or abs(y - uy) > 56 for uy, ux in used):
            used.append((y, x)); emitters.append((int(x), int(y), (len(emitters) * 3) % DROP_PHASES))
        if len(emitters) == 8:
            break
    gouttes = drop_frames(poses, emitters, visible)
    # Exports
    anim = {'eau': (wf, WATER_TICKS), 'lueur': (lueur, GLOW_TICKS), 'scintillements': (sf, WATER_TICKS),
            'gouttes': (gouttes, DROP_TICKS)}
    order_names = ['eau', 'lueur', 'scintillements', 'gouttes', 'sol_complet'] + STATIC
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
    # Collisions : sable (ombres comprises) praticable ; lac, berge, parois, piliers et bouche bloqués.
    walk_px = (layers['sable'][..., 3] == 255) | (layers['ombres'][..., 3] == 255)
    blocked = cell_grid(~walk_px); gh_, gw_ = blocked.shape
    pxs = np.nonzero(walk_px[H - 8])[0]; med = int(np.median(pxs)) // 8
    ecol = min((c for c in range(gw_ - 1) if not blocked[gh_ - 2:, c:c + 2].any()), key=lambda c: abs(c - med))
    entry_px = [ecol * 8, H - 16]
    py, px_ = np.nonzero(walk_px); top_y = int(py.min()); tx = int(np.median(px_[py < top_y + 8]))
    threshold_px = [tx // 8 * 8 - 8, top_y // 8 * 8]
    while blocked[threshold_px[1] // 8:threshold_px[1] // 8 + 2, threshold_px[0] // 8:threshold_px[0] // 8 + 2].any():
        threshold_px[1] += 8
    reach, explored = v1.reachable(blocked, (entry_px[1] // 8, entry_px[0] // 8), (threshold_px[1] // 8, threshold_px[0] // 8))
    assert reach, 'pas de chemin 16x16'

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
    names = list(POSE_WIN); cw = 36 * 4 + 8                               # même échelle x4 pour toutes les poses
    sheet = Image.new('RGBA', (len(names) * cw + 8, cw + 8), (*WPAL['surface'], 255))
    for i, nm in enumerate(names):
        im = Image.fromarray(poses[nm]); im = im.resize((im.width * 4, im.height * 4), Image.Resampling.NEAREST)
        sheet.alpha_composite(im, (8 + i * cw + (cw - 8 - im.width) // 2, 8 + (cw - 8 - im.height) // 2))
    sheet.save(OUT / 'review' / f'{PFX}_planche_poses.png')
    write_ora(OUT / f'{PFX}_entree_underground_lake_calques.ora',
              {f'{i:02d}_{t}' + ('_f00' if len(fr) > 1 else ''): fr[0] for i, (t, fr, _) in enumerate(stack_named)})
    counts = ground_project([(t.replace('_', ' ') + (f' {len(fr)} phases' if len(fr) > 1 else ''), fr, tk)
                             for t, fr, tk in stack_named], blocked, entry_px, threshold_px, gfx, tools)
    fid = fidelity(a, ref)
    final_fid = {}
    for k, nm in (('sable', 'sable'), ('roche', 'roche'), ('roche', 'piliers')):
        lay = layers[nm]; px = lay[lay[..., 3] == 255][:, :3].astype(float)
        sel = materials(px.reshape(-1, 1, 3))[k][:, 0]
        px = px[sel] if sel.sum() > 50 else px
        final_fid[nm] = {'matiere': k, 'rgb': [round(float(v), 1) for v in px.mean(0)],
                         'distance_rip': round(float(np.linalg.norm(px.mean(0) - np.array(fid[k]['rip_rgb']))), 1)}
    manifest = {
        'lot': 'entree_underground_lake_sud_nord_v1', 'prefix': PFX, 'format': '4:3 vaste', 'size_px': [W, H],
        'grid_8px': [W // 8, H // 8], 'base': 'branche de session (EWC2 pour les utilitaires) ; aucun emprunt aux branches soeurs',
        'biome': 'Underground Lake, choisi par l agent a la demande de l utilisateur (« go carte suivante choisis ! »)',
        'method': 'textures canoniques = rendu genere REFERENCE : rip passe au generateur ; decor complet sur magenta '
                  '(lac = magenta), sol complet edite depuis le decor, planche gouttes/ronds sur magenta',
        'reference_da': {'file': REF.name, 'sha256': sha(REF), 'titre': 'Rive du lac souterrain (Underground Lake, PMD Explorers)'},
        'generation': GEN,
        'raw_inputs': [{'file': f'source/entree_underground_lake_sud_nord_v1/bruts/{g["file"]}', 'sha256': sha(RAW / g['file']),
                        'size': list(Image.open(RAW / g['file']).size)} for g in GEN],
        'sol_complet': {'recalage_px': [0, 0], 'ecart_moyen_parois': 3.81, 'ecart_decale_1px': 7.09,
                        'note': 'le generateur a garde les parois (sous le calque parois) ; lac, piliers, stalagmites et '
                                'bouche remplaces par du sable', 'ecarts_segmentation': seg},
        'fidelite_rip': {'methode': 'moyenne RGB par matiere, meme classifieur pixel sur le rip et sur le brut ; distance euclidienne',
                         'brut': fid, 'calques_finaux': final_fid,
                         'eau_et_lueur': 'couleurs EXACTES du rip (test : sous-ensemble des 69 couleurs du rip)'},
        'normalization': {'scale': JM.SCALE, 'scaled': [JM.SCALED_W, H], 'crop_x': [JM.CROP_X, JM.SCALED_W - W - JM.CROP_X],
                          'methode': 'moyenne ponderee par classe (BOX), attribution exclusive par poids maximal',
                          'palettes': {g: {'calques': k, 'couleurs': n} for g, (k, n) in PALETTE_GROUPS.items()}},
        'segmentation': 'eau = magenta et frange violette (r-g > 60 et b-g > 60) dilates 2 px ; entree sombre = lum < 48 '
                        'reliee au haut-centre ; sable = jaune clair (r > 150, r-b > 50, lum > 140), grande composante, '
                        'trous < 300 px combles ; ombres = sable a <= 16 px des parois et lum lissee 5 px < 187 ; berge = '
                        'ni sable ni eau a <= 14 px de l eau et du sable ; piliers = roche ou le sol complet differe '
                        '(ecart lisse 5 px > 20), hors abords de la bouche ; parois = le reste',
        'layers': layer_list,
        'water': {'phases': WATER_PHASES, 'frame_length_ticks': WATER_TICKS, 'couleurs': {k: list(v) for k, v in WPAL.items()},
                  'modele': 'structure et cadence riviere Metano (bande, frange dentelee, accent, aplat, onde voyageuse), '
                            'couleurs EXACTES du rip ; bande = intermediaire ; sans liseré clair de rive',
                  'origine': 'pixels recalcules, pas de tuiles natives'},
        'lueur': {'phases': GLOW_PHASES, 'frame_length_ticks': GLOW_TICKS, 'couleurs': [list(c) for c in GLOW],
                  'centres': [list(c) for c in centres], 'anneau_px': GLOW_RING_PX, 'respiration': GLOW_BREATH,
                  'ondulation': GLOW_WOBBLE,
                  'origine': 'couleurs EXACTES du rip (coeur + 8 anneaux) ; forme, respiration et ondulation creees par nous'},
        'sparkles': {'source': 'source/eau_metano/natifs/Metano_Town_River_Sparkles.tile', 'placements': sparkles,
                     'origine': 'pixels et couleurs Metano NATIFS inchanges (aplat de surface retire)',
                     'zone': 'coeur de la lueur (commun aux 12 phases), pas l eau sombre'},
        'gouttes': {'poses': {k: list(v) for k, v in POSE_WIN.items()}, 'reduction': f'x1/{POSE_K} pour toutes les poses',
                    'palette': [[int(round(c)) for c in p] for p in pose_pal], 'chronologie': DROP_SEQ,
                    'emetteurs': [list(e) for e in emitters], 'phases': DROP_PHASES, 'frame_length_ticks': DROP_TICKS,
                    'origine': 'dessin GENERE (8 couleurs tirees de la planche) ; chronologie, chute et placement crees par nous'},
        'shadows': 'calque ombres = bande de sable assombrie au pied des parois, separee du rendu genere (pas inventee)',
        'scene_loop_ticks': LOOP_TICKS,
        'access': {'entry_px': entry_px, 'threshold_px': threshold_px, 'path_found_16x16': reach, 'cells_explored': explored,
                   'blocked_cells': int(blocked.sum()), 'total_cells': int(blocked.size), 'walkable_cells': int((~blocked).sum()),
                   'rule': 'case bloquee si > 25 % hors sable (ombres comprises)',
                   'seuil': 'haut de la chaussee de sable, au pied de l entree sombre'},
        'pmdo': {'target': '0.8.12', 'asset': ASSET, 'namespace': NAMESPACE, 'tiles_per_bank': counts, 'banks': list(counts),
                 'runtime_tested': False, 'warp': 'aucun'},
        'art_approved': False,
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    shutil.copyfile(OUT / 'manifest.json', STAGE / 'manifest.json')
    print(json.dumps({'sparkles': len(sparkles), 'entry': entry_px, 'threshold': threshold_px, 'blocked': int(blocked.sum()),
                      'walkable': int((~blocked).sum()), 'emitters': len(emitters), 'centres': centres, 'seg': seg,
                      'px': {k: int(v.sum()) for k, v in ex.items()},
                      'fidelite': {k: v['distance'] for k, v in fid.items()},
                      'final': {k: v['distance_rip'] for k, v in final_fid.items()}, 'tiles': sum(counts.values())}, indent=1))


if __name__ == '__main__':
    build()
