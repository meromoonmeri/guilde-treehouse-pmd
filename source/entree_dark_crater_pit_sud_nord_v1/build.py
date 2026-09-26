"""Entrée Dark Crater — fosse de lave sud -> nord V1 (EDP1) — format 4:3 vaste (768 x 576 px, 96 x 72 cases).

Demande : « passe à la suite stp » (après EFF2). Biome choisi par l'agent : Dark Crater Pit, référence
`Dark_Crater_Pit_TDS.png` (PMD Explorers), jamais utilisée comme référence principale. Méthode « textures
canoniques » = rendu généré RÉFÉRENCÉ (rip passé au générateur en images=) :
- decor_magenta.png : décor complet 4:3 (1200 x 896), toute la lave en magenta ;
- lave_complete.png : le décor édité par le générateur (décor + rip en références), magenta remplacé par la lave ;
- sol_complet.png : pierre grise complète éditée depuis le décor (2e essai : le 1er a rendu une réponse sans image) ;
- bulles_poses.png : planche de bulles de lave sur magenta ; seules les 5 poses détourables (gerbes, anneaux) servent.
Calques : sol complet, sol praticable (plateau et chemins), rebords rocheux, grand mur noir, aiguilles et débris dans
la lave, grotte (bouche sombre).
Animations, chacune sur son calque, boucles fermées :
- lave : pixels du brut lave_complete ramenés aux 11 couleurs EXACTES du rip (rampe du rouge au jaune), cycle de
  palette : l'indice de rampe oscille de +/- 1 selon une onde qui traverse la lave, 12 x 8 ticks (créé par nous) ;
- bulles : gerbes et anneaux générés, 24 x 4 ticks.
Scène : PPCM(96, 96) = 96 ticks = 1,6 s.
Lancer : .venv/bin/python source/entree_dark_crater_pit_sud_nord_v1/build.py
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
OUT = R / 'renders/entree_dark_crater_pit_sud_nord_v1'
STAGE = R / '.cache/entree_dark_crater_pit_sud_nord_v1/entree_dark_crater_pit_sud_nord'
NAMESPACE = 'entree_dark_crater_pit_sud_nord'
ASSET = 'edp1_entree_dark_crater_pit'
PFX = 'EDP1'
W, H = 768, 576
SRC = (1200, 896)
LAVA_PHASES, LAVA_TICKS = 12, 8
BUB_PHASES, BUB_TICKS = 24, 4
LOOP_TICKS = 96
# Rampe de lave : les 11 couleurs du rip présentes à plus de 3000 px, du rouge sombre au jaune (mesurées).
LAVA_RAMP = [(247, 39, 31), (247, 63, 31), (247, 95, 31), (247, 119, 31), (247, 135, 31), (247, 151, 39),
             (255, 167, 39), (255, 175, 39), (255, 199, 47), (255, 223, 55), (255, 255, 47)]
GEN = [
    {'file': 'decor_magenta.png', 'images': ['Dark_Crater_Pit_TDS.png'], 'prompt':
     'Use EXACTLY the same textures, palette and pixel-art style as the reference image (Pokemon Mystery Dungeon '
     'Explorers of Sky, Dark Crater pit): same flat dark grey volcanic stone ground with fine speckles, same jagged '
     'black-brown rock cliff rims with sharp spikes, same black obsidian rock spires. Make a NEW, larger top-down map. '
     'WIDE LANDSCAPE 4:3, zoomed out so the area feels vast. Layout: the player arrives at the SOUTH (bottom edge center) '
     'on a grey stone path bordered by jagged dark rock rims; the path widens into a large grey stone plateau in the '
     'middle, then a stone bridge-path continues NORTH to a dark cave opening in a big black rock wall at the top center. '
     'Lava surrounds the plateau and paths on the left and right sides, with a few black rock spires standing in the '
     'lava. IMPORTANT: all the lava is filled with flat pure magenta #FF00FF, no texture. No characters, no text, no UI, '
     'no border.'},
    {'file': 'lave_complete.png', 'images': ['source/entree_dark_crater_pit_sud_nord_v1/bruts/decor_magenta.png',
                                             'Dark_Crater_Pit_TDS.png'], 'prompt':
     'Same image, same size, same framing and pixel-art style, but replace ALL the flat magenta areas with bubbling lava '
     'exactly like the reference lava: bright yellow-orange molten lava with a cellular pattern of red-orange blobs and '
     'darker red cracks. Keep everything else identical.'},
    {'file': 'sol_complet.png', 'images': ['source/entree_dark_crater_pit_sud_nord_v1/bruts/decor_magenta.png'], 'prompt':
     'Same image, same framing and pixel-art style, but only plain grey stone ground everywhere, nothing else.',
     'essais': 'deuxieme essai ; le premier (prompt plus long) a rendu une reponse sans image'},
    {'file': 'bulles_poses.png', 'images': ['Dark_Crater_Pit_TDS.png'], 'prompt':
     'Pixel-art sprite sheet on a flat pure magenta #FF00FF background, same style and colors as the reference lava '
     '(Pokemon Mystery Dungeon Explorers of Sky). 2 rows of 6 small separate sprites: a lava bubble growing, swelling, '
     'bursting with small orange-yellow splash droplets, then a fading ring. Sprites well separated, no text, no grid lines.',
     'note': 'rendue en 4 rangees ; les 6 premieres poses ont un fond de lave rectangulaire (non detourables) et les 2 '
             'dernieres sont tramees sur le magenta : seules les poses 7 a 11 (gerbes, anneaux) sont utilisees'},
]


def loadmod(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


EM = loadmod('emf1_build', R / 'source/entree_mystifying_forest_sud_nord_v1/build.py')   # utilitaires EMF1
V1, JM = EM.V1, EM.JM
assert (JM.W, JM.H, JM.SRC) == (W, H, SRC)
keep_large, cell_grid, close_ = V1.keep_large, V1.cell_grid, V1.close_
down_class, down_full, rgba, quantize_group = V1.down_class, V1.down_full, V1.rgba, V1.quantize_group
open_, sha, rgb, paste, write_ora_emf = EM.open_, EM.sha, EM.rgb, EM.paste, EM.write_ora
PALETTE_GROUPS = {'terrain': (['sol_complet', 'sol'], 64), 'rebords': (['rebords'], 48), 'mur': (['mur'], 32),
                  'aiguilles': (['aiguilles'], 32), 'grotte': (['grotte'], 12)}
STATIC = ['sol', 'rebords', 'mur', 'aiguilles', 'grotte']


def is_mag(a):
    return (a[..., 0] > 180) & (a[..., 2] > 180) & (a[..., 1] < 120)


# ---------------------------------------------------------------- fidélité au rip (même classifieur des deux côtés)
def materials(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]; lum = a @ [.299, .587, .114]; sat = a.max(-1) - a.min(-1)
    stone = (sat < 25) & (lum > 60) & (lum < 140) & ~is_mag(a)
    rock = (lum < 60) & (r >= b) & ~is_mag(a)
    lava = (r > 180) & (r - b > 100)
    return {'pierre': stone, 'roche_sombre': rock, 'lave': lava}


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
    lava = nd.binary_dilation(is_mag(a) | ((r - g > 90) & (b - g > 90)), iterations=2)
    # Pierre grise (mesurée (89,87,80), sat < 15) : grande composante = plateau et chemins.
    stone = (sat < 28) & (lum > 58) & (lum < 140) & ~lava
    stone = nd.binary_fill_holes(keep_large(open_(close_(stone, 2), 2), 20000)) & ~lava
    # Bouche : arche sombre (lum < 21, mesurée (22,17,16)) dans la fenêtre mesurée x 575-636, y 70-140, juste au-dessus du chemin ;
    # sans fenêtre, la composante sombre rejoignait tout le mur noir.
    win = (yy >= 70) & (yy < 140) & (xx >= 575) & (xx < 636)
    mouth = nd.binary_fill_holes(keep_large(close_((lum < 21) & win & ~lava & ~stone, 2), 500)) & ~stone
    rest = ~(lava | stone | mouth)
    rl, _ = nd.label(rest)
    top = set(np.unique(rl[:4][rest[:4]])) - {0}
    wall = np.isin(rl, list(top)) & (yy < 200)
    wall = nd.binary_fill_holes(wall | mouth) & ~mouth & ~stone & ~lava
    near = nd.binary_dilation(stone, iterations=6)
    touch = set(np.unique(rl[near & rest])) - {0}
    rims = np.isin(rl, list(touch)) & rest & ~wall
    spires = rest & ~wall & ~rims
    return dict(lave=lava, sol=stone, rebords=rims, mur=wall, aiguilles=spires, grotte=mouth)

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
    o.update(Name={'DefaultText': 'Entree Dark Crater - fosse de lave, sud vers nord (4:3)', 'LocalTexts': {}}, AssetName=ASSET,
             Released=False, TexSize=1, Music='', EdgeView=1, ViewCenter=None, ViewOffset={'X': 0, 'Y': 0},
             ActiveChar=None, Status={}, Layers=layers,
             Background={'$type': 'RogueEssence.Dungeon.LayeredBG, RogueEssence', 'Layers': []},
             Comment='PMDO 0.8.12. Rendu genere 4:3 reference sur le rip Dark Crater Pit ; lave generee aux 11 couleurs exactes '
                     'du rip en cycle de palette, bulles generees. Collisions de base a verifier. Seuil non raccorde. '
                     'Biome choisi par l agent.')
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
  <Name>Entree Dark Crater fosse sud-nord 4:3 - Atelier 0.8.12</Name>
  <Author>meromoonmeri</Author>
  <Description>Projet d'edition : fosse volcanique generee au format 4:3 (ref. rip Dark Crater Pit), lave en cycle de palette, bulles animees. Pas une aventure jouable.</Description>
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




# ---------------------------------------------------------------- lave et bulles
def lava_index(cols):
    """Chaque pixel de lave -> indice de la couleur de rampe la plus proche (11 couleurs exactes du rip)."""
    ramp = np.array(LAVA_RAMP, float)
    return ((cols[..., None, :].astype(float) - ramp[None, None]) ** 2).sum(-1).argmin(-1)


def lava_frames(k, mask, ts=range(LAVA_PHASES)):
    """Cycle de palette : indice + round(sin(2 pi t/12 + phi(x, y))), phi = onde oblique (créée par nous)."""
    yy, xx = np.mgrid[:H, :W]; phi = 2 * np.pi * (xx / 96 + yy / 64)
    ramp = np.array(LAVA_RAMP, 'uint8'); out = []
    for t in ts:
        kk = np.clip(k + np.rint(np.sin(2 * np.pi * t / LAVA_PHASES + phi)).astype(int), 0, len(LAVA_RAMP) - 1)
        f = np.zeros((H, W, 4), 'uint8'); f[..., :3] = ramp[kk]; f[..., 3] = 255; f[~mask] = 0
        out.append(f)
    return out


BUB_USED = [6, 7, 8, 9, 10]                        # gerbes x3, anneaux x2 (poses détourables de la planche)
BUB_K = 10                                         # réduction x1/10
BUB_SEQ = [0, 1, 2, 3, 3, 4, 4] + [-1] * 17         # 24 phases : éclatement, anneau qui s'élargit, repos


def bubble_poses(path):
    src = rgb(path); bg = is_mag(src) | ((src[..., 0] - src[..., 1] > 60) & (src[..., 2] - src[..., 1] > 60))
    lab, n = nd.label(nd.binary_dilation(~bg, iterations=8)); items = []
    for i, sl in enumerate(nd.find_objects(lab), 1):
        m = (lab[sl] == i) & ~bg[sl]
        if m.sum() > 1500:
            items.append((sl[0].start, sl[1].start, sl, m))
    rows = {}
    for it in sorted(items, key=lambda t: t[0]):
        key = next((r_ for r_ in rows if abs(r_ - it[0]) < 120), it[0]); rows.setdefault(key, []).append(it)
    items = [it for r_ in sorted(rows) for it in sorted(rows[r_], key=lambda t: t[1])]
    # Poses détourables choisies à la main par position (les rectangles de lave des rangées 1-2 se touchent et
    # fusionnent ; la rangée 4 est tramée) : gerbes (rangée 2 à droite, rangée 3 à gauche) puis anneaux (rangée 3).
    sel = [it for it in items if 280 <= it[2][0].start < 760 and not (it[2][0].start < 500 and it[2][1].start < 505)]
    assert len(sel) == len(BUB_USED), [(it[2][0].start, it[2][1].start) for it in items]
    px = np.concatenate([src[sl][m] for *_, sl, m in sel])
    q = Image.fromarray(px.reshape(-1, 1, 3).astype('uint8')).quantize(colors=8, method=Image.Quantize.MEDIANCUT)
    pal = np.array(q.getpalette()[:24], float).reshape(-1, 3); out = []
    for *_, sl, m in sel:
        s = src[sl].astype(float); hh, ww = (m.shape[0] // BUB_K) * BUB_K, (m.shape[1] // BUB_K) * BUB_K
        mb = m[:hh, :ww].reshape(hh // BUB_K, BUB_K, ww // BUB_K, BUB_K); cov = mb.mean((1, 3))
        col = (s[:hh, :ww] * m[:hh, :ww, None]).reshape(hh // BUB_K, BUB_K, ww // BUB_K, BUB_K, 3).sum((1, 3))
        col /= np.maximum(mb.sum((1, 3)), 1)[..., None]
        o = np.zeros((*cov.shape, 4), 'uint8')
        o[..., :3] = pal[((col[..., None, :] - pal[None, None]) ** 2).sum(-1).argmin(-1)]; o[..., 3] = 255
        o[cov < 0.4] = 0; out.append(o)
    return out, pal, len(items)


def bubble_frames(poses, spots, clip, ts=range(BUB_PHASES)):
    frames = []
    for t in ts:
        f = np.zeros((H, W, 4), 'uint8')
        for x, y, off in spots:
            p = BUB_SEQ[(t + off) % BUB_PHASES]
            if p >= 0:
                paste(f, poses[p], x, y)
        f[~clip] = 0; frames.append(f)
    return frames


def write_ora(path, layers):
    import xml.etree.ElementTree as ET
    root = ET.Element('image', w=str(W), h=str(H), name='Entree Dark Crater fosse sud-nord V1 (EDP1)')
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
    a = rgb(RAW / 'decor_magenta.png'); lv = rgb(RAW / 'lave_complete.png'); f = rgb(RAW / 'sol_complet.png'); ref = rgb(REF)
    assert a.shape[:2] == lv.shape[:2] == f.shape[:2] == (SRC[1], SRC[0])
    m = classify(a)
    order = ['lave', 'grotte', 'sol', 'aiguilles', 'mur', 'rebords']
    ex, cols = down_class(a, m, order)
    _, lcols = down_class(lv, m, order)                                  # même partition, pixels de la lave générée
    lava = ex['lave']
    layers = {'sol_complet': rgba(down_full(f), ~lava)}
    for k in STATIC:
        layers[k] = rgba(cols[k], ex[k])
    q = {}
    for keys, n in PALETTE_GROUPS.values():
        q.update(quantize_group({k: layers[k] for k in keys}, n))
    layers = q
    for k, v in ex.items():
        Image.fromarray((v * 255).astype('uint8')).save(OUT / 'masques' / f'{PFX}_masque_{k}.png')
    kidx = lava_index(lcols['lave'])
    lave = lava_frames(kidx, lava)
    land = np.zeros((H, W), bool)
    for k in STATIC:
        land |= layers[k][..., 3] == 255
    visible = lava & ~land
    bub, bub_pal, n_items = bubble_poses(RAW / 'bulles_poses.png')
    for i, p in enumerate(bub):
        Image.fromarray(p).save(OUT / 'poses' / f'{PFX}_bulle_{i}.png')
    dist = nd.distance_transform_edt(visible)
    cand = np.argwhere(dist > 16); rng = np.random.default_rng(4); spots = []
    for y, x in cand[rng.permutation(len(cand))]:
        if all(abs(x - sx) > 70 or abs(y - sy) > 70 for sx, sy, _ in spots):
            spots.append((int(x), int(y), (len(spots) * 3) % BUB_PHASES))
        if len(spots) == 12:
            break
    bulles = bubble_frames(bub, spots, visible)
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
    walk_px = layers['sol'][..., 3] == 255
    blocked = cell_grid(~walk_px); gh_, gw_ = blocked.shape
    pxs = np.nonzero(walk_px[H - 8])[0]; med = int(np.median(pxs)) // 8
    ecol = min((c for c in range(gw_ - 1) if not blocked[gh_ - 2:, c:c + 2].any()), key=lambda c: abs(c - med))
    entry_px = [ecol * 8, H - 16]
    gy, gx = np.nonzero(ex['grotte']); cx = int(gx.mean())
    threshold_px = [cx // 8 * 8 - 8, (int(gy.max()) + 1 + 7) // 8 * 8]
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
    cw = max(max(p.shape[:2]) for p in bub) * 4 + 8
    sheet = Image.new('RGBA', (len(bub) * cw, cw), (60, 20, 20, 255))
    for i, p in enumerate(bub):
        im = Image.fromarray(p); sheet.alpha_composite(im.resize((im.width * 4, im.height * 4), Image.Resampling.NEAREST), (i * cw + 4, 4))
    sheet.save(OUT / 'review' / f'{PFX}_planche_poses.png')
    write_ora(OUT / f'{PFX}_entree_dark_crater_pit_calques.ora',
              {f'{i:02d}_{t}' + ('_f00' if len(fr) > 1 else ''): fr[0] for i, (t, fr, _) in enumerate(stack_named)})
    counts = ground_project([(t.replace('_', ' ') + (f' {len(fr)} phases' if len(fr) > 1 else ''), fr, tk)
                             for t, fr, tk in stack_named], blocked, entry_px, threshold_px, gfx, tools)
    fid = fidelity(a, ref)
    fid['lave'] = fidelity(lv, ref)['lave']                               # lave : mesurée sur le brut lave_complete
    final_fid = {}
    for k, nm in (('pierre', 'sol'), ('roche_sombre', 'rebords')):
        lay = layers[nm]; px = lay[lay[..., 3] == 255][:, :3].astype(float)
        sel = materials(px.reshape(-1, 1, 3))[k][:, 0]
        px = px[sel] if sel.sum() > 50 else px
        final_fid[k] = {'calque': nm, 'rgb': [round(float(v), 1) for v in px.mean(0)],
                        'distance_rip': round(float(np.linalg.norm(px.mean(0) - np.array(fid[k]['rip_rgb']))), 1)}
    manifest = {
        'lot': 'entree_dark_crater_pit_sud_nord_v1', 'prefix': PFX, 'format': '4:3 vaste', 'size_px': [W, H],
        'grid_8px': [W // 8, H // 8], 'base': 'branche de session (EMF1 pour les utilitaires) ; aucun emprunt aux branches soeurs',
        'biome': 'Dark Crater Pit, choisi par l agent (« passe a la suite »)',
        'method': 'textures canoniques = rendu genere REFERENCE : rip passe au generateur ; decor complet sur magenta '
                  '(lave = magenta), lave completee par edition du decor, sol complet edite, planche de bulles sur magenta',
        'reference_da': {'file': REF.name, 'sha256': sha(REF), 'titre': 'Fosse de Dark Crater (PMD Explorers)'},
        'generation': GEN,
        'raw_inputs': [{'file': f'source/entree_dark_crater_pit_sud_nord_v1/bruts/{g["file"]}', 'sha256': sha(RAW / g['file']),
                        'size': list(Image.open(RAW / g['file']).size)} for g in GEN],
        'fidelite_rip': {'methode': 'moyenne RGB par matiere, meme classifieur pixel sur le rip et sur le brut ; distance euclidienne',
                         'brut': fid, 'calques_finaux': final_fid,
                         'lave_finale': 'couleurs EXACTES du rip (11 couleurs de rampe)'},
        'normalization': {'scale': JM.SCALE, 'scaled': [JM.SCALED_W, H], 'crop_x': [JM.CROP_X, JM.SCALED_W - W - JM.CROP_X],
                          'methode': 'moyenne ponderee par classe (BOX), attribution exclusive par poids maximal ; meme partition '
                                     'appliquee au brut lave_complete',
                          'palettes': {g: {'calques': k, 'couleurs': n} for g, (k, n) in PALETTE_GROUPS.items()}},
        'segmentation': 'lave = magenta dilate 2 px ; sol = pierre grise (sat < 28, 58 < lum < 140), grande composante ; '
                        'grotte = lum < 21 dans la fenetre x 575-636, y 70-140 ; mur = composantes du reste touchant le bord '
                        'nord (y < 200) ; rebords = composantes au contact du sol (6 px) ; aiguilles = le reste',
        'layers': layer_list,
        'lave': {'phases': LAVA_PHASES, 'frame_length_ticks': LAVA_TICKS, 'rampe': [list(c) for c in LAVA_RAMP],
                 'modele': 'indice de rampe du pixel genere + round(sin(2 pi t/12 + 2 pi (x/96 + y/64)))',
                 'origine': 'motif GENERE (lave_complete), couleurs EXACTES du rip, cycle cree par nous'},
        'bulles': {'poses_planche': n_items, 'poses_utilisees': BUB_USED, 'reduction': f'x1/{BUB_K}',
                   'palette': [[int(c) for c in p] for p in bub_pal], 'chronologie': BUB_SEQ, 'points': [list(s_) for s_ in spots],
                   'phases': BUB_PHASES, 'frame_length_ticks': BUB_TICKS,
                   'origine': 'dessin GENERE ; chronologie et placement crees par nous'},
        'scene_loop_ticks': LOOP_TICKS,
        'access': {'entry_px': entry_px, 'threshold_px': threshold_px, 'path_found_16x16': ok, 'cells_explored': explored,
                   'blocked_cells': int(blocked.sum()), 'total_cells': int(blocked.size), 'walkable_cells': int((~blocked).sum()),
                   'rule': 'case bloquee si > 25 % hors pierre grise', 'seuil': 'haut du pont de pierre, devant la grotte'},
        'pmdo': {'target': '0.8.12', 'asset': ASSET, 'namespace': NAMESPACE, 'tiles_per_bank': counts, 'banks': list(counts),
                 'runtime_tested': False, 'warp': 'aucun'},
        'art_approved': False,
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    shutil.copyfile(OUT / 'manifest.json', STAGE / 'manifest.json')
    print(json.dumps({'entry': entry_px, 'threshold': threshold_px, 'walkable': int((~blocked).sum()), 'items': n_items,
                      'spots': len(spots), 'fidelite': {k: v['distance'] for k, v in fid.items()},
                      'final': {k: v['distance_rip'] for k, v in final_fid.items()}, 'tiles': sum(counts.values())}))


if __name__ == '__main__':
    build()
