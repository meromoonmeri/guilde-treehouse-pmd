"""Entrée Cascade — sud vers nord, V2 : RENDU GÉNÉRÉ RÉFÉRENCÉ Waterfall Cave (4:3 vaste, 768×576).

Méthode de la série (Vapeur → Jungle) : le générateur reçoit les rips canoniques
`Waterfall_Cave_ledge_TDS.png` + `Waterfall_Cave_gem_TDS.png` en référence et produit le décor complet
sur magenta (toute l'eau = magenta), en 1200×896. Segmentation en pleine résolution, réduction uniforme
×576/896 par classe, calques séparés (sol complet, fond, plafond, parois, pierres, cristaux), bassins
« façon rivière Métano » (4 × 10 ticks) avec la palette turquoise des bassins de Waterfall Cave,
cascade = frames NATIVES Métano (translation pure, 4 × 10 ticks), scintillements Métano natifs.
Le sol complet est édité par quilting depuis le sol du décor (le générateur n'a pas su l'effacer).
V1 (`source/entree_cascade_sud_nord_v1/`, pixels natifs exacts) est conservée telle quelle.

.venv/bin/python source/entree_cascade_sud_nord_v2/build.py
"""
from pathlib import Path
import hashlib, importlib.util, json, shutil, uuid, zipfile

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
RAW = HERE / 'bruts'
OUT = R / 'renders/entree_cascade_sud_nord_v2'
STAGE = R / '.cache/entree_cascade_sud_nord_v2/entree_cascade_sud_nord_v2'
NAMESPACE = 'entree_cascade_sud_nord_v2'
ASSET = 'ecn2_entree_cascade'
PFX = 'ECN2'
W, H = 768, 576
SRC = (1200, 896)
SCALE = H / SRC[1]
SCALED_W = round(SRC[0] * SCALE)     # 771
CROP_X = (SCALED_W - W) // 2         # 1
PHASES, TICKS = 4, 10
LOOP_TICKS = PHASES * TICKS
# Palette des bassins : couleurs EXACTES des sources turquoise de Waterfall_Cave_ledge_TDS.png (rôles Métano).
PAL = {'surface': (31, 151, 167), 'bande': (31, 119, 135), 'inter': (31, 143, 159), 'accent': (39, 175, 191),
       'clair': (215, 215, 215)}       # liseré clair natif des bassins du rip
CASCADE_ROWS = (66, 102, 120)        # corps tuilé lignes 66..101 (36 px : motif ^^^ régulier, sans bandes de crête), pied lignes 102..119 ; colonnes 8..55


def loadmod(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


JM = loadmod('ejn1_pipeline', R / 'source/entree_jungle_sud_nord_v1/build.py')   # même géométrie 1200×896 → 768×576
assert (JM.W, JM.H, JM.SCALED_W, JM.CROP_X) == (W, H, SCALED_W, CROP_X)
JM.PAL = PAL
BM = JM.BM
keep_large, quantize_layers, place, cell_grid, write_ora = BM.keep_large, BM.quantize_layers, BM.place, BM.cell_grid, BM.write_ora
down_class, down_full, rgba, water_phases, sha, rgb = JM.down_class, JM.down_full, JM.rgba, JM.water_phases, JM.sha, JM.rgb


# ---------------------------------------------------------------- segmentation pleine résolution (mesures dans le README)
def classify(a):
    r, g, b = a.transpose(2, 0, 1); lum = a @ [.299, .587, .114]; sat = a.max(2) - a.min(2)
    h, w = lum.shape; yy, xx = np.mgrid[:h, :w]
    mag = (r > g * 1.5) & (b > g * 1.3) & (r > 150) & (b > 130)
    water = nd.binary_dilation(mag, iterations=2)
    lab, n = nd.label(water)
    falls = np.isin(lab, list(set(np.unique(lab[water & (yy < 40)])) - {0}))      # la bande reliée au bord haut
    pool = water & ~falls
    crystal = nd.binary_dilation((sat > 110) & ~water, iterations=1)
    # Sol : bleu franc (b−r ≈ 67 lissé 5 px) et clair (lum ≈ 110) ; composante reliée au bord sud, trous remplis.
    BR = nd.uniform_filter((b - r).astype(float), 5); LU = nd.uniform_filter(lum, 5)
    floorish = nd.binary_closing((BR > 52) & (LU > 92) & ~water & ~crystal, iterations=2)
    lab2, _ = nd.label(floorish)
    floor = nd.binary_fill_holes(np.isin(lab2, list(set(np.unique(lab2[floorish & (yy > h - 6)])) - {0})))
    stones = floor & (lum < 70) & ~crystal
    stones = nd.binary_fill_holes(nd.binary_closing(nd.binary_opening(stones, iterations=1), iterations=1))
    lab3, n3 = nd.label(stones); sizes = nd.sum(stones, lab3, range(1, n3 + 1))
    stones = np.isin(lab3, [i + 1 for i in range(n3) if 30 <= sizes[i] <= 1500])
    crystal &= floor | ~floor
    void = nd.binary_opening(nd.binary_closing((lum < 52) & (sat < 32) & ~water & ~floor, iterations=2), iterations=2)
    rest = ~(water | floor | void | crystal)
    walls = nd.binary_fill_holes(nd.binary_closing(rest & (LU >= 78), iterations=6)) & rest
    ceiling = rest & ~walls
    floor_only = floor & ~stones & ~crystal
    return dict(water=water, falls=falls, pool=pool, floor=floor_only, stones=stones, crystal=crystal & ~water,
                void=void, walls=walls, ceiling=ceiling)


# ---------------------------------------------------------------- sol complet édité depuis le sol du décor (quilting)
def quilt_full(a, ok, block=96, overlap=24, seed=3):
    """Remplit toute l'image par blocs du décor entièrement inclus dans `ok` (sol sans pierres ni cristaux)."""
    rng = np.random.default_rng(seed); h, w = ok.shape
    okint = nd.uniform_filter(ok.astype(float), block, mode='constant') > 0.999
    ys, xs = np.nonzero(okint[block // 2:h - block // 2, block // 2:w - block // 2])
    cands = np.stack([xs, ys], 1)[::7]
    patches = np.stack([a[y:y + block, x:x + block] for x, y in cands]).astype(np.int32)
    out = np.zeros_like(a); filled = np.zeros((h, w), bool); step = block - overlap
    for y in range(0, h, step):
        for x in range(0, w, step):
            y1, x1 = min(y + block, h), min(x + block, w); bh, bw = y1 - y, x1 - x
            f = filled[y:y1, x:x1]; tgt = out[y:y1, x:x1].astype(np.int32)
            P = patches[:, :bh, :bw]
            if f.any():
                cost = ((P - tgt) ** 2).sum(3)[:, f].sum(1); best = np.argsort(cost)[:4]
            else:
                best = np.arange(len(cands))
            px, py = cands[rng.choice(best)]; patch = a[py:py + bh, px:px + bw]
            take = np.ones((bh, bw), bool); d = ((patch.astype(np.int32) - tgt) ** 2).sum(2)
            lc = f[:, :overlap]
            if lc.any():
                path = min_path(np.where(lc, d[:, :overlap], 0)); take[:, :overlap] &= (np.arange(min(overlap, bw))[None, :] >= path[:, None]) | ~lc
            tc = f[:overlap, :]
            if tc.any():
                path = min_path(np.where(tc, d[:overlap, :], 0).T); take[:overlap, :] &= (np.arange(min(overlap, bh))[:, None] >= path[None, :]) | ~tc
            out[y:y1, x:x1][take] = patch[take]; filled[y:y1, x:x1] = True
    return out


def min_path(cost):
    h, w = cost.shape; acc = cost.astype(float).copy(); back = np.zeros((h, w), int)
    for r_ in range(1, h):
        prev = acc[r_ - 1]; left = np.concatenate(([np.inf], prev[:-1])); right = np.concatenate((prev[1:], [np.inf]))
        st = np.stack([left, prev, right]); k = st.argmin(0); back[r_] = np.arange(w) + k - 1; acc[r_] += st[k, np.arange(w)]
    path = np.zeros(h, int); path[-1] = int(acc[-1].argmin())
    for r_ in range(h - 1, 0, -1):
        path[r_ - 1] = back[r_, path[r_]]
    return path


# ---------------------------------------------------------------- cascade native Métano dans la bande magenta
def cascade_frames(falls):
    """Pour chaque phase : pied natif (lignes 102..119) au bas de la bande, corps natif (lignes 38..101)
    tuilé vers le haut, colonnes 8..55 tuilées depuis le bord gauche de la bande. Translation pure."""
    ys, xs = np.nonzero(falls); y_bot = ys.max() + 1; x_left = xs.min()
    r0, r1, r2 = CASCADE_ROWS; body = r1 - r0
    yy, xx = np.mgrid[:H, :W]
    k = y_bot - yy                                        # 1 = dernière ligne de la bande
    src_row = np.where(k <= (r2 - r1), r2 - k, r1 - 1 - ((k - (r2 - r1) - 1) % body))
    src_col = 8 + ((xx - x_left) % 48)
    frames, maps = [], []
    for t in range(PHASES):
        nat = np.array(Image.open(R / f'sprites/eau_metano/cascade_frame_{t + 1}.png').convert('RGBA'))
        f = np.zeros((H, W, 4), 'uint8')
        f[falls] = nat[src_row[falls], src_col[falls]]
        f[..., 3] = np.where(falls, 255, 0)
        frames.append(f)
    return frames, {'x_left': int(x_left), 'y_bottom': int(y_bot), 'rows': list(CASCADE_ROWS), 'cols': [8, 56]}


# ---------------------------------------------------------------- Ground PMDO
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
    o.update(Name={'DefaultText': 'Entree Cascade V2 - sud vers nord (4:3)', 'LocalTexts': {}}, AssetName=ASSET, Released=False,
             TexSize=1, Music='', EdgeView=1, ViewCenter=None, ViewOffset={'X': 0, 'Y': 0}, ActiveChar=None, Status={},
             Layers=layers, Background={'$type': 'RogueEssence.Dungeon.LayeredBG, RogueEssence', 'Layers': []},
             Comment='PMDO 0.8.12. Rendu genere 4:3 reference Waterfall Cave (rips passes au generateur) ; bassins facon Metano '
                     '(palette Waterfall Cave), cascade = frames Metano natives, scintillements natifs. Collisions de base a verifier. Seuil non raccorde.')
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
  <Name>Entree Cascade V2 sud-nord 4:3 - Atelier 0.8.12</Name>
  <Author>meromoonmeri</Author>
  <Description>Projet d'edition : entree de grotte a cascade au format 4:3, rendu genere d'apres les rips Waterfall Cave, bassins facon Metano, cascade et scintillements Metano natifs. Pas une aventure jouable.</Description>
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
    for d in ['calques', 'animation/eau', 'animation/cascade', 'animation/scintillements', 'masques', 'review']:
        (OUT / d).mkdir(parents=True, exist_ok=True)
    a = rgb(RAW / 'decor_magenta.png')
    assert a.shape[:2] == (SRC[1], SRC[0])
    m = classify(a)
    if not (RAW / 'sol_complet.png').exists():
        Image.fromarray(quilt_full(a.astype('uint8'), m['floor']).astype('uint8')).save(RAW / 'sol_complet.png')
    f = rgb(RAW / 'sol_complet.png'); assert f.shape == a.shape
    order = ['pool', 'falls', 'floor', 'stones', 'crystal', 'void', 'ceiling', 'walls']
    ex, cols = down_class(a, m, order)
    pool, falls = ex['pool'], ex['falls']
    names = {'void': 'fond_vide', 'ceiling': 'plafond_stalactites', 'walls': 'parois_rochers', 'stones': 'pierres', 'crystal': 'cristaux'}
    layers = {'sol_complet': rgba(down_full(f), ~(pool | falls))}
    for k, nm in names.items():
        layers[nm] = rgba(cols[k], ex[k])
    crystals = layers.pop('cristaux')
    layers = quantize_layers(layers); layers['cristaux'] = crystals          # palette propre : les cristaux sont trop rares pour la palette commune
    for k, v in ex.items():
        Image.fromarray((v * 255).astype('uint8')).save(OUT / 'masques' / f'{PFX}_masque_{k}.png')
    # Eau des bassins façon Métano, palette Waterfall Cave ; visible = bassin non couvert par un calque opaque.
    cover = np.zeros((H, W), bool)
    for nm in names.values():
        cover |= layers[nm][..., 3] == 255
    visible = pool & ~cover
    wf, dist = water_phases(pool, visible)
    cf, cmap = cascade_frames(falls)
    fams = BM.sparkle_families(); taken = np.zeros((H, W), bool)
    sf = [np.zeros((H, W, 4), 'uint8') for _ in range(PHASES)]; sparkles = []
    for fi, (name, frames) in enumerate(fams.items()):
        hh, ww = frames[0].shape[:2]
        for (y, x) in place(visible & (dist > 4), (hh, ww), 4, 31 + fi, taken, core=8):
            sparkles.append({'famille': name, 'xy': [x, y]})
            for t in range(PHASES):
                mm = frames[t][..., 3] > 0; sf[t][y:y+hh, x:x+ww][mm] = frames[t][mm]
    for arr in sf:
        arr[~visible] = 0
    # Exports
    for t in range(PHASES):
        Image.fromarray(wf[t]).save(OUT / 'animation/eau' / f'{PFX}_00_eau_bassins_f{t}.png')
        Image.fromarray(cf[t]).save(OUT / 'animation/cascade' / f'{PFX}_01_cascade_f{t}.png')
        Image.fromarray(sf[t]).save(OUT / 'animation/scintillements' / f'{PFX}_02_scintillements_f{t}.png')
    static_order = ['sol_complet', 'fond_vide', 'plafond_stalactites', 'parois_rochers', 'pierres', 'cristaux']
    files = {}
    for i, nm in enumerate(static_order, start=3):
        fn = f'{PFX}_{i:02d}_{nm}.png'; Image.fromarray(layers[nm]).save(OUT / 'calques' / fn); files[nm] = fn
    stack_named = [('eau_bassins', wf, TICKS), ('cascade', cf, TICKS), ('scintillements', sf, TICKS)] + \
                  [(nm, [layers[nm]], 60) for nm in static_order]
    # Collisions : sol visible praticable (ni eau, ni cascade, ni calque opaque au-dessus).
    walk = (layers['sol_complet'][..., 3] == 255) & ~cover & ~pool & ~falls
    blocked = cell_grid(~walk)
    gh_, gw_ = blocked.shape
    px = np.nonzero(walk[H - 8, :])[0]; med = int(np.median(px)) // 8
    cx = min((c for c in range(gw_ - 1) if not blocked[gh_ - 2:, c:c + 2].any()), key=lambda c: abs(c - med))
    entry_px = [cx * 8, H - 16]
    fx = np.nonzero(falls.any(0))[0]; threshold_px = [int((fx[0] + fx[-1]) / 2) // 8 * 8 - 8, (cmap['y_bottom'] + 7) // 8 * 8]
    while blocked[threshold_px[1] // 8:threshold_px[1] // 8 + 2, threshold_px[0] // 8:threshold_px[0] // 8 + 2].any():
        threshold_px[1] += 8
    ok, explored = v1.reachable(blocked, (entry_px[1] // 8, entry_px[0] // 8), (threshold_px[1] // 8, threshold_px[0] // 8))
    assert ok, 'pas de chemin 16x16'

    def scene(tick):
        p = (tick // TICKS) % PHASES
        im = Image.new('RGBA', (W, H))
        for title, frames, _ in stack_named:
            im.alpha_composite(Image.fromarray(frames[p if len(frames) > 1 else 0]))
        return im
    scenes = [scene(t * TICKS) for t in range(PHASES)]
    scenes[0].save(OUT / 'review' / f'{PFX}_scene_t000.png')
    scenes[0].save(OUT / 'review' / f'{PFX}_scene_animee.webp', save_all=True, append_images=scenes[1:],
                   duration=round(TICKS * 1000 / 60), loop=0, lossless=True)
    col = scenes[0].copy(); ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(ov)
    for y, x in zip(*np.nonzero(blocked)):
        dr.rectangle([x*8, y*8, x*8+7, y*8+7], fill=(220, 40, 40, 90))
    for (qx, qy), c in ((entry_px, (255, 230, 40, 255)), (threshold_px, (60, 220, 255, 255))):
        dr.rectangle([qx, qy, qx + 15, qy + 15], outline=c, width=2)
    col.alpha_composite(ov); col.save(OUT / 'review' / f'{PFX}_collisions_marqueurs.png')
    write_ora(OUT / f'{PFX}_entree_cascade_calques.ora',
              {f'{i:02d}_{t}' + ('_f0' if len(fr) > 1 else ''): fr[0] for i, (t, fr, _) in enumerate(stack_named)})
    counts = ground_project([(t.replace('_', ' ') + (f' {len(fr)} phases' if len(fr) > 1 else ''), fr, tk)
                             for t, fr, tk in stack_named], blocked, entry_px, threshold_px, gfx, tools)
    order_files = [f'animation/eau/{PFX}_00_eau_bassins_fX.png', f'animation/cascade/{PFX}_01_cascade_fX.png',
                   f'animation/scintillements/{PFX}_02_scintillements_fX.png'] + [f'calques/{files[nm]}' for nm in static_order]
    manifest = {
        'lot': 'entree_cascade_sud_nord_v2', 'format': '4:3 vaste', 'size_px': [W, H], 'grid_8px': [W // 8, H // 8],
        'method': 'rendu genere reference PMD : les deux rips Waterfall Cave passes au generateur, decor complet sur magenta (eau = magenta), '
                  'sol complet edite par quilting depuis le sol du decor',
        'reference_da': ['Waterfall_Cave_ledge_TDS.png', 'Waterfall_Cave_gem_TDS.png'],
        'raw_inputs': [{'file': f'source/entree_cascade_sud_nord_v2/bruts/{n}', 'sha256': sha(RAW / n),
                        'size': list(Image.open(RAW / n).size)} for n in ['decor_magenta.png', 'sol_complet.png']],
        'normalization': {'scale': SCALE, 'scaled': [SCALED_W, H], 'crop_x': [CROP_X, SCALED_W - W - CROP_X],
                          'methode': 'moyenne ponderee par classe (BOX), attribution exclusive par poids maximal, palette commune 96 couleurs sauf cristaux (couleurs propres)'},
        'segmentation': 'eau = magenta dilate 2 px, cascade = composante reliee au bord haut ; sol = (b-r lisse 5 px > 52) & (lum lisse > 92), '
                        'composante reliee au bord sud, trous remplis ; pierres = lum < 70 dans le sol (30..1500 px) ; cristaux = saturation > 110 ; '
                        'vide = lum < 52 & sat < 32 ; parois = reste avec lum lisse >= 78 (fermeture 6 px) ; plafond = reste',
        'layer_order_bottom_to_top': order_files,
        'water': {'phases': PHASES, 'frame_length_ticks': TICKS, 'couleurs': {k: list(v) for k, v in PAL.items()},
                  'modele': 'structure et cadence riviere Metano, palette = couleurs exactes des sources turquoise de Waterfall Cave',
                  'origine': 'pixels recalcules, pas de tuiles natives'},
        'cascade': {'phases': PHASES, 'frame_length_ticks': TICKS, 'mapping': cmap,
                    'origine': 'cascade_frame_1..4 Metano NATIVES : pied lignes 102..119, corps lignes 66..101 tuile, colonnes 8..55 tuilees ; translation pure',
                    'cadence': 'proposee (10 ticks), non prouvee par la map Metano'},
        'sparkles': {'source': 'source/eau_metano/natifs/Metano_Town_River_Sparkles.tile', 'placements': sparkles,
                     'origine': 'pixels et couleurs Metano NATIFS inchanges'},
        'scene_loop_ticks': LOOP_TICKS,
        'access': {'entry_px': entry_px, 'threshold_px': threshold_px, 'path_found_16x16': ok, 'cells_explored': explored,
                   'blocked_cells': int(blocked.sum()), 'total_cells': int(blocked.size),
                   'rule': 'case bloquee si > 25 % hors sol visible'},
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
