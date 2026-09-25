"""Glace & Aurore canoniques V17 — relayouts sud->nord aux pixels natifs + BG anime.

Mixte annonce : composition guidee par le layout existant
(source/ice_arena_aurora_v1/generation/layout_guide.png, sud->nord),
TOUS les pixels visibles viennent des trois references canoniques, sans
recoloration / miroir / rotation / echelle sur les couches fixes :
- aurorepmdsky.png  (264x216) : BG ciel + etoiles + aurore + frise de glace
- pmdskyicearena.png (504x408) : arene de glace sud->nord
- iceroadpmdsky.png  (504x360) : route / lac gele sud->nord

Nouveau (documente, PAS du natif) : positions des modules, coupes organiques
calculees (suivent les crevasses sombres, sans fondu), remplissage du ciel
derriere rubans/etoiles par voisins natifs, animations (onde aurore 10f,
scintillement etoiles 4f, reflets glace 4f). Aucune generation IA dans ce lot.

Sorties : PNG couches (dims /8), NPZ provenance source_sxy, TSX 8px,
apercu HTML autonome, manifestes. Import vise : PNG to Tileset 8px.
"""
from pathlib import Path
import json, hashlib, base64, io
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

R = Path(__file__).resolve().parents[2]
O = R / 'renders/glace_aurore_canonique_v1'
SRC = {  # id -> fichier racine
    0: 'aurorepmdsky.png',
    1: 'pmdskyicearena.png',
    2: 'iceroadpmdsky.png',
}
A = {i: np.array(Image.open(R / f).convert('RGBA')) for i, f in SRC.items()}
for i, a in A.items():
    assert a.shape[2] == 4, i

# ---------------------------------------------------------------- utils
def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def seam(cost):
    """Chemin vertical de cout minimal (haut->bas)."""
    h, w = cost.shape
    dist = cost.astype(float).copy()
    prev = np.zeros((h, w), int)
    for y in range(1, h):
        for x in range(w):
            lo, hi = max(0, x - 1), min(w, x + 2)
            p = lo + int(np.argmin(dist[y - 1, lo:hi]))
            prev[y, x] = p
            dist[y, x] += dist[y - 1, p]
    x = int(np.argmin(dist[-1]))
    path = []
    for y in reversed(range(h)):
        path.append(x)
        x = prev[y, x]
    return np.array(path[::-1])

def organic_vcut(module_rgb, x_line, wander, prefer_dark=True):
    """Masque : garde le cote exterieur d'une coupe verticale organique.

    module_rgb : patch (h,w,3). La coupe serpente autour de x_line (+/-wander)
    en preferant les pixels sombres (crevasses) si prefer_dark.
    Retourne (keep_left, keep_right) : deux masques (h,w) bool.
    """
    h, w = module_rgb.shape[:2]
    x0, x1 = max(0, x_line - wander), min(w, x_line + wander + 1)
    band = module_rgb[:, x0:x1].astype(float)
    lum = band.mean(axis=2)
    cost = lum if prefer_dark else (255.0 - lum)
    # penalite de pente : evite les zigzags brutaux
    cost = cost + 8.0
    path = seam(cost) + x0
    yy, xx = np.mgrid[:h, :w]
    keep_left = xx < path[:, None]
    keep_right = xx >= path[:, None]
    return keep_left, keep_right, path

def organic_hcut(module_rgb, y_line, wander):
    """Masque : coupe horizontale organique (preferant les crevasses sombres).

    Retourne (keep_top, keep_bottom) : deux masques (h,w) bool.
    """
    h, w = module_rgb.shape[:2]
    y0, y1 = max(0, y_line - wander), min(h, y_line + wander + 1)
    band = module_rgb[y0:y1, :].astype(float)
    lum = band.mean(axis=2)
    path = seam((lum + 8.0).T) + y0  # indice par colonne
    yy, xx = np.mgrid[:h, :w]
    keep_top = yy < path[None, :]
    keep_bottom = yy >= path[None, :]
    return keep_top, keep_bottom, path

class Map:
    def __init__(self, id, W, H):
        self.id = id; self.W = W; self.H = H
        self.layers = []; self.ops = []
        (O / id).mkdir(parents=True, exist_ok=True)

    def layer(self, name):
        l = [name, np.zeros((self.H, self.W, 4), np.uint8),
             np.full((self.H, self.W, 3), -1, np.int16)]
        self.layers.append(l)
        return l

    def put(self, l, s, box, pos, mask=None):
        x0, y0, x1, y1 = box; x, y = pos
        p = A[s][y0:y1, x0:x1]
        hh, ww = p.shape[:2]
        assert x >= 0 and y >= 0 and x + ww <= self.W and y + hh <= self.H, (box, pos)
        m = (p[:, :, 3] > 0) if mask is None else (mask & (p[:, :, 3] > 0))
        sy, sx = np.mgrid[y0:y1, x0:x1]
        q = np.stack([np.full(sx.shape, s), sx, sy], 2)
        l[1][y:y + hh, x:x + ww][m] = p[m]
        l[2][y:y + hh, x:x + ww][m] = q[m]
        self.ops.append(dict(layer=l[0], source=s, rect=list(box), position=list(pos)))

    def fill(self, l, s, boxes, mask=None, seed=11):
        """Pavage sol/lac par patches natifs, joints par cout minimal, sans fondu."""
        rng = np.random.default_rng(seed)
        mask = np.ones((self.H, self.W), bool) if mask is None else mask
        hh = boxes[0][3] - boxes[0][1]; ww = boxes[0][2] - boxes[0][0]
        ov = min(8, hh // 2, ww // 2)
        H, W = self.H, self.W
        for y in range(0, H, hh - ov):
            for x in range(0, W, ww - ov):
                h = min(hh, H - y); w = min(ww, W - x)
                want = mask[y:y + h, x:x + w]
                if not want.any():
                    continue
                old = l[1][y:y + h, x:x + w]
                occupied = (old[:, :, 3] > 0) & want
                best = None
                for idx in rng.permutation(len(boxes))[:24]:
                    x0, y0, _, _ = boxes[idx]
                    patch = A[s][y0:y0 + h, x0:x0 + w]
                    cost = ((old[:, :, :3].astype(float) - patch[:, :, :3].astype(float)) ** 2).sum(2)
                    score = cost[occupied].mean() if occupied.any() else rng.random()
                    if best is None or score < best[0]:
                        best = (score, x0, y0, patch, cost)
                _, x0, y0, patch, cost = best
                take = want.copy()
                if x and w >= ov:
                    take[:, :ov] &= np.arange(ov)[None, :] >= seam(cost[:, :ov])[:, None]
                if y and h >= ov:
                    take[:ov, :] &= np.arange(ov)[:, None] >= seam(cost[:ov, :].T)[None, :]
                take |= want & (old[:, :, 3] == 0)
                sy, sx = np.mgrid[y0:y0 + h, x0:x0 + w]
                q = np.stack([np.full(sx.shape, s), sx, sy], 2)
                old[take] = patch[take]
                l[2][y:y + h, x:x + w][take] = q[take]
        self.ops.append(dict(layer=l[0], source=s, method='native patch overlap, no blending',
                             patches=boxes, seed=seed))

    def save_layer(self, l, prefix):
        d = O / self.id
        fn = f'{prefix}_{self.id}_{l[0]}.png'
        Image.fromarray(l[1]).save(d / fn)
        np.savez_compressed(d / (l[0] + '_source.npz'), source_sxy=l[2])
        root = ET.Element('tileset', version='1.10', name=Path(fn).stem,
                          tilewidth='8', tileheight='8',
                          columns=str(self.W // 8),
                          tilecount=str(self.W // 8 * (self.H // 8)))
        ET.SubElement(root, 'image', source=fn, width=str(self.W), height=str(self.H))
        ET.ElementTree(root).write(d / (Path(fn).stem + '.tsx'),
                                   encoding='utf-8', xml_declaration=True)
        return fn

# ------------------------------------------------- BG aurore (264x216)
CUT, FADE, T_AUR, MS_AUR = 144, 10, 10, 160
AMP1, L1 = 4.0, 2
AMP2, L2, PH2 = 2.0, 5, 0.4
ENV = 20.0

def decalage(x, t, larg=264):
    return AMP1 * np.sin(2 * np.pi * (L1 * x / larg - t / T_AUR)) + \
        AMP2 * np.sin(2 * np.pi * (L2 * x / larg - t / T_AUR) + PH2)

def enveloppe(x, larg=264):
    return np.clip(np.minimum(x / ENV, (larg - 1 - x) / ENV), 0, 1)

def extraire_rubans():
    """Rubans lumineux 1x, ciel retire, etoiles exclues (methode V10 a 1x)."""
    ref = A[0][:, :, :3].astype(float)
    lum = ref.mean(axis=2); sat = ref.max(axis=2) - ref.min(axis=2)
    alpha = np.clip((sat - 75) * 3.0, 0, 255) + np.clip((lum - 105) * 2.0, 0, 255)
    alpha = np.clip(alpha, 0, 255)
    alpha[:CUT - FADE][alpha[:CUT - FADE] < 34] = 0
    fondu = np.ones(216); fondu[CUT - FADE:CUT] = np.linspace(1, 0, FADE); fondu[CUT:] = 0
    alpha = alpha * fondu[:, None]
    masque = alpha > 0
    lab, n = nd.label(masque)
    if n:
        tailles = np.bincount(lab.ravel()); tailles[0] = 0
        alpha[(tailles < 6)[lab]] = 0
        restant = alpha > 0
        lab2, n2 = nd.label(restant)
        if n2:
            sumsat = nd.mean(sat, lab2, range(1, n2 + 1))
            sizes = np.bincount(lab2.ravel()); sizes[0] = 0
            etoiles = np.array([k + 1 for k in range(n2)
                                if sumsat[k] < 70 and sizes[k + 1] < 40])
            alpha[np.isin(lab2, etoiles)] = 0
    noyau = (alpha >= 100) & (sat >= 70)
    dist_ruban = nd.distance_transform_edt(~noyau)
    alpha[(alpha >= 100) & (sat < 50) & (dist_ruban > 10)] = 0
    # Note verifiee : les 230 petites composantes a faible alpha touchent toutes
    # un halo fort a <=2 px : ce sont des franges du ruban, pas des etoiles
    # isolees. Elles restent dans le calque aurore (mouvement legitime).
    rgba = np.dstack([ref, alpha]).astype('uint8')
    rgba[rgba[:, :, 3] == 0] = 0
    im = Image.fromarray(rgba, 'RGBA').crop((0, 0, 264, CUT))
    a = np.array(im)
    a[:, 0, 3] = 0; a[:, -1, 3] = 0
    a[a[:, :, 3] == 0] = 0
    return Image.fromarray(a, 'RGBA'), (alpha > 0)

def extraire_etoiles(ruban_mask):
    """Etoiles : petites composantes brillantes hors rubans, y < CUT."""
    ref = A[0][:, :, :3].astype(float)
    lum = ref.mean(axis=2); sat = ref.max(axis=2) - ref.min(axis=2)
    cand = (lum > 110) & (sat < 90) & (~ruban_mask)
    cand[CUT:] = False
    lab, n = nd.label(cand)
    sizes = np.bincount(lab.ravel()); sizes[0] = 0
    keep = np.zeros_like(cand)
    # composantes 1..36 px, au moins un pixel bien brillant
    for k in range(1, n + 1):
        if 1 <= sizes[k] <= 36:
            ys, xs = np.nonzero(lab == k)
            if lum[ys, xs].max() > 140:
                keep[ys, xs] = True
    return keep, lab, n

def ciel_rempli(trous, epines):
    """Ciel+nuages : trous (rubans/etoiles) combles par plus proche voisin natif.
    Zone epines (frise) -> transparente. Retourne (rgba, donneurs_sxy)."""
    H, W = 216, 264
    trous_total = trous | epines
    # distance_transform_edt : entree = pixels NON NULS (les trous) ; indices
    # retournes = plus proche pixel NUL (donneur natif). Ne pas inverser.
    _, inds = nd.distance_transform_edt(trous_total, return_indices=True)
    donneurs = np.stack([np.zeros((H, W), np.int16), inds[1].astype(np.int16),
                         inds[0].astype(np.int16)], 2)
    out = A[0][inds[0], inds[1]].copy()
    out[epines] = 0
    donneurs[epines] = -1
    return out, donneurs

def onde_frame(effet, t):
    m = np.array(effet); H, W = m.shape[:2]
    out = np.zeros_like(m)
    for x in range(W):
        d = int(round(float(decalage(x, t, W)) * float(enveloppe(x, W))))
        col = m[:, x, :].copy()
        if d > 0:
            out[d:, x, :] = col[:H - d]
        elif d < 0:
            out[:H + d, x, :] = col[-d:]
        else:
            out[:, x, :] = col
    return Image.fromarray(out, 'RGBA')

def build_bg():
    m = Map('bg_aurore', 264, 216)
    effet, ruban = extraire_rubans()
    # frise de glace : pixels clairs bleutes en bas, composantes touche-bas
    ref = A[0][:, :, :3].astype(float)
    lum = ref.mean(axis=2)
    bas = np.zeros((216, 264), bool); bas[140:] = True
    cand = bas & (lum > 55) & (ref[:, :, 2] > ref[:, :, 0] + 8)
    lab, n = nd.label(cand)
    bas_ids = set(np.unique(lab[215, :])) - {0}
    frise = np.isin(lab, list(bas_ids))
    frise = nd.binary_fill_holes(frise)
    # gouttelettes isolees de la frise rattachees si proches
    frise = nd.binary_closing(frise, structure=np.ones((3, 3)))
    # etoiles
    star_mask, slab, sn = extraire_etoiles(ruban)
    trous = ruban | star_mask
    trous[frise] = False
    # 01 ciel
    ciel_l = m.layer('01_ciel_nuages')
    rgba, donneurs = ciel_rempli(trous, frise)
    ciel_l[1][:] = rgba; ciel_l[2][:] = donneurs
    m.ops.append(dict(layer='01_ciel_nuages', source=0,
                      method='trous rubans/etoiles combles par plus proche voisin natif (distance_transform), frise transparente'))
    # 02 etoiles : statique + groupes de scintillement
    star_l = m.layer('02_etoiles')
    star_l[1][star_mask] = A[0][star_mask]
    sy, sx = np.nonzero(star_mask)
    star_l[2][star_mask] = np.stack([np.zeros_like(sx), sx, sy], 1).astype(np.int16)
    # groupes : parite de l'indice de composante (alterne dans le ciel)
    comp = slab.copy(); comp[~star_mask] = 0
    grp = np.zeros((216, 264), np.uint8)
    ky = np.minimum(slab[star_mask], sn)
    grp[star_mask] = (ky % 2).astype(np.uint8)  # 0/1
    # 04 frise
    fr_l = m.layer('04_frise_glace')
    fr_l[1][frise] = A[0][frise]
    fy, fx = np.nonzero(frise)
    fr_l[2][frise] = np.stack([np.zeros_like(fx), fx, fy], 1).astype(np.int16)
    pfx = 'GLACE_V17'
    files = {}
    for l in m.layers:
        files[l[0]] = m.save_layer(l, pfx)
    d = O / 'bg_aurore'
    # 03 aurore : 10 frames onde (264x144)
    effet.save(d / f'{pfx}_bg_aurore_03_aurore_base.png')
    frames = [onde_frame(effet, t) for t in range(T_AUR)]
    for t, im in enumerate(frames):
        im.save(d / f'{pfx}_bg_aurore_03_aurore_f{t:02d}.png')
    frames[0].save(d / f'{pfx}_bg_aurore_03_aurore_10f.webp', save_all=True,
                   append_images=frames[1:], duration=MS_AUR, loop=0,
                   lossless=True, method=4)
    # 02b etoiles scintillement : 4 frames, groupes alternes 255/176
    base = np.array(Image.open(d / files['02_etoiles']))
    star_frames = []
    for f in range(4):
        g = base.copy()
        a0 = 255 if f in (0, 1) else 176
        a1 = 176 if f in (0, 1) else 255
        if f == 1:
            a0, a1 = 216, 216
        if f == 3:
            a0, a1 = 216, 216
        gg = g[:, :, 3] > 0
        g[gg & (grp == 0), 3] = a0
        g[gg & (grp == 1), 3] = a1
        im = Image.fromarray(g, 'RGBA')
        im.save(d / f'{pfx}_bg_aurore_02_etoiles_tw{f}.png')
        star_frames.append(im)
    star_frames[0].save(d / f'{pfx}_bg_aurore_02_etoiles_4f.webp', save_all=True,
                        append_images=star_frames[1:], duration=200, loop=0,
                        lossless=True, method=4)
    # stats honnetes
    comp0 = Image.open(d / files['01_ciel_nuages']).convert('RGBA')
    comp0.alpha_composite(Image.open(d / files['02_etoiles']).convert('RGBA'))
    comp0.alpha_composite(frames[0], (0, 0))
    comp0.alpha_composite(Image.open(d / files['04_frise_glace']).convert('RGBA'))
    diff = (np.array(comp0)[:, :, :3].astype(int)
            - A[0][:, :, :3].astype(int))
    ndiff = int((np.abs(diff).sum(axis=2) > 24).sum())
    return dict(id='bg_aurore', title='BG ciel boreal — ciel, etoiles, aurore 10f, frise',
                size=[264, 216], layers=[files['01_ciel_nuages'], files['02_etoiles'],
                                         files['04_frise_glace']],
                aurore_frames=[f'{pfx}_bg_aurore_03_aurore_f{t:02d}.png' for t in range(T_AUR)],
                aurore_ms=MS_AUR, star_frames=4, star_ms=200,
                n_ruban=int(ruban.sum()), n_etoiles=int(star_mask.sum()),
                n_frise=int(frise.sum()),
                recompose_diff_px=ndiff,
                operations=m.ops, runtime='NOT TESTED', art_approved=False,
                notes='Aurore : texture canonique extraite (V10 a 1x), onde transversale verticale pure, boucle exacte. Etoiles : RGB natifs, seul alpha module. Ciel : trous combles par voisins natifs.')

# ------------------------------------------------------- masques fissures
def masque_fissures(a, box):
    """Fissures sombres bleutees dans un sol clair. Retourne masque (h,w)."""
    x0, y0, x1, y1 = box
    p = a[y0:y1, x0:x1, :3].astype(float)
    lum = p.mean(axis=2)
    med = nd.median_filter(lum, size=9)
    fiss = (med - lum > 22) & (p[:, :, 2] > p[:, :, 0] + 6) & (lum < 200)
    lab, n = nd.label(fiss)
    sizes = np.bincount(lab.ravel()); sizes[0] = 0
    keep = sizes >= 6
    return keep[lab]

def masque_roche(a, box):
    """Pixels rocheux (non-neige) dans un rect melange."""
    x0, y0, x1, y1 = box
    p = a[y0:y1, x0:x1, :3].astype(float)
    lum = p.mean(axis=2); sat = p.max(axis=2) - p.min(axis=2)
    roche = ~((lum > 200) & (sat < 70))
    lab, n = nd.label(roche)
    sizes = np.bincount(lab.ravel()); sizes[0] = 0
    return (sizes >= 10)[lab]

# ------------------------------------------------------- arene (504x408)
def build_arene():
    m = Map('arene_glace', 504, 408)
    pfx = 'GLACE_V17'
    # 01 sol : pavage neige native (bandes claires y 208..288)
    sol = m.layer('01_sol_neige')
    floor_mask = np.zeros((408, 504), bool); floor_mask[128:, :] = True
    m.fill(sol, 1, [(48, 224, 112, 256), (208, 224, 272, 256),
                    (304, 232, 368, 264), (120, 248, 184, 280),
                    (368, 224, 432, 256), (160, 208, 224, 240),
                    (240, 184, 304, 216), (40, 184, 104, 216)], floor_mask, 21)
    # 02 mur nord : paroi arriere entiere remontee (sans ciel),
    # bas organique suivant les crevasses (pas de coupe droite)
    nord = m.layer('02_mur_nord')
    keep_top, _, _ = organic_hcut(A[1][36:196, 0:504, :3], 152, 10)
    m.put(nord, 1, (0, 36, 504, 196), (0, 0), keep_top)
    # 03 blocs lateraux : eboulis au pied, masque roche (pas de coupe droite)
    cotes = m.layer('03_blocs_cotes')
    for box, pos in [((312, 176, 472, 216), (16, 208)),
                     ((40, 176, 200, 216), (344, 232))]:
        mk = masque_roche(A[1], box)
        m.put(cotes, 1, box, pos, nd.binary_fill_holes(mk))
    # 04 crete sud : crete avant en deux volets, ouverture sud organique
    crete = m.layer('04_crete_sud')
    # volet gauche : src large, coupe organique cote ouverture
    boxL = (0, 304, 248, 408)
    pL = A[1][304:408, 0:248, :3]
    keepL, _, _ = organic_vcut(pL, 216, 14)
    m.put(crete, 1, boxL, (0, 304), keepL)
    # volet droit : autre zone source (sans miroir)
    boxR = (288, 304, 504, 408)
    pR = A[1][304:408, 288:504, :3]
    _, keepR, _ = organic_vcut(pR, 32, 14)
    m.put(crete, 1, boxR, (288, 304), keepR)
    # 05 fissures : extraites du sol, reposees sur l'arene
    fiss = m.layer('05_fissures')
    m.put(fiss, 1, (80, 200, 200, 240), (120, 248), masque_fissures(A[1], (80, 200, 200, 240)))
    m.put(fiss, 1, (280, 200, 400, 240), (272, 280), masque_fissures(A[1], (280, 200, 400, 240)))
    files = {}
    for l in m.layers:
        files[l[0]] = m.save_layer(l, pfx)
    # chemin sud->centre : ouverture x~216..320 vers centre (252,200)
    yy, xx = np.mgrid[:408, :504]
    path = (xx >= 232) & (xx < 304) & (yy >= 200)
    # degagement : pas de crete sur le chemin
    crete_a = np.array(Image.open(O / 'arene_glace' / files['04_crete_sud']))
    bloque = (crete_a[:, :, 3] > 0) & path
    return m, files, path, bloque

# ------------------------------------------------------- route (504x360)
def build_route():
    m = Map('route_glacee', 504, 360)
    pfx = 'GLACE_V17'
    # 01 fond montagnes : ciel + pics intacts
    fond = m.layer('01_fond_montagnes')
    m.put(fond, 2, (0, 0, 504, 96), (0, 0))
    # 02 lac gele : pavage (bandes claires y 150..215), continu sous les
    # ouvertures sud et le defile nord (pas de trou transparent)
    lac = m.layer('02_lac_gele')
    lac_mask = np.zeros((360, 504), bool); lac_mask[88:, :] = True
    m.fill(lac, 2, [(150, 155, 214, 187), (250, 155, 314, 187),
                    (180, 170, 244, 202), (300, 170, 364, 202),
                    (120, 185, 184, 217), (330, 150, 394, 182),
                    (200, 150, 264, 182), (90, 165, 154, 197)], lac_mask, 33)
    # 03 parois nord : deux massifs, coupe organique cote defile
    parois = m.layer('03_parois_nord')
    boxL = (0, 88, 224, 184)   # h=96
    pL = A[2][88:184, 0:224, :3]
    keepL, _, _ = organic_vcut(pL, 192, 16)
    keepT, _, _ = organic_hcut(pL, 88, 10)
    m.put(parois, 2, boxL, (0, 88), keepL & keepT)
    boxR = (280, 88, 504, 184)
    pR = A[2][88:184, 280:504, :3]
    _, keepR, _ = organic_vcut(pR, 32, 16)
    keepT, _, _ = organic_hcut(pR, 88, 10)
    m.put(parois, 2, boxR, (280, 88), keepR & keepT)
    # 04 blocs sud : premiers plans, ouverture sud organique
    blocs = m.layer('04_blocs_sud')
    boxBL = (0, 264, 240, 360)  # h=96
    qL = A[2][264:360, 0:240, :3]
    keepBL, _, _ = organic_vcut(qL, 208, 14)
    _, keepB, _ = organic_hcut(qL, 8, 8)
    m.put(blocs, 2, boxBL, (0, 264), keepBL & keepB)
    boxBR = (264, 264, 504, 360)
    qR = A[2][264:360, 264:504, :3]
    _, keepBR, _ = organic_vcut(qR, 32, 14)
    _, keepB, _ = organic_hcut(qR, 8, 8)
    m.put(blocs, 2, boxBR, (264, 264), keepBR & keepB)
    # 05 fissures du lac
    fiss = m.layer('05_fissures')
    m.put(fiss, 2, (140, 150, 260, 190), (150, 200), masque_fissures(A[2], (140, 150, 260, 190)))
    m.put(fiss, 2, (260, 150, 380, 190), (290, 220), masque_fissures(A[2], (260, 150, 380, 190)))
    files = {}
    for l in m.layers:
        files[l[0]] = m.save_layer(l, pfx)
    yy, xx = np.mgrid[:360, :504]
    path = (xx >= 224) & (xx < 280) & (yy >= 140)
    blocs_a = np.array(Image.open(O / 'route_glacee' / files['04_blocs_sud']))
    parois_a = np.array(Image.open(O / 'route_glacee' / files['03_parois_nord']))
    bloque = ((blocs_a[:, :, 3] > 0) | (parois_a[:, :, 3] > 0)) & path
    return m, files, path, bloque

# ------------------------------------------------------- reflets animes
def build_reflets(map_id, files, layers_for_mask, W, H, prefix='GLACE_V17'):
    """Overlay 4f : pulsation douce des reflets (pixels clairs froids).

    NOUVELLE animation (pas un cycle officiel) : RGB d'origine modules
    +/-5%, deux groupes en opposition de phase, boucle exacte 4x150ms.
    """
    d = O / map_id
    comp = Image.new('RGBA', (W, H))
    for lname in layers_for_mask:
        comp.alpha_composite(Image.open(d / files[lname]).convert('RGBA'))
    a = np.array(comp)
    lum = a[:, :, :3].mean(axis=2)
    hl = (a[:, :, 3] > 0) & (lum >= 195) & ((a[:, :, 2].astype(int) - a[:, :, 0].astype(int)) >= 12)
    yy, xx = np.mgrid[:H, :W]
    grp = ((xx // 16 + yy // 16) % 2 == 0)
    out = []
    for f in range(4):
        g = np.zeros((H, W, 4), np.uint8)
        s0 = 1.0 + 0.05 * np.sin(2 * np.pi * f / 4)
        s1 = 1.0 + 0.05 * np.sin(2 * np.pi * f / 4 + np.pi)
        for gg, s in ((grp, s0), (~grp, s1)):
            sel = hl & gg
            if sel.any():
                g[sel] = np.column_stack([np.clip(a[sel][:, :3].astype(float) * s, 0, 255),
                                          np.full(sel.sum(), 255)]).astype(np.uint8)
        im = Image.fromarray(g, 'RGBA')
        im.save(d / f'{prefix}_{map_id}_06_reflets_f{f}.png')
        out.append(im)
    out[0].save(d / f'{prefix}_{map_id}_06_reflets_4f.webp', save_all=True,
                append_images=out[1:], duration=150, loop=0, lossless=True, method=4)
    # provenance donneurs (identite, RGB modules separement)
    q = np.full((H, W, 3), -1, np.int16)
    sy, sx = np.nonzero(hl)
    q[hl] = np.stack([np.full(sx.shape, -2), sx, sy], 1)  # -2 = scene locale
    np.savez_compressed(d / '06_reflets_source.npz', source_sxy=q)
    return [f'{prefix}_{map_id}_06_reflets_f{f}.png' for f in range(4)], int(hl.sum())

# ------------------------------------------------------- viewer + main
def uri(p):
    return 'data:image/png;base64,' + base64.b64encode(Path(p).read_bytes()).decode()

VIEWER = """<!doctype html><html lang="fr"><meta charset="utf-8">
<title>V17 · Glace &amp; Aurore canoniques — sud-nord, PNG 8px</title>
<style>
body{background:#0d1626;color:#dfe8f5;font:15px system-ui;max-width:1180px;margin:28px auto;padding:20px}
p{line-height:1.55;color:#b9c7dd}article{background:#16233a;border:1px solid #33507a;border-radius:12px;padding:18px;margin:26px 0}
canvas{image-rendering:pixelated;background:#05080f;max-width:100%}label{display:inline-block;margin:6px 10px 6px 0;font-size:13px}
button{padding:8px 12px;background:#9fc7ff;color:#0b1526;border:0;border-radius:6px;margin-right:8px}
small{color:#8fa3c4}input[type=range]{width:220px;vertical-align:middle}.row{display:flex;flex-wrap:wrap;gap:18px;align-items:flex-start}
</style>
<h1>V17 · Glace &amp; Aurore canoniques — sud → nord</h1>
<p>Relayouts aux <b>pixels natifs exacts</b> (aucun pixel IA, ni recoloration/miroir/echelle sur les couches fixes).
Composition guidee par le layout sud-nord existant. Animations <b>nouvelles et documentees</b>
(onde aurore, scintillement, reflets) : pas des cycles officiels recuperes.
Tous les PNG sont multiples de 8 px, prets pour <b>PNG to Tileset 8 px</b>.</p>
<div id="maps"></div>
<script>const DATA=__DATA__;
for(const s of DATA){const a=document.createElement('article');
a.innerHTML='<h2>'+s.title+'</h2><small>'+s.size.join(' × ')+' px · grille 8 px · '+s.note+'</small>';
const wrap=document.createElement('div');wrap.className='row';a.append(wrap);
const c=document.createElement('canvas');c.width=s.size[0];c.height=s.size[1];wrap.append(c);
const side=document.createElement('div');wrap.append(side);
const ctx=c.getContext('2d');ctx.imageSmoothingEnabled=false;
const statics=s.static_layers.map(l=>{const im=new Image();im.src=l.uri;return{im,on:true,name:l.name}});
const animF=s.anim_frames.map(f=>{const im=new Image();im.src=f;return im});
const anim2=(s.anim2_frames||[]).map(f=>{const im=new Image();im.src=f;return im});
const showA=document.createElement('div'),show2=document.createElement('div');
statics.forEach((l,i)=>{const lb=document.createElement('label');const ch=document.createElement('input');
ch.type='checkbox';ch.checked=true;ch.onchange=()=>{l.on=ch.checked;draw()};lb.append(ch,document.createTextNode(l.name));side.append(lb);side.append(document.createElement('br'))});
let t=0,t2=0,play=true,timer=null,grid=false;
function draw(){ctx.clearRect(0,0,c.width,c.height);
for(const l of statics)if(l.on&&l.im.complete&&l.im.naturalWidth)ctx.drawImage(l.im,0,0);
if(onA.checked&&animF.length&&animF[t].complete)ctx.drawImage(animF[t],0,0);
if(on2&&on2.checked&&anim2.length&&anim2[t2].complete)ctx.drawImage(anim2[t2],0,0);
if(grid){ctx.strokeStyle='rgba(120,180,255,.18)';ctx.beginPath();
for(let x=0;x<=c.width;x+=8){ctx.moveTo(x+.5,0);ctx.lineTo(x+.5,c.height)}
for(let y=0;y<=c.height;y+=8){ctx.moveTo(0,y+.5);ctx.lineTo(c.width,y+.5)}ctx.stroke()}}
const onA=document.createElement('input');onA.type='checkbox';onA.checked=true;onA.onchange=draw;
const lbA=document.createElement('label');lbA.append(onA,document.createTextNode(s.anim_name+' (anime)'));side.append(lbA);
let on2=null;
if(anim2.length){side.append(document.createElement('br'));on2=document.createElement('input');on2.type='checkbox';on2.checked=true;on2.onchange=draw;
const lb2=document.createElement('label');lb2.append(on2,document.createTextNode(s.anim2_name+' (anime)'));side.append(lb2)}
side.append(document.createElement('br'));
const bP=document.createElement('button');bP.textContent='Pause';
const bF=document.createElement('button');bF.textContent='Frame +';
const bG=document.createElement('button');bG.textContent='Grille 8px';
side.append(bP,bF,bG);
bP.onclick=()=>{play=!play;bP.textContent=play?'Pause':'Lecture';if(play)tick();else clearTimeout(timer)};
bF.onclick=()=>{t=(t+1)%animF.length;if(anim2.length)t2=(t2+1)%anim2.length;draw()};
bG.onclick=()=>{grid=!grid;draw()};
function tick(){if(!play)return;
t=(t+1)%animF.length;if(animF.length&&t%2===0&&anim2.length)t2=(t2+1)%anim2.length;draw();
timer=setTimeout(tick,s.anim_ms)}
let n=0;const all=[...statics.map(l=>l.im),...animF,...anim2];
all.forEach(im=>{im.onload=()=>{if(++n===all.length){draw();tick()}}});
const p=document.createElement('p');p.textContent=s.notes;side.append(p);
document.getElementById('maps').append(a)}
</script></html>"""

def construire():
    O.mkdir(parents=True, exist_ok=True)
    bg = build_bg()
    mA, filesA, pathA, bloqA = build_arene()
    mR, filesR, pathR, bloqR = build_route()
    # revues d'acces (indicatif, pas collision moteur)
    for (mid, files, path, bloq, W, H, entr) in (
            ('arene_glace', filesA, pathA, bloqA, 504, 408, (252, 200)),
            ('route_glacee', filesR, pathR, bloqR, 504, 360, (252, 140))):
        comp = Image.new('RGBA', (W, H))
        for fn in files.values():
            comp.alpha_composite(Image.open(O / mid / fn).convert('RGBA'))
        comp.save(O / mid / 'composite_statique.png')
        rev = comp.copy(); dr = ImageDraw.Draw(rev)
        xs = [int(np.flatnonzero(path[y]).mean()) for y in range(H) if path[y].any()]
        ys = [y for y in range(H) if path[y].any()]
        if xs:
            dr.line(list(zip(xs, ys)), fill=(255, 90, 60, 255), width=2)
        dr.ellipse((entr[0] - 6, entr[1] - 6, entr[0] + 6, entr[1] + 6),
                   outline=(255, 255, 0, 255), width=2)
        rev.save(O / mid / 'access_review_NOT_RUNTIME.png')
    refrA, nrefA = build_reflets('arene_glace', filesA,
                                 ['01_sol_neige', '02_mur_nord', '03_blocs_cotes',
                                  '04_crete_sud', '05_fissures'], 504, 408)
    refrR, nrefR = build_reflets('route_glacee', filesR,
                                 ['01_fond_montagnes', '02_lac_gele', '03_parois_nord',
                                  '04_blocs_sud', '05_fissures'], 504, 360)
    # viewer
    d = O / 'bg_aurore'
    data = [
        dict(title=bg['title'], size=bg['size'], note='BG anime',
             static_layers=[
                 dict(name='01_ciel_nuages', uri=uri(d / bg['layers'][0])),
                 dict(name='04_frise_glace', uri=uri(d / bg['layers'][2]))],
             anim_name='03_aurore (10f onde)', anim_ms=160,
             anim_frames=[uri(d / f) for f in bg['aurore_frames']],
             anim2_name='02_etoiles (4f scintillement)', anim2_ms=200,
             anim2_frames=[uri(d / f'GLACE_V17_bg_aurore_02_etoiles_tw{f}.png') for f in range(4)],
             notes=bg['notes']),
        dict(title='Arene de glace — arrivee sud, paroi au nord', size=[504, 408],
             note='terrain sud-nord',
             static_layers=[dict(name=k, uri=uri(O / 'arene_glace' / v))
                            for k, v in filesA.items()],
             anim_name='06_reflets (4f)', anim_ms=150,
             anim_frames=[uri(O / 'arene_glace' / f) for f in refrA],
             anim2_frames=[],
             notes='Paroi nord entiere remontee, crete sud ouverte au sud (coupe organique), '
                   'eboulis masks, fissures replacees. Reflets : pulsation douce NOUVELLE.'),
        dict(title='Route du lac gele — sud vers defile nord', size=[504, 360],
             note='terrain sud-nord',
             static_layers=[dict(name=k, uri=uri(O / 'route_glacee' / v))
                            for k, v in filesR.items()],
             anim_name='06_reflets (4f)', anim_ms=150,
             anim_frames=[uri(O / 'route_glacee' / f) for f in refrR],
             anim2_frames=[],
             notes='Montagnes intactes, defile nord aux coupes organiques, blocs sud ouverts, '
                   'lac pave natif. Reflets : pulsation douce NOUVELLE.'),
    ]
    (R / 'apercu_glace_aurore_canonique_v1.html').write_text(
        VIEWER.replace('__DATA__', json.dumps(data)), encoding='utf-8')
    manifest = dict(
        lot='glace_aurore_canonique_v1 (V17)', grille_px=8,
        methode='mixte : composition guidee par layout_guide sud-nord existant ; '
                '100% pixels natifs sur couches fixes ; coupes organiques calculees ; '
                'animations nouvelles (onde/sci/reflets), pas de cycles officiels.',
        sources=[dict(id=i, file=f, sha256=sha(R / f)) for i, f in SRC.items()],
        bg=bg,
        arene=dict(layers=filesA, reflets=refrA, n_reflets=nrefA,
                   chemin_bloque_px=int(bloqA.sum()), operations=mA.ops,
                   runtime='NOT TESTED', art_approved=False),
        route=dict(layers=filesR, reflets=refrR, n_reflets=nrefR,
                   chemin_bloque_px=int(bloqR.sum()), operations=mR.ops,
                   runtime='NOT TESTED', art_approved=False),
        import_png_to_tileset='8 px, noms GLACE_V17_* uniques ; poser les couches dans '
                              'l ordre, frames animees en overlay au-dessus.',
        runtime_PMDO='NON TESTE', autres_zones='ouvertes')
    (O / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print('V17 construit : BG aurore + arene + route.')
    print('chemin arene bloque :', int(bloqA.sum()), '| route :', int(bloqR.sum()))
    print('recompose BG diff px :', bg['recompose_diff_px'])

if __name__ == '__main__':
    construire()
