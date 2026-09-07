"""
generer_foret_pmd.py — les deux zones forestières en direction artistique
Pokémon Mystery Dungeon (Explorers of Sky / Rescue Team), en vue de dessus.

Contrairement aux zones peintes, le décor n'est pas une planche unique : il est
**monté** à partir d'éléments isolés — un sol répétable, des rochers, des
arbres — placés par le script. C'est ce qui permet des calques réellement
séparés, et non une image découpée après coup.
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
from generer_zones import (Toile, arc, particules, rais_lumiere, vignette,
                           composer, coherence, LARG, HAUT, N_IMG)

RACINE = os.path.abspath(os.path.join(ICI, ".."))
SOURCES = os.path.join(RACINE, "sources_ia")
PX_JEU = 3          # un pixel PMD vaut 3 pixels d'écran


def sol_repetable(chemin, tuile=96):
    """
    Réduit la planche de sol à une tuile, la rend répétable par fondu croisé
    sur ses bords, puis la pave. Sans le fondu, la répétition ferait apparaître
    une grille très visible.
    """
    im = Image.open(chemin).convert("RGB")
    c = min(im.size)
    im = im.crop(((im.size[0] - c) // 2, (im.size[1] - c) // 2,
                  (im.size[0] - c) // 2 + c, (im.size[1] - c) // 2 + c))
    im = im.resize((tuile, tuile), Image.LANCZOS)
    a = np.asarray(im, dtype=np.float32)
    b = max(6, tuile // 8)
    r = np.linspace(0, 1, b)[:, None, None]
    a[:b] = a[:b] * r + a[-b:][::-1] * (1 - r)
    r2 = np.linspace(0, 1, b)[None, :, None]
    a[:, :b] = a[:, :b] * r2 + a[:, -b:][:, ::-1] * (1 - r2)
    tui = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
    tui = PX.posteriser(tui, 6).quantize(
        colors=18, method=Image.Quantize.MAXCOVERAGE,
        dither=Image.Dither.NONE).convert("RGBA")
    tui = tui.resize((tuile * PX_JEU, tuile * PX_JEU), Image.NEAREST)
    out = Image.new("RGBA", (LARG, HAUT))
    for y in range(0, HAUT, tui.size[1]):
        for x in range(0, LARG, tui.size[0]):
            out.paste(tui, (x, y))
    return out, tui


def elements(chemin, haut_max, n_couleurs=16):
    """Isole les éléments d'une planche tirée sur fond noir."""
    if not os.path.isfile(chemin):
        return []
    try:
        objets = PX.decouper_objets(chemin, n_couleurs=n_couleurs)
    except Exception as e:
        print("   découpe:", e)
        return []
    mis = []
    for o in objets:
        k = min(150 / o.size[0], haut_max / o.size[1], 1.0)
        mis.append(o.resize((max(8, int(o.size[0] * k)),
                             max(8, int(o.size[1] * k))), Image.LANCZOS))
    objets = mis
    nets = []
    for o in objets:
        if o.size[0] < 14 or o.size[1] < 14:
            continue
        # ramener à une résolution PMD puis regrossir : c'est ce passage qui
        # donne le pixel franc, la planche générée étant trop fine
        p = o.resize((max(6, o.size[0] // PX_JEU), max(6, o.size[1] // PX_JEU)),
                     Image.LANCZOS)
        a = np.array(p)
        a[..., 3] = np.where(a[..., 3] > 110, 255, 0)
        p = Image.fromarray(a, "RGBA").resize(
            (p.size[0] * PX_JEU, p.size[1] * PX_JEU), Image.NEAREST)
        nets.append(p)
    return nets


def ombre_portee(im, decal=(4, 6), force=110):
    a = np.array(im)
    o = np.zeros_like(a)
    o[..., 3] = (a[..., 3] > 0) * force
    o[..., :3] = np.array([12, 20, 14])
    return Image.fromarray(o, "RGBA")


def poser(cible, ombres, im, x, y, ancre_bas=True):
    px = int(x - im.size[0] // 2)
    py = int(y - im.size[1]) if ancre_bas else int(y)
    om = ombre_portee(im)
    ombres.alpha_composite(om, (px + 5, py + 7))
    cible.alpha_composite(im, (px, py))


def batir(cle, titre, plan_arbres, plan_rochers, teinte, part_c, rais):
    sol, _ = sol_repetable(os.path.join(SOURCES, "pmd_sol_foret.png"))
    arbres = elements(os.path.join(SOURCES, "pmd_arbres.png"), 210)
    rochers = elements(os.path.join(SOURCES, "pmd_rochers.png"), 120)
    print(f"  {cle}: {len(arbres)} arbres, {len(rochers)} éléments de sol")
    if not arbres or not rochers:
        print("  !! découpe insuffisante")
        return None

    c_roch = Image.new("RGBA", (LARG, HAUT))
    c_arb_ar = Image.new("RGBA", (LARG, HAUT))
    c_arb_av = Image.new("RGBA", (LARG, HAUT))
    c_omb = Image.new("RGBA", (LARG, HAUT))

    rng = np.random.default_rng(hash(cle) % 9999)
    for (x, y, i, ech) in plan_rochers:
        e = rochers[i % len(rochers)]
        e2 = e.resize((max(8, int(e.size[0] * ech)), max(8, int(e.size[1] * ech))),
                      Image.NEAREST)
        poser(c_roch, c_omb, e2, x, y)
    for (x, y, i, ech, avant) in plan_arbres:
        a = arbres[i % len(arbres)]
        a2 = a.resize((max(12, int(a.size[0] * ech)), max(12, int(a.size[1] * ech))),
                      Image.NEAREST)
        poser(c_arb_av if avant else c_arb_ar, c_omb, a2, x, y)

    ecl = vignette(190)
    struct = [
        {"nom": "GROUPE_SOL", "type": "groupe"},
        {"nom": "00_sol", "niveau": 1},
        {"nom": "01_ombres", "niveau": 1, "fusion": aseprite.MULTIPLIER,
         "opacite": 190},
        {"nom": "02_rochers", "niveau": 1},
        {"nom": "GROUPE_ARBRES", "type": "groupe"},
        {"nom": "03_arbres_arriere", "niveau": 1},
        {"nom": "04_arbres_avant", "niveau": 1},
        {"nom": "GROUPE_VIE", "type": "groupe"},
        {"nom": "05_particules", "niveau": 1, "fusion": aseprite.ADDITION},
        {"nom": "06_rais", "niveau": 1, "fusion": aseprite.ADDITION},
        {"nom": "07_eclairage", "fusion": aseprite.MULTIPLIER, "opacite": 200},
    ]
    add = {"05_particules", "06_rais"}

    images = []
    for i in range(N_IMG):
        ph = i / N_IMG
        images.append({
            "00_sol": sol, "01_ombres": c_omb, "02_rochers": c_roch,
            "03_arbres_arriere": c_arb_ar, "04_arbres_avant": c_arb_av,
            "05_particules": particules(ph, 70, 4242, part_c,
                                        (30, 20, 738, 490), (0.22, -0.4), 1, 0.5),
            "06_rais": rais_lumiere(ph, rais, (235, 240, 165), 0.22)
            if rais else Image.new("RGBA", (LARG, HAUT)),
            "07_eclairage": ecl,
        })

    frames = [composer(struct, j, add) for j in images]
    moy, mx, ec = coherence(frames)
    print(f"     fluidité : moyen {moy:.2f}  max {mx:.2f}  régularité {ec:.2f}")

    dz = os.path.join(RACINE, "decor", cle)
    os.makedirs(dz, exist_ok=True)
    for nom, im in images[0].items():
        im.save(os.path.join(dz, f"{nom}.png"), optimize=True)
    frames[0].convert("RGB").save(os.path.join(dz, "compose.png"), optimize=True)
    aseprite.ecrire_avance(
        os.path.join(RACINE, "aseprite", f"{cle}.aseprite"), struct, images,
        (LARG, HAUT), 100, palette=[arc(k / 12, 0.45, 0.9) for k in range(12)],
        tags=[("ambiance", 0, N_IMG - 1, aseprite.AVANT, (140, 210, 120))])
    g = [f.resize((LARG // 2, HAUT // 2), Image.LANCZOS).convert(
        "P", palette=Image.ADAPTIVE, colors=255) for f in frames]
    g[0].save(os.path.join(RACINE, "apercus", f"{cle}.gif"), save_all=True,
              append_images=g[1:], duration=100, loop=0, disposal=2, optimize=True)
    return (moy, mx, ec)


def main():
    os.makedirs(os.path.join(RACINE, "apercus"), exist_ok=True)
    # lisière : un chemin ouvert au centre, bordé d'arbres
    arb_e, roc_e = [], []
    for k in range(11):
        arb_e.append((10 + k * 76, 104 + (k % 3) * 14, k, 0.80, False))
    for k in range(11):
        arb_e.append((-24 + k * 76, 556 + (k % 2) * 16, k + 3, 0.92, True))
    for k in range(5):
        arb_e.append((-16 + k * 200, 300 + (k % 2) * 40, k + 1, 0.72,
                      False) if k in (0, 4) else (999, 999, 0, 0.1, False))
    arb_e[:] = [a for a in arb_e if a[0] < 900]
    for k in range(16):
        roc_e.append((70 + (k * 137) % 640, 220 + (k * 71) % 190, k, 0.62))
    r1 = batir("foret_entree_pmd", "Lisière — vue de dessus", arb_e, roc_e,
               0.26, (240, 245, 175), [(200, 20, 320), (520, 18, 300)])

    # clairière : anneau d'arbres fermé, centre dégagé
    arb_c, roc_c = [], []
    for k in range(20):
        a = 2 * math.pi * k / 20
        x = 384 + math.cos(a) * 392
        y = 262 + math.sin(a) * 268
        arb_c.append((x, y + 74, k, 0.74 + 0.18 * (math.sin(a) > 0),
                      math.sin(a) > 0.35))
    for k in range(16):
        a = 2 * math.pi * k / 16 + 0.3
        roc_c.append((384 + math.cos(a) * 250, 276 + math.sin(a) * 158, k, 0.60))
    r2 = batir("foret_coeur_pmd", "Clairière de Zarude — vue de dessus",
               arb_c, roc_c, 0.32, (185, 255, 190), [(384, 26, 300)])
    print("\nrécapitulatif :")
    for k, r in (("foret_entree_pmd", r1), ("foret_coeur_pmd", r2)):
        if r:
            print(f"  {k:<18} régularité {r[2]:.2f}  "
                  f"{'OK' if r[2] < 0.20 else 'à surveiller'}")


if __name__ == "__main__":
    main()
