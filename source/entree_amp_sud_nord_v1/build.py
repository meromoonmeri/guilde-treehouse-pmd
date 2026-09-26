"""Entrée Amp sud -> nord V1 — plaine électrique, format 4:3 vaste (768 x 576 px, 96 x 72 cases).

Réf. DA : Amp_Plains_entrance_TD.png (TDS). Exigence utilisateur : « même endroit, autre lieu » —
mêmes matériaux atténués (herbe olive, roche bleu-gris, arbres morts noirs), layout inédit (sentier
en S, grotte au nord). Les bruts décor/sol/touffes sont générés AVEC la ref canonique en guide
(une première version sans guide, trop saturée, a été écartée après comparaison colorimétrique).
Fidélité mesurée : test_canonical_grass compare l'herbe du décor à celle de la ref.
Méthode rendu généré : décor 1200x896 + sol complet normalisé (cover uniforme + recadrage centré).
Réduction x(576/896) par classe (jungle), palette commune 96 couleurs.
Animations, chacune sur son calque :
- touffes d'herbe (12 x 10 ticks, cycle sinusoïdal sur inclinaisons MESURÉES, méthode bristle) ;
- étincelles électriques (8 poses lifecycle x2 + 8 repos = 24 x 5 ticks, 7 émetteurs décalés).
Scène : 120 ticks = 2 s. Pas d'eau (plaine sèche), pas de magenta résiduel (0 px en entrée).
Lancer : .venv/bin/python source/entree_amp_sud_nord_v1/build.py
"""
from pathlib import Path
import hashlib, importlib.util, json, shutil, uuid, zipfile

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
RAW = HERE / 'bruts'
OUT = R / 'renders/entree_amp_sud_nord_v1'
STAGE = R / '.cache/entree_amp_sud_nord_v1/entree_amp_sud_nord'
NAMESPACE = 'entree_amp_sud_nord'
ASSET = 'ean1_entree_amp'
PFX = 'EAN1'
W, H = 768, 576                      # 4:3, 96 x 72 cases
SRC = (1200, 896)
SCALE = H / SRC[1]                   # 0,642857, identique en X et Y
SCALED_W = round(SRC[0] * SCALE)     # 771
CROP_X = (SCALED_W - W) // 2         # 1
TUFT_PHASES, TUFT_TICKS = 12, 10
SPK_POSES, SPK_ACTIVE, SPK_PHASES, SPK_TICKS = 8, 16, 24, 5
LOOP_TICKS = 120
TCELL, SCELL = 16, 24


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
    # Sentier : tan clair (lum~182, r-b~40) ; germes sûrs puis croissance bornée, compo touchant le bas.
    seed = (lum > 175) & (rb > 38)
    grow = (lum > 145) & (rb > 30)
    path = seed
    for _ in range(6):
        path = (nd.binary_dilation(path) & grow) | seed
    path = nd.binary_fill_holes(keep_large(nd.binary_closing(path, iterations=2), 1500))
    lab, n = nd.label(path)
    keep = set(np.unique(lab[-10:][path[-10:]])) - {0}
    path = np.isin(lab, list(keep)) if keep else path
    # Roche : bleu-gris, r-b négatif (murs ~-22, blocs ~-11).
    rock = (rb < 0) & (lum < 175)
    rock = nd.binary_closing(rock, iterations=2)
    dark = rock & (lum < 62)
    # Grotte : compo sombre contenant le pixel le plus sombre de la boîte nord-centre.
    yy, xx = np.mgrid[:a.shape[0], :a.shape[1]]
    box = (xx > 430) & (xx < 770) & (yy < 230)
    cand = dark & box
    lab, n = nd.label(cand)
    assert n > 0, 'aucune compo sombre dans la boite grotte'
    sz = nd.sum(cand, lab, range(1, n + 1)); bi = int(np.argmax(sz)) + 1
    cave = nd.binary_fill_holes(lab == bi)
    assert 1500 < cave.sum() < 25000, ('grotte inattendue', int(cave.sum()))
    rock_nb = nd.binary_closing(rock & ~cave, iterations=2)
    # Parois = roche touchant le bord ; blocs = composantes intérieures >= 250 px.
    lab, n = nd.label(rock_nb); band = np.zeros_like(rock_nb)
    band[:8] = band[-8:] = True; band[:, :8] = band[:, -8:] = True
    border = set(np.unique(lab[band & rock_nb])) - {0}
    walls = np.isin(lab, list(border))
    boulders = keep_large(rock_nb & ~walls, 250)
    # Arbres morts : troncs/branches (lum < 125, r-b < 8) posés sur la plaine, hors rochers.
    tree_cand = (lum < 125) & (rb < 8) & ~path
    tree_cand &= ~nd.binary_dilation(walls | boulders | cave, iterations=12)
    trees = keep_large(nd.binary_closing(tree_cand, iterations=1), 150)
    _lab, _n = nd.label(trees)
    assert 1 <= _n <= 8 and 500 < trees.sum() < 30000, ('arbres', _n, int(trees.sum()))
    grass = ~(path | walls | boulders | trees | cave)
    return dict(grass=grass, path=path, walls=walls, boulders=boulders, trees=trees, cave=cave)


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


# ---------------------------------------------------------------- touffes : inclinaisons mesurées, cycle sinusoïdal (bristle)
def tuft_poses():
    src = rgb(RAW / 'touffes_vent_poses.png'); mag = is_mag(src)
    obj = nd.binary_closing(~mag, iterations=2)
    lab, n = nd.label(obj); sizes = nd.sum(obj, lab, range(1, n + 1))
    ids = [i + 1 for i in np.argsort(sizes)[-8:]]
    assert len(ids) == 8 and sizes[ids[0] - 1] > 400, ('touffes', n, sorted(sizes))
    hmax = 0
    for i in ids:
        ys = np.nonzero(((lab == i) & ~mag).any(1))[0]; hmax = max(hmax, ys.max() - ys.min())
    k = max(5, int(np.ceil((hmax + 8) / TCELL))); win = TCELL * k
    poses = []
    for i in ids:
        ys, xs = np.nonzero((lab == i) & ~mag)
        by = ys.max(); bottom = ys >= by - (by - ys.min()) * 0.2
        bx = int(round(xs[bottom].mean())); top = ys <= ys.min() + (by - ys.min()) * 0.4
        lean = (xs[top].mean() - bx) / max(by - ys.min(), 1)
        y0, x0 = by + 1 - win, bx - win // 2
        assert 0 <= y0 and 0 <= x0 and y0 + win <= src.shape[0] and x0 + win <= src.shape[1]
        pad = src[y0:y0 + win, x0:x0 + win]
        pm = ((lab == i) & ~mag)[y0:y0 + win, x0:x0 + win]
        cov = pm.reshape(TCELL, k, TCELL, k).mean((1, 3))
        col = (pad * pm[..., None]).reshape(TCELL, k, TCELL, k, 3).sum((1, 3)) / np.maximum(pm.reshape(TCELL, k, TCELL, k).sum((1, 3)), 1)[..., None]
        o = np.zeros((TCELL, TCELL, 4), 'uint8'); o[..., :3] = np.clip(col, 0, 255); o[..., 3] = 255; o[cov < 0.3] = 0
        poses.append({'lean': float(lean), 'img': o})
    opq = np.concatenate([p['img'][p['img'][..., 3] > 0][:, :3] for p in poses])
    q = Image.fromarray(opq.reshape(-1, 1, 3)).quantize(7, method=Image.Quantize.MEDIANCUT)
    pal = np.array(q.getpalette()[:21], 'uint8').reshape(7, 3)
    for p in poses:
        m = p['img'][..., 3] > 0
        p['img'][..., :3] = pal[np.array(Image.fromarray(p['img'][..., :3]).quantize(palette=q, dither=Image.Dither.NONE))]
        p['img'][~m] = 0
    poses.sort(key=lambda p: p['lean'])
    leans = np.array([p['lean'] for p in poses]); mid = float((leans.max() + leans.min()) / 2)
    amp = float((leans.max() - leans.min()) / 2)   # pleine amplitude mesurée : le cycle balaie toutes les poses
    cycle = [int(np.abs(leans - (mid + amp * np.sin(2 * np.pi * t / TUFT_PHASES))).argmin()) for t in range(TUFT_PHASES)]
    return poses, cycle, [float(v) for v in leans], pal, k


# ---------------------------------------------------------------- étincelles : 8 poses lifecycle centrées, traits fins
def down_rgba(win, size, cov_min):
    f = win.astype(np.float32); al = f[..., 3:4] / 255.0
    num = np.stack([np.array(Image.fromarray((f[..., c] * al[..., 0]), 'F').resize((size, size), Image.Resampling.BOX)) for c in range(3)], -1)
    den = np.array(Image.fromarray(al[..., 0], 'F').resize((size, size), Image.Resampling.BOX))
    o = np.zeros((size, size, 4), 'uint8')
    o[..., :3] = np.clip(np.round(num / np.maximum(den, 1e-6)[..., None]), 0, 255)
    o[..., 3] = 255; o[den < cov_min] = 0
    return o


def spark_poses():
    src = rgb(RAW / 'etincelles_poses.png'); h, w = src.shape[:2]; mag = is_mag(src)
    cw = w / SPK_POSES; poses = []
    for cx in range(SPK_POSES):
        cell = ~mag[:, int(cx * cw):int((cx + 1) * cw)]
        ys, xs = np.nonzero(nd.binary_opening(cell, iterations=1))
        assert len(ys) > 0, ('case étincelle vide', cx)
        cy = int((ys.min() + ys.max()) / 2); xx = int(cx * cw + (xs.min() + xs.max()) / 2)
        side = int(max(ys.max() - ys.min(), xs.max() - xs.min())) + 16
        y0, x0 = cy - side // 2, xx - side // 2
        win = np.zeros((side, side, 4), 'uint8')
        sy0, sx0 = max(0, y0), max(0, x0); sy1, sx1 = min(h, y0 + side), min(w, x0 + side)
        win[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0, :3] = src[sy0:sy1, sx0:sx1]
        content = ~mag[sy0:sy1, sx0:sx1]
        eroded = nd.binary_erosion(content, iterations=1)   # anti-frange magenta (traits conservés : repli sinon)
        use = eroded if eroded.sum() > 60 else content
        win[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0, 3] = np.where(use, 255, 0)
        o = down_rgba(win, SCELL, 0.12)
        assert (o[..., 3] > 0).sum() > 15, ('étincelle vide', cx)
        poses.append(o)
    for i in range(len(poses)):
        for j in range(i + 1, len(poses)):
            assert (poses[i] != poses[j]).any(), ('poses étincelles identiques', i, j)
    opq = np.concatenate([p[p[..., 3] > 0][:, :3] for p in poses])
    q = Image.fromarray(opq.reshape(-1, 1, 3)).quantize(12, method=Image.Quantize.MEDIANCUT)
    spal = np.array(q.getpalette()[:36], 'uint8').reshape(12, 3)
    for p in poses:
        m = p[..., 3] > 0
        p[..., :3] = spal[np.array(Image.fromarray(p[..., :3]).quantize(palette=q, dither=Image.Dither.NONE))]
        p[~m] = 0
    return poses, spal


# ---------------------------------------------------------------- Ground (gabarit jungle, textes Amp)
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
    o.update(Name={'DefaultText': 'Entree Amp - sud vers nord (4:3)', 'LocalTexts': {}}, AssetName=ASSET, Released=False,
             TexSize=1, Music='', EdgeView=1, ViewCenter=None, ViewOffset={'X': 0, 'Y': 0}, ActiveChar=None, Status={},
             Layers=layers, Background={'$type': 'RogueEssence.Dungeon.LayeredBG, RogueEssence', 'Layers': []},
             Comment='PMDO 0.8.12. Rendu genere 4:3 (ref. Amp Plains, guide canonique) ; touffes et etincelles '
                     'generees. Collisions de base a verifier. Seuil non raccorde.')
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
  <Name>Entree Amp sud-nord 4:3 - Atelier 0.8.12</Name>
  <Author>meromoonmeri</Author>
  <Description>Projet d'edition : grande entree de plaine generee au format 4:3 (ref. Amp Plains), touffes et etincelles animees. Pas une aventure jouable.</Description>
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
    for d in ['calques', 'animation/touffes', 'animation/etincelles', 'poses_touffes', 'poses_etincelles', 'masques', 'review']:
        (OUT / d).mkdir(parents=True, exist_ok=True)
    a = rgb(RAW / 'decor_magenta.png')
    assert a.shape[:2] == (SRC[1], SRC[0]), a.shape
    f_raw = rgb(RAW / 'sol_complet.png')
    sol_scale, sol_crop, f = norm_full(f_raw)
    m = classify(a)
    order = ['grass', 'path', 'walls', 'boulders', 'trees', 'cave']
    ex, cols = down_class(a, m, order)
    names = {'grass': 'plaine', 'path': 'sentier', 'walls': 'parois', 'boulders': 'blocs', 'trees': 'arbres_morts', 'cave': 'grotte'}
    layers = {'sol_complet': rgba(down_full(f), np.ones((H, W), bool))}
    for k, nm in names.items():
        layers[nm] = rgba(cols[k], ex[k])
    layers = quantize_layers(layers)
    for k, v in ex.items():
        Image.fromarray((v * 255).astype('uint8')).save(OUT / 'masques' / f'{PFX}_masque_{k}.png')
    grass_mean = layers['plaine'][layers['plaine'][..., 3] == 255][:, :3].mean(0).round(1)
    # Touffes : 10 émetteurs sur la plaine, rafale d'ouest en est (décalage x//40).
    poses, cycle, leans, tpal, tk = tuft_poses()
    for i, p in enumerate(poses):
        Image.fromarray(p['img']).save(OUT / 'poses_touffes' / f'{PFX}_touffe_{i}.png')
    taken = np.zeros((H, W), bool)
    free = ex['grass']
    tufts = []
    for (y, x) in place(free, (TCELL, TCELL), 10, 41, taken, core=8):
        tufts.append({'xy': [x, y], 'decalage': (x // 40) % TUFT_PHASES})
    assert len(tufts) == 10, len(tufts)
    tf = [np.zeros((H, W, 4), 'uint8') for _ in range(TUFT_PHASES)]
    for e in tufts:
        x, y = e['xy']
        for t in range(TUFT_PHASES):
            p = poses[cycle[(t + e['decalage']) % TUFT_PHASES]]['img']; mm = p[..., 3] > 0
            tf[t][y:y + TCELL, x:x + TCELL][mm] = p[mm]
    # Étincelles : 7 émetteurs sur la plaine près des rochers (< 32 px), cycle 16 actives + 8 repos.
    spk, spal = spark_poses()
    for i, p in enumerate(spk):
        Image.fromarray(p).save(OUT / 'poses_etincelles' / f'{PFX}_etincelle_{i}.png')
    rock = ex['walls'] | ex['boulders']
    near = (nd.distance_transform_edt(~rock) < 32) & ex['grass']
    sparks = []
    for i, (y, x) in enumerate(place(near, (SCELL, SCELL), 7, 97, taken, core=8)):
        sparks.append({'xy': [x, y], 'decalage': (i * 3) % SPK_PHASES})
    assert len(sparks) == 7, len(sparks)
    sf = [np.zeros((H, W, 4), 'uint8') for _ in range(SPK_PHASES)]
    for e in sparks:
        x, y = e['xy']
        for t in range(SPK_PHASES):
            u = (t - e['decalage']) % SPK_PHASES
            if u < SPK_ACTIVE:
                p = spk[u // 2]; mm = p[..., 3] > 0
                sf[t][y:y + SCELL, x:x + SCELL][mm] = p[mm]
    # Exports
    for t, fr in enumerate(tf):
        Image.fromarray(fr).save(OUT / 'animation/touffes' / f'{PFX}_07_touffes_f{t:02d}.png')
    for t, fr in enumerate(sf):
        Image.fromarray(fr).save(OUT / 'animation/etincelles' / f'{PFX}_08_etincelles_f{t:02d}.png')
    static_order = ['sol_complet'] + list(names.values())
    files = {}
    for i, nm in enumerate(static_order):
        fn = f'{PFX}_{i:02d}_{nm}.png'; Image.fromarray(layers[nm]).save(OUT / 'calques' / fn); files[nm] = fn
    stack_named = [(nm, [layers[nm]], 60) for nm in static_order] + [('touffes', tf, TUFT_TICKS), ('etincelles', sf, SPK_TICKS)]
    # Collisions : plaine et sentier praticables.
    walk = (layers['plaine'][..., 3] == 255) | (layers['sentier'][..., 3] == 255)
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
        tp = (tick // TUFT_TICKS) % TUFT_PHASES; sp = (tick // SPK_TICKS) % SPK_PHASES
        im = Image.new('RGBA', (W, H))
        for title, frames, _ in stack_named:
            im.alpha_composite(Image.fromarray(frames[{'touffes': tp, 'etincelles': sp}.get(title, 0)]))
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
    sheet = Image.new('RGBA', (8 * 68, 136), (141, 146, 117, 255))
    for i, p in enumerate(poses):
        sheet.alpha_composite(Image.fromarray(p['img']).resize((64, 64), Image.Resampling.NEAREST), (i * 68, 0))
    for i, p in enumerate(spk):
        sheet.alpha_composite(Image.fromarray(p).resize((64, 64), Image.Resampling.NEAREST), (i * 68, 72))
    sheet.save(OUT / 'review' / f'{PFX}_planche_poses_x4.png')
    spk_colors = int(len(np.unique(np.concatenate([p[p[..., 3] > 0][:, :3] for p in spk]).reshape(-1, 3), axis=0)))
    write_ora(OUT / f'{PFX}_entree_amp_calques.ora',
              {f'{i:02d}_{t}' + ('_f0' if len(fr) > 1 else ''): fr[0] for i, (t, fr, _) in enumerate(stack_named)})
    counts = ground_project([(t.replace('_', ' ') + (f' {len(fr)} phases' if len(fr) > 1 else ''), fr, tk)
                             for t, fr, tk in stack_named], blocked, entry_px, threshold_px, gfx, tools)
    order_files = [f'calques/{files[nm]}' for nm in static_order] + \
                  [f'animation/touffes/{PFX}_07_touffes_fXX.png', f'animation/etincelles/{PFX}_08_etincelles_fXX.png']
    ref = rgb(R / 'Amp_Plains_entrance_TD.png'); rr, rg, rb_ = ref.transpose(2, 0, 1); rlum = ref @ [.299, .587, .114]
    ref_grass = ref[((rr - rb_) > 15) & (rlum > 100) & (rlum < 175)].mean(0).round(1)
    manifest = {
        'lot': 'entree_amp_sud_nord_v1', 'format': '4:3 vaste', 'size_px': [W, H], 'grid_8px': [W // 8, H // 8],
        'method': 'rendu genere 4:3 guide par la ref canonique : decor complet + sol genere separement',
        'reference_da': 'Amp_Plains_entrance_TD.png',
        'raw_inputs': [{'file': f'source/entree_amp_sud_nord_v1/bruts/{n}', 'sha256': sha(RAW / n),
                        'size': list(Image.open(RAW / n).size)} for n in ['decor_magenta.png', 'sol_complet.png', 'touffes_vent_poses.png', 'etincelles_poses.png']],
        'normalization': {'scale': SCALE, 'scaled': [SCALED_W, H], 'crop_x': [CROP_X, SCALED_W - W - CROP_X],
                          'methode': 'moyenne ponderee par classe (BOX), attribution exclusive par poids maximal, palette commune 96 couleurs',
                          'sol': {'facteur_cover': sol_scale, 'recadrage_xy': list(sol_crop), 'taille_source': list(Image.open(RAW / 'sol_complet.png').size)}},
        'segmentation': 'sentier = germes lum>175 & r-b>38 + croissance bornee 6 px (lum>145 & r-b>30), compo touchant le bas ; '
                        'roche = r-b<0 & lum<175 ; grotte = compo sombre de la boite nord-centre (430-770, <230) ; '
                        'parois = roche au bord ; blocs = compos >= 250 px ; arbres = lum<125 & r-b<8 hors sentier et hors rochers dilates 12 px, compos >= 150 px ; plaine = reste',
        'layer_order_bottom_to_top': order_files,
        'touffes': {'poses': TUFT_PHASES and len(poses), 'phases': TUFT_PHASES, 'frame_length_ticks': TUFT_TICKS,
                    'inclinaisons_mesurees': leans, 'cycle': cycle, 'fenetre_reduction': tk,
                    'palette_7': [list(map(int, c)) for c in tpal], 'emetteurs': tufts,
                    'origine': 'dessin GENERE guide par la ref, palette propre olive ; cycle sinusoidal sur mesures, pas une animation officielle'},
        'etincelles': {'poses': SPK_POSES, 'phases_actives': SPK_ACTIVE, 'phases': SPK_PHASES, 'frame_length_ticks': SPK_TICKS,
                       'couleurs_distinctes': spk_colors, 'palette_12': [list(map(int, c)) for c in spal], 'emetteurs': sparks,
                       'origine': 'dessin GENERE, chronologie creee (8 poses x2 + 8 repos) ; pas une animation officielle'},
        'canonique': {'ref_herbe_moyenne': list(map(float, ref_grass)), 'decor_herbe_moyenne': list(map(float, grass_mean)),
                      'distance': float(np.linalg.norm(np.array(grass_mean, float) - np.array(ref_grass, float)))},
        'scene_loop_ticks': LOOP_TICKS,
        'access': {'entry_px': entry_px, 'threshold_px': threshold_px, 'path_found_16x16': ok, 'cells_explored': explored,
                   'blocked_cells': int(blocked.sum()), 'total_cells': int(blocked.size),
                   'rule': 'case bloquee si > 25 % hors plaine/sentier'},
        'pmdo': {'target': '0.8.12', 'asset': ASSET, 'namespace': NAMESPACE, 'tiles_per_bank': counts, 'banks': list(counts),
                 'runtime_tested': False, 'warp': 'aucun'},
        'art_approved': False,
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    shutil.copyfile(OUT / 'manifest.json', STAGE / 'manifest.json')
    print(json.dumps({'leans': [round(v, 3) for v in leans], 'cycle': cycle, 'k': tk, 'entry': entry_px, 'threshold': threshold_px,
                      'blocked': int(blocked.sum()), 'cells': int(blocked.size), 'herbe': list(map(float, grass_mean)),
                      'ref_herbe': list(map(float, ref_grass)), 'spk_colors': spk_colors, 'tiles': counts}, indent=1))


if __name__ == '__main__':
    build()
