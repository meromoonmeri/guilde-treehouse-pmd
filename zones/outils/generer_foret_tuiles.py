"""
generer_foret_tuiles.py — forêt en vraies tuiles, à la façon des donjons PMD.

Ce que les rendus précédents rataient : une salle de PMD n'est pas une
illustration, c'est une **grille de tuiles de 24 px** en basse résolution, avec
une palette très courte et des aplats sans dégradé. Le mur n'est pas une
collection d'arbres posés, c'est une masse pleine dotée d'un rebord.

Chaîne : planche de tuiles -> extraction -> quantification à 14 couleurs ->
plan de salle -> pose par autotuilage -> calques -> .aseprite.
"""

import os
import sys
import math
import numpy as np
from PIL import Image

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
sys.path.insert(0, os.path.join(ICI, "..", "..", "foulards_pmd", "outils"))
sys.path.insert(0, os.path.join(ICI, "..", "..", "zone_boss_terapagos", "outils"))
import aseprite
import pixelisation as PX
from generer_zones import Toile, arc, coherence

RACINE = os.path.abspath(os.path.join(ICI, ".."))
SOURCES = os.path.join(RACINE, "sources_ia")

T = 24                      # tuile PMD
COLS, LIGNES = 32, 21
LARG, HAUT = COLS * T, LIGNES * T          # 768 x 504
N_IMG = 12

# palette courte, imposée : c'est elle qui donne le cachet DS
PALETTE = [
    (0x14, 0x1A, 0x12), (0x1E, 0x2C, 0x1C), (0x2A, 0x3E, 0x24),
    (0x38, 0x54, 0x2C), (0x4A, 0x6E, 0x34), (0x60, 0x8A, 0x3E),
    (0x7C, 0xA8, 0x4C), (0x9C, 0xC0, 0x60),
    (0x2E, 0x22, 0x18), (0x46, 0x34, 0x22), (0x5E, 0x48, 0x2E),
    (0x7A, 0x60, 0x3C), (0x96, 0x7C, 0x50), (0xB4, 0x9A, 0x68),
    (0x30, 0x3A, 0x2E), (0xD8, 0xCE, 0x9A),
]


def _snap(im, palette=PALETTE):
    a = np.array(im.convert("RGBA"))
    m = a[..., 3] > 0
    if not m.any():
        return im
    p = np.array(palette, dtype=np.float32)
    px = a[m][:, :3].astype(np.float32)
    d = np.linalg.norm(px[:, None, :] - p[None, :, :], axis=2)
    a[m, :3] = p[np.argmin(d, axis=1)].astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def composer(structure, jeu, additifs):
    """Composition locale : la salle fait 504 px de haut, pas 512."""
    out = np.zeros((HAUT, LARG, 4), dtype=np.float32)
    for c in structure:
        if c.get("type") == "groupe":
            continue
        im = jeu.get(c["nom"])
        if im is None:
            continue
        a = np.asarray(im.convert("RGBA"), dtype=np.float32)[:HAUT, :LARG]
        k = a[..., 3:4] / 255.0
        if c["nom"] in additifs:
            out[..., :3] = np.minimum(255.0, out[..., :3] + a[..., :3] * k)
            out[..., 3] = np.minimum(255.0, out[..., 3] + a[..., 3])
        else:
            out[..., :3] = a[..., :3] * k + out[..., :3] * (1 - k)
            out[..., 3] = np.minimum(255.0, a[..., 3] + out[..., 3] * (1 - k[..., 0]))
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")


def vignette(force=160):
    ys, xs = np.mgrid[0:HAUT, 0:LARG]
    d = np.sqrt(((xs - LARG / 2) / (LARG * 0.64)) ** 2
                + ((ys - HAUT / 2) / (HAUT * 0.72)) ** 2)
    v = np.clip((d - 0.72) * 1.8, 0, 1)
    a = np.zeros((HAUT, LARG, 4), dtype=np.uint8)
    a[..., :3] = np.array([6, 10, 8])
    a[..., 3] = (v * force).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def particules(phase, n, graine, couleur, zone, derive, taille=1, force=0.5):
    t = Toile(LARG, HAUT)
    rng = np.random.default_rng(graine)
    x0, y0, x1, y1 = zone
    for i in range(n):
        bx, by = rng.uniform(x0, x1), rng.uniform(y0, y1)
        vx, vy = derive
        px = x0 + ((bx - x0) + vx * phase * (x1 - x0)) % (x1 - x0)
        py = y0 + ((by - y0) + vy * phase * (y1 - y0)) % (y1 - y0)
        px += math.sin(phase * 2 * math.pi + i) * 3.0
        vif = 0.45 + 0.55 * (0.5 + 0.5 * math.sin(phase * 6.28 * 2 + i * 1.7))
        t.ajouter(px, py, couleur, force * vif)
    return t.img()


def extraire_tuiles():
    """Isole les tuiles de la planche, les ramène à 24 px et cale la palette."""
    chemin = os.path.join(SOURCES, "pmd_tileset.png")
    objets = PX.decouper_objets(chemin, ech_travail=4, n_couleurs=16,
                                marge=0, aire_min=0.0008)
    tuiles = []
    for o in objets:
        c = min(o.size)
        o = o.crop(((o.size[0] - c) // 2, (o.size[1] - c) // 2,
                    (o.size[0] - c) // 2 + c, (o.size[1] - c) // 2 + c))
        o = o.resize((T, T), Image.LANCZOS)
        a = np.array(o)
        a[..., 3] = 255
        # Rejet des tuiles polluées par la gouttière blanche de la planche :
        # elles se répètent ensuite en barres claires sur tout le sol.
        lum = a[..., :3].astype(np.float32).mean(axis=2)
        if (lum > 196).mean() > 0.04 or lum.mean() > 172:
            continue
        tuiles.append(_snap(Image.fromarray(a, "RGBA")))
    return tuiles


def trier(tuiles):
    """Range les tuiles en sol, canopée et rebord, d'après leur teinte."""
    sol, feuille, bord = [], [], []
    for t in tuiles:
        a = np.asarray(t.convert("RGB"), dtype=np.float32)
        r, g, b = a[..., 0].mean(), a[..., 1].mean(), a[..., 2].mean()
        lum = (r + g + b) / 3
        vert = g - max(r, b)
        if vert > 14 and lum < 96:
            feuille.append(t)
        elif lum < 62:
            bord.append(t)
        else:
            sol.append(t)
    if not sol:
        sol = tuiles[:1]
    if not feuille:
        feuille = tuiles[-1:]
    if not bord:
        bord = [assombrir(feuille[0], 0.55)]
    return sol, feuille, bord


def assombrir(t, k):
    a = np.array(t, dtype=np.float32)
    a[..., :3] *= k
    return _snap(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA"))


# --------------------------------------------------------------------------
# Plan de salle
# --------------------------------------------------------------------------

def plan_lisiere():
    """Un couloir large qui traverse, mur en haut et en bas."""
    g = np.ones((LIGNES, COLS), dtype=np.int8)          # 1 = mur
    for y in range(LIGNES):
        for x in range(COLS):
            haut_ = 4 + int(1.6 * math.sin(x * 0.42))
            bas = LIGNES - 5 - int(1.6 * math.cos(x * 0.33))
            if haut_ <= y <= bas:
                g[y, x] = 0
    return g


def plan_clairiere():
    """Une clairière ronde cernée de mur, avec deux ouvertures."""
    g = np.ones((LIGNES, COLS), dtype=np.int8)
    cx, cy = COLS / 2, LIGNES / 2
    for y in range(LIGNES):
        for x in range(COLS):
            d = math.hypot((x - cx) / (COLS * 0.40), (y - cy) / (LIGNES * 0.40))
            d += 0.06 * math.sin(math.atan2(y - cy, x - cx) * 5.0)
            if d < 1.0:
                g[y, x] = 0
    for x in range(COLS // 2 - 2, COLS // 2 + 2):
        g[:, x] = np.where(np.arange(LIGNES) < 3, 1, g[:, x])
        g[LIGNES - 3:, x] = 0
        g[:3, x] = 0
    return g


def poser_salle(g, sol, feuille, bord):
    """
    Pose les tuiles. Le rebord n'est dessiné que sous une case de mur dont la
    voisine du dessous est du sol : c'est ce liseré qui donne le relief des
    donjons PMD, et sans lui la masse de feuillage paraît plate.
    """
    c_sol = Image.new("RGBA", (LARG, HAUT))
    c_mur = Image.new("RGBA", (LARG, HAUT))
    c_bord = Image.new("RGBA", (LARG, HAUT))
    rng = np.random.default_rng(7)
    for y in range(LIGNES):
        for x in range(COLS):
            px, py = x * T, y * T
            c_sol.paste(sol[rng.integers(0, len(sol))], (px, py))
            if g[y, x] == 1:
                c_mur.paste(feuille[rng.integers(0, len(feuille))], (px, py))
                dessous = g[y + 1, x] if y + 1 < LIGNES else 1
                if dessous == 0:
                    c_bord.paste(bord[rng.integers(0, len(bord))], (px, py + T))
    return c_sol, c_mur, c_bord


def contour(masque_img, couleur=(0x0A, 0x10, 0x0A)):
    """Cerne la masse de mur d'un trait sombre, comme dans les donjons."""
    a = np.array(masque_img)
    plein = a[..., 3] > 0
    pad = np.pad(plein, 1, constant_values=False)
    vois = np.zeros_like(plein)
    for dy in (0, 1, 2):
        for dx in (0, 1, 2):
            vois |= pad[dy:dy + plein.shape[0], dx:dx + plein.shape[1]]
    bord = vois & ~plein
    o = np.zeros_like(a)
    o[bord, :3] = couleur
    o[bord, 3] = 255
    return Image.fromarray(o, "RGBA")


def batir(cle, g, part_c):
    tuiles = extraire_tuiles()
    sol, feuille, bord = trier(tuiles)
    print(f"  {cle}: {len(tuiles)} tuiles -> {len(sol)} sol, "
          f"{len(feuille)} canopée, {len(bord)} rebord")
    c_sol, c_mur, c_bord = poser_salle(g, sol, feuille, bord)
    c_ctr = contour(c_mur)
    ecl = vignette(150)

    struct = [
        {"nom": "GROUPE_SALLE", "type": "groupe"},
        {"nom": "00_sol", "niveau": 1},
        {"nom": "01_rebord", "niveau": 1},
        {"nom": "02_mur_feuillage", "niveau": 1},
        {"nom": "03_contour", "niveau": 1},
        {"nom": "GROUPE_VIE", "type": "groupe"},
        {"nom": "04_particules", "niveau": 1, "fusion": aseprite.ADDITION},
        {"nom": "05_eclairage", "fusion": aseprite.MULTIPLIER, "opacite": 170},
    ]
    add = {"04_particules"}
    images = []
    for i in range(N_IMG):
        ph = i / N_IMG
        images.append({
            "00_sol": c_sol, "01_rebord": c_bord, "02_mur_feuillage": c_mur,
            "03_contour": c_ctr,
            "04_particules": particules(ph, 46, 99, part_c,
                                        (20, 20, LARG - 20, HAUT - 20),
                                        (0.18, -0.34), 1, 0.42),
            "05_eclairage": ecl,
        })
    frames = [composer(struct, j, add) for j in images]
    moy, mx, ec = coherence(frames)
    print(f"     fluidité : moyen {moy:.2f}  régularité {ec:.2f}")

    dz = os.path.join(RACINE, "decor", cle)
    os.makedirs(dz, exist_ok=True)
    for nom, im in images[0].items():
        im.save(os.path.join(dz, f"{nom}.png"), optimize=True)
    frames[0].convert("RGB").save(os.path.join(dz, "compose.png"), optimize=True)
    Image.new("RGBA", (T * len(tuiles), T)).save(os.path.join(dz, "_t.png"))
    ts = Image.new("RGBA", (T * len(tuiles), T))
    for i, t in enumerate(tuiles):
        ts.paste(t, (i * T, 0))
    ts.save(os.path.join(dz, "tileset.png"))
    os.remove(os.path.join(dz, "_t.png"))
    aseprite.ecrire_avance(
        os.path.join(RACINE, "aseprite", f"{cle}.aseprite"), struct, images,
        (LARG, HAUT), 100, palette=PALETTE,
        tags=[("ambiance", 0, N_IMG - 1, aseprite.AVANT, (120, 190, 90))])
    g2 = [f.convert("P", palette=Image.ADAPTIVE, colors=64) for f in frames]
    g2[0].save(os.path.join(RACINE, "apercus", f"{cle}.gif"), save_all=True,
               append_images=g2[1:], duration=110, loop=0, disposal=2,
               optimize=True)
    return frames[0]


def main():
    os.makedirs(os.path.join(RACINE, "apercus"), exist_ok=True)
    a = batir("foret_entree_tuiles", plan_lisiere(), (0xD8, 0xCE, 0x9A))
    b = batir("foret_coeur_tuiles", plan_clairiere(), (0x9C, 0xC0, 0x60))
    o = Image.new("RGB", (LARG, HAUT * 2))
    o.paste(a.convert("RGB"), (0, 0))
    o.paste(b.convert("RGB"), (0, HAUT))
    o.save(os.path.join(RACINE, "apercus", "foret_tuiles.png"))


if __name__ == "__main__":
    main()
