# -*- coding: utf-8 -*-
"""Portraits PMD Sprite Collab de Terapagos — base verrouillée.

MÉTHODE (celle d'un spriter SpriteCollab, pas une illustration réduite) :

  1. On construit UNE tête canonique 40x40, pixel par pixel, sur une palette
     indexée fixe. Aucun redimensionnement, aucun anti-aliasing, aucun pixel
     semi-transparent : chaque pixel est posé volontairement.
  2. Cette base est ensuite VERROUILLÉE.
  3. Les 20 expressions sont obtenues en ne repeignant QUE la fenêtre faciale
     (yeux, sourcils, paupières, bouche, joues). Tout le reste — silhouette,
     contour, carapace, fourrure, ombres structurelles, fond — est copié bit
     à bit depuis la base.
  4. Un contrôle final compare chaque portrait au portrait Normal hors
     fenêtre faciale et échoue si un seul pixel diffère.

Le fond est un aplat strictement uniforme, identique dans les 20 cases.
"""
import os
import sys
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fonds as F

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
T = 40

# --------------------------------------------------------------- palette ---
# Palette indexée fixe (15 couleurs + fond). Aucune teinte n'est créée par
# interpolation : les ombres sont des plages franches.
P = {
    "fond":     (72, 104, 152),   # aplat de fond, strictement identique
    "cont":     (16, 18, 38),     # contour dur
    "tet_omb":  (28, 32, 62),     # tête, ombre
    "tet_mid":  (44, 50, 92),     # tête, ton moyen
    "tet_hau":  (66, 76, 126),    # tête, lumière
    "four_omb": (126, 170, 152),  # fourrure, ombre
    "four_mid": (178, 214, 184),  # fourrure, ton moyen
    "four_hau": (222, 238, 200),  # fourrure, lumière
    "four_cre": (246, 248, 214),  # fourrure, pointes crème
    "nerv":     (196, 226, 168),  # nervures du vitrail
    "vit_omb":  (40, 44, 84),     # vitrail sombre
    "vit_vio":  (96, 78, 140),    # cellule violette
    "vit_ros":  (162, 92, 126),   # cellule rose
    "vit_cya":  (62, 122, 160),   # cellule cyan
    "or":       (242, 208, 74),   # éclair jaune
    "rouge":    (204, 60, 76),    # anneau de l'oeil
    "cyan":     (104, 216, 212),  # iris
    "blanc":    (248, 250, 244),  # éclat / sclère
}

# ------------------------------------------------------- fenêtre faciale ---
# SEULE zone que les expressions ont le droit de modifier.
FX0, FY0, FX1, FY1 = 10, 19, 30, 35


class Toile:
    def __init__(self):
        self.p = [["fond"] * T for _ in range(T)]

    def s(self, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < T and 0 <= y < T:
            self.p[y][x] = c

    def g(self, x, y):
        x, y = int(x), int(y)
        if 0 <= x < T and 0 <= y < T:
            return self.p[y][x]
        return None

    def ell(self, cx, cy, rx, ry, c):
        for y in range(int(cy - ry), int(cy + ry) + 1):
            for x in range(int(cx - rx), int(cx + rx) + 1):
                u = (x - cx) / float(rx)
                v = (y - cy) / float(ry)
                if u * u + v * v <= 1.0:
                    self.s(x, y, c)

    def rect(self, x0, y0, x1, y1, c):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                self.s(x, y, c)

    def image(self, transparent=False):
        """transparent=True : le fond devient alpha 0 (tête détourée)."""
        im = Image.new("RGBA", (T, T), (0, 0, 0, 0))
        d = im.load()
        for y in range(T):
            for x in range(T):
                c = self.p[y][x]
                if transparent and c == "fond":
                    continue
                d[x, y] = P[c] + (255,)
        return im

    def copie(self):
        n = Toile()
        n.p = [ligne[:] for ligne in self.p]
        return n


# ============================================================== BASE ======
def base_verrouillee():
    """Tête canonique de Terapagos. Dessinée une seule fois."""
    t = Toile()

    # --- carapace de vitrail, sommet du cadre ------------------------------
    # calotte basse et large, coupée par le haut du cadre (cadrage PMD)
    # Les cellules sont obtenues par germes (Voronoi discret) : contours
    # polygonaux irréguliers, comme le vitrail de l'artwork.
    germes = [(10, 1, "vit_vio"), (20, 0, "vit_omb"), (30, 1, "vit_ros"),
              (7, 8, "vit_cya"), (16, 7, "vit_omb"), (25, 7, "vit_vio"),
              (33, 8, "vit_cya")]
    for y in range(0, 18):
        for x in range(T):
            u = (x - 20) / 16.0
            v = (y - 3) / 13.0
            if u * u + v * v > 1.0:
                continue
            best, bd = None, 1e9
            for (gx, gy, gc) in germes:
                d = (x - gx) ** 2 + ((y - gy) * 1.35) ** 2
                if d < bd:
                    bd, best = d, gc
            t.s(x, y, best)

    # nervures menthe entre cellules
    for y in range(0, 18):
        for x in range(T):
            c = t.g(x, y)
            if c is None or not c.startswith("vit"):
                continue
            for dx, dy in ((1, 0), (0, 1)):
                n = t.g(x + dx, y + dy)
                if n is not None and n.startswith("vit") and n != c:
                    t.s(x, y, "nerv")
    # cerclage menthe du bord de carapace
    for y in range(0, 18):
        for x in range(T):
            c = t.g(x, y)
            if c is None or not c.startswith(("vit", "nerv")):
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = t.g(x + dx, y + dy)
                if n is None or not n.startswith(("vit", "nerv")):
                    t.s(x, y, "nerv")
                    break

    # éclair jaune, motif franc de la carapace
    for dx, dy in ((1, 0), (2, 0), (0, 1), (1, 1), (2, 1), (0, 2), (1, 2),
                   (1, 3), (2, 3), (0, 4), (1, 4), (1, 5)):
        t.s(17 + dx, 1 + dy, "or")

    # --- fourrure : mèches pointues encadrant la tête ----------------------
    for (mx, my, ml, sens) in ((9, 20, 3, -1), (7, 27, 3, -1), (10, 33, 2, -1),
                               (30, 20, 3, 1), (32, 27, 3, 1), (29, 33, 2, 1)):
        for k in range(ml):
            larg = max(0, 2 - k // 2)
            for dy in range(-larg, larg + 1):
                c = "four_cre" if k >= ml - 2 else (
                    "four_mid" if sens < 0 else "four_omb")
                t.s(mx + sens * k, my + dy, c)

    # collerette pleine autour de la tête
    t.ell(20, 27, 13, 11, "four_mid")
    for y in range(15, T):
        for x in range(T):
            if t.g(x, y) != "four_mid":
                continue
            u = (x - 20) / 13.0
            v = (y - 27) / 11.0
            lum = -0.6 * u - 0.8 * v
            if lum > 0.45:
                t.s(x, y, "four_hau")
            elif lum < -0.45:
                t.s(x, y, "four_omb")

    # --- tête bleu nuit, au premier plan -----------------------------------
    t.ell(20, 27, 10, 9, "tet_mid")
    for y in range(14, T):
        for x in range(T):
            if t.g(x, y) != "tet_mid":
                continue
            u = (x - 20) / 10.0
            v = (y - 27) / 9.0
            lum = -0.55 * u - 0.8 * v
            if lum > 0.5:
                t.s(x, y, "tet_hau")
            elif lum < -0.4:
                t.s(x, y, "tet_omb")
    # reflet fixe sur le crâne (structure d'ombre, jamais modifié ensuite)
    for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1), (2, 1), (1, 2)):
        t.s(15 + dx, 22 + dy, "tet_hau")

    # --- contour dur --------------------------------------------------------
    contourner(t)
    return t


def contourner(t):
    aj = []
    for y in range(T):
        for x in range(T):
            if t.g(x, y) != "fond":
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = t.g(x + dx, y + dy)
                if n is not None and n != "fond" and n != "cont":
                    aj.append((x, y))
                    break
    for (x, y) in aj:
        t.s(x, y, "cont")


# ========================================================= EXPRESSIONS ====
# Chaque fonction ne peint QUE dans la fenêtre faciale.
OG, OD = 16, 24      # centre des deux yeux
OY = 26              # ligne des yeux
BX, BY = 20, 32      # centre de la bouche


def _oeil(t, ox, ouvert=1.0, ir_dx=0, ir_dy=0, iris=True, sclere=False):
    """Oeil canonique : anneau rouge, iris cyan, pupille sombre, éclat."""
    if ouvert <= 0.08:
        for dx in range(-3, 4):
            t.s(ox + dx, OY, "cont")
        return
    ry = max(1, int(round(3 * ouvert)))
    for dy in range(-ry, ry + 1):
        for dx in range(-3, 4):
            if (dx * dx) / 9.0 + (dy * dy) / float(ry * ry) <= 1.0:
                t.s(ox + dx, OY + dy, "rouge")
    ry2 = max(1, ry - 1)
    for dy in range(-ry2, ry2 + 1):
        for dx in range(-3, 4):
            if (dx * dx) / 4.0 + (dy * dy) / float(ry2 * ry2) <= 1.0:
                t.s(ox + dx + ir_dx, OY + dy + ir_dy,
                    "blanc" if sclere else ("cyan" if iris else "blanc"))
    if iris and not sclere:
        t.s(ox + ir_dx, OY + ir_dy, "cont")
        t.s(ox + ir_dx, OY + ir_dy + 1, "cont")
    t.s(ox - 1 + ir_dx, OY - 1 + ir_dy, "blanc")


def _sourcil(t, ox, sens, haut=6):
    """sens = -1 froncé (colère), +1 relevé (tristesse/inquiétude)."""
    for i in range(6):
        dy = (i // 2) * sens * (1 if ox < 20 else -1)
        t.s(ox - 3 + i, OY - haut + dy, "cont")


def _paupiere(t, ox, bas=False):
    """Paupière supérieure (fatigue) ou inférieure (méfiance)."""
    y = OY + 2 if bas else OY - 2
    for dx in range(-4, 5):
        t.s(ox + dx, y, "tet_omb")
        if not bas:
            for k in range(1, 4):
                t.s(ox + dx, y - k, "tet_omb")


def _bouche(t, forme):
    """Bouche en zigzag caractéristique de Terapagos, ou variantes."""
    if forme == "zigzag":
        for i, dx in enumerate(range(-5, 6)):
            t.s(BX + dx, BY + (i % 2), "cont")
    elif forme == "sourire":
        for dx in range(-5, 6):
            dy = 0 if abs(dx) > 3 else 1
            t.s(BX + dx, BY + dy, "cont")
        for dx in range(-3, 4):
            t.s(BX + dx, BY + 2, "cont")
    elif forme == "grand_sourire":
        for dy in range(0, 4):
            for dx in range(-5, 6):
                if (dx * dx) / 25.0 + ((dy - 1) ** 2) / 6.0 <= 1.0:
                    t.s(BX + dx, BY + dy, "cont")
        for dx in range(-3, 4):
            t.s(BX + dx, BY, "blanc")
    elif forme == "triste":
        for dx in range(-4, 5):
            dy = 1 if abs(dx) > 2 else 0
            t.s(BX + dx, BY + dy - 1, "cont")
    elif forme == "cri":
        for dy in range(-1, 4):
            for dx in range(-4, 5):
                if (dx * dx) / 16.0 + ((dy - 1) ** 2) / 6.0 <= 1.0:
                    t.s(BX + dx, BY + dy, "cont")
        for dx in range(-2, 3):
            t.s(BX + dx, BY + 2, "rouge")
    elif forme == "rond":
        for dy in range(-1, 3):
            for dx in range(-2, 3):
                if (dx * dx) / 4.0 + ((dy - 0.5) ** 2) / 2.5 <= 1.0:
                    t.s(BX + dx, BY + dy, "cont")
    elif forme == "plat":
        for dx in range(-4, 5):
            t.s(BX + dx, BY, "cont")
    elif forme == "ondule":
        for i, dx in enumerate(range(-5, 6)):
            t.s(BX + dx, BY + (0 if (i // 2) % 2 else 1), "cont")


def _joues(t):
    """Rougeur des joues (gêne), en plages franches."""
    for s in (-1, 1):
        for dx in range(0, 4):
            for dy in range(0, 2):
                t.s(20 + s * (8 + dx), 28 + dy, "rouge")


def _larme(t, ox, n=2):
    for k in range(n):
        t.s(ox + 4, OY + 4 + k, "cyan")


EXPRESSIONS = {
    # slot officiel : (libellé FR, fonction)
    "Normal":     ("Normal", lambda t: (
        _oeil(t, OG), _oeil(t, OD), _bouche(t, "zigzag"))),

    "Happy":      ("Heureux", lambda t: (
        _oeil(t, OG, 0.55), _oeil(t, OD, 0.55), _bouche(t, "sourire"))),

    "Joyous":     ("Très heureux", lambda t: (
        _oeil(t, OG, 0.0), _oeil(t, OD, 0.0), _bouche(t, "grand_sourire"),
        _joues(t))),

    "Sad":        ("Triste", lambda t: (
        _oeil(t, OG, 0.75, ir_dy=1), _oeil(t, OD, 0.75, ir_dy=1),
        _sourcil(t, OG, 1), _sourcil(t, OD, 1), _bouche(t, "triste"))),

    "Angry":      ("En colère", lambda t: (
        _oeil(t, OG, 0.7, ir_dx=1), _oeil(t, OD, 0.7, ir_dx=-1),
        _sourcil(t, OG, -1), _sourcil(t, OD, -1), _bouche(t, "plat"))),

    "Shouting":   ("Très en colère", lambda t: (
        _oeil(t, OG, 0.85, ir_dx=1), _oeil(t, OD, 0.85, ir_dx=-1),
        _sourcil(t, OG, -1, 7), _sourcil(t, OD, -1, 7), _bouche(t, "cri"))),

    "Surprised":  ("Surpris", lambda t: (
        _oeil(t, OG, 1.0), _oeil(t, OD, 1.0), _bouche(t, "rond"))),

    "Stunned":    ("Choqué", lambda t: (
        _oeil(t, OG, 1.0, sclere=True), _oeil(t, OD, 1.0, sclere=True),
        _bouche(t, "rond"))),

    "Special0":   ("Effrayé", lambda t: (
        _oeil(t, OG, 1.0, sclere=True), _oeil(t, OD, 1.0, sclere=True),
        _sourcil(t, OG, 1), _sourcil(t, OD, 1), _bouche(t, "ondule"))),

    "Worried":    ("Inquiet", lambda t: (
        _oeil(t, OG, 0.8, ir_dy=1), _oeil(t, OD, 0.8, ir_dy=1),
        _sourcil(t, OG, 1), _sourcil(t, OD, 1), _bouche(t, "ondule"))),

    "Dizzy":      ("Confus", lambda t: (
        _oeil(t, OG, 0.9, iris=False), _oeil(t, OD, 0.9, iris=False),
        _spirale(t, OG), _spirale(t, OD), _bouche(t, "ondule"))),

    "Special1":   ("Pensif", lambda t: (
        _oeil(t, OG, 0.6, ir_dx=1, ir_dy=-1),
        _oeil(t, OD, 0.6, ir_dx=1, ir_dy=-1),
        _paupiere(t, OG), _paupiere(t, OD), _bouche(t, "plat"))),

    "Determined": ("Déterminé", lambda t: (
        _oeil(t, OG, 0.75, ir_dx=1), _oeil(t, OD, 0.75, ir_dx=-1),
        _sourcil(t, OG, -1), _sourcil(t, OD, -1), _bouche(t, "zigzag"))),

    "Inspired":   ("Combatif", lambda t: (
        _oeil(t, OG, 0.9), _oeil(t, OD, 0.9),
        _sourcil(t, OG, -1, 7), _sourcil(t, OD, -1, 7),
        _bouche(t, "grand_sourire"))),

    "Sigh":       ("Fatigué", lambda t: (
        _oeil(t, OG, 0.35), _oeil(t, OD, 0.35),
        _paupiere(t, OG), _paupiere(t, OD), _bouche(t, "plat"))),

    "Special2":   ("Endormi", lambda t: (
        _oeil(t, OG, 0.0), _oeil(t, OD, 0.0), _bouche(t, "rond"))),

    "Special3":   ("Gêné", lambda t: (
        _oeil(t, OG, 0.5), _oeil(t, OD, 0.5), _joues(t),
        _bouche(t, "ondule"))),

    "Crying":     ("Embarrassé / pleurs", lambda t: (
        _oeil(t, OG, 0.45, ir_dy=1), _oeil(t, OD, 0.45, ir_dy=1),
        _sourcil(t, OG, 1), _sourcil(t, OD, 1),
        _larme(t, OG, 3), _larme(t, OD, 3), _bouche(t, "triste"))),

    "Pain":       ("Douleur", lambda t: (
        _oeil(t, OG, 0.25), _oeil(t, OD, 0.25),
        _sourcil(t, OG, 1), _sourcil(t, OD, 1), _bouche(t, "ondule"))),

    "Teary-Eyed": ("Déçu", lambda t: (
        _oeil(t, OG, 0.7, ir_dy=1), _oeil(t, OD, 0.7, ir_dy=1),
        _sourcil(t, OG, 1), _sourcil(t, OD, 1),
        _larme(t, OG, 1), _larme(t, OD, 1), _bouche(t, "triste"))),
}

ORDRE = ["Normal", "Happy", "Joyous", "Sad", "Angry",
         "Shouting", "Surprised", "Stunned", "Special0", "Worried",
         "Dizzy", "Special1", "Determined", "Inspired", "Sigh",
         "Special2", "Special3", "Crying", "Pain", "Teary-Eyed"]


def _spirale(t, ox):
    """Oeil en spirale (confusion), tracé franc."""
    for dx, dy in ((0, -2), (1, -1), (1, 0), (0, 1), (-1, 1), (-2, 0),
                   (-2, -1), (-1, -2), (0, -3), (2, -2), (2, 1), (-1, 2)):
        t.s(ox + dx, OY + dy, "cont")


# =========================================================== ASSEMBLAGE ===
def construire():
    base = base_verrouillee()
    out = {}
    for nom in ORDRE:
        libelle, fn = EXPRESSIONS[nom]
        t = base.copie()          # <- base copiée bit à bit
        fn(t)                     # <- seule la fenêtre faciale est repeinte
        # sécurité absolue : on restaure tout ce qui sort de la fenêtre
        for y in range(T):
            for x in range(T):
                if not (FX0 <= x <= FX1 and FY0 <= y <= FY1):
                    t.p[y][x] = base.p[y][x]
        out[nom] = (libelle, t)
    return base, out


def verifier(base, portraits):
    """Contrôle final : hors fenêtre faciale, aucun pixel ne doit différer."""
    ref = portraits["Normal"][1]
    erreurs = []
    for nom, (_lib, t) in portraits.items():
        diff = 0
        for y in range(T):
            for x in range(T):
                if FX0 <= x <= FX1 and FY0 <= y <= FY1:
                    continue
                if t.p[y][x] != ref.p[y][x]:
                    diff += 1
        if diff:
            erreurs.append((nom, diff))
    # le fond doit être un aplat strictement uniforme et identique partout
    fonds = set()
    for nom, (_lib, t) in portraits.items():
        for y in range(T):
            for x in range(T):
                if t.p[y][x] == "fond":
                    fonds.add(P["fond"])
    return erreurs, fonds


VARIANTES = {
    "0000": {},                       # Teracristal : palette de référence
    "0001": {"vit_vio": (74, 110, 92), "vit_ros": (96, 128, 92),
             "vit_cya": (70, 118, 96), "vit_omb": (38, 62, 52)},
    "0002": {"vit_vio": (120, 92, 176), "vit_ros": (196, 104, 150),
             "vit_cya": (74, 152, 200), "or": (255, 226, 96)},
}


def generer(dst, variante=None):
    os.makedirs(dst, exist_ok=True)
    sauve = dict(P)
    if variante:
        P.update(variante)
    base, portraits = construire()
    erreurs, fonds = verifier(base, portraits)
    if erreurs:
        raise SystemExit("BASE NON VERROUILLÉE : %s" % erreurs)
    if len(fonds) != 1:
        raise SystemExit("FOND NON UNIFORME : %s" % fonds)

    feuille = Image.new("RGBA", (T * 5, T * 8), (0, 0, 0, 0))
    for i, nom in enumerate(ORDRE):
        _lib, t = portraits[nom]
        im = F.fond(nom)              # fond canonique PMD
        im.alpha_composite(t.image(transparent=True))  # tête par-dessus
        im.save(os.path.join(dst, "%s.png" % nom))
        feuille.paste(im, ((i % 5) * T, (i // 5) * T))
        mi = im.transpose(Image.FLIP_LEFT_RIGHT)
        mi.save(os.path.join(dst, "%s^.png" % nom))
        feuille.paste(mi, ((i % 5) * T, (i // 5 + 4) * T))
    feuille.save(os.path.join(dst, "Portraits.png"))
    P.clear()
    P.update(sauve)
    open(os.path.join(dst, "credits.txt"), "w").write(
        "Guilde Treehouse\tTerapagos — portraits 40x40, base verrouillée, "
        "format PMD Sprite Collab (CC BY-NC 4.0)\n")
    return len(ORDRE), len(P)


if __name__ == "__main__":
    for code in ("0000", "0001", "0002"):
        n, npal = generer(os.path.join(R, "portrait", code),
                          VARIANTES.get(code))
        print("%s : %d expressions, %d couleurs, base verrouillée OK"
              % (code, n, npal))
