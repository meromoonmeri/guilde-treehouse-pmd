"""
composer_carte.py — carte de décor en calques, façon fond de sol PMD.

Les couches ne sont pas découpées après coup dans une image unique : chacune
est **dessinée séparément**, le fond lointain et le sol en pleine page, la
structure et les objets isolés sur fond noir. C'est la seule manière d'obtenir
des calques réellement indépendants, où l'on peut déplacer une arche ou retirer
un rocher sans toucher au reste.

Les lueurs de cristal sont animées par substitution de palette (DPLA), sur la
palette 11 — celle que le jeu réserve aux lueurs, la pierre restant fixe.
"""

from __future__ import annotations

import os
import sys
import json
import math
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
sys.path.insert(0, os.path.join(ICI, "..", "..", "foulards_pmd", "outils"))
sys.path.insert(0, os.path.join(ICI, "..", "..", "zones_pmd", "outils"))
sys.path.insert(0, os.path.join(ICI, "..", "..", "zone_boss_terapagos", "outils"))
import pixelisation as PX
import dpla as DPLA
import aseprite

RACINE = os.path.abspath(os.path.join(ICI, ".."))
SOURCES = os.path.join(RACINE, "sources_ia")
LARG, HAUT = 768, 512
N_IMG = 12
DUREE_MS = 110

CALQUES = [
    {"nom": "GROUPE_DECOR", "type": "groupe"},
    {"nom": "00_fond", "niveau": 1},
    {"nom": "01_sol", "niveau": 1},
    {"nom": "02_structure", "niveau": 1},
    {"nom": "03_objets", "niveau": 1},
    {"nom": "GROUPE_VIE", "type": "groupe"},
    {"nom": "04_lueurs", "niveau": 1, "fusion": aseprite.ADDITION},
    {"nom": "05_lumiere", "niveau": 1, "fusion": aseprite.ADDITION},
    {"nom": "06_particules", "niveau": 1, "fusion": aseprite.ADDITION},
    {"nom": "07_bordure_avant", "fusion": aseprite.MULTIPLIER, "opacite": 215},
]
ADDITIFS = {"04_lueurs", "05_lumiere", "06_particules"}


# --------------------------------------------------------------------------

def pleine_page(chemin, couleurs=30):
    im, _ = PX.convertir(chemin, LARG, HAUT, n_couleurs=couleurs, niveaux=7)
    return im.convert("RGBA")


def detourer(chemin, seuil=34, couleurs=26):
    """
    Détoure un élément dessiné sur fond noir.

    Le seuil porte sur la luminance : tout ce qui est plus sombre devient
    transparent. Les contours sont ensuite adoucis d'un pixel pour éviter le
    liseré noir que laisse un détourage brut.
    """
    im = Image.open(chemin).convert("RGB")
    im = ImageEnhance.Color(im).enhance(0.94)
    im = PX.refroidir(PX.purger_magenta(im))
    im = im.filter(ImageFilter.MedianFilter(3))
    im = PX.posteriser(im, 7)
    q = im.quantize(colors=couleurs, method=Image.Quantize.MAXCOVERAGE,
                    dither=Image.Dither.NONE).convert("RGBA")
    a = np.array(q)
    lum = a[..., :3].astype(np.float32).mean(axis=2)
    a[..., 3] = np.where(lum > seuil, 255, 0)
    # on efface les pixels isolés, résidus du fond
    m = a[..., 3] > 0
    pad = np.pad(m, 1, constant_values=False)
    v = np.zeros_like(m, dtype=int)
    for dy in (0, 1, 2):
        for dx in (0, 1, 2):
            if dy == 1 and dx == 1:
                continue
            v += pad[dy:dy + m.shape[0], dx:dx + m.shape[1]].astype(int)
    a[..., 3] = np.where(m & (v >= 2), 255, 0)
    return Image.fromarray(a, "RGBA")


def decouper_objets(im, aire_min=900):
    """Sépare les objets d'une planche détourée, par composantes connexes."""
    from collections import deque
    a = np.array(im)
    m = a[..., 3] > 0
    h, w = m.shape
    vus = np.zeros_like(m)
    objets = []
    for y0 in range(h):
        for x0 in range(w):
            if not m[y0, x0] or vus[y0, x0]:
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
                        if 0 <= ny < h and 0 <= nx < w and m[ny, nx] and not vus[ny, nx]:
                            vus[ny, nx] = True
                            q.append((ny, nx))
            if n >= aire_min:
                objets.append(im.crop((xs0, ys0, xs1 + 1, ys1 + 1)))
    objets.sort(key=lambda o: -o.size[0] * o.size[1])
    return objets


def masque_lueur(im, seuil_cyan=0.16, lum_min=0.34):
    """Pixels de lueur : cyan franc et clair. Ce sont eux qui s'animeront."""
    a = np.asarray(im.convert("RGBA"), dtype=np.float32) / 255.0
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return ((np.minimum(g, b) - r) > seuil_cyan) & (a[..., :3].mean(2) > lum_min) \
        & (a[..., 3] > 0.5)


def calque_depuis_masque(im, masque):
    a = np.array(im.convert("RGBA"))
    o = np.zeros_like(a)
    o[masque] = a[masque]
    return Image.fromarray(o, "RGBA")


def rayons(points, couleur, force=0.32):
    t = np.zeros((HAUT, LARG, 4), dtype=np.float32)
    for (cx, base, lw, haut) in points:
        for j in range(haut):
            y = base - j
            if y < 0 or y >= HAUT:
                continue
            u = j / max(haut - 1, 1)
            l = lw * (1 + u * 0.8)
            for dx in range(int(-l), int(l) + 1):
                x = cx + dx
                if not (0 <= x < LARG):
                    continue
                d = abs(dx) / max(l, 1e-6)
                f = (1 - d) ** 2.4 * (1 - u) ** 0.9 * force
                t[y, x, :3] = np.minimum(255, t[y, x, :3] + np.array(couleur) * f)
                t[y, x, 3] = min(255, t[y, x, 3] + 255 * f)
    return Image.fromarray(np.clip(t, 0, 255).astype(np.uint8), "RGBA")


def poussiere(phase, n=60, couleur=(170, 225, 255), graine=5):
    t = np.zeros((HAUT, LARG, 4), dtype=np.float32)
    rng = np.random.default_rng(graine)
    for i in range(n):
        bx, by = rng.uniform(0, LARG), rng.uniform(0, HAUT)
        x = (bx + phase * 22 * rng.uniform(0.4, 1.4)) % LARG
        y = (by - phase * 30 * rng.uniform(0.4, 1.4)) % HAUT
        f = 0.30 + 0.45 * (0.5 + 0.5 * math.sin(phase * 6.283 * 2 + i))
        xi, yi = int(x), int(y)
        t[yi, xi, :3] = np.minimum(255, t[yi, xi, :3] + np.array(couleur) * f)
        t[yi, xi, 3] = min(255, t[yi, xi, 3] + 255 * f)
    return Image.fromarray(np.clip(t, 0, 255).astype(np.uint8), "RGBA")


def bordure_avant(force=190):
    ys, xs = np.mgrid[0:HAUT, 0:LARG]
    d = np.sqrt(((xs - LARG / 2) / (LARG * 0.66)) ** 2
                + ((ys - HAUT * 0.56) / (HAUT * 0.72)) ** 2)
    v = np.clip((d - 0.66) * 1.9, 0, 1)
    a = np.zeros((HAUT, LARG, 4), dtype=np.uint8)
    a[..., :3] = np.array([5, 7, 18])
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
# Montage
# --------------------------------------------------------------------------

def main(graine=3):
    for d in ("calques", "aseprite", "tiled", "apercus"):
        os.makedirs(os.path.join(RACINE, d), exist_ok=True)
    rng = np.random.default_rng(graine)

    fond = pleine_page(os.path.join(SOURCES, "01_fond.png"), 26)
    # Le sol garde une palette large : réduire à 18 couleurs le rendait
    # blotchy et détruisait la lecture de la pierre. Un essai concluant est
    # revenu en arrière ici.
    sol_src = pleine_page(os.path.join(SOURCES, "02_sol.png"), 30)

    # le sol n'occupe que la partie basse ; le haut reste au fond lointain
    a = np.array(sol_src)
    horizon = int(HAUT * 0.42)
    fondu = 26
    a[:horizon, 3] = 0
    for i in range(fondu):
        a[horizon + i, 3] = int(255 * (i / fondu))
    sol = Image.fromarray(a, "RGBA")

    arche_pl = detourer(os.path.join(SOURCES, "03_structure.png"), seuil=40)
    arches = decouper_objets(arche_pl, aire_min=6000)
    objets_pl = detourer(os.path.join(SOURCES, "04_objets.png"), seuil=38)
    props = decouper_objets(objets_pl, aire_min=1200)
    print(f"  arche : {len(arches)} élément(s) | objets : {len(props)}")

    # --- structure : l'arche, posée sur la ligne d'horizon ------------------
    c_struct = Image.new("RGBA", (LARG, HAUT))
    if arches:
        arc = arches[0]
        k = min(LARG * 0.52 / arc.size[0], HAUT * 0.52 / arc.size[1])
        arc = arc.resize((int(arc.size[0] * k), int(arc.size[1] * k)),
                         Image.LANCZOS)
        # l'arche est posée pied sur l'horizon, pas suspendue au-dessus
        c_struct.paste(arc, (LARG // 2 - arc.size[0] // 2,
                             horizon + 26 - arc.size[1]), arc)

    # --- objets : posés sur le sol, les plus bas devant ---------------------
    c_obj = Image.new("RGBA", (LARG, HAUT))
    # Placement avec écart minimal : sans contrainte de distance les objets
    # s'entassent d'un côté et se chevauchent.
    places = []
    essais = 0
    while len(places) < 6 and essais < 200 and props:
        essais += 1
        p = props[int(rng.integers(0, len(props)))]
        k = rng.uniform(0.26, 0.42)
        p2 = p.resize((max(12, int(p.size[0] * k)), max(12, int(p.size[1] * k))),
                      Image.LANCZOS)
        y = int(rng.uniform(horizon + 60, HAUT - 24))
        # plus l'objet est bas, plus il est proche : il grandit un peu
        prof = (y - horizon) / max(HAUT - horizon, 1)
        e = 0.85 + 0.45 * prof
        p2 = p2.resize((int(p2.size[0] * e), int(p2.size[1] * e)), Image.LANCZOS)
        x = int(rng.uniform(16, LARG - 16 - p2.size[0]))
        cx = x + p2.size[0] // 2
        # le passage central reste dégagé
        if abs(cx - LARG // 2) < 110:
            continue
        if any(abs(cx - (px + pp.size[0] // 2)) < 70 and abs(y - py) < 60
               for py, px, pp in places):
            continue
        places.append((y, x, p2))
    for y, x, p2 in sorted(places):
        c_obj.paste(p2, (x, y - p2.size[1]), p2)

    # --- lueurs : extraites de la structure et des objets -------------------
    fusion = Image.alpha_composite(c_struct, c_obj)
    m_lueur = masque_lueur(fusion)
    c_lueur = calque_depuis_masque(fusion, m_lueur)
    print(f"  pixels de lueur : {int(m_lueur.sum())}")

    rampe = DPLA.rampe_depuis_tuiles([c_lueur.convert("RGB")], n_couleurs=10) \
        if m_lueur.any() else []
    table = DPLA.table_depuis_rampe(rampe, depuis=3) if len(rampe) >= 3 else None

    lueurs_img = [c_lueur] * N_IMG
    if table is not None:
        arr = np.array(c_lueur)
        plein = arr[..., 3] > 0
        r = np.array(rampe, dtype=np.float32)
        px = arr[plein][:, :3].astype(np.float32)
        carte = np.zeros(arr.shape[:2], dtype=np.int32)
        carte[plein] = np.argmin(np.linalg.norm(px[:, None, :] - r[None, :, :],
                                                axis=2), axis=1)
        periode = table.periode(0) or 12
        pas = max(1, periode // N_IMG)
        lueurs_img = []
        for k in range(N_IMG):
            pal = table.palette_a_l_image(0, k * pas)
            tab = np.array([pal[i] if i < len(pal) else rampe[min(i, len(rampe) - 1)]
                            for i in range(len(rampe))], dtype=np.uint8)
            for i in range(min(3, len(rampe))):
                tab[i] = rampe[i]
            o = np.zeros_like(arr)
            o[..., :3] = tab[np.clip(carte, 0, len(tab) - 1)]
            o[..., 3] = np.where(plein, 255, 0)
            lueurs_img.append(Image.fromarray(o, "RGBA"))

    # --- lumière et bordure -------------------------------------------------
    pts = [(LARG // 2, horizon + 120, 22, 200),
           (int(LARG * 0.22), HAUT - 60, 16, 240),
           (int(LARG * 0.80), HAUT - 80, 18, 220)]
    c_lum = rayons(pts, (150, 215, 255), 0.26)
    c_bord = bordure_avant()

    images = []
    for k in range(N_IMG):
        images.append({
            "00_fond": fond, "01_sol": sol, "02_structure": c_struct,
            "03_objets": c_obj, "04_lueurs": lueurs_img[k],
            "05_lumiere": c_lum,
            "06_particules": poussiere(k / N_IMG),
            "07_bordure_avant": c_bord,
        })

    for nom, im in images[0].items():
        im.save(os.path.join(RACINE, "calques", f"{nom}.png"), optimize=True)
    frames = [composer(j) for j in images]
    frames[0].convert("RGB").save(os.path.join(RACINE, "calques", "compose.png"),
                                  optimize=True)

    aseprite.ecrire_avance(
        os.path.join(RACINE, "aseprite", "carte_entree.aseprite"),
        CALQUES, images, (LARG, HAUT), duree_ms=DUREE_MS,
        palette=[tuple(c) for c in rampe] or None,
        tags=[("ambiance", 0, N_IMG - 1, aseprite.AVANT, (120, 200, 240))])
    if table is not None:
        table.ecrire_json(os.path.join(RACINE, "calques", "lueurs_dpla.json"))

    gif = [f.resize((LARG // 2, HAUT // 2), Image.LANCZOS)
           .convert("P", palette=Image.ADAPTIVE, colors=128) for f in frames]
    gif[0].save(os.path.join(RACINE, "apercus", "carte_entree.gif"),
                save_all=True, append_images=gif[1:], duration=DUREE_MS,
                loop=0, disposal=2, optimize=True)

    ecrire_tmx()
    json.dump({"taille": [LARG, HAUT], "horizon": horizon,
               "calques": [c["nom"] for c in CALQUES if c.get("type") != "groupe"],
               "images": N_IMG, "duree_ms": DUREE_MS,
               "lueurs_animees": table is not None,
               "periode_tics": table.periode(0) if table else None},
              open(os.path.join(RACINE, "carte.json"), "w"), indent=1,
              ensure_ascii=False)
    print("  calques, .aseprite, .tmx et GIF écrits")


def ecrire_tmx():
    """Carte Tiled : un calque d'image par couche, dans l'ordre."""
    noms = [c["nom"] for c in CALQUES if c.get("type") != "groupe"]
    L = ['<?xml version="1.0" encoding="UTF-8"?>',
         f'<map version="1.10" tiledversion="1.10.2" orientation="orthogonal" '
         f'renderorder="right-down" width="{LARG // 8}" height="{HAUT // 8}" '
         f'tilewidth="8" tileheight="8" infinite="0" '
         f'nextlayerid="{len(noms) + 1}" nextobjectid="1">']
    for i, n in enumerate(noms, start=1):
        L.append(f' <imagelayer id="{i}" name="{n}">')
        L.append(f'  <image source="../calques/{n}.png" '
                 f'width="{LARG}" height="{HAUT}"/>')
        L.append(' </imagelayer>')
    L.append('</map>')
    open(os.path.join(RACINE, "tiled", "carte_entree.tmx"), "w").write(
        "\n".join(L) + "\n")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 3)
