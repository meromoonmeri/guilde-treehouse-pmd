"""Entrée Foggy Forest — clairière SANS tentes, sud -> nord V2 (EFF2) — format 4:3 vaste (768 x 576 px).

Demande : « la version sans tente stp et que les arbres aient leur propre calque, ombre etc ; même méthode avec
preview html ». Mêmes bruts générés qu'EFF1 (rendu généré RÉFÉRENCÉ sur Foggy_Forest_Base_Camp_TDS.png), aucune
nouvelle génération ; EFF1 reste intact.
- Tentes retirées : leur emprise (boîte de chaque tente, dilatée 3 px) est remplacée AVANT segmentation par les pixels
  du sol complet généré (herbe pâle éditée depuis le même décor, même cadrage) ; la segmentation est ensuite relancée.
- Arbres séparés en trois calques : ombres portées (aplat sombre lisse sous les houppiers), troncs et racines
  (brun), houppiers (le reste). Calques : sol complet, herbe, chemin, sous-bois, buissons, rochers, ombres des
  arbres, troncs, houppiers, grotte ; animations eau Métano, scintillements natifs, brume tramée (comme EFF1).
Lancer : .venv/bin/python source/entree_foggy_forest_sud_nord_v2/build.py
"""
from pathlib import Path
import hashlib, importlib.util, io, json, shutil, uuid, zipfile

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
RAW = HERE.parent / 'entree_foggy_forest_sud_nord_v1' / 'bruts'          # bruts EFF1 réutilisés
REF = R / 'Foggy_Forest_Base_Camp_TDS.png'
OUT = R / 'renders/entree_foggy_forest_sud_nord_v2'
STAGE = R / '.cache/entree_foggy_forest_sud_nord_v2/entree_foggy_forest_sans_tentes'
NAMESPACE = 'entree_foggy_forest_sans_tentes'
ASSET = 'eff2_entree_foggy_forest_sans_tentes'
PFX = 'EFF2'
W, H = 768, 576
SRC = (1200, 896)
WATER_PHASES, WATER_TICKS = 4, 10
FOG_PHASES, FOG_TICKS = 48, 5
LOOP_TICKS = 240
FOG_K = 4                                   # réduction des nappes x1/4
FOG_AMP = 20                                # dérive +/- 20 px
GEN = [
    {'file': 'decor_magenta.png', 'images': ['Foggy_Forest_Base_Camp_TDS.png'], 'prompt':
     'Use EXACTLY the same textures, palette and pixel-art style as the reference image (Pokemon Mystery Dungeon '
     'Explorers of Sky, Foggy Forest base camp): same pale mint-green short grass clearing, same darker striped green '
     'grass around, same beige-brown dirt path with ragged grass edges, same big round dark green trees with bright '
     'yellow-green highlights and brown roots, same pink Wigglytuff tents with ears and wooden stakes, same small '
     'pinkish-grey rocks and small dark green bushes, small flowers. Make a NEW, larger top-down map. WIDE LANDSCAPE 4:3, '
     'zoomed out so the area feels vast. Layout: the player arrives at the SOUTH (bottom edge center) on the dirt path; '
     'the path goes NORTH through a wide pale-green camp clearing with four pink tents spread around it, and continues '
     'north up to a dark shadowy opening between dense trees at the top center (the dungeon entrance). Dense trees fill '
     'the left and right sides and the top. A small calm pond on the right side of the clearing, away from the path. '
     'IMPORTANT: the pond water surface is filled with flat pure magenta #FF00FF, no ripples. No characters, no text, '
     'no UI, no border.'},
    {'file': 'sol_complet.png', 'images': ['source/entree_foggy_forest_sud_nord_v1/bruts/decor_magenta.png'], 'prompt':
     'Same image, same size and pixel-art style, but showing only the plain pale mint-green short grass ground '
     'everywhere (trees, path, tents, rocks, bushes, cave and pink pond all removed and replaced by that same grass).'},
    {'file': 'brume_poses.png', 'images': ['Foggy_Forest_Base_Camp_TDS.png'], 'prompt':
     'Pixel-art sprite sheet on a flat pure magenta #FF00FF background, in the style and soft colors of the reference '
     'image (Pokemon Mystery Dungeon Explorers of Sky, Foggy Forest). 2 rows of 4 separate soft pale white-green fog '
     'wisps / mist clouds, each a horizontally elongated puffy shape with a lighter core and dithered edges, different '
     'shapes. Sprites well separated with wide magenta spacing, no text, no grid lines.',
     'note': 'rendue en 4 rangees x 2 colonnes (896 x 1183) : poses extraites par composantes'},
]


def loadmod(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


EM = loadmod('emf1_build', R / 'source/entree_mystifying_forest_sud_nord_v1/build.py')   # utilitaires EMF1
V2, V1, JM, BM = EM.V2, EM.V1, EM.JM, EM.BM
assert (JM.W, JM.H, JM.SRC) == (W, H, SRC)
keep_large, place, cell_grid, close_ = V1.keep_large, V1.place, V1.cell_grid, V1.close_
down_class, down_full, rgba, quantize_group = V1.down_class, V1.down_full, V1.rgba, V1.quantize_group
open_, sha, rgb, paste = EM.open_, EM.sha, EM.rgb, EM.paste
PAL = BM.PAL
PALETTE_GROUPS = {'terrain': (['sol_complet', 'herbe', 'chemin', 'sous_bois', 'buissons'], 96),
                  'houppiers': (['houppiers'], 40), 'troncs': (['troncs'], 16), 'ombres': (['ombres_arbres'], 12), 'rochers': (['rochers'], 16),
                  'grotte': (['grotte'], 16)}
STATIC = ['herbe', 'chemin', 'sous_bois', 'buissons', 'rochers', 'ombres_arbres', 'troncs', 'houppiers', 'grotte']


def is_mag(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return (r > 180) & (b > 180) & (g < 150)


# ---------------------------------------------------------------- fidélité au rip (même classifieur des deux côtés)
def materials(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]; lum = a @ [.299, .587, .114]; mag = is_mag(a)
    path = (r >= g - 2) & (r - b > 25) & (r - b < 60) & (lum > 130) & (lum < 205) & (np.abs(r - g) < 20) & ~mag
    pale = (g > r + 20) & (g > b + 25) & (lum > 160) & ~mag
    dark = (g > r + 45) & (g > b + 35) & (lum > 110) & (lum < 160) & ~mag
    pink = (r > g + 40) & (r > b + 30) & (r > 170) & ~mag
    return {'herbe_camp': pale, 'chemin': path, 'sous_bois': dark, 'tentes': pink}


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
    L = nd.uniform_filter(lum, 9); GR = nd.uniform_filter(g - r, 11)
    # Mare : magenta et sa frange rosée antialiasée, dilatés 3 px.
    water = nd.binary_dilation(is_mag(a) | ((r > 200) & (b > 170) & (g < 185) & (r - g > 40) & (b - g > 20)), iterations=3)
    # Grotte (haut-centre) : bouche sombre (mesurée (78,88,97)) + encadrement de pierre grise peu saturée.
    cave_zone = (yy < 200) & (xx > 500) & (xx < 700)
    mouth = cave_zone & (lum < 100) & (sat < 30)
    mouth = nd.binary_fill_holes(keep_large(close_(mouth, 2), 800))
    stone = cave_zone & (sat < 45) & (lum < 175) & (np.abs(g - r) < 30) & nd.binary_dilation(mouth, iterations=40)
    cave = nd.binary_fill_holes(close_(keep_large(close_(stone | mouth, 3), 800), 3)) & cave_zone
    # Chemin (mesuré (185,178,148)) : beige, grande composante.
    path = (r >= g - 2) & (r - b > 22) & (np.abs(r - g) < 22) & (lum > 125) & (lum < 215) & ~water & ~cave
    path = nd.binary_fill_holes(keep_large(open_(close_(path, 2), 1), 5000)) & ~water & ~cave
    # Tentes et rochers : roses (tentes (232,185,190)) ; composantes fermées, trous (portes, hublots) comblés.
    pink = (r > g + 25) & (r > b + 12) & ~water & ~cave & ~path
    pk = nd.binary_fill_holes(close_(pink, 4)); lab, n = nd.label(pk); sizes = nd.sum(pk, lab, range(1, n + 1))
    tents = np.isin(lab, [i + 1 for i, v in enumerate(sizes) if v >= 2500])
    # Porte blanche et piquets : on englobe la boîte convexe basse de chaque tente (fermeture forte puis bouchage).
    # Porte blanche, piquets, ombre : dans la boîte de chaque tente (+10 px en bas), tout ce qui n'est pas herbe pâle.
    paleg = (g > r + 18) & (g > b + 22) & (lum > 165)
    tl, tn = nd.label(tents); t2 = tents.copy()
    for sl in nd.find_objects(tl):
        ys, xs = slice(sl[0].start, min(hh, sl[0].stop + 10)), slice(max(0, sl[1].start - 4), min(ww, sl[1].stop + 4))
        t2[ys, xs] |= ~paleg[ys, xs] & ~path[ys, xs] & ~water[ys, xs]
    tents = nd.binary_fill_holes(open_(close_(t2, 2), 1))
    rocks = np.isin(lab, [i + 1 for i, v in enumerate(sizes) if 40 <= v < 2500]) & ~tents
    rocks = nd.binary_dilation(rocks, iterations=1) & ~tents & ~path & ~water
    # Herbe pâle du camp (mesurée (165,204,156)) : critère régional, composantes reliées au chemin.
    clear = (L > 168) & (GR > 18) & ~path & ~water & ~cave & ~tents & ~rocks
    clear = open_(close_(clear, 2), 2)
    cl, _ = nd.label(clear); touch = set(np.unique(cl[nd.binary_dilation(path, iterations=4) & clear])) - {0}
    walk = keep_large(np.isin(cl, list(touch)), 5000)
    U = close_(walk | path, 3)
    holes = nd.binary_fill_holes(U) & ~U; hl, _ = nd.label(holes)
    hs = nd.sum(holes, hl, range(1, hl.max() + 1)) if hl.max() else []
    enclosed = np.isin(hl, [i + 1 for i, v in enumerate(hs) if v < 6000])     # buissons et fleurs, dans le camp
    walk = U & ~path & ~water & ~cave & ~tents & ~rocks
    # Buissons et fleurs : trous fermés assez sombres (lum lissée < 160) et > 150 px ; anneau d'ombre des rochers
    # rendu aux rochers ; le reste (touffes le long du chemin) redevient herbe praticable.
    enclosed &= ~tents & ~rocks & ~water & ~cave & ~path
    rocks |= enclosed & nd.binary_dilation(rocks, iterations=4)
    el, _ = nd.label(enclosed & ~rocks); keep = []
    for i, sl in enumerate(nd.find_objects(el), 1):
        c = el[sl] == i
        if c.sum() > 150 and L[sl][c].mean() < 160:
            keep.append(i)
    bushes = np.isin(el, keep)
    walk |= enclosed & ~rocks & ~bushes
    rest = ~(water | cave | path | walk | tents | rocks | bushes)
    # Herbe pâle isolée (au nord de la grotte, entre une tente et la lisière) : calque herbe, pas arbres.
    iso = keep_large(open_(rest & (L > 168) & (GR > 18), 2), 300)
    walk |= iso; rest &= ~iso
    # Sous-bois (herbe sombre rayée, g-r ~ 65) contre houppiers (g-r ~ 24) : g-r lissé 11 px.
    trees = rest & (GR < 42)
    trees = nd.binary_fill_holes(keep_large(open_(close_(trees, 3), 2), 1500)) & rest
    under = rest & ~trees
    # Petites îles sombres isolées dans le camp (< 6000 px, loin des bords) : buissons, pas sous-bois.
    ul, _ = nd.label(under)
    for i, sl in enumerate(nd.find_objects(ul), 1):
        c = ul[sl] == i
        if c.sum() < 6000 and sl[0].start > 0 and sl[1].start > 0 and sl[0].stop < hh and sl[1].stop < ww:
            bushes[sl] |= c; under[sl] &= ~c
    return dict(water=water, herbe=walk, chemin=path, sous_bois=under, buissons=bushes, rochers=rocks, tentes=tents,
                arbres=trees, grotte=cave, bouche=mouth)

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
    o.update(Name={'DefaultText': 'Entree Foggy Forest - clairiere sans tentes, sud vers nord (4:3)', 'LocalTexts': {}}, AssetName=ASSET,
             Released=False, TexSize=1, Music='', EdgeView=1, ViewCenter=None, ViewOffset={'X': 0, 'Y': 0},
             ActiveChar=None, Status={}, Layers=layers,
             Background={'$type': 'RogueEssence.Dungeon.LayeredBG, RogueEssence', 'Layers': []},
             Comment='PMDO 0.8.12. Rendu genere 4:3 reference sur le rip Foggy Forest Base Camp ; mare facon Metano sans '
                     'liseré (couleurs Metano exactes), scintillements Metano natifs, brume generee tramee. '
                     'Collisions de base a verifier. Seuil non raccorde. Biome demande par l utilisateur.')
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
  <Name>Entree Foggy Forest sans tentes sud-nord 4:3 - Atelier 0.8.12</Name>
  <Author>meromoonmeri</Author>
  <Description>Projet d'edition : clairiere de foret generee sans tentes, arbres en calques houppiers/troncs/ombres, au format 4:3 (ref. rip Foggy Forest Base Camp), mare facon Metano, brume animee. Pas une aventure jouable.</Description>
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




# ---------------------------------------------------------------- V2 : retrait des tentes, arbres en calques
def remove_tents(a, f):
    """Emprise de chaque tente d'EFF1 (même classifieur), dilatée 3 px, recouverte par de l'herbe du camp recopiée
    du MÊME décor généré (décalage le plus proche où toute l'emprise tombe sur l'herbe pâle, sans retournement).
    Le sol complet généré (1er essai) avait une texture plus striée : ses pièces se voyaient comme des rustines."""
    m = classify(a); t = nd.binary_dilation(m['tentes'], iterations=3); ok = m['herbe'] & ~t
    lab, n = nd.label(t); b = a.copy(); patches = []
    hh, ww = t.shape
    for i, sl in enumerate(nd.find_objects(lab), 1):
        c = lab[sl] == i; best = None
        for dy in range(-240, 241, 4):
            for dx in range(-400, 401, 4):
                y0, x0 = sl[0].start + dy, sl[1].start + dx
                y1, x1 = y0 + c.shape[0], x0 + c.shape[1]
                if (dy == 0 and dx == 0) or y0 < 0 or x0 < 0 or y1 > hh or x1 > ww:
                    continue
                if ok[y0:y1, x0:x1][c].all() and (best is None or dy * dy + dx * dx < best[0]):
                    best = (dy * dy + dx * dx, dy, dx)
        assert best, 'pas de source d herbe pour la tente %d' % i
        _, dy, dx = best
        src = a[sl[0].start + dy:sl[0].stop + dy, sl[1].start + dx:sl[1].stop + dx]
        b[sl][c] = src[c]; patches.append({'boite': [sl[1].start, sl[0].start, sl[1].stop, sl[0].stop], 'decalage': [dx, dy]})
    return b, {'pixels_remplaces': int(t.sum()), 'source': 'herbe du camp du meme decor genere, recopiee sans retournement',
               'dilatation_px': 3, 'pieces': patches}


def split_trees(a, m):
    """Zone boisée (arbres + sous-bois d'EFF1) redécoupée par couleur lissée 5 px. Mesures sur le décor : sous-bois
    (99,164,111) g-r 65 ; houppier (107,137,87) b/g 0,64 ; ombre portée (100,123,94) b/g 0,76, g-r 23, aplat lisse ;
    tronc et racines (154,139,104) bruns.
    - ombres : b/g > 0,72, g-r < 42, lum < 140 ; composantes > 400 px (les petites taches sombres dans le feuillage
      restent au houppier) ;
    - troncs : r > g + 6 et r > b + 30, composantes >= 15 px au contact d'une ombre ou d'un houppier ;
    - sous-bois : g-r >= 45 et b/g > 0,6 ; trous < 300 px dans un houppier rendus au houppier ;
    - houppiers : le reste ; îlots < 300 px rendus au sous-bois ; liserés de moins de 5 px (ouverture 2) rendus au sous-bois."""
    zone = m.pop('arbres') | m['sous_bois']
    x = a.astype(float); r, g, b = x[..., 0], x[..., 1], x[..., 2]
    BG = nd.uniform_filter(b / np.maximum(g, 1), 5); GR = nd.uniform_filter(g - r, 5)
    L = nd.uniform_filter(x @ [.299, .587, .114], 5)
    sh = zone & (BG > 0.72) & (GR < 42) & (L < 140)
    gr = zone & (GR >= 45) & (BG > 0.6) & ~sh
    tr = zone & (r > g + 6) & (r > b + 30)
    sh &= ~tr; gr &= ~tr
    can = zone & ~sh & ~gr & ~tr
    small_sh = sh & ~keep_large(sh, 400); sh &= ~small_sh; can |= small_sh
    tl, _ = nd.label(tr); near = nd.binary_dilation(sh | can, iterations=2)
    sizes = nd.sum(tr, tl, range(1, tl.max() + 1)) if tl.max() else []
    touch = set(np.unique(tl[near & tr])) - {0}
    good = np.isin(tl, [i + 1 for i, v in enumerate(sizes) if v >= 15 and (i + 1) in touch])
    can |= tr & ~good; tr = good
    holes = gr & ~keep_large(gr, 300); gr &= ~holes; can |= holes
    thin = (can & ~open_(can, 2)) | (sh & ~open_(sh, 2))       # liserés fins (bord sombre de la clairière)
    thin &= ~nd.binary_dilation(tr, iterations=2)
    can &= ~thin; sh &= ~thin; gr |= thin
    isl = can & ~keep_large(can, 300); can &= ~isl; gr |= isl
    isl = sh & ~keep_large(sh, 400); sh &= ~isl; gr |= isl
    m['sous_bois'] = gr; m['ombres_arbres'] = sh; m['troncs'] = tr; m['houppiers'] = can
    return m


# ---------------------------------------------------------------- brume générée
def fog_poses(path):
    """8 nappes de la planche (composantes sur magenta), réduites x1/FOG_K par moyenne de blocs, 6 couleurs."""
    src = rgb(path); bg = is_mag(src) | ((src[..., 0] - src[..., 1] > 50) & (src[..., 2] - src[..., 1] > 50))
    lab, n = nd.label(nd.binary_dilation(~bg, iterations=4)); items = []
    for i, sl in enumerate(nd.find_objects(lab), 1):
        m = (lab[sl] == i) & ~bg[sl]
        if m.sum() > 2000:
            items.append((sl[0].start, sl[1].start, sl, m))
    items.sort(key=lambda t: (t[0] // 200, t[1]))
    px = np.concatenate([src[sl][m] for *_, sl, m in items])
    q = Image.fromarray(px.reshape(-1, 1, 3).astype('uint8')).quantize(colors=6, method=Image.Quantize.MEDIANCUT)
    pal = np.array(q.getpalette()[:18], float).reshape(-1, 3)
    out = []
    for *_, sl, m in items:
        s = src[sl].astype(float); hh, ww = (m.shape[0] // FOG_K) * FOG_K, (m.shape[1] // FOG_K) * FOG_K
        mb = m[:hh, :ww].reshape(hh // FOG_K, FOG_K, ww // FOG_K, FOG_K); cov = mb.mean((1, 3))
        col = (s[:hh, :ww] * m[:hh, :ww, None]).reshape(hh // FOG_K, FOG_K, ww // FOG_K, FOG_K, 3).sum((1, 3))
        col /= np.maximum(mb.sum((1, 3)), 1)[..., None]
        o = np.zeros((*cov.shape, 4), 'uint8')
        o[..., :3] = pal[((col[..., None, :] - pal[None, None]) ** 2).sum(-1).argmin(-1)]; o[..., 3] = 255
        o[cov < 0.5] = 0; out.append(o)
    return out, pal


def fog_frames(poses, wisps, ts=range(FOG_PHASES)):
    """Dérive sinusoïdale fermée sur 48 phases ; trame en damier FIXE sur la carte (alpha 0/255)."""
    yy, xx = np.mgrid[:H, :W]; checker = (xx + yy) % 2 == 0
    frames = []
    for t in ts:
        f = np.zeros((H, W, 4), 'uint8')
        for k, (x0, y0, ph) in enumerate(wisps):
            u = 2 * np.pi * t / FOG_PHASES + ph
            paste(f, poses[k % len(poses)], x0 + FOG_AMP * np.sin(u), y0 + 3 * np.sin(2 * u))
        f[~checker] = 0
        frames.append(f)
    return frames


def write_ora(path, layers):
    import xml.etree.ElementTree as ET
    root = ET.Element('image', w=str(W), h=str(H), name='Entree Foggy Forest sans tentes sud-nord V2 (EFF2)')
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
    ANIMS = ['eau', 'scintillements', 'brume']
    if OUT.exists():
        for d in ['calques', 'animation', 'poses', 'masques', 'review']:
            shutil.rmtree(OUT / d, ignore_errors=True)
    for d in ['calques', 'poses', 'masques', 'review'] + [f'animation/{x}' for x in ANIMS]:
        (OUT / d).mkdir(parents=True, exist_ok=True)
    a = rgb(RAW / 'decor_magenta.png'); f = rgb(RAW / 'sol_complet.png'); ref = rgb(REF)
    assert a.shape[:2] == f.shape[:2] == (SRC[1], SRC[0])
    a0 = a; a, notent = remove_tents(a, f)          # a0 : brut intact (fidélité mesurée dessus)
    m = split_trees(a, classify(a)); mouth_full = m.pop('bouche')
    rest_t = m.pop('tentes'); notent['residu_rose_px'] = int(rest_t.sum())   # résidu éventuel -> herbe
    m['herbe'] = m['herbe'] | rest_t
    order = ['water', 'grotte', 'chemin', 'rochers', 'buissons', 'troncs', 'ombres_arbres', 'houppiers', 'sous_bois', 'herbe']
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
    wf, dist = V2.water_phases(water, visible)                          # Métano exactes, sans liseré de rive
    fams = BM.sparkle_families(); taken = np.zeros((H, W), bool)
    sf = [np.zeros((H, W, 4), 'uint8') for _ in range(WATER_PHASES)]; sparkles = []
    for fi, (name, frames) in enumerate(fams.items()):
        hh, ww = frames[0].shape[:2]
        for (y, x) in place(visible & (dist > 4), (hh, ww), 2, 61 + fi, taken, core=8):
            sparkles.append({'famille': name, 'xy': [x, y]})
            for t in range(WATER_PHASES):
                mm = frames[t][..., 3] > 0; sf[t][y:y+hh, x:x+ww][mm] = frames[t][mm]
    for arr in sf:
        arr[~visible] = 0
    # Brume : nappes générées, dérive créée.
    fogs, fog_pal = fog_poses(RAW / 'brume_poses.png')
    assert len(fogs) == 8, len(fogs)
    for i, p in enumerate(fogs):
        Image.fromarray(p).save(OUT / 'poses' / f'{PFX}_brume_{i}.png')
    wisps = [(150, 60, 0.0), (430, 110, 1.3), (690, 70, 2.1), (110, 250, 3.4), (330, 300, 0.7), (560, 230, 4.2),
             (700, 330, 5.0), (200, 420, 2.7), (470, 470, 3.9), (660, 520, 1.8)]
    brume = fog_frames(fogs, wisps)
    anim = {'eau': (wf, WATER_TICKS), 'scintillements': (sf, WATER_TICKS), 'brume': (brume, FOG_TICKS)}
    order_names = ['eau', 'scintillements', 'sol_complet'] + STATIC + ['brume']
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
    # Collisions : herbe du camp + chemin praticables ; tout le reste bloqué.
    walk_px = (layers['herbe'][..., 3] == 255) | (layers['chemin'][..., 3] == 255)
    blocked = cell_grid(~walk_px); gh_, gw_ = blocked.shape
    pth = layers['chemin'][..., 3] == 255
    pxs = np.nonzero(pth[H - 8])[0]; med = int(np.median(pxs)) // 8
    ecol = min((c for c in range(gw_ - 1) if not blocked[gh_ - 2:, c:c + 2].any()), key=lambda c: abs(c - med))
    entry_px = [ecol * 8, H - 16]
    # Seuil : sous la bouche de la grotte (centre de la bouche, premier couple de rangées libres).
    my, mx = np.nonzero(mouth_full); cx = int(mx.mean() * JM.SCALE) - JM.CROP_X
    cave_bottom = int(np.nonzero(ex['grotte'].any(1))[0].max())
    threshold_px = [cx // 8 * 8 - 8, (cave_bottom + 1 + 7) // 8 * 8]
    while blocked[threshold_px[1] // 8:threshold_px[1] // 8 + 2, threshold_px[0] // 8:threshold_px[0] // 8 + 2].any():
        threshold_px[1] += 8
    ok, explored = v1.reachable(blocked, (entry_px[1] // 8, entry_px[0] // 8), (threshold_px[1] // 8, threshold_px[0] // 8))
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
    cw = max(max(p.shape[:2]) for p in fogs) * 2 + 8
    sheet = Image.new('RGBA', (4 * cw, 2 * cw), (90, 150, 100, 255))
    for i, p in enumerate(fogs):
        im = Image.fromarray(p); sheet.alpha_composite(im.resize((im.width * 2, im.height * 2), Image.Resampling.NEAREST),
                                                       ((i % 4) * cw + 4, (i // 4) * cw + 4))
    sheet.save(OUT / 'review' / f'{PFX}_planche_poses.png')
    write_ora(OUT / f'{PFX}_entree_foggy_forest_sans_tentes_calques.ora',
              {f'{i:02d}_{t}' + ('_f00' if len(fr) > 1 else ''): fr[0] for i, (t, fr, _) in enumerate(stack_named)})
    counts = ground_project([(t.replace('_', ' ') + (f' {len(fr)} phases' if len(fr) > 1 else ''), fr, tk)
                             for t, fr, tk in stack_named], blocked, entry_px, threshold_px, gfx, tools)
    fid = fidelity(a0, ref)
    final_fid = {}
    for k, nm in (('herbe_camp', 'herbe'), ('chemin', 'chemin'), ('sous_bois', 'sous_bois')):
        lay = layers[nm]; px = lay[lay[..., 3] == 255][:, :3].astype(float)
        sel = materials(px.reshape(-1, 1, 3))[k][:, 0]
        px = px[sel] if sel.sum() > 50 else px
        final_fid[k] = {'calque': nm, 'rgb': [round(float(v), 1) for v in px.mean(0)],
                        'distance_rip': round(float(np.linalg.norm(px.mean(0) - np.array(fid[k]['rip_rgb']))), 1)}
    manifest = {
        'lot': 'entree_foggy_forest_sud_nord_v2', 'variante_de': 'EFF1 (memes bruts generes), sans tentes, arbres en 3 calques', 'prefix': PFX, 'format': '4:3 vaste', 'size_px': [W, H],
        'grid_8px': [W // 8, H // 8], 'base': 'branche de session (EMF1 pour les utilitaires) ; aucun emprunt aux branches soeurs',
        'biome': 'Foggy Forest Base Camp sans tentes, demande par l utilisateur', 'retrait_tentes': notent,
        'method': 'textures canoniques = rendu genere REFERENCE : rip passe au generateur ; decor complet sur magenta '
                  '(mare = magenta), herbe complete editee depuis le decor, planche de brume sur magenta',
        'reference_da': {'file': REF.name, 'sha256': sha(REF), 'titre': 'Camp de base de Foggy Forest (PMD Explorers)'},
        'generation': GEN,
        'raw_inputs': [{'file': f'source/entree_foggy_forest_sud_nord_v1/bruts/{g["file"]}', 'sha256': sha(RAW / g['file']),
                        'size': list(Image.open(RAW / g['file']).size)} for g in GEN],
        'fidelite_rip': {'methode': 'moyenne RGB par matiere, meme classifieur pixel sur le rip et sur le brut ; distance euclidienne',
                         'brut': fid, 'calques_finaux': final_fid,
                         'note': 'le generateur a rendu une scene plus claire et laiteuse que le rip (voile de brume) : '
                                 'ecarts plus grands que sur les lots precedents, non corriges pour ne pas recolorer'},
        'normalization': {'scale': JM.SCALE, 'scaled': [JM.SCALED_W, H], 'crop_x': [JM.CROP_X, JM.SCALED_W - W - JM.CROP_X],
                          'methode': 'moyenne ponderee par classe (BOX), attribution exclusive par poids maximal',
                          'palettes': {g: {'calques': k, 'couleurs': n} for g, (k, n) in PALETTE_GROUPS.items()}},
        'segmentation': 'eau = magenta et frange rosee dilates 3 px ; grotte = bouche sombre (lum<100, sat<30) et pierre grise '
                        'peu saturee a <= 40 px, zone haut-centre ; chemin = beige (r-b>22, |r-g|<22), grande composante ; '
                        'tentes = roses (r>g+25) >= 2500 px + boite de chaque tente hors herbe pale ; rochers = roses < 2500 px '
                        '+ anneau d ombre ; herbe du camp = lum lissee > 168 et g-r lisse > 18 reliee au chemin ; buissons = '
                        'trous fermes sombres > 150 px et iles sombres isolees ; arbres = g-r lisse 11 px < 42 ; sous-bois = le reste',
        'layers': layer_list,
        'water': {'phases': WATER_PHASES, 'frame_length_ticks': WATER_TICKS,
                  'couleurs': {k: list(v) for k, v in PAL.items() if k != 'clair'},
                  'modele': 'structure et cadence riviere Metano, couleurs Metano EXACTES, sans liseré de rive (water_phases d EWC2)',
                  'origine': 'pixels recalcules, pas de tuiles natives'},
        'sparkles': {'source': 'source/eau_metano/natifs/Metano_Town_River_Sparkles.tile', 'placements': sparkles,
                     'origine': 'pixels et couleurs Metano NATIFS inchanges (aplat de surface retire)'},
        'brume': {'poses': len(fogs), 'tailles_px': [list(p.shape[:2]) for p in fogs], 'reduction': f'x1/{FOG_K}',
                  'palette': [[int(c) for c in p] for p in fog_pal], 'nappes': [list(w_) for w_ in wisps],
                  'derive': f'x0 + {FOG_AMP} sin(2 pi t/48 + phi), y0 + 3 sin(4 pi t/48 + 2 phi)',
                  'trame': 'damier fixe sur la carte ((x+y) pair), alpha 0/255 uniquement (pas de translucidite a premultiplier)',
                  'phases': FOG_PHASES, 'frame_length_ticks': FOG_TICKS,
                  'origine': 'dessin GENERE ; derive, trame et boucle creees par nous (pas une animation officielle)'},
        'scene_loop_ticks': LOOP_TICKS,
        'access': {'entry_px': entry_px, 'threshold_px': threshold_px, 'path_found_16x16': ok, 'cells_explored': explored,
                   'blocked_cells': int(blocked.sum()), 'total_cells': int(blocked.size), 'walkable_cells': int((~blocked).sum()),
                   'rule': 'case bloquee si > 25 % hors herbe du camp et chemin',
                   'seuil': 'devant la bouche de la grotte, au nord'},
        'pmdo': {'target': '0.8.12', 'asset': ASSET, 'namespace': NAMESPACE, 'tiles_per_bank': counts, 'banks': list(counts),
                 'runtime_tested': False, 'warp': 'aucun'},
        'art_approved': False,
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    shutil.copyfile(OUT / 'manifest.json', STAGE / 'manifest.json')
    print(json.dumps({'sparkles': len(sparkles), 'entry': entry_px, 'threshold': threshold_px, 'blocked': int(blocked.sum()),
                      'walkable': int((~blocked).sum()), 'fidelite': {k: v['distance'] for k, v in fid.items()},
                      'final': {k: v['distance_rip'] for k, v in final_fid.items()}, 'tiles': sum(counts.values())}, indent=1))


if __name__ == '__main__':
    build()
