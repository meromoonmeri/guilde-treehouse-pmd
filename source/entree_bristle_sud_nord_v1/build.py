"""Entrée Bristle sud -> nord V1 — rendu généré, référence PMD « Mt. Bristle ».

Méthode rendu généré (comme ESN1/ECN1) : décor complet sur magenta (torrent = magenta), sol de sable complet
généré séparément, normalisation x0,5 exacte (848x1264 -> 424x632), moyenne 2x2 par classe.
Animations, chacune sur son calque :
- torrent « façon rivière Métano » avec les COULEURS EXACTES de la rivière Métano (biome de jour), 4 x 10 ticks ;
- scintillements Metano_Town_River_Sparkles NATIFS (pixels et couleurs inchangés), 4 x 10 ticks ;
- touffes d'herbe au vent : planche générée 4 x 6, poses ordonnées par inclinaison MESURÉE, 12 phases x 10 ticks,
  décalage par colonne (rafale d'ouest en est). Elles remplacent les touffes du décor à leurs positions.
Scène : PPCM 120 ticks = 2 s.
Lancer : .venv/bin/python source/entree_bristle_sud_nord_v1/build.py
"""
from pathlib import Path
import hashlib, importlib.util, io, json, shutil, uuid, zipfile

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
RAW = HERE / 'bruts'
OUT = R / 'renders/entree_bristle_sud_nord_v1'
STAGE = R / '.cache/entree_bristle_sud_nord_v1/entree_bristle_sud_nord'
NAMESPACE = 'entree_bristle_sud_nord'
ASSET = 'ebn1_entree_bristle'
PFX = 'EBN1'
W, H = 424, 632
FULL = (848, 1264)
WATER_PHASES, WATER_TICKS = 4, 10
TUFT_PHASES, TUFT_TICKS = 12, 10
LOOP_TICKS = 120
TCELL = 16
PALETTE_COLORS = 96
METANO_SPARK = R / 'source/eau_metano/natifs/Metano_Town_River_Sparkles.tile'
M_SURFACE = (131, 218, 230)
# Couleurs exactes de la rivière Métano (mesurées sur Metano_Town_River_Animation_1..4).
PAL = {'surface': (131, 218, 230), 'bande': (87, 135, 191), 'inter': (95, 183, 207), 'accent': (111, 207, 231),
       'clair': (148, 230, 238)}


def loadmod(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rgb(p):
    return np.array(Image.open(p).convert('RGB')).astype(int)


def keep_large(m, k):
    lab, n = nd.label(m)
    if n == 0:
        return m
    return np.isin(lab, 1 + np.flatnonzero(nd.sum(m, lab, range(1, n + 1)) >= k))


# ---------------------------------------------------------------- segmentation pleine résolution
def classify(a):
    r, g, b = a.transpose(2, 0, 1); lum = a @ [.299, .587, .114]; sat = a.max(2) - a.min(2)
    mag = (r > g * 1.5) & (b > g * 1.3) & (r > 150) & (b > 130)
    water = nd.binary_dilation(mag, iterations=2)                # liseré rose antialiasé inclus
    green = (g > r + 10) & (g > b + 10) & ~water
    tuft = nd.binary_dilation(keep_large(nd.binary_closing(green, iterations=2), 30), iterations=1)
    # Mesures : roche sat ~5, sable sat ~87 ; fraction grise lissée sur 7 px.
    grey = nd.uniform_filter(((sat < 40) & ~water).astype(float), 7) > 0.5
    rock = keep_large(nd.binary_opening(grey, iterations=2), 2500)
    yy, xx = np.mgrid[:a.shape[0], :a.shape[1]]
    gorge = (xx > 370) & (xx < 480) & (yy < 220) & (lum < 85)
    gorge = nd.binary_fill_holes(keep_large(nd.binary_closing(gorge, iterations=3), 500))
    rock &= ~gorge
    V = np.sqrt(np.maximum(nd.uniform_filter(lum ** 2, 7) - nd.uniform_filter(lum, 7) ** 2, 0))
    sandish = ~(rock | water | tuft | gorge)
    near = nd.binary_dilation(water, iterations=26)
    bank = keep_large(nd.binary_closing(near & sandish & (V > 14), iterations=3) & near & sandish, 400)
    boulder = (sat > 95) & (lum < 180) & sandish & ~bank
    boulder = keep_large(nd.binary_closing(boulder, iterations=2), 80)
    boulder = nd.binary_fill_holes(nd.binary_dilation(boulder, iterations=2)) & sandish & ~bank
    s2 = sandish & ~bank & ~boulder
    lab, _ = nd.label(s2); bottom = [v for v in np.unique(lab[-3:]) if v]
    sand = np.isin(lab, bottom)
    rock |= s2 & ~sand                                               # replats enclavés -> falaises
    return dict(water=water, sand=sand, bank=bank, boulder=boulder, tuft=tuft, rock=rock, gorge=gorge)


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


# ---------------------------------------------------------------- torrent façon Métano (couleurs Métano exactes)
def water_phases(water, visible):
    d = nd.distance_transform_edt(visible); yy, xx = np.mgrid[:H, :W]
    jag = nd.gaussian_filter(np.random.default_rng(9).random((H, W)), 1.0); jag = (jag - jag.min()) / np.ptp(jag)
    frames = []
    for t in range(WATER_PHASES):
        ph = 2 * np.pi * t / WATER_PHASES
        # torrent : l'onde voyage vers le sud (sens du courant) — terme en y dominant
        n = 0.6 * np.sin(yy * 0.23 + xx * 0.08 - ph) + 0.4 * np.sin(yy * 0.09 - xx * 0.19 + 1.3 - ph)
        T = 4.5 + 1.1 * n; jr = np.roll(jag, t * 2, axis=0); fringe = T + 0.6 + 2.6 * jr
        a = np.zeros((H, W, 4), 'uint8'); a[..., 3] = 255; a[..., :3] = PAL['surface']
        a[d <= fringe] = (*PAL['inter'], 255)
        a[(d <= fringe) & (jr > 0.62)] = (*PAL['accent'], 255)
        a[d <= T] = (*PAL['inter'], 255)
        a[d <= T - 1] = (*PAL['bande'], 255)
        a[(d <= 1.0) & (np.sin(xx * 0.3 + yy * 0.5 - ph) > -0.35)] = (*PAL['clair'], 255)
        a[~water] = 0; a[water & ~visible] = (*PAL['bande'], 255)
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
            # pixels natifs : on retire seulement l'aplat de surface (identique à notre surface)
            keep = (a[..., 3] == 255) & (np.abs(a[..., :3].astype(int) - M_SURFACE).sum(2) > 0)
            a[~keep] = 0; out.append(a)
        return out
    return {'A_16x24': cluster([0, 1], [0, 1, 2], 3), 'B_24x16': cluster([2, 3, 4], [0, 1], 2),
            'C_16x32': cluster([0, 1], [12, 13, 14, 15], 4)}


# ---------------------------------------------------------------- touffes au vent (générées)
def tuft_poses(decor, tuft_mask):
    src = rgb(RAW / 'touffes_vent_poses.png'); r, g, b = src.transpose(2, 0, 1)
    mag = (r > 150) & (b > 110) & (g < 120) & (r > g * 1.5)
    obj = nd.binary_closing(~mag, iterations=3)
    lab, n = nd.label(obj); sizes = nd.sum(obj, lab, range(1, n + 1))
    ids = [i + 1 for i in np.flatnonzero(sizes > 800)]
    # palette : couleurs des touffes du décor (cohérence avec la map)
    dec = decor[tuft_mask & ((decor[..., 1] > decor[..., 0]) | (decor.sum(2) < 200))]
    pal_img = Image.fromarray(dec.reshape(-1, 1, 3).astype('uint8')).quantize(7, method=Image.Quantize.MEDIANCUT)
    pal = np.array(pal_img.getpalette()[:21]).reshape(7, 3)
    poses = []
    k = 5; win = TCELL * k
    for i in ids:
        ys, xs = np.nonzero((lab == i) & ~mag)
        by = ys.max(); bottom = ys >= by - (by - ys.min()) * 0.2
        bx = int(round(xs[bottom].mean())); top = ys <= ys.min() + (by - ys.min()) * 0.4
        lean = (xs[top].mean() - bx) / max(by - ys.min(), 1)
        y0, x0 = by + 1 - win, bx - win // 2
        pad = np.zeros((win, win, 3), int); pm = np.zeros((win, win), bool)
        sy0, sx0 = max(0, y0), max(0, x0); sy1, sx1 = min(src.shape[0], y0 + win), min(src.shape[1], x0 + win)
        pad[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = src[sy0:sy1, sx0:sx1]
        pm[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = ((lab == i) & ~mag)[sy0:sy1, sx0:sx1]
        cov = pm.reshape(TCELL, k, TCELL, k).mean((1, 3))
        col = (pad * pm[..., None]).reshape(TCELL, k, TCELL, k, 3).sum((1, 3)) / np.maximum(pm.reshape(TCELL, k, TCELL, k).sum((1, 3)), 1)[..., None]
        dist = ((col[..., None, :] - pal[None, None]) ** 2).sum(-1)
        o = np.zeros((TCELL, TCELL, 4), 'uint8'); o[..., :3] = pal[dist.argmin(-1)]; o[..., 3] = 255; o[cov < 0.3] = 0
        poses.append({'lean': float(lean), 'img': o, 'src_xy': [int(bx), int(by)]})
    poses.sort(key=lambda p: p['lean'])
    # cycle : inclinaison cible = sinusoïde entre les extrêmes mesurés ; pose la plus proche (mesure, pas l'ordre annoncé)
    leans = np.array([p['lean'] for p in poses]); mid = np.median(leans); amp = min(leans.max() - mid, mid - leans.min())
    cycle = []
    for t in range(TUFT_PHASES):
        target = mid + amp * np.sin(2 * np.pi * t / TUFT_PHASES)
        cycle.append(int(np.abs(leans - target).argmin()))
    return poses, cycle, pal


# ---------------------------------------------------------------- utilitaires
def place(free, size, count, seed, taken, core=None):
    rng = np.random.default_rng(seed); out = []; hh, ww = size
    cands = [(y, x) for y in range(0, H - hh + 1, 8) for x in range(0, W - ww + 1, 8)]; rng.shuffle(cands)
    for y, x in cands:
        if core:
            cy, cx = (hh - core) // 2, (ww - core) // 2; ok = free[y + cy:y + cy + core, x + cx:x + cx + core].all()
        else:
            ok = free[y:y + hh, x:x + ww].all()
        if ok and not taken[max(0, y - 4):y + hh + 4, max(0, x - 4):x + ww + 4].any():
            out.append((y, x)); taken[y:y + hh, x:x + ww] = True
            if len(out) == count:
                break
    return out


def cell_grid(block):
    return block.reshape(H // 8, 8, W // 8, 8).mean((1, 3)) > 0.25


def ground_project(stack, blocked, entry_px, threshold_px, gfx, tools):
    """stack : liste (titre, frames, ticks) du bas vers le haut."""
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
    o.update(Name={'DefaultText': 'Entree Bristle - sud vers nord', 'LocalTexts': {}}, AssetName=ASSET, Released=False,
             TexSize=1, Music='', EdgeView=1, ViewCenter=None, ViewOffset={'X': 0, 'Y': 0}, ActiveChar=None, Status={},
             Layers=layers, Background={'$type': 'RogueEssence.Dungeon.LayeredBG, RogueEssence', 'Layers': []},
             Comment='PMDO 0.8.12. Rendu genere (ref. Mt. Bristle) ; torrent facon riviere Metano (couleurs Metano), '
                     'scintillements Metano natifs, touffes au vent generees. Collisions de base a verifier. Seuil non raccorde.')
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
  <Name>Entree Bristle sud-nord - Atelier 0.8.12</Name>
  <Author>meromoonmeri</Author>
  <Description>Projet d'edition : entree de canyon generee (ref. Mt. Bristle), torrent, scintillements et touffes au vent animes. Pas une aventure jouable.</Description>
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


def write_ora(path, layers):
    import xml.etree.ElementTree as ET
    root = ET.Element('image', w=str(W), h=str(H), name='Entree Bristle sud-nord V1')
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
    for d in ['calques', 'animation/eau', 'animation/scintillements', 'animation/touffes', 'poses_touffes', 'masques', 'review']:
        (OUT / d).mkdir(parents=True, exist_ok=True)
    a = rgb(RAW / 'decor_magenta.png'); f = rgb(RAW / 'sol_complet.png')
    assert a.shape[:2] == f.shape[:2] == (FULL[1], FULL[0])
    m = classify(a)
    order = ['water', 'sand', 'bank', 'boulder', 'tuft', 'rock', 'gorge']
    ex = exclusive(m, order)
    water = ex['water']
    layers = {
        'sol_complet': rgba(down_colors(f, np.ones(FULL[::-1], bool)), ~water),
        'sable': rgba(down_colors(a, m['sand']), ex['sand']),          # trous aux touffes -> sol complet dessous
        'berge_galets': rgba(down_colors(a, m['bank']), ex['bank']),
        'rochers': rgba(down_colors(a, m['boulder']), ex['boulder']),
        'falaises': rgba(down_colors(a, m['rock']), ex['rock']),
        'gorge': rgba(down_colors(a, m['gorge']), ex['gorge']),
    }
    layers = quantize_layers(layers)
    for k, v in ex.items():
        Image.fromarray((v * 255).astype('uint8')).save(OUT / 'masques' / f'{PFX}_masque_{k}.png')
    land = np.zeros((H, W), bool)
    for k in ['sable', 'berge_galets', 'rochers', 'falaises', 'gorge']:
        land |= layers[k][..., 3] == 255
    visible = water & ~land
    wf, dist = water_phases(water, visible)
    # Scintillements natifs
    fams = sparkle_families(); taken = np.zeros((H, W), bool)
    sf = [np.zeros((H, W, 4), 'uint8') for _ in range(WATER_PHASES)]; sparkles = []
    for fi, (name, frames) in enumerate(fams.items()):
        hh, ww = frames[0].shape[:2]
        for (y, x) in place(visible & (dist > 3), (hh, ww), 2, 21 + fi, taken, core=8):
            sparkles.append({'famille': name, 'xy': [x, y]})
            for t in range(WATER_PHASES):
                mm = frames[t][..., 3] > 0; sf[t][y:y+hh, x:x+ww][mm] = frames[t][mm]
    for arr in sf:
        arr[~visible] = 0
    # Touffes : une par touffe du décor, base = bas du blob, décalage de phase par colonne (rafale d'ouest).
    poses, cycle, tpal = tuft_poses(a, m['tuft'])
    for i, p in enumerate(poses):
        Image.fromarray(p['img']).save(OUT / 'poses_touffes' / f'{PFX}_touffe_{i:02d}.png')
    lab, n = nd.label(m['tuft']); tufts = []
    tf = [np.zeros((H, W, 4), 'uint8') for _ in range(TUFT_PHASES)]
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        bx, by = int(round(xs.mean() / 2)), int(ys.max() / 2)
        x0, y0 = bx - TCELL // 2, by - TCELL + 1
        assert 0 <= x0 and x0 + TCELL <= W and 0 <= y0 and y0 + TCELL <= H
        off = (bx // 40) % TUFT_PHASES
        tufts.append({'base_xy': [bx, by], 'decalage': off})
        for t in range(TUFT_PHASES):
            img = poses[cycle[(t - off) % TUFT_PHASES]]['img']; mm = img[..., 3] > 0
            tf[t][y0:y0 + TCELL, x0:x0 + TCELL][mm] = img[mm]
    # Exports
    for t, fr in enumerate(wf):
        Image.fromarray(fr).save(OUT / 'animation/eau' / f'{PFX}_00_eau_metano_f{t}.png')
    for t, fr in enumerate(sf):
        Image.fromarray(fr).save(OUT / 'animation/scintillements' / f'{PFX}_01_scintillements_f{t}.png')
    for t, fr in enumerate(tf):
        Image.fromarray(fr).save(OUT / 'animation/touffes' / f'{PFX}_06_touffes_f{t:02d}.png')
    numbers = {'sol_complet': 2, 'sable': 3, 'berge_galets': 4, 'rochers': 5, 'falaises': 7, 'gorge': 8}
    files = {}
    for k, nb in numbers.items():
        fn = f'{PFX}_{nb:02d}_{k}.png'; Image.fromarray(layers[k]).save(OUT / 'calques' / fn); files[k] = fn
    stack_named = [('eau_metano', wf, WATER_TICKS), ('scintillements', sf, WATER_TICKS),
                   ('sol_complet', [layers['sol_complet']], 60), ('sable', [layers['sable']], 60),
                   ('berge_galets', [layers['berge_galets']], 60), ('rochers', [layers['rochers']], 60),
                   ('touffes', tf, TUFT_TICKS), ('falaises', [layers['falaises']], 60), ('gorge', [layers['gorge']], 60)]
    # Collisions : sable (et emplacement des touffes) praticables ; eau, berge, rochers, falaises, gorge bloquent.
    walk = (layers['sable'][..., 3] == 255) | ex['tuft'] | ((layers['sol_complet'][..., 3] == 255) & ~land & ~water)
    walk &= ~(water | (layers['rochers'][..., 3] > 0) | (layers['falaises'][..., 3] > 0) | (layers['berge_galets'][..., 3] > 0) |
              (layers['gorge'][..., 3] > 0))
    blocked = cell_grid(~walk)
    xs = np.nonzero(walk[H - 8])[0]; med = int(np.median(xs)) // 8
    gh_, gw_ = blocked.shape
    cx = min((c for c in range(gw_ - 1) if not blocked[gh_ - 2:, c:c + 2].any()), key=lambda c: abs(c - med))
    entry_px = [cx * 8, H - 16]
    gy, gx = np.nonzero(ex['gorge']); threshold_px = [int(gx.mean()) // 8 * 8 - 8, (int(gy.max()) + 8) // 8 * 8]
    # seuil : premier emplacement 16x16 libre sous la gorge
    while blocked[threshold_px[1] // 8:threshold_px[1] // 8 + 2, threshold_px[0] // 8:threshold_px[0] // 8 + 2].any():
        threshold_px[1] += 8
    ok, explored = v1.reachable(blocked, (entry_px[1] // 8, entry_px[0] // 8), (threshold_px[1] // 8, threshold_px[0] // 8))
    assert ok, 'pas de chemin 16x16'

    def scene(tick):
        wp = (tick // WATER_TICKS) % WATER_PHASES; tp = (tick // TUFT_TICKS) % TUFT_PHASES
        im = Image.new('RGBA', (W, H))
        for title, frames, ticks in stack_named:
            idx = {'eau_metano': wp, 'scintillements': wp, 'touffes': tp}.get(title, 0)
            im.alpha_composite(Image.fromarray(frames[idx]))
        return im
    scenes = [scene(t * 5) for t in range(LOOP_TICKS // 5)]
    scenes[0].save(OUT / 'review' / f'{PFX}_scene_t000.png')
    scenes[0].save(OUT / 'review' / f'{PFX}_scene_animee.webp', save_all=True, append_images=scenes[1:],
                   duration=round(5 * 1000 / 60), loop=0, lossless=True)
    col = scenes[0].copy(); ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(ov)
    for y, x in zip(*np.nonzero(blocked)):
        dr.rectangle([x*8, y*8, x*8+7, y*8+7], fill=(220, 40, 40, 90))
    for (px, py), c in ((entry_px, (255, 230, 40, 255)), (threshold_px, (60, 220, 255, 255))):
        dr.rectangle([px, py, px + 15, py + 15], outline=c, width=2)
    col.alpha_composite(ov); col.save(OUT / 'review' / f'{PFX}_collisions_marqueurs.png')
    sheet = Image.new('RGBA', (len(poses) * 70, 90), (216, 185, 128, 255)); dr = ImageDraw.Draw(sheet)
    for i, p in enumerate(poses):
        sheet.alpha_composite(Image.fromarray(p['img']).resize((64, 64), Image.Resampling.NEAREST), (i * 70, 0))
        dr.text((i * 70 + 4, 70), f"{p['lean']:+.2f}", fill=(40, 30, 20, 255))
    sheet.save(OUT / 'review' / f'{PFX}_poses_touffes_par_inclinaison.png')
    ora = {}
    for i, (title, frames, _) in enumerate(stack_named):
        ora[f'{i:02d}_{title}' + ('_f0' if len(frames) > 1 else '')] = frames[0]
    write_ora(OUT / f'{PFX}_entree_bristle_calques.ora', ora)
    counts = ground_project([(t.replace('_', ' ') + (f' {len(fr)} phases' if len(fr) > 1 else ''), fr, tk)
                             for t, fr, tk in stack_named], blocked, entry_px, threshold_px, gfx, tools)
    order_files = [f'animation/eau/{PFX}_00_eau_metano_fX.png', f'animation/scintillements/{PFX}_01_scintillements_fX.png',
                   f'calques/{files["sol_complet"]}', f'calques/{files["sable"]}', f'calques/{files["berge_galets"]}',
                   f'calques/{files["rochers"]}', f'animation/touffes/{PFX}_06_touffes_fXX.png', f'calques/{files["falaises"]}',
                   f'calques/{files["gorge"]}']
    manifest = {
        'lot': 'entree_bristle_sud_nord_v1', 'size_px': [W, H], 'grid_8px': [W // 8, H // 8],
        'method': 'rendu genere : decor complet sur magenta (torrent = magenta) + sol de sable complet genere separement',
        'reference_da': 'Mt_Bristle_entrance_TD.png',
        'raw_inputs': [{'file': f'source/entree_bristle_sud_nord_v1/bruts/{n}', 'sha256': sha(RAW / n),
                        'size': list(Image.open(RAW / n).size)} for n in ['decor_magenta.png', 'sol_complet.png', 'touffes_vent_poses.png']],
        'normalization': 'x0.5 exact (848x1264 -> 424x632), moyenne 2x2 par classe, palette commune 96 couleurs',
        'segmentation': 'torrent = magenta dilate 2 px ; roche = fraction grise (sat<40) > 0.5 sur 7 px ; gorge = lum<85 dans la fente nord ; '
                        'berge = texture (ecart lum > 14) a < 26 px du torrent ; rochers = orange sature sombre ; touffes = vert ; '
                        'sable = composante reliee au bord sud, replats enclaves rattaches aux falaises',
        'layer_order_bottom_to_top': order_files,
        'water': {'phases': WATER_PHASES, 'frame_length_ticks': WATER_TICKS, 'couleurs': {k: list(v) for k, v in PAL.items()},
                  'modele': 'structure et cadence riviere Metano, couleurs Metano exactes, onde orientee vers le sud (courant)',
                  'origine': 'couleurs natives Metano, pixels recalcules sur notre torrent (pas de tuiles natives)'},
        'sparkles': {'source': 'source/eau_metano/natifs/Metano_Town_River_Sparkles.tile', 'sha256': sha(METANO_SPARK),
                     'placements': sparkles, 'origine': 'pixels et couleurs Metano NATIFS inchanges, positions nouvelles'},
        'tufts': {'brut': 'source/entree_bristle_sud_nord_v1/bruts/touffes_vent_poses.png', 'poses_detectees': len(poses),
                  'inclinaisons_mesurees': [round(p['lean'], 3) for p in poses], 'cycle_indices_par_phase': cycle,
                  'phases': TUFT_PHASES, 'frame_length_ticks': TUFT_TICKS, 'cellule_px': TCELL,
                  'reduction': 'fenetre 80 px -> 16 px (x0.2) identique, ancrage base, palette 7 couleurs des touffes du decor',
                  'placements': tufts, 'origine': 'dessin GENERE, ordre par inclinaison mesuree (la planche ne suivait pas l ordre demande), '
                                                  'cycle cree ; pas une animation officielle'},
        'scene_loop_ticks': LOOP_TICKS,
        'access': {'entry_px': entry_px, 'threshold_px': threshold_px, 'path_found_16x16': ok, 'cells_explored': explored,
                   'blocked_cells': int(blocked.sum()), 'total_cells': int(blocked.size),
                   'rule': 'case bloquee si > 25 % non praticable (torrent, berge, rochers, falaises, gorge)'},
        'pmdo': {'target': '0.8.12', 'asset': ASSET, 'namespace': NAMESPACE, 'tiles_per_bank': counts, 'banks': list(counts),
                 'runtime_tested': False, 'warp': 'aucun'},
        'art_approved': False,
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    shutil.copyfile(OUT / 'manifest.json', STAGE / 'manifest.json')
    print(json.dumps({'poses': len(poses), 'cycle': cycle, 'tufts': len(tufts), 'sparkles': len(sparkles),
                      'entry': entry_px, 'threshold': threshold_px, 'blocked': int(blocked.sum()), 'tiles': counts}, indent=1))


if __name__ == '__main__':
    build()
