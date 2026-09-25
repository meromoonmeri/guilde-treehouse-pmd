"""Entrée Jungle sud -> nord V1 — premier lot au format 4:3 VASTE (768 x 576 px, 96 x 72 cases).

Demande : « j'aimerais que les map soit plus vaste 4:3 ratio etc stp ! » puis « lance toi la suite ! ».
Méthode rendu généré (comme les lots précédents) : décor complet sur magenta (eau = magenta) généré en 4:3
(1200 x 896), sol d'herbe complet généré séparément. Normalisation UNIFORME x(576/896) = 0,642857 -> 771 x 576,
puis recadrage centré à 768 (1 px à gauche, 2 px à droite). Facteur non entier : réduction par moyenne pondérée
PAR CLASSE (aucun mélange entre classes), attribution exclusive de chaque pixel à la classe de poids maximal.
Animations, chacune sur son calque :
- rivière et mare « façon rivière Métano » (structure/cadence 4 x 10 ticks), palette jungle choisie à la main ;
- scintillements Métano natifs (pixels et couleurs inchangés) ;
- papillons générés (planche 2 x 6 : 2 couleurs x 6 poses de battement), 6 papillons sur des boucles en huit,
  48 phases x 5 ticks = 4 s.
Scène : PPCM 240 ticks = 4 s.
Lancer : .venv/bin/python source/entree_jungle_sud_nord_v1/build.py
"""
from pathlib import Path
import hashlib, importlib.util, json, shutil, uuid, zipfile

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
RAW = HERE / 'bruts'
OUT = R / 'renders/entree_jungle_sud_nord_v1'
STAGE = R / '.cache/entree_jungle_sud_nord_v1/entree_jungle_sud_nord'
NAMESPACE = 'entree_jungle_sud_nord'
ASSET = 'ejn1_entree_jungle'
PFX = 'EJN1'
W, H = 768, 576                      # 4:3, 96 x 72 cases
SRC = (1200, 896)
SCALE = H / SRC[1]                   # 0.642857, identique en X et Y
SCALED_W = round(SRC[0] * SCALE)     # 771
CROP_X = (SCALED_W - W) // 2         # 1
WATER_PHASES, WATER_TICKS = 4, 10
FLY_PHASES, FLY_TICKS = 48, 5
LOOP_TICKS = 240
BCELL = 24
# Palette eau jungle : rôles et ordre de luminance Métano, teintes vert-sarcelle choisies à la main.
PAL = {'surface': (72, 176, 168), 'bande': (30, 92, 96), 'inter': (48, 132, 132), 'accent': (60, 156, 152),
       'clair': (132, 214, 196)}


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


# ---------------------------------------------------------------- segmentation pleine résolution
def classify(a):
    r, g, b = a.transpose(2, 0, 1); lum = a @ [.299, .587, .114]
    mag = (r > g * 1.5) & (b > g * 1.3) & (r > 150) & (b > 130)
    water = nd.binary_dilation(mag, iterations=2)
    # Mesures : sentier (99,215,74) lum 164 ; clairière (48,136,64) lum 102 ; jungle lum 30-47.
    path = (g > 185) & (r > 70) & (r < 170) & (b < 130)
    path = nd.binary_fill_holes(keep_large(nd.binary_opening(nd.binary_closing(path, iterations=3), iterations=1), 3000))
    L = nd.uniform_filter(lum, 15)
    jungle = (L < 72) & ~water & ~path
    jungle = keep_large(nd.binary_opening(nd.binary_closing(jungle, iterations=2), iterations=2, border_value=1), 600)
    yy, xx = np.mgrid[:a.shape[0], :a.shape[1]]
    cave = (xx > 540) & (xx < 660) & (yy < 150) & (lum < 45) & (b >= r)
    cave = nd.binary_fill_holes(keep_large(nd.binary_closing(cave, iterations=3), 800))
    jungle &= ~cave
    near = nd.binary_dilation(water, iterations=16)
    bank = near & ~water & ~jungle & ~path & ((r > g - 35) | (lum < 80))
    bank = keep_large(nd.binary_closing(bank, iterations=2) & near & ~water & ~path, 300)
    open_ = ~(water | path | jungle | cave | bank)
    dirt = open_ & (r > 85) & (np.abs(r - g) < 35) & (b < 95) & (lum > 90)
    dirt = nd.binary_fill_holes(keep_large(nd.binary_closing(dirt, iterations=2), 60)) & open_
    boulder = open_ & ~dirt & ((g - r) < 48) & (lum > 95) & (b > 70)
    boulder = nd.binary_fill_holes(keep_large(nd.binary_closing(boulder, iterations=2), 150)) & open_ & ~dirt
    grass = open_ & ~dirt & ~boulder
    # Îlots d'arbres : composantes de jungle sans contact avec une bande de 8 px au bord.
    lab, n = nd.label(jungle); band = np.zeros_like(jungle); band[:8] = band[-8:] = True; band[:, :8] = band[:, -8:] = True
    border = set(np.unique(lab[band & jungle])) - {0}
    islands = jungle & ~np.isin(lab, list(border))
    return dict(water=water, grass=grass, path=path, dirt=dirt, bank=bank, boulder=boulder,
                islands=islands, jungle=jungle & ~islands, cave=cave)


# ---------------------------------------------------------------- réduction uniforme non entière, par classe
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


def rgba(colors, mask):
    out = np.zeros((H, W, 4), 'uint8'); out[..., :3] = colors; out[..., 3] = 255; out[~mask] = 0
    return out


# ---------------------------------------------------------------- eau façon Métano (palette jungle)
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


# ---------------------------------------------------------------- papillons générés
def butterfly_poses():
    src = rgb(RAW / 'papillons_poses.png'); h, w = src.shape[:2]; r, g, b = src.transpose(2, 0, 1)
    mag = (r > 150) & (b > 110) & (g < 120) & (r > g * 1.5) & (b > g * 1.3)
    cw, ch = w / 6, h / 2; k = 11; win = BCELL * k
    poses = {}
    for ry, name in ((0, 'jaune'), (1, 'bleu')):
        seq = []
        for cx in range(6):
            cell = ~mag[int(ry * ch):int((ry + 1) * ch), int(cx * cw):int((cx + 1) * cw)]
            ys, xs = np.nonzero(nd.binary_opening(cell, iterations=1))
            cy0 = int(ry * ch) + int((ys.min() + ys.max()) / 2); cx0 = int(cx * cw) + int((xs.min() + xs.max()) / 2)
            y0, x0 = cy0 - win // 2, cx0 - win // 2
            pad = np.zeros((win, win, 3), int); pm = np.zeros((win, win), bool)
            sy0, sx0 = max(0, y0), max(0, x0); sy1, sx1 = min(h, y0 + win), min(w, x0 + win)
            pad[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = src[sy0:sy1, sx0:sx1]
            pm[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = ~mag[sy0:sy1, sx0:sx1]
            box = np.zeros_like(pm)
            box[max(0, int(ry * ch) - y0):max(0, int((ry + 1) * ch) - y0), max(0, int(cx * cw) - x0):max(0, int((cx + 1) * cw) - x0)] = True
            pm &= box
            cov = pm.reshape(BCELL, k, BCELL, k).mean((1, 3))
            col = (pad * pm[..., None]).reshape(BCELL, k, BCELL, k, 3).sum((1, 3)) / np.maximum(pm.reshape(BCELL, k, BCELL, k).sum((1, 3)), 1)[..., None]
            o = np.zeros((BCELL, BCELL, 4), 'uint8'); o[..., :3] = np.clip(col, 0, 255); o[..., 3] = 255; o[cov < 0.3] = 0
            seq.append(o)
        # palette de la rangée (7 couleurs) : aplats nets
        opq = np.concatenate([s[s[..., 3] > 0][:, :3] for s in seq])
        q = Image.fromarray(opq.reshape(-1, 1, 3)).quantize(7, method=Image.Quantize.MEDIANCUT)
        pal = np.array(q.getpalette()[:21], 'uint8').reshape(7, 3)
        for s in seq:
            m = s[..., 3] > 0
            if m.any():
                s[..., :3] = pal[np.array(Image.fromarray(s[..., :3]).quantize(palette=q, dither=Image.Dither.NONE))]
            s[~m] = 0
        poses[name] = seq
    return poses


# ---------------------------------------------------------------- Ground
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
    o.update(Name={'DefaultText': 'Entree Jungle - sud vers nord (4:3)', 'LocalTexts': {}}, AssetName=ASSET, Released=False,
             TexSize=1, Music='', EdgeView=1, ViewCenter=None, ViewOffset={'X': 0, 'Y': 0}, ActiveChar=None, Status={},
             Layers=layers, Background={'$type': 'RogueEssence.Dungeon.LayeredBG, RogueEssence', 'Layers': []},
             Comment='PMDO 0.8.12. Rendu genere 4:3 (ref. Southern Jungle) ; riviere facon Metano, scintillements Metano natifs, '
                     'papillons generes. Collisions de base a verifier. Seuil non raccorde.')
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
  <Name>Entree Jungle sud-nord 4:3 - Atelier 0.8.12</Name>
  <Author>meromoonmeri</Author>
  <Description>Projet d'edition : grande entree de jungle generee au format 4:3 (ref. Southern Jungle), riviere, scintillements et papillons animes. Pas une aventure jouable.</Description>
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
    for d in ['calques', 'animation/eau', 'animation/scintillements', 'animation/papillons', 'poses_papillons', 'masques', 'review']:
        (OUT / d).mkdir(parents=True, exist_ok=True)
    a = rgb(RAW / 'decor_magenta.png'); f = rgb(RAW / 'sol_complet.png')
    assert a.shape[:2] == f.shape[:2] == (SRC[1], SRC[0])
    m = classify(a)
    order = ['water', 'grass', 'path', 'dirt', 'bank', 'boulder', 'islands', 'jungle', 'cave']
    ex, cols = down_class(a, m, order)
    water = ex['water']
    names = {'grass': 'clairiere', 'path': 'sentier', 'dirt': 'terre', 'bank': 'berge', 'boulder': 'rochers',
             'islands': 'ilots_arbres', 'jungle': 'jungle', 'cave': 'entree_sombre'}
    layers = {'sol_complet': rgba(down_full(f), ~water)}
    for k, nm in names.items():
        layers[nm] = rgba(cols[k], ex[k])
    layers = quantize_layers(layers)
    for k, v in ex.items():
        Image.fromarray((v * 255).astype('uint8')).save(OUT / 'masques' / f'{PFX}_masque_{k}.png')
    land = np.zeros((H, W), bool)
    for nm in names.values():
        land |= layers[nm][..., 3] == 255
    visible = water & ~land
    wf, dist = water_phases(water, visible)
    fams = BM.sparkle_families(); taken = np.zeros((H, W), bool)
    sf = [np.zeros((H, W, 4), 'uint8') for _ in range(WATER_PHASES)]; sparkles = []
    for fi, (name, frames) in enumerate(fams.items()):
        hh, ww = frames[0].shape[:2]
        for (y, x) in place(visible & (dist > 4), (hh, ww), 3, 31 + fi, taken, core=8):
            sparkles.append({'famille': name, 'xy': [x, y]})
            for t in range(WATER_PHASES):
                mm = frames[t][..., 3] > 0; sf[t][y:y+hh, x:x+ww][mm] = frames[t][mm]
    for arr in sf:
        arr[~visible] = 0
    # Papillons : 6 boucles en huit fermées au-dessus de la clairière (48 phases), battement 6 poses par 6 phases.
    poses = butterfly_poses()
    for nm, seq in poses.items():
        for i, p in enumerate(seq):
            Image.fromarray(p).save(OUT / 'poses_papillons' / f'{PFX}_papillon_{nm}_{i}.png')
    flights = [((200, 300), (70, 40), 0, 'jaune'), ((520, 250), (80, 50), 17, 'bleu'), ((360, 420), (60, 36), 31, 'jaune'),
               ((640, 420), (55, 45), 8, 'bleu'), ((300, 150), (60, 30), 40, 'bleu'), ((560, 120), (70, 35), 24, 'jaune')]
    bf = [np.zeros((H, W, 4), 'uint8') for _ in range(FLY_PHASES)]; tracks = []
    for (cx, cy), (ax, ay), off, colr in flights:
        pts = []
        for t in range(FLY_PHASES):
            u = 2 * np.pi * (t + off) / FLY_PHASES
            x = int(round(cx + ax * np.sin(u))); y = int(round(cy + ay * np.sin(2 * u)))   # huit fermé : t=48 == t=0
            p = poses[colr][(t + off) % 6]; mm = p[..., 3] > 0
            x0, y0 = x - BCELL // 2, y - BCELL // 2
            assert 0 <= x0 and x0 + BCELL <= W and 0 <= y0 and y0 + BCELL <= H
            bf[t][y0:y0 + BCELL, x0:x0 + BCELL][mm] = p[mm]; pts.append([x, y])
        tracks.append({'centre': [cx, cy], 'amplitude': [ax, ay], 'decalage': off, 'couleur': colr, 'positions': pts})
    # Exports
    for t, fr in enumerate(wf):
        Image.fromarray(fr).save(OUT / 'animation/eau' / f'{PFX}_00_eau_jungle_f{t}.png')
    for t, fr in enumerate(sf):
        Image.fromarray(fr).save(OUT / 'animation/scintillements' / f'{PFX}_01_scintillements_f{t}.png')
    for t, fr in enumerate(bf):
        Image.fromarray(fr).save(OUT / 'animation/papillons' / f'{PFX}_11_papillons_f{t:02d}.png')
    static_order = ['sol_complet'] + list(names.values())
    files = {}
    for i, nm in enumerate(static_order, start=2):
        fn = f'{PFX}_{i:02d}_{nm}.png'; Image.fromarray(layers[nm]).save(OUT / 'calques' / fn); files[nm] = fn
    stack_named = [('eau_jungle', wf, WATER_TICKS), ('scintillements', sf, WATER_TICKS)] + \
                  [(nm, [layers[nm]], 60) for nm in static_order] + [('papillons', bf, FLY_TICKS)]
    # Collisions : clairière, sentier, terre praticables.
    walk = (layers['clairiere'][..., 3] == 255) | (layers['sentier'][..., 3] == 255) | (layers['terre'][..., 3] == 255)
    blocked = cell_grid(~walk)
    gh_, gw_ = blocked.shape
    px = np.nonzero(layers['sentier'][H - 8, :, 3])[0]; med = int(np.median(px)) // 8
    cx = min((c for c in range(gw_ - 1) if not blocked[gh_ - 2:, c:c + 2].any()), key=lambda c: abs(c - med))
    entry_px = [cx * 8, H - 16]
    gy, gx = np.nonzero(ex['cave']); threshold_px = [int(gx.mean()) // 8 * 8 - 8, (int(gy.max()) + 8) // 8 * 8]
    while blocked[threshold_px[1] // 8:threshold_px[1] // 8 + 2, threshold_px[0] // 8:threshold_px[0] // 8 + 2].any():
        threshold_px[1] += 8
    ok, explored = v1.reachable(blocked, (entry_px[1] // 8, entry_px[0] // 8), (threshold_px[1] // 8, threshold_px[0] // 8))
    assert ok, 'pas de chemin 16x16'

    def scene(tick):
        wp = (tick // WATER_TICKS) % WATER_PHASES; fp = (tick // FLY_TICKS) % FLY_PHASES
        im = Image.new('RGBA', (W, H))
        for title, frames, _ in stack_named:
            im.alpha_composite(Image.fromarray(frames[{'eau_jungle': wp, 'scintillements': wp, 'papillons': fp}.get(title, 0)]))
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
    sheet = Image.new('RGBA', (6 * 100, 200), (48, 136, 64, 255))
    for r_, nm in enumerate(poses):
        for i, p in enumerate(poses[nm]):
            sheet.alpha_composite(Image.fromarray(p).resize((96, 96), Image.Resampling.NEAREST), (i * 100, r_ * 100))
    sheet.save(OUT / 'review' / f'{PFX}_planche_papillons_x4.png')
    write_ora(OUT / f'{PFX}_entree_jungle_calques.ora',
              {f'{i:02d}_{t}' + ('_f0' if len(fr) > 1 else ''): fr[0] for i, (t, fr, _) in enumerate(stack_named)})
    counts = ground_project([(t.replace('_', ' ') + (f' {len(fr)} phases' if len(fr) > 1 else ''), fr, tk)
                             for t, fr, tk in stack_named], blocked, entry_px, threshold_px, gfx, tools)
    order_files = [f'animation/eau/{PFX}_00_eau_jungle_fX.png', f'animation/scintillements/{PFX}_01_scintillements_fX.png'] + \
                  [f'calques/{files[nm]}' for nm in static_order] + [f'animation/papillons/{PFX}_11_papillons_fXX.png']
    manifest = {
        'lot': 'entree_jungle_sud_nord_v1', 'format': '4:3 vaste', 'size_px': [W, H], 'grid_8px': [W // 8, H // 8],
        'method': 'rendu genere 4:3 : decor complet sur magenta (eau = magenta) + sol d herbe complet genere separement',
        'reference_da': 'Southern_Jungle_entrance_S.png',
        'raw_inputs': [{'file': f'source/entree_jungle_sud_nord_v1/bruts/{n}', 'sha256': sha(RAW / n),
                        'size': list(Image.open(RAW / n).size)} for n in ['decor_magenta.png', 'sol_complet.png', 'papillons_poses.png']],
        'normalization': {'scale': SCALE, 'scaled': [SCALED_W, H], 'crop_x': [CROP_X, SCALED_W - W - CROP_X],
                          'methode': 'moyenne ponderee par classe (BOX), attribution exclusive par poids maximal, palette commune 96 couleurs'},
        'segmentation': 'eau = magenta dilate 2 px ; sentier = vert lime (g>185) ; jungle = luminance lissee 15 px < 72 ; '
                        'grotte = lum<45 dans la fente nord ; berge = brun a < 16 px de l eau ; terre = brun sur clairiere ; '
                        'rochers = gris-vert clair ; ilots = jungle sans contact avec la bande de bord de 8 px',
        'layer_order_bottom_to_top': order_files,
        'water': {'phases': WATER_PHASES, 'frame_length_ticks': WATER_TICKS, 'couleurs': {k: list(v) for k, v in PAL.items()},
                  'modele': 'structure et cadence riviere Metano, palette jungle a la main (roles Metano)',
                  'origine': 'pixels recalcules, pas de tuiles natives'},
        'sparkles': {'source': 'source/eau_metano/natifs/Metano_Town_River_Sparkles.tile', 'placements': sparkles,
                     'origine': 'pixels et couleurs Metano NATIFS inchanges'},
        'butterflies': {'brut': 'source/entree_jungle_sud_nord_v1/bruts/papillons_poses.png', 'poses_par_couleur': 6,
                        'reduction': 'fenetre 264 px -> 24 px (x1/11) centree, palette 7 couleurs par rangee',
                        'phases': FLY_PHASES, 'frame_length_ticks': FLY_TICKS, 'loop_s': FLY_PHASES * FLY_TICKS / 60,
                        'battement': '6 poses, 1 pose par phase (0,5 s par battement), 48 = 8 battements -> boucle fermee',
                        'trajectoires': tracks, 'origine': 'dessin GENERE, trajectoires et chronologie creees ; pas une animation officielle'},
        'scene_loop_ticks': LOOP_TICKS,
        'access': {'entry_px': entry_px, 'threshold_px': threshold_px, 'path_found_16x16': ok, 'cells_explored': explored,
                   'blocked_cells': int(blocked.sum()), 'total_cells': int(blocked.size),
                   'rule': 'case bloquee si > 25 % hors clairiere/sentier/terre'},
        'pmdo': {'target': '0.8.12', 'asset': ASSET, 'namespace': NAMESPACE, 'tiles_per_bank': counts, 'banks': list(counts),
                 'runtime_tested': False, 'warp': 'aucun'},
        'art_approved': False,
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    shutil.copyfile(OUT / 'manifest.json', STAGE / 'manifest.json')
    print(json.dumps({'sparkles': len(sparkles), 'entry': entry_px, 'threshold': threshold_px, 'blocked': int(blocked.sum()),
                      'cells': int(blocked.size), 'tiles': counts}, indent=1))


if __name__ == '__main__':
    build()
