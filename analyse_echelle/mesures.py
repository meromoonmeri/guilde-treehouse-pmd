# -*- coding: utf-8 -*-
"""
Mesure comparative d'echelle : guilde du projet vs guilde de Halcyon (Palikadude).

Unites de reference PMD / RogueEssence-PMDO :
  - bloc de collision d'une ground map      : 8 px
  - "case" de donjon PMD (unite de lecture) : 24 px
  - collider d'un personnage en ground map  : 16 x 16 px
  - sprite visible d'un Pokemon moyen       : ~20 x 22 px (mesure sur les .chara de Halcyon)

Sorties : analyse_echelle/mesures.json
"""
import json, io, os, sys, glob
import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rsread import load_ground, render_ground

TILE = 24          # case PMD de reference
BLOCK = 8          # bloc de collision ground map
SPRITE_W, SPRITE_H = 20, 22   # sprite Pokemon moyen mesure (Charmander idle)
COLLIDER = 16

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HALCYON = os.environ.get('HALCYON_DIR', '/home/user/halcyon')


# ----------------------------------------------------------------- outils

def runs(line):
    """longueurs des segments continus True"""
    out, s = [], None
    for i, v in enumerate(line):
        if v and s is None:
            s = i
        elif not v and s is not None:
            out.append(i - s); s = None
    if s is not None:
        out.append(len(line) - s)
    return out


def mask_metrics(mask, label, px_per_unit=1):
    """mask : ndarray bool (H, W) en pixels, True = sol praticable."""
    H, W = mask.shape
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    bw, bh = x1 - x0, y1 - y0
    area = int(mask.sum())

    # segments horizontaux / verticaux (largeurs de circulation)
    hr = [r for y in range(y0, y1) for r in runs(mask[y]) if r >= BLOCK]
    vr = [r for x in range(x0, x1) for r in runs(mask[:, x]) if r >= BLOCK]

    # distance au mur le plus proche (vide autour d'un personnage)
    dist = ndimage.distance_transform_edt(mask)
    dmax = float(dist.max())
    dmean = float(dist[mask].mean())
    dmed = float(np.median(dist[mask]))

    # mobilier / trous interieurs = trous du masque praticable
    filled = ndimage.binary_fill_holes(mask)
    holes = filled & ~mask
    hole_area = int(holes.sum())
    n_holes, _ = ndimage.label(holes)
    n_holes = int(n_holes.max()) if hasattr(n_holes, 'max') else 0
    lbl, n_holes = ndimage.label(holes)

    d = {
        'nom': label,
        'canvas_px': [int(W), int(H)],
        'bbox_sol_px': [int(bw), int(bh)],
        'bbox_sol_cases24': [round(bw / TILE, 1), round(bh / TILE, 1)],
        'bbox_sol_blocs8': [int(round(bw / BLOCK)), int(round(bh / BLOCK))],
        'aire_sol_px2': area,
        'aire_sol_cases24': round(area / (TILE * TILE), 1),
        'aire_sol_colliders16': round(area / (COLLIDER * COLLIDER), 1),
        'taux_remplissage_bbox': round(area / float(bw * bh), 3),
        'largeur_circulation_px': {
            'mediane': int(np.median(hr)) if hr else 0,
            'p90': int(np.percentile(hr, 90)) if hr else 0,
            'max': int(max(hr)) if hr else 0,
        },
        'hauteur_circulation_px': {
            'mediane': int(np.median(vr)) if vr else 0,
            'p90': int(np.percentile(vr, 90)) if vr else 0,
            'max': int(max(vr)) if vr else 0,
        },
        'distance_mur_px': {'max': round(dmax, 1), 'moyenne': round(dmean, 1)},
        'distance_mur_cases24': {'max': round(dmax / TILE, 2), 'moyenne': round(dmean / TILE, 2)},
        # largeur locale = 2 x distance au mur : "epaisseur" reelle de l'espace
        'largeur_locale_cases24': {'mediane': round(2 * dmed / TILE, 2),
                                   'max': round(2 * dmax / TILE, 2)},
        'mobilier_trous_px2': hole_area,
        'mobilier_trous_cases24': round(hole_area / (TILE * TILE), 1),
        'mobilier_nb_ilots': int(n_holes),
        'ratio_aire_sol_sur_sprite': round(area / float(SPRITE_W * SPRITE_H), 1),
        'largeur_en_sprites': round(bw / float(SPRITE_W), 1),
        'hauteur_en_sprites': round(bh / float(SPRITE_H), 1),
        'ecrans_320x240': round((bw * bh) / (320.0 * 240.0), 2),
    }
    return d


# ------------------------------------------------------- lecture Halcyon

RENDER_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rendus_halcyon')


def halcyon_room(path):
    """Halcyon ne peint la collision qu'autour des zones jouables : le vide hors
    piece reste 'non bloque'. On ne garde donc que la composante praticable
    reellement atteignable depuis les marqueurs d'entree."""
    g = load_ground(path)
    name = os.path.basename(path).replace('.rsground', '')
    os.makedirs(RENDER_DIR, exist_ok=True)
    cache = os.path.join(RENDER_DIR, name + '.png')
    if os.path.exists(cache):
        render = Image.open(cache).convert('RGBA')
    else:
        render = render_ground(g, HALCYON)
        render.save(cache)
    ob = g['obstacles']
    W, H = len(ob), len(ob[0])
    walk = np.zeros((H * BLOCK, W * BLOCK), dtype=bool)
    for x in range(W):
        for y in range(H):
            if ob[x][y]['Tags'] == 0:
                walk[y * BLOCK:(y + 1) * BLOCK, x * BLOCK:(x + 1) * BLOCK] = True

    # le sol reellement peint (calque Floor) : evite de compter le vide hors piece
    floor_layers = [L for L in g['Layers'] if 'Floor' in L['Name']] or g['Layers'][:1]
    floor = np.zeros((H, W), dtype=bool)
    for L in floor_layers:
        T = L['Tiles']
        for x in range(W):
            for y in range(H):
                for sub in T[x][y]['Layers']:
                    if sub['Frames'][0]['Sheet']:
                        floor[y, x] = True
    walk &= np.kron(floor, np.ones((BLOCK, BLOCK), dtype=bool))

    # le vide hors batiment n'est ni peint ni bloque : on le retire a partir du
    # rendu composite (pixels transparents, ou couleur de fond uniforme du bord)
    rgba = np.array(render)
    body = rgba[:, :, 3] > 0
    border = np.concatenate([rgba[0, :, :3], rgba[-1, :, :3],
                             rgba[:, 0, :3], rgba[:, -1, :3]])
    cols, cnt = np.unique(border, axis=0, return_counts=True)
    dom = cols[int(np.argmax(cnt))]
    if cnt.max() > 0.5 * len(border):
        void = np.all(rgba[:, :, :3] == dom[None, None, :], axis=2) & (rgba[:, :, 3] > 0)
        if void.mean() > 0.02:
            body &= ~void
    body = ndimage.binary_closing(body, np.ones((3, 3), dtype=bool))
    walk &= body

    ent = g['Entities'][0]
    seeds, entrances = [], []
    for src in (ent['Markers'], ent['MapChars'], ent['GroundObjects'], ent['Spawners']):
        for o in src:
            c = o.get('Collider')
            if not c:
                continue
            pt = (int(c['Y'] + c['Height'] / 2), int(c['X'] + c['Width'] / 2))
            seeds.append(pt)
            if 'ntrance' in o.get('EntName', '') or 'pawn' in o.get('EntName', ''):
                entrances.append(pt)
    lbl, n = ndimage.label(walk)
    sizes = ndimage.sum(walk, lbl, range(1, n + 1))

    def comps(points):
        return {int(lbl[y, x]) for (y, x) in points
                if 0 <= y < walk.shape[0] and 0 <= x < walk.shape[1] and lbl[y, x]}

    keep = comps(entrances)
    if not keep:
        keep = comps(seeds)
    # on ecarte les eclats de collision isoles (< 15 % de la plus grande piece)
    if keep:
        top = max(sizes[c - 1] for c in keep)
        keep = {c for c in keep if sizes[c - 1] >= 0.15 * top}
    if not keep or max(sizes[c - 1] for c in keep) < 0.25 * sizes.max():
        keep = {int(np.argmax(sizes)) + 1}
    walk = np.isin(lbl, list(keep))

    # surfaces couvertes par les calques de mobilier / decor
    prop = np.zeros((H, W), dtype=bool)
    for L in g['Layers']:
        if 'Object' not in L['Name']:
            continue
        T = L['Tiles']
        for x in range(W):
            for y in range(H):
                for sub in T[x][y]['Layers']:
                    if sub['Frames'][0]['Sheet']:
                        prop[y, x] = True

    # on ne compte que le decor pose dans l'espace jouable ou a son contact
    zone = ndimage.binary_dilation(walk, np.ones((BLOCK * 3, BLOCK * 3), dtype=bool))
    prop_px = np.kron(prop, np.ones((BLOCK, BLOCK), dtype=bool)) & zone

    m = mask_metrics(walk, name)
    m['decor_blocs8'] = int(prop_px.sum() // (BLOCK * BLOCK))
    m['decor_cases24'] = round(prop_px.sum() / float(TILE * TILE), 1)
    m['decor_pct_du_sol'] = round(100.0 * prop_px.sum() / max(1, int(walk.sum())), 1)
    ent = g['Entities'][0]
    m['carte_px'] = [W * BLOCK, H * BLOCK]
    m['carte_cases24'] = [round(W * BLOCK / TILE, 1), round(H * BLOCK / TILE, 1)]
    m['nb_calques_tuiles'] = len(g['Layers'])
    m['calques'] = [l['Name'] for l in g['Layers']]
    m['nb_objets_sol'] = len(ent['GroundObjects'])
    m['nb_pnj'] = len(ent['MapChars'])
    m['nb_marqueurs'] = len(ent['Markers'])
    m['nb_decors_animes'] = sum(len(d['Anims']) for d in g['Decorations'])
    return m


# ------------------------------------------------------- lecture projet

def projet_room(folder):
    sol = os.path.join(REPO, 'calques', folder, 'jour', '01_sol.png')
    im = Image.open(sol).convert('RGBA')
    q = np.array(im)
    # un trou de plancher (pixels tres sombres) n'est pas de la surface jouable
    walk = (q[:, :, 3] > 8) & (q[:, :, :3].mean(2) > 70)
    lbl, n = ndimage.label(walk)
    if n > 1:
        sizes = ndimage.sum(walk, lbl, range(1, n + 1))
        walk = lbl == (int(np.argmax(sizes)) + 1)
    m = mask_metrics(walk, folder)
    m['carte_px'] = list(im.size)
    m['carte_cases24'] = [round(im.size[0] / TILE, 1), round(im.size[1] / TILE, 1)]
    # densite de decor reellement posee dans les calques
    props = 0
    for c in ('06_decorations', '07_objets'):
        p = os.path.join(REPO, 'calques', folder, 'jour', c + '.png')
        if os.path.exists(p):
            aa = np.array(Image.open(p).convert('RGBA'))[:, :, 3]
            props += int((aa > 8).sum())
    m['pixels_decor_poses'] = props
    m['decor_cases24'] = round(props / float(TILE * TILE), 1)
    m['decor_pct_du_sol'] = round(100.0 * props / max(1, int(walk.sum())), 1)
    return m


def main():
    out = {'unites': {'case_px': TILE, 'bloc_collision_px': BLOCK,
                      'collider_perso_px': COLLIDER,
                      'sprite_moyen_px': [SPRITE_W, SPRITE_H]},
           'projet': [], 'halcyon': []}

    kit = json.load(open(os.path.join(REPO, 'kit.json'), encoding='utf-8'))
    for s in kit['salles']:
        m = projet_room(s['dossier'])
        m['id'] = s['id']; m['titre'] = s['nom']
        out['projet'].append(m)

    for p in sorted(glob.glob(os.path.join(HALCYON, 'Data', 'Ground', 'guild_*.rsground'))):
        out['halcyon'].append(halcyon_room(p))
    for extra in ('metano_inn', 'metano_cafe', 'ledian_dojo', 'metano_normal_home'):
        p = os.path.join(HALCYON, 'Data', 'Ground', extra + '.rsground')
        if os.path.exists(p):
            out['halcyon'].append(halcyon_room(p))

    dest = os.path.join(REPO, 'analyse_echelle', 'mesures.json')
    with io.open(dest, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print('ecrit', dest)


if __name__ == '__main__':
    main()
