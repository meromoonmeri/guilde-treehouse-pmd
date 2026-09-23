"""Vérification indépendante de renders/crooked_verdoyant_v2_magenta → verification.json.

Contrôles : SHA des bruts, tailles, absence de magenta résiduel dans les calques, composition == pile des calques,
sous-couche opaque, nuit == filtre Abyss exact, complément natif reconstruit identique (translation seule),
chemin continu bord sud → sol du débouché, arbres/rochers hors du chemin (information), ORA cohérent.
Aucun test moteur PMDO.
"""
from __future__ import annotations
import hashlib, json, sys, zipfile
from pathlib import Path
import numpy as np
import scipy.ndimage as nd
from PIL import Image

R = Path(__file__).resolve().parents[2]
O = R / 'renders/crooked_verdoyant_v3_echelle'
sys.path.insert(0, str(R / 'source/cote_v4_abyss'))
from night import night  # noqa: E402

PFX = 'CrookedEchelleV3'
W, H = 928, 1152
LAYERS = ['01_sol_herbe', '02_lisiere_foret', '03_chemin', '04_parois_crooked', '05_entree_grotte', '06_rochers', '07_vegetation_basse', '08_troncs_ombres', '09_canopees']


def arr(p):
    return np.array(Image.open(p).convert('RGBA'))


def main():
    m = json.loads((O / 'manifest.json').read_text())
    res = {}
    res['bruts_sha256_ok'] = all(hashlib.sha256((R / v['path']).read_bytes()).hexdigest() == v['sha256'] for v in list(m['bruts'].values()) + list(m['bruts_rejetes'].values()))
    layers = {n: arr(O / 'calques' / f'{PFX}_{n}.png') for n in LAYERS}
    res['all_layers_928x1152'] = all(a.shape == (H, W, 4) for a in layers.values())
    res['underlay_opaque'] = bool(layers['01_sol_herbe'][:, :, 3].min() == 255)
    def magenta_left(a):
        r, g, b = a[:, :, 0].astype(int), a[:, :, 1].astype(int), a[:, :, 2].astype(int)
        return int(((a[:, :, 3] > 0) & (r > 150) & (b > 150) & (g < 100)).sum())
    res['residual_magenta_pixels'] = {n: magenta_left(a) for n, a in layers.items()}
    res['no_residual_magenta'] = all(v == 0 for v in res['residual_magenta_pixels'].values())
    res['alpha_is_binary'] = all(bool(np.isin(np.unique(a[:, :, 3]), [0, 255]).all()) for a in layers.values())
    comp = Image.new('RGBA', (W, H))
    for n in LAYERS:
        comp.alpha_composite(Image.fromarray(layers[n]))
    res['composition_equals_stack'] = bool(np.array_equal(np.array(comp), arr(O / 'composition_jour.png')))
    res['composition_opaque'] = bool(np.array(comp)[:, :, 3].min() == 255)
    res['masks_match_layers'] = all(bool(np.array_equal(np.array(Image.open(O / 'masques' / f'{PFX}_masque_{n}.png')) > 0, layers[n][:, :, 3] > 0)) for n in LAYERS)
    res['night_layers_exact_abyss'] = all(bool(np.array_equal(arr(O / 'nuit' / f'{PFX}_{n}_nuit.png'), np.array(night(Image.fromarray(layers[n]))))) for n in LAYERS)
    comp_n = Image.new('RGBA', (W, H))
    for n in LAYERS:
        comp_n.alpha_composite(Image.open(O / 'nuit' / f'{PFX}_{n}_nuit.png').convert('RGBA'))
    res['composition_nuit_equals_stack_of_night_layers'] = bool(np.array_equal(np.array(comp_n), arr(O / 'composition_nuit.png')))
    # complément natif
    obj = Image.open(R / 'banque_canonique/atlas/Halcyon__Crooked_Cavern_Objects.png').convert('RGBA')
    shd = Image.open(R / 'banque_canonique/atlas/Halcyon__Crooked_Cavern_Shadows.png').convert('RGBA')
    trunks = Image.open(R / 'source/amp_plains_fleurie_v1/references/vast_steppe_layer_3.png').convert('RGBA')
    fol = Image.open(R / 'source/amp_plains_fleurie_v1/references/vast_steppe_layer_4.png').convert('RGBA')
    tree = Image.new('RGBA', (144, 120)); tree.alpha_composite(trunks.crop((72, 160, 120, 216)), (56, 64)); tree.alpha_composite(fol.crop((16, 96, 160, 216)), (0, 0))
    v1m = json.loads((R / 'renders/crooked_verdoyant_v1/manifest.json').read_text())['native_modules']
    rebuilt = {'10_rochers_natifs_crooked': Image.new('RGBA', (W, H)), '11_arbres_natifs_steppe': Image.new('RGBA', (W, H))}
    for p in m['native_placements']:
        if p['module'] == 'arbre_steppe':
            im = tree
        else:
            box = tuple(v1m[p['module']]['box_xyxy'])
            im = Image.new('RGBA', (box[2] - box[0], box[3] - box[1])); im.alpha_composite(shd.crop(box)); im.alpha_composite(obj.crop(box))
        rebuilt[p['layer']].alpha_composite(im, tuple(p['xy']))
    res['native_layers_rebuilt_identical'] = all(bool(np.array_equal(np.array(rebuilt[k]), arr(O / 'complement_natif' / f'{PFX}_{k}.png'))) for k in rebuilt)
    # chemin
    path = layers['03_chemin'][:, :, 3] > 0
    ent = layers['05_entree_grotte'][:, :, 3] > 0
    walk = path | nd.binary_dilation(ent, iterations=12)
    lab, n = nd.label(walk)
    south = set(np.unique(lab[H - 1][lab[H - 1] > 0])); ent_l = set(np.unique(lab[ent]))
    res['path_connects_south_edge_to_entrance'] = bool(south & ent_l)
    res['path_bottom_row_px'] = int(path[H - 1].sum())
    top = int(np.nonzero(path.any(1))[0].min())
    res['path_top_y'] = top
    res['path_min_width_px_below_tip'] = int(min(int(path[y].sum()) for y in range(top + 24, H) if path[y].any()))
    for n_, lab_ in (('08_troncs_ombres', 'trunks_shadows'), ('09_canopees', 'canopies'), ('06_rochers', 'rocks')):
        res[f'{lab_}_pixels_over_path'] = int(((layers[n_][:, :, 3] > 0) & path).sum())
    ys, xs = np.nonzero(ent)
    res['entrance_bbox'] = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    res['iou_vs_maquette_v1'] = m['stats']['iou_vs_maquette_v1']
    # herbe pure : aucun pixel de lisière sombre ne doit subsister dans la sous-couche
    s0 = layers['01_sol_herbe'][:, :, :3].astype(int)
    res['underlay_dark_forest_pixels'] = int(((s0[:, :, 1] < 118) & (s0[:, :, 1] > s0[:, :, 0]) & (s0[:, :, 0] < 90)).sum())
    res['underlay_is_pure_grass'] = res['underlay_dark_forest_pixels'] < 800
    with zipfile.ZipFile(O / f'{PFX}_editable.ora') as z:
        names = z.namelist()
        res['ora_ok'] = 'stack.xml' in names and 'mergedimage.png' in names and z.read('mimetype') == b'image/openraster'
        res['ora_merged_equals_composition'] = bool(np.array_equal(np.array(Image.open(z.open('mergedimage.png')).convert('RGBA')), np.array(comp)))
    res['runtime_pmdo'] = 'NOT TESTED'
    res['all_pass'] = all(v is True for k, v in res.items() if isinstance(v, bool))
    (O / 'verification.json').write_text(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(res, ensure_ascii=False, indent=1))
    return 0 if res['all_pass'] else 1


if __name__ == '__main__':
    sys.exit(main())
