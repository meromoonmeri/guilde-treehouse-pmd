"""
generer_zones_pmd.py — 150 zones jouables bâties sur les tuiles PMD d'origine.

Principe
--------
Chaque zone est tirée de la banque de tuiles d'un donjon réel (voir banque.py),
ce qui garantit une palette et une texture parfaitement homogènes, identiques
à celles du jeu. Seul le plan de salle est neuf.

Animation
---------
À la manière des consoles Nintendo, le mouvement ne redessine rien : il fait
**tourner la palette**. Les liquides et les lueurs sont rendus en couleurs
indexées, et chaque image permute un petit groupe d'indices. C'est la technique
d'origine du GBA et de la DS, elle coûte quasiment rien et donne le scintillement
caractéristique de l'eau et de la lave.

Chaque zone livre ses calques séparés, un .aseprite, la description du cycle de
palette pour le moteur, et un aperçu animé.
"""

import os
import sys
import json
import math
import colorsys
import numpy as np
from PIL import Image

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
sys.path.insert(0, os.path.join(ICI, "..", "..", "foulards_pmd", "outils"))
import banque as B
import dpla as DPLA
import aseprite

RACINE = os.path.abspath(os.path.join(ICI, ".."))
T = B.T
COLS, LIGNES = 20, 15
LARG, HAUT = COLS * T, LIGNES * T          # 480 x 360
N_IMG = 12                                  # un cycle DPLA complet (PPCM 12)

CALQUES = [
    {"nom": "GROUPE_TERRAIN", "type": "groupe"},
    {"nom": "00_sol", "niveau": 1},
    {"nom": "01_liquide", "niveau": 1},
    {"nom": "02_mur", "niveau": 1},
    {"nom": "GROUPE_VIE", "type": "groupe"},
    {"nom": "03_decor", "niveau": 1},
    {"nom": "04_lumiere", "niveau": 1, "fusion": aseprite.ADDITION},
    {"nom": "05_particules", "niveau": 1, "fusion": aseprite.ADDITION},
    {"nom": "06_eclairage", "fusion": aseprite.MULTIPLIER, "opacite": 205},
]
ADDITIFS = {"04_lumiere", "05_particules"}


# --------------------------------------------------------------------------
# Plans de salle
# --------------------------------------------------------------------------

def _lisser(g, tours=2):
    for _ in range(tours):
        n = g.copy()
        for y in range(LIGNES):
            for x in range(COLS):
                v = 0
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        yy, xx = y + dy, x + dx
                        v += 0 if (0 <= yy < LIGNES and 0 <= xx < COLS
                                   and g[yy, xx]) else 1
                n[y, x] = False if v >= 5 else (True if v <= 3 else g[y, x])
        g = n
    return g


def _bord(g, ep=1):
    g[:ep, :] = False
    g[-ep:, :] = False
    g[:, :ep] = False
    g[:, -ep:] = False
    return g


def p_ovale(rng):
    g = np.zeros((LIGNES, COLS), bool)
    rx = rng.uniform(0.30, 0.42)
    ry = rng.uniform(0.30, 0.42)
    for y in range(LIGNES):
        for x in range(COLS):
            g[y, x] = math.hypot((x - COLS / 2) / (COLS * rx),
                                 (y - LIGNES / 2) / (LIGNES * ry)) < 1.0
    return _bord(g)


def p_croix(rng):
    g = np.zeros((LIGNES, COLS), bool)
    e = int(rng.integers(2, 4))
    cy, cx = LIGNES // 2, COLS // 2
    g[cy - e:cy + e + 1, :] = True
    g[:, cx - e:cx + e + 1] = True
    return _bord(g)


def p_couloir(rng):
    g = np.zeros((LIGNES, COLS), bool)
    amp = rng.uniform(0.14, 0.30)
    per = rng.uniform(0.16, 0.34)
    for x in range(COLS):
        cy = LIGNES / 2 + math.sin(x * per) * LIGNES * amp
        d = rng.uniform(1.8, 3.2)
        for y in range(LIGNES):
            if abs(y - cy) <= d:
                g[y, x] = True
    return _bord(g)


def p_grotte(rng):
    g = rng.random((LIGNES, COLS)) > 0.46
    g = _lisser(g, 4)
    for y in range(LIGNES):
        for x in range(COLS):
            if math.hypot((x - COLS / 2) / (COLS * 0.22),
                          (y - LIGNES / 2) / (LIGNES * 0.22)) < 1.0:
                g[y, x] = True
    return _bord(g)


def p_anneau(rng):
    g = np.zeros((LIGNES, COLS), bool)
    for y in range(LIGNES):
        for x in range(COLS):
            d = math.hypot((x - COLS / 2) / (COLS * 0.40),
                           (y - LIGNES / 2) / (LIGNES * 0.40))
            g[y, x] = 0.42 < d < 1.0
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        for t in np.linspace(0, 1, 20):
            x = int(COLS / 2 + math.cos(a) * t * COLS * 0.36)
            y = int(LIGNES / 2 + math.sin(a) * t * LIGNES * 0.36)
            if 0 <= y < LIGNES and 0 <= x < COLS:
                g[y, x] = True
    return _bord(g)


def p_deux_salles(rng):
    g = np.zeros((LIGNES, COLS), bool)
    for cx, cy in ((COLS * 0.28, LIGNES * 0.35), (COLS * 0.72, LIGNES * 0.65)):
        r = rng.uniform(0.20, 0.28)
        for y in range(LIGNES):
            for x in range(COLS):
                if math.hypot((x - cx) / (COLS * r), (y - cy) / (LIGNES * r * 1.3)) < 1:
                    g[y, x] = True
    y0, y1 = int(LIGNES * 0.35), int(LIGNES * 0.65)
    for t in np.linspace(0, 1, 40):
        x = int(COLS * (0.28 + 0.44 * t))
        y = int(y0 + (y1 - y0) * t)
        for d in (-1, 0, 1):
            if 0 <= y + d < LIGNES:
                g[y + d, x] = True
    return _bord(g)


def p_damier(rng):
    g = np.ones((LIGNES, COLS), bool)
    pas = int(rng.integers(3, 5))
    for y in range(LIGNES):
        for x in range(COLS):
            if (x // pas + y // pas) % 2 == 0 and rng.random() < 0.55:
                g[y, x] = False
    return _bord(g)


def p_spirale(rng):
    g = np.zeros((LIGNES, COLS), bool)
    for t in np.linspace(0, 1, 400):
        a = t * math.pi * 4.2
        r = t * min(COLS, LIGNES) * 0.42
        x = int(COLS / 2 + math.cos(a) * r)
        y = int(LIGNES / 2 + math.sin(a) * r * 0.78)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if 0 <= y + dy < LIGNES and 0 <= x + dx < COLS:
                    g[y + dy, x + dx] = True
    return _bord(g)


def p_arene(rng):
    g = np.zeros((LIGNES, COLS), bool)
    for y in range(LIGNES):
        for x in range(COLS):
            g[y, x] = math.hypot((x - COLS / 2) / (COLS * 0.44),
                                 (y - LIGNES / 2) / (LIGNES * 0.44)) < 1.0
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        ix = int(COLS / 2 + math.cos(a) * COLS * 0.24)
        iy = int(LIGNES / 2 + math.sin(a) * LIGNES * 0.24)
        for dy in (-1, 0):
            for dx in (-1, 0):
                if 0 <= iy + dy < LIGNES and 0 <= ix + dx < COLS:
                    g[iy + dy, ix + dx] = False
    return _bord(g)


def p_labyrinthe(rng):
    g = np.zeros((LIGNES, COLS), bool)
    for y in range(1, LIGNES - 1, 2):
        g[y, 1:COLS - 1] = True
    for x in range(1, COLS - 1, 3):
        g[1:LIGNES - 1, x] = True
    for _ in range(int(rng.integers(6, 12))):
        y = int(rng.integers(1, LIGNES - 1))
        x = int(rng.integers(1, COLS - 1))
        g[y, x] = False
    return _bord(g)


PLANS = [("ovale", p_ovale), ("croix", p_croix), ("couloir", p_couloir),
         ("grotte", p_grotte), ("anneau", p_anneau), ("deux_salles", p_deux_salles),
         ("damier", p_damier), ("spirale", p_spirale), ("arene", p_arene),
         ("labyrinthe", p_labyrinthe)]


# --------------------------------------------------------------------------
# Liquides : repérage dans les cartes d'origine
# --------------------------------------------------------------------------

def _teinte_moyenne(t):
    a = np.asarray(t, dtype=np.float32) / 255.0
    r, g, b = a[..., 0].mean(), a[..., 1].mean(), a[..., 2].mean()
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return h, s, v


def banque_liquide(cartes, max_tuiles=10):
    """
    Cherche dans les cartes des tuiles d'eau ou de lave : très répétées,
    saturées, et de teinte franchement bleue ou franchement chaude.
    """
    from collections import Counter
    cand = {"eau": [], "lave": []}
    for p in cartes:
        grille, dim = B.decouper(p)
        if grille is None:
            continue
        cols, lignes = dim
        freq = Counter()
        for y in range(lignes):
            for x in range(cols):
                freq[B._cle(grille[y][x])] += 1
        for y in range(lignes):
            for x in range(cols):
                k = B._cle(grille[y][x])
                if freq[k] < max(4, cols * lignes * 0.012):
                    continue
                t = grille[y][x]
                h, s, v = _teinte_moyenne(t)
                if s < 0.28 or v < 0.13:
                    continue
                if 0.50 <= h <= 0.66 and len(cand["eau"]) < max_tuiles:
                    if all(B._cle(u) != k for u in cand["eau"]):
                        cand["eau"].append(t)
                elif (h >= 0.94 or h <= 0.09) and v > 0.30 \
                        and len(cand["lave"]) < max_tuiles:
                    if all(B._cle(u) != k for u in cand["lave"]):
                        cand["lave"].append(t)
    return cand


def zone_liquide(g, rng, forme="mare"):
    """Creuse une nappe de liquide à l'intérieur de la zone praticable."""
    L = np.zeros_like(g)
    if forme == "mare":
        cx = rng.uniform(COLS * 0.35, COLS * 0.65)
        cy = rng.uniform(LIGNES * 0.35, LIGNES * 0.65)
        rx = rng.uniform(0.22, 0.34) * COLS
        ry = rng.uniform(0.20, 0.32) * LIGNES
        for y in range(LIGNES):
            for x in range(COLS):
                if math.hypot((x - cx) / rx, (y - cy) / ry) < 1.0:
                    L[y, x] = True
    else:                                    # rivière
        per = rng.uniform(0.18, 0.36)
        for x in range(COLS):
            cy = LIGNES / 2 + math.sin(x * per + rng.uniform(0, 3)) * LIGNES * 0.18
            for dy in (-2, -1, 0, 1, 2):
                y = int(cy + dy)
                if 0 <= y < LIGNES:
                    L[y, x] = True
    return L & g


# --------------------------------------------------------------------------
# Animation par rotation de palette
# --------------------------------------------------------------------------

def rendre_liquide_dpla(c_liq, tuiles, n_img=N_IMG):
    """
    Anime la nappe de liquide selon le format DPLA de Chunsoft.

    La rampe de couleurs est relevée sur les tuiles d'eau ou de lave du jeu,
    triée par luminance, et sert de palette indexée à la nappe. Chaque image
    substitue ensuite les valeurs de la palette, sans jamais toucher aux
    pixels — c'est le mécanisme du matériel.
    """
    rampe = DPLA.rampe_depuis_tuiles(tuiles, n_couleurs=12)
    if len(rampe) < 3:
        return [c_liq] * n_img, None
    table = DPLA.table_depuis_rampe(rampe)

    a = np.array(c_liq.convert("RGBA"))
    plein = a[..., 3] > 0
    if not plein.any():
        return [c_liq] * n_img, None
    r = np.array(rampe, dtype=np.float32)
    px = a[plein][:, :3].astype(np.float32)
    idx = np.argmin(np.linalg.norm(px[:, None, :] - r[None, :, :], axis=2), axis=1)
    carte = np.zeros(a.shape[:2], dtype=np.int32)
    carte[plein] = idx

    periode = table.periode(0)
    pas = max(1, periode // n_img)
    images = []
    for k in range(n_img):
        pal = table.palette_a_l_image(0, k * pas)
        tab = np.array(pal[:len(rampe)] if len(pal) >= len(rampe)
                       else pal + [(0, 0, 0)] * (len(rampe) - len(pal)),
                       dtype=np.uint8)
        out = np.zeros_like(a)
        out[..., :3] = tab[np.clip(carte, 0, len(tab) - 1)]
        out[..., 3] = np.where(plein, 255, 0)
        images.append(Image.fromarray(out, "RGBA"))
    return images, table


def indexer(im, n=12):
    """Réduit un calque à une palette indexée et renvoie (indices, palette)."""
    rgba = np.array(im)
    alpha = rgba[..., 3]
    plein = alpha > 0
    if not plein.any():
        return None, None, plein
    rgb = Image.fromarray(rgba[..., :3], "RGB")
    q = rgb.quantize(colors=n, method=Image.Quantize.MAXCOVERAGE,
                     dither=Image.Dither.NONE)
    pal = q.getpalette()[: n * 3]
    return np.array(q), [tuple(pal[i * 3:i * 3 + 3]) for i in range(n)], plein


def cycler(idx, pal, plein, decalage, plage):
    """
    Rend le calque avec la palette tournée de `decalage` sur `plage` indices.
    C'est la technique d'animation d'origine : les pixels ne bougent pas, ce
    sont les couleurs qui défilent dans le nuancier.
    """
    d, f = plage
    n = f - d
    p2 = list(pal)
    for i in range(n):
        p2[d + i] = pal[d + ((i + decalage) % n)]
    tab = np.array(p2, dtype=np.uint8)
    out = np.zeros(idx.shape + (4,), dtype=np.uint8)
    out[..., :3] = tab[np.clip(idx, 0, len(tab) - 1)]
    out[..., 3] = np.where(plein, 255, 0)
    return Image.fromarray(out, "RGBA")


def trier_palette_par_luminance(pal):
    ordre = sorted(range(len(pal)), key=lambda i: sum(pal[i]))
    table = {o: i for i, o in enumerate(ordre)}
    return [pal[o] for o in ordre], table


# --------------------------------------------------------------------------
# Lumière et particules
# --------------------------------------------------------------------------

def rayons(g, rng, couleur, n=3):
    """Puits de lumière verticaux tombant sur des cases praticables."""
    im = np.zeros((HAUT, LARG, 4), dtype=np.float32)
    libres = [(x, y) for y in range(LIGNES) for x in range(COLS) if g[y, x]]
    if not libres:
        return Image.fromarray(im.astype(np.uint8), "RGBA")
    rng.shuffle(libres)
    for (tx, ty) in libres[:n]:
        cx = tx * T + T // 2
        base = ty * T + T
        haut = int(rng.integers(HAUT // 3, HAUT))
        lw = rng.uniform(T * 0.5, T * 1.1)
        for j in range(haut):
            y = base - j
            if y < 0:
                break
            if y >= HAUT:
                continue
            u = j / haut
            for dx in range(int(-lw * (1 + u)), int(lw * (1 + u)) + 1):
                x = cx + dx
                if not (0 <= x < LARG):
                    continue
                d = abs(dx) / max(lw * (1 + u), 1e-6)
                f = (1 - d) ** 2.6 * (1 - u) ** 1.1 * 0.30
                im[y, x, :3] = np.minimum(255, im[y, x, :3] + np.array(couleur) * f)
                im[y, x, 3] = min(255, im[y, x, 3] + 255 * f)
    return Image.fromarray(np.clip(im, 0, 255).astype(np.uint8), "RGBA")


def poussiere(phase, rng_graine, couleur, n=44):
    im = np.zeros((HAUT, LARG, 4), dtype=np.float32)
    rng = np.random.default_rng(rng_graine)
    for i in range(n):
        bx, by = rng.uniform(0, LARG), rng.uniform(0, HAUT)
        x = (bx + phase * 26 * rng.uniform(0.4, 1.3)) % LARG
        y = (by - phase * 34 * rng.uniform(0.4, 1.3)) % HAUT
        f = 0.35 + 0.45 * (0.5 + 0.5 * math.sin(phase * 6.283 * 2 + i))
        xi, yi = int(x), int(y)
        im[yi, xi, :3] = np.minimum(255, im[yi, xi, :3] + np.array(couleur) * f)
        im[yi, xi, 3] = min(255, im[yi, xi, 3] + 255 * f)
    return Image.fromarray(np.clip(im, 0, 255).astype(np.uint8), "RGBA")


def vignette(force=170):
    ys, xs = np.mgrid[0:HAUT, 0:LARG]
    d = np.sqrt(((xs - LARG / 2) / (LARG * 0.64)) ** 2
                + ((ys - HAUT / 2) / (HAUT * 0.70)) ** 2)
    v = np.clip((d - 0.68) * 1.9, 0, 1)
    a = np.zeros((HAUT, LARG, 4), dtype=np.uint8)
    a[..., :3] = np.array([6, 7, 16])
    a[..., 3] = (v * force).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def composer(jeu):
    out = np.zeros((HAUT, LARG, 4), dtype=np.float32)
    for c in CALQUES:
        if c.get("type") == "groupe":
            continue
        im = jeu.get(c["nom"])
        if im is None:
            continue
        a = np.asarray(im.convert("RGBA"), dtype=np.float32)
        k = a[..., 3:4] / 255.0
        if c["nom"] in ADDITIFS:
            out[..., :3] = np.minimum(255.0, out[..., :3] + a[..., :3] * k)
            out[..., 3] = np.minimum(255.0, out[..., 3] + a[..., 3])
        else:
            out[..., :3] = a[..., :3] * k + out[..., :3] * (1 - k)
            out[..., 3] = np.minimum(255.0, a[..., 3] + out[..., 3] * (1 - k[..., 0]))
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")


# --------------------------------------------------------------------------
# Production
# --------------------------------------------------------------------------

TEINTE_LUMIERE = {
    "foret": (150, 210, 120), "eau": (140, 200, 240), "lave": (255, 170, 90),
    "glace": (190, 230, 255), "cristal": (200, 170, 255), "desert": (250, 225, 160),
    "pierre": (190, 200, 220), "abysse": (120, 150, 220), "prairie": (215, 235, 150),
}
TEINTE_POUSSIERE = {
    "foret": (220, 240, 170), "eau": (180, 225, 255), "lave": (255, 190, 120),
    "glace": (225, 245, 255), "cristal": (225, 195, 255), "desert": (245, 230, 190),
    "pierre": (210, 215, 230), "abysse": (150, 180, 240), "prairie": (235, 250, 190),
}


def biome_du_donjon(noms, table):
    from collections import Counter
    c = Counter()
    for n in noms:
        for b, lst in table.items():
            if n in lst:
                c[b] += 1
    return c.most_common(1)[0][0] if c else "pierre"


def _sauver(im, chemin, couleurs=180):
    """PNG indexé : ces calques tiennent largement dans une palette courte."""
    a = np.array(im.convert("RGBA"))
    if (a[..., 3] > 0).sum() == 0:
        Image.fromarray(a, "RGBA").save(chemin, optimize=True)
        return
    if (a[..., 3] < 255).any():
        im.save(chemin, optimize=True)     # transparence partielle : on garde RGBA
        return
    im.convert("RGB").quantize(colors=couleurs,
                               method=Image.Quantize.MAXCOVERAGE,
                               dither=Image.Dither.NONE).save(chemin, optimize=True)


def decouper_salle(chemin, rng):
    """
    Prélève une fenêtre de 20 x 15 tuiles dans une carte réelle, avec une
    variation possible par miroir ou demi-tour.

    Reconstruire une salle tuile par tuile s'est révélé une impasse : déduire
    de la seule fréquence quelle tuile est du sol, de la lisière ou de la
    masse échoue sur les sols variés, et la salle vire au patchwork. Prélever
    une fenêtre garantit au contraire une cohérence parfaite, puisque
    l'agencement vient du jeu lui-même.
    """
    im = Image.open(chemin).convert("RGB")
    w, h = im.size
    cw, ch = COLS * T, LIGNES * T
    if w < cw or h < ch:
        im = im.resize((max(w, cw), max(h, ch)), Image.NEAREST)
        w, h = im.size
    ox = int(rng.integers(0, (w - cw) // T + 1)) * T
    oy = int(rng.integers(0, (h - ch) // T + 1)) * T
    sub = im.crop((ox, oy, ox + cw, oy + ch))
    v = rng.random()
    if v < 0.30:
        sub = sub.transpose(Image.FLIP_LEFT_RIGHT)
    elif v < 0.45:
        sub = sub.transpose(Image.ROTATE_180)
    return sub.convert("RGBA"), (ox // T, oy // T)


def masque_praticable(salle):
    """
    Repère grossièrement les cases praticables d'une salle prélevée : celles
    dont la tuile est répétée et peu contrastée. Ne sert qu'à placer les
    effets — liquides, lumière, accessoires — pas à choisir les tuiles.
    """
    from collections import Counter
    freq = Counter()
    infos = {}
    for y in range(LIGNES):
        for x in range(COLS):
            t = salle.crop((x * T, y * T, x * T + T, y * T + T))
            k = t.tobytes()
            freq[k] += 1
            if k not in infos:
                a = np.asarray(t.convert("RGB"), dtype=np.float32)
                infos[k] = (a.mean(), a.std())
    ordre = sorted(((n, k) for k, n in freq.items()
                    if infos[k][0] >= 14 and infos[k][1] <= 74), reverse=True)
    sols, cumul = set(), 0
    for n, k in ordre:
        sols.add(k)
        cumul += n
        if cumul >= 0.34 * COLS * LIGNES:
            break
    m = np.zeros((LIGNES, COLS), bool)
    for y in range(LIGNES):
        for x in range(COLS):
            k = salle.crop((x * T, y * T, x * T + T, y * T + T)).tobytes()
            m[y, x] = k in sols
    return m


def richesse(salle):
    """
    Deux mesures de contenu d'une découpe : nombre de tuiles distinctes et
    part de pixels non noirs. Certaines cartes du jeu sont des aplats de
    remplissage ; sans ce contrôle elles produisent des salles vides.
    """
    vues = set()
    for y in range(LIGNES):
        for x in range(COLS):
            vues.add(salle.crop((x * T, y * T, x * T + T, y * T + T)).tobytes())
    a = np.asarray(salle.convert("RGB"), dtype=np.float32)
    plein = float((a.mean(axis=2) > 14).mean())
    return len(vues), plein


def batir_zone(cle, cartes, liquides, biome, nom_variante, graine, dossier):
    rng = np.random.default_rng(graine)
    salle = origine = src = None
    for essai in range(10):
        cand = cartes[int(rng.integers(0, len(cartes)))]
        s, o = decouper_salle(cand, rng)
        n_tuiles, plein = richesse(s)
        if n_tuiles >= 10 and plein >= 0.55:
            salle, origine, src = s, o, cand
            break
        if salle is None or n_tuiles > richesse(salle)[0]:
            salle, origine, src = s, o, cand
    if salle is None:
        return None
    n_tuiles, plein = richesse(salle)
    if n_tuiles < 6 or plein < 0.35:
        return None
    g = masque_praticable(salle)

    c_sol = salle
    c_mur = Image.new("RGBA", (LARG, HAUT))     # tout est dans la salle prélevée

    # --- liquide -----------------------------------------------------------
    c_liq = Image.new("RGBA", (LARG, HAUT))
    type_liq = None
    if liquides["lave"] and biome in ("lave", "abysse", "desert", "pierre", "cristal"):
        type_liq = "lave"
    elif liquides["eau"]:
        type_liq = "eau"
    # Le liquide n'est creusé que dans le cœur du sol : on érode d'abord le
    # masque, sinon des tuiles d'eau se posent sur les murs ou dans le vide.
    noyau = g.copy()
    for _ in range(1):
        e = noyau.copy()
        for y in range(LIGNES):
            for x in range(COLS):
                if not noyau[y, x]:
                    continue
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        yy, xx = y + dy, x + dx
                        if not (0 <= yy < LIGNES and 0 <= xx < COLS) \
                                or not noyau[yy, xx]:
                            e[y, x] = False
        noyau = e
    # Sur les salles très encombrées l'érosion ne laisse presque rien : on
    # retombe alors sur le masque brut plutôt que de renoncer au liquide.
    base_liq = noyau if noyau.sum() >= 6 else g
    if type_liq and base_liq.sum() >= 6 and rng.random() < 0.80:
        L = zone_liquide(base_liq, rng, "riviere" if rng.random() < 0.4 else "mare")
        lot = liquides[type_liq]
        if L.sum() >= 6:
            pose = 0
            for y in range(LIGNES):
                for x in range(COLS):
                    if not L[y, x]:
                        continue
                    # dernier garde-fou : une tuile de liquide n'est posée que
                    # si son voisinage est lui aussi praticable, sinon des
                    # carrés d'eau flottent au milieu des murs
                    appui = sum(1 for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                                if 0 <= y + dy < LIGNES and 0 <= x + dx < COLS
                                and base_liq[y + dy, x + dx])
                    if appui < 6:
                        continue
                    c_liq.paste(lot[int(rng.integers(0, len(lot)))].convert("RGBA"),
                                (x * T, y * T))
                    pose += 1
            if pose < 4:
                c_liq = Image.new("RGBA", (LARG, HAUT))
                type_liq = None
        else:
            type_liq = None
    else:
        type_liq = None

    # --- accessoires -------------------------------------------------------
    c_dec = Image.new("RGBA", (LARG, HAUT))
    props = [p for p in (liquides.get("props") or [])
             if np.asarray(p.convert("RGB"), dtype=np.float32).mean() > 26]
    if props and base_liq.sum() > 10:
        libres = [(x, y) for y in range(1, LIGNES - 1) for x in range(1, COLS - 1)
                  if base_liq[y, x]
                  and not c_liq.getpixel((x * T + T // 2, y * T + T // 2))[3]]
        rng.shuffle(libres)
        for (x, y) in libres[: int(rng.integers(1, 5))]:
            c_dec.paste(props[int(rng.integers(0, len(props)))].convert("RGBA"),
                        (x * T, y * T))

    # --- lumière, poussière, vignette --------------------------------------
    c_lum = rayons(noyau if noyau.any() else (g if g.any()
                   else np.ones((LIGNES, COLS), bool)), rng,
                   TEINTE_LUMIERE.get(biome, (200, 210, 230)),
                   n=int(rng.integers(1, 4)))
    ecl = vignette()

    liq_images, table_dpla = ([c_liq] * N_IMG, None)
    if type_liq:
        liq_images, table_dpla = rendre_liquide_dpla(c_liq, liquides[type_liq])
    idx_r, pal_r, plein_r = indexer(c_lum, 8)
    if pal_r:
        pal_r, table_r = trier_palette_par_luminance(pal_r)
        remap_r = np.zeros(16, dtype=np.int64)
        for o, i in table_r.items():
            remap_r[o] = i
        idx_r = remap_r[np.clip(idx_r, 0, 15)]

    images = []
    for i in range(N_IMG):
        ph = i / N_IMG
        liq = liq_images[i]
        lum = (cycler(idx_r, pal_r, plein_r, i // 2, (4, 8))
               if pal_r is not None else c_lum)
        images.append({
            "00_sol": c_sol, "01_liquide": liq, "02_mur": c_mur,
            "03_decor": c_dec, "04_lumiere": lum,
            "05_particules": poussiere(ph, graine,
                                       TEINTE_POUSSIERE.get(biome, (220, 225, 240))),
            "06_eclairage": ecl,
        })

    frames = [composer(j) for j in images]
    os.makedirs(dossier, exist_ok=True)
    for nom, im in images[0].items():
        _sauver(im, os.path.join(dossier, f"{nom}.png"))
    frames[0].convert("RGB").quantize(
        colors=200, method=Image.Quantize.MAXCOVERAGE,
        dither=Image.Dither.NONE).save(
        os.path.join(dossier, "compose.png"), optimize=True)

    # Une seule image dans le .aseprite : l'animation étant une rotation de
    # palette décrite par cycles.json, dupliquer huit fois le calque de sol
    # multipliait le poids du dossier par six sans rien apporter.
    pal_ase = ([tuple(c) for c in (table_dpla.palette_a_l_image(0, 0)
                                   if table_dpla else [])] + (pal_r or []))
    aseprite.ecrire_avance(
        os.path.join(dossier, "zone.aseprite"), CALQUES, images[:1],
        (LARG, HAUT), duree_ms=110, palette=pal_ase[:64] or None)

    cycles = {
        "liquide": {
            "type": type_liq,
            "methode": "DPLA — substitution de palette, format Chunsoft",
            "palette_cible": DPLA.PALETTES_ANIMEES[0],
            "periode_tics": table_dpla.periode(0) if table_dpla else None,
            "table": "dpla.json",
        } if table_dpla else None,
        "lumiere": ({"methode": "rotation d'indices, approximation",
                     "palette": ["#%02X%02X%02X" % c for c in pal_r],
                     "plage_cyclee": [4, 8], "pas_par_image": 0.5}
                    if pal_r is not None else None),
        "images_rendues": N_IMG, "duree_ms": 110,
    }
    json.dump(cycles, open(os.path.join(dossier, "cycles.json"), "w"),
              indent=1, ensure_ascii=False)
    if table_dpla:
        table_dpla.ecrire_json(os.path.join(dossier, "dpla.json"))

    return {"cle": cle, "biome": biome, "variante": nom_variante,
            "liquide": type_liq, "praticable_pct": round(float(g.mean()), 3),
            "source": os.path.basename(src)[:-4], "origine_tuiles": list(origine),
            "frames": frames}


def main(limite=150, gifs=16):
    table = json.load(open("/home/user/biomes.json"))
    import re
    cartes = B.cartes_alignees()
    # seuls les donjons : les cartes de village, de scène et de sol sont des
    # illustrations uniques, pas des tilemaps, et donnent du patchwork
    cartes = [p for p in cartes
              if re.match(r"^d\d+p\d+", os.path.basename(p))]
    groupes = B.grouper_par_donjon(cartes)
    # La dominance doit rester dans une fourchette : trop basse, c'est une
    # illustration ; trop haute, c'est une carte unie de remplissage. Les deux
    # extrêmes ont été rencontrés et donnent respectivement du patchwork et
    # des salles vides.
    # on garde les donjons assez grands pour qu'une fenêtre de 20 x 15 tuiles
    # y tienne, et dont le sol n'est ni absent ni uniforme
    retenus = []
    for cle, maps in groupes.items():
        assez = [p for p in maps
                 if Image.open(p).size[0] >= COLS * T
                 and Image.open(p).size[1] >= LIGNES * T]
        if not assez:
            continue
        d = B.dominance_sol(assez[:3])
        if not (0.06 <= d <= 0.80):
            continue
        retenus.append((cle, assez, len(assez)))
    retenus.sort(key=lambda t: -t[2])
    print(f"donjons retenus : {len(retenus)} / {len(groupes)}")
    ordre = [(c, m) for c, m, _ in retenus]

    dz = os.path.join(RACINE, "zones")
    os.makedirs(dz, exist_ok=True)
    os.makedirs(os.path.join(RACINE, "apercus"), exist_ok=True)

    manifeste = {"format": "zones PMD, tuiles d'origine, animation par rotation "
                           "de palette", "taille": [LARG, HAUT], "tuile": T,
                 "grille": [COLS, LIGNES], "images_par_cycle": N_IMG, "zones": []}
    faits, i_plan, vignettes, cache_liq = 0, 0, [], {}
    gifs_faits = []
    tours = 0
    while faits < limite and tours < 12:
        tours += 1
        for cle, maps in ordre:
            if faits >= limite:
                break
            noms = [os.path.basename(p)[:-4] for p in maps]
            biome = biome_du_donjon(noms, table)
            if cle not in cache_liq:
                lq = banque_liquide(maps[:5])
                lq["props"] = B.construire(maps[:5])[0].get("props") or []
                cache_liq[cle] = lq
            liq = cache_liq[cle]
            nom_var = f"v{tours}"
            nom_zone = f"{faits + 1:03d}_{cle}_{nom_var}"
            info = batir_zone(cle, maps, liq, biome, nom_var,
                              1000 + faits * 7 + tours, os.path.join(dz, nom_zone))
            if info is None:
                continue
            frames = info.pop("frames")
            info["dossier"] = f"zones/{nom_zone}"
            manifeste["zones"].append(info)
            if len(gifs_faits) < gifs and (info.get("liquide")
                                           or len(gifs_faits) < 4):
                g8 = [f.convert("P", palette=Image.ADAPTIVE, colors=128)
                      for f in frames]
                g8[0].save(os.path.join(RACINE, "apercus", f"{nom_zone}.gif"),
                           save_all=True, append_images=g8[1:], duration=110,
                           loop=0, disposal=2, optimize=True)
                gifs_faits.append(nom_zone)
            vignettes.append((nom_zone, frames[0]))
            faits += 1
            if faits % 25 == 0:
                print(f"  {faits} zones…")

    manifeste["total"] = faits
    json.dump(manifeste, open(os.path.join(RACINE, "manifeste.json"), "w"),
              indent=1, ensure_ascii=False)

    C = 10
    R = (len(vignettes) + C - 1) // C
    W, H = LARG // 4, HAUT // 4
    pl = Image.new("RGB", (W * C, H * R), (16, 16, 20))
    for i, (_, f) in enumerate(vignettes):
        pl.paste(f.convert("RGB").resize((W, H), Image.NEAREST),
                 ((i % C) * W, (i // C) * H))
    pl.save(os.path.join(RACINE, "apercus", "planche_150.png"))
    print(f"\n{faits} zones produites")
    from collections import Counter
    print("biomes :", dict(Counter(z["biome"] for z in manifeste["zones"])))
    print("liquides :", dict(Counter(str(z["liquide"]) for z in manifeste["zones"])))


if __name__ == "__main__":
    lim = int(sys.argv[1]) if len(sys.argv) > 1 else 150
    main(lim)
