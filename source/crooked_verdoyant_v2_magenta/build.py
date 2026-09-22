"""Crooked Cavern verdoyante V2 — calques GÉNÉRÉS SÉPARÉMENT sur fond magenta (« générateur fond magenta multicalque »).

Différence avec V1 (une scène découpée par masques) : ici chaque calque est une génération propre sur magenta
#FF00FF (méthode `source/layouts_magenta_v1/WORKFLOW.md` : générateur → détourage magenta → calques alignés),
la scène V1 servant de maquette de mise en page (image d'entrée de chaque extraction) pour garder l'alignement.

Bruts retenus (renders/crooked_verdoyant_v2_magenta/bruts/) :
  sol_herbe_brut.png                 sous-couche herbe + lisière (pleine, sans magenta)
  magenta_chemin_brut_v2.png         chemin de terre sur magenta (1er essai rejeté : gardait la paroi)
  magenta_parois_entree_brut.png     parois Crooked + ouverture + sol du débouché sur magenta
  magenta_rochers_brut.png           rochers/cailloux sur magenta
  magenta_arbres_brut.png            5 arbres (canopée, tronc, ombre) sur magenta
  magenta_feuille_vegetation_brut.png feuille de 8 plantes basses sur magenta (posées aux emplacements de la maquette V1 ;
                                     deux extractions directes de la végétation ont été rejetées : gardaient paroi/arbres/herbe)

Reproduction : .venv/bin/python source/crooked_verdoyant_v2_magenta/build.py
"""
from __future__ import annotations
import base64, hashlib, importlib.util, io, json, sys, zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
import scipy.ndimage as nd
from PIL import Image

R = Path(__file__).resolve().parents[2]
SRC = R / 'source/crooked_verdoyant_v2_magenta'
O = R / 'renders/crooked_verdoyant_v2_magenta'
V1 = R / 'renders/crooked_verdoyant_v1'
sys.path.insert(0, str(R / 'source/cote_v4_abyss'))
from night import night  # noqa: E402  (filtre Abyss V4 exact)

W, H = 512, 640
PFX = 'CrookedMagentaV2'
BRUTS = {
    'sol_herbe': O / 'bruts/sol_herbe_brut.png',
    'chemin': O / 'bruts/magenta_chemin_brut_v2.png',
    'parois_entree': O / 'bruts/magenta_parois_entree_brut.png',
    'rochers': O / 'bruts/magenta_rochers_brut.png',
    'arbres': O / 'bruts/magenta_arbres_brut.png',
    'feuille_vegetation': O / 'bruts/magenta_feuille_vegetation_brut.png',
}
REJETES = {
    'chemin_essai1': O / 'bruts/rejetes/magenta_chemin_brut.png',
    'vegetation_essai1': O / 'bruts/rejetes/magenta_vegetation_brut.png',
    'vegetation_essai2': O / 'bruts/rejetes/magenta_vegetation_brut_v2.png',
}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def key(im: Image.Image, strong: bool = True) -> Image.Image:
    """Détourage magenta (pleine résolution) : fond (r,b hauts, g bas) → alpha 0, puis frange.
    strong=True (chemin, parois, rochers, arbres : aucun rose légitime) : 3 px de frange où le bleu dépasse le vert
    (mélange magenta) sont retirés. strong=False (feuille de fleurs roses) : seule la frange nettement magenta
    (|r-b|<70 et g<0.6·min(r,b)) est retirée, pour ne pas manger les pétales."""
    a = np.array(im.convert('RGBA'))
    r, g, b = a[:, :, 0].astype(int), a[:, :, 1].astype(int), a[:, :, 2].astype(int)
    bg = (r > 150) & (b > 150) & (g < 100)
    if strong:
        fringe = nd.binary_dilation(bg, iterations=3) & ~bg & (b > g + 10)
    else:
        fringe = nd.binary_dilation(bg, iterations=2) & ~bg & (np.abs(r - b) < 70) & (g < 0.6 * np.minimum(r, b))
    a[bg | fringe] = 0
    return Image.fromarray(a)


def norm(im: Image.Image) -> Image.Image:
    return im.resize((W, H), Image.NEAREST)


def clean_alpha(im: Image.Image, min_px: int) -> Image.Image:
    a = np.array(im)
    m = a[:, :, 3] > 0
    lab, n = nd.label(m, structure=np.ones((3, 3)))
    if n:
        counts = np.bincount(lab.ravel()); keep = counts >= min_px; keep[0] = False
        a[~keep[lab]] = 0
    return Image.fromarray(a)


def components(m: np.ndarray):
    lab, n = nd.label(m, structure=np.ones((3, 3)))
    return lab, [(i, sl) for i, sl in enumerate(nd.find_objects(lab), 1) if sl is not None]


def split_entrance(parois: Image.Image):
    """Sépare l'ouverture sombre + sol du débouché (entrée) du reste de la paroi (même règle que V1)."""
    a = np.array(parois)
    rock = a[:, :, 3] > 0
    r, g, b = a[:, :, 0].astype(int), a[:, :, 1].astype(int), a[:, :, 2].astype(int)
    mx = np.maximum(np.maximum(r, g), b)
    dark = nd.binary_closing((mx < 78) & rock, iterations=2)
    dlab, dcomps = components(dark)
    best = max(dcomps, key=lambda c: (dlab == c[0]).sum())[0]
    cave = nd.binary_fill_holes(dlab == best)
    ys_c = np.nonzero(cave.any(1))[0]
    low = cave.copy(); low[: ys_c.min() + int((ys_c.max() - ys_c.min()) * 0.7)] = False
    xs = np.nonzero(low.any(0))[0]
    cols = np.zeros((H, W), bool); cols[:, max(0, xs.min() - 2): min(W, xs.max() + 3)] = True
    cols[: (ys_c.min() + ys_c.max()) // 2] = False
    dirt = rock & cols & ~cave & (mx < 175)
    floor = cave.copy()
    for _ in range(60):
        grown = nd.binary_dilation(floor, iterations=1) & (dirt | cave)
        if np.array_equal(grown, floor):
            break
        floor = grown
    cave = nd.binary_fill_holes(floor) & rock
    ent = a.copy(); ent[~cave] = 0
    par = a.copy(); par[cave] = 0
    return Image.fromarray(par), Image.fromarray(ent)


def sheet_sprites(sheet: Image.Image):
    """Découpe la feuille de végétation détourée en sprites (composantes), triés rangée/colonne."""
    a = np.array(sheet); m = a[:, :, 3] > 0
    lab, comps = components(nd.binary_closing(m, iterations=3))
    out = []
    for i, sl in comps:
        cm = (lab == i) & m
        if cm.sum() < 200:
            continue
        ys, xs = np.nonzero(cm)
        box = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
        sp = a[box[1]:box[3], box[0]:box[2]].copy(); sp[~cm[box[1]:box[3], box[0]:box[2]]] = 0
        out.append((box, Image.fromarray(sp)))
    out.sort(key=lambda t: (t[0][1] // 300, t[0][0]))
    return out


def ora(path: Path, layers: dict, name: str):
    root = ET.Element('image', w=str(W), h=str(H), name=name); stack = ET.SubElement(root, 'stack')
    comp = Image.new('RGBA', (W, H))
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', 'image/openraster', compress_type=zipfile.ZIP_STORED)
        items = list(layers.items())
        for i, (lname, (im, visible)) in reversed(list(enumerate(items))):
            fn = f'data/layer{i:02}.png'
            ET.SubElement(stack, 'layer', name=lname, src=fn, x='0', y='0', opacity='1.0', visibility='visible' if visible else 'hidden', **{'composite-op': 'svg:src-over'})
            bio = io.BytesIO(); im.save(bio, format='PNG'); z.writestr(fn, bio.getvalue())
        for im, visible in layers.values():
            if visible:
                comp.alpha_composite(im)
        bio = io.BytesIO(); comp.save(bio, format='PNG'); z.writestr('mergedimage.png', bio.getvalue())
        th = comp.copy(); th.thumbnail((256, 256)); bio = io.BytesIO(); th.save(bio, format='PNG'); z.writestr('Thumbnails/thumbnail.png', bio.getvalue())
        z.writestr('stack.xml', ET.tostring(root, encoding='utf-8', xml_declaration=True))


def iou(a: np.ndarray, b: np.ndarray) -> float:
    u = (a | b).sum()
    return float((a & b).sum() / u) if u else 1.0


def load_v1_native():
    spec = importlib.util.spec_from_file_location('crooked_v1_build', R / 'source/crooked_verdoyant_v1/build.py')
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod.native_modules()


def build():
    for d in ('calques', 'masques', 'nuit', 'complement_natif', 'review'):
        (O / d).mkdir(parents=True, exist_ok=True)
    stats = {}
    # ---- détourage + normalisation ---------------------------------------------------------
    sol = norm(Image.open(BRUTS['sol_herbe']).convert('RGBA'))
    assert np.array(sol)[:, :, 3].min() == 255
    keyed = {}
    for k in ('chemin', 'parois_entree', 'rochers', 'arbres'):
        full = key(Image.open(BRUTS[k]))
        stats[f'{k}_magenta_fraction_brut'] = round(float((np.array(full)[:, :, 3] == 0).mean()), 4)
        keyed[k] = clean_alpha(norm(full), 6)
    parois, entree = split_entrance(keyed['parois_entree'])
    # ---- végétation basse : sprites de la feuille magenta posés aux emplacements de la maquette V1 ----------
    sheet = key(Image.open(BRUTS['feuille_vegetation']), strong=False)
    sprites = sheet_sprites(sheet)
    assert len(sprites) >= 6, len(sprites)
    ferns = [s for (box, s) in sprites[:4]]
    flowers = [s for (box, s) in sprites[4:6]]
    v1_mask = np.array(Image.open(V1 / 'masques/CrookedVerdoyantV1_masque_08_vegetation_basse.png')) > 0
    v1_scene = np.array(Image.open(V1 / 'bruts/scene_complete_512x640.png').convert('RGB')).astype(int)
    v1_rock = np.array(Image.open(V1 / 'masques/CrookedVerdoyantV1_masque_05_parois_crooked.png')) > 0
    veg = Image.new('RGBA', (W, H))
    placements = []
    lab, comps = components(v1_mask)
    fi = 0
    for i, sl in comps:
        cm = lab == i
        area = int(cm.sum())
        if area < 40:
            continue
        ys, xs = np.nonzero(cm)
        x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        if nd.binary_dilation(v1_rock, iterations=3)[y0:y1, x0:x1].any():
            continue  # cailloux du pied de paroi : déjà dans le calque rochers
        pr, pg, pb = v1_scene[cm][:, 0], v1_scene[cm][:, 1], v1_scene[cm][:, 2]
        pink = int(((pr > 180) & (pb > 150) & (pr > pg + 30)).sum())
        if pink >= 5:
            sp = flowers[fi % 2]
        else:
            sp = ferns[fi % 4]
        fi += 1
        tw = max(12, x1 - x0)
        th = max(10, round(sp.height * tw / sp.width))
        sp2 = sp.resize((tw, th), Image.NEAREST)
        px, py = int((x0 + x1) // 2 - tw // 2), int(y1 - th)
        px = int(max(0, min(W - tw, px))); py = int(max(0, min(H - th, py)))
        veg.alpha_composite(sp2, (px, py))
        placements.append({'sprite': 'fleur' if pink >= 5 else 'fougere', 'xy': [px, py], 'size': [int(tw), int(th)], 'v1_component_area': area})
    layers = {
        '01_sol_herbe': sol,
        '02_chemin': keyed['chemin'],
        '03_parois_crooked': parois,
        '04_entree_grotte': entree,
        '05_rochers': keyed['rochers'],
        '06_vegetation_basse': veg,
        '07_arbres': keyed['arbres'],
    }
    comp = Image.new('RGBA', (W, H))
    for n, im in layers.items():
        im.save(O / 'calques' / f'{PFX}_{n}.png')
        Image.fromarray(((np.array(im)[:, :, 3] > 0) * 255).astype('uint8')).save(O / 'masques' / f'{PFX}_masque_{n}.png')
        comp.alpha_composite(im)
    comp.save(O / 'composition_jour.png')
    # ---- contrôle d'alignement avec la maquette V1 (information, pas une exigence d'identité) ----------
    v1m = {n: np.array(Image.open(V1 / f'masques/CrookedVerdoyantV1_masque_{n}.png')) > 0 for n in
           ('04_chemin_visible', '05_parois_crooked', '06_entree_grotte', '07_rochers', '08_vegetation_basse', '09_arbres')}
    al = lambda n: np.array(layers[n])[:, :, 3] > 0
    stats['iou_vs_maquette_v1'] = {
        'chemin': round(iou(al('02_chemin'), v1m['04_chemin_visible'] | v1m['06_entree_grotte']), 3),
        'parois': round(iou(al('03_parois_crooked') | al('04_entree_grotte'), v1m['05_parois_crooked'] | v1m['06_entree_grotte']), 3),
        'entree': round(iou(al('04_entree_grotte'), v1m['06_entree_grotte']), 3),
        'rochers': round(iou(nd.binary_dilation(al('05_rochers'), iterations=2), nd.binary_dilation(v1m['07_rochers'], iterations=2)), 3),
        'arbres': round(iou(al('07_arbres'), v1m['09_arbres']), 3),
    }
    stats['layer_pixels'] = {n: int((np.array(im)[:, :, 3] > 0).sum()) for n, im in layers.items()}
    # ---- complément natif (mêmes modules que V1, positions relevées sur les calques V2) ------------------
    mods = load_v1_native()
    nat_rochers = Image.new('RGBA', (W, H)); nat_arbres = Image.new('RGBA', (W, H)); nat_pl = []
    rlab, rcomps = components(nd.binary_dilation(al('05_rochers'), iterations=3))
    groups = []
    for i, sl in rcomps:
        cm = (rlab == i) & al('05_rochers')
        if cm.sum() < 250:
            continue
        ys, xs = np.nonzero(cm); groups.append((int(xs.mean()), int(ys.max()), int(cm.sum())))
    groups.sort(key=lambda t: -t[2])
    big = sorted(groups[:2], key=lambda t: t[0]); small = groups[2:4]
    for (cx, by, _), n in list(zip(big, ['rocher_groupe_ouest', 'rocher_groupe_est'])) + list(zip(small, ['petit_rocher_a', 'petit_rocher_b'])):
        im = mods[n][0]; x = int(max(0, min(W - im.width, cx - im.width // 2))); y = int(max(0, min(H - im.height, by - im.height + 4)))
        nat_rochers.alpha_composite(im, (x, y)); nat_pl.append({'module': n, 'layer': '10_rochers_natifs_crooked', 'xy': [x, y], 'size': [im.width, im.height]})
    tree = mods['arbre_steppe'][0]
    cores = nd.binary_erosion(al('07_arbres'), iterations=10)
    clab, ccomps = components(cores); anchors = []
    for i, sl in ccomps:
        cm = clab == i
        if cm.sum() < 150:
            continue
        ys, xs = np.nonzero(cm); cand = (int(xs.mean()), int(ys.mean()) + 44)
        if all(abs(cand[0] - ax) + abs(cand[1] - ay) > 40 for ax, ay in anchors):
            anchors.append(cand)
    path_mask = nd.binary_dilation(al('02_chemin'), iterations=4)
    for (cx, by) in sorted(anchors, key=lambda t: (t[1], t[0])):
        x, y = cx - 80, by - 112
        x = int(max(0, min(W - tree.width, x))); y = int(max(0, min(H - tree.height, y)))
        for _ in range(12):
            if path_mask[y + 16:y + 112, x + 8:x + 134].sum() == 0:
                break
            x += -8 if cx < W // 2 else 8; x = max(0, min(W - tree.width, x))
        nat_arbres.alpha_composite(tree, (x, y)); nat_pl.append({'module': 'arbre_steppe', 'layer': '11_arbres_natifs_steppe', 'xy': [x, y], 'size': [tree.width, tree.height]})
    nat_rochers.save(O / 'complement_natif' / f'{PFX}_10_rochers_natifs_crooked.png')
    nat_arbres.save(O / 'complement_natif' / f'{PFX}_11_arbres_natifs_steppe.png')
    comp_nat = sol.copy()
    for n in ('02_chemin', '03_parois_crooked', '04_entree_grotte'):
        comp_nat.alpha_composite(layers[n])
    comp_nat.alpha_composite(nat_rochers); comp_nat.alpha_composite(nat_arbres)
    comp_nat.save(O / 'complement_natif' / 'composition_objets_natifs_jour.png')
    # ---- nuit -------------------------------------------------------------------------------------
    for n, im in layers.items():
        night(im).save(O / 'nuit' / f'{PFX}_{n}_nuit.png')
    for n, im in (('10_rochers_natifs_crooked', nat_rochers), ('11_arbres_natifs_steppe', nat_arbres)):
        night(im).save(O / 'nuit' / f'{PFX}_{n}_nuit.png')
    comp_n = Image.new('RGBA', (W, H))
    for n in layers:
        comp_n.alpha_composite(Image.open(O / 'nuit' / f'{PFX}_{n}_nuit.png'))
    comp_n.save(O / 'composition_nuit.png')
    night(comp_nat).save(O / 'complement_natif' / 'composition_objets_natifs_nuit.png')
    # ---- ORA + review ------------------------------------------------------------------------------
    ora_layers = {n: (im, True) for n, im in layers.items()}
    ora_layers['10_rochers_natifs_crooked (natif, masqué par défaut)'] = (nat_rochers, False)
    ora_layers['11_arbres_natifs_steppe (natif, masqué par défaut)'] = (nat_arbres, False)
    ora(O / f'{PFX}_editable.ora', ora_layers, 'Crooked Cavern verdoyante V2 — calques magenta')
    rv = Image.new('RGBA', (W * 3 + 48, H), (30, 30, 34, 255))
    rv.alpha_composite(Image.open(V1 / 'composition_jour.png').convert('RGBA'), (0, 0)); rv.alpha_composite(comp, (W + 24, 0)); rv.alpha_composite(comp_nat, (2 * W + 48, 0))
    rv.save(O / 'review' / 'maquette_v1_vs_magenta_v2_vs_natifs_1x.png')
    rvn = Image.new('RGBA', (W * 2 + 24, H), (30, 30, 34, 255)); rvn.alpha_composite(comp_n, (0, 0)); rvn.alpha_composite(Image.open(O / 'complement_natif/composition_objets_natifs_nuit.png').convert('RGBA'), (W + 24, 0))
    rvn.save(O / 'review' / 'nuit_v2_vs_natifs_1x.png')
    board = Image.new('RGBA', (4 * 512 + 24, 2 * 640 + 8), (255, 0, 255, 255))
    for i, (n, im) in enumerate(layers.items()):
        board.alpha_composite(im, ((i % 4) * 520, (i // 4) * 648))
    board.resize((board.width // 2, board.height // 2), Image.NEAREST).save(O / 'review' / 'planche_calques_0.5x.png')
    # ---- manifeste ----------------------------------------------------------------------------------
    manifest = {
        'zone': 'Crooked Cavern verdoyante V2 — calques générés séparément sur fond magenta (sud → nord)',
        'size': [W, H], 'prefix': PFX,
        'workflow': 'audit (source/crooked_verdoyant_v1/AUDIT.md §5) → génération de chaque calque sur magenta #FF00FF (maquette V1 en entrée pour l’alignement) → détourage magenta + frange 1 px → normalisation 512×640 NEAREST → séparation ouverture/sol du débouché → végétation basse = sprites de la feuille magenta posés aux emplacements de la maquette → complément natif → nuit Abyss exacte → ORA/galerie',
        'terrain_origin': 'PIXELS GÉNÉRÉS (redessinés d’après références PMD : Crooked Cavern entrance, Vast Steppe entrance, Relic Forest Base). PAS des pixels natifs certifiés.',
        'native_pixels': 'uniquement complement_natif/*.png (translation seule)',
        'key': {'background': '(r>150)&(b>150)&(g<100)', 'fringe_forte_3px': 'b>g+10 (chemin, parois, rochers, arbres : aucun pixel légitime n’a b>g)', 'fringe_douce_2px_feuille': '|r-b|<70 & g<0.6·min(r,b)', 'note': 'roses du chemin (g≈b) et fleurs (g>0.6·min(r,b)) préservés'},
        'bruts': {k: {'path': str(p.relative_to(R)), 'sha256': sha(p), 'size': list(Image.open(p).size)} for k, p in BRUTS.items()},
        'bruts_rejetes': {k: {'path': str(p.relative_to(R)), 'sha256': sha(p), 'raison': {'chemin_essai1': 'gardait la paroi et un ciel teinté', 'vegetation_essai1': 'gardait paroi et lisières', 'vegetation_essai2': 'gardait arbres, paroi partielle et herbe plate'}[k]} for k, p in REJETES.items() if p.exists()},
        'maquette': 'renders/crooked_verdoyant_v1/bruts/scene_complete_brut.png (image d’entrée des extractions) ; sol : renders/crooked_verdoyant_v1/bruts/sol_complet_brut.png',
        'layers_order_bottom_to_top': list(layers.keys()),
        'vegetation_placements': placements,
        'native_placements': nat_pl,
        'stats': stats,
        'night': 'source/cote_v4_abyss/night.py appliqué calque par calque',
        'arrival': 'bord sud, chemin centré', 'objective': 'bouche de grotte au nord (04_entree_grotte)',
        'not_tested': 'PMDO runtime, collisions, warps : NON TESTÉS',
    }
    (O / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    # ---- galerie ------------------------------------------------------------------------------------
    def uri(p: Path):
        return 'data:image/png;base64,' + base64.b64encode(p.read_bytes()).decode()
    data = {
        'layers': [{'id': n, 'uri': uri(O / 'calques' / f'{PFX}_{n}.png'), 'nuit': uri(O / 'nuit' / f'{PFX}_{n}_nuit.png')} for n in layers],
        'natifs': [{'id': n, 'uri': uri(O / 'complement_natif' / f'{PFX}_{n}.png'), 'nuit': uri(O / 'nuit' / f'{PFX}_{n}_nuit.png')} for n in ('10_rochers_natifs_crooked', '11_arbres_natifs_steppe')],
        'bruts': [{'label': k, 'uri': uri(p)} for k, p in BRUTS.items()],
        'refs': [{'label': 'Crooked Cavern entrance (natif)', 'uri': uri(R / 'banque_canonique/cartes_natives/Halcyon__crooked_cavern_entrance.png')},
                 {'label': 'Vast Steppe entrance (natif)', 'uri': uri(R / 'banque_canonique/cartes_natives/vast_steppe_entrance.png')}],
        'generated_ids': ['02_chemin', '03_parois_crooked', '04_entree_grotte', '05_rochers', '06_vegetation_basse', '07_arbres'],
    }
    page = (SRC / 'gallery_template.html').read_text().replace('__DATA__', json.dumps(data, ensure_ascii=False))
    (R / 'apercu_crooked_verdoyant_v2_magenta.html').write_text(page)
    print('OK', json.dumps(stats, ensure_ascii=False), len(placements), 'plantes,', len(nat_pl), 'modules natifs')


if __name__ == '__main__':
    build()
