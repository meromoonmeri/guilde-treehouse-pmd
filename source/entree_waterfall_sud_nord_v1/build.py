"""Entrée Waterfall sud -> nord V1 — caverne aux gemmes, format 4:3 vaste (768 x 576 px, 96 x 72 cases).

Réf. DA : Waterfall_Cave_gem_TDS.png. Exigence « même endroit, autre lieu » (amp) : décor et sol
générés AVEC la ref canonique en guide ; la roche rouge du décor est mesurée proche de celle de
la ref (test_canonical_rock). Méthode rendu généré : décor 1200x896 (8 bassins en magenta) + sol
complet normalisé (cover uniforme + recadrage centré). Réduction x(576/896) par classe (jungle),
palette commune 96 couleurs.
Segmentation : eau = magenta dilaté ; sentier = pâle touchant le bas ; gemmes = saturées petites ;
stalagmites = gris-bleu (b>r) ; parois = sombre touchant les bords sauf le bas ; sol = reste.
Animations, chacune sur son calque :
- eau luminescente « façon rivière Métano » (structure/cadence 4 x 10 ticks, palette cave à la main) ;
- scintillements de gemmes (planche 1 x 8 : point -> étoile -> flash -> déclin), 8 poses x2 + 8 repos = 24 x 5.
Scène : PPCM 120 ticks = 2 s.
Lancer : .venv/bin/python source/entree_waterfall_sud_nord_v1/build.py
"""
from pathlib import Path
import hashlib, importlib.util, json, shutil, uuid, zipfile

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
RAW = HERE / 'bruts'
OUT = R / 'renders/entree_waterfall_sud_nord_v1'
STAGE = R / '.cache/entree_waterfall_sud_nord_v1/entree_waterfall_sud_nord'
NAMESPACE = 'entree_waterfall_sud_nord'
ASSET = 'ewn1_entree_waterfall'
PFX = 'EWN1'
W, H = 768, 576                      # 4:3, 96 x 72 cases
SRC = (1200, 896)
SCALE = H / SRC[1]                   # 0,642857, identique en X et Y
SCALED_W = round(SRC[0] * SCALE)     # 771
CROP_X = (SCALED_W - W) // 2         # 1
WATER_PHASES, WATER_TICKS = 4, 10
SPK_POSES, SPK_ACTIVE, SPK_PHASES, SPK_TICKS = 8, 16, 24, 5
LOOP_TICKS = 120
SCELL = 24
# Palette eau cave : rôles et ordre de luminance Métano, teintes bleu luminescent à la main.
PAL = {'surface': (36, 110, 180), 'bande': (12, 40, 110), 'inter': (24, 74, 150), 'accent': (60, 140, 210),
       'clair': (150, 220, 255)}


def loadmod(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


BM = loadmod('ebn1_utils', R / 'source/entree_bristle_sud_nord_v1/build.py')
BM.W, BM.H = W, H                    # les utilitaires Bristle lisent W/H au moment de l'appel
keep_large, quantize_layers, place, cell_grid, write_ora = BM.keep_large, BM.quantize_layers, BM.place, BM.cell_grid, BM.write_ora


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rgb(p):
    return np.array(Image.open(p).convert('RGB')).astype(int)


# ---------------------------------------------------------------- segmentation pleine résolution (mesures § build)
def classify(a):
    r, g, b = a.transpose(2, 0, 1); lum = a.max(-1); rb = r - b
    sat = a.max(-1) - a.min(-1)
    mag = (r > 150) & (b > 130) & (r > g * 1.5) & (b > g * 1.3)
    # Bassins = grandes composantes magenta (les gemmes violettes confondent la règle : tri par taille).
    _ml, _mn = nd.label(mag)
    _msz = nd.sum(mag, _ml, range(1, _mn + 1))
    pools = np.isin(_ml, [i + 1 for i in np.flatnonzero(_msz > 1500)])
    _pl, _pn = nd.label(pools)
    assert _pn == 8, ('bassins', _pn)
    # Gemmes AVANT l'eau : saturées et lumineuses, petites composantes, hors bassins.
    gcand = (sat > 75) & (lum > 65) & ~pools
    lab, n = nd.label(gcand)
    gems = np.zeros_like(gcand)
    if n:
        sizes = nd.sum(gcand, lab, range(1, n + 1))
        gems = np.isin(lab, [i + 1 for i in np.flatnonzero((sizes >= 30) & (sizes <= 2500))])
    water = nd.binary_dilation(pools, iterations=2) & ~nd.binary_dilation(gems, iterations=1)
    # Sentier : pâle (lum>90), compo touchant le bas.
    pcand = (lum > 90) & ~water
    pcand = nd.binary_fill_holes(keep_large(nd.binary_closing(pcand, iterations=3), 1500))
    lab, n = nd.label(pcand)
    keep = set(np.unique(lab[-10:][pcand[-10:]])) - {0}
    path = np.isin(lab, list(keep)) if keep else pcand
    # Passage : plus grosse compo très sombre de la boîte nord-centre.
    yy, xx = np.mgrid[:a.shape[0], :a.shape[1]]
    box = (xx > 430) & (xx < 770) & (yy < 230)
    lab, n = nd.label((lum < 35) & box)
    assert n > 0, 'aucune compo sombre dans la boite passage'
    sz = nd.sum((lum < 35) & box, lab, range(1, n + 1)); bi = int(np.argmax(sz)) + 1
    cave = nd.binary_fill_holes(lab == bi)
    assert 1500 < cave.sum() < 25000, ('passage inattendu', int(cave.sum()))
    # Stalagmites : gris-bleu (b>r), tons moyens, composantes intérieures.
    scand = (b > r) & (lum > 35) & (lum < 130) & ~water & ~gems & ~cave
    stalag = keep_large(nd.binary_closing(scand, iterations=2), 500)
    _sl, _sn = nd.label(stalag)
    assert 6 <= _sn <= 24 and 3000 < stalag.sum() < 60000, ('stalagmites', _sn, int(stalag.sum()))
    # Parois : sombre touchant les bords gauche/droit/haut (le sol peut toucher le bas).
    darkred = (lum < 75) & ~water & ~path & ~gems & ~stalag & ~cave
    lab, n = nd.label(darkred); band = np.zeros_like(darkred)
    band[:8] = True; band[:, :8] = band[:, -8:] = True
    border = set(np.unique(lab[band & darkred])) - {0}
    walls = np.isin(lab, list(border))
    floor = ~(water | path | gems | stalag | cave | walls)
    return dict(water=water, floor=floor, path=path, walls=walls, stalag=stalag, gems=gems, cave=cave)


# ---------------------------------------------------------------- réduction uniforme non entière, par classe (jungle)
def resize_plane(p):
    return np.array(Image.fromarray(p.astype(np.float32), 'F').resize((SCALED_W, H), Image.Resampling.BOX))[:, CROP_X:CROP_X + W]


def down_class(a, masks, order):
    weights = {k: resize_plane(masks[k].astype(np.float32)) for k in order}
    stackw = np.stack([weights[k] for k in order]); win = stackw.argmax(0); has = stackw.max(0) > 0.05
    ex = {k: (win == i) & has for i, k in enumerate(order)}
    cols = {}
    for k in order:
        w = weights[k]; m = masks[k].astype(np.float32)
        c = np.stack([resize_plane(a[..., ch] * m) for ch in range(3)], -1) / np.maximum(w, 1e-6)[..., None]
        cols[k] = np.clip(np.round(c), 0, 255).astype('uint8')
    return ex, cols


def down_full(a):
    return np.clip(np.round(np.stack([resize_plane(a[..., ch].astype(np.float32)) for ch in range(3)], -1)), 0, 255).astype('uint8')


def norm_full(f):
    """Sol de taille libre -> 1200x896 : cover UNIFORME + recadrage centré (documenté)."""
    h, w = f.shape[:2]; s = max(SRC[0] / w, SRC[1] / h)
    im = Image.fromarray(f.astype('uint8')).resize((round(w * s), round(h * s)), Image.Resampling.BOX)
    arr = np.array(im); y0 = (arr.shape[0] - SRC[1]) // 2; x0 = (arr.shape[1] - SRC[0]) // 2
    return (s, (x0, y0), arr[y0:y0 + SRC[1], x0:x0 + SRC[0]])


def rgba(colors, mask):
    out = np.zeros((H, W, 4), 'uint8'); out[..., :3] = colors; out[..., 3] = 255; out[~mask] = 0
    return out


def is_mag(a):
    r, g, b = a.transpose(2, 0, 1)
    return (r > 150) & (b > 110) & (g < 130) & (r > g * 1.4) & (b > g * 1.2)


# ---------------------------------------------------------------- eau façon Métano (palette cave, méthode jungle)
def water_phases(water, visible):
    d = nd.distance_transform_edt(visible); yy, xx = np.mgrid[:H, :W]
    jag = nd.gaussian_filter(np.random.default_rng(13).random((H, W)), 1.0); jag = (jag - jag.min()) / np.ptp(jag)
    frames = []
    for t in range(WATER_PHASES):
        ph = 2 * np.pi * t / WATER_PHASES
        n = 0.6 * np.sin(yy * 0.23 + xx * 0.08 - ph) + 0.4 * np.sin(yy * 0.09 - xx * 0.19 + 1.3 - ph)
        T = 4.5 + 1.1 * n; jr = np.roll(jag, t * 2, axis=0); fringe = T + 0.6 + 2.6 * jr
        f = np.zeros((H, W, 4), 'uint8'); f[..., 3] = 255; f[..., :3] = PAL['surface']
        f[d <= fringe] = (*PAL['inter'], 255)
        f[(d <= fringe) & (jr > 0.62)] = (*PAL['accent'], 255)
        f[d <= T] = (*PAL['inter'], 255)
        f[d <= T - 1] = (*PAL['bande'], 255)
        f[(d <= 1.0) & (np.sin(xx * 0.3 + yy * 0.5 - ph) > -0.35)] = (*PAL['clair'], 255)
        f[~water] = 0; f[water & ~visible] = (*PAL['bande'], 255)
        frames.append(f)
    return frames, d


def down_rgba(win, size, cov_min):
    f = win.astype(np.float32); al = f[..., 3:4] / 255.0
    num = np.stack([np.array(Image.fromarray((f[..., c] * al[..., 0]), 'F').resize((size, size), Image.Resampling.BOX)) for c in range(3)], -1)
    den = np.array(Image.fromarray(al[..., 0], 'F').resize((size, size), Image.Resampling.BOX))
    o = np.zeros((size, size, 4), 'uint8')
    o[..., :3] = np.clip(np.round(num / np.maximum(den, 1e-6)[..., None]), 0, 255)
    o[..., 3] = 255; o[den < cov_min] = 0
    return o


def twinkle_poses():
    src = rgb(RAW / 'scintillements_poses.png'); h, w = src.shape[:2]; mag = is_mag(src)
    cw = w / SPK_POSES; poses = []
    for cx in range(SPK_POSES):
        cell = ~mag[:, int(cx * cw):int((cx + 1) * cw)]
        ys, xs = np.nonzero(nd.binary_opening(cell, iterations=1))
        assert len(ys) > 0, ('case scintillement vide', cx)
        cy = int((ys.min() + ys.max()) / 2); xx = int(cx * cw + (xs.min() + xs.max()) / 2)
        side = int(max(ys.max() - ys.min(), xs.max() - xs.min())) + 16
        y0, x0 = cy - side // 2, xx - side // 2
        win = np.zeros((side, side, 4), 'uint8')
        sy0, sx0 = max(0, y0), max(0, x0); sy1, sx1 = min(h, y0 + side), min(w, x0 + side)
        win[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0, :3] = src[sy0:sy1, sx0:sx1]
        content = ~mag[sy0:sy1, sx0:sx1]
        eroded = nd.binary_erosion(content, iterations=1)
        use = eroded if eroded.sum() > 60 else content
        win[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0, 3] = np.where(use, 255, 0)
        o = down_rgba(win, SCELL, 0.12)
        assert (o[..., 3] > 0).sum() > 15, ('scintillement vide', cx)
        poses.append(o)
    for i in range(len(poses)):
        for j in range(i + 1, len(poses)):
            assert (poses[i] != poses[j]).any(), ('poses scintillements identiques', i, j)
    opq = np.concatenate([p[p[..., 3] > 0][:, :3] for p in poses])
    q = Image.fromarray(opq.reshape(-1, 1, 3)).quantize(12, method=Image.Quantize.MEDIANCUT)
    spal = np.array(q.getpalette()[:36], 'uint8').reshape(12, 3)
    for p in poses:
        m = p[..., 3] > 0
        p[..., :3] = spal[np.array(Image.fromarray(p[..., :3]).quantize(palette=q, dither=Image.Dither.NONE))]
        p[~m] = 0
    return poses, spal


# ---------------------------------------------------------------- Ground (gabarit horn, textes Waterfall)
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
    o.update(Name={'DefaultText': 'Entree Waterfall - sud vers nord (4:3)', 'LocalTexts': {}}, AssetName=ASSET, Released=False,
             TexSize=1, Music='', EdgeView=1, ViewCenter=None, ViewOffset={'X': 0, 'Y': 0}, ActiveChar=None, Status={},
             Layers=layers, Background={'$type': 'RogueEssence.Dungeon.LayeredBG, RogueEssence', 'Layers': []},
             Comment='PMDO 0.8.12. Rendu genere 4:3 (ref. Waterfall Cave, guide canonique) ; eau facon Metano et '
                     'scintillements generes. Collisions de base a verifier. Seuil non raccorde.')
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
  <Name>Entree Waterfall sud-nord 4:3 - Atelier 0.8.12</Name>
  <Author>meromoonmeri</Author>
  <Description>Projet d'edition : grande entree de caverne generee au format 4:3 (ref. Waterfall Cave), eau et scintillements animes. Pas une aventure jouable.</Description>
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
    for d in ['calques', 'animation/eau', 'animation/scintillements', 'poses_scintillements', 'masques', 'review']:
        (OUT / d).mkdir(parents=True, exist_ok=True)
    a = rgb(RAW / 'decor_magenta.png')
    assert a.shape[:2] == (SRC[1], SRC[0]), a.shape
    f_raw = rgb(RAW / 'sol_complet.png')
    sol_scale, sol_crop, f = norm_full(f_raw)
    m = classify(a)
    order = ['water', 'floor', 'path', 'walls', 'stalag', 'gems', 'cave']
    ex, cols = down_class(a, m, order)
    water = ex['water']
    names = {'floor': 'sol_caverne', 'path': 'sentier', 'walls': 'parois', 'stalag': 'stalagmites', 'gems': 'gemmes', 'cave': 'passage'}
    layers = {'sol_complet': rgba(down_full(f), ~water)}
    for k, nm in names.items():
        layers[nm] = rgba(cols[k], ex[k])
    layers = quantize_layers(layers)
    for k, v in ex.items():
        Image.fromarray((v * 255).astype('uint8')).save(OUT / 'masques' / f'{PFX}_masque_{k}.png')
    rock_pix = np.concatenate([layers['sol_caverne'][layers['sol_caverne'][..., 3] == 255][:, :3],
                               layers['parois'][layers['parois'][..., 3] == 255][:, :3]]).astype(int)
    rock_mean = rock_pix.mean(0).round(1)
    land = np.zeros((H, W), bool)
    for nm in names.values():
        land |= layers[nm][..., 3] == 255
    visible = water & ~land
    wf, dist = water_phases(water, visible)
    # Scintillements : 7 émetteurs centrés sur les gemmes, 16 actives + 8 repos.
    spk, spal = twinkle_poses()
    for i, p in enumerate(spk):
        Image.fromarray(p).save(OUT / 'poses_scintillements' / f'{PFX}_scintillement_{i}.png')
    taken = np.zeros((H, W), bool)
    near_gems = nd.binary_dilation(ex['gems'], iterations=8)
    sparkles = []
    for i, (y, x) in enumerate(place(near_gems, (SCELL, SCELL), 7, 113, taken, core=8)):
        sparkles.append({'xy': [x, y], 'decalage': (i * 3) % SPK_PHASES})
    assert len(sparkles) == 7, len(sparkles)
    sf = [np.zeros((H, W, 4), 'uint8') for _ in range(SPK_PHASES)]
    for e in sparkles:
        x, y = e['xy']
        for t in range(SPK_PHASES):
            u = (t - e['decalage']) % SPK_PHASES
            if u < SPK_ACTIVE:
                p = spk[u // 2]; mm = p[..., 3] > 0
                sf[t][y:y + SCELL, x:x + SCELL][mm] = p[mm]
    # Exports
    for t, fr in enumerate(wf):
        Image.fromarray(fr).save(OUT / 'animation/eau' / f'{PFX}_00_eau_cave_f{t}.png')
    for t, fr in enumerate(sf):
        Image.fromarray(fr).save(OUT / 'animation/scintillements' / f'{PFX}_08_scintillements_f{t:02d}.png')
    static_order = ['sol_complet'] + list(names.values())
    files = {}
    for i, nm in enumerate(static_order, start=1):
        fn = f'{PFX}_{i:02d}_{nm}.png'; Image.fromarray(layers[nm]).save(OUT / 'calques' / fn); files[nm] = fn
    stack_named = [('eau_cave', wf, WATER_TICKS)] + [(nm, [layers[nm]], 60) for nm in static_order] + [('scintillements', sf, SPK_TICKS)]
    # Collisions : sol de caverne et sentier praticables.
    walk = (layers['sol_caverne'][..., 3] == 255) | (layers['sentier'][..., 3] == 255)
    blocked = cell_grid(~walk)
    gh_, gw_ = blocked.shape
    px = np.nonzero(layers['sentier'][H - 8, :, 3])[0]
    assert len(px) > 0, 'sentier absent au bord sud'
    med = int(np.median(px)) // 8
    cx = min((c for c in range(gw_ - 1) if not blocked[gh_ - 2:, c:c + 2].any()), key=lambda c: abs(c - med))
    entry_px = [cx * 8, H - 16]
    gy, gx = np.nonzero(ex['cave']); threshold_px = [int(gx.mean()) // 8 * 8 - 8, (int(gy.max()) + 8) // 8 * 8]
    while blocked[threshold_px[1] // 8:threshold_px[1] // 8 + 2, threshold_px[0] // 8:threshold_px[0] // 8 + 2].any():
        threshold_px[1] += 8
    ok, explored = v1.reachable(blocked, (entry_px[1] // 8, entry_px[0] // 8), (threshold_px[1] // 8, threshold_px[0] // 8))
    if not ok:
        Image.fromarray((walk * 255).astype('uint8')).save(OUT / 'review/DIAG_acces.png')
        raise AssertionError('pas de chemin 16x16 (voir review/DIAG_acces.png)')

    def scene(tick):
        wp = (tick // WATER_TICKS) % WATER_PHASES; sp = (tick // SPK_TICKS) % SPK_PHASES
        im = Image.new('RGBA', (W, H))
        for title, frames, _ in stack_named:
            im.alpha_composite(Image.fromarray(frames[{'eau_cave': wp, 'scintillements': sp}.get(title, 0)]))
        return im
    scenes = [scene(t * 5) for t in range(LOOP_TICKS // 5)]
    scenes[0].save(OUT / 'review' / f'{PFX}_scene_t000.png')
    scenes[0].save(OUT / 'review' / f'{PFX}_scene_animee.webp', save_all=True, append_images=scenes[1:],
                   duration=round(5 * 1000 / 60), loop=0, lossless=True)
    col = scenes[0].copy(); ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(ov)
    for y, x in zip(*np.nonzero(blocked)):
        dr.rectangle([x*8, y*8, x*8+7, y*8+7], fill=(220, 40, 40, 90))
    for (qx, qy), c in ((entry_px, (255, 230, 40, 255)), (threshold_px, (60, 220, 255, 255))):
        dr.rectangle([qx, qy, qx + 15, qy + 15], outline=c, width=2)
    col.alpha_composite(ov); col.save(OUT / 'review' / f'{PFX}_collisions_marqueurs.png')
    sheet = Image.new('RGBA', (8 * 68, 72), (88, 50, 63, 255))
    for i, p in enumerate(spk):
        sheet.alpha_composite(Image.fromarray(p).resize((64, 64), Image.Resampling.NEAREST), (i * 68, 4))
    sheet.save(OUT / 'review' / f'{PFX}_planche_scintillements_x4.png')
    spk_colors = int(len(np.unique(np.concatenate([p[p[..., 3] > 0][:, :3] for p in spk]).reshape(-1, 3), axis=0)))
    write_ora(OUT / f'{PFX}_entree_waterfall_calques.ora',
              {f'{i:02d}_{t}' + ('_f0' if len(fr) > 1 else ''): fr[0] for i, (t, fr, _) in enumerate(stack_named)})
    counts = ground_project([(t.replace('_', ' ') + (f' {len(fr)} phases' if len(fr) > 1 else ''), fr, tk)
                             for t, fr, tk in stack_named], blocked, entry_px, threshold_px, gfx, tools)
    order_files = [f'animation/eau/{PFX}_00_eau_cave_fX.png'] + [f'calques/{files[nm]}' for nm in static_order] + \
                  [f'animation/scintillements/{PFX}_08_scintillements_fXX.png']
    ref = rgb(R / 'Waterfall_Cave_gem_TDS.png'); rr, rg, rb_ = ref.transpose(2, 0, 1); rlum = ref @ [.299, .587, .114]
    ref_rock = ref[((rr - rb_) > 10) & (rlum > 25) & (rlum < 110)].mean(0).round(1)
    manifest = {
        'lot': 'entree_waterfall_sud_nord_v1', 'format': '4:3 vaste', 'size_px': [W, H], 'grid_8px': [W // 8, H // 8],
        'method': 'rendu genere 4:3 guide par la ref canonique : decor complet (8 bassins magenta) + sol genere separement',
        'reference_da': 'Waterfall_Cave_gem_TDS.png',
        'raw_inputs': [{'file': f'source/entree_waterfall_sud_nord_v1/bruts/{n}', 'sha256': sha(RAW / n),
                        'size': list(Image.open(RAW / n).size)} for n in ['decor_magenta.png', 'sol_complet.png', 'scintillements_poses.png']],
        'normalization': {'scale': SCALE, 'scaled': [SCALED_W, H], 'crop_x': [CROP_X, SCALED_W - W - CROP_X],
                          'methode': 'moyenne ponderee par classe (BOX), attribution exclusive par poids maximal, palette commune 96 couleurs',
                          'sol': {'facteur_cover': sol_scale, 'recadrage_xy': list(sol_crop), 'taille_source': list(Image.open(RAW / 'sol_complet.png').size)}},
        'segmentation': 'eau = grandes composantes magenta (>1500 px, 8 bassins) dilatees 2 px hors gemmes ; sentier = lum>90 touchant le bas ; '
                        'passage = compo lum<35 de la boite nord-centre (430-770, <230) ; gemmes = sat>75 & lum>65 hors bassins, compos 30-2500 px (detectees avant eau) ; '
                        'stalagmites = b>r & lum 35-130, compos >= 150 px ; parois = sombre (lum<75) touchant gauche/droit/haut ; sol = reste',
        'layer_order_bottom_to_top': order_files,
        'water': {'bassins': 8, 'phases': WATER_PHASES, 'frame_length_ticks': WATER_TICKS,
                  'couleurs': {k: list(v) for k, v in PAL.items()},
                  'modele': 'structure et cadence riviere Metano, palette cave luminescente a la main',
                  'origine': 'pixels recalcules, pas de tuiles natives'},
        'scintillements': {'poses': SPK_POSES, 'phases_actives': SPK_ACTIVE, 'phases': SPK_PHASES, 'frame_length_ticks': SPK_TICKS,
                           'couleurs_distinctes': spk_colors, 'palette_12': [list(map(int, c)) for c in spal], 'emetteurs': sparkles,
                           'origine': 'dessin GENERE (planche 1x8), chronologie creee (8 poses x2 + 8 repos) ; pas une animation officielle'},
        'canonique': {'ref_roche_moyenne': list(map(float, ref_rock)), 'decor_roche_moyenne': list(map(float, rock_mean)),
                      'distance': float(np.linalg.norm(np.array(rock_mean, float) - np.array(ref_rock, float)))},
        'scene_loop_ticks': LOOP_TICKS,
        'access': {'entry_px': entry_px, 'threshold_px': threshold_px, 'path_found_16x16': ok, 'cells_explored': explored,
                   'blocked_cells': int(blocked.sum()), 'total_cells': int(blocked.size),
                   'rule': 'case bloquee si > 25 % hors sol/sentier'},
        'pmdo': {'target': '0.8.12', 'asset': ASSET, 'namespace': NAMESPACE, 'tiles_per_bank': counts, 'banks': list(counts),
                 'runtime_tested': False, 'warp': 'aucun'},
        'art_approved': False,
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    shutil.copyfile(OUT / 'manifest.json', STAGE / 'manifest.json')
    print(json.dumps({'entry': entry_px, 'threshold': threshold_px, 'blocked': int(blocked.sum()), 'cells': int(blocked.size),
                      'roche': list(map(float, rock_mean)), 'ref_roche': list(map(float, ref_rock)),
                      'spk_colors': spk_colors, 'tiles': counts}, indent=1))


if __name__ == '__main__':
    build()
