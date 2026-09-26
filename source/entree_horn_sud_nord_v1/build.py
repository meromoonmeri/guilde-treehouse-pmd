"""Entrée Horn sud -> nord V1 — montagne ocre, format 4:3 vaste (768 x 576 px, 96 x 72 cases).

Réf. DA : Mt_Horn_entrance_Sky.png. Exigence « même endroit, autre lieu » (amp) : décor et sol
générés AVEC la ref canonique en guide ; le sable du décor est mesuré proche de celui de la ref
(test_canonical_sand). Méthode rendu généré : décor 1200x896 + sol complet normalisé (cover
uniforme + recadrage centré). Réduction x(576/896) par classe (jungle), palette commune 96.
Tout est ocre ici : roche = germes sombres + croissance bornée ; sentier = zone lisse et claire
touchant le bas ; buissons = micro-relief dense, exclus de la roche.
Animations, chacune sur son calque :
- éboulis (planche 1 x 8 : détachement -> chute -> impact -> tas), 8 poses x2 + 8 repos = 24 x 5 ;
- poussières (planche 2 x 5 lue en ligne : puff -> boule -> dissipation), 10 poses x2 + 4 repos = 24 x 5.
Scène : 120 ticks = 2 s. Pas d'eau (montagne sèche), pas de magenta résiduel (0 px en entrée).
Lancer : .venv/bin/python source/entree_horn_sud_nord_v1/build.py
"""
from pathlib import Path
import hashlib, importlib.util, json, shutil, uuid, zipfile

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
RAW = HERE / 'bruts'
OUT = R / 'renders/entree_horn_sud_nord_v1'
STAGE = R / '.cache/entree_horn_sud_nord_v1/entree_horn_sud_nord'
NAMESPACE = 'entree_horn_sud_nord'
ASSET = 'ehn1_entree_horn'
PFX = 'EHN1'
W, H = 768, 576                      # 4:3, 96 x 72 cases
SRC = (1200, 896)
SCALE = H / SRC[1]                   # 0,642857, identique en X et Y
SCALED_W = round(SRC[0] * SCALE)     # 771
CROP_X = (SCALED_W - W) // 2         # 1
EB_POSES, EB_ACTIVE, EB_PHASES, EB_TICKS = 8, 16, 24, 5
DU_POSES, DU_ACTIVE, DU_PHASES, DU_TICKS = 10, 20, 24, 5
LOOP_TICKS = 120
EB_CELL, DU_CELL = 24, 32


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
    r, g, b = a.transpose(2, 0, 1); lum = a @ [.299, .587, .114]; rb = r - b
    fl = lum.astype(float)
    std11 = np.sqrt(np.maximum(nd.uniform_filter(fl ** 2, 11) - nd.uniform_filter(fl, 11) ** 2, 0))
    std3 = np.sqrt(np.maximum(nd.uniform_filter(fl ** 2, 3) - nd.uniform_filter(fl, 3) ** 2, 0))
    # Buissons AVANT la roche : touffes = micro-relief dense (6 buissons visibles, aucun extra à 0,40).
    dens = nd.uniform_filter((std3 > 12).astype(float), 31)
    bush = keep_large(nd.binary_closing(dens > 0.40, iterations=1), 800)
    _blab, _bn = nd.label(bush)
    assert 3 <= _bn <= 9 and 10000 < bush.sum() < 50000, ('buissons', _bn, int(bush.sum()))
    # Roche : germes sombres (lum<125 & r-b<105) + croissance bornée 8 px dans les tons moyens.
    seed = (lum < 125) & (rb < 105) & ~bush
    grow = (lum < 170) & (rb < 130) & ~bush
    rock = seed
    for _ in range(8):
        rock = (nd.binary_dilation(rock) & grow) | seed
    rock = nd.binary_closing(rock, iterations=2)
    dark = rock & (lum < 80)
    # Grotte : plus grosse compo sombre de la boîte nord-centre.
    yy, xx = np.mgrid[:a.shape[0], :a.shape[1]]
    box = (xx > 430) & (xx < 770) & (yy < 230)
    lab, n = nd.label(dark & box)
    assert n > 0, 'aucune compo sombre dans la boite grotte'
    sz = nd.sum(dark & box, lab, range(1, n + 1)); bi = int(np.argmax(sz)) + 1
    cave = nd.binary_fill_holes(lab == bi)
    assert 1500 < cave.sum() < 25000, ('grotte inattendue', int(cave.sum()))
    rock_nb = nd.binary_closing(rock & ~cave, iterations=2)
    lab, n = nd.label(rock_nb); band = np.zeros_like(rock_nb)
    band[:8] = band[-8:] = True; band[:, :8] = band[:, -8:] = True
    border = set(np.unique(lab[band & rock_nb])) - {0}
    walls = np.isin(lab, list(border))
    boulders = keep_large(rock_nb & ~walls, 400)
    # Sentier : lisse (std11<9) et clair, compo touchant le bas.
    cand = (std11 < 9) & (lum > 150) & (rb > 110)
    cand = nd.binary_fill_holes(keep_large(nd.binary_closing(cand, iterations=3), 1500))
    lab, n = nd.label(cand)
    keep = set(np.unique(lab[-10:][cand[-10:]])) - {0}
    path = np.isin(lab, list(keep)) if keep else cand
    sand = ~(path | walls | boulders | bush | cave)
    return dict(sand=sand, path=path, walls=walls, boulders=boulders, bush=bush, cave=cave)


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


def is_bg(a):
    r, g, b = a.transpose(2, 0, 1)
    return (r > 140) & (b > 100) & (r > g) & (b > g)   # magenta + lignes de grille (claires ou sombres)


def down_rgba(win, size, cov_min):
    f = win.astype(np.float32); al = f[..., 3:4] / 255.0
    num = np.stack([np.array(Image.fromarray((f[..., c] * al[..., 0]), 'F').resize((size, size), Image.Resampling.BOX)) for c in range(3)], -1)
    den = np.array(Image.fromarray(al[..., 0], 'F').resize((size, size), Image.Resampling.BOX))
    o = np.zeros((size, size, 4), 'uint8')
    o[..., :3] = np.clip(np.round(num / np.maximum(den, 1e-6)[..., None]), 0, 255)
    o[..., 3] = 255; o[den < cov_min] = 0
    return o


def grid_bounds(n, total, profile, radius):
    """Bornes de cases : extremum local (grille claire ou sombre) près de chaque multiple du pas."""
    pitch = total / n; med = float(np.median(profile)); bounds = [0]
    for k in range(1, n):
        c = int(round(k * pitch)); lo = max(0, c - radius); hi = min(total, c + radius + 1)
        bounds.append(lo + int(np.abs(profile[lo:hi] - med).argmax()))
    bounds.append(total)
    return bounds


def extract_cells(fname, rows, cols, cell_px, cov_min, min_opaque, npal):
    src = rgb(RAW / fname); h, w = src.shape[:2]; bg = is_bg(src)
    lum = src @ [.299, .587, .114]
    xs = grid_bounds(cols, w, lum.mean(0), 12); ys = grid_bounds(rows, h, lum.mean(1), 20) if rows > 1 else [0, h]
    poses = []
    for ry in range(rows):
        for cx in range(cols):
            cell = ~bg[ys[ry]:ys[ry + 1], xs[cx]:xs[cx + 1]]
            lyr, lxs = np.nonzero(nd.binary_opening(cell, iterations=1))
            assert len(lyr) > 0, ('case vide', fname, ry, cx)
            cy = ys[ry] + int((lyr.min() + lyr.max()) / 2); xx = xs[cx] + int((lxs.min() + lxs.max()) / 2)
            side = int(max(lyr.max() - lyr.min(), lxs.max() - lxs.min())) + 16
            y0, x0 = cy - side // 2, xx - side // 2
            win = np.zeros((side, side, 4), 'uint8')
            sy0, sx0 = max(0, y0), max(0, x0); sy1, sx1 = min(h, y0 + side), min(w, x0 + side)
            win[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0, :3] = src[sy0:sy1, sx0:sx1]
            content = ~bg[sy0:sy1, sx0:sx1]
            eroded = nd.binary_erosion(content, iterations=1)
            use = eroded if eroded.sum() > 60 else content
            win[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0, 3] = np.where(use, 255, 0)
            o = down_rgba(win, cell_px, cov_min)
            assert (o[..., 3] > 0).sum() > min_opaque, ('pose vide', fname, ry, cx)
            poses.append(o)
    for i in range(len(poses)):
        for j in range(i + 1, len(poses)):
            assert (poses[i] != poses[j]).any(), ('poses identiques', fname, i, j)
    opq = np.concatenate([p[p[..., 3] > 0][:, :3] for p in poses])
    q = Image.fromarray(opq.reshape(-1, 1, 3)).quantize(npal, method=Image.Quantize.MEDIANCUT)
    spal = np.array(q.getpalette()[:npal * 3], 'uint8').reshape(npal, 3)
    for p in poses:
        m = p[..., 3] > 0
        p[..., :3] = spal[np.array(Image.fromarray(p[..., :3]).quantize(palette=q, dither=Image.Dither.NONE))]
        p[~m] = 0
    return poses, spal


# ---------------------------------------------------------------- Ground (gabarit amp, textes Horn)
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
    o.update(Name={'DefaultText': 'Entree Horn - sud vers nord (4:3)', 'LocalTexts': {}}, AssetName=ASSET, Released=False,
             TexSize=1, Music='', EdgeView=1, ViewCenter=None, ViewOffset={'X': 0, 'Y': 0}, ActiveChar=None, Status={},
             Layers=layers, Background={'$type': 'RogueEssence.Dungeon.LayeredBG, RogueEssence', 'Layers': []},
             Comment='PMDO 0.8.12. Rendu genere 4:3 (ref. Mt Horn, guide canonique) ; eboulis et poussieres '
                     'generes. Collisions de base a verifier. Seuil non raccorde.')
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
  <Name>Entree Horn sud-nord 4:3 - Atelier 0.8.12</Name>
  <Author>meromoonmeri</Author>
  <Description>Projet d'edition : grande entree de montagne generee au format 4:3 (ref. Mt Horn), eboulis et poussieres animes. Pas une aventure jouable.</Description>
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
    for d in ['calques', 'animation/eboulis', 'animation/poussieres', 'poses_eboulis', 'poses_poussieres', 'masques', 'review']:
        (OUT / d).mkdir(parents=True, exist_ok=True)
    a = rgb(RAW / 'decor_magenta.png')
    assert a.shape[:2] == (SRC[1], SRC[0]), a.shape
    f_raw = rgb(RAW / 'sol_complet.png')
    sol_scale, sol_crop, f = norm_full(f_raw)
    m = classify(a)
    order = ['sand', 'path', 'walls', 'boulders', 'bush', 'cave']
    ex, cols = down_class(a, m, order)
    names = {'sand': 'cour', 'path': 'sentier', 'walls': 'parois', 'boulders': 'blocs', 'bush': 'buissons', 'cave': 'grotte'}
    layers = {'sol_complet': rgba(down_full(f), np.ones((H, W), bool))}
    for k, nm in names.items():
        layers[nm] = rgba(cols[k], ex[k])
    layers = quantize_layers(layers)
    for k, v in ex.items():
        Image.fromarray((v * 255).astype('uint8')).save(OUT / 'masques' / f'{PFX}_masque_{k}.png')
    sand_mean = layers['cour'][layers['cour'][..., 3] == 255][:, :3].mean(0).round(1)
    taken = np.zeros((H, W), bool)
    rock = ex['walls'] | ex['boulders']
    # Éboulis : 6 émetteurs au pied des rochers (< 32 px), 16 actives + 8 repos.
    eb, ebpal = extract_cells('eboulis_poses.png', 1, 8, EB_CELL, 0.12, 15, 12)
    for i, p in enumerate(eb):
        Image.fromarray(p).save(OUT / 'poses_eboulis' / f'{PFX}_eboulis_{i}.png')
    near = (nd.distance_transform_edt(~rock) < 32) & ex['sand']
    eboulis = []
    for i, (y, x) in enumerate(place(near, (EB_CELL, EB_CELL), 6, 53, taken, core=8)):
        eboulis.append({'xy': [x, y], 'decalage': (i * 4) % EB_PHASES})
    assert len(eboulis) == 6, len(eboulis)
    ef = [np.zeros((H, W, 4), 'uint8') for _ in range(EB_PHASES)]
    for e in eboulis:
        x, y = e['xy']
        for t in range(EB_PHASES):
            u = (t - e['decalage']) % EB_PHASES
            if u < EB_ACTIVE:
                p = eb[u // 2]; mm = p[..., 3] > 0
                ef[t][y:y + EB_CELL, x:x + EB_CELL][mm] = p[mm]
    # Poussières : 6 émetteurs sur la cour, 20 actives + 4 repos.
    du, dupal = extract_cells('poussieres_poses.png', 2, 5, DU_CELL, 0.10, 8, 12)
    for i, p in enumerate(du):
        Image.fromarray(p).save(OUT / 'poses_poussieres' / f'{PFX}_poussiere_{i}.png')
    poussieres = []
    for i, (y, x) in enumerate(place(ex['sand'], (DU_CELL, DU_CELL), 6, 71, taken, core=8)):
        poussieres.append({'xy': [x, y], 'decalage': (i * 4 + 2) % DU_PHASES})
    assert len(poussieres) == 6, len(poussieres)
    df = [np.zeros((H, W, 4), 'uint8') for _ in range(DU_PHASES)]
    for e in poussieres:
        x, y = e['xy']
        for t in range(DU_PHASES):
            u = (t - e['decalage']) % DU_PHASES
            if u < DU_ACTIVE:
                p = du[u // 2]; mm = p[..., 3] > 0
                df[t][y:y + DU_CELL, x:x + DU_CELL][mm] = p[mm]
    # Exports
    for t, fr in enumerate(ef):
        Image.fromarray(fr).save(OUT / 'animation/eboulis' / f'{PFX}_07_eboulis_f{t:02d}.png')
    for t, fr in enumerate(df):
        Image.fromarray(fr).save(OUT / 'animation/poussieres' / f'{PFX}_08_poussieres_f{t:02d}.png')
    static_order = ['sol_complet'] + list(names.values())
    files = {}
    for i, nm in enumerate(static_order):
        fn = f'{PFX}_{i:02d}_{nm}.png'; Image.fromarray(layers[nm]).save(OUT / 'calques' / fn); files[nm] = fn
    stack_named = [(nm, [layers[nm]], 60) for nm in static_order] + [('eboulis', ef, EB_TICKS), ('poussieres', df, DU_TICKS)]
    # Collisions : cour et sentier praticables.
    walk = (layers['cour'][..., 3] == 255) | (layers['sentier'][..., 3] == 255)
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
        ep = (tick // EB_TICKS) % EB_PHASES; dp = (tick // DU_TICKS) % DU_PHASES
        im = Image.new('RGBA', (W, H))
        for title, frames, _ in stack_named:
            im.alpha_composite(Image.fromarray(frames[{'eboulis': ep, 'poussieres': dp}.get(title, 0)]))
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
    sheet = Image.new('RGBA', (10 * 68, 72), (213, 180, 120, 255))
    for i, p in enumerate(eb):
        sheet.alpha_composite(Image.fromarray(p).resize((64, 64), Image.Resampling.NEAREST), (i * 68, 4))
    sheet.save(OUT / 'review' / f'{PFX}_planche_eboulis_x4.png')
    sheet2 = Image.new('RGBA', (10 * 68, 72), (213, 180, 120, 255))
    for i, p in enumerate(du):
        sheet2.alpha_composite(Image.fromarray(p).resize((64, 64), Image.Resampling.NEAREST), (i * 68, 4))
    sheet2.save(OUT / 'review' / f'{PFX}_planche_poussieres_x4.png')
    eb_colors = int(len(np.unique(np.concatenate([p[p[..., 3] > 0][:, :3] for p in eb]).reshape(-1, 3), axis=0)))
    du_colors = int(len(np.unique(np.concatenate([p[p[..., 3] > 0][:, :3] for p in du]).reshape(-1, 3), axis=0)))
    write_ora(OUT / f'{PFX}_entree_horn_calques.ora',
              {f'{i:02d}_{t}' + ('_f0' if len(fr) > 1 else ''): fr[0] for i, (t, fr, _) in enumerate(stack_named)})
    counts = ground_project([(t.replace('_', ' ') + (f' {len(fr)} phases' if len(fr) > 1 else ''), fr, tk)
                             for t, fr, tk in stack_named], blocked, entry_px, threshold_px, gfx, tools)
    order_files = [f'calques/{files[nm]}' for nm in static_order] + \
                  [f'animation/eboulis/{PFX}_07_eboulis_fXX.png', f'animation/poussieres/{PFX}_08_poussieres_fXX.png']
    ref = rgb(R / 'Mt_Horn_entrance_Sky.png'); rr, rg, rb_ = ref.transpose(2, 0, 1); rlum = ref @ [.299, .587, .114]
    ref_sand = ref[((rr - rb_) > 30) & (rlum > 100) & (rlum < 220)].mean(0).round(1)
    manifest = {
        'lot': 'entree_horn_sud_nord_v1', 'format': '4:3 vaste', 'size_px': [W, H], 'grid_8px': [W // 8, H // 8],
        'method': 'rendu genere 4:3 guide par la ref canonique : decor complet + sol genere separement',
        'reference_da': 'Mt_Horn_entrance_Sky.png',
        'raw_inputs': [{'file': f'source/entree_horn_sud_nord_v1/bruts/{n}', 'sha256': sha(RAW / n),
                        'size': list(Image.open(RAW / n).size)} for n in ['decor_magenta.png', 'sol_complet.png', 'eboulis_poses.png', 'poussieres_poses.png']],
        'normalization': {'scale': SCALE, 'scaled': [SCALED_W, H], 'crop_x': [CROP_X, SCALED_W - W - CROP_X],
                          'methode': 'moyenne ponderee par classe (BOX), attribution exclusive par poids maximal, palette commune 96 couleurs',
                          'sol': {'facteur_cover': sol_scale, 'recadrage_xy': list(sol_crop), 'taille_source': list(Image.open(RAW / 'sol_complet.png').size)}},
        'segmentation': 'roche = germes lum<125 & r-b<105 + croissance bornee 8 px (lum<170 & r-b<130) ; '
                        'grotte = compo sombre de la boite nord-centre (430-770, <230) ; parois = roche au bord ; '
                        'blocs = compos >= 400 px ; sentier = lisse (std11<9) et clair touchant le bas ; '
                        'buissons = densite std3>12 en 31 px > 0,40 (compos >= 800 px, 6 attendus), exclus de la roche ; cour = reste',
        'layer_order_bottom_to_top': order_files,
        'eboulis': {'poses': EB_POSES, 'phases_actives': EB_ACTIVE, 'phases': EB_PHASES, 'frame_length_ticks': EB_TICKS,
                    'couleurs_distinctes': eb_colors, 'palette_12': [list(map(int, c)) for c in ebpal], 'emetteurs': eboulis,
                    'origine': 'dessin GENERE (planche 1x8), chronologie creee (8 poses x2 + 8 repos) ; pas une animation officielle'},
        'poussieres': {'poses': DU_POSES, 'phases_actives': DU_ACTIVE, 'phases': DU_PHASES, 'frame_length_ticks': DU_TICKS,
                       'couleurs_distinctes': du_colors, 'palette_12': [list(map(int, c)) for c in dupal], 'emetteurs': poussieres,
                       'origine': 'dessin GENERE (planche 2x5 lue en ligne), chronologie creee (10 poses x2 + 4 repos) ; pas une animation officielle'},
        'canonique': {'ref_sable_moyenne': list(map(float, ref_sand)), 'decor_sable_moyenne': list(map(float, sand_mean)),
                      'distance': float(np.linalg.norm(np.array(sand_mean, float) - np.array(ref_sand, float)))},
        'scene_loop_ticks': LOOP_TICKS,
        'access': {'entry_px': entry_px, 'threshold_px': threshold_px, 'path_found_16x16': ok, 'cells_explored': explored,
                   'blocked_cells': int(blocked.sum()), 'total_cells': int(blocked.size),
                   'rule': 'case bloquee si > 25 % hors cour/sentier'},
        'pmdo': {'target': '0.8.12', 'asset': ASSET, 'namespace': NAMESPACE, 'tiles_per_bank': counts, 'banks': list(counts),
                 'runtime_tested': False, 'warp': 'aucun'},
        'art_approved': False,
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    shutil.copyfile(OUT / 'manifest.json', STAGE / 'manifest.json')
    print(json.dumps({'entry': entry_px, 'threshold': threshold_px, 'blocked': int(blocked.sum()), 'cells': int(blocked.size),
                      'sable': list(map(float, sand_mean)), 'ref_sable': list(map(float, ref_sand)),
                      'eb_colors': eb_colors, 'du_colors': du_colors, 'tiles': counts}, indent=1))


if __name__ == '__main__':
    build()
