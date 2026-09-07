# -*- coding: utf-8 -*-
"""Modèle pixel de Terapagos — Forme Teracristal, d'après l'artwork officiel.

Anatomie réelle (référence fournie par l'utilisateur) :
  - carapace BASSE et LARGE en vitrail : cellules polygonales sombres
    (bleu nuit, violet, rose, vert, cyan) séparées par des nervures menthe
    claires ; un motif d'éclair jaune sur une cellule du dessus ;
  - une fourrure vaporeuse menthe/crème débordant tout autour de la carapace,
    en mèches pointues, plus fournie à l'arrière ;
  - une petite tête bleu nuit basse à l'avant, œil cerclé de rouge à iris
    cyan, bouche en zigzag ;
  - une longue queue-panache fourchue en fourrure claire, relevée à l'arrière ;
  - pas de pattes visibles : le corps repose au sol, la fourrure masque la base.

Vue PMD 3/4 plongeante, 8 directions, contour dur, aucun anti-aliasing.
"""
import math
from moteur import Toile

L = H = 48
ANCRE_X, ANCRE_Y = 24, 40

DIRS = ["S", "SE", "E", "NE", "N", "NO", "O", "SO"]
LIGNES = DIRS
VEC = {
    "S": (0.0, 1.0), "SE": (0.80, 0.62), "E": (1.0, 0.0), "NE": (0.80, -0.62),
    "N": (0.0, -1.0), "NO": (-0.80, -0.62), "O": (-1.0, 0.0), "SO": (-0.80, 0.62),
}
FACE = {"S": 1.0, "SE": 0.55, "E": 0.0, "NE": -0.55, "N": -1.0,
        "NO": -0.55, "O": 0.0, "SO": 0.55}

CELL = ["vit_bas", "vit_mid", "vit_vio", "vit_omb", "vit_ros", "vit_cya",
        "vit_ver", "vit_mid", "vit_vio", "vit_bas", "vit_cya", "vit_omb"]


# --------------------------------------------------------------- fourrure ---
def fourrure(t, cx, cy, rx, ry, phase, arriere=False, ampleur=1.0):
    """Halo de fourrure vaporeuse : mèches pointues autour de la carapace."""
    n = 26
    for i in range(n):
        a = 2 * math.pi * i / n
        ca, sa = math.cos(a), math.sin(a)
        # mèches plus longues à l'arrière et sur les flancs
        lon = 4.2 + 3.0 * abs(ca) + 2.0 * max(0.0, -sa)
        lon *= ampleur * (0.82 + 0.18 * math.sin(a * 3 + phase * 6.283))
        x0 = cx + ca * rx
        y0 = cy + sa * ry
        x1 = cx + ca * (rx + lon)
        y1 = cy + sa * (ry + lon * 0.62)
        # mèche = triangle fin, dessinée en dégradé de 3 tons
        pas = max(1, int(max(abs(x1 - x0), abs(y1 - y0))))
        for k in range(pas + 1):
            u = k / max(pas, 1)
            x = x0 + (x1 - x0) * u
            y = y0 + (y1 - y0) * u
            w = max(0, (1.0 - u) * 1.9)
            if u > 0.72:
                c = "four_cre"
            elif sa < -0.15:
                c = "four_hau" if u > 0.35 else "four_mid"
            elif sa > 0.35:
                c = "four_omb" if u < 0.4 else "four_bas"
            else:
                c = "four_bas" if u < 0.5 else "four_mid"
            for dx in range(-int(w), int(w) + 1):
                for dy in range(-int(w * 0.7), int(w * 0.7) + 1):
                    t.set(x + dx, y + dy, c)
    # corps de fourrure, anneau plein qui relie les mèches
    for y in range(int(cy - ry - 6), int(cy + ry + 6)):
        for x in range(int(cx - rx - 8), int(cx + rx + 8)):
            u = (x - cx) / (rx + 2.2)
            v = (y - cy) / (ry + 2.0)
            d = u * u + v * v
            if 0.62 <= d <= 1.0 and t.get(x, y) is None:
                lum = -0.6 * u - 0.85 * v
                t.set(x, y, "four_hau" if lum > 0.45 else
                      ("four_mid" if lum > -0.1 else
                       ("four_bas" if lum > -0.55 else "four_omb")))


# --------------------------------------------------------------- carapace ---
def carapace(t, cx, cy, rx, ry, eclair=True):
    """Dôme bas en vitrail : cellules polygonales sombres + nervures menthe."""
    t.disque(cx, cy, rx, ry, "vit_bas")
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            if t.get(x, y) != "vit_bas":
                continue
            u = (x - cx) / rx
            v = (y - cy) / ry
            # partition en cellules : grille irrégulière quantifiée
            a = math.atan2(v, u)
            r = math.sqrt(u * u + v * v)
            sect = int((a + math.pi) / (2 * math.pi) * 8) % 8
            couronne = 0 if r < 0.46 else 1
            idx = (sect + couronne * 5) % len(CELL)
            c = CELL[idx]
            # éclairage global haut-gauche, deux crans seulement
            lum = -0.55 * u - 0.8 * v
            if lum > 0.5 and c in ("vit_omb", "vit_bas"):
                c = "vit_mid"
            elif lum < -0.5 and c in ("vit_mid", "vit_cya", "vit_ver"):
                c = "vit_bas"
            t.set(x, y, c)
    # nervures menthe entre cellules (traits nets de 1 px)
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            c = t.get(x, y)
            if c is None or not c.startswith("vit"):
                continue
            for dx, dy in ((1, 0), (0, 1)):
                v2 = t.get(x + dx, y + dy)
                if v2 is not None and v2.startswith("vit") and v2 != c:
                    t.set(x, y, "nerv_hau" if y < cy else "nerv_mid")
    # cerclage menthe du pourtour de la carapace
    for y in range(int(cy - ry) - 2, int(cy + ry) + 3):
        for x in range(int(cx - rx) - 2, int(cx + rx) + 3):
            c = t.get(x, y)
            if c is None or not c.startswith(("vit", "nerv")):
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = t.get(x + dx, y + dy)
                if n is None or not n.startswith(("vit", "nerv", "or_")):
                    t.set(x, y, "nerv_hau" if y < cy else "nerv_mid")
                    break
    # motif d'éclair jaune sur une cellule du dessus (détail officiel)
    if eclair:
        ex, ey = cx + rx * 0.06, cy - ry * 0.34
        for dx, dy, c in ((0, -2, "or_hau"), (-1, -1, "or_mid"), (0, -1, "or_hau"),
                          (-1, 0, "or_mid"), (0, 0, "or_mid"), (1, 0, "or_hau"),
                          (0, 1, "or_mid"), (1, 1, "or_omb"), (0, 2, "or_omb")):
            t.set(ex + dx, ey + dy, c)
    # deux éclats de facette, nets
    t.set(cx - rx * 0.45, cy - ry * 0.42, "vit_ecl")
    t.set(cx - rx * 0.45 + 1, cy - ry * 0.42, "vit_ecl")
    t.set(cx + rx * 0.40, cy - ry * 0.10, "vit_ecl")


# ------------------------------------------------------------------- tête ---
def tete(t, cx, cy, d, expr="neutre", clign=0.0, taille=1.0):
    """Petite tête bleu nuit, œil cerclé de rouge à iris cyan."""
    f = FACE[d]
    vx = VEC[d][0]
    rx = 6.8 * taille
    ry = 5.6 * taille
    t.disque(cx, cy, rx, ry, "tet_mid")
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            if t.get(x, y) != "tet_mid":
                continue
            u, v = (x - cx) / rx, (y - cy) / ry
            lum = -0.5 * u - 0.85 * v
            if lum > 0.5:
                t.set(x, y, "tet_hau")
            elif lum < -0.35:
                t.set(x, y, "tet_omb")
    if f <= -0.25:
        return  # de dos : pas de visage
    # --- yeux : anneau rouge + iris cyan + pupille --------------------------
    ec = 2.9 * taille * (0.4 + 0.6 * abs(f))
    dep = vx * 1.4
    oy = cy - 0.3 * taille
    for s in (-1, 1):
        if d in ("E", "O") and s * (1 if d == "E" else -1) < 0:
            continue
        ox = cx + s * ec + dep
        ouvert = 1.0 - clign
        if expr in ("dodo", "ko"):
            ouvert = 0.0
        hh = 2.6 * taille * ouvert
        if hh < 0.8:
            t.ligne(ox - 1, oy, ox + 1, oy, "oeil_rou")
            continue
        t.disque(ox, oy, 2.3 * taille, hh, "oeil_rou")
        px = ox + (0.5 * s if expr in ("colere", "determination") else 0.0)
        py = oy + (0.4 if expr in ("triste", "peur") else 0.0)
        t.disque(px, py, 1.5 * taille, hh * 0.72, "oeil_cya")
        t.disque(px, py + 0.2, 1.0 * taille, hh * 0.5, "oeil_ver")
        t.disque(px, py + 0.3, 0.6 * taille, hh * 0.34, "oeil_pu")
        t.set(int(px - 1), int(py - 1), "oeil_bl")
        if expr in ("colere", "determination"):
            t.ligne(ox - 2, oy - 3, ox + 2 * s, oy - 2, "tet_omb")
        if expr == "triste":
            t.ligne(ox - 2 * s, oy - 3, ox + 2 * s, oy - 2, "tet_omb")
        if expr == "peur":
            t.set(int(ox + 2 * s), int(oy + 2), "four_hau")
    # --- bouche en zigzag (détail officiel) ---------------------------------
    by = cy + 2.6 * taille
    bx = cx + dep * 0.7
    if expr in ("joie", "determination"):
        for i, (dx, dy) in enumerate(((-3, 0), (-2, 1), (-1, 1), (0, 1),
                                      (1, 1), (2, 1), (3, 0))):
            t.set(bx + dx, by + dy, "bouche")
    elif expr in ("triste", "peur"):
        for dx, dy in ((-2, 1), (-1, 0), (0, 0), (1, 0), (2, 1)):
            t.set(bx + dx, by + dy, "bouche")
    elif expr == "surprise":
        t.disque(bx, by, 1.2, 1.3, "bouche")
    elif expr == "colere":
        for dx, dy in ((-3, 1), (-2, 0), (-1, 1), (0, 0), (1, 1), (2, 0), (3, 1)):
            t.set(bx + dx, by + dy, "bouche")
    elif expr == "dodo":
        t.disque(bx, by, 0.9, 0.9, "bouche")
    else:  # zigzag neutre caractéristique
        for dx, dy in ((-3, 0), (-2, 1), (-1, 0), (0, 1), (1, 0), (2, 1), (3, 0)):
            t.set(bx + dx, by + dy, "bouche")


# ------------------------------------------------------------------ queue ---
def queue(t, cx, cy, d, phase, ech=1.0):
    """Queue-panache fourchue en fourrure claire, relevée à l'arrière."""
    vx, vy = VEC[d]
    bx = cx - vx * 12 * ech
    by = cy - vy * 3 * ech + 1
    ond = math.sin(phase * 2 * math.pi) * 1.2
    # direction de fuite = opposée au regard, projetée, avec relevé constant
    fx, fy = -vx, -vy * 0.62
    n = math.hypot(fx, fy) or 1.0
    fx, fy = fx / n, fy / n
    px_, py_ = -fy, fx  # perpendiculaire, pour écarter les deux mèches
    for s_, lon in ((-1, 6.0), (1, 5.0)):
        for k in range(int(lon)):
            u = k / lon
            ax = bx + fx * (2.0 + k * 1.15) * ech + px_ * s_ * (1.0 + u * 3.2)
            ay = by + fy * (2.0 + k * 1.15) * ech + py_ * s_ * (1.0 + u * 3.2) \
                 - (1.2 + k * 0.55) * ech + ond * u
            c = "four_cre" if u > 0.62 else ("four_hau" if u > 0.28 else "four_mid")
            w = max(0, int(round(1.9 * (1 - u * 0.65))))
            for i in range(-w, w + 1):
                for j in range(-1, 1):
                    t.set(ax + i, ay + j, c)


# ------------------------------------------------------------------ rendu ---
def terapagos(d="S", phase=0.0, expr="neutre", pas=0.0, saut=0.0,
              incl=0.0, ecrase=0.0, clign=0.0, retrait=0.0, ech=1.0):
    t = Toile(L, H)
    f = FACE[d]
    vx, vy = VEC[d]
    resp = math.sin(phase * 2 * math.pi)
    # léger balancement de marche (le corps rampe, il ne marche pas sur pattes)
    balance = math.sin(pas * 2 * math.pi) * 0.9
    cy = ANCRE_Y - 10 - saut + resp * 0.45
    cx = ANCRE_X + incl + balance * 0.5
    sy = (1.0 - 0.16 * ecrase) * ech
    sx = (1.0 + 0.10 * ecrase) * ech

    crx = 13.2 * sx
    cry = 7.6 * sy
    ccy = cy - 1.0

    # queue derrière tout
    if f > -0.6:
        queue(t, cx, ccy, d, phase + pas, ech)

    # tête derrière la carapace si le sujet regarde vers le nord
    hx = cx + vx * 13.0 * sx
    hy = cy + vy * 2.4 + 5.2 * sy + retrait * 3.5
    tt = (1.0 - 0.30 * retrait) * ech
    if f <= 0.0 and retrait < 0.9:
        tete(t, hx, hy, d, expr, clign, tt)

    # fourrure vaporeuse (sous la carapace, débordant tout autour)
    fourrure(t, cx, ccy + 1.2, crx * 0.92, cry * 0.95, phase,
             ampleur=ech * (1.0 + 0.12 * ecrase))

    # carapace en vitrail
    carapace(t, cx, ccy, crx, cry)

    # tête au premier plan si tournée vers la caméra
    if f > 0.0 and retrait < 0.9:
        tete(t, hx, hy, d, expr, clign, tt)

    t.contourner("contour")
    return t


def ombre_portee(saut=0.0, ecrase=0.0):
    pts = []
    rx = 13 - saut * 0.25 + ecrase
    ry = 3.6 - saut * 0.08
    for y in range(int(ANCRE_Y - ry) - 1, int(ANCRE_Y + ry) + 2):
        for x in range(int(ANCRE_X - rx) - 1, int(ANCRE_X + rx) + 2):
            u = (x - ANCRE_X) / rx
            v = (y - ANCRE_Y) / max(ry, 0.5)
            if u * u + v * v <= 1:
                pts.append((x, y))
    return pts
