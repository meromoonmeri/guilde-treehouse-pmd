"""Entrée Grotte de cristal sud -> nord V1 (ECC1) — format 4:3 vaste (768 x 576 px, 96 x 72 cases).

Demande : « passe à la suite stp » (après EFF2). Carte suivante de la série, biome choisi par l'agent : salle du
joyau de Waterfall Cave, référence `Waterfall_Cave_gem_TDS.png` (PMD Explorers), jamais utilisée comme référence
principale. Méthode « textures canoniques » = rendu généré RÉFÉRENCÉ (rip passé au générateur en images=) :
- decor_magenta.png : décor complet 4:3 (1200 x 896), les bassins en magenta ;
- sol_complet.png : sol de galets complet édité depuis le décor (sous-couche) ;
- eclats_poses.png : planche d'éclats d'étoile sur magenta (3 rangées de 4 ; rangées cyan et rose utilisées).
Calques : sol complet, sol de galets, vide ardoise, fond marron, stalactites (paroi du fond), rochers (bordures des
bassins), racines, cristaux, tunnel.
Animations, chacune sur son calque, boucles fermées :
- bassins façon rivière Métano (structure, cadence 4 x 10), couleurs EXACTES du rip, sans liseré clair ;
- scintillements Métano natifs, 4 x 10 ticks ;
- éclats sur les cristaux (poses générées), 48 x 5 ticks (chronologie créée par nous).
Scène : PPCM(40, 240) = 240 ticks = 4 s.
Lancer : .venv/bin/python source/entree_crystal_cave_sud_nord_v1/build.py
"""
from pathlib import Path
import hashlib, importlib.util, io, json, shutil, uuid, zipfile

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
RAW = HERE / 'bruts'
REF = R / 'Waterfall_Cave_gem_TDS.png'
OUT = R / 'renders/entree_crystal_cave_sud_nord_v1'
STAGE = R / '.cache/entree_crystal_cave_sud_nord_v1/entree_crystal_cave_sud_nord'
NAMESPACE = 'entree_crystal_cave_sud_nord'
ASSET = 'ecc1_entree_crystal_cave'
PFX = 'ECC1'
W, H = 768, 576
SRC = (1200, 896)
WATER_PHASES, WATER_TICKS = 4, 10
GLINT_PHASES, GLINT_TICKS = 48, 5
LOOP_TICKS = 240
GLINT_K, GLINT_WIN = 12, 168                 # fenêtre 168 px -> 14 px
GLINT_SEQ = [0, 1, 2, 3, 3, 2, 1, 0]          # 8 phases allumées sur 48, puis repos
GLINT_N = 18
# Eau : couleurs EXACTES du rip (mesurées dans les bassins) : aplat, bande sombre de rive, accent clair des cellules.
WPAL = {'surface': (0, 87, 143), 'bande': (0, 63, 111), 'accent': (23, 135, 191)}
GEN = [
    {'file': 'decor_magenta.png', 'images': ['Waterfall_Cave_gem_TDS.png'], 'prompt':
     'Use EXACTLY the same textures, palette and pixel-art style as the reference image (Pokemon Mystery Dungeon '
     'Explorers of Sky, Waterfall Cave gem chamber): same blue-grey pebbly cave floor, same rounded teal-grey boulders '
     'edging the water, same tall grey-blue stalactite columns against a very dark maroon cave background, same small '
     'colorful crystals (pink, blue, yellow, purple) scattered on the floor, same dark red roots on the rock edges. Make '
     'a NEW, larger top-down map. WIDE LANDSCAPE 4:3, zoomed out so the cavern feels vast. Layout: the player arrives at '
     'the SOUTH (bottom edge center) on a pebbly path between boulder walls; the path widens into a large pebbly cave '
     'floor strewn with crystals; underground water pools fill the left and right sides, edged by boulders; at the top '
     'center a large pink gem crystal stands beside a dark tunnel opening in the back wall of stalactite columns (the '
     'dungeon entrance), reachable dry on foot. IMPORTANT: all water surfaces are filled with flat pure magenta #FF00FF, '
     'no ripples, no pattern. No characters, no text, no UI, no border.'},
    {'file': 'sol_complet.png', 'images': ['source/entree_crystal_cave_sud_nord_v1/bruts/decor_magenta.png'], 'prompt':
     'Same image, same size and pixel-art style, but showing only the plain blue-grey pebbly cave floor everywhere (all '
     'boulders, crystals, gem, stalactites, roots, dark areas and pink water removed and replaced by that same pebbly floor).',
     'note': 'premier essai ; une trace plus claire du chemin sud subsiste (sous-couche uniquement)'},
    {'file': 'eclats_poses.png', 'images': ['Waterfall_Cave_gem_TDS.png'], 'prompt':
     'Pixel-art sprite sheet on a flat pure magenta #FF00FF background, in the style and colors of the reference image '
     '(Pokemon Mystery Dungeon Explorers of Sky crystal cave). 2 rows of 6 separate small sprites: a crystal glint / '
     'four-pointed star sparkle in white and pale cyan, 6 poses from tiny dot, growing, full bright star with rays, '
     'shrinking, fading. Row 2 same in pale pink. Sprites well separated with wide magenta spacing, no text, no grid lines.',
     'note': 'rendue en 3 rangees de 4 (cyan, rose, rose saumon) : rangees 1 et 2 utilisees, poses par composantes'},
]


def loadmod(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


EM = loadmod('emf1_build', R / 'source/entree_mystifying_forest_sud_nord_v1/build.py')   # utilitaires EMF1
UL = loadmod('eul1_build', R / 'source/entree_underground_lake_sud_nord_v1/build.py')    # eau aux couleurs du rip
UL.WPAL = WPAL                                                                           # lake_water lit ce global
V2, V1, JM, BM = EM.V2, EM.V1, EM.JM, EM.BM
assert (JM.W, JM.H, JM.SRC) == (W, H, SRC)
keep_large, place, cell_grid, close_ = V1.keep_large, V1.place, V1.cell_grid, V1.close_
down_class, down_full, rgba, quantize_group = V1.down_class, V1.down_full, V1.rgba, V1.quantize_group
open_, sha, rgb, paste, reduce_pose = EM.open_, EM.sha, EM.rgb, EM.paste, EM.reduce_pose
PALETTE_GROUPS = {'terrain': (['sol_complet', 'sol', 'vide'], 64), 'roche': (['stalactites', 'rochers'], 48),
                  'fond': (['fond', 'racines'], 24), 'cristaux': (['cristaux'], 40), 'grotte': (['grotte'], 12)}
STATIC = ['sol', 'vide', 'fond', 'stalactites', 'rochers', 'racines', 'cristaux', 'grotte']
ROCK_SPLIT_Y = 300                            # décor : au-dessus = paroi du fond (stalactites), en dessous = rochers


def is_mag(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return (r > 180) & (b > 180) & (g < 150)


# ---------------------------------------------------------------- fidélité au rip (même classifieur des deux côtés)
def materials(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]; lum = a @ [.299, .587, .114]; mag = is_mag(a)
    sol = (b > r + 60) & (b >= g + 20) & (lum > 80) & (lum < 125) & ~mag
    roche = (b > r + 15) & (b < r + 60) & (np.abs(g - b) < 30) & (lum > 60) & (lum < 150) & ~mag
    fond = (r > g + 25) & (lum < 60) & ~mag
    return {'sol_galets': sol, 'roche': roche, 'fond': fond}


def fidelity(decor, ref):
    fr, fd = materials(ref), materials(decor); out = {}
    for k in fr:
        mr, md = ref[fr[k]].mean(0), decor[fd[k]].mean(0)
        out[k] = {'rip_rgb': [round(float(v), 1) for v in mr], 'decor_rgb': [round(float(v), 1) for v in md],
                  'distance': round(float(np.linalg.norm(mr - md)), 1)}
    return out


# ---------------------------------------------------------------- segmentation pleine résolution
def classify(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]; lum = a @ [.299, .587, .114]; sat = a.max(2) - a.min(2)
    hh, ww = lum.shape; yy, xx = np.mgrid[:hh, :ww]
    L = nd.uniform_filter(lum, 7); BR = nd.uniform_filter(b - r, 7)
    # Bassins : magenta en grandes nappes (> 5000 px : le joyau rose n'en fait pas partie), dilaté 3 px.
    water = nd.binary_dilation(keep_large(is_mag(a), 5000), iterations=3)
    # Fond marron (54,1,31) : r > g + 25, lum < 70, moitié haute.
    fond = open_(close_((r > g + 25) & (lum < 70) & (yy < 330) & ~water, 2), 1)
    # Vide ardoise du bas (45,61,76) : aplat (écart-type local < 1,5).
    sd = np.sqrt(np.maximum(nd.uniform_filter(lum ** 2, 5) - nd.uniform_filter(lum, 5) ** 2, 0))
    vide = keep_large(open_((sd < 1.5) & (np.abs(lum - 58) < 8) & (yy > 560) & ~water, 2), 5000)
    # Racines rouge sombre, bas de la carte.
    roots = keep_large(close_((r > g + 15) & (r > b - 10) & (yy > 560) & ~water & ~vide, 1), 30)
    # Tunnel : très sombre, haut-centre ; fermeture forte puis bouchage.
    tun = (lum < 34) & (yy > 100) & (yy < 260) & (xx > 480) & (xx < 720) & ~fond
    tun = nd.binary_fill_holes(close_(keep_large(close_(tun, 3), 800), 6))
    # Cristaux : saturés hors du bleu du sol (rose, jaune, violet, rouge, vert) ou très clairs.
    crys = (((sat > 70) & ~((b > r + 40) & (b >= g)) & (lum > 60)) | (lum > 170)) & ~water & ~fond & ~roots
    crys = nd.binary_dilation(keep_large(nd.binary_fill_holes(close_(crys, 2)), 12), iterations=2) & ~water & ~tun
    # Sol de galets (62,105,141) : b - r lissé > 72, lum lissée 85-135, grande composante ; trous comblés.
    floor = (BR > 72) & (L > 85) & (L < 135) & ~water & ~fond & ~crys & ~tun
    floor = keep_large(open_(close_(floor, 2), 3), 20000)
    floor = nd.binary_fill_holes(floor | crys) & ~water & ~crys
    rest = ~(water | fond | vide | roots | tun | crys | floor)
    return dict(water=water, sol=floor, fond=fond, vide=vide, racines=roots, stalactites=rest & (yy < ROCK_SPLIT_Y),
                rochers=rest & (yy >= ROCK_SPLIT_Y), cristaux=crys, grotte=tun)


# ---------------------------------------------------------------- éclats générés
def glint_poses(path):
    """Planche 3 x 4 : composantes regroupées en rangées ; rangées 1 (cyan) et 2 (rose), 4 poses chacune."""
    src = rgb(path); bg = is_mag(src) | ((src[..., 0] - src[..., 1] > 60) & (src[..., 2] - src[..., 1] > 60))
    lab, n = nd.label(nd.binary_dilation(~bg, iterations=5)); items = []
    for i, sl in enumerate(nd.find_objects(lab), 1):
        m = (lab[sl] == i) & ~bg[sl]
        if m.sum() > 40:
            ys, xs = np.nonzero(m); items.append((sl[0].start + ys.mean(), sl[1].start + xs.mean(), m))
    rows = {}
    for it in items:
        rows.setdefault(int(it[0] // 150), []).append(it)
    rows = [sorted(v, key=lambda t: t[1]) for _, v in sorted(rows.items())]
    assert len(rows) >= 2 and len(rows[0]) == 4 and len(rows[1]) == 4, [len(r_) for r_ in rows]
    out = []
    for row in rows[:2]:
        px = np.concatenate([src[int(cy) - 80:int(cy) + 80, int(cx) - 80:int(cx) + 80][~bg[int(cy) - 80:int(cy) + 80, int(cx) - 80:int(cx) + 80]] for cy, cx, _ in row])
        q = Image.fromarray(px.reshape(-1, 1, 3).astype('uint8')).quantize(colors=5, method=Image.Quantize.MEDIANCUT)
        pal = np.array(q.getpalette()[:15], float).reshape(-1, 3)
        out.append([reduce_pose(src, bg, cy, cx, GLINT_WIN, GLINT_K, pal, 0.25) for cy, cx, _ in row])
    return out, [(int(cy), int(cx)) for row in rows[:2] for cy, cx, _ in row]


def glint_frames(poses, spots, ts=range(GLINT_PHASES)):
    frames = []
    for t in ts:
        f = np.zeros((H, W, 4), 'uint8')
        for x, y, off, fam in spots:
            u = (t + off) % GLINT_PHASES
            if u < len(GLINT_SEQ):
                paste(f, poses[fam][GLINT_SEQ[u]], x, y)
        frames.append(f)
    return frames


# ---------------------------------------------------------------- ORA et Ground
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
    o.update(Name={'DefaultText': 'Entree Grotte de cristal - sud vers nord (4:3)', 'LocalTexts': {}}, AssetName=ASSET,
             Released=False, TexSize=1, Music='', EdgeView=1, ViewCenter=None, ViewOffset={'X': 0, 'Y': 0},
             ActiveChar=None, Status={}, Layers=layers,
             Background={'$type': 'RogueEssence.Dungeon.LayeredBG, RogueEssence', 'Layers': []},
             Comment='PMDO 0.8.12. Rendu genere 4:3 reference sur le rip Waterfall Cave (salle du joyau) ; bassins facon Metano '
                     'aux couleurs exactes du rip, scintillements Metano natifs, eclats de cristaux generes. '
                     'Collisions de base a verifier. Seuil non raccorde. Biome choisi par l agent.')
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
  <Name>Entree Grotte de cristal sud-nord 4:3 - Atelier 0.8.12</Name>
  <Author>meromoonmeri</Author>
  <Description>Projet d'edition : grotte de cristal generee au format 4:3 (ref. rip Waterfall Cave, salle du joyau), bassins facon Metano, eclats de cristaux animes. Pas une aventure jouable.</Description>
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
    root = ET.Element('image', w=str(W), h=str(H), name='Entree Grotte de cristal sud-nord V1 (ECC1)')
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
    ANIMS = ['eau', 'scintillements', 'eclats']
    if OUT.exists():
        for d in ['calques', 'animation', 'poses', 'masques', 'review']:
            shutil.rmtree(OUT / d, ignore_errors=True)
    for d in ['calques', 'poses', 'masques', 'review'] + [f'animation/{x}' for x in ANIMS]:
        (OUT / d).mkdir(parents=True, exist_ok=True)
    a = rgb(RAW / 'decor_magenta.png'); f = rgb(RAW / 'sol_complet.png'); ref = rgb(REF)
    assert a.shape[:2] == f.shape[:2] == (SRC[1], SRC[0])
    m = classify(a)
    order = ['water', 'grotte', 'cristaux', 'racines', 'vide', 'fond', 'rochers', 'stalactites', 'sol']
    ex, cols = down_class(a, m, order)
    water = ex['water']
    layers = {'sol_complet': rgba(down_full(f), ~water)}
    for k in STATIC:
        layers[k] = rgba(cols[k], ex[k])
    q = {}
    for keys, n in PALETTE_GROUPS.values():
        q.update(quantize_group({k: layers[k] for k in keys}, n))
    layers = q
    for k, v in ex.items():
        Image.fromarray((v * 255).astype('uint8')).save(OUT / 'masques' / f'{PFX}_masque_{k}.png')
    land = np.zeros((H, W), bool)
    for k in STATIC:
        land |= layers[k][..., 3] == 255
    visible = water & ~land
    wf, dist = UL.lake_water(water, visible)                            # structure Métano, couleurs du rip
    fams = BM.sparkle_families(); taken = np.zeros((H, W), bool)
    sf = [np.zeros((H, W, 4), 'uint8') for _ in range(WATER_PHASES)]; sparkles = []
    for fi, (name, frames) in enumerate(fams.items()):
        hh, ww = frames[0].shape[:2]
        for (y, x) in place(visible & (dist > 4), (hh, ww), 3, 61 + fi, taken, core=8):
            sparkles.append({'famille': name, 'xy': [x, y]})
            for t in range(WATER_PHASES):
                mm = frames[t][..., 3] > 0; sf[t][y:y+hh, x:x+ww][mm] = frames[t][mm]
    for arr in sf:
        arr[~visible] = 0
    # Éclats : sur les plus gros cristaux, chronologies décalées, famille cyan / rose alternée.
    poses, pose_xy = glint_poses(RAW / 'eclats_poses.png')
    for fi, fam in enumerate(poses):
        for i, p in enumerate(fam):
            Image.fromarray(p).save(OUT / 'poses' / f'{PFX}_eclat_{"cyan" if fi == 0 else "rose"}_{i}.png')
    cl, n = nd.label(ex['cristaux']); sizes = nd.sum(ex['cristaux'], cl, range(1, n + 1))
    big = sorted(range(n), key=lambda i: -sizes[i])[:GLINT_N]
    cms = nd.center_of_mass(ex['cristaux'], cl, [i + 1 for i in big])
    spots = [(int(round(cx)), int(round(cy)) - 2, (k * 11) % GLINT_PHASES, k % 2) for k, (cy, cx) in enumerate(cms)]
    eclats = glint_frames(poses, spots)
    anim = {'eau': (wf, WATER_TICKS), 'scintillements': (sf, WATER_TICKS), 'eclats': (eclats, GLINT_TICKS)}
    order_names = ['eau', 'scintillements', 'sol_complet'] + STATIC + ['eclats']
    stack_named, layer_list = [], []
    for i, nm in enumerate(order_names):
        if nm in anim:
            frames, ticks = anim[nm]
            for t, fr in enumerate(frames):
                Image.fromarray(fr).save(OUT / 'animation' / nm / f'{PFX}_{i:02d}_{nm}_f{t:02d}.png')
            layer_list.append({'file': f'animation/{nm}/{PFX}_{i:02d}_{nm}_fNN.png', 'phases': len(frames), 'ticks': ticks})
        else:
            frames, ticks = [layers[nm]], 60
            Image.fromarray(layers[nm]).save(OUT / 'calques' / f'{PFX}_{i:02d}_{nm}.png')
            layer_list.append({'file': f'calques/{PFX}_{i:02d}_{nm}.png', 'phases': 1, 'ticks': 60})
        stack_named.append((nm, frames, ticks))
    # Collisions : sol de galets praticable ; petits cristaux posés sur le sol (< 120 px) traversables.
    cr = layers['cristaux'][..., 3] == 255; crl, cn = nd.label(cr)
    csz = nd.sum(cr, crl, range(1, cn + 1)) if cn else []
    small_cr = np.isin(crl, [i + 1 for i, v in enumerate(csz) if v < 120])
    walk_px = (layers['sol'][..., 3] == 255) | small_cr
    blocked = cell_grid(~walk_px); gh_, gw_ = blocked.shape
    sol = layers['sol'][..., 3] == 255
    pxs = np.nonzero(sol[H - 8])[0]; med = int(np.median(pxs)) // 8
    ecol = min((c for c in range(gw_ - 1) if not blocked[gh_ - 2:, c:c + 2].any()), key=lambda c: abs(c - med))
    entry_px = [ecol * 8, H - 16]
    ty, tx_ = np.nonzero(ex['grotte']); tcx = int(tx_.mean())
    free = [(y, x) for y in range(gh_ - 1) for x in range(gw_ - 1) if not blocked[y:y + 2, x:x + 2].any()]
    ty0, tx0 = min(free, key=lambda p: (p[0] * 8 - 0) + abs(p[1] * 8 + 8 - tcx) * 2)
    threshold_px = [tx0 * 8, ty0 * 8]
    ok, explored = v1.reachable(blocked, (entry_px[1] // 8, entry_px[0] // 8), (ty0, tx0))
    assert ok, 'pas de chemin 16x16'

    def scene(tick):
        im = Image.new('RGBA', (W, H))
        for _, frames, ticks in stack_named:
            im.alpha_composite(Image.fromarray(frames[(tick // ticks) % len(frames)]))
        return im
    step = 5
    scenes = [scene(t) for t in range(0, LOOP_TICKS, step)]
    scenes[0].save(OUT / 'review' / f'{PFX}_scene_t000.png')
    scenes[0].save(OUT / 'review' / f'{PFX}_scene_animee.webp', save_all=True, append_images=scenes[1:],
                   duration=round(step * 1000 / 60), loop=0, lossless=True)
    col = scenes[0].copy(); ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(ov)
    for y, x in zip(*np.nonzero(blocked)):
        dr.rectangle([x*8, y*8, x*8+7, y*8+7], fill=(220, 40, 40, 90))
    for (qx, qy), c in ((entry_px, (255, 230, 40, 255)), (threshold_px, (60, 220, 255, 255))):
        dr.rectangle([qx, qy, qx + 15, qy + 15], outline=c, width=2)
    col.alpha_composite(ov); col.save(OUT / 'review' / f'{PFX}_collisions_marqueurs.png')
    sheet = Image.new('RGBA', (4 * 64, 2 * 64), (*WPAL['bande'], 255))
    for fi, fam in enumerate(poses):
        for i, p in enumerate(fam):
            im = Image.fromarray(p); sheet.alpha_composite(im.resize((im.width * 4, im.height * 4), Image.Resampling.NEAREST), (i * 64 + 4, fi * 64 + 4))
    sheet.save(OUT / 'review' / f'{PFX}_planche_poses.png')
    write_ora(OUT / f'{PFX}_entree_crystal_cave_calques.ora',
              {f'{i:02d}_{t}' + ('_f00' if len(fr) > 1 else ''): fr[0] for i, (t, fr, _) in enumerate(stack_named)})
    counts = ground_project([(t.replace('_', ' ') + (f' {len(fr)} phases' if len(fr) > 1 else ''), fr, tk)
                             for t, fr, tk in stack_named], blocked, entry_px, threshold_px, gfx, tools)
    fid = fidelity(a, ref)
    final_fid = {}
    for k, nm in (('sol_galets', 'sol'), ('roche', 'rochers'), ('fond', 'fond')):
        lay = layers[nm]; px = lay[lay[..., 3] == 255][:, :3].astype(float)
        sel = materials(px.reshape(-1, 1, 3))[k][:, 0]
        px = px[sel] if sel.sum() > 50 else px
        final_fid[k] = {'calque': nm, 'rgb': [round(float(v), 1) for v in px.mean(0)],
                        'distance_rip': round(float(np.linalg.norm(px.mean(0) - np.array(fid[k]['rip_rgb']))), 1)}
    manifest = {
        'lot': 'entree_crystal_cave_sud_nord_v1', 'prefix': PFX, 'format': '4:3 vaste', 'size_px': [W, H],
        'grid_8px': [W // 8, H // 8], 'base': 'branche de session (EMF1/EUL1 pour les utilitaires) ; aucun emprunt aux branches soeurs',
        'biome': 'Grotte de cristal (salle du joyau de Waterfall Cave), choisie par l agent (« passe a la suite »)',
        'method': 'textures canoniques = rendu genere REFERENCE : rip passe au generateur ; decor complet sur magenta '
                  '(bassins = magenta), sol complet edite depuis le decor, planche d eclats sur magenta',
        'reference_da': {'file': REF.name, 'sha256': sha(REF), 'titre': 'Salle du joyau de Waterfall Cave (PMD Explorers)'},
        'generation': GEN,
        'raw_inputs': [{'file': f'source/entree_crystal_cave_sud_nord_v1/bruts/{g["file"]}', 'sha256': sha(RAW / g['file']),
                        'size': list(Image.open(RAW / g['file']).size)} for g in GEN],
        'fidelite_rip': {'methode': 'moyenne RGB par matiere, meme classifieur pixel sur le rip et sur le brut ; distance euclidienne',
                         'brut': fid, 'calques_finaux': final_fid,
                         'eau': 'couleurs EXACTES du rip (test : sous-ensemble des couleurs du rip)'},
        'normalization': {'scale': JM.SCALE, 'scaled': [JM.SCALED_W, H], 'crop_x': [JM.CROP_X, JM.SCALED_W - W - JM.CROP_X],
                          'methode': 'moyenne ponderee par classe (BOX), attribution exclusive par poids maximal',
                          'palettes': {g: {'calques': k, 'couleurs': n} for g, (k, n) in PALETTE_GROUPS.items()}},
        'segmentation': 'eau = nappes magenta > 5000 px dilatees 3 px ; fond = marron (r>g+25, lum<70) moitie haute ; vide = '
                        'aplat ardoise du bas (ecart-type local < 1,5) ; racines = rouge sombre du bas ; tunnel = lum<34 haut-centre ; '
                        'cristaux = satures hors bleu ou tres clairs ; sol = b-r lisse > 72, lum lissee 85-135, grande composante ; '
                        f'le reste = roche, separee en stalactites (y < {ROCK_SPLIT_Y} dans le decor) et rochers',
        'layers': layer_list,
        'water': {'phases': WATER_PHASES, 'frame_length_ticks': WATER_TICKS, 'couleurs': {k: list(v) for k, v in WPAL.items()},
                  'modele': 'structure et cadence riviere Metano (lake_water d EUL1), couleurs EXACTES du rip, sans liseré clair',
                  'origine': 'pixels recalcules, pas de tuiles natives'},
        'sparkles': {'source': 'source/eau_metano/natifs/Metano_Town_River_Sparkles.tile', 'placements': sparkles,
                     'origine': 'pixels et couleurs Metano NATIFS inchanges (aplat de surface retire)'},
        'eclats': {'poses': [len(p) for p in poses], 'centres_planche': pose_xy, 'reduction': f'fenetre {GLINT_WIN} px -> {GLINT_WIN // GLINT_K} px',
                   'sequence': GLINT_SEQ, 'points': [list(s_) for s_ in spots], 'phases': GLINT_PHASES,
                   'frame_length_ticks': GLINT_TICKS,
                   'origine': 'dessin GENERE (5 couleurs par famille) ; placement sur les cristaux et chronologie crees par nous'},
        'scene_loop_ticks': LOOP_TICKS,
        'access': {'entry_px': entry_px, 'threshold_px': threshold_px, 'path_found_16x16': ok, 'cells_explored': explored,
                   'blocked_cells': int(blocked.sum()), 'total_cells': int(blocked.size), 'walkable_cells': int((~blocked).sum()),
                   'rule': 'case bloquee si > 25 % hors sol de galets (petits cristaux < 120 px traversables)',
                   'seuil': 'case libre la plus au nord, au plus pres de l axe du tunnel ; le tunnel est sur la paroi du fond, '
                            'derriere la rangee de rochers : le raccord reste a scripter'},
        'pmdo': {'target': '0.8.12', 'asset': ASSET, 'namespace': NAMESPACE, 'tiles_per_bank': counts, 'banks': list(counts),
                 'runtime_tested': False, 'warp': 'aucun'},
        'art_approved': False,
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    shutil.copyfile(OUT / 'manifest.json', STAGE / 'manifest.json')
    print(json.dumps({'sparkles': len(sparkles), 'entry': entry_px, 'threshold': threshold_px, 'blocked': int(blocked.sum()),
                      'walkable': int((~blocked).sum()), 'glints': len(spots), 'fidelite': {k: v['distance'] for k, v in fid.items()},
                      'final': {k: v['distance_rip'] for k, v in final_fid.items()}, 'tiles': sum(counts.values())}, indent=1))


if __name__ == '__main__':
    build()
