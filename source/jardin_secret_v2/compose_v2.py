"""Jardin secret v2 — assemblage multicalque (816×1152, origine commune 0,0).

Sol et feuillage : générés plein cadre sur la maquette (maquette.py), recalés 816×1152, palette de secretgarden.png.
Objets : sprites de extract_v2.py posés par translation seule.
Rayon : sprite natif de secretgarden.png (segmentation du lot v1), inchangé.
"""
import json, os
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
import sys
sys.path.insert(0, HERE)
from extract_v2 import snap_to, PAL_REF, key_magenta

W, H = 816, 1152
SP = 'travail/sprites_v2'


def spr(n):
    return np.array(Image.open(f'{SP}/{n}.png').convert('RGBA'))


def blank():
    return np.zeros((H, W, 4), np.uint8)


def stamp(layer, s, x, y, occ=None):
    h, w = s.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    sub = s[y0 - y:y1 - y, x0 - x:x1 - x]
    m = sub[..., 3] > 0
    layer[y0:y1, x0:x1][m] = sub[m]
    if occ is not None:
        occ[y0:y1, x0:x1] |= m


# ---------------- sol ----------------
def ground():
    g = Image.open('bruts/v2_sol_brut.png').convert('RGB').resize((W, H), Image.LANCZOS)
    g = snap_to(np.array(g), PAL_REF)
    r, gg, b = [g[..., i].astype(int) for i in range(3)]
    light = gg >= 150
    lawn = light & (b >= 75)
    carpet = light & (b < 75)
    void = gg < 110
    # masques de classification : touffes sombres du tapis/pelouse incluses (fermeture + trous bouchés)
    carpet = ndi.binary_fill_holes(ndi.binary_closing(carpet, iterations=3, border_value=1)) & ~void
    lawn = ndi.binary_fill_holes(ndi.binary_closing(lawn, iterations=3, border_value=1)) & ~void & ~carpet
    # correction : aucune touffe isolée dans le sous-bois (petites îles claires -> couleur du sous-bois voisin)
    lab, n = ndi.label(~void)
    sz = ndi.sum(~void, lab, range(1, n + 1))
    small = np.isin(lab, 1 + np.flatnonzero(sz < 400))
    if small.any():
        idx = ndi.distance_transform_edt(small, return_distances=False, return_indices=True)
        g[small] = g[idx[0][small], idx[1][small]]
    return g, lawn, carpet, void


def foliage():
    f = np.array(Image.open('bruts/v2_magenta_feuillage_brut.png').convert('RGB'))
    a = key_magenta(f, fringe=3)
    a = ndi.binary_fill_holes(a) & a | a
    rgb = np.array(Image.fromarray(f).resize((W, H), Image.NEAREST))
    al = np.array(Image.fromarray((a * 255).astype(np.uint8)).resize((W, H), Image.NEAREST)) > 127
    rgb = snap_to(rgb, PAL_REF)
    # correction : le générateur a débordé de la maquette -> recoupe sur le masque de la maquette + 18 px
    fol = np.load('travail/v2_masques.npz')['fol']
    base = ndi.binary_dilation(fol, iterations=10)
    # bord festonné : demi-disques (r 7..11 px) posés tous les ~14 px le long du bord -> silhouette de grappes
    rng = np.random.default_rng(5)
    ring = base & ~ndi.binary_erosion(base, iterations=1, border_value=1)
    pts = np.argwhere(ring)
    keep = base.copy()
    yy, xx = np.mgrid[-12:13, -12:13]
    taken = np.zeros_like(base)
    for y, x in pts[rng.permutation(len(pts))]:
        if taken[y, x]:
            continue
        r = int(rng.integers(7, 12))
        y0, y1, x0, x1 = max(0, y - 12), min(H, y + 13), max(0, x - 12), min(W, x + 13)
        d = (yy ** 2 + xx ** 2 <= r * r)[y0 - y + 12:y1 - y + 12, x0 - x + 12:x1 - x + 12]
        keep[y0:y1, x0:x1] |= d
        taken[max(0, y - 9):y + 10, max(0, x - 9):x + 10] = True
    cut = al & ~keep
    al &= keep
    al = ndi.binary_opening(al, iterations=1) & al
    # contour 1 px très sombre + 1 px d'ombre intérieure sur les coupes (lecture « grappe » comme le brut)
    edge = al & ndi.binary_dilation(~al, iterations=1)
    newedge = edge & ndi.binary_dilation(cut, iterations=2)
    rgb[newedge] = (23, 63, 39)
    inner = al & ~edge & ndi.binary_dilation(newedge, iterations=1)
    rgb[inner] = (39, 79, 47)
    out = blank()
    out[..., :3] = rgb
    out[..., 3] = al * 255
    out[~al] = 0
    return out


# ---------------- placements ----------------
TEMPLE_XY = (358, 112)                     # souche + hokora, sommet de la clairière
BEAM = ('../jardin_secret_v1/segmentation/rayon.png')
TREES = [  # (sprite, x, y)  — pieds sur la pelouse, cimes pouvant passer sous le feuillage
    ('arbre_00_arbre', 190, 140),
    ('arbre_06_arbre', 500, 128),
    ('arbre_02_arbre', 150, 548),
    ('arbre_07_arbre', 548, 800),
    ('arbre_01_arbre', 442, 420),
    ('arbre_08_arbre', 250, 872),
]
CROWNS = [  # cimes seules façon Halcyon, en lisière (au-dessus du joueur)
    ('arbre_03_cime_seule', 200, 400),
    ('arbre_04_cime_seule', 520, 640),
    ('arbre_05_cime_seule', 196, 780),
    ('arbre_03_cime_seule', 540, 1000),
]
ROCKS = [('rocher_05', 610, 260), ('rocher_14', 206, 336), ('rocher_08', 222, 690),
         ('rocher_04', 630, 930), ('rocher_12', 300, 820), ('rocher_16', 480, 1010)]
CLOCKS = [8, 10, 14]
COULEURS = ['blanche', 'rose', 'jaune']


def split_tree(s):
    """troncs + ombre (sous le joueur) / cime (au-dessus) : cime = feuilles vertes et leur contour sombre."""
    a = s[..., 3] > 0
    r, g, b = [s[..., i].astype(int) for i in range(3)]
    leaf = a & (g > r + 20) & (g > b + 15) & (g >= 95)
    crown = ndi.binary_closing(leaf, iterations=3) & a
    crown = ndi.binary_dilation(crown, iterations=1) & a
    # l'ombre au sol (vert terne, sous la cime) reste au sol
    shadow = a & (np.abs(g - r) < 45) & (g < 110) & (np.arange(s.shape[0])[:, None] > s.shape[0] * 0.6)
    crown &= ~shadow
    low = s.copy()
    low[crown] = 0
    top = s.copy()
    top[~crown] = 0
    return low, top


def compose():
    sol, lawn, carpet, void = ground()
    L = {k: blank() for k in ['04_souche_temple', '03_rochers', '05_arbres_troncs', '06_arbres_cimes', '07_rayon']}
    occ = np.zeros((H, W), bool)
    placements = []
    warn = []

    t = spr('souche_temple')
    stamp(L['04_souche_temple'], t, *TEMPLE_XY, occ)
    placements.append(('souche_temple', TEMPLE_XY))

    beam = np.array(Image.open(BEAM).convert('RGBA'))
    bx = TEMPLE_XY[0] + t.shape[1] // 2 - beam.shape[1] // 2
    by = 0                                  # le rayon tombe du haut de la carte, comme dans la référence
    stamp(L['07_rayon'], beam, bx, by)
    placements.append(('rayon_natif_secretgarden', (bx, by)))

    for n, x, y in ROCKS:
        s = spr(n)
        stamp(L['03_rochers'], s, x, y, occ)
        placements.append((n, (x, y)))

    for n, x, y in TREES:
        s = spr(n)
        low, top = split_tree(s)
        stamp(L['05_arbres_troncs'], low, x, y, occ)
        stamp(L['06_arbres_cimes'], top, x, y)
        # contrôle : pied (bas du tronc) sur la pelouse
        fy = min(H - 1, y + s.shape[0] - 8)
        fx = x + s.shape[1] // 2
        if not lawn[fy, fx] and not carpet[fy, fx]:
            warn.append(f'{n} pied hors pelouse ({fx},{fy})')
        placements.append((n, (x, y)))
    for n, x, y in CROWNS:
        stamp(L['06_arbres_cimes'], spr(n), x, y)
        placements.append((n + '_lisiere', (x, y)))

    # fleurs : touffes 24×24 sur la pelouse libre (pas sur le tapis), espacées, 3 horloges
    rng = np.random.default_rng(24)
    free = lawn & ~ndi.binary_dilation(occ | carpet, iterations=10)
    free = ndi.binary_erosion(free, iterations=12, border_value=0)
    cand = np.argwhere(free)
    rng.shuffle(cand)
    flowers = []
    for y, x in cand:
        if len(flowers) >= 34:
            break
        if any(abs(x - fx) < 30 and abs(y - fy) < 26 for fx, fy, *_ in flowers):
            continue
        flowers.append((int(x), int(y), COULEURS[rng.integers(3)], CLOCKS[len(flowers) % 3], int(rng.integers(4))))

    return sol, L, flowers, placements, warn, (lawn, carpet, void)


SEQ = [0, 1, 0, 2]


def flower_layers(flowers):
    """Un calque par horloge et par pose : JSEC2_02_fleurs_cXX_pY. Dans PMDO : 3 calques animés,
    chacun avec 3 images, séquence 0,1,0,2, durée = XX frames de jeu par image."""
    poses = {(c, p): spr(f'fleur_{c}_pose{p}') for c in COULEURS for p in range(3)}
    out = {}
    for clock in CLOCKS:
        for p in range(3):
            lay = blank()
            for x, y, c, ck, off in flowers:
                if ck != clock:
                    continue
                stamp(lay, poses[(c, p)], x - 12, y - 18)
            out[(clock, p)] = lay
    return out


def over(dst, src):
    m = src[..., 3] > 0
    dst[m] = src[m]


if __name__ == '__main__':
    sol, L, flowers, placements, warn, _ = compose()
    fol = foliage()
    fl = flower_layers(flowers)
    comp = np.dstack([sol, np.full((H, W), 255, np.uint8)])
    for c in CLOCKS:
        over(comp, fl[(c, 0)])
    for k in ['03_rochers', '04_souche_temple', '05_arbres_troncs', '06_arbres_cimes', '07_rayon']:
        over(comp, L[k])
    Image.fromarray(comp).save('travail/v2_sans_feuillage.png')
    over(comp, fol)
    Image.fromarray(comp).save('travail/v2_composition.png')
    print('fleurs', len(flowers), 'avertissements', warn)
