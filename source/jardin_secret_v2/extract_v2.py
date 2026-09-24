"""Jardin secret v2 — extraction des bruts magenta : détourage, échelle canonique, palette, sprites.

Échelles :
- arbres : largeur de cime ramenée à 126 px = cime de l'arbre Halcyon Vast Steppe 144×120
  (source/zones_south_north_v3/references/native_tree_complete.png, bbox 8..133) ;
- fleurs : cellules 24×24 = Vast_Steppe_Flower_Animations.png (3 poses, séquence 0,1,0,2) ;
- souche + temple : souche ramenée à 100 px de large = souche de secretgarden.png (100×80).
"""
import json, os
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
OUT = 'travail/sprites_v2'
os.makedirs(OUT, exist_ok=True)
REF = np.array(Image.open('../../secretgarden.png').convert('RGB'))
PAL_REF = np.unique(REF.reshape(-1, 3), axis=0).astype(np.int32)
WGT = np.array([3, 4, 2])


def snap_to(rgb, pal):
    flat = rgb.reshape(-1, 3).astype(np.int32)
    u, inv = np.unique(flat, axis=0, return_inverse=True)
    d = (((u[:, None, :] - pal[None]) ** 2) * WGT).sum(-1)
    return pal[d.argmin(1)][inv.ravel()].reshape(rgb.shape).astype(np.uint8)


def own_palette(rgba_list, n):
    """Palette limitée propre au lot (pour les couleurs absentes de la référence : rouge du temple, jaune des fleurs)."""
    px = np.concatenate([a[a[..., 3] > 0][:, :3] for a in rgba_list])
    im = Image.fromarray(px[None].astype(np.uint8)).quantize(n, method=Image.Quantize.MEDIANCUT)
    pal = np.array(im.getpalette()[:n * 3]).reshape(-1, 3)
    return pal.astype(np.int32)


def key_magenta(rgb, fringe=3):
    r, g, b = [rgb[..., i].astype(int) for i in range(3)]
    bg = (r > 150) & (b > 150) & (g < 120)
    a = ~bg
    near = ndi.binary_dilation(bg, iterations=fringe)
    a &= ~(near & (b > g + 10) & (r > g + 10))
    lab, n = ndi.label(a)
    if n:
        sz = ndi.sum(a, lab, range(1, n + 1))
        a = np.isin(lab, 1 + np.flatnonzero(sz >= 30))
    return a


def downscale(rgb, a, size):
    """Réduction « pixel artist » : moyenne des seuls pixels opaques par case, alpha = couverture ≥ 50 %."""
    w, h = size
    A = Image.fromarray((a * 255).astype(np.uint8)).resize(size, Image.BOX)
    pre = rgb.astype(float) * a[..., None]
    P = np.stack([np.array(Image.fromarray(pre[..., i].astype(np.float32), 'F').resize(size, Image.BOX)) for i in range(3)], -1)
    cov = np.array(A).astype(float) / 255
    col = P / np.maximum(cov[..., None], 1e-6)
    alpha = cov >= 0.5
    return np.clip(col, 0, 255).astype(np.uint8), alpha


def bbox(a):
    ys, xs = np.nonzero(a)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def to_rgba(rgb, a):
    o = np.zeros(rgb.shape[:2] + (4,), np.uint8)
    o[..., :3] = rgb
    o[..., 3] = a * 255
    o[~a] = 0
    return o


def save(name, arr):
    Image.fromarray(arr).save(f'{OUT}/{name}.png')


def main():
    meta = {}

    # ---------- arbres ----------
    T = np.array(Image.open('bruts/v2_magenta_arbres_brut.png').convert('RGB'))
    aT = key_magenta(T)

    def runs(v, gap=8):
        idx = np.flatnonzero(v); out = []
        if not len(idx): return out
        st = idx[0]; pv = idx[0]
        for i in idx[1:]:
            if i - pv > gap: out.append((st, pv + 1)); st = i
            pv = i
        out.append((st, pv + 1)); return out

    labT = np.zeros(aT.shape, int); objs = []
    # bandes de la planche (rangées vides mesurées ; rangées 2 et 3 se touchent à y=608)
    for (y0, y1) in [(0, 393), (433, 608), (608, 1024)]:
        for (x0, x1) in runs(aT[y0:y1].any(0), gap=2):
            if aT[y0:y1, x0:x1].sum() < 3000: continue
            lid = len(objs) + 1
            labT[y0:y1, x0:x1][aT[y0:y1, x0:x1]] = lid
            ys = np.flatnonzero(aT[y0:y1, x0:x1].any(1))
            objs.append(((slice(y0 + ys[0], y0 + ys[-1] + 1), slice(x0, x1)), lid))
    for k, (sl, lid) in enumerate(objs):
        sub = T[sl]
        a = aT[sl] & (labT[sl] == lid)
        rr, gg, bb = [sub[..., i].astype(int) for i in range(3)]
        leaf = a & (gg > rr + 25) & (gg > bb + 25) & (gg > 70)
        brown = a & (rr > gg) & (rr > bb + 15)
        lx0, _, lx1, _ = bbox(leaf)
        s = 126 / (lx1 - lx0)
        size = (max(1, round(sub.shape[1] * s)), max(1, round(sub.shape[0] * s)))
        rgb2, a2 = downscale(sub, a, size)
        rgb2 = snap_to(rgb2, PAL_REF)
        kind = 'arbre' if brown.sum() > 200 else 'cime_seule'
        name = f'arbre_{k:02d}_{kind}'
        save(name, to_rgba(rgb2, a2))
        meta[name] = {'brut': 'v2_magenta_arbres_brut.png', 'boite_brut': [sl[1].start, sl[0].start, sl[1].stop, sl[0].stop], 'echelle': round(s, 4), 'taille': list(size)}

    # ---------- fleurs (3 couleurs × 3 poses) ----------
    F = np.array(Image.open('bruts/v2_magenta_fleurs_anim_brut.png').convert('RGB'))
    cs = F.shape[0] / 3
    cells = {}
    for r in range(3):
        for c in range(3):
            sub = F[round(r * cs):round((r + 1) * cs), round(c * cs):round((c + 1) * cs)]
            a = key_magenta(sub, fringe=2)
            rgb2, a2 = downscale(sub, a, (24, 24))
            cells[(r, c)] = to_rgba(rgb2, a2)
    palf = own_palette(list(cells.values()), 20)
    for (r, c), arr in cells.items():
        arr[..., :3] = snap_to(arr[..., :3], palf)
        arr[arr[..., 3] == 0] = 0
    # Ancrage : la base de feuilles reste celle de la pose neutre (règle vegetation_treehouse_v1 :
    # les poses sont réarticulées depuis le neutre ; seules tiges/pétales bougent).
    BASE_ROW = 14
    couleurs = ['blanche', 'rose', 'jaune']
    for r in range(3):
        p0 = cells[(r, 0)]
        for c in range(3):
            arr = cells[(r, c)].copy()
            if c:
                arr[BASE_ROW:] = p0[BASE_ROW:]
            save(f'fleur_{couleurs[r]}_pose{c}', arr)
    meta['fleurs'] = {'brut': 'v2_magenta_fleurs_anim_brut.png', 'cellule': '24x24', 'poses': 3,
                      'sequence': [0, 1, 0, 2], 'cadences_frames_jeu': [8, 10, 14],
                      'ancrage': f'lignes {BASE_ROW}-23 = pose 0', 'palette': len(palf)}

    # ---------- souche + temple ----------
    S = np.array(Image.open('bruts/v2_magenta_souche_temple_brut.png').convert('RGB'))
    a = key_magenta(S)
    x0, y0, x1, y1 = bbox(a)
    sub, a = S[y0:y1, x0:x1], a[y0:y1, x0:x1]
    # largeur de la souche (racines comprises, sans les pousses) : lignes basses
    rows = np.nonzero(a.any(1))[0]
    low = a[int(len(a) * 0.55):]
    sx0, _, sx1, _ = bbox(low)
    s = 100 / (sx1 - sx0)
    size = (round(sub.shape[1] * s), round(sub.shape[0] * s))
    rgb2, a2 = downscale(sub, a, size)
    temple = to_rgba(rgb2, a2)
    palt = own_palette([temple], 28)
    temple[..., :3] = snap_to(temple[..., :3], palt)
    temple[temple[..., 3] == 0] = 0
    save('souche_temple', temple)
    meta['souche_temple'] = {'brut': 'v2_magenta_souche_temple_brut.png', 'echelle': round(s, 4), 'taille': list(size), 'palette': len(palt)}

    # ---------- rochers (bruts de l'essai 1, générés, hors souche) ----------
    Rk = np.array(Image.open('bruts/magenta_rochers_souche_brut.png').convert('RGB').resize((816, 1152), Image.NEAREST))
    a = key_magenta(Rk)
    lab, n = ndi.label(ndi.binary_closing(a, iterations=2) & a | a)
    rocks = []
    for i, sl in enumerate(ndi.find_objects(lab)):
        m = lab[sl] == i + 1
        rgb = Rk[sl]
        rr, gg, bb = [rgb[..., j][m].astype(int) for j in range(3)]
        if m.sum() < 60:
            continue
        if ((rr > 180) & (gg > 150) & (bb < 80)).mean() > 0.2:   # or de la souche : exclu
            continue
        arr = to_rgba(snap_to(rgb, PAL_REF), m)
        name = f'rocher_{len(rocks):02d}'
        save(name, arr)
        rocks.append({'nom': name, 'taille': [m.shape[1], m.shape[0]], 'pixels': int(m.sum())})
    meta['rochers'] = rocks

    json.dump(meta, open(f'{OUT}/sprites_v2.json', 'w'), ensure_ascii=False, indent=1, default=int)

    # planche de contrôle ×3
    names = sorted(f[:-4] for f in os.listdir(OUT) if f.endswith('.png') and not f.startswith('_'))
    ims = [Image.open(f'{OUT}/{n}.png') for n in names]
    Wb = 1100
    x = y = 0
    rowh = 0
    pos = []
    for im in ims:
        if x + im.width > Wb:
            x = 0
            y += rowh + 6
            rowh = 0
        pos.append((x, y))
        x += im.width + 6
        rowh = max(rowh, im.height)
    board = Image.new('RGBA', (Wb, y + rowh), (60, 110, 70, 255))
    for im, p in zip(ims, pos):
        board.alpha_composite(im, p)
    board.resize((board.width * 2, board.height * 2), Image.NEAREST).save(f'{OUT}/_planche_x2.png')
    print(len(names), 'sprites', [ (n, im.size) for n, im in zip(names, ims) if not n.startswith('rocher')])


if __name__ == '__main__':
    main()
