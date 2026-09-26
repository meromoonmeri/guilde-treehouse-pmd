"""Entrée de la fosse du Dark Crater sud -> nord V1 (ECF1) — format 4:3 vaste (768 x 576 px, 96 x 72 cases).

Demande : « passe à la suite stp » (après EFF2). Carte suivante, biome choisi par l'agent : fosse du Dark Crater,
référence `Dark_Crater_Pit_TDS.png` (PMD Explorers), jamais utilisée comme référence principale. Méthode « textures
canoniques » = rendu généré RÉFÉRENCÉ (rip passé au générateur en images=) :
- decor_magenta.png : décor complet 4:3 (1200 x 896), TOUTE la lave en magenta ;
- sol_complet.png : roche complète éditée depuis le décor (2e essai ; le générateur a gardé la paroi nord et la
  bouche, qui restent sous leurs calques) ;
- bulles_lave_poses.png : planche sur magenta (rangée 1 : bulle qui gonfle et éclate ; rangée 2 non utilisée).
Calques : sol complet, sol praticable, bordures de roche, pics noirs, paroi nord, bouche de la grotte.
Animations, chacune sur son calque, boucles fermées :
- lave : cellules (Voronoï) aux 11 couleurs EXACTES de la rampe du rip, palette cycling + bande rouge contre la
  roche, 12 x 8 ticks (animation créée) ;
- bulles de lave (poses générées), 24 x 4 ticks.
Scène : PPCM(96, 96) = 96 ticks = 1,6 s.
Lancer : .venv/bin/python source/entree_cratere_fosse_sud_nord_v1/build.py
"""
from pathlib import Path
import hashlib, importlib.util, io, json, shutil, uuid, zipfile

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
RAW = HERE / 'bruts'
REF = R / 'Dark_Crater_Pit_TDS.png'
OUT = R / 'renders/entree_cratere_fosse_sud_nord_v1'
STAGE = R / '.cache/entree_cratere_fosse_sud_nord_v1/entree_cratere_fosse_sud_nord'
NAMESPACE = 'entree_cratere_fosse_sud_nord'
ASSET = 'ecf1_entree_cratere_fosse'
PFX = 'ECF1'
W, H = 768, 576
SRC = (1200, 896)
LAVA_PHASES, LAVA_TICKS = 12, 8
BUB_PHASES, BUB_TICKS = 24, 4
LOOP_TICKS = 96
# Rampe de lave : couleurs EXACTES du rip (mesurées, 11 teintes du rouge au jaune clair).
RAMP = [(247, 39, 31), (247, 63, 31), (247, 95, 31), (247, 119, 31), (247, 135, 31), (247, 151, 39),
        (255, 167, 39), (255, 175, 39), (255, 199, 47), (255, 223, 55), (255, 255, 47)]
CELL = 18                                    # pas moyen des cellules (px, carte) ; ~ cellules du rip x 0,64
BUB_K = 8                                    # réduction des bulles x1/8
BUB_WIN = 176                                # fenêtre carrée par pose
BUB_X = [118, 343, 573, 800, 1030, 1258]     # centres des 6 poses de la rangée 1 (choisis à la main)
BUB_Y = 200
BUB_SEQ = [0, 0, 1, 1, 2, 2, 3, 3, 4, 5, 5] + [-1] * 13
assert len(BUB_SEQ) == BUB_PHASES
GEN = [
    {'file': 'decor_magenta.png', 'images': ['Dark_Crater_Pit_TDS.png'], 'prompt':
     'Use EXACTLY the same textures, palette and pixel-art style as the reference image (Pokemon Mystery Dungeon '
     'Explorers of Sky, Dark Crater pit): same flat grey-brown volcanic rock ground with fine stippled texture, same '
     'jagged dark brown-black rock rims with lighter edge highlights around the rock island, same black pointed rock '
     'spikes. Make a NEW, larger top-down map. WIDE LANDSCAPE 4:3, zoomed out so the crater feels vast. Layout: the '
     'player arrives at the SOUTH (bottom edge center) on a rock path bordered by jagged dark rims; the path widens '
     'into a large irregular rock plateau in the middle; from the plateau a narrow winding rock bridge goes NORTH up to '
     'a dark cave opening in a tall black rock wall at the top center; a few black rock spikes stand around. Everything '
     'that is not rock is molten lava: IMPORTANT fill ALL lava areas with flat pure magenta #FF00FF, no lava texture, '
     'no glow. No characters, no text, no UI, no border.'},
    {'file': 'sol_complet.png', 'images': ['source/entree_cratere_fosse_sud_nord_v1/bruts/decor_magenta.png'], 'prompt':
     'Same image, same framing and pixel-art style, but only plain grey-brown rock ground everywhere, nothing else.',
     'essais': 'deuxieme essai ; le premier (prompt plus long) a rendu une reponse sans image. Paroi nord et bouche gardees'},
    {'file': 'bulles_lave_poses.png', 'images': ['Dark_Crater_Pit_TDS.png'], 'prompt':
     'Pixel-art sprite sheet on a flat pure magenta #FF00FF background, same style and lava colors as the reference '
     'image (Pokemon Mystery Dungeon Explorers of Sky, Dark Crater). 2 rows of 6 separate small sprites. Row 1: a lava '
     'bubble growing, swelling and bursting (yellow-orange-red). Row 2: a small ember spark rising and fading. Sprites '
     'well separated with wide magenta spacing, no text, no grid lines.'},
]


def loadmod(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


EM = loadmod('emf1_build', R / 'source/entree_mystifying_forest_sud_nord_v1/build.py')   # utilitaires EMF1
V1, JM = EM.V1, EM.JM
assert (JM.W, JM.H, JM.SRC) == (W, H, SRC)
keep_large, cell_grid, close_ = V1.keep_large, V1.cell_grid, V1.close_
down_class, down_full, rgba, quantize_group = V1.down_class, V1.down_full, V1.rgba, V1.quantize_group
open_, sha, rgb, paste = EM.open_, EM.sha, EM.rgb, EM.paste
PALETTE_GROUPS = {'terrain': (['sol_complet', 'sol', 'bordures'], 96), 'pics': (['pics'], 16),
                  'paroi': (['paroi'], 32), 'grotte': (['grotte'], 8)}
STATIC = ['sol', 'bordures', 'pics', 'paroi', 'grotte']


def is_mag(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return (r - g > 60) & (b - g > 60)


# ---------------------------------------------------------------- fidélité au rip (même classifieur des deux côtés)
def materials(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]; lum = a @ [.299, .587, .114]; sat = a.max(-1) - a.min(-1)
    lava = (r > 200) & (r - b > 150); mag = is_mag(a)
    sol = (sat < 28) & (lum > 70) & (lum < 125) & (r >= b) & ~lava & ~mag
    bord = (r - b > 25) & (lum > 35) & (lum < 170) & ~lava & ~mag
    noir = (lum < 45) & ~mag
    return {'sol': sol, 'bordures': bord, 'roche_noire': noir}


def fidelity(decor, ref):
    fr, fd = materials(ref), materials(decor); out = {}
    for k in fr:
        mr, md = ref[fr[k]].mean(0), decor[fd[k]].mean(0)
        out[k] = {'rip_rgb': [round(float(v), 1) for v in mr], 'decor_rgb': [round(float(v), 1) for v in md],
                  'distance': round(float(np.linalg.norm(mr - md)), 1)}
    return out


# ---------------------------------------------------------------- segmentation pleine résolution
def classify(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]; lum = a @ [.299, .587, .114]; sat = a.max(2) - a.min(2)
    hh, ww = lum.shape; yy, xx = np.mgrid[:hh, :ww]
    L = nd.uniform_filter(lum, 9); S = nd.uniform_filter(sat.astype(float), 9)
    lava = nd.binary_dilation(is_mag(a), iterations=2)
    # Bouche (mesurée (16,17,22), écart-type 1) : aplat sombre uniforme, haut-centre.
    sd = np.sqrt(np.maximum(nd.uniform_filter(lum ** 2, 5) - nd.uniform_filter(lum, 5) ** 2, 0))
    mouth = (lum < 40) & (sd < 4) & (yy < 180) & (xx > 480) & (xx < 720)
    ml, _ = nd.label(close_(mouth, 2)); sizes = nd.sum(mouth, ml, range(1, ml.max() + 1))
    mouth = nd.binary_fill_holes(ml == int(np.argmax(sizes)) + 1)            # plus grand aplat : la bouche
    # Sol praticable (mesuré (101,92,81)) : gris-brun peu saturé, critère régional, grande composante + îlots.
    sol = (L > 70) & (L < 130) & (S < 30) & ~lava & ~mouth
    sol = keep_large(open_(close_(sol, 2), 2), 800)
    sol = nd.binary_fill_holes(sol) & ~lava & ~mouth
    # Roche sombre (lum lissée < 40) : reliée au bord haut -> paroi nord ; isolée dans la lave -> pics.
    dark = (L < 40) & ~lava & ~mouth & ~sol
    dl, _ = nd.label(close_(dark, 2)); top = set(np.unique(dl[:4][dark[:4]])) - {0}
    wall = np.isin(dl, list(top)) & ~lava & ~mouth & ~sol
    wall = nd.binary_fill_holes(wall | mouth) & ~mouth & ~lava & ~sol
    # Pics : composantes sombres entièrement cernées de lave (anneau de 4 px), boîte complétée hors lave
    # (reflets violets, liserés clairs) ; le reste sombre au contact du plateau reste aux bordures.
    cand = ~lava & ~mouth & ~sol & ~wall
    cl, _ = nd.label(cand); spikes = np.zeros_like(cand)
    for i, s in enumerate(nd.find_objects(cl), 1):
        c = cl == i
        ring = nd.binary_dilation(c, iterations=4) & ~c
        if 300 <= c.sum() < 20000 and lava[ring].mean() > 0.97:
            spikes |= c
    rims = ~(lava | mouth | sol | wall | spikes)
    return dict(lava=lava, sol=sol, bordures=rims, pics=spikes, paroi=wall, grotte=mouth)


# ---------------------------------------------------------------- lave (animation créée, couleurs exactes du rip)
def lava_frames(visible, rock_dist, ts=range(LAVA_PHASES)):
    """Cellules de Voronoï (graine 21, pas CELL) : centre jaune, bords rouges comme sur le rip ; chaque cellule
    respire (indice de rampe + round(2 sin(2 pi t/12 + phi_c))) ; bande rouge contre la roche (<= 3 px) et bande
    orangée (<= 6 px). t = 12 égale t = 0 par construction."""
    rng = np.random.default_rng(21)
    gy, gx = np.mgrid[CELL // 2:H + CELL:CELL, CELL // 2:W + CELL:CELL]
    sy = (gy + rng.integers(-CELL // 3, CELL // 3 + 1, gy.shape)).ravel()
    sx = (gx + rng.integers(-CELL // 3, CELL // 3 + 1, gx.shape)).ravel()
    ok = (sy < H) & (sx < W); sy, sx = sy[ok], sx[ok]
    seeds = np.ones((H, W), bool); seeds[sy, sx] = False
    _, (iy, ix) = nd.distance_transform_edt(seeds, return_indices=True)
    lab = iy * W + ix
    edge = np.zeros((H, W), bool)
    edge[:-1] |= lab[:-1] != lab[1:]; edge[:, :-1] |= lab[:, :-1] != lab[:, 1:]
    F = nd.distance_transform_edt(~edge)
    base = np.clip(np.round(F / (CELL * 0.45) * 10), 0, 10).astype(int)
    phi = (np.sin(lab * 12.9898) * 43758.5453) % 1 * 2 * np.pi
    ramp = np.array(RAMP, 'uint8'); frames = []
    for t in ts:
        idx = np.clip(base + np.round(2 * np.sin(2 * np.pi * t / LAVA_PHASES + phi)).astype(int), 0, 10)
        idx = np.where(rock_dist <= 6, np.minimum(idx, 2), idx)
        idx = np.where(rock_dist <= 3, 0, idx)
        f = np.zeros((H, W, 4), 'uint8'); f[..., :3] = ramp[idx]; f[..., 3] = 255
        f[~visible] = 0; frames.append(f)
    return frames


# ---------------------------------------------------------------- bulles (poses générées)
def bubble_poses(path):
    src = rgb(path); bg = is_mag(src) | ((src[..., 0] - src[..., 1] > 40) & (src[..., 2] - src[..., 1] > 40))
    px = src[~bg & (np.mgrid[:src.shape[0], :src.shape[1]][0] < 330)]
    q = Image.fromarray(px.reshape(-1, 1, 3).astype('uint8')).quantize(colors=8, method=Image.Quantize.MEDIANCUT)
    pal = np.array(q.getpalette()[:24], float).reshape(-1, 3)
    return [EM.reduce_pose(src, bg, BUB_Y, cx, BUB_WIN, BUB_K, pal, 0.3) for cx in BUB_X], pal


def bubble_frames(poses, spots, ts=range(BUB_PHASES)):
    frames = []
    for t in ts:
        f = np.zeros((H, W, 4), 'uint8')
        for x, y, off in spots:
            p = BUB_SEQ[(t + off) % BUB_PHASES]
            if p >= 0:
                paste(f, poses[p], x, y)
        frames.append(f)
    return frames


# ---------------------------------------------------------------- ORA et Ground
def write_ora(path, layers):
    import xml.etree.ElementTree as ET
    root = ET.Element('image', w=str(W), h=str(H), name='Entree Fosse Dark Crater sud-nord V1 (ECF1)')
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


# ---------------------------------------------------------------- main

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
    o.update(Name={'DefaultText': 'Entree Fosse du Dark Crater - sud vers nord (4:3)', 'LocalTexts': {}}, AssetName=ASSET,
             Released=False, TexSize=1, Music='', EdgeView=1, ViewCenter=None, ViewOffset={'X': 0, 'Y': 0},
             ActiveChar=None, Status={}, Layers=layers,
             Background={'$type': 'RogueEssence.Dungeon.LayeredBG, RogueEssence', 'Layers': []},
             Comment='PMDO 0.8.12. Rendu genere 4:3 reference sur le rip Dark Crater Pit ; lave aux couleurs '
                     'exactes du rip (cellules, palette cycling), bulles de lave generees. '
                     'Collisions de base a verifier. Seuil non raccorde. Biome choisi par l agent.')
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
  <Name>Entree Fosse Dark Crater sud-nord 4:3 - Atelier 0.8.12</Name>
  <Author>meromoonmeri</Author>
  <Description>Projet d'edition : fosse volcanique generee au format 4:3 (ref. rip Dark Crater Pit), lave animee, bulles de lave. Pas une aventure jouable.</Description>
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
    ANIMS = ['lave', 'bulles']
    if OUT.exists():
        for d in ['calques', 'animation', 'poses', 'masques', 'review']:
            shutil.rmtree(OUT / d, ignore_errors=True)
    for d in ['calques', 'poses', 'masques', 'review'] + [f'animation/{x}' for x in ANIMS]:
        (OUT / d).mkdir(parents=True, exist_ok=True)
    a = rgb(RAW / 'decor_magenta.png'); f = rgb(RAW / 'sol_complet.png'); ref = rgb(REF)
    assert a.shape[:2] == f.shape[:2] == (SRC[1], SRC[0])
    m = classify(a)
    order = ['lava', 'grotte', 'pics', 'paroi', 'sol', 'bordures']
    ex, cols = down_class(a, m, order)
    lava = ex['lava']
    layers = {'sol_complet': rgba(down_full(f), ~lava)}
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
    visible = lava & ~land
    rock_dist = nd.distance_transform_edt(visible)
    lave = lava_frames(visible, rock_dist)
    bubs, bub_pal = bubble_poses(RAW / 'bulles_lave_poses.png')
    for i, p in enumerate(bubs):
        Image.fromarray(p).save(OUT / 'poses' / f'{PFX}_bulle_{i}.png')
    cand = np.argwhere(rock_dist > 22); rng = np.random.default_rng(4); spots, used = [], []
    for y, x in cand[rng.permutation(len(cand))]:
        if all(abs(x - ux) > 70 or abs(y - uy) > 70 for uy, ux in used):
            used.append((y, x)); spots.append((int(x), int(y), (len(spots) * 7) % BUB_PHASES))
        if len(spots) == 14:
            break
    bulles = bubble_frames(bubs, spots)
    for fr in bulles:
        fr[~visible] = 0
    anim = {'lave': (lave, LAVA_TICKS), 'bulles': (bulles, BUB_TICKS)}
    order_names = ['lave', 'bulles', 'sol_complet'] + STATIC
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
    # Collisions : sol gris + bordures à plus de 3 px de la lave (le pont de roche ne fait qu'une case de sol gris :
    # ses rebords sont praticables, pas leur arête contre la lave).
    far = nd.distance_transform_edt(~lava) > 3
    walk_px = (layers['sol'][..., 3] == 255) | ((layers['bordures'][..., 3] == 255) & far)
    blocked = cell_grid(~walk_px); gh_, gw_ = blocked.shape
    pxs = np.nonzero(walk_px[H - 8])[0]; med = int(np.median(pxs)) // 8
    ecol = min((c for c in range(gw_ - 1) if not blocked[gh_ - 2:, c:c + 2].any()), key=lambda c: abs(c - med))
    entry_px = [ecol * 8, H - 16]
    gy_, gx_ = np.nonzero(ex['grotte']); cx = int(gx_.mean())
    threshold_px = [cx // 8 * 8 - 8, (int(gy_.max()) + 8) // 8 * 8]
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
    sheet = Image.new('RGBA', (6 * 92, 92), (60, 40, 35, 255))
    for i, p in enumerate(bubs):
        im = Image.fromarray(p); sheet.alpha_composite(im.resize((im.width * 4, im.height * 4), Image.Resampling.NEAREST), (i * 92 + 2, 2))
    sheet.save(OUT / 'review' / f'{PFX}_planche_poses.png')
    write_ora(OUT / f'{PFX}_entree_cratere_fosse_calques.ora',
              {f'{i:02d}_{t}' + ('_f00' if len(fr) > 1 else ''): fr[0] for i, (t, fr, _) in enumerate(stack_named)})
    counts = ground_project([(t.replace('_', ' ') + (f' {len(fr)} phases' if len(fr) > 1 else ''), fr, tk)
                             for t, fr, tk in stack_named], blocked, entry_px, threshold_px, gfx, tools)
    fid = fidelity(a, ref)
    final_fid = {}
    for k, nm in (('sol', 'sol'), ('bordures', 'bordures'), ('roche_noire', 'paroi')):
        lay = layers[nm]; px = lay[lay[..., 3] == 255][:, :3].astype(float)
        sel = materials(px.reshape(-1, 1, 3))[k][:, 0]
        px = px[sel] if sel.sum() > 50 else px
        final_fid[k] = {'calque': nm, 'rgb': [round(float(v), 1) for v in px.mean(0)],
                        'distance_rip': round(float(np.linalg.norm(px.mean(0) - np.array(fid[k]['rip_rgb']))), 1)}
    manifest = {
        'lot': 'entree_cratere_fosse_sud_nord_v1', 'prefix': PFX, 'format': '4:3 vaste', 'size_px': [W, H],
        'grid_8px': [W // 8, H // 8], 'base': 'branche de session (EMF1 pour les utilitaires) ; aucun emprunt aux branches soeurs',
        'biome': 'fosse du Dark Crater, choisi par l agent (« passe a la suite »)',
        'method': 'textures canoniques = rendu genere REFERENCE : rip passe au generateur ; decor complet sur magenta '
                  '(lave = magenta), roche complete editee depuis le decor, planche de bulles sur magenta',
        'reference_da': {'file': REF.name, 'sha256': sha(REF), 'titre': 'Fosse du Dark Crater (PMD Explorers)'},
        'generation': GEN,
        'raw_inputs': [{'file': f'source/entree_cratere_fosse_sud_nord_v1/bruts/{g["file"]}', 'sha256': sha(RAW / g['file']),
                        'size': list(Image.open(RAW / g['file']).size)} for g in GEN],
        'fidelite_rip': {'methode': 'moyenne RGB par matiere, meme classifieur pixel sur le rip et sur le brut ; distance euclidienne',
                         'brut': fid, 'calques_finaux': final_fid,
                         'lave': 'couleurs EXACTES du rip (rampe de 11 teintes, test : sous-ensemble des couleurs du rip)'},
        'normalization': {'scale': JM.SCALE, 'scaled': [JM.SCALED_W, H], 'crop_x': [JM.CROP_X, JM.SCALED_W - W - JM.CROP_X],
                          'methode': 'moyenne ponderee par classe (BOX), attribution exclusive par poids maximal',
                          'palettes': {g: {'calques': k, 'couleurs': n} for g, (k, n) in PALETTE_GROUPS.items()}},
        'segmentation': 'lave = magenta dilate 2 px ; grotte = plus grand aplat sombre uniforme (lum<40, ecart-type<4) du '
                        'haut-centre ; sol = gris-brun peu sature (lum lissee 70-130, sat lissee < 30), composantes > 800 px ; '
                        'paroi = roche sombre reliee au bord haut ; pics = composantes cernees de lave (anneau 4 px > 97 %) ; '
                        'bordures = le reste',
        'layers': layer_list,
        'lave': {'phases': LAVA_PHASES, 'frame_length_ticks': LAVA_TICKS, 'rampe': [list(c) for c in RAMP], 'cellule_px': CELL,
                 'modele': 'cellules de Voronoi (graine 21), indice de rampe par distance au bord de cellule, respiration '
                           'round(2 sin(2 pi t/12 + phi_cellule)), bande rouge <= 3 px et orangee <= 6 px contre la roche',
                 'origine': 'couleurs EXACTES du rip ; motif et mouvement crees par nous (pas une animation officielle)'},
        'bulles': {'poses': len(bubs), 'fenetres': {'x': BUB_X, 'y': BUB_Y, 'cote': BUB_WIN}, 'reduction': f'x1/{BUB_K}',
                   'palette': [[int(c) for c in p] for p in bub_pal], 'chronologie': BUB_SEQ, 'points': [list(s) for s in spots],
                   'phases': BUB_PHASES, 'frame_length_ticks': BUB_TICKS,
                   'origine': 'dessin GENERE (rangee 1 de la planche) ; chronologie et placement crees par nous'},
        'scene_loop_ticks': LOOP_TICKS,
        'access': {'entry_px': entry_px, 'threshold_px': threshold_px, 'path_found_16x16': ok, 'cells_explored': explored,
                   'blocked_cells': int(blocked.sum()), 'total_cells': int(blocked.size), 'walkable_cells': int((~blocked).sum()),
                   'rule': 'case bloquee si > 25 % hors sol gris et bordures a plus de 3 px de la lave', 'seuil': 'devant la bouche de la grotte, en haut du pont de roche'},
        'pmdo': {'target': '0.8.12', 'asset': ASSET, 'namespace': NAMESPACE, 'tiles_per_bank': counts, 'banks': list(counts),
                 'runtime_tested': False, 'warp': 'aucun'},
        'art_approved': False,
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    shutil.copyfile(OUT / 'manifest.json', STAGE / 'manifest.json')
    print(json.dumps({'entry': entry_px, 'threshold': threshold_px, 'walkable': int((~blocked).sum()), 'bulles': len(spots),
                      'fidelite': {k: v['distance'] for k, v in fid.items()},
                      'final': {k: v['distance_rip'] for k, v in final_fid.items()}, 'tiles': sum(counts.values())}))


if __name__ == '__main__':
    build()
