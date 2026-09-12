# -*- coding: utf-8 -*-
"""
composeur de la clairière de la guilde — zone extérieure en calques.

La clairière fusionne les deux références : le cadre de jungle dense et
sombre qui cerne la carte, et la clairière ensoleillée avec son grand
arbre, son chemin de sable et son grand bassin au nord muni de
plateformes de pierre.

Calques, dans l'ordre de composition :
  00_jungle_bordure   cadre de jungle immergée (opaque, ouvert aux passages)
  01_sol              herbe claire + chemin de sable creusé
  02_bassin           nappe d'eau animée (12 images) + rive de sable
  03_plateformes      plateformes de pierre posées sur l'eau
  04_arbre            grand arbre central et son ombre de contact
  05_objets           buissons, rochers, fleurs, souches…
  06_lueurs           reflets clairs de la végétation, scintillants (animé)
  07_lumiere          puits de lumière au-dessus du bassin (animé, additif)
  08_particules       pollen en dérive / lucioles la nuit (animé, additif)
  09_bordure_avant    feuilles qui débordent, interrompues aux passages
  10_vignette         vignette (multiplicatif)

Sorties :
  calques/jour|nuit/         une image par calque (+ _00..11 pour les animés)
  tiled/clairiere_jour|nuit.tmj   cartes Tiled 8×8 + bassin_eau.tsx animé
  clairiere_jour|nuit.aseprite    un fichier par ambiance, 12 images
  apercus/                   aperçu fixe, GIF et visionneuse HTML
"""

from __future__ import annotations

import base64
import io
import json
import math
import os
import struct
import sys
import zlib
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent
SOURCES = RACINE / "sources_ia"
CALQUES = RACINE / "calques"
TILED = RACINE / "tiled"
APERCUS = RACINE / "apercus"

LARG, HAUT = 1024, 768
T = 8                                    # grille du dépôt
N_IMG = 12                               # images d'animation
PAS_MS = 110                             # durée d'un pas (~DPLA, 6 tics/60 Hz)

MODES = ("jour", "nuit")

CALQUE_IDS = [
    ("00_jungle_bordure", "Bordure de jungle", False),
    ("01_sol", "Sol et chemin de sable", False),
    ("02_bassin", "Bassin (animé)", True),
    ("03_plateformes", "Plateformes de pierre", False),
    ("04_arbre", "Grand arbre", False),
    ("05_objets", "Objets", False),
    ("06_lueurs", "Lueurs (animé)", True),
    ("07_lumiere", "Lumière (animé, additif)", True),
    ("08_particules", "Particules (animé, additif)", True),
    ("09_bordure_avant", "Bordure avant, coupée aux passages", False),
    ("10_vignette", "Vignette (multiplicative)", False),
]
ANIMES = {cid for cid, _, anim in CALQUE_IDS if anim}
ORDRE = [cid for cid, _, _ in CALQUE_IDS]
ADDITIFS = {"06_lueurs", "07_lumiere", "08_particules"}

# ---------------------------------------------------------------- géométrie
YS, XS = np.mgrid[0:HAUT, 0:LARG].astype(np.float32)


def formes_de_base():
    """Ellipse de clairière + bruit : masques jungle, bande, ouvertures."""
    dx = (XS - LARG / 2) / (LARG / 2)
    dy = (YS - HAUT / 2) / (HAUT / 2)
    d = np.sqrt(dx * dx + dy * dy)
    n = (np.sin(XS * 0.011 + 1.0) + np.sin(YS * 0.013 + 2.3)
         + np.sin((XS + YS) * 0.007) + np.sin((XS - YS) * 0.009 + 0.7)) / 4
    val = d + 0.055 * n
    # la jungle s'écarte autour du bassin : l'eau mord dans la bordure
    creux = 0.17 * np.exp(-(((XS - 512) / 330.0) ** 2 + ((YS - 170) / 260.0) ** 2))
    valc = val - creux
    jungle = valc > 0.60
    bande = (valc > 0.60) & (valc < 0.92)
    # passages percés de part en part ; seule la frange la plus externe
    # (feuilles en surplomb) reste au-dessus du passage
    ouvertures = (
        (XS > 470) & (XS < 554) & (YS < 150),            # nord : canal du bassin
        (YS > HAUT - 110) & (XS > 436) & (XS < 594),     # sud
        (XS < 116) & (YS > 332) & (YS < 456),            # ouest
        (XS > LARG - 116) & (YS > 292) & (YS < 440),     # est
    )
    coupe = np.zeros((HAUT, LARG), bool)
    for o in ouvertures:
        coupe |= jungle & o & (valc < 0.98)
    jungle_f = jungle & ~coupe
    # le feuillage avant est la frange intérieure qui recouvre la clairière
    avant = jungle_f & (valc > 0.60) & (valc < 0.72)
    return jungle_f, avant, val, ouvertures, valc


def masque_eau():
    """Grand bassin au nord + canal qui fuit vers le bord."""
    e = (((XS - 512) / 330.0) ** 2 + ((YS - 195) / 118.0) ** 2
         + 0.05 * np.sin(XS * 0.021) * np.sin(YS * 0.031))
    m = e < 1.0
    m |= (XS > 484) & (XS < 540) & (YS < 200)          # le canal nord
    return m


def grille_de(mask):
    """Échantillonne un masque pixel sur la grille de tuiles."""
    g = np.zeros((HAUT // T, LARG // T), bool)
    for gy in range(g.shape[0]):
        for gx in range(g.shape[1]):
            cy, cx = gy * T + T / 2, gx * T + T / 2
            if mask[int(cy), int(cx)]:
                g[gy, gx] = True
    return g


def dilater_grille(g, r=1):
    p = np.pad(g, r, constant_values=False)
    out = np.zeros_like(g)
    for dy in range(2 * r + 1):
        for dx in range(2 * r + 1):
            out |= p[dy:dy + g.shape[0], dx:dx + g.shape[1]]
    return out


def chemin_masque():
    """Traces de sable : ouest→sud (devant l'arbre) et vers l'est."""
    m = np.zeros((HAUT, LARG), bool)
    traces = [
        ([(0, 392), (180, 402), (318, 442), (430, 520), (508, 596),
          (522, 664), (512, HAUT)], 34, 40),
        ([(736, 292), (878, 342), (LARG, 368)], 30, 30),
        ([(508, 596), (430, 470), (360, 330)], 26, 26),   # écart vers le bassin
    ]
    for pts, w0, w1 in traces:
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            seg = max(int(math.hypot(x1 - x0, y1 - y0)), 1)
            for s in range(seg + 1):
                u = s / seg
                x, y = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
                w = (w0 + (w1 - w0) * u) / 2
                ww = w * (1 + 0.16 * math.sin(y * 0.05) * math.sin(x * 0.04))
                m[int(y - ww):int(y + ww) + 1,
                  int(x - ww):int(x + ww) + 1] = True
    return m


# ---------------------------------------------------------------- textures
def recadrer_noir(im, seuil=14, marge=6):
    """Retire le cadre noir pur autour d'un élément isolé."""
    a = np.asarray(im.convert("RGB"), dtype=np.float32)
    m = a.mean(axis=2) > seuil
    ys, xs = np.nonzero(m)
    if len(ys) == 0:
        return im
    y0, y1 = max(0, ys.min() + marge), min(im.size[1], ys.max() + 1 - marge)
    x0, x1 = max(0, xs.min() + marge), min(im.size[0], xs.max() + 1 - marge)
    return im.crop((x0, y0, x1, y1))


def recadrer_voile(im, part=0.35):
    """Retire le voile désaturé qui entoure une texture générée."""
    a = np.asarray(im.convert("RGB"), dtype=np.float32)
    lum = a.mean(axis=2)
    sat = a.max(axis=2) - a.min(axis=2)
    contenu = (lum < 112) | (sat > 40)
    h, w = contenu.shape
    lignes = np.nonzero(contenu.mean(axis=1) > part)[0]
    cols = np.nonzero(contenu.mean(axis=0) > part)[0]
    if len(lignes) < h // 2 or len(cols) < w // 2:
        return im
    return im.crop((cols[0], lignes[0], cols[-1] + 1, lignes[-1] + 1))


def pave(chemin, couleurs, pas=128, teinte=None):
    """Texture répétée, bords fondus pour éviter la grille, couleurs bornées."""
    im = chemin if isinstance(chemin, Image.Image) \
        else Image.open(chemin).convert("RGB")
    im = im.convert("RGB")
    c = min(im.size)
    im = im.crop(((im.size[0] - c) // 2, (im.size[1] - c) // 2,
                  (im.size[0] - c) // 2 + c, (im.size[1] - c) // 2 + c))
    im = im.resize((pas, pas), Image.Resampling.LANCZOS)
    a = np.asarray(im, dtype=np.float32)
    b = max(6, pas // 6)
    r = np.linspace(0, 1, b)[:, None, None]
    a[:b] = a[:b] * r + a[-b:][::-1] * (1 - r)
    r2 = np.linspace(0, 1, b)[None, :, None]
    a[:, :b] = a[:, :b] * r2 + a[:, -b:][:, ::-1] * (1 - r2)
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    im = im.quantize(colors=couleurs, method=Image.Quantize.MAXCOVERAGE,
                     dither=Image.Dither.NONE).convert("RGB")
    im = im.resize((pas * 2, pas * 2), Image.Resampling.NEAREST)
    if teinte is not None:
        a = np.asarray(im, dtype=np.float32) * np.array(teinte, np.float32)
        im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    out = Image.new("RGB", (LARG, HAUT))
    for y in range(0, HAUT, im.size[1]):
        for x in range(0, LARG, im.size[0]):
            out.paste(im, (x, y))
    return out


def detourer(im, seuil=30, couleurs=40):
    """Détoure un élément sur fond noir, sans liseré."""
    im = im.filter(ImageFilter.MedianFilter(3))
    q = im.quantize(colors=couleurs, method=Image.Quantize.MAXCOVERAGE,
                    dither=Image.Dither.NONE).convert("RGBA")
    a = np.array(q)
    lum = a[..., :3].astype(np.float32).mean(axis=2)
    a[..., 3] = np.where(lum > seuil, 255, 0)
    m = a[..., 3] > 0
    pad = np.pad(m, 1, constant_values=False)
    v = np.zeros_like(m, dtype=int)
    for dy in (0, 1, 2):
        for dx in (0, 1, 2):
            if dy == 1 and dx == 1:
                continue
            v += pad[dy:dy + m.shape[0], dx:dx + m.shape[1]].astype(int)
    a[..., 3] = np.where(m & (v >= 3), 255, 0)
    return Image.fromarray(a, "RGBA")


def objets_de(im, aire_min=600, erosion=0):
    """Composantes connexes, triées par aire décroissante. L'érosion casse
    les ponts fins (franges de mousse) avant l'étiquetage."""
    a = np.array(im)
    m = a[..., 3] > 0
    if erosion > 0:
        p = np.pad(m, erosion, constant_values=False)
        me = np.ones_like(m)
        for dy in range(2 * erosion + 1):
            for dx in range(2 * erosion + 1):
                me &= p[dy:dy + m.shape[0], dx:dx + m.shape[1]]
        m_lab = me
    else:
        m_lab = m
    h, w = m.shape
    vus = np.zeros_like(m_lab, bool)
    out = []
    e = erosion + 2
    for y0 in range(h):
        for x0 in range(w):
            if not m_lab[y0, x0] or vus[y0, x0]:
                continue
            q = deque([(y0, x0)])
            vus[y0, x0] = True
            xs0 = xs1 = x0
            ys0 = ys1 = y0
            n = 0
            while q:
                y, x = q.popleft()
                n += 1
                xs0, xs1 = min(xs0, x), max(xs1, x)
                ys0, ys1 = min(ys0, y), max(ys1, y)
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < h and 0 <= nx < w and m_lab[ny, nx] and not vus[ny, nx]:
                            vus[ny, nx] = True
                            q.append((ny, nx))
            if n >= 40 and (xs1 - xs0 + 1) * (ys1 - ys0 + 1) >= aire_min:
                ca = im.crop((max(0, xs0 - e), max(0, ys0 - e),
                              min(w, xs1 + 1 + e), min(h, ys1 + 1 + e)))
                ca = ca.copy()
                caq = np.array(ca)
                caq[caq[..., 3] < 90] = 0
                out.append(Image.fromarray(caq, "RGBA"))
    out.sort(key=lambda o: -o.size[0] * o.size[1])
    return out


# ---------------------------------------------------------------- effets
def rayons(cx, base, lw, hauteur, couleur, force):
    t = np.zeros((HAUT, LARG, 4), dtype=np.float32)
    for j in range(hauteur):
        y = base - j
        if not (0 <= y < HAUT):
            continue
        u = j / max(hauteur - 1, 1)
        l = lw * (1 + u * 0.9)
        fmax = force * (1 - u) ** 0.8
        for x in range(int(cx - l), int(cx + l) + 1):
            if not (0 <= x < LARG):
                continue
            dd = abs(x - cx) / max(l, 1e-6)
            f = (1 - dd) ** 2.2 * fmax
            t[y, x, :3] = np.minimum(255, t[y, x, :3] + np.array(couleur, np.float32) * f)
            t[y, x, 3] = min(255, t[y, x, 3] + 255 * f)
    return Image.fromarray(np.clip(t, 0, 255).astype(np.uint8), "RGBA")


def nappe_lumiere(cx, cy, rx, ry, couleur, force):
    ys, xs = np.mgrid[0:HAUT, 0:LARG].astype(np.float32)
    dd = np.sqrt(((xs - cx) / rx) ** 2 + ((ys - cy) / ry) ** 2)
    f = np.clip(1 - dd, 0, 1) ** 1.8 * force
    a = np.zeros((HAUT, LARG, 4), np.uint8)
    a[..., :3] = np.clip(np.array(couleur, np.float32)[None, None, :] * f[..., None], 0, 255)
    a[..., 3] = np.clip(f * 255, 0, 255)
    return Image.fromarray(a, "RGBA")


def particules(phase, couleur, n=64, graine=11, croix=0.35):
    t = np.zeros((HAUT, LARG, 4), dtype=np.float32)
    rng = np.random.default_rng(graine)
    for i in range(n):
        bx, by = rng.uniform(0, LARG), rng.uniform(0, HAUT)
        v = rng.uniform(0.4, 1.4)
        x = (bx + phase * 14 * v) % LARG
        y = (by - phase * 22 * v) % HAUT
        f = 0.26 + 0.34 * (0.5 + 0.5 * math.sin(phase * 6.283 * 2 + i * 0.9))
        iy, ix = int(y) % HAUT, int(x) % LARG
        t[iy, ix, :3] = np.minimum(255, t[iy, ix, :3] + np.array(couleur, np.float32) * f)
        t[iy, ix, 3] = min(255, t[iy, ix, 3] + 255 * f)
        if croix:
            for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
                yy, xx = (iy + dy) % HAUT, (ix + dx) % LARG
                t[yy, xx, :3] = np.minimum(
                    255, t[yy, xx, :3] + np.array(couleur, np.float32) * f * croix)
                t[yy, xx, 3] = min(255, t[yy, xx, 3] + 255 * f * croix)
    return Image.fromarray(np.clip(t, 0, 255).astype(np.uint8), "RGBA")


def scintiller(base, graine=7):
    a = np.array(base)
    m = a[..., 3] > 0
    ys, xs = np.nonzero(m)
    if len(ys) == 0:
        return [base.copy() for _ in range(N_IMG)]
    rng = np.random.default_rng(graine)
    sema = rng.uniform(0, 6.283, size=len(ys))
    base_px = a[ys, xs].astype(np.float32)
    out = []
    for k in range(N_IMG):
        f = 0.55 + 0.45 * np.sin(k / N_IMG * 6.283 * 2 + sema)
        b = a.copy()
        b[ys, xs, :3] = np.clip(base_px[:, :3] * f[:, None], 0, 255).astype(np.uint8)
        out.append(Image.fromarray(b, "RGBA"))
    return out


def vignette(force):
    ys, xs = np.mgrid[0:HAUT, 0:LARG].astype(np.float32)
    d = np.sqrt(((xs - LARG / 2) / (LARG * 0.68)) ** 2
                + ((ys - HAUT / 2) / (HAUT * 0.70)) ** 2)
    v = np.clip((d - 0.70) * 2.0, 0, 1)
    a = np.zeros((HAUT, LARG, 4), dtype=np.uint8)
    a[..., :3] = np.array([6, 12, 8])
    a[..., 3] = (v * force).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def composer(jeu, mode="jour"):
    out = np.zeros((HAUT, LARG, 4), dtype=np.float32)
    for nom in ORDRE:
        v = jeu[nom]
        im = v[0] if isinstance(v, list) else v
        if im is None:
            continue
        a = np.asarray(im.convert("RGBA"), dtype=np.float32)
        k = a[..., 3:4] / 255.0
        if nom in ADDITIFS:
            out[..., :3] = np.minimum(255.0, out[..., :3] + a[..., :3] * k)
            out[..., 3] = np.minimum(255.0, out[..., 3] + a[..., 3])
        elif nom == "10_vignette":
            out[..., :3] = out[..., :3] * (1 - a[..., :3] / 255.0 * k)
        else:
            out[..., :3] = a[..., :3] * k + out[..., :3] * (1 - k)
            out[..., 3] = np.minimum(255.0, a[..., 3] + out[..., 3] * (1 - k[..., 0]))
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")


def nuit(im, k=(0.34, 0.36, 0.52), plus=(7, 8, 22)):
    a = np.array(im.convert("RGBA"))
    a[..., :3] = np.rint(a[..., :3] * np.array(k, np.float32)
                         + np.array(plus, np.float32)).clip(0, 255).astype(np.uint8)
    a[a[..., 3] == 0] = 0
    return Image.fromarray(a, "RGBA")


# ---------------------------------------------------------------- assemblage
ARBRE_XY = (512, 596)


def construire():
    print("— textures")
    jungle_im = pave(recadrer_voile(Image.open(SOURCES / "jungle_bordure.png")),
                     couleurs=36, pas=170, teinte=(0.94, 1.03, 0.92))
    herbe = pave(SOURCES / "herbe_claire.png", couleurs=26, pas=112,
                 teinte=(0.95, 0.97, 0.88))
    sable = pave(SOURCES / "sable.png", couleurs=16, pas=96,
                 teinte=(1.02, 0.99, 0.94))
    eau_pave = pave(recadrer_noir(Image.open(SOURCES / "tuile_eau.png")),
                    couleurs=24, pas=120)

    print("— formes")
    jungle_m, avant_m, val, ouvertures, valc = formes_de_base()
    eau_m = masque_eau() & ~jungle_m
    chemin_m = chemin_masque() & ~jungle_m & ~eau_m
    g_eau = grille_de(eau_m)
    # la rive de sable encadre toujours l'eau, même sur l'angle de jungle :
    # c'est elle qui donne la bordure propre du bassin
    g_rive = dilater_grille(g_eau, 1) & ~g_eau
    g_chemin = grille_de(chemin_m) & ~g_rive

    print("— sol")
    sol = Image.new("RGBA", (LARG, HAUT))
    a = np.array(herbe.convert("RGBA"))
    s = np.array(sable.convert("RGBA"))
    pm = np.zeros((HAUT, LARG), bool)
    for gy in range(g_chemin.shape[0]):
        for gx in range(g_chemin.shape[1]):
            if g_chemin[gy, gx]:
                pm[gy * T:(gy + 1) * T, gx * T:(gx + 1) * T] = True
    a[pm] = s[pm]
    a[..., 3] = np.where(~jungle_m, 255, 0)   # le sol s'arrête où commence la jungle
    sol = Image.fromarray(a, "RGBA")

    print("— jungle et rives")
    jungle_c = np.array(jungle_im.convert("RGBA"))
    jungle_c[..., 3] = np.where(jungle_m, 255, 0)
    jungle_c = jungle_c.astype(np.float32)
    # assombrit la jungle vers l'extérieur : épaisseur immersive, sans noir
    prof = 0.62 - 0.18 * np.clip((valc - 0.60) / 0.45, 0, 1)
    jungle_c[..., :3] = np.clip(jungle_c[..., :3] * prof[..., None], 0, 255)
    jungle_calque = Image.fromarray(jungle_c.astype(np.uint8), "RGBA")

    rive = Image.new("RGBA", (LARG, HAUT))
    ra = np.array(rive)
    sa = np.array(sable.convert("RGBA"))
    for gy in range(g_rive.shape[0]):
        for gx in range(g_rive.shape[1]):
            if g_rive[gy, gx]:
                ra[gy * T:(gy + 1) * T, gx * T:(gx + 1) * T] = \
                    sa[gy * T:(gy + 1) * T, gx * T:(gx + 1) * T]
    rive = Image.fromarray(ra, "RGBA")

    print("— eau animée")
    src = eau_pave
    images_eau = []
    masque_px = np.zeros((HAUT, LARG), bool)
    for gy in range(g_eau.shape[0]):
        for gx in range(g_eau.shape[1]):
            if g_eau[gy, gx]:
                masque_px[gy * T:(gy + 1) * T, gx * T:(gx + 1) * T] = True
    for k in range(N_IMG):
        dx = int(k * 7) % src.size[0]
        dy = int(k * 11) % src.size[1]
        nappe = Image.new("RGB", (LARG + src.size[0], HAUT + src.size[1]))
        for y in range(-src.size[1], HAUT + src.size[1], src.size[1]):
            for x in range(-src.size[0], LARG + src.size[0], src.size[0]):
                nappe.paste(src, (x + dx, y + dy))
        aa = np.asarray(nappe, dtype=np.float32)[:HAUT, :LARG].copy()
        ond = (0.5 + 0.5 * np.sin(np.arange(LARG) * 0.045 + k * 0.6))[None, :] \
            * (0.5 + 0.5 * np.sin(np.arange(HAUT) * 0.038 - k * 0.4))[:, None]
        aa *= (1.0 + 0.06 * ond)[..., None]
        im = Image.fromarray(np.clip(aa, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
        q = np.array(im)
        q[..., 3] = np.where(masque_px, 255, 0)
        images_eau.append(Image.fromarray(q, "RGBA"))

    print("— plateformes")
    pf = detourer(Image.open(SOURCES / "plateformes.png").convert("RGB"))
    objs_pf = objets_de(pf, aire_min=1200, erosion=3)[:5]
    cibles = [96, 76, 118, 64, 46]              # largeurs voulues, en px
    ajustees = []
    for o, c in zip(objs_pf, cibles):
        if o.size[1] > o.size[0] * 1.3:         # plateforme dessinée debout
            o = o.transpose(Image.ROTATE_90)
        ajustees.append(o.resize((c, max(8, int(o.size[1] * c / o.size[0]))),
                                 Image.Resampling.LANCZOS))
    objs_pf = ajustees
    print(f"   {len(objs_pf)} plateformes")
    interieur = g_eau & ~dilater_grille(~g_eau | g_rive, 1)
    cells = [(gy, gx) for gy in range(g_eau.shape[0]) for gx in range(g_eau.shape[1])
             if interieur[gy, gx]]
    rng = np.random.default_rng(5)
    poses = []
    if cells and objs_pf:
        cells.sort(key=lambda c: c[1])
        n = len(objs_pf)
        for i, o in enumerate(objs_pf):
            lo = int(len(cells) * i / n)
            hi = max(int(len(cells) * (i + 1) / n), lo + 1)
            gy, gx = cells[rng.integers(lo, hi)]
            ox = gx * T + T // 2 - o.size[0] // 2
            oy = gy * T + T // 2 - o.size[1] // 2
            poses.append((o, ox, oy))
    plateformes = Image.new("RGBA", (LARG, HAUT))
    pd = Image.new("RGBA", (LARG, HAUT))
    for o, ox, oy in poses:
        sh = Image.new("RGBA", (o.size[0] + 12, o.size[1] + 10), (0, 0, 0, 0))
        Image.Draw2 = None
        from PIL import ImageDraw
        ImageDraw.Draw(sh).ellipse([6, 6, o.size[0] + 6, o.size[1] + 4],
                                   fill=(8, 20, 30, 110))
        pd.alpha_composite(sh, (ox - 6, oy - 4))
        plateformes.alpha_composite(o, (ox, oy))

    print("— grand arbre")
    arbre_src = detourer(Image.open(SOURCES / "arbre.png").convert("RGB"))
    echelle = 340 / arbre_src.size[1]
    arbre = arbre_src.resize((int(arbre_src.size[0] * echelle), 340),
                             Image.Resampling.LANCZOS)
    aa = np.array(arbre)
    aa[..., :3] = (aa[..., :3] // 12) * 12 + 6
    aa[..., 3] = np.where(aa[..., 3] > 110, 255, 0)
    arbre = Image.fromarray(aa, "RGBA")
    ax = ARBRE_XY[0] - arbre.size[0] // 2
    ay = ARBRE_XY[1] - arbre.size[1] + 18
    from PIL import ImageDraw
    ombre = Image.new("RGBA", (LARG, HAUT))
    ImageDraw.Draw(ombre).ellipse(
        [ARBRE_XY[0] - 105, ARBRE_XY[1] - 26, ARBRE_XY[0] + 105, ARBRE_XY[1] + 26],
        fill=(10, 18, 12, 95))
    ombre = ombre.filter(ImageFilter.GaussianBlur(5))
    arbre_calque = Image.new("RGBA", (LARG, HAUT))
    arbre_calque.alpha_composite(ombre)
    arbre_calque.alpha_composite(arbre, (ax, ay))

    print("— objets")
    props_src = objets_de(detourer(Image.open(SOURCES / "props.png").convert("RGB")),
                          aire_min=180, erosion=2)
    print(f"   {len(props_src)} objets découpés")
    objets_calque = Image.new("RGBA", (LARG, HAUT))
    poses_props = []
    rng = np.random.default_rng(23)
    essais = 0
    while len(poses_props) < 22 and essais < 6000:
        essais += 1
        x = int(rng.uniform(130, LARG - 130))
        y = int(rng.uniform(300, HAUT - 120))
        if jungle_m[y, x] or eau_m[max(0, y - 14):y + 14, max(0, x - 14):x + 14].any():
            continue
        if chemin_m[max(0, y - 26):y + 26, max(0, x - 26):x + 26].any():
            continue
        if abs(x - ARBRE_XY[0]) < 130 and abs(y - ARBRE_XY[1]) < 95:
            continue
        if any(abs(x - px) < 74 and abs(y - py) < 64 for px, py in poses_props):
            continue
        poses_props.append((x, y))
    poses_props.sort(key=lambda p: p[1])
    for i, (x, y) in enumerate(poses_props):
        o = props_src[i % len(props_src)]
        e = float(rng.uniform(0.52, 0.78))
        o2 = o.resize((max(8, int(o.size[0] * e)), max(8, int(o.size[1] * e))),
                      Image.Resampling.NEAREST)
        if max(o2.size) > 78:                    # les rochers restent des props
            f2 = 78 / max(o2.size)
            o2 = o2.resize((int(o2.size[0] * f2), int(o2.size[1] * f2)),
                           Image.Resampling.NEAREST)
        omb = Image.new("RGBA", (o2.size[0] + 6, 8), (0, 0, 0, 0))
        ImageDraw.Draw(omb).ellipse([3, 2, o2.size[0] + 3, 7], fill=(10, 16, 10, 80))
        objets_calque.alpha_composite(omb, (x - o2.size[0] // 2 - 3, y - 3))
        objets_calque.alpha_composite(o2, (x - o2.size[0] // 2, y - o2.size[1]))

    print("— bordure avant")
    avant = np.array(jungle_im.convert("RGBA"))
    avant[..., 3] = np.where(avant_m, 255, 0)
    bordure_avant = Image.fromarray(avant, "RGBA")

    print("— lueurs, lumière, particules, vignette")
    lum_j = np.asarray(jungle_calque.convert("RGB"), dtype=np.float32) / 255.0
    lueurs_m = (lum_j[..., 1] - np.maximum(lum_j[..., 0], lum_j[..., 2]) > 0.08) \
        & (lum_j.mean(2) > 0.36) & jungle_m & (val < 0.80)
    ys_l, xs_l = np.nonzero(lueurs_m)
    if len(ys_l) > 170:
        idx = np.random.default_rng(4).choice(len(ys_l), 170, replace=False)
        ys_l, xs_l = ys_l[idx], xs_l[idx]
    lueurs_img = Image.new("RGBA", (LARG, HAUT))
    lb = np.array(lueurs_img)
    lb[ys_l, xs_l] = (230, 255, 170, 255)
    lueurs_img = Image.fromarray(lb, "RGBA")

    jour = {
        "00_jungle_bordure": jungle_calque,
        "01_sol": sol,
        "02_bassin": images_eau,
        "03_plateformes": [Image.alpha_composite(rive, plateformes)],
        "04_arbre": arbre_calque,
        "05_objets": objets_calque,
        "06_lueurs": scintiller(lueurs_img),
        "07_lumiere": [Image.alpha_composite(
            rayons(452, 300, 46, 300, (255, 248, 200), 0.30),
            Image.alpha_composite(
                rayons(548, 310, 40, 310, (255, 248, 200), 0.26),
                rayons(505, 330, 60, 330, (255, 251, 214), 0.22)))]
            + [Image.alpha_composite(
                nappe_lumiere(512, 176, 250, 78, (255, 244, 190), 0.30),
                nappe_lumiere(512, 596, 190, 70, (255, 240, 180), 0.16))]
        ,
        "08_particules": [particules(k / N_IMG, (255, 250, 195)) for k in range(N_IMG)],
        "09_bordure_avant": bordure_avant,
        "10_vignette": vignette(170),
    }
    # la lumière doit respirer : 12 images en jouant sur l'opacité
    base_lum = jour["07_lumiere"][0]
    frames_lum = []
    for k in range(N_IMG):
        f = 0.80 + 0.20 * math.sin(k / N_IMG * 6.283 * 2)
        a = np.array(base_lum)
        a[..., :3] = np.clip(a[..., :3] * f, 0, 255)
        a[..., 3] = np.clip(a[..., 3] * f, 0, 255)
        frames_lum.append(Image.fromarray(a, "RGBA"))
    jour["07_lumiere"] = frames_lum

    print("— déclinaison de nuit")
    nuit_jeu = {
        "00_jungle_bordure": nuit(jour["00_jungle_bordure"], (0.30, 0.34, 0.50), (6, 8, 22)),
        "01_sol": nuit(jour["01_sol"]),
        "02_bassin": [nuit(im) for im in images_eau],
        "03_plateformes": [nuit(jour["03_plateformes"][0])],
        "04_arbre": nuit(jour["04_arbre"]),
        "05_objets": nuit(jour["05_objets"]),
        "06_lueurs": scintiller(lueurs_img, graine=9),
        "07_lumiere": [Image.alpha_composite(
            rayons(452, 300, 46, 300, (150, 180, 255), 0.12),
            rayons(560, 320, 38, 320, (150, 180, 255), 0.10))]
            + [nappe_lumiere(512, 176, 260, 84, (168, 198, 255), 0.22)],
        "08_particules": [particules(k / N_IMG, (225, 255, 160), n=58,
                                     graine=31, croix=0.8) for k in range(N_IMG)],
        "09_bordure_avant": nuit(jour["09_bordure_avant"], (0.30, 0.34, 0.50), (6, 8, 22)),
        "10_vignette": vignette(215),
    }
    base_ln = nuit_jeu["07_lumiere"][0]
    fln = []
    for k in range(N_IMG):
        f = 0.80 + 0.20 * math.sin(k / N_IMG * 6.283 * 2)
        a = np.array(base_ln)
        a[..., :3] = np.clip(a[..., :3] * f, 0, 255)
        a[..., 3] = np.clip(a[..., 3] * f, 0, 255)
        fln.append(Image.fromarray(a, "RGBA"))
    nuit_jeu["07_lumiere"] = fln

    for jeu_mode in (jour, nuit_jeu):
        for cid in ORDRE:
            if not isinstance(jeu_mode[cid], list):
                jeu_mode[cid] = [jeu_mode[cid]]

    return {"jour": jour, "nuit": nuit_jeu}


# ---------------------------------------------------------------- exports
def ecrire_calques(jeu_mode, dossier):
    d = CALQUES / dossier
    d.mkdir(parents=True, exist_ok=True)
    for cid in ORDRE:
        v = jeu_mode[cid]
        if cid in ANIMES:
            for k, im in enumerate(v):
                im.save(d / f"{cid}_{k:02d}.png")
        else:
            v[0].save(d / f"{cid}.png")


def ensemble_de(im, nom, firstgid, dossier_rel):
    """Tileset embarqué : l'image du calque découpée en tuiles 8×8."""
    w, h = im.size
    return {
        "firstgid": firstgid, "name": nom,
        "tilewidth": T, "tileheight": T,
        "tilecount": (w // T) * (h // T), "columns": w // T,
        "image": dossier_rel, "imagewidth": w, "imageheight": h,
        "margin": 0, "spacing": 0,
    }


def donnees_de(im):
    """gid par cellule : 0 = transparent."""
    a = np.array(im.convert("RGBA"))
    cols, rows = im.size[0] // T, im.size[1] // T
    alpha = a[..., 3].reshape(rows, T, cols, T).mean(axis=(1, 3))
    data = []
    first = 1
    for gy in range(rows):
        for gx in range(cols):
            n = 0
            cel = a[gy * T:(gy + 1) * T, gx * T:(gx + 1) * T, 3]
            if (cel > 0).mean() > 0.02:
                n = first + gy * cols + gx
            data.append(n)
    return data


def ecrire_tiled(jeu_mode, mode, strips):
    """Carte .tmj : calques statiques embarqués + bassin animé externe."""
    suffixe = "_nuit" if mode == "nuit" else ""
    nom_eau = f"bassin_eau{suffixe}"
    cols, rows = LARG // T, HAUT // T
    tilesets = []
    layers = []
    gid = 1
    # le tsx animé d'abord
    tilesets.append({
        "firstgid": 1, "name": nom_eau,
        "tilewidth": T, "tileheight": T,
        "columns": strips["cols"], "tilecount": strips["cols"] * strips["rows"],
        "image": f"{nom_eau}.png",
        "imagewidth": strips["cols"] * T, "imageheight": strips["rows"] * T,
        "margin": 0, "spacing": 0,
    })
    gid = 1 + strips["cols"] * strips["rows"]
    data_eau = strips["data"]
    for cid, label, anim in CALQUE_IDS:
        if cid == "02_bassin":
            continue
        im = jeu_mode[cid][0]
        png_rel = f"../calques/{mode}/{cid}_00.png" if anim \
            else f"../calques/{mode}/{cid}.png"
        tilesets.append(ensemble_de(im, cid, gid, png_rel))
        layers.append({
            "id": len(layers) + 2, "name": label, "type": "tilelayer",
            "width": cols, "height": rows, "x": 0, "y": 0,
            "opacity": 1.0, "visible": True,
            "data": donnees_de(im),
        })
        gid += (im.size[0] // T) * (im.size[1] // T)
    # couche d'eau : animation via le tsx
    layers.insert(0, {
        "id": 1, "name": "Bassin (animé)", "type": "tilelayer",
        "width": cols, "height": rows, "x": 0, "y": 0,
        "opacity": 1.0, "visible": True,
        "data": data_eau,
    })
    tm = {
        "type": "map", "version": "1.10", "tiledversion": "1.11.0",
        "orientation": "orthogonal", "renderorder": "right-down",
        "tilewidth": T, "tileheight": T,
        "width": cols, "height": rows,
        "infinite": False,
        "nextlayerid": len(layers) + 1, "nextobjectid": 1,
        "layers": layers, "tilesets": tilesets,
    }
    (TILED / f"clairiere_{mode}.tmj").write_text(
        json.dumps(tm, ensure_ascii=False, separators=(",", ":")))
    # le .tsx externe porte l'animation de chaque cellule d'eau
    cols_s, rows_s = strips["cols"], strips["frame_rows"]
    tiles_anim = []
    for (gy, gx) in strips["cells"]:
        base = gy * strips["cols"] + gx
        frames = [{"tileid": base + f * strips["cols"] * strips["frame_rows"],
                   "duration": PAS_MS} for f in range(N_IMG)]
        tiles_anim.append({"id": base, "animation": frames})
    tsx = {
        "type": "tileset", "version": "1.10", "tiledversion": "1.11.0",
        "name": nom_eau, "tilewidth": T, "tileheight": T,
        "tilecount": strips["cols"] * strips["rows"], "columns": strips["cols"],
        "image": f"{nom_eau}.png",
        "imagewidth": strips["cols"] * T, "imageheight": strips["rows"] * T,
        "margin": 0, "spacing": 0,
        "tiles": tiles_anim,
    }
    (TILED / f"{nom_eau}.tsx").write_text(
        json.dumps(tsx, ensure_ascii=False, separators=(",", ":")))
    # l'image-bande du bassin (12 images empilées, cadrées sur le bassin)
    strips["image"].save(TILED / f"{nom_eau}.png")


def bandeau_bassin(images_eau, g_eau):
    """Découpe le bassin cadré sur 12 images empilées + carte des cells."""
    m = g_eau
    gys, gxs = np.nonzero(m)
    y0, y1 = int(gys.min()), int(gys.max()) + 1
    x0, x1 = int(gxs.min()), int(gxs.max()) + 1
    px0, py0 = x0 * T, y0 * T
    px1, py1 = x1 * T, y1 * T
    fw, fh = px1 - px0, py1 - py0
    strip = Image.new("RGBA", (fw, fh * N_IMG), (0, 0, 0, 0))
    for f, im in enumerate(images_eau):
        strip.paste(im.crop((px0, py0, px1, py1)), (0, f * fh))
    cells = [(int(gy - y0), int(gx - x0)) for gy, gx in zip(*np.nonzero(m))]
    data = [0] * ((LARG // T) * (HAUT // T))
    for gy, gx in zip(*np.nonzero(m)):
        data[int(gy) * (LARG // T) + int(gx)] = 1
    return {
        "image": strip, "cols": fw // T, "rows": (fh * N_IMG) // T,
        "frame_rows": fh // T, "cells": cells, "data": data,
    }


# ------------------------------------------------------------- Aseprite
def ase_bytes(calques, w, h, frames=N_IMG, duree=PAS_MS):
    """Fichier .aseprite : cels liés pour les calques fixes."""
    def ch(k, d):
        return struct.pack("<IH", len(d) + 6, k) + d

    def astr(s):
        b = s.encode("utf-8")
        return struct.pack("<H", len(b)) + b

    chunks = []
    frames_parts = [[] for _ in range(frames)]
    for i, (nom, _, _) in enumerate(calques):
        flags = 1 | 2
        frames_parts[0].append(ch(0x2004, struct.pack(
            "<HHHHHHBxxx", flags, 0, 0, 0, 0, 0, 255) + astr(nom)))
    for f in range(frames):
        for i, (nom, imgs, anim) in enumerate(calques):
            if anim:
                im = imgs[f]
            else:
                im = imgs[0] if f == 0 else "link"
            if im == "link":
                frames_parts[f].append(ch(0x2006, struct.pack("<HH", i, 0)))
                continue
            box = im.getbbox()
            if box is None:
                continue
            x, y = box[0], box[1]
            q = im.crop(box)
            data = struct.pack("<HhhBHh", i, x, y, 255, 2, 0) + b"\0" * 5 \
                + struct.pack("<HH", q.size[0], q.size[1]) \
                + zlib.compress(q.convert("RGBA").tobytes(), 9)
            frames_parts[f].append(ch(0x2005, data))
    for parts in frames_parts:
        body = b"".join(parts)
        frame = struct.pack("<IHHH2sI", len(body) + 16, 0xF1FA,
                            min(len(parts), 0xFFFF), duree, b"\0\0",
                            len(parts)) + body
        chunks.append(frame)
    data = b"".join(chunks)
    total = len(data) + 128
    head = bytearray(128)
    struct.pack_into("<IHHHHHIH", head, 0, total, 0xA5E0, frames, w, h, 32, 1, duree)
    struct.pack_into("<H", head, 18, duree)          # speed (hérité)
    struct.pack_into("<HBBhhHH", head, 32, 0, 1, 1, 0, 0, T, T)
    return head + data


# ------------------------------------------------------------- HTML
def b64_webp(im):
    b = io.BytesIO()
    im.convert("RGBA").save(b, format="WEBP", lossless=True, exact=True, method=4)
    return "data:image/webp;base64," + base64.b64encode(b.getvalue()).decode()


def ecrire_html(jeu):
    data = {"calques": [], "modes": {}}
    for mode in MODES:
        frames = {}
        for cid in ORDRE:
            v = jeu[mode][cid]
            frames[cid] = [b64_webp(im) for im in (v if cid in ANIMES else [v[0]])]
        data["modes"][mode] = frames
    data["ids"] = [{"id": cid, "nom": label, "anime": anim}
                   for cid, label, anim in CALQUE_IDS]
    gabarit = """<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Clairière de la guilde — visionneuse</title><style>
:root{color-scheme:dark}body{margin:0;background:#171b18;color:#f2ecda;
font:14px/1.45 system-ui,sans-serif}main{max-width:1200px;margin:auto;padding:20px}
h1{font-size:22px;margin:4px 0 10px}.bar{display:flex;gap:8px;flex-wrap:wrap;
align-items:center;margin-bottom:12px}button,select{border:1px solid #3e4735;
border-radius:7px;background:#2a3126;color:inherit;padding:7px 10px;cursor:pointer}
button.on{background:#e7c37a;color:#2b2314;font-weight:650}
.stage{background:#12142f;border-radius:10px;padding:10px;overflow:auto}
canvas{display:block;image-rendering:pixelated;margin:auto}
.layers{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));
gap:4px 16px;margin-top:12px}.layer{display:flex;gap:6px;align-items:center;
font-size:12px;border-bottom:1px solid #384031;padding:6px 0}
</style></head><body><main>
<h1>Clairière de la guilde</h1>
<div class="sub">Jungle immersive · grand arbre · chemin de sable · bassin animé
au nord avec plateformes de pierre. 1024 × 768, calques 8 × 8, eau 12 images.</div>
<div class="bar">
<button class="on" data-mode="jour">Jour</button>
<button data-mode="nuit">Nuit</button>
<button id="play" class="on">⏸ Animation</button>
<select id="zoom"><option value="fit">Ajuster</option>
<option value="1">1×</option><option value="2">2×</option></select>
<span id="dim" style="font-size:11px;color:#a7b19a"></span></div>
<div class="stage"><canvas id="c" width="1024" height="768"></canvas></div>
<div class="layers" id="layers"></div>
<script>const DATA=__DATA__;
const C=document.getElementById('c'),X=C.getContext('2d');
let mode='jour',frame=0,play=true,images={};
const precharger=(cid,arr)=>{DATA.modes.jour[cid].forEach((_,f)=>{
const src=DATA.modes[mode][cid][Math.min(f,arr.length-1)];
});};
function imgsDe(cid){const arr=DATA.modes[mode][cid];
if(!images[mode+cid]){images[mode+cid]=arr.map(u=>{const i=new Image();
i.src=u;return i;});}return images[mode+cid];}
function dessiner(){X.clearRect(0,0,C.width,C.height);
for(const q of DATA.ids){if(!etat[q.id])continue;
const arr=imgsDe(q.id);const im=arr[Math.min(frame,arr.length-1)];
if(im.complete)X.drawImage(im,0,0);}
if(play){frame=(frame+1)%12;}}
let etat={};DATA.ids.forEach(q=>etat[q.id]=true);
const box=document.getElementById('layers');
DATA.ids.forEach(q=>{const l=document.createElement('label');l.className='layer';
l.innerHTML=`<input type="checkbox" checked> ${q.nom}`;
l.querySelector('input').onchange=e=>{etat[q.id]=e.target.checked;dessiner();};
box.appendChild(l);});
document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{
document.querySelectorAll('[data-mode]').forEach(x=>x.classList.remove('on'));
b.classList.add('on');mode=b.dataset.mode;dessiner();});
const pb=document.getElementById('play');
pb.onclick=()=>{play=!play;pb.classList.toggle('on',play);
pb.textContent=play?'⏸ Animation':'▶ Animation';};
const z=document.getElementById('zoom');
z.onchange=()=>{if(z.value==='fit'){C.style.width='100%';C.style.height='auto';}
else{C.style.width=C.style.height=(1024*+z.value)+'px';}};
C.style.width='100%';C.style.height='auto';
document.getElementById('dim').textContent='1024 × 768 · tuiles 8 px';
setInterval(()=>{if(play)dessiner();},110);dessiner();
</script></main></body></html>"""
    html = gabarit.replace("__DATA__", json.dumps(data, separators=(",", ":")))
    (RACINE / "apercu_clairiere.html").write_text(html)


# ---------------------------------------------------------------- main
def main():
    os.makedirs(CALQUES, exist_ok=True)
    os.makedirs(TILED, exist_ok=True)
    os.makedirs(APERCUS, exist_ok=True)
    jeu = construire()

    print("— calques")
    for mode in MODES:
        ecrire_calques(jeu[mode], mode)

    print("— Tiled")
    strips = bandeau_bassin(jeu["jour"]["02_bassin"],
                            grille_de(masque_eau() & ~formes_de_base()[0]))
    for mode in MODES:
        ecrire_tiled(jeu[mode], mode, strips)

    print("— Aseprite")
    for mode in MODES:
        calq = [(cid, jeu[mode][cid], anim)
                for cid, _, anim in CALQUE_IDS]
        (RACINE / f"clairiere_{mode}.aseprite").write_bytes(
            ase_bytes(calq, LARG, HAUT))

    print("— aperçus")
    montage_j = composer(jeu["jour"])
    montage_j.convert("RGB").save(APERCUS / "apercu_jour.png")
    composer(jeu["nuit"]).convert("RGB").save(APERCUS / "apercu_nuit.png")
    frames = []
    for mode in MODES:
        for k in range(N_IMG):
            jk = {cid: (jeu[mode][cid][k] if cid in ANIMES else jeu[mode][cid])
                  for cid in ORDRE}
            frames.append(composer(jk, mode).convert("RGB"))
    frames[0].save(APERCUS / "apercu_anime.gif", save_all=True,
                   append_images=frames[1:], duration=PAS_MS, loop=0)

    print("— visionneuse")
    ecrire_html(jeu)

    print("fini —", RACINE)


if __name__ == "__main__":
    main()
