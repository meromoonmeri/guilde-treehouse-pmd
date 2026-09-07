"""
generer_zone.py — Sanctuaire de Terapagos : décor de la zone de boss et
effets visuels de la transformation Terastal vers Stellaire.

Tout est produit ici, rien n'est repris d'un pack existant : sol de cristal
en pavage de Voronoï, piliers de cristal à facettes, cercle rituel, colonnes
de lumière arc-en-ciel, anneau de foudre et sphère d'enveloppement.

Sorties :
  decor/     planches PNG du décor, par calque et composées
  vfx/       feuilles de sprites des effets, une colonne par image
  aseprite/  sources éditables, multi-calques et multi-images
  apercus/   GIF de contrôle
  sons/      effets sonores de synthèse (voir sons.py)
"""

import os
import sys
import math
import colorsys
import numpy as np
from PIL import Image

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
sys.path.insert(0, os.path.join(ICI, "..", "..", "foulards_pmd", "outils"))
import aseprite
import sons as S

RACINE = os.path.abspath(os.path.join(ICI, ".."))
SC = os.environ.get("SPRITECOLLAB", "/home/user/sc_tmp")

LARG, HAUT = 768, 512          # multiples de la grille 8 px du projet
GRILLE = 8
CX, CY = LARG // 2, 300        # centre de l'arène, au sol

# --------------------------------------------------------------------------
# Palette du sanctuaire
# --------------------------------------------------------------------------

P = {
    "vide":        (0x07, 0x08, 0x18),
    "sol_creux":   (0x0F, 0x12, 0x38),
    "sol_ombre":   (0x18, 0x1D, 0x52),
    "sol_base":    (0x23, 0x2A, 0x68),
    "sol_clair":   (0x31, 0x3B, 0x88),
    "sol_arete":   (0x0B, 0x0E, 0x2C),
    "sol_reflet":  (0x4C, 0x5C, 0xB8),
    "cristal_bas": (0x1C, 0x24, 0x6E),
    "cristal_mid": (0x2E, 0x42, 0xA8),
    "cristal_haut": (0x63, 0x9A, 0xE0),
    "cristal_vif": (0xA8, 0xE8, 0xFF),
    "cristal_coeur": (0xE8, 0xFF, 0xFF),
    "or":          (0xE8, 0xC8, 0x6A),
}


def hsv(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, max(0, min(1, s)), max(0, min(1, v)))
    return (int(r * 255), int(g * 255), int(b * 255))


def arc_en_ciel(t, s=0.72, v=1.0):
    return hsv(t, s, v)


# --------------------------------------------------------------------------
# Toile RGBA avec mélange additif pour la lumière
# --------------------------------------------------------------------------

class Toile:
    def __init__(self, w=LARG, h=HAUT):
        self.w, self.h = w, h
        self.a = np.zeros((h, w, 4), dtype=np.float32)

    def poser(self, x, y, c, alpha=1.0):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h and alpha > 0:
            if alpha >= 1.0:
                self.a[y, x, :3] = c
                self.a[y, x, 3] = 255
            else:
                d = self.a[y, x]
                na = alpha * 255 + d[3] * (1 - alpha)
                if na > 0:
                    d[:3] = (np.array(c) * alpha * 255 + d[:3] * d[3] * (1 - alpha)) / na
                    d[3] = na

    def ajouter(self, x, y, c, force=1.0):
        """Mélange additif : la lumière s'accumule."""
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h and force > 0:
            d = self.a[y, x]
            d[:3] = np.minimum(255.0, d[:3] + np.array(c, dtype=np.float32) * force)
            d[3] = min(255.0, d[3] + 255.0 * force)

    def img(self):
        return Image.fromarray(np.clip(self.a, 0, 255).astype(np.uint8), "RGBA")


def composer(calques):
    out = Image.new("RGBA", (LARG, HAUT), (0, 0, 0, 0))
    for _, im in calques:
        out = Image.alpha_composite(out, im)
    return out


# --------------------------------------------------------------------------
# Sol de cristal
# --------------------------------------------------------------------------

def sol_cristal(graine=17):
    """
    Dallage de cristal : pavage de Voronoï sur une grille perturbée, chaque
    cellule facettée et éclairée depuis le centre de l'arène. Les arêtes sont
    creusées, ce qui donne la lecture « cristal taillé » plutôt que « pierre ».
    """
    rng = np.random.default_rng(graine)
    pas = 34
    germes = []
    for gy in range(-1, HAUT // pas + 2):
        for gx in range(-1, LARG // pas + 2):
            germes.append((gx * pas + rng.uniform(-11, 11),
                           gy * pas + rng.uniform(-11, 11),
                           rng.uniform(0, 1)))
    G = np.array([[g[0], g[1]] for g in germes], dtype=np.float32)
    teinte = np.array([g[2] for g in germes], dtype=np.float32)

    ys, xs = np.mgrid[0:HAUT, 0:LARG]
    pts = np.stack([xs.ravel(), ys.ravel()], axis=1).astype(np.float32)
    d = np.empty((len(pts), 2), dtype=np.float32)
    idx = np.empty(len(pts), dtype=np.int32)
    bloc = 40000
    for i in range(0, len(pts), bloc):
        seg = pts[i:i + bloc]
        dist = np.linalg.norm(seg[:, None, :] - G[None, :, :], axis=2)
        o = np.argsort(dist, axis=1)[:, :2]
        idx[i:i + bloc] = o[:, 0]
        d[i:i + bloc, 0] = np.take_along_axis(dist, o[:, :1], 1)[:, 0]
        d[i:i + bloc, 1] = np.take_along_axis(dist, o[:, 1:2], 1)[:, 0]
    d0 = d[:, 0].reshape(HAUT, LARG)
    d1 = d[:, 1].reshape(HAUT, LARG)
    cell = idx.reshape(HAUT, LARG)
    arete = (d1 - d0)                     # petite valeur = proche d'une arête

    # éclairement : plus lumineux vers le centre de l'arène
    dist_c = np.sqrt(((xs - CX) / (LARG * 0.52)) ** 2 +
                     ((ys - CY) / (HAUT * 0.62)) ** 2)
    lum = np.clip(1.15 - dist_c * 1.25, 0.0, 1.0)

    var = teinte[cell]
    base = np.zeros((HAUT, LARG, 3), dtype=np.float32)
    c_creux = np.array(P["sol_creux"], dtype=np.float32)
    c_ombre = np.array(P["sol_ombre"], dtype=np.float32)
    c_base = np.array(P["sol_base"], dtype=np.float32)
    c_clair = np.array(P["sol_clair"], dtype=np.float32)
    c_arete = np.array(P["sol_arete"], dtype=np.float32)
    c_reflet = np.array(P["sol_reflet"], dtype=np.float32)

    k = np.clip(lum * (0.72 + 0.55 * var), 0.0, 1.4)
    base += c_creux * np.clip(1.0 - k * 2.2, 0, 1)[..., None]
    base += c_ombre * np.clip(1.0 - np.abs(k - 0.34) * 3.2, 0, 1)[..., None]
    base += c_base * np.clip(1.0 - np.abs(k - 0.62) * 3.0, 0, 1)[..., None]
    base += c_clair * np.clip(1.0 - np.abs(k - 0.92) * 3.0, 0, 1)[..., None]
    base += c_reflet * np.clip((k - 1.05) * 3.0, 0, 1)[..., None]

    # arêtes taillées, plus une lèvre claire d'un côté
    m_ar = arete < 1.15
    base[m_ar] = c_arete
    m_lev = (arete >= 1.15) & (arete < 2.3) & (var[..., None][..., 0] > 0.55)
    base[m_lev] = np.minimum(255.0, base[m_lev] * 1.28 + 12.0)

    out = np.zeros((HAUT, LARG, 4), dtype=np.uint8)
    out[..., :3] = np.clip(base, 0, 255).astype(np.uint8)
    out[..., 3] = 255
    return Image.fromarray(out, "RGBA"), cell, arete, lum


def veines(cell, arete, phase):
    """Veines lumineuses qui courent dans les arêtes du dallage."""
    t = Toile()
    ys, xs = np.mgrid[0:HAUT, 0:LARG]
    onde = 0.5 + 0.5 * np.sin((xs * 0.018 + ys * 0.026) * 2.0
                              - phase * 2 * math.pi * 2.0)
    dist_c = np.sqrt(((xs - CX) / (LARG * 0.5)) ** 2 + ((ys - CY) / (HAUT * 0.6)) ** 2)
    force = np.clip(1.1 - dist_c, 0, 1) ** 1.6 * onde
    m = (arete < 1.6) & (force > 0.26)
    ys2, xs2 = np.nonzero(m)
    for y, x in zip(ys2, xs2):
        h = ((x + y) * 0.0016 + phase * 0.5) % 1.0
        t.ajouter(x, y, arc_en_ciel(h, 0.55, 1.0), float(force[y, x]) * 0.55)
    return t.img()


# --------------------------------------------------------------------------
# Piliers de cristal
# --------------------------------------------------------------------------

def _shard(t, cx, base_y, hauteur, largeur, teinte, eclat, rng, penche=0.0):
    """Un éclat de cristal : prisme facetté qui s'affine et s'incline."""
    for i in range(hauteur):
        u = i / max(hauteur - 1, 1)
        lg = max(0.7, largeur * 0.5 * (1.0 - u ** 1.9))
        dxc = penche * u * hauteur * 0.22
        y = base_y - i
        for dx in range(int(-lg) - 1, int(lg) + 2):
            nx = dx / max(lg, 1e-6)
            if abs(nx) > 1.02:
                continue
            f = abs(((nx + 1.0) * 1.5) % 1.0 - 0.5) * 2.0
            l = (0.28 + 0.60 * f) * (0.45 + 0.65 * u) * eclat
            if abs(nx) > 0.86:
                c, l = P["cristal_bas"], l * 0.45
            elif abs(nx) < 0.24:
                c = P["cristal_coeur"] if u > 0.35 else P["cristal_vif"]
            elif l > 0.72:
                c = P["cristal_haut"]
            elif l > 0.46:
                c = P["cristal_mid"]
            else:
                c = P["cristal_bas"]
            col = np.array(c, dtype=np.float32) * (0.60 + 0.55 * l)
            col = col * 0.86 + np.array(arc_en_ciel(teinte, 0.5, 1.0)) * 0.14
            t.poser(cx + dx + dxc, y, tuple(int(min(255, v)) for v in col))


def pilier(hauteur, largeur, teinte=0.58, eclat=1.0, graine=3):
    """
    Pilier de cristal : une grappe de trois à cinq éclats de hauteurs et
    d'inclinaisons différentes, plantés dans un socle de débris. Bien plus
    minéral qu'un cône unique.
    """
    w = int(largeur * 2.4) + 12
    h = hauteur + 18
    t = Toile(w, h)
    rng = np.random.default_rng(graine)
    cx = w // 2
    base_y = h - 7

    # socle : gros débris à la base
    for _ in range(int(largeur * 1.6)):
        a = rng.uniform(-1, 1)
        d = rng.uniform(0.25, 1.15) * largeur
        hh = int(rng.uniform(4, 13))
        _shard(t, cx + a * d, base_y + rng.integers(0, 3), hh,
               max(3, int(hh * 0.55)), teinte, eclat * 0.85, rng,
               penche=a * 0.25)

    # éclats secondaires puis l'éclat maître, dessiné en dernier
    n = int(rng.integers(3, 6))
    ordres = []
    for k in range(n):
        a = (k - (n - 1) / 2) / max((n - 1) / 2, 1)
        hh = int(hauteur * rng.uniform(0.42, 0.78))
        lw = max(4, int(largeur * rng.uniform(0.35, 0.62)))
        ordres.append((abs(a), cx + a * largeur * 0.62, hh, lw, a * 0.5))
    ordres.sort(reverse=True)
    for _, px, hh, lw, pe in ordres:
        _shard(t, px, base_y, hh, lw, teinte, eclat * 0.92, rng, pe)
    _shard(t, cx, base_y, hauteur, largeur, teinte, eclat, rng,
           penche=rng.uniform(-0.12, 0.12))

    # contour sombre : sans lui, le cristal se dilue dans le sol
    a = t.a
    plein = a[..., 3] > 0
    voisin = np.zeros_like(plein)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            voisin |= np.roll(np.roll(plein, dy, 0), dx, 1)
    bord = voisin & ~plein
    a[bord, :3] = np.array((6, 8, 26), dtype=np.float32)
    a[bord, 3] = 235
    # densifier les demi-teintes pour que le volume se lise
    corps = plein & (a[..., :3].sum(axis=2) < 330)
    a[corps, :3] *= 0.80
    return t.img()


def placer_piliers():
    """Disposition en couronne autour de l'aire de combat."""
    plan = [
        # (x, y au sol, hauteur, largeur, teinte, avant/arrière)
        (96, 250, 118, 34, 0.72, False), (208, 214, 92, 26, 0.60, False),
        (382, 196, 150, 42, 0.55, False), (556, 214, 92, 26, 0.46, False),
        (668, 250, 118, 34, 0.34, False),
        (44, 372, 150, 44, 0.80, True), (232, 418, 104, 30, 0.66, True),
        (536, 418, 104, 30, 0.20, True), (724, 372, 150, 44, 0.08, True),
    ]
    arriere, avant = Toile(), Toile()
    for i, (x, y, hh, lw, te, av) in enumerate(plan):
        im = pilier(hh, lw, te, 1.0 if av else 0.82, graine=3 + i)
        cible = avant if av else arriere
        buf = Image.new("RGBA", (LARG, HAUT), (0, 0, 0, 0))
        buf.paste(im, (int(x - im.size[0] // 2), int(y - im.size[1] + 6)), im)
        cible.a = np.maximum(cible.a, np.array(buf, dtype=np.float32))
    return arriere.img(), avant.img(), plan


def halo_piliers(plan, phase):
    """Lueur pulsée au pied et au sommet de chaque pilier."""
    t = Toile()
    for i, (x, y, hh, lw, te, av) in enumerate(plan):
        pul = 0.55 + 0.45 * math.sin(phase * 2 * math.pi + i * 0.8)
        c = arc_en_ciel(te, 0.62, 1.0)
        r = lw * 1.5
        for dy in range(int(-r * 0.45), int(r * 0.45) + 1):
            for dx in range(int(-r), int(r) + 1):
                d = math.hypot(dx / r, dy / (r * 0.45))
                if d > 1:
                    continue
                t.ajouter(x + dx, y + dy - 2, c, (1 - d) ** 2 * 0.30 * pul)
        sy = y - hh - 4
        for dy in range(-6, 7):
            for dx in range(-6, 7):
                d = math.hypot(dx, dy) / 6.0
                if d > 1:
                    continue
                t.ajouter(x + dx, sy + dy, c, (1 - d) ** 2 * 0.55 * pul)
    return t.img()


# --------------------------------------------------------------------------
# Cercle rituel au sol
# --------------------------------------------------------------------------

def cercle_rituel(phase, rayon=150):
    t = Toile()
    ry = rayon * 0.42
    for k, (rr, ep, vit, sat) in enumerate(((1.00, 2, 1.0, 0.55),
                                            (0.82, 1, -0.7, 0.70),
                                            (0.52, 1, 1.6, 0.85))):
        n = int(2 * math.pi * rayon * rr * 1.6)
        for i in range(n):
            a = 2 * math.pi * i / n
            h = (a / (2 * math.pi) + phase * vit) % 1.0
            c = arc_en_ciel(h, sat, 1.0)
            for e in range(ep):
                x = CX + math.cos(a) * (rayon * rr + e)
                y = CY + math.sin(a) * (ry * rr + e * 0.42)
                t.ajouter(x, y, c, 0.5)
    # dix-huit repères, un par type
    for i in range(18):
        a = 2 * math.pi * i / 18 + phase * 2 * math.pi * 0.25
        x = CX + math.cos(a) * rayon * 0.91
        y = CY + math.sin(a) * ry * 0.91
        c = arc_en_ciel(i / 18.0, 0.80, 1.0)
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                if abs(dx) + abs(dy) > 2:
                    continue
                t.ajouter(x + dx, y + dy, c, 0.55)
    # hexagramme intérieur
    for br in range(6):
        a0 = 2 * math.pi * br / 6 + phase * 2 * math.pi * 0.12
        a1 = a0 + 2 * math.pi * 2 / 6
        for s in range(120):
            u = s / 119.0
            x = CX + (math.cos(a0) * (1 - u) + math.cos(a1) * u) * rayon * 0.46
            y = CY + (math.sin(a0) * (1 - u) + math.sin(a1) * u) * ry * 0.46
            t.ajouter(x, y, arc_en_ciel((u + phase) % 1.0, 0.45, 1.0), 0.40)
    return t.img()


# --------------------------------------------------------------------------
# Colonnes de lumière arc-en-ciel
# --------------------------------------------------------------------------

def colonnes_lumiere(plan, phase, intensite=1.0):
    t = Toile()
    for i, (x, y, hh, lw, te, av) in enumerate(plan):
        ph = (phase + i / len(plan)) % 1.0
        mont = min(1.0, ph * 2.2)
        vie = math.sin(min(1.0, ph * 1.4) * math.pi) ** 0.6
        if vie <= 0.02:
            continue
        larg = lw * 0.55
        haut = int((HAUT * 0.9) * mont)
        for j in range(haut):
            yy = y - j
            if yy < 0:
                break
            u = j / max(haut - 1, 1)
            h = (te + u * 0.55 + phase * 0.6) % 1.0
            c = arc_en_ciel(h, 0.62, 1.0)
            att = (1 - u) ** 0.55 * vie * intensite
            lw2 = larg * (1.0 + u * 0.55)
            for dx in range(int(-lw2), int(lw2) + 1):
                d = abs(dx) / max(lw2, 1e-6)
                t.ajouter(x + dx, yy, c, (1 - d) ** 2.2 * 0.42 * att)
    return t.img()


# --------------------------------------------------------------------------
# Anneau de foudre arc-en-ciel
# --------------------------------------------------------------------------

def cercle_foudre(phase, rayon=118, hauteur=54, brins=9, graine=0, intensite=1.0):
    """
    Anneau de foudre : des arcs brisés sautent d'un point à l'autre d'une
    ellipse qui ceinture le boss. La graine change à chaque image, ce qui
    donne le grésillement.
    """
    t = Toile()
    rng = np.random.default_rng(graine * 977 + 13)
    ry = rayon * 0.40
    for b in range(brins):
        a0 = 2 * math.pi * (b / brins) + phase * 2 * math.pi * 0.6
        a1 = a0 + 2 * math.pi / brins * rng.uniform(0.7, 1.45)
        teinte = ((b / brins) + phase) % 1.0
        c = arc_en_ciel(teinte, 0.70, 1.0)
        cv = arc_en_ciel(teinte, 0.20, 1.0)
        seg = 16
        pts = []
        for s in range(seg + 1):
            u = s / seg
            a = a0 + (a1 - a0) * u
            r = rayon * (1.0 + rng.uniform(-0.055, 0.055))
            zz = math.sin(u * math.pi) * hauteur * rng.uniform(0.35, 1.0)
            x = CX + math.cos(a) * r
            y = CY + math.sin(a) * ry - zz
            pts.append((x, y))
        for s in range(seg):
            x0, y0 = pts[s]
            x1, y1 = pts[s + 1]
            n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
            for k in range(n + 1):
                u = k / max(n, 1)
                x, y = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
                t.ajouter(x, y, cv, 0.85 * intensite)
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    t.ajouter(x + dx, y + dy, c, 0.34 * intensite)
        # embranchements
        if rng.random() < 0.6:
            i0 = rng.integers(3, seg - 2)
            x, y = pts[i0]
            ang = rng.uniform(0, 2 * math.pi)
            for k in range(int(rng.integers(5, 14))):
                x += math.cos(ang) * 1.6
                y += math.sin(ang) * 1.2
                ang += rng.uniform(-0.5, 0.5)
                t.ajouter(x, y, c, 0.5 * intensite * (1 - k / 14))
    return t.img()


# --------------------------------------------------------------------------
# Sphère d'enveloppement
# --------------------------------------------------------------------------

def sphere(rayon, phase, opacite=1.0, fracture=0.0, w=LARG, h=HAUT,
           cx=None, cy=None):
    """
    Sphère de cristal translucide qui enveloppe Terapagos : facettes
    hexagonales, lisière lumineuse, et fracture progressive à l'éclatement.
    """
    cx = CX if cx is None else cx
    cy = (CY - 40) if cy is None else cy
    t = Toile(w, h)
    if rayon < 1:
        return t.img()
    rng = np.random.default_rng(4)
    for y in range(int(cy - rayon) - 2, int(cy + rayon) + 3):
        for x in range(int(cx - rayon) - 2, int(cx + rayon) + 3):
            dx, dy = (x - cx) / rayon, (y - cy) / rayon
            d = math.hypot(dx, dy)
            if d > 1.0:
                continue
            # facettes hexagonales sur la sphère
            u = dx * 6.0 + phase * 2.0
            v = dy * 6.0 * 1.15
            fx = abs(u - round(u))
            fy = abs(v - round(v))
            bord = fx < 0.10 or fy < 0.10
            z = math.sqrt(max(0.0, 1 - d * d))
            ecl = max(0.0, (-dx * 0.45 - dy * 0.55 + z * 0.75))
            teinte = (phase * 0.7 + d * 0.45) % 1.0
            c = arc_en_ciel(teinte, 0.42 - 0.25 * ecl, 1.0)
            a = (0.10 + 0.42 * ecl) * opacite
            if d > 0.88:                                # lisière vive
                a = (0.55 + 0.45 * (d - 0.88) / 0.12) * opacite
                c = arc_en_ciel(teinte, 0.30, 1.0)
            if bord:
                a *= 1.7
            if fracture > 0:
                fis = abs(math.sin(math.atan2(dy, dx) * 5.0 + phase * 3.0))
                if fis < fracture * 0.42:
                    a = 0.0
            t.ajouter(x, y, c, min(1.0, a))
    return t.img()


def eclats(phase, n=40, w=LARG, h=HAUT, cx=None, cy=None, portee=140):
    """Éclats de cristal projetés à l'éclatement de la sphère."""
    cx = CX if cx is None else cx
    cy = (CY - 40) if cy is None else cy
    t = Toile(w, h)
    rng = np.random.default_rng(21)
    for i in range(n):
        a = 2 * math.pi * i / n + rng.uniform(-0.14, 0.14)
        d = portee * phase * rng.uniform(0.55, 1.25)
        x, y = cx + math.cos(a) * d, cy + math.sin(a) * d * 0.72
        c = arc_en_ciel((i / n + phase) % 1.0, 0.55, 1.0)
        L = max(1, int(5 * (1 - phase)))
        for k in range(L):
            t.ajouter(x - math.cos(a) * k, y - math.sin(a) * k * 0.72,
                      c, (1 - phase) * (1 - k / max(L, 1)) * 0.9)
    return t.img()


# --------------------------------------------------------------------------
# Sprites de Terapagos, pour la séquence de transformation
# --------------------------------------------------------------------------

def sprite_terapagos(chemin_dossier, direction=0, image=0):
    import xml.etree.ElementTree as ET
    r = ET.parse(f"{chemin_dossier}/AnimData.xml").getroot()
    a = next(x for x in r.find("Anims")
             if x.findtext("Name") == "Idle" and x.findtext("CopyOf") is None)
    w, h = int(a.findtext("FrameWidth")), int(a.findtext("FrameHeight"))
    im = Image.open(f"{chemin_dossier}/Idle-Anim.png").convert("RGBA")
    cols = im.size[0] // w
    c = image % cols
    return im.crop((c * w, direction * h, (c + 1) * w, (direction + 1) * h))


def teinter(im, couleur, force):
    a = np.array(im, dtype=np.float32)
    m = a[..., 3] > 0
    a[m, :3] = a[m, :3] * (1 - force) + np.array(couleur, dtype=np.float32) * force
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def blanchir(im, force):
    return teinter(im, (255, 255, 255), force)


# --------------------------------------------------------------------------
# Séquence de transformation
# --------------------------------------------------------------------------

VW, VH = 208, 248            # case de la feuille d'effet
VCX, VCY = VW // 2, 176      # centre au sol dans la case

PHASES = [
    ("appel", 6), ("montee", 6), ("enveloppe", 6), ("suspens", 3),
    ("eclat", 4), ("revelation", 7),
]


def image_transformation(i, total, terastal, stellaire):
    """Une image de la séquence, sur fond transparent."""
    ph = i / max(total - 1, 1)
    fond = Toile(VW, VH)
    dessus = Toile(VW, VH)

    # bornes des phases
    b, seq = 0, {}
    for nom, n in PHASES:
        seq[nom] = (b, b + n)
        b += n

    def dans(nom):
        d, f = seq[nom]
        return d <= i < f

    def u(nom):
        d, f = seq[nom]
        return min(1.0, max(0.0, (i - d) / max(f - d - 1, 1)))

    # cercle rituel au sol, présent tout du long, qui s'intensifie
    inten = 0.35 + 0.65 * ph
    ry = 62 * 0.42
    for k, (rr, vit) in enumerate(((1.0, 1.0), (0.66, -1.3))):
        n = int(2 * math.pi * 62 * rr * 1.5)
        for s in range(n):
            a = 2 * math.pi * s / n
            h = (a / (2 * math.pi) + ph * vit) % 1.0
            fond.ajouter(VCX + math.cos(a) * 62 * rr,
                         VCY + math.sin(a) * ry * rr,
                         arc_en_ciel(h, 0.62, 1.0), 0.5 * inten)

    corps_y = VCY
    sp = terastal
    voile = 0.0

    if dans("appel"):
        k = u("appel")
        for j in range(26):
            a = 2 * math.pi * j / 26 + k * 3.0
            d = 96 * (1 - k) + 14
            fond.ajouter(VCX + math.cos(a) * d, VCY - 26 + math.sin(a) * d * 0.5,
                         arc_en_ciel((j / 26 + k) % 1.0, 0.6, 1.0), 0.8 * k)
    elif dans("montee"):
        k = u("montee")
        corps_y = VCY - int(10 * k)
        voile = 0.18 * k
        dessus.a = np.maximum(dessus.a, np.array(
            cercle_foudre(k, rayon=74, hauteur=34, brins=7, graine=i,
                          intensite=0.9 * k).resize((VW, VH)), dtype=np.float32)) \
            if False else dessus.a
        for j in range(9):
            a = 2 * math.pi * j / 9 + k * 5.0
            for s in range(int(30 * k)):
                y = VCY - s * 2.2
                fond.ajouter(VCX + math.cos(a) * 40 * (1 - s / 40.0),
                             y, arc_en_ciel((j / 9 + k) % 1.0, 0.6, 1.0),
                             0.55 * (1 - s / 34.0) * k)
    elif dans("enveloppe"):
        k = u("enveloppe")
        corps_y = VCY - 10
        voile = 0.18 + 0.35 * k
        r = 30 + 46 * k
        dessus.a = np.maximum(dessus.a, np.array(
            sphere(r, ph, opacite=0.55 + 0.45 * k, w=VW, h=VH,
                   cx=VCX, cy=VCY - 44), dtype=np.float32))
    elif dans("suspens"):
        k = u("suspens")
        corps_y = VCY - 10
        voile = 0.55 + 0.45 * k
        dessus.a = np.maximum(dessus.a, np.array(
            sphere(76, ph, opacite=1.0, w=VW, h=VH, cx=VCX, cy=VCY - 44),
            dtype=np.float32))
        for y in range(VH):
            for x in range(VW):
                dessus.ajouter(x, y, (255, 255, 255), 0.35 * k)
    elif dans("eclat"):
        k = u("eclat")
        sp = stellaire
        corps_y = VCY - 6
        voile = max(0.0, 0.85 - k)
        dessus.a = np.maximum(dessus.a, np.array(
            sphere(76 + 26 * k, ph, opacite=max(0.0, 0.7 - k),
                   fracture=k * 2.2, w=VW, h=VH, cx=VCX, cy=VCY - 44),
            dtype=np.float32))
        dessus.a = np.maximum(dessus.a, np.array(
            eclats(k, 44, VW, VH, VCX, VCY - 44, 130), dtype=np.float32))
        for y in range(VH):
            for x in range(VW):
                dessus.ajouter(x, y, (255, 255, 255), max(0.0, 0.55 - k * 0.8))
    else:
        k = u("revelation")
        sp = stellaire
        corps_y = VCY - int(4 * (1 - k))
        # colonnes de lumière qui jaillissent autour
        for j in range(6):
            a = 2 * math.pi * j / 6 + 0.2
            x = VCX + math.cos(a) * 66
            hh = int(150 * min(1.0, k * 1.7))
            for s in range(hh):
                uu = s / max(hh - 1, 1)
                fond.ajouter(x, VCY + math.sin(a) * 26 - s,
                             arc_en_ciel((j / 6 + uu * 0.5 + ph) % 1.0, 0.6, 1.0),
                             (1 - uu) ** 0.6 * 0.5 * (1 - k * 0.35))
                fond.ajouter(x + 1, VCY + math.sin(a) * 26 - s,
                             arc_en_ciel((j / 6 + uu * 0.5 + ph) % 1.0, 0.4, 1.0),
                             (1 - uu) ** 0.6 * 0.3 * (1 - k * 0.35))
        dessus.a = np.maximum(dessus.a, np.array(
            cercle_foudre_local(k, VW, VH, VCX, VCY, 78, 40, 8, i,
                                0.9 * (1 - k * 0.4)), dtype=np.float32))

    corps = blanchir(sp, voile)
    lame = Image.new("RGBA", (VW, VH), (0, 0, 0, 0))
    lame.paste(corps, (VCX - corps.size[0] // 2, corps_y - corps.size[1]), corps)

    out = Image.alpha_composite(fond.img(), lame)
    return Image.alpha_composite(out, dessus.img())


def cercle_foudre_local(phase, w, h, cx, cy, rayon, hauteur, brins, graine,
                        intensite):
    t = Toile(w, h)
    rng = np.random.default_rng(graine * 977 + 13)
    ry = rayon * 0.40
    for b in range(brins):
        a0 = 2 * math.pi * (b / brins) + phase * 2 * math.pi * 0.6
        a1 = a0 + 2 * math.pi / brins * rng.uniform(0.7, 1.45)
        teinte = ((b / brins) + phase) % 1.0
        c = arc_en_ciel(teinte, 0.70, 1.0)
        cv = arc_en_ciel(teinte, 0.20, 1.0)
        seg = 14
        pts = []
        for s in range(seg + 1):
            uu = s / seg
            a = a0 + (a1 - a0) * uu
            r = rayon * (1.0 + rng.uniform(-0.055, 0.055))
            zz = math.sin(uu * math.pi) * hauteur * rng.uniform(0.35, 1.0)
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * ry - zz))
        for s in range(seg):
            x0, y0 = pts[s]
            x1, y1 = pts[s + 1]
            n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
            for k in range(n + 1):
                uu = k / max(n, 1)
                x, y = x0 + (x1 - x0) * uu, y0 + (y1 - y0) * uu
                t.ajouter(x, y, cv, 0.85 * intensite)
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    t.ajouter(x + dx, y + dy, c, 0.34 * intensite)
    return t.img()


# --------------------------------------------------------------------------
# Assemblage
# --------------------------------------------------------------------------

CALQUES = ["00_vide", "01_sol_cristal", "02_veines", "03_piliers_arriere",
           "04_cercle_rituel", "05_boss", "06_piliers_avant",
           "07_colonnes_lumiere", "08_cercle_foudre", "09_sphere",
           "10_eclairage"]

N_BOUCLE = 12                      # images de la boucle d'ambiance


def fond_vide():
    a = np.zeros((HAUT, LARG, 4), dtype=np.uint8)
    ys, xs = np.mgrid[0:HAUT, 0:LARG]
    d = np.sqrt(((xs - CX) / (LARG * 0.7)) ** 2 + ((ys - CY) / (HAUT * 0.8)) ** 2)
    k = np.clip(1.0 - d, 0, 1)[..., None]
    a[..., :3] = (np.array(P["vide"]) + k * np.array([18, 22, 60])).astype(np.uint8)
    a[..., 3] = 255
    return Image.fromarray(a, "RGBA")


def eclairage():
    """Vignette et voile froid, posés en dernier."""
    t = Toile()
    ys, xs = np.mgrid[0:HAUT, 0:LARG]
    d = np.sqrt(((xs - CX) / (LARG * 0.62)) ** 2 + ((ys - CY) / (HAUT * 0.72)) ** 2)
    v = np.clip((d - 0.72) * 1.7, 0, 1)
    a = np.zeros((HAUT, LARG, 4), dtype=np.uint8)
    a[..., :3] = np.array([4, 5, 16])
    a[..., 3] = (v * 205).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def main():
    for d in ("decor", "vfx", "aseprite", "apercus", "sons"):
        os.makedirs(os.path.join(RACINE, d), exist_ok=True)

    print("sol de cristal…")
    sol, cell, arete, lum = sol_cristal()
    pil_arr, pil_av, plan = placer_piliers()
    vide = fond_vide()
    ecl = eclairage()

    boss_stellaire = sprite_terapagos(
        os.path.join(RACINE, "..", "terapagos_stellaire", "sprite", "1024", "0002"))
    boss_terastal = sprite_terapagos(f"{SC}/sprite/1024/0001")

    def calque_boss(sp):
        b = Image.new("RGBA", (LARG, HAUT), (0, 0, 0, 0))
        z = sp.resize((sp.size[0] * 2, sp.size[1] * 2), Image.NEAREST)
        b.paste(z, (CX - z.size[0] // 2, CY - z.size[1] + 8), z)
        return b

    boss = calque_boss(boss_stellaire)

    print("boucle d'ambiance…")
    images = []
    for i in range(N_BOUCLE):
        ph = i / N_BOUCLE
        jeu = {
            "00_vide": vide, "01_sol_cristal": sol,
            "02_veines": veines(cell, arete, ph),
            "03_piliers_arriere": pil_arr,
            "04_cercle_rituel": cercle_rituel(ph),
            "05_boss": boss,
            "06_piliers_avant": pil_av,
            "07_colonnes_lumiere": colonnes_lumiere(plan, ph, 0.85),
            "08_cercle_foudre": cercle_foudre(ph, graine=i),
            "09_sphere": Image.new("RGBA", (LARG, HAUT), (0, 0, 0, 0)),
            "10_eclairage": ecl,
        }
        # le halo des piliers rejoint le calque des colonnes
        jeu["07_colonnes_lumiere"] = Image.alpha_composite(
            jeu["07_colonnes_lumiere"], halo_piliers(plan, ph))
        images.append(jeu)
        print(f"  image {i + 1}/{N_BOUCLE}")

    # décor : PNG par calque, sur la première image
    for nom, im in images[0].items():
        im.save(os.path.join(RACINE, "decor", f"{nom}.png"), optimize=True)
    composer(list(images[0].items())).save(
        os.path.join(RACINE, "decor", "arene.png"), optimize=True)

    aseprite.ecrire_anime(os.path.join(RACINE, "aseprite", "arene.aseprite"),
                          CALQUES, images, (LARG, HAUT), duree_ms=90)

    fr = [composer(list(j.items())) for j in images]
    gif = [f.resize((LARG // 2, HAUT // 2), Image.LANCZOS).convert(
        "P", palette=Image.ADAPTIVE, colors=255) for f in fr]
    gif[0].save(os.path.join(RACINE, "apercus", "arene.gif"), save_all=True,
                append_images=gif[1:], duration=90, loop=0, disposal=2,
                optimize=True)

    print("transformation…")
    total = sum(n for _, n in PHASES)
    trans = [image_transformation(i, total, boss_terastal, boss_stellaire)
             for i in range(total)]
    feuille = Image.new("RGBA", (VW * total, VH), (0, 0, 0, 0))
    for i, im in enumerate(trans):
        feuille.paste(im, (i * VW, 0), im)
    feuille.save(os.path.join(RACINE, "vfx", "transformation-Anim.png"),
                 optimize=True)
    aseprite.ecrire_anime(
        os.path.join(RACINE, "aseprite", "transformation.aseprite"),
        ["transformation"], [{"transformation": im} for im in trans],
        (VW, VH), duree_ms=[110] * total)
    g = [im.convert("RGBA") for im in trans]
    fond_g = Image.new("RGBA", (VW, VH), (18, 18, 28, 255))
    g = [Image.alpha_composite(fond_g, im).convert("P", palette=Image.ADAPTIVE,
                                                   colors=255) for im in g]
    g[0].save(os.path.join(RACINE, "apercus", "transformation.gif"),
              save_all=True, append_images=g[1:], duration=110, loop=0,
              disposal=2, optimize=True)

    print("effets isolés…")
    # anneau de foudre, bouclable
    fw, fh, n = 320, 200, 12
    sheet = Image.new("RGBA", (fw * n, fh), (0, 0, 0, 0))
    gf = []
    for i in range(n):
        im = cercle_foudre_local(i / n, fw, fh, fw // 2, fh - 60, 118, 54, 9, i, 1.0)
        sheet.paste(im, (i * fw, 0), im)
        gf.append(im)
    sheet.save(os.path.join(RACINE, "vfx", "cercle_foudre-Anim.png"), optimize=True)
    aseprite.ecrire_anime(os.path.join(RACINE, "aseprite", "cercle_foudre.aseprite"),
                          ["foudre"], [{"foudre": im} for im in gf], (fw, fh), 80)

    # sphère
    sw, sh, n2 = 208, 208, 16
    sheet2 = Image.new("RGBA", (sw * n2, sh), (0, 0, 0, 0))
    gs = []
    for i in range(n2):
        k = i / (n2 - 1)
        im = sphere(24 + 74 * min(1.0, k * 1.3), k, opacite=min(1.0, 0.35 + k),
                    fracture=max(0.0, (k - 0.8) * 5.0), w=sw, h=sh,
                    cx=sw // 2, cy=sh // 2)
        sheet2.paste(im, (i * sw, 0), im)
        gs.append(im)
    sheet2.save(os.path.join(RACINE, "vfx", "sphere-Anim.png"), optimize=True)
    aseprite.ecrire_anime(os.path.join(RACINE, "aseprite", "sphere.aseprite"),
                          ["sphere"], [{"sphere": im} for im in gs], (sw, sh), 90)

    # colonne de lumière isolée
    cw, ch, n3 = 96, 384, 16
    sheet3 = Image.new("RGBA", (cw * n3, ch), (0, 0, 0, 0))
    gc = []
    for i in range(n3):
        k = i / (n3 - 1)
        t = Toile(cw, ch)
        haut = int(ch * min(1.0, k * 2.0))
        vie = math.sin(min(1.0, k * 1.25) * math.pi) ** 0.5
        for j in range(haut):
            uu = j / max(haut - 1, 1)
            c = arc_en_ciel((uu * 0.6 + k) % 1.0, 0.62, 1.0)
            lw = 12 * (1 + uu * 0.6)
            for dx in range(int(-lw), int(lw) + 1):
                dd = abs(dx) / lw
                t.ajouter(cw // 2 + dx, ch - 1 - j, c, (1 - dd) ** 2.2 * 0.5 * vie)
        im = t.img()
        sheet3.paste(im, (i * cw, 0), im)
        gc.append(im)
    sheet3.save(os.path.join(RACINE, "vfx", "colonne_lumiere-Anim.png"), optimize=True)
    aseprite.ecrire_anime(os.path.join(RACINE, "aseprite", "colonne_lumiere.aseprite"),
                          ["colonne"], [{"colonne": im} for im in gc], (cw, ch), 70)

    # piliers isolés, pour réemploi
    pl = Image.new("RGBA", (420, 200), (0, 0, 0, 0))
    x = 4
    for i, (hh, lw, te) in enumerate(((150, 44, 0.80), (118, 34, 0.60),
                                      (104, 30, 0.42), (92, 26, 0.20))):
        im = pilier(hh, lw, te, 1.0, graine=11 + i)
        pl.paste(im, (x, 196 - im.size[1]), im)
        x += im.size[0] + 8
    pl.save(os.path.join(RACINE, "decor", "piliers_variantes.png"), optimize=True)

    print("sons…")
    duree = {}
    for nom, (fn, _) in S.CATALOGUE.items():
        duree[nom] = S.ecrire(os.path.join(RACINE, "sons", f"{nom}.wav"), fn())
        print(f"  {nom}.wav  {duree[nom]:.2f} s")

    print("\nterminé.")


if __name__ == "__main__":
    main()
