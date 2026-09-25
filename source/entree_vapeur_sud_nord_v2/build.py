"""Entrée Vapeur sud -> nord, V2 — eau « façon rivière de Métano » + bulles de marais.

Demande : « pour l'animation d'eau fait quelque chose comme metano town river ! et fait des
animation bulle genere les cohérente a l'eau qui éclate car c'est un peu marécageux ».

- Terrain V1 conservé : les 7 calques opaques V1 sont relus tels quels (renders/..._v1/calques).
  Le calque V1 « ombres » est retiré : la bande de berge Métano le remplace.
- Eau V2 : STRUCTURE et CADENCE de la rivière Métano (Halcyon da6c2130, FrameLength 10, 4 phases) :
  aplat, bande sombre de 4 px, 1 px intermédiaire, frange dentelée sur ~3 px, lèvre claire contre la
  berge. Profil mesuré sur les 4 feuilles Metano_Town_River_Animation_1..4. Les bandes sont
  RECALCULÉES sur nos bassins (on ne peut pas transplanter la géométrie Métano) et les couleurs sont
  transposées vers la teinte de nos bassins : pas des tuiles Métano natives.
- Scintillements : pixels réels de Metano_Town_River_Sparkles (3 familles d'amas, 4 phases), même
  transposition de couleur, positions nouvelles.
- Bulles : planche GÉNÉRÉE (bruts/bulles_8_poses.png, 2x6 cases reçues au lieu de 1x8), 7 poses
  retenues + 1 anneau atténué dérivé, réduction uniforme x0,1, palette de l'eau V2.
Lancer : .venv/bin/python source/entree_vapeur_sud_nord_v2/build.py
"""
from pathlib import Path
import colorsys, hashlib, importlib.util, io, json, shutil, struct, uuid, zipfile

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
V1 = R / 'renders/entree_vapeur_sud_nord_v1'
OUT = R / 'renders/entree_vapeur_sud_nord_v2'
STAGE = R / '.cache/entree_vapeur_sud_nord_v2/entree_vapeur_sud_nord_v2'
NAMESPACE = 'entree_vapeur_sud_nord_v2'
ASSET = 'esn2_entree_vapeur_jour'
PFX = 'ESN2'
W, H = 424, 632
WATER_PHASES, WATER_TICKS = 4, 10            # rivière Métano vérifiée : 4 phases, FrameLength 10
BUBBLE_PHASES, BUBBLE_TICKS = 24, 5          # 24 x 5 ticks = 2 s ; PPCM avec l'eau (40 ticks) = 120 ticks
LOOP_TICKS = 120
CELL = 24                                    # case d'une bulle : 3 x 3 tuiles

METANO_RIVER = [R / f'source/eau_metano/natifs/Metano_Town_River_Animation_{i}.tile' for i in range(1, 5)]
METANO_SPARK = R / 'source/eau_metano/natifs/Metano_Town_River_Sparkles.tile'
M_SURFACE = (131, 218, 230)
M_ROLES = {'surface': (131, 218, 230), 'bande': (87, 135, 191), 'inter': (95, 183, 207),
           'accent': (111, 207, 231), 'clair': (148, 230, 238), 'reflet': (247, 255, 255),
           'contour': (65, 141, 189)}


def loadmod(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def decode_tile(path):
    raw = Path(path).read_bytes(); size, n = struct.unpack_from('<ii', raw); tiles = {}
    for i in range(n):
        x, y, off = struct.unpack_from('<iiq', raw, 8 + 16 * i)
        ln, = struct.unpack_from('<q', raw, off)
        tiles[x, y] = np.array(Image.open(io.BytesIO(raw[off + 8:off + 8 + ln])).convert('RGBA'))
    return tiles


def transpose_color(c):
    """Rôle Métano -> teinte de nos bassins : teinte -10°, saturation x1,45, valeur x0,5.
    Le reflet quasi blanc garde une valeur haute pour rester lisible."""
    h, s, v = colorsys.rgb_to_hsv(*(x / 255 for x in c[:3]))
    h = (h - 10 / 360) % 1; s = min(1, s * 1.45 if s > 0.1 else s + 0.12)
    v = v * (0.86 if v > 0.95 else 0.5)
    return tuple(round(x * 255) for x in colorsys.hsv_to_rgb(h, s, v))


# Palette V2 : mêmes rôles et même ORDRE de luminance que la rivière Métano, teintes choisies à la main
# autour de l'eau sarcelle V1 (la transposition HSV seule écrasait accent/clair sur l'aplat).
PAL = {'surface': (43, 115, 112), 'bande': (20, 62, 84), 'contour': (14, 50, 74), 'inter': (30, 92, 100),
       'accent': (36, 104, 108), 'clair': (84, 158, 146), 'reflet': (190, 226, 214)}


# ---------------------------------------------------------------- mesure Métano
def measure_metano():
    """Profil de la bande Métano par distance au bord, sur les 4 phases (contrôle, pas copie)."""
    prof = []
    for p in METANO_RIVER:
        t = decode_tile(p); xs = [k[0] for k in t]; ys = [k[1] for k in t]
        a = np.zeros(((max(ys) + 1) * 8, (max(xs) + 1) * 8, 4), 'uint8')
        for (x, y), im in t.items():
            a[y*8:y*8+8, x*8:x*8+8] = im
        op = a[..., 3] > 0; d = np.round(nd.distance_transform_edt(op))
        non_surface = op & (np.abs(a[..., :3].astype(int) - M_SURFACE).sum(2) > 0)
        prof.append([round(float(non_surface[(d == k) & op].mean()), 3) for k in range(1, 11)])
    return prof


# ---------------------------------------------------------------- eau façon Métano
def hash_noise(seed):
    rng = np.random.default_rng(seed)
    return nd.gaussian_filter(rng.random((H, W)), 1.0)


def water_phases(visible, water):
    d = nd.distance_transform_edt(visible)
    yy, xx = np.mgrid[:H, :W]
    jag = hash_noise(7); jag = (jag - jag.min()) / np.ptp(jag)
    frames = []
    for t in range(WATER_PHASES):
        ph = 2 * np.pi * t / WATER_PHASES
        # Ondulation qui voyage le long des berges : le bord intérieur de la bande avance/recule.
        n = 0.6 * np.sin(xx * 0.23 + yy * 0.11 - ph) + 0.4 * np.sin(xx * 0.07 - yy * 0.21 + 1.3 - ph)
        T = 4.5 + 1.1 * n                       # épaisseur bande sombre + intermédiaire ~4-6 px (Métano : 4 + 1)
        fringe = T + 0.6 + 2.6 * np.roll(jag, t * 2, axis=1)   # frange dentelée qui change à chaque phase
        a = np.zeros((H, W, 4), 'uint8'); a[..., 3] = 255
        a[..., :3] = PAL['surface']
        a[d <= fringe] = (*PAL['inter'], 255)
        a[(d <= fringe) & (np.roll(jag, t * 2, axis=1) > 0.62)] = (*PAL['accent'], 255)
        a[d <= T] = (*PAL['inter'], 255)
        a[d <= T - 1] = (*PAL['bande'], 255)
        lip = (d <= 1.0) & (np.sin(xx * 0.5 + yy * 0.3 - ph) > -0.35)
        a[lip] = (*PAL['accent'], 255)
        a[~water] = 0
        # Sous les buissons en surplomb (eau non visible) : aplat uniforme, invariant.
        hidden = water & ~visible
        a[hidden] = (*PAL['bande'], 255)
        frames.append(a)
    return frames, d


# ---------------------------------------------------------------- scintillements Métano
def sparkle_families():
    t = decode_tile(METANO_SPARK)

    def cluster(cols, rows, step):
        out = []
        for k in range(4):
            a = np.zeros((len(rows) * 8, len(cols) * 8, 4), 'uint8')
            for j, r in enumerate(rows):
                for i, c in enumerate(cols):
                    a[j*8:j*8+8, i*8:i*8+8] = t[c, r + step * k]
            out.append(a)
        return out
    fams = {'A_16x24': cluster([0, 1], [0, 1, 2], 3), 'B_24x16': cluster([2, 3, 4], [0, 1], 2),
            'C_16x32': cluster([0, 1], [12, 13, 14, 15], 4)}
    lut = {v: PAL[k] for k, v in M_ROLES.items()}
    res = {}
    for name, frames in fams.items():
        conv = []
        for a in frames:
            o = np.zeros_like(a)
            m = (a[..., 3] == 255) & (np.abs(a[..., :3].astype(int) - M_SURFACE).sum(2) > 0)
            for y, x in zip(*np.nonzero(m)):
                c = tuple(int(v) for v in a[y, x, :3])
                o[y, x, :3] = lut.get(c, transpose_color(c)); o[y, x, 3] = 255
            conv.append(o)
        res[name] = conv
    return res


# ---------------------------------------------------------------- bulles générées
def bubble_poses():
    src = np.array(Image.open(HERE / 'bruts/bulles_8_poses.png').convert('RGB')).astype(int)
    h, w = src.shape[:2]; rows, cols = 2, 6
    r, g, b = src.transpose(2, 0, 1)
    mag = (r > 150) & (b > 150) & (g < 110) & (r > g * 1.5)
    ch, cw = h / rows, w / cols
    # (rangée, colonne) des poses retenues, dans l'ordre de l'animation.
    picks = [('point', 0, 0), ('petite', 0, 1), ('ronde', 0, 2), ('dome', 0, 3),
             ('tension', 1, 0), ('eclatement', 0, 4), ('anneaux', 0, 5)]
    win = 240; f = CELL / win
    pal = np.array([PAL['bande'], PAL['inter'], PAL['surface'], PAL['accent'], PAL['clair'],
                    PAL['reflet'], transpose_color((20, 40, 70))], int)
    raw = {}
    for name, ry, cx in picks:
        cy0 = int((ry + 0.5) * ch); cx0 = int((cx + 0.5) * cw)
        y0, x0 = cy0 - win // 2, cx0 - win // 2
        crop = src[max(0, y0):y0 + win, max(0, x0):x0 + win]; m = ~mag[max(0, y0):y0 + win, max(0, x0):x0 + win]
        pad = np.zeros((win, win, 3), int); pm = np.zeros((win, win), bool)
        oy, ox = max(0, -y0), max(0, -x0)
        pad[oy:oy + crop.shape[0], ox:ox + crop.shape[1]] = crop; pm[oy:oy + m.shape[0], ox:ox + m.shape[1]] = m
        k = win // CELL
        cov = pm.reshape(CELL, k, CELL, k).mean((1, 3))
        col = (pad * pm[..., None]).reshape(CELL, k, CELL, k, 3).sum((1, 3)) / np.maximum(pm.reshape(CELL, k, CELL, k).sum((1, 3)), 1)[..., None]
        # traits fins (anneaux, gouttelettes) : seuil de couverture plus bas pour ne pas les casser
        keep = cov >= (0.1 if name in ('anneaux', 'eclatement') else 0.22)
        raw[name] = (col @ [.299, .587, .114], keep)
    # Plage de luminance COMMUNE à toutes les poses (la planche générée est plus claire que nos bassins).
    allv = np.concatenate([l[k] for l, k in raw.values()])
    lo, hi = np.percentile(allv, [3, 98])
    pal_lum = pal @ [.299, .587, .114]
    poses = {}
    for name, (src_lum, keep) in raw.items():
        tgt = pal_lum.min() + (np.clip(src_lum, lo, hi) - lo) / max(hi - lo, 1) * (pal_lum.max() - pal_lum.min())
        idx = np.abs(tgt[..., None] - pal_lum[None, None, :]).argmin(-1)
        o = np.zeros((CELL, CELL, 4), 'uint8'); o[..., :3] = pal[idx]; o[..., 3] = 255; o[~keep] = 0
        poses[name] = o
    # Tension : le dôme + les seules gouttelettes de la pose « tension » (son intérieur généré était trop sombre).
    t = poses['dome'].copy(); drops = (poses['tension'][..., 3] > 0) & (poses['dome'][..., 3] == 0)
    t[drops] = poses['tension'][drops]; poses['tension'] = t
    # Anneaux : ride claire lisible sur l'aplat (teinte claire), comme les lèvres de la rivière Métano.
    op = poses['anneaux'][..., 3] > 0; poses['anneaux'][op, :3] = PAL['clair']
    # Anneau atténué dérivé : on garde l'anneau extérieur seulement (retrait des pixels proches du centre).
    ring = poses['anneaux'].copy(); yy, xx = np.mgrid[:CELL, :CELL]
    rr = np.hypot(yy - (CELL - 1) / 2, xx - (CELL - 1) / 2)
    op = ring[..., 3] > 0
    ring[op & (rr < np.percentile(rr[op], 50))] = 0
    ring[ring[..., 3] > 0, :3] = PAL['accent']
    poses['anneau_final'] = ring
    return poses


BUBBLE_TIMELINE = (['point'] * 2 + ['petite'] * 2 + ['ronde'] * 2 + ['dome'] * 3 + ['tension'] * 2 +
                   ['eclatement'] * 2 + ['anneaux'] * 2 + ['anneau_final'] * 2)   # 17 phases, 7 au repos


# ---------------------------------------------------------------- placements
def place(free, sizes, count, seed, taken):
    """Positions alignées sur 8 px, empreinte entièrement sur eau visible libre, sans chevauchement."""
    rng = np.random.default_rng(seed); out = []
    cands = [(y, x) for y in range(0, H - 32, 8) for x in range(0, W - 24, 8)]
    rng.shuffle(cands)
    for y, x in cands:
        hh, ww = sizes
        if y + hh > H or x + ww > W:
            continue
        if free[y:y + hh, x:x + ww].all() and not taken[max(0, y - 8):y + hh + 8, max(0, x - 8):x + ww + 8].any():
            out.append((y, x)); taken[y:y + hh, x:x + ww] = True
            if len(out) == count:
                break
    return out


# ---------------------------------------------------------------- Ground
def ground_project(tracks, static, blocked, entry_px, threshold_px, gfx, tools):
    if STAGE.exists():
        shutil.rmtree(STAGE)
    with zipfile.ZipFile(R / 'mod_metano_expeditions_pmdo_0812.zip') as z:
        tpl = json.loads(z.read('metano_expeditions/Data/Ground/v50812_01_crete_sillage_jour.rsground'))
    o = tpl['Object']; gw, gh = W // 8, H // 8; layers, banks = [], []
    for i, (title, frames, ticks) in enumerate(tracks):
        bank = gfx.TileBank(f'{PFX}_{i:02d}_{title.split()[0].upper()}')
        bank.ids[bytes(256)] = (0, 0); bank.data[(0, 0)] = bytes(256)

        def cell(x, y, frames=frames, bank=bank):
            fs = []
            for a in frames:
                f = bank.add(Image.fromarray(a[y*8:y*8+8, x*8:x*8+8]), x, y)
                fs.append(f if f else {'Sheet': bank.name, 'TexLoc': {'X': 0, 'Y': 0}})
            if all(f['TexLoc'] == {'X': 0, 'Y': 0} for f in fs):
                return []
            if all(f == fs[0] for f in fs):
                return [fs[0]]
            return fs
        layers.append(gfx.layer(f'{i:02d} {title}', gw, gh, cell, ticks)); banks.append(bank)
    base = len(layers)
    for j, (name, a) in enumerate(static.items()):
        bank = gfx.TileBank(f'{PFX}_{base + j:02d}_{name.upper()}')

        def cell(x, y, a=a, bank=bank):
            f = bank.add(Image.fromarray(a[y*8:y*8+8, x*8:x*8+8]), x, y)
            return [f] if f else []
        layers.append(gfx.layer(f'{base + j:02d} {name}', gw, gh, cell)); banks.append(bank)
    layers.append(gfx.layer(f'{len(layers):02d} Vos elements avant-plan (Top)', gw, gh, draw=4))
    for bank in banks:
        bank.write(STAGE / f'Content/Tile/{bank.name}.tile')
    o.update(Name={'DefaultText': 'Entree Vapeur V2 - sud vers nord', 'LocalTexts': {}}, AssetName=ASSET,
             Released=False, TexSize=1, Music='', EdgeView=1, ViewCenter=None, ViewOffset={'X': 0, 'Y': 0},
             ActiveChar=None, Status={}, Layers=layers,
             Comment='PMDO 0.8.12. Terrain genere V1 ; eau facon riviere Metano (structure/cadence, couleurs transposees), '
                     'scintillements Metano recolores, bulles generees. Collisions de base a verifier. Seuil non raccorde.',
             Background={'$type': 'RogueEssence.Dungeon.LayeredBG, RogueEssence', 'Layers': []})
    o['obstacles'] = [[{'Bounds': {'X': x*8, 'Y': y*8, 'Width': 8, 'Height': 8}, 'Tags': int(blocked[y, x])}
                       for y in range(gh)] for x in range(gw)]
    mk = lambda n, p: {'EntName': n, 'Direction': 4, 'EntEnabled': True, 'triggerType': 0,
                       'Collider': {'X': p[0], 'Y': p[1], 'Width': 16, 'Height': 16}}
    o['Entities'] = [{'Name': 'Entrees et vos acteurs', 'Visible': True, 'MapChars': [], 'GroundObjects': [],
                      'Spawners': [], 'Markers': [mk('entrance', entry_px), mk('donjon_seuil', threshold_px)]}]
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
  <Name>Entree Vapeur sud-nord V2 - Atelier 0.8.12</Name>
  <Author>meromoonmeri</Author>
  <Description>Projet d'edition : entree generee, eau facon riviere Metano, scintillements et bulles de marais animes. Pas une aventure jouable.</Description>
  <Namespace>{NAMESPACE}</Namespace>
  <UUID>{ident}</UUID>
  <Version>2.0.0.0</Version>
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
    v1 = loadmod('esn1', R / 'source/entree_sud_nord_generee_v1/build.py')
    gfx = loadmod('pmdo_codec', R / 'source/pmdo_cote/build.py')
    tools = loadmod('index_tools', R / 'source/pmdo_cote/INSTALLER.py')
    for d in ['calques', 'animation/eau', 'animation/scintillements', 'animation/bulles', 'poses_bulles', 'review']:
        (OUT / d).mkdir(parents=True, exist_ok=True)
    v1m = json.loads((V1 / 'manifest.json').read_text())
    names = ['sol_complet', 'herbe', 'chemin_terre', 'buissons', 'falaises', 'piliers_entree', 'bouche_grotte']
    static = {}
    for p in v1m['layer_order_bottom_to_top'][1:]:
        key = Path(p).stem.split('_', 2)[2]
        if key in names:
            static[key] = np.array(Image.open(V1 / p).convert('RGBA'))
    assert list(static) == names
    water = np.array(Image.open(V1 / 'masques/ESN1_masque_eau_complete.png')) > 0
    land = np.zeros((H, W), bool)
    for a in static.values():
        land |= a[..., 3] == 255
    visible = water & ~land
    wf, dist = water_phases(visible, water)
    # Bulles générées : émetteurs décalés.
    taken = np.zeros((H, W), bool)
    poses = bubble_poses()
    for k, a in poses.items():
        Image.fromarray(a).save(OUT / 'poses_bulles' / f'{PFX}_bulle_{k}.png')
    emitters = place(visible, (CELL, CELL), 9, 29, taken)
    # Scintillements Métano : amas sur l'eau dégagée (distance > 5 px).
    fams = sparkle_families()
    deep = visible & (dist > 5)
    sp_frames = [np.zeros((H, W, 4), 'uint8') for _ in range(WATER_PHASES)]; sparkles = []
    for fi, (name, frames) in enumerate(fams.items()):
        hh, ww = frames[0].shape[:2]
        for (y, x) in place(deep, (hh, ww), 4, 11 + fi, taken):
            sparkles.append({'famille': name, 'xy': [x, y]})
            for t in range(WATER_PHASES):
                m = frames[t][..., 3] > 0; sp_frames[t][y:y+hh, x:x+ww][m] = frames[t][m]
    offsets = [(i * 7) % BUBBLE_PHASES for i in range(len(emitters))]
    bf = [np.zeros((H, W, 4), 'uint8') for _ in range(BUBBLE_PHASES)]
    for (y, x), off in zip(emitters, offsets):
        for t in range(BUBBLE_PHASES):
            k = (t - off) % BUBBLE_PHASES
            if k < len(BUBBLE_TIMELINE):
                pose = poses[BUBBLE_TIMELINE[k]]; m = pose[..., 3] > 0
                bf[t][y:y+CELL, x:x+CELL][m] = pose[m]
    for arr in sp_frames + bf:
        arr[~visible] = 0                         # jamais sur la berge ni sous un buisson
    # Exports PNG
    for t, a in enumerate(wf):
        Image.fromarray(a).save(OUT / 'animation/eau' / f'{PFX}_00_eau_metano_f{t}.png')
    for t, a in enumerate(sp_frames):
        Image.fromarray(a).save(OUT / 'animation/scintillements' / f'{PFX}_01_scintillements_f{t}.png')
    for t, a in enumerate(bf):
        Image.fromarray(a).save(OUT / 'animation/bulles' / f'{PFX}_02_bulles_f{t:02d}.png')
    files = {}
    for j, (k, a) in enumerate(static.items(), start=3):
        fn = f'{PFX}_{j:02d}_{k}.png'; Image.fromarray(a).save(OUT / 'calques' / fn); files[k] = fn
    # Collisions / accès (mêmes règles que V1)
    walk = ((static['herbe'][..., 3] == 255) | (static['chemin_terre'][..., 3] == 255))
    walk &= ~(water | (static['buissons'][..., 3] > 0) | (static['falaises'][..., 3] > 0) |
              (static['piliers_entree'][..., 3] > 0) | (static['bouche_grotte'][..., 3] > 0))
    blocked = v1.cell_grid(~walk)
    entry_px = v1m['access']['entry_px']; threshold_px = v1m['access']['threshold_px']
    ok, explored = v1.reachable(blocked, (entry_px[1] // 8, entry_px[0] // 8), (threshold_px[1] // 8, threshold_px[0] // 8))
    assert ok
    # Scène animée complète : 24 images x 5 ticks, eau et scintillements à 10 ticks.
    scenes = []
    for t in range(LOOP_TICKS // BUBBLE_TICKS):
        tick = t * BUBBLE_TICKS; wp = (tick // WATER_TICKS) % WATER_PHASES; bp = (tick // BUBBLE_TICKS) % BUBBLE_PHASES
        im = Image.fromarray(wf[wp]); im.alpha_composite(Image.fromarray(sp_frames[wp])); im.alpha_composite(Image.fromarray(bf[bp]))
        for a in static.values():
            im.alpha_composite(Image.fromarray(a))
        scenes.append(im)
    scenes[0].save(OUT / 'review' / f'{PFX}_scene_t000.png')
    scenes[0].save(OUT / 'review' / f'{PFX}_scene_animee.webp', save_all=True, append_images=scenes[1:],
                   duration=round(BUBBLE_TICKS * 1000 / 60), loop=0, lossless=True)
    scenes[0].resize((W * 2, H * 2), Image.Resampling.NEAREST).save(OUT / 'review' / f'{PFX}_scene_x2.png')
    col = scenes[0].copy(); ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(ov)
    for y, x in zip(*np.nonzero(blocked)):
        dr.rectangle([x*8, y*8, x*8+7, y*8+7], fill=(220, 40, 40, 90))
    for (px, py), c in ((entry_px, (255, 230, 40, 255)), (threshold_px, (60, 220, 255, 255))):
        dr.rectangle([px, py, px + 15, py + 15], outline=c, width=2)
    col.alpha_composite(ov); col.save(OUT / 'review' / f'{PFX}_collisions_marqueurs.png')
    # planche des poses de bulles x6 et bande d'eau x4
    sheet = Image.new('RGBA', (len(poses) * (CELL * 6 + 6), CELL * 6), (*PAL['surface'], 255))
    for i, a in enumerate(poses.values()):
        sheet.alpha_composite(Image.fromarray(a).resize((CELL * 6, CELL * 6), Image.Resampling.NEAREST), (i * (CELL * 6 + 6), 0))
    sheet.save(OUT / 'review' / f'{PFX}_planche_bulles_x6.png')
    ora = {f'00_eau_metano_f0': wf[0], '01_scintillements_f0': sp_frames[0], '02_bulles_f00': bf[0],
           **{Path(v).stem.replace(PFX + '_', ''): static[k] for k, v in files.items()}}
    v1.W, v1.H = W, H
    v1.write_ora(OUT / f'{PFX}_entree_vapeur_calques.ora', ora)
    tracks = [('Eau facon riviere Metano 4 phases', wf, WATER_TICKS),
              ('Scintillements Metano 4 phases', sp_frames, WATER_TICKS),
              ('Bulles de marais 24 phases', bf, BUBBLE_TICKS)]
    counts = ground_project(tracks, static, blocked, entry_px, threshold_px, gfx, tools)
    prof = measure_metano()
    manifest = {
        'lot': 'entree_vapeur_sud_nord_v2', 'size_px': [W, H], 'grid_8px': [W // 8, H // 8],
        'terrain': 'V1 inchange (7 calques relus depuis renders/entree_vapeur_sud_nord_v1/calques) ; calque V1 ombres retire.',
        'layer_order_bottom_to_top': ['animation/eau/ESN2_00_eau_metano_fX.png', 'animation/scintillements/ESN2_01_scintillements_fX.png',
                                      'animation/bulles/ESN2_02_bulles_fXX.png'] + [f'calques/{v}' for v in files.values()],
        'water': {'phases': WATER_PHASES, 'frame_length_ticks': WATER_TICKS, 'loop_s': WATER_PHASES * WATER_TICKS / 60,
                  'modele': 'riviere Metano Town (Halcyon da6c2130), FrameLength 10 et 4 phases verifies dans source/eau_metano/animations_carte.json',
                  'structure': 'aplat + bande sombre ~4 px + 1 px intermediaire + frange dentelee ~3 px + levre claire, recalcules sur nos bassins',
                  'profil_metano_non_surface_par_distance_1_a_10px': prof,
                  'couleurs': {k: list(v) for k, v in PAL.items()},
                  'transposition': 'palette a la main, roles et ordre de luminance Metano (surface/bande/contour/inter/accent/clair/reflet) ; couleurs hors roles des scintillements : HSV teinte -10 deg, sat x1.45, valeur x0.5',
                  'origine': 'Structure et cadence Metano ; pixels et couleurs recalcules. PAS des tuiles Metano natives.'},
        'sparkles': {'source': 'source/eau_metano/natifs/Metano_Town_River_Sparkles.tile', 'sha256': sha(METANO_SPARK),
                     'familles': {'A_16x24': 'colonnes 0-1, rangees 0-2, pas 3', 'B_24x16': 'colonnes 2-4, rangees 0-1, pas 2',
                                  'C_16x32': 'colonnes 0-1, rangees 12-15, pas 4'},
                     'placements': sparkles, 'origine': 'pixels Metano reels, couleurs transposees, positions nouvelles, phases synchrones comme Metano'},
        'bubbles': {'brut': 'source/entree_vapeur_sud_nord_v2/bruts/bulles_8_poses.png', 'sha256': sha(HERE / 'bruts/bulles_8_poses.png'),
                    'brut_recu': '2 rangees x 6 cases (demande : 1 x 8), doublons ; disque sombre (rangee 2, case 3) ecarte',
                    'poses': list(poses), 'derivee': 'tension = dome + gouttelettes de la pose tension ; anneaux recolores clair ; anneau_final = anneau exterieur seul, teinte accent',
                    'reduction': 'fenetre 240 px -> 24 px, facteur 0.1 identique pour toutes les poses ; couleurs = palette eau V2 par rang de luminance',
                    'timeline_phases': BUBBLE_TIMELINE, 'phases': BUBBLE_PHASES, 'frame_length_ticks': BUBBLE_TICKS,
                    'loop_s': BUBBLE_PHASES * BUBBLE_TICKS / 60, 'emetteurs': [{'xy': [x, y], 'decalage': o} for (y, x), o in zip(emitters, offsets)],
                    'origine': 'dessin GENERE + chronologie creee par nous ; pas une animation officielle'},
        'scene_loop_ticks': LOOP_TICKS,
        'access': {'entry_px': entry_px, 'threshold_px': threshold_px, 'path_found_16x16': ok, 'blocked_cells': int(blocked.sum())},
        'pmdo': {'target': '0.8.12', 'asset': ASSET, 'namespace': NAMESPACE, 'tiles_per_bank': counts,
                 'banks': list(counts), 'runtime_tested': False, 'warp': 'aucun'},
        'art_approved': False,
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    shutil.copyfile(OUT / 'manifest.json', STAGE / 'manifest.json')
    print(json.dumps({'sparkles': len(sparkles), 'emitters': len(emitters), 'tiles': counts, 'profil_metano_phase0': prof[0]}, indent=1))


if __name__ == '__main__':
    build()
