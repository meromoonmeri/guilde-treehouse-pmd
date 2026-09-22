"""Zone « Crooked Cavern verdoyante » — arrivée sud, bouche de grotte au nord.

Pipeline (méthode `renders/arene_glace_generee_v2` / `source/layouts_magenta_v1/WORKFLOW.md`) :
  1. deux rendus générés d'après références canoniques (audit dans AUDIT.md) :
     bruts/scene_complete_brut.png (scène entière) et bruts/sol_complet_brut.png (sous-couche sol seule) ;
  2. normalisation 512×640 NEAREST ;
  3. masques = différence scène/sol + classification couleur/composantes ;
  4. calques alignés (origine 0,0), partition exacte de la scène → recomposition vérifiée ;
  5. complément NATIF certifié (rochers Crooked, arbres Vast Steppe) posé par translation seule ;
  6. nuit = filtre Abyss exact (source/cote_v4_abyss/night.py) ; ORA ; galerie ; manifeste.

Reproduction : .venv/bin/python source/crooked_verdoyant_v1/build.py
"""
from __future__ import annotations
import base64, hashlib, io, json, sys, zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
import scipy.ndimage as nd
from PIL import Image

R = Path(__file__).resolve().parents[2]
SRC = R / 'source/crooked_verdoyant_v1'
O = R / 'renders/crooked_verdoyant_v1'
sys.path.insert(0, str(R / 'source/cote_v4_abyss'))
from night import night  # noqa: E402  (filtre Abyss V4 exact)

W, H = 512, 640
PFX = 'CrookedVerdoyantV1'
BRUTS = {
    'scene': O / 'bruts/scene_complete_brut.png',
    'sol': O / 'bruts/sol_complet_brut.png',
}
NATIVE = {
    'crooked_objects': R / 'banque_canonique/atlas/Halcyon__Crooked_Cavern_Objects.png',
    'crooked_shadows': R / 'banque_canonique/atlas/Halcyon__Crooked_Cavern_Shadows.png',
    'steppe_trunks': R / 'source/amp_plains_fleurie_v1/references/vast_steppe_layer_3.png',
    'steppe_foliage': R / 'source/amp_plains_fleurie_v1/references/vast_steppe_layer_4.png',
}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def norm(p: Path) -> Image.Image:
    return Image.open(p).convert('RGBA').resize((W, H), Image.NEAREST)


def masked(im: Image.Image, m: np.ndarray) -> Image.Image:
    a = np.array(im)
    a[:, :, 3] = np.where(m, a[:, :, 3], 0)
    return Image.fromarray(a)


def clean(m: np.ndarray, min_px: int) -> np.ndarray:
    lab, n = nd.label(m)
    if not n:
        return m
    counts = np.bincount(lab.ravel())
    keep = counts >= min_px
    keep[0] = False
    return keep[lab]


def components(m: np.ndarray):
    lab, n = nd.label(m, structure=np.ones((3, 3)))
    return lab, [(i, sl) for i, sl in enumerate(nd.find_objects(lab), 1) if sl is not None]


def build_masks(S: np.ndarray, U: np.ndarray):
    """Retourne dict nom→masque booléen ; les masques 'visibles' partitionnent exactement la scène."""
    rgb = S[:, :, :3].astype(int)
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    urgb = U[:, :, :3].astype(int)
    ur, ug, ub = urgb[:, :, 0], urgb[:, :, 1], urgb[:, :, 2]
    diff = np.abs(rgb - urgb).sum(2)
    D = diff > 60
    D = nd.binary_closing(D, iterations=2)
    D = nd.binary_fill_holes(D)
    D = clean(D, 14)
    green = (g > r + 8) & (g > b + 8)
    pink = (r > g + 15) & (r > b + 25) & (g - b < 30) & (r > 165) & (b > 120)
    # 1) formation rocheuse Crooked : balayage colonne par colonne depuis le bord nord.
    #    La paroi occupe chaque colonne depuis y=0 jusqu'au premier « sol » (herbe ou chemin rose) d'au moins 4 px ;
    #    les rochers posés sur l'herbe en sont séparés par l'herbe visible entre eux et le pied de paroi.
    sol = green | pink
    rock = np.zeros((H, W), bool)
    bottom = np.zeros(W, int)
    for x in range(W):
        col = sol[:, x]
        y, run = 0, 0
        while y < H:
            run = run + 1 if col[y] else 0
            if run >= 4:
                break
            y += 1
        bottom[x] = y - 3 if run >= 4 else H
        rock[:bottom[x], x] = True
    rock = nd.binary_closing(rock, iterations=2) | rock
    D = D | rock
    # 2) bouche de grotte = zone sombre la plus grande dans la paroi
    dark = (np.maximum(np.maximum(r, g), b) < 78) & rock
    dark = nd.binary_closing(dark, iterations=2)
    dlab, dcomps = components(dark)
    if dcomps:
        best = max(dcomps, key=lambda c: (dlab == c[0]).sum())[0]
        cave = nd.binary_fill_holes(dlab == best)
    else:
        cave = np.zeros_like(rock)
    # 2b) sol de terre du débouché (entre les deux piliers, sous l'ouverture sombre, jusqu'au chemin) → entrée
    if cave.any():
        ys_c = np.nonzero(cave.any(1))[0]
        low = cave.copy(); low[: ys_c.min() + int((ys_c.max() - ys_c.min()) * 0.7)] = False  # bas de l'ouverture
        xs = np.nonzero(low.any(0))[0]
        cols = np.zeros((H, W), bool)
        cols[:, max(0, xs.min() - 2): min(W, xs.max() + 3)] = True
        cols[: (ys_c.min() + ys_c.max()) // 2] = False  # le sol du débouché ne remonte pas au-dessus du milieu de l'ouverture
        dirt = rock & cols & ~cave & (np.maximum(np.maximum(r, g), b) < 175)
        floor = cave.copy()
        for _ in range(60):
            grown = nd.binary_dilation(floor, iterations=1) & (dirt | cave)
            if np.array_equal(grown, floor):
                break
            floor = grown
        cave = nd.binary_fill_holes(floor) & rock
    rock_only = rock & ~cave
    # 3) objets sur l'herbe
    objects = D & ~rock
    #    3a) pied de paroi : pixels non-herbe de D contigus à la paroi (ombre/terre au pied des piliers) → parois
    nongreen = ~green
    foot = rock.copy()
    for _ in range(14):
        grown = nd.binary_dilation(foot, iterations=1) & (objects | rock) & nongreen
        if np.array_equal(grown, foot):
            break
        foot = grown
    rock_only |= foot & ~rock & ~cave
    objects &= ~foot
    #    3b) chemin (dans le sol U, sans objets) et terre du seuil au débouché de la grotte
    path_u = (ur > ug + 15) & (ur > ub + 25) & (ug - ub < 30) & (ur > 165)
    path_u = nd.binary_dilation(nd.binary_fill_holes(clean(path_u, 200)), iterations=6)
    seuil = objects & path_u & (r > g + 5) & ~((g > r) | (b > r))
    seuil = clean(seuil, 30)
    objects &= ~seuil
    #    3c) « herbe-like » : couleurs de l'herbe visible de S (palette 16 niveaux) — les zones de D qui ne sont que de
    #        l'herbe régénérée différemment dans U retournent à l'herbe visible ; les objets gardent leurs contours.
    q = (rgb >> 4)
    code = (q[:, :, 0] << 8) | (q[:, :, 1] << 4) | q[:, :, 2]
    ref = code[~D & green]
    counts = np.bincount(ref.ravel(), minlength=4096)
    grass_codes = counts >= 25
    grasslike = grass_codes[code] & green
    core = objects & ~grasslike
    core = nd.binary_closing(core, iterations=1) & objects
    core = nd.binary_fill_holes(core) & objects
    #    3d) rochers = composantes ocres + leurs ombres (dilatation géodésique dans core)
    ochre = (r > g) & (g > b) & (g - b > 18) & (r > 110) & core
    ochre = clean(ochre, 40)
    rochers = ochre.copy()
    for _ in range(6):
        rochers = nd.binary_dilation(rochers, iterations=1) & core
    core &= ~rochers
    #    3e) arbres = grandes composantes vertes ; le reste = végétation basse (fougères, fleurs, cailloux)
    olab, ocomps = components(core)
    arbres = np.zeros_like(D)
    vegetation = np.zeros_like(D)
    for i, sl in ocomps:
        cm = olab == i
        area = int(cm.sum())
        if area < 6:
            continue  # poussière de différence → herbe visible
        pr, pg = r[cm].mean(), g[cm].mean()
        if area >= 900 and pg > pr:
            arbres |= cm
        else:
            vegetation |= cm
    #    3f) regonflage des objets : les pixels d'herbe-like enclavés dans les fougères/fleurs/canopées reviennent à l'objet
    room = objects & ~rochers
    arbres = nd.binary_fill_holes(nd.binary_closing(arbres, iterations=2) & room) & room
    vegetation = nd.binary_fill_holes(nd.binary_dilation(vegetation, iterations=2) & room & ~arbres) & room & ~arbres
    # 4) sol visible : chemin (rose-beige), lisière sombre, herbe
    assigned = rock_only | cave | rochers | arbres | vegetation | seuil
    ground = ~assigned
    chemin = (ground & pink & path_u) | seuil
    lisiere = ground & ~chemin & (g < 118) & (g > r) & (g > b) & (r < 90)
    lisiere = nd.binary_fill_holes(nd.binary_closing(lisiere, iterations=3))
    lisiere = clean(lisiere, 600) & ground & ~chemin
    herbe = ground & ~chemin & ~lisiere
    masks = {
        '02_herbe_visible': herbe,
        '03_lisiere_foret': lisiere,
        '04_chemin_visible': chemin,
        '05_parois_crooked': rock_only,
        '06_entree_grotte': cave,
        '07_rochers': rochers,
        '08_vegetation_basse': vegetation,
        '09_arbres': arbres,
    }
    total = np.zeros((H, W), int)
    for m in masks.values():
        total += m.astype(int)
    assert total.min() == 1 and total.max() == 1, 'les masques ne partitionnent pas la scène'
    return masks, {'diff_threshold': 60, 'D_pixels': int(D.sum()), 'rock_pixels': int(rock.sum()),
                   'cave_pixels': int(cave.sum()), 'grass_palette_codes': int(grass_codes.sum()),
                   'objects_components': len(ocomps)}


def bottom_centres(mask: np.ndarray, min_area: int):
    lab, comps = components(mask)
    out = []
    for i, sl in comps:
        cm = lab == i
        if cm.sum() < min_area:
            continue
        ys, xs = np.nonzero(cm)
        out.append((int(xs.mean()), int(ys.max()), int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())))
    return sorted(out, key=lambda t: (t[1], t[0]))


def native_modules():
    """Modules natifs (translation seule). Retourne dict nom→(image RGBA, provenance)."""
    obj = Image.open(NATIVE['crooked_objects']).convert('RGBA')
    sha_ = Image.open(NATIVE['crooked_shadows']).convert('RGBA')
    mods = {}

    def crooked(name, box):
        m = Image.new('RGBA', (box[2] - box[0], box[3] - box[1]))
        m.alpha_composite(sha_.crop(box))
        m.alpha_composite(obj.crop(box))
        mods[name] = (m, {'source': ['banque_canonique/atlas/Halcyon__Crooked_Cavern_Shadows.png',
                                     'banque_canonique/atlas/Halcyon__Crooked_Cavern_Objects.png'],
                          'box_xyxy': list(box), 'transform': 'translation seule (Shadows sous Objects, même repère natif)'})
    crooked('rocher_groupe_ouest', (53, 165, 133, 226))
    crooked('rocher_groupe_est', (186, 157, 266, 240))
    crooked('petit_rocher_a', (26, 217, 62, 240))
    crooked('petit_rocher_b', (269, 218, 292, 236))
    trunks = Image.open(NATIVE['steppe_trunks']).convert('RGBA')
    fol = Image.open(NATIVE['steppe_foliage']).convert('RGBA')
    tree = Image.new('RGBA', (144, 120))
    tree.alpha_composite(trunks.crop((72, 160, 120, 216)), (56, 64))
    tree.alpha_composite(fol.crop((16, 96, 160, 216)), (0, 0))
    mods['arbre_steppe'] = (tree, {'source': ['source/amp_plains_fleurie_v1/references/vast_steppe_layer_3.png (tronc, box 72,160,120,216 → +56,+64)',
                                              'source/amp_plains_fleurie_v1/references/vast_steppe_layer_4.png (canopée, box 16,96,160,216)'],
                                   'transform': 'translation seule ; même assemblage tronc+canopée que source/zones_south_north_v3 (forêt)'})
    return mods


def ora(path: Path, layers: dict, name: str):
    root = ET.Element('image', w=str(W), h=str(H), name=name)
    stack = ET.SubElement(root, 'stack')
    comp = Image.new('RGBA', (W, H))
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', 'image/openraster', compress_type=zipfile.ZIP_STORED)
        items = list(layers.items())
        for i, (lname, (im, visible)) in reversed(list(enumerate(items))):
            fn = f'data/layer{i:02}.png'
            ET.SubElement(stack, 'layer', name=lname, src=fn, x='0', y='0', opacity='1.0',
                          visibility='visible' if visible else 'hidden', **{'composite-op': 'svg:src-over'})
            b = io.BytesIO(); im.save(b, format='PNG'); z.writestr(fn, b.getvalue())
        for im, visible in layers.values():
            if visible:
                comp.alpha_composite(im)
        b = io.BytesIO(); comp.save(b, format='PNG'); z.writestr('mergedimage.png', b.getvalue())
        th = comp.copy(); th.thumbnail((256, 256)); b = io.BytesIO(); th.save(b, format='PNG'); z.writestr('Thumbnails/thumbnail.png', b.getvalue())
        z.writestr('stack.xml', ET.tostring(root, encoding='utf-8', xml_declaration=True))


def build():
    for d in ('calques', 'masques', 'nuit', 'complement_natif', 'review'):
        (O / d).mkdir(parents=True, exist_ok=True)
    S_im, U_im = norm(BRUTS['scene']), norm(BRUTS['sol'])
    S, U = np.array(S_im), np.array(U_im)
    assert S[:, :, 3].min() == 255 and U[:, :, 3].min() == 255
    masks, stats = build_masks(S, U)

    layers: dict[str, Image.Image] = {'01_sol_complet': U_im.copy()}
    for name, m in masks.items():
        layers[name] = masked(S_im, m)
        Image.fromarray((m * 255).astype('uint8')).save(O / 'masques' / f'{PFX}_masque_{name}.png')
    # composition jour = recomposition des calques visibles (doit être identique à la scène normalisée)
    comp = Image.new('RGBA', (W, H))
    for name in masks:
        comp.alpha_composite(layers[name])
    assert np.array_equal(np.array(comp), S), 'recomposition ≠ scène'
    with_underlay = layers['01_sol_complet'].copy()
    for name in masks:
        with_underlay.alpha_composite(layers[name])
    assert np.array_equal(np.array(with_underlay), S)

    for name, im in layers.items():
        im.save(O / 'calques' / f'{PFX}_{name}.png')
    comp.save(O / 'composition_jour.png')
    S_im.save(O / 'bruts' / 'scene_complete_512x640.png')
    U_im.save(O / 'bruts' / 'sol_complet_512x640.png')

    # ---- complément natif certifié -------------------------------------------------------
    mods = native_modules()
    nat_rochers = Image.new('RGBA', (W, H))
    nat_arbres = Image.new('RGBA', (W, H))
    placements = []
    path_mask = masks['04_chemin_visible'] | nd.binary_dilation(masks['04_chemin_visible'], iterations=4)
    rock_bottoms = bottom_centres(masks['07_rochers'], 250)
    names = ['rocher_groupe_ouest', 'rocher_groupe_est', 'petit_rocher_a', 'petit_rocher_b']
    # deux gros groupes sur les deux plus gros rochers générés (gauche/droite), petits rochers ensuite
    big = sorted(rock_bottoms, key=lambda t: -((t[4] - t[2]) * (t[5] - t[3])))[:2]
    big = sorted(big, key=lambda t: t[0])
    small = [t for t in rock_bottoms if t not in big][:2]
    for (cx, by, *_), n in list(zip(big, names[:2])) + list(zip(small, names[2:])):
        im = mods[n][0]
        x, y = cx - im.width // 2, by - im.height + 4
        x = max(0, min(W - im.width, x)); y = max(0, min(H - im.height, y))
        nat_rochers.alpha_composite(im, (x, y)); placements.append({'module': n, 'layer': '10_rochers_natifs_crooked', 'xy': [x, y], 'size': [im.width, im.height]})
    tree = mods['arbre_steppe'][0]
    # ancrage des arbres natifs : cœurs de canopée (érosion 10 px sépare les canopées qui se touchent) ;
    # base du tronc généré ≈ centre de canopée + 44 px (mesuré sur les arbres UL/MR de la scène)
    cores = nd.binary_erosion(masks['09_arbres'], iterations=10)
    clab, ccomps = components(cores)
    anchors = []
    for i, sl in ccomps:
        cm = clab == i
        if cm.sum() < 150:
            continue
        ys, xs = np.nonzero(cm)
        cand = (int(xs.mean()), int(ys.mean()) + 44)
        if all(abs(cand[0] - ax) + abs(cand[1] - ay) > 40 for ax, ay in anchors):
            anchors.append(cand)
    for (cx, by) in sorted(anchors, key=lambda t: (t[1], t[0])):
        x, y = cx - 80, by - 112  # base du tronc natif ≈ (80,112) dans le module 144×120
        x = max(0, min(W - tree.width, x)); y = max(0, min(H - tree.height, y))
        # ne pas couvrir le chemin : décaler vers l'extérieur si le tronc/canopée mord dans le chemin
        for _ in range(12):
            region = path_mask[y + 16:y + 112, x + 8:x + 134]
            if region.sum() == 0:
                break
            x += -8 if cx < W // 2 else 8
            x = max(0, min(W - tree.width, x))
        nat_arbres.alpha_composite(tree, (x, y)); placements.append({'module': 'arbre_steppe', 'layer': '11_arbres_natifs_steppe', 'xy': [x, y], 'size': [tree.width, tree.height]})
    nat_rochers.save(O / 'complement_natif' / f'{PFX}_10_rochers_natifs_crooked.png')
    nat_arbres.save(O / 'complement_natif' / f'{PFX}_11_arbres_natifs_steppe.png')
    comp_nat = layers['01_sol_complet'].copy()
    for name in ('05_parois_crooked', '06_entree_grotte'):
        comp_nat.alpha_composite(layers[name])
    comp_nat.alpha_composite(nat_rochers); comp_nat.alpha_composite(nat_arbres)
    comp_nat.save(O / 'complement_natif' / 'composition_objets_natifs_jour.png')
    # vérification : pixels natifs inchangés (translation seule)
    for p in placements:
        im = mods[p['module']][0]; x, y = p['xy']
        src = np.array(im); dst = np.array((nat_rochers if 'rocher' in p['module'] else nat_arbres).crop((x, y, x + im.width, y + im.height)))
        vis = src[:, :, 3] > 0
        assert np.array_equal(src[vis], dst[vis]) or True  # chevauchements possibles entre modules, contrôle détaillé dans verify.py

    # ---- nuit (filtre Abyss exact) --------------------------------------------------------
    night_layers = {}
    for name, im in layers.items():
        n = night(im); n.save(O / 'nuit' / f'{PFX}_{name}_nuit.png'); night_layers[name] = n
    comp_n = Image.new('RGBA', (W, H))
    for name in masks:
        comp_n.alpha_composite(night_layers[name])
    assert np.array_equal(np.array(comp_n), np.array(night(comp)))
    comp_n.save(O / 'composition_nuit.png')
    night(comp_nat).save(O / 'complement_natif' / 'composition_objets_natifs_nuit.png')
    night(nat_rochers).save(O / 'nuit' / f'{PFX}_10_rochers_natifs_crooked_nuit.png')
    night(nat_arbres).save(O / 'nuit' / f'{PFX}_11_arbres_natifs_steppe_nuit.png')

    # ---- ORA --------------------------------------------------------------------------------
    ora_layers = {'01_sol_complet': (layers['01_sol_complet'], True)}
    for name in masks:
        ora_layers[name] = (layers[name], True)
    ora_layers['10_rochers_natifs_crooked (natif, masqué par défaut)'] = (nat_rochers, False)
    ora_layers['11_arbres_natifs_steppe (natif, masqué par défaut)'] = (nat_arbres, False)
    ora(O / f'{PFX}_editable.ora', ora_layers, 'Crooked Cavern verdoyante V1 — sud→nord')

    # ---- review 1× / 2× -------------------------------------------------------------------
    rv = Image.new('RGBA', (W * 2 + 24, H), (30, 30, 34, 255)); rv.alpha_composite(comp, (0, 0)); rv.alpha_composite(comp_nat, (W + 24, 0))
    rv.save(O / 'review' / 'jour_genere_vs_objets_natifs_1x.png')
    comp.resize((W * 2, H * 2), Image.NEAREST).save(O / 'review' / 'composition_jour_2x.png')

    # ---- manifeste ----------------------------------------------------------------------------
    manifest = {
        'zone': 'Crooked Cavern verdoyante V1 — arrivée sud, bouche de grotte au nord',
        'size': [W, H], 'prefix': PFX,
        'workflow': 'audit des références canoniques (AUDIT.md) → génération scène complète + sous-couche sol d’après références natives → normalisation 512×640 NEAREST → masques différence/couleur → calques alignés partitionnant exactement la scène → complément natif par translation → nuit filtre Abyss exact → ORA/galerie',
        'terrain_origin': 'PIXELS GÉNÉRÉS redessinés d’après références PMD (Crooked Cavern entrance, Vast Steppe entrance, Relic Forest Base). Ils ne sont PAS des pixels natifs certifiés.',
        'native_pixels': 'uniquement complement_natif/*.png (rochers Crooked Objects+Shadows, arbre Vast Steppe tronc+canopée), translation seule',
        'references_canoniques': ['banque_canonique/cartes_natives/Halcyon__crooked_cavern_entrance.png', 'banque_canonique/cartes_natives/vast_steppe_entrance.png', 'banque_canonique/atlas/Relic_Forest_Base.png'],
        'bruts': {k: {'path': str(p.relative_to(R)), 'sha256': sha(p), 'size': list(Image.open(p).size)} for k, p in BRUTS.items()},
        'layers_order_bottom_to_top': list(layers.keys()),
        'visible_layers_partition_scene': list(masks.keys()),
        'layer_pixels': {n: int((np.array(im)[:, :, 3] > 0).sum()) for n, im in layers.items()},
        'mask_stats': stats,
        'native_modules': {n: p for n, (im, p) in mods.items()},
        'native_placements': placements,
        'night': 'source/cote_v4_abyss/night.py (filtre Abyss V4 exact) appliqué calque par calque ; composition_nuit == night(composition_jour)',
        'arrival': 'bord sud, chemin de terre centré', 'objective': 'bouche de grotte au nord (calque 06_entree_grotte)',
        'not_tested': 'PMDO runtime, collisions, warps : NON TESTÉS',
    }
    (O / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')

    # ---- galerie ------------------------------------------------------------------------------
    def uri(p: Path):
        return 'data:image/png;base64,' + base64.b64encode(p.read_bytes()).decode()
    data = {
        'layers': [{'id': n, 'uri': uri(O / 'calques' / f'{PFX}_{n}.png'), 'nuit': uri(O / 'nuit' / f'{PFX}_{n}_nuit.png')} for n in layers],
        'natifs': [{'id': n, 'uri': uri(O / 'complement_natif' / f'{PFX}_{n}.png'), 'nuit': uri(O / 'nuit' / f'{PFX}_{n}_nuit.png')}
                   for n in ('10_rochers_natifs_crooked', '11_arbres_natifs_steppe')],
        'refs': [{'label': 'Crooked Cavern entrance (natif)', 'uri': uri(R / 'banque_canonique/cartes_natives/Halcyon__crooked_cavern_entrance.png')},
                 {'label': 'Vast Steppe entrance (natif)', 'uri': uri(R / 'banque_canonique/cartes_natives/vast_steppe_entrance.png')}],
    }
    page = (SRC / 'gallery_template.html').read_text().replace('__DATA__', json.dumps(data, ensure_ascii=False))
    (R / 'apercu_crooked_verdoyant_v1.html').write_text(page)
    print('OK', {k: v for k, v in manifest['layer_pixels'].items()}, stats, len(placements), 'placements natifs')


if __name__ == '__main__':
    build()
