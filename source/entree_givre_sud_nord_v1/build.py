"""Entrée Givre sud -> nord V1 — rendu généré, référence Frosty Forest (reference/).

Même méthode que les entrées Vapeur/Cratère : décor complet généré sur magenta (eau = magenta), sol complet
généré séparément, normalisation uniforme exacte x0,5 (848x1264 -> 424x632), moyenne 2x2 par classe.
Le ruisseau généré coupait le sentier : un GUÉ GELÉ est dessiné par le script sur l'eau au croisement
(plaque de glace, pas un pixel généré) pour rendre l'accès possible. Animations, chacune sur son calque :
- eau glacée « façon rivière Métano » (4 phases x 10 ticks), palette froide choisie selon les rôles Métano ;
- scintillements : pixels réels Metano_Town_River_Sparkles recolorés en blanc bleuté, 4 x 10 ticks ;
- flocons : planche générée (6 flocons + 6 boules de neige qui tournent), 40 émetteurs décalés ;
  chaque flocon tombe ~64 px en ondulant puis se pose (pose réduite dérivée), 48 phases x 5 ticks = 4 s.
Scène complète : PPCM 240 ticks = 4 s.
Lancer : .venv/bin/python source/entree_givre_sud_nord_v1/build.py
"""
from pathlib import Path
import hashlib, importlib.util, json, shutil, uuid, zipfile

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
RAW = HERE / 'bruts'
REF = HERE / 'reference/Frosty_Forest_Entrance_RT_mysterydungeonwiki.png'
OUT = R / 'renders/entree_givre_sud_nord_v1'
STAGE = R / '.cache/entree_givre_sud_nord_v1/entree_givre_sud_nord'
NAMESPACE = 'entree_givre_sud_nord'
ASSET = 'egn1_entree_givre'
PFX = 'EGN1'
W, H = 424, 632
FULL = (848, 1264)
WATER_PHASES, WATER_TICKS = 4, 10
FLAKE_PHASES, FLAKE_TICKS = 48, 5
LOOP_TICKS = 240
FCELL = 8
N_FLAKES = 40
FALL_PX = 64
GUE_CENTER_FULL = (436, 976)      # croisement ruisseau / sentier repéré sur le décor pleine résolution
PATH_MARGIN = 6                   # congères basses praticables le long du sentier (collision seulement)
TREE_E = 0.24                     # seuil de densité de contours des sapins

PAL = {'lip': (170, 212, 244), 'bande': (58, 92, 168), 'inter': (84, 136, 204), 'accent': (100, 158, 218),
       'surface': (112, 172, 226), 'clair': (170, 212, 244), 'reflet': (240, 248, 255)}
ICE = {'base': (206, 232, 246), 'ombre': (184, 214, 238), 'fissure': (150, 186, 222), 'bord': (120, 160, 210),
       'reflet': (244, 250, 255)}
FLAKE_PAL = np.array([(250, 252, 255), (220, 230, 250), (178, 188, 228), (118, 128, 184)], int)


def loadmod(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


cr = loadmod('ecn1_utils', R / 'source/entree_cratere_sud_nord_v1/build.py')   # utilitaires communs (même W, H)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rgb(p):
    return np.array(Image.open(p).convert('RGB')).astype(int)


# ---------------------------------------------------------------- segmentation pleine résolution
def classify(a):
    r, g, b = a.transpose(2, 0, 1); lum = a @ [.299, .587, .114]; br = b - r
    yy, xx = np.mgrid[:a.shape[0], :a.shape[1]]
    water = nd.binary_dilation((r > g * 1.6) & (b > g * 1.4) & (r > 120) & (b > 100), iterations=1)
    floes = nd.binary_fill_holes(nd.binary_closing(water, iterations=6)) & ~water
    # Falaise de glace : b-r > 40 dans la bande nord, puis tout ce qui est au-dessus de sa limite basse par colonne.
    ice = cr.keep_large(nd.binary_opening((br > 40) & (yy < 380) & ~water, iterations=2), 2000)
    cliff = np.zeros_like(ice)
    for x in range(a.shape[1]):
        ys = np.nonzero(ice[:, x])[0]
        if len(ys):
            cliff[:ys.max() + 1, x] = True
    cliff = nd.binary_closing(cliff, iterations=4) & (yy < 380)
    cave_box = (yy > 120) & (yy < 340) & (xx > 290) & (xx < 560)
    mouth = cave_box & (((lum < 130) & (br > 40)) | ((br > 60) & (yy > 250)))
    mouth = cr.keep_large(nd.binary_fill_holes(nd.binary_closing(mouth, iterations=3)), 3000) & cave_box
    cliff &= ~mouth
    stump_box = (yy > 860) & (yy < 980) & (xx > 130) & (xx < 280)
    stump = cr.keep_large(nd.binary_fill_holes(nd.binary_closing(stump_box & (lum < 165) & (br < 40), iterations=3)), 800)
    # Sentier gris lilas : luminance 120-200, b-r 18-48, lissé sur 9 px.
    pathpix = (lum > 120) & (lum < 200) & (br > 18) & (br < 48) & ~water
    path = nd.uniform_filter(pathpix.astype(float), 9) > 0.45
    path = cr.keep_large(nd.binary_opening(nd.binary_closing(path, iterations=3), iterations=2), 3000) & ~cliff & ~mouth & ~stump
    # Sapins et congères : densité de contours (lum < 205) > 0,16 sur 25 px ; neige plane = 0.
    E = nd.uniform_filter((lum < 205).astype(float), 25)
    other = path | water | floes | cliff | mouth | stump
    trees = nd.binary_opening(nd.binary_closing((E > TREE_E) & ~other, iterations=4), iterations=3)
    trees = cr.keep_large(nd.binary_fill_holes(trees), 4000) & ~other
    snow = ~(other | trees)
    return dict(water=water, floes=floes, snow=snow, path=path, stump=stump, trees=trees, cliff=cliff, mouth=mouth)


# ---------------------------------------------------------------- gué gelé (dessiné)
def ford_zone(scale=1.35):
    """Zone d'approche du gué (ellipse élargie) : les petites boules de neige y deviennent praticables."""
    cx, cy = GUE_CENTER_FULL[0] / 2, GUE_CENTER_FULL[1] / 2
    yy, xx = np.mgrid[:H, :W]
    return ((xx - cx) / (40 * scale)) ** 2 + ((yy - cy) / (30 * scale)) ** 2 <= 1


def ice_ford(water):
    """Plaque de glace irrégulière sur l'eau autour du croisement ; retourne (masque, calque RGBA)."""
    cx, cy = GUE_CENTER_FULL[0] / 2, GUE_CENTER_FULL[1] / 2
    yy, xx = np.mgrid[:H, :W]
    ang = np.arctan2(yy - cy, xx - cx)
    rad = 1 + 0.12 * np.sin(3 * ang + 0.7) + 0.08 * np.sin(5 * ang + 2.1)
    blob = ((xx - cx) / 40) ** 2 + ((yy - cy) / 30) ** 2 <= rad ** 2
    m = water & blob
    m = nd.binary_opening(m, iterations=1)
    out = np.zeros((H, W, 4), 'uint8')
    out[m] = (*ICE['base'], 255)
    d = nd.distance_transform_edt(m)
    shade = m & ((xx - cx) + (yy - cy) > 18)
    out[shade] = (*ICE['ombre'], 255)
    rng = np.random.default_rng(4)
    im = Image.fromarray(out); dr = ImageDraw.Draw(im)
    for _ in range(6):                             # fissures
        x0, y0 = cx + rng.uniform(-28, 28), cy + rng.uniform(-18, 18)
        pts = [(x0, y0)]
        for _ in range(3):
            x0 += rng.uniform(-7, 7); y0 += rng.uniform(-5, 5); pts.append((x0, y0))
        dr.line(pts, fill=(*ICE['fissure'], 255), width=1)
    for _ in range(5):                             # reflets en biais
        x0, y0 = cx + rng.uniform(-26, 18), cy + rng.uniform(-16, 12)
        dr.line([(x0, y0), (x0 + 5, y0 - 3)], fill=(*ICE['reflet'], 255), width=1)
    out = np.array(im); out[~m] = 0
    edge_water = m & nd.binary_dilation(water & ~m, iterations=1)
    out[edge_water] = (*ICE['bord'], 255)                                  # bord contre l'eau vive
    inner = m & ~edge_water & nd.binary_dilation(edge_water, iterations=1)
    out[inner] = (*ICE['reflet'], 255)                                     # lèvre claire
    return m, out


# ---------------------------------------------------------------- eau glacée façon Métano
def water_phases(water, visible):
    d = nd.distance_transform_edt(visible)
    yy, xx = np.mgrid[:H, :W]
    jag = cr.hash_noise(9); jag = (jag - jag.min()) / np.ptp(jag)
    frames = []
    for t in range(WATER_PHASES):
        ph = 2 * np.pi * t / WATER_PHASES
        n = 0.6 * np.sin(xx * 0.23 + yy * 0.11 - ph) + 0.4 * np.sin(xx * 0.07 - yy * 0.21 + 1.3 - ph)
        T = 3.8 + 0.9 * n
        jr = np.roll(jag, t * 2, axis=1); fringe = T + 0.6 + 2.4 * jr
        a = np.zeros((H, W, 4), 'uint8'); a[..., 3] = 255; a[..., :3] = PAL['surface']
        a[d <= fringe] = (*PAL['inter'], 255)
        a[(d <= fringe) & (jr > 0.62)] = (*PAL['accent'], 255)
        a[d <= T] = (*PAL['inter'], 255)
        a[d <= T - 1] = (*PAL['bande'], 255)
        a[(d <= 1.0) & (np.sin(xx * 0.5 + yy * 0.3 - ph) > -0.35)] = (*PAL['lip'], 255)   # lèvre de glace
        a[~water] = 0; a[water & ~visible] = (*PAL['bande'], 255)
        frames.append(a)
    return frames, d


def sparkle_families():
    v2 = loadmod('esn2_tiles', R / 'source/entree_vapeur_sud_nord_v2/build.py')
    t = v2.decode_tile(cr.METANO_SPARK)

    def cluster(cols, rows, step):
        out = []
        for k in range(4):
            a = np.zeros((len(rows) * 8, len(cols) * 8, 4), 'uint8')
            for j, rr in enumerate(rows):
                for i, c in enumerate(cols):
                    a[j*8:j*8+8, i*8:i*8+8] = t[c, rr + step * k]
            out.append(a)
        return out
    res = {}
    for name, frames in {'A_16x24': cluster([0, 1], [0, 1, 2], 3), 'B_24x16': cluster([2, 3, 4], [0, 1], 2)}.items():
        conv = []
        for a in frames:
            o = np.zeros_like(a)
            m = (a[..., 3] == 255) & (np.abs(a[..., :3].astype(int) - cr.M_SURFACE).sum(2) > 0)
            lum = a[..., :3].astype(float) @ [.299, .587, .114]
            o[m & (lum >= 235), :3] = PAL['reflet']; o[m & (lum < 235), :3] = PAL['clair']; o[m, 3] = 255
            conv.append(o)
        res[name] = conv
    return res


# ---------------------------------------------------------------- flocons générés
def flake_poses():
    """12 cases (2 x 6), fenêtre 208 px centrée sur le contenu de chaque case -> 8 x 8 (x 1/26)."""
    src = rgb(RAW / 'flocons_poses.png'); h, w = src.shape[:2]
    r, g, b = src.transpose(2, 0, 1)
    mag = (r > 150) & (b > 110) & (g < 130) & (r > g * 1.5) & (b > g * 1.25)
    cw, ch = w / 6, h / 2; win = 208; k = win // FCELL
    poses = {}
    for ry in range(2):
        for cx in range(6):
            y0c, y1c, x0c, x1c = int(ry * ch), int((ry + 1) * ch), int(cx * cw), int((cx + 1) * cw)
            m = cr.keep_large(~mag[y0c:y1c, x0c:x1c], 40)
            ys, xs = np.nonzero(m)
            cyy, cxx = y0c + (ys.min() + ys.max()) // 2, x0c + (xs.min() + xs.max()) // 2
            y0, x0 = cyy - win // 2, cxx - win // 2
            crop = src[y0:y0 + win, x0:x0 + win]; pm = ~mag[y0:y0 + win, x0:x0 + win]
            cov = pm.reshape(FCELL, k, FCELL, k).mean((1, 3))
            col = (crop * pm[..., None]).reshape(FCELL, k, FCELL, k, 3).sum((1, 3)) / np.maximum(pm.reshape(FCELL, k, FCELL, k).sum((1, 3)), 1)[..., None]
            keep = cov >= 0.3
            dist = ((col[..., None, :] - FLAKE_PAL[None, None]) ** 2).sum(-1)
            o = np.zeros((FCELL, FCELL, 4), 'uint8'); o[..., :3] = FLAKE_PAL[dist.argmin(-1)]; o[..., 3] = 255; o[~keep] = 0
            poses[f"{'flocon' if ry == 0 else 'boule'}_{cx}"] = o
    # Pose « posé » dérivée : 2 x 2 px blanc + contour, pour la fin de chute.
    pose = np.zeros((FCELL, FCELL, 4), 'uint8')
    pose[3:5, 3:5] = (*FLAKE_PAL[0], 255); pose[5, 3:5] = (*FLAKE_PAL[3], 255)
    poses['pose'] = pose
    return poses


def flake_frames(poses, rng):
    frames = [np.zeros((H, W, 4), 'uint8') for _ in range(FLAKE_PHASES)]
    emitters = []
    fall_frames = 40
    for i in range(N_FLAKES):
        kind = 'flocon' if i % 2 == 0 else 'boule'
        x0 = int(rng.integers(4, W - 12)); y0 = int(rng.integers(0, H - FALL_PX - 10))
        off = (i * 11) % FLAKE_PHASES; phi = float(rng.uniform(0, 2 * np.pi)); amp = float(rng.uniform(2, 4))
        emitters.append({'type': kind, 'depart_xy': [x0, y0], 'decalage': off, 'amplitude_px': round(amp, 2)})
        for t in range(FLAKE_PHASES):
            k = (t - off) % FLAKE_PHASES
            if k < fall_frames:
                y = int(round(y0 + k * FALL_PX / fall_frames)); x = int(round(x0 + amp * np.sin(2 * np.pi * k / 24 + phi)))
                p = poses[f'{kind}_{(k // 2) % 6}']
            elif k < fall_frames + 2:
                y = y0 + FALL_PX; x = int(round(x0 + amp * np.sin(2 * np.pi * fall_frames / 24 + phi))); p = poses['pose']
            else:
                continue
            m = p[..., 3] > 0
            frames[t][y:y + FCELL, x:x + FCELL][m] = p[m]
    return frames, emitters


# ---------------------------------------------------------------- Ground générique
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
    o.update(Name={'DefaultText': 'Entree Givre - sud vers nord', 'LocalTexts': {}}, AssetName=ASSET, Released=False,
             TexSize=1, Music='', EdgeView=1, ViewCenter=None, ViewOffset={'X': 0, 'Y': 0}, ActiveChar=None, Status={},
             Layers=layers, Background={'$type': 'RogueEssence.Dungeon.LayeredBG, RogueEssence', 'Layers': []},
             Comment='PMDO 0.8.12. Rendu genere (ref. Frosty Forest) ; eau glacee facon riviere Metano, scintillements Metano '
                     'recolores, flocons generes ; gue gele dessine par script. Collisions de base a verifier. Seuil non raccorde.')
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
  <Name>Entree Givre sud-nord - Atelier 0.8.12</Name>
  <Author>meromoonmeri</Author>
  <Description>Projet d'edition : entree enneigee generee (ref. Frosty Forest), eau glacee, scintillements et flocons animes. Pas une aventure jouable.</Description>
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
    for d in ['calques', 'animation/eau', 'animation/scintillements', 'animation/flocons', 'poses_flocons', 'masques', 'review']:
        (OUT / d).mkdir(parents=True, exist_ok=True)
    a = rgb(RAW / 'decor_magenta.png'); f = rgb(RAW / 'sol_complet.png')
    assert a.shape[:2] == f.shape[:2] == (FULL[1], FULL[0])
    m = classify(a)
    order = ['water', 'floes', 'snow', 'path', 'stump', 'trees', 'cliff', 'mouth']
    ex = cr.exclusive(m, order)
    water = ex['water']
    gue_mask, gue = ice_ford(water)
    layers = {
        'sol_complet': cr.rgba(cr.down_colors(f, np.ones(FULL[::-1], bool)), ~water),
        'neige': cr.rgba(cr.down_colors(a, m['snow']), ex['snow']),
        'sentier': cr.rgba(cr.down_colors(a, m['path']), ex['path']),
        'glacons': cr.rgba(cr.down_colors(a, m['floes']), ex['floes']),
        'souche': cr.rgba(cr.down_colors(a, m['stump']), ex['stump']),
        'sapins_congeres': cr.rgba(cr.down_colors(a, m['trees']), ex['trees']),
        'falaises_glace': cr.rgba(cr.down_colors(a, m['cliff']), ex['cliff']),
        'bouche_glace': cr.rgba(cr.down_colors(a, m['mouth']), ex['mouth']),
    }
    layers = cr.quantize_layers(layers)
    layers['glacons'][gue_mask] = 0
    static_order = ['sol_complet', 'neige', 'sentier', 'gue_gele', 'glacons', 'souche', 'sapins_congeres', 'falaises_glace', 'bouche_glace']
    layers['gue_gele'] = gue
    for k, v in ex.items():
        Image.fromarray((v * 255).astype('uint8')).save(OUT / 'masques' / f'{PFX}_masque_{k}.png')
    Image.fromarray((gue_mask * 255).astype('uint8')).save(OUT / 'masques' / f'{PFX}_masque_gue_gele.png')
    land = np.zeros((H, W), bool)
    for k in static_order[1:]:
        land |= layers[k][..., 3] == 255
    visible = water & ~land
    wf, dist = water_phases(water, visible)
    taken = np.zeros((H, W), bool)
    fams = sparkle_families(); sf = [np.zeros((H, W, 4), 'uint8') for _ in range(WATER_PHASES)]; sparkles = []
    for fi, (name, frames) in enumerate(fams.items()):
        hh, ww = frames[0].shape[:2]
        for (y, x) in cr.place(visible & (dist > 2), (hh, ww), 3, 31 + fi, taken, core=8):
            sparkles.append({'famille': name, 'xy': [x, y]})
            for t in range(WATER_PHASES):
                mm = frames[t][..., 3] > 0; sf[t][y:y+hh, x:x+ww][mm] = frames[t][mm]
    for arr in sf:
        arr[~visible] = 0
    poses = flake_poses()
    for k, p in poses.items():
        Image.fromarray(p).save(OUT / 'poses_flocons' / f'{PFX}_flocon_{k}.png')
    ff, emitters = flake_frames(poses, np.random.default_rng(12))
    # Exports
    for t, fr in enumerate(wf):
        Image.fromarray(fr).save(OUT / 'animation/eau' / f'{PFX}_00_eau_glacee_f{t}.png')
    for t, fr in enumerate(sf):
        Image.fromarray(fr).save(OUT / 'animation/scintillements' / f'{PFX}_01_scintillements_f{t}.png')
    files = {}
    for j, k in enumerate(static_order, start=2):
        fn = f'{PFX}_{j:02d}_{k}.png'; Image.fromarray(layers[k]).save(OUT / 'calques' / fn); files[k] = fn
    nflake = 2 + len(static_order)
    for t, fr in enumerate(ff):
        Image.fromarray(fr).save(OUT / 'animation/flocons' / f'{PFX}_{nflake:02d}_flocons_f{t:02d}.png')
    # Collisions et accès : neige visible, sentier, gué gelé.
    walk = (layers['neige'][..., 3] == 255) | (layers['sentier'][..., 3] == 255) | gue_mask
    approach = ford_zone() & (layers['sapins_congeres'][..., 3] == 255)   # boules de neige au bord du gué
    path_or_ford = (layers['sentier'][..., 3] == 255) | gue_mask
    approach |= nd.binary_dilation(path_or_ford, iterations=PATH_MARGIN) & (layers['sapins_congeres'][..., 3] == 255)
    walk |= approach
    for k in ['glacons', 'souche', 'falaises_glace', 'bouche_glace']:
        walk &= layers[k][..., 3] == 0
    walk &= (layers['sapins_congeres'][..., 3] == 0) | approach
    blocked = cr.cell_grid(~walk)
    gh, gw = blocked.shape
    ok2 = np.zeros_like(blocked)
    for y in range(gh - 1):
        for x in range(gw - 1):
            ok2[y, x] = not blocked[y:y + 2, x:x + 2].any()
    cand = [x for x in range(gw - 1) if ok2[gh - 2, x]]
    sx = min(cand, key=lambda x: abs(x - gw // 2 + 1))
    entry_px = [sx * 8, (gh - 2) * 8]
    mb = np.nonzero(ex['mouth']); mx_ = int(mb[1].mean()) // 8; my_ = int(mb[0].max()) // 8
    threshold_px = None
    for gy in range(my_ + 1, my_ + 12):             # première case 2x2 libre et atteignable sous la bouche
        for dx in sorted(range(-5, 6), key=abs):
            gx = mx_ + dx
            if 0 <= gx < gw - 1 and ok2[gy, gx]:
                okr, explored = v1.reachable(blocked, (gh - 2, sx), (gy, gx))
                if okr:
                    threshold_px = [gx * 8, gy * 8]; break
        if threshold_px:
            break
    if not threshold_px:                            # diagnostic : zone atteinte depuis l'arrivée
        from collections import deque
        S = np.zeros_like(ok2); q = deque([(gh - 2, sx)]); S[gh - 2, sx] = True
        while q:
            y, x = q.popleft()
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < gh - 1 and 0 <= nx < gw - 1 and ok2[ny, nx] and not S[ny, nx]:
                    S[ny, nx] = True; q.append((ny, nx))
        im = Image.fromarray(a.astype('uint8')).resize((W, H)).convert('RGBA'); im.alpha_composite(Image.fromarray(gue))
        ov = Image.new('RGBA', (W, H)); dr = ImageDraw.Draw(ov)
        for y, x in zip(*np.nonzero(blocked)):
            dr.rectangle([x*8, y*8, x*8+7, y*8+7], fill=(255, 0, 0, 90))
        for y, x in zip(*np.nonzero(S)):
            dr.rectangle([x*8+2, y*8+2, x*8+5, y*8+5], fill=(0, 200, 0, 220))
        im.alpha_composite(ov); im.save(OUT / 'review' / 'DIAG_acces.png')
        raise SystemExit('pas de chemin 16x16 jusqu a la grotte : voir review/DIAG_acces.png')
    # Scènes (5 ticks par image, eau à 10 ticks)
    def scene(tick):
        wp = (tick // WATER_TICKS) % WATER_PHASES; fp = (tick // FLAKE_TICKS) % FLAKE_PHASES
        im = Image.fromarray(wf[wp]); im.alpha_composite(Image.fromarray(sf[wp]))
        for k in static_order:
            im.alpha_composite(Image.fromarray(layers[k]))
        im.alpha_composite(Image.fromarray(ff[fp]))
        return im
    scenes = [scene(t * FLAKE_TICKS) for t in range(LOOP_TICKS // FLAKE_TICKS)]
    scenes[0].save(OUT / 'review' / f'{PFX}_scene_t000.png')
    scenes[0].save(OUT / 'review' / f'{PFX}_scene_animee.webp', save_all=True, append_images=scenes[1:],
                   duration=round(FLAKE_TICKS * 1000 / 60), loop=0, lossless=True)
    col = scenes[0].copy(); ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(ov)
    for y, x in zip(*np.nonzero(blocked)):
        dr.rectangle([x*8, y*8, x*8+7, y*8+7], fill=(220, 40, 40, 90))
    for (px, py), c in ((entry_px, (255, 200, 0, 255)), (threshold_px, (0, 170, 255, 255))):
        dr.rectangle([px, py, px + 15, py + 15], outline=c, width=2)
    col.alpha_composite(ov); col.save(OUT / 'review' / f'{PFX}_collisions_marqueurs.png')
    sheet = Image.new('RGBA', (len(poses) * 54, 48), (*PAL['surface'], 255))
    for i, p in enumerate(poses.values()):
        sheet.alpha_composite(Image.fromarray(p).resize((48, 48), Image.Resampling.NEAREST), (i * 54, 0))
    sheet.save(OUT / 'review' / f'{PFX}_planche_flocons_x6.png')
    ora = {'00_eau_glacee_f0': wf[0], '01_scintillements_f0': sf[0],
           **{Path(files[k]).stem.replace(PFX + '_', ''): layers[k] for k in static_order}, f'{nflake:02d}_flocons_f00': ff[0]}
    cr.write_ora(OUT / f'{PFX}_entree_givre_calques.ora', ora, 'Entree Givre sud-nord V1')
    stack = ([('Eau glacee facon riviere Metano 4 phases', wf, WATER_TICKS), ('Scintillements Metano recolores 4 phases', sf, WATER_TICKS)] +
             [(k, [layers[k]], 60) for k in static_order] + [('Flocons 48 phases', ff, FLAKE_TICKS)])
    counts = ground_project(stack, blocked, entry_px, threshold_px, gfx, tools)
    manifest = {
        'lot': 'entree_givre_sud_nord_v1', 'size_px': [W, H], 'grid_8px': [W // 8, H // 8],
        'method': 'rendu genere : decor complet sur magenta (eau = magenta) + sol complet genere separement',
        'reference_da': {'file': 'source/entree_givre_sud_nord_v1/reference/Frosty_Forest_Entrance_RT_mysterydungeonwiki.png',
                         'sha256': sha(REF), 'origine': 'mysterydungeonwiki.com, Rescue Team : Frosty Forest (recherche d images)'},
        'raw_inputs': [{'file': f'source/entree_givre_sud_nord_v1/bruts/{n}', 'sha256': sha(RAW / n), 'size': list(Image.open(RAW / n).size)}
                       for n in ['decor_magenta.png', 'sol_complet.png', 'flocons_poses.png']],
        'normalization': 'x0.5 exact (848x1264 -> 424x632), moyenne 2x2 par classe, palette commune 96 couleurs',
        'segmentation': 'eau = magenta dilate 1 px ; glacons = trous remplis de l eau ; falaise = b-r > 40 en bande nord puis tout au-dessus '
                        'par colonne ; sentier = lum 120-200 et b-r 18-48 lisse 9 px ; sapins/congeres = densite de contours > 0.16 sur 25 px',
        'layer_order_bottom_to_top': ([f'animation/eau/{PFX}_00_eau_glacee_fX.png', f'animation/scintillements/{PFX}_01_scintillements_fX.png'] +
                                      [f'calques/{files[k]}' for k in static_order] + [f'animation/flocons/{PFX}_{nflake:02d}_flocons_fXX.png']),
        'gue_gele': {'centre_full_px': list(GUE_CENTER_FULL), 'pixels': int(gue_mask.sum()), 'couleurs': {k: list(v) for k, v in ICE.items()},
                     'origine': 'DESSINE par le script (plaque, fissures, reflets) : le ruisseau genere coupait le sentier. '
                                'Une edition generative du croisement a ete rejetee (elle modifiait tout le ruisseau).'},
        'water': {'phases': WATER_PHASES, 'frame_length_ticks': WATER_TICKS, 'couleurs': {k: list(v) for k, v in PAL.items()},
                  'modele': 'structure et cadence de la riviere Metano (comme ESN2) recalculees sur nos berges ; palette froide a la main',
                  'origine': 'pixels recalcules, pas de tuiles natives'},
        'sparkles': {'source': 'source/eau_metano/natifs/Metano_Town_River_Sparkles.tile', 'placements': sparkles,
                     'origine': 'pixels Metano reels recolores blanc bleute'},
        'flakes': {'brut': 'source/entree_givre_sud_nord_v1/bruts/flocons_poses.png', 'poses': list(poses),
                   'reduction': 'fenetre 208 px centree -> 8 px (x1/26), palette 4 couleurs froides', 'derivee': 'pose = flocon pose 2x2 dessine',
                   'phases': FLAKE_PHASES, 'frame_length_ticks': FLAKE_TICKS, 'chute_px': FALL_PX, 'chute_phases': 40, 'pose_phases': 2,
                   'rotation': 'une pose toutes les 2 phases, 6 poses', 'ondulation': 'sinus periode 24 phases',
                   'emetteurs': emitters, 'origine': 'dessin GENERE, trajectoires creees ; pas la meteo officielle PMD'},
        'scene_loop_ticks': LOOP_TICKS,
        'access': {'entry_px': entry_px, 'threshold_px': threshold_px, 'path_found_16x16': True, 'blocked_cells': int(blocked.sum()),
                   'total_cells': int(blocked.size), 'rule': 'case bloquee si > 25 % hors neige visible, sentier et gue gele',
                   'approche_gue_px': int(approach.sum()), 'approche_gue': 'boules de neige dans l ellipse x1.35 du gue et congeres a moins de 6 px du sentier/gue rendues praticables (collision seulement, dessin inchange)'},
        'pmdo': {'target': '0.8.12', 'asset': ASSET, 'namespace': NAMESPACE, 'tiles_per_bank': counts, 'banks': list(counts),
                 'runtime_tested': False, 'warp': 'aucun'},
        'art_approved': False,
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    shutil.copyfile(OUT / 'manifest.json', STAGE / 'manifest.json')
    print(json.dumps({'sparkles': len(sparkles), 'flakes': len(emitters), 'gue_px': int(gue_mask.sum()), 'entry': entry_px,
                      'threshold': threshold_px, 'blocked': int(blocked.sum()), 'tiles': counts}, indent=1))


if __name__ == '__main__':
    build()
