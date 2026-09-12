# -*- coding: utf-8 -*-
"""Tileset animé « Falaises de Métano / Treasure Town » pour le kit Guilde Treehouse.

Genère, pour les 6 ambiances du kit :
  - falaises/<amb>/tileset_falaises_<amb>.aseprite : feuille Aseprite multi-frames
    (4 frames de 150 ms, chaque frame = la planche complète de 24 tuiles 24×24) ;
  - falaises/<amb>/planche_f1..f4.png : les mêmes frames en PNG tilesheet ;
  - falaises/<amb>/animation.png : APNG de prévisualisation ;
  - falaises/exemple_<amb>.png : scène d'assemblage (falaises reliées) ;
  - falaises/falaises.json : manifeste (tuiles, animations, chemins) ;
  - apercu_falaises.html : aperçu autonome hors ligne animé.

Style : roche ocre type Trésor-Ville (PMD Explorateurs) harmonisée avec la palette
teal/verte du panorama extérieur du kit. Tuiles de 24 px (multiple de la grille
8 px du kit), raccords sans couture sur les 4 côtés pour les parois.
"""
from pathlib import Path
from PIL import Image
import json, random, struct, zlib, base64, io

R = Path(__file__).resolve().parents[1]
OUT = R / 'falaises'
OUT.mkdir(exist_ok=True)

T = 24                      # côté d'une tuile
COLS, ROWS = 8, 3           # planche : 8 × 3 tuiles
FRAMES = 4
DUREE = 150                 # ms par frame, comme les animations PMD
AMBIANCES = ['jour', 'nuit', 'crepuscule', 'aube', 'soir', 'orageux']

# ---------------------------------------------------------------- palettes
ROC_HI    = (232, 199, 143)   # lèvre supérieure / arête éclairée
ROC_CLAIR = (212, 174, 118)   # noise clair
ROC_MID   = (198, 156, 100)   # corps de roche
ROC_LOW   = (172, 128, 78)    # poche d'ombre / flanc
ROC_DARK  = (136, 98, 60)     # strate, ombre portée
ROC_LINE  = (104, 72, 44)     # contour de silhouette, fissure
HER_HI    = (188, 234, 152)
HER_MID   = (142, 214, 128)
HER_LOW   = (99, 171, 99)
HER_DARK  = (66, 126, 82)
SOL       = (122, 92, 58)
BOIS_HI   = (216, 170, 104)
BOIS_MID  = (178, 130, 72)
BOIS_DRK  = (126, 88, 48)
CORDE_HI  = (236, 218, 172)
CORDE_MID = (198, 174, 122)
BRUME     = (226, 241, 241)
FLEURS    = [(250, 250, 246), (255, 214, 110), (232, 110, 120)]

# Teintes d'ambiance calées sur les moyennes des panoramas exterieur/*.png
# (nuit = formule exacte du kit).
TEINTES = {
    'jour':       ((1.00, 1.00, 1.00), (0, 0, 0)),
    'nuit':       ((0.36, 0.34, 0.43), (9, 10, 19)),
    'crepuscule': ((0.48, 0.40, 0.70), (8, 8, 30)),
    'aube':       ((0.95, 0.76, 0.90), (10, 8, 14)),
    'soir':       ((0.98, 0.80, 0.70), (6, 6, 10)),
    'orageux':    ((0.63, 0.58, 0.75), (4, 5, 10)),
}


def teinte(im, amb):
    m, a = TEINTES[amb]
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, al = px[x, y]
            if al:
                px[x, y] = (min(255, int(r * m[0] + a[0])), min(255, int(g * m[1] + a[1])),
                            min(255, int(b * m[2] + a[2])), al)
    return im


# ---------------------------------------------------------------- bruit périodique
def lisse(t):
    return t * t * (3 - 2 * t)


def bruit(seed, cells=6):
    """Bruit de valeur périodique sur 24 px : les tuiles restent sans couture."""
    rng = random.Random(seed)
    lat = [[rng.random() for _ in range(cells)] for _ in range(cells)]
    pas = T / cells

    def n(x, y):
        fx, fy = x / pas, y / pas
        x0, y0 = int(fx) % cells, int(fy) % cells
        x1, y1 = (x0 + 1) % cells, (y0 + 1) % cells
        tx, ty = lisse(fx - int(fx)), lisse(fy - int(fy))
        h0 = lat[y0][x0] * (1 - tx) + lat[y0][x1] * tx
        h1 = lat[y1][x0] * (1 - tx) + lat[y1][x1] * tx
        return h0 * (1 - ty) + h1 * ty
    return n


# ---------------------------------------------------------------- roche de base
def poche(p, rng, ton, rmin, rmax):
    """Poche organique emballée mod 24 : pas de trame, raccord sans couture."""
    cx, cy = rng.randrange(T), rng.randrange(T)
    r = rng.randint(rmin, rmax)
    for dy in range(-r, r + 1):
        w = int((r * r - dy * dy) ** 0.5) + rng.randint(-1, 1)
        if w < 1:
            continue
        for dx in range(-w, w + 1):
            yy, xx = (cy + dy) % T, (cx + dx) % T
            if p[yy][xx] != ROC_DARK:
                p[yy][xx] = ton


def motif_roche():
    """Motif 24×24 périodique : tout raccord rocheux y est échantillonné.
    Paroi calme façon Trésor-Ville : corps ocre posé, grandes poches
    d'ombre et zones claires, terrasses horizontales discontinues,
    deux traînées verticales, grain rare. Période 24 : sans couture."""
    rng = random.Random(20260912)
    p = [[ROC_MID] * T for _ in range(T)]
    for _ in range(3):
        poche(p, rng, ROC_LOW, 4, 6)
    for _ in range(2):
        poche(p, rng, ROC_CLAIR, 3, 4)
    for b in range(3):                                    # terrasses discontinues
        y = b * 8 + 7
        for seg in range(2):
            x0 = (b * 7 + seg * 12 + rng.randint(0, 3)) % T
            ln = rng.randint(4, 7)
            for k in range(ln):
                xx = (x0 + k) % T
                p[y][xx] = ROC_LOW
                if k == 0:
                    p[y][xx] = ROC_DARK
                if rng.random() < 0.3:
                    p[(y - 1) % T][xx] = ROC_CLAIR
    for vx, ln in ((5, 13), (16, 10)):                    # traînées verticales
        y0 = rng.randrange(T)
        x = vx
        for i in range(ln):
            yy = (y0 + i) % T
            if i % 4 == 0:
                x = vx + rng.choice((-1, 0, 0, 1))
            p[yy][x % T] = ROC_LOW
            if i % 5 == 2:
                p[yy][(x + 1) % T] = ROC_DARK
    for _ in range(7):
        p[rng.randrange(T)][rng.randrange(T)] = ROC_DARK
    for _ in range(5):
        p[rng.randrange(T)][rng.randrange(T)] = ROC_HI
    return p


ROC = motif_roche()


def roc(gy, x):
    return ROC[gy % T][x % T]


def neuf():
    return [[(0, 0, 0, 0)] * T for _ in range(T)]


def pose(g, x, y, c):
    if 0 <= x < T and 0 <= y < T:
        g[y][x] = c if len(c) == 4 else c + (255,)


SWAY = [0, 1, 0, -1]          # balancement 4 frames, comme l'herbe PMD


# ---------------------------------------------------------------- tuiles roche
def t_face(f, fissure=False, mousse=False):
    g = neuf()
    for y in range(T):
        for x in range(T):
            g[y][x] = roc(y, x) + (255,)
    if fissure:
        rng = random.Random(91)
        x = 10
        for y in range(T):
            x = min(16, max(6, x + rng.choice((-1, 0, 0, 1))))
            pose(g, x, y, ROC_LINE)
            if y % 4 == 1:
                pose(g, x + 1, y, ROC_DARK)
    if mousse:
        rng = random.Random(57)
        for _ in range(2):
            cx, cy = rng.randrange(T), rng.randrange(T)
            r = rng.randint(3, 5)
            for dy in range(-r, r + 1):
                w = max(1, int((r * r - dy * dy) ** 0.5))
                for dx in range(-w, w + 1):
                    yy, xx = (cy + dy) % T, (cx + dx) % T
                    bord = abs(dx) >= w - 1 or abs(dy) >= r - 1
                    g[yy][xx] = (HER_DARK if bord else (HER_LOW if (xx + yy) % 2 else HER_MID)) + (255,)
        for _ in range(6):
            g[rng.randrange(T)][rng.randrange(T)] = HER_DARK + (255,)
    return g


def couronne_herbe(g, y0, f):
    """Surface herbeuse épaisse : frange claire, corps, ourlet de terre."""
    rng = random.Random(400 + f)
    for x in range(T):
        g[y0][x] = HER_HI if (x * 7 + f) % 9 else HER_MID
        g[y0 + 1][x] = HER_MID
        g[y0 + 2][x] = HER_MID if (x + f) % 5 else HER_LOW
        g[y0 + 3][x] = HER_LOW
        g[y0 + 4][x] = HER_LOW if (x * 3 + f) % 7 else HER_DARK
        g[y0 + 5][x] = HER_DARK if (x + f) % 6 < 2 else SOL
        g[y0 + 6][x] = SOL if (x + f) % 8 < 5 else ROC_DARK
    for _ in range(5):                                    # mèches animées
        x = rng.randrange(T)
        g[y0 + 1][x] = HER_HI
        g[y0 + 2][(x + 1) % T] = HER_HI
    for x in range(T):                                    # dents descendantes
        if (x * 5 + f * 3) % 11 == 2:
            g[y0 + 4][x] = HER_DARK
            g[y0 + 5][x] = HER_DARK


def t_sommet(f):
    g = t_face(f)
    couronne_herbe(g, 0, f)
    return g


def t_plateau(f):
    g = neuf()
    for y in range(T):
        for x in range(T):
            g[y][x] = HER_MID
    rng = random.Random(900 + f)
    for _ in range(4):
        cx, cy = rng.randrange(T), rng.randrange(T)
        r = rng.randint(3, 5)
        for dy in range(-r, r + 1):
            w = int((r * r - dy * dy) ** 0.5) + rng.randint(-1, 1)
            for dx in range(-w, w + 1):
                bord = abs(dx) >= w - 1 or abs(dy) >= r - 1
                g[(cy + dy) % T][(cx + dx) % T] = HER_MID if bord else HER_LOW
    for _ in range(3):
        cx, cy = rng.randrange(T), rng.randrange(T)
        r = rng.randint(2, 3)
        for dy in range(-r, r + 1):
            w = max(1, int((r * r - dy * dy) ** 0.5))
            for dx in range(-w, w + 1):
                g[(cy + dy) % T][(cx + dx) % T] = HER_MID
    for _ in range(7):                                    # brins animés
        x, y = rng.randrange(T), rng.randrange(T)
        g[y][x] = HER_HI
        g[(y + 1) % T][x] = HER_MID
    for _ in range(5):
        x, y = rng.randrange(T), rng.randrange(T)
        g[y][x] = HER_DARK
    return g


def profil_bord(y, off):
    """Silhouette à bossages arrondis : chaque bande de 8 px bombe dehors."""
    dy = abs((y % 8) - 3)
    prot = max(0, 2 - dy)
    return 3 - prot + ((y // 8) + off) % 2


def lobe_dy(y):
    return (y % 8) - 3


def t_bord(f, droite=False):
    g = neuf()
    for y in range(T):
        e = profil_bord(y, 0 if droite else 3)
        dy = lobe_dy(y)
        for x in range(T):
            xx = (T - 1 - x) if droite else x
            if xx < e:
                continue
            if xx == e:
                c = ROC_DARK
            elif xx == e + 1:
                c = ROC_HI if dy <= -2 else (ROC_LOW if dy >= 2 else ROC_MID)
            elif xx == e + 2 and dy >= 2:
                c = ROC_LOW
            else:
                c = roc(y, xx)
            g[y][x] = c + (255,)
    return g


def t_coin(f, droite=False):
    g = t_sommet(f)
    for y in range(T):
        e = profil_bord(y, 0 if droite else 3)
        dy = lobe_dy(y)
        if y < 8:
            e = max(e, 8 - y)                             # coin arrondi
        for x in range(T):
            xx = (T - 1 - x) if droite else x
            if xx < e:
                g[y][x] = (0, 0, 0, 0)
            elif xx == e:
                g[y][x] = ROC_DARK + (255,)
            elif xx == e + 1:
                g[y][x] = (ROC_HI if dy <= -2 or y < 8 else
                           (ROC_LOW if dy >= 2 else ROC_MID)) + (255,)
            elif xx == e + 2 and dy >= 2 and y > 7:
                g[y][x] = ROC_LOW + (255,)
    return g


def t_sommet_nu(f):
    g = t_face(f)
    rng = random.Random(300)
    for x in range(T):
        g[0][x] = ROC_HI if (x * 7) % 9 else ROC_CLAIR
        g[1][x] = ROC_CLAIR
        g[2][x] = ROC_MID if x % 5 else ROC_LOW
    for _ in range(4):
        x = rng.randrange(T)
        g[1][x] = ROC_HI
    return g


def t_pente(f, droite=True):
    g = neuf()
    for x in range(T):
        d = (x // 2) * 2
        surf = (T - 1 - d) if droite else d
        dent = 1 if (x * 5 + f) % 8 == 0 else 0
        for y in range(max(0, surf - dent), T):
            k = y - surf
            if k < 0:
                c = HER_HI
            elif k == 0:
                c = HER_HI if (x * 7 + f) % 9 else HER_MID
            elif k <= 2:
                c = HER_MID
            elif k == 3:
                c = HER_LOW
            elif k == 4:
                c = SOL
            else:
                c = roc(y, x)
            g[y][x] = c + (255,)
    return g


def t_escalier(f, droite=True):
    g = neuf()
    for k in range(3):
        x0, x1 = k * 8, k * 8 + 7
        top = (16 - 8 * k) if droite else (8 * k)
        if not droite:
            top = 16 - top
        for x in range(x0, x1 + 1):
            for y in range(top, T):
                kk = y - top
                if kk == 0:
                    c = HER_HI if (x * 7 + f) % 9 else HER_MID
                elif kk <= 2:
                    c = HER_MID
                elif kk == 3:
                    c = SOL
                else:
                    c = roc(y, x)
                g[y][x] = c + (255,)
        for y in range(top, min(T, top + 8)):             # contremarche
            xx = x0 if droite else x1
            g[y][xx] = ROC_LINE + (255,)
            g[y][xx + (1 if droite else -1)] = ROC_LOW + (255,)
    return g


# ---------------------------------------------------------------- ponts / échelle
def t_pont_corde(f):
    g = neuf()
    s = SWAY[f]
    for x in range(T):
        pose(g, x, 5 + s, CORDE_HI if (x + f) % 6 < 4 else CORDE_MID)
        pose(g, x, 17, CORDE_MID if x % 4 else CORDE_HI)
    for x in (2, 12, 22):
        for y in range(6 + s, 12):
            pose(g, x, y, CORDE_MID)
    for x in range(T):                                    # tablier
        pose(g, x, 12, BOIS_HI)
        pose(g, x, 13, BOIS_MID if x % 4 < 3 else BOIS_DRK)
        pose(g, x, 14, BOIS_MID if x % 4 < 3 else BOIS_DRK)
        pose(g, x, 15, BOIS_MID if (x + 2) % 4 < 3 else BOIS_DRK)
        pose(g, x, 16, BOIS_DRK)
    return g


def t_pilier_corde(f):
    g = t_pont_corde(f)
    for y in range(2, 24):
        for x in range(10, 14):
            g[y][x] = (BOIS_HI if x == 10 else BOIS_DRK if x == 13 else BOIS_MID) + (255,)
    for x in range(9, 15):
        g[2][x] = BOIS_HI + (255,)
        g[3][x] = BOIS_MID + (255,)
    g[6][11] = CORDE_MID + (255,)
    g[6][12] = CORDE_MID + (255,)
    return g


def t_pont_bois(f):
    g = neuf()
    for x in range(T):
        pose(g, x, 3, BOIS_HI)
        pose(g, x, 4, BOIS_MID if x % 6 < 5 else BOIS_DRK)
    for x in (2, 3, 20, 21):
        for y in range(3, 12):
            pose(g, x, y, BOIS_MID if x % 2 else BOIS_DRK)
    for x in range(T):
        pose(g, x, 12, BOIS_HI)
        for y in range(13, 18):
            pose(g, x, y, BOIS_MID if y % 3 else BOIS_DRK)
        pose(g, x, 18, BOIS_DRK)
    for x in range(6, 18):
        pose(g, x, 10, BOIS_DRK if x % 3 else BOIS_MID)
    return g


def t_pilier_bois(f):
    g = t_pont_bois(f)
    for y in range(1, 24):
        for x in range(9, 15):
            g[y][x] = (BOIS_HI if x == 9 else BOIS_DRK if x == 14 else BOIS_MID) + (255,)
    for x in range(8, 16):
        g[1][x] = BOIS_HI + (255,)
    return g


def t_echelle(f):
    g = neuf()
    for y in range(T):
        for x in (8, 9, 14, 15):
            g[y][x] = (BOIS_MID if x in (9, 14) else BOIS_DRK) + (255,)
    for y in (3, 9, 15, 21):
        for x in range(10, 14):
            g[y][x] = BOIS_HI + (255,)
    return g


# ---------------------------------------------------------------- décor animé
def t_touffe(f):
    g = neuf()
    s = SWAY[f]
    brins = [(3, 6), (5, 9), (8, 11), (11, 8), (13, 12), (16, 9), (18, 7), (20, 5)]
    for i, (x, h) in enumerate(brins):
        for k in range(h):
            y = 23 - k
            dx = (s if k > h // 2 else 0) + (1 if i % 3 == 0 and k == h - 1 else 0)
            c = HER_HI if k >= h - 2 else (HER_MID if i % 2 else HER_LOW)
            pose(g, x + dx, y, c)
            if k < 3:
                pose(g, x + dx + 1, y, HER_LOW if i % 2 else HER_MID)
    for x in (4, 9, 14, 19):
        pose(g, x, 23, HER_DARK)
    return g


def t_lierre(f):
    g = neuf()
    s = SWAY[f]
    xs = []
    for y in range(T):
        x = 12 + (1 if (y // 5) % 2 else 0) + (s if y > 10 else 0)
        xs.append(x)
        pose(g, x, y, HER_DARK)
    for j, y in enumerate((3, 8, 13, 18, 22)):
        x = xs[y]
        d = 1 if j % 2 else -1
        for dx in (d, 2 * d):
            pose(g, x + dx, y, HER_MID)
            pose(g, x + dx, y + 1, HER_LOW)
        pose(g, x + d, y - 1, HER_HI)
    return g


def t_brume(f):
    g = neuf()
    dx = f * 6
    for y in range(T):                                    # voile continu
        for x in range(T):
            if 9 <= y <= 15:
                g[y][x] = BRUME + (70,)
    for cx in (2, 14):                                    # nappes denses
        c = (cx + dx) % T
        for ox in (-T, 0, T):
            for y in range(6, 19):
                for x in range(T):
                    ddx = (x - (c + ox)) / 9.5
                    ddy = (y - 12) / 6.0
                    d = ddx * ddx + ddy * ddy
                    if d < 1.0:
                        a = int(165 * (1 - d) ** 1.3)
                        if a > g[y][x][3]:
                            g[y][x] = BRUME + (a,)
    return g


def t_fleurs(f):
    g = neuf()
    for (x, h, c) in [(6, 7, FLEURS[0]), (12, 9, FLEURS[1]), (18, 6, FLEURS[2])]:
        for k in range(h):
            pose(g, x, 23 - k, HER_DARK if k % 2 else HER_LOW)
        pose(g, x - 1, 23 - h + 2, HER_MID)
        pose(g, x + 1, 23 - h + 3, HER_MID)
        ty = 23 - h
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            pose(g, x + dx, ty + dy, c)
        pose(g, x, ty, (255, 240, 180))
    return g


def t_eboulis(f):
    g = neuf()
    for (cx, cy, r) in [(5, 18, 4), (13, 16, 5), (20, 20, 3)]:
        for y in range(cy - r, 24):
            t = (y - (cy - r)) / (r * 2)
            w = max(1, int(r * (0.55 + 0.65 * t)))
            for x in range(cx - w, cx + w + 1):
                if y == cy - r:
                    c = ROC_HI
                elif y == cy - r + 1:
                    c = ROC_CLAIR
                elif x >= cx + w - 1:
                    c = ROC_LOW
                elif y > cy + r // 2:
                    c = ROC_DARK
                else:
                    c = ROC_MID
                pose(g, x, y, c)
        pose(g, cx - w - 1, cy + 1, ROC_LINE)
        pose(g, cx + w + 1, cy + 1, ROC_LINE)
    return g


# ---------------------------------------------------------------- planche
TUILES = [
    ('face_roche',          'Paroi de falaise, raccords 4 côtés', False, t_face),
    ('face_roche_fissure',  'Paroi fissurée (variant)', False, lambda f: t_face(f, fissure=True)),
    ('face_roche_mousse',   'Paroi moussue (variant)', False, lambda f: t_face(f, mousse=True)),
    ('sommet_herbe',        'Sommet marchable, frange herbeuse', True, t_sommet),
    ('plateau_herbe',       'Plateau herbeux (remplissage)', True, t_plateau),
    ('sommet_roche_nu',     'Sommet rocheux nu', False, t_sommet_nu),
    ('coin_haut_gauche',    'Coin haut gauche', True, lambda f: t_coin(f, False)),
    ('coin_haut_droit',     'Coin haut droit', True, lambda f: t_coin(f, True)),
    ('bord_gauche',         'Flanc gauche de falaise', False, lambda f: t_bord(f, False)),
    ('bord_droit',          'Flanc droit de falaise', False, lambda f: t_bord(f, True)),
    ('pente_droite',        'Pente herbeuse montante à droite', True, lambda f: t_pente(f, True)),
    ('pente_gauche',        'Pente herbeuse montante à gauche', True, lambda f: t_pente(f, False)),
    ('escalier_droit',      'Escalier taillé, montant à droite', True, lambda f: t_escalier(f, True)),
    ('escalier_gauche',     'Escalier taillé, montant à gauche', True, lambda f: t_escalier(f, False)),
    ('pont_corde',          'Tablier de pont de corde', True, t_pont_corde),
    ('pilier_corde',        'Pilier de pont de corde', True, t_pilier_corde),
    ('pont_bois',           'Passerelle de bois', False, t_pont_bois),
    ('pilier_bois',         'Pilier de passerelle', False, t_pilier_bois),
    ('echelle',             'Échelle de paroi', False, t_echelle),
    ('touffe_herbe',        'Touffe d’herbe (décor animé)', True, t_touffe),
    ('lierre',              'Lierre suspendu (décor animé)', True, t_lierre),
    ('brume',               'Nappe de brume (décor animé)', True, t_brume),
    ('fleurs',              'Fleurs des sommets (décor)', False, t_fleurs),
    ('eboulis',             'Éboulis au pied de falaise', False, t_eboulis),
]
assert len(TUILES) == COLS * ROWS


def planche(f):
    im = Image.new('RGBA', (COLS * T, ROWS * T), (0, 0, 0, 0))
    px = im.load()
    for i, (_n, _d, _a, fn) in enumerate(TUILES):
        g = fn(f)
        ox, oy = (i % COLS) * T, (i // COLS) * T
        for y in range(T):
            for x in range(T):
                c = g[y][x]
                px[ox + x, oy + y] = c if len(c) == 4 else c + (255,)
    return im


# ---------------------------------------------------------------- scène exemple
SC = 20, 10
SCENE = [
    # falaise gauche (sommet rang 2)
    (0, 2, 'sommet_herbe'), (1, 2, 'sommet_herbe'), (2, 2, 'sommet_herbe'),
    (3, 2, 'sommet_herbe'), (4, 2, 'coin_haut_droit'),
    # pont de corde ancré aux bordures
    (5, 2, 'pilier_corde'), (6, 2, 'pont_corde'), (7, 2, 'pont_corde'), (8, 2, 'pilier_corde'),
    # falaise centrale : jonction d'escalier en pleine surface
    (9, 2, 'coin_haut_gauche'), (10, 2, 'sommet_herbe'), (11, 2, 'sommet_herbe'),
    (12, 2, 'sommet_herbe'), (13, 2, 'escalier_droit'),
    # falaise droite d'un rang plus bas, coupée par la passerelle de bois
    (14, 3, 'sommet_herbe'), (15, 3, 'sommet_herbe'), (16, 3, 'pilier_bois'),
    (17, 3, 'pont_bois'), (18, 3, 'pilier_bois'), (19, 3, 'coin_haut_droit'),
    # décors de sommet
    (1, 1, 'touffe_herbe'), (10, 1, 'touffe_herbe'), (15, 2, 'touffe_herbe'),
    (11, 1, 'fleurs'), (19, 2, 'fleurs'),
    # décors de paroi et de fond
    (12, 4, 'lierre'), (12, 5, 'lierre'), (4, 5, 'lierre'), (4, 6, 'lierre'),
    (15, 5, 'echelle'), (15, 6, 'echelle'), (15, 7, 'echelle'),
    (5, 6, 'brume'), (6, 6, 'brume'), (7, 6, 'brume'), (8, 6, 'brume'),
    (16, 7, 'brume'), (17, 7, 'brume'),
    (1, 9, 'eboulis'), (10, 9, 'eboulis'), (18, 9, 'eboulis'),
    (5, 9, 'plateau_herbe'), (6, 9, 'plateau_herbe'), (7, 9, 'plateau_herbe'),
    (6, 8, 'eboulis'), (8, 8, 'pente_droite'),
]
for r in range(3, SC[1]):
    SCENE += [(0, r, 'bord_gauche')] + [(c, r, 'face_roche' if (c + r) % 5 else 'face_roche_fissure') for c in (1, 2, 3)] + [(4, r, 'bord_droit')]
    SCENE += [(9, r, 'bord_gauche')] + [(c, r, 'face_roche' if (c + r) % 7 else 'face_roche_mousse') for c in (10, 11)] + [(12, r, 'bord_droit')]
    SCENE += [(13, r, 'bord_gauche')]
for r in range(4, SC[1]):
    SCENE += [(c, r, 'face_roche' if (c + r) % 6 else 'face_roche_fissure') for c in (14, 15)]
    SCENE += [(16, r, 'bord_droit'), (18, r, 'bord_gauche'), (19, r, 'bord_droit')]


def scene(f):
    im = Image.new('RGBA', (SC[0] * T, SC[1] * T), (0, 0, 0, 0))
    idx = {n: i for i, (n, _d, _a, _fn) in enumerate(TUILES)}
    sh = planche(f)
    for (c, r, nom) in SCENE:
        i = idx[nom]
        im.alpha_composite(sh.crop(((i % COLS) * T, (i // COLS) * T,
                                    (i % COLS) * T + T, (i // COLS) * T + T)), (c * T, r * T))
    return im


# ---------------------------------------------------------------- zones map
# Classes de calques : ground (terrain praticable), falaise (roche structurelle),
# décor (animation/ornement). Chaque zone est un plan de tuiles canoniques :
# rendu pixel perfect par copie exacte des cellules de la planche.
CLASSES = {}
for _n, _d, _a, _f in TUILES:
    CLASSES[_n] = ('ground' if _n in ('sommet_herbe', 'plateau_herbe', 'sommet_roche_nu',
                                      'pente_droite', 'pente_gauche', 'escalier_droit',
                                      'escalier_gauche', 'pont_corde', 'pilier_corde',
                                      'pont_bois', 'pilier_bois')
                   else 'falaise' if _n in ('face_roche', 'face_roche_fissure',
                                            'face_roche_mousse', 'coin_haut_gauche',
                                            'coin_haut_droit', 'bord_gauche', 'bord_droit')
                   else 'decor')
COUCHES = ['ground', 'falaise', 'decor']
ROCSOLIDE = {'face_roche', 'face_roche_fissure', 'face_roche_mousse', 'bord_gauche',
             'bord_droit', 'sommet_herbe', 'plateau_herbe', 'sommet_roche_nu',
             'coin_haut_gauche', 'coin_haut_droit', 'pente_droite', 'pente_gauche',
             'escalier_droit', 'escalier_gauche'}


def compact(poses):
    """Un flanc voisin d'une roche devient paroi : les massifs accolés se
    fondent sans fente blanche ; les silhouettes ne restent qu'au contact
    de l'air. La déduplication se fait par calque : un décor se superpose
    à la roche de sa cellule au lieu de la remplacer."""
    d = {}
    for (c, r, n) in poses:
        d[(c, r, CLASSES[n])] = n
    roche = {(c, r): n for (c, r, cl), n in d.items() if cl in ('ground', 'falaise')}
    out = []
    for (c, r, cl), n in d.items():
        if cl == 'falaise':
            if n == 'bord_gauche' and roche.get((c - 1, r)) in ROCSOLIDE:
                n = 'face_roche'
            elif n == 'bord_droit' and roche.get((c + 1, r)) in ROCSOLIDE:
                n = 'face_roche'
        out.append((c, r, n))
    return out


def _massif(pos, c0, c1, r0, r1, var=6):
    """Corps de falaise : flancs + parois, avec variants rares."""
    out = []
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if c == c0:
                out.append((c, r, 'bord_gauche'))
            elif c == c1:
                out.append((c, r, 'bord_droit'))
            else:
                out.append((c, r, 'face_roche' if (c + r) % var else 'face_roche_fissure'))
    return out


ZONE_A = [  # col de montagne : deux pics, selle centrale, escaliers taillés
    (0, 1, 'sommet_herbe'), (1, 1, 'sommet_herbe'), (2, 1, 'sommet_herbe'), (3, 1, 'sommet_herbe'),
    (4, 1, 'escalier_gauche'),
    (5, 2, 'sommet_herbe'), (6, 2, 'sommet_herbe'), (7, 2, 'sommet_herbe'),
    (8, 2, 'sommet_herbe'), (9, 2, 'sommet_herbe'), (10, 2, 'sommet_herbe'),
    (11, 1, 'escalier_droit'),
    (12, 1, 'sommet_herbe'), (13, 1, 'sommet_herbe'), (14, 1, 'sommet_herbe'), (15, 1, 'coin_haut_droit'),
    (1, 0, 'touffe_herbe'), (7, 1, 'touffe_herbe'), (13, 0, 'fleurs'),
    (3, 4, 'lierre'), (3, 5, 'lierre'), (13, 4, 'echelle'), (13, 5, 'echelle'), (13, 6, 'echelle'),
    (5, 6, 'brume'), (6, 6, 'brume'), (7, 6, 'brume'), (8, 6, 'brume'), (9, 6, 'brume'), (10, 6, 'brume'),
    (2, 9, 'eboulis'), (8, 9, 'eboulis'), (14, 9, 'eboulis'),
]
ZONE_A = compact(ZONE_A + (_massif(None, 0, 4, 2, 9, 5) + _massif(None, 5, 10, 3, 9, 7) + _massif(None, 11, 15, 2, 9, 6)))

ZONE_B = compact(SCENE)          # plateaux reliés : pont de corde, escalier, passerelle

ZONE_C = [  # gouffre : passerelle de bois ancrée aux bordures, échelle, brume
    (0, 3, 'sommet_herbe'), (1, 3, 'sommet_herbe'), (2, 3, 'sommet_herbe'), (3, 3, 'sommet_herbe'),
    (4, 3, 'pilier_bois'), (5, 3, 'pont_bois'), (6, 3, 'pont_bois'), (7, 3, 'pont_bois'),
    (8, 3, 'pont_bois'), (9, 3, 'pont_bois'), (10, 3, 'pilier_bois'),
    (11, 3, 'sommet_herbe'), (12, 3, 'sommet_herbe'), (13, 3, 'sommet_herbe'),
    (14, 3, 'sommet_herbe'), (15, 3, 'coin_haut_droit'),
    (1, 2, 'touffe_herbe'), (12, 2, 'touffe_herbe'), (14, 2, 'fleurs'),
    (2, 5, 'echelle'), (2, 6, 'echelle'), (2, 7, 'echelle'),
    (10, 4, 'lierre'), (10, 5, 'lierre'),
    (5, 7, 'brume'), (6, 7, 'brume'), (7, 7, 'brume'), (8, 7, 'brume'), (9, 7, 'brume'),
    (5, 8, 'brume'), (6, 8, 'brume'), (7, 8, 'brume'), (8, 8, 'brume'), (9, 8, 'brume'),
    (6, 9, 'eboulis'), (8, 9, 'eboulis'),
]
ZONE_C = compact(ZONE_C + _massif(None, 0, 4, 4, 9, 6) + _massif(None, 10, 15, 4, 9, 7))

ZONE_D = [  # corniche en zigzag : trois vires reliées par escaliers taillés
    (0, 2, 'sommet_herbe'), (1, 2, 'sommet_herbe'), (2, 2, 'sommet_herbe'), (3, 2, 'sommet_herbe'),
    (4, 2, 'sommet_herbe'), (5, 2, 'escalier_gauche'),
    (6, 3, 'sommet_herbe'), (7, 3, 'sommet_herbe'), (8, 3, 'sommet_herbe'), (9, 3, 'sommet_herbe'),
    (10, 3, 'escalier_gauche'),
    (11, 4, 'sommet_herbe'), (12, 4, 'sommet_herbe'), (13, 4, 'sommet_herbe'),
    (14, 4, 'sommet_herbe'), (15, 4, 'coin_haut_droit'), (10, 4, 'face_roche'),
    (2, 1, 'touffe_herbe'), (7, 2, 'touffe_herbe'), (13, 3, 'touffe_herbe'), (12, 3, 'fleurs'),
    (9, 5, 'lierre'), (9, 6, 'lierre'),
    (2, 5, 'echelle'), (2, 6, 'echelle'), (2, 7, 'echelle'),
    (6, 7, 'brume'), (7, 7, 'brume'), (8, 7, 'brume'), (9, 7, 'brume'), (10, 7, 'brume'),
    (11, 7, 'brume'), (12, 7, 'brume'),
    (5, 9, 'eboulis'), (13, 9, 'eboulis'),
]
ZONE_D = compact(ZONE_D + (_massif(None, 0, 5, 3, 9, 5) + _massif(None, 6, 9, 4, 9, 7) + _massif(None, 10, 15, 5, 9, 6)))

ZONE_E = [  # worldmap : tous les types de tuiles, cinq niveaux
    (0, 1, 'sommet_roche_nu'), (1, 1, 'sommet_roche_nu'), (2, 1, 'sommet_roche_nu'),
    (3, 1, 'sommet_roche_nu'), (4, 1, 'escalier_gauche'),
    (5, 2, 'sommet_herbe'), (6, 2, 'sommet_herbe'), (7, 2, 'sommet_herbe'), (8, 2, 'sommet_herbe'),
    (9, 2, 'sommet_herbe'), (10, 2, 'pilier_corde'), (11, 2, 'pont_corde'), (12, 2, 'pont_corde'),
    (13, 2, 'pont_corde'), (14, 2, 'pont_corde'), (15, 2, 'pilier_corde'),
    (16, 2, 'sommet_herbe'), (17, 2, 'sommet_herbe'), (18, 2, 'sommet_herbe'), (19, 2, 'sommet_herbe'),
    (20, 2, 'sommet_herbe'), (21, 2, 'escalier_gauche'), (21, 3, 'face_roche'),
    (22, 3, 'sommet_herbe'), (23, 3, 'sommet_herbe'), (24, 3, 'sommet_herbe'), (25, 3, 'pilier_bois'),
    (26, 3, 'pont_bois'), (27, 3, 'pont_bois'), (28, 3, 'pont_bois'), (29, 3, 'pilier_bois'),
    (30, 3, 'coin_haut_gauche'), (31, 3, 'sommet_herbe'),
    (0, 7, 'sommet_herbe'), (1, 7, 'sommet_herbe'), (2, 7, 'sommet_herbe'), (3, 7, 'sommet_herbe'),
    (4, 7, 'sommet_herbe'), (5, 7, 'sommet_herbe'), (6, 7, 'sommet_herbe'), (7, 7, 'sommet_herbe'),
    (8, 7, 'sommet_herbe'), (9, 7, 'pente_gauche'),
    (10, 8, 'plateau_herbe'), (11, 8, 'plateau_herbe'), (12, 8, 'plateau_herbe'), (13, 8, 'plateau_herbe'),
    (14, 7, 'pente_droite'),
    (1, 0, 'touffe_herbe'), (6, 1, 'touffe_herbe'), (17, 1, 'touffe_herbe'), (23, 2, 'touffe_herbe'),
    (31, 2, 'touffe_herbe'), (5, 6, 'touffe_herbe'),
    (8, 1, 'fleurs'), (19, 1, 'fleurs'), (24, 2, 'fleurs'), (2, 6, 'fleurs'),
    (8, 9, 'lierre'), (8, 10, 'lierre'), (20, 6, 'lierre'), (20, 7, 'lierre'),
    (17, 10, 'echelle'), (17, 11, 'echelle'), (17, 12, 'echelle'), (17, 13, 'echelle'),
    (5, 12, 'brume'), (6, 12, 'brume'), (7, 12, 'brume'),
    (26, 9, 'brume'), (27, 9, 'brume'), (28, 9, 'brume'),
    (27, 12, 'brume'), (28, 12, 'brume'),
    (3, 17, 'eboulis'), (11, 17, 'eboulis'), (18, 17, 'eboulis'), (30, 17, 'eboulis'),
    (27, 17, 'eboulis'), (28, 17, 'eboulis'),
    (6, 11, 'face_roche_mousse'), (18, 6, 'face_roche_mousse'),
]
ZONE_E = compact(ZONE_E + (_massif(None, 0, 4, 2, 4, 5) + _massif(None, 5, 10, 3, 6, 7) +
           _massif(None, 15, 20, 3, 17, 6) + _massif(None, 21, 25, 4, 17, 7) +
           _massif(None, 29, 31, 4, 17, 5) +
           [(0, r, 'bord_gauche') for r in range(5, 18)] +
           [(c, r, 'face_roche' if (c + r) % 6 else 'face_roche_fissure') for r in range(5, 18) for c in (1, 2, 3)] +
           [(4, r, 'bord_droit') for r in range(5, 18)] +
           [(c, r, 'face_roche' if (c + r) % 7 else 'face_roche_mousse') for r in range(8, 18) for c in (5, 6, 7)] +
           [(8, r, 'bord_droit') for r in range(8, 18)] +
           [(9, r, 'bord_gauche') for r in range(8, 18)] +
           [(c, r, 'face_roche' if (c + r) % 5 else 'face_roche_fissure') for r in range(9, 18) for c in (10, 11, 12)] +
           [(13, r, 'bord_droit') for r in range(9, 18)] +
           [(14, r, 'face_roche') for r in range(8, 18)]))


ZONES = [
    {'nom': 'col_montagne', 'w': 16, 'h': 10, 'poses': ZONE_A,
     'desc': 'Col : deux pics reliés par une selle, escaliers taillés dans la roche.'},
    {'nom': 'plateaux_ponts', 'w': 20, 'h': 10, 'poses': ZONE_B,
     'desc': 'Plateaux reliés : pont de corde, escalier d’un rang, passerelle de bois.'},
    {'nom': 'gouffre_passerelle', 'w': 16, 'h': 10, 'poses': ZONE_C,
     'desc': 'Gouffre franchi par une passerelle de bois, échelle et brume au fond.'},
    {'nom': 'corniche_escalier', 'w': 16, 'h': 10, 'poses': ZONE_D,
     'desc': 'Corniche en zigzag : trois vires reliées par escaliers taillés.'},
    {'nom': 'worldmap', 'w': 32, 'h': 18, 'poses': ZONE_E,
     'desc': 'Grande zone démonstrative : toutes les tuiles du tileset, cinq niveaux.'},
]


def rend_zone(zone, planches):
    """Rendu pixel perfect : chaque cellule est une copie exacte de la tuile
    canonique de la planche. Retourne {couche: [frames]} + composite [frames]."""
    idx = {n: i for i, (n, _d, _a, _fn) in enumerate(TUILES)}
    w, h = zone['w'] * T, zone['h'] * T
    couches = {c: [Image.new('RGBA', (w, h), (0, 0, 0, 0)) for _ in range(FRAMES)] for c in COUCHES}
    for (c, r, nom) in sorted(zone['poses'], key=lambda q: COUCHES.index(CLASSES[q[2]])):
        i = idx[nom]
        cl = CLASSES[nom]
        for f in range(FRAMES):
            tile = planches[f].crop(((i % COLS) * T, (i // COLS) * T,
                                     (i % COLS) * T + T, (i // COLS) * T + T))
            couches[cl][f].alpha_composite(tile, (c * T, r * T))
    comp = []
    for f in range(FRAMES):
        im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        for c in COUCHES:
            im.alpha_composite(couches[c][f])
        comp.append(im)
    return couches, comp


# ---------------------------------------------------------------- Aseprite
def astr(s):
    b = s.encode()
    return struct.pack('<H', len(b)) + b


def chunk(k, d):
    return struct.pack('<IH', len(d) + 6, k) + d


def aseprite(path, frames_im, duree, grille):
    w, h = frames_im[0].size
    entetes = [chunk(0x2004, struct.pack('<HHHHHHB', 3, 0, 0, 0, 0, 0, 255) + b'\0' * 3 + astr('tileset'))]
    data = b''
    for fi, im in enumerate(frames_im):
        cels = [chunk(0x2005, struct.pack('<HhhBHh', 0, 0, 0, 255, 2, 0) + b'\0' * 5 +
                      struct.pack('<HH', im.width, im.height) + zlib.compress(im.tobytes(), 9))]
        morceaux = (entetes if fi == 0 else []) + cels
        blob = b''.join(morceaux)
        data += struct.pack('<IHHH2sI', len(blob) + 16, 0xF1FA, len(morceaux), duree, b'\0\0', len(morceaux)) + blob
    header = bytearray(128)
    struct.pack_into('<IHHHHHIH', header, 0, len(data) + 128, 0xA5E0, len(frames_im), w, h, 32, 1, duree)
    struct.pack_into('<HBBhhHH', header, 32, 0, 1, 1, 0, 0, grille, grille)
    path.write_bytes(header + data)


def apng(path, frames_im, duree):
    frames_im[0].save(path, save_all=True, append_images=frames_im[1:],
                      duration=duree, loop=0, disposal=1)


# ---------------------------------------------------------------- aperçu HTML
def apercu(html_path, par_amb, zones_data):
    assets = {}
    for amb, d in par_amb.items():
        assets[amb] = ['data:image/png;base64,' + base64.b64encode(b).decode()
                       for b in d['frames_png']]
    data = json.dumps({'ambiances': AMBIANCES, 'assets': assets, 'zones': zones_data,
                       'tiles': [{'id': i, 'nom': n, 'desc': d, 'anime': a, 'classe': CLASSES[n]}
                                 for i, (n, d, a, _f) in enumerate(TUILES)],
                       'frames': FRAMES, 'duree': DUREE, 'taille': T,
                       'cols': COLS, 'rows': ROWS}, ensure_ascii=False)
    html = '''<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Falaises Métano / Treasure Town — tileset animé & zones map</title>
<style>
:root{--bg:#1d2a26;--pan:#24352f;--tx:#e8f2e4;--ac:#8fd6a8;--mu:#9db4a6}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tx);font:14px/1.45 system-ui,sans-serif}
header{padding:14px 18px;background:var(--pan);border-bottom:2px solid #0e1613}
h1{margin:0;font-size:17px}p.s{margin:4px 0 0;color:var(--mu);font-size:12px}
main{padding:16px 18px;max-width:1180px;margin:0 auto}
.bar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:0 0 12px}
button{background:#2e463c;color:var(--tx);border:1px solid #0e1613;border-radius:8px;padding:6px 10px;cursor:pointer;font:inherit}
button[aria-pressed=true]{background:var(--ac);color:#122019}
.box{background:var(--pan);border:1px solid #0e1613;border-radius:12px;padding:12px;margin:0 0 16px}
canvas{image-rendering:pixelated;background:
 repeating-conic-gradient(#2b3b34 0% 25%,#22312b 0% 50%) 0 0/16px 16px;border-radius:6px;max-width:100%}
.lab{color:var(--mu);font-size:12px;margin:6px 0 0}
.grille{display:grid;grid-template-columns:repeat(8,1fr);gap:6px;margin-top:10px}
.tu{background:#20302a;border:1px solid #0e1613;border-radius:8px;padding:6px;text-align:center}
.tu canvas{background:repeating-conic-gradient(#2b3b34 0% 25%,#22312b 0% 50%) 0 0/12px 12px}
.tu b{display:block;font-size:11px;margin-top:4px}.tu span{display:block;color:var(--mu);font-size:10px}
.anim{color:var(--ac);font-size:10px;font-style:normal}
.cl{color:#e8d29a;font-size:10px}
</style></head><body>
<header><h1>Falaises de Métano / Treasure Town — tileset animé &amp; zones map</h1>
<p class="s">24 tuiles de 24 × 24 px · 4 frames de 150 ms · feuille Aseprite multi-frames · 6 ambiances · 5 zones map rendues pixel perfect en calques ground / falaise / décor</p></header>
<main>
<div class="bar" id="amb"></div>
<div class="bar"><button id="play" aria-pressed="true">⏸ Pause</button>
<button id="prec">◀ Frame</button><button id="suiv">Frame ▶</button>
<span class="lab" id="etat"></span></div>
<div class="box"><canvas id="sheet" width="192" height="72" style="width:768px;height:288px"></canvas>
<p class="lab">Planche tilesheet (8 × 3 tuiles) — chaque frame est une planche complète, comme dans la feuille Aseprite.</p></div>
<div class="box"><h2 style="margin:0 0 8px;font-size:14px">Zones map falaise (rendu pixel perfect, tuiles canoniques)</h2>
<div class="bar" id="zon"></div>
<div class="bar" id="cou"></div>
<canvas id="zc" width="480" height="240" style="width:960px;max-width:100%"></canvas>
<p class="lab" id="zdesc"></p></div>
<div class="box"><h2 style="margin:0 0 4px;font-size:14px">Tuiles</h2><div class="grille" id="gr"></div></div>
</main><script>
const D=__DATA__;
let amb=D.ambiances[0], f=0, joue=true, zone=D.zones[0].nom, cou='composite';
const imgs={};
function get(a,i){const k=a+'#'+i;if(!imgs[k]){imgs[k]=new Image();imgs[k].src=D.assets[a][i];}return imgs[k]}
function zget(z,a,i){const k=z+a+i;if(!imgs[k]){imgs[k]=new Image();imgs[k].src=D.zones.find(q=>q.nom===z).frames[a][i];}return imgs[k]}
function lget(z,c){const k=z+'L'+c;if(!imgs[k]){imgs[k]=new Image();imgs[k].src=D.zones.find(q=>q.nom===z).layers[c];}return imgs[k]}
const bar=document.getElementById('amb');
D.ambiances.forEach(a=>{const b=document.createElement('button');b.textContent=a;b.dataset.a=a;
 b.onclick=()=>{amb=a;maj();};bar.appendChild(b);});
const zb=document.getElementById('zon');
D.zones.forEach(z=>{const b=document.createElement('button');b.textContent=z.nom;b.dataset.z=z.nom;
 b.onclick=()=>{zone=z.nom;maj();};zb.appendChild(b);});
const cb=document.getElementById('cou');
['composite','ground','falaise','decor'].forEach(c=>{const b=document.createElement('button');
 b.textContent=c;b.dataset.c=c;b.onclick=()=>{cou=c;maj();};cb.appendChild(b);});
const gr=document.getElementById('gr');
D.tiles.forEach((tl,i)=>{const d=document.createElement('div');d.className='tu';
 const c=document.createElement('canvas');c.width=24;c.height=24;c.style.width='72px';c.style.height='72px';
 d.appendChild(c);d.innerHTML+='<b>'+tl.nom+'</b><span class="cl">'+tl.classe+'</span><span>'+(tl.anime?'<em class="anim">animé · </em>':'')+tl.desc+'</span>';
 gr.appendChild(d);tl._c=c;});
function maj(){[...bar.children].forEach(b=>b.setAttribute('aria-pressed',b.dataset.a===amb));
 [...zb.children].forEach(b=>b.setAttribute('aria-pressed',b.dataset.z===zone));
 [...cb.children].forEach(b=>b.setAttribute('aria-pressed',b.dataset.c===cou));
 const z=D.zones.find(q=>q.nom===zone);
 document.getElementById('etat').textContent='ambiance '+amb+' — frame '+(f+1)+'/'+D.frames+' ('+D.duree+' ms)';
 const cs=document.getElementById('sheet').getContext('2d');cs.clearRect(0,0,192,72);cs.drawImage(get(amb,f),0,0);
 const cv=document.getElementById('zc');cv.width=z.w*24;cv.height=z.h*24;
 cv.style.width=(z.w*24*2)+'px';cv.style.height=(z.h*24*2)+'px';
 const cx=cv.getContext('2d');cx.clearRect(0,0,cv.width,cv.height);
 if(cou==='composite')cx.drawImage(zget(zone,amb,f),0,0);
 else cx.drawImage(lget(zone,cou),0,0);
 document.getElementById('zdesc').textContent=z.desc+' — calque affiché : '+cou+
  (cou==='composite'?' (ground + falaise + décor, animé)':' (statique, isolé)');
 D.tiles.forEach((tl,i)=>{const ctx=tl._c.getContext('2d');ctx.clearRect(0,0,24,24);
  ctx.drawImage(get(amb,f),(i%8)*24,Math.floor(i/8)*24,24,24,0,0,24,24);});}
setInterval(()=>{if(joue){f=(f+1)%D.frames;maj();}},D.duree);
document.getElementById('play').onclick=e=>{joue=!joue;e.currentTarget.setAttribute('aria-pressed',joue);
 e.currentTarget.textContent=joue?'⏸ Pause':'▶ Lecture';};
document.getElementById('prec').onclick=()=>{f=(f+D.frames-1)%D.frames;maj();};
document.getElementById('suiv').onclick=()=>{f=(f+1)%D.frames;maj();};
let prets=0;const tot=D.ambiances.length*D.frames+D.zones.length*(D.ambiances.length*D.frames+3);
function ok(){prets++;if(prets>=tot)maj();}
D.ambiances.forEach(a=>{for(let i=0;i<D.frames;i++)get(a,i).onload=ok;});
D.zones.forEach(z=>{D.ambiances.forEach(a=>{for(let i=0;i<D.frames;i++)zget(z.nom,a,i).onload=ok;});
 ['ground','falaise','decor'].forEach(c=>lget(z.nom,c).onload=ok);});
maj();
</script></body></html>'''
    html_path.write_text(html.replace('__DATA__', data), encoding='utf-8')


# ---------------------------------------------------------------- génération
def main():
    par_amb = {}
    zones_data = []
    manifeste = {'titre': 'Falaises de Métano / Treasure Town — tileset animé',
                 'grille_tuile': T, 'grille_kit': 8, 'frames': FRAMES, 'duree_ms': DUREE,
                 'ambiances': AMBIANCES, 'planche': [COLS, ROWS],
                 'tuiles': [{'id': i, 'nom': n, 'usage': d, 'anime': a, 'classe': CLASSES[n],
                             'colonne': i % COLS, 'ligne': i // COLS}
                            for i, (n, d, a, _f) in enumerate(TUILES)],
                 'zones': [], 'fichiers': {}}
    brutes = [planche(f) for f in range(FRAMES)]
    for amb in AMBIANCES:
        d = OUT / amb
        d.mkdir(exist_ok=True)
        frames = [teinte(im.copy(), amb) for im in brutes] if amb != 'jour' else [im.copy() for im in brutes]
        for i, im in enumerate(frames):
            im.save(d / f'planche_f{i + 1}.png', optimize=True)
        aseprite(d / f'tileset_falaises_{amb}.aseprite', frames, DUREE, T)
        apng(d / 'animation.png', frames, DUREE)
        fps = []
        for im in frames:
            b = io.BytesIO()
            im.save(b, format='PNG', optimize=True)
            fps.append(b.getvalue())
        par_amb[amb] = {'frames_png': fps}
        manifeste['fichiers'][amb] = {
            'aseprite': f'falaises/{amb}/tileset_falaises_{amb}.aseprite',
            'planches': [f'falaises/{amb}/planche_f{i + 1}.png' for i in range(FRAMES)],
            'apng': f'falaises/{amb}/animation.png'}
    # ---- zones map : rendu pixel perfect depuis les tuiles canoniques
    zdir = OUT / 'zones'
    zdir.mkdir(exist_ok=True)
    for zone in ZONES:
        couches, comp = rend_zone(zone, brutes)
        zd = zdir / zone['nom']
        zd.mkdir(exist_ok=True)
        zrec = {'nom': zone['nom'], 'desc': zone['desc'], 'cellules': [zone['w'], zone['h']],
                'dimensions_px': [zone['w'] * T, zone['h'] * T], 'poses': len(zone['poses']),
                'fichiers': {'calques': {}, 'composites': {}}}
        zdata = {'nom': zone['nom'], 'w': zone['w'], 'h': zone['h'], 'desc': zone['desc'],
                 'frames': {}, 'layers': {}}
        for c in COUCHES:
            b = io.BytesIO()
            couches[c][0].save(b, format='PNG', optimize=True)
            zdata['layers'][c] = 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()
            couches[c][0].save(zd / f'{c}_jour.png', optimize=True)
            n = teinte(couches[c][0].copy(), 'nuit')
            n.save(zd / f'{c}_nuit.png', optimize=True)
            zrec['fichiers']['calques'][c] = {'jour': f'falaises/zones/{zone["nom"]}/{c}_jour.png',
                                              'nuit': f'falaises/zones/{zone["nom"]}/{c}_nuit.png'}
        for amb in AMBIANCES:
            fr = comp if amb == 'jour' else [teinte(im.copy(), amb) for im in comp]
            bufs = []
            for im in fr:
                b = io.BytesIO()
                im.save(b, format='PNG', optimize=True)
                bufs.append(b.getvalue())
            fr[0].save(zd / f'zone_{amb}.png', optimize=True)
            zrec['fichiers']['composites'][amb] = f'falaises/zones/{zone["nom"]}/zone_{amb}.png'
            zdata['frames'][amb] = ['data:image/png;base64,' + base64.b64encode(b).decode() for b in bufs]
        apng(zd / 'zone_jour_anim.png', comp, DUREE)
        zrec['fichiers']['apng'] = f'falaises/zones/{zone["nom"]}/zone_jour_anim.png'
        zrec['tuiles_utilisees'] = sorted({n for (_c, _r, n) in zone['poses']})
        manifeste['zones'].append(zrec)
        zones_data.append(zdata)
    (OUT / 'falaises.json').write_text(json.dumps(manifeste, ensure_ascii=False, indent=2), encoding='utf-8')
    apercu(R / 'apercu_falaises.html', par_amb, zones_data)
    kit = json.loads((R / 'kit.json').read_text())
    kit['falaises'] = {'manifeste': 'falaises/falaises.json', 'apercu': 'apercu_falaises.html',
                       'tuiles': len(TUILES), 'frames': FRAMES, 'duree_ms': DUREE,
                       'ambiances': AMBIANCES, 'zones': [z['nom'] for z in ZONES]}
    (R / 'kit.json').write_text(json.dumps(kit, ensure_ascii=False, indent=2), encoding='utf-8')
    print('OK falaises :', len(TUILES), 'tuiles ×', FRAMES, 'frames ×', len(AMBIANCES),
          'ambiances +', len(ZONES), 'zones map pixel perfect')


if __name__ == '__main__':
    main()
