"""
foulard.py — Générateur de foulards pixel art au format PMDCollab / SpriteCollab.

Le foulard n'est pas dessiné à la main image par image : il est *rendu* pour
chaque case de chaque planche à partir des données que le format PMD fournit
déjà (marqueurs d'Offsets.png + silhouette de Anim.png). C'est ce qui lui
permet de suivre le Pokémon dans la totalité de ses animations.

Conventions du format vérifiées sur le dépôt (voir AUDIT_FORMAT.md) :
  * Offsets.png : 1 pixel par marqueur et par case
      noir  (0,0,0)     -> tête (point 3D projeté, sert d'ancre aux icônes)
      vert  (0,255,0)   -> centre du corps
      rouge (255,0,0)   -> main « droite » de l'entité
      bleu  (0,0,255)   -> main « gauche » de l'entité
  * Lignes de la planche = 8 directions, dans l'ordre
      0=S  1=SE  2=E  3=NE  4=N  5=NO  6=O  7=SO
    (ordre établi empiriquement, cf. AUDIT_FORMAT.md)
  * Colonnes = images de l'animation, une durée par colonne dans AnimData.xml
"""

import math
import numpy as np

# --------------------------------------------------------------------------
# Directions
# --------------------------------------------------------------------------

# Vecteur « vers où regarde le Pokémon », en coordonnées écran (y vers le bas).
DIRECTIONS = [
    (0.0, 1.0),    # 0 S
    (0.7071, 0.7071),   # 1 SE
    (1.0, 0.0),    # 2 E
    (0.7071, -0.7071),  # 3 NE
    (0.0, -1.0),   # 4 N
    (-0.7071, -0.7071),  # 5 NO
    (-1.0, 0.0),   # 6 O
    (-0.7071, 0.7071),  # 7 SO
]
NOMS_DIRECTIONS = ["S", "SE", "E", "NE", "N", "NO", "O", "SO"]

# Raccourci apparent du col selon la direction (vue de profil = plus étroit).
RACCOURCI = [1.00, 0.74, 0.38, 0.74, 1.00, 0.74, 0.38, 0.74]

MARQUEURS = {
    "tete": (0, 0, 0),
    "centre": (0, 255, 0),
    "main_d": (255, 0, 0),
    "main_g": (0, 0, 255),
}

# --------------------------------------------------------------------------
# Énergie du foulard par animation : amplitude du flottement des pans.
# --------------------------------------------------------------------------

ENERGIE = {
    "Idle": 0.30, "Sleep": 0.08, "EventSleep": 0.08, "Laying": 0.10,
    "Sit": 0.16, "Wake": 0.30, "LookUp": 0.26, "Nod": 0.32, "Eat": 0.30,
    "DeepBreath": 0.34, "Pose": 0.42, "Appeal": 0.55, "Dance": 0.75,
    "Walk": 0.72, "Hop": 0.95, "LeapForth": 1.00, "Float": 0.55,
    "Sink": 0.30, "Rotate": 0.62, "Twirl": 0.85, "Shake": 0.70,
    "Attack": 0.90, "Kick": 0.95, "Strike": 0.90, "Swing": 0.85,
    "Shoot": 0.72, "Charge": 0.60, "SpAttack": 0.80, "Slam": 0.95,
    "Ricochet": 1.00, "RearUp": 0.70, "Withdraw": 0.35, "Rumble": 0.70,
    "Double": 0.55, "Head": 0.70, "Pull": 0.60, "Hurt": 0.80, "Pain": 0.70,
    "Cringe": 0.55, "Faint": 0.85, "Trip": 0.95, "Tumble": 1.10,
    "TumbleBack": 1.10, "LostBalance": 0.90, "HitGround": 1.00,
}
ENERGIE_DEFAUT = 0.55


def energie(nom_anim: str) -> float:
    return ENERGIE.get(nom_anim, ENERGIE_DEFAUT)


# --------------------------------------------------------------------------
# Palettes de foulard — teintes « franchise PMD » : saturées, chaudes, lisibles
# --------------------------------------------------------------------------

PALETTES = {
    "rouge_explorateur":  (0xD2, 0x2E, 0x2E),
    "or_guilde":          (0xE3, 0xA5, 0x1E),
    "orange_braise":      (0xE0, 0x6E, 0x22),
    "rose_aurore":        (0xE1, 0x54, 0x8E),
    "violet_crepuscule":  (0x8B, 0x4E, 0xC8),
    "indigo_nuit":        (0x44, 0x51, 0xB0),
    "azur_ciel":          (0x2C, 0x81, 0xD6),
    "cyan_givre":         (0x3D, 0xBF, 0xD8),
    "turquoise_lagon":    (0x1D, 0xA8, 0x94),
    "vert_lierre":        (0x46, 0xA5, 0x45),
    "prune_profonde":     (0x7A, 0x2E, 0x5C),
    "ocre_parchemin":     (0xC8, 0x8A, 0x3C),
    "grenat_ancien":      (0xA8, 0x2B, 0x40),
}

# Léger avantage aux couleurs emblématiques de la franchise.
BONUS_FRANCHISE = {
    "rouge_explorateur": 0.16, "or_guilde": 0.09, "azur_ciel": 0.05,
    "orange_braise": 0.04, "turquoise_lagon": 0.03,
}


def _rgb_hsv(r, g, b):
    import colorsys
    return colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)


def _hsv_rgb(h, s, v):
    import colorsys
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, max(0.0, min(1.0, s)), max(0.0, min(1.0, v)))
    return (int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))


def rampe(base_rgb):
    """4 tons pixel art : contour, ombre, base, lumière."""
    h, s, v = _rgb_hsv(*base_rgb)
    return {
        "lumiere": _hsv_rgb(h + 0.018, s * 0.66, min(1.0, v * 1.26 + 0.06)),
        "base":    tuple(base_rgb),
        "ombre":   _hsv_rgb(h - 0.014, min(1.0, s * 1.10), v * 0.66),
        "contour": _hsv_rgb(h - 0.022, min(1.0, s * 1.02), v * 0.30),
    }


def _luminance(c):
    return (0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]) / 255.0


def choisir_palette(couleurs_corps, deja_prises=()):
    """
    Choisit la teinte de foulard qui s'harmonise le mieux avec un Pokémon :
    teinte nettement distincte de celle du corps, contraste de luminance
    suffisant, et préférence pour les couleurs emblématiques de la franchise.

    couleurs_corps : liste de (rgb, poids) échantillonnée sur le sprite.
    """
    total = sum(p for _, p in couleurs_corps) or 1.0
    teintes = []
    lum_corps = 0.0
    for rgb, p in couleurs_corps:
        h, s, v = _rgb_hsv(*rgb)
        lum_corps += _luminance(rgb) * p / total
        if s > 0.15 and v > 0.12:
            teintes.append((h, s * (p / total)))

    meilleur, note_max = None, -1e9
    for nom, rgb in PALETTES.items():
        h, s, v = _rgb_hsv(*rgb)
        # distance de teinte au corps (0 = identique, 0.5 = opposé)
        if teintes:
            d = min(min(abs(h - hc), 1 - abs(h - hc)) for hc, _ in teintes)
            dp = sum(min(abs(h - hc), 1 - abs(h - hc)) * w for hc, w in teintes)
            dp /= (sum(w for _, w in teintes) or 1.0)
        else:
            d = dp = 0.5
        contraste = abs(_luminance(rgb) - lum_corps)
        note = (2.4 * min(d, 0.28) + 1.5 * dp + 1.9 * min(contraste, 0.45)
                + BONUS_FRANCHISE.get(nom, 0.0))
        if d < 0.075:
            note -= 1.4          # trop proche : le foulard se fondrait
        if contraste < 0.10:
            note -= 0.9
        if nom in deja_prises:
            note -= 0.30         # variété au sein d'une même lignée
        if note > note_max:
            note_max, meilleur = note, nom
    return meilleur, rampe(PALETTES[meilleur])


# --------------------------------------------------------------------------
# Lecture des marqueurs
# --------------------------------------------------------------------------

def marqueurs_case(offsets, x0, y0, w, h):
    """Renvoie les 4 marqueurs (moyenne des pixels de chaque couleur) d'une case."""
    sub = offsets[y0:y0 + h, x0:x0 + w]
    a = sub[..., 3] > 0
    out = {}
    for nom, (r, g, b) in MARQUEURS.items():
        m = a & (sub[..., 0] == r) & (sub[..., 1] == g) & (sub[..., 2] == b)
        ys, xs = np.nonzero(m)
        out[nom] = (float(xs.mean()), float(ys.mean())) if len(xs) else None
    return out


# --------------------------------------------------------------------------
# Géométrie du cou
# --------------------------------------------------------------------------

def _segment_horizontal(masque, y, x):
    """Étendue opaque continue de la ligne y contenant (ou la plus proche de) x."""
    h, w = masque.shape
    y = int(round(max(0, min(h - 1, y))))
    ligne = masque[y]
    if not ligne.any():
        return None
    x = int(round(max(0, min(w - 1, x))))
    if not ligne[x]:
        idx = np.nonzero(ligne)[0]
        x = int(idx[np.argmin(np.abs(idx - x))])
    x0 = x
    while x0 > 0 and ligne[x0 - 1]:
        x0 -= 1
    x1 = x
    while x1 < w - 1 and ligne[x1 + 1]:
        x1 += 1
    return x0, x1


def largeur_ligne(masque, y, x):
    s = _segment_horizontal(masque, y, x)
    return None if s is None else (s[1] - s[0] + 1, s)


def point_cou(masque, mk, reglage, tc, direction=0):
    """
    Position du cou dans la case.

    Le marqueur noir d'Offsets.png est la tête en 3D projetée : elle bascule
    fortement selon la direction (Salamèche : y=16 de face, y=8 de dos). Le cou
    n'a pas ce basculement, il reste sur l'axe du corps. On retire donc le biais
    de projection propre à la direction (mesuré par pipeline.biais_direction),
    ce qui ramène l'ancre sur l'axe tout en gardant le mouvement réel de la
    tête image par image, puis on descend d'une fraction de la taille du corps.
    """
    tete, centre = mk.get("tete"), mk.get("centre")
    if tete is None and centre is None:
        return None
    if tete is None:
        tete = centre
    if centre is None:
        centre = tete

    bi = reglage.get("biais") or [(0.0, 0.0)] * 8
    bx0, by0 = bi[direction % 8] if len(bi) == 8 else (0.0, 0.0)

    ax = tete[0] - bx0
    ay = tete[1] - by0

    fx, fy = DIRECTIONS[direction % 8]
    av = reglage.get("avance", 0.11) * tc

    # Deuxième ancre, indépendante : la ligne d'épaules, milieu des deux
    # marqueurs de mains. Elle suit l'animation image par image et reste
    # juste sous le cou, y compris chez les Pokémon à très grosse tête.
    cou_x = ax
    cou_y = ay + reglage.get("descente_cou", 0.10) * tc * reglage.get("descente", 1.0)
    mg, md = mk.get("main_g"), mk.get("main_d")
    w_ep = reglage.get("poids_epaules", 0.45)
    if mg is not None and md is not None and w_ep > 0:
        ep_x = (mg[0] + md[0]) / 2.0
        ep_y = (mg[1] + md[1]) / 2.0 - reglage.get("releve_epaules", 0.13) * tc
        cou_x = cou_x * (1 - w_ep * 0.7) + ep_x * (w_ep * 0.7)
        cou_y = cou_y * (1 - w_ep) + ep_y * w_ep

    bx = cou_x + fx * av + reglage.get("dx", 0.0)
    by = cou_y + fy * av * 0.40 + reglage.get("dy", 0.0)

    fen = int(reglage.get("fenetre_cou", 2))
    meilleur = None
    for dy in range(-fen, fen + 1):
        r = largeur_ligne(masque, by + dy, bx)
        if r is None:
            continue
        lg, seg = r
        note = lg + 3.2 * abs(dy)
        if meilleur is None or note < meilleur[0]:
            meilleur = (note, by + dy, seg)
    if meilleur is None:
        return None
    _, ny, (x0, x1) = meilleur
    return bx, ny, x0, x1


# --------------------------------------------------------------------------
# Rastérisation
# --------------------------------------------------------------------------

class Toile:
    """Petit tampon RGBA avec pose de pixels prioritaires (z simple)."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = np.zeros((h, w, 4), dtype=np.uint8)
        self.z = np.full((h, w), -1, dtype=np.int16)

    def poser(self, x, y, couleur, z=0, y_max=None):
        if y_max is not None and y > y_max:
            return
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h and z >= self.z[y, x]:
            self.px[y, x, 0:3] = couleur
            self.px[y, x, 3] = 255
            self.z[y, x] = z


def _signe(v):
    return 1.0 if v > 0 else (-1.0 if v < 0 else 0.0)


def _norm(vx, vy):
    n = math.hypot(vx, vy)
    return (vx / n, vy / n) if n > 1e-6 else (0.0, 1.0)


def dessiner_foulard(masque, mk, direction, phase, nrj, pal, reglage, taille_corps,
                     infos=None):
    """
    Dessine le foulard d'une case et renvoie la toile RGBA (transparente ailleurs).

    masque       : silhouette booléenne du Pokémon dans la case
    mk           : marqueurs de la case
    direction    : 0..7 (0=S, 2=E, 4=N, 6=O)
    phase        : avancement 0..1 dans l'animation (flottement des pans)
    nrj          : énergie de l'animation
    pal          : rampe de 4 couleurs
    taille_corps : largeur médiane du sprite, sert d'échelle
    """
    h, w = masque.shape
    toile = Toile(w, h)
    lignes = np.nonzero(masque.any(axis=1))[0]
    y_sol = float(lignes[-1]) if len(lignes) else h - 1.0

    tc = taille_corps * reglage.get("echelle", 1.0)
    cou = point_cou(masque, mk, reglage, tc, direction)
    if cou is None:
        return toile.px
    nx, ny, x0, x1 = cou
    if infos is not None:
        infos.update(nx=nx, ny=ny, run=(x0, x1), y_sol=y_sol)

    fx, fy = DIRECTIONS[direction % 8]

    # --- échelle du trait ---------------------------------------------------
    k = max(0.75, min(3.0, tc / 16.0))
    if tc < 19:
        ep = 2
    elif tc < 27:
        ep = 3
    elif tc < 38:
        ep = 4
    else:
        ep = 5

    # Largeur du col : mesurée sur l'écartement des marqueurs de mains du
    # Pokémon (stable, propre au format PMD), raccourcie selon la direction,
    # puis bornée par la silhouette réelle de la case.
    lc = reglage.get("largeur_cou", tc * 0.55)
    demi = lc / 2.0 * RACCOURCI[direction % 8] * reglage.get("largeur", 1.0)
    demi = min(demi, (x1 - x0 + 1) / 2.0)
    demi = max(demi, 1.5)
    prof = abs(fx)
    cx = (x0 + x1) / 2.0
    w_cx = 0.45 * (1.0 - prof)
    bx = nx * (1.0 - w_cx) + cx * w_cx

    amp_arc = (0.9 + 0.55 * ep) * abs(fy) + 0.35   # creux de face, bombé de dos

    contour, ombre, base, lumiere = (pal["contour"], pal["ombre"],
                                     pal["base"], pal["lumiere"])
    if infos is not None:
        infos.update(bx=bx, demi=demi, ep=ep, k=k)

    # --- bandeau, plaqué sur la silhouette ----------------------------------
    xd, xf = int(math.floor(bx - demi)), int(math.ceil(bx + demi))
    for x in range(xd, xf + 1):
        if not (0 <= x < w):
            continue
        u = (x - bx) / max(demi, 1e-6)
        if abs(u) > 1.02:
            continue
        arc = -_signe(fy) * (u * u - 0.36) * amp_arc + fx * u * 0.45
        # les extrémités se replient légèrement vers le bas
        ytop = ny + arc - (ep - 1) / 2.0
        bord = abs(u) > 0.80
        for i in range(ep):
            y = int(round(ytop)) + i
            if not (0 <= y < h) or not masque[y, x]:
                continue
            if bord:
                c = ombre if i < ep - 1 else contour
            elif i == 0 and ep >= 3:
                c = lumiere if u < 0.30 else base
            elif i == ep - 1 and ep >= 3:
                c = contour
            elif i == ep - 2 and ep >= 4:
                c = ombre
            else:
                c = base if (i == 0 or u > 0.30) else lumiere
            toile.poser(x, y, c, z=3)
        # liseré bas quand le bandeau est fin
        if ep == 2:
            y = int(round(ytop)) + ep
            if 0 <= y < h and masque[y, x]:
                toile.poser(x, y, ombre if not bord else contour, z=2)

    # --- nœud ---------------------------------------------------------------
    vis_noeud = (1.0 + fy) / 2.0                       # 1 de face, 0 de dos
    if vis_noeud > 0.20:
        rn = 1 if k < 1.35 else (2 if k < 2.2 else 3)
        # le nœud est ramené sur la silhouette : sur les vues de profil, le
        # point « devant le cou » peut tomber dans le vide à côté du corps.
        kx = ky = None
        for t in (1.0, 0.72, 0.45, 0.20, 0.0):
            cx_ = bx + (fx * demi * 0.55 + (0.0 if abs(fx) < 0.3 else fx * 0.5)) * t
            cy_ = ny + (fy * (ep * 0.45) + ep * 0.45 + rn * 0.25) * t
            xi, yi = int(round(cx_)), int(round(cy_))
            if 0 <= xi < w and 0 <= yi < h and masque[yi, xi]:
                kx, ky = cx_, cy_
                break
        if kx is not None:
            for dy in range(-rn, rn + 1):
                for dx in range(-rn, rn + 1):
                    if abs(dx) + abs(dy) > rn + max(0, rn - 1):
                        continue
                    x, y = int(round(kx)) + dx, int(round(ky)) + dy
                    if not (0 <= x < w and 0 <= y < h) or not masque[y, x]:
                        continue
                    if dx < 0 and dy < 0:
                        c = lumiere
                    elif dx >= rn or dy >= rn:
                        c = ombre
                    else:
                        c = base
                    toile.poser(x, y, c, z=5)

    # --- pans ---------------------------------------------------------------
    vis_pans = (1.0 - fy) / 2.0                        # 0 de face, 1 de dos
    if vis_pans < 0.28:
        # De face, les pans passent derrière le corps : seules leurs pointes
        # dépassent de part et d'autre du cou.
        lg = max(1, int(round((1.0 + 1.4 * nrj) * k)))
        for signe in (-1, 1):
            sx = bx + signe * demi * 0.90
            sy = ny + ep * 0.30
            for i in range(lg):
                fl = math.sin(phase * 2 * math.pi + i * 0.85 + signe) * nrj
                x = sx + signe * (0.75 + 0.55 * i + fl * 0.35)
                y = sy + i * 0.75
                if y > y_sol + 0.5:
                    break
                toile.poser(x, y, base if i < lg - 1 else ombre, z=1, y_max=y_sol + 1)
        if infos is not None:
            infos['bandeau'] = toile.z >= 3
        return toile.px

    # Deux rubans distincts qui partent de la nuque, s'écartent en tombant et
    # ondulent d'autant plus que l'animation est vive.
    dx_t, dy_t = _norm(-fx * 0.80, 0.85)
    ang0 = math.atan2(dy_t, dx_t)
    lg = max(4, int(round((5.5 + 6.5 * nrj) * k
                          * (0.55 + 0.60 * vis_pans) * (1.0 - 0.30 * prof))))
    ecart = demi * 0.78
    # un pan flotte, mais ne balaie pas le sol sous les pieds
    marge_sol = 0.4 + 1.1 * nrj * k

    for signe in (-1, 1):
        px_ = bx - fx * (demi * 0.55 + 0.9) + signe * ecart
        py_ = ny + ep * 0.55
        ang = ang0 + signe * 0.26
        for i in range(lg):
            s = i / max(lg - 1, 1)
            fl = math.sin(phase * 2 * math.pi + i * 0.50 + signe * 1.7)
            ang += fl * nrj * 0.15 * (0.30 + s) + signe * 0.035
            px_ += math.cos(ang)
            py_ += math.sin(ang) * 0.95
            if py_ > y_sol + marge_sol:
                break
            perp = (-math.sin(ang), math.cos(ang))
            toile.poser(px_, py_, base if s < 0.72 else ombre, z=1, y_max=y_sol + 1)
            if k >= 1.55 and s < 0.86:
                toile.poser(px_ + perp[0], py_ + perp[1], ombre, z=1, y_max=y_sol + 1)
            if k >= 2.30 and s < 0.55:
                toile.poser(px_ - perp[0], py_ - perp[1], lumiere, z=1, y_max=y_sol + 1)
        toile.poser(px_, py_ + 1, contour, z=0, y_max=y_sol + 1)

    if infos is not None:
        infos['bandeau'] = toile.z >= 3
    return toile.px
