"""Entrée Cratère sud -> nord V1 — rendu généré, référence PMD Sky « Dark Crater ».

Même méthode que l'Entrée Vapeur : décor complet généré sur magenta (lave = magenta), sol complet
généré séparément, normalisation uniforme exacte x0,5 (848x1264 -> 424x632), moyenne 2x2 par classe.
Animations, chacune sur son calque :
- lave « façon rivière Métano » : structure/cadence Métano (4 phases x 10 ticks) recalculée sur nos mares,
  palette tirée de la matière de lave générée (bruts/lave_matiere.png) ;
- éclats : pixels réels Metano_Town_River_Sparkles recolorés en tons de lave, 4 x 10 ticks ;
- bulles de lave : planche générée 2 x 6 (12 poses distinctes), 24 phases x 5 ticks, émetteurs décalés ;
- braises des roches : pixels orange du décor, pulsation créée 6 phases x 10 ticks.
Scène complète : PPCM 120 ticks = 2 s.
Lancer : .venv/bin/python source/entree_cratere_sud_nord_v1/build.py
"""
from pathlib import Path
import hashlib, importlib.util, io, json, shutil, uuid, zipfile

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
RAW = HERE / 'bruts'
OUT = R / 'renders/entree_cratere_sud_nord_v1'
STAGE = R / '.cache/entree_cratere_sud_nord_v1/entree_cratere_sud_nord'
NAMESPACE = 'entree_cratere_sud_nord'
ASSET = 'ecn1_entree_cratere'
PFX = 'ECN1'
W, H = 424, 632
FULL = (848, 1264)
LAVA_PHASES, LAVA_TICKS = 4, 10
EMBER_PHASES, EMBER_TICKS = 6, 10
BUBBLE_PHASES, BUBBLE_TICKS = 24, 5
LOOP_TICKS = 120
CELL = 24
PALETTE_COLORS = 96
METANO_SPARK = R / 'source/eau_metano/natifs/Metano_Town_River_Sparkles.tile'
M_SURFACE = (131, 218, 230)

# Palette de lave : teintes de la matière générée (quantification 8 couleurs), rôles et ordre Métano.
PAL = {'lip': (70, 20, 26), 'bande': (120, 26, 22), 'inter': (194, 40, 8), 'accent': (232, 72, 6),
       'surface': (246, 108, 10), 'chaud': (252, 150, 12), 'jaune': (253, 184, 30), 'clair': (253, 227, 121)}


def loadmod(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rgb(p):
    return np.array(Image.open(p).convert('RGB')).astype(int)


def keep_large(mask, minimum):
    lab, n = nd.label(mask)
    if n == 0:
        return mask
    return np.isin(lab, 1 + np.flatnonzero(nd.sum(mask, lab, range(1, n + 1)) >= minimum))


# ---------------------------------------------------------------- segmentation (pleine résolution)
def classify(a):
    r, g, b = a.transpose(2, 0, 1); lum = a @ [.299, .587, .114]; sat = a.max(2) - a.min(2)
    mag = (r > g * 1.6) & (b > g * 1.4) & (r > 120) & (b > 100)
    lava = nd.binary_dilation(mag, iterations=1)                  # mange le liseré antialiasé
    ember = (r > 170) & (g > 60) & (g < 200) & (b < 90) & (r > b + 100)
    # Mesures : cendre sat ~10 / écart lum ~12 ; roche sat ~23 ou écart lum ~20 (fenêtre 11 px).
    S = nd.uniform_filter(sat.astype(float), 11)
    V = np.sqrt(np.maximum(nd.uniform_filter(lum ** 2, 11) - nd.uniform_filter(lum, 11) ** 2, 0))
    rock = ((S > 16) | (V > 17)) & ~lava
    rock = nd.binary_opening(nd.binary_closing(rock, iterations=3), iterations=2)
    void = (np.abs(r - 50) < 10) & (np.abs(g - 20) < 9) & (np.abs(b - 43) < 10)
    rock = nd.binary_fill_holes(keep_large(rock, 1500) | nd.binary_opening(void, iterations=2)) & ~lava
    yy, xx = np.mgrid[:a.shape[0], :a.shape[1]]
    box = (yy > 200) & (yy < 340) & (xx > 340) & (xx < 510)
    mouth = nd.binary_fill_holes(nd.binary_closing(box & (lum < 30), iterations=2))
    mouth = keep_large(mouth, int(nd.sum(mouth, nd.label(mouth)[0], range(1, nd.label(mouth)[1] + 1)).max()))
    rock &= ~mouth
    ember &= rock
    # Rebords des mares : roche à moins de 22 px de la lave, dans la moitié sud praticable.
    near = nd.binary_dilation(lava, iterations=22)
    rims = rock & near & (yy > 560)
    cliffs = rock & ~rims
    ash = ~(rock | lava | mouth)
    return dict(lava=lava, ash=ash, rims=rims, cliffs=cliffs, mouth=mouth, ember=ember)


def down_mask(m):
    return m.reshape(H, 2, W, 2).sum((1, 3)) >= 2


def down_colors(a, m):
    w = m.reshape(H, 2, W, 2).astype(float)
    s = (a.reshape(H, 2, W, 2, 3) * w[..., None]).sum((1, 3)); n = w.sum((1, 3))[..., None]
    return np.clip(np.round(s / np.maximum(n, 1)), 0, 255).astype('uint8')


def exclusive(masks, order):
    counts = np.stack([masks[k].reshape(H, 2, W, 2).sum((1, 3)) for k in order])
    win = counts.argmax(0); has = counts.max(0) >= 2
    return {k: (win == i) & has for i, k in enumerate(order)}


def rgba(colors, mask):
    out = np.zeros((H, W, 4), 'uint8'); out[..., :3] = colors; out[..., 3] = 255; out[~mask] = 0
    return out


def quantize_layers(layers):
    opaque = np.concatenate([l[l[..., 3] == 255][:, :3] for l in layers.values()])
    pal_img = Image.fromarray(opaque.reshape(-1, 1, 3)).quantize(colors=PALETTE_COLORS, method=Image.Quantize.MEDIANCUT,
                                                                 dither=Image.Dither.NONE)
    pal = np.array(pal_img.getpalette()[:PALETTE_COLORS * 3], 'uint8').reshape(-1, 3)
    out = {}
    for k, l in layers.items():
        a = l.copy(); m = a[..., 3] == 255
        if m.any():
            a[..., :3] = pal[np.array(Image.fromarray(a[..., :3]).quantize(palette=pal_img, dither=Image.Dither.NONE))]
        a[~m] = 0; out[k] = a
    return out


# ---------------------------------------------------------------- lave façon Métano
def hash_noise(seed):
    return nd.gaussian_filter(np.random.default_rng(seed).random((H, W)), 1.0)


def lava_phases(lava, visible):
    d = nd.distance_transform_edt(visible)
    yy, xx = np.mgrid[:H, :W]
    jag = hash_noise(5); jag = (jag - jag.min()) / np.ptp(jag)
    frames = []
    for t in range(LAVA_PHASES):
        ph = 2 * np.pi * t / LAVA_PHASES
        n = 0.6 * np.sin(xx * 0.23 + yy * 0.11 - ph) + 0.4 * np.sin(xx * 0.07 - yy * 0.21 + 1.3 - ph)
        T = 3.6 + 0.9 * n                              # mares plus petites que les bassins : bande un peu plus fine
        jr = np.roll(jag, t * 2, axis=1); fringe = T + 0.6 + 2.4 * jr
        a = np.zeros((H, W, 4), 'uint8'); a[..., 3] = 255; a[..., :3] = PAL['surface']
        a[d <= fringe] = (*PAL['accent'], 255)
        a[(d <= fringe) & (jr > 0.62)] = (*PAL['chaud'], 255)   # stries chaudes dans la frange
        a[d <= T] = (*PAL['inter'], 255)
        a[d <= T - 1] = (*PAL['bande'], 255)
        a[(d <= 1.0) & (np.sin(xx * 0.5 + yy * 0.3 - ph) > -0.35)] = (*PAL['lip'], 255)   # croûte refroidie
        a[~lava] = 0; a[lava & ~visible] = (*PAL['bande'], 255)
        frames.append(a)
    return frames, d


def sparkle_families():
    v2 = loadmod('esn2_tiles', R / 'source/entree_vapeur_sud_nord_v2/build.py')
    t = v2.decode_tile(METANO_SPARK)

    def cluster(cols, rows, step):
        out = []
        for k in range(4):
            a = np.zeros((len(rows) * 8, len(cols) * 8, 4), 'uint8')
            for j, r in enumerate(rows):
                for i, c in enumerate(cols):
                    a[j*8:j*8+8, i*8:i*8+8] = t[c, r + step * k]
            out.append(a)
        return out
    fams = {'A_16x24': cluster([0, 1], [0, 1, 2], 3), 'B_24x16': cluster([2, 3, 4], [0, 1], 2)}
    res = {}
    for name, frames in fams.items():
        conv = []
        for a in frames:
            o = np.zeros_like(a)
            m = (a[..., 3] == 255) & (np.abs(a[..., :3].astype(int) - M_SURFACE).sum(2) > 0)
            lum = a[..., :3].astype(float) @ [.299, .587, .114]
            # recoloration par luminance : les pixels les plus clairs -> jaune pâle, puis jaune, puis chaud
            o[m & (lum >= 240), :3] = PAL['clair']; o[m & (lum < 240) & (lum >= 215), :3] = PAL['jaune']
            o[m & (lum < 215), :3] = PAL['chaud']; o[m, 3] = 255
            conv.append(o)
        res[name] = conv
    return res


# ---------------------------------------------------------------- bulles de lave générées
PICKS = [('point', 0, 0), ('petite', 0, 1), ('ronde', 0, 2), ('dome', 0, 3), ('fissure', 0, 4), ('eclatement', 0, 5),
         ('couronne', 1, 0), ('croute', 1, 1), ('anneau', 1, 2), ('anneau_pale', 1, 3), ('etincelles', 1, 4),
         ('etincelles_fin', 1, 5)]
BUBBLE_TIMELINE = (['point'] * 2 + ['petite'] * 2 + ['ronde'] * 2 + ['dome'] * 2 + ['fissure'] * 2 + ['eclatement'] +
                   ['couronne'] + ['croute'] * 2 + ['anneau'] * 2 + ['anneau_pale'] + ['etincelles'] + ['etincelles_fin'])


def bubble_poses():
    src = rgb(RAW / 'bulles_lave_poses.png'); h, w = src.shape[:2]
    r, g, b = src.transpose(2, 0, 1)
    mag = (r > 150) & (b > 110) & (g < 120) & (r > g * 1.6) & (b > g * 1.3)
    cw, ch = w / 6, h / 2
    win = 288; k = win // CELL
    pal = np.array(list(PAL.values()), int); pal_lum = pal @ [.299, .587, .114]
    raw = {}
    for name, ry, cx in PICKS:
        x0 = int((cx + 0.5) * cw) - win // 2
        cell_mask = ~mag[int(ry * ch):int((ry + 1) * ch), int(cx * cw):int((cx + 1) * cw)]
        ys = np.nonzero(cell_mask.any(1))[0]
        # base commune par rangée (mesurée sur la planche) : bas de la bulle / de l'éclaboussure
        base = int(ry * ch) + (300 if ry == 0 else 262)
        y0 = base - int(win * 20 / 24)
        pad = np.zeros((win, win, 3), int); pm = np.zeros((win, win), bool)
        sy0, sx0 = max(0, y0), max(0, x0); sy1, sx1 = min(h, y0 + win), min(w, x0 + win)
        pad[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = src[sy0:sy1, sx0:sx1]
        pm[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = ~mag[sy0:sy1, sx0:sx1]
        # ne garder que ce qui appartient à la case (pas de débordement d'une pose voisine)
        cx0, cx1 = int(cx * cw) - x0, int((cx + 1) * cw) - x0; cy0, cy1 = int(ry * ch) - y0, int((ry + 1) * ch) - y0
        keepbox = np.zeros_like(pm); keepbox[max(0, cy0):max(0, cy1), max(0, cx0):max(0, cx1)] = True; pm &= keepbox
        cov = pm.reshape(CELL, k, CELL, k).mean((1, 3))
        col = (pad * pm[..., None]).reshape(CELL, k, CELL, k, 3).sum((1, 3)) / np.maximum(pm.reshape(CELL, k, CELL, k).sum((1, 3)), 1)[..., None]
        thin = name in ('anneau', 'anneau_pale', 'etincelles', 'etincelles_fin', 'point', 'eclatement', 'couronne')
        keep = cov >= (0.06 if thin else 0.2)
        # couleur la plus proche en RGB dans la palette de lave (la planche est déjà dans ces tons)
        dist = ((col[..., None, :] - pal[None, None]) ** 2).sum(-1)
        o = np.zeros((CELL, CELL, 4), 'uint8'); o[..., :3] = pal[dist.argmin(-1)]; o[..., 3] = 255; o[~keep] = 0
        raw[name] = o
    # L'anneau pâle généré est mêlé au magenta (rose pâle) et disparaît au détourage : dérivé de l'anneau,
    # teinte 'accent' proche de la surface pour l'effet d'estompe.
    derived = []
    if (raw['anneau_pale'][..., 3] > 0).sum() < 0.5 * (raw['anneau'][..., 3] > 0).sum():
        ap = raw['anneau'].copy(); ap[ap[..., 3] > 0, :3] = PAL['accent']; raw['anneau_pale'] = ap
        derived.append('anneau_pale = anneau recolore accent (brut mele au magenta)')
    bubble_poses.derived = derived
    return raw


# ---------------------------------------------------------------- utilitaires carte
def place(free, size, count, seed, taken, core=None):
    rng = np.random.default_rng(seed); out = []
    hh, ww = size
    cands = [(y, x) for y in range(0, H - hh + 1, 8) for x in range(0, W - ww + 1, 8)]; rng.shuffle(cands)
    for y, x in cands:
        if core:
            c0 = (hh - core) // 2; ok = free[y + c0:y + c0 + core, x + c0:x + c0 + core].all()
        else:
            ok = free[y:y + hh, x:x + ww].all()
        if ok and not taken[max(0, y - 4):y + hh + 4, max(0, x - 4):x + ww + 4].any():
            out.append((y, x)); taken[y:y + hh, x:x + ww] = True
            if len(out) == count:
                break
    return out


def cell_grid(block):
    return block.reshape(H // 8, 8, W // 8, 8).mean((1, 3)) > 0.25


def ground_project(tracks, static, blocked, entry_px, threshold_px, gfx, tools):
    if STAGE.exists():
        shutil.rmtree(STAGE)
    with zipfile.ZipFile(R / 'mod_metano_expeditions_pmdo_0812.zip') as z:
        tpl = json.loads(z.read('metano_expeditions/Data/Ground/v50812_01_crete_sillage_jour.rsground'))
    o = tpl['Object']; gw, gh = W // 8, H // 8; layers, banks = [], []
    order = [('track', t) for t in tracks[:2]] + [('static', ('sol_complet', static['sol_complet']))] + \
            [('track', tracks[2])] + [('static', (k, v)) for k, v in static.items() if k != 'sol_complet'] + [('track', tracks[3])]
    for i, (kind, item) in enumerate(order):
        if kind == 'track':
            title, frames, ticks = item
        else:
            title, frames, ticks = item[0], [item[1]], 60
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
    o.update(Name={'DefaultText': 'Entree Cratere - sud vers nord', 'LocalTexts': {}}, AssetName=ASSET, Released=False,
             TexSize=1, Music='', EdgeView=1, ViewCenter=None, ViewOffset={'X': 0, 'Y': 0}, ActiveChar=None, Status={},
             Layers=layers, Background={'$type': 'RogueEssence.Dungeon.LayeredBG, RogueEssence', 'Layers': []},
             Comment='PMDO 0.8.12. Rendu genere (ref. Dark Crater) ; lave facon riviere Metano, eclats Metano recolores, '
                     'bulles de lave generees, braises pulsees. Collisions de base a verifier. Seuil non raccorde.')
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
  <Name>Entree Cratere sud-nord - Atelier 0.8.12</Name>
  <Author>meromoonmeri</Author>
  <Description>Projet d'edition : entree de cratere generee (ref. Dark Crater), lave, eclats, bulles et braises animes. Pas une aventure jouable.</Description>
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
    return [l['Name'] if 'Name' in l else None for l in layers], {b.name: len(b.data) for b in banks}


def write_ora(path, layers):
    import xml.etree.ElementTree as ET
    root = ET.Element('image', w=str(W), h=str(H), name='Entree Cratere sud-nord V1')
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
    for d in ['calques', 'animation/lave', 'animation/eclats', 'animation/bulles', 'animation/braises', 'poses_bulles',
              'masques', 'review']:
        (OUT / d).mkdir(parents=True, exist_ok=True)
    a = rgb(RAW / 'decor_magenta.png'); f = rgb(RAW / 'sol_complet.png')
    assert a.shape[:2] == f.shape[:2] == (FULL[1], FULL[0])
    m = classify(a)
    fmag = (f[..., 0] > f[..., 1] * 1.6) & (f[..., 2] > f[..., 1] * 1.4) & (f[..., 0] > 120)
    assert fmag.sum() == 0, 'sol complet : magenta résiduel'
    ex = exclusive(m, ['lava', 'ash', 'rims', 'cliffs', 'mouth'])
    lava = ex['lava']
    ember_full = m['ember']
    ember = down_mask(ember_full) & (ex['cliffs'] | ex['rims'])
    floor_mask = ~lava
    layers = {
        'sol_complet': rgba(down_colors(f, np.ones(FULL[::-1], bool)), floor_mask),
        'cendre': rgba(down_colors(a, m['ash']), ex['ash']),
        'rebords_mares': rgba(down_colors(a, m['rims'] & ~ember_full), ex['rims']),
        'falaises': rgba(down_colors(a, m['cliffs'] & ~ember_full), ex['cliffs']),
        'bouche_cratere': rgba(down_colors(a, m['mouth']), ex['mouth']),
    }
    layers = quantize_layers(layers)
    for k, v in ex.items():
        Image.fromarray((v * 255).astype('uint8')).save(OUT / 'masques' / f'{PFX}_masque_{k}.png')
    Image.fromarray((ember * 255).astype('uint8')).save(OUT / 'masques' / f'{PFX}_masque_braises.png')
    land = np.zeros((H, W), bool)
    for k in ['cendre', 'rebords_mares', 'falaises', 'bouche_cratere']:
        land |= layers[k][..., 3] == 255
    visible = lava & ~land
    lf, dist = lava_phases(lava, visible)
    # Braises : pulsation 6 phases sur la couleur d'origine (rang de luminance 0..2) — calque au-dessus des falaises.
    lum_e = down_colors(a, ember_full).astype(float) @ [.299, .587, .114]
    rank = np.clip(np.digitize(lum_e, np.percentile(lum_e[ember], [33, 66])), 0, 2) if ember.any() else np.zeros((H, W), int)
    ramp = [PAL['bande'], PAL['inter'], PAL['surface'], PAL['jaune'], PAL['clair']]
    pulse = [0, 1, 2, 2, 1, 0]
    ef = []
    for t in range(EMBER_PHASES):
        e = np.zeros((H, W, 4), 'uint8'); idx = np.clip(rank + pulse[t], 0, 4)
        for i, c in enumerate(ramp):
            e[ember & (idx == i)] = (*c, 255)
        ef.append(e)
    # Bulles d'abord (place limitée), puis éclats.
    taken = np.zeros((H, W), bool)
    poses = bubble_poses()
    for k, p in poses.items():
        Image.fromarray(p).save(OUT / 'poses_bulles' / f'{PFX}_bulle_{k}.png')
    emitters = place(visible & (dist > 3), (CELL, CELL), 7, 3, taken, core=8)
    offsets = [(i * 7) % BUBBLE_PHASES for i in range(len(emitters))]
    bf = [np.zeros((H, W, 4), 'uint8') for _ in range(BUBBLE_PHASES)]
    for (y, x), off in zip(emitters, offsets):
        for t in range(BUBBLE_PHASES):
            k = (t - off) % BUBBLE_PHASES
            if k < len(BUBBLE_TIMELINE):
                p = poses[BUBBLE_TIMELINE[k]]; mm = p[..., 3] > 0
                bf[t][y:y+CELL, x:x+CELL][mm] = p[mm]
    fams = sparkle_families(); sf = [np.zeros((H, W, 4), 'uint8') for _ in range(LAVA_PHASES)]; sparkles = []
    for fi, (name, frames) in enumerate(fams.items()):
        hh, ww = frames[0].shape[:2]
        for (y, x) in place(visible & (dist > 2), (hh, ww), 3, 17 + fi, taken, core=8):
            sparkles.append({'famille': name, 'xy': [x, y]})
            for t in range(LAVA_PHASES):
                mm = frames[t][..., 3] > 0; sf[t][y:y+hh, x:x+ww][mm] = frames[t][mm]
    for arr in bf + sf:
        arr[~visible] = 0
    # Exports
    for t, fr in enumerate(lf):
        Image.fromarray(fr).save(OUT / 'animation/lave' / f'{PFX}_00_lave_f{t}.png')
    for t, fr in enumerate(sf):
        Image.fromarray(fr).save(OUT / 'animation/eclats' / f'{PFX}_01_eclats_f{t}.png')
    for t, fr in enumerate(bf):
        Image.fromarray(fr).save(OUT / 'animation/bulles' / f'{PFX}_03_bulles_f{t:02d}.png')
    for t, fr in enumerate(ef):
        Image.fromarray(fr).save(OUT / 'animation/braises' / f'{PFX}_08_braises_f{t}.png')
    static_order = ['sol_complet', 'cendre', 'rebords_mares', 'falaises', 'bouche_cratere']
    numbers = {'sol_complet': 2, 'cendre': 4, 'rebords_mares': 5, 'falaises': 6, 'bouche_cratere': 7}
    files = {}
    for k in static_order:
        fn = f'{PFX}_{numbers[k]:02d}_{k}.png'; Image.fromarray(layers[k]).save(OUT / 'calques' / fn); files[k] = fn
    # Collisions et accès : seule la cendre visible est praticable.
    walk = layers['cendre'][..., 3] == 255
    blocked = cell_grid(~walk)
    rows = np.nonzero(walk[-16:].all(0))[0]
    ex_ = int(np.median(np.nonzero(walk[H - 8])[0])); entry_px = [ex_ // 8 * 8 - 8, H - 16]
    mb = np.nonzero(ex['mouth'])
    mx_ = int(mb[1].mean()); my_ = int(mb[0].max())
    threshold_px = [mx_ // 8 * 8 - 8, (my_ + 8) // 8 * 8]
    ok, explored = v1.reachable(blocked, (entry_px[1] // 8, entry_px[0] // 8), (threshold_px[1] // 8, threshold_px[0] // 8))
    assert ok, 'pas de chemin 16x16'
    # Scènes
    def scene(tick, with_ember=True):
        lp = (tick // LAVA_TICKS) % LAVA_PHASES; bp = (tick // BUBBLE_TICKS) % BUBBLE_PHASES; ep = (tick // EMBER_TICKS) % EMBER_PHASES
        im = Image.fromarray(lf[lp]); im.alpha_composite(Image.fromarray(sf[lp]))
        im.alpha_composite(Image.fromarray(layers['sol_complet'])); im.alpha_composite(Image.fromarray(bf[bp]))
        for k in static_order[1:]:
            im.alpha_composite(Image.fromarray(layers[k]))
        im.alpha_composite(Image.fromarray(ef[ep]))
        return im
    scenes = [scene(t * BUBBLE_TICKS) for t in range(LOOP_TICKS // BUBBLE_TICKS)]
    scenes[0].save(OUT / 'review' / f'{PFX}_scene_t000.png')
    scenes[0].save(OUT / 'review' / f'{PFX}_scene_animee.webp', save_all=True, append_images=scenes[1:],
                   duration=round(BUBBLE_TICKS * 1000 / 60), loop=0, lossless=True)
    col = scenes[0].copy(); ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(ov)
    for y, x in zip(*np.nonzero(blocked)):
        dr.rectangle([x*8, y*8, x*8+7, y*8+7], fill=(220, 40, 40, 90))
    for (px, py), c in ((entry_px, (255, 230, 40, 255)), (threshold_px, (60, 220, 255, 255))):
        dr.rectangle([px, py, px + 15, py + 15], outline=c, width=2)
    col.alpha_composite(ov); col.save(OUT / 'review' / f'{PFX}_collisions_marqueurs.png')
    sheet = Image.new('RGBA', (len(poses) * (CELL * 5 + 5), CELL * 5), (*PAL['surface'], 255))
    for i, p in enumerate(poses.values()):
        sheet.alpha_composite(Image.fromarray(p).resize((CELL * 5, CELL * 5), Image.Resampling.NEAREST), (i * (CELL * 5 + 5), 0))
    sheet.save(OUT / 'review' / f'{PFX}_planche_bulles_x5.png')
    ora = {'00_lave_f0': lf[0], '01_eclats_f0': sf[0], '02_sol_complet': layers['sol_complet'], '03_bulles_f00': bf[0],
           **{f'{numbers[k]:02d}_{k}': layers[k] for k in static_order[1:]}, '08_braises_f0': ef[0]}
    write_ora(OUT / f'{PFX}_entree_cratere_calques.ora', ora)
    tracks = [('Lave facon riviere Metano 4 phases', lf, LAVA_TICKS), ('Eclats Metano recolores 4 phases', sf, LAVA_TICKS),
              ('Bulles de lave 24 phases', bf, BUBBLE_TICKS), ('Braises pulsees 6 phases', ef, EMBER_TICKS)]
    _, counts = ground_project(tracks, {k: layers[k] for k in static_order}, blocked, entry_px, threshold_px, gfx, tools)
    order = ([f'animation/lave/{PFX}_00_lave_fX.png', f'animation/eclats/{PFX}_01_eclats_fX.png', f'calques/{files["sol_complet"]}',
              f'animation/bulles/{PFX}_03_bulles_fXX.png'] + [f'calques/{files[k]}' for k in static_order[1:]] +
             [f'animation/braises/{PFX}_08_braises_fX.png'])
    manifest = {
        'lot': 'entree_cratere_sud_nord_v1', 'size_px': [W, H], 'grid_8px': [W // 8, H // 8],
        'method': 'rendu genere : decor complet sur magenta (lave = magenta) + sol complet genere separement',
        'reference_da': 'Dark_Crater_entrance_TDS.png',
        'raw_inputs': [{'file': f'source/entree_cratere_sud_nord_v1/bruts/{n}', 'sha256': sha(RAW / n),
                        'size': list(Image.open(RAW / n).size)} for n in
                       ['decor_magenta.png', 'sol_complet.png', 'lave_matiere.png', 'bulles_lave_poses.png']],
        'normalization': 'x0.5 exact (848x1264 -> 424x632), moyenne 2x2 par classe, palette commune 96 couleurs',
        'segmentation': 'lave = magenta plein dilate 1 px ; roche = saturation lissee > 16 ou ecart de luminance > 17 (fenetre 11 px) ; '
                        'bouche = pixels < 30 dans la cavite ; rebords = roche a < 22 px de la lave dans la moitie sud ; braises = orange sur roche',
        'layer_order_bottom_to_top': order,
        'lava': {'phases': LAVA_PHASES, 'frame_length_ticks': LAVA_TICKS, 'couleurs': {k: list(v) for k, v in PAL.items()},
                 'modele': 'structure et cadence de la riviere Metano (comme ESN2), recalculees sur nos mares ; palette de la matiere generee',
                 'origine': 'pixels recalcules, pas de tuiles natives'},
        'sparkles': {'source': 'source/eau_metano/natifs/Metano_Town_River_Sparkles.tile', 'placements': sparkles,
                     'origine': 'pixels Metano reels recolores en tons de lave par luminance'},
        'bubbles': {'brut': 'source/entree_cratere_sud_nord_v1/bruts/bulles_lave_poses.png', 'poses': [p[0] for p in PICKS],
                    'reduction': 'fenetre 288 px -> 24 px (x1/12) identique, base commune par rangee, palette de lave',
                    'timeline_phases': BUBBLE_TIMELINE, 'phases': BUBBLE_PHASES, 'frame_length_ticks': BUBBLE_TICKS,
                    'emetteurs': [{'xy': [x, y], 'decalage': o} for (y, x), o in zip(emitters, offsets)],
                    'derivees': getattr(bubble_poses, 'derived', []),
                    'origine': 'dessin GENERE (12 poses recues comme demande), chronologie creee ; pas une animation officielle'},
        'embers': {'phases': EMBER_PHASES, 'frame_length_ticks': EMBER_TICKS, 'pulse_offsets': pulse, 'pixels': int(ember.sum()),
                   'origine': 'pixels orange du decor genere ; pulsation creee'},
        'scene_loop_ticks': LOOP_TICKS,
        'access': {'entry_px': entry_px, 'threshold_px': threshold_px, 'path_found_16x16': ok, 'cells_explored': explored,
                   'blocked_cells': int(blocked.sum()), 'total_cells': int(blocked.size),
                   'rule': 'case bloquee si > 25 % hors cendre visible (lave, roche, rebords, bouche)'},
        'pmdo': {'target': '0.8.12', 'asset': ASSET, 'namespace': NAMESPACE, 'tiles_per_bank': counts, 'banks': list(counts),
                 'runtime_tested': False, 'warp': 'aucun'},
        'art_approved': False,
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    shutil.copyfile(OUT / 'manifest.json', STAGE / 'manifest.json')
    print(json.dumps({'emitters': len(emitters), 'sparkles': len(sparkles), 'embers': int(ember.sum()),
                      'entry': entry_px, 'threshold': threshold_px, 'blocked': int(blocked.sum()), 'tiles': counts}, indent=1))


if __name__ == '__main__':
    build()
