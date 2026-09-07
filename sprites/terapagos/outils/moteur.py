# -*- coding: utf-8 -*-
"""Moteur de rendu pixel-art pour Terapagos (conventions PMD Sprite Collab).

Aucun anti-aliasing : tout est tracé par masques booleens sur une grille de
pixels, puis contourné par dilatation de l'alpha. Palette indexée limitée.
"""
from PIL import Image
import math

# ---------------------------------------------------------------- palettes ---
# Palette Terapagos — Forme Teracristal (dome de cristal bleu, corps ivoire,
# yeux ambre, marques dorées). 16 teintes utiles, style PMD (3 tons/matiere).
PAL = {
    "vide":      (0, 0, 0, 0),
    "contour":   (24, 30, 52, 255),   # outline sombre unique, jamais noir pur

    # --- carapace : vitrail polygonal sombre, nervures claires -------------
    "nerv_hau":  (196, 232, 186, 255),  # nervures menthe claires du vitrail
    "nerv_mid":  (140, 196, 156, 255),
    "vit_omb":   (34, 38, 74, 255),     # cellules de vitrail, base sombre
    "vit_bas":   (52, 56, 104, 255),
    "vit_mid":   (74, 80, 136, 255),
    "vit_vio":   (98, 76, 138, 255),    # cellule violette
    "vit_ros":   (150, 92, 128, 255),   # cellule rose
    "vit_ver":   (70, 124, 110, 255),   # cellule verte
    "vit_cya":   (62, 122, 158, 255),   # cellule cyan
    "vit_ecl":   (186, 226, 240, 255),  # éclat de facette

    # --- fourrure vaporeuse menthe / crème ---------------------------------
    "four_omb":  (128, 186, 176, 255),
    "four_bas":  (170, 214, 196, 255),
    "four_mid":  (206, 234, 206, 255),
    "four_hau":  (238, 246, 214, 255),
    "four_cre":  (248, 248, 208, 255),  # pointes crème/jaune pâle

    # --- tête bleu nuit -----------------------------------------------------
    "tet_omb":   (26, 32, 62, 255),
    "tet_mid":   (44, 54, 96, 255),
    "tet_hau":   (68, 84, 132, 255),

    # --- oeil : anneau rouge, iris cyan ------------------------------------
    "oeil_rou":  (206, 62, 74, 255),
    "oeil_cya":  (96, 220, 214, 255),
    "oeil_ver":  (56, 168, 150, 255),
    "oeil_pu":   (20, 26, 46, 255),
    "oeil_bl":   (236, 248, 246, 255),

    "or_mid":    (238, 206, 96, 255),   # éclair jaune de la carapace
    "or_hau":    (252, 238, 150, 255),
    "or_omb":    (192, 152, 52, 255),
    "bouche":    (30, 36, 66, 255),
    "ombre":     (40, 38, 60, 90),
}

ORDRE_PAL = [k for k in PAL if k not in ("vide", "ombre")]


class Toile:
    """Grille de pixels adressée par nom de couleur."""

    def __init__(self, l, h):
        self.l, self.h = l, h
        self.px = [[None] * l for _ in range(h)]

    def set(self, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < self.l and 0 <= y < self.h and c is not None:
            self.px[y][x] = c

    def get(self, x, y):
        x, y = int(x), int(y)
        if 0 <= x < self.l and 0 <= y < self.h:
            return self.px[y][x]
        return None

    # -- primitives sans anti-aliasing ------------------------------------
    def disque(self, cx, cy, rx, ry, c):
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                if rx <= 0 or ry <= 0:
                    continue
                dx = (x - cx) / rx
                dy = (y - cy) / ry
                if dx * dx + dy * dy <= 1.0:
                    self.set(x, y, c)

    def rect(self, x0, y0, x1, y1, c):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                self.set(x, y, c)

    def polygone(self, pts, c):
        if not pts:
            return
        ys = [p[1] for p in pts]
        for y in range(int(math.floor(min(ys))), int(math.ceil(max(ys))) + 1):
            noeuds = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    t = (y - y0) / (y1 - y0)
                    noeuds.append(x0 + t * (x1 - x0))
            noeuds.sort()
            for i in range(0, len(noeuds) - 1, 2):
                for x in range(int(math.ceil(noeuds[i] - 0.5)),
                               int(math.floor(noeuds[i + 1] + 0.5)) + 1):
                    self.set(x, y, c)

    def ligne(self, x0, y0, x1, y1, c):
        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    # -- traitements -------------------------------------------------------
    def contourner(self, couleur="contour", cibles=None):
        """Ajoute un contour 4-connexe autour de toute matiere opaque."""
        aj = []
        for y in range(self.h):
            for x in range(self.l):
                if self.px[y][x] is not None:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    v = self.get(x + dx, y + dy)
                    if v is not None and v != couleur and \
                       (cibles is None or v in cibles):
                        aj.append((x, y))
                        break
        for x, y in aj:
            self.px[y][x] = couleur

    def decaler(self, dx, dy):
        n = Toile(self.l, self.h)
        for y in range(self.h):
            for x in range(self.l):
                n.set(x + dx, y + dy, self.px[y][x])
        return n

    def fusion(self, autre, dx=0, dy=0):
        for y in range(autre.h):
            for x in range(autre.l):
                if autre.px[y][x] is not None:
                    self.set(x + dx, y + dy, autre.px[y][x])

    def image(self, ombre=None):
        im = Image.new("RGBA", (self.l, self.h), (0, 0, 0, 0))
        d = im.load()
        if ombre:
            for (x, y) in ombre:
                if 0 <= x < self.l and 0 <= y < self.h:
                    d[x, y] = PAL["ombre"]
        for y in range(self.h):
            for x in range(self.l):
                c = self.px[y][x]
                if c is not None:
                    d[x, y] = PAL[c]
        return im
