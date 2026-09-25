"""Entrée Vapeur sud -> nord, V1 — méthode « rendu généré » (layouts_magenta_v1).

Pipeline : décor complet généré sur magenta + sol complet généré (même cadrage)
+ matière d'eau générée -> normalisation uniforme x0,5 (848x1264 -> 424x632,
53x79 cases de 8 px) -> segmentation en calques alignés -> eau en palette
cycling à indices fixes -> PNG / ORA / aperçu -> projet Ground PMDO 0.8.12.

Le terrain est un DESSIN GÉNÉRÉ référencé PMD Sky (Steam Cave entrance), PAS des
pixels natifs certifiés et PAS un collage de morceaux de maps.
Lancer :  .venv/bin/python source/entree_sud_nord_generee_v1/build.py
"""
from pathlib import Path
import base64, hashlib, importlib.util, io, json, shutil, struct, uuid, zipfile
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
RAW = HERE / 'bruts'
OUT = R / 'renders/entree_vapeur_sud_nord_v1'
STAGE = R / '.cache/entree_vapeur_sud_nord_v1/entree_vapeur_sud_nord'
NAMESPACE = 'entree_vapeur_sud_nord'
ASSET = 'esn1_entree_vapeur_jour'
PFX = 'ESN1'
W, H = 424, 632           # 848x1264 x 0.5 exactement, 53 x 79 cases
FULL = (848, 1264)
WATER_FRAMES, WATER_TICKS = 12, 10   # 12 x 10/60 s = 2,0 s
PALETTE_COLORS = 96


def loadmod(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rgb(path):
    return np.array(Image.open(path).convert('RGB')).astype(int)


def poly(points, size=FULL):
    im = Image.new('L', size); ImageDraw.Draw(im).polygon(points, fill=255)
    return np.array(im) > 0


def keep_large(mask, minimum):
    lab, n = nd.label(mask)
    if n == 0:
        return mask
    sz = nd.sum(mask, lab, range(1, n + 1))
    return np.isin(lab, 1 + np.flatnonzero(sz >= minimum))


# ---------------------------------------------------------------- segmentation
def classify_terrain(a):
    r, g, b = a.transpose(2, 0, 1)
    mx = a.max(2)
    mag = (r > g * 1.3) & (b > g * 1.3) & (r > 60) & (b > 60)
    water = mag & (r > 200) & (b > 200) & (g < 90)          # magenta plein
    shadow = mag & ~water                                     # ombre de berge peinte en magenta sombre
    solid = ~mag
    green = (g > r + 8) & (g > b + 8) & solid
    lum = a @ [.299, .587, .114]
    wgt = green.astype(float)
    gmean = nd.uniform_filter(np.where(green, lum, 0.0), 21) / np.maximum(nd.uniform_filter(wgt, 21), 1e-3)
    # Histogramme bimodal mesuré : buissons ~96, herbe ~128, creux 108-112.
    bush = green & (gmean < 110)
    bush = nd.binary_opening(nd.binary_closing(bush, iterations=3), iterations=2)
    bush = nd.binary_fill_holes(bush) & solid
    bush = keep_large(bush, 400)
    # Roche : composante non verte reliée au bord nord.
    nongreen = solid & ~green
    lab, _ = nd.label(nongreen)
    top = [v for v in np.unique(lab[0]) if v]
    rock = np.isin(lab, top)
    # Piste de terre sous la bouche : olive (b << r), dans la zone praticable repérée.
    track_zone = poly([(360, 444), (472, 444), (482, 468), (505, 500), (510, 545), (474, 590),
                       (396, 594), (352, 560), (345, 510), (368, 478)])
    olive = solid & ~green & (b < r * 0.62) & (mx >= 60)
    dirt = track_zone & olive
    dirt = nd.binary_closing(dirt, iterations=2) & solid & ~green & track_zone
    # Tâche de terre isolée plus au sud (brune, entourée d'herbe).
    brown = solid & ~green & (r >= g) & (g >= b - 6)
    dirt |= keep_large(brown & ~rock, 300)
    rock &= ~dirt
    # Bouche : pixels sombres connexes dans la cavité.
    mouth_box = poly([(362, 372), (482, 372), (482, 462), (362, 462)])
    mouth = mouth_box & solid & (mx < 72)
    mouth = keep_large(nd.binary_closing(mouth, iterations=2) & mouth_box & solid, 600)
    mouth = nd.binary_fill_holes(mouth)
    rock &= ~mouth
    # Piliers qui encadrent l'entrée : sous-ensemble de la roche, calque séparé.
    pillars = rock & (poly([(296, 352), (388, 352), (394, 484), (296, 484)]) |
                      poly([(452, 376), (566, 376), (570, 504), (448, 504)]))
    rock &= ~pillars
    grass = solid & ~bush & ~rock & ~pillars & ~dirt & ~mouth
    return dict(water=water, shadow=shadow, grass=grass, dirt=dirt, bush=bush,
                rock=rock, pillars=pillars, mouth=mouth)


def classify_floor(f):
    r, g, b = f.transpose(2, 0, 1)
    mag = (r > g * 1.3) & (b > g * 1.3) & (r > 60) & (b > 60)
    return dict(valid=~mag, water=mag)


# ---------------------------------------------------------------- réduction x0,5
def down_mask(m):
    return m.reshape(H, 2, W, 2).sum((1, 3)) >= 2


def down_colors(a, m):
    """Moyenne 2x2 des seuls pixels de la classe (pas de mélange magenta)."""
    w = m.reshape(H, 2, W, 2).astype(float)
    s = (a.reshape(H, 2, W, 2, 3) * w[..., None]).sum((1, 3))
    n = w.sum((1, 3))[..., None]
    return np.clip(np.round(s / np.maximum(n, 1)), 0, 255).astype('uint8')


def exclusive(masks, order):
    """Réduit chaque masque puis attribue chaque case 2x2 à une seule classe."""
    counts = np.stack([masks[k].reshape(H, 2, W, 2).sum((1, 3)) for k in order])
    win = counts.argmax(0); has = counts.max(0) >= 2
    return {k: (win == i) & has for i, k in enumerate(order)}


def rgba(colors, mask, alpha=None):
    out = np.zeros((H, W, 4), 'uint8')
    out[..., :3] = colors
    out[..., 3] = 255 if alpha is None else alpha
    out[~mask] = 0
    return out


def quantize_layers(layers, colors=PALETTE_COLORS):
    """Palette commune limitée (aplats PMD), sans tramage ; alpha inchangé."""
    opaque = np.concatenate([l[l[..., 3] == 255][:, :3] for l in layers.values()])
    sample = Image.fromarray(opaque.reshape(-1, 1, 3))
    pal_img = sample.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = np.array(pal_img.getpalette()[:colors * 3], 'uint8').reshape(-1, 3)
    out = {}
    for k, l in layers.items():
        a = l.copy(); m = a[..., 3] == 255
        if m.any():
            q = Image.fromarray(a[..., :3]).quantize(palette=pal_img, dither=Image.Dither.NONE)
            a[..., :3] = pal[np.array(q)]
        a[~m] = 0 if k != 'ombres' else a[~m]
        a[a[..., 3] == 0] = 0
        out[k] = a
    return out, pal


# ---------------------------------------------------------------- eau
def water_frames(water_mask):
    src = Image.open(RAW / 'eau_matiere.png').convert('RGB')
    small = src.resize((src.width // 2, src.height // 2), Image.Resampling.BOX)
    q = small.quantize(colors=6, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = np.array(q.getpalette()[:18], int).reshape(6, 3)
    order = np.argsort(pal @ [.299, .587, .114])
    ramp = pal[order]                                   # 6 teintes générées, sombre -> clair
    rank = np.empty(6, int); rank[order] = np.arange(6)
    level_tile = rank[np.array(q)]
    th, tw = level_tile.shape
    yy, xx = np.mgrid[:H, :W]
    # Échantillonnage ondulé : les reflets suivent des courbes, pas des bandes droites.
    warp = np.round(5 * np.sin(2 * np.pi * xx / 70) + 3 * np.sin(2 * np.pi * xx / 23 + 1.1)).astype(int)
    level = level_tile[(yy + warp) % th, xx % tw]
    # Bandes de phase fixes : front légèrement ondulé qui descend vers le sud.
    band = ((yy // 3) + np.round(3 * np.sin(2 * np.pi * xx / 96)).astype(int)) % WATER_FRAMES
    index = (level * WATER_FRAMES + band).astype('uint8')   # 72 indices fixes
    frames, palettes = [], []
    for t in range(WATER_FRAMES):
        table = np.zeros((256, 3), 'uint8')
        for L in range(6):
            for bnd in range(WATER_FRAMES):
                d = (bnd - t) % WATER_FRAMES
                bump = 1 if d == 0 else (1 if (L >= 2 and d in (1, WATER_FRAMES - 1)) else 0)
                table[L * WATER_FRAMES + bnd] = ramp[min(5, L + bump)]
        palettes.append(table[:6 * WATER_FRAMES].tolist())
        a = np.zeros((H, W, 4), 'uint8'); a[..., :3] = table[index]; a[..., 3] = 255
        a[~water_mask] = 0
        frames.append(a)
    return frames, index, ramp.tolist(), palettes


# ---------------------------------------------------------------- ORA
def write_ora(path, layers):
    root = ET.Element('image', w=str(W), h=str(H), name='Entrée Vapeur sud-nord V1')
    stack = ET.SubElement(root, 'stack'); comp = Image.new('RGBA', (W, H))
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', 'image/openraster', compress_type=zipfile.ZIP_STORED)
        items = list(layers.items())
        for i, (name, a) in reversed(list(enumerate(items))):
            fn = f'data/layer{i:02d}.png'
            ET.SubElement(stack, 'layer', name=name, src=fn, x='0', y='0', opacity='1.0',
                          visibility='visible', **{'composite-op': 'svg:src-over'})
            b = io.BytesIO(); Image.fromarray(a).save(b, format='PNG'); z.writestr(fn, b.getvalue())
        for _, a in items:
            comp.alpha_composite(Image.fromarray(a))
        b = io.BytesIO(); comp.save(b, format='PNG'); z.writestr('mergedimage.png', b.getvalue())
        th = comp.copy(); th.thumbnail((256, 256)); b = io.BytesIO(); th.save(b, format='PNG')
        z.writestr('Thumbnails/thumbnail.png', b.getvalue())
        z.writestr('stack.xml', ET.tostring(root, encoding='utf-8', xml_declaration=True))


# ---------------------------------------------------------------- collisions
def cell_grid(block):
    """Case 8x8 bloquée si plus de 25 % de ses pixels sont non praticables."""
    return block.reshape(H // 8, 8, W // 8, 8).mean((1, 3)) > 0.25


def reachable(blocked, start, goal, clearance=2):
    """BFS sur cases, personnage 16x16 = 2x2 cases libres."""
    gh, gw = blocked.shape
    ok = np.zeros_like(blocked)
    for y in range(gh - clearance + 1):
        for x in range(gw - clearance + 1):
            ok[y, x] = not blocked[y:y + clearance, x:x + clearance].any()
    from collections import deque
    seen = np.zeros_like(ok); q = deque([start]); seen[start] = True
    while q:
        y, x = q.popleft()
        if (y, x) == goal:
            return True, int(seen.sum())
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < gh and 0 <= nx < gw and ok[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True; q.append((ny, nx))
    return False, int(seen.sum())


# ---------------------------------------------------------------- Ground PMDO
def ground_project(static, water, blocked, entry_px, threshold_px):
    gfx = loadmod('pmdo_codec', R / 'source/pmdo_cote/build.py')
    tools = loadmod('index_tools', R / 'source/pmdo_cote/INSTALLER.py')
    if STAGE.exists():
        shutil.rmtree(STAGE)
    with zipfile.ZipFile(R / 'mod_metano_expeditions_pmdo_0812.zip') as z:
        tpl = json.loads(z.read('metano_expeditions/Data/Ground/v50812_01_crete_sillage_jour.rsground'))
    o = tpl['Object']
    gw, gh = W // 8, H // 8
    layers, banks = [], []
    # Eau animée : une banque, 12 frames explicites par case, FrameLength 10.
    wbank = gfx.TileBank(f'{PFX}_00_EAU_ANIMEE'); wbank.ids[bytes(256)] = (0, 0); wbank.data[(0, 0)] = bytes(256)

    def water_cell(x, y):
        fs = []
        for a in water:
            f = wbank.add(Image.fromarray(a[y*8:y*8+8, x*8:x*8+8]), x, y)
            fs.append(f if f else {'Sheet': wbank.name, 'TexLoc': {'X': 0, 'Y': 0}})
        if all(f['TexLoc'] == {'X': 0, 'Y': 0} for f in fs):
            return []
        return fs
    layers.append(gfx.layer('00 Eau - palette cycling 12 phases', gw, gh, water_cell, WATER_TICKS))
    banks.append(wbank)
    for i, (name, a) in enumerate(static.items(), start=1):
        bank = gfx.TileBank(f'{PFX}_{i:02d}_{name.upper()}')

        def cell(x, y, a=a, bank=bank):
            f = bank.add(Image.fromarray(a[y*8:y*8+8, x*8:x*8+8]), x, y)
            return [f] if f else []
        layers.append(gfx.layer(f'{i:02d} {name}', gw, gh, cell))
        banks.append(bank)
    layers.append(gfx.layer(f'{len(layers):02d} Vos elements avant-plan (Top)', gw, gh, draw=4))
    for bank in banks:
        bank.write(STAGE / f'Content/Tile/{bank.name}.tile')
    o.update(Name={'DefaultText': 'Entree Vapeur - sud vers nord', 'LocalTexts': {}}, AssetName=ASSET,
             Released=False, TexSize=1, Music='', EdgeView=1, ViewCenter=None,
             ViewOffset={'X': 0, 'Y': 0}, ActiveChar=None, Status={},
             Comment='PMDO 0.8.12. Rendu genere reference PMD Sky (non natif certifie). Arrivee sud, grotte au nord. '
                     'Collisions de base deduites des calques : a verifier en jeu. Seuil de donjon non raccorde.',
             Background={'$type': 'RogueEssence.Dungeon.LayeredBG, RogueEssence', 'Layers': []},
             Layers=layers)
    o['obstacles'] = [[{'Bounds': {'X': x*8, 'Y': y*8, 'Width': 8, 'Height': 8},
                        'Tags': int(blocked[y, x])} for y in range(gh)] for x in range(gw)]
    marker = lambda name, p, d: {'EntName': name, 'Direction': d, 'EntEnabled': True, 'triggerType': 0,
                                 'Collider': {'X': p[0], 'Y': p[1], 'Width': 16, 'Height': 16}}
    o['Entities'] = [{'Name': 'Entrees et vos acteurs', 'Visible': True, 'MapChars': [], 'GroundObjects': [],
                      'Spawners': [], 'Markers': [marker('entrance', entry_px, 4),
                                                  marker('donjon_seuil', threshold_px, 4)]}]
    o['Decorations'] = [{'Name': 'Vos decorations', 'Layer': 2, 'Visible': True, 'Anims': []}]
    tpl['Version'] = '0.8.12.0'
    gfx.save(STAGE / f'Data/Ground/{ASSET}.rsground', json.dumps(tpl, ensure_ascii=False, separators=(',', ':')).encode())
    lua = (f'-- {ASSET} : base d edition. Aucun warp : raccorder donjon_seuil a votre donjon.\n'
           f'local {ASSET} = {{}}\nreturn {ASSET}\n').encode()
    gfx.save(STAGE / f'Data/Script/{NAMESPACE}/ground/{ASSET}/init.lua', lua)
    nodes = {}
    for p in sorted((STAGE / 'Content/Tile').glob('*.tile')):
        with p.open('rb') as f:
            nodes[p.stem] = tools.read_node(f)
    (STAGE / 'Content/Tile/index.idx').write_bytes(tools.encode_index(nodes))
    ident = uuid.uuid5(uuid.NAMESPACE_URL, 'https://github.com/meromoonmeri/guilde-treehouse-pmd/' + NAMESPACE)
    (STAGE / 'Mod.xml').write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<Header>
  <Name>Entree Vapeur sud-nord - Atelier 0.8.12</Name>
  <Author>meromoonmeri</Author>
  <Description>Projet d'edition : une entree de donjon generee (arrivee sud, grotte nord), 10 calques dont eau animee. Pas une aventure jouable.</Description>
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
    script = script.replace(needle, needle + '''            # The delivered index belongs ONLY to this standalone project.
            # Merge its tile headers below; never overwrite another mod's index.
            if relative.as_posix() == 'Content/Tile/index.idx':
                continue
''')
    (STAGE / 'INSTALLER.py').write_text(script)
    return [b.name for b in banks], {b.name: len(b.data) for b in banks}


# ---------------------------------------------------------------- main
def build():
    for d in ['calques', 'animation/eau', 'masques', 'review']:
        (OUT / d).mkdir(parents=True, exist_ok=True)
    a = rgb(RAW / 'terrain_magenta.png'); f = rgb(RAW / 'sol_complet.png')
    assert a.shape[:2] == (FULL[1], FULL[0]) and f.shape == a.shape
    cls = classify_terrain(a); fl = classify_floor(f)
    order = ['water', 'shadow', 'grass', 'dirt', 'bush', 'rock', 'pillars', 'mouth']
    ex = exclusive(cls, order)
    # Eau sous TOUT ce qui n'est pas terrain opaque (y compris sous les buissons en surplomb).
    water_mask = ex['water'] | ex['shadow'] | down_mask(fl['water'] & ~(cls['grass'] | cls['dirt']))
    water_mask &= ~(ex['grass'] | ex['dirt'] | ex['rock'] | ex['pillars'] | ex['mouth'])
    # Sol complet : sol généré partout où le terrain n'est pas de l'eau.
    floor_mask = down_mask(fl['valid']) & ~water_mask
    lum = a @ [.299, .587, .114]
    ref = np.median(lum[cls['water']])
    shade = np.clip((1 - lum / ref) * 1.25, 0, 1)
    sh_alpha = (down_colors(np.repeat((shade * 255)[..., None], 3, 2), cls['shadow'])[..., 0] * 0.8 + 40).clip(0, 190).astype('uint8')
    raw_layers = {
        'ombres': rgb_shadow(ex['shadow'], sh_alpha),
        'sol_complet': rgba(down_colors(f, fl['valid']), floor_mask),
        'herbe': rgba(down_colors(a, cls['grass']), ex['grass']),
        'chemin_terre': rgba(down_colors(a, cls['dirt']), ex['dirt']),
        'buissons': rgba(down_colors(a, cls['bush']), ex['bush']),
        'falaises': rgba(down_colors(a, cls['rock']), ex['rock']),
        'piliers_entree': rgba(down_colors(a, cls['pillars']), ex['pillars']),
        'bouche_grotte': rgba(down_colors(a, cls['mouth']), ex['mouth']),
    }
    static, palette = quantize_layers(raw_layers)
    water, windex, ramp, palettes = water_frames(water_mask)
    # Couverture : aucune case vide dans la scène.
    cover = water_mask.copy()
    for k, l in static.items():
        if k != 'ombres':
            cover |= l[..., 3] == 255
    holes = int((~cover).sum())
    names = {}
    for i, (k, l) in enumerate(static.items(), start=1):
        fn = f'{PFX}_{i:02d}_{k}.png'; Image.fromarray(l).save(OUT / 'calques' / fn); names[k] = fn
    for t, l in enumerate(water):
        Image.fromarray(l).save(OUT / 'animation/eau' / f'{PFX}_00_eau_f{t:02d}.png')
    Image.fromarray(windex).save(OUT / 'animation/eau' / f'{PFX}_00_eau_indices.png')
    (OUT / 'animation/eau/palettes_12_phases.json').write_text(json.dumps(
        {'ramp_generee_sombre_vers_clair': ramp, 'indices': 'index = niveau*12 + bande', 'palettes': palettes}, indent=1))
    for k, m in ex.items():
        Image.fromarray(np.uint8(m) * 255).save(OUT / 'masques' / f'{PFX}_masque_{k}.png')
    Image.fromarray(np.uint8(water_mask) * 255).save(OUT / 'masques' / f'{PFX}_masque_eau_complete.png')

    # --- collisions et accès
    walk = np.zeros((H, W), bool)
    walk |= static['herbe'][..., 3] == 255
    walk |= static['chemin_terre'][..., 3] == 255
    walk &= ~(water_mask | (static['buissons'][..., 3] > 0) | (static['falaises'][..., 3] > 0) |
              (static['piliers_entree'][..., 3] > 0) | (static['bouche_grotte'][..., 3] > 0))
    blocked = cell_grid(~walk)
    gh, gw = blocked.shape
    # Arrivée : case libre 2x2 la plus centrale sur les 4 dernières rangées.
    ent = min(((abs(x - gw // 2 + 1), -y, y, x) for y in range(gh - 6, gh - 1) for x in range(gw - 1)
               if not blocked[y:y+2, x:x+2].any()))
    entry = (ent[2], ent[3])
    # Seuil : case libre 2x2 la plus au nord sous la bouche.
    mouth_cells = np.argwhere(cell_grid(static['bouche_grotte'][..., 3] == 0) == False)
    mcx = int(round(mouth_cells[:, 1].mean())); mby = int(mouth_cells[:, 0].max())
    thr = min(((y, abs(x - mcx + 1), y, x) for y in range(mby, mby + 12) for x in range(mcx - 6, mcx + 6)
               if not blocked[y:y+2, x:x+2].any()))
    threshold = (thr[2], thr[3])
    ok, explored = reachable(blocked, entry, threshold)
    assert ok, 'chemin sud -> seuil introuvable'
    entry_px = [entry[1] * 8, entry[0] * 8]; threshold_px = [threshold[1] * 8, threshold[0] * 8]

    # --- ORA + rendus de contrôle
    ora_layers = {'00_eau_phase00': water[0], **{f'{i:02d}_{k}': l for i, (k, l) in enumerate(static.items(), start=1)}}
    write_ora(OUT / f'{PFX}_entree_vapeur_calques.ora', ora_layers)
    scenes = []
    for t in range(WATER_FRAMES):
        im = Image.fromarray(water[t])
        for l in static.values():
            im.alpha_composite(Image.fromarray(l))
        scenes.append(im)
    scenes[0].save(OUT / 'review' / f'{PFX}_scene_phase00.png')
    scenes[0].save(OUT / 'review' / f'{PFX}_scene_animee.webp', save_all=True, append_images=scenes[1:],
                   duration=round(WATER_TICKS * 1000 / 60), loop=0, lossless=True)
    x2 = scenes[0].resize((W * 2, H * 2), Image.Resampling.NEAREST); x2.save(OUT / 'review' / f'{PFX}_scene_x2.png')
    over = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(over)
    for y in range(gh):
        for x in range(gw):
            if blocked[y, x]:
                d.rectangle([x*8, y*8, x*8+7, y*8+7], fill=(255, 0, 0, 80))
    col = scenes[0].copy(); col.alpha_composite(over); d = ImageDraw.Draw(col)
    for p, c in [(entry_px, (40, 120, 255, 220)), (threshold_px, (255, 220, 0, 230))]:
        d.rectangle([p[0], p[1], p[0]+15, p[1]+15], outline=c, width=2)
    col.save(OUT / 'review' / f'{PFX}_collisions_marqueurs.png')
    # Viewport PMDO x1 simulé (320x240) à l'arrivée et devant la grotte.
    for tag, p in [('arrivee', entry_px), ('seuil', threshold_px)]:
        cx = min(max(p[0] + 8 - 160, 0), W - 320); cy = min(max(p[1] + 8 - 120, 0), H - 240)
        scenes[0].crop((cx, cy, cx + 320, cy + 240)).save(OUT / 'review' / f'{PFX}_viewport_{tag}.png')

    banks, counts = ground_project(static, water, blocked, entry_px, threshold_px)
    manifest = {
        'lot': 'entree_vapeur_sud_nord_v1', 'size_px': [W, H], 'grid_8px': [W // 8, H // 8],
        'method': 'Rendu genere (source/layouts_magenta_v1/WORKFLOW.md) : decor complet sur magenta, sol complet genere, '
                  'matiere d eau generee, normalisation uniforme x0.5, segmentation en calques alignes.',
        'reference_da': {'file': 'Steam_Cave_entrance_TDS.png', 'sha256': sha(R / 'Steam_Cave_entrance_TDS.png'),
                         'role': 'reference de style et de composition donnee au generateur, aucun pixel copie'},
        'terrain_origin': 'DESSIN GENERE reference PMD Sky. PAS pixels natifs certifies. PAS collage de maps.',
        'raw_inputs': [{'file': f'source/entree_sud_nord_generee_v1/bruts/{p.name}', 'size': list(Image.open(p).size), 'sha256': sha(p)} for p in sorted(RAW.glob('*.png'))],
        'normalization': '848x1264 -> 424x632, facteur 0.5 identique en X et Y ; moyenne 2x2 par classe (pas de melange magenta) ; '
                         f'palette commune {PALETTE_COLORS} couleurs sans tramage.',
        'layer_order_bottom_to_top': ['animation/eau/ESN1_00_eau_fXX.png'] + [f'calques/{v}' for v in names.values()],
        'water': {'frames': WATER_FRAMES, 'engine_frame_length_ticks': WATER_TICKS,
                  'ms_per_frame': round(WATER_TICKS * 1000 / 60, 2), 'loop_s': WATER_FRAMES * WATER_TICKS / 60,
                  'type': 'palette cycling a indices fixes (6 niveaux x 12 bandes = 72 indices), front qui descend vers le sud',
                  'origin': 'matiere d eau generee + mouvement cree par nous ; PAS un cycle officiel recupere'},
        'layers_limits': 'Partitions d une composition unique. Sol complet genere sous buissons/falaises. '
                         'Faces cachees des falaises et buissons non reconstruites.',
        'holes_px': holes,
        'access': {'entry_px': entry_px, 'threshold_px': threshold_px, 'path_found_16x16': ok,
                   'cells_explored': explored, 'blocked_cells': int(blocked.sum()), 'total_cells': int(blocked.size),
                   'rule': 'case bloquee si >25% non praticable (eau, buissons, roche, piliers, bouche)'},
        'pmdo': {'target': '0.8.12', 'serialization': '0.8.12.0', 'asset': ASSET, 'namespace': NAMESPACE,
                 'tex_size': 1, 'tile_px': 8, 'banks': banks, 'tiles_per_bank': counts,
                 'template': 'mod_metano_expeditions_pmdo_0812.zip v50812_01_crete_sillage_jour (charge par PMDO 0.8.12 reel en sept.)',
                 'runtime_tested': False, 'warp': 'aucun : donjon_seuil a raccorder'},
        'import_png_to_tileset': 'Chaque PNG de calques/ et animation/eau/ : 424x632, importer en 8 px. Noms ESN1_* uniques.',
        'art_approved': False,
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    shutil.copyfile(OUT / 'manifest.json', STAGE / 'manifest.json')
    shutil.copyfile(HERE / 'README_PACK.md', STAGE / 'README.md')
    print(json.dumps({'holes': holes, 'entry': entry_px, 'threshold': threshold_px, 'blocked': int(blocked.sum()),
                      'tiles': counts}, indent=1))
    return manifest


def rgb_shadow(mask, alpha):
    out = np.zeros((H, W, 4), 'uint8'); out[..., 0] = 8; out[..., 1] = 22; out[..., 2] = 30
    out[..., 3] = alpha; out[~mask] = 0
    return out


if __name__ == '__main__':
    build()
