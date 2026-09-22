"""Aride finale magenta V3 — 6 elements generes sur fond magenta, normalises /3,
remappes palette native (99 couleurs de la reference), assembles sud -> nord.

Bruts (tous 1224x864) : cliff_magenta, sol_magenta, chemin_magenta,
props_magenta (arbres + roches), ombre_magenta.
Rejetes/archives : parois_magenta (bol), fx_magenta (non demande), guide_compo_v2.

Canvas final 408x288, grille 8 px. Motifs generes, palette 100% native.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image
from scipy.ndimage import label as ndlabel, binary_erosion, distance_transform_edt

R = Path(__file__).resolve().parents[2]
SRC = Path(__file__).resolve().parent
BRUTS = SRC / 'bruts'
OUT = R / 'renders' / 'aride_finale_magenta_v3'
REF = R / 'entrancearidedungeonpmdsky.png'
CW, CH = 408, 288
MAGENTA = np.array([255, 0, 255])
D_MAG = 170  # seuil magenta-like (meme recette que V2 session parallele)

# Placements (x, y) du COIN HAUT-GAUCHE de chaque sprite, pieds sur grille 8 px.
# Regles visuellement : Om_B* ombres des blocs, Om_A* ombres des arbres,
# mur = bandeau d'ombre au pied du cliff.
PLACEMENTS = {
    'arbre0': (28, 160), 'arbre1': (309, 164), 'arbre2': (244, 168), 'arbre3': (104, 175),
    'bloc0': (4, 224), 'bloc1': (257, 241),
    'caillou0': (128, 228), 'caillou1': (200, 236), 'caillou2': (124, 252),
    'caillou3': (196, 260), 'caillou4': (132, 272), 'caillou5': (208, 276),
}


def ref_palette():
    a = np.array(Image.open(REF).convert('RGB')).reshape(-1, 3)
    return np.unique(a, axis=0).astype(int)


def flood_keep(rgb):
    """Masque des pixels a garder : tout sauf le magenta inonde depuis les bords."""
    d = np.sqrt(((rgb.astype(int) - MAGENTA) ** 2).sum(axis=2))
    mag = d < D_MAG
    lab, _ = ndlabel(mag)
    border_ids = set(np.unique(np.concatenate([lab[0, :], lab[-1, :], lab[:, 0], lab[:, -1]])))
    border_ids.discard(0)
    bg = np.isin(lab, list(border_ids)) | mag  # fond + residus magenta interieurs
    keep = ~bg
    keep = binary_erosion(keep, iterations=2)  # pelage AA rose (recette V2)
    return keep


def down3(rgba):
    return np.array(Image.fromarray(rgba).resize((CW, CH), Image.NEAREST))


def remap(rgba, pal):
    rgb = rgba[:, :, :3].astype(int)
    d = ((rgb[:, :, None, :] - pal[None, None, :, :]) ** 2).sum(axis=3)
    rgba[:, :, :3] = pal[d.argmin(axis=2)]
    rgba[:, :, :3][rgba[:, :, 3] == 0] = 0  # RGB zero sous alpha 0 (lecon V10)
    return rgba, np.sqrt(d.min(axis=2))


def extract(name):
    rgb = np.array(Image.open(BRUTS / f'{name}.png').convert('RGB'))
    assert rgb.shape[:2] == (864, 1224), rgb.shape
    keep = flood_keep(rgb)
    rgba = np.dstack([rgb, (keep * 255).astype(np.uint8)])
    rgba = down3(rgba)
    return rgba


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'sprites').mkdir(exist_ok=True)
    pal = ref_palette()
    assert len(pal) == 99
    dists = {}

    # --- L00 sol plein cadre ---
    sol = extract('sol_magenta')
    sol, d = remap(sol, pal)
    dists['sol'] = float(d[sol[:, :, 3] > 0].mean())
    hole = sol[:, :, 3] == 0
    print('sol: trous a reboucher:', int(hole.sum()))
    if hole.any():
        # rebouchage par sable natif le plus proche (cadre magenta uniquement)
        _, (yy, xx) = distance_transform_edt(hole, return_indices=True)
        sand = (sol[:, :, 3] > 0)
        assert sand.any()
        filled = sol.copy()
        filled[holeswap(hole)] = sol[yy[holeswap(hole)], xx[holeswap(hole)]]
        filled[holeswap(hole), 3] = 255
        sol = filled
    L00 = sol

    # --- L01 chemin (plein cadre, transparent hors sentier) ---
    chemin = extract('chemin_magenta')
    chemin, d = remap(chemin, pal)
    dists['chemin'] = float(d[chemin[:, :, 3] > 0].mean())
    # le sentier s'arrete au seuil de la bouche (pas d'empreintes dans le noir)
    chemin[0:96, 172:238] = 0
    L01 = chemin

    # --- L02 cliff (parois + bouche, corridor transparent) ---
    cliff = extract('cliff_magenta')
    cliff, d = remap(cliff, pal)
    dists['cliff'] = float(d[cliff[:, :, 3] > 0].mean())
    L02 = cliff
    # bbox bouche = composante sombre haute centrale (controle)
    lum = L02[:, :, :3].astype(int).sum(axis=2)
    dark = (L02[:, :, 3] > 0) & (lum < 200)
    dark[:40, :] = False
    lab, n = ndlabel(dark)
    mouth = None
    for i in range(1, n + 1):
        ys, xs = np.where(lab == i)
        if len(xs) > 300 and 120 < xs.mean() < 290 and ys.mean() < 140:
            mouth = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
            break
    print('bouche:', mouth)

    # --- props : split par composantes connexes ---
    props = extract('props_magenta')
    props, d = remap(props, pal)
    dists['props'] = float(d[props[:, :, 3] > 0].mean())
    lab, n = ndlabel(props[:, :, 3] > 0)
    comps = []
    for i in range(1, n + 1):
        ys, xs = np.where(lab == i)
        if len(xs) > 60:
            comps.append({'n': len(xs), 'x0': int(xs.min()), 'y0': int(ys.min()),
                          'x1': int(xs.max()) + 1, 'y1': int(ys.max()) + 1})
    comps.sort(key=lambda c: -c['n'])
    print('props composantes:', len(comps), [(c['x0'], c['y0'], c['x1'], c['y1']) for c in comps])
    # tri : 4 arbres (hauts), 2 blocs (larges), 6 cailloux (petits)
    by_h = sorted(comps, key=lambda c: -(c['y1'] - c['y0']))
    sprites = {}
    for k, c in zip(['arbre0', 'arbre1', 'arbre2', 'arbre3'], by_h[:4]):
        sprites[k] = cut(props, c)
    rest = by_h[4:]
    rest.sort(key=lambda c: -c['n'])
    for k, c in zip(['bloc0', 'bloc1'], rest[:2]):
        sprites[k] = cut(props, c)
    small = sorted(rest[2:], key=lambda c: (c['y0'], c['x0']))[:6]
    for k, c in zip([f'caillou{i}' for i in range(6)], small):
        sprites[k] = cut(props, c)
    for k, v in sprites.items():
        Image.fromarray(v).save(OUT / 'sprites' / f'{k}.png')

    # --- L05 ombres : split + alpha uniforme ---
    omb = extract('ombre_magenta')
    omb, d = remap(omb, pal)
    lab, n = ndlabel(omb[:, :, 3] > 0)
    ocomps = []
    for i in range(1, n + 1):
        ys, xs = np.where(lab == i)
        if len(xs) > 200:
            ocomps.append({'n': len(xs), 'x0': int(xs.min()), 'y0': int(ys.min()),
                           'x1': int(xs.max()) + 1, 'y1': int(ys.max()) + 1})
    ocomps.sort(key=lambda c: -c['n'])
    print('ombres composantes:', len(ocomps), [(c['x0'], c['y0'], c['x1'], c['y1']) for c in ocomps])
    # 0 = bandeau mur, 1-2 = rondes arbres, 3-4 = ovales blocs
    om_sprites = [cut(omb, c) for c in ocomps[:5]]
    for s in om_sprites:
        s[:, :, 3][s[:, :, 3] > 0] = 110  # translucidite d'assemblage (documentee)
        s[:, :, :3][s[:, :, 3] == 0] = 0
    names = ['mur', 'ovale0', 'ovale1', 'ronde0', 'ronde1']
    for k, v in zip(names, om_sprites):
        Image.fromarray(v).save(OUT / 'sprites' / f'ombre_{k}.png')

    # --- assemblage ---
    H, W = CH, CW
    L03 = np.zeros((H, W, 4), np.uint8)  # roches
    L04 = np.zeros((H, W, 4), np.uint8)  # arbres
    L05 = np.zeros((H, W, 4), np.uint8)  # ombres
    for k in ['bloc0', 'bloc1'] + [f'caillou{i}' for i in range(6)]:
        paste(L03, sprites[k], PLACEMENTS[k])
    for k in ['arbre0', 'arbre1', 'arbre2', 'arbre3']:
        paste(L04, sprites[k], PLACEMENTS[k])
    # ombres sous chaque prop + bandeau au pied du cliff
    for k, sh in [('bloc0', 'ovale0'), ('bloc1', 'ovale1')]:
        x, y = PLACEMENTS[k]
        sw, shh = om_sprites[names.index(sh)].shape[1], om_sprites[names.index(sh)].shape[0]
        pw = sprites[k].shape[1]
        paste(L05, om_sprites[names.index(sh)], (x + pw // 2 - sw // 2, y + sprites[k].shape[0] - shh // 2))
    for k, sh in [('arbre0', 'ronde0'), ('arbre1', 'ronde1'), ('arbre2', 'ronde0'), ('arbre3', 'ronde1')]:
        x, y = PLACEMENTS[k]
        o = om_sprites[names.index(sh)]
        paste(L05, o, (x + sprites[k].shape[1] // 2 - o.shape[1] // 2, y + sprites[k].shape[0] - o.shape[0] // 2))
    # bandeau mur : centre en x, juste sous la base du cliff (y estime, regle visuellement)
    o = om_sprites[0]
    paste(L05, o, (CW // 2 - o.shape[1] // 2, 150 - o.shape[0] // 2))
    # les chevauchements translucides melangent les RGB : requantifier palette native
    m5 = L05[:, :, 3] > 0
    d5 = ((L05[:, :, :3].astype(int)[:, :, None, :] - pal[None, None, :, :]) ** 2).sum(axis=3)
    L05[:, :, :3][m5] = pal[d5.argmin(axis=2)[m5]]

    layers = {'L00_sol': L00, 'L01_chemin': L01, 'L02_cliff': L02,
              'L03_roches': L03, 'L04_arbres': L04, 'L05_ombres': L05}
    for k, v in layers.items():
        Image.fromarray(v).save(OUT / f'{k}.png')
        print(k, 'opaques:', int((v[:, :, 3] > 0).sum()))
    comp = Image.fromarray(L00)
    for k in ['L01_chemin', 'L02_cliff', 'L05_ombres', 'L03_roches', 'L04_arbres']:
        comp.alpha_composite(Image.fromarray(layers[k]))
    comp.save(OUT / 'composite.png')

    # --- review acces sud -> bouche ---
    ground = (L00[:, :, 3] > 0)
    blocked = (L02[:, :, 3] > 0) & ~mouth_door(L02, mouth)
    walk = ground & ~blocked
    start = (CW // 2, CH - 4)
    seen = flood(walk, start)
    goal = ((mouth[0] + mouth[2]) // 2, mouth[3] + 2) if mouth else (CW // 2, 100)
    ok = bool(seen[min(goal[1], CH - 1), goal[0]])
    print('acces sud->bouche:', ok, 'start', start, 'goal', goal)
    vis = np.array(comp.convert('RGB'))
    vis[~walk] = vis[~walk] // 2 + np.array([80, 0, 0])
    Image.fromarray(vis).save(OUT / 'access_review.png')

    manifest = {
        'canvas': [CW, CH], 'grille_px': 8,
        'methode': 'generateur sur fond magenta -> inondation + pelage 2px -> /3 NEAREST -> remap palette native 99 couleurs sans trame',
        'bruts': {b: [1224, 864] for b in ['cliff_magenta', 'sol_magenta', 'chemin_magenta', 'props_magenta', 'ombre_magenta']},
        'rejetes': ['parois_magenta (bol avec fond)', 'fx_magenta (non demande)', 'guide_compo_v2 (plein cadre, hors methode magenta)'],
        'remap_dist_moy': dists,
        'bouche_bbox': mouth,
        'placements': PLACEMENTS,
        'ombres_alpha': 110,
        'acces_sud_bouche': ok,
        'ordre': ['L00_sol', 'L01_chemin', 'L02_cliff', 'L05_ombres', 'L03_roches', 'L04_arbres'],
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    print('OK', OUT)


def holeswap(hole):
    return hole


def cut(rgba, c):
    return rgba[c['y0']:c['y1'], c['x0']:c['x1']].copy()


def paste(dst, spr, xy):
    x, y = xy
    h, w = spr.shape[:2]
    x0, y0 = max(x, 0), max(y, 0)
    x1, y1 = min(x + w, dst.shape[1]), min(y + h, dst.shape[0])
    if x1 <= x0 or y1 <= y0:
        return
    s = spr[y0 - y:y1 - y, x0 - x:x1 - x]
    d = dst[y0:y1, x0:x1]
    m = s[:, :, 3] > 0
    # ombres (alpha partiel) : over ; opaques : remplacement
    if (s[:, :, 3][m] < 255).any():
        # vrai over alpha
        sa = s[:, :, 3:4].astype(float) / 255
        da = d[:, :, 3:4].astype(float) / 255
        oa = sa + da * (1 - sa)
        rgb = (s[:, :, :3].astype(float) * sa + d[:, :, :3].astype(float) * da * (1 - sa)) / np.maximum(oa, 1e-6)
        d[:, :, :3] = np.where(m[:, :, None], rgb, d[:, :, :3]).astype(np.uint8)
        d[:, :, 3] = np.where(m, (oa[:, :, 0] * 255), d[:, :, 3]).astype(np.uint8)
    else:
        d[m] = s[m]


def mouth_door(L02, mouth):
    """Le seuil devant la bouche reste marchable (petit rectangle sous la bbox)."""
    m = np.zeros(L02.shape[:2], bool)
    if mouth:
        x0, y0, x1, y1 = mouth
        m[y1:min(y1 + 10, L02.shape[0]), x0:x1] = True
    return m


def flood(walk, start):
    from collections import deque
    H, W = walk.shape
    seen = np.zeros_like(walk)
    sx, sy = start
    if not walk[sy, sx]:
        return seen
    dq = deque([(sx, sy)])
    seen[sy, sx] = True
    while dq:
        x, y = dq.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < W and 0 <= ny < H and walk[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True
                dq.append((nx, ny))
    return seen


if __name__ == '__main__':
    main()
