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
    for y in range(2, 18):
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
    for y in range(1, 20):
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
    # pont de corde vers la falaise centrale
    (5, 2, 'pilier_corde'), (6, 2, 'pont_corde'), (7, 2, 'pont_corde'), (8, 2, 'pilier_corde'),
    # falaise centrale (sommet rang 2)
    (9, 2, 'coin_haut_gauche'), (10, 2, 'sommet_herbe'), (11, 2, 'sommet_herbe'),
    (12, 2, 'coin_haut_droit'),
    # escalier taillé : descente d'un rang vers la falaise droite
    (13, 2, 'escalier_droit'),
    # falaise droite (sommet rang 3) coupée par une passerelle de bois
    (13, 3, 'coin_haut_gauche'), (14, 3, 'sommet_herbe'), (15, 3, 'sommet_herbe'),
    (16, 3, 'pilier_bois'), (17, 3, 'pont_bois'), (18, 3, 'pilier_bois'),
    (19, 3, 'sommet_herbe'),
    # décors de sommet
    (1, 1, 'touffe_herbe'), (10, 1, 'touffe_herbe'), (14, 2, 'touffe_herbe'),
    (11, 1, 'fleurs'), (19, 2, 'fleurs'),
]
for r in range(3, SC[1]):
    for c in range(0, 4):
        SCENE.append((c, r, 'face_roche' if (c + r) % 5 else 'face_roche_fissure'))
    SCENE.append((4, r, 'bord_droit'))
    for c in range(10, 12):
        SCENE.append((c, r, 'face_roche' if (c + r) % 7 else 'face_roche_mousse'))
    SCENE.append((9, r, 'bord_gauche'))
    SCENE.append((12, r, 'bord_droit'))
for r in range(4, SC[1]):
    SCENE.append((13, r, 'face_roche' if r % 3 else 'face_roche_mousse'))
    for c in range(14, 16):
        SCENE.append((c, r, 'face_roche' if (c + r) % 6 else 'face_roche_fissure'))
    SCENE.append((16, r, 'bord_droit'))
    SCENE.append((18, r, 'bord_gauche'))
    SCENE.append((19, r, 'face_roche'))
SCENE += [(12, 4, 'lierre'), (12, 5, 'lierre'), (4, 5, 'lierre'), (4, 6, 'lierre'),
          (15, 5, 'echelle'), (15, 6, 'echelle'), (15, 7, 'echelle'),
          (5, 6, 'brume'), (6, 6, 'brume'), (7, 6, 'brume'), (8, 6, 'brume'),
          (16, 7, 'brume'), (17, 7, 'brume'),
          (1, 9, 'eboulis'), (10, 9, 'eboulis'), (18, 9, 'eboulis'),
          # talus au pied : sol de vallée puis pente remontant vers la paroi
          (5, 9, 'plateau_herbe'), (6, 9, 'plateau_herbe'), (7, 9, 'plateau_herbe'),
          (6, 8, 'eboulis'), (8, 8, 'pente_droite')]


def scene(f):
    im = Image.new('RGBA', (SC[0] * T, SC[1] * T), (0, 0, 0, 0))
    idx = {n: i for i, (n, _d, _a, _fn) in enumerate(TUILES)}
    sh = planche(f)
    for (c, r, nom) in SCENE:
        i = idx[nom]
        im.alpha_composite(sh.crop(((i % COLS) * T, (i // COLS) * T,
                                    (i % COLS) * T + T, (i // COLS) * T + T)), (c * T, r * T))
    return im


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
def apercu(html_path, par_amb):
    assets = {}
    for amb, d in par_amb.items():
        assets[amb] = ['data:image/png;base64,' + base64.b64encode(b).decode()
                       for b in d['frames_png']]
        assets[amb + '_scene'] = ['data:image/png;base64,' + base64.b64encode(b).decode()
                                  for b in d['scene_png']]
    data = json.dumps({'ambiances': AMBIANCES, 'assets': assets,
                       'tiles': [{'id': i, 'nom': n, 'desc': d, 'anime': a}
                                 for i, (n, d, a, _f) in enumerate(TUILES)],
                       'frames': FRAMES, 'duree': DUREE, 'taille': T,
                       'cols': COLS, 'rows': ROWS}, ensure_ascii=False)
    html = '''<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Falaises Métano / Treasure Town — tileset animé PMD</title>
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
</style></head><body>
<header><h1>Falaises de Métano / Treasure Town — tileset animé</h1>
<p class="s">24 tuiles de 24 × 24 px · 4 frames de 150 ms · feuille Aseprite multi-frames · 6 ambiances · roche ocre harmonisée au panorama du kit</p></header>
<main>
<div class="bar" id="amb"></div>
<div class="bar"><button id="play" aria-pressed="true">⏸ Pause</button>
<button id="prec">◀ Frame</button><button id="suiv">Frame ▶</button>
<span class="lab" id="etat"></span></div>
<div class="box"><canvas id="sheet" width="192" height="72" style="width:768px;height:288px"></canvas>
<p class="lab">Planche tilesheet (8 × 3 tuiles) — chaque frame est une planche complète, comme dans la feuille Aseprite.</p></div>
<div class="box"><canvas id="sc" width="480" height="240" style="width:960px;height:480px;max-width:100%"></canvas>
<p class="lab">Exemple d’assemblage : falaises reliées par pont de corde, escalier taillé et passerelle de bois ; échelle de paroi, talus, brume et éboulis.</p></div>
<div class="box"><h2 style="margin:0 0 4px;font-size:14px">Tuiles</h2><div class="grille" id="gr"></div></div>
</main><script>
const D=__DATA__;
let amb=D.ambiances[0], f=0, joue=true;
const imgs={};
function get(a,i){const k=a+'#'+i;if(!imgs[k]){imgs[k]=new Image();imgs[k].src=D.assets[a][i];}return imgs[k]}
function getSc(a,i){const k=a+'sc'+i;if(!imgs[k]){imgs[k]=new Image();imgs[k].src=D.assets[a+'_scene'][i];}return imgs[k]}
const bar=document.getElementById('amb');
D.ambiances.forEach(a=>{const b=document.createElement('button');b.textContent=a;b.dataset.a=a;
 b.onclick=()=>{amb=a;maj();};bar.appendChild(b);});
const gr=document.getElementById('gr');
D.tiles.forEach((tl,i)=>{const d=document.createElement('div');d.className='tu';
 const c=document.createElement('canvas');c.width=24;c.height=24;c.style.width='72px';c.style.height='72px';
 d.appendChild(c);d.innerHTML+='<b>'+tl.nom+'</b><span>'+(tl.anime?'<em class="anim">animé · </em>':'')+tl.desc+'</span>';
 gr.appendChild(d);tl._c=c;});
function maj(){[...bar.children].forEach(b=>b.setAttribute('aria-pressed',b.dataset.a===amb));
 document.getElementById('etat').textContent='ambiance '+amb+' — frame '+(f+1)+'/'+D.frames+' ('+D.duree+' ms)';
 const cs=document.getElementById('sheet').getContext('2d');cs.clearRect(0,0,192,72);cs.drawImage(get(amb,f),0,0);
 const cc=document.getElementById('sc').getContext('2d');cc.clearRect(0,0,480,240);cc.drawImage(getSc(amb,f),0,0);
 D.tiles.forEach((tl,i)=>{const ctx=tl._c.getContext('2d');ctx.clearRect(0,0,24,24);
  ctx.drawImage(get(amb,f),(i%8)*24,Math.floor(i/8)*24,24,24,0,0,24,24);});}
setInterval(()=>{if(joue){f=(f+1)%D.frames;maj();}},D.duree);
document.getElementById('play').onclick=e=>{joue=!joue;e.currentTarget.setAttribute('aria-pressed',joue);
 e.currentTarget.textContent=joue?'⏸ Pause':'▶ Lecture';};
document.getElementById('prec').onclick=()=>{f=(f+D.frames-1)%D.frames;maj();};
document.getElementById('suiv').onclick=()=>{f=(f+1)%D.frames;maj();};
let prets=0;const tot=D.ambiances.length*(D.frames*2);
function ok(){prets++;if(prets>=tot)maj();}
D.ambiances.forEach(a=>{for(let i=0;i<D.frames;i++){get(a,i).onload=ok;getSc(a,i).onload=ok;}});
maj();
</script></body></html>'''
    html_path.write_text(html.replace('__DATA__', data), encoding='utf-8')


# ---------------------------------------------------------------- génération
def main():
    par_amb = {}
    manifeste = {'titre': 'Falaises de Métano / Treasure Town — tileset animé',
                 'grille_tuile': T, 'grille_kit': 8, 'frames': FRAMES, 'duree_ms': DUREE,
                 'ambiances': AMBIANCES, 'planche': [COLS, ROWS],
                 'tuiles': [{'id': i, 'nom': n, 'usage': d, 'anime': a,
                             'colonne': i % COLS, 'ligne': i // COLS}
                            for i, (n, d, a, _f) in enumerate(TUILES)],
                 'fichiers': {}}
    for amb in AMBIANCES:
        d = OUT / amb
        d.mkdir(exist_ok=True)
        frames = [teinte(planche(f), amb) for f in range(FRAMES)]
        scs = [teinte(scene(f), amb) for f in range(FRAMES)]
        sc = scs[0]
        for i, im in enumerate(frames):
            im.save(d / f'planche_f{i + 1}.png', optimize=True)
        aseprite(d / f'tileset_falaises_{amb}.aseprite', frames, DUREE, T)
        apng(d / 'animation.png', frames, DUREE)
        scene_png = []
        for q in scs:
            buf = io.BytesIO()
            q.save(buf, format='PNG', optimize=True)
            scene_png.append(buf.getvalue())
        sc.save(OUT / f'exemple_{amb}.png', optimize=True)
        fps = []
        for im in frames:
            b = io.BytesIO()
            im.save(b, format='PNG', optimize=True)
            fps.append(b.getvalue())
        par_amb[amb] = {'frames_png': fps, 'scene_png': scene_png}
        manifeste['fichiers'][amb] = {
            'aseprite': f'falaises/{amb}/tileset_falaises_{amb}.aseprite',
            'planches': [f'falaises/{amb}/planche_f{i + 1}.png' for i in range(FRAMES)],
            'apng': f'falaises/{amb}/animation.png',
            'exemple': f'falaises/exemple_{amb}.png'}
    (OUT / 'falaises.json').write_text(json.dumps(manifeste, ensure_ascii=False, indent=2), encoding='utf-8')
    apercu(R / 'apercu_falaises.html', par_amb)
    kit = json.loads((R / 'kit.json').read_text())
    kit['falaises'] = {'manifeste': 'falaises/falaises.json', 'apercu': 'apercu_falaises.html',
                       'tuiles': len(TUILES), 'frames': FRAMES, 'duree_ms': DUREE,
                       'ambiances': AMBIANCES}
    (R / 'kit.json').write_text(json.dumps(kit, ensure_ascii=False, indent=2), encoding='utf-8')
    print('OK falaises :', len(TUILES), 'tuiles ×', FRAMES, 'frames ×', len(AMBIANCES), 'ambiances')


if __name__ == '__main__':
    main()
