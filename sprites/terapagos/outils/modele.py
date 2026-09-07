# -*- coding: utf-8 -*-
"""Modèle pixel de Terapagos — Forme Teracristal.

Construction fidèle au design officiel : petite tortue au corps ivoire, tête
ronde blanche à joues arrondies, yeux ambre, dôme/carapace de cristal bleu
translucide à facettes portant sept pointes de cristal, liseré doré à la base
de la carapace, quatre pattes courtes, petite queue cristalline.

Le rendu suit les conventions PMD : vue 3/4 plongeante, 8 directions,
contour dur, 3 tons par matière, aucun anti-aliasing.
"""
import math
from moteur import Toile

# Canvas standard du set (Terapagos est un « gros » sprite PMD).
L = H = 48
# Point d'ancrage : centre des pieds, identique pour TOUTES les animations.
ANCRE_X, ANCRE_Y = 24, 40

DIRS = ["S", "SE", "E", "NE", "N", "NO", "O", "SO"]
# vecteur écran (x vers la droite, y vers le bas) par direction, 3/4 plongé
VEC = {
    "S":  (0.0, 1.0), "SE": (0.80, 0.62), "E": (1.0, 0.0), "NE": (0.80, -0.62),
    "N":  (0.0, -1.0), "NO": (-0.80, -0.62), "O": (-1.0, 0.0), "SO": (-0.80, 0.62),
}
# 1 = de face (tête visible), -1 = de dos
FACE = {"S": 1.0, "SE": 0.55, "E": 0.0, "NE": -0.55, "N": -1.0,
        "NO": -0.55, "O": 0.0, "SO": 0.55}


def _facettes(t, cx, cy, rx, ry, brille):
    """Facettes du dôme de cristal : bandes obliques + éclat fixe."""
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            if t.get(x, y) not in ("cri_bas", "cri_mid", "cri_hau", "cri_omb"):
                continue
            u = (x - cx) / max(rx, 1)
            v = (y - cy) / max(ry, 1)
            # dégradé lumière haut-gauche (convention PMD)
            lum = -0.7 * u - 0.9 * v
            # découpe en facettes : quantification par bandes
            bande = math.floor((u * 2.2 + v * 1.2) * 1.05)
            lum += 0.13 * ((bande % 3) - 1)
            if lum > 0.95:
                c = "cri_ecl"
            elif lum > 0.42:
                c = "cri_hau"
            elif lum > -0.05:
                c = "cri_mid"
            elif lum > -0.55:
                c = "cri_bas"
            else:
                c = "cri_omb"
            t.set(x, y, c)
    # éclat spéculaire net, deux pixels, jamais dégradé
    if brille:
        t.set(int(cx - rx * 0.42), int(cy - ry * 0.45), "cri_ecl")
        t.set(int(cx - rx * 0.42) + 1, int(cy - ry * 0.45), "cri_ecl")
        t.set(int(cx - rx * 0.30), int(cy - ry * 0.60), "cri_ecl")


def _aretes(t, cx, cy, rx, ry):
    """Arêtes internes du cristal (traits fins, couleur d'outline interne)."""
    for ang in (-118, -22):
        a = math.radians(ang)
        x1 = cx + math.cos(a) * rx * 0.82
        y1 = cy + math.sin(a) * ry * 0.82
        avant = []
        t.ligne(cx + math.cos(a) * rx * 0.2, cy + math.sin(a) * ry * 0.2, x1, y1, "cont_cri")
        del avant


def _pointe(t, x, y, h, l, sens=1):
    """Pointe de cristal (prisme triangulaire) plantée sur la carapace."""
    for i in range(int(h)):
        w = max(0, int(round(l * (1 - i / h))))
        for dx in range(-w, w + 1):
            c = "cri_hau" if dx <= 0 else "cri_bas"
            if dx == -w and w > 0:
                c = "cri_ecl"
            t.set(x + dx, y - i, c)
    t.set(x, y - int(h), "cri_ecl")


def tete(t, cx, cy, d, expr="neutre", clign=0.0, taille=1.0):
    """Tête ivoire + yeux ambre. expr pilote sourcils/bouche/pupilles."""
    f = FACE[d]
    vx = VEC[d][0]
    rx = 7.4 * taille
    ry = 6.6 * taille
    t.disque(cx, cy, rx, ry, "corp_mid")
    # volume : bas et côté opposé à la lumière plus sombres
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            if t.get(x, y) != "corp_mid":
                continue
            u, v = (x - cx) / rx, (y - cy) / ry
            lum = -0.55 * u - 0.85 * v
            if lum > 0.55:
                t.set(x, y, "corp_hau")
            elif lum < -0.45:
                t.set(x, y, "corp_omb")
            elif lum < -0.05:
                t.set(x, y, "corp_bas")
    # petite crête de cristal frontale (présente sur le design officiel)
    if f > -0.2:
        t.set(int(cx), int(cy - ry), "cri_hau")
        t.set(int(cx - 1), int(cy - ry + 1), "cri_mid")
        t.set(int(cx + 1), int(cy - ry + 1), "cri_bas")
    if f <= -0.2:
        return  # de dos : pas de visage
    # --- yeux -------------------------------------------------------------
    ec = 3.2 * taille * (0.45 + 0.55 * abs(f))
    dep = vx * 1.6
    oy = cy - 0.4 * taille
    for s in (-1, 1):
        ox = cx + s * ec + dep
        if d in ("E", "O") and s * (1 if d == "E" else -1) < 0:
            continue  # œil caché de profil
        ouvert = 1.0 - clign
        if expr in ("dodo", "ko"):
            ouvert = 0.0
        hh = 2.4 * taille * ouvert
        if hh < 0.7:
            t.ligne(ox - 1, oy, ox + 1, oy, "contour")
            continue
        t.disque(ox, oy, 1.6 * taille, hh, "oeil_bl")
        px = ox + (0.6 if expr in ("colere", "determination") else 0.0) * s
        py = oy + (0.5 if expr in ("triste", "peur") else 0.0)
        t.disque(px, py, 1.2 * taille, hh * 0.85, "oeil_ir")
        t.disque(px, py + 0.3, 0.7 * taille, hh * 0.5, "oeil_pu")
        t.set(int(px - 1), int(py - 1), "oeil_bl")
        if expr == "surprise":
            t.disque(px, py, 0.9, hh * 0.45, "oeil_pu")
        if expr in ("colere", "determination"):
            t.ligne(ox - 2, oy - 2.5, ox + 1.5 * s, oy - 1.5, "contour")
        if expr == "triste":
            t.ligne(ox - 2 * s, oy - 2.5, ox + 2 * s, oy - 1.5, "contour")
        if expr == "peur":
            t.set(int(ox + 2 * s), int(oy + 2), "cri_mid")
    # --- bouche ------------------------------------------------------------
    by = cy + 2.6 * taille
    bx = cx + dep * 0.7
    if expr in ("joie", "determination"):
        t.ligne(bx - 2, by - 1, bx - 1, by, "bouche")
        t.ligne(bx - 1, by, bx + 1, by, "bouche")
        t.ligne(bx + 1, by, bx + 2, by - 1, "bouche")
    elif expr in ("triste", "peur"):
        t.ligne(bx - 1, by, bx, by - 1, "bouche")
        t.ligne(bx, by - 1, bx + 1, by, "bouche")
    elif expr == "surprise":
        t.disque(bx, by, 1.1, 1.3, "bouche")
    elif expr == "colere":
        t.ligne(bx - 2, by, bx + 2, by, "bouche")
        t.set(int(bx), int(by - 1), "bouche")
    elif expr in ("dodo",):
        t.disque(bx, by, 0.9, 0.9, "bouche")
    else:
        t.ligne(bx - 1, by, bx + 1, by, "bouche")


def patte(t, x, y, lev=0.0, arriere=False):
    h = 3 if not arriere else 2
    y = y - lev
    t.disque(x, y, 2.0, h * 0.75, "corp_bas")
    t.disque(x, y - 0.6, 1.7, h * 0.6, "corp_mid")
    t.set(int(x), int(y + 1), "corp_omb")


def terapagos(d="S", phase=0.0, expr="neutre", pas=0.0, saut=0.0,
              incl=0.0, ecrase=0.0, clign=0.0, retrait=0.0, ech=1.0):
    """Rend une frame complète.

    d       : direction PMD
    phase   : 0..1 respiration / cycle
    pas     : 0..1 cycle de marche (alternance des pattes)
    saut    : décalage vertical (px, positif = en l'air)
    incl    : inclinaison horizontale (recul de dégâts, élan d'attaque)
    ecrase  : 0..1 écrasement vertical (anticipation, impact)
    retrait : 0..1 tête rentrée dans la carapace (peur, sommeil, KO)
    """
    t = Toile(L, H)
    f = FACE[d]
    vx, vy = VEC[d]
    resp = math.sin(phase * 2 * math.pi)
    cy = ANCRE_Y - 13 - saut + resp * 0.5
    cx = ANCRE_X + incl
    sy = (1.0 - 0.18 * ecrase) * ech
    sx = (1.0 + 0.12 * ecrase) * ech

    # --- pattes (derrière le corps quand on va vers le nord) --------------
    lev_a = max(0.0, math.sin(pas * 2 * math.pi)) * 2.0
    lev_b = max(0.0, math.sin(pas * 2 * math.pi + math.pi)) * 2.0
    py = ANCRE_Y - 1 + resp * 0.3 - saut
    ecart = 8.5 * sx
    patte(t, cx - ecart, py - 2, lev_a, arriere=True)
    patte(t, cx + ecart, py - 2, lev_b, arriere=True)

    # --- corps ivoire sous la carapace ------------------------------------
    bry = 5.6 * sy
    brx = 11.0 * sx
    t.disque(cx, cy + 6 * sy, brx, bry, "corp_mid")
    for y in range(int(cy), H):
        for x in range(L):
            if t.get(x, y) == "corp_mid":
                u = (x - cx) / brx
                v = (y - (cy + 6 * sy)) / bry
                l = -0.6 * u - 0.8 * v
                if l > 0.45:
                    t.set(x, y, "corp_hau")
                elif l < -0.5:
                    t.set(x, y, "corp_omb")
                elif l < -0.05:
                    t.set(x, y, "corp_bas")

    # --- pattes avant ------------------------------------------------------
    patte(t, cx - ecart * 0.85, py, lev_b)
    patte(t, cx + ecart * 0.85, py, lev_a)

    # --- queue cristalline -------------------------------------------------
    if f < 0.3:
        qx = cx - vx * 10 * sx
        qy = cy + 6 * sy - vy * 2
        t.disque(qx, qy, 2.2, 1.6, "cri_mid")
        t.set(int(qx - 1), int(qy - 1), "cri_hau")

    # --- tête (derrière la carapace quand on regarde vers le nord) --------
    hx = cx + vx * 10.0 * sx
    hy = cy + vy * 2.2 + 9.5 * sy + retrait * 4.0
    tt = (1.0 - 0.35 * retrait) * ech
    if f <= 0.0 and retrait < 0.95:
        tete(t, hx, hy, d, expr, clign, tt)

    # --- carapace / dôme de cristal ----------------------------------------
    drx = 13.5 * sx
    dry = 8.0 * sy
    dcy = cy - 1.0
    t.disque(cx, dcy, drx, dry, "cri_mid")
    _facettes(t, cx, dcy, drx, dry, True)
    _aretes(t, cx, dcy, drx, dry)
    # liseré doré à la base du dôme
    for x in range(int(cx - drx), int(cx + drx) + 1):
        for y in range(int(dcy), int(dcy + dry) + 2):
            if t.get(x, y) in ("cri_bas", "cri_omb", "cri_mid") and \
               t.get(x, y + 1) not in ("cri_bas", "cri_omb", "cri_mid",
                                        "cri_hau", "cri_ecl"):
                t.set(x, y, "or_mid")
                t.set(x, y - 1, "or_hau" if x < cx else "or_omb")
    # sept pointes de cristal (design officiel : couronne dorsale)
    pointes = [(-0.95, 0.28, 2), (-0.70, -0.30, 3), (-0.30, -0.58, 3),
               (0.30, -0.58, 3), (0.70, -0.30, 3), (0.95, 0.28, 2)]
    for u, v, hh in pointes:
        px = cx + u * drx * 0.92
        py = dcy + v * dry * 0.92 + 1
        _pointe(t, px, py, hh * sy + 1, 2.0)
    _pointe(t, cx, dcy - dry * 0.70, 4 * sy, 2.2)

    # tête au premier plan lorsqu'elle est tournée vers la caméra
    if f > 0.0 and retrait < 0.95:
        tete(t, hx, hy, d, expr, clign, tt)

    # contour dur global
    t.contourner("contour")
    return t


def ombre_portee(saut=0.0, ecrase=0.0):
    """Ombre elliptique PMD, ancrée au sol, indépendante du saut."""
    pts = []
    rx = 11 - saut * 0.25 + ecrase
    ry = 3.4 - saut * 0.08
    for y in range(int(ANCRE_Y - ry) - 1, int(ANCRE_Y + ry) + 2):
        for x in range(int(ANCRE_X - rx) - 1, int(ANCRE_X + rx) + 2):
            u = (x - ANCRE_X) / rx
            v = (y - ANCRE_Y) / max(ry, 0.5)
            if u * u + v * v <= 1:
                pts.append((x, y))
    return pts
