"""Entrée Ruine sud -> nord V1 — rendu généré, référence PMD Sky « Sealed Ruin ».

Même méthode que ESN/ECN : décor complet généré sur magenta (fosses de sables mouvants = magenta), sol complet
généré séparément, normalisation uniforme exacte x0,5 (848x1264 -> 424x632), moyenne 2x2 par classe.
Animations, chacune sur son calque :
- sables mouvants « façon rivière Métano » : structure/cadence Métano (4 phases x 10 ticks) recalculée sur nos fosses ;
- bulles de sable : planche générée 2 x 6 (12 poses), 24 phases x 5 ticks, émetteurs décalés ;
- tourbillons de poussière : planche générée 2 x 4 (8 poses), 8 phases x 5 ticks, décoratifs (pas de collision).
Scène complète : PPCM 120 ticks = 2 s.
Lancer : .venv/bin/python source/entree_ruine_sud_nord_v1/build.py
"""
from pathlib import Path
import hashlib, importlib.util, json, shutil, uuid, zipfile

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
RAW = HERE / 'bruts'
OUT = R / 'renders/entree_ruine_sud_nord_v1'
STAGE = R / '.cache/entree_ruine_sud_nord_v1/entree_ruine_sud_nord'
NAMESPACE = 'entree_ruine_sud_nord'
ASSET = 'ern1_entree_ruine'
PFX = 'ERN1'
W, H = 424, 632
FULL = (848, 1264)
SAND_PHASES, SAND_TICKS = 4, 10
BUBBLE_PHASES, BUBBLE_TICKS = 24, 5
DEVIL_PHASES, DEVIL_TICKS = 8, 5
LOOP_TICKS = 120
CELL = 24
DEVIL_CELL = 40
SAND_REF = (229, 206, 153)          # sable du décor, mesuré (moyenne de deux zones dégagées)

# Palette des sables mouvants : rôles et ordre de luminance Métano, teintes du sable du décor assombries.
PAL = {'lip': (112, 72, 36), 'bande': (146, 100, 54), 'inter': (172, 128, 74), 'accent': (190, 148, 92),
       'surface': (206, 166, 108), 'clair': (224, 192, 136), 'pale': (238, 216, 166), 'contour': (86, 52, 26)}

cr = None


def loadmod(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rgb(p):
    return np.array(Image.open(p).convert('RGB')).astype(int)


# ---------------------------------------------------------------- segmentation (pleine résolution)
def classify(a):
    keep_large = cr.keep_large
    r, g, b = a.transpose(2, 0, 1); lum = a @ [.299, .587, .114]; sat = a.max(2) - a.min(2)
    mag = (r > g * 1.6) & (b > g * 1.4) & (r > 120) & (b > 100)
    pits = nd.binary_dilation(mag, iterations=1)
    d = np.sqrt(((a - SAND_REF) ** 2).sum(2))
    sand = nd.binary_opening(nd.uniform_filter((d < 45).astype(float), 7) > 0.6, iterations=2) & ~pits
    sand = keep_large(sand, 5000)
    non = nd.binary_opening(~sand & ~pits, iterations=1)
    # Arbres morts : cœur gris (sat < 50, |r-b| < 50, lum 80-210), fermé, étendu aux contours sombres peu saturés.
    core = (sat < 50) & (np.abs(r - b) < 50) & (lum > 80) & (lum < 210)
    trees = keep_large(nd.binary_closing(core, iterations=3), 800)
    trees = nd.binary_fill_holes(nd.binary_dilation(trees, iterations=3) & (sat < 75) & ~pits) | trees
    trees = keep_large(trees & (d > 25), 800)                        # jamais de pixel couleur sable
    yy, xx = np.mgrid[:a.shape[0], :a.shape[1]]
    mouth = (lum < 25) & (yy > 300) & (yy < 460) & (xx > 380) & (xx < 540) & ~trees
    mouth = keep_large(nd.binary_fill_holes(nd.binary_opening(nd.binary_closing(mouth, iterations=2), iterations=2)), 2000)
    rest = non & ~trees & ~mouth
    lab, _ = nd.label(rest)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    cliffs = np.isin(lab, list(border))
    near = nd.binary_dilation(pits, iterations=24)
    rims = rest & ~cliffs & near
    boulders = keep_large(rest & ~cliffs & ~rims, 300)
    sand = ~(cliffs | trees | boulders | rims | pits | mouth)       # cailloux/miettes isolés -> sable
    return dict(pits=pits, sand=sand, rims=rims, boulders=boulders, cliffs=cliffs, mouth=mouth, trees=trees)


# ---------------------------------------------------------------- planches générées
def extract_poses(path, rows, cols, picks, win, cell, thin, pal):
    src = rgb(path); h, w = src.shape[:2]
    r, g, b = src.transpose(2, 0, 1)
    mag = (r > 150) & (b > 110) & (g < 130) & (r > g * 1.5) & (b > g * 1.25)
    cw, ch = w / cols, h / rows; k = win // cell
    # base verticale commune par rangée = médiane des bas de contenu des cases de la rangée
    bases = []
    for ry in range(rows):
        bots = []
        for cx in range(cols):
            m = ~mag[int(ry * ch):int((ry + 1) * ch), int(cx * cw):int((cx + 1) * cw)]
            m = cr.keep_large(m, 30)
            ys = np.nonzero(m.any(1))[0]
            if len(ys):
                bots.append(int(ry * ch) + ys.max())
        bases.append(int(np.median(bots)))
    out = {}
    for name, ry, cx in picks:
        x0 = int((cx + 0.5) * cw) - win // 2; y0 = bases[ry] - int(win * (cell - 3) / cell)
        pad = np.zeros((win, win, 3), int); pm = np.zeros((win, win), bool)
        sy0, sx0 = max(0, y0), max(0, x0); sy1, sx1 = min(h, y0 + win), min(w, x0 + win)
        pad[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = src[sy0:sy1, sx0:sx1]
        pm[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = ~mag[sy0:sy1, sx0:sx1]
        box = np.zeros_like(pm)
        box[max(0, int(ry * ch) - y0):max(0, int((ry + 1) * ch) - y0), max(0, int(cx * cw) - x0):max(0, int((cx + 1) * cw) - x0)] = True
        pm &= box
        cov = pm.reshape(cell, k, cell, k).mean((1, 3))
        col = (pad * pm[..., None]).reshape(cell, k, cell, k, 3).sum((1, 3)) / np.maximum(pm.reshape(cell, k, cell, k).sum((1, 3)), 1)[..., None]
        keep = cov >= (0.08 if name in thin else 0.22)
        dist = ((col[..., None, :] - pal[None, None]) ** 2).sum(-1)
        o = np.zeros((cell, cell, 4), 'uint8'); o[..., :3] = pal[dist.argmin(-1)]; o[..., 3] = 255; o[~keep] = 0
        out[name] = o
    return out, bases


BUBBLE_PICKS = [('creux', 0, 0), ('bosse', 0, 1), ('ronde', 0, 2), ('dome', 0, 3), ('fissure', 0, 4), ('eclatement', 0, 5),
                ('retombee', 1, 0), ('cratere', 1, 1), ('anneau', 1, 2), ('anneau_pale', 1, 3), ('poussiere', 1, 4),
                ('poussiere_fin', 1, 5)]
BUBBLE_TIMELINE = (['creux'] * 2 + ['bosse'] * 2 + ['ronde'] * 2 + ['dome'] * 2 + ['fissure'] * 2 + ['eclatement'] +
                   ['retombee'] + ['cratere'] * 2 + ['anneau'] * 2 + ['anneau_pale'] + ['poussiere'] + ['poussiere_fin'])
DEVIL_PICKS = [(f'tourbillon_{i}', i // 4, i % 4) for i in range(8)]


# ---------------------------------------------------------------- sables mouvants façon Métano
def sand_phases(pits, visible):
    d = nd.distance_transform_edt(visible)
    yy, xx = np.mgrid[:H, :W]
    jag = cr.hash_noise(9); jag = (jag - jag.min()) / np.ptp(jag)
    frames = []
    for t in range(SAND_PHASES):
        ph = 2 * np.pi * t / SAND_PHASES
        n = 0.6 * np.sin(xx * 0.23 + yy * 0.11 - ph) + 0.4 * np.sin(xx * 0.07 - yy * 0.21 + 1.3 - ph)
        T = 3.6 + 0.9 * n
        jr = np.roll(jag, t * 2, axis=1); fringe = T + 0.6 + 2.4 * jr
        a = np.zeros((H, W, 4), 'uint8'); a[..., 3] = 255; a[..., :3] = PAL['surface']
        a[d <= fringe] = (*PAL['accent'], 255)
        a[(d <= fringe) & (jr > 0.62)] = (*PAL['clair'], 255)
        a[d <= T] = (*PAL['inter'], 255)
        a[d <= T - 1] = (*PAL['bande'], 255)
        a[(d <= 1.0) & (np.sin(xx * 0.5 + yy * 0.3 - ph) > -0.35)] = (*PAL['lip'], 255)
        a[~pits] = 0; a[pits & ~visible] = (*PAL['bande'], 255)
        frames.append(a)
    return frames, d


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
    o.update(Name={'DefaultText': 'Entree Ruine - sud vers nord', 'LocalTexts': {}}, AssetName=ASSET, Released=False,
             TexSize=1, Music='', EdgeView=1, ViewCenter=None, ViewOffset={'X': 0, 'Y': 0}, ActiveChar=None, Status={},
             Layers=layers, Background={'$type': 'RogueEssence.Dungeon.LayeredBG, RogueEssence', 'Layers': []},
             Comment='PMDO 0.8.12. Rendu genere (ref. Sealed Ruin) ; sables mouvants facon riviere Metano, bulles de sable '
                     'et tourbillons generes. Collisions de base a verifier. Seuil non raccorde.')
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
  <Name>Entree Ruine sud-nord - Atelier 0.8.12</Name>
  <Author>meromoonmeri</Author>
  <Description>Projet d'edition : entree de ruine generee (ref. Sealed Ruin), sables mouvants, bulles de sable et tourbillons animes. Pas une aventure jouable.</Description>
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
    global cr
    cr = loadmod('ecn1', R / 'source/entree_cratere_sud_nord_v1/build.py')
    gfx = loadmod('pmdo_codec', R / 'source/pmdo_cote/build.py')
    tools = loadmod('index_tools', R / 'source/pmdo_cote/INSTALLER.py')
    v1 = loadmod('esn1', R / 'source/entree_sud_nord_generee_v1/build.py')
    for d in ['calques', 'animation/sables', 'animation/bulles', 'animation/tourbillons', 'poses', 'masques', 'review']:
        (OUT / d).mkdir(parents=True, exist_ok=True)
    a = rgb(RAW / 'decor_magenta.png'); f = rgb(RAW / 'sol_complet.png')
    assert a.shape[:2] == f.shape[:2] == (FULL[1], FULL[0])
    fr_, fg_, fb_ = f.transpose(2, 0, 1)
    assert int(((fr_ > fg_ * 1.6) & (fb_ > fg_ * 1.4) & (fr_ > 120)).sum()) == 0, 'sol complet : magenta résiduel'
    m = classify(a)
    order = ['pits', 'sand', 'rims', 'boulders', 'cliffs', 'mouth', 'trees']
    ex = cr.exclusive(m, order)
    pits = ex['pits']
    names = {'sand': 'sable', 'rims': 'rebords_fosses', 'boulders': 'rochers', 'cliffs': 'falaises', 'mouth': 'bouche_ruine',
             'trees': 'arbres_morts'}
    layers = {'sol_complet': cr.rgba(cr.down_colors(f, np.ones(FULL[::-1], bool)), ~pits)}
    for k, n in names.items():
        layers[n] = cr.rgba(cr.down_colors(a, m[k]), ex[k])
    # Arbres morts gris : palette propre (dans la palette commune, dominée par les ocres, ils viraient au brun).
    trees_layer = layers.pop('arbres_morts')
    layers = cr.quantize_layers(layers)
    tm = trees_layer[..., 3] == 255
    tq = Image.fromarray(trees_layer[..., :3]).quantize(colors=24, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    trees_layer[..., :3] = np.array(tq.convert('RGB')); trees_layer[~tm] = 0
    layers['arbres_morts'] = trees_layer
    for k, v in ex.items():
        Image.fromarray((v * 255).astype('uint8')).save(OUT / 'masques' / f'{PFX}_masque_{k}.png')
    land = np.zeros((H, W), bool)
    for n in names.values():
        land |= layers[n][..., 3] == 255
    visible = pits & ~land
    sf, dist = sand_phases(pits, visible)
    pal = np.array(list(PAL.values()), int)
    poses, bases_b = extract_poses(RAW / 'bulles_sable_poses.png', 2, 6, BUBBLE_PICKS, 264, CELL,
                                   {'creux', 'anneau', 'anneau_pale', 'poussiere', 'poussiere_fin', 'eclatement', 'retombee'}, pal)
    derived = []
    if (poses['anneau_pale'][..., 3] > 0).sum() < 0.5 * (poses['anneau'][..., 3] > 0).sum():
        ap = poses['anneau'].copy(); ap[ap[..., 3] > 0, :3] = PAL['accent']; poses['anneau_pale'] = ap
        derived.append('anneau_pale = anneau recolore accent (brut trop pale)')
    devil_pal = np.array([PAL['pale'], PAL['clair'], PAL['surface'], PAL['accent'], PAL['inter'], (246, 230, 190)], int)
    devils, bases_d = extract_poses(RAW / 'tourbillon_8_poses.png', 2, 4, DEVIL_PICKS, 360, DEVIL_CELL, {p[0] for p in DEVIL_PICKS}, devil_pal)
    # Tourbillons trop pâles sur le sable : remappage par rang de luminance sur toute la rampe (brun -> pâle).
    ramp = np.array([PAL['bande'], PAL['inter'], PAL['accent'], PAL['surface'], PAL['clair'], PAL['pale']], int)
    allv = np.concatenate([p[p[..., 3] > 0][:, :3] @ [.299, .587, .114] for p in devils.values()])
    qs = np.percentile(allv, np.linspace(0, 100, len(ramp) + 1)[1:-1])
    for p in devils.values():
        mm = p[..., 3] > 0; lum = p[..., :3].astype(float) @ [.299, .587, .114]
        p[mm, :3] = ramp[np.digitize(lum[mm], qs)]
    for k, p in {**poses, **devils}.items():
        Image.fromarray(p).save(OUT / 'poses' / f'{PFX}_{k}.png')
    # Bulles sur les fosses (cœur 8x8 sur sable mouvant visible), détourées à la fosse visible.
    taken = np.zeros((H, W), bool)
    emitters = cr.place(visible & (dist > 3), (CELL, CELL), 8, 5, taken, core=8)
    offsets = [(i * 7) % BUBBLE_PHASES for i in range(len(emitters))]
    bf = [np.zeros((H, W, 4), 'uint8') for _ in range(BUBBLE_PHASES)]
    for (y, x), off in zip(emitters, offsets):
        for t in range(BUBBLE_PHASES):
            k = (t - off) % BUBBLE_PHASES
            if k < len(BUBBLE_TIMELINE):
                p = poses[BUBBLE_TIMELINE[k]]; mm = p[..., 3] > 0
                bf[t][y:y+CELL, x:x+CELL][mm] = p[mm]
    for arr in bf:
        arr[~visible] = 0
    # Tourbillons : 2 positions fixes sur le sable dégagé, loin des fosses et du chemin d'arrivée.
    sand_open = (layers['sable'][..., 3] == 255) & ~nd.binary_dilation(pits | land & ~(layers['sable'][..., 3] == 255), iterations=6)
    dtaken = np.zeros((H, W), bool)
    yy = np.mgrid[:H, :W][0]
    dpos = (cr.place(sand_open & (yy < H * 0.55), (DEVIL_CELL, DEVIL_CELL), 1, 13, dtaken) +
            cr.place(sand_open & (yy >= H * 0.55), (DEVIL_CELL, DEVIL_CELL), 1, 14, dtaken))
    df = [np.zeros((H, W, 4), 'uint8') for _ in range(DEVIL_PHASES)]
    for j, (y, x) in enumerate(dpos):
        for t in range(DEVIL_PHASES):
            p = devils[f'tourbillon_{(t + 3 * j) % DEVIL_PHASES}']; mm = p[..., 3] > 0
            df[t][y:y+DEVIL_CELL, x:x+DEVIL_CELL][mm] = p[mm]
    # Exports
    for t, fr in enumerate(sf):
        Image.fromarray(fr).save(OUT / 'animation/sables' / f'{PFX}_00_sables_mouvants_f{t}.png')
    for t, fr in enumerate(bf):
        Image.fromarray(fr).save(OUT / 'animation/bulles' / f'{PFX}_01_bulles_sable_f{t:02d}.png')
    num = {'sol_complet': 2, 'sable': 3, 'rebords_fosses': 4, 'rochers': 5, 'falaises': 6, 'bouche_ruine': 7}
    files = {}
    for k, i in num.items():
        fn = f'{PFX}_{i:02d}_{k}.png'; Image.fromarray(layers[k]).save(OUT / 'calques' / fn); files[k] = fn
    for t, fr in enumerate(df):
        Image.fromarray(fr).save(OUT / 'animation/tourbillons' / f'{PFX}_08_tourbillons_f{t}.png')
    files['arbres_morts'] = f'{PFX}_09_arbres_morts.png'
    Image.fromarray(layers['arbres_morts']).save(OUT / 'calques' / files['arbres_morts'])
    stack = ([('Sables mouvants facon Metano 4 phases', sf, SAND_TICKS), ('Bulles de sable 24 phases', bf, BUBBLE_TICKS)] +
             [(k, [layers[k]], 60) for k in num] + [('Tourbillons 8 phases', df, DEVIL_TICKS)] +
             [('arbres_morts', [layers['arbres_morts']], 60)])
    order_paths = ([f'animation/sables/{PFX}_00_sables_mouvants_fX.png', f'animation/bulles/{PFX}_01_bulles_sable_fXX.png'] +
                   [f'calques/{files[k]}' for k in num] + [f'animation/tourbillons/{PFX}_08_tourbillons_fX.png',
                                                          f'calques/{files["arbres_morts"]}'])
    # Collisions / accès : seul le sable est praticable (tourbillons décoratifs, non bloquants).
    walk = layers['sable'][..., 3] == 255
    blocked = cr.cell_grid(~walk)
    ex_ = int(np.median(np.nonzero(walk[H - 8])[0])); entry_px = [ex_ // 8 * 8 - 8, H - 16]
    # Seuil : première case 2x2 libre sous la bouche, dans l'axe de la grotte (la bande d'ombre devant la bouche est rocheuse).
    mb = np.nonzero(ex['mouth']); tx = int(mb[1].mean()) // 8 - 1
    ok = False
    for ty in range(int(mb[0].max()) // 8 + 1, H // 8 - 2):
        if not blocked[ty:ty + 2, tx:tx + 2].any():
            ok, explored = v1.reachable(blocked, (entry_px[1] // 8, entry_px[0] // 8), (ty, tx))
            if ok:
                break
    threshold_px = [tx * 8, ty * 8]
    assert ok, 'pas de chemin 16x16'
    ticks = [s[2] for s in stack]

    def scene(tick):
        im = Image.new('RGBA', (W, H))
        for (_, frames, tk) in stack:
            im.alpha_composite(Image.fromarray(frames[(tick // tk) % len(frames)]))
        return im
    scenes = [scene(t * 5) for t in range(LOOP_TICKS // 5)]
    scenes[0].save(OUT / 'review' / f'{PFX}_scene_t000.png')
    scenes[0].save(OUT / 'review' / f'{PFX}_scene_animee.webp', save_all=True, append_images=scenes[1:],
                   duration=round(5000 / 60), loop=0, lossless=True)
    col = scenes[0].copy(); ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(ov)
    for y, x in zip(*np.nonzero(blocked)):
        dr.rectangle([x*8, y*8, x*8+7, y*8+7], fill=(220, 40, 40, 90))
    for (px, py), c in ((entry_px, (255, 230, 40, 255)), (threshold_px, (60, 220, 255, 255))):
        dr.rectangle([px, py, px + 15, py + 15], outline=c, width=2)
    col.alpha_composite(ov); col.save(OUT / 'review' / f'{PFX}_collisions_marqueurs.png')
    allp = list(poses.values()) + list(devils.values())
    sheet = Image.new('RGBA', (len(allp) * (DEVIL_CELL * 4 + 4), DEVIL_CELL * 4), (*PAL['surface'], 255))
    for i, p in enumerate(allp):
        sheet.alpha_composite(Image.fromarray(p).resize((p.shape[1] * 4, p.shape[0] * 4), Image.Resampling.NEAREST), (i * (DEVIL_CELL * 4 + 4), 0))
    sheet.save(OUT / 'review' / f'{PFX}_planche_poses_x4.png')
    ora = {f'{i:02d}_{Path(p).stem.replace(PFX + "_", "").split("_f")[0] if "_f" in Path(p).stem else Path(p).stem.replace(PFX + "_", "")}':
           frames[0] for i, (p, (_, frames, _t)) in enumerate(zip(order_paths, stack))}
    cr.write_ora(OUT / f'{PFX}_entree_ruine_calques.ora', ora)
    counts = ground_project(stack, blocked, entry_px, threshold_px, gfx, tools)
    manifest = {
        'lot': 'entree_ruine_sud_nord_v1', 'size_px': [W, H], 'grid_8px': [W // 8, H // 8],
        'method': 'rendu genere : decor complet sur magenta (sables mouvants = magenta) + sol complet genere separement',
        'reference_da': 'Sealed_Ruin_entrance_TDS.png',
        'raw_inputs': [{'file': f'source/entree_ruine_sud_nord_v1/bruts/{n}', 'sha256': sha(RAW / n), 'size': list(Image.open(RAW / n).size)}
                       for n in ['decor_magenta.png', 'sol_complet.png', 'bulles_sable_poses.png', 'tourbillon_8_poses.png']],
        'normalization': 'x0.5 exact (848x1264 -> 424x632), moyenne 2x2 par classe, palette commune 96 couleurs (arbres morts : palette propre 24 couleurs)',
        'segmentation': 'fosses = magenta dilate 1 px ; sable = distance RVB a (229,206,153) < 45 sur 60 % d une fenetre 7 px ; '
                        'arbres = coeur gris ferme + contours peu satures ; falaises = non-sable relie au bord ; rebords = non-sable a < 24 px '
                        'd une fosse ; rochers = reste > 300 px ; bouche = pixels < 25 dans la cavite',
        'layer_order_bottom_to_top': order_paths, 'layer_ticks': ticks,
        'quicksand': {'phases': SAND_PHASES, 'frame_length_ticks': SAND_TICKS, 'couleurs': {k: list(v) for k, v in PAL.items()},
                      'modele': 'structure et cadence riviere Metano (comme ESN2/ECN1), recalculees sur nos fosses', 'origine': 'pixels recalcules'},
        'bubbles': {'brut': 'source/entree_ruine_sud_nord_v1/bruts/bulles_sable_poses.png', 'poses': [p[0] for p in BUBBLE_PICKS],
                    'bases_rangees_px': bases_b, 'reduction': 'fenetre 264 px -> 24 px (x1/11), base commune par rangee',
                    'derivees': derived, 'timeline_phases': BUBBLE_TIMELINE, 'phases': BUBBLE_PHASES, 'frame_length_ticks': BUBBLE_TICKS,
                    'emetteurs': [{'xy': [x, y], 'decalage': o} for (y, x), o in zip(emitters, offsets)],
                    'origine': 'dessin GENERE, chronologie creee ; pas une animation officielle'},
        'dust_devils': {'brut': 'source/entree_ruine_sud_nord_v1/bruts/tourbillon_8_poses.png', 'poses': [p[0] for p in DEVIL_PICKS],
                        'bases_rangees_px': bases_d, 'reduction': 'fenetre 360 px -> 40 px (x1/9), couleurs remappees par rang de luminance sur la rampe sable', 'phases': DEVIL_PHASES,
                        'frame_length_ticks': DEVIL_TICKS, 'positions': [[x, y] for (y, x) in dpos], 'decalages': [3 * j for j in range(len(dpos))],
                        'collision': 'aucune (decoratif)', 'origine': 'dessin GENERE, boucle de 8 poses demandee au generateur'},
        'scene_loop_ticks': LOOP_TICKS,
        'access': {'entry_px': entry_px, 'threshold_px': threshold_px, 'path_found_16x16': ok, 'cells_explored': explored,
                   'blocked_cells': int(blocked.sum()), 'total_cells': int(blocked.size),
                   'rule': 'case bloquee si > 25 % hors sable visible (fosses, rebords, rochers, falaises, bouche, arbres)'},
        'pmdo': {'target': '0.8.12', 'asset': ASSET, 'namespace': NAMESPACE, 'tiles_per_bank': counts, 'banks': list(counts),
                 'runtime_tested': False, 'warp': 'aucun'},
        'art_approved': False,
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    shutil.copyfile(OUT / 'manifest.json', STAGE / 'manifest.json')
    print(json.dumps({'emitters': len(emitters), 'devils': dpos, 'entry': entry_px, 'threshold': threshold_px,
                      'blocked': int(blocked.sum()), 'derived': derived, 'tiles': counts}, indent=1))


if __name__ == '__main__':
    build()
