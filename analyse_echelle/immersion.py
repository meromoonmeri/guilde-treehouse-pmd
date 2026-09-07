# -*- coding: utf-8 -*-
"""
Cadre d'immersion PMD : feuillage autour des extremites des bordures de bois,
fondu dans le fond noir.

Principe :
  - une bande noire (6-10 px) au ras du canvas, hors passages : le bord de
    l'image devient noir, la meme couleur que le fond du jeu — la piece semble
    posee dans le noir, sans couture ;
  - des bouquets de feuilles en pixel art, ancres au ras des bords du canvas et
    a l'arete des murs, denses aux coins, clairsemes au milieu ; les feuilles
    arriere sont tres sombres et se confondent avec la bande noire ;
  - quelques lianes tombant du bord superieur ;
  - les passages (contenu touchant le bord) restent totalement degages : le
    feuillage ne bouche jamais un acces ; les fenetres non plus.

Palette olive reprise des feuillages du kit (sprites de vegetation :
#4f6714, #718c1c, #9ab541), etendue vers le noir pour le fondu.
La couche nuit est le calque jour passe par la conversion nuit du kit
(meme transform que source/rebuild_kit.py).

Sorties :
  calques_reduits/<dossier>/<jour|nuit>/11_immersion_feuilles.png
  salles_reduites/<dossier>_<jour|nuit>.png   (composite des calques 01..10 + 11)

Enchaine apres la reduction :
  python3 analyse_echelle/reduire.py
  python3 analyse_echelle/immersion.py
"""
import io
import json
import math
import os
import random

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

CALQUES = ['01_sol', '02_structure', '03_cadres_fenetres', '04_tableaux',
           '05_porte_maitre', '06_decorations', '07_objets', '08_ombres_acces',
           '09_eclairage_fixe', '10_bordure_avant', '11_immersion_feuilles']

# codes -> RGB jour (palette olive du kit, du plus sombre au highlight)
PAL = {
    1: (11, 15, 8),      # contour, presque noir : epouse le fond
    7: (26, 36, 16),     # feuille arriere
    2: (44, 60, 22),     # sombre
    3: (79, 103, 20),    # moyen  (#4f6714)
    4: (113, 140, 28),   # clair
    5: (154, 181, 65),   # reflet (#9ab541)
    6: (58, 44, 23),     # tige
}
NOIR_FOND = (5, 8, 10)   # degrade du bord : se confond avec le fond noir du jeu


def night(a):
    a = a.copy()
    a[:, :, :3] = np.rint(
        a[:, :, :3] * [.36, .34, .43] + [9, 10, 19]).clip(0, 255).astype('uint8')
    a[a[:, :, 3] == 0] = 0
    return a


# --------------------------------------------------------------- passages

def runs(v):
    out, s = [], None
    for i, x in enumerate(v):
        if x and s is None:
            s = i
        elif not x and s is not None:
            out.append((s, i))
            s = None
    if s is not None:
        out.append((s, len(v)))
    return out


def zones_passages(al, lat=18, prof=26, min_run=5):
    """Rectangles a laisser totalement libres : le contenu (sol, structure)
    touchant un bord = un acces qui traverse le cadre."""
    H, W = al.shape
    z = []
    for a, b in runs(al[0:2].any(axis=0)):
        if b - a >= min_run:
            z.append((max(0, a - lat), 0, min(W, b + lat), prof))
    for a, b in runs(al[-2:].any(axis=0)):
        if b - a >= min_run:
            z.append((max(0, a - lat), H - prof, min(W, b + lat), H))
    for a, b in runs(al[:, 0:2].any(axis=1)):
        if b - a >= min_run:
            z.append((0, max(0, a - lat), prof, min(H, b + lat)))
    for a, b in runs(al[:, -2:].any(axis=1)):
        if b - a >= min_run:
            z.append((W - prof, max(0, a - lat), W, min(H, b + lat)))
    return z


# ------------------------------------------------------------- feuillage

def draw_leaf(g, cx, cy, ang, L, Wd, back=False):
    """Feuille en goutte, pointe dans la direction ang. Rasterisee pixel par
    pixel : pas d'antialiasing, style pixel art."""
    H, W = g.shape
    ca, sa = math.cos(ang), math.sin(ang)
    r = int(L * 0.8) + 2
    for y in range(max(0, cy - r), min(H, cy + r + 1)):
        for x in range(max(0, cx - r), min(W, cx + r + 1)):
            dx, dy = x - cx, y - cy
            u = dx * ca + dy * sa
            v = -dx * sa + dy * ca
            t = (u + L / 2.0) / L
            if t < 0 or t > 1:
                continue
            half = Wd / 2.0 * (math.sin(math.pi * t) ** 0.65)
            if abs(v) > half:
                continue
            if back:
                code = 7
                if Wd >= 5 and half - abs(v) < 0.9:
                    code = 1
                g[y, x] = code
                continue
            if Wd >= 5 and half - abs(v) < 0.9:
                code = 1                                  # contour
            elif L >= 11 and abs(v) <= 0.7 and 0.15 < t < 0.85:
                code = 2                                  # nervure
            elif t > 0.72:
                code = 2                                  # pointe
            elif v > half * 0.45:
                code = 2 if Wd >= 7 else 3                # dessous
            elif v < 0:
                code = 4
                if (L >= 9 and t < 0.45
                        and -half * 0.55 <= v <= -half * 0.15):
                    code = 5                              # reflet
            else:
                code = 3
            g[y, x] = code


def draw_cluster(g, ax, ay, ang, L, rng):
    """Bouquet : tige courte, feuilles arriere sombres, eventail de feuilles
    devant, toutes pointees vers l'interieur de la piece."""
    dx, dy = math.cos(ang), math.sin(ang)
    for i in range(rng.randint(2, 4)):                    # tige
        x, y = int(round(ax + dx * i)), int(round(ay + dy * i))
        if 0 <= x < g.shape[1] and 0 <= y < g.shape[0]:
            g[y, x] = 6
    for _ in range(rng.randint(2, 3)):                    # feuilles arriere
        Lb = L * rng.uniform(0.75, 1.05)
        bx = int(ax + dx * (Lb / 2 + 1))
        by = int(ay + dy * (Lb / 2 + 1))
        draw_leaf(g, bx, by, ang + rng.uniform(-0.9, 0.9), Lb, Lb * 0.5,
                  back=True)
    n = rng.randint(3, 6)                                 # feuilles avant
    for k in range(n):
        if k == 0:
            f, a2 = 1.0, ang + rng.uniform(-0.25, 0.25)
        else:
            f, a2 = rng.uniform(0.55, 0.95), ang + rng.uniform(-0.85, 0.85)
        Lf = L * f
        fx = int(ax + dx * (Lf / 2 + 1))
        fy = int(ay + dy * (Lf / 2 + 1))
        draw_leaf(g, fx, fy, a2, Lf, Lf * 0.46)


def draw_vine(g, x0, long, phase, rng, block):
    """Liane tombante : tige ondulee 1 px + petite feuille au bout."""
    H, W = g.shape
    xi = x0
    for i in range(long):
        xi = x0 + int(round(2.0 * math.sin(i * 0.33 + phase)))
        if not (0 <= xi < W) or block[i, xi]:
            return
        g[i, xi] = 2 if (i % 7) < 5 else 7
    draw_leaf(g, xi, min(H - 1, long), math.pi / 2 + rng.uniform(-0.35, 0.35),
              rng.uniform(6, 9), 4.0)


def build_layer(W, H, al, fen, seed):
    rng = random.Random(seed)
    zones = zones_passages(al)
    block = np.zeros((H, W), bool)
    for (x0, y0, x1, y1) in zones:
        block[max(0, y0):y1, max(0, x0):x1] = True
    dist = ndimage.distance_transform_edt(~block)
    soft = np.clip(dist / 14.0, 0, 1)     # fondu du degrade pres des passages

    # --- degrade noir le long des bords (hors passages)
    yy, xx = np.mgrid[0:H, 0:W]
    a_haut = np.clip(1 - yy / 10.0, 0, 1) ** 1.6
    a_bas = np.clip(1 - (H - 1 - yy) / 6.0, 0, 1) ** 1.6
    a_g = np.clip(1 - xx / 10.0, 0, 1) ** 1.6
    a_d = np.clip(1 - (W - 1 - xx) / 10.0, 0, 1) ** 1.6
    alpha = np.maximum(np.maximum(a_haut, a_bas), np.maximum(a_g, a_d))
    alpha *= soft
    # au bas, pas de noir sur un sol qui continue jusqu'au bord
    pres_sol = np.zeros((H, W), bool)
    pres_sol[H - 5] = al[H - 5]
    pres_sol = ndimage.binary_dilation(pres_sol, np.ones((1, 19), bool))
    alpha *= (~pres_sol).astype(np.float32)

    # --- interdits pour le feuillage : passages + fenetres (marge 6)
    fen_m = [(x0 - 6, y0 - 6, x1 + 6, y1 + 6) for (x0, y0, x1, y1) in fen]

    def libre(ax, ay, r):
        x0, y0, x1, y1 = ax - r, ay - r, ax + r, ay + r
        if block[max(0, y0):min(H, y1 + 1), max(0, x0):min(W, x1 + 1)].any():
            return False
        for (fx0, fy0, fx1, fy1) in fen_m:
            if not (x1 < fx0 or x0 > fx1 or y1 < fy0 or y0 > fy1):
                return False
        return True

    g = np.zeros((H, W), np.int16)
    pas = max(1.0, min(2.0, W / 432.0))   # espacement relatif a la largeur

    # coins : grands bouquets diagonaux
    for (cx, cy, ang) in [(2, 2, math.radians(45)),
                          (W - 3, 2, math.radians(135)),
                          (2, H - 3, math.radians(-45)),
                          (W - 3, H - 3, math.radians(-135))]:
        for _ in range(3):
            L = rng.uniform(16, 22)
            if libre(cx, cy, int(L * 1.2) + 2):
                draw_cluster(g, cx, cy, ang, L, rng)

    # bord superieur : bouquets suspendus, denses, qui mordent le haut des murs
    x = 4
    while x < W - 4:
        L = rng.uniform(17, 23) if (x < 60 or x > W - 60) else rng.uniform(14, 19)
        if rng.random() < 0.9 and libre(x, 1, int(L) + 3):
            draw_cluster(g, x, 1, math.pi / 2 + rng.uniform(-0.3, 0.3), L, rng)
        x += int(rng.randint(8, 12) * pas)

    # arete superieure des murs : bouquets poses sur le haut du bois
    prof = np.full(W, H, int)
    for x in range(W):
        if al[0:2, x].any():
            continue
        ys = np.nonzero(al[:, x])[0]
        if len(ys):
            prof[x] = ys[0]
    x = 10
    while x < W - 10:
        yt = int(prof[x])
        if 6 < yt < int(H * 0.5) and rng.random() < 0.62 and libre(x, yt - 1, 14):
            draw_cluster(g, x, yt - 1, math.pi / 2 + rng.uniform(-0.35, 0.35),
                         rng.uniform(9, 14), rng)
        x += rng.randint(14, 26)

    # bords lateraux : bouquets pointant vers l'interieur
    for (ax, ang) in ((1, 0.0), (W - 2, math.pi)):
        y = 6
        while y < int(H * 0.70):
            L = rng.uniform(12, 17) if y < 50 else rng.uniform(9, 14)
            if rng.random() < 0.75 and libre(ax, y, int(L) + 3):
                draw_cluster(g, ax, y, ang + rng.uniform(-0.3, 0.3), L, rng)
            y += int(rng.randint(10, 15) * pas)

    # arete des murs : petits bouquets poses sur le bord du contenu
    ys, xs = np.nonzero(al)
    if len(ys):
        haut, x0c, x1c = int(ys.min()), int(xs.min()), int(xs.max())
        for (ax, ang) in ((x0c - 1, 0.0), (x1c + 1, math.pi)):
            y = haut + 10
            while y < min(int(H * 0.45), haut + 140):
                if rng.random() < 0.6 and libre(ax, y, 12):
                    draw_cluster(g, ax, y, ang + rng.uniform(-0.25, 0.25),
                                 rng.uniform(7, 10), rng)
                y += rng.randint(14, 26)

    # bas : touffes de premier plan aux coins seulement
    for bx in (rng.randint(4, 14), rng.randint(18, 34),
               W - 1 - rng.randint(4, 14), W - 1 - rng.randint(18, 34)):
        L = rng.uniform(10, 15)
        if libre(bx, H - 2, int(L) + 3):
            draw_cluster(g, bx, H - 2, -math.pi / 2 + rng.uniform(-0.4, 0.4),
                         L, rng)

    # lianes tombantes
    for _ in range(rng.choice([0, 1, 1, 2])):
        x0 = rng.randint(60, max(61, W - 60))
        if libre(x0, 4, 8):
            draw_vine(g, x0, rng.randint(22, 46), rng.uniform(0, 6.28), rng,
                      block)

    # --- rasterisation : degrade puis feuilles opaques par-dessus
    img = np.zeros((H, W, 4), np.uint8)
    img[..., 0], img[..., 1], img[..., 2] = NOIR_FOND
    img[..., 3] = (alpha * 235).astype(np.uint8)
    coul = np.zeros((H, W, 3), np.uint8)
    for code, col in PAL.items():
        coul[g == code] = col
    m = g > 0
    for c in range(3):
        img[..., c][m] = coul[..., c][m]
    img[..., 3][m] = 255
    return img


# ------------------------------------------------------------- composite

def recomposite(dossier, palette, W, H):
    comp = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for c in CALQUES:
        p = os.path.join(REPO, 'calques_reduits', dossier, palette, c + '.png')
        if os.path.exists(p):
            comp.alpha_composite(Image.open(p).convert('RGBA'))
    comp.save(os.path.join(REPO, 'salles_reduites',
                           '%s_%s.png' % (dossier, palette)))


def main():
    kit = json.load(io.open(os.path.join(REPO, 'kit.json'), encoding='utf-8'))
    cibles = {c['id']: c for c in json.load(io.open(
        os.path.join(HERE, 'cibles.json'), encoding='utf-8'))['salles']}
    for s in kit['salles']:
        W, H = cibles[s['id']]['toile_ajustee_px']
        # contenu des calques 01..10 (sans le paysage) : passages + murs
        al = np.zeros((H, W), bool)
        for c in CALQUES[:-1]:
            p = os.path.join(REPO, 'calques_reduits', s['dossier'], 'jour',
                             c + '.png')
            al |= np.array(Image.open(p).convert('RGBA'))[:, :, 3] > 8
        # fenetres des coordonnees plein format -> canvas reduit
        fw, fh = float(s['dimensions'][0]), float(s['dimensions'][1])
        fen = [(int(r[0] * W / fw), int(r[1] * H / fh),
                int(r[2] * W / fw), int(r[3] * H / fh))
               for r in (s.get('fenetres') or [])]

        jour = build_layer(W, H, al, fen, seed=int(s['id']) * 100 + 7)
        nuit = night(jour)
        for pal, arr in (('jour', jour), ('nuit', nuit)):
            dst = os.path.join(REPO, 'calques_reduits', s['dossier'], pal,
                               '11_immersion_feuilles.png')
            Image.fromarray(arr, 'RGBA').save(dst)
            recomposite(s['dossier'], pal, W, H)
        cov = 100.0 * (jour[:, :, 3] > 200).sum() / (W * H)
        print('%s %-26s cadre +%d.%02d %% de feuilles' % (
            s['id'], s['nom'][:26], int(cov), int(cov * 100) % 100))


if __name__ == '__main__':
    main()
