# -*- coding: utf-8 -*-
"""
Cadre d'immersion en feuillage autour des bordures de bois.

Principe PMD : la pièce est une île de bois posée sur du noir. Pour que la
coupure ne se voie pas, on borde l'extrémité du contour de feuilles qui
débordent vers l'extérieur et s'éteignent dans le fond noir. Le feuillage :

- suit le contour réel de la salle (lancer de rayons depuis le centre) ;
- pend depuis le toit, s'accroche aux joues latérales, court en guirlande sur
  le rebord avant, et s'épaissit aux quatre extrémités du cadre ;
- s'arrête aux passages (là où c'est le plancher qui sort du contour) et aux
  fenêtres, qui doivent rester traversantes ;
- est assombri en fonction de la distance au bois : clair sur la bordure,
  presque noir à la pointe des feuilles, pour se fondre dans le fond noir.

Les feuilles viennent de la banque `sprites/individuels/vegetation_*.png` du
kit, elles ne sont pas redessinées.

Le feuillage est écrit dans le calque **10_bordure_avant** (bordure de premier
plan) : le kit garde ses 11 calques et ses contrôles.

Rejouable : les calques d'avant feuillage sont conservés dans
`source/feuillage_avant_cadre/`, et la salle 02 est reconstruite en rejouant
`retouche_hall_02.py` (passage ouest, demi-cercle de l'échelle, arche) avant
d'ajouter les feuilles.
"""
import io
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import retouche_hall_02 as H   # noqa: E402  (helpers PNG / Aseprite / nuit)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LABELS = H.LABELS
SAUV = os.path.join(REPO, 'source', 'feuillage_avant_cadre')
VEG = os.path.join(REPO, 'sprites', 'individuels')

# ---------------------------------------------------------------- banques
# Familles de la banque de végétation, triées par emploi dans le cadre.
POOLS = {
    # masses feuillues qui pendent : bord haut
    'canopee': ['01_01', '01_02', '01_05', '01_07', '01_08', '02_09', '05_10',
                '05_11', '06_01', '06_02', '06_09', '06_10', '09_03', '09_05',
                '12_02', '12_09'],
    # rideaux et lianes fines : compléments du bord haut et des joues
    'rideau': ['04_13', '04_14', '03_07', '05_07', '05_08', '08_06', '08_07',
               '08_08', '08_10', '09_02', '09_04', '12_03', '12_05'],
    # pièces d'angle : extrémités du cadre
    'angle': ['02_08', '03_02', '03_12', '03_13', '08_02', '12_01', '12_08',
              '06_06', '01_03', '02_06'],
    # guirlandes horizontales : rebord avant
    'guirlande': ['03_18', '03_19', '09_09', '09_10', '09_11', '09_12', '05_01',
                  '05_02', '08_01', '08_12', '08_13', '06_03', '06_04', '04_11'],
    # petites touffes : liaisons et remplissage
    'touffe': ['04_02', '04_03', '05_04', '08_11', '08_14', '09_06', '03_04',
               '03_17', '02_05', '02_07', '04_15'],
}

# Réglage par famille : échelle du sprite, part de la pièce qui sort du bois.
REGLAGE = {
    'canopee':   {'echelle': (0.34, 0.52), 'sortie': 0.58},
    'rideau':    {'echelle': (0.30, 0.48), 'sortie': 0.52},
    'angle':     {'echelle': (0.36, 0.58), 'sortie': 0.60},
    'guirlande': {'echelle': (0.34, 0.54), 'sortie': 0.50},
    'touffe':    {'echelle': (0.32, 0.52), 'sortie': 0.55},
}

# Accents : grosses touffes aux quatre extrémités du cadre.
ACCENTS = {'canopee': (0.55, 0.80), 'angle': (0.60, 0.85)}

BANDE = 26.0          # profondeur du fondu vers le noir, en px
FOND = np.array([7, 12, 8], float)      # vert de nuit forestière


def sprite(nom):
    return Image.open(os.path.join(VEG, 'vegetation_%s.png' % nom)).convert('RGBA')


# ------------------------------------------------------------- géométrie

def masques(L):
    """Silhouette pleine de la salle, bois porteur et plancher nu."""
    bois = np.zeros(L['01_sol'].shape[:2], bool)
    for n in ('02_structure', '03_cadres_fenetres', '04_tableaux',
              '05_porte_maitre', '10_bordure_avant'):
        bois |= L[n][:, :, 3] > 8
    sol = L['01_sol'][:, :, 3] > 8
    plein = ndimage.binary_fill_holes(bois | sol)
    return plein, bois, sol


def contour_ordonne(plein, espacement, rng):
    """Points d'accroche répartis à intervalle constant le long du contour, avec
    la normale sortante lissée. On suit le bord réel, pas un cercle : les bouts
    plats du haut et le rebord avant reçoivent autant de feuilles que les joues.
    """
    bord = plein & ~ndimage.binary_erosion(plein, np.ones((3, 3), bool))
    ys, xs = np.nonzero(bord)
    cy, cx = np.nonzero(plein)[0].mean(), np.nonzero(plein)[1].mean()
    ordre = np.argsort(np.arctan2(ys - cy, xs - cx))
    ys, xs = ys[ordre], xs[ordre]

    flou = ndimage.gaussian_filter(plein.astype(float), 7.0)
    gy, gx = np.gradient(flou)

    pts, cumul = [], espacement
    for i in range(len(xs)):
        x, y = int(xs[i]), int(ys[i])
        if i:
            cumul += min(float(np.hypot(x - xs[i - 1], y - ys[i - 1])), espacement)
        if cumul < espacement * rng.uniform(0.82, 1.18):
            continue
        cumul = 0.0
        dx, dy = -gx[y, x], -gy[y, x]
        n = float(np.hypot(dx, dy))
        if n < 1e-6:
            dx, dy = x - cx, y - cy
            n = float(np.hypot(dx, dy)) or 1.0
        pts.append((x, y, dx / n, dy / n, 0.0))
    return pts


def famille(dy, dx):
    """Choix de la famille suivant l'orientation de la normale sortante."""
    if dy < -0.62:
        return 'canopee'
    if dy > 0.62:
        return 'guirlande'
    if abs(dy) < 0.28:
        return 'angle'
    return 'rideau' if dy < 0 else 'touffe'


def oriente(im, dx, dy, rng):
    """Pas de rotation libre en pixel art : miroirs et quarts de tour."""
    if dx < 0:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    elif rng.random() < 0.35:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    if dy > 0.62 and rng.random() < 0.5:
        im = im.transpose(Image.FLIP_TOP_BOTTOM)
    return im


def redimensionne(im, k):
    w = max(6, int(round(im.width * k)))
    h = max(6, int(round(im.height * k)))
    q = np.array(im.resize((w, h), Image.LANCZOS))
    q[:, :, 3] = np.where(q[:, :, 3] >= 112, 255, 0)     # alpha franc
    box = Image.fromarray(q, 'RGBA').getbbox()
    return Image.fromarray(q, 'RGBA').crop(box) if box else Image.fromarray(q, 'RGBA')


def marge_cadre(x, y, dx, dy, W, H):
    """Place disponible entre le point de contour et le bord de l'image, dans
    la direction sortante : le feuillage ne doit pas être coupé net."""
    m = 1e9
    if dx > 1e-3:
        m = min(m, (W - 2 - x) / dx)
    if dx < -1e-3:
        m = min(m, (x - 1) / -dx)
    if dy > 1e-3:
        m = min(m, (H - 2 - y) / dy)
    if dy < -1e-3:
        m = min(m, (y - 1) / -dy)
    return max(0.0, min(m, 40.0))


def extremites(plein, points):
    """Index des points de contour les plus extrêmes : haut-gauche, haut,
    haut-droit, gauche, droite. Ce sont les angles du cadre, on y met les
    grosses touffes."""
    ys, xs = np.nonzero(plein)
    cx, cy = xs.mean(), ys.mean()
    cibles = [(-1, -0.55), (0, -1), (1, -0.55), (-1, -0.05), (1, -0.05)]
    idx = set()
    for tx, ty in cibles:
        n = np.hypot(tx, ty)
        tx, ty = tx / n, ty / n
        best, bi = -9, None
        for i, (x, y, dx, dy, a) in enumerate(points):
            s = dx * tx + dy * ty
            if s > best:
                best, bi = s, i
        if bi is not None:
            idx.update({bi, max(0, bi - 1), min(len(points) - 1, bi + 1)})
    return idx


def zones_passage(L, acces):
    """Corridors de passage : la langue de plancher qui sort du cadre sur un
    côté. On la repère à l'extrémité du plancher dans la direction de l'accès,
    puis on élargit d'un rayon de sécurité : le feuillage s'arrête là."""
    sol = L['01_sol'][:, :, 3] > 8
    if not sol.any():
        return np.zeros_like(sol)
    ys, xs = np.nonzero(sol)
    seed = np.zeros_like(sol)
    directions = set()
    for a in acces:
        u = a.strip().upper()
        if u in ('O', 'OUEST') or u.endswith(' O'):
            directions.add('O')
        if u in ('E', 'EST') or u.endswith(' E'):
            directions.add('E')
        if u in ('S', 'SUD') or u.endswith(' S'):
            directions.add('S')
        if u in ('N', 'NORD') or u.endswith(' N') or 'ÉCHELLE N' in u:
            directions.add('N')
    for d in directions:
        if d == 'O':
            seed[:, :xs.min() + 7] |= sol[:, :xs.min() + 7]
        if d == 'E':
            seed[:, xs.max() - 6:] |= sol[:, xs.max() - 6:]
        if d == 'S':
            seed[ys.max() - 6:, :] |= sol[ys.max() - 6:, :]
        if d == 'N':
            seed[:ys.min() + 7, :] |= sol[:ys.min() + 7, :]
    if not seed.any():
        return np.zeros_like(sol)
    return ndimage.binary_dilation(seed, np.ones((85, 85), bool)) & \
        ndimage.binary_dilation(sol, np.ones((85, 85), bool))


def frange(plein, rng, interdit, fenetres):
    """Frange de feuillage continue sur l'arête du bois : une suite de petites
    masses de feuilles qui relient les bouquets, cassent la découpe nette du
    contour et donnent son épaisseur au cadre. Aplats francs, pas de dégradé :
    on reste en pixel art."""
    Hh, Ww = plein.shape
    masse = np.zeros((Hh, Ww), bool)
    yy, xx = np.mgrid[-6:7, -6:7]
    for x, y, dx, dy, _ in contour_ordonne(plein, 4.0, rng):
        if interdit[y, x] or fenetres[y, x]:
            continue
        r = rng.choice([2, 3, 3, 4, 4, 5])
        px = int(round(x + dx * rng.uniform(-1.5, 2.6)))
        py = int(round(y + dy * rng.uniform(-1.5, 2.6)))
        y0, y1 = max(0, py - 6), min(Hh, py + 7)
        x0, x1 = max(0, px - 6), min(Ww, px + 7)
        if y1 <= y0 or x1 <= x0:
            continue
        disque = (xx ** 2 + (yy * 1.15) ** 2) <= r * r
        masse[y0:y1, x0:x1] |= disque[y0 - py + 6:y1 - py + 6, x0 - px + 6:x1 - px + 6]
    masse &= ~interdit & ~fenetres
    if not masse.any():
        return np.zeros((Hh, Ww, 4), 'uint8')

    # marbrure en gros pixels : aplats de feuillage, jamais un dégradé lisse
    bh, bw = Hh // 4 + 1, Ww // 4 + 1
    grain = np.kron(rng.rand(bh, bw), np.ones((4, 4)))[:Hh, :Ww]
    grain = 0.65 * grain + 0.35 * np.kron(rng.rand(bh // 3 + 1, bw // 3 + 1),
                                          np.ones((12, 12)))[:Hh, :Ww]
    lumiere = np.clip(0.5 + (np.mgrid[0:Hh, 0:Ww][0] * -0.0016 + 0.35), 0, 1)

    a = np.zeros((Hh, Ww, 4), 'uint8')
    tons = np.array([[24, 38, 19], [44, 66, 27], [72, 100, 38], [104, 134, 50]])
    idx = np.clip(np.rint(grain * 2.2 + lumiere * 1.1 - 0.35), 0, 3).astype(int)
    a[:, :, :3] = tons[idx]
    a[:, :, 3] = np.where(masse, 255, 0)
    # cerne sombre sur le pourtour de la masse : elle se détache du bois
    cerne = masse & ~ndimage.binary_erosion(masse, np.ones((3, 3), bool))
    a[cerne, :3] = np.array([15, 24, 13], 'uint8')
    return a


# ------------------------------------------------------------- feuillage

def feuillage(L, rid, acces, graine, pas, densite=1.0):
    """Compose la couronne de feuilles d'une salle."""
    Himg, Wimg = L['01_sol'].shape[:2]
    rng = np.random.RandomState(graine)
    plein, bois, sol = masques(L)

    # passages : le plancher qui sort du cadre, aucun feuillage ne les barre
    interdit = zones_passage(L, acces)

    # fenêtres : elles doivent rester traversantes
    mq = os.path.join(REPO, 'fenetres_exterieur', rid, 'masque.png')
    if os.path.exists(mq):
        trous = np.array(Image.open(mq).convert('L')) > 0
        fenetres = ndimage.binary_dilation(trous, np.ones((9, 9), bool))
    else:
        fenetres = np.zeros_like(plein)

    canvas = Image.new('RGBA', (Wimg, Himg))
    canvas.alpha_composite(Image.fromarray(frange(plein, rng, interdit, fenetres), 'RGBA'))
    poses = 0
    points = contour_ordonne(plein, pas, rng)
    accents = extremites(plein, points)

    for i, (x, y, dx, dy, ang) in enumerate(points):
        if interdit[y, x] or fenetres[y, x]:
            continue
        poids = densite * (1.0 if dy < -0.2 else (0.85 if dy < 0.4 else 0.6))
        if rng.random() > poids:
            continue
        gros = i in accents
        fam = famille(dy, dx)
        if gros and fam in ACCENTS:
            ech = ACCENTS[fam]
        else:
            ech = REGLAGE[fam]['echelle']
        nom = POOLS[fam][rng.randint(len(POOLS[fam]))]
        im = oriente(sprite(nom), dx, dy, rng)
        im = redimensionne(im, rng.uniform(*ech))
        etendue = abs(dx) * im.width + abs(dy) * im.height
        # la pièce mord le bois d'un côté et déborde de l'autre, sans sortir du cadre
        libre = marge_cadre(x, y, dx, dy, Wimg, Himg)
        sortie = min(etendue * REGLAGE[fam]['sortie'], libre)
        cxp = x + dx * (sortie - etendue / 2.0)
        cyp = y + dy * (sortie - etendue / 2.0)
        ox = int(round(cxp - im.width / 2.0))
        oy = int(round(cyp - im.height / 2.0))
        tampon = Image.new('RGBA', (Wimg, Himg))
        tampon.paste(im, (ox, oy), im)
        canvas.alpha_composite(tampon)
        poses += 1

    a = np.array(canvas)
    a[fenetres & (a[:, :, 3] > 0)] = 0
    a[interdit & (a[:, :, 3] > 0)] = 0
    return a, plein, poses


def fondu_noir(a, plein):
    """Fondu du feuillage : encore vivant sur le bois, éteint dans le noir."""
    dehors = ndimage.distance_transform_edt(~plein)
    dedans = ndimage.distance_transform_edt(plein)
    k = np.clip(1.0 - dehors / BANDE, 0.0, 1.0)          # 1 sur le bois, 0 au loin
    m = a[:, :, 3] > 0
    rgb = a[:, :, :3].astype(float)

    # 1. extinction vers l'extérieur : la pointe des feuilles rejoint le noir
    f = 0.16 + 0.60 * (k ** 1.35)
    # 2. les feuilles qui mordent loin sur le bois passent en retrait
    f = f * np.clip(1.0 - dedans / 90.0, 0.62, 1.0)
    rgb *= f[:, :, None]
    # 3. dérive vers le vert profond au fur et à mesure qu'on quitte le bois
    w = ((1.0 - k) * 0.72)[:, :, None]
    rgb = rgb * (1 - w) + FOND * w
    # 4. accroche chaude côté salle : le bois renvoie sa lumière dans le feuillage
    chaud = np.clip(dedans / 16.0, 0, 1)[:, :, None] * 0.22
    rgb = rgb * (1 - chaud) + np.array([178, 138, 62]) * chaud

    b = a.copy()
    b[:, :, :3] = np.clip(np.rint(rgb), 0, 255).astype('uint8')
    b[~m] = 0
    return b


def quantifie(a, couleurs=30):
    """Ramène le feuillage à une petite palette : le rendu reste du pixel art."""
    m = a[:, :, 3] > 0
    if not m.any():
        return a
    plat = Image.fromarray(a[:, :, :3], 'RGB').quantize(
        colors=couleurs, method=Image.MEDIANCUT, dither=Image.NONE).convert('RGB')
    b = a.copy()
    b[:, :, :3] = np.array(plat)
    b[~m] = 0
    return b


def applique(L, rid, acces, graine, pas, densite=1.0):
    a, plein, poses = feuillage(L, rid, acces, graine, pas, densite)
    a = quantifie(fondu_noir(a, plein))
    base = Image.fromarray(L['10_bordure_avant'], 'RGBA')
    base.alpha_composite(Image.fromarray(a, 'RGBA'))
    L['10_bordure_avant'] = np.array(base)
    return poses


# --------------------------------------------------------------- écriture

def calques_du_disque(dossier, palette):
    """Les 11 calques d'une salle, en prenant la bordure avant dans la copie
    d'avant feuillage : le script repart toujours du bois nu, il est donc
    rejouable à l'identique."""
    src = os.path.join(REPO, 'calques', dossier, palette)
    sauv = os.path.join(SAUV, dossier, palette)
    if not os.path.isdir(sauv):
        os.makedirs(sauv)
        Image.open(os.path.join(src, '10_bordure_avant.png')).save(
            os.path.join(sauv, '10_bordure_avant.png'))
    L = {}
    for n, _ in LABELS:
        d = sauv if n == '10_bordure_avant' else src
        L[n] = np.array(Image.open(os.path.join(d, n + '.png')).convert('RGBA'))
    return L


def ecrire(L, dossier, rid, palette, extra=()):
    d = os.path.join(REPO, 'calques', dossier, palette)
    for n, _ in LABELS:
        H.png(Image.fromarray(L[n], 'RGBA'), os.path.join(d, n + '.png'))
    for n in extra:
        H.png(Image.fromarray(L[n], 'RGBA'), os.path.join(d, n + '.png'))

    fd = os.path.join(REPO, 'salles', dossier)
    Himg, Wimg = L['01_sol'].shape[:2]
    comp = Image.new('RGBA', (Wimg, Himg))
    base = Image.new('RGBA', (Wimg, Himg))
    export = []
    for n, label in LABELS:
        q = Image.fromarray(L[n], 'RGBA')
        comp.alpha_composite(q)
        if n != '00_exterieur':
            base.alpha_composite(q)
        export.append((label, q))
    H.png(comp, os.path.join(fd, 'salle_%s.png' % palette))
    H.png(base, os.path.join(fd, 'base_%s_transparente.png' % palette))
    chroma = Image.new('RGBA', (Wimg, Himg), (255, 0, 255, 255))
    chroma.alpha_composite(base)
    H.png(chroma, os.path.join(fd, 'base_%s_magenta.png' % palette))
    H.ase(os.path.join(fd, '%s_%s.aseprite' % (rid, palette)), export, (Wimg, Himg))

    cols, rows = Wimg // 8, Himg // 8
    count = cols * rows
    sets, tls = [], []
    for i, (n, label) in enumerate(LABELS):
        occ = L[n][:, :, 3].reshape(rows, 8, cols, 8).max((1, 3)) > 0
        first = 1 + i * count
        data = np.arange(first, first + count, dtype=np.uint32).reshape(rows, cols)
        data[~occ] = 0
        sets.append({'firstgid': first, 'name': n, 'tilewidth': 8, 'tileheight': 8,
                     'tilecount': count, 'columns': cols,
                     'image': '../calques/%s/%s/%s.png' % (dossier, palette, n),
                     'imagewidth': Wimg, 'imageheight': Himg, 'margin': 0, 'spacing': 0})
        tls.append({'id': i + 1, 'name': label, 'type': 'tilelayer', 'width': cols,
                    'height': rows, 'x': 0, 'y': 0, 'opacity': 1, 'visible': True,
                    'data': data.ravel().tolist()})
    tm = {'type': 'map', 'version': '1.10', 'tiledversion': '1.11.0',
          'orientation': 'orthogonal', 'renderorder': 'right-down', 'tilewidth': 8,
          'tileheight': 8, 'width': cols, 'height': rows, 'infinite': False,
          'nextlayerid': len(LABELS) + 1, 'nextobjectid': 1, 'layers': tls,
          'tilesets': sets}
    with io.open(os.path.join(REPO, 'tiled', '%s_%s.tmj' % (rid, palette)), 'w',
                 encoding='utf-8') as f:
        json.dump(tm, f, ensure_ascii=False, separators=(',', ':'))


# ------------------------------------------------------------------ salles

def calques_jour(salle):
    """Calques de départ d'une salle, feuillage non compris. La salle 02 est
    reconstruite en rejouant ses retouches (passage ouest, demi-cercle de
    l'échelle, arche) pour que tout reste rejouable dans l'ordre."""
    dossier, rid = salle['dossier'], salle['id']
    if rid == '02':
        J = H.charger('jour')
        H.passage_ouest(J)
        H.trou_sous_tronc(J)
        H.porte(J)
        return J, ('05_porte_maitre_battants',)
    return calques_du_disque(dossier, 'jour'), ()


def traite(salle, apercu=False):
    dossier, rid = salle['dossier'], salle['id']
    J, extra = calques_jour(salle)
    largeur = J['01_sol'].shape[1]
    pas = 30.0 if largeur > 900 else 25.0
    poses = applique(J, rid, salle['acces'], graine=int(rid) * 977 + 13, pas=pas)

    if apercu:
        comp = Image.new('RGBA', (J['01_sol'].shape[1], J['01_sol'].shape[0]))
        for n, _ in LABELS:
            comp.alpha_composite(Image.fromarray(J[n], 'RGBA'))
        fond = Image.new('RGBA', comp.size, (0, 0, 0, 255))
        fond.alpha_composite(comp)
        fond.convert('RGB').save('/tmp/apercu_%s.png' % rid)
        return poses

    N = {}
    for n in J:
        N[n] = J[n].copy() if n == '08_ombres_acces' else H.nuit(J[n])
    N['00_exterieur'] = np.array(Image.open(os.path.join(
        REPO, 'calques', dossier, 'nuit', '00_exterieur.png')).convert('RGBA'))

    ecrire(J, dossier, rid, 'jour', extra)
    ecrire(N, dossier, rid, 'nuit', extra)
    return poses


def main():
    apercu = '--apercu' in sys.argv
    voulues = [a for a in sys.argv[1:] if not a.startswith('-')]
    kit = json.loads(io.open(os.path.join(REPO, 'kit.json'), encoding='utf-8').read())
    for salle in kit['salles']:
        if voulues and salle['id'] not in voulues:
            continue
        poses = traite(salle, apercu)
        print('salle %s — %d bouquets de feuillage%s'
              % (salle['id'], poses, ' (aperçu)' if apercu else ''))


if __name__ == '__main__':
    main()
