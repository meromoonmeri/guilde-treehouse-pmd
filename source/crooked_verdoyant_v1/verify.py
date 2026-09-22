"""Vérification indépendante de renders/crooked_verdoyant_v1 → verification.json.

Contrôles : tailles/alignement, partition exacte des calques visibles, recomposition == scène normalisée,
sous-couche opaque, nuit == filtre Abyss exact, pixels natifs du complément inchangés (translation seule),
connexité du chemin bord sud → entrée nord, SHA-256 des bruts conformes au manifeste.
Aucun test moteur PMDO (non installé) : ce script ne prouve ni collisions ni warps.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
import numpy as np
import scipy.ndimage as nd
from PIL import Image

R = Path(__file__).resolve().parents[2]
O = R / 'renders/crooked_verdoyant_v1'
sys.path.insert(0, str(R / 'source/cote_v4_abyss'))
from night import night  # noqa: E402

PFX = 'CrookedVerdoyantV1'
W, H = 512, 640
VIS = ['02_herbe_visible', '03_lisiere_foret', '04_chemin_visible', '05_parois_crooked', '06_entree_grotte',
       '07_rochers', '08_vegetation_basse', '09_arbres']


def arr(p):
    return np.array(Image.open(p).convert('RGBA'))


def main():
    m = json.loads((O / 'manifest.json').read_text())
    res = {}
    # 1) bruts inchangés
    res['bruts_sha256_ok'] = all(hashlib.sha256((R / v['path']).read_bytes()).hexdigest() == v['sha256'] for v in m['bruts'].values())
    S = np.array(Image.open(R / m['bruts']['scene']['path']).convert('RGBA').resize((W, H), Image.NEAREST))
    U = np.array(Image.open(R / m['bruts']['sol']['path']).convert('RGBA').resize((W, H), Image.NEAREST))
    res['scene_512x640_matches_brut_nearest'] = bool(np.array_equal(S, arr(O / 'bruts/scene_complete_512x640.png')))
    # 2) calques : tailles, partition, recomposition
    layers = {n: arr(O / 'calques' / f'{PFX}_{n}.png') for n in ['01_sol_complet'] + VIS}
    res['all_layers_512x640'] = all(a.shape == (H, W, 4) for a in layers.values())
    cover = np.zeros((H, W), int)
    for n in VIS:
        cover += (layers[n][:, :, 3] > 0).astype(int)
    res['visible_layers_exact_partition'] = bool(cover.min() == 1 and cover.max() == 1)
    comp = Image.new('RGBA', (W, H))
    for n in VIS:
        comp.alpha_composite(Image.fromarray(layers[n]))
    res['recomposition_equals_scene'] = bool(np.array_equal(np.array(comp), S))
    res['composition_jour_file_equals_scene'] = bool(np.array_equal(arr(O / 'composition_jour.png'), S))
    res['underlay_opaque_and_equals_sol_brut'] = bool(layers['01_sol_complet'][:, :, 3].min() == 255 and np.array_equal(layers['01_sol_complet'], U))
    # pixels de chaque calque = pixels de la scène (aucune retouche)
    res['layer_pixels_identical_to_scene'] = all(bool(np.array_equal(layers[n][layers[n][:, :, 3] > 0], S[layers[n][:, :, 3] > 0])) for n in VIS)
    # masques cohérents avec les calques
    res['masks_match_layers'] = all(bool(np.array_equal(np.array(Image.open(O / 'masques' / f'{PFX}_masque_{n}.png')) > 0, layers[n][:, :, 3] > 0)) for n in VIS)
    # 3) nuit
    res['night_layers_exact_abyss'] = all(bool(np.array_equal(arr(O / 'nuit' / f'{PFX}_{n}_nuit.png'), np.array(night(Image.fromarray(layers[n]))))) for n in layers)
    res['composition_nuit_equals_night_of_jour'] = bool(np.array_equal(arr(O / 'composition_nuit.png'), np.array(night(Image.fromarray(S)))))
    # 4) complément natif : chaque module posé = pixels sources exacts (translation seule ; chevauchement autorisé
    #    seulement par un module posé après lui dans le même calque)
    obj = Image.open(R / 'banque_canonique/atlas/Halcyon__Crooked_Cavern_Objects.png').convert('RGBA')
    shd = Image.open(R / 'banque_canonique/atlas/Halcyon__Crooked_Cavern_Shadows.png').convert('RGBA')
    trunks = Image.open(R / 'source/amp_plains_fleurie_v1/references/vast_steppe_layer_3.png').convert('RGBA')
    fol = Image.open(R / 'source/amp_plains_fleurie_v1/references/vast_steppe_layer_4.png').convert('RGBA')
    tree = Image.new('RGBA', (144, 120)); tree.alpha_composite(trunks.crop((72, 160, 120, 216)), (56, 64)); tree.alpha_composite(fol.crop((16, 96, 160, 216)), (0, 0))
    nat = {'10_rochers_natifs_crooked': arr(O / 'complement_natif' / f'{PFX}_10_rochers_natifs_crooked.png'),
           '11_arbres_natifs_steppe': arr(O / 'complement_natif' / f'{PFX}_11_arbres_natifs_steppe.png')}
    rebuilt = {k: Image.new('RGBA', (W, H)) for k in nat}
    for p in m['native_placements']:
        if p['module'] == 'arbre_steppe':
            im = tree
        else:
            box = tuple(m['native_modules'][p['module']]['box_xyxy'])
            im = Image.new('RGBA', (box[2] - box[0], box[3] - box[1])); im.alpha_composite(shd.crop(box)); im.alpha_composite(obj.crop(box))
        rebuilt[p['layer']].alpha_composite(im, tuple(p['xy']))
    res['native_layers_rebuilt_identical'] = all(bool(np.array_equal(np.array(rebuilt[k]), nat[k])) for k in nat)
    res['native_layers_only_translation'] = res['native_layers_rebuilt_identical']
    res['native_placements_count'] = len(m['native_placements'])
    # 5) chemin : connexité bord sud → entrée (masque chemin ∪ entrée ∪ seuil), largeur ≥ 16 px sur tout le tracé
    path = layers['04_chemin_visible'][:, :, 3] > 0
    cave = layers['06_entree_grotte'][:, :, 3] > 0
    walk = path | nd.binary_dilation(cave, iterations=12)
    lab, n = nd.label(walk)
    south = set(np.unique(lab[H - 1][lab[H - 1] > 0]))
    cave_labels = set(np.unique(lab[cave]))
    res['path_connects_south_edge_to_cave'] = bool(south & cave_labels)
    top = int(np.nonzero(path.any(1))[0].min())
    rows_with_path = [int((path[y]).sum()) for y in range(top + 24, H) if path[y].any()]
    res['path_min_width_px_below_tip'] = int(min(rows_with_path)) if rows_with_path else 0
    res['path_top_y'] = int(np.nonzero(path.any(1))[0].min()) if path.any() else None
    res['cave_bbox'] = [int(v) for v in (np.nonzero(cave.any(0))[0].min(), np.nonzero(cave.any(1))[0].min(), np.nonzero(cave.any(0))[0].max(), np.nonzero(cave.any(1))[0].max())]
    # 6) ORA présent et cohérent
    import zipfile
    with zipfile.ZipFile(O / f'{PFX}_editable.ora') as z:
        names = z.namelist()
        res['ora_ok'] = 'stack.xml' in names and 'mergedimage.png' in names and z.read('mimetype') == b'image/openraster'
        merged = np.array(Image.open(z.open('mergedimage.png')).convert('RGBA'))
    res['ora_merged_equals_scene'] = bool(np.array_equal(merged, S))
    res['runtime_pmdo'] = 'NOT TESTED'
    res['all_pass'] = all(v is True for k, v in res.items() if isinstance(v, bool))
    (O / 'verification.json').write_text(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(res, ensure_ascii=False, indent=1))
    return 0 if res['all_pass'] else 1


if __name__ == '__main__':
    sys.exit(main())
