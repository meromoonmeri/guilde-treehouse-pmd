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
    "contour":   (26, 24, 46, 255),   # outline sombre unique, jamais noir pur
    "cont_cri":  (30, 52, 96, 255),   # outline interne du cristal
    "cri_omb":   (44, 96, 158, 255),
    "cri_bas":   (63, 143, 208, 255),
    "cri_mid":   (111, 195, 232, 255),
    "cri_hau":   (176, 231, 247, 255),
    "cri_ecl":   (233, 251, 255, 255),
    "corp_omb":  (150, 146, 138, 255),
    "corp_bas":  (198, 195, 182, 255),
    "corp_mid":  (231, 228, 214, 255),
    "corp_hau":  (250, 249, 240, 255),
    "or_omb":    (176, 116, 32, 255),
    "or_mid":    (238, 176, 58, 255),
    "or_hau":    (255, 219, 128, 255),
    "oeil_bl":   (252, 252, 248, 255),
    "oeil_ir":   (240, 158, 42, 255),
    "oeil_pu":   (40, 34, 40, 255),
    "bouche":    (108, 60, 74, 255),
    "ombre":     (40, 38, 60, 90),
}

ORDRE_PAL = ["vide", "contour", "cont_cri", "cri_omb", "cri_bas", "cri_mid",
             "cri_hau", "cri_ecl", "corp_omb", "corp_bas", "corp_mid",
             "corp_hau", "or_omb", "or_mid", "or_hau", "oeil_bl", "oeil_ir",
             "oeil_pu", "bouche"]


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
